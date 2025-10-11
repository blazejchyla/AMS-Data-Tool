# ./main.py
import sys
import locale
from PySide6.QtWidgets import QApplication
from modules import core, i18n
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "locales"

def main():
    # Detect OS language
    lang = locale.getdefaultlocale()[0]
    if not lang:
        lang = "en"
    lang = lang.split("_")[0]  # e.g., 'en_US' → 'en'

    # Initialize localization
    loc = i18n.get_localization(lang=lang)

    # Launch app
    app = QApplication(sys.argv)
    win = core.MainWindow(loc)  # <-- pass loc here
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
