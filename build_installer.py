#!/usr/bin/env python3
"""build_installer.py — build the version-stamped Windows installer (Inno Setup)."""
import os
import sys
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from version import __version__

DIST_APP = os.path.join(HERE, "dist", "mf6VoronoiStudio")


def write_version_iss() -> str:
    path = os.path.join(HERE, "version.iss")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f'#define MyAppVersion "{__version__}"\n')
    print(f"Wrote version.iss  (version {__version__})")
    return path


def find_iscc():
    exe = shutil.which("ISCC") or shutil.which("ISCC.exe")
    if exe:
        return exe
    for base in (os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                 os.environ.get("ProgramFiles", r"C:\Program Files")):
        cand = os.path.join(base, "Inno Setup 6", "ISCC.exe")
        if os.path.exists(cand):
            return cand
    return None


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


def main() -> int:
    force = "--build" in sys.argv
    if not ensure_app(force):
        return 2
    write_version_iss()
    iscc = find_iscc()
    if not iscc:
        print("\nInno Setup compiler (ISCC.exe) was not found.")
        print("Install Inno Setup 6 from https://jrsoftware.org/isdl.php,")
        print("then re-run this script, or compile installer.iss in the IDE.")
        return 3
    print(f"Compiling installer with: {iscc}")
    rc = subprocess.call([iscc, "installer.iss"], cwd=HERE)
    if rc == 0:
        out = os.path.join(HERE, "installer_output",
                           f"mf6VoronoiStudio-{__version__}-Setup.exe")
        print("\nInstaller build complete.")
        print("Installer:", out)
    else:
        print("\nInno Setup compilation failed (exit %d)." % rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
