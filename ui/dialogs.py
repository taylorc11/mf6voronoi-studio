"""
dialogs.py
==========
Modal dialogs used by the main window: layer/refinement setup, CRS entry,
manual image extent entry, and the ModelMuse / layer-elevation export dialogs.
"""
from __future__ import annotations

import os

from PyQt5 import QtWidgets

import engine


class LayerRefDialog(QtWidgets.QDialog):
    def __init__(self, parent, title, default_name, unit="units"):
        super().__init__(parent)
        self.setWindowTitle(title)
        form = QtWidgets.QFormLayout(self)
        self.name = QtWidgets.QLineEdit(default_name)
        self.ref = QtWidgets.QDoubleSpinBox()
        self.ref.setRange(0.001, 1e9)
        self.ref.setDecimals(3)
        self.ref.setValue(50.0)
        form.addRow("Layer name:", self.name)
        form.addRow(f"Target cell size ({unit}):", self.ref)
        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

    def values(self):
        return self.name.text().strip(), self.ref.value()


class CrsDialog(QtWidgets.QDialog):
    """Set/change the project CRS with immediate validity feedback."""

    def __init__(self, parent, current_epsg=None):
        super().__init__(parent)
        self.setWindowTitle("Set coordinate system (CRS)")
        self.setMinimumWidth(420)
        lay = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.edit = QtWidgets.QLineEdit(str(current_epsg) if current_epsg else "32612")
        form.addRow("EPSG code or PROJ/WKT string:", self.edit)
        lay.addLayout(form)
        hint = QtWidgets.QLabel(
            "mf6Voronoi needs a <b>projected</b> CRS whose length unit is "
            "<b>metres or feet</b> (e.g. EPSG 32612 = UTM 12N, metres).")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#94a0b3;")
        lay.addWidget(hint)
        self.status = QtWidgets.QLabel(" ")
        self.status.setWordWrap(True)
        lay.addWidget(self.status)
        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.edit.textChanged.connect(self._validate)
        self._validate()

    def _validate(self):
        text = self.edit.text().strip()
        if not text:
            self.status.setText(" ")
            return
        try:
            import pyproj
            crs = pyproj.CRS.from_user_input(text)
        except Exception as e:
            self.status.setText(f"Invalid CRS: {e}")
            self.status.setStyleSheet("color:#ef5350;")
            return
        if engine.crs_is_valid_for_meshing(crs):
            self.status.setText(f"Looks good — {crs.name}, "
                                f"unit: {engine.crs_length_unit(crs)}")
            self.status.setStyleSheet("color:#3ecf8e;")
        else:
            self.status.setText(
                f"{crs.name} — unit '{engine.crs_length_unit(crs)}' is not "
                "usable for meshing (need metres or feet).")
            self.status.setStyleSheet("color:#f5a623;")

    def value(self) -> str:
        return self.edit.text().strip()


class ExtentDialog(QtWidgets.QDialog):
    """Manual georeferenced extent entry for a PNG/JPG with no world file."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Image extent")
        form = QtWidgets.QFormLayout(self)
        note = QtWidgets.QLabel(
            "No world file was found next to this image. Enter its "
            "georeferenced extent in project CRS units:")
        note.setWordWrap(True)
        form.addRow(note)
        self.xmin = QtWidgets.QDoubleSpinBox(); self.xmin.setRange(-1e12, 1e12); self.xmin.setDecimals(3)
        self.xmax = QtWidgets.QDoubleSpinBox(); self.xmax.setRange(-1e12, 1e12); self.xmax.setDecimals(3)
        self.ymin = QtWidgets.QDoubleSpinBox(); self.ymin.setRange(-1e12, 1e12); self.ymin.setDecimals(3)
        self.ymax = QtWidgets.QDoubleSpinBox(); self.ymax.setRange(-1e12, 1e12); self.ymax.setDecimals(3)
        for box in (self.xmin, self.xmax, self.ymin, self.ymax):
            box.setMaximumWidth(160)
        form.addRow("X min:", self.xmin)
        form.addRow("X max:", self.xmax)
        form.addRow("Y min:", self.ymin)
        form.addRow("Y max:", self.ymax)
        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self._on_accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)
        self._error = None

    def _on_accept(self):
        if self.xmax.value() <= self.xmin.value() or self.ymax.value() <= self.ymin.value():
            QtWidgets.QMessageBox.warning(
                self, "Image extent", "X max must be greater than X min, and "
                "Y max must be greater than Y min.")
            return
        self.accept()

    def values(self):
        return (self.xmin.value(), self.xmax.value(), self.ymin.value(), self.ymax.value())


class AddBackgroundDialog(QtWidgets.QDialog):
    """Add a background image either from a local file or from an
    interactive online satellite/aerial basemap."""

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("Add background image")
        self.setMinimumSize(780, 640)
        root = QtWidgets.QVBoxLayout(self)

        tabs = QtWidgets.QTabWidget()
        root.addWidget(tabs, 1)

        file_tab = QtWidgets.QWidget()
        file_l = QtWidgets.QVBoxLayout(file_tab)
        note = QtWidgets.QLabel(
            "Import a local GeoTIFF, PNG or JPG. A world file (.pgw/.jgw/.wld) "
            "next to the image is used automatically if present; otherwise "
            "you'll be asked for its extent in project CRS units.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#94a0b3;")
        file_l.addWidget(note)
        btn_browse = QtWidgets.QPushButton("Browse and add…")
        btn_browse.setObjectName("PillButtonPrimary")
        btn_browse.clicked.connect(self._on_browse_file)
        file_l.addWidget(btn_browse)
        file_l.addStretch(1)
        tabs.addTab(file_tab, "From file")

        from .online_imagery import OnlineImageryPanel
        self.online_panel = OnlineImageryPanel(main_window, self)
        self.online_panel.log_message.connect(main_window.log_msg)
        self.online_panel.background_added.connect(self._on_online_added)
        tabs.addTab(self.online_panel, "Online satellite map")

        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        bb.rejected.connect(self.reject)
        bb.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.reject)
        root.addWidget(bb)

    def _on_browse_file(self):
        if self.main_window._add_background_file_flow():
            self.accept()

    def _on_online_added(self, path):
        self.main_window._add_background_from_geotiff_path(path)
        self.accept()


class ElevationField(QtWidgets.QWidget):
    def __init__(self, parent=None, default="0", raster=None):
        super().__init__(parent)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.edit = QtWidgets.QLineEdit(raster if raster else str(default))
        self.edit.setPlaceholderText("number (e.g. 100) or raster path")
        btn = QtWidgets.QPushButton("Raster…")
        btn.setMaximumWidth(70)
        btn.clicked.connect(self._browse)
        clr = QtWidgets.QToolButton()
        clr.setText("×")
        clr.setToolTip("Clear raster / reset to a constant")
        clr.clicked.connect(lambda: self.edit.setText("0"))
        lay.addWidget(self.edit, 1)
        lay.addWidget(btn)
        lay.addWidget(clr)

    def _browse(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose elevation raster", "",
            "Rasters (*.tif *.tiff *.asc *.vrt)")
        if path:
            self.edit.setText(path)

    def is_raster(self) -> bool:
        t = self.edit.text().strip()
        if not t:
            return False
        try:
            float(t)
            return False
        except ValueError:
            return True

    def value(self):
        t = self.edit.text().strip()
        if self.is_raster():
            return t
        return float(t) if t else 0.0


class ModelMuseDialog(QtWidgets.QDialog):
    def __init__(self, parent, project=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Export MODFLOW 6 DISV for ModelMuse")
        self.setMinimumWidth(560)
        root = QtWidgets.QVBoxLayout(self)
        top_form = QtWidgets.QFormLayout()
        self.nlay = QtWidgets.QSpinBox(); self.nlay.setRange(1, 999)
        self.nlay.setValue(1)
        self.nlay.valueChanged.connect(self._rebuild_table)
        self.exe = QtWidgets.QLineEdit("mf6")
        top_form.addRow("Number of layers:", self.nlay)
        top_form.addRow("MODFLOW 6 executable:", self.exe)
        root.addLayout(top_form)

        top_box = QtWidgets.QGroupBox("Model top (constant or raster)")
        top_l = QtWidgets.QVBoxLayout(top_box)
        self.top_field = ElevationField(default="100")
        top_l.addWidget(self.top_field)
        root.addWidget(top_box)

        botm_box = QtWidgets.QGroupBox(
            "Layer bottoms (each: constant value or raster)")
        botm_l = QtWidgets.QVBoxLayout(botm_box)
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Layer", "Bottom elevation"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 70)
        botm_l.addWidget(self.table)
        root.addWidget(botm_box)

        hint = QtWidgets.QLabel(
            "Tip: type a number for a flat surface, or click <b>Raster…</b> to "
            "sample a GeoTIFF at each cell centroid.<br>"
            "In ModelMuse: <b>File → Import → Import MODFLOW-6 Model</b> → "
            "select the generated <b>mfsim.nam</b>.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#94a0b3;")
        root.addWidget(hint)

        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        root.addWidget(bb)

        self._fields: list = []
        self._seed_top = None
        self._seed_botm = None
        self._prefill_from_layers()
        self._rebuild_table(self.nlay.value())

    def _prefill_from_layers(self):
        if not self.project:
            return
        for lyr in self.project.layers:
            if getattr(lyr, "top_raster", None) and self._seed_top is None:
                self._seed_top = lyr.top_raster
            if getattr(lyr, "botm_raster", None) and self._seed_botm is None:
                self._seed_botm = lyr.botm_raster
        if self._seed_top:
            self.top_field.edit.setText(self._seed_top)

    def _rebuild_table(self, n):
        prev = [f.edit.text() for f in self._fields] if self._fields else []
        self.table.setRowCount(n)
        self._fields = []
        for i in range(n):
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(f"Layer {i+1}"))
            if i < len(prev):
                field = ElevationField(default=prev[i]) if not self._looks_path(prev[i]) \
                    else ElevationField(raster=prev[i])
            else:
                if i == n - 1 and self._seed_botm:
                    field = ElevationField(raster=self._seed_botm)
                else:
                    field = ElevationField(default=str(-50 * (i + 1)))
            self._fields.append(field)
            self.table.setCellWidget(i, 1, field)
        self.table.resizeRowsToContents()

    @staticmethod
    def _looks_path(text):
        try:
            float(text)
            return False
        except ValueError:
            return True

    def values(self):
        top = self.top_field.value()
        botm = [f.value() for f in self._fields]
        return self.nlay.value(), top, botm, self.exe.text().strip()


class LayerElevationDialog(QtWidgets.QDialog):
    def __init__(self, parent, layer):
        super().__init__(parent)
        self.setWindowTitle(f"Elevation rasters — {layer.name}")
        self.setMinimumWidth(480)
        form = QtWidgets.QFormLayout(self)
        self.top = ElevationField(default="", raster=getattr(layer, "top_raster", None))
        self.botm = ElevationField(default="", raster=getattr(layer, "botm_raster", None))
        if not getattr(layer, "top_raster", None):
            self.top.edit.setText("")
        if not getattr(layer, "botm_raster", None):
            self.botm.edit.setText("")
        self.top.edit.setPlaceholderText("(optional) top raster path")
        self.botm.edit.setPlaceholderText("(optional) bottom raster path")
        form.addRow("Top raster:", self.top)
        form.addRow("Bottom raster:", self.botm)
        note = QtWidgets.QLabel(
            "These rasters become available as defaults when exporting the "
            "ModelMuse MODFLOW 6 model.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#94a0b3;")
        form.addRow(note)
        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

    def values(self):
        t = self.top.edit.text().strip()
        b = self.botm.edit.text().strip()
        t = t if (t and self._looks_path(t)) else ""
        b = b if (b and self._looks_path(b)) else ""
        return t, b

    @staticmethod
    def _looks_path(text):
        try:
            float(text)
            return False
        except ValueError:
            return True
