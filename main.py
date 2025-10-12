# main.py
__version__ = "1.0"
import sys
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox
from modules.core import MainWindow
from modules.i18n import get_localization, L

# =======================================================
# Language Selection Dialog
# =======================================================
class LanguageSelectionDialog(QDialog):
    def __init__(self, available_languages=None):
        super().__init__()
        self.setWindowTitle("Select Language")
        self.resize(300, 100)
        self.selected_language = None

        if available_languages is None:
            available_languages = ["en", "de", "pl", "jp"]

        layout = QVBoxLayout(self)
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(available_languages)
        hlayout.addWidget(self.lang_combo)
        layout.addLayout(hlayout)

        # OK / Cancel buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def on_ok(self):
        self.selected_language = self.lang_combo.currentText()
        self.accept()

# =======================================================
# Application Entry Point
# =======================================================
def main():
    app = QApplication(sys.argv)

    # Prompt user for language
    dlg = LanguageSelectionDialog()
    if dlg.exec() == QDialog.Accepted:
        lang = dlg.selected_language
    else:
        lang = "en"  # fallback

    # Initialize localization globally
    get_localization(lang)

    # Launch main window
    loc = get_localization(lang)
    window = MainWindow(loc)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
