"""Derived cropland layers from the downloaded public maps (run after all downloads are logged).

For each AOI (Aweil, Bor South) and each cropland product in the manifest:
  1. a 0/1 crop layer on the AOI's 10 m UTM grid (Sentinel-2 aligned), using the
     class codes recorded in MANIFEST.csv. Products that are not on that grid
     (EPSG:4326 products, 30 m products) are brought to it by nearest neighbour;
     this only duplicates or drops whole source pixels, it never blends classes;
  2. the 30 m assessment grid (3 x 3 blocks of the 10 m grid): crop if at least
     5 of the 9 pixels are crop; the crop fraction (share of the 9 pixels that
     are crop, in %) is kept too. Blocks with fewer than 5 valid pixels are no-data;
  3. a "number of maps saying crop" layer (0-4) on the 30 m grid from the four
     priority-A maps for the 2022 reference season;
  4. a per-county table of cropland area (ha) per product, measured on each
     product's NATIVE pixels (geodesic pixel area for EPSG:4326 grids), next to
     ASAP crop-mask area and the CFSAM 2022 harvested cereal area. CFSAM is a
     modelled estimate from a field mission and is context only, not a reference.

Outputs go to data/cropland/derived/<aoi>/ and data/cropland/county_cropland_areas.csv.
No accuracy statistics are computed here.

Usage (repo root, global Python 3.13):
    python -m processing_data.cropland.derived_cropland_layers [--aoi aweil borsouth] [--skip-rasters]
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.transform import Affine
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window, from_bounds

from processing_data.cropland.common import (
    AOIS, CROPLAND_DIR, aoi_geometry, counties, file_fields, read_manifest, today, upsert_manifest, utm_grid,
)
from processing_data.paths import COURSE_RAW, EXT_DATA

NODATA = 255
STRIP_ROWS_10M = 3 * 1024  # strip height on the 10 m grid (multiple of 3 so strips hold whole 30 m blocks)
ASAP_CROP = COURSE_RAW / "farmland" / "asap_mask_crop_v04.tif"
CFSAM_CSV = EXT_DATA / "FEWS_crop_data" / "crop_data.csv"


@dataclass
class CropProduct:
    """One crop map: which files, which band, and which values mean crop / no data."""
    key: str                    # short name used in file names and table columns
    label: str
    files: Callable[[str], list[Path]]
    band: int                   # 1-based band index
    is_crop: Callable[[np.ndarray], np.ndarray]
    is_valid: Callable[[np.ndarray], np.ndarray]
    rule: str                   # plain-language crop rule, copied to the manifest
    agreement: bool = False     # counts in the 0-4 "maps saying crop" layer
    extra: dict = field(default_factory=dict)


def _glob(sub: str, pattern: str) -> Callable[[str], list[Path]]:
    return lambda aoi: sorted((CROPLAND_DIR / sub).glob(pattern.format(aoi=aoi)))


def _not(v):
    return lambda a: a != v


def _from_manifest(product_prefix: str, band: str | None = None, year: str | None = None) -> Callable[[str], list[Path]]:
    """Files logged in MANIFEST.csv for an AOI (used where one folder holds tiles for both AOIs)."""
    root = EXT_DATA.parent

    def files(aoi: str) -> list[Path]:
        rows = [r for r in read_manifest() if r["product"].startswith(product_prefix) and r["aoi"] == aoi
                and r["status"] == "obtained" and (band is None or r["band"] == band)
                and (year is None or r["year"] == year)]
        return sorted(root / r["file_path"] for r in rows)
    return files


PRODUCTS: list[CropProduct] = [
    CropProduct("worldcereal2021", "ESA WorldCereal 2021 v100 temporary crops",
                _glob("worldcereal", "worldcereal_2021_v100_temporarycrops_aez*_{aoi}.tif"), 1,
                lambda a: a == 100, _not(NODATA), "classification == 100", agreement=True),
    CropProduct("worldcover2021", "ESA WorldCover 2021 v200", _glob("worldcover", "worldcover_2021_v200_{aoi}.tif"), 1,
                lambda a: a == 40, lambda a: (a != NODATA) & (a != 0), "Map == 40", agreement=True),
    CropProduct("worldcover2020", "ESA WorldCover 2020 v100", _glob("worldcover", "worldcover_2020_v100_{aoi}.tif"), 1,
                lambda a: a == 40, lambda a: (a != NODATA) & (a != 0), "Map == 40"),
    *[CropProduct(f"esri{y}", f"Esri/IO 10 m land cover {y}", _glob("esri_lulc", f"esri_lulc_{y}_{{aoi}}.tif"), 1,
                  lambda a: a == 5, lambda a: (a != NODATA) & (a != 0), "b1 == 5 (Esri original coding: 5 = crops)",
                  agreement=(y == 2022))
      for y in (2021, 2022, 2023, 2024)],
    CropProduct("dw2022jjason", "Dynamic World V1, mode of label Jun-Nov 2022",
                _glob("dynamic_world", "dynamic_world_v1_2022-06_2022-11_{aoi}.tif"), 1,
                lambda a: a == 4, _not(NODATA), "label_mode == 4 (crops)", agreement=True),
    CropProduct("dw2022year", "Dynamic World V1, mode of label Jan-Dec 2022",
                _glob("dynamic_world", "dynamic_world_v1_2022_{aoi}.tif"), 1,
                lambda a: a == 4, _not(NODATA), "label_mode == 4 (crops)"),
    # 6-8: comparison maps (priority B). Tiles are the delivered files, so several per AOI.
    CropProduct("deafrica2019", "Digital Earth Africa crop_mask 2019 (pixel mask)",
                _from_manifest("Digital Earth Africa", band="mask"), 1,
                lambda a: a == 1, _not(NODATA), "mask == 1 (files' no-data is 255)"),
    CropProduct("deafrica2019filt", "Digital Earth Africa crop_mask 2019 (object-filtered)",
                _from_manifest("Digital Earth Africa", band="filtered"), 1,
                lambda a: a == 1, _not(NODATA), "filtered == 1"),
    CropProduct("glad2019", "GLAD cropland 2016-2019", _glob("glad_cropland", "glad_cropland_2016-2019_{aoi}.tif"), 1,
                lambda a: a == 1, _not(NODATA), "b1 == 1"),
    CropProduct("glad2015", "GLAD cropland 2012-2015", _glob("glad_cropland", "glad_cropland_2012-2015_{aoi}.tif"), 1,
                lambda a: a == 1, _not(NODATA), "b1 == 1"),
    CropProduct("gfsad2015", "GFSAD30 Africa cropland extent 2015", _glob("gfsad30", "GFSAD30AFCE_*_{aoi}.tif"), 1,
                lambda a: a == 2, _not(NODATA), "b1 == 2 (0 = water/no data and 1 = non-cropland count as not crop)"),
]


# --- grids and I/O -------------------------------------------------------------------

def grid_profile(aoi: str, res: int) -> dict:
    g = utm_grid(aoi, res)
    rows, cols = g["shape"]
    a, b, c, d, e, f = g["transform"]
    return {"driver": "GTiff", "dtype": "uint8", "nodata": NODATA, "count": 1, "crs": g["crs"],
            "transform": Affine(a, b, c, d, e, f), "width": cols, "height": rows,
            "tiled": True, "blockxsize": 512, "blockysize": 512, "compress": "deflate", "predictor": 2,
            "BIGTIFF": "IF_SAFER"}


def read_on_grid(paths: list[Path], band: int, prof: dict, win: Window) -> np.ndarray:
    """Read a window of the 10 m grid from one or more source files (nearest neighbour).

    Where several files cover a pixel (WorldCereal AEZ images), the first file with a
    valid value wins; AEZ images do not overlap in their valid areas.
    """
    out = np.full((int(win.height), int(win.width)), NODATA, dtype=np.uint8)
    for p in paths:
        with rasterio.open(p) as src:
            with WarpedVRT(src, crs=prof["crs"], transform=prof["transform"], width=prof["width"],
                           height=prof["height"], resampling=Resampling.nearest, nodata=src.nodata,
                           src_nodata=src.nodata) as vrt:
                arr = vrt.read(band, window=win)
                nod = src.nodata
        fill = (out == NODATA) & (arr != nod) if nod is not None else (out == NODATA)
        out[fill] = arr[fill]
    return out


def block3(a: np.ndarray) -> np.ndarray:
    """Sum over non-overlapping 3 x 3 blocks (array shape must be multiples of 3)."""
    r, c = a.shape
    return a.reshape(r // 3, 3, c // 3, 3).sum(axis=(1, 3))


def aoi_mask_30m(aoi: str, prof30: dict) -> np.ndarray:
    geom = aoi_geometry(aoi)  # UTM
    return rasterize([(geom, 1)], out_shape=(prof30["height"], prof30["width"]), transform=prof30["transform"],
                     fill=0, dtype="uint8").astype(bool)


def make_rasters(aoi: str, prod: CropProduct) -> dict | None:
    paths = prod.files(aoi)
    if not paths:
        print(f"  {prod.key}: no files for {aoi}, skipped")
        return None
    out_dir = CROPLAND_DIR / "derived" / aoi
    out_dir.mkdir(parents=True, exist_ok=True)
    p10 = grid_profile(aoi, 10)
    p30 = grid_profile(aoi, 30)
    # 10 m grid dimensions are 3x the 30 m grid (same snapped bounds)
    assert p10["height"] == 3 * p30["height"] and p10["width"] == 3 * p30["width"]
    f10 = out_dir / f"{prod.key}_crop10m_{aoi}.tif"
    f30 = out_dir / f"{prod.key}_crop30m_{aoi}.tif"
    ffr = out_dir / f"{prod.key}_cropfrac30m_{aoi}.tif"
    with rasterio.open(f10, "w", **p10) as d10, rasterio.open(f30, "w", **p30) as d30, \
            rasterio.open(ffr, "w", **p30) as dfr:
        for r0 in range(0, p10["height"], STRIP_ROWS_10M):
            h = min(STRIP_ROWS_10M, p10["height"] - r0)
            win = Window(0, r0, p10["width"], h)
            raw = read_on_grid(paths, prod.band, p10, win)
            valid = prod.is_valid(raw)
            crop = prod.is_crop(raw) & valid
            b10 = np.where(valid, crop.astype(np.uint8), NODATA).astype(np.uint8)
            d10.write(b10, 1, window=win)
            nvalid = block3(valid.astype(np.uint16))
            ncrop = block3(crop.astype(np.uint16))
            ok = nvalid >= 5
            c30 = np.where(ok, (ncrop >= 5).astype(np.uint8), NODATA).astype(np.uint8)
            frac = np.where(ok, np.round(100.0 * ncrop / np.maximum(nvalid, 1)), NODATA).astype(np.uint8)
            w30 = Window(0, r0 // 3, p30["width"], h // 3)
            d30.write(c30, 1, window=w30)
            dfr.write(frac, 1, window=w30)
    for f, what in [(f10, "0/1 crop on 10 m UTM grid"), (f30, "0/1 crop on 30 m grid (>= 5 of 9 pixels crop)"),
                    (ffr, "crop fraction on 30 m grid, % of valid 10 m pixels (0-100)")]:
        row = dict(product=f"derived: {prod.label}", version="derived", year=prod.key, aoi=aoi,
                   source="processing_data/cropland/derived_cropland_layers.py from " + "; ".join(p.name for p in paths),
                   access_date=today(), licence="as source product", band=what,
                   class_codes=f"crop rule: {prod.rule}; 1 = crop, 0 = not crop, 255 = no data" if "fraction" not in what
                   else "0-100 = % of valid 10 m pixels that are crop; 255 = no data (< 5 valid pixels)",
                   status="obtained", notes="Nearest-neighbour onto the Sentinel-2-aligned UTM grid; no class blending.")
        row.update(file_fields(f))
        upsert_manifest(row)
    print(f"  {prod.key}: wrote {f10.name}, {f30.name}, {ffr.name}")
    return {"crop30": f30}


def agreement_layer(aoi: str) -> None:
    out_dir = CROPLAND_DIR / "derived" / aoi
    p30 = grid_profile(aoi, 30)
    members = [p for p in PRODUCTS if p.agreement]
    files = [out_dir / f"{p.key}_crop30m_{aoi}.tif" for p in members]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        print(f"  agreement layer skipped, missing: {missing}")
        return
    total = np.zeros((p30["height"], p30["width"]), np.uint8)
    anyvalid = np.zeros_like(total, dtype=bool)
    allvalid = np.ones_like(total, dtype=bool)
    for f in files:
        with rasterio.open(f) as s:
            a = s.read(1)
        v = a != NODATA
        total += np.where(v, a, 0).astype(np.uint8)
        anyvalid |= v
        allvalid &= v
    out = np.where(allvalid, total, NODATA).astype(np.uint8)
    path = out_dir / f"n_maps_crop_30m_{aoi}.tif"
    with rasterio.open(path, "w", **p30) as d:
        d.write(out, 1)
    row = dict(product="derived: number of maps saying crop", version="derived", year="2021-2022", aoi=aoi,
               source="derived from " + "; ".join(f.name for f in files), access_date=today(),
               licence="as source products", band="count 0-4",
               class_codes=f"0-{len(files)} = number of these 30 m crop layers saying crop: "
                           + ", ".join(p.key for p in members) + "; 255 = any member has no data",
               status="obtained", notes="Members: WorldCereal 2021, WorldCover 2021, Esri 2022, Dynamic World Jun-Nov 2022.")
    row.update(file_fields(path))
    upsert_manifest(row)
    print(f"  wrote {path.name}")


BUILDING_DIST_CAP_M = 1500


def building_distance(aoi: str) -> None:
    """Distance (m) from each 30 m cell centre to the nearest Open Buildings footprint, capped at 1.5 km.

    Buildings (confidence >= 0.70) are burned into the 30 m grid (a cell is 'building'
    if any footprint touches it); the Euclidean distance transform then runs tile by
    tile with a halo wider than the cap, so the capped result is exact.
    """
    import geopandas as gpd
    from scipy.ndimage import distance_transform_edt

    src = CROPLAND_DIR / "open_buildings" / f"open_buildings_v3_conf070_{aoi}.gpkg"
    if not src.exists():
        print(f"  building distance skipped: {src.name} missing")
        return
    p30 = grid_profile(aoi, 30)
    p30 = dict(p30, dtype="uint16", nodata=65535)
    b = gpd.read_file(src).to_crs(p30["crs"])
    burned = rasterize(((g, 1) for g in b.geometry), out_shape=(p30["height"], p30["width"]),
                       transform=p30["transform"], fill=0, dtype="uint8", all_touched=True).astype(bool)
    del b
    inside = aoi_mask_30m(aoi, grid_profile(aoi, 30))
    halo = int(math.ceil(BUILDING_DIST_CAP_M / 30)) + 2
    tile = 2048
    H, W = burned.shape
    path = CROPLAND_DIR / "derived" / aoi / f"dist_to_building_30m_{aoi}.tif"
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **p30) as dst:
        for r0 in range(0, H, tile):
            for c0 in range(0, W, tile):
                r1, c1 = min(r0 + tile, H), min(c0 + tile, W)
                R0, C0, R1, C1 = max(r0 - halo, 0), max(c0 - halo, 0), min(r1 + halo, H), min(c1 + halo, W)
                sub = burned[R0:R1, C0:C1]
                if sub.any():
                    d = distance_transform_edt(~sub, sampling=30.0)
                else:
                    d = np.full(sub.shape, np.inf)
                d = np.minimum(d, BUILDING_DIST_CAP_M)[r0 - R0:r1 - R0, c0 - C0:c1 - C0]
                out = np.where(inside[r0:r1, c0:c1], np.round(d), 65535).astype(np.uint16)
                dst.write(out, 1, window=Window(c0, r0, c1 - c0, r1 - r0))
    row = dict(product="derived: distance to nearest building (Open Buildings v3, conf >= 0.70)", version="derived",
               year="2023", aoi=aoi, source=f"processing_data/cropland/derived_cropland_layers.py from {src.name}",
               access_date=today(), licence="as Open Buildings (CC-BY-4.0 / ODbL)", band="distance (m)",
               class_codes=f"metres from 30 m cell centre to nearest building cell centre, capped at {BUILDING_DIST_CAP_M}; "
                           "0 = cell touches a building; 65535 = outside buffered AOI",
               status="obtained", notes="Buildings burned with all_touched; exact within the cap (tiled EDT with halo).")
    row.update(file_fields(path))
    upsert_manifest(row)
    print(f"  wrote {path.name}")


# --- county areas on native pixels ----------------------------------------------------

def pixel_area_m2(src) -> np.ndarray:
    """Per-row pixel area (m2): exact for projected grids, geodesic (sphere) for EPSG:4326 grids."""
    t = src.transform
    if not src.crs.is_geographic:
        return np.full(src.height, abs(t.a * t.e))
    R = 6371007.2  # authalic radius (m)
    lat_top = t.f + t.e * np.arange(src.height)
    lat_bot = lat_top + t.e
    band = np.abs(np.sin(np.radians(lat_top)) - np.sin(np.radians(lat_bot)))
    return R * R * np.radians(abs(t.a)) * band


def native_county_area(paths: list[Path], band: int, fn: Callable[[np.ndarray], np.ndarray],
                       cty, weight: bool = False) -> dict[str, float]:
    """Sum of crop area (ha) per county on each file's native pixels.

    weight=True treats the band as percent cover (ASAP): area = pct/100 x pixel area.
    A pixel belongs to a county when its centre falls inside it; with several files
    (WorldCereal AEZs) a pixel is counted once, from the file that has valid data.
    """
    out = {pc: 0.0 for pc in cty["adm2_pcode"]}
    for p in paths:
        with rasterio.open(p) as src:
            c = cty.to_crs(src.crs)
            area_row = pixel_area_m2(src)
            nod = src.nodata
            # only the counties' window (ASAP is a global file)
            full = Window(0, 0, src.width, src.height)
            cw = from_bounds(*c.total_bounds, src.transform).round_offsets(op="floor").round_lengths(op="ceil")
            cw = cw.intersection(full)
            c0, rw0, cwid, chgt = int(cw.col_off), int(cw.row_off), int(cw.width), int(cw.height)
            for r0 in range(rw0, rw0 + chgt, 2048):
                h = min(2048, rw0 + chgt - r0)
                win = Window(c0, r0, cwid, h)
                a = src.read(band, window=win)
                wt = src.window_transform(win)
                ids = rasterize([(g, i + 1) for i, g in enumerate(c.geometry)], out_shape=a.shape, transform=wt,
                                fill=0, dtype="uint8")
                valid = (a != nod) if nod is not None else np.ones(a.shape, bool)
                val = (a.astype(np.float64) / 100.0) if weight else fn(a).astype(np.float64)
                val = np.where(valid, val, 0.0) * area_row[r0:r0 + h, None]
                for i, pc in enumerate(c["adm2_pcode"]):
                    out[pc] += float(val[ids == i + 1].sum()) / 1e4
    return out


def cfsam_2022(cty) -> pd.Series:
    d = pd.read_csv(CFSAM_CSV, encoding="utf-8-sig")
    d = d[(d["indicator"] == "Area Harvested") & (d["season_year"] == "Main harvest 2022")]
    names = dict(zip(cty["adm2_name"], cty["adm2_pcode"]))
    d = d[d["admin_2"].isin(names)]
    return d.groupby(d["admin_2"].map(names))["value"].sum()


def county_table() -> pd.DataFrame:
    rows = []
    for aoi, spec in AOIS.items():
        cty = counties(spec["pcodes"])
        cty_km2 = cty.to_crs(spec["utm"]).area / 1e6
        base = pd.DataFrame({"aoi": aoi, "adm2_pcode": cty["adm2_pcode"], "adm2_name": cty["adm2_name"],
                             "county_area_km2": cty_km2.round(1).values})
        for prod in PRODUCTS:
            paths = prod.files(aoi)
            if paths:
                base[f"{prod.key}_ha"] = base["adm2_pcode"].map(native_county_area(paths, prod.band, prod.is_crop, cty)).round(0)
        if ASAP_CROP.exists():
            base["asap_crop_v04_ha"] = base["adm2_pcode"].map(
                native_county_area([ASAP_CROP], 1, None, cty, weight=True)).round(0)
        base["cfsam2022_cereal_harvested_ha_MODELLED"] = base["adm2_pcode"].map(cfsam_2022(cty))
        rows.append(base)
        print(f"  county areas done for {aoi}")
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aoi", nargs="+", default=list(AOIS), choices=list(AOIS))
    ap.add_argument("--skip-rasters", action="store_true", help="only rebuild the county table")
    ap.add_argument("--only-building-distance", action="store_true")
    args = ap.parse_args()
    if args.only_building_distance:
        for aoi in args.aoi:
            building_distance(aoi)
        return
    if not args.skip_rasters:
        for aoi in args.aoi:
            print(f"== {aoi}")
            for prod in PRODUCTS:
                make_rasters(aoi, prod)
            agreement_layer(aoi)
            building_distance(aoi)
    tab = county_table()
    path = CROPLAND_DIR / "county_cropland_areas.csv"
    tab.to_csv(path, index=False)
    print(tab.to_string(index=False))
    row = dict(product="derived: county cropland areas", version="derived", year="various", aoi="aweil; borsouth",
               source="processing_data/cropland/derived_cropland_layers.py", access_date=today(),
               licence="as source products", band="table",
               class_codes="ha of cropland per county per product (native pixels, pixel centre in county); "
                           "ASAP = sum of % cover x pixel area; CFSAM = 2022 main-harvest cereal area harvested (modelled, context only)",
               status="obtained", notes="Not an accuracy assessment.")
    row.update(file_fields(path))
    upsert_manifest(row)


if __name__ == "__main__":
    main()
