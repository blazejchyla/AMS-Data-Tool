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
        self.toggle_chart_settings_btn.setChecked(True)
        layout.addWidget(self.toggle_chart_settings_btn)

        # --- Chart Settings ---
        self.chart_settings_container = QWidget()
        self.chart_settings_container.setVisible(True)
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
            cb.clicked.connect(self.on_y_checkbox_clicked) # Changed line
            row = i // max_per_row
            col_idx = i % max_per_row
            grid_cb_layout.addWidget(cb, row, col_idx)
            self.y_checkboxes.append(cb)

        outer_cb_layout.addLayout(grid_cb_layout)
        chart_layout.addLayout(outer_cb_layout)
        layout.addWidget(self.chart_settings_container)
        self.toggle_chart_settings_btn.toggled.connect(
            lambda checked: self.toggle_panel(self.chart_settings_container, checked)
        )

        # --- Plot Canvas ---
        self.fig, self.ax_main = plt.subplots(figsize=(10, 4))
        self.ax_twin = None # Add this line to track the second Y-axis
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # --- Toolbar ---
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setVisible(False)
        layout.addWidget(self.toolbar)
        self.toggle_toolbar_btn = QPushButton(T("plot.btn.toggle_plot_toolbox", "Toggle Plot Toolbox"))
        self.toggle_toolbar_btn.setCheckable(True)
        self.toggle_toolbar_btn.toggled.connect(
            lambda checked: self.toggle_panel(self.toolbar, checked)
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
        self.spike_window.setValue(3)
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
        smooth_layout.addWidget(QLabel(T("plot.label.smoothing_window", "Smoothing Window:")), 1, 0, Qt.AlignRight)
        self.filter_window = QSpinBox()
        self.filter_window.setMinimum(1)
        self.filter_window.setMaximum(1000)
        self.filter_window.setValue(5)
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
            lambda checked: self.toggle_panel(self.filter_container, checked)
        )

        # --- Initial plot ---
        self.on_y_checkbox_clicked()
        
        # Set a crisp initial size that perfectly fits the UI
        self.resize(1100, 750)
        
        # Center horizontally, but pin near the top of the screen
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = 40  # 40 pixels from the top edge of the usable screen area
        self.move(x, y)

    def on_y_checkbox_clicked(self):
        checked_cbs = [cb for cb in self.y_checkboxes if cb.isChecked()]
        
        # Enforce the limit
        if len(checked_cbs) > 2:
            sender = self.sender()
            if sender: # Safeguard for when triggered programmatically during __init__
                sender.blockSignals(True)
                sender.setChecked(False)
                sender.blockSignals(False)
                checked_cbs.remove(sender) # Re-adjust list after reverting
            return

        # UX: Gray out unchecked boxes if limit is reached
        limit_reached = (len(checked_cbs) == 2)
        for cb in self.y_checkboxes:
            if limit_reached and not cb.isChecked():
                cb.setEnabled(False)  # Gray out
            else:
                cb.setEnabled(True)   # Keep normal
                
        # FILTER TOOLBOX SYNC: Only show filters for currently selected plots
        for main_cb, filter_cb in zip(self.y_checkboxes, self.filter_y_checkboxes):
            filter_cb.setVisible(main_cb.isChecked())
            
            # Safety cleanup: if a plot is removed, quietly uncheck its filter too
            if not main_cb.isChecked():
                filter_cb.setChecked(False)

        self.update_plot()

    # --- Remaining methods unchanged ---
    def toggle_panel(self, panel, is_visible):
        """Shows/hides a panel and adjusts the window height by the exact panel size to prevent chart squishing."""
        panel.setVisible(is_visible)
        if is_visible:
            self.resize(self.width(), self.height() + panel.height())
        else:
            self.resize(self.width(), self.height() - panel.height())

    def reset_filters(self):
        self.spike_cb.setChecked(False)
        self.spike_window.setValue(3)
        self.filter_type.setCurrentIndex(0)
        self.filter_window.setValue(5)
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
        
        # Ensure twin axis always exists
        if not hasattr(self, 'ax_twin') or self.ax_twin is None:
            self.ax_twin = self.ax_main.twinx()
            
        self.ax_twin.clear()
        
        # FIX: ax.clear() resets the axis to the left side! 
        # We must explicitly force the ticks and label back to the right side.
        self.ax_twin.yaxis.tick_right()
        self.ax_twin.yaxis.set_label_position("right")
        
        # PHANTOM AXIS: Reserve exact space invisibly to prevent the chart from shifting.
        # We use the longest column name to guarantee enough padding is reserved.
        longest_col = max(self.y_columns, key=len) if self.y_columns else "                    "
        self.ax_twin.set_ylabel(longest_col, color='none') 
        self.ax_twin.tick_params(axis='y', labelcolor='none', color='none')

        checked_pairs = [(cb, col) for cb, col in zip(self.y_checkboxes, self.y_columns) if cb.isChecked()]
        
        if not checked_pairs:
            self.canvas.draw()
            return

        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

        # --- PLOT 1 (Left Y-Axis) ---
        cb1, col1 = checked_pairs[0]
        if col1 in [cb.text() for cb in self.filter_y_checkboxes if cb.isChecked()]:
            data1 = self.apply_filter(filtered[col1], col1)
        else:
            data1 = filtered[col1]
        
        line1 = self.ax_main.plot(filtered[self.datetime_col], data1, label=col1, color=colors[0])
        self.ax_main.set_ylabel(col1, color=colors[0], fontweight='bold')
        self.ax_main.tick_params(axis='y', labelcolor=colors[0])

        lines = line1
        labels = [col1]

        # --- PLOT 2 (Right Y-Axis) ---
        if len(checked_pairs) > 1:
            cb2, col2 = checked_pairs[1]
            if col2 in [cb.text() for cb in self.filter_y_checkboxes if cb.isChecked()]:
                data2 = self.apply_filter(filtered[col2], col2)
            else:
                data2 = filtered[col2]
            
            line2 = self.ax_twin.plot(filtered[self.datetime_col], data2, label=col2, color=colors[1])
            self.ax_twin.set_ylabel(col2, color=colors[1], fontweight='bold')
            # Restore the tick colors so they are visible again
            self.ax_twin.tick_params(axis='y', labelcolor=colors[1], color=colors[1]) 
            
            lines += line2
            labels.append(col2)

        # Formatting
        self.ax_main.set_xlabel("")
        self.ax_main.set_title("")
        self.ax_main.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y %H:%M'))
        
        time_span = (end_time - start_time).total_seconds() / 3600
        if time_span > 6:
            self.ax_main.xaxis.set_minor_locator(mdates.HourLocator())
        else:
            self.ax_main.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=range(0, 60, 5)))
            
        # Unified Legend
        self.ax_main.legend(
            lines, labels, 
            loc='lower center', 
            bbox_to_anchor=(0.5, 1.02),
            ncol=len(labels),
            frameon=True
        )
        
        self.ax_main.figure.autofmt_xdate()
        
        # Hardcode the plot margins to lock the drawing area in place.
        # This overrides dynamic resizing, preventing any horizontal shifts.
        self.fig.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.25)
        
        self.canvas.draw()