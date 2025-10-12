# hooks/hook_qt_plugins.py
import os
from pathlib import Path
from PySide6 import QtCore

# Only run if PySide6 is imported
try:
    # Find the folder where PySide6 plugins are bundled by PyInstaller
    base_path = Path(os.path.dirname(__file__)).parent  # adjust if needed
    plugins_path = base_path / "PySide6" / "plugins"

    if plugins_path.exists():
        QtCore.QCoreApplication.setLibraryPaths([str(plugins_path)])
except Exception as e:
    print(f"[hook_qt_plugins] Error setting QT_PLUGIN_PATH: {e}")