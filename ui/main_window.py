"""
main_window.py
==============
The application window: menus, toolbar, side panel, and all the wiring
between the map canvas (ui.canvas.MapView) and the engine (engine.MeshProject).
"""
from __future__ import annotations

import os
import sys
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal

import pandas as pd
import geopandas as gpd

import engine
from .canvas import MapView, Mode
from .dialogs import (LayerRefDialog, ModelMuseDialog, LayerElevationDialog,
                      CrsDialog, ExtentDialog, AddBackgroundDialog)
from . import theme

try:
    from version import __version__ as APP_VERSION
except Exception:
    APP_VERSION = "2.0.0"


def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_portable() -> bool:
    return os.path.exists(os.path.join(_app_dir(), "portable.txt"))


def settings_path() -> str:
    return os.path.join(_app_dir(), "mf6VoronoiStudio.ini")


def make_settings() -> "QtCore.QSettings":
    if is_portable():
        return QtCore.QSettings(settings_path(), QtCore.QSettings.IniFormat)
    return QtCore.QSettings("mf6Voronoi Studio", "mf6VoronoiStudio")


def app_icon() -> "QtGui.QIcon":
    candidates = [os.path.join(_app_dir(), "mf6voronoi.ico")]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "mf6voronoi.ico"))
    for c in candidates:
        if os.path.exists(c):
            return QtGui.QIcon(c)
    return QtGui.QIcon()


# =========================================================================== #
class MeshWorker(QThread):
    log = pyqtSignal(str)
    finished_ok = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, project, params):
        super().__init__()
        self.project = project
        self.params = params

    def run(self):
        try:
            res = self.project.build_mesh(
                max_ref=self.params["max_ref"],
                multiplier=self.params["multiplier"],
                overlapping=self.params["overlapping"],
                quality_threshold=self.params["quality"],
                log_cb=self.log.emit,
            )
            self.finished_ok.emit(res)
        except Exception:
            self.failed.emit(traceback.format_exc())


# =========================================================================== #
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(app_icon())
        self.resize(1360, 860)
        self.project = engine.MeshProject()
        self.settings = make_settings()
        self._last_dir = ""
        self._pending_layer: engine.RefinementLayer | None = None
        self._pending_void_name: str | None = None
        self.worker: MeshWorker | None = None
        self._last_report = None
        self._current_project_path: str | None = None
        self._dirty = False
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_tray_icon()
        self._update_title()
        self._update_crs_label()
        self._refresh_layer_list()
        self._refresh_void_list()
        self._refresh_background_list()
        self._update_layer_buttons()
        self._restore_settings()

    # ------------------------------------------------------------------ #
    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QHBoxLayout(central)

        self.canvas = MapView(self.project, self)
        self.canvas.geometry_finished.connect(self._on_geometry_drawn)
        self.canvas.status_message.connect(self.statusBar().showMessage)
        self.canvas.remove_background_requested.connect(self._remove_background_by_ref)
        self.canvas.finish_layer_requested.connect(self._finish_pending_layer)
        self.canvas.cancel_layer_requested.connect(self._cancel_pending_layer)
        root.addWidget(self.canvas, 3)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(340)
        panel = QtWidgets.QWidget()
        right = QtWidgets.QVBoxLayout(panel)
        scroll.setWidget(panel)

        crs_box = QtWidgets.QGroupBox("Coordinate system (CRS)")
        crs_l = QtWidgets.QVBoxLayout(crs_box)
        self.crs_label = QtWidgets.QLabel("No CRS set")
        self.crs_label.setWordWrap(True)
        crs_btn = QtWidgets.QPushButton("Set / change CRS…")
        crs_btn.clicked.connect(self.action_set_crs)
        crs_hint = QtWidgets.QLabel(
            "⚠ Every shapefile you import must use this exact coordinate "
            "system. A CRS is detected automatically from a shapefile's "
            ".prj file when one is present.")
        crs_hint.setWordWrap(True)
        crs_hint.setStyleSheet("color:#94a0b3; font-weight: normal;")
        crs_l.addWidget(self.crs_label)
        crs_l.addWidget(crs_btn)
        crs_l.addWidget(crs_hint)
        right.addWidget(crs_box)

        bg_box = QtWidgets.QGroupBox("Background images")
        bg_l = QtWidgets.QVBoxLayout(bg_box)
        self.bg_list = QtWidgets.QListWidget()
        self.bg_list.setMinimumHeight(80)
        self.bg_list.itemChanged.connect(self._on_background_item_changed)
        self.bg_list.currentRowChanged.connect(self._update_background_buttons)
        bg_l.addWidget(self.bg_list)
        bg_row = QtWidgets.QHBoxLayout()
        btn_bg_import = QtWidgets.QPushButton("Add…")
        btn_bg_import.setToolTip("Add a background image from a local file or "
                                 "an online satellite map.")
        btn_bg_import.clicked.connect(self.action_import_background)
        self.btn_bg_remove = QtWidgets.QPushButton("Remove")
        self.btn_bg_remove.setObjectName("DangerButton")
        self.btn_bg_remove.clicked.connect(self.action_remove_background)
        bg_row.addWidget(btn_bg_import)
        bg_row.addWidget(self.btn_bg_remove)
        bg_l.addLayout(bg_row)
        right.addWidget(bg_box)

        lyr_box = QtWidgets.QGroupBox("Refinement layers")
        lyr_l = QtWidgets.QVBoxLayout(lyr_box)
        self.layer_list = QtWidgets.QListWidget()
        self.layer_list.setMinimumHeight(120)
        self.layer_list.itemChanged.connect(self._on_layer_item_changed)
        self.layer_list.currentRowChanged.connect(self._update_layer_buttons)
        lyr_l.addWidget(self.layer_list)
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_edit_ref = QtWidgets.QPushButton("Edit size…")
        self.btn_edit_ref.clicked.connect(self.action_edit_ref)
        self.btn_del_layer = QtWidgets.QPushButton("Delete")
        self.btn_del_layer.clicked.connect(self.action_delete_layer)
        btn_row.addWidget(self.btn_edit_ref)
        btn_row.addWidget(self.btn_del_layer)
        lyr_l.addLayout(btn_row)
        self.btn_layer_elev = QtWidgets.QPushButton("Layer top/botm rasters…")
        self.btn_layer_elev.clicked.connect(self.action_layer_elevations)
        lyr_l.addWidget(self.btn_layer_elev)
        right.addWidget(lyr_box)

        void_box = QtWidgets.QGroupBox("Void polygons (no mesh generated inside)")
        void_l = QtWidgets.QVBoxLayout(void_box)
        self.void_list = QtWidgets.QListWidget()
        self.void_list.setMinimumHeight(80)
        self.void_list.itemChanged.connect(self._on_void_item_changed)
        self.void_list.currentRowChanged.connect(self._update_void_buttons)
        void_l.addWidget(self.void_list)
        void_btn_row = QtWidgets.QHBoxLayout()
        btn_draw_void = QtWidgets.QPushButton("Draw void…")
        btn_draw_void.clicked.connect(lambda: self._start_draw_void())
        btn_import_void = QtWidgets.QPushButton("Import…")
        btn_import_void.clicked.connect(self.action_import_void)
        self.btn_del_void = QtWidgets.QPushButton("Delete")
        self.btn_del_void.clicked.connect(self.action_delete_void)
        void_btn_row.addWidget(btn_draw_void)
        void_btn_row.addWidget(btn_import_void)
        void_btn_row.addWidget(self.btn_del_void)
        void_l.addLayout(void_btn_row)
        right.addWidget(void_box)

        opt_box = QtWidgets.QGroupBox("Voronoi refinement options")
        opt_form = QtWidgets.QFormLayout(opt_box)
        mp = self.project.mesh_params
        self.opt_maxref = QtWidgets.QDoubleSpinBox()
        self.opt_maxref.setRange(0.1, 1e9); self.opt_maxref.setDecimals(2)
        self.opt_maxref.setValue(mp["max_ref"])
        self.opt_maxref.setToolTip("Coarse (maximum) cell size away from refinements.")
        self.opt_mult = QtWidgets.QDoubleSpinBox()
        self.opt_mult.setRange(1.0, 10.0); self.opt_mult.setSingleStep(0.1)
        self.opt_mult.setDecimals(2); self.opt_mult.setValue(mp["multiplier"])
        self.opt_mult.setToolTip("Progressive growth multiplier between refinement rings.")
        self.opt_overlap = QtWidgets.QCheckBox("Allow overlapping refinement")
        self.opt_overlap.setChecked(mp["overlapping"])
        self.opt_quality = QtWidgets.QDoubleSpinBox()
        self.opt_quality.setRange(0.0, 1e6); self.opt_quality.setDecimals(3)
        self.opt_quality.setValue(mp["quality"])
        self.opt_quality.setToolTip("Fix Voronoi edges shorter than this length "
                                    "(0 = disabled).")
        self.opt_maxref.valueChanged.connect(self._on_mesh_option_changed)
        self.opt_mult.valueChanged.connect(self._on_mesh_option_changed)
        self.opt_overlap.toggled.connect(self._on_mesh_option_changed)
        self.opt_quality.valueChanged.connect(self._on_mesh_option_changed)
        opt_form.addRow("Coarse (max) cell size:", self.opt_maxref)
        opt_form.addRow("Refinement multiplier:", self.opt_mult)
        opt_form.addRow("", self.opt_overlap)
        opt_form.addRow("Fix short edges below:", self.opt_quality)
        right.addWidget(opt_box)

        mesh_box = QtWidgets.QGroupBox("Mesh")
        mesh_l = QtWidgets.QVBoxLayout(mesh_box)
        self.btn_build = QtWidgets.QPushButton("⚙  Generate Voronoi mesh")
        self.btn_build.clicked.connect(self.action_build_mesh)
        self.mesh_info = QtWidgets.QLabel("No mesh generated.")
        self.chk_mesh_visible = QtWidgets.QCheckBox("Show generated mesh")
        self.chk_mesh_visible.setChecked(True)
        self.chk_mesh_visible.toggled.connect(self.canvas.set_mesh_visible)
        mesh_l.addWidget(self.btn_build)
        mesh_l.addWidget(self.mesh_info)
        mesh_l.addWidget(self.chk_mesh_visible)
        right.addWidget(mesh_box)

        rep_box = QtWidgets.QGroupBox("Cell-count / quality report")
        rep_l = QtWidgets.QVBoxLayout(rep_box)
        self.report_table = QtWidgets.QTableWidget(0, 2)
        self.report_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.report_table.horizontalHeader().setStretchLastSection(True)
        self.report_table.verticalHeader().setVisible(False)
        self.report_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.report_table.setMinimumHeight(210)
        rep_l.addWidget(self.report_table)
        rep_btn_row = QtWidgets.QHBoxLayout()
        self.btn_report = QtWidgets.QPushButton("Compute report")
        self.btn_report.clicked.connect(self.action_quality_report)
        self.btn_report_export = QtWidgets.QPushButton("Save report…")
        self.btn_report_export.clicked.connect(self.action_export_report)
        rep_btn_row.addWidget(self.btn_report)
        rep_btn_row.addWidget(self.btn_report_export)
        rep_l.addLayout(rep_btn_row)
        right.addWidget(rep_box)

        log_box = QtWidgets.QGroupBox("Log")
        log_l = QtWidgets.QVBoxLayout(log_box)
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(120)
        self.log.setMaximumBlockCount(5000)
        log_l.addWidget(self.log)
        right.addWidget(log_box)

        right.addStretch(1)
        root.addWidget(scroll, 1)

    def _build_menu(self):
        mb = self.menuBar()
        m_file = mb.addMenu("&File")
        self._add(m_file, "New project", self.action_new_project, "Ctrl+N")
        self._add(m_file, "Open project…", self.action_open_project, "Ctrl+O")
        self._add(m_file, "Save project", self.action_save_project, "Ctrl+S")
        self._add(m_file, "Save project as…", self.action_save_project_as, "Ctrl+Shift+S")
        m_file.addSeparator()
        self._add(m_file, "Import limit polygon…", self.action_import_limit)
        self._add(m_file, "Import refinement shapefile…", self.action_import_layer)
        self._add(m_file, "Add background image (file or online map)…",
                  self.action_import_background)
        self._add(m_file, "Remove background image", self.action_remove_background)
        self._add(m_file, "Import void polygon shapefile…", self.action_import_void)
        m_file.addSeparator()
        self._add(m_file, "Export mesh shapefile…", self.action_export_shp)
        self._add(m_file, "Export DISV properties (JSON)…", self.action_export_json)
        self._add(m_file, "Export quality report…", self.action_export_report)
        self._add(m_file, "Export ModelMuse MODFLOW 6 model…",
                  self.action_export_modelmuse)
        m_file.addSeparator()
        self._add(m_file, "Quit", self.close)

        m_draw = mb.addMenu("&Draw")
        self._add(m_draw, "Navigate (pan/zoom)", lambda: self._set_mode(Mode.NAVIGATE))
        m_draw.addSeparator()
        self._add(m_draw, "Draw limit polygon", lambda: self._set_mode(Mode.LIMIT))
        self._add(m_draw, "New point refinement layer…",
                  lambda: self._start_draw_layer(Mode.POINT))
        self._add(m_draw, "New polyline refinement layer…",
                  lambda: self._start_draw_layer(Mode.LINE))
        self._add(m_draw, "New polygon refinement layer…",
                  lambda: self._start_draw_layer(Mode.POLYGON))
        self._add(m_draw, "New void polygon…", lambda: self._start_draw_void())
        m_draw.addSeparator()
        self._add(m_draw, "Finish current layer", self._finish_pending_layer)
        self._add(m_draw, "Cancel current layer", self._cancel_pending_layer)

        m_view = mb.addMenu("&View")
        self._add(m_view, "Zoom to data", self.canvas.zoom_to_data)
        self._add(m_view, "Zoom in", self.canvas.zoom_in)
        self._add(m_view, "Zoom out", self.canvas.zoom_out)
        m_view.addSeparator()
        self._add(m_view, "Measure distance", lambda: self._set_mode(Mode.MEASURE))

        m_help = mb.addMenu("&Help")
        self._add(m_help, "About", self.action_about)

    def _build_toolbar(self):
        tb = self.addToolBar("Tools")
        tb.setObjectName("MainToolBar")
        tb.setIconSize(QSize(18, 18))

        def act(kind, text, slot, checkable=False):
            a = QtWidgets.QAction(theme.make_icon(kind), text, self)
            a.triggered.connect(slot)
            a.setCheckable(checkable)
            tb.addAction(a)
            return a

        self.act_nav = act("navigate", "Navigate", lambda: self._set_mode(Mode.NAVIGATE), True)
        tb.addSeparator()
        self.act_limit = act("limit", "Limit", lambda: self._set_mode(Mode.LIMIT), True)
        self.act_point = act("point", "+Points", lambda: self._start_draw_layer(Mode.POINT), True)
        self.act_line = act("line", "+Lines", lambda: self._start_draw_layer(Mode.LINE), True)
        self.act_poly = act("polygon", "+Polygons", lambda: self._start_draw_layer(Mode.POLYGON), True)
        self.act_void = act("void", "+Void", lambda: self._start_draw_void(), True)
        self.act_measure = act("measure", "Measure", lambda: self._set_mode(Mode.MEASURE), True)
        tb.addSeparator()
        act("finish", "Finish layer", self._finish_pending_layer)
        act("trash", "Cancel layer", self._cancel_pending_layer)
        tb.addSeparator()
        act("generate", "Generate mesh", self.action_build_mesh)
        tb.addSeparator()
        act("zoom-in", "Zoom in", self.canvas.zoom_in)
        act("zoom-out", "Zoom out", self.canvas.zoom_out)
        act("fit", "Fit to data", self.canvas.zoom_to_data)

        self._mode_actions = {
            Mode.NAVIGATE: self.act_nav, Mode.LIMIT: self.act_limit,
            Mode.POINT: self.act_point, Mode.LINE: self.act_line,
            Mode.POLYGON: self.act_poly, Mode.VOID: self.act_void,
            Mode.MEASURE: self.act_measure,
        }
        self.act_nav.setChecked(True)

    def _add(self, menu, text, slot, shortcut=None):
        a = QtWidgets.QAction(text, self)
        a.triggered.connect(slot)
        if shortcut:
            a.setShortcut(shortcut)
        menu.addAction(a)
        return a

    # ------------------------------------------------------------------ #
    def _build_tray_icon(self):
        self.tray = None
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QtWidgets.QSystemTrayIcon(app_icon(), self)
        self.tray.setToolTip("mf6Voronoi Studio")
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def _notify(self, title: str, message: str, warning: bool = False):
        icon = (QtWidgets.QSystemTrayIcon.Warning if warning
               else QtWidgets.QSystemTrayIcon.Information)
        if self.tray is not None:
            self.tray.showMessage(title, message, icon, 5000)
        else:
            self.statusBar().showMessage(f"{title}: {message}", 5000)

    # ------------------------------------------------------------------ #
    def log_msg(self, msg: str):
        self.log.appendPlainText(msg)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    # ------------------------------------------------------------------ #
    def _update_title(self):
        title = f"mf6Voronoi Studio {APP_VERSION}"
        if is_portable():
            title += "  •  Portable"
        if self._current_project_path:
            title += f"  —  {os.path.basename(self._current_project_path)}"
        if self._dirty:
            title += " *"
        self.setWindowTitle(title)

    def _mark_dirty(self):
        self._dirty = True
        self._update_title()

    def _confirm_discard_if_dirty(self, title: str = "mf6Voronoi Studio") -> bool:
        """Returns True if it's OK to proceed (nothing to lose, changes were
        saved, or the user chose to discard them)."""
        if not self._dirty:
            return True
        resp = QtWidgets.QMessageBox.question(
            self, title,
            "The current project has unsaved changes. Save them first?",
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard
            | QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.Save)
        if resp == QtWidgets.QMessageBox.Cancel:
            return False
        if resp == QtWidgets.QMessageBox.Save:
            self.action_save_project()
            return not self._dirty
        return True

    def _unit(self):
        return engine.crs_length_unit(self.project.crs) if self.project.crs else "units"

    # ------------------------------------------------------------------ #
    def _set_mode(self, mode: str):
        if mode in (Mode.NAVIGATE, Mode.LIMIT, Mode.VOID) and self._pending_layer:
            self._finish_pending_layer(silent=True)
        self.canvas.set_mode(mode)
        for m, a in getattr(self, "_mode_actions", {}).items():
            a.setChecked(m == mode)

    def _start_draw_void(self):
        if self.project.crs is None:
            self._warn("Set the project CRS before drawing.")
            self._sync_mode_buttons()
            return
        if self._pending_layer:
            self._finish_pending_layer(silent=True)
        name, ok = QtWidgets.QInputDialog.getText(
            self, "New void polygon", "Name:",
            text=f"void_{len(self.project.voids) + 1}")
        if not ok or not name.strip():
            return
        self._pending_void_name = name.strip()
        self.canvas.set_mode(Mode.VOID)
        self._sync_mode_buttons(Mode.VOID)
        self.log_msg(f"Drawing void polygon '{self._pending_void_name}'.")

    def _start_draw_layer(self, mode: str):
        if self.project.crs is None:
            self._warn("Set the project CRS before drawing.")
            self._sync_mode_buttons()
            return
        if self._pending_layer:
            self._finish_pending_layer(silent=True)
        dtype = {Mode.POINT: "points", Mode.LINE: "polyline", Mode.POLYGON: "polygon"}[mode]
        dlg = LayerRefDialog(self, f"New {dtype} refinement layer",
                             f"{dtype}_{len(self.project.layers)+1}", unit=self._unit())
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            self._set_mode(Mode.NAVIGATE)
            return
        name, ref = dlg.values()
        empty = gpd.GeoDataFrame({"id": []}, geometry=[], crs=self.project.crs)
        color = engine.LAYER_COLORS[len(self.project.layers) % len(engine.LAYER_COLORS)]
        self._pending_layer = engine.RefinementLayer(name=name, gdf=empty, ref=ref, color=color)
        self.canvas.set_mode(mode)
        self.canvas.begin_pending_layer(color)
        self._sync_mode_buttons(mode)
        self.log_msg(f"Drawing layer '{name}' (cell size {ref} {self._unit()}). "
                     "Click 'Finish layer' when done.")

    def _on_geometry_drawn(self, geom, geom_type):
        if self.canvas.mode == Mode.LIMIT:
            self.project.set_limit_from_gdf(
                gpd.GeoDataFrame({"id": [1]}, geometry=[geom], crs=self.project.crs))
            self.log_msg("Limit polygon set.")
            self._mark_dirty()
            self._set_mode(Mode.NAVIGATE)
            self.canvas.sync_limit()
            return
        if self.canvas.mode == Mode.VOID:
            name = self._pending_void_name or f"void_{len(self.project.voids) + 1}"
            self._pending_void_name = None
            gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[geom], crs=self.project.crs)
            self.project.add_void_from_gdf(name, gdf)
            self.log_msg(f"Void polygon '{name}' added.")
            self._mark_dirty()
            self._refresh_void_list()
            self.canvas.sync_voids()
            self._set_mode(Mode.NAVIGATE)
            return
        if self._pending_layer is None:
            return
        gdf = self._pending_layer.gdf
        new = gpd.GeoDataFrame({"id": [len(gdf) + 1]}, geometry=[geom], crs=self.project.crs)
        if gdf is None or gdf.empty:
            self._pending_layer.gdf = new
        else:
            self._pending_layer.gdf = gpd.GeoDataFrame(
                pd.concat([gdf, new], ignore_index=True), crs=self.project.crs)
        self._mark_dirty()
        self.canvas.add_committed_feature(geom, geom_type)

    def _finish_pending_layer(self, silent=False):
        if not self._pending_layer:
            if not silent:
                self.statusBar().showMessage("No layer is being drawn.")
            return
        self.canvas.auto_finish_partial()
        lyr = self._pending_layer
        self._pending_layer = None
        self.canvas.end_pending_layer()
        if lyr.gdf is None or lyr.gdf.empty:
            self.log_msg(f"Layer '{lyr.name}' had no features — discarded.")
        else:
            self.project.layers.append(lyr)
            self.log_msg(f"Committed layer '{lyr.name}' ({lyr.feature_count} feature(s)).")
            self._mark_dirty()
            self._refresh_layer_list()
            self.canvas.sync_layers()
        self._set_mode(Mode.NAVIGATE)

    def _cancel_pending_layer(self):
        if not self._pending_layer:
            self.statusBar().showMessage("No layer is being drawn.")
            return
        n = self._pending_layer.feature_count
        if n > 0:
            if QtWidgets.QMessageBox.question(
                    self, "Cancel layer",
                    f"Discard {n} drawn feature(s) in '{self._pending_layer.name}'?") \
                    != QtWidgets.QMessageBox.Yes:
                return
        self._pending_layer = None
        self.canvas.end_pending_layer()
        self._set_mode(Mode.NAVIGATE)
        self.log_msg("Cancelled the layer being drawn.")

    def _sync_mode_buttons(self, mode=Mode.NAVIGATE):
        for m, a in getattr(self, "_mode_actions", {}).items():
            a.setChecked(m == mode)

    # ------------------------------------------------------------------ #
    def action_set_crs(self):
        current = None
        if self.project.crs is not None:
            try:
                current = self.project.crs.to_epsg()
            except Exception:
                current = None
        dlg = CrsDialog(self, current_epsg=current)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        text = dlg.value()
        if not text:
            return
        try:
            self.project.set_crs(text)
        except Exception as e:
            self._warn(f"Invalid CRS: {e}")
            return
        if not engine.crs_is_valid_for_meshing(self.project.crs):
            self._warn(
                "This CRS is not usable for meshing. mf6Voronoi needs a "
                "projected CRS whose length unit is metres or feet.\n\n"
                f"Detected unit: {engine.crs_length_unit(self.project.crs)}")
        self._mark_dirty()
        self._update_crs_label()

    def _update_crs_label(self):
        crs = self.project.crs
        if crs is None:
            self.crs_label.setText("No CRS set")
            self.crs_label.setStyleSheet("color:#ef5350;")
            return
        ok = engine.crs_is_valid_for_meshing(crs)
        self.crs_label.setText(self.project.crs_summary())
        self.crs_label.setStyleSheet("color:#3ecf8e;" if ok else "color:#ef5350;")

    # ------------------------------------------------------------------ #
    def action_import_limit(self):
        path = self._open_file("Import limit polygon", "Shapefiles (*.shp)")
        if not path:
            return
        had_crs_before = self.project.crs is not None
        try:
            probe = gpd.read_file(path, rows=1)
        except Exception as e:
            self._warn(f"Could not read shapefile: {e}")
            return
        try:
            self.project.load_limit_shapefile(path)
        except Exception as e:
            self._warn(f"Could not load limit: {e}")
            return
        self._mark_dirty()
        self._update_crs_label()
        self.log_msg(f"Imported limit polygon from {os.path.basename(path)}.")
        if probe.crs is not None:
            if not had_crs_before:
                self.log_msg(f"Detected CRS from the shapefile's .prj file: "
                            f"{self.project.crs_summary()}")
        else:
            self._warn(
                "This shapefile has no coordinate system information (no "
                ".prj file found alongside it).\n\n"
                "The limit polygon was loaded anyway. Please set the CRS "
                "manually (“Set / change CRS…”) and make sure "
                "every shapefile you import uses that exact same coordinate "
                "system.")
        self.canvas.sync_limit()
        self.canvas.zoom_to_data()

    def action_import_layer(self):
        if self.project.crs is None:
            self._warn("Set or import a CRS first (import the limit polygon).")
            return
        path = self._open_file("Import refinement shapefile", "Shapefiles (*.shp)")
        if not path:
            return
        try:
            probe = gpd.read_file(path, rows=1)
        except Exception as e:
            self._warn(f"Could not read shapefile: {e}")
            return
        if probe.crs is not None and not probe.crs.equals(self.project.crs):
            self._warn(
                "This shapefile's CRS differs from the project CRS.\n\n"
                f"Project: {self.project.crs.name}\nFile: {probe.crs.name}\n\n"
                "All inputs must share the same CRS. Re-project it first.")
            return
        if probe.crs is None:
            self._warn(
                "This shapefile has no coordinate system information (no "
                ".prj file found alongside it).\n\n"
                "It will be assumed to already be in the project's "
                f"coordinate system ({self.project.crs_summary()}).\n\n"
                "Make sure every shapefile you import uses that exact same "
                "coordinate system — otherwise features will be "
                "misaligned on the map.")
        dlg = LayerRefDialog(self, "Refinement size",
                             os.path.splitext(os.path.basename(path))[0], unit=self._unit())
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        name, ref = dlg.values()
        try:
            self.project.load_layer_shapefile(path, ref, name)
        except Exception as e:
            self._warn(f"Could not add layer: {e}")
            return
        self.log_msg(f"Imported refinement layer '{name}' (cell size {ref} {self._unit()}).")
        self._mark_dirty()
        self._refresh_layer_list()
        self.canvas.sync_layers()
        self.canvas.zoom_to_data()

    def action_import_void(self):
        if self.project.crs is None:
            self._warn("Set or import a CRS first (import the limit polygon).")
            return
        path = self._open_file("Import void polygon shapefile", "Shapefiles (*.shp)")
        if not path:
            return
        try:
            probe = gpd.read_file(path, rows=1)
        except Exception as e:
            self._warn(f"Could not read shapefile: {e}")
            return
        if probe.crs is not None and not probe.crs.equals(self.project.crs):
            self._warn(
                "This shapefile's CRS differs from the project CRS.\n\n"
                f"Project: {self.project.crs.name}\nFile: {probe.crs.name}\n\n"
                "All inputs must share the same CRS. Re-project it first.")
            return
        if probe.crs is None:
            self._warn(
                "This shapefile has no coordinate system information (no "
                ".prj file found alongside it).\n\n"
                "It will be assumed to already be in the project's "
                f"coordinate system ({self.project.crs_summary()}).\n\n"
                "Make sure every shapefile you import uses that exact same "
                "coordinate system — otherwise features will be "
                "misaligned on the map.")
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Void polygon name", "Name:",
            text=os.path.splitext(os.path.basename(path))[0])
        if not ok or not name.strip():
            return
        try:
            self.project.load_void_shapefile(path, name.strip())
        except Exception as e:
            self._warn(f"Could not add void polygon: {e}")
            return
        self.log_msg(f"Imported void polygon '{name.strip()}' from "
                     f"{os.path.basename(path)}.")
        self._mark_dirty()
        self._refresh_void_list()
        self.canvas.sync_voids()
        self.canvas.zoom_to_data()

    def action_import_background(self):
        dlg = AddBackgroundDialog(self, self)
        dlg.exec_()

    def _add_background_file_flow(self) -> bool:
        path = self._open_file(
            "Import background image", "Images (*.tif *.tiff *.png *.jpg *.jpeg)")
        if not path:
            return False
        ext = path.lower().rsplit(".", 1)[-1]
        world = None
        extent = None
        if ext in ("png", "jpg", "jpeg"):
            for wext in (".pgw", ".jgw", ".wld"):
                cand = os.path.splitext(path)[0] + wext
                if os.path.exists(cand):
                    world = cand
                    break
            if world is None:
                dlg = ExtentDialog(self)
                if dlg.exec_() != QtWidgets.QDialog.Accepted:
                    return False
                extent = dlg.values()
        try:
            bg = self.project.add_background(path, extent=extent, world_file=world)
        except Exception as e:
            self._warn(f"Could not load image: {e}")
            return False
        if bg.crs is not None and self.project.crs is not None:
            if not bg.crs.equals(self.project.crs):
                self._warn("Note: the image CRS differs from the project CRS. "
                           "It is shown as a backdrop only.")
        self.log_msg(f"Loaded background image {os.path.basename(path)}.")
        self._mark_dirty()
        self.canvas.sync_backgrounds()
        self.canvas.zoom_to_data()
        self._refresh_background_list()
        return True

    def _add_background_from_geotiff_path(self, path: str):
        try:
            bg = self.project.add_background(path)
        except Exception as e:
            self._warn(f"Could not add background image: {e}")
            return
        self.log_msg(f"Added online satellite image as background '{bg.name}'.")
        self._mark_dirty()
        self.canvas.sync_backgrounds()
        self.canvas.zoom_to_data()
        self._refresh_background_list()

    def action_remove_background(self):
        row = self.bg_list.currentRow()
        if row < 0:
            return
        name = self.project.backgrounds[row].name
        self.project.remove_background(row)
        self._mark_dirty()
        self.canvas.sync_backgrounds()
        self._refresh_background_list()
        self.log_msg(f"Background image '{name}' removed.")

    def _remove_background_by_ref(self, bg_ref):
        for i, bg in enumerate(self.project.backgrounds):
            if bg is bg_ref:
                self.project.remove_background(i)
                self._mark_dirty()
                self.canvas.sync_backgrounds()
                self._refresh_background_list()
                self.log_msg(f"Background image '{bg.name}' removed.")
                return

    def _refresh_background_list(self):
        self.bg_list.blockSignals(True)
        self.bg_list.clear()
        for bg in self.project.backgrounds:
            h, w = bg.image.shape[0], bg.image.shape[1]
            item = QtWidgets.QListWidgetItem(f"{bg.name}  ({w}×{h}px)")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if bg.visible else Qt.Unchecked)
            self.bg_list.addItem(item)
        self.bg_list.blockSignals(False)
        self._update_background_buttons()

    def _on_background_item_changed(self, item):
        row = self.bg_list.row(item)
        if 0 <= row < len(self.project.backgrounds):
            visible = item.checkState() == Qt.Checked
            self.project.backgrounds[row].visible = visible
            self.canvas.set_background_visible(row, visible)

    def _update_background_buttons(self, *_):
        self.btn_bg_remove.setEnabled(self.bg_list.currentRow() >= 0)

    # ------------------------------------------------------------------ #
    def _refresh_layer_list(self):
        self.layer_list.blockSignals(True)
        self.layer_list.clear()
        for lyr in self.project.layers:
            elev = ""
            if getattr(lyr, "top_raster", None) or getattr(lyr, "botm_raster", None):
                elev = "  ⛰"
            item = QtWidgets.QListWidgetItem(
                f"{lyr.name}  [{lyr.geom_type}]  size={lyr.ref:g}{elev}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if lyr.visible else Qt.Unchecked)
            item.setForeground(QtGui.QColor(lyr.color))
            tip = []
            if getattr(lyr, "top_raster", None):
                tip.append(f"top: {lyr.top_raster}")
            if getattr(lyr, "botm_raster", None):
                tip.append(f"botm: {lyr.botm_raster}")
            if tip:
                item.setToolTip("\n".join(tip))
            self.layer_list.addItem(item)
        self.layer_list.blockSignals(False)
        self._update_layer_buttons()

    def _on_layer_item_changed(self, item):
        row = self.layer_list.row(item)
        if 0 <= row < len(self.project.layers):
            visible = item.checkState() == Qt.Checked
            self.project.layers[row].visible = visible
            self.canvas.set_layer_visible(row, visible)

    def _update_layer_buttons(self, *_):
        has = self.layer_list.currentRow() >= 0
        self.btn_edit_ref.setEnabled(has)
        self.btn_del_layer.setEnabled(has)
        self.btn_layer_elev.setEnabled(has)

    def action_edit_ref(self):
        row = self.layer_list.currentRow()
        if row < 0:
            return
        lyr = self.project.layers[row]
        val, ok = QtWidgets.QInputDialog.getDouble(
            self, "Edit cell size", f"Target cell size for '{lyr.name}':",
            lyr.ref, 0.001, 1e9, 3)
        if ok:
            self.project.set_layer_ref(row, val)
            self._mark_dirty()
            self._refresh_layer_list()

    def action_delete_layer(self):
        row = self.layer_list.currentRow()
        if row < 0:
            return
        name = self.project.layers[row].name
        self.project.remove_layer(row)
        self.log_msg(f"Deleted layer '{name}'.")
        self._mark_dirty()
        self._refresh_layer_list()
        self.canvas.sync_layers()

    # ------------------------------------------------------------------ #
    def _refresh_void_list(self):
        self.void_list.blockSignals(True)
        self.void_list.clear()
        for void in self.project.voids:
            item = QtWidgets.QListWidgetItem(
                f"{void.name}  ({void.feature_count} polygon(s))")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if void.visible else Qt.Unchecked)
            item.setForeground(QtGui.QColor(void.color))
            self.void_list.addItem(item)
        self.void_list.blockSignals(False)
        self._update_void_buttons()

    def _on_void_item_changed(self, item):
        row = self.void_list.row(item)
        if 0 <= row < len(self.project.voids):
            visible = item.checkState() == Qt.Checked
            self.project.voids[row].visible = visible
            self.canvas.set_void_visible(row, visible)

    def _update_void_buttons(self, *_):
        self.btn_del_void.setEnabled(self.void_list.currentRow() >= 0)

    def action_delete_void(self):
        row = self.void_list.currentRow()
        if row < 0:
            return
        name = self.project.voids[row].name
        self.project.remove_void(row)
        self.log_msg(f"Deleted void polygon '{name}'.")
        self._mark_dirty()
        self._refresh_void_list()
        self.canvas.sync_voids()

    def action_layer_elevations(self):
        row = self.layer_list.currentRow()
        if row < 0:
            self._warn("Select a refinement layer first.")
            return
        lyr = self.project.layers[row]
        dlg = LayerElevationDialog(self, lyr)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        top_r, botm_r = dlg.values()
        lyr.top_raster = top_r or None
        lyr.botm_raster = botm_r or None
        self.log_msg(
            f"Layer '{lyr.name}' elevation rasters set "
            f"(top={os.path.basename(top_r) if top_r else '—'}, "
            f"botm={os.path.basename(botm_r) if botm_r else '—'}).")
        self._mark_dirty()
        self._refresh_layer_list()

    # ------------------------------------------------------------------ #
    def _sync_mesh_params(self, *_):
        self.project.mesh_params = {
            "max_ref": self.opt_maxref.value(),
            "multiplier": self.opt_mult.value(),
            "overlapping": self.opt_overlap.isChecked(),
            "quality": self.opt_quality.value(),
        }

    def _on_mesh_option_changed(self, *_):
        self._sync_mesh_params()
        self._mark_dirty()

    def _load_mesh_params_into_panel(self):
        mp = self.project.mesh_params
        widgets = (self.opt_maxref, self.opt_mult, self.opt_overlap, self.opt_quality)
        for w in widgets:
            w.blockSignals(True)
        self.opt_maxref.setValue(mp.get("max_ref", 200.0))
        self.opt_mult.setValue(mp.get("multiplier", 1.3))
        self.opt_overlap.setChecked(mp.get("overlapping", True))
        self.opt_quality.setValue(mp.get("quality", 0.0))
        for w in widgets:
            w.blockSignals(False)

    # ------------------------------------------------------------------ #
    def action_quality_report(self, *_, silent: bool = False):
        if self.project.result is None:
            if not silent:
                self._warn("Generate a mesh first.")
            return
        thr = self.opt_quality.value()
        try:
            rep = self.project.quality_report(short_edge_threshold=thr, log_cb=self.log_msg)
        except Exception as e:
            if not silent:
                self._warn(f"Could not compute report: {e}")
            return
        self._last_report = rep
        self._populate_report_table(rep)

    def _populate_report_table(self, rep: dict):
        u = rep["unit"]
        rows = [
            ("Cells (ncpl)", f"{rep['ncpl']:,}"),
            ("Vertices (nvert)", f"{rep['nvert']:,}"),
            (f"Cell area min ({u}²)", f"{rep['area_min']:,.2f}"),
            (f"Cell area max ({u}²)", f"{rep['area_max']:,.2f}"),
            (f"Cell area mean ({u}²)", f"{rep['area_mean']:,.2f}"),
            (f"Cell area median ({u}²)", f"{rep['area_median']:,.2f}"),
            (f"Total area ({u}²)", f"{rep['area_total']:,.2f}"),
            ("Vertices / cell (min)", f"{rep['verts_min']}"),
            ("Vertices / cell (max)", f"{rep['verts_max']}"),
            ("Vertices / cell (mean)", f"{rep['verts_mean']:.2f}"),
            (f"Shortest edge ({u})", f"{rep['edge_min']:.4f}"),
            (f"Mean of min edges ({u})", f"{rep['edge_min_mean']:.4f}"),
            (f"Short-edge threshold ({u})", f"{rep['short_edge_threshold']:.3f}"),
            ("Cells with short edges", f"{rep['short_edge_cells']}"),
        ]
        self.report_table.setRowCount(len(rows))
        for r, (k, v) in enumerate(rows):
            self.report_table.setItem(r, 0, QtWidgets.QTableWidgetItem(k))
            item = QtWidgets.QTableWidgetItem(v)
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if k == "Cells with short edges" and rep['short_edge_cells'] > 0:
                item.setForeground(QtGui.QColor("#ef5350"))
            self.report_table.setItem(r, 1, item)
        self.report_table.resizeColumnsToContents()

    def action_export_report(self):
        if not self._last_report:
            self._warn("Compute the report first.")
            return
        path = self._save_file(
            "Save quality report", f"{self.project.mesh_name}_report.csv",
            "CSV (*.csv);;JSON (*.json)")
        if not path:
            return
        try:
            if path.lower().endswith(".json"):
                import json as _json
                with open(path, "w") as fh:
                    _json.dump(self._last_report, fh, indent=2)
            else:
                import csv
                with open(path, "w", newline="") as fh:
                    w = csv.writer(fh)
                    w.writerow(["metric", "value"])
                    for k, v in self._last_report.items():
                        w.writerow([k, v])
            self.log_msg(f"Quality report written: {path}")
        except Exception as e:
            self._warn(f"Could not save report: {e}")

    # ------------------------------------------------------------------ #
    def action_new_project(self):
        if not self._confirm_discard_if_dirty("New project"):
            return
        self.project = engine.MeshProject()
        self._pending_layer = None
        self.canvas.set_project(self.project)
        self._last_report = None
        self.report_table.setRowCount(0)
        self.mesh_info.setText("No mesh generated.")
        self.chk_mesh_visible.setChecked(True)
        self.log.clear()
        self._load_mesh_params_into_panel()
        self._update_crs_label()
        self._refresh_layer_list()
        self._refresh_void_list()
        self._refresh_background_list()
        self._current_project_path = None
        self._dirty = False
        self._update_title()
        self.log_msg("Started a new project.")

    def action_save_project(self):
        """Quick save: reuse the current file path if known, else prompt
        exactly like Save As."""
        if self._current_project_path:
            self._save_to(self._current_project_path)
        else:
            self.action_save_project_as()

    def action_save_project_as(self):
        path = self._save_file("Save project as", f"{self.project.mesh_name}.mf6vor",
                               "mf6Voronoi project (*.mf6vor);;JSON (*.json)")
        if not path:
            return
        self._save_to(path)

    def _save_to(self, path: str) -> bool:
        try:
            self._sync_mesh_params()
            self.project.save_project(path)
            self._current_project_path = path
            self._dirty = False
            self._update_title()
            self.log_msg(f"Project saved: {path}")
            return True
        except Exception:
            self.log_msg("ERROR:\n" + traceback.format_exc())
            self._warn("Could not save project. See the log for details.")
            return False

    def action_open_project(self):
        if not self._confirm_discard_if_dirty("Open project"):
            return
        path = self._open_file("Open project", "mf6Voronoi project (*.mf6vor *.json)")
        if not path:
            return
        self.open_project_path(path)

    def open_project_path(self, path: str):
        try:
            proj = engine.MeshProject.load_project(path)
        except Exception:
            self.log_msg("ERROR:\n" + traceback.format_exc())
            self._warn("Could not open project. See the log for details.")
            return
        self.project = proj
        self._pending_layer = None
        self.canvas.set_project(proj)
        self._last_report = None
        self.report_table.setRowCount(0)
        self.chk_mesh_visible.setChecked(True)
        self._load_mesh_params_into_panel()
        self._update_crs_label()
        self._refresh_layer_list()
        self._refresh_void_list()
        self._refresh_background_list()
        self._current_project_path = path
        self._dirty = False
        self._update_title()
        if proj.result is not None:
            self.mesh_info.setText(f"{len(proj.result.gdf)} cells (loaded).")
        else:
            self.mesh_info.setText("No mesh generated.")
        self.log_msg(f"Project loaded: {path}")
        if proj.result is not None:
            self.action_quality_report(silent=True)

    # ------------------------------------------------------------------ #
    def action_build_mesh(self):
        ok, problems = self.project.validate()
        if not ok:
            self._warn("Please fix the following before meshing:\n\n- "
                       + "\n- ".join(problems))
            return
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Generate Voronoi mesh", "Mesh name:", text=self.project.mesh_name)
        if not ok:
            return
        self.project.mesh_name = name.strip() or "voronoiModel"
        self._sync_mesh_params()
        vals = dict(self.project.mesh_params)
        vals["name"] = self.project.mesh_name
        self.btn_build.setEnabled(False)
        self.log_msg("\n=== Generating Voronoi mesh ===")
        self.log_msg(f"  coarse={vals['max_ref']:g}, multiplier={vals['multiplier']:g}, "
                     f"overlapping={vals['overlapping']}, "
                     f"fix-short-edges={vals['quality']:g}")
        self.worker = MeshWorker(self.project, vals)
        self.worker.log.connect(self.log_msg)
        self.worker.finished_ok.connect(self._on_mesh_done)
        self.worker.failed.connect(self._on_mesh_failed)
        self.worker.start()

    def _on_mesh_done(self, result):
        self.btn_build.setEnabled(True)
        n = len(result.gdf)
        self.mesh_info.setText(f"{n} cells generated.")
        self.log_msg(f"Mesh ready: {n} cells.")
        self._mark_dirty()
        self.canvas.sync_mesh()
        try:
            self.action_quality_report(silent=True)
        except Exception:
            pass
        summary = self._quality_summary_text()
        message = f"The mesh has been created: {n:,} cells." \
            + (f"\n\n{summary}" if summary else "")
        self._notify("mf6Voronoi Studio", message)
        self._show_mesh_popup("Mesh generated", message)

    def _quality_summary_text(self) -> str:
        rep = self._last_report
        if not rep:
            return ""
        return (f"Quality report: {rep['ncpl']:,} cells, "
               f"area {rep['area_min']:.2f}–{rep['area_max']:.2f} "
               f"{rep['unit']}², shortest edge {rep['edge_min']:.4f} "
               f"{rep['unit']}.")

    def _show_mesh_popup(self, title: str, text: str) -> None:
        """A guaranteed-visible in-app popup: unlike the OS-level tray
        notification (which Windows can silently suppress for unsigned/
        frozen apps, or if Focus Assist / notification permissions block
        it), this is a normal window Qt always renders. Non-modal so it
        doesn't block further work."""
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Information)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        box.setModal(False)
        box.show()
        self._mesh_popup = box  # keep a reference so it isn't garbage-collected

    def _on_mesh_failed(self, tb):
        self.btn_build.setEnabled(True)
        self.log_msg("ERROR during mesh generation:\n" + tb)
        self._notify("mf6Voronoi Studio", "Mesh generation failed.", warning=True)
        self._warn("Mesh generation failed. See the log for details.")

    # ------------------------------------------------------------------ #
    def action_export_shp(self):
        if not self._has_mesh():
            return
        path = self._save_file("Export mesh shapefile",
                               f"{self.project.mesh_name}_voronoi.shp", "Shapefile (*.shp)")
        if not path:
            return
        try:
            self.project.export_shapefile(path)
            self.log_msg(f"Mesh shapefile written: {path}")
        except Exception as e:
            self._warn(f"Export failed: {e}")

    def action_export_json(self):
        if not self._has_mesh():
            return
        path = self._save_file("Export DISV JSON",
                               f"{self.project.mesh_name}_disv.json", "JSON (*.json)")
        if not path:
            return
        try:
            self.log_msg("Computing DISV properties…")
            self.project.export_disv_json(path, log_cb=self.log_msg)
            self.log_msg(f"DISV properties written: {path}")
        except Exception as e:
            self._warn(f"Export failed: {e}")

    def action_export_modelmuse(self):
        if not self._has_mesh():
            return
        dlg = ModelMuseDialog(self, project=self.project)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        try:
            nlay, top, botm, exe = dlg.values()
        except Exception as e:
            self._warn(f"Invalid layer elevations: {e}")
            return
        if len(botm) != nlay:
            self._warn(f"Provide exactly {nlay} bottom elevation(s); got {len(botm)}.")
            return
        for spec, lbl in [(top, "top")] + [(b, f"layer {i+1} bottom")
                                           for i, b in enumerate(botm)]:
            if isinstance(spec, str) and not os.path.exists(spec):
                self._warn(f"Raster for {lbl} not found:\n{spec}")
                return
        ws = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose an (empty) output folder for the MODFLOW 6 model")
        if not ws:
            return
        try:
            n_rasters = sum(1 for s in [top] + botm if isinstance(s, str))
            self.log_msg(f"Building MODFLOW 6 DISV model "
                         f"({nlay} layer(s), {n_rasters} raster surface(s))…")
            nam = self.project.export_modelmuse(
                ws, nlay=nlay, top=top, botm=botm, mf6_exe=exe, log_cb=self.log_msg)
            self.log_msg(f"ModelMuse model written. Import '{nam}' in ModelMuse "
                         "(File → Import → Import MODFLOW-6 Model).")
            QtWidgets.QMessageBox.information(
                self, "Export complete",
                "MODFLOW 6 DISV model written.\n\nIn ModelMuse:\n"
                "File → Import → Import MODFLOW-6 Model → select 'mfsim.nam'.")
        except Exception as e:
            self.log_msg("ERROR:\n" + traceback.format_exc())
            self._warn(f"ModelMuse export failed: {e}")

    # ------------------------------------------------------------------ #
    def action_about(self):
        QtWidgets.QMessageBox.about(
            self, "About mf6Voronoi Studio",
            f"<h3>mf6Voronoi Studio</h3>"
            f"<p><b>Version {APP_VERSION}</b></p>"
            "<p>A graphical front-end for the "
            "<a href='https://github.com/hatarilabs/mf6Voronoi'>mf6Voronoi</a> "
            "package to create, edit and export MODFLOW 6 DISV Voronoi meshes."
            "</p><p>Requires a single projected CRS in metres or feet.</p>"
            "<hr>"
            "<p><b>Credits:</b><br>"
            "mf6Voronoi — Saul Montoya<br>"
            "GUI developer — An Ho Taylor</p>"
            "<p><i>Viva el Software Libre</i></p>")

    def _has_mesh(self):
        if self.project.result is None:
            self._warn("Generate a mesh first.")
            return False
        return True

    def _warn(self, msg):
        QtWidgets.QMessageBox.warning(self, "mf6Voronoi Studio", msg)

    def _open_file(self, title, flt):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, title, self._last_dir, flt)
        if path:
            self._last_dir = os.path.dirname(path)
        return path

    def _save_file(self, title, default, flt):
        start = os.path.join(self._last_dir, default) if self._last_dir else default
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, title, start, flt)
        if path:
            self._last_dir = os.path.dirname(path)
        return path

    # ------------------------------------------------------------------ #
    def _restore_settings(self):
        s = self.settings
        geo = s.value("window/geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        state = s.value("window/state")
        if state is not None:
            self.restoreState(state)
        self._last_dir = s.value("io/last_dir", "", type=str)
        widgets = (self.opt_maxref, self.opt_mult, self.opt_overlap, self.opt_quality)
        for w in widgets:
            w.blockSignals(True)
        try:
            self.opt_maxref.setValue(float(s.value("mesh/max_ref", self.opt_maxref.value())))
            self.opt_mult.setValue(float(s.value("mesh/multiplier", self.opt_mult.value())))
            self.opt_overlap.setChecked(
                s.value("mesh/overlapping", self.opt_overlap.isChecked(), type=bool))
            self.opt_quality.setValue(float(s.value("mesh/quality", self.opt_quality.value())))
        except Exception:
            pass
        finally:
            for w in widgets:
                w.blockSignals(False)
        self._sync_mesh_params()

    def _save_settings(self):
        s = self.settings
        s.setValue("window/geometry", self.saveGeometry())
        s.setValue("window/state", self.saveState())
        s.setValue("io/last_dir", self._last_dir)
        mp = self.project.mesh_params
        s.setValue("mesh/max_ref", mp.get("max_ref", 200.0))
        s.setValue("mesh/multiplier", mp.get("multiplier", 1.3))
        s.setValue("mesh/overlapping", mp.get("overlapping", True))
        s.setValue("mesh/quality", mp.get("quality", 0.0))
        s.sync()

    def closeEvent(self, event):
        if not self._confirm_discard_if_dirty("Exit mf6Voronoi Studio"):
            event.ignore()
            return
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait(2000)
        try:
            self._save_settings()
        except Exception:
            pass
        if self.tray is not None:
            self.tray.hide()
        event.accept()
