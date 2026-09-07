"""
scene_items.py
==============
Custom QGraphicsItem subclasses used by the map canvas (ui.canvas).

World <-> scene coordinate convention: scene_x = world_x, scene_y = -world_y.
This keeps world (CRS) coordinates usable directly (no extra scale factor) while
matching Qt's downward-positive scene Y axis to a normal upward-positive map Y axis.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (QPainterPath, QPolygonF, QPen, QBrush, QColor, QPixmap,
                         QImage, QTransform)

import engine


def world_to_scene(x: float, y: float) -> QPointF:
    return QPointF(x, -y)


def scene_to_world(pt: QPointF) -> tuple:
    return (pt.x(), -pt.y())


def ring_to_qpolygon(coords) -> QPolygonF:
    poly = QPolygonF()
    for x, y in coords:
        poly.append(world_to_scene(x, y))
    return poly


def geom_to_qpainterpath(geom) -> QPainterPath:
    """Shapely geometry (Polygon/MultiPolygon/LineString/MultiLineString) -> path."""
    path = QPainterPath()
    gt = geom.geom_type
    if gt == "Polygon":
        _add_polygon(path, geom)
    elif gt == "MultiPolygon":
        for g in geom.geoms:
            _add_polygon(path, g)
    elif gt == "LineString":
        _add_line(path, geom)
    elif gt == "MultiLineString":
        for g in geom.geoms:
            _add_line(path, g)
    return path


def _add_polygon(path: QPainterPath, poly) -> None:
    path.addPolygon(ring_to_qpolygon(poly.exterior.coords))
    for interior in poly.interiors:
        path.addPolygon(ring_to_qpolygon(interior.coords))


def _add_line(path: QPainterPath, line) -> None:
    coords = list(line.coords)
    if not coords:
        return
    poly = ring_to_qpolygon(coords)
    path.moveTo(poly[0])
    for pt in list(poly)[1:]:
        path.lineTo(pt)


def array_to_qpixmap(arr: np.ndarray) -> QPixmap:
    """numpy array (H, W[, 3|4]) -> QPixmap. Non-uint8 arrays are min-max stretched."""
    arr = np.ascontiguousarray(arr)
    if arr.dtype != np.uint8:
        finite = arr[np.isfinite(arr)]
        lo, hi = (float(finite.min()), float(finite.max())) if finite.size else (0.0, 1.0)
        span = (hi - lo) or 1.0
        arr = np.clip((arr - lo) / span * 255.0, 0, 255).astype(np.uint8)
        arr = np.ascontiguousarray(arr)
    if arr.ndim == 2:
        h, w = arr.shape
        qimg = QImage(arr.data, w, h, arr.strides[0], QImage.Format_Grayscale8)
    elif arr.ndim == 3 and arr.shape[2] == 3:
        h, w, _ = arr.shape
        qimg = QImage(arr.data, w, h, arr.strides[0], QImage.Format_RGB888)
    elif arr.ndim == 3 and arr.shape[2] == 4:
        h, w, _ = arr.shape
        qimg = QImage(arr.data, w, h, arr.strides[0], QImage.Format_RGBA8888)
    elif arr.ndim == 3 and arr.shape[2] == 1:
        h, w = arr.shape[0], arr.shape[1]
        qimg = QImage(arr[:, :, 0].copy().data, w, h, w, QImage.Format_Grayscale8)
    else:
        raise ValueError(f"Unsupported background image shape: {arr.shape}")
    return QPixmap.fromImage(qimg.copy())


class BackgroundImageItem(QtWidgets.QGraphicsPixmapItem):
    """A georeferenced background image. Selectable + deletable, never movable."""

    def __init__(self, pixmap: QPixmap, extent: tuple, bg_ref=None, z: float = -100.0):
        super().__init__(pixmap)
        self.bg_ref = bg_ref
        xmin, xmax, ymin, ymax = extent
        w, h = pixmap.width(), pixmap.height()
        sx = (xmax - xmin) / w if w else 1.0
        sy = (ymax - ymin) / h if h else 1.0
        self.setTransform(QTransform().scale(sx, sy))
        top_left = world_to_scene(xmin, ymax)
        self.setPos(top_left)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(z)
        self.setTransformationMode(Qt.SmoothTransformation)

    def paint(self, painter, option, widget=None) -> None:
        opt = QtWidgets.QStyleOptionGraphicsItem(option)
        opt.state &= ~QtWidgets.QStyle.State_Selected  # draw our own selection border
        super().paint(painter, opt, widget)
        if self.isSelected():
            painter.save()
            pen = QPen(QColor("#4f8cff"), 2.0)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.pixmap().rect())
            painter.restore()


class LimitPolygonItem(QtWidgets.QGraphicsPathItem):
    def __init__(self):
        super().__init__()
        pen = QPen(QColor("#2bb3a3"), 2.2)
        pen.setCosmetic(True)
        self.setPen(pen)
        self.setBrush(QBrush(Qt.NoBrush))
        self.setZValue(-10)

    def set_geometry(self, gdf) -> None:
        path = QPainterPath()
        if gdf is not None and not gdf.empty:
            for geom in gdf.geometry:
                if geom is not None and not geom.is_empty:
                    path.addPath(geom_to_qpainterpath(geom))
        self.setPath(path)


class MeshLayerItem(QtWidgets.QGraphicsPathItem):
    def __init__(self):
        super().__init__()
        pen = QPen(QColor("#7d8695"), 0.6)
        pen.setCosmetic(True)
        self.setPen(pen)
        self.setBrush(QBrush(Qt.NoBrush))
        self.setZValue(-50)

    def set_geometry(self, gdf) -> None:
        path = QPainterPath()
        if gdf is not None and not gdf.empty:
            for geom in gdf.geometry:
                if geom is not None and not geom.is_empty:
                    path.addPath(geom_to_qpainterpath(geom))
        self.setPath(path)


class VoidPolygonItem(QtWidgets.QGraphicsPathItem):
    """A polygon where no mesh cells are generated -- rendered as a hatched,
    semi-transparent overlay so it reads clearly as an excluded area."""

    def __init__(self, void, z: float = 50.0):
        super().__init__()
        self.setZValue(z)
        self.rebuild(void)

    def rebuild(self, void) -> None:
        path = QPainterPath()
        if void.gdf is not None and not void.gdf.empty:
            for geom in void.gdf.geometry:
                if geom is not None and not geom.is_empty:
                    path.addPath(geom_to_qpainterpath(geom))
        self.setPath(path)
        color = QColor(void.color)
        pen = QPen(color, 2.0)
        pen.setCosmetic(True)
        pen.setStyle(Qt.DashLine)
        self.setPen(pen)
        fill = QColor(color)
        fill.setAlpha(90)
        self.setBrush(QBrush(fill, Qt.DiagCrossPattern))
        self.setVisible(void.visible)


class LayerItemGroup(QtWidgets.QGraphicsItemGroup):
    """Renders one engine.RefinementLayer (points / lines / polygons)."""

    def __init__(self, layer, z: float = 0.0):
        super().__init__()
        self.setZValue(z)
        self.rebuild(layer)

    def rebuild(self, layer) -> None:
        for child in list(self.childItems()):
            self.removeFromGroup(child)
            if child.scene() is not None:
                child.scene().removeItem(child)
        color = QColor(layer.color)
        gdf = layer.gdf
        if gdf is not None and not gdf.empty:
            gt = layer.geom_type
            for geom in gdf.geometry:
                if geom is None or geom.is_empty:
                    continue
                if gt == "Point":
                    self.addToGroup(_point_item(geom, color))
                elif gt == "LineString":
                    self.addToGroup(_path_item(geom, color, 2.2))
                else:
                    self.addToGroup(_path_item(geom, color, 1.8))
        self.setVisible(layer.visible)


def _point_item(geom, color: QColor) -> QtWidgets.QGraphicsEllipseItem:
    # Radius is in pixels, not world units (ItemIgnoresTransformations) so the
    # marker stays visible at any zoom level, however large the model extent.
    r = 4.5
    item = QtWidgets.QGraphicsEllipseItem(-r, -r, 2 * r, 2 * r)
    item.setPos(world_to_scene(geom.x, geom.y))
    item.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
    item.setBrush(QBrush(color))
    item.setPen(QPen(QColor("#141720"), 0.8))
    return item


def _path_item(geom, color: QColor, width: float) -> QtWidgets.QGraphicsPathItem:
    item = QtWidgets.QGraphicsPathItem(geom_to_qpainterpath(geom))
    pen = QPen(color, width)
    pen.setCosmetic(True)
    item.setPen(pen)
    item.setBrush(QBrush(Qt.NoBrush))
    return item


def make_feature_preview_item(geom, geom_type: str, color: str):
    """One already-committed feature, drawn immediately while a layer is drawn."""
    qcolor = QColor(color)
    if geom_type == engine.GEOM_POINT:
        return _point_item(geom, qcolor)
    width = 2.2 if geom_type == engine.GEOM_LINE else 1.8
    return _path_item(geom, qcolor, width)
