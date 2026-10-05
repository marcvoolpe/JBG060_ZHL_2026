"""
Step 10 - Flooded cropland in 2025 (METHODOLOGY.md section 8).

Aweil (little flooding in 2025) and Bor South (wide flooding) are the two
contrasting cases.

  - Flood cells: every NASA MCDWD pixel (~232 m) flooded at least once between
    1 June and 31 December 2025, from raw_data/flood_masks (recurring + unusual).
  - Per map: the crop fraction inside every flood cell (Earth Engine, 10 m,
    sent in chunks of cell boxes), times the cell's area. ASAP is read locally.
  - From the sample, independent of any map: the labelled share of each box
    that is cropland (or cropped; mean of the two labellers) for points in a
    flood cell, 0 elsewhere,
    averaged with the stratum weights and times the study area, with a 95%
    interval. Also the upper bound: boxes that hold any cropland.

Output: cropland/results/flooded_cropland.csv
Run from group_repo: python cropland/10_flood.py cropland/rule1_<date>.json
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

import common as C
import estimators as E

CELL = 0.0020833              # MCDWD pixel size in degrees
TILES = {"aweil": "h20v08", "bor_south": "h21v08"}
CHUNK = 1500


def flood_cells(area):
    parts = []
    for kind in ("compact_recurring", "compact_unusual"):
        df = pd.read_parquet(C.RAW / "flood_masks" / kind / f"flood_events_{TILES[area]}_{C.YEAR}.parquet",
                             columns=["date", "lat", "lon"])
        df = df[pd.to_datetime(df.date.astype(str)) >= f"{C.YEAR}-06-01"]
        parts.append(df[["lat", "lon"]].astype(float).round(6))   # float32 from parquet -> float64 for Earth Engine
    cells = pd.concat(parts).drop_duplicates().reset_index(drop=True)
    cells["ha"] = (CELL * 111_320 * np.cos(np.radians(cells.lat))) * (CELL * 110_540) / 1e4
    return cells


def in_area(ee, cells, area):
    import geopandas as gpd
    admin = gpd.read_file(C.ADMIN2)
    poly = admin[admin.adm2_name.isin(C.AREAS[area])].dissolve().geometry.iloc[0]
    pts = gpd.GeoSeries(gpd.points_from_xy(cells.lon, cells.lat), crs=4326)
    return cells[pts.within(poly).to_numpy()].reset_index(drop=True)


def map_fractions(ee, cells, stack):
    """Mean of every 0/1 map band inside each flood cell."""
    out = []
    h = CELL / 2
    for i in range(0, len(cells), CHUNK):
        part = cells.iloc[i:i + CHUNK]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Rectangle([r.lon - h, r.lat - h, r.lon + h, r.lat + h]), {"i": int(k)})
                                   for k, r in part.iterrows()])
        got = stack.reduceRegions(fc, ee.Reducer.mean(), scale=10, tileScale=4).getInfo()["features"]
        out += [f["properties"] for f in got]
        print(f"  {min(i + CHUNK, len(cells))}/{len(cells)} cells", flush=True)
    return pd.DataFrame(out).set_index("i").sort_index()


def main() -> None:
    rule_file = Path(sys.argv[1])
    ee = C.ee_init()
    s = pd.read_csv(C.HERE / "sample.csv")
    lab = pd.read_csv(C.HERE / "labels_final.csv")
    W = pd.read_csv(C.HERE / "strata_areas.csv")
    rows = []
    for area in C.AREAS:
        cells = in_area(ee, flood_cells(area), area)
        print(f"{area}: {len(cells)} flooded cells ({cells.ha.sum():,.0f} ha)")
        maps = {k: img for k, (img, _) in C.public_maps(ee).items()}
        maps["rule1"] = ee.Image(f"{C.ASSETS}/{rule_file.stem}_{area}").unmask(0).rename("rule1")
        frac = map_fractions(ee, cells, ee.Image.cat(list(maps.values())))
        for m in maps:
            rows.append({"area": area, "map": m, "flooded_crop_ha": float((frac[m].fillna(0) * cells.ha).sum())})
        with rasterio.open(C.RAW / "farmland" / "asap_mask_crop_v04.tif") as src:
            v = np.array([x[0] for x in src.sample(zip(cells.lon, cells.lat))]).astype(float)
        v = np.where((v >= 5) & (v <= 100), v / 100, 0)                 # ASAP value = % of the cell that is crop
        rows.append({"area": area, "map": "asap_v04", "flooded_crop_ha": float((v * cells.ha).sum())})

        # reference estimate, independent of any map
        pts = s[s.area == area].merge(lab, on="id")
        pts = pts[pts.cropland_avg.notna()]                              # labelled (mean of the two labellers)
        near = np.array([((abs(cells.lat - r.lat) <= CELL / 2) & (abs(cells.lon - r.lon) <= CELL / 2)).any()
                         for r in pts.itertuples()])
        w = W[W.area == area].set_index("stratum").share.to_dict()
        total = W[W.area == area].ha.sum()
        for name, avg, share in (("reference: cropland", "cropland_avg", "share_avg"),
                                 ("reference: cropped 2025", "crop_avg", "share_crop_avg")):
            ok = pts[share].notna().to_numpy()
            for label, y, keep in ((f"{name} (share of box)", pts[share].fillna(0).to_numpy() * near, ok),
                                   (f"{name}, upper bound (box holds it)", pts[avg].to_numpy() * near, np.ones(len(pts), bool))):
                est, se = E.area(np.asarray(y, float)[keep], pts.stratum.to_numpy()[keep], w)
                rows.append({"area": area, "map": label, "flooded_crop_ha": est * total,
                             "ci_low_ha": max(0, est - 1.96 * se) * total, "ci_high_ha": (est + 1.96 * se) * total})
        rows.append({"area": area, "map": "all flooded land", "flooded_crop_ha": cells.ha.sum()})
    out = pd.DataFrame(rows)
    (C.HERE / "results").mkdir(exist_ok=True)
    out.to_csv(C.HERE / "results" / "flooded_cropland.csv", index=False)
    print(out.round(0).to_string(index=False))


if __name__ == "__main__":
    main()
