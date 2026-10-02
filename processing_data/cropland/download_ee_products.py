"""Download the Earth Engine cropland and context layers for the cropland audit AOIs.

Products (numbers follow the download brief):
  1 ESA WorldCereal 2021 v100 temporary crops    ESA/WorldCereal/2021/MODELS/v100
  2 ESA WorldCover v200 (2021) and v100 (2020)   ESA/WorldCover/v200, ESA/WorldCover/v100
  3 Esri / Impact Observatory 10 m LULC 2021-24  projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS
  4 Google Dynamic World V1 composites 2022      GOOGLE/DYNAMICWORLD/V1
 10 MERIT Hydro (hnd, upa)                       MERIT/Hydro/v1_0_1

Every raster is fetched on the product's own native grid (no resampling): the
request uses the source image's CRS and pixel transform and only restricts the
window to the buffered AOI. Pixels outside the buffered AOI polygon are set to
no-data. Downloads go straight to disk in tiles through geedim (no Drive step),
so there are no Earth Engine task IDs; the exact request parameters are stored in
the manifest column `export_params` instead.

Usage (repo root, global Python 3.13):
    python -m processing_data.cropland.download_ee_products [--products worldcereal esri ...] [--aoi aweil]
"""

from __future__ import annotations

import argparse
import json
import math
import time
from importlib.metadata import version

import ee
import geedim  # noqa: F401  (registers the ee.Image.gd accessor)

from processing_data.cropland.common import (
    AOIS, aoi_geometry, file_fields, product_dir, today, upsert_manifest, utm_grid,
)

EE_PROJECT = "southsudan-509222"
NODATA_U8 = 255
# Parallel tile requests per process. geedim's default (32) exceeds this project's
# concurrent interactive request limit when two scripts run at once.
MAX_REQUESTS = 6
SOFTWARE = {p: version(p) for p in ("earthengine-api", "geedim", "geemap")}


def init_ee() -> None:
    ee.Initialize(project=EE_PROJECT)


def ee_aoi(aoi: str) -> ee.Geometry:
    return ee.Geometry(aoi_geometry(aoi, "EPSG:4326").__geo_interface__)


def native_window(transform: list[float], aoi: str, crs: str) -> tuple[list[float], tuple[int, int]]:
    """Sub-window of a native grid (given by its affine) covering the buffered AOI.

    Keeps the source pixel size and the source pixel lattice; only the origin
    moves by whole pixels.
    """
    a, _, c, _, e, f = transform
    minx, miny, maxx, maxy = aoi_geometry(aoi, crs).bounds
    if e > 0:  # some EE assets store a bottom-up transform; express it top-down
        raise ValueError("bottom-up transform: pass the top-down equivalent")
    col0 = math.floor((minx - c) / a)
    col1 = math.ceil((maxx - c) / a)
    row0 = math.floor((maxy - f) / e)
    row1 = math.ceil((miny - f) / e)
    new = [a, 0.0, c + col0 * a, 0.0, e, f + row0 * e]
    return new, (row1 - row0, col1 - col0)


def download(img: ee.Image, path, crs: str, transform: list[float], shape: tuple[int, int],
             dtype: str, nodata) -> dict:
    """Fetch img on an exact grid to a (compressed, tiled) GeoTIFF; return request params."""
    params = {"crs": crs, "crs_transform": [float(v) for v in transform], "shape": list(shape),
              "dtype": dtype, "nodata": nodata, "resampling": "near (none: native grid)",
              "software": SOFTWARE}
    if path.exists():
        print(f"  exists, skipping download: {path.name}")
        return params
    # Fill masked pixels (outside the AOI, or no observation) with an explicit no-data
    # value; otherwise geedim writes its own per-dtype default, which can collide with
    # a real class code (e.g. WorldCereal 0 = other).
    filled = img.unmask(nodata, False)
    prepared = filled.gd.prepareForExport(crs=crs, crs_transform=transform, shape=shape, dtype=dtype)
    tmp = path.with_suffix(".part.tif")
    for attempt in range(1, 6):
        try:
            prepared.gd.toGeoTIFF(tmp, overwrite=True, nodata=nodata, driver="cog", max_requests=MAX_REQUESTS)
            break
        except ee.EEException as exc:
            # "Too Many Requests" = the project's concurrent interactive request limit
            if "Too Many Requests" not in str(exc) or attempt == 5:
                raise
            wait = 60 * attempt
            print(f"  EE concurrency limit hit (attempt {attempt}); waiting {wait} s")
            time.sleep(wait)
    tmp.replace(path)
    params["driver"] = "COG (geedim)"
    return params


def record(path, params: dict, **fields) -> None:
    row = {"access_date": today(), "status": "obtained", "export_params": params, "ee_task_id": "n/a (direct tiled download via geedim)"}
    row.update(fields)
    row.update(file_fields(path))
    upsert_manifest(row)
    print(f"  logged {path.name}: {row['file_size_bytes'] / 1e6:.1f} MB")


# --- 1 WorldCereal ------------------------------------------------------------------

WORLDCEREAL = {
    "licence": "CC-BY-4.0 (see README)",
    "classes": "classification: 100 = temporary crops, 0 = other (not temporary crops); confidence: 0-100 model confidence (%); 255 = no data / outside AOI",
}


def worldcereal(aoi: str) -> None:
    """One file per agro-ecological zone (AEZ): each AEZ image has its own EPSG:4326 grid."""
    geom = ee_aoi(aoi)
    col = (ee.ImageCollection("ESA/WorldCereal/2021/MODELS/v100")
           .filter(ee.Filter.eq("product", "temporarycrops")).filterBounds(geom))
    out = product_dir("worldcereal")
    for info in col.toList(50).getInfo():
        band = info["bands"][0]
        props = info["properties"]
        asset_id = info["id"]
        transform, shape = native_window(band["crs_transform"], aoi, band["crs"])
        img = ee.Image(asset_id).select(["classification", "confidence"]).clip(geom)
        path = out / f"worldcereal_2021_v100_temporarycrops_aez{props['aez_id']}_{aoi}.tif"
        print(f"WorldCereal AEZ {props['aez_id']} ({aoi}) {shape}")
        params = download(img, path, band["crs"], transform, shape, "uint8", NODATA_U8)
        params["season"] = props.get("season")
        record(path, params, product="ESA WorldCereal temporary crops", version="v100", year="2021",
               aoi=aoi, source=f"Earth Engine {asset_id}", licence=WORLDCEREAL["licence"],
               band="classification; confidence", class_codes=WORLDCEREAL["classes"],
               notes=f"AEZ {props['aez_id']}, season {props.get('season')}; one image per AEZ, each on its own "
                     f"1/12000 deg grid, clipped to the buffered AOI (the AEZ image only covers its own zone).")


# --- 2 WorldCover ----------------------------------------------------------------------

WORLDCOVER_CLASSES = ("10 tree cover, 20 shrubland, 30 grassland, 40 cropland, 50 built-up, 60 bare/sparse vegetation, "
                      "70 snow and ice, 80 permanent water bodies, 90 herbaceous wetland, 95 mangroves, 100 moss and lichen; "
                      "255 = no data / outside AOI (the product's own no-data 0 does not occur over land here)")


def worldcover(aoi: str) -> None:
    geom = ee_aoi(aoi)
    out = product_dir("worldcover")
    for ver, year, asset in [("v200", "2021", "ESA/WorldCover/v200"), ("v100", "2020", "ESA/WorldCover/v100")]:
        img = ee.ImageCollection(asset).first()
        band = img.select("Map").getInfo()["bands"][0]
        transform, shape = native_window(band["crs_transform"], aoi, band["crs"])
        path = out / f"worldcover_{year}_{ver}_{aoi}.tif"
        print(f"WorldCover {ver} ({aoi}) {shape}")
        params = download(img.select("Map").clip(geom), path, band["crs"], transform, shape, "uint8", NODATA_U8)
        record(path, params, product="ESA WorldCover", version=ver, year=year, aoi=aoi,
               source=f"Earth Engine {asset}", licence="CC-BY-4.0 (see README)", band="Map",
               class_codes=WORLDCOVER_CLASSES, notes="Cropland = 40.")


# --- 3 Esri / Impact Observatory ---------------------------------------------------

ESRI_CLASSES = ("Esri original coding (checked on the pixel values: codes 3 and 6 never occur): 1 water, 2 trees, "
                "4 flooded vegetation, 5 crops, 7 built area, 8 bare ground, 9 snow/ice, 10 clouds, 11 rangeland; "
                "255 = no data / outside AOI. NOTE: crops = 5 in this asset; 4 is flooded vegetation. The 1-9 "
                "remap (crops = 4) exists only in the community catalogue's example script, not in the asset.")


def esri(aoi: str, years=(2021, 2022, 2023, 2024)) -> None:
    """The asset holds one image per UTM zone and year; the AOI's zone images share one 10 m lattice."""
    geom = ee_aoi(aoi)
    grid = utm_grid(aoi, 10)
    out = product_dir("esri_lulc")
    col = ee.ImageCollection("projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS")
    zone = grid["crs"][-2:]  # "35" or "36"
    for y in years:
        yc = col.filterDate(f"{y}-01-01", f"{y + 1}-01-01").filterBounds(geom)
        infos = yc.getInfo()["features"]
        ids = [i["id"] for i in infos]
        for i in infos:
            b = i["bands"][0]
            assert b["crs"] == grid["crs"], (b["crs"], grid["crs"])
            assert all(abs(v % 10) < 1e-6 for v in b["crs_transform"][2::3]), "source grid not on 10 m lattice"
            assert i["properties"]["system:index"].startswith(zone)
        img = yc.mosaic().select(["b1"]).clip(geom)
        path = out / f"esri_lulc_{y}_{aoi}.tif"
        print(f"Esri LULC {y} ({aoi}) {grid['shape']} from {ids}")
        params = download(img, path, grid["crs"], grid["transform"], grid["shape"], "uint8", NODATA_U8)
        params["source_images"] = ids
        record(path, params, product="Esri / Impact Observatory 10 m annual land cover", version="model v3 per community catalogue (sat-io mirror)",
               year=str(y), aoi=aoi, source="Earth Engine projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS",
               licence="CC-BY-4.0 (see README)", band="b1", class_codes=ESRI_CLASSES,
               notes="Mosaic of the UTM-zone images listed in export_params; they share the same CRS and 10 m pixel lattice, "
                     "so the mosaic is on the native grid.")


# --- 4 Dynamic World -----------------------------------------------------------------

DW_CLASSES = ("label_mode: most frequent per-image top class; 0 water, 1 trees, 2 grass, 3 flooded vegetation, 4 crops, "
              "5 shrub and scrub, 6 built, 7 bare, 8 snow and ice; 255 = no observation / outside AOI. "
              "crops_mean_pct: mean of the per-image 'crops' probability x 100, rounded (0-100); 255 = no observation. "
              "n_obs: number of cloud-free Dynamic World observations of the pixel in the period (capped at 254).")


def dynamic_world(aoi: str) -> None:
    geom = ee_aoi(aoi)
    grid = utm_grid(aoi, 10)
    out = product_dir("dynamic_world")
    for tag, d0, d1 in [("2022-06_2022-11", "2022-06-01", "2022-12-01"), ("2022", "2022-01-01", "2023-01-01")]:
        col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(geom).filterDate(d0, d1)
        n_img = col.size().getInfo()
        crs_set = col.map(lambda i: i.set("c", i.select("label").projection().crs())).aggregate_array("c").distinct().getInfo()
        assert crs_set == [grid["crs"]], crs_set
        label = col.select("label").reduce(ee.Reducer.mode()).rename("label_mode")
        crops = col.select("crops").mean().multiply(100).round().rename("crops_mean_pct")
        nobs = col.select("label").count().min(254).rename("n_obs")
        img = ee.Image.cat([label, crops, nobs]).clip(geom)
        path = out / f"dynamic_world_v1_{tag}_{aoi}.tif"
        print(f"Dynamic World {tag} ({aoi}) {grid['shape']} from {n_img} images")
        params = download(img, path, grid["crs"], grid["transform"], grid["shape"], "uint8", NODATA_U8)
        params.update({"date_start": d0, "date_end_exclusive": d1, "n_images": n_img,
                       "composite": "label: ee.Reducer.mode(); crops: mean x 100 rounded; n_obs: count of label"})
        record(path, params, product="Google Dynamic World V1", version="V1", year=tag, aoi=aoi,
               source="Earth Engine GOOGLE/DYNAMICWORLD/V1", licence="CC-BY-4.0 (see README)",
               band="label_mode; crops_mean_pct; n_obs", class_codes=DW_CLASSES,
               notes="Composite made by this script from all DW images intersecting the AOI in the period "
                     "(all in the AOI's UTM zone, 10 m, same pixel lattice as the export grid). Ties in the mode go "
                     "to Earth Engine's default tie rule.")


# --- 10 MERIT Hydro --------------------------------------------------------------------

def merit(aoi: str) -> None:
    geom = ee_aoi(aoi)
    img = ee.Image("MERIT/Hydro/v1_0_1").select(["hnd", "upa"])
    band = img.getInfo()["bands"][0]
    transform, shape = native_window(band["crs_transform"], aoi, band["crs"])
    path = product_dir("merit_hydro") / f"merit_hydro_v1_0_1_hnd_upa_{aoi}.tif"
    print(f"MERIT Hydro ({aoi}) {shape}")
    params = download(img.clip(geom), path, band["crs"], transform, shape, "float32", -9999.0)
    record(path, params, product="MERIT Hydro", version="v1.0.1", year="static", aoi=aoi,
           source="Earth Engine MERIT/Hydro/v1_0_1", licence="see README", band="hnd; upa",
           class_codes="hnd: height above nearest drainage (m); upa: upstream drainage area (km2); -9999 = no data / outside AOI",
           notes="3 arc-second (~93 m) native grid.")


# --- 7 GLAD global cropland extent ------------------------------------------------------

def glad(aoi: str, years=(2019, 2015)) -> None:
    """Producer's own Earth Engine copy (named on glad.umd.edu/dataset/croplands).

    Four quadrant images per interval on one global 0.00025 deg grid; the AOIs lie
    in the NE quadrant. The year in the name is the last year of the 4-year interval.
    """
    geom = ee_aoi(aoi)
    out = product_dir("glad_cropland")
    for y in years:
        asset = f"users/potapovpeter/Global_cropland_{y}"
        col = ee.ImageCollection(asset).filterBounds(geom)
        infos = col.getInfo()["features"]
        tr = {tuple(i["bands"][0]["crs_transform"]) for i in infos}
        assert len(tr) == 1, f"quadrants on different grids: {tr}"
        band = infos[0]["bands"][0]
        transform, shape = native_window(band["crs_transform"], aoi, band["crs"])
        path = out / f"glad_cropland_{y - 3}-{y}_{aoi}.tif"
        print(f"GLAD cropland {y - 3}-{y} ({aoi}) {shape} from {[i['id'] for i in infos]}")
        params = download(col.mosaic().select(["b1"]).clip(geom), path, band["crs"], transform, shape, "uint8", NODATA_U8)
        params["source_images"] = [i["id"] for i in infos]
        record(path, params, product="GLAD global cropland extent (Potapov et al. 2022)", version="2003-2019 release",
               year=f"{y - 3}-{y}", aoi=aoi, source=f"Earth Engine {asset} (author's copy; files also at "
               f"https://glad.geog.umd.edu/Potapov/Global_Crop/Data/Global_cropland_NE_{y}.tif)",
               licence="not stated for the data (article CC-BY-4.0); see README", band="b1",
               class_codes="1 = cropland, 0 = no cropland or no data (producer's coding); 255 = outside AOI",
               notes="Cropland detected in any year of the 4-year interval (max fallow 4 years); shifting cultivation, "
                     "permanent pasture and woody crops excluded.")


# --- 8 GFSAD30 Africa cropland extent ------------------------------------------------

GFSAD_CLASSES = ("0 = water bodies / no data, 1 = non-cropland, 2 = cropland (GFSAD30AFCE User Guide V1, p. 6, "
                 "section 2.1.4); 255 = outside AOI")


def gfsad(aoi: str) -> None:
    """Community-catalogue copy of the LP DAAC GFSAD30AFCE granules (10 x 10 deg tiles, own grids)."""
    geom = ee_aoi(aoi)
    out = product_dir("gfsad30")
    col = ee.ImageCollection("projects/sat-io/open-datasets/GFSAD/GCEP30").filterBounds(geom)
    for info in col.getInfo()["features"]:
        granule = info["properties"]["system:index"]
        if not granule.startswith("GFSAD30AFCE"):
            print(f"  skipping non-Africa granule {granule}")
            continue
        band = info["bands"][0]
        transform, shape = native_window(band["crs_transform"], aoi, band["crs"])
        path = out / f"{granule}_{aoi}.tif"
        print(f"GFSAD30 {granule} ({aoi}) {shape}")
        params = download(ee.Image(info["id"]).select(["b1"]).clip(geom), path, band["crs"], transform, shape,
                          "uint8", NODATA_U8)
        record(path, params, product="NASA GFSAD30 Africa cropland extent (GFSAD30AFCE)", version="V001",
               year="2015 (nominal; 2013-2016 data)", aoi=aoi,
               source=f"Earth Engine {info['id']} (community copy of LP DAAC granule {granule}; "
                      f"DOI 10.5067/MEaSUREs/GFSAD/GFSAD30AFCE.001)",
               licence="NASA EOSDIS open data, no restriction (see README)", band="b1", class_codes=GFSAD_CLASSES,
               notes="One file per 10 deg granule, each on its own ~0.000269 deg grid; cells outside the granule "
                     "are 255. Cropland includes fallow.")


PRODUCTS = {"worldcereal": worldcereal, "worldcover": worldcover, "esri": esri,
            "dynamic_world": dynamic_world, "merit": merit, "glad": glad, "gfsad": gfsad}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--products", nargs="+", default=list(PRODUCTS), choices=list(PRODUCTS))
    ap.add_argument("--aoi", nargs="+", default=list(AOIS), choices=list(AOIS))
    args = ap.parse_args()
    init_ee()
    for p in args.products:
        for a in args.aoi:
            PRODUCTS[p](a)


if __name__ == "__main__":
    main()
