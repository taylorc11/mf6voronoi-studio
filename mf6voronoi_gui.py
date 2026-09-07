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


def main() -> None:
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
