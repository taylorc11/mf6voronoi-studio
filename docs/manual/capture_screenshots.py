#!/usr/bin/env python3
"""Drive mf6Voronoi Studio 2.0.5 with the bundled ``Example`` dataset and
capture the screenshots used by the user manual.

Run with the Python that has the app's dependencies installed:

    py -3.12 docs/manual/capture_screenshots.py

Every image is a real ``QWidget.grab()`` of the live application, so the
manual always matches the shipping UI.
"""
from __future__ import annotations

import json
import os
import sys
import time

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJ)
os.chdir(PROJ)

IMG = os.path.join(PROJ, "docs", "manual", "images")
EX = os.path.join(PROJ, "Example")
os.makedirs(IMG, exist_ok=True)

from PyQt5 import QtCore, QtGui, QtWidgets  # noqa: E402
from PyQt5.QtCore import QPoint  # noqa: E402

from ui import dialogs  # noqa: E402
from ui import theme  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402

FACTS: dict = {}


def pump(ms: int = 260) -> None:
    """Let Qt lay out / paint before we grab a pixmap."""
    end = time.time() + ms / 1000.0
    while time.time() < end:
        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents, 40)
        time.sleep(0.01)


def save(pm: QtGui.QPixmap, name: str) -> None:
    path = os.path.join(IMG, f"{name}.png")
    pm.save(path, "PNG")
    print(f"  [shot] {name}.png  {pm.width()}x{pm.height()}")


def shot(widget: QtWidgets.QWidget, name: str) -> None:
    pump()
    save(widget.grab(), name)


def shot_dialog(dlg: QtWidgets.QDialog, name: str) -> None:
    """Show a dialog non-modally, grab it, close it."""
    dlg.setModal(False)
    dlg.show()
    pump(420)
    save(dlg.grab(), name)
    dlg.close()
    pump(80)


def menu_shot(win: MainWindow, title: str, name: str) -> None:
    """Composite an opened top-level menu onto the main-window pixmap."""
    mb = win.menuBar()
    target = None
    for a in mb.actions():
        if a.text().replace("&", "") == title:
            target = a
            break
    if target is None:
        print(f"  !! menu '{title}' not found")
        return
    menu = target.menu()
    rect = mb.actionGeometry(target)
    menu.popup(mb.mapToGlobal(rect.bottomLeft()))
    pump(420)

    base = win.grab()
    mpm = menu.grab()
    off = win.mapFromGlobal(menu.mapToGlobal(QPoint(0, 0)))
    p = QtGui.QPainter(base)
    # Drop shadow so the menu reads as floating above the window.
    p.fillRect(QtCore.QRect(off + QPoint(6, 6),
                            QtCore.QSize(mpm.width(), mpm.height())),
               QtGui.QColor(0, 0, 0, 110))
    p.drawPixmap(off, mpm)
    p.setPen(QtGui.QPen(QtGui.QColor("#5a6b7c"), 1))
    p.drawRect(QtCore.QRect(off, QtCore.QSize(mpm.width() - 1, mpm.height() - 1)))
    p.end()
    menu.close()
    pump(80)
    save(base, name)


def crop(widget: QtWidgets.QWidget, name: str, pad: int = 8) -> None:
    """Grab a sidebar group box with a little padding around it."""
    if widget is None:
        print(f"  !! widget for {name} not found")
        return
    pump()
    pm = widget.grab()
    if pad:
        out = QtGui.QPixmap(pm.width() + pad * 2, pm.height() + pad * 2)
        out.fill(QtGui.QColor("#12161d"))
        p = QtGui.QPainter(out)
        p.drawPixmap(pad, pad, pm)
        p.end()
        pm = out
    save(pm, name)


def group_box(win: MainWindow, title_startswith: str):
    for gb in win.findChildren(QtWidgets.QGroupBox):
        if gb.title().startswith(title_startswith):
            return gb
    return None


# --------------------------------------------------------------------------- #
def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("mf6Voronoi Studio")
    theme.apply_theme(app)

    win = MainWindow()
    win.resize(1560, 940)
    win.show()
    pump(900)

    print("== empty application ==")
    shot(win, "01_main_empty")
    crop(group_box(win, "Coordinate system"), "02_panel_crs_empty")

    # ---------------------------------------------------------------- CRS --
    print("== CRS dialog ==")
    dlg = dialogs.CrsDialog(win, None)
    dlg.edit.setText("32631")
    dlg.show()
    pump(300)
    for probe in ("_validate", "_check", "_on_text"):
        fn = getattr(dlg, probe, None)
        if callable(fn):
            try:
                fn()
                break
            except Exception:
                pass
    pump(400)
    save(dlg.grab(), "03_dialog_crs")
    dlg.close()

    win.project.set_crs("EPSG:32631")
    win._update_crs_label()
    pump()
    crop(group_box(win, "Coordinate system"), "04_panel_crs_set")
    FACTS["crs_summary"] = win.project.crs_summary()
    print("   CRS:", FACTS["crs_summary"])

    # -------------------------------------------------------------- limit --
    print("== import model limit ==")
    win.project.load_limit_shapefile(os.path.join(EX, "modelLimit.shp"))
    win.log_msg("Imported limit polygon from modelLimit.shp.")
    win.log_msg("Detected CRS from the shapefile's .prj file: "
                + win.project.crs_summary())
    win.canvas.sync_limit()
    win.canvas.zoom_to_data()
    pump(400)
    shot(win, "05_limit_imported")

    b = win.project.limit_gdf.total_bounds
    FACTS["limit_bounds"] = [round(float(v), 1) for v in b]
    FACTS["limit_width"] = round(float(b[2] - b[0]), 1)
    FACTS["limit_height"] = round(float(b[3] - b[1]), 1)
    FACTS["limit_area"] = round(float(win.project.limit_gdf.area.iloc[0]), 1)

    # -------------------------------------------------- refinement dialog --
    print("== refinement-size dialog ==")
    d = dialogs.LayerRefDialog(win, "Refinement size", "modelGhb", unit="m")
    d.ref.setValue(10.0)
    shot_dialog(d, "06_dialog_refinement_size")

    # -------------------------------------------------- refinement layers --
    print("== import refinement layers ==")
    plan = [
        ("modelGhb.shp", "modelGhb", 10.0),
        ("site.shp", "site", 4.0),
        ("hfb.shp", "hfb", 3.0),
        ("drains.shp", "drains", 2.0),
        ("pointWell.shp", "pointWell", 1.0),
    ]
    layer_facts = []
    for fn, name, ref in plan:
        lyr = win.project.load_layer_shapefile(os.path.join(EX, fn), ref, name)
        win.log_msg(f"Imported refinement layer '{name}' (cell size {ref:g} m).")
        layer_facts.append({
            "file": fn, "name": name, "ref": ref,
            "geom": lyr.geom_type, "features": lyr.feature_count,
            "color": lyr.color,
        })
        print(f"   {name:10s} {lyr.geom_type:12s} n={lyr.feature_count} ref={ref}")
    FACTS["layers"] = layer_facts

    win._refresh_layer_list()
    win.canvas.sync_layers()
    win.canvas.zoom_to_data()
    pump(500)
    shot(win, "07_layers_loaded")
    crop(group_box(win, "Refinement layers"), "08_panel_layers")
    crop(group_box(win, "Void polygons"), "09_panel_voids")

    # ------------------------------------------------------------ options --
    print("== mesh options ==")
    win.opt_maxref.setValue(20.0)
    win.opt_mult.setValue(1.3)
    win.opt_overlap.setChecked(True)
    win.opt_quality.setValue(0.2)
    win._sync_mesh_params()
    pump()
    crop(group_box(win, "Voronoi refinement options"), "10_panel_options")
    FACTS["mesh_params"] = dict(win.project.mesh_params)

    # -------------------------------------------------------------- menus --
    print("== menus & toolbar ==")
    menu_shot(win, "File", "11_menu_file")
    menu_shot(win, "Draw", "12_menu_draw")
    menu_shot(win, "View", "13_menu_view")
    menu_shot(win, "Help", "14_menu_help")

    tb = win.findChild(QtWidgets.QToolBar, "MainToolBar")
    if tb is not None:
        pump()
        pm = tb.grab()
        # The toolbar stretches the full window width; keep only the part
        # that actually holds buttons.
        dpr = pm.width() / max(tb.width(), 1)
        used = 0
        for a in tb.actions():
            w = tb.widgetForAction(a)
            if w is not None:
                used = max(used, w.geometry().right())
        used = int((used + 10) * dpr) if used else pm.width()
        save(pm.copy(0, 0, min(used, pm.width()), pm.height()), "15_toolbar")

    # ------------------------------------------------------ mesh name box --
    inp = QtWidgets.QInputDialog(win)
    inp.setWindowTitle("Generate Voronoi mesh")
    inp.setLabelText("Mesh name:")
    inp.setTextValue("voronoiModel")
    inp.setMinimumWidth(360)
    shot_dialog(inp, "16_dialog_mesh_name")

    # ------------------------------------------------------- generate mesh --
    print("== generating mesh (this takes a while) ==")
    win.project.mesh_name = "voronoiModel"
    mp = win.project.mesh_params
    win.log_msg("\n=== Generating Voronoi mesh ===")
    win.log_msg(f"  coarse={mp['max_ref']:g}, multiplier={mp['multiplier']:g}, "
                f"overlapping={mp['overlapping']}, "
                f"fix-short-edges={mp['quality']:g}")
    t0 = time.time()
    res = win.project.build_mesh(
        max_ref=mp["max_ref"], multiplier=mp["multiplier"],
        overlapping=mp["overlapping"], quality_threshold=mp["quality"],
        log_cb=win.log_msg)
    dt = time.time() - t0
    ncell = len(res.gdf)
    FACTS["mesh_seconds"] = round(dt, 1)
    FACTS["ncell"] = ncell
    print(f"   mesh: {ncell} cells in {dt:.1f}s")

    win.mesh_info.setText(f"{ncell} cells generated.")
    win.log_msg(f"Mesh ready: {ncell} cells.")
    win.canvas.sync_mesh()
    win.action_quality_report(silent=True)
    pump(600)
    shot(win, "17_mesh_generated")
    crop(group_box(win, "Mesh"), "18_panel_mesh")
    rep_gb = group_box(win, "Cell-count")
    win.report_table.resizeRowsToContents()
    rows_h = sum(win.report_table.rowHeight(r)
                 for r in range(win.report_table.rowCount()))
    win.report_table.setMinimumHeight(
        rows_h + win.report_table.horizontalHeader().height() + 8)
    pump(200)
    crop(rep_gb, "19_panel_report")
    win.report_table.setMinimumHeight(210)
    crop(group_box(win, "Log"), "20_panel_log")
    FACTS["report"] = {k: (round(v, 4) if isinstance(v, float) else v)
                       for k, v in (win._last_report or {}).items()}

    # canvas only: full extent, then zoomed on the refined site
    save(win.canvas.grab(), "21_canvas_full")
    for _ in range(6):
        win.canvas.zoom_in()
    pump(500)
    save(win.canvas.grab(), "22_canvas_zoom_site")
    win.canvas.zoom_to_data()
    pump(300)

    # mesh-finished popup
    summary = win._quality_summary_text()
    box = QtWidgets.QMessageBox(win)
    box.setIcon(QtWidgets.QMessageBox.Information)
    box.setWindowTitle("Mesh generated")
    box.setText(f"The mesh has been created: {ncell:,} cells."
                + (f"\n\n{summary}" if summary else ""))
    box.setStandardButtons(QtWidgets.QMessageBox.Ok)
    shot_dialog(box, "23_popup_mesh_done")

    # ------------------------------------------------------------ exports --
    print("== export dialogs ==")
    d = dialogs.LayerElevationDialog(win, win.project.layers[1])
    d.top.edit.setText(os.path.join(EX, "modelTop.tif"))
    d.botm.edit.setText(os.path.join(EX, "bottomLy1.tif"))
    shot_dialog(d, "24_dialog_layer_rasters")

    d = dialogs.ModelMuseDialog(win, win.project)
    d.nlay.setValue(4)
    d.top_field.edit.setText(os.path.join(EX, "modelTop.tif"))
    for i, f in enumerate(d._fields):
        f.edit.setText(os.path.join(EX, f"bottomLy{i + 1}.tif"))
    shot_dialog(d, "25_dialog_modelmuse")

    d = dialogs.ExtentDialog(win)
    d.xmin.setValue(592557); d.xmax.setValue(593159)
    d.ymin.setValue(5762320); d.ymax.setValue(5762910)
    shot_dialog(d, "26_dialog_image_extent")

    # -------------------------------------------------- online imagery --
    print("== online satellite imagery (live network) ==")
    from ui.online_imagery import PROVIDERS as _IMAGERY_PROVIDERS
    bg_dlg = dialogs.AddBackgroundDialog(win, win)
    bg_dlg.setModal(False)
    bg_dlg.resize(940, 720)
    tabs = bg_dlg.findChild(QtWidgets.QTabWidget)
    tabs.setCurrentIndex(1)  # "Online satellite map"
    panel = bg_dlg.online_panel
    bg_dlg.show()
    panel._fit_to_project()  # centres on the tutorial's real model extent
    pump(4000)  # let real tiles download over the network
    panel.map.update()
    pump(1500)
    save(bg_dlg.grab(), "30_dialog_online_imagery")
    FACTS["online_imagery_providers"] = list(_IMAGERY_PROVIDERS.keys())
    FACTS["online_imagery_info_label"] = panel.info_label.text()
    print("   info label:", FACTS["online_imagery_info_label"])
    bg_dlg.close()
    pump(80)

    # About — QMessageBox.about() is modal, so grab it from inside its own
    # event loop via a timer, then dismiss it.
    print("== about ==")

    def _grab_about():
        for w in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(w, QtWidgets.QMessageBox) and w.isVisible() \
                    and w.windowTitle().startswith("About"):
                save(w.grab(), "27_dialog_about")
                FACTS["about_text"] = w.text()
                w.done(0)
                return
        print("  !! About dialog not found")

    QtCore.QTimer.singleShot(700, _grab_about)
    win.action_about()
    pump(200)

    # ------------------------------------------------ real export outputs --
    print("== running real exports ==")
    out = os.path.join(PROJ, "docs", "manual", "_example_output")
    os.makedirs(out, exist_ok=True)
    win.project.export_shapefile(os.path.join(out, "voronoiModel_voronoi.shp"))
    disv = win.project.compute_disv()
    win.project.export_disv_json(os.path.join(out, "voronoiModel_disv.json"))
    FACTS["disv_keys"] = sorted(disv.keys())
    FACTS["disv_ncpl"] = disv.get("ncpl")
    FACTS["disv_nvert"] = disv.get("nvert")

    mm = os.path.join(out, "modelmuse")
    os.makedirs(mm, exist_ok=True)
    try:
        win.project.export_modelmuse(
            mm, nlay=4,
            top=os.path.join(EX, "modelTop.tif"),
            botm=[os.path.join(EX, f"bottomLy{i}.tif") for i in range(1, 5)],
            mf6_exe="mf6", log_cb=win.log_msg)
        FACTS["modelmuse_files"] = sorted(os.listdir(mm))
        print("   modelmuse files:", FACTS["modelmuse_files"])
    except Exception as e:
        FACTS["modelmuse_error"] = f"{type(e).__name__}: {e}"
        print("   !! modelmuse export failed:", e)

    # Save a project file so the manual can quote a real .mf6vor size.
    proj_file = os.path.join(out, "example.mf6vor")
    try:
        win.project.save_project(proj_file)
        FACTS["mf6vor_bytes"] = os.path.getsize(proj_file)
    except Exception as e:
        FACTS["mf6vor_error"] = f"{type(e).__name__}: {e}"

    win.action_quality_report(silent=True)
    pump(300)
    shot(win, "28_main_final")

    sa = win.findChild(QtWidgets.QScrollArea)
    if sa is not None:
        sa.verticalScrollBar().setValue(sa.verticalScrollBar().maximum())
        pump(400)
        shot(win, "29_main_sidebar_scrolled")

    with open(os.path.join(PROJ, "docs", "manual", "capture_facts.json"),
              "w", encoding="utf-8") as fh:
        json.dump(FACTS, fh, indent=2, default=str)
    print("\nDone. Facts written to docs/manual/capture_facts.json")

    win.close()
    app.quit()
    # Qt can stall on interpreter shutdown once every dialog has been
    # grabbed and closed; everything is already written to disk by here.
    os._exit(0)


if __name__ == "__main__":
    main()
