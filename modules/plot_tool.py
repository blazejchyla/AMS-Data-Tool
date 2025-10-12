# ./modules/plot_tool.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSlider,
    QPushButton, QComboBox, QSpinBox, QWidget, QSizePolicy, QSpacerItem,
    QGridLayout, QFrame
)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import timedelta
from .i18n import L  # <-- Use global L from core

class PlotDialog(QDialog):
    def __init__(self, db_manager, table_name, parent=None, loc=None):
        super().__init__(parent)
        self.db = db_manager
        self.table_name = table_name
        self.loc = loc  # <-- passed from MainWindow

        # Helper: get localized string
        def T(key, default=None):
            return L(key, default)

        # --- Window ---
        self.setWindowTitle(T("plot.title", "Plot Data"))
        self.resize(1100, 730)

        # Load full table
        total_rows = self.db.table_count(table_name)
        self.df = self.db.get_page(table_name, 0, total_rows)

        # Detect datetime column
        datetime_cols = self.df.select_dtypes(include=['datetime64', 'object']).columns
        self.datetime_col = None
        for col in datetime_cols:
            try:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce', format='%d/%m/%Y %H:%M:%S.%f')
                if self.df[col].notna().any():
                    self.datetime_col = col
                    break
            except Exception:
                try:
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    if self.df[col].notna().any():
                        self.datetime_col = col
                        break
                except Exception:
                    continue

        if not self.datetime_col:
            raise ValueError(T("plot.error.no_datetime_col", "No valid datetime column found in table"))

        # Detect numeric columns
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        self.y_columns = [col for col in numeric_cols if col != self.datetime_col]
        if not self.y_columns:
            raise ValueError(T("plot.error.no_numeric_cols", "No numeric columns available for plotting"))

        self.df = self.df.sort_values(self.datetime_col).reset_index(drop=True)

        # Timeline
        self.slider_resolution = timedelta(minutes=1)
        start_time = self.df[self.datetime_col].min().replace(second=0, microsecond=0)
        end_time = self.df[self.datetime_col].max().replace(second=0, microsecond=0)
        self.timeline = pd.date_range(start=start_time, end=end_time, freq=self.slider_resolution)
        self.timeline_len = max(1, len(self.timeline))

        self.y_checkboxes = []

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(5, 5, 5, 5)

        # --- Toggle Chart Settings Button ---
        self.toggle_chart_settings_btn = QPushButton(T("plot.btn.toggle_chart_settings", "Toggle Chart Settings"))
        self.toggle_chart_settings_btn.setCheckable(True)
        self.toggle_chart_settings_btn.setChecked(False)
        layout.addWidget(self.toggle_chart_settings_btn)

        # --- Chart Settings ---
        self.chart_settings_container = QWidget()
        self.chart_settings_container.setVisible(False)
        self.chart_settings_container.setFixedSize(1080, 140)
        chart_layout = QVBoxLayout(self.chart_settings_container)
        chart_layout.setSpacing(2)
        chart_layout.setContentsMargins(0, 2, 0, 2)

        # Start slider
        start_layout = QHBoxLayout()
        start_layout.setSpacing(2)
        start_layout.setContentsMargins(0, 2, 0, 2)
        start_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        start_layout.addWidget(QLabel(T("plot.label.start", "Start:")))
        start_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.start_label = QLabel(str(self.timeline[0]))
        start_layout.addWidget(self.start_label)
        start_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.setMinimum(0)
        self.start_slider.setMaximum(self.timeline_len - 1)
        self.start_slider.setValue(0)
        self.start_slider.valueChanged.connect(self.on_slider_change)
        start_layout.addWidget(self.start_slider)
        start_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        chart_layout.addLayout(start_layout)

        # End slider
        end_layout = QHBoxLayout()
        end_layout.setSpacing(2)
        end_layout.setContentsMargins(0, 2, 0, 2)
        end_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        end_layout.addWidget(QLabel(T("plot.label.end", "End:")))
        end_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.end_label = QLabel(str(self.timeline[-1]))
        end_layout.addWidget(self.end_label)
        end_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.setMinimum(0)
        self.end_slider.setMaximum(self.timeline_len - 1)
        self.end_slider.setValue(self.timeline_len - 1)
        self.end_slider.valueChanged.connect(self.on_slider_change)
        end_layout.addWidget(self.end_slider)
        end_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        chart_layout.addLayout(end_layout)

        # Divider
        chart_divider_layout = QHBoxLayout()
        chart_divider_layout.addStretch()
        chart_divider = QFrame()
        chart_divider.setFrameShape(QFrame.HLine)
        chart_divider.setFrameShadow(QFrame.Sunken)
        chart_divider.setStyleSheet("background-color: #E0E0E0;")
        chart_divider.setFixedHeight(1)
        chart_divider.setFixedWidth(600)
        chart_divider_layout.addWidget(chart_divider)
        chart_divider_layout.addStretch()
        chart_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        chart_layout.addLayout(chart_divider_layout)
        chart_layout.addSpacerItem(QSpacerItem(0, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Y-axis checkboxes
        outer_cb_layout = QVBoxLayout()
        outer_cb_layout.setSpacing(3)
        outer_cb_layout.setContentsMargins(100, 2, 100, 5)
        outer_cb_layout.addWidget(QLabel(T("plot.label.select_data_for_plot", "Select data for plot:")))

        grid_cb_layout = QGridLayout()
        grid_cb_layout.setSpacing(3)
        max_per_row = 4
        for i, col in enumerate(self.y_columns):
            cb = QCheckBox(col)
            cb.setChecked(i == 0)
            cb.stateChanged.connect(self.update_plot)
            row = i // max_per_row
            col_idx = i % max_per_row
            grid_cb_layout.addWidget(cb, row, col_idx)
            self.y_checkboxes.append(cb)

        outer_cb_layout.addLayout(grid_cb_layout)
        chart_layout.addLayout(outer_cb_layout)
        layout.addWidget(self.chart_settings_container)
        self.toggle_chart_settings_btn.toggled.connect(
            lambda checked: [self.chart_settings_container.setVisible(checked), self.adjust_window_height()]
        )

        # --- Plot Canvas ---
        self.fig, self.ax_main = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # --- Toolbar ---
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setVisible(False)
        layout.addWidget(self.toolbar)
        self.toggle_toolbar_btn = QPushButton(T("plot.btn.toggle_plot_toolbox", "Toggle Plot Toolbox"))
        self.toggle_toolbar_btn.setCheckable(True)
        self.toggle_toolbar_btn.toggled.connect(
            lambda checked: [self.toolbar.setVisible(checked), self.adjust_window_height()]
        )
        layout.addWidget(self.toggle_toolbar_btn)

        # --- Filter toolbox ---
        self.toggle_filter_btn = QPushButton(T("plot.btn.toggle_filter_toolbox", "Toggle Filter Toolbox"))
        self.toggle_filter_btn.setCheckable(True)
        self.toggle_filter_btn.setChecked(False)
        layout.addWidget(self.toggle_filter_btn)

        self.filter_container = QWidget()
        self.filter_container.setVisible(False)
        self.filter_container.setFixedSize(1080, 170)
        filter_layout = QVBoxLayout(self.filter_container)
        filter_layout.setSpacing(2)
        filter_layout.setContentsMargins(20, 2, 20, 2)

        self.filter_y_checkboxes = []
        outer_filter_cb_layout = QVBoxLayout()
        outer_filter_cb_layout.setSpacing(3)
        outer_filter_cb_layout.setContentsMargins(0, 5, 0, 5)
        outer_filter_cb_layout.addWidget(QLabel(T("plot.label.assign_filter_to", "Assign filter to:")))

        grid_filter_cb_layout = QGridLayout()
        grid_filter_cb_layout.setSpacing(3)
        for i, col in enumerate(self.y_columns):
            cb = QCheckBox(col)
            cb.setChecked(False)
            cb.stateChanged.connect(self.update_plot)
            row = i // max_per_row
            col_idx = i % max_per_row
            grid_filter_cb_layout.addWidget(cb, row, col_idx)
            self.filter_y_checkboxes.append(cb)

        outer_filter_cb_layout.addLayout(grid_filter_cb_layout)
        filter_layout.addLayout(outer_filter_cb_layout)

        # Divider
        divider_layout = QHBoxLayout()
        divider_layout.addStretch()
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("background-color: #E0E0E0;")
        divider.setFixedHeight(1)
        divider.setFixedWidth(600)
        divider_layout.addWidget(divider)
        divider_layout.addStretch()
        filter_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        filter_layout.addLayout(divider_layout)
        filter_layout.addSpacerItem(QSpacerItem(0, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Filter form
        form_grid = QGridLayout()
        form_grid.setSpacing(10)
        form_grid.setContentsMargins(0, 5, 0, 5)

        # Peak reduction
        peak_container = QWidget()
        peak_layout = QGridLayout(peak_container)
        peak_layout.setSpacing(5)
        peak_layout.setContentsMargins(0, 0, 0, 0)
        peak_layout.addWidget(QLabel(T("plot.label.spike_removal", "Spike removal:")), 0, 0, Qt.AlignRight)
        self.spike_cb = QCheckBox(T("plot.chk.enable", "Enable"))
        self.spike_cb.stateChanged.connect(self.update_plot)
        peak_layout.addWidget(self.spike_cb, 0, 1, Qt.AlignLeft)
        peak_layout.addWidget(QLabel(T("plot.label.spike_window", "Spike window:")), 1, 0, Qt.AlignRight)
        self.spike_window = QSpinBox()
        self.spike_window.setMinimum(1)
        self.spike_window.setMaximum(50)
        self.spike_window.valueChanged.connect(self.update_plot)
        peak_layout.addWidget(self.spike_window, 1, 1, Qt.AlignLeft)
        form_grid.addWidget(peak_container, 0, 0, Qt.AlignTop)

        # Smoothing
        smooth_container = QWidget()
        smooth_layout = QGridLayout(smooth_container)
        smooth_layout.setSpacing(5)
        smooth_layout.setContentsMargins(0, 0, 0, 0)
        smooth_layout.addWidget(QLabel(T("plot.label.smoothing", "Smoothing:")), 0, 0, Qt.AlignRight)
        self.filter_type = QComboBox()
        self.filter_type.addItems([
            T("plot.opt.none", "None"),
            T("plot.opt.sma", "SMA"),
            T("plot.opt.ema", "EMA"),
        ])
        self.filter_type.currentIndexChanged.connect(self.update_plot)
        smooth_layout.addWidget(self.filter_type, 0, 1, Qt.AlignLeft)
        smooth_layout.addWidget(QLabel(T("plot.label.window", "Window:")), 1, 0, Qt.AlignRight)
        self.filter_window = QSpinBox()
        self.filter_window.setMinimum(1)
        self.filter_window.setMaximum(1000)
        self.filter_window.valueChanged.connect(self.update_plot)
        smooth_layout.addWidget(self.filter_window, 1, 1, Qt.AlignLeft)
        form_grid.addWidget(smooth_container, 0, 1, Qt.AlignTop)

        # Reset filters
        self.reset_filters_btn = QPushButton(T("plot.btn.reset_filters", "Reset Filters"))
        self.reset_filters_btn.setMaximumWidth(120)
        self.reset_filters_btn.clicked.connect(self.reset_filters)
        form_grid.addWidget(self.reset_filters_btn, 0, 2, Qt.AlignTop | Qt.AlignRight)

        filter_layout.addLayout(form_grid)
        layout.addWidget(self.filter_container)
        self.toggle_filter_btn.toggled.connect(
            lambda checked: [self.filter_container.setVisible(checked), self.adjust_window_height()]
        )

        # --- Initial plot ---
        self.update_plot()
        self.adjust_window_height()
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        self.move(x, screen_geometry.top())

    # --- Remaining methods unchanged ---
    def adjust_window_height(self):
        self.layout().activate()
        w = self.width()
        base_height = 730
        height_offset = 0
        toolbar_widget = getattr(self, "toolbar", None)
        for widget in [self.chart_settings_container, toolbar_widget, self.filter_container]:
            if widget and widget.isVisible():
                height_offset += widget.size().height()
        total_height = base_height + self.layout().contentsMargins().top() + self.layout().contentsMargins().bottom() + height_offset
        self.resize(w, total_height)

    def reset_filters(self):
        self.spike_cb.setChecked(False)
        self.spike_window.setValue(3)
        self.filter_type.setCurrentIndex(0)
        self.filter_window.setValue(5)
        for cb in self.filter_y_checkboxes:
            cb.setChecked(False)
        self.update_plot()

    def on_slider_change(self):
        start_idx = min(self.start_slider.value(), self.end_slider.value())
        end_idx = max(self.start_slider.value(), self.end_slider.value())
        self.start_slider.blockSignals(True)
        self.end_slider.blockSignals(True)
        self.start_slider.setValue(start_idx)
        self.end_slider.setValue(end_idx)
        self.start_slider.blockSignals(False)
        self.end_slider.blockSignals(False)
        self.start_label.setText(str(self.timeline[start_idx]))
        self.end_label.setText(str(self.timeline[end_idx]))
        self.update_plot()

    def apply_filter(self, series, col):
        data = series.copy()
        if self.spike_cb.isChecked() and col in [cb.text() for cb in self.filter_y_checkboxes if cb.isChecked()]:
            k = self.spike_window.value()
            data = data.rolling(window=k, center=True, min_periods=1).median()
        filter_type = self.filter_type.currentText()
        window = self.filter_window.value()
        if filter_type == self.filter_type.itemText(1) and col in [cb.text() for cb in self.filter_y_checkboxes if cb.isChecked()]:
            data = data.rolling(window=window, min_periods=1).mean()
        elif filter_type == self.filter_type.itemText(2) and col in [cb.text() for cb in self.filter_y_checkboxes if cb.isChecked()]:
            data = data.ewm(span=window, adjust=False).mean()
        return data

    def update_plot(self):
        start_time = self.timeline[self.start_slider.value()]
        end_time = self.timeline[self.end_slider.value()]
        filtered = self.df[(self.df[self.datetime_col] >= start_time) & (self.df[self.datetime_col] <= end_time)]
        self.ax_main.clear()
        for cb, col in zip(self.y_checkboxes, self.y_columns):
            if cb.isChecked():
                if col in [cb.text() for cb in self.filter_y_checkboxes if cb.isChecked()]:
                    data_to_plot = self.apply_filter(filtered[col], col)
                else:
                    data_to_plot = filtered[col]
                self.ax_main.plot(filtered[self.datetime_col], data_to_plot, label=col)
        self.ax_main.set_xlabel("")
        self.ax_main.set_ylabel("")
        self.ax_main.set_title("")
        self.ax_main.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y %H:%M'))
        time_span = (end_time - start_time).total_seconds() / 3600
        if time_span > 6:
            self.ax_main.xaxis.set_minor_locator(mdates.HourLocator())
        else:
            self.ax_main.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=range(0, 60, 5)))
        self.ax_main.legend().set_visible(False)
        self.ax_main.figure.autofmt_xdate()
        self.canvas.draw()
