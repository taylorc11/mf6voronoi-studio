#!/usr/bin/env python3
"""build_exe.py — build the standalone executable (onedir, or --onefile)."""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "mf6voronoi_studio.spec")


def _have_pyinstaller() -> bool:
    try:
        import PyInstaller  # noqa: F401
        return True
    except Exception:
        return False


def build_onedir() -> int:
    return subprocess.call(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", SPEC], cwd=HERE)


def build_onefile() -> int:
    collect = ["mf6Voronoi", "geopandas", "pyproj", "fiona", "rasterio",
               "shapely", "flopy", "matplotlib"]
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile",
           "--windowed", "--name", "mf6VoronoiStudio",
           "--hidden-import", "mf6voronoi_bootstrap"]
    for pkg in collect:
        cmd += ["--collect-all", pkg]
    for mod in ("tkinter", "PySide6", "PyQt6", "vtk", "pyvista", "trame"):
        cmd += ["--exclude-module", mod]
    cmd += ["mf6voronoi_gui.py"]
    return subprocess.call(cmd, cwd=HERE)


def main() -> int:
    if not _have_pyinstaller():
        print("PyInstaller is not installed.  Run:  pip install pyinstaller")
        return 2
    onefile = "--onefile" in sys.argv
    print(f"Building mf6Voronoi Studio ({'onefile' if onefile else 'onedir'})…")
    rc = build_onefile() if onefile else build_onedir()
    if rc == 0:
        out = os.path.join(HERE, "dist", "mf6VoronoiStudio")
        print("\nBuild complete.")
        print("Executable folder:", out)
        if os.name == "nt":
            print("Run:  dist\\mf6VoronoiStudio\\mf6VoronoiStudio.exe")
        else:
            print("Run:  ./dist/mf6VoronoiStudio/mf6VoronoiStudio")
    else:
        print("\nBuild failed (exit %d). See PyInstaller output above." % rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
