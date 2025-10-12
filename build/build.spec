# -*- mode: python ; coding: utf-8 -*-
# build.spec — OneDir build for AMS Data Tool
# Python 3.12 / PySide6 compatible

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
import sys
import os

# ---------------------------------
# Determine PROJECT_ROOT safely
# ---------------------------------
if '__file__' in globals():
    PROJECT_ROOT = Path(__file__).parent.parent.resolve()
else:
    PROJECT_ROOT = Path(os.getcwd()).resolve()

BUILD_DIR = PROJECT_ROOT / "build"  # build folder for dist/work
DIST_DIR = BUILD_DIR / "dist"       # output folder for the executable
MAIN_SCRIPT = PROJECT_ROOT / "main.py"

APP_NAME = "AMS Data Tool"
APP_VERSION = "1.0"
APP_AUTHOR = "Błażej Chyła"
APP_LICENSE = "MIT"
APP_COMPANY = "SMC"
ICON_PATH = PROJECT_ROOT / "resources/icons/app_icon.ico"

# -------------------------
# Collect resources
# -------------------------
pyside6_datas = (
    collect_data_files("PySide6.QtCore") +
    collect_data_files("PySide6.QtGui") +
    collect_data_files("PySide6.QtWidgets") +
    copy_metadata("PySide6")
)

qt_plugins = [
    (str(PROJECT_ROOT / "resources" / "plugins" / "platforms"), "PySide6/plugins/platforms"),
]

app_datas = [
    (str(PROJECT_ROOT / "locales"), "locales"),
    (str(PROJECT_ROOT / "resources"), "resources"),
]

datas = pyside6_datas + qt_plugins + app_datas + copy_metadata("duckdb")

# -------------------------
# Hidden imports and exclusions
# -------------------------
hiddenimports = [
    "numpy",
    "pandas",
    "matplotlib",
]

excluded_modules = [
    "matplotlib.tests",
    "matplotlib.backends._tkagg",
    "matplotlib.backends._gtkagg",
    "mpl_toolkits.tests",
    "numpy.random._examples",
    "numpy.testing",
    "PySide6.scripts.deploy_lib",
    "project_lib",
]

# -------------------------
# PyInstaller build spec
# -------------------------
block_cipher = None

a = Analysis(
    [str(MAIN_SCRIPT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,   # UPX disabled
    console=False,
    icon=str(ICON_PATH),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=False,
    name=APP_NAME,
    distpath=str(DIST_DIR),  # put final dist inside ./build/dist
    workpath=str(BUILD_DIR / "work")  # temporary build files inside ./build/work
)
