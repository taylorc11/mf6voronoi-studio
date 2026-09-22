#!/usr/bin/env python3
"""
mf6Voronoi Studio — a graphical front-end for the ``mf6Voronoi`` package.

Create, edit, refine and export MODFLOW 6 DISV Voronoi meshes.
All mf6Voronoi/geospatial logic lives in ``engine.py``; the UI lives in ``ui/``.

Run:  ``python mf6voronoi_gui.py``
"""
from __future__ import annotations

import os
import sys

from PyQt5 import QtWidgets

from ui import theme
from ui.main_window import MainWindow, app_icon

try:
    from version import __version__ as APP_VERSION
except Exception:
    APP_VERSION = "2.0.0"


def _set_windows_app_id() -> None:
    """Give Windows a stable app identity for this process. Without this,
    Windows may attribute (or silently drop) toast notifications under a
    generic "Python" identity instead of the app's own icon/name."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "HatariLabs.mf6VoronoiStudio")
    except Exception:
        pass


def _selftest() -> int:
    """``mf6VoronoiStudio.exe --selftest``: build a small mesh with the bundled
    libraries and write the outcome to %TEMP%/mf6voronoi_selftest.txt (a
    windowed exe has no console). Exit code 0 = the install works."""
    import tempfile
    import traceback
    out = os.path.join(tempfile.gettempdir(), "mf6voronoi_selftest.txt")
    try:
        import engine
        import geopandas as gpd
        from shapely.geometry import Point, LineString, box
        crs = "EPSG:32631"
        p = engine.MeshProject()
        p.set_crs(crs)
        p.set_limit_from_gdf(gpd.GeoDataFrame({"id": [1]}, geometry=[box(0, 0, 1000, 1000)], crs=crs))
        p.add_layer_from_gdf("w", gpd.GeoDataFrame({"id": [1]}, geometry=[Point(500, 500)], crs=crs), 10.0)
        p.add_layer_from_gdf("l", gpd.GeoDataFrame({"id": [1]}, geometry=[LineString([(3, 50), (3, 950)])], crs=crs), 20.0)
        n = len(p.build_mesh(100.0, 1.3).gdf)
        disv = p.compute_disv()
        assert n > 100 and disv["ncpl"] == n, n
        msg = (f"OK  app {APP_VERSION}  mf6Voronoi {engine.engine_version()}  "
               f"{n} cells  {disv['nvert']} vertices")
        code = 0
    except BaseException:
        msg, code = "FAILED\n" + traceback.format_exc(), 1
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(msg + "\n")
    return code


def main() -> None:
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    _set_windows_app_id()
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("mf6Voronoi Studio")
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(app_icon())
    theme.apply_theme(app)

    win = MainWindow()
    win.show()
    app.aboutToQuit.connect(win._save_settings)

    args = [a for a in app.arguments()[1:] if not a.startswith("-")]
    for a in args:
        if a.lower().endswith((".mf6vor", ".json")) and os.path.exists(a):
            try:
                win.open_project_path(a)
            except Exception:
                pass
            break

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
