import os
import pandas as pd
import duckdb
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTableView,
    QProgressBar, QDialog, QComboBox
)
from PySide6.QtGui import QKeySequence, QShortcut
from .plot_tool import PlotDialog
from .i18n import Localization

CHUNK_SIZE = 1000
UNDO_LIMIT = 10

# --- DuckDB Manager ---
class DuckDBManager:
    def __init__(self, path="local.duckdb"):
        self.conn = duckdb.connect(database=path, read_only=False)

    def import_csv(self, csv_path, table_name, delimiter=';', has_header=True, ignore_errors=True, progress_callback=None):
        hdr = 'true' if has_header else 'false'
        err_flag = 'true' if ignore_errors else 'false'
        sql = f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_csv_auto(
                '{csv_path}',
                header={hdr},
                delim='{delimiter}',
                ignore_errors={err_flag},
                sample_size=-1
            );
        """
        self.conn.execute(sql)
        if progress_callback:
            progress_callback(100)

    def table_count(self, table_name):
        return self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    def get_page(self, table_name, offset=0, limit=CHUNK_SIZE):
        return self.conn.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}").fetchdf()

    def export_query_to_csv(self, sql, path, delimiter=';'):
        self.conn.execute(f"COPY ({sql}) TO '{path}' (DELIMITER '{delimiter}', HEADER TRUE);")

    def reformat_datetime_full_table(self, table_name):
        total_rows = self.table_count(table_name)
        if total_rows == 0: return
        df = self.get_page(table_name, 0, total_rows)
        if df.shape[1] < 2:
            raise ValueError("Not enough columns to reformat date and time")
        dates = df.iloc[:, 0].astype(str).str.replace(r'^D#', '', regex=True)
        times = df.iloc[:, 1].astype(str).str.replace(r'^TOD#', '', regex=True)
        combined = dates + ' ' + times
        dt = pd.to_datetime(combined, format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
        formatted = dt.dt.strftime('%d/%m/%Y %H:%M:%S.%f').str[:-3]
        df.iloc[:, 0] = formatted
        df.drop(df.columns[1], axis=1, inplace=True)
        self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.conn.register("tmp_df", df)
        self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM tmp_df")
        self.conn.unregister("tmp_df")

# --- Worker Thread ---
class WorkerThread(QtCore.QThread):
    progress = Signal(int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn, self.args, self.kwargs = fn, args, kwargs

    def run(self):
        try:
            def cb(p): self.progress.emit(int(p))
            if "progress_callback" in self.kwargs:
                self.kwargs["progress_callback"] = cb
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# --- Paging Table Model ---
class PagingTableModel(QAbstractTableModel):
    def __init__(self, db, table_name, parent=None):
        super().__init__(parent)
        self.db = db
        self.table_name = table_name
        self.page = 0
        self.page_size = CHUNK_SIZE
        self.total_rows = self.db.table_count(table_name)
        self._df = pd.DataFrame()
        self.undo_stack = []
        self.redo_stack = []
        self.load_page(0)

    def load_page(self, page_index):
        offset = page_index * self.page_size
        self._df = self.db.get_page(self.table_name, offset, self.page_size)
        self.page = page_index
        self.layoutChanged.emit()

    def rowCount(self, parent=QModelIndex()): return len(self._df)
    def columnCount(self, parent=QModelIndex()): return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            try: return str(self._df.iat[index.row(), index.column()])
            except: return ""
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and role == Qt.EditRole:
            self.push_undo()
            self._df.iat[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        return False

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole: return None
        return str(self._df.columns[section]) if orientation == Qt.Horizontal else str(section + 1 + self.page * self.page_size)

    # Undo/Redo
    def push_undo(self):
        self.undo_stack.append(self._df.copy())
        if len(self.undo_stack) > UNDO_LIMIT: self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self._df.copy())
            self._df = self.undo_stack.pop()
            self.layoutChanged.emit()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self._df.copy())
            self._df = self.redo_stack.pop()
            self.layoutChanged.emit()

# --- Advanced Settings Dialog ---
class AdvancedSettingsDialog(QDialog):
    def __init__(self, loc, initial_language="en", initial_delimiter=";"):
        super().__init__()
        self.loc = loc
        L = self.loc.t
        self.setWindowTitle(L("core.btn.advanced_settings"))
        self.resize(400, 150)

        self.selected_language = initial_language
        self.selected_delimiter = initial_delimiter

        layout = QVBoxLayout(self)

        # Language
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel(L("label.language")))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["en", "pl", "de", "jp"])
        self.lang_combo.setCurrentText(initial_language)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Delimiter
        delim_layout = QHBoxLayout()
        delim_layout.addWidget(QLabel(L("label.csv_delimiter")))
        self.delim_combo = QComboBox()
        self.delim_combo.addItems([L("delimiter.semicolon"), L("delimiter.comma"),
                                   L("delimiter.tab"), L("delimiter.pipe")])
        delim_map = {";": 0, ",": 1, "\t": 2, "|": 3}
        self.delim_combo.setCurrentIndex(delim_map.get(initial_delimiter, 0))
        delim_layout.addWidget(self.delim_combo)
        layout.addLayout(delim_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton(L("general.ok"))
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton(L("general.cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def get_values(self):
        lang = self.lang_combo.currentText()
        delim_index = self.delim_combo.currentIndex()
        delim_map_rev = {0: ";", 1: ",", 2: "\t", 3: "|"}
        delim = delim_map_rev.get(delim_index, ";")
        return lang, delim

# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self, loc, parent=None):
        super().__init__(parent)
        self.loc = loc
        self.db = DuckDBManager()
        self.current_table = None
        self.delimiter = ";"
        self.ignore_errors = True
        self.active_threads = []
        self.paging_model = None
        self.init_ui()

    def init_ui(self):
        L = self.loc.t
        self.setWindowTitle(L("core.app.title"))
        self.resize(1200, 800)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Toolbar
        toolbar = QHBoxLayout()
        self.table_name_input = QLineEdit("my_table")
        toolbar.addWidget(QLabel(L("core.label.table")))
        toolbar.addWidget(self.table_name_input)

        self.import_btn = QPushButton(L("core.btn.import_csv"))
        self.import_btn.clicked.connect(self.on_import)
        toolbar.addWidget(self.import_btn)

        self.clear_btn = QPushButton(L("core.btn.clear_table"))
        self.clear_btn.clicked.connect(self.on_clear)
        toolbar.addWidget(self.clear_btn)

        self.reformat_btn = QPushButton(L("core.btn.reformat_datetime"))
        self.reformat_btn.clicked.connect(self.reformat_datetime_column)
        toolbar.addWidget(self.reformat_btn)

        self.plot_btn = QPushButton(L("core.btn.plot_data"))
        self.plot_btn.clicked.connect(self.on_plot)
        toolbar.addWidget(self.plot_btn)

        self.settings_btn = QPushButton(L("core.btn.advanced_settings"))
        self.settings_btn.clicked.connect(self.on_advanced_settings)
        toolbar.addWidget(self.settings_btn)

        layout.addLayout(toolbar)

        # Table view
        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        # Pager
        pager = QHBoxLayout()
        self.prev_btn = QPushButton(L("core.btn.previous"))
        self.prev_btn.clicked.connect(self.on_prev_page)
        self.next_btn = QPushButton(L("core.btn.next"))
        self.next_btn.clicked.connect(self.on_next_page)
        self.page_label = QLabel()
        pager.addWidget(self.prev_btn)
        pager.addWidget(self.next_btn)
        pager.addWidget(self.page_label)
        layout.addLayout(pager)

        # Export
        tools = QHBoxLayout()
        self.export_csv_btn = QPushButton(L("core.btn.export_csv"))
        self.export_csv_btn.clicked.connect(self.on_export_csv)
        tools.addWidget(self.export_csv_btn)
        layout.addLayout(tools)

        # Status
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.status = QLabel(L("general.ready"))
        layout.addWidget(self.status)

        # Undo/Redo
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.on_undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self.on_redo)

        self.refresh_ui_texts()

    def refresh_ui_texts(self):
        L = self.loc.t
        self.setWindowTitle(L("core.app.title"))
        self.import_btn.setText(L("core.btn.import_csv"))
        self.clear_btn.setText(L("core.btn.clear_table"))
        self.reformat_btn.setText(L("core.btn.reformat_datetime"))
        self.plot_btn.setText(L("core.btn.plot_data"))
        self.settings_btn.setText(L("core.btn.advanced_settings"))
        self.prev_btn.setText(L("core.btn.previous"))
        self.next_btn.setText(L("core.btn.next"))
        self.export_csv_btn.setText(L("core.btn.export_csv"))
        self.status.setText(L("general.ready"))
        self.update_page_label()

    # --- Advanced Settings ---
    def on_advanced_settings(self):
        dlg = AdvancedSettingsDialog(
            self.loc,
            initial_language=self.loc.lang if hasattr(self.loc, "lang") else "en",
            initial_delimiter=self.delimiter
        )
        if dlg.exec() == QDialog.Accepted:
            new_lang, new_delim = dlg.get_values()
            self.loc.set_language(new_lang)
            self.delimiter = new_delim
            self.refresh_ui_texts()
            self.status.setText(f"Settings updated: Language={new_lang}, Delimiter={repr(new_delim)}")

    # --- Import ---
    def on_import(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not path: return
        table = self.table_name_input.text().strip()
        if not table:
            QtWidgets.QMessageBox.warning(self, "Table name needed", "Please provide a table name")
            return
        self.current_table = table
        self.set_busy(True)
        worker = WorkerThread(self.db.import_csv, path, self.current_table, self.delimiter, True, self.ignore_errors)
        self.active_threads.append(worker)
        worker.finished.connect(lambda _: self._on_import_finished(worker))
        worker.error.connect(lambda msg: self._on_worker_error(msg, worker))
        worker.start()

    @Slot()
    def _on_import_finished(self, worker):
        if worker in self.active_threads: self.active_threads.remove(worker)
        self.set_busy(False)
        self.on_load_full()
        self.status.setText(f"Imported {self.current_table}")

    # --- Clear ---
    def on_clear(self):
        self.current_table = None
        self.paging_model = None
        self.table_view.setModel(None)
        self.page_label.setText("Page: 0")
        self.status.setText("Table cleared")

    # --- Load Full ---
    def on_load_full(self):
        if not self.current_table:
            QMessageBox.warning(self, "No table", "Please import a CSV first.")
            return
        self.paging_model = PagingTableModel(self.db, self.current_table)
        self.table_view.setModel(self.paging_model)
        self.update_page_label()
        self.table_view.resizeColumnsToContents()

    # --- Plot Tool ---
    def on_plot(self):
        if not self.current_table:
            QMessageBox.warning(self, "No table", "Load or import a table first")
            return
        dlg = PlotDialog(self.db, self.current_table, self, self.loc)
        dlg.exec()

    # --- Pager ---
    def on_prev_page(self):
        if self.paging_model:
            new_page = max(0, self.paging_model.page - 1)
            self.paging_model.load_page(new_page)
            self.update_page_label()
            self.table_view.resizeColumnsToContents()

    def on_next_page(self):
        if self.paging_model:
            max_page = max(0, (self.paging_model.total_rows - 1) // self.paging_model.page_size)
            new_page = min(max_page, self.paging_model.page + 1)
            self.paging_model.load_page(new_page)
            self.update_page_label()
            self.table_view.resizeColumnsToContents()

    def update_page_label(self):
        L = self.loc.t
        if self.paging_model:
            max_page = max(0, (self.paging_model.total_rows - 1) // self.paging_model.page_size)
            self.page_label.setText(L("core.label.page", current=self.paging_model.page, max=max_page, total=self.paging_model.total_rows))
        else:
            self.page_label.setText(L("core.label.page", current=0, max=0, total=0))

    # --- Export ---
    def on_export_csv(self):
        if not self.current_table:
            QMessageBox.warning(self, "No table", "Load or import a table first")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not path: return
        sql = f"SELECT * FROM {self.current_table}"
        self.set_busy(True)
        worker = WorkerThread(self.db.export_query_to_csv, sql, path, self.delimiter)
        self.active_threads.append(worker)
        worker.finished.connect(lambda _: self._on_export_finished(worker, path))
        worker.error.connect(lambda msg: self._on_worker_error(msg, worker))
        worker.start()

    @Slot()
    def _on_export_finished(self, worker, path):
        if worker in self.active_threads: self.active_threads.remove(worker)
        self.set_busy(False)
        QMessageBox.information(self, "Export finished", f"Exported to {path}")
        self.status.setText(f"Exported to {path}")

    # --- Undo/Redo ---
    def on_undo(self):
        if self.paging_model:
            self.paging_model.undo()
            self.table_view.resizeColumnsToContents()

    def on_redo(self):
        if self.paging_model:
            self.paging_model.redo()
            self.table_view.resizeColumnsToContents()

    # --- Date/Time Reformat ---
    def reformat_datetime_column(self):
        if not self.current_table: return
        self.set_busy(True)
        def job():
            self.db.reformat_datetime_full_table(self.current_table)
            return True
        worker = WorkerThread(job)
        self.active_threads.append(worker)
        worker.finished.connect(lambda _: self._on_full_reformat_done(worker))
        worker.error.connect(lambda msg: self._on_worker_error(msg, worker))
        worker.start()

    @Slot()
    def _on_full_reformat_done(self, worker):
        if worker in self.active_threads: self.active_threads.remove(worker)
        if not self.current_table:
            self.set_busy(False)
            return
        self.on_load_full()
        self.set_busy(False)
        self.status.setText("Full table date/time reformat completed")

    # --- Worker Error ---
    def _on_worker_error(self, msg, worker):
        if worker in self.active_threads: self.active_threads.remove(worker)
        self.set_busy(False)
        QMessageBox.critical(self, "Error", msg)
        self.status.setText("Error: " + msg)

    # --- Utilities ---
    def set_busy(self, busy):
        self.import_btn.setEnabled(not busy)
        self.clear_btn.setEnabled(not busy)
        self.reformat_btn.setEnabled(not busy)
        self.export_csv_btn.setEnabled(not busy)
        self.plot_btn.setEnabled(not busy)
        self.settings_btn.setEnabled(not busy)
