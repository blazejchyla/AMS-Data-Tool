# main.py
import sys
import os
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QFileDialog, QMessageBox
from modules.core import MainWindow
from modules.i18n import get_localization
from modules.cmtk_converter import convert_cmtk_to_d055

class AppDispatcher(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMS Data Tool - Select Mode")
        self.setFixedSize(400, 200)
        self.result_path = None
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Data Source Type:", alignment=Qt.AlignCenter))
        
        btn_layout = QHBoxLayout()
        self.btn_d055 = QPushButton("AMS Case D055\n(Standard)")
        self.btn_cmtk = QPushButton("AMS Case CMTK\n(Multi-file Conversion)")
        
        # Style buttons to be big
        for btn in [self.btn_d055, self.btn_cmtk]:
            btn.setMinimumHeight(100)
            btn_layout.addWidget(btn)
            
        layout.addLayout(btn_layout)
        
        self.btn_d055.clicked.connect(self.accept) # Just opens main window
        self.btn_cmtk.clicked.connect(self.handle_cmtk)

    def handle_cmtk(self):
        # Quick file selection prompts
        p_path, _ = QFileDialog.getOpenFileName(self, "Select Pressure CSV", "", "CSV (*.csv)")
        if not p_path: return
        f_path, _ = QFileDialog.getOpenFileName(self, "Select Flow CSV", "", "CSV (*.csv)")
        if not f_path: return
        t_path, _ = QFileDialog.getOpenFileName(self, "Select Temperature CSV (Optional)", "", "CSV (*.csv)")
        
        try:
            self.result_path = convert_cmtk_to_d055(p_path, f_path, t_path)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", f"Failed to unify files: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    dispatcher = AppDispatcher()
    if dispatcher.exec() == QDialog.Accepted:
        # Default to English as the selector is removed
        loc = get_localization("en")
        window = MainWindow(loc)
        
        # If conversion happened, auto-trigger the import
        if dispatcher.result_path:
            window.auto_import_file(dispatcher.result_path)
            
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()