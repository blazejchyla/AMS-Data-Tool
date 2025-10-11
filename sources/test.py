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
        self.resize(1050, 730)

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
        layout.setSpacing(0)
        layout.setContentsMargins(5, 5, 5, 5)

        # --- Toggle Chart Settings Button ---
        self.toggle_chart_settings_btn = QPushButton("Toggle Chart Settings")
        self.toggle_chart_settings_btn.setCheckable(True)
        self.toggle_chart_settings_btn.setChecked(False)
        layout.addWidget(self.toggle_chart_settings_btn)

        # --- Chart Settings Container ---
        self.chart_settings_container = QWidget()
        self.chart_settings_container.setVisible(False)
        self.chart_settings_container.setFixedSize(1050, 100)
        chart_layout = QVBoxLayout(self.chart_settings_container)
        chart_layout.setSpacing(2)
        chart_layout.setContentsMargins(0, 2, 0, 2)

        # --- Start Slider ---
        start_layout = QHBoxLayout()
        start_layout.setSpacing(2)
        start_layout.setContentsMargins(0, 2, 0, 2)
        start_layout.addWidget(QLabel("Start:"))
        self.start_label = QLabel(str(self.timeline[0]))
        start_layout.addWidget(self.start_label)
        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.setMinimum(0)
        self.start_slider.setMaximum(self.timeline_len - 1)
        self.start_slider.setValue(0)
        self.start_slider.valueChanged.connect(self.on_slider_change)
        start_layout.addWidget(self.start_slider)
        chart_layout.addLayout(start_layout)

        # --- End Slider ---
        end_layout = QHBoxLayout()
        end_layout.setSpacing(2)
        end_layout.setContentsMargins(0, 2, 0, 2)
        end_layout.addWidget(QLabel("End:"))
        self.end_label = QLabel(str(self.timeline[-1]))
        end_layout.addWidget(self.end_label)
        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.setMinimum(0)
        self.end_slider.setMaximum(self.timeline_len - 1)
        self.end_slider.setValue(self.timeline_len - 1)
        self.end_slider.valueChanged.connect(self.on_slider_change)
        end_layout.addWidget(self.end_slider)
        chart_layout.addLayout(end_layout)

        # --- Y-axis checkboxes ---
        cb_layout = QHBoxLayout()
        cb_layout.setSpacing(3)
        cb_layout.setContentsMargins(0, 2, 0, 2)
        for i, col in enumerate(self.y_columns):
            cb = QCheckBox(col)
            cb.setChecked(i == 0)
            cb.stateChanged.connect(self.update_plot)
            cb_layout.addWidget(cb)
            self.y_checkboxes.append(cb)
        chart_layout.addLayout(cb_layout)

        layout.addWidget(self.chart_settings_container)
        self.toggle_chart_settings_btn.toggled.connect(
            lambda checked: [self.chart_settings_container.setVisible(checked), self.adjust_window_height()]
        )

        # --- Plot Canvas ---
        self.fig, self.ax_main = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # --- Plot Toolbar ---
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setVisible(False)
        layout.addWidget(self.toolbar)
        self.toggle_toolbar_btn = QPushButton("Toggle Plot Toolbox")
        self.toggle_toolbar_btn.setCheckable(True)
        self.toggle_toolbar_btn.toggled.connect(
            lambda checked: [self.toolbar.setVisible(checked), self.adjust_window_height()]
        )
        layout.addWidget(self.toggle_toolbar_btn)

        # --- Filter Toolbox ---
        self.toggle_filter_btn = QPushButton("Toggle Filter Toolbox")
        self.toggle_filter_btn.setCheckable(True)
        self.toggle_filter_btn.setChecked(False)
        layout.addWidget(self.toggle_filter_btn)

        # Outer filter container
        self.filter_container = QWidget()
        self.filter_container.setVisible(False)
        self.filter_container.setFixedWidth(1050)
        filter_layout = QVBoxLayout(self.filter_container)
        filter_layout.setSpacing(6)
        filter_layout.setContentsMargins(6, 6, 6, 6)

        # Horizontal layout for two filter groups
        filter_groups_layout = QHBoxLayout()
        filter_groups_layout.setSpacing(8)

        # Peak Reduction Group
        self.peak_filter_container = QWidget()
        self.peak_filter_container.setFixedHeight(70)
        peak_layout = QVBoxLayout(self.peak_filter_container)
        peak_layout.setContentsMargins(8, 6, 8, 6)
        peak_layout.setSpacing(4)

        self.peak_filter_container.setStyleSheet("""
            QWidget {
                border: 1px solid #888;
                border-radius: 4px;
            }
        """)

        # Peak controls (original style)
        peak_controls_layout = QHBoxLayout()
        peak_controls_layout.addWidget(QLabel("Spike removal:"))
        self.spike_cb = QCheckBox("Enable")
        self.spike_cb.setChecked(False)
        self.spike_cb.stateChanged.connect(self.update_plot)
        peak_controls_layout.addWidget(self.spike_cb)
        peak_controls_layout.addWidget(QLabel("Spike window:"))
        self.spike_window = QSpinBox()
        self.spike_window.setMinimum(1)
        self.spike_window.setMaximum(50)
        self.spike_window.setValue(3)
        self.spike_window.valueChanged.connect(self.update_plot)
        peak_controls_layout.addStretch()
        peak_layout.addLayout(peak_controls_layout)

        filter_groups_layout.addWidget(self.peak_filter_container, stretch=1)

        # Smoothing Group
        self.smoothing_container = QWidget()
        self.smoothing_container.setFixedHeight(70)
        smooth_layout = QVBoxLayout(self.smoothing_container)
        smooth_layout.setContentsMargins(8, 6, 8, 6)
        smooth_layout.setSpacing(4)

        self.smoothing_container.setStyleSheet("""
            QWidget {
                border: 1px solid #888;
                border-radius: 4px;
            }
        """)

        # Smoothing controls (original style)
        smooth_controls_layout = QHBoxLayout()
        smooth_controls_layout.addWidget(QLabel("Smoothing:"))
        self.filter_type = QComboBox()
        self.filter_type.addItems(["None", "SMA", "EMA"])
        self.filter_type.currentIndexChanged.connect(self.update_plot)
        smooth_controls_layout.addWidget(self.filter_type)
        smooth_controls_layout.addWidget(QLabel("Window:"))
        self.filter_window = QSpinBox()
        self.filter_window.setMinimum(1)
        self.filter_window.setMaximum(1000)
        self.filter_window.setValue(5)
        self.filter_window.valueChanged.connect(self.update_plot)
        smooth_controls_layout.addStretch()
        smooth_layout.addLayout(smooth_controls_layout)

        filter_groups_layout.addWidget(self.smoothing_container, stretch=1)

        filter_layout.addLayout(filter_groups_layout)

        # Assign filter to checkboxes
        assign_label = QLabel("Assign filter to:")
        assign_label.setStyleSheet("font-weight: bold; margin-top: 4px;")
        filter_layout.addWidget(assign_label)

        self.filter_y_checkboxes = []
        filter_y_layout = QHBoxLayout()
        filter_y_layout.setSpacing(6)
        for i, col in enumerate(self.y_columns):
            cb = QCheckBox(col)
            cb.setChecked(False)
            cb.stateChanged.connect(self.update_plot)
            filter_y_layout.addWidget(cb)
            self.filter_y_checkboxes.append(cb)
        filter_layout.addLayout(filter_y_layout)

        # Reset filters button
        self.reset_filters_btn = QPushButton("Reset Filters")
        self.reset_filters_btn.setMaximumWidth(120)
        self.reset_filters_btn.clicked.connect(self.reset_filters)
        filter_layout.addWidget(self.reset_filters_btn, alignment=Qt.AlignLeft)

        layout.addWidget(self.filter_container)
        self.toggle_filter_btn.toggled.connect(
            lambda checked: [self.filter_container.setVisible(checked), self.adjust_window_height()]
        )

        # --- Initial plot ---
        self.update_plot()

    # --- Window resize helper ---
    def adjust_window_height(self):
        self.layout().activate()
        w = self.width()
        base_height = 730
        height_offset = 0
        for widget in [self.chart_settings_container, self.toolbar, self.filter_container]:
            if widget.isVisible():
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

        start_time = self.timeline[start_idx]
        end_time = self.timeline[end_idx]

        self.start_label.setText(str(start_time))
        self.end_label.setText(str(end_time))

        self.update_plot()

    def apply_filter(self, series, col):
        data = series.copy()
        if self.spike_cb.isChecked() and col in [cb.text() for cb in self.filter_y_checkboxes if cb.isChecked()]:
            k = self.spike_window.value()
            data = data.rolling(window=k, center=True, min_periods=1).median()
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
