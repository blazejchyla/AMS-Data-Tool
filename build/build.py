#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMS Data Tool — Automated Build Script
--------------------------------------

Usage:
    python build.py [--clean] [--onefile] [--noupx]

Options:
    --clean     : Deletes previous build/dist/output folders before building
    --onefile   : Builds a single-file executable
    --noupx     : Skips compression step
"""

import shutil
import subprocess
import sys
from pathlib import Path
import datetime
import zipfile
import re

# ------------------------------------------
# Project Info
# ------------------------------------------
PYTHON_EXE = r"C:\Users\SMClocal\AppData\Local\Programs\Python\Python312\python.exe"
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = BUILD_DIR / "dist"
OUTPUT_DIR = BUILD_DIR / "output"
SPEC_FILE = BUILD_DIR / "build.spec"
MAIN_FILE = PROJECT_ROOT / "main.py"

APP_NAME = "AMS Data Tool"
APP_COMPANY = "SMC"
APP_AUTHOR = "Błażej Chyła"
APP_LICENSE = "MIT"

# ------------------------------------------
# Utilities
# ------------------------------------------
def get_version():
    """Auto-detect version from main.py or core.py"""
    candidates = [MAIN_FILE, PROJECT_ROOT / "modules" / "core.py"]
    version_pattern = re.compile(r'__version__\s*=\s*["\']([^"\']+)["\']')
    for file in candidates:
        if file.exists():
            text = file.read_text(encoding="utf-8")
            match = version_pattern.search(text)
            if match:
                return match.group(1)
    return "1.0.0"

def run(cmd, **kwargs):
    """Run a shell command and print output live."""
    print(f"\n🔧 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, shell=False, **kwargs)
    if result.returncode != 0:
        print(f"\n❌ Build failed with exit code {result.returncode}")
        sys.exit(result.returncode)

def clean():
    """Remove old build, dist, and output directories."""
    print("🧹 Cleaning old build artifacts...")
    for d in [BUILD_DIR / "build", DIST_DIR, OUTPUT_DIR]:
        if d.exists():
            shutil.rmtree(d)
            print(f"  Removed: {d}")
    print("✅ Clean complete.\n")

def copy_to_output(app_name, version, onefile):
    """Copy the built app to a versioned folder and zip it."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    build_type = "onefile" if onefile else "onedir"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    target_dir = OUTPUT_DIR / f"{app_name.replace(' ', '_')}_v{version}_{build_type}_{timestamp}"
    target_dir.mkdir(parents=True, exist_ok=True)

    dist_folder = DIST_DIR / app_name
    if not dist_folder.exists():
        print(f"⚠️  No built app found at {dist_folder}")
        return

    print(f"📦 Copying build to: {target_dir}")
    shutil.copytree(dist_folder, target_dir, dirs_exist_ok=True)

    # Create a ZIP archive for easy distribution
    zip_path = target_dir.with_suffix(".zip")
    print(f"🗜️  Creating ZIP archive: {zip_path}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in target_dir.rglob("*"):
            zipf.write(file_path, file_path.relative_to(target_dir))
    print("✅ Packaging complete.\n")

def main():
    args = sys.argv[1:]
    onefile = "--onefile" in args
    version = get_version()

    if "--clean" in args:
        clean()

    print(f"🚀 Building {APP_NAME} v{version} ({'one-file' if onefile else 'one-dir'}) for {APP_COMPANY} ({APP_LICENSE} License)...")

    cmd = [
        PYTHON_EXE,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR / 'work'}",
        str(SPEC_FILE)
    ]
    if onefile:
        cmd.append("--onefile")

    run(cmd)
    copy_to_output(APP_NAME, version, onefile)
    print("🎉 Build completed successfully!")

# ------------------------------------------
if __name__ == "__main__":
    main()
