"""
canvas.py
=========
Native QGraphicsView/QGraphicsScene map canvas. Replaces the old matplotlib
embedded canvas: hardware-transformed pan/zoom, native item selection, and
incremental (not full-clear) rendering.
"""
from __future__ import annotations

from typing import Optional

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import QPainterPath, QPainter, QPen, QColor

from shapely.geometry import Point, LineString, Polygon

import engine
from .scene_items import (
    BackgroundImageItem, LimitPolygonItem, MeshLayerItem, LayerItemGroup,
    VoidPolygonItem, make_feature_preview_item, world_to_scene, scene_to_world,
    array_to_qpixmap,
)


class Mode:
    NAVIGATE = "navigate"
    LIMIT = "limit"
    POINT = "point"
    LINE = "line"
    POLYGON = "polygon"
    VOID = "void"
    MEASURE = "measure"


_HINTS = {
    Mode.LIMIT: "Click to add vertices for the model limit polygon. "
                "Double-click or Enter closes it.",
    Mode.POINT: "Click to drop refinement points into this layer. "
                "Click ‘Finish layer’ above when you're done.",
    Mode.LINE: "Click to add vertices. Double-click or Enter finishes this "
               "line and adds it to the layer — draw more, or click "
               "‘Finish layer’ when done.",
    Mode.POLYGON: "Click to add vertices. Double-click or Enter finishes this "
                  "polygon and adds it to the layer — draw more, or click "
                  "‘Finish layer’ when done.",
    Mode.VOID: "Click to add vertices for a void polygon — no mesh cells "
               "are generated inside it. Double-click or Enter closes it.",
    Mode.MEASURE: "Click a start point, then an end point to measure the "
                  "distance between them. Esc cancels; click again to "
                  "start a new measurement.",
}


def _unit_label(crs) -> str:
    if crs is None:
        return "units"
    unit = engine.crs_length_unit(crs)
    return {"meter": "m", "foot": "ft"}.get(unit, unit)


class _StatusPill(QtWidgets.QFrame):
    finish_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("StatusPill")
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 10, 8)
        lay.setSpacing(10)
        self.label = QtWidgets.QLabel()
        self.label.setObjectName("StatusPillLabel")
        btn_finish = QtWidgets.QPushButton("Finish layer")
        btn_finish.setObjectName("PillButtonPrimary")
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_finish.clicked.connect(self.finish_clicked.emit)
        btn_cancel.clicked.connect(self.cancel_clicked.emit)
        lay.addWidget(self.label, 1)
        lay.addWidget(btn_finish)
        lay.addWidget(btn_cancel)
        self.hide()

    def set_text(self, text: str) -> None:
        self.label.setText(text)
        self.adjustSize()


class MapScene(QtWidgets.QGraphicsScene):
    pass


class MapView(QtWidgets.QGraphicsView):
    geometry_finished = pyqtSignal(object, str)   # shapely geometry, geom_type
    status_message = pyqtSignal(str)
    remove_background_requested = pyqtSignal(object)   # engine.BackgroundImage
    finish_layer_requested = pyqtSignal()
    cancel_layer_requested = pyqtSignal()

    def __init__(self, project: engine.MeshProject, parent=None):
        self._scene = MapScene()
        super().__init__(self._scene, parent)
        self.project = project
        self.mode = Mode.NAVIGATE

        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._scene.setBackgroundBrush(QColor("#1a1d24"))

        self._panning = False
        self._pan_start = QPointF()
        self._pending_vertices: list = []
        self._vertex_dots: list = []
        self._rubberband_item: Optional[QtWidgets.QGraphicsPathItem] = None

        self._measure_anchor: Optional[tuple] = None
        self._measure_active = False
        self._measure_line_item: Optional[QtWidgets.QGraphicsPathItem] = None
        self._measure_label_item: Optional[QtWidgets.QGraphicsSimpleTextItem] = None

        self._bg_items: list = []
        self._limit_item = LimitPolygonItem()
        self._scene.addItem(self._limit_item)
        self._mesh_item = MeshLayerItem()
        self._scene.addItem(self._mesh_item)
        self._layer_groups: list = []
        self._void_items: list = []
        self._pending_color = "#4363d8"
        self._pending_preview_group: Optional[QtWidgets.QGraphicsItemGroup] = None
        self._pending_feature_count = 0

        self._pill = _StatusPill(self)
        self._pill.finish_clicked.connect(self.finish_layer_requested.emit)
        self._pill.cancel_clicked.connect(self.cancel_layer_requested.emit)

        self.rebuild_all()

    # ------------------------------------------------------------------ #
    def set_project(self, project: engine.MeshProject) -> None:
        self.project = project
        self.end_pending_layer()
        self.rebuild_all()

    def rebuild_all(self) -> None:
        self.sync_backgrounds()
        self.sync_limit()
        self.sync_layers()
        self.sync_voids()
        self.sync_mesh()
        self.zoom_to_data()

    def sync_backgrounds(self) -> None:
        for item in self._bg_items:
            self._scene.removeItem(item)
        self._bg_items = []
        for i, bg in enumerate(self.project.backgrounds):
            pixmap = array_to_qpixmap(bg.image)
            item = BackgroundImageItem(pixmap, bg.extent, bg_ref=bg, z=-200.0 + i)
            item.setVisible(bg.visible)
            self._scene.addItem(item)
            self._bg_items.append(item)

    def set_background_visible(self, index: int, visible: bool) -> None:
        if 0 <= index < len(self._bg_items):
            self._bg_items[index].setVisible(visible)

    def sync_limit(self) -> None:
        self._limit_item.set_geometry(self.project.limit_gdf)

    def sync_layers(self) -> None:
        for grp in self._layer_groups:
            self._scene.removeItem(grp)
        self._layer_groups = []
        for i, lyr in enumerate(self.project.layers):
            grp = LayerItemGroup(lyr, z=float(i))
            self._scene.addItem(grp)
            self._layer_groups.append(grp)

    def sync_voids(self) -> None:
        for item in self._void_items:
            self._scene.removeItem(item)
        self._void_items = []
        for void in self.project.voids:
            item = VoidPolygonItem(void)
            self._scene.addItem(item)
            self._void_items.append(item)

    def sync_mesh(self) -> None:
        gdf = self.project.result.gdf if self.project.result is not None else None
        self._mesh_item.set_geometry(gdf)

    def set_layer_visible(self, index: int, visible: bool) -> None:
        if 0 <= index < len(self._layer_groups):
            self._layer_groups[index].setVisible(visible)

    def set_void_visible(self, index: int, visible: bool) -> None:
        if 0 <= index < len(self._void_items):
            self._void_items[index].setVisible(visible)

    def set_mesh_visible(self, visible: bool) -> None:
        self._mesh_item.setVisible(visible)

    # ------------------------------------------------------------------ #
    def zoom_to_data(self) -> None:
        rect = self._data_bounds()
        if rect is None or rect.isEmpty():
            self.resetTransform()
            self.centerOn(0, 0)
            return
        mx = (rect.width() * 0.06) or 25.0
        my = (rect.height() * 0.06) or 25.0
        self.fitInView(rect.adjusted(-mx, -my, mx, my), Qt.KeepAspectRatio)

    def _data_bounds(self) -> Optional[QRectF]:
        items = ([self._limit_item, self._mesh_item] + self._layer_groups
                + self._void_items + self._bg_items)
        rect = QRectF()
        has_any = False
        for it in items:
            br = it.sceneBoundingRect()
            if br.isNull() or br.isEmpty():
                continue
            rect = br if not has_any else rect.united(br)
            has_any = True
        return rect if has_any else None

    def zoom_in(self) -> None:
        self.scale(1.25, 1.25)

    def zoom_out(self) -> None:
        self.scale(0.8, 0.8)

    # ------------------------------------------------------------------ #
    def set_mode(self, mode: str) -> None:
        self._cancel_current_shape(silent=True)
        self._clear_measure()
        self.mode = mode
        if mode == Mode.NAVIGATE:
            self.setCursor(Qt.ArrowCursor)
            self.status_message.emit(
                "Navigate: drag empty space to pan, wheel to zoom, click a "
                "feature to select it.")
        else:
            self.setCursor(Qt.CrossCursor)
            self.status_message.emit(_HINTS[mode])
            self.setFocus(Qt.OtherFocusReason)

    def begin_pending_layer(self, color: str) -> None:
        self.end_pending_layer()
        self._pending_color = color
        self._pending_feature_count = 0
        self._pending_preview_group = QtWidgets.QGraphicsItemGroup()
        self._pending_preview_group.setZValue(90)
        self._scene.addItem(self._pending_preview_group)
        self._show_pill("0 feature(s) added")

    def add_committed_feature(self, geom, geom_type: str) -> None:
        if self._pending_preview_group is None:
            return
        item = make_feature_preview_item(geom, geom_type, self._pending_color)
        self._pending_preview_group.addToGroup(item)
        self._pending_feature_count += 1
        self._show_pill(f"{self._pending_feature_count} feature(s) added")

    def end_pending_layer(self) -> None:
        if self._pending_preview_group is not None:
            self._scene.removeItem(self._pending_preview_group)
            self._pending_preview_group = None
        self._pending_feature_count = 0
        self._pill.hide()

    def auto_finish_partial(self) -> None:
        """Commit an in-progress shape (if long enough) instead of losing it
        silently when the layer is finished."""
        if self.mode in (Mode.LIMIT, Mode.POLYGON, Mode.VOID) and \
                len(self._pending_vertices) >= 3:
            self._finish_current_shape()
        elif self.mode == Mode.LINE and len(self._pending_vertices) >= 2:
            self._finish_current_shape()
        else:
            self._cancel_current_shape(silent=True)

    def _show_pill(self, text: str) -> None:
        self._pill.set_text(text)
        self._pill.show()
        self._position_pill()

    def _position_pill(self) -> None:
        vp = self.viewport().rect()
        x = (vp.width() - self._pill.width()) // 2
        self._pill.move(max(x, 8), 12)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_pill()

    # ------------------------------------------------------------------ #
    def _clear_vertex_preview(self) -> None:
        for dot in self._vertex_dots:
            self._scene.removeItem(dot)
        self._vertex_dots = []
        if self._rubberband_item is not None:
            self._scene.removeItem(self._rubberband_item)
            self._rubberband_item = None

    def _update_vertex_preview(self, cursor=None) -> None:
        self._clear_vertex_preview()
        pts = list(self._pending_vertices)
        if cursor is not None:
            pts = pts + [cursor]
        if not pts:
            return
        scene_pts = [world_to_scene(x, y) for x, y in pts]
        path = QPainterPath()
        path.moveTo(scene_pts[0])
        for p in scene_pts[1:]:
            path.lineTo(p)
        item = QtWidgets.QGraphicsPathItem(path)
        pen = QPen(QColor("#ff5f6d"), 1.6)
        pen.setCosmetic(True)
        item.setPen(pen)
        item.setZValue(95)
        self._scene.addItem(item)
        self._rubberband_item = item
        n_dots = len(pts) - 1 if cursor is not None else len(pts)
        r = 3.5
        for sp in scene_pts[:n_dots]:
            dot = QtWidgets.QGraphicsEllipseItem(-r, -r, 2 * r, 2 * r)
            dot.setPos(sp)
            dot.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
            dot.setBrush(QColor("#ff5f6d"))
            dot.setPen(QPen(Qt.NoPen))
            dot.setZValue(96)
            self._scene.addItem(dot)
            self._vertex_dots.append(dot)

    def _cancel_current_shape(self, silent: bool = False) -> None:
        if self._pending_vertices:
            self._pending_vertices = []
            self._clear_vertex_preview()
            if not silent:
                self.status_message.emit("Cancelled the current shape.")

    def _finish_current_shape(self) -> None:
        verts = self._pending_vertices
        self._pending_vertices = []
        self._clear_vertex_preview()
        if self.mode in (Mode.LIMIT, Mode.POLYGON, Mode.VOID) and len(verts) >= 3:
            self.geometry_finished.emit(Polygon(verts), engine.GEOM_POLYGON)
        elif self.mode == Mode.LINE and len(verts) >= 2:
            self.geometry_finished.emit(LineString(verts), engine.GEOM_LINE)

    # ------------------------------------------------------------------ #
    def _measure_click(self, wx: float, wy: float) -> None:
        if not self._measure_active:
            self._clear_measure()
            self._measure_anchor = (wx, wy)
            self._measure_active = True
            self._render_measure_line(self._measure_anchor, (wx, wy))
        else:
            self._render_measure_line(self._measure_anchor, (wx, wy))
            self._measure_active = False

    def _render_measure_line(self, p1: tuple, p2: tuple) -> None:
        if self._measure_line_item is not None:
            self._scene.removeItem(self._measure_line_item)
        if self._measure_label_item is not None:
            self._scene.removeItem(self._measure_label_item)

        sp1, sp2 = world_to_scene(*p1), world_to_scene(*p2)
        path = QPainterPath()
        path.moveTo(sp1)
        path.lineTo(sp2)
        line = QtWidgets.QGraphicsPathItem(path)
        pen = QPen(QColor("#f5c542"), 1.8, Qt.DashLine)
        pen.setCosmetic(True)
        line.setPen(pen)
        line.setZValue(97)
        self._scene.addItem(line)
        self._measure_line_item = line

        dist = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
        text = f"{dist:,.2f} {_unit_label(self.project.crs)}"
        label = QtWidgets.QGraphicsSimpleTextItem(text)
        label.setBrush(QColor("#f5c542"))
        font = label.font()
        font.setBold(True)
        font.setPointSize(9)
        label.setFont(font)
        label.setPos(QPointF((sp1.x() + sp2.x()) / 2, (sp1.y() + sp2.y()) / 2))
        label.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        label.setZValue(98)
        self._scene.addItem(label)
        self._measure_label_item = label
        self.status_message.emit(f"Distance: {text}")

    def _clear_measure(self) -> None:
        if self._measure_line_item is not None:
            self._scene.removeItem(self._measure_line_item)
            self._measure_line_item = None
        if self._measure_label_item is not None:
            self._scene.removeItem(self._measure_label_item)
            self._measure_label_item = None
        self._measure_anchor = None
        self._measure_active = False

    # ------------------------------------------------------------------ #
    def _click_blocks_pan(self, pos) -> bool:
        item = self.itemAt(pos)
        return item is not None and bool(
            item.flags() & QtWidgets.QGraphicsItem.ItemIsSelectable)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MiddleButton:
            self._start_pan(event.pos())
            event.accept()
            return
        if self.mode == Mode.NAVIGATE:
            if event.button() == Qt.LeftButton and not self._click_blocks_pan(event.pos()):
                self._start_pan(event.pos())
                event.accept()
                return
            super().mousePressEvent(event)
            return
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        scene_pt = self.mapToScene(event.pos())
        wx, wy = scene_to_world(scene_pt)
        if self.mode == Mode.POINT:
            self.geometry_finished.emit(Point(wx, wy), engine.GEOM_POINT)
            event.accept()
            return
        if self.mode == Mode.MEASURE:
            self._measure_click(wx, wy)
            event.accept()
            return
        self._pending_vertices.append((wx, wy))
        self._update_vertex_preview()
        event.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        if self.mode in (Mode.LIMIT, Mode.POLYGON, Mode.LINE, Mode.VOID) and \
                event.button() == Qt.LeftButton:
            scene_pt = self.mapToScene(event.pos())
            wx, wy = scene_to_world(scene_pt)
            self._pending_vertices.append((wx, wy))
            self._finish_current_shape()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            hbar, vbar = self.horizontalScrollBar(), self.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())
            event.accept()
            return
        if self.mode == Mode.MEASURE and self._measure_active:
            scene_pt = self.mapToScene(event.pos())
            self._render_measure_line(self._measure_anchor, scene_to_world(scene_pt))
        elif self.mode not in (Mode.NAVIGATE, Mode.POINT) and self._pending_vertices:
            scene_pt = self.mapToScene(event.pos())
            self._update_vertex_preview(cursor=scene_to_world(scene_pt))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._panning and event.button() in (Qt.LeftButton, Qt.MiddleButton):
            self._panning = False
            self.setCursor(Qt.ArrowCursor if self.mode == Mode.NAVIGATE
                           else Qt.CrossCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _start_pan(self, pos) -> None:
        self._panning = True
        self._pan_start = pos
        self.setCursor(Qt.ClosedHandCursor)

    def wheelEvent(self, event) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        event.accept()

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self._pending_vertices:
                self._finish_current_shape()
                return
        elif key == Qt.Key_Escape:
            if self.mode == Mode.MEASURE and self._measure_active:
                self._clear_measure()
                self.status_message.emit("Measurement cancelled.")
                return
            if self._pending_vertices:
                self._cancel_current_shape()
                return
            self._scene.clearSelection()
            return
        elif key in (Qt.Key_Delete, Qt.Key_Backspace):
            self._delete_selected()
            return
        super().keyPressEvent(event)

    def _delete_selected(self) -> None:
        for item in self._scene.selectedItems():
            if isinstance(item, BackgroundImageItem):
                self.remove_background_requested.emit(item.bg_ref)
                return
