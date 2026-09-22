# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for mf6Voronoi Studio (onedir build).

Build with:  pyinstaller --noconfirm --clean mf6voronoi_studio.spec
"""
import os
from PyInstaller.utils.hooks import collect_all

HERE = os.path.dirname(os.path.abspath(SPEC))

datas = [(os.path.join(HERE, "mf6voronoi.ico"), ".")]
binaries = []
hiddenimports = ["mf6voronoi_bootstrap"]

for pkg in ("mf6Voronoi", "geopandas", "pyproj", "fiona", "rasterio", "shapely", "flopy"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ["mf6voronoi_gui.py"],
    pathex=[HERE],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    excludes=["tkinter", "PySide6", "PyQt6", "vtk", "pyvista", "trame"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="mf6VoronoiStudio",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(HERE, "mf6voronoi.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="mf6VoronoiStudio",
)
