"""
Step 4 - Images for the labelling tool (METHODOLOGY.md section 4).

For every point in a points file (pilot_points.csv or sample.csv) and for
2025 (the year we label) and 2024 (context only, to recognise fallow: a field
cropped in 2024 and left in 2025) this makes:
  - a strip of 12 monthly Sentinel-2 L2A images, true colour;
  - the same strip in false colour (near-infrared as red, so vegetation is red);
  - the monthly NDVI of the box we label (median of its 21 x 21 pixels, with
    the 10th-90th percentile band) and the median of the ~500 m square around
    it (for the "harvested earlier than the grass" cue);
  - the box split into up to 3 patches whose NDVI curves differ (k-means on the
    2025 curves of its pixels), with each patch's 2025 and 2024 curve, its
    share of the box and a map of where it is. A field in a box of grass gets
    its own curve instead of vanishing into the box median;
  - up to 3 small spots (30 m) of the box that differ most from the 500 m
    square the way a field does (barer in Apr-May, browner in Sep-Nov; trees
    and never-green spots left out), each with its 2025 and 2024 curve and a
    map of where it is. The patches are large and mostly follow the 500 m
    curve; a small field shows up better as a spot;
  - the monthly Sentinel-1 VH radar backscatter of the box (dB), which sees
    through the clouds of the rainy season;
  - the capture date of the Esri high-resolution image at the point, from
    Esri's imagery metadata (needs internet; empty if Esri does not answer).
The yellow square on every image is the box we label: 210 m x 210 m
(common.BOX_M), drawn in the same place as the "outer box" of the first version.

Each point is one Earth Engine request (a 51 x 51 pixel, 10 m grid for all 12
months), so a few hundred points take a few minutes. Months with no clear
image are drawn grey with "no clear image".

Outputs: cropland/label_tool/img/<id>_<year>_tc.webp, <id>_<year>_fc.webp and
         cropland/label_tool/data_<set>.js (points, NDVI, links) for the tool.

Run from group_repo:
  python cropland/04_image_strips.py pilot     (uses pilot_points.csv)
  python cropland/04_image_strips.py sample    (uses sample.csv)
"""

import json
import os
import sys
from itertools import combinations
import urllib.parse
import urllib.request
import warnings
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")      # avoids a harmless core-count warning on Windows
from sklearn.cluster import KMeans  # noqa: E402

import common as C

BOX = 51                       # pixels per side, 10 m each (~510 m)
HALF = C.BOX_M // 20           # the box reaches 10 pixels each side of the centre pixel: 21 x 21 = 210 m
MIN_CLEAR = 0.5                # a month's box value needs at least half the box free of cloud
PATCH_GAP = 0.08               # patches are kept apart only if their curves differ by this much NDVI in some month
PATCH_MIN = 0.05               # and each covers at least 5% of the box
SPOT_PX = 3                    # spots: 3 x 3 pixels (30 m), 7 x 7 of them tile the 21 x 21 box
SPOT_N = 3                     # at most this many spots are shown
SPOT_MIN = 0.08                # a spot is shown only if it is barer (Apr-May) plus browner (Sep-Nov) than the 500 m square by this much NDVI
SPOT_TREE = 0.05               # spots greener than the 500 m square in Jan-Mar by this much are trees / shrub, not fields
SPOT_GREEN = 0.35              # spots that never reach this NDVI in Jun-Aug never grew anything
ESRI_HALF_DEG = 0.003         # high-resolution image: ~660 m square, the box is about a third of it
SCALE = 3                      # thumbnail upscaling, nearest neighbour
YEARS = (2025, 2024)
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
TOOL = C.HERE / "label_tool"
ESRI_META = "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/{}/query"
IMG = TOOL / "img"


def fetch(ee, lat, lon, year):
    """(12, 4, BOX, BOX) array of B2, B3, B4, B8 reflectance; NaN where no clear image."""
    pt = ee.Geometry.Point(lon, lat)
    months = C.s2_monthly(ee, pt.buffer(1000), year)
    bands = ["B2", "B3", "B4", "B8"]
    stack = ee.Image.cat([m.select(bands).rename([f"{b}_{i:02d}" for b in bands])
                          for i, m in enumerate(months)]).unmask(-1)
    dx, dy = 10 / (111_320 * np.cos(np.radians(lat))), 10 / 110_540
    arr = ee.data.computePixels({
        "expression": stack, "fileFormat": "NUMPY_NDARRAY",
        "grid": {"dimensions": {"width": BOX, "height": BOX}, "crsCode": "EPSG:4326",
                 "affineTransform": {"scaleX": dx, "shearX": 0, "translateX": lon - dx * BOX / 2,
                                     "shearY": 0, "scaleY": -dy, "translateY": lat + dy * BOX / 2}}})
    out = np.stack([[arr[f"{b}_{i:02d}"] for b in bands] for i in range(12)]).astype(float)
    out[out < 0] = np.nan
    return out


def stretch(x, hi):
    return np.clip(np.nan_to_num(x) / hi, 0, 1) ** 0.8 * 255


def strip(data, kind):
    tiles = []
    size = BOX * SCALE
    for m in range(12):
        b2, b3, b4, b8 = data[m]
        if np.isnan(b4).all():
            tile = Image.new("RGB", (size, size), (190, 190, 190))
            ImageDraw.Draw(tile).text((8, size - 16), "no clear image", fill=(60, 60, 60))
        else:
            rgb = [stretch(b4, .3), stretch(b3, .3), stretch(b2, .3)] if kind == "tc" \
                else [stretch(b8, .5), stretch(b4, .3), stretch(b3, .3)]
            arr = np.dstack(rgb)
            arr[np.isnan(b4)] = 190                            # cloud-masked pixels grey, like empty months
            tile = Image.fromarray(arr.astype(np.uint8)).resize((size, size), Image.NEAREST)
        d = ImageDraw.Draw(tile)
        c0, c1 = (BOX // 2 - HALF) * SCALE - 1, (BOX // 2 + HALF + 1) * SCALE   # the 210 m box, lines just outside it
        d.rectangle([c0, c0, c1, c1], outline=(255, 230, 0), width=1)
        d.rectangle([0, 0, 30, 13], fill=(0, 0, 0)); d.text((3, 1), MONTHS[m], fill=(255, 255, 255))
        tiles.append(tile)
    out = Image.new("RGB", (size * 6 + 5 * 4, size * 2 + 4), (255, 255, 255))
    for m, t in enumerate(tiles):
        out.paste(t, ((m % 6) * (size + 4), (m // 6) * (size + 4)))
    return out


def _r(a, ok=True):
    """12 monthly values as a JSON list; None where missing or not clear enough."""
    return [None if (np.isnan(x) or not k) else round(float(x), 3) for x, k in zip(a, np.broadcast_to(ok, 12))]


def ndvi(data):
    """Box median, 10th and 90th percentile, 500 m median, plus the raw box pixels (12 x 441) for the patches."""
    b4, b8 = data[:, 2], data[:, 3]
    with np.errstate(invalid="ignore", divide="ignore"):
        v = (b8 - b4) / (b8 + b4)
    c = BOX // 2
    box = v[:, c - HALF:c + HALF + 1, c - HALF:c + HALF + 1].reshape(12, -1)
    clear = np.isfinite(box).mean(axis=1) >= MIN_CLEAR
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)             # all-NaN months
        lo, med, hi = np.nanpercentile(box, [10, 50, 90], axis=1)
        hood = np.nanmedian(v.reshape(12, -1), axis=1)
    return _r(med, clear), _r(lo, clear), _r(hi, clear), _r(hood), box, clear


def patches(box25, clear25, box24, clear24):
    """Split the box into up to 3 patches with different 2025 NDVI curves.

    k-means on each pixel's clear 2025 months (gaps filled with that month's box
    median). k = 2 or 3 is kept only if every patch covers PATCH_MIN of the box
    and every two patch curves differ by PATCH_GAP in some month; otherwise the
    box is one patch. Patches are ordered largest first. Returns the patches
    (share, 2025 curve, 2024 curve of the same pixels) and the patch of every
    box pixel, row by row from the north-west corner.
    """
    lab = np.zeros(box25.shape[1], int)
    if clear25.sum() >= 3:
        X = box25[clear25].T
        X = np.where(np.isnan(X), np.nanmedian(X, axis=0), X)
        for k in (2, 3):
            got = KMeans(k, n_init=10, random_state=C.SEED).fit_predict(X)
            shares = np.bincount(got, minlength=k) / len(got)
            curves = [np.median(X[got == j], axis=0) for j in range(k)]
            if shares.min() >= PATCH_MIN and min(np.abs(a - b).max() for a, b in combinations(curves, 2)) >= PATCH_GAP:
                lab = got
    order = np.argsort(-np.bincount(lab))
    lab = np.argsort(order)[lab]                                     # relabel: 0 = largest patch
    out = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        for j in range(lab.max() + 1):
            m = lab == j
            out.append({"share": round(float(m.mean()), 3),
                        "ndvi": _r(np.nanmedian(box25[:, m], axis=1), clear25),
                        "ndvi_2024": _r(np.nanmedian(box24[:, m], axis=1), clear24)})
    return out, "".join(map(str, lab))


def spots(box25, box24, hood25):
    """The up to SPOT_N small spots (3 x 3 pixels, 30 m) of the box that differ most from the 500 m square
    the way a field does: barer in Apr-May and browner in Sep-Nov (cues a and c).

    The box is cut into 7 x 7 non-overlapping spots. A spot's month counts when at least 5 of its 9 pixels
    are clear. Left out: spots greener than the 500 m square in Jan-Mar by SPOT_TREE (trees / shrub) and spots
    that never reach SPOT_GREEN in Jun-Aug (bare ground, water, roofs). Score = how much barer in Apr-May plus
    how much browner in Sep-Nov than the 500 m square; a spot is shown only if both are > 0 and the score is
    at least SPOT_MIN, and no two shown spots touch. Returns the spots (score, 2025 and 2024 curve, best first)
    and, for every box pixel, the spot it belongs to ("." for none), row by row from the north-west corner.
    """
    n, s = 2 * HALF + 1, SPOT_PX
    k = n // s
    h = np.array([np.nan if v is None else v for v in hood25])
    grid25, grid24 = box25.reshape(12, n, n), box24.reshape(12, n, n)
    cand = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        for r in range(k):
            for c in range(k):
                w25 = grid25[:, r * s:(r + 1) * s, c * s:(c + 1) * s].reshape(12, -1)
                w24 = grid24[:, r * s:(r + 1) * s, c * s:(c + 1) * s].reshape(12, -1)
                ok25, ok24 = np.isfinite(w25).sum(axis=1) >= 5, np.isfinite(w24).sum(axis=1) >= 5
                c25 = np.where(ok25, np.nanmedian(w25, axis=1), np.nan)
                if np.nanmean(c25[0:3] - h[0:3]) > SPOT_TREE or not np.nanmax(c25[5:8]) >= SPOT_GREEN:
                    continue
                bare, brown = np.nanmean(h[3:5] - c25[3:5]), np.nanmean(h[8:11] - c25[8:11])
                if not (bare > 0 and brown > 0 and bare + brown >= SPOT_MIN):
                    continue
                cand.append((bare + brown, r, c, c25, np.where(ok24, np.nanmedian(w24, axis=1), np.nan)))
    cand.sort(key=lambda t: -t[0])
    out, where = [], np.full((n, n), ".")
    for score, r, c, c25, c24 in cand:
        if len(out) == SPOT_N:
            break
        if any(max(abs(r - q["row"]), abs(c - q["col"])) <= 1 for q in out):
            continue                                                  # touches a spot already shown
        where[r * s:(r + 1) * s, c * s:(c + 1) * s] = str(len(out))
        out.append({"score": round(float(score), 3), "row": r, "col": c, "ndvi": _r(c25), "ndvi_2024": _r(c24)})
    return out, "".join(where.ravel())


def radar(ee, lat, lon, year: int = C.YEAR):
    """Monthly Sentinel-1 VH backscatter (dB), mean over the box; None for a month without a pass."""
    box = C.box(ee, lon, lat)
    s1 = (ee.ImageCollection("COPERNICUS/S1_GRD").filterBounds(box)
          .filter(ee.Filter.eq("instrumentMode", "IW"))
          .filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))      # as in features.py
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")).select("VH"))
    months = []
    for m in range(1, 13):
        col = s1.filterDate(ee.Date.fromYMD(year, m, 1), ee.Date.fromYMD(year, m, 1).advance(1, "month"))
        empty = ee.Image.constant(0).updateMask(0)
        months.append(ee.Image(ee.Algorithms.If(col.size().gt(0), col.mean(), empty)).rename(f"m{m:02d}"))
    got = ee.Image.cat(months).reduceRegion(ee.Reducer.mean(), box, 10).getInfo()
    return [None if got.get(f"m{m:02d}") is None else round(got[f"m{m:02d}"], 2) for m in range(1, 13)]


def esri_date(lat, lon):
    """Capture date, resolution and provider of the Esri image at a point (metadata layers, finest first)."""
    q = urllib.parse.urlencode({"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                                "spatialRel": "esriSpatialRelIntersects", "outFields": "SRC_DATE,SRC_RES,NICE_DESC",
                                "returnGeometry": "false", "f": "json"})
    for layer in range(9, 14):                     # 30 cm, 60 cm, 1.2 m, 2.4 m, 4.8 m metadata
        feats = None
        for _ in range(3):                         # the service sometimes times out
            try:
                with urllib.request.urlopen(ESRI_META.format(layer) + "?" + q, timeout=30) as r:
                    feats = json.load(r).get("features", [])
                break
            except (OSError, ValueError):
                pass
        if feats:
            a = feats[0]["attributes"]
            d = str(a.get("SRC_DATE") or "")
            if len(d) == 8:
                return {"date": f"{d[:4]}-{d[4:6]}-{d[6:]}", "res_m": a.get("SRC_RES"), "source": a.get("NICE_DESC")}
    return None


def one(ee, row):
    curves = {}
    for year in YEARS:
        data = fetch(ee, row.lat, row.lon, year)
        strip(data, "tc").save(IMG / f"{row.id}_{year}_tc.webp", quality=90, method=6)   # WebP: ~4x smaller than PNG, fits in git
        strip(data, "fc").save(IMG / f"{row.id}_{year}_fc.webp", quality=90, method=6)
        curves[year] = ndvi(data)
    parts, where = patches(curves[2025][4], curves[2025][5], curves[2024][4], curves[2024][5])
    sp, sp_where = spots(curves[2025][4], curves[2024][4], curves[2025][3])
    d = ESRI_HALF_DEG
    return {"id": row.id, "lat": row.lat, "lon": row.lon, "area": getattr(row, "area", "pilot"),
            "box_m": C.BOX_M, "esri_half_deg": d,
            "ndvi": curves[2025][0], "ndvi_p10": curves[2025][1], "ndvi_p90": curves[2025][2],
            "ndvi_500m": curves[2025][3], "ndvi_2024": curves[2024][0], "vh": radar(ee, row.lat, row.lon),
            "patches": parts, "patch_map": where, "spots": sp, "spot_map": sp_where,
            "labellers": [getattr(row, "labeller_1", ""), getattr(row, "labeller_2", "")],
            "esri_date": esri_date(row.lat, row.lon),
            "esri": ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
                     f"?bbox={row.lon - d},{row.lat - d},{row.lon + d},{row.lat + d}&bboxSR=4326&imageSR=3857"
                     "&size=400,400&format=jpg&f=image"),
            "google": f"https://www.google.com/maps/@{row.lat},{row.lon},250m/data=!3m1!1e3",
            "wayback": f"https://livingatlas.arcgis.com/wayback/#mapCenter={row.lon}%2C{row.lat}%2C17",
            "eo": (f"https://browser.dataspace.copernicus.eu/?zoom=16&lat={row.lat}&lng={row.lon}"
                   f"&fromTime={C.YEAR}-09-01T00:00:00.000Z&toTime={C.YEAR}-09-30T23:59:59.999Z"
                   "&datasetId=S2_L2A_CDAS&layerId=1_TRUE_COLOR")}


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    pts = pd.read_csv(C.HERE / ("pilot_points.csv" if which == "pilot" else "sample.csv"))
    IMG.mkdir(parents=True, exist_ok=True)
    ee = C.ee_init()
    with ThreadPoolExecutor(8) as pool:
        recs = list(pool.map(lambda r: one(ee, r), pts.itertuples()))
    (TOOL / f"data_{which}.js").write_text(f"window.POINTS_{which.upper()} = " + json.dumps(recs) + ";\n")
    print(f"{len(recs)} points written for '{which}'")


if __name__ == "__main__":
    main()
