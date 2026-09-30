"""
Step 4 - Images for the labelling tool (METHODOLOGY.md section 4).

For every point in a points file (pilot_points.csv or sample.csv) and for
2025 (the year we label) and 2024 (context only, to recognise fallow: a field
cropped in 2024 and left in 2025) this makes:
  - a strip of 12 monthly Sentinel-2 L2A images, true colour;
  - the same strip in false colour (near-infrared as red, so vegetation is red);
  - the monthly NDVI of the point's 10 m pixel and the median of the ~500 m
    square around it (for the "harvested earlier than the grass" cue).

Each point is one Earth Engine request (a 51 x 51 pixel, 10 m grid for all 12
months), so a few hundred points take a few minutes. Months with no clear
image are drawn grey with "no clear image".

Outputs: cropland/label_tool/img/<id>_<year>_tc.png, <id>_<year>_fc.png and
         cropland/label_tool/data_<set>.js (points, NDVI, links) for the tool.

Run from group_repo:
  python cropland/04_image_strips.py pilot     (uses pilot_points.csv)
  python cropland/04_image_strips.py sample    (uses sample.csv)
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

import common as C

BOX = 51                       # pixels per side, 10 m each (~510 m)
SCALE = 3                      # thumbnail upscaling, nearest neighbour
YEARS = (2025, 2024)
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
TOOL = C.HERE / "label_tool"
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
            ImageDraw.Draw(tile).text((8, size // 2 - 6), "no clear image", fill=(60, 60, 60))
        else:
            rgb = [stretch(b4, .3), stretch(b3, .3), stretch(b2, .3)] if kind == "tc" \
                else [stretch(b8, .5), stretch(b4, .3), stretch(b3, .3)]
            arr = np.dstack(rgb)
            arr[np.isnan(b4)] = 190                            # cloud-masked pixels grey, like empty months
            tile = Image.fromarray(arr.astype(np.uint8)).resize((size, size), Image.NEAREST)
        d = ImageDraw.Draw(tile)
        c0, c1 = (BOX // 2) * SCALE - 1, (BOX // 2 + 1) * SCALE     # the point's own 10 m pixel
        d.rectangle([c0, c0, c1, c1], outline=(255, 230, 0), width=1)
        d.rectangle([c0 - 30, c0 - 30, c1 + 30, c1 + 30], outline=(255, 230, 0))   # ~110 m guide box
        d.rectangle([0, 0, 30, 13], fill=(0, 0, 0)); d.text((3, 1), MONTHS[m], fill=(255, 255, 255))
        tiles.append(tile)
    out = Image.new("RGB", (size * 6 + 5 * 4, size * 2 + 4), (255, 255, 255))
    for m, t in enumerate(tiles):
        out.paste(t, ((m % 6) * (size + 4), (m // 6) * (size + 4)))
    return out


def ndvi(data):
    b4, b8 = data[:, 2], data[:, 3]
    with np.errstate(invalid="ignore", divide="ignore"):
        v = (b8 - b4) / (b8 + b4)
    centre = v[:, BOX // 2, BOX // 2]
    hood = np.nanmedian(v.reshape(12, -1), axis=1)
    r = lambda a: [None if np.isnan(x) else round(float(x), 3) for x in a]
    return r(centre), r(hood)


def one(ee, row):
    curves = {}
    for year in YEARS:
        data = fetch(ee, row.lat, row.lon, year)
        strip(data, "tc").save(IMG / f"{row.id}_{year}_tc.png", optimize=True)
        strip(data, "fc").save(IMG / f"{row.id}_{year}_fc.png", optimize=True)
        curves[year] = ndvi(data)
    d = 0.003
    return {"id": row.id, "lat": row.lat, "lon": row.lon,
            "ndvi": curves[2025][0], "ndvi_500m": curves[2025][1], "ndvi_2024": curves[2024][0],
            "labellers": [getattr(row, "labeller_1", ""), getattr(row, "labeller_2", "")],
            "esri": ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
                     f"?bbox={row.lon - d},{row.lat - d},{row.lon + d},{row.lat + d}&bboxSR=4326&imageSR=3857"
                     "&size=400,400&format=jpg&f=image"),
            "google": f"https://www.google.com/maps/@{row.lat},{row.lon},250m/data=!3m1!1e3",
            "wayback": f"https://livingatlas.arcgis.com/wayback/#mapCenter={row.lon}%2C{row.lat}%2C17",
            "eo": (f"https://apps.sentinel-hub.com/eo-browser/?zoom=16&lat={row.lat}&lng={row.lon}"
                   f"&fromTime={C.YEAR}-01-01&toTime={C.YEAR}-12-31")}


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
