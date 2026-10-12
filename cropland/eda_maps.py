"""
EDA of the public cropland maps: why a checked cropland number is needed
(report: context, business and data understanding).

What it measures, for the five Aweil counties, Bor South, a strip along the
Lol river and the whole country:
  1. crop share per map, per county and per state, next to CFSAM and FAOSTAT;
  2. how many of the 7 strata maps call a pixel crop (0-7), and how much the
     crop class of every two maps overlaps;
  3. how the yearly maps (Esri 2017-2025, Dynamic World 2016-2025) change from
     one year to the next with no real change on the ground;
  4. flooded cropland per map in 2022 and 2025 (NASA flood masks, course data),
     and whether a "flood inundating cropland" trigger would fire.

How. Earth Engine evaluates every map on a fine grid (~10 m in the study
areas, ~15 m nationally) and counts the crop pixels inside every cell of the
NASA flood grid (1/480 degree, ~232 m). Counting at the fine grid matters:
reading a map at a coarse scale uses Earth Engine's pyramids, which drop rare
classes such as crop. The counts are exported as assets in your Earth Engine
project (batch tasks, no time limit), downloaded once into
raw_data/cropland/eda/ (not in git), and everything after that runs locally.
Because the counts sit on the flood grid, the flood overlay is a plain join.

Run order (eda_public_maps.ipynb does it):
    python cropland/eda_maps.py export [zoa stab national]   start the export tasks
                                       (7 batch tasks; on a free project they can queue for hours)
    python cropland/eda_maps.py status                       see whether they are done
    python cropland/eda_maps.py download [names]             save them to raw_data/cropland/eda/
Earth Engine project: set CROPLAND_EE_PROJECT=<your project> first (Windows).

The maps are made crop / not crop exactly as for the strata (common.py,
Kerner et al. 2024). Agreement between maps is not accuracy: only the
labelled sample says which map is right.
"""

import json
import os
import sys
from itertools import combinations
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

import common as C

PROJECT = os.environ.get("CROPLAND_EE_PROJECT", C.GROUP_PROJECT)
ASSETS = f"projects/{PROJECT}/assets/cropland_eda"
CACHE = C.OUT / "eda"                               # downloaded counts, not in git
CACHE.mkdir(parents=True, exist_ok=True)

# course data: raw_data/ in the repo, or the course folder next to the repo
COURSE = next((p for p in (C.RAW, C.REPO.parent / "data-JBG060-2026") if (p / "flood_masks").exists()), C.RAW)
ADMIN = COURSE / "Administrative boundaries"

GRID = 1 / 480                                       # NASA MCDWD cell, degrees (~232 m)
SUB = {"zoa": 24, "stab": 12, "national": 15}       # fine pixels per cell side: ~9.6, ~19 and ~15 m
MAPS = ["worldcover_2021", "glad_2019", "deafrica_2019", "worldcereal_2021",
        "esri_2025", "dynamicworld_2025", "gfsad_2015"]          # the 7 strata maps
EXTRA = ["esri_2022", "dynamicworld_2022"]                       # same products, the 2022 flood year
PAIRS = list(combinations(MAPS, 2))
ESRI_YEARS = list(range(2017, 2026))
DW_YEARS = list(range(2016, 2026))
TILES = {"h20v08": (20, 10), "h21v08": (30, 10)}                 # flood tile -> (west lon, north lat)


# ---------------------------------------------------------------- Earth Engine side

def esri(ee, year):
    col = ee.ImageCollection("projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS")
    return col.filterDate(f"{year}-01-01", f"{year + 1}-01-01").mosaic().eq(5).unmask(0).toByte()


def dynamic_world(ee, year, region):
    """Most common Dynamic World class over the year; crop = class 4 (same as common.py)."""
    col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(region)
    return col.filterDate(f"{year}-01-01", f"{year + 1}-01-01").select("label").mode().eq(4).unmask(0).toByte()


def map_stack(ee, region):
    """The 7 strata maps (as in common.public_maps) plus Esri and Dynamic World for 2022."""
    maps = {k: img for k, (img, _) in C.public_maps(ee).items()}
    maps["dynamicworld_2025"] = dynamic_world(ee, 2025, region)   # same map, bounded for speed
    maps["esri_2022"] = esri(ee, 2022)
    maps["dynamicworld_2022"] = dynamic_world(ee, 2022, region)
    return {k: v.rename(k) for k, v in maps.items()}


def _proj(ee, step):
    return ee.Projection("EPSG:4326", [step, 0, 0, 0, -step, 0])


def _counts(ee, img, sub):
    """Number of fine pixels per flood cell where img is 1 (img evaluated on a grid sub times finer)."""
    fine = img.reproject(_proj(ee, GRID / sub))
    return fine.reduceResolution(ee.Reducer.sum().unweighted(), maxPixels=sub * sub + 1).reproject(_proj(ee, GRID))


def admin(level):
    return gpd.read_file(ADMIN / f"ssd_admin{level}.geojson")


def _ee_geom(ee, geom, simplify=0.0):
    geom = geom.simplify(simplify) if simplify else geom
    return ee.Geometry(json.loads(gpd.GeoSeries([geom], crs=4326).to_json())["features"][0]["geometry"])


def grid_box(bounds, pad=2):
    """Bounds snapped outwards to the flood grid: (west, south, east, north, width, height)."""
    w, s, e, n = bounds
    w, s = np.floor(w / GRID - pad) * GRID, np.floor(s / GRID - pad) * GRID
    e, n = np.ceil(e / GRID + pad) * GRID, np.ceil(n / GRID + pad) * GRID
    return w, s, e, n, int(round((e - w) / GRID)), int(round((n - s) / GRID))


def _export(ee, img, name, bounds):
    w, s, e, n, _, _ = grid_box(bounds)
    task = ee.batch.Export.image.toAsset(
        image=img, description=f"eda_{name}", assetId=f"{ASSETS}/{name}",
        region=ee.Geometry.Rectangle([w, s, e, n], None, False), crs="EPSG:4326",
        crsTransform=[GRID, 0, w, 0, -GRID, n], maxPixels=1e10)
    task.start()
    print(f"started {name} ({task.id})")


def export(ee, parts=("zoa", "stab", "national")):
    """Start the batch exports; parts picks which (python cropland/eda_maps.py export stab)."""
    try:
        ee.data.createAsset({"type": "FOLDER"}, ASSETS)
    except ee.EEException:
        pass                                                      # folder exists
    counties = admin(2)
    for area, names in C.AREAS.items():
        geom = counties[counties.adm2_name.isin(names)].dissolve().geometry.iloc[0]
        region = _ee_geom(ee, geom)
        if "zoa" in parts:
            maps = map_stack(ee, region)
            n = ee.Image.cat([maps[m] for m in MAPS]).reduce(ee.Reducer.sum())
            bands = [maps[m] for m in MAPS + EXTRA]
            bands += [n.eq(k).rename(f"agree_{k}") for k in range(8)]
            bands += [maps[a].And(maps[b]).rename(f"pair_{i}_{j}") for (i, a), (j, b)
                      in combinations(enumerate(MAPS), 2)]
            bands += [ee.Image(1).clip(_ee_geom(ee, g)).unmask(0).rename(f"in_{c.replace(' ', '_')}")
                      for c, g in zip(counties.adm2_name, counties.geometry) if c in names]
            _export(ee, _counts(ee, ee.Image.cat(bands).toByte(), SUB["zoa"]).toUint16(), f"zoa_{area}", geom.bounds)
        if "stab" in parts:
            # same product, every year: does the crop class move without real change on the ground?
            # One export per product at ~19 m: all years at ~10 m in one task ran out of memory.
            for p, years in (("esri", ESRI_YEARS), ("dw", DW_YEARS)):
                imgs = [esri(ee, y) if p == "esri" else dynamic_world(ee, y, region) for y in years]
                bands = [img.rename(f"{p}_{y}") for img, y in zip(imgs, years)]
                bands += [a.And(b).rename(f"{p}_keep_{y}") for a, b, y in zip(imgs, imgs[1:], years)]
                total = ee.Image.cat(imgs).reduce(ee.Reducer.sum())
                bands += [total.gte(1).rename(f"{p}_any"), total.eq(len(years)).rename(f"{p}_all")]
                _export(ee, _counts(ee, ee.Image.cat(bands).toByte(), SUB["stab"]).toUint16(),
                        f"stab_{p}_{area}", geom.bounds)

    if "national" in parts:
        country = admin(0).geometry.iloc[0]
        region = _ee_geom(ee, country, 0.01)
        maps = map_stack(ee, region)
        n = ee.Image.cat([maps[m] for m in MAPS]).reduce(ee.Reducer.sum())
        bands = [maps[m] for m in MAPS + EXTRA] + [n.eq(k).rename(f"agree_{k}") for k in range(8)]
        _export(ee, _counts(ee, ee.Image.cat(bands).toByte(), SUB["national"]).toUint8(), "national", country.bounds)


def status(ee):
    for t in ee.data.getTaskList()[:20]:
        if t.get("description", "").startswith("eda_"):
            print(t["description"], t["state"], t.get("error_message", ""))


def download(ee, names=None):
    """Save every exported asset as a compressed .npz of band arrays (rows from north, cols from west)."""
    names = names or ([f"zoa_{a}" for a in C.AREAS] + [f"stab_{p}_{a}" for p in ("esri", "dw") for a in C.AREAS]
                      + ["national"])
    for name in names:
        out = CACHE / f"{name}.npz"
        if out.exists():
            print(f"{out.name} already there")
            continue
        img = ee.Image(f"{ASSETS}/{name}")
        info = img.getInfo()
        bands = [b["id"] for b in info["bands"]]
        w, h = info["bands"][0]["dimensions"]
        x0, y0 = info["bands"][0]["crs_transform"][2], info["bands"][0]["crs_transform"][5]
        itemsize = 2 if info["bands"][0]["data_type"].get("max", 255) > 255 else 1
        rows = max(1, int(12e6 // (w * len(bands) * itemsize)))            # well under the 48 MB request limit
        parts = []
        for r in range(0, h, rows):
            nr = min(rows, h - r)
            arr = ee.data.computePixels({
                "expression": img, "fileFormat": "NUMPY_NDARRAY",
                "grid": {"dimensions": {"width": w, "height": nr},
                         "affineTransform": {"scaleX": GRID, "shearX": 0, "translateX": x0,
                                             "shearY": 0, "scaleY": -GRID, "translateY": y0 - r * GRID},
                         "crsCode": "EPSG:4326"}})
            parts.append(arr)
            print(f"  {name}: rows {r + nr}/{h}", flush=True)
        arr = np.concatenate(parts)
        np.savez_compressed(out, west=x0, north=y0, **{b: arr[b] for b in bands})
        print(f"saved {out}")


# ---------------------------------------------------------------- local side

NAMES = {"worldcover_2021": "WorldCover 2021", "glad_2019": "GLAD 2019", "deafrica_2019": "DE Africa 2019",
         "worldcereal_2021": "WorldCereal 2021", "esri_2025": "Esri 2025", "dynamicworld_2025": "Dynamic World 2025",
         "gfsad_2015": "GFSAD 2015", "esri_2022": "Esri 2022", "dynamicworld_2022": "Dynamic World 2022",
         "asap_v04": "ASAP v04 (course data)"}
TABLES = C.REPO / "deliverables" / "cropland_report" / "tables"
FIGURES = C.REPO / "deliverables" / "cropland_report" / "figures"
LOL = C.HERE / "lol_river_osm.geojson"                 # OpenStreetMap, Overpass 10 Oct 2026


def load(name):
    """One export as {band: 2-D count array}, its grid origin (west, north) and the cell area in ha per row."""
    z = np.load(CACHE / f"{name}.npz")
    bands = {k: z[k] for k in z.files if k not in ("west", "north")}
    h = next(iter(bands.values())).shape[0]
    north = float(z["north"])
    lat = north - (np.arange(h) + 0.5) * GRID
    ha_row = GRID * 111_320 * np.cos(np.radians(lat)) * GRID * 110_574 / 1e4    # cells shrink towards the poles
    return bands, float(z["west"]), north, ha_row


def global_index(lat, lon):
    """Row and column of a flood cell in one global 1/480 degree grid, so tables join exactly."""
    return np.round((90 - np.asarray(lat)) / GRID - 0.5).astype(np.int64), np.round((np.asarray(lon) + 180) / GRID - 0.5).astype(np.int64)


def zoa_cells(area):
    """One row per flood cell touching a study area: share of the cell inside each county, cell area,
    and every map, agreement and pair band as a share of the cell (0-1)."""
    bands, west, north, ha_row = load(f"zoa_{area}")
    n = SUB["zoa"] ** 2
    h, w = next(iter(bands.values())).shape
    rows, cols = np.indices((h, w))
    df = pd.DataFrame({"lat": (north - (rows + 0.5) * GRID).ravel(), "lon": (west + (cols + 0.5) * GRID).ravel(),
                       "ha": np.repeat(ha_row, w)})
    for k, v in bands.items():
        df[k] = (v.ravel() / n).astype(np.float32)
    inside = [k for k in bands if k.startswith("in_")]
    df["inside"] = df[inside].sum(axis=1)
    df = df[df.inside > 0].reset_index(drop=True)
    df["gr"], df["gc"] = global_index(df.lat, df.lon)
    df["asap_v04"] = asap_at(df.lat.to_numpy(), df.lon.to_numpy())
    return df


def asap_at(lat, lon):
    """ASAP v04 crop fraction (0-1) of the ~500 m ASAP cell under each point (course data)."""
    import rasterio
    with rasterio.open(COURSE / "farmland" / "asap_mask_crop_v04.tif") as src:
        win = rasterio.windows.from_bounds(lon.min() - 0.01, lat.min() - 0.01, lon.max() + 0.01, lat.max() + 0.01, src.transform)
        win = win.round_offsets().round_lengths()
        a = src.read(1, window=win)
        t = src.window_transform(win)
    r = np.clip(((lat - t.f) / t.e).astype(int), 0, a.shape[0] - 1)
    c = np.clip(((lon - t.c) / t.a).astype(int), 0, a.shape[1] - 1)
    v = a[r, c].astype(np.float32)
    return np.where(v <= 100, v / 100, 0).astype(np.float32)        # value = % of the cell that is crop


def county_columns(df):
    return [k for k in df.columns if k.startswith("in_")]


def crop_shares(df, maps=None):
    """Crop area (ha) and share of land per map, for every county and for the whole area."""
    maps = maps or MAPS + EXTRA + ["asap_v04"]
    out = []
    groups = {c[3:].replace("_", " "): df[c] for c in county_columns(df)}
    if len(groups) > 1:
        groups["all counties"] = df.inside
    for g, frac in groups.items():
        land = (frac * df.ha).sum()
        for m in maps:
            crop = (df[m] * frac * df.ha).sum()
            out.append({"unit": g, "map": m, "land_ha": land, "crop_ha": crop, "crop_pct": 100 * crop / land})
    return pd.DataFrame(out)


def agreement(df):
    """Share of land on which k of the 7 strata maps say crop (k = 0..7), per county and overall."""
    groups = {c[3:].replace("_", " "): df[c] for c in county_columns(df)}
    if len(groups) > 1:
        groups["all counties"] = df.inside
    rows = []
    for g, frac in groups.items():
        land = (frac * df.ha).sum()
        rows.append({"unit": g, **{f"{k} maps": 100 * (df[f"agree_{k}"] * frac * df.ha).sum() / land for k in range(8)}})
    return pd.DataFrame(rows).set_index("unit")


def pairwise(df):
    """For every two strata maps: overlap of their crop class (intersection over union) and Cohen's kappa."""
    w = df.inside * df.ha
    a = {m: (df[m] * w).sum() / w.sum() for m in MAPS}
    iou, kap, agree = (pd.DataFrame(np.nan, index=MAPS, columns=MAPS) for _ in range(3))
    for i, j in combinations(range(len(MAPS)), 2):
        mi, mj = MAPS[i], MAPS[j]
        both = (df[f"pair_{i}_{j}"] * w).sum() / w.sum()
        union = a[mi] + a[mj] - both
        po = 1 - (a[mi] + a[mj] - 2 * both)                     # same class (crop or not crop)
        pe = a[mi] * a[mj] + (1 - a[mi]) * (1 - a[mj])
        for t, v in ((iou, both / union if union else np.nan), (kap, (po - pe) / (1 - pe)), (agree, po)):
            t.loc[mi, mj] = t.loc[mj, mi] = v
    return iou, kap, agree


def flood_cells(tile, year, start="06-01", end="12-31"):
    """Flood days per NASA MCDWD cell between start and end of a year, recurring and unusual separately."""
    parts = []
    for kind in ("recurring", "unusual"):
        f = COURSE / "flood_masks" / f"compact_{kind}" / f"flood_events_{tile}_{year}.parquet"
        d = pd.read_parquet(f, columns=["date", "lat", "lon"])
        day = pd.to_datetime(d.date.astype(str))
        d = d[(day >= f"{year}-{start}") & (day <= f"{year}-{end}")]
        gr, gc = global_index(d.lat.astype(float), d.lon.astype(float))
        parts.append(pd.DataFrame({"gr": gr, "gc": gc}).value_counts().rename(f"days_{kind}"))
    out = pd.concat(parts, axis=1).fillna(0).reset_index()
    out["days"] = out.days_recurring + out.days_unusual           # a cell is one class per day
    return out


def flooded_crop(df, flood, maps=None, min_days=1, unit="inside"):
    """Cropland under water per map: crop share x flooded cell area, for cells flooded >= min_days."""
    maps = maps or MAPS + EXTRA + ["asap_v04"]
    f = df.merge(flood[flood.days >= min_days], on=["gr", "gc"], how="inner")
    w = f[unit] * f.ha
    rows = [{"map": m, "flooded_crop_ha": (f[m] * w).sum(), "map_crop_ha": (df[m] * df[unit] * df.ha).sum()}
            for m in maps]
    out = pd.DataFrame(rows)
    out["share_of_map_crop_flooded_pct"] = 100 * out.flooded_crop_ha / out.map_crop_ha
    out["flooded_land_ha"] = w.sum()
    return out


def lol_distance_km(df):
    """Distance from every cell centre to the Lol river (OSM line), in km (UTM zone 35N)."""
    river = gpd.read_file(LOL).to_crs(32635).union_all()
    pts = gpd.GeoSeries(gpd.points_from_xy(df.lon, df.lat), crs=4326).to_crs(32635)
    return pts.distance(river).to_numpy() / 1000


# national: arrays, not tables (24 M cells)

def national():
    """National counts (uint8, out of 225 fine pixels), the county of every cell and the cell area grid."""
    import rasterio.features
    from affine import Affine
    bands, west, north, ha_row = load("national")
    h, w = next(iter(bands.values())).shape
    counties = admin(2)
    label = rasterio.features.rasterize(((g, i + 1) for i, g in enumerate(counties.geometry)), out_shape=(h, w),
                                        transform=Affine(GRID, 0, west, 0, -GRID, north), fill=0, dtype="int32")
    return bands, label, counties, west, north, ha_row


def national_by_county(nat):
    """Crop area (ha) per map and county from the national counts, plus ASAP."""
    bands, label, counties, west, north, ha_row = nat
    h, w = label.shape
    ha = np.repeat(ha_row[:, None], w, axis=1).astype(np.float32)
    n = SUB["national"] ** 2
    out = pd.DataFrame({"county": counties.adm2_name, "state": counties.adm1_name})
    out["land_ha"] = np.bincount(label.ravel(), weights=ha.ravel(), minlength=len(counties) + 1)[1:]
    for m in MAPS + EXTRA + [f"agree_{k}" for k in range(8)]:
        out[m] = np.bincount(label.ravel(), weights=(bands[m].astype(np.float32) / n * ha).ravel(),
                             minlength=len(counties) + 1)[1:]
    lat = north - (np.arange(h) + 0.5) * GRID
    lon = west + (np.arange(w) + 0.5) * GRID
    asap = np.empty((h, w), np.float32)
    for r in range(0, h, 500):                                       # in bands of rows to keep memory low
        la, lo = np.meshgrid(lat[r:r + 500], lon, indexing="ij")
        asap[r:r + 500] = asap_at(la.ravel(), lo.ravel()).reshape(la.shape)
    out["asap_v04"] = np.bincount(label.ravel(), weights=(asap * ha).ravel(), minlength=len(counties) + 1)[1:]
    return out


def national_flooded_crop(nat, year, min_days=1):
    """Flooded cropland per map in the whole country (south of 10 N, where the flood tiles reach)."""
    bands, label, counties, west, north, ha_row = nat
    flood = pd.concat([flood_cells(t, year) for t in TILES])
    flood = flood[flood.days >= min_days]
    r = (flood.gr - np.round((90 - north) / GRID)).astype(int).to_numpy()
    c = (flood.gc - np.round((west + 180) / GRID)).astype(int).to_numpy()
    ok = (r >= 0) & (r < label.shape[0]) & (c >= 0) & (c < label.shape[1])
    r, c = r[ok], c[ok]
    inside = label[r, c] > 0
    r, c = r[inside], c[inside]
    ha = ha_row[r]
    n = SUB["national"] ** 2
    rows = [{"map": m, "flooded_crop_ha": float((bands[m][r, c] / n * ha).sum())} for m in MAPS + EXTRA]
    lat = north - (r + 0.5) * GRID
    lon = west + (c + 0.5) * GRID
    rows.append({"map": "asap_v04", "flooded_crop_ha": float((asap_at(lat, lon) * ha).sum())})
    out = pd.DataFrame(rows)
    out["flooded_land_ha"] = ha.sum()
    out["year"] = year
    return out


def stability(area):
    """Esri and Dynamic World, every year: crop share of the area, and how much of one year's crop is crop the next."""
    rows = []
    for p, years in (("esri", ESRI_YEARS), ("dw", DW_YEARS)):
        f = CACHE / f"stab_{p}_{area}.npz"
        if not f.exists():
            continue
        bands, west, north, ha_row = load(f"stab_{p}_{area}")
        h, w = next(iter(bands.values())).shape
        frac = zoa_inside_on_grid(area, west, north, h, w)
        ha = np.repeat(ha_row[:, None], w, axis=1) * frac
        n = SUB["stab"] ** 2
        land = ha.sum()
        for y in years:
            crop = (bands[f"{p}_{y}"] / n * ha).sum()
            keep = (bands[f"{p}_keep_{y}"] / n * ha).sum() if f"{p}_keep_{y}" in bands else np.nan
            rows.append({"area": area, "product": p, "year": y, "crop_pct": 100 * crop / land,
                         "crop_ha": crop, "still_crop_next_year_pct": 100 * keep / crop if crop else np.nan})
        for k in ("any", "all"):
            rows.append({"area": area, "product": p, "year": k,
                         "crop_pct": 100 * (bands[f"{p}_{k}"] / n * ha).sum() / land})
    return pd.DataFrame(rows)


def zoa_inside_on_grid(area, west, north, h, w):
    """Share of every cell inside the study area, read from the zoa export (same grid, maybe other origin)."""
    bands, w0, n0, _ = load(f"zoa_{area}")
    inside = sum(v.astype(np.float32) for k, v in bands.items() if k.startswith("in_")) / SUB["zoa"] ** 2
    dr, dc = int(round((north - n0) / GRID)), int(round((w0 - west) / GRID))   # zoa cell (i, j) = this cell (i + dr, j + dc)
    out = np.zeros((h, w), np.float32)
    hh, ww = inside.shape
    rd, rs = max(0, dr), max(0, -dr)
    cd, cs = max(0, dc), max(0, -dc)
    nr, nc = min(h - rd, hh - rs), min(w - cd, ww - cs)
    out[rd:rd + nr, cd:cd + nc] = inside[rs:rs + nr, cs:cs + nc]
    return out


def ee_init():
    import ee
    ee.Initialize(project=PROJECT)
    return ee


if __name__ == "__main__":
    step = {"export": export, "status": status, "download": download}[sys.argv[1]]
    step(ee_init(), *([sys.argv[2:]] if len(sys.argv) > 2 else []))
