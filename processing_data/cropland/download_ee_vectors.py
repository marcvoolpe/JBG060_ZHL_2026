"""Download the Earth Engine vector layers the sampling design needs.

  9 Google Open Buildings v3 polygons, confidence >= 0.70, per AOI
                                    GOOGLE/Research/open-buildings/v3/polygons
 11 HydroSHEDS free-flowing rivers, all of South Sudan (small)
                                    WWF/HydroSHEDS/v1/FreeFlowingRivers

Features are pulled with FeatureCollection.getDownloadURL (GeoJSON) in spatial
cells small enough for one request, then merged and saved as GeoPackage. A
building is assigned to the cell that holds its centroid, so none is counted
twice. Attribute values are kept as delivered.

Usage (repo root, global Python 3.13):
    python -m processing_data.cropland.download_ee_vectors [--layers buildings rivers] [--aoi aweil]
"""

from __future__ import annotations

import argparse
import io
import time

import ee
import geopandas as gpd
import pandas as pd
import requests

from processing_data.cropland.common import (
    AOIS, aoi_geometry, counties, file_fields, product_dir, today, upsert_manifest,
)
from processing_data.cropland.download_ee_products import EE_PROJECT, SOFTWARE

OB_ASSET = "GOOGLE/Research/open-buildings/v3/polygons"
OB_MIN_CONF = 0.70
FFR_ASSET = "WWF/HydroSHEDS/v1/FreeFlowingRivers"
MAX_PER_REQUEST = 15000


def fetch_geojson(fc: ee.FeatureCollection, selectors: list[str], retries: int = 4) -> gpd.GeoDataFrame:
    # '.geo' must be listed explicitly: with selectors, Earth Engine otherwise returns null geometries
    url = fc.getDownloadURL(filetype="geojson", selectors=list(selectors) + [".geo"])
    for k in range(retries):
        try:
            r = requests.get(url, timeout=600)
            r.raise_for_status()
            g = gpd.read_file(io.BytesIO(r.content))
            if len(g) and g.geometry.isna().any():
                raise ValueError(f"{g.geometry.isna().sum()} features without geometry")
            return g.set_crs("EPSG:4326", allow_override=True)
        except Exception as exc:  # network hiccups / EE busy
            if k == retries - 1:
                raise
            print(f"    retry {k + 1}: {exc}")
            time.sleep(10 * (k + 1))


def cells(bounds, step: float):
    x0, y0, x1, y1 = bounds
    x = x0
    while x < x1:
        y = y0
        while y < y1:
            yield (x, y, min(x + step, x1), min(y + step, y1))
            y += step
        x += step


def buildings(aoi: str) -> None:
    geom_4326 = aoi_geometry(aoi, "EPSG:4326")
    aoi_ee = ee.Geometry(geom_4326.__geo_interface__)
    fc_all = ee.FeatureCollection(OB_ASSET).filterBounds(aoi_ee).filter(ee.Filter.gte("confidence", OB_MIN_CONF))
    selectors = ["confidence", "area_in_meters", "full_plus_code"]
    parts = []
    todo = list(cells(geom_4326.bounds, 0.25))
    while todo:
        c = todo.pop()
        rect = ee.Geometry.Rectangle(list(c), "EPSG:4326", False)
        # centroid-in-cell (half-open on the upper edges) so each building is taken once
        fc = fc_all.filterBounds(rect).map(lambda f: f.set("cx", f.geometry().centroid(1).coordinates().get(0),
                                                             "cy", f.geometry().centroid(1).coordinates().get(1)))
        fc = fc.filter(ee.Filter.And(ee.Filter.gte("cx", c[0]), ee.Filter.lt("cx", c[2]),
                                     ee.Filter.gte("cy", c[1]), ee.Filter.lt("cy", c[3])))
        n = fc.size().getInfo()
        if n == 0:
            continue
        if n > MAX_PER_REQUEST:
            mx, my = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
            todo += [(c[0], c[1], mx, my), (mx, c[1], c[2], my), (c[0], my, mx, c[3]), (mx, my, c[2], c[3])]
            continue
        g = fetch_geojson(fc, selectors)
        assert len(g) == n, (len(g), n, c)
        parts.append(g)
        print(f"  cell {tuple(round(v, 3) for v in c)}: {n} buildings")
    g = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs="EPSG:4326")
    g = g.drop_duplicates("full_plus_code")
    # keep buildings whose centroid lies in the buffered AOI polygon
    cent = g.geometry.representative_point()
    g = g[cent.within(geom_4326)].reset_index(drop=True)
    path = product_dir("open_buildings") / f"open_buildings_v3_conf070_{aoi}.gpkg"
    g.to_file(path, driver="GPKG", layer="buildings")

    # per-county counts (unbuffered counties, centroid in county)
    cty = counties(AOIS[aoi]["pcodes"])
    pts = gpd.GeoDataFrame(geometry=g.geometry.representative_point(), crs="EPSG:4326")
    j = gpd.sjoin(pts, cty[["adm2_pcode", "adm2_name", "geometry"]], predicate="within")
    counts = j.groupby(["adm2_pcode", "adm2_name"]).size().rename("buildings_conf_ge_070").reset_index()
    counts_path = product_dir("open_buildings") / f"open_buildings_v3_county_counts_{aoi}.csv"
    counts.to_csv(counts_path, index=False)
    print(counts.to_string(index=False))

    row = dict(product="Google Open Buildings", version="v3", year="2023 (inference May 2023)", aoi=aoi,
               source=f"Earth Engine {OB_ASSET}", access_date=today(), licence="CC-BY-4.0 (Earth Engine catalogue)",
               native_resolution="vector polygons", crs="EPSG:4326", band="confidence; area_in_meters; full_plus_code",
               class_codes="each feature = one building footprint; confidence = model score (0.65-1.0 in the release); kept >= 0.70",
               ee_task_id="n/a (getDownloadURL GeoJSON per spatial cell)",
               export_params={"filter": f"confidence >= {OB_MIN_CONF}", "cell_deg": 0.25,
                              "max_per_request": MAX_PER_REQUEST, "selectors": selectors,
                              "dedupe": "full_plus_code; centroid within buffered AOI", "software": SOFTWARE},
               status="obtained", notes=f"{len(g)} buildings in the buffered AOI; county counts in {counts_path.name}.")
    row.update(file_fields(path))
    upsert_manifest(row)
    row2 = dict(row, file_path="", band="county counts", notes="Buildings (confidence >= 0.70) per county, centroid in county.")
    row2.update(file_fields(counts_path))
    upsert_manifest(row2)


def rivers() -> None:
    nat = counties().union_all()
    nat_ee = ee.Geometry(nat.buffer(0.02).__geo_interface__)
    fc = ee.FeatureCollection(FFR_ASSET).filterBounds(nat_ee)
    selectors = ["REACH_ID", "NOID", "NDOID", "NUOID", "UPLAND_SKM", "RIV_ORD", "DIS_AV_CMS", "LENGTH_KM", "CSI", "CSI_FF",
                 "BAS_ID", "BB_NAME", "COUNTRY"]
    n = fc.size().getInfo()
    print(f"FFR reaches intersecting South Sudan: {n}")
    parts = []
    if n <= MAX_PER_REQUEST:
        parts.append(fetch_geojson(fc, selectors))
    else:
        for c in cells(nat.bounds, 3.0):
            sub = fc.filterBounds(ee.Geometry.Rectangle(list(c), "EPSG:4326", False))
            if sub.size().getInfo():
                parts.append(fetch_geojson(sub, selectors))
    g = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs="EPSG:4326").drop_duplicates("REACH_ID")
    path = product_dir("hydrosheds_ffr") / "hydrosheds_ffr_v1_south_sudan.gpkg"
    g.to_file(path, driver="GPKG", layer="rivers")
    row = dict(product="HydroSHEDS free-flowing rivers", version="v1", year="static", aoi="south_sudan",
               source=f"Earth Engine {FFR_ASSET}", access_date=today(), licence="see README",
               native_resolution="vector lines (HydroSHEDS 15 arc-second network)", crs="EPSG:4326",
               band=", ".join(selectors),
               class_codes="UPLAND_SKM = upstream catchment area (km2); RIV_ORD = river order by long-term mean discharge "
                           "(1 = largest); DIS_AV_CMS = long-term mean discharge (m3/s); CSI = connectivity status index",
               ee_task_id="n/a (getDownloadURL GeoJSON)", export_params={"filter": "intersects South Sudan (+0.02 deg)",
                                                                         "selectors": selectors, "software": SOFTWARE},
               status="obtained", notes=f"{len(g)} river reaches.")
    row.update(file_fields(path))
    upsert_manifest(row)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", nargs="+", default=["buildings", "rivers"], choices=["buildings", "rivers"])
    ap.add_argument("--aoi", nargs="+", default=list(AOIS), choices=list(AOIS))
    args = ap.parse_args()
    ee.Initialize(project=EE_PROJECT)
    if "rivers" in args.layers:
        rivers()
    if "buildings" in args.layers:
        for a in args.aoi:
            buildings(a)


if __name__ == "__main__":
    main()
