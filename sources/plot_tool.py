# plot_tool.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSlider,
    QPushButton, QComboBox, QSpinBox, QWidget
)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import timedelta

class PlotDialog(QDialog):
    def __init__(self, db_manager, table_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Data")
        self.resize(1050, 700)  # Start width 1050

        self.db = db_manager
        self.table_name = table_name

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
            except:
                continue
        if not self.datetime_col:
            raise ValueError("No valid datetime column found in table")

        # Detect numeric columns
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        self.y_columns = [col for col in numeric_cols if col != self.datetime_col]
        if not self.y_columns:
            raise ValueError("No numeric columns available for plotting")

        self.df = self.df.sort_values(self.datetime_col).reset_index(drop=True)

        # Timeline resolution
        self.slider_resolution = timedelta(minutes=1)
        start_time = self.df[self.datetime_col].min().replace(second=0, microsecond=0)
        end_time = self.df[self.datetime_col].max().replace(second=0, microsecond=0)
        self.timeline = pd.date_range(start=start_time, end=end_time, freq=self.slider_resolution)
        self.timeline_len = len(self.timeline)

        self.y_checkboxes = []

        layout = QVBoxLayout(self)

        # --- Toggle button at top ---
        self.toggle_chart_settings_btn = QPushButton("Toggle Chart Settings")
        self.toggle_chart_settings_btn.setCheckable(True)
        self.toggle_chart_settings_btn.setChecked(False)
        layout.addWidget(self.toggle_chart_settings_btn)

        # --- Chart settings container below toggle button ---
        self.chart_settings_container = QWidget()
        self.chart_settings_container.setVisible(False)
        chart_layout = QVBoxLayout(self.chart_settings_container)
        chart_layout.setSpacing(2)  # compact spacing
        chart_layout.setContentsMargins(0,2,0,2)

        # --- Start slider layout ---
        start_layout = QHBoxLayout()
        start_layout.setSpacing(2)
        start_layout.setContentsMargins(0,2,0,2)
        start_layout.addWidget(QLabel("Start:"))
        self.start_label = QLabel(str(self.timeline[0]))
        start_layout.addWidget(self.start_label)
        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.setMinimum(0)
        self.start_slider.setMaximum(self.timeline_len - 1)
        self.start_slider.setValue(0)
        self.start_slider.setFixedHeight(20)
        self.start_slider.valueChanged.connect(self.on_slider_change)
        start_layout.addWidget(self.start_slider)
        chart_layout.addLayout(start_layout)

        # --- End slider layout ---
        end_layout = QHBoxLayout()
        end_layout.setSpacing(2)
        end_layout.setContentsMargins(0,2,0,2)
        end_layout.addWidget(QLabel("End:"))
        self.end_label = QLabel(str(self.timeline[-1]))
        end_layout.addWidget(self.end_label)
        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.setMinimum(0)
        self.end_slider.setMaximum(self.timeline_len - 1)
        self.end_slider.setValue(self.timeline_len - 1)
        self.end_slider.setFixedHeight(20)
        self.end_slider.valueChanged.connect(self.on_slider_change)
        end_layout.addWidget(self.end_slider)
        chart_layout.addLayout(end_layout)

        # --- Y-axis checkboxes (horizontal row) ---
        cb_layout = QHBoxLayout()
        cb_layout.setSpacing(3)
        for i, col in enumerate(self.y_columns):
            cb = QCheckBox(col)
            cb.setChecked(i == 0)  # default first ticked
            cb.stateChanged.connect(self.update_plot)
            cb_layout.addWidget(cb)
            self.y_checkboxes.append(cb)
        chart_layout.addLayout(cb_layout)

        layout.addWidget(self.chart_settings_container)

        # Connect toggle to adjust window dynamically
        self.toggle_chart_settings_btn.toggled.connect(
            lambda checked: [self.chart_settings_container.setVisible(checked), self.adjust_window_height(self.chart_settings_container)]
        )

        # --- Plot canvas and toolbar ---
        self.fig, self.ax_main = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setVisible(False)
        layout.addWidget(self.toolbar)

        self.toggle_toolbar_btn = QPushButton("Toggle Plot Toolbox")
        self.toggle_toolbar_btn.setCheckable(True)
        self.toggle_toolbar_btn.toggled.connect(
            lambda checked: [self.toolbar.setVisible(checked), self.adjust_window_height(self.toolbar)]
        )
        layout.addWidget(self.toggle_toolbar_btn)

        # --- Filter toolbox ---
        self.toggle_filter_btn = QPushButton("Toggle Filter Toolbox")
        self.toggle_filter_btn.setCheckable(True)
        self.toggle_filter_btn.setChecked(False)
        layout.addWidget(self.toggle_filter_btn)

        self.filter_container = QWidget()
        self.filter_container.setVisible(False)
        filter_layout = QVBoxLayout(self.filter_container)
        filter_layout.setSpacing(2)
        filter_layout.setContentsMargins(0,2,0,2)

        # Filter options
        filt_layout = QHBoxLayout()
        filt_layout.addWidget(QLabel("Spike removal:"))
        self.spike_cb = QCheckBox("Enable")
        self.spike_cb.setChecked(False)
        self.spike_cb.stateChanged.connect(self.update_plot)
        filt_layout.addWidget(self.spike_cb)
        filt_layout.addWidget(QLabel("Spike window:"))
        self.spike_window = QSpinBox()
        self.spike_window.setMinimum(1)
        self.spike_window.setMaximum(50)
        self.spike_window.setValue(3)
        self.spike_window.valueChanged.connect(self.update_plot)
        filt_layout.addWidget(self.spike_window)

        filt_layout.addWidget(QLabel("Smoothing:"))
        self.filter_type = QComboBox()
        self.filter_type.addItems(["None", "SMA", "EMA"])
        self.filter_type.currentIndexChanged.connect(self.update_plot)
        filt_layout.addWidget(self.filter_type)
        filt_layout.addWidget(QLabel("Window:"))
        self.filter_window = QSpinBox()
        self.filter_window.setMinimum(1)
        self.filter_window.setMaximum(1000)
        self.filter_window.setValue(5)
        self.filter_window.valueChanged.connect(self.update_plot)
        filt_layout.addWidget(self.filter_window)
        filter_layout.addLayout(filt_layout)

        # Y-column filter checkboxes
        self.filter_y_checkboxes = []
        filter_y_layout = QHBoxLayout()
        for i, col in enumerate(self.y_columns):
            cb = QCheckBox(col)
            cb.setChecked(False)
            cb.stateChanged.connect(self.update_plot)
            filter_y_layout.addWidget(cb)
            self.filter_y_checkboxes.append(cb)
        filter_layout.addLayout(filter_y_layout)

        # Reset filters button
        self.reset_filters_btn = QPushButton("Reset Filters")
        self.reset_filters_btn.setFixedWidth(100)
        self.reset_filters_btn.clicked.connect(self.reset_filters)
        filter_layout.addWidget(self.reset_filters_btn)

        layout.addWidget(self.filter_container)
        self.toggle_filter_btn.toggled.connect(
            lambda checked: [self.filter_container.setVisible(checked), self.adjust_window_height(self.filter_container)]
        )

        # --- Initial plot ---
        self.update_plot()

    # --- Window resize helper ---
    def adjust_window_height(self, container=None):
        """
        Adjust window height dynamically for a specific container.
        If container is None, compute total visible height.
        """
        if container is None:
            total_height = 0
            for w in [self.toggle_chart_settings_btn, self.chart_settings_container,
                      self.canvas, self.toolbar, self.toggle_toolbar_btn,
                      self.toggle_filter_btn, self.filter_container]:
                if w.isVisible():
                    total_height += w.sizeHint().height()
            self.resize(self.width(), total_height + 20)
        else:
            h = container.sizeHint().height()
            if container.isVisible():
                self.resize(self.width(), self.height() + h)
            else:
                self.resize(self.width(), self.height() - h)

    def toggle_toolbar(self, checked):
        self.toolbar.setVisible(checked)

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

        start_time = self.timeline[start_idx]
        end_time = self.timeline[end_idx]

        self.start_label.setText(str(start_time))
        self.end_label.setText(str(end_time))

        self.update_plot()

    def apply_filter(self, series, col):
        data = series.copy()
        # Spike removal
        if self.spike_cb.isChecked() and col in [cb.text() for cb in self.filter_y_checkboxes if cb.isChecked()]:
            k = self.spike_window.value()
            data = data.rolling(window=k, center=True, min_periods=1).median()
        # Smoothing
        filter_type = self.filter_type.currentText()
        window = self.filter_window.value()
        if filter_type == "SMA" and col in [cb.text() for cb in self.filter_y_checkboxes if cb.isChecked()]:
            data = data.rolling(window=window, min_periods=1).mean()
        elif filter_type == "EMA" and col in [cb.text() for cb in self.filter_y_checkboxes if cb.isChecked()]:
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
            self.ax_main.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=range(0,60,5)))
        self.ax_main.legend().set_visible(False)
        self.ax_main.figure.autofmt_xdate()
        self.canvas.draw()
