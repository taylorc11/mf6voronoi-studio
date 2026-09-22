"""
engine.py
=========
Headless backend for the mf6Voronoi GUI.

Contains all logic that talks to the ``mf6Voronoi`` package and to geospatial
libraries.  Has no GUI dependency, so it can be unit-tested and scripted alone.
"""

from __future__ import annotations

import os
import sys


def _sanitize_path_env() -> None:
    """Drop PATH entries that don't resolve to a readable directory.

    Some Windows machines end up with a broken/protected entry in the system
    PATH (observed: a literal ``...\\config\\systemprofile\\...\\WindowsApps``
    path). GDAL/PROJ fall back to scanning PATH when they can't find their
    bundled data directory (which happens in PyInstaller-frozen builds, where
    a module's ``__file__`` isn't a real filesystem path), and that scan can
    raise ``PermissionError`` on such an entry instead of skipping it. Doing
    this once, before any geospatial import, prevents that crash regardless
    of which library/call ends up walking PATH.
    """
    parts = os.environ.get("PATH", "").split(os.pathsep)
    keep = [p for p in parts if p and os.path.isdir(p)]
    os.environ["PATH"] = os.pathsep.join(keep)


def _newest_proj_dir(candidate_dirs) -> Optional[str]:
    """Of the given directories, return the one whose ``proj.db`` reports the
    highest ``DATABASE.LAYOUT.VERSION`` (or None if none are readable).

    pyproj and rasterio/GDAL each vendor their own copy of PROJ's data, and
    the two copies are not always the same version — the frozen build was
    observed shipping pyproj's proj.db at layout 1.4 alongside rasterio's at
    layout 1.6. Forcing everything onto the *older* one broke any code path
    that goes through rasterio's (newer, stricter) compiled PROJ core with
    ``rasterio.errors.CRSError: ... DATABASE.LAYOUT.VERSION.MINOR = 4 whereas
    a number >= 6 is expected``. A newer proj.db read by an older-but-still
    modern PROJ core works fine (verified against pyproj 3.7.2 / PROJ 9.5.1
    reading rasterio's PROJ-9.7.1-vintage database), so picking the newest
    available copy — whichever package happens to carry it — satisfies both.
    """
    import sqlite3

    best_dir, best_version = None, (-1, -1)
    for d in candidate_dirs:
        db_path = os.path.join(d, "proj.db")
        if not os.path.isfile(db_path):
            continue
        try:
            con = sqlite3.connect(db_path)
            try:
                cur = con.execute(
                    "SELECT key, value FROM metadata WHERE key IN "
                    "('DATABASE.LAYOUT.VERSION.MAJOR', "
                    "'DATABASE.LAYOUT.VERSION.MINOR')")
                vals = dict(cur.fetchall())
            finally:
                con.close()
            version = (int(vals.get("DATABASE.LAYOUT.VERSION.MAJOR", 0)),
                       int(vals.get("DATABASE.LAYOUT.VERSION.MINOR", 0)))
        except Exception:
            continue
        if version > best_version:
            best_dir, best_version = d, version
    return best_dir


def _fix_frozen_geo_env() -> None:
    """In a frozen/compiled build (PyInstaller or Nuitka), point PROJ/GDAL
    straight at their bundled data directories instead of letting them try
    (and fail) to locate that data relative to their own ``__file__``.

    These are forced (not merely defaulted) because a stray PROJ_DATA/
    GDAL_DATA already present in the environment — left behind by another
    GIS install (QGIS, ArcGIS, OSGeo4W, ...) — would otherwise take priority
    over our bundled, version-matched copy and risk a data/library mismatch.
    """
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)  # PyInstaller's extraction dir
    if meipass:
        candidates.append(meipass)
    # Nuitka standalone/onefile (and PyInstaller too) set sys.frozen = True;
    # Nuitka also injects a "__compiled__" global into every module it
    # compiles. Either way, bundled packages sit next to the executable.
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        candidates.append(os.path.dirname(sys.executable))
    if not candidates:
        return

    for base in candidates:
        proj_dir = _newest_proj_dir([
            os.path.join(base, "pyproj", "proj_dir", "share", "proj"),
            os.path.join(base, "rasterio", "proj_data"),
            os.path.join(base, "fiona", "proj_data"),
            os.path.join(base, "pyogrio", "proj_data"),
        ])
        if proj_dir:
            os.environ["PROJ_DATA"] = proj_dir
            os.environ["PROJ_LIB"] = proj_dir
            break

    for base in candidates:
        found = False
        for pkg in ("fiona", "rasterio", "pyogrio"):
            gdal_dir = os.path.join(base, pkg, "gdal_data")
            if os.path.isdir(gdal_dir):
                os.environ["GDAL_DATA"] = gdal_dir
                found = True
                break
        if found:
            break


_sanitize_path_env()
_fix_frozen_geo_env()

# Keep ``import mf6Voronoi`` light: stub pyvista/VTK if not installed.
import mf6voronoi_bootstrap  # noqa: F401

import io
import json
import shutil
import tempfile
import contextlib
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
import pyproj


# --------------------------------------------------------------------------- #
#  Constants
# --------------------------------------------------------------------------- #

_METRE_ALIASES = {"metre", "meter", "metres", "meters", "m"}
_FOOT_ALIASES = {
    "foot", "feet", "ft",
    "us survey foot", "foot_us", "us_survey_foot",
    "foot us", "ussurveyfoot", "foot (international)",
    "international foot",
}

GEOM_POINT = "Point"
GEOM_LINE = "LineString"
GEOM_POLYGON = "Polygon"

LAYER_COLORS = [
    "#e6194B", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
    "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990",
]


# --------------------------------------------------------------------------- #
#  Data classes
# --------------------------------------------------------------------------- #

@dataclass
class RefinementLayer:
    """A single refinement feature-set (points, polylines or polygons)."""
    name: str
    gdf: gpd.GeoDataFrame
    ref: float
    color: str = "#4363d8"
    visible: bool = True
    top_raster: Optional[str] = None
    botm_raster: Optional[str] = None

    @property
    def geom_type(self) -> str:
        if self.gdf is None or self.gdf.empty:
            return "Empty"
        gt = self.gdf.geom_type.iloc[0]
        return gt.replace("Multi", "")

    @property
    def feature_count(self) -> int:
        return 0 if self.gdf is None else len(self.gdf)


@dataclass
class VoidPolygon:
    """A polygon inside the model limit where no mesh cells are generated
    (e.g. a lake or an area to exclude from the active model domain)."""
    name: str
    gdf: gpd.GeoDataFrame
    color: str = "#ef5350"
    visible: bool = True

    @property
    def feature_count(self) -> int:
        return 0 if self.gdf is None else len(self.gdf)


@dataclass
class BackgroundImage:
    path: str
    image: np.ndarray
    extent: tuple
    crs: Optional[pyproj.CRS] = None
    name: str = ""
    visible: bool = True

    def __post_init__(self):
        if not self.name:
            self.name = os.path.basename(self.path)


@dataclass
class MeshResult:
    gdf: gpd.GeoDataFrame
    disv: dict = field(default_factory=dict)
    shp_path: Optional[str] = None


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

def crs_length_unit(crs: pyproj.CRS) -> str:
    if crs is None:
        return "unknown"
    try:
        unit = crs.axis_info[0].unit_name.lower().strip()
    except Exception:
        return "unknown"
    if unit in _METRE_ALIASES:
        return "meter"
    if unit in _FOOT_ALIASES or "foot" in unit or "feet" in unit:
        return "foot"
    return unit


def crs_is_valid_for_meshing(crs: pyproj.CRS) -> bool:
    if crs is None:
        return False
    if crs.is_geographic:
        return False
    return crs_length_unit(crs) in ("meter", "foot")


def _explode_singleparts(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    exploded = gdf.explode(index_parts=False, ignore_index=True)
    exploded = exploded[~exploded.geometry.is_empty & exploded.geometry.notna()]
    return exploded.reset_index(drop=True)


# --------------------------------------------------------------------------- #
#  Main project object
# --------------------------------------------------------------------------- #

class MeshProject:
    PROJECT_VERSION = 3

    def __init__(self) -> None:
        self.crs: Optional[pyproj.CRS] = None
        self.limit_gdf: Optional[gpd.GeoDataFrame] = None
        self.layers: list[RefinementLayer] = []
        self.voids: list[VoidPolygon] = []
        self.backgrounds: list[BackgroundImage] = []
        self.result: Optional[MeshResult] = None
        self.mesh_name: str = "voronoiModel"
        self.mesh_params: dict = {
            "max_ref": 200.0,
            "multiplier": 1.3,
            "overlapping": True,
            "quality": 0.0,
        }

    # ------------------------------------------------------------------ #
    def set_crs(self, crs) -> None:
        self.crs = pyproj.CRS.from_user_input(crs)

    def crs_summary(self) -> str:
        if self.crs is None:
            return "No CRS defined"
        unit = crs_length_unit(self.crs)
        try:
            epsg = self.crs.to_epsg()
        except Exception:
            epsg = None
        name = self.crs.name
        tag = f"EPSG:{epsg}" if epsg else "custom"
        return f"{name} ({tag}) — unit: {unit}"

    def validate(self) -> tuple[bool, list[str]]:
        problems: list[str] = []
        if self.crs is None:
            problems.append("No coordinate reference system (CRS) has been set.")
        elif not crs_is_valid_for_meshing(self.crs):
            if self.crs.is_geographic:
                problems.append(
                    "CRS is geographic (degrees). A projected CRS in metres or "
                    "feet is required.")
            else:
                problems.append(
                    f"CRS length unit '{crs_length_unit(self.crs)}' is not "
                    "supported. Use metres or feet.")
        if self.limit_gdf is None or self.limit_gdf.empty:
            problems.append("No model limit polygon has been defined.")
        elif len(self.limit_gdf) != 1:
            problems.append("The model limit must be exactly one single polygon.")
        elif self.limit_gdf.geom_type.iloc[0] not in ("Polygon",):
            problems.append("The model limit layer must be a single Polygon.")
        if not self.layers:
            problems.append("Add at least one refinement layer (point, line or polygon).")
        for lyr in self.layers:
            if lyr.gdf.crs is not None and self.crs is not None:
                if not lyr.gdf.crs.equals(self.crs):
                    problems.append(
                        f"Layer '{lyr.name}' has a different CRS than the project.")
        for void in self.voids:
            if void.gdf.crs is not None and self.crs is not None:
                if not void.gdf.crs.equals(self.crs):
                    problems.append(
                        f"Void polygon '{void.name}' has a different CRS than "
                        "the project.")
        return (len(problems) == 0, problems)

    # ------------------------------------------------------------------ #
    def set_limit_from_gdf(self, gdf: gpd.GeoDataFrame) -> None:
        gdf = gdf[gdf.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
        if gdf.empty:
            raise ValueError("The limit layer contains no polygon geometry.")
        geom = unary_union(gdf.geometry.values)
        if geom.geom_type == "MultiPolygon":
            geom = max(geom.geoms, key=lambda g: g.area)
        crs = gdf.crs if gdf.crs is not None else self.crs
        self.limit_gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[geom], crs=crs)
        if crs is not None and self.crs is None:
            self.crs = pyproj.CRS.from_user_input(crs)

    def load_limit_shapefile(self, path: str) -> None:
        gdf = gpd.read_file(path)
        if gdf.crs is not None and self.crs is None:
            self.crs = gdf.crs
        self.set_limit_from_gdf(gdf)

    # ------------------------------------------------------------------ #
    def _next_color(self) -> str:
        return LAYER_COLORS[len(self.layers) % len(LAYER_COLORS)]

    def add_layer_from_gdf(self, name: str, gdf: gpd.GeoDataFrame,
                           ref: float) -> RefinementLayer:
        gdf = _explode_singleparts(gdf)
        if gdf.empty:
            raise ValueError(f"Layer '{name}' has no valid geometry.")
        if gdf.crs is None and self.crs is not None:
            gdf = gdf.set_crs(self.crs, allow_override=True)
        layer = RefinementLayer(name=name, gdf=gdf, ref=float(ref),
                                color=self._next_color())
        self.layers.append(layer)
        return layer

    def load_layer_shapefile(self, path: str, ref: float,
                             name: Optional[str] = None) -> RefinementLayer:
        gdf = gpd.read_file(path)
        if self.crs is None and gdf.crs is not None:
            self.crs = gdf.crs
        if name is None:
            name = os.path.splitext(os.path.basename(path))[0]
        return self.add_layer_from_gdf(name, gdf, ref)

    def remove_layer(self, index: int) -> None:
        if 0 <= index < len(self.layers):
            del self.layers[index]

    # ------------------------------------------------------------------ #
    def add_void_from_gdf(self, name: str, gdf: gpd.GeoDataFrame) -> VoidPolygon:
        gdf = gdf[gdf.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
        gdf = _explode_singleparts(gdf)
        if gdf.empty:
            raise ValueError(f"Void polygon '{name}' has no valid geometry.")
        if gdf.crs is None and self.crs is not None:
            gdf = gdf.set_crs(self.crs, allow_override=True)
        void = VoidPolygon(name=name, gdf=gdf)
        self.voids.append(void)
        return void

    def load_void_shapefile(self, path: str,
                            name: Optional[str] = None) -> VoidPolygon:
        gdf = gpd.read_file(path)
        if self.crs is None and gdf.crs is not None:
            self.crs = gdf.crs
        if name is None:
            name = os.path.splitext(os.path.basename(path))[0]
        return self.add_void_from_gdf(name, gdf)

    def remove_void(self, index: int) -> None:
        if 0 <= index < len(self.voids):
            del self.voids[index]

    def _void_union(self):
        geoms = []
        for v in self.voids:
            if v.gdf is not None and not v.gdf.empty:
                geoms.extend(list(v.gdf.geometry))
        if not geoms:
            return None
        return unary_union(geoms)

    def remove_background(self, index: int) -> None:
        if 0 <= index < len(self.backgrounds):
            del self.backgrounds[index]

    def set_layer_ref(self, index: int, ref: float) -> None:
        self.layers[index].ref = float(ref)

    # ------------------------------------------------------------------ #
    def add_background(self, image_path: str,
                       extent: Optional[tuple] = None,
                       world_file: Optional[str] = None) -> BackgroundImage:
        from PIL import Image

        ext = image_path.lower().rsplit(".", 1)[-1]
        crs = None

        if ext in ("tif", "tiff") and extent is None and world_file is None:
            import rasterio
            with rasterio.open(image_path) as src:
                arr = src.read()
                arr = np.transpose(arr, (1, 2, 0))
                if arr.shape[2] == 1:
                    arr = arr[:, :, 0]
                b = src.bounds
                extent = (b.left, b.right, b.bottom, b.top)
                crs = pyproj.CRS.from_user_input(src.crs) if src.crs else None
        else:
            with Image.open(image_path) as pil_img:
                if pil_img.mode not in ("RGB", "L"):
                    pil_img = pil_img.convert("RGBA")
                img = np.asarray(pil_img)
            if world_file is not None:
                extent = self._extent_from_worldfile(world_file, img.shape)
            if extent is None:
                h, w = img.shape[0], img.shape[1]
                extent = (0, w, 0, h)
            arr = img

        bg = BackgroundImage(path=image_path, image=arr, extent=tuple(extent),
                             crs=crs)
        self.backgrounds.append(bg)
        return bg

    @staticmethod
    def _extent_from_worldfile(world_file: str, shape) -> tuple:
        vals = [float(v) for v in open(world_file).read().split()]
        a, d, b, e, c, f = vals[:6]
        h, w = shape[0], shape[1]
        left = c - a / 2.0
        top = f - e / 2.0
        right = left + w * a
        bottom = top + h * e
        ymin, ymax = sorted((bottom, top))
        return (left, right, ymin, ymax)

    # ------------------------------------------------------------------ #
    def build_mesh(self, max_ref: float, multiplier: float,
                   overlapping: bool = True,
                   quality_threshold: float = 0.0,
                   log_cb: Optional[Callable[[str], None]] = None) -> MeshResult:
        ok, problems = self.validate()
        if not ok:
            raise ValueError("Cannot build mesh:\n- " + "\n- ".join(problems))

        from mf6Voronoi.geoVoronoi import createVoronoi
        from mf6Voronoi.utils import getVoronoiAsShp

        def log(msg: str) -> None:
            if log_cb:
                log_cb(msg)

        void_union = self._void_union()

        # mf6Voronoi silently drops ALL refinement points for a layer whose
        # buffer(ref) doesn't fit entirely inside the model limit -- this is
        # its own internal safety check (processVertexFilterCloseLimit), not
        # something we can pass a flag to disable. It bites hard on a very
        # common real case: a boundary-condition line (e.g. a GHB) that
        # legitimately runs close to the model edge, closer than its own
        # refinement size -- every single point along it then fails the
        # check and the layer gets zero refinement, with no warning at all.
        # Work around it by meshing against a temporarily expanded limit
        # (roomy enough for every layer's own ref), then clipping the result
        # back down to the real limit afterward.
        all_refs = [lyr.ref for lyr in self.layers]
        void_ref = min(all_refs, default=max_ref / 4) if void_union is not None else None
        margin = max(all_refs + ([void_ref] if void_ref is not None else []) + [0.0])
        true_limit_geom = self.limit_gdf.geometry.iloc[0]
        mesh_limit_geom = true_limit_geom.buffer(margin) if margin > 0 else true_limit_geom

        tmp = tempfile.mkdtemp(prefix="mf6vor_")
        try:
            limit_path = os.path.join(tmp, "limit.shp")
            limit_for_mesh = gpd.GeoDataFrame({"id": [1]}, geometry=[mesh_limit_geom],
                                              crs=self.crs)
            limit_for_mesh.to_file(limit_path)

            layer_paths = []
            for lyr in self.layers:
                p = os.path.join(tmp, f"{_safe_name(lyr.name)}.shp")
                g = lyr.gdf.copy().set_crs(self.crs, allow_override=True)
                g.to_file(p)
                layer_paths.append((lyr.name, p, lyr.ref))

            # mf6Voronoi has no native concept of a "hole" in the limit
            # polygon: addLimit() only reads the exterior ring, and the DISV
            # export can't represent a cell with an interior ring either. So
            # instead we seed points along each void's boundary (as an
            # ordinary polyline refinement layer) so cells snap cleanly to
            # its edge, then remove/clip cells that fall inside it below.
            if void_union is not None:
                void_polys = [void_union] if void_union.geom_type == "Polygon" \
                    else list(void_union.geoms)
                boundary_geoms = [LineString(vp.exterior.coords) for vp in void_polys]
                void_gdf = gpd.GeoDataFrame(
                    {"id": range(1, len(boundary_geoms) + 1)},
                    geometry=boundary_geoms, crs=self.crs)
                void_layer_path = os.path.join(tmp, "__void_boundary.shp")
                void_gdf.to_file(void_layer_path)
                layer_paths.append(("__void_boundary", void_layer_path, void_ref))
                log(f"Void polygon(s) present: seeding their boundary at "
                    f"{void_ref:g} {crs_length_unit(self.crs)}.")

            # mf6Voronoi >=0.0.38 calls exit() on bad input; that would kill
            # the worker thread silently, so surface it as a normal error.
            with _capture_stdout(log), _exit_as_error():
                vor = createVoronoi(meshName=self.mesh_name, maxRef=max_ref,
                                    multiplier=multiplier, overlapping=overlapping)
                vor.addLimit("limit", limit_path)
                for name, p, ref in layer_paths:
                    vor.addLayer(name, p, ref)
                vor.generateOrgDistVertices()
                vor.createPointCloud()
                vor.generateVoronoi()

                if quality_threshold and quality_threshold > 0:
                    vor.checkVoronoiQuality(threshold=quality_threshold)
                    if vor.modelDis.get("fixPoints"):
                        log(f"Fixing {len(vor.modelDis['fixPoints'])} short edges "
                            "and regenerating…")
                        vor.fixVoronoiShortSides()
                        vor.generateVoronoi()

                out_shp = os.path.join(tmp, f"{self.mesh_name}_voronoi.shp")
                getVoronoiAsShp(vor.modelDis, shapePath=out_shp)

            mesh_gdf = gpd.read_file(out_shp)
            if mesh_gdf.crs is None:
                mesh_gdf = mesh_gdf.set_crs(self.crs, allow_override=True)

            if margin > 0:
                mesh_gdf = self._clip_to_limit(mesh_gdf, true_limit_geom, log)

            if void_union is not None:
                mesh_gdf = self._apply_voids(mesh_gdf, void_union, log)

            mesh_gdf = self._weld_vertices(mesh_gdf, log)

            stable = tempfile.mkdtemp(prefix="mf6vor_mesh_")
            stable_shp = os.path.join(stable, f"{self.mesh_name}_voronoi.shp")
            mesh_gdf.to_file(stable_shp)

            self.result = MeshResult(gdf=mesh_gdf, shp_path=stable_shp)
            log(f"\nMesh complete: {len(mesh_gdf)} cells generated.")
            return self.result
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    @staticmethod
    def _clean_polygon_result(geom):
        """Normalize a boolean-op result to a single hole-free Polygon (or
        None). mf6Voronoi's own DISV export can only represent one simple
        polygon per cell, so any multi-part/holed/degenerate result is
        reduced to its largest, hole-free piece rather than kept exactly."""
        if geom is None or geom.is_empty:
            return None
        if geom.geom_type == "GeometryCollection":
            polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
            if not polys:
                return None
            geom = unary_union(polys)
            if geom.is_empty:
                return None
        if geom.geom_type == "MultiPolygon":
            geom = max(geom.geoms, key=lambda g: g.area)
        if geom.geom_type != "Polygon" or geom.area < 1e-9:
            return None
        if geom.interiors:
            geom = Polygon(geom.exterior.coords)
        return geom

    @classmethod
    def _clip_to_limit(cls, mesh_gdf: gpd.GeoDataFrame, limit_geom,
                       log: Callable[[str], None]) -> gpd.GeoDataFrame:
        """Clip cells (generated against a temporarily expanded limit, see
        build_mesh) back down to the real model limit."""
        keep_geoms = []
        dropped = 0
        for geom in mesh_gdf.geometry:
            if geom is None or geom.is_empty:
                continue
            clipped = cls._clean_polygon_result(geom.intersection(limit_geom))
            if clipped is None:
                dropped += 1
                continue
            keep_geoms.append(clipped)
        if dropped:
            log(f"Clipped mesh to the model limit ({dropped} sliver/empty "
                "cell(s) removed).")
        return gpd.GeoDataFrame({"id": range(len(keep_geoms))},
                                geometry=keep_geoms, crs=mesh_gdf.crs)

    @classmethod
    def _apply_voids(cls, mesh_gdf: gpd.GeoDataFrame, void_union,
                     log: Callable[[str], None]) -> gpd.GeoDataFrame:
        """Drop cells that fall inside a void polygon; clip cells that only
        partially overlap one."""
        keep_geoms = []
        removed = 0
        clipped = 0
        for geom in mesh_gdf.geometry:
            if geom is None or geom.is_empty:
                continue
            if not geom.intersects(void_union):
                keep_geoms.append(geom)
                continue
            # Always clip via difference (never drop a straddling cell
            # outright by centroid) so the portion of the cell outside the
            # void is never silently lost.
            diff = cls._clean_polygon_result(geom.difference(void_union))
            if diff is None:
                removed += 1
                continue
            if diff.area < geom.area - 1e-6:
                clipped += 1
            keep_geoms.append(diff)
        log(f"Void polygon(s) applied: {removed} cell(s) removed, "
            f"{clipped} cell(s) clipped.")
        return gpd.GeoDataFrame({"id": range(len(keep_geoms))},
                                geometry=keep_geoms, crs=mesh_gdf.crs)

    WELD_TOL = 0.01  # CRS units (1 cm / 0.01 ft); far below any real cell size

    @classmethod
    def _weld_vertices(cls, mesh_gdf: gpd.GeoDataFrame,
                       log: Callable[[str], None]) -> gpd.GeoDataFrame:
        """Merge vertices closer than WELD_TOL across the whole mesh.

        Clipping leaves edges of a few micrometres. They are valid geometry
        but MODFLOW 6 aborts with "floating invalid" in its DISV connection
        routine on such meshes. Welding is done on shared vertex ids, so
        neighbouring cells stay perfectly conforming."""
        from scipy.spatial import cKDTree
        rings = [np.asarray(g.exterior.coords)[:-1] for g in mesh_gdf.geometry]
        uniq, inv = np.unique(np.vstack(rings), axis=0, return_inverse=True)
        inv = inv.reshape(-1)
        parent = np.arange(len(uniq))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for a, b in cKDTree(uniq).query_pairs(cls.WELD_TOL):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
        rep = np.array([find(i) for i in range(len(uniq))])
        if (rep == np.arange(len(uniq))).all():
            return mesh_gdf

        out, dropped, pos = [], 0, 0
        for r in rings:
            ids = rep[inv[pos:pos + len(r)]]
            pos += len(r)
            ids = [ids[i] for i in range(len(ids)) if ids[i] != ids[i - 1]]
            poly = Polygon(uniq[ids]) if len(set(ids)) >= 3 else None
            if poly is None or not poly.is_valid or poly.area <= 0:
                dropped += 1
                continue
            out.append(poly)
        log(f"Merged {int((rep != np.arange(len(uniq))).sum())} near-duplicate "
            f"vertices (< {cls.WELD_TOL:g} units apart)"
            + (f"; {dropped} collapsed cell(s) removed." if dropped else "."))
        return gpd.GeoDataFrame({"id": range(len(out))}, geometry=out,
                                crs=mesh_gdf.crs)

    # ------------------------------------------------------------------ #
    def export_shapefile(self, path: str) -> None:
        self._require_mesh()
        gdf = self.result.gdf.copy().set_crs(self.crs, allow_override=True)
        gdf.to_file(path)

    def compute_disv(self, log_cb: Optional[Callable[[str], None]] = None) -> dict:
        self._require_mesh()
        from mf6Voronoi.meshProperties import meshShape
        with _capture_stdout(log_cb or (lambda s: None)):
            ms = meshShape(self.result.shp_path)
            disv = ms.get_gridprops_disv()
        self.result.disv = disv
        return disv

    def export_disv_json(self, path: str,
                         log_cb: Optional[Callable[[str], None]] = None) -> None:
        disv = self.result.disv if (self.result and self.result.disv) \
            else self.compute_disv(log_cb)
        with open(path, "w") as fh:
            json.dump(disv, fh)

    # ------------------------------------------------------------------ #
    def cell_centroids(self,
                       log_cb: Optional[Callable[[str], None]] = None
                       ) -> np.ndarray:
        disv = self.result.disv if (self.result and self.result.disv) \
            else self.compute_disv(log_cb)
        cents = disv.get("centroids")
        if cents:
            return np.asarray(cents, dtype=float)
        g = self.result.gdf.geometry
        return np.column_stack([g.centroid.x.values, g.centroid.y.values])

    def sample_raster_at_centroids(self, raster_path: str,
                                   log_cb: Optional[Callable[[str], None]] = None
                                   ) -> np.ndarray:
        import rasterio

        def log(msg):
            if log_cb:
                log_cb(msg)

        pts = self.cell_centroids(log_cb)
        with rasterio.open(raster_path) as src:
            try:
                if src.crs is not None and self.crs is not None:
                    if not pyproj.CRS.from_user_input(src.crs).equals(self.crs):
                        log(f"WARNING: raster '{os.path.basename(raster_path)}' "
                            "CRS differs from the project CRS; sampling anyway.")
            except Exception:
                pass
            nodata = src.nodata
            vals = np.array(
                [v[0] for v in src.sample(pts.tolist())], dtype=float)

        mask = np.isfinite(vals)
        if nodata is not None:
            mask &= (vals != nodata)
        if not mask.any():
            raise ValueError(
                f"Raster '{os.path.basename(raster_path)}' produced no valid "
                "samples over the mesh (check its extent / CRS).")
        if not mask.all():
            fill = float(vals[mask].mean())
            vals[~mask] = fill
            log(f"Filled {int((~mask).sum())} nodata cell(s) in "
                f"'{os.path.basename(raster_path)}' with mean {fill:.3f}.")
        return vals

    def _resolve_elevation(self, spec, ncpl: int,
                           log_cb: Optional[Callable[[str], None]] = None):
        if spec is None:
            raise ValueError("Elevation specification is missing.")
        if isinstance(spec, (int, float, np.floating)):
            return float(spec)
        if isinstance(spec, str):
            arr = self.sample_raster_at_centroids(spec, log_cb)
            if arr.shape[0] != ncpl:
                raise ValueError("Sampled elevation length does not match ncpl.")
            return arr
        arr = np.asarray(spec, dtype=float)
        if arr.shape[0] != ncpl:
            raise ValueError(
                f"Elevation array length {arr.shape[0]} != ncpl {ncpl}.")
        return arr

    def export_modelmuse(self, workspace: str, nlay: int,
                         top, botm: list,
                         mf6_exe: str = "mf6",
                         log_cb: Optional[Callable[[str], None]] = None) -> str:
        self._require_mesh()
        import flopy

        def log(msg: str) -> None:
            if log_cb:
                log_cb(msg)

        disv = self.result.disv if (self.result and self.result.disv) \
            else self.compute_disv(log_cb)
        ncpl = disv["ncpl"]

        if len(botm) != nlay:
            raise ValueError(
                f"Expected {nlay} bottom elevation(s), got {len(botm)}.")

        log("Resolving layer elevations…")
        top_res = self._resolve_elevation(top, ncpl, log_cb)
        botm_res = [self._resolve_elevation(b, ncpl, log_cb) for b in botm]

        self._warn_elevation_order(top_res, botm_res, ncpl, log)

        os.makedirs(workspace, exist_ok=True)
        name = _safe_name(self.mesh_name)[:16] or "gwfmodel"

        with _capture_stdout(log):
            sim = flopy.mf6.MFSimulation(
                sim_name=name, sim_ws=workspace, exe_name=mf6_exe)
            flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(1.0, 1, 1.0)])
            flopy.mf6.ModflowIms(sim, complexity="MODERATE")
            gwf = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)

            flopy.mf6.ModflowGwfdisv(
                gwf,
                length_units="METERS" if crs_length_unit(self.crs) == "meter"
                else "FEET",
                nlay=nlay,
                ncpl=ncpl,
                nvert=disv["nvert"],
                top=top_res,
                botm=botm_res,
                vertices=disv["vertices"],
                cell2d=disv["cell2d"],
            )
            layer_tops = [top_res] + botm_res[:-1]
            strt = [t if np.isscalar(t) else np.asarray(t) for t in layer_tops]
            flopy.mf6.ModflowGwfic(gwf, strt=strt)
            flopy.mf6.ModflowGwfnpf(gwf, save_flows=True, icelltype=0, k=1.0)
            flopy.mf6.ModflowGwfoc(
                gwf,
                head_filerecord=f"{name}.hds",
                budget_filerecord=f"{name}.cbc",
                saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
            )
            sim.write_simulation()

        nam = os.path.join(workspace, "mfsim.nam")
        log(f"\nModelMuse-ready MODFLOW 6 model written to: {workspace}")
        return nam

    @staticmethod
    def _warn_elevation_order(top_res, botm_res, ncpl, log):
        def as_arr(v):
            return np.full(ncpl, v, dtype=float) if np.isscalar(v) \
                else np.asarray(v, dtype=float)
        surfaces = [as_arr(top_res)] + [as_arr(b) for b in botm_res]
        bad = 0
        for upper, lower in zip(surfaces[:-1], surfaces[1:]):
            bad += int((lower > upper).sum())
        if bad:
            log(f"WARNING: {bad} cell-layer interface(s) have bottom above the "
                "surface below/above. Check your raster elevations.")

    # ------------------------------------------------------------------ #
    def quality_report(self, short_edge_threshold: float = 0.0,
                       log_cb: Optional[Callable[[str], None]] = None) -> dict:
        self._require_mesh()
        gdf = self.result.gdf
        geoms = list(gdf.geometry)
        n = len(geoms)

        areas = np.array([g.area for g in geoms], dtype=float)
        n_verts = np.array(
            [len(g.exterior.coords) - 1 for g in geoms], dtype=float)

        min_edges = np.empty(n)
        all_min = np.inf
        short_count = 0
        for i, g in enumerate(geoms):
            coords = list(g.exterior.coords)
            elen = [
                ((coords[k][0] - coords[k + 1][0]) ** 2 +
                 (coords[k][1] - coords[k + 1][1]) ** 2) ** 0.5
                for k in range(len(coords) - 1)
            ]
            if elen:
                mn = min(elen)
                min_edges[i] = mn
                all_min = min(all_min, mn)
                if short_edge_threshold > 0 and mn < short_edge_threshold:
                    short_count += 1
            else:
                min_edges[i] = np.nan

        disv = self.result.disv or {}
        report = {
            "ncpl": n,
            "nvert": int(disv.get("nvert", 0)),
            "nlay_hint": 1,
            "area_min": float(np.nanmin(areas)),
            "area_max": float(np.nanmax(areas)),
            "area_mean": float(np.nanmean(areas)),
            "area_median": float(np.nanmedian(areas)),
            "area_total": float(np.nansum(areas)),
            "verts_min": int(np.nanmin(n_verts)),
            "verts_max": int(np.nanmax(n_verts)),
            "verts_mean": float(np.nanmean(n_verts)),
            "edge_min": float(all_min if np.isfinite(all_min) else np.nan),
            "edge_min_mean": float(np.nanmean(min_edges)),
            "short_edge_threshold": float(short_edge_threshold),
            "short_edge_cells": int(short_count),
            "unit": crs_length_unit(self.crs) if self.crs else "units",
        }
        if log_cb:
            log_cb(f"Quality report: {n} cells, "
                   f"area {report['area_min']:.2f}–{report['area_max']:.2f} "
                   f"{report['unit']}², shortest edge "
                   f"{report['edge_min']:.4f} {report['unit']}.")
        return report

    # ------------------------------------------------------------------ #
    def save_project(self, path: str) -> None:
        data = {
            "version": self.PROJECT_VERSION,
            "mesh_name": self.mesh_name,
            "crs": self.crs.to_wkt() if self.crs is not None else None,
            "limit": None,
            "layers": [],
            "voids": [],
            "backgrounds": [],
            "mesh_params": getattr(self, "mesh_params", {}),
            "result": None,
        }
        if self.limit_gdf is not None and not self.limit_gdf.empty:
            data["limit"] = json.loads(self.limit_gdf.to_json())
        for lyr in self.layers:
            data["layers"].append({
                "name": lyr.name,
                "ref": lyr.ref,
                "color": lyr.color,
                "visible": lyr.visible,
                "top_raster": getattr(lyr, "top_raster", None),
                "botm_raster": getattr(lyr, "botm_raster", None),
                "gdf": json.loads(lyr.gdf.to_json()),
            })
        for void in self.voids:
            data["voids"].append({
                "name": void.name,
                "color": void.color,
                "visible": void.visible,
                "gdf": json.loads(void.gdf.to_json()),
            })
        for bg in self.backgrounds:
            data["backgrounds"].append({
                "path": bg.path,
                "extent": list(bg.extent),
                "crs": bg.crs.to_wkt() if bg.crs is not None else None,
                "name": bg.name,
                "visible": bg.visible,
            })
        if self.result is not None and self.result.gdf is not None:
            data["result"] = {
                "gdf": json.loads(self.result.gdf.to_json()),
                "disv": self.result.disv or {},
            }
        with open(path, "w") as fh:
            json.dump(data, fh)

    @classmethod
    def load_project(cls, path: str) -> "MeshProject":
        with open(path) as fh:
            data = json.load(fh)

        proj = cls()
        proj.mesh_name = data.get("mesh_name", "voronoiModel")
        if data.get("crs"):
            proj.crs = pyproj.CRS.from_user_input(data["crs"])
        proj.mesh_params = data.get("mesh_params", {}) or {}

        if data.get("limit"):
            proj.limit_gdf = gpd.GeoDataFrame.from_features(
                data["limit"]["features"], crs=proj.crs)

        for ld in data.get("layers", []):
            gdf = gpd.GeoDataFrame.from_features(
                ld["gdf"]["features"], crs=proj.crs)
            layer = RefinementLayer(
                name=ld["name"], gdf=gdf, ref=float(ld["ref"]),
                color=ld.get("color", "#4363d8"),
                visible=ld.get("visible", True))
            layer.top_raster = ld.get("top_raster")
            layer.botm_raster = ld.get("botm_raster")
            proj.layers.append(layer)

        for vd in data.get("voids", []):
            gdf = gpd.GeoDataFrame.from_features(
                vd["gdf"]["features"], crs=proj.crs)
            proj.voids.append(VoidPolygon(
                name=vd["name"], gdf=gdf,
                color=vd.get("color", "#ef5350"),
                visible=vd.get("visible", True)))

        bg_list = data.get("backgrounds")
        if bg_list is None:
            # Backward compatibility with pre-3 project files that stored a
            # single background under the "background" key.
            legacy = data.get("background")
            bg_list = [legacy] if legacy else []
        for bg in bg_list:
            if bg and _is_local_file(bg.get("path")):
                try:
                    added = proj.add_background(bg["path"], extent=tuple(bg["extent"]))
                    added.name = bg.get("name") or added.name
                    added.visible = bg.get("visible", True)
                except Exception:
                    pass

        res = data.get("result")
        if res and res.get("gdf"):
            gdf = gpd.GeoDataFrame.from_features(
                res["gdf"]["features"], crs=proj.crs)
            stable = tempfile.mkdtemp(prefix="mf6vor_mesh_")
            shp = os.path.join(stable, f"{_safe_name(proj.mesh_name)}_voronoi.shp")
            try:
                gdf.to_file(shp)
            except Exception:
                shp = None
            proj.result = MeshResult(gdf=gdf, disv=res.get("disv", {}) or {},
                                     shp_path=shp)
        return proj

    # ------------------------------------------------------------------ #
    def _require_mesh(self) -> None:
        if self.result is None or self.result.gdf is None:
            raise RuntimeError("No mesh has been generated yet.")


# --------------------------------------------------------------------------- #
#  small utilities
# --------------------------------------------------------------------------- #

def _is_local_file(path) -> bool:
    """True only for an existing plain local file. Project files are untrusted
    input: refuse UNC shares (Windows would send NTLM credentials to the host),
    URLs and GDAL /vsi* virtual paths so a crafted .mf6vor can't make the app
    reach out to a remote machine."""
    if not isinstance(path, str) or not path:
        return False
    p = path.replace("/", "\\")
    if p.startswith("\\\\") or "://" in path or path.lower().startswith("/vsi"):
        return False
    return os.path.isfile(path)


def engine_version() -> str:
    """Installed mf6Voronoi (meshing engine) version, or 'unknown'."""
    try:
        from importlib.metadata import version
        return version("mf6Voronoi")
    except Exception:
        return "unknown"


def _safe_name(name: str) -> str:
    keep = "-_"
    return "".join(c if (c.isalnum() or c in keep) else "_" for c in name)


@contextlib.contextmanager
def _exit_as_error():
    try:
        yield
    except SystemExit as exc:
        raise RuntimeError(
            "mf6Voronoi rejected the input (see the log above; the limit must "
            "be a single polygon and every layer valid).") from exc


@contextlib.contextmanager
def _capture_stdout(log_cb: Callable[[str], None]):
    """Redirect stdout/stderr to ``log_cb`` line by line.

    Reentrancy- and None-safe: in a windowed / PyInstaller ``--windowed`` app,
    ``sys.stdout`` and ``sys.stderr`` are ``None``.  The library prints with
    ``flush=True`` and tqdm writes to stderr, so both streams are replaced with a
    guarded writer that never touches a ``None`` passthrough.
    """
    import sys
    old_out = sys.stdout
    old_err = sys.stderr

    class _Writer(io.TextIOBase):
        def __init__(self, passthrough):
            self._busy = False
            self._passthrough = passthrough

        def write(self, s):
            if not s:
                return 0
            if self._busy:
                if self._passthrough is not None:
                    try:
                        self._passthrough.write(s)
                    except Exception:
                        pass
                return len(s)
            self._busy = True
            try:
                if log_cb:
                    text = s.rstrip("\n")
                    if text:
                        log_cb(text)
            finally:
                self._busy = False
            return len(s)

        def flush(self):
            if self._passthrough is not None:
                try:
                    self._passthrough.flush()
                except Exception:
                    pass

    try:
        sys.stdout = _Writer(old_out)
        sys.stderr = _Writer(old_err)   # tqdm writes here; also None when windowed
        yield
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
