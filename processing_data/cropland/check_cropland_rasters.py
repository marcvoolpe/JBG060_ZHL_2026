"""Sanity checks on the downloaded cropland data (no accuracy statistics).

1. Every raster in MANIFEST.csv: CRS, resolution, no-data, whether the product's
   files together cover the buffered AOI, and exact value counts (read in strips).
2. Class-code check at five rule-based locations in the Aweil AOI: each product's
   raw value and its documented meaning are printed so codes can be judged.
3. Per-county cropland areas: products more than 10x away from the median of the
   other products are flagged.
4. Git: no raster / GeoPackage under data/cropland is tracked or staged.

Writes data/cropland/CHECKS.md. Usage (repo root, global Python 3.13):
    python -m processing_data.cropland.check_cropland_rasters
"""

from __future__ import annotations

import subprocess
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import Window
from shapely.geometry import Point, box
from shapely.ops import nearest_points, unary_union

from processing_data.cropland.common import AOIS, CROPLAND_DIR, aoi_geometry, read_manifest
from processing_data.paths import EXT_DATA

ROOT = EXT_DATA.parent
OCHA_PLACES = EXT_DATA / "Gazetteers_OSM" / "ocha_populated_places_2022"
REPORT = CROPLAND_DIR / "CHECKS.md"

# documented meanings, used to translate sampled values
MEANINGS = {
    "ESA WorldCereal": {0: "other", 100: "temporary crops", 255: "no data"},
    "ESA WorldCover": {10: "tree cover", 20: "shrubland", 30: "grassland", 40: "cropland", 50: "built-up",
                       60: "bare/sparse", 70: "snow/ice", 80: "permanent water", 90: "herbaceous wetland",
                       95: "mangroves", 100: "moss/lichen", 0: "no data", 255: "no data"},
    "Esri": {1: "water", 2: "trees", 4: "flooded vegetation", 5: "crops", 7: "built area", 8: "bare ground",
             9: "snow/ice", 10: "clouds", 11: "rangeland", 0: "no data", 255: "no data"},
    "Google Dynamic World": {0: "water", 1: "trees", 2: "grass", 3: "flooded vegetation", 4: "crops",
                             5: "shrub and scrub", 6: "built", 7: "bare", 8: "snow and ice", 255: "no observation"},
    "Digital Earth Africa": {0: "not crop", 1: "crop", 255: "no data"},
    "GLAD": {0: "no cropland / no data", 1: "cropland", 255: "outside AOI"},
    "NASA GFSAD30": {0: "water / no data", 1: "non-cropland", 2: "cropland", 255: "outside AOI"},
}


def meaning(product: str, v) -> str:
    for k, m in MEANINGS.items():
        if product.startswith(k):
            return m.get(int(v), f"UNDOCUMENTED CODE {v}")
    return ""


def raster_rows() -> list[dict]:
    return [r for r in read_manifest() if r["file_path"].endswith(".tif") and not r["product"].startswith("derived")]


# --- 1 per-raster checks ---------------------------------------------------------------

def value_counts(src, band: int, max_distinct: int = 300) -> dict:
    counts = np.zeros(256, np.int64) if src.dtypes[band - 1] == "uint8" else None
    stats = {"min": np.inf, "max": -np.inf, "nodata": 0, "n": 0}
    for r0 in range(0, src.height, 1024):
        a = src.read(band, window=Window(0, r0, src.width, min(1024, src.height - r0)))
        if counts is not None:
            counts += np.bincount(a.ravel(), minlength=256)
        else:
            nd = a == src.nodata if src.nodata is not None else np.zeros(a.shape, bool)
            stats["nodata"] += int(nd.sum())
            stats["n"] += a.size
            if (~nd).any():
                stats["min"] = min(stats["min"], float(a[~nd].min()))
                stats["max"] = max(stats["max"], float(a[~nd].max()))
    if counts is not None:
        nz = np.nonzero(counts)[0]
        return {int(k): int(counts[k]) for k in nz[:max_distinct]}
    return stats


def check_files(lines: list[str]) -> None:
    lines += ["## 1. File checks", "",
              "| product | year | AOI | file | CRS | pixel size | no-data | covers AOI (product) | values: count |",
              "|---|---|---|---|---|---|---|---|---|"]
    groups = defaultdict(list)
    rows = raster_rows()
    for r in rows:
        groups[(r["product"], r["year"], r["aoi"], r["band"])].append(r)
    coverage = {}
    for key, rs in groups.items():
        aoi = key[2]
        if aoi not in AOIS:
            continue
        polys = []
        for r in rs:
            with rasterio.open(ROOT / r["file_path"]) as s:
                polys.append(box(*transform_bounds(s.crs, "EPSG:4326", *s.bounds, densify_pts=21)))
        union = unary_union(polys)
        need = aoi_geometry(aoi, "EPSG:4326")
        coverage[key] = union.buffer(1e-6).covers(need)
    seen = set()
    for r in rows:
        path = ROOT / r["file_path"]
        with rasterio.open(path) as s:
            bands = range(1, s.count + 1)
            for b in bands:
                if (r["file_path"], b) in seen:
                    continue
                seen.add((r["file_path"], b))
                vc = value_counts(s, b)
                if "min" in vc:
                    vtxt = f"min {vc['min']:.3g}, max {vc['max']:.3g}, no-data {100 * vc['nodata'] / max(vc['n'], 1):.1f}%"
                else:
                    tot = sum(vc.values())
                    if len(vc) > 12:
                        keys = sorted(vc)
                        vtxt = f"{len(vc)} distinct, {keys[0]}..{keys[-2]} + {keys[-1]} ({100 * vc[keys[-1]] / tot:.1f}%)"
                    else:
                        vtxt = ", ".join(f"{k}: {100 * v / tot:.2f}%" for k, v in sorted(vc.items()))
                bname = s.descriptions[b - 1] or f"band {b}"
                cov = coverage.get((r["product"], r["year"], r["aoi"], r["band"]), "n/a")
                lines.append(f"| {r['product']} | {r['year']} | {r['aoi']} | {Path(r['file_path']).name} [{bname}] | "
                             f"{s.crs.to_string()} | {s.res[0]:.6g} | {s.nodata} | {cov} | {vtxt} |")
    lines.append("")
    bad = [k for k, v in coverage.items() if not v]
    lines.append(f"Products whose files do not cover the whole buffered AOI: {bad or 'none'}.")
    lines.append("")


# --- 2 class-code check at five locations -----------------------------------------------

def check_points() -> list[tuple[str, str, Point]]:
    """Five locations in the Aweil AOI, each from a fixed rule (recorded in the report)."""
    aoi_poly = aoi_geometry("aweil", "EPSG:4326")
    places = gpd.read_file(OCHA_PLACES)
    pick = lambda name, adm2: places[(places.featureNam == name) & (places.ADM2_EN_18 == adm2)].geometry.iloc[0]
    aweil = pick("Aweil", "Aweil West")
    nyamlel = pick("Nyamlel", "Aweil West")
    utm = AOIS["aweil"]["utm"]
    to_utm = lambda p: gpd.GeoSeries([p], crs="EPSG:4326").to_crs(utm).iloc[0]
    to_ll = lambda p: gpd.GeoSeries([p], crs=utm).to_crs("EPSG:4326").iloc[0]

    pts = []
    a_u = to_utm(aweil)
    pts.append(("town outskirts", "5 km due north of the OCHA 'Aweil' (Aweil Town) point",
                to_ll(Point(a_u.x, a_u.y + 5000))))

    rivers = gpd.read_file(CROPLAND_DIR / "hydrosheds_ffr" / "hydrosheds_ffr_v1_south_sudan.gpkg")
    big = rivers[(rivers.UPLAND_SKM >= 5000) & rivers.intersects(aoi_poly)].to_crs(utm)
    mid = Point((a_u.x + to_utm(nyamlel).x) / 2, (a_u.y + to_utm(nyamlel).y) / 2)
    net = unary_union(big.geometry.values)
    p2 = nearest_points(net, mid)[0]
    pts.append(("Lol floodplain", "point on the HydroSHEDS network with upstream area >= 5,000 km2 nearest to the "
                "midpoint of OCHA 'Nyamlel' (Aweil West) and 'Aweil'", to_ll(p2)))

    # toich: MERIT HND <= 1 m, >= 1.5 km from any building, <= 5 km from the big-river network, nearest to Aweil
    with rasterio.open(CROPLAND_DIR / "merit_hydro" / "merit_hydro_v1_0_1_hnd_upa_aweil.tif") as s:
        hnd = s.read(1)
        rr, cc = np.nonzero((hnd >= 0) & (hnd <= 1.0))
        xs, ys = rasterio.transform.xy(s.transform, rr, cc)
    cand = gpd.GeoSeries(gpd.points_from_xy(xs, ys), crs="EPSG:4326").to_crs(utm)
    near_river = cand.distance(net) <= 5000
    cand = cand[near_river]
    with rasterio.open(CROPLAND_DIR / "derived" / "aweil" / "dist_to_building_30m_aweil.tif") as s:
        d = np.array([v[0] for v in s.sample([(p.x, p.y) for p in cand])])
    cand = cand[(d >= 1500) & (d != 65535)]
    p3 = cand.iloc[int(np.argmin(cand.distance(a_u).values))]
    pts.append(("toich wetland", "MERIT HND <= 1 m, >= 1.5 km from any Open Buildings footprint, <= 5 km from the "
                ">= 5,000 km2 river network; the candidate nearest to Aweil", to_ll(p3)))

    # woodland: WorldCover 2021 = tree cover AND Esri 2022 = trees, >= 1.5 km from buildings, nearest to Aweil
    with rasterio.open(CROPLAND_DIR / "esri_lulc" / "esri_lulc_2022_aweil.tif") as es:
        step = 30  # every 300 m
        a = es.read(1)[::step, ::step]
        rr, cc = np.nonzero(a == 2)
        xs, ys = rasterio.transform.xy(es.transform, rr * step, cc * step)
    cand = gpd.GeoSeries(gpd.points_from_xy(xs, ys), crs=utm)
    with rasterio.open(CROPLAND_DIR / "worldcover" / "worldcover_2021_v200_aweil.tif") as s:
        ll = cand.to_crs("EPSG:4326")
        wc = np.array([v[0] for v in s.sample([(p.x, p.y) for p in ll])])
    with rasterio.open(CROPLAND_DIR / "derived" / "aweil" / "dist_to_building_30m_aweil.tif") as s:
        d = np.array([v[0] for v in s.sample([(p.x, p.y) for p in cand])])
    cand = cand[(wc == 10) & (d >= 1500) & (d != 65535)]
    p4 = cand.iloc[int(np.argmin(cand.distance(a_u).values))]
    pts.append(("woodland patch", "sampled every 300 m: Esri 2022 = trees AND WorldCover 2021 = tree cover, >= 1.5 km "
                "from any building; the candidate nearest to Aweil (so these two maps agree here by construction)",
                to_ll(p4)))

    b = gpd.read_file(CROPLAND_DIR / "open_buildings" / "open_buildings_v3_conf070_aweil.gpkg").to_crs(utm)
    c = b.geometry.representative_point()
    far = c.distance(a_u) > 10000
    ix = (np.floor(c.x[far] / 1000)).astype(int)
    iy = (np.floor(c.y[far] / 1000)).astype(int)
    top = pd.Series(1, index=pd.MultiIndex.from_arrays([ix, iy])).groupby(level=[0, 1]).sum().idxmax()
    p5 = Point(top[0] * 1000 + 500, top[1] * 1000 + 500)
    pts.append(("village cluster", "centre of the 1 km x 1 km cell (UTM 35N) with the most Open Buildings footprints "
                "(confidence >= 0.70), excluding cells within 10 km of Aweil", to_ll(p5)))
    return pts


def sample_product(r: dict, pt_ll: Point) -> list[tuple[str, int]]:
    out = []
    with rasterio.open(ROOT / r["file_path"]) as s:
        p = gpd.GeoSeries([pt_ll], crs="EPSG:4326").to_crs(s.crs).iloc[0]
        b = s.bounds
        if not (b.left <= p.x <= b.right and b.bottom <= p.y <= b.top):
            return out
        vals = next(s.sample([(p.x, p.y)]))
        for i, v in enumerate(vals):
            out.append((s.descriptions[i] or f"band {i + 1}", v))
    return out


def check_codes(lines: list[str]) -> None:
    lines += ["## 2. Class-code check at five locations (Aweil AOI)", "",
              "Raw value of each product at each point, with its documented meaning. This checks that codes behave as "
              "documented; it is not an accuracy assessment.", ""]
    pts = check_points()
    for name, rule, p in pts:
        lines.append(f"### {name} ({p.y:.5f} N, {p.x:.5f} E)")
        lines.append(f"Rule: {rule}.")
        lines.append("")
        lines.append("| product | year | band | value | meaning |")
        lines.append("|---|---|---|---|---|")
        for r in raster_rows():
            if r["aoi"] != "aweil" or r["product"].startswith("MERIT"):
                continue
            for bname, v in sample_product(r, p):
                m = meaning(r["product"], v) if bname in ("classification", "Map", "b1", "label_mode", "band 1") \
                    else ("%" if "pct" in bname or bname == "confidence" else "")
                if r["product"].startswith("Digital Earth Africa") and r["band"] == "prob":
                    m = "% crop probability"
                if r["product"].startswith("ESA WorldCereal") and v == 255:
                    continue  # this AEZ file does not cover the point
                if r["product"].startswith("Digital Earth Africa") and v == 255:
                    continue
                lines.append(f"| {r['product']} | {r['year']} | {r['band'] if r['product'].startswith('Digital') else bname} | {v} | {m} |")
        lines.append("")


# --- 3 county areas --------------------------------------------------------------------

def check_areas(lines: list[str]) -> None:
    lines += ["## 3. Per-county cropland area: products more than 10x from the others", ""]
    path = CROPLAND_DIR / "county_cropland_areas.csv"
    if not path.exists():
        lines += ["county_cropland_areas.csv not found (run derived_cropland_layers.py first).", ""]
        return
    t = pd.read_csv(path)
    cols = [c for c in t.columns if c.endswith("_ha") and "cfsam" not in c]
    lines.append("Flag rule: a product's county area is more than 10x above or below the median of the other map "
                 "products for that county (CFSAM excluded from the median; ASAP included).")
    lines.append("")
    flags = []
    for _, row in t.iterrows():
        for c in cols:
            others = row[[o for o in cols if o != c]].astype(float)
            med = np.nanmedian(others)
            v = float(row[c])
            if med > 0 and (v > 10 * med or v < med / 10):
                flags.append(f"- {row['adm2_name']}: {c} = {v:,.0f} ha vs median of others {med:,.0f} ha "
                             f"({v / med:.2g}x)")
    lines += flags or ["- none"]
    lines.append("")


# --- 4 git ------------------------------------------------------------------------------

def check_git(lines: list[str]) -> None:
    lines += ["## 4. Git", ""]
    tracked = subprocess.run(["git", "ls-files", "--cached", "data/cropland"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    big = [f for f in tracked if f.endswith((".tif", ".gpkg")) or (ROOT / f).stat().st_size > 20e6]
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    staged_big = [f for f in staged if f.endswith((".tif", ".gpkg"))]
    probe = subprocess.run(["git", "check-ignore", "-q", "data/cropland/esri_lulc/esri_lulc_2022_aweil.tif"], cwd=ROOT)
    lines.append(f"- Large rasters/GeoPackages tracked under data/cropland: {big or 'none'}")
    lines.append(f"- Rasters/GeoPackages staged: {staged_big or 'none'}")
    lines.append(f"- .gitignore rule catches data/cropland/**/*.tif: {'yes' if probe.returncode == 0 else 'NO'}")
    lines.append("")


def main() -> None:
    lines = ["# Cropland data checks", "",
             "Generated by `processing_data/cropland/check_cropland_rasters.py`. No accuracy statistics.", ""]
    check_files(lines)
    check_codes(lines)
    check_areas(lines)
    check_git(lines)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
