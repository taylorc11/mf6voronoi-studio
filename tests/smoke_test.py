"""Headless end-to-end check of the meshing engine (no GUI needed).

Run:  python tests/smoke_test.py
Uses synthetic data only, so it works from a clean checkout.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, box

import engine

CRS = "EPSG:32631"
LIMIT = box(0, 0, 1000, 1000)


def make_project(with_void=False):
    p = engine.MeshProject()
    p.set_crs(CRS)
    p.set_limit_from_gdf(gpd.GeoDataFrame({"id": [1]}, geometry=[LIMIT], crs=CRS))
    p.add_layer_from_gdf("wells", gpd.GeoDataFrame(
        {"id": [1, 2]}, geometry=[Point(500, 500), Point(300, 700)], crs=CRS), 10.0)
    # GHB-like line running closer to the edge than its own ref (2.0.5 regression)
    p.add_layer_from_gdf("ghb", gpd.GeoDataFrame(
        {"id": [1]}, geometry=[LineString([(3, 50), (3, 950)])], crs=CRS), 20.0)
    p.add_layer_from_gdf("zone", gpd.GeoDataFrame(
        {"id": [1]}, geometry=[box(650, 150, 800, 300)], crs=CRS), 25.0)
    if with_void:
        p.add_void_from_gdf("lake", gpd.GeoDataFrame(
            {"id": [1]}, geometry=[box(100, 100, 200, 200)], crs=CRS))
    return p


def check_mesh(p, with_void=False):
    res = p.build_mesh(max_ref=100.0, multiplier=1.3, overlapping=True)
    g = res.gdf
    assert len(g) > 100, f"too few cells: {len(g)}"
    assert g.is_valid.all() and not g.is_empty.any(), "invalid/empty cells"
    assert (g.geom_type == "Polygon").all(), "non-polygon cells"
    assert g.crs is not None
    # cells must tile the domain: no overlaps, no gaps (minus void)
    expect = LIMIT.area - (100 * 100 if with_void else 0)
    assert abs(g.area.sum() - expect) / expect < 1e-3, f"area {g.area.sum()} != {expect}"
    assert g.geometry.union_all().within(LIMIT.buffer(1e-6)), "cells outside limit"
    # refinement really applied: cells near the well are much finer than far away
    near = g[g.geometry.distance(Point(500, 500)) < 15].area.median()
    far = g[g.geometry.distance(Point(950, 950)) < 100].area.median()
    assert near < far / 4, f"no refinement near well ({near} vs {far})"
    # layer running along the boundary was refined too (silent-skip regression)
    edge = g[g.geometry.distance(Point(3, 500)) < 25].area.median()
    assert edge < far / 2, f"boundary line not refined ({edge} vs {far})"
    return g


def check_disv_and_modflow(p, g, tmp):
    disv = p.compute_disv()
    assert disv["ncpl"] == len(g)
    nv = disv["nvert"]
    for c in disv["cell2d"]:
        assert c[3] == len(c) - 4
        assert all(0 <= v < nv for v in c[4:]), "vertex index out of range"
    ws = os.path.join(tmp, "mf6")
    nam = p.export_modelmuse(ws, nlay=2, top=10.0, botm=[0.0, -10.0])
    assert os.path.exists(nam)
    assert any(f.endswith(".disv") for f in os.listdir(ws))


def check_solver(p, tmp):
    """No vertex pairs closer than the weld tolerance, and (if mf6 is on PATH)
    the exported model must actually solve."""
    from scipy.spatial import cKDTree
    v = np.array(p.result.disv["uniqueVerticesList"])
    assert not len(cKDTree(v).query_pairs(engine.MeshProject.WELD_TOL)), "near-duplicate vertices"
    import shutil
    import subprocess
    if not shutil.which("mf6"):
        print("  (mf6 not on PATH, solver run skipped)")
        return
    r = subprocess.run(["mf6"], cwd=os.path.join(tmp, "mf6"), capture_output=True, text=True)
    assert "Normal termination" in r.stdout, r.stdout[-400:]


def check_roundtrip(p, tmp):
    f = os.path.join(tmp, "p.mf6vor")
    p.save_project(f)
    q = engine.MeshProject.load_project(f)
    assert len(q.layers) == len(p.layers) and len(q.result.gdf) == len(p.result.gdf)
    assert q.crs == p.crs


def check_bad_input():
    p = engine.MeshProject()
    try:
        p.build_mesh(100, 1.3)
    except ValueError:
        return
    raise AssertionError("empty project must be rejected, not crash/exit")


def check_exit_becomes_error():
    from mf6Voronoi import geoVoronoi
    orig = geoVoronoi.createVoronoi.addLimit
    geoVoronoi.createVoronoi.addLimit = lambda *a, **k: sys.exit(1)
    try:
        make_project().build_mesh(100.0, 1.3)
    except RuntimeError:
        return
    finally:
        geoVoronoi.createVoronoi.addLimit = orig
    raise AssertionError("library exit() must surface as RuntimeError")


def check_untrusted_paths():
    for bad in (r"\\evil\share\x.tif", "//evil/share/x.tif", "/vsicurl/http://x/y.tif",
                "http://evil/x.tif", "", None):
        assert not engine._is_local_file(bad), bad
    assert engine._is_local_file(os.path.abspath(__file__))
    assert engine.engine_version() != "unknown"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        for void in (False, True):
            p = make_project(void)
            g = check_mesh(p, void)
            print(f"void={void}: {len(g)} cells OK")
            check_disv_and_modflow(p, g, tmp)
            check_solver(p, tmp)
            check_roundtrip(p, tmp)
    check_bad_input()
    check_exit_becomes_error()
    check_untrusted_paths()
    print("ALL OK")


if __name__ == "__main__":
    main()
