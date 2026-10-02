"""Show what the cropland maps look like, on a demo window OUTSIDE the study AOIs.

The labelling of the team's sample must stay blind to the maps inside the AOIs,
so this figure uses a 6 km x 6 km window around Turalei (Twic county, Warrap),
about 49 km outside the buffered Aweil AOI. Every map is fetched for that window
and put on one 10 m UTM 35N grid (nearest neighbour), for display only.

Outputs (data/cropland/demo/):
  demo_maps_turalei.png         satellite image + each map's crop pixels
  demo_10m_to_30m_turalei.png   how 3 x 3 pixels of 10 m become one 30 m cell

Usage (repo root, global Python 3.13):
    python -m processing_data.cropland.demo_map_panels
"""

from __future__ import annotations

import math

import ee
import geedim  # noqa: F401
import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import requests
from matplotlib.colors import ListedColormap
from rasterio.enums import Resampling
from rasterio.transform import Affine
from rasterio.vrt import WarpedVRT
from shapely.geometry import Point, box

from processing_data.cropland.common import CROPLAND_DIR, aoi_geometry
from processing_data.cropland.download_ee_products import EE_PROJECT

OUT = CROPLAND_DIR / "demo"
CENTRE = (28.429351, 9.087426)   # OCHA populated places 2022: Turalei, Twic, Warrap
HALF = 3000                      # m, so the window is 6 km x 6 km
CRS = "EPSG:32635"
RES = 10


def window_grid():
    p = gpd.GeoSeries([Point(*CENTRE)], crs=4326).to_crs(CRS).iloc[0]
    x0 = math.floor((p.x - HALF) / 60) * 60
    y1 = math.ceil((p.y + HALF) / 60) * 60
    n = int(2 * HALF / RES)
    return [RES, 0, x0, 0, -RES, y1], (n, n)


def assert_outside_aois():
    tr, (h, w) = window_grid()
    win = gpd.GeoSeries([box(tr[2], tr[5] - h * RES, tr[2] + w * RES, tr[5])], crs=CRS).iloc[0]
    for a in ("aweil", "borsouth"):
        aoi = gpd.GeoSeries([aoi_geometry(a, "EPSG:4326")], crs=4326).to_crs(CRS).iloc[0]
        assert not win.intersects(aoi), f"demo window overlaps the {a} AOI"


def fetch(img: ee.Image, name: str, dtype="uint8") -> np.ndarray:
    tr, shape = window_grid()
    path = OUT / f"{name}.tif"
    if not path.exists():
        filled = img.unmask(255 if dtype == "uint8" else 0, False)
        filled.gd.prepareForExport(crs=CRS, crs_transform=tr, shape=shape, dtype=dtype).gd.toGeoTIFF(
            path, overwrite=True, max_requests=4)
    with rasterio.open(path) as s:
        return s.read()


def deafrica_mask() -> np.ndarray:
    """DE Africa is not in Earth Engine: fetch the covering 96 km tile and warp the window locally."""
    path = OUT / "deafrica_mask.tif"
    tr, (h, w) = window_grid()
    if not path.exists():
        win = gpd.GeoSeries([box(tr[2], tr[5] - h * RES, tr[2] + w * RES, tr[5])], crs=CRS).to_crs(4326).iloc[0]
        r = requests.get("https://explorer.digitalearth.africa/stac/search",
                         params={"collections": "crop_mask", "bbox": ",".join(map(str, win.bounds))},
                         timeout=120).json()
        out = np.full((h, w), 255, np.uint8)
        for k, feat in enumerate(r["features"]):   # the window can straddle tile edges
            href = feat["assets"]["mask"]["href"].replace(
                "s3://deafrica-services/", "https://deafrica-services.s3.af-south-1.amazonaws.com/")
            tile = OUT / f"deafrica_tile_{k}.tif"
            tile.write_bytes(requests.get(href, timeout=300).content)
            with rasterio.open(tile) as src, WarpedVRT(src, crs=CRS, transform=Affine(*tr), width=w, height=h,
                                                        resampling=Resampling.nearest, nodata=255) as v:
                a = v.read(1)
            fill = (out == 255) & (a != 255)
            out[fill] = a[fill]
            tile.unlink()
        prof = dict(driver="GTiff", dtype="uint8", count=1, crs=CRS, transform=Affine(*tr), width=w, height=h)
        with rasterio.open(path, "w", **prof) as d:
            d.write(out, 1)
    with rasterio.open(path) as s:
        return s.read(1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert_outside_aois()
    ee.Initialize(project=EE_PROJECT)
    tr, (h, w) = window_grid()
    ll = gpd.GeoSeries([box(tr[2], tr[5] - h * RES, tr[2] + w * RES, tr[5])], crs=CRS).to_crs(4326).iloc[0]
    geom = ee.Geometry(ll.buffer(0.01).__geo_interface__)

    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(geom).filterDate("2022-10-01", "2023-01-01")
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).median().select(["B4", "B3", "B2"]))
    rgb = fetch(s2, "sentinel2_oct_dec_2022_rgb", dtype="uint16").astype(float)
    rgb = np.clip(np.moveaxis(rgb, 0, -1) / 3000.0, 0, 1)

    wc = ee.ImageCollection("ESA/WorldCereal/2021/MODELS/v100").filter(ee.Filter.eq("product", "temporarycrops")) \
        .filterBounds(geom).mosaic().select("classification")
    maps = {
        "WorldCereal 2021\n(classification = 100)": (fetch(wc, "worldcereal")[0], lambda a: a == 100),
        "WorldCover 2021\n(Map = 40)": (fetch(ee.ImageCollection("ESA/WorldCover/v200").first(), "worldcover")[0],
                                        lambda a: a == 40),
        "Esri 2022\n(b1 = 5)": (fetch(ee.ImageCollection("projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS")
                                      .filterDate("2022-01-01", "2023-01-01").filterBounds(geom).mosaic(), "esri2022")[0],
                                lambda a: a == 5),
        "Dynamic World Jun-Nov 2022\n(mode of label = 4)": (
            fetch(ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(geom).filterDate("2022-06-01", "2022-12-01")
                  .select("label").reduce(ee.Reducer.mode()), "dw_jjason")[0], lambda a: a == 4),
        "DE Africa 2019\n(mask = 1)": (deafrica_mask(), lambda a: a == 1),
        "GLAD 2016-2019\n(b1 = 1)": (fetch(ee.ImageCollection("users/potapovpeter/Global_cropland_2019").filterBounds(geom)
                                           .mosaic(), "glad2019")[0], lambda a: a == 1),
        "GFSAD 2015\n(b1 = 2)": (fetch(ee.ImageCollection("projects/sat-io/open-datasets/GFSAD/GCEP30").filterBounds(geom)
                                       .mosaic(), "gfsad2015")[0], lambda a: a == 2),
    }

    km = [0, 2 * HALF / 1000, 0, 2 * HALF / 1000]
    fig, axes = plt.subplots(2, 4, figsize=(17, 9.2), constrained_layout=True)
    axes = axes.ravel()
    axes[0].imshow(rgb, extent=km)
    axes[0].set_title("Sentinel-2 image, Oct-Dec 2022\n(true colour, for orientation)", fontsize=10)
    crop_cmap = ListedColormap(["#ece7dc", "#d4a017", "#ffffff"])
    for ax, (title, (arr, is_crop)) in zip(axes[1:], maps.items()):
        disp = np.where(arr == 255, 2, is_crop(arr).astype(int))
        ax.imshow(disp, cmap=crop_cmap, vmin=0, vmax=2, extent=km, interpolation="nearest")
        share = 100 * is_crop(arr)[arr != 255].mean()
        ax.set_title(f"{title}\ncrop: {share:.1f}% of window", fontsize=10)
    for ax in axes:
        ax.set_xlabel("km")
        ax.set_ylabel("km")
    fig.legend(handles=[mpatches.Patch(color="#d4a017", label="map says crop"),
                        mpatches.Patch(color="#ece7dc", label="map says not crop")],
               loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.suptitle("What the cropland maps look like: demo window 6 x 6 km around Turalei (Twic county), "
                 "OUTSIDE the study counties", fontsize=13)
    p1 = OUT / "demo_maps_turalei.png"
    fig.savefig(p1, dpi=110, bbox_inches="tight")
    plt.close(fig)

    # 10 m -> 30 m illustration: the 180 m x 180 m patch of a 10 m map closest to half crop
    name = "DE Africa 2019\n(mask = 1)"
    arr, is_crop = maps[name]
    c = is_crop(arr).astype(int)
    n = 18  # 18 x 18 pixels of 10 m = 180 m = 6 x 6 cells of 30 m
    best, pos = None, (0, 0)
    for r in range(0, c.shape[0] - n, 6):
        for q in range(0, c.shape[1] - n, 6):
            if (arr[r:r + n, q:q + n] == 255).any():
                continue
            gap = abs(c[r:r + n, q:q + n].mean() - 0.5)
            if best is None or gap < best:
                best, pos = gap, (r, q)
    r, q = pos
    sub = c[r:r + n, q:q + n]
    frac = sub.reshape(n // 3, 3, n // 3, 3).sum(axis=(1, 3))
    side = n * RES
    fig, ax = plt.subplots(1, 2, figsize=(13, 6.3), constrained_layout=True)
    ax[0].imshow(sub, cmap=ListedColormap(["#ece7dc", "#d4a017"]), extent=[0, side, 0, side], interpolation="nearest")
    ax[0].set_title(f"Step 2: 10 m pixels, crop yes / no\n({name.splitlines()[0]}, {side} m x {side} m patch of the demo window)")
    for t in range(0, side + 1, 10):
        lw = 1.6 if t % 30 == 0 else 0.3
        ax[0].axhline(t, color="k", lw=lw)
        ax[0].axvline(t, color="k", lw=lw)
    ax[1].imshow(frac / 9, cmap="YlOrBr", vmin=0, vmax=1, extent=[0, side, 0, side], interpolation="nearest")
    for t in range(0, side + 1, 30):
        ax[1].axhline(t, color="k", lw=1.6)
        ax[1].axvline(t, color="k", lw=1.6)
    for i in range(n // 3):
        for j in range(n // 3):
            v = frac[i, j]
            ax[1].text(15 + 30 * j, side - 15 - 30 * i, f"{v}/9 = {100 * v / 9:.0f}%\n{'CROP' if v >= 5 else 'not crop'}",
                       ha="center", va="center", fontsize=8, color="k" if v < 7 else "w")
    ax[1].set_title("Step 3: each 30 m cell = 3 x 3 pixels (thick lines)\ncrop share = crop pixels / 9; "
                    "cell = 'CROP' if at least 5 of 9")
    for a_ in ax:
        a_.set_xlabel("m")
        a_.set_ylabel("m")
    p2 = OUT / "demo_10m_to_30m_turalei.png"
    fig.savefig(p2, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print(p1, p2)


if __name__ == "__main__":
    main()
