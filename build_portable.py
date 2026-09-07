#!/usr/bin/env python3
"""build_portable.py — build a portable, no-install ZIP of mf6Voronoi Studio."""
import os
import sys
import shutil
import platform
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from version import __version__, APP_NAME, APP_ID

DIST_APP = os.path.join(HERE, "dist", APP_ID)
STAGE_ROOT = os.path.join(HERE, "portable_build")
OUT_DIR = os.path.join(HERE, "portable_output")
EXE_NAME = APP_ID + (".exe" if os.name == "nt" else "")


def ensure_app(force: bool) -> bool:
    if force or not os.path.isdir(DIST_APP):
        print("Building the application with PyInstaller…")
        if subprocess.call([sys.executable, "build_exe.py"], cwd=HERE) != 0:
            print("PyInstaller build failed.")
            return False
    if not os.path.isdir(DIST_APP):
        print(f"Expected app folder not found: {DIST_APP}")
        return False
    return True


def _os_tag() -> str:
    system = platform.system().lower()
    return {"windows": "win64", "darwin": "macos", "linux": "linux"}.get(
        system, system or "unknown")


def _launcher_bat() -> str:
    return ("@echo off\r\n"
            "REM Launch mf6Voronoi Studio (portable). Settings are kept in\r\n"
            "REM mf6VoronoiStudio.ini next to this launcher.\r\n"
            "cd /d \"%~dp0\"\r\n"
            f"start \"\" \"app\\{EXE_NAME}\"\r\n")


def _launcher_sh() -> str:
    return ("#!/bin/bash\n"
            "# Launch mf6Voronoi Studio (portable).\n"
            'cd "$(dirname "$0")"\n'
            f'exec "./app/{APP_ID}" "$@"\n')


def _readme() -> str:
    return f"""{APP_NAME} {__version__} — Portable edition
{'=' * 48}

This is a PORTABLE build. Nothing is installed and nothing is written to your
user profile or the Windows registry.

How to run
----------
  * Windows : double-click  "Run {APP_NAME}.bat"
              (or open the  app\\  folder and run {EXE_NAME})
  * Linux   : ./Run-mf6VoronoiStudio.sh   (needs libGL: sudo apt install libgl1)

Settings live in  mf6VoronoiStudio.ini  next to the launcher. Delete it to
reset. Copy this whole folder to a USB stick to take it with you.

Example shapefiles are in  sample_data\\ . See README.md for full docs.
"""


def stage() -> str:
    name = f"{APP_ID}-{__version__}-portable"
    stage_dir = os.path.join(STAGE_ROOT, name)
    if os.path.isdir(stage_dir):
        shutil.rmtree(stage_dir)
    os.makedirs(stage_dir, exist_ok=True)

    app_dst = os.path.join(stage_dir, "app")
    print("Copying application files…")
    shutil.copytree(DIST_APP, app_dst)

    with open(os.path.join(app_dst, "portable.txt"), "w") as fh:
        fh.write("This file marks a portable install. Settings are kept next "
                 "to the executable.\n")

    with open(os.path.join(stage_dir, f"Run {APP_NAME}.bat"), "w",
              newline="") as fh:
        fh.write(_launcher_bat())
    sh = os.path.join(stage_dir, "Run-mf6VoronoiStudio.sh")
    with open(sh, "w", newline="\n") as fh:
        fh.write(_launcher_sh())
    try:
        os.chmod(sh, 0o755)
    except Exception:
        pass

    sample_src = os.path.join(HERE, "sample_data")
    if os.path.isdir(sample_src):
        shutil.copytree(sample_src, os.path.join(stage_dir, "sample_data"))
    for doc in ("README.md", "LICENSE.txt"):
        src = os.path.join(HERE, doc)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(stage_dir, doc))
    with open(os.path.join(stage_dir, "README-PORTABLE.txt"), "w") as fh:
        fh.write(_readme())
    return stage_dir


def zip_it(stage_dir: str) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    base = f"{APP_ID}-{__version__}-portable-{_os_tag()}"
    print("Compressing ZIP (this can take a minute)…")
    return shutil.make_archive(
        base_name=os.path.join(OUT_DIR, base), format="zip",
        root_dir=os.path.dirname(stage_dir),
        base_dir=os.path.basename(stage_dir))


def main() -> int:
    force = "--build" in sys.argv
    if not ensure_app(force):
        return 2
    stage_dir = stage()
    zip_path = zip_it(stage_dir)
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print("\nPortable build complete.")
    print(f"Folder : {stage_dir}")
    print(f"ZIP    : {zip_path}  ({size_mb:.1f} MB)")
    print("\nUnzip anywhere and run the launcher — no installation needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
