# main.py
import sys
import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QPushButton, 
                               QLabel, QHBoxLayout, QFileDialog, QMessageBox, QGridLayout)
from modules.core import MainWindow
from modules.i18n import get_localization
from modules.cmtk_converter import convert_cmtk_to_d055

# =======================================================
# CMTK Importer UI
# =======================================================
class CmtkImporterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CMTK Data Importer")
        self.setFixedSize(500, 320)
        self.result_path = None
        
        # File paths
        self.p_path = None
        self.f_path = None
        self.t_path = None

        layout = QVBoxLayout(self)
        
        # Grid for file selectors
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        # Pressure
        grid.addWidget(QLabel("<b>Pressure Data</b> (Required):"), 0, 0)
        self.btn_p = QPushButton("Browse...")
        self.btn_p.clicked.connect(lambda: self.browse_file('p'))
        grid.addWidget(self.btn_p, 0, 1)
        self.lbl_p = QLabel("No file selected")
        self.lbl_p.setStyleSheet("color: gray; font-style: italic;")
        grid.addWidget(self.lbl_p, 1, 0, 1, 2)

        # Flow
        grid.addWidget(QLabel("<b>Flow Data</b> (Required):"), 2, 0)
        self.btn_f = QPushButton("Browse...")
        self.btn_f.clicked.connect(lambda: self.browse_file('f'))
        grid.addWidget(self.btn_f, 2, 1)
        self.lbl_f = QLabel("No file selected")
        self.lbl_f.setStyleSheet("color: gray; font-style: italic;")
        grid.addWidget(self.lbl_f, 3, 0, 1, 2)

        # Temp
        grid.addWidget(QLabel("<b>Temperature Data</b> (Optional):"), 4, 0)
        self.btn_t = QPushButton("Browse...")
        self.btn_t.clicked.connect(lambda: self.browse_file('t'))
        grid.addWidget(self.btn_t, 4, 1)
        self.lbl_t = QLabel("No file selected")
        self.lbl_t.setStyleSheet("color: gray; font-style: italic;")
        grid.addWidget(self.lbl_t, 5, 0, 1, 2)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        # Action Button
        self.btn_convert = QPushButton("Convert & Import")
        self.btn_convert.setMinimumHeight(45)
        self.btn_convert.setEnabled(False) # Disabled until P and F are selected
        self.btn_convert.clicked.connect(self.process_conversion)
        layout.addWidget(self.btn_convert)

    def browse_file(self, ftype):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if path:
            filename = os.path.basename(path)
            if ftype == 'p':
                self.p_path = path
                self.lbl_p.setText(f"✓ {path}")
                self.lbl_p.setStyleSheet("color: green; font-weight: bold;")
            elif ftype == 'f':
                self.f_path = path
                self.lbl_f.setText(f"✓ {path}")
                self.lbl_f.setStyleSheet("color: green; font-weight: bold;")
            elif ftype == 't':
                self.t_path = path
                self.lbl_t.setText(f"✓ {path}")
                self.lbl_t.setStyleSheet("color: green; font-weight: bold;")
        
        # Unlock convert button only if mandatory files are chosen
        if self.p_path and self.f_path:
            self.btn_convert.setEnabled(True)

    def process_conversion(self):
        # Update UI to show activity
        self.btn_convert.setText("Converting... Please wait")
        self.btn_convert.setEnabled(False)
        QApplication.processEvents() # Force Qt to paint the button update before processing
        
        try:
            self.result_path = convert_cmtk_to_d055(self.p_path, self.f_path, self.t_path)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", f"Failed to unify files: {str(e)}")
            self.btn_convert.setText("Convert & Import")
            self.btn_convert.setEnabled(True)

# =======================================================
# Primary Dispatcher (The Splash Screen)
# =======================================================
class AppDispatcher(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMS Data Tool - Select Mode")
        self.setFixedSize(400, 200)
        self.result_path = None
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Data Source Type:", alignment=Qt.AlignCenter))
        
        btn_layout = QHBoxLayout()
        self.btn_d055 = QPushButton("AMS Case D055\n(Single CSV)")
        self.btn_cmtk = QPushButton("AMS Case CMTK\n(Multi-file CSV Conversion)")
        
        for btn in [self.btn_d055, self.btn_cmtk]:
            btn.setMinimumHeight(100)
            btn_layout.addWidget(btn)
            
        layout.addLayout(btn_layout)
        
        self.btn_d055.clicked.connect(self.accept)
        self.btn_cmtk.clicked.connect(self.handle_cmtk)

    def handle_cmtk(self):
        dlg = CmtkImporterDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.result_path = dlg.result_path
            self.accept()

# =======================================================
# Main Entry Point
# =======================================================
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    
    # --- Apply Global Application Icon ---
    icon_path = get_resource_path(os.path.join("resources", "icons", "app_icon.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    # -------------------------------------
    
    dispatcher = AppDispatcher()
    if dispatcher.exec() == QDialog.Accepted:
        loc = get_localization("en")
        window = MainWindow(loc)
        
        if dispatcher.result_path:
            # CMTK Path: auto-load the converted file silently
            window.auto_import_file(dispatcher.result_path)
        else:
            # D055 Path: Pop open the standard CSV selector
            QTimer.singleShot(100, window.on_import)
            
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()