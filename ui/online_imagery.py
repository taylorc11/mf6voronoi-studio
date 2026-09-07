"""
online_imagery.py
==================
Interactive online satellite/aerial basemap. Lets the user pan and zoom a
free imagery provider (Esri World Imagery or EOX Sentinel-2 Cloudless),
pick an area (the current view, or a drawn rectangle), and save it as a
georeferenced GeoTIFF — reprojected into the project's CRS, or into an
automatically detected UTM zone if the project has none yet.

The resulting GeoTIFF is a normal georeferenced raster (embedded CRS, no
sidecar world file needed), so it can be added immediately as a background
or re-imported later through the regular "Add background image" flow.

No new third-party dependency is introduced: networking uses PyQt5's
QtNetwork (interactive tiles) and the standard library's urllib (bulk
export), image handling uses Pillow/NumPy, and reprojection uses rasterio
— all already required by this application.
"""
from __future__ import annotations

import io
import json
import math
import os
import tempfile
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from PIL import Image

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QThread, QRectF, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

try:
    from version import __version__ as _APP_VERSION
except Exception:
    _APP_VERSION = "2.0"

USER_AGENT = f"mf6VoronoiStudio/{_APP_VERSION} (desktop GIS app)"

TILE_SIZE = 256
EARTH_CIRCUMFERENCE = 2.0 * math.pi * 6378137.0  # Web Mercator sphere, metres
MAX_EXPORT_TILES = 576  # a 24x24 grid -> up to ~6144px/side before reprojection

# Free, no-API-key tile providers. Both are commonly used this way in
# desktop GIS tools; review each provider's terms before commercial /
# redistribution use — this tool is intended for personal & evaluation use.
PROVIDERS = OrderedDict([
    ("Esri World Imagery (satellite)", {
        "url": ("https://server.arcgisonline.com/ArcGIS/rest/services/"
                "World_Imagery/MapServer/tile/{z}/{y}/{x}"),
        "ext": "jpg",
        "max_zoom": 19,
        "attribution": "Imagery: Esri, Maxar, Earthstar Geographics, GIS User Community",
    }),
    ("Sentinel-2 Cloudless 2020 (EOX)", {
        "url": ("https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/"
                "default/g/{z}/{y}/{x}.jpg"),
        "ext": "jpg",
        "max_zoom": 14,
        "attribution": "Sentinel-2 cloudless — contains modified Copernicus "
                       "Sentinel data, EOX IT Services GmbH",
    }),
])


# --------------------------------------------------------------------------- #
#  Web Mercator tile math
# --------------------------------------------------------------------------- #

def lonlat_to_world_px(lon: float, lat: float, zoom: int):
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * TILE_SIZE * n
    lat = max(min(lat, 85.05112878), -85.05112878)
    lat_rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) \
        / 2.0 * TILE_SIZE * n
    return x, y


def world_px_to_lonlat(x: float, y: float, zoom: int):
    n = 2 ** zoom
    lon = x / (TILE_SIZE * n) * 360.0 - 180.0
    y_frac = y / (TILE_SIZE * n)
    lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * y_frac)))
    return lon, math.degrees(lat_rad)


def utm_epsg_for_lonlat(lon: float, lat: float) -> int:
    zone = int((lon + 180.0) / 6.0) % 60 + 1
    return (32600 if lat >= 0 else 32700) + zone


def project_bounds_lonlat(project):
    """Overall (lon_min, lat_min, lon_max, lat_max) of the project's current
    geometry (limit polygon, layers, voids, backgrounds), or None."""
    if project is None or project.crs is None:
        return None
    xs, ys = [], []

    def add(bounds):
        xs.extend([bounds[0], bounds[2]])
        ys.extend([bounds[1], bounds[3]])

    try:
        if project.limit_gdf is not None and not project.limit_gdf.empty:
            add(project.limit_gdf.total_bounds)
        for lyr in project.layers:
            if lyr.gdf is not None and not lyr.gdf.empty:
                add(lyr.gdf.total_bounds)
        for void in project.voids:
            if void.gdf is not None and not void.gdf.empty:
                add(void.gdf.total_bounds)
        for bg in project.backgrounds:
            xmin, xmax, ymin, ymax = bg.extent
            add((xmin, ymin, xmax, ymax))
    except Exception:
        pass
    if not xs:
        return None
    import pyproj
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    transformer = pyproj.Transformer.from_crs(project.crs, "EPSG:4326", always_xy=True)
    lon0, lat0 = transformer.transform(xmin, ymin)
    lon1, lat1 = transformer.transform(xmax, ymax)
    return (min(lon0, lon1), min(lat0, lat1), max(lon0, lon1), max(lat0, lat1))


# --------------------------------------------------------------------------- #
#  Tile fetching (disk-cached, so repeated pans / exports don't re-download)
# --------------------------------------------------------------------------- #

def _tile_cache_dir() -> str:
    d = os.path.join(tempfile.gettempdir(), "mf6voronoi_tile_cache")
    os.makedirs(d, exist_ok=True)
    return d


def _cache_path(provider_key: str, z: int, x: int, y: int, ext: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in provider_key)
    d = os.path.join(_tile_cache_dir(), safe, str(z), str(x))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{y}.{ext}")


def fetch_tile_bytes(provider: dict, provider_key: str, z: int, x: int, y: int,
                      timeout: float = 8.0) -> bytes:
    cpath = _cache_path(provider_key, z, x, y, provider["ext"])
    if os.path.exists(cpath):
        with open(cpath, "rb") as fh:
            return fh.read()
    url = provider["url"].format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    try:
        with open(cpath, "wb") as fh:
            fh.write(data)
    except OSError:
        pass
    return data


# --------------------------------------------------------------------------- #
#  Interactive pan/zoom slippy map with a rectangle "export area" tool
# --------------------------------------------------------------------------- #

class SlippyMapWidget(QtWidgets.QWidget):
    zoom_changed = pyqtSignal()
    selection_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(320, 240)
        self.setCursor(Qt.OpenHandCursor)

        self.provider_key = next(iter(PROVIDERS))
        self.zoom = 3
        self.center_lon = 0.0
        self.center_lat = 20.0

        self.selection_lonlat = None  # (lon_min, lat_min, lon_max, lat_max)

        self._dragging = False
        self._drag_start = None
        self._drag_center0 = None
        self._select_mode = False
        self._selecting = False
        self._select_start_screen = None
        self._select_rect_screen = None

        self._pixmap_cache: "OrderedDict[tuple, QPixmap]" = OrderedDict()
        self._pending: set = set()
        self._nam = QNetworkAccessManager(self)

    # -- provider / zoom limits ----------------------------------------- #
    def max_zoom(self) -> int:
        return PROVIDERS[self.provider_key]["max_zoom"]

    def set_provider(self, key: str):
        self.provider_key = key
        self.zoom = min(self.zoom, self.max_zoom())
        self.update()
        self.zoom_changed.emit()

    def set_select_mode(self, on: bool):
        self._select_mode = bool(on)
        self.setCursor(Qt.CrossCursor if on else Qt.OpenHandCursor)

    def clear_selection(self):
        self.selection_lonlat = None
        self.update()
        self.selection_changed.emit()

    # -- geographic queries ----------------------------------------------#
    def current_view_bbox(self):
        w, h = max(self.width(), 1), max(self.height(), 1)
        cx, cy = lonlat_to_world_px(self.center_lon, self.center_lat, self.zoom)
        left, top = cx - w / 2.0, cy - h / 2.0
        lon0, lat0 = world_px_to_lonlat(left, top + h, self.zoom)
        lon1, lat1 = world_px_to_lonlat(left + w, top, self.zoom)
        return (min(lon0, lon1), min(lat0, lat1), max(lon0, lon1), max(lat0, lat1))

    def export_bbox(self):
        return self.selection_lonlat or self.current_view_bbox()

    def fit_to_bbox(self, lon_min, lat_min, lon_max, lat_max, set_selection=False):
        lon_min, lon_max = sorted((lon_min, lon_max))
        lat_min, lat_max = sorted((lat_min, lat_max))
        pad_lon = (lon_max - lon_min) * 0.05 or 0.05
        pad_lat = (lat_max - lat_min) * 0.05 or 0.05
        vlon_min, vlon_max = lon_min - pad_lon, lon_max + pad_lon
        vlat_min, vlat_max = lat_min - pad_lat, lat_max + pad_lat
        self.center_lon = (vlon_min + vlon_max) / 2.0
        self.center_lat = (vlat_min + vlat_max) / 2.0
        w, h = max(self.width(), 1), max(self.height(), 1)
        best = 2
        for z in range(2, self.max_zoom() + 1):
            x0, y0 = lonlat_to_world_px(vlon_min, vlat_max, z)
            x1, y1 = lonlat_to_world_px(vlon_max, vlat_min, z)
            if (x1 - x0) <= w and (y1 - y0) <= h:
                best = z
            else:
                break
        self.zoom = best
        if set_selection:
            self.selection_lonlat = (lon_min, lat_min, lon_max, lat_max)
        self.update()
        self.zoom_changed.emit()
        if set_selection:
            self.selection_changed.emit()

    # -- painting ---------------------------------------------------------#
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#11141a"))
        w, h = self.width(), self.height()
        z = self.zoom
        n = 2 ** z
        cx, cy = lonlat_to_world_px(self.center_lon, self.center_lat, z)
        left, top = cx - w / 2.0, cy - h / 2.0

        tx0 = int(math.floor(left / TILE_SIZE))
        ty0 = int(math.floor(top / TILE_SIZE))
        tx1 = int(math.floor((left + w) / TILE_SIZE))
        ty1 = int(math.floor((top + h) / TILE_SIZE))

        for ty in range(ty0, ty1 + 1):
            if ty < 0 or ty >= n:
                continue
            for tx in range(tx0, tx1 + 1):
                txw = tx % n
                key = (self.provider_key, z, txw, ty)
                sx = tx * TILE_SIZE - left
                sy = ty * TILE_SIZE - top
                pix = self._pixmap_cache.get(key)
                if pix is not None:
                    p.drawPixmap(int(round(sx)), int(round(sy)), pix)
                else:
                    p.fillRect(QRectF(sx, sy, TILE_SIZE, TILE_SIZE), QColor("#1c2029"))
                    self._request_tile(key)

        if self.selection_lonlat:
            lon_min, lat_min, lon_max, lat_max = self.selection_lonlat
            x0, y0 = lonlat_to_world_px(lon_min, lat_max, z)
            x1, y1 = lonlat_to_world_px(lon_max, lat_min, z)
            rect = QRectF(x0 - left, y0 - top, x1 - x0, y1 - y0)
            pen = QPen(QColor("#ffd54f")); pen.setWidth(2)
            p.setPen(pen)
            p.setBrush(QBrush(QColor(255, 213, 79, 40)))
            p.drawRect(rect)

        if self._selecting and self._select_rect_screen is not None:
            pen = QPen(QColor("#4f8cff")); pen.setWidth(2); pen.setStyle(Qt.DashLine)
            p.setPen(pen)
            p.setBrush(QBrush(QColor(79, 140, 255, 40)))
            p.drawRect(self._select_rect_screen)
        p.end()

    # -- tile loading -------------------------------------------------- #
    def _request_tile(self, key):
        if key in self._pending:
            return
        provider_key, z, x, y = key
        provider = PROVIDERS[provider_key]
        cpath = _cache_path(provider_key, z, x, y, provider["ext"])
        if os.path.exists(cpath):
            pix = QPixmap(cpath)
            if not pix.isNull():
                self._store_pixmap(key, pix)
                return
        self._pending.add(key)
        url = provider["url"].format(z=z, x=x, y=y)
        req = QNetworkRequest(QtCore.QUrl(url))
        req.setRawHeader(b"User-Agent", USER_AGENT.encode("utf-8"))
        reply = self._nam.get(req)
        reply.finished.connect(lambda r=reply, k=key, cp=cpath: self._on_tile_reply(r, k, cp))

    def _on_tile_reply(self, reply, key, cache_path):
        self._pending.discard(key)
        try:
            if reply.error() == QNetworkReply.NoError:
                data = bytes(reply.readAll())
                pix = QPixmap()
                if pix.loadFromData(data):
                    self._store_pixmap(key, pix)
                    try:
                        with open(cache_path, "wb") as fh:
                            fh.write(data)
                    except OSError:
                        pass
                    self.update()
        finally:
            reply.deleteLater()

    def _store_pixmap(self, key, pix):
        self._pixmap_cache[key] = pix
        self._pixmap_cache.move_to_end(key)
        while len(self._pixmap_cache) > 600:
            self._pixmap_cache.popitem(last=False)

    # -- mouse / wheel interaction --------------------------------------- #
    def mousePressEvent(self, ev):
        if self._select_mode and ev.button() == Qt.LeftButton:
            self._selecting = True
            self._select_start_screen = ev.pos()
            self._select_rect_screen = QRectF(ev.pos(), ev.pos())
            self.update()
            return
        if ev.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start = ev.pos()
            self._drag_center0 = lonlat_to_world_px(self.center_lon, self.center_lat, self.zoom)
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, ev):
        if self._selecting:
            self._select_rect_screen = QRectF(self._select_start_screen, ev.pos()).normalized()
            self.update()
            return
        if self._dragging:
            dx = ev.pos().x() - self._drag_start.x()
            dy = ev.pos().y() - self._drag_start.y()
            cx0, cy0 = self._drag_center0
            self.center_lon, self.center_lat = world_px_to_lonlat(
                cx0 - dx, cy0 - dy, self.zoom)
            self.update()

    def mouseReleaseEvent(self, ev):
        if self._selecting and ev.button() == Qt.LeftButton:
            self._selecting = False
            rect = self._select_rect_screen
            self._select_rect_screen = None
            if rect is not None and rect.width() > 4 and rect.height() > 4:
                w, h = self.width(), self.height()
                z = self.zoom
                cx, cy = lonlat_to_world_px(self.center_lon, self.center_lat, z)
                left, top = cx - w / 2.0, cy - h / 2.0
                lon0, lat0 = world_px_to_lonlat(left + rect.left(), top + rect.bottom(), z)
                lon1, lat1 = world_px_to_lonlat(left + rect.right(), top + rect.top(), z)
                self.selection_lonlat = (min(lon0, lon1), min(lat0, lat1),
                                          max(lon0, lon1), max(lat0, lat1))
                self.selection_changed.emit()
            self.set_select_mode(False)
            self.update()
            return
        if self._dragging and ev.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(Qt.CrossCursor if self._select_mode else Qt.OpenHandCursor)

    def wheelEvent(self, ev):
        delta = ev.angleDelta().y()
        if delta == 0:
            return
        old_zoom = self.zoom
        new_zoom = max(2, min(self.max_zoom(), old_zoom + (1 if delta > 0 else -1)))
        if new_zoom == old_zoom:
            return
        w, h = self.width(), self.height()
        pos = ev.pos()
        cx, cy = lonlat_to_world_px(self.center_lon, self.center_lat, old_zoom)
        left, top = cx - w / 2.0, cy - h / 2.0
        lon, lat = world_px_to_lonlat(left + pos.x(), top + pos.y(), old_zoom)
        self.zoom = new_zoom
        npx, npy = lonlat_to_world_px(lon, lat, new_zoom)
        self.center_lon, self.center_lat = world_px_to_lonlat(
            npx - (pos.x() - w / 2.0), npy - (pos.y() - h / 2.0), new_zoom)
        self.update()
        self.zoom_changed.emit()


# --------------------------------------------------------------------------- #
#  Background workers (network / CPU work off the UI thread)
# --------------------------------------------------------------------------- #

class GeocodeThread(QThread):
    found = pyqtSignal(float, float, object, str)  # lat, lon, bbox-or-None, label
    failed = pyqtSignal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        try:
            url = ("https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
                   + urllib.parse.quote(self.query))
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=10) as resp:
                results = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            self.failed.emit(str(e))
            return
        if not results:
            self.failed.emit("No results found.")
            return
        r = results[0]
        bbox = r.get("boundingbox")
        bbox = tuple(float(v) for v in bbox) if bbox else None
        self.found.emit(float(r["lat"]), float(r["lon"]), bbox,
                         r.get("display_name", self.query))


class ImageryExportWorker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str)
    finished_ok = pyqtSignal(str, str, bool)  # out_path, dst_crs_wkt, used_auto_utm
    failed = pyqtSignal(str)

    def __init__(self, bbox_lonlat, zoom, provider_key, target_crs, out_path):
        super().__init__()
        self.bbox = bbox_lonlat
        self.zoom = zoom
        self.provider_key = provider_key
        self.target_crs = target_crs
        self.out_path = out_path

    def run(self):
        try:
            self._run()
        except Exception:
            self.failed.emit(traceback.format_exc())

    def _run(self):
        import rasterio
        from rasterio.crs import CRS as RioCRS
        from rasterio.transform import from_bounds
        from rasterio.warp import Resampling, calculate_default_transform, reproject

        lon_min, lat_min, lon_max, lat_max = self.bbox
        z = self.zoom
        provider = PROVIDERS[self.provider_key]
        n = 2 ** z

        x0, y0 = lonlat_to_world_px(lon_min, lat_max, z)  # top-left
        x1, y1 = lonlat_to_world_px(lon_max, lat_min, z)  # bottom-right
        tx0, ty0 = int(math.floor(x0 / TILE_SIZE)), int(math.floor(y0 / TILE_SIZE))
        tx1 = int(math.floor((x1 - 1) / TILE_SIZE))
        ty1 = int(math.floor((y1 - 1) / TILE_SIZE))
        ty0, ty1 = max(0, ty0), min(n - 1, ty1)
        n_tiles_x = tx1 - tx0 + 1
        n_tiles_y = ty1 - ty0 + 1
        total = n_tiles_x * n_tiles_y

        if total <= 0:
            self.failed.emit("Selected area is empty.")
            return
        if total > MAX_EXPORT_TILES:
            self.failed.emit(
                f"That area needs {total} tiles at zoom {z} (limit "
                f"{MAX_EXPORT_TILES}). Zoom in or draw a smaller area.")
            return

        big = np.zeros((n_tiles_y * TILE_SIZE, n_tiles_x * TILE_SIZE, 3), dtype=np.uint8)
        done = 0
        failures = 0
        self.progress.emit(0, total)

        def fetch_one(tx, ty):
            txw = tx % n
            return tx, ty, fetch_tile_bytes(provider, self.provider_key, z, txw, ty)

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(fetch_one, tx, ty)
                       for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)]
            for fut in as_completed(futures):
                try:
                    tx, ty, data = fut.result()
                    img = Image.open(io.BytesIO(data)).convert("RGB")
                    arr = np.asarray(img)
                    ox, oy = (tx - tx0) * TILE_SIZE, (ty - ty0) * TILE_SIZE
                    big[oy:oy + TILE_SIZE, ox:ox + TILE_SIZE, :] = arr
                except Exception as e:
                    failures += 1
                    self.log.emit(f"Tile failed: {e}")
                done += 1
                self.progress.emit(done, total)

        if failures > total * 0.5:
            self.failed.emit("Too many tiles failed to download — check your "
                             "internet connection and try again.")
            return

        meters_per_px = EARTH_CIRCUMFERENCE / (TILE_SIZE * n)
        left_m = tx0 * TILE_SIZE * meters_per_px - EARTH_CIRCUMFERENCE / 2.0
        top_m = EARTH_CIRCUMFERENCE / 2.0 - ty0 * TILE_SIZE * meters_per_px
        right_m = left_m + n_tiles_x * TILE_SIZE * meters_per_px
        bottom_m = top_m - n_tiles_y * TILE_SIZE * meters_per_px

        src_crs = RioCRS.from_epsg(3857)
        src_transform = from_bounds(left_m, bottom_m, right_m, top_m,
                                     n_tiles_x * TILE_SIZE, n_tiles_y * TILE_SIZE)

        used_auto_utm = False
        if self.target_crs is not None:
            dst_crs = RioCRS.from_wkt(self.target_crs.to_wkt())
        else:
            dst_crs = RioCRS.from_epsg(utm_epsg_for_lonlat(
                (lon_min + lon_max) / 2.0, (lat_min + lat_max) / 2.0))
            used_auto_utm = True

        self.log.emit("Reprojecting…")
        dst_transform, dst_w, dst_h = calculate_default_transform(
            src_crs, dst_crs, n_tiles_x * TILE_SIZE, n_tiles_y * TILE_SIZE,
            left=left_m, bottom=bottom_m, right=right_m, top=top_m)

        src_bands = np.transpose(big, (2, 0, 1))
        dst_bands = np.zeros((3, dst_h, dst_w), dtype=np.uint8)
        for i in range(3):
            reproject(
                source=src_bands[i], destination=dst_bands[i],
                src_transform=src_transform, src_crs=src_crs,
                dst_transform=dst_transform, dst_crs=dst_crs,
                resampling=Resampling.bilinear)

        with rasterio.open(
                self.out_path, "w", driver="GTiff",
                height=dst_h, width=dst_w, count=3, dtype="uint8",
                crs=dst_crs, transform=dst_transform, photometric="RGB") as dst:
            dst.write(dst_bands)

        self.finished_ok.emit(self.out_path, dst_crs.to_wkt(), used_auto_utm)


# --------------------------------------------------------------------------- #
#  The panel embedded as the "Online satellite map" tab
# --------------------------------------------------------------------------- #

class OnlineImageryPanel(QtWidgets.QWidget):
    log_message = pyqtSignal(str)
    background_added = pyqtSignal(str)  # emits the saved GeoTIFF path

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._worker = None
        self._worker_add_to_project = False
        self._geo_thread = None

        root = QtWidgets.QVBoxLayout(self)

        top_row = QtWidgets.QHBoxLayout()
        top_row.addWidget(QtWidgets.QLabel("Provider:"))
        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.addItems(list(PROVIDERS.keys()))
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        top_row.addWidget(self.provider_combo, 1)
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search a place… (e.g. Springfield, IL)")
        self.search_edit.returnPressed.connect(self._on_search)
        top_row.addWidget(self.search_edit, 2)
        btn_search = QtWidgets.QPushButton("Search")
        btn_search.clicked.connect(self._on_search)
        top_row.addWidget(btn_search)
        root.addLayout(top_row)

        self.map = SlippyMapWidget(self)
        self.map.selection_changed.connect(self._update_info)
        self.map.zoom_changed.connect(self._update_info)
        root.addWidget(self.map, 1)

        self.attribution_label = QtWidgets.QLabel()
        self.attribution_label.setWordWrap(True)
        self.attribution_label.setStyleSheet("color:#7d8598; font-size: 10px;")
        root.addWidget(self.attribution_label)

        ctrl_row = QtWidgets.QHBoxLayout()
        btn_zoom_in = QtWidgets.QToolButton()
        btn_zoom_in.setText("+")
        btn_zoom_in.clicked.connect(lambda: self._step_zoom(1))
        btn_zoom_out = QtWidgets.QToolButton()
        btn_zoom_out.setText("−")
        btn_zoom_out.clicked.connect(lambda: self._step_zoom(-1))
        self.btn_select = QtWidgets.QPushButton("Draw export area")
        self.btn_select.setCheckable(True)
        self.btn_select.toggled.connect(self.map.set_select_mode)
        btn_clear_sel = QtWidgets.QPushButton("Clear area")
        btn_clear_sel.clicked.connect(self._clear_selection)
        btn_fit_project = QtWidgets.QPushButton("Fit to project extent")
        btn_fit_project.clicked.connect(lambda: self._fit_to_project())
        ctrl_row.addWidget(btn_zoom_in)
        ctrl_row.addWidget(btn_zoom_out)
        ctrl_row.addWidget(self.btn_select)
        ctrl_row.addWidget(btn_clear_sel)
        ctrl_row.addWidget(btn_fit_project)
        ctrl_row.addStretch(1)
        root.addLayout(ctrl_row)

        self.info_label = QtWidgets.QLabel(" ")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color:#94a0b3;")
        root.addWidget(self.info_label)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_export = QtWidgets.QPushButton("Export GeoTIFF…")
        self.btn_export.setToolTip(
            "Save the imagery as a georeferenced GeoTIFF you can import later "
            "as a background image.")
        self.btn_export.clicked.connect(lambda: self._do_export(add_to_project=False))
        self.btn_add = QtWidgets.QPushButton("Add to project as background…")
        self.btn_add.setObjectName("PillButtonPrimary")
        self.btn_add.clicked.connect(lambda: self._do_export(add_to_project=True))
        btn_row.addWidget(self.btn_export)
        btn_row.addWidget(self.btn_add)
        root.addLayout(btn_row)

        self._on_provider_changed(self.provider_combo.currentText())
        self._fit_to_project(initial=True)
        self._update_info()

    # ------------------------------------------------------------------ #
    def _on_provider_changed(self, key):
        self.map.set_provider(key)
        attrib = PROVIDERS[key]["attribution"]
        self.attribution_label.setText(
            f"{attrib}. Free tiles for personal / evaluation use — check the "
            "provider's terms before commercial or redistributed use.")
        self._update_info()

    def _step_zoom(self, delta):
        self.map.zoom = max(2, min(self.map.max_zoom(), self.map.zoom + delta))
        self.map.update()
        self._update_info()

    def _clear_selection(self):
        self.map.clear_selection()
        self.btn_select.setChecked(False)
        self._update_info()

    def _fit_to_project(self, initial=False):
        bbox = project_bounds_lonlat(self.main_window.project)
        if bbox:
            self.map.fit_to_bbox(*bbox, set_selection=not initial)
        elif not initial:
            self.log_message.emit(
                "No project geometry yet (draw or import a limit polygon "
                "first) — pan/zoom manually or use search.")
        self._update_info()

    def _on_search(self):
        text = self.search_edit.text().strip()
        if not text or self._geo_thread is not None:
            return
        self.log_message.emit(f"Searching for '{text}'…")
        self._geo_thread = GeocodeThread(text)
        self._geo_thread.found.connect(self._on_geocode_found)
        self._geo_thread.failed.connect(self._on_geocode_failed)
        self._geo_thread.finished.connect(self._on_geocode_thread_done)
        self._geo_thread.start()

    def _on_geocode_thread_done(self):
        self._geo_thread = None

    def _on_geocode_found(self, lat, lon, bbox, label):
        if bbox:
            lat0, lat1, lon0, lon1 = bbox
            self.map.fit_to_bbox(lon0, lat0, lon1, lat1)
        else:
            self.map.center_lon, self.map.center_lat = lon, lat
            self.map.zoom = 14
            self.map.update()
        self.log_message.emit(f"Found: {label}")
        self._update_info()

    def _on_geocode_failed(self, msg):
        self.log_message.emit(f"Search failed: {msg}")

    def _update_info(self):
        lon_min, lat_min, lon_max, lat_max = self.map.export_bbox()
        zoom = self.map.zoom
        x0, y0 = lonlat_to_world_px(lon_min, lat_max, zoom)
        x1, y1 = lonlat_to_world_px(lon_max, lat_min, zoom)
        tiles_x = max(1, int(math.ceil(x1 / TILE_SIZE)) - int(math.floor(x0 / TILE_SIZE)))
        tiles_y = max(1, int(math.ceil(y1 / TILE_SIZE)) - int(math.floor(y0 / TILE_SIZE)))
        n_tiles = tiles_x * tiles_y
        mid_lat = (lat_min + lat_max) / 2.0
        meters_per_px = (EARTH_CIRCUMFERENCE / (TILE_SIZE * (2 ** zoom))
                         * math.cos(math.radians(mid_lat)))
        src = "current view" if self.map.selection_lonlat is None else "drawn area"
        ok = n_tiles <= MAX_EXPORT_TILES
        warn = "" if ok else "  ⚠ Too large at this zoom — zoom in or draw a smaller area."
        self.info_label.setText(
            f"Export source: {src}  •  zoom {zoom}  •  ~{meters_per_px:.2f} m/pixel  •  "
            f"{tiles_x}×{tiles_y} tiles ({n_tiles}){warn}")
        self.btn_export.setEnabled(ok and self._worker is None)
        self.btn_add.setEnabled(ok and self._worker is None)

    # ------------------------------------------------------------------ #
    def _do_export(self, add_to_project: bool):
        if self._worker is not None:
            return
        bbox = self.map.export_bbox()
        zoom = self.map.zoom
        provider_key = self.provider_combo.currentText()

        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = self.main_window._save_file(
            "Save georeferenced satellite image", f"satellite_{ts}.tif",
            "GeoTIFF (*.tif)")
        if not out_path:
            return
        if not out_path.lower().endswith((".tif", ".tiff")):
            out_path += ".tif"

        target_crs = self.main_window.project.crs

        self.progress.setVisible(True)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self._worker_add_to_project = add_to_project
        self._update_info()
        self.log_message.emit(f"Downloading imagery ({provider_key}, zoom {zoom})…")

        self._worker = ImageryExportWorker(bbox, zoom, provider_key, target_crs, out_path)
        self._worker.progress.connect(self._on_export_progress)
        self._worker.log.connect(self.log_message.emit)
        self._worker.finished_ok.connect(self._on_export_done)
        self._worker.failed.connect(self._on_export_failed)
        self._worker.finished.connect(self._on_export_thread_done)
        self._worker.start()

    def _on_export_progress(self, done, total):
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(done)

    def _on_export_thread_done(self):
        self._worker = None
        self.progress.setVisible(False)
        self._update_info()

    def _on_export_done(self, path, crs_wkt, used_auto_utm):
        self.log_message.emit(f"Saved georeferenced image to {os.path.basename(path)}.")
        if used_auto_utm and self.main_window.project.crs is None:
            import pyproj
            crs = pyproj.CRS.from_wkt(crs_wkt)
            resp = QtWidgets.QMessageBox.question(
                self, "Set project CRS",
                "The project has no coordinate system yet. Use the imagery's "
                f"automatically detected UTM zone ({crs.name}) as the project "
                "CRS?\n\nYou can change this later from the CRS panel.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if resp == QtWidgets.QMessageBox.Yes:
                self.main_window.project.set_crs(crs)
                self.main_window._update_crs_label()
                self.main_window._mark_dirty()
                self.log_message.emit(f"Project CRS set to {crs.name}.")
        if self._worker_add_to_project:
            self.background_added.emit(path)

    def _on_export_failed(self, msg):
        QtWidgets.QMessageBox.warning(self, "Online imagery", msg)
