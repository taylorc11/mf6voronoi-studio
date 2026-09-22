"""Headless GUI check: real MainWindow, real worker thread, offscreen Qt.

Run:  python tests/gui_test.py
"""
import os
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5 import QtWidgets

import smoke_test
from ui import theme
from ui.main_window import MainWindow

app = QtWidgets.QApplication([])
theme.apply_theme(app)

# Never block on modal dialogs.
seen = []
QtWidgets.QInputDialog.getText = staticmethod(lambda *a, **k: ("gui_test", True))
QtWidgets.QMessageBox.warning = staticmethod(lambda *a, **k: seen.append(("warn", a[2])))
QtWidgets.QMessageBox.about = staticmethod(lambda *a, **k: seen.append(("about", a[2])))


def pump(cond, timeout=120):
    t = time.time()
    while not cond():
        app.processEvents()
        assert time.time() - t < timeout, "timed out"
        time.sleep(0.02)


win = MainWindow()
win.show()
win.project = smoke_test.make_project(with_void=True)
win.canvas.set_project(win.project)

win.action_build_mesh()
pump(lambda: win.worker is not None and not win.worker.isRunning() and win.project.result)
n = len(win.project.result.gdf)
assert n > 100 and not [s for s in seen if s[0] == "warn"], seen
print("GUI mesh build OK:", n, "cells")

win.action_about()
about = [s for s in seen if s[0] == "about"][0][1]
assert "3.0.1" in about and "0.0.38" in about, about
print("About OK")

with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, "t.mf6vor")
    win.project.save_project(f)
    win.open_project_path(f)
    assert len(win.project.result.gdf) == n
print("Save/open OK")
win._dirty = False
win.close()
print("GUI OK")
