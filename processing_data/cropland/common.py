"""Shared helpers for the cropland download scripts: AOIs, grids, manifest, file checks.

Run the scripts from the repo root with the global Python 3.13 (it has rasterio):
    python -m processing_data.cropland.<script>
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import os
import time
from contextlib import contextmanager
from pathlib import Path

import geopandas as gpd

from processing_data.paths import COURSE_RAW, EXT_DATA

CROPLAND_DIR = EXT_DATA / "cropland"
MANIFEST = CROPLAND_DIR / "MANIFEST.csv"
ADMIN2 = COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson"

# Areas of interest. Each AOI is processed in the UTM zone that holds it (the
# Sentinel-2 grid for that area): Aweil lies at 26-28 E (zone 35N), Bor South at
# 31-33 E (zone 36N).
AOIS = {
    "aweil": {
        "pcodes": ["SS0501", "SS0502", "SS0503", "SS0504", "SS0505"],
        "utm": "EPSG:32635",
        "label": "Northern Bahr el Ghazal (5 Aweil counties)",
    },
    "borsouth": {
        "pcodes": ["SS0303"],
        "utm": "EPSG:32636",
        "label": "Bor South, Jonglei",
    },
}
BUFFER_M = 2000
# Grid origins are snapped to multiples of 60 m in UTM. Sentinel-2 tile corners
# sit on this lattice, so 10 m and 30 m cells here line up with Sentinel-2 pixels.
GRID_SNAP_M = 60

# Licence per product (manifest `product` prefix -> licence), as stated by the producer or
# catalogue page cited in data/cropland/README.md. Applied to every manifest row.
LICENCES = {
    "ESA WorldCereal": "CC-BY-4.0",
    "ESA WorldCover": "CC-BY-4.0",
    "Esri / Impact Observatory": "CC-BY-4.0 (attribution: (c) Esri / Impact Observatory)",
    "Google Dynamic World": "CC-BY-4.0 (attribution required, see README)",
    "Digital Earth Africa": "CC-BY-4.0",
    "GLAD global cropland": "not stated for the data by the producer (article is CC-BY-4.0); cite Potapov et al. 2022",
    "NASA GFSAD30": "NASA EOSDIS open data, shared without restriction (cite DOI 10.5067/MEaSUREs/GFSAD/GFSAD30AFCE.001)",
    "Google Open Buildings": "CC-BY-4.0 (Earth Engine catalogue)",
    "MERIT Hydro": "CC-BY-NC-4.0 or ODbL-1.0 (non-commercial use under CC-BY-NC)",
    "HydroSHEDS": "HydroSHEDS licence: free for non-commercial and commercial use, attribution required",
    "JRC ASAP": "EC reuse policy (Decision 2011/833/EU): reuse authorised, source acknowledged",
}
# short names used by the derived-layer rows
LICENCES.update({
    "Esri/IO": LICENCES["Esri / Impact Observatory"],
    "Dynamic World": LICENCES["Google Dynamic World"],
    "GLAD cropland": LICENCES["GLAD global cropland"],
    "GFSAD30": LICENCES["NASA GFSAD30"],
    "distance to nearest building": LICENCES["Google Open Buildings"],
})

MANIFEST_COLUMNS = [
    "product", "version", "year", "aoi", "file_path", "source", "access_date",
    "licence", "native_resolution", "crs", "band", "class_codes", "file_size_bytes",
    "checksum_sha256", "ee_task_id", "export_params", "status", "notes",
]


def counties(pcodes: list[str] | None = None) -> gpd.GeoDataFrame:
    """Admin-2 polygons (EPSG:4326), optionally restricted to some pcodes."""
    g = gpd.read_file(ADMIN2)[["adm2_pcode", "adm2_name", "adm1_name", "geometry"]]
    if pcodes is not None:
        g = g[g["adm2_pcode"].isin(pcodes)].reset_index(drop=True)
    return g


def aoi_geometry(aoi: str, crs: str | None = None):
    """Union of the AOI's counties buffered by 2 km (buffer applied in UTM metres)."""
    spec = AOIS[aoi]
    g = counties(spec["pcodes"]).to_crs(spec["utm"])
    geom = g.union_all().buffer(BUFFER_M)
    out = gpd.GeoSeries([geom], crs=spec["utm"])
    return out.to_crs(crs).iloc[0] if crs else geom


def utm_grid(aoi: str, res: float) -> dict:
    """Grid covering the buffered AOI in its UTM zone, origin snapped to 60 m.

    Returns crs, the GDAL-style affine (a, b, c, d, e, f) as used by Earth
    Engine's crsTransform, and the (rows, cols) shape.
    """
    spec = AOIS[aoi]
    minx, miny, maxx, maxy = aoi_geometry(aoi).bounds
    x0 = math.floor(minx / GRID_SNAP_M) * GRID_SNAP_M
    y1 = math.ceil(maxy / GRID_SNAP_M) * GRID_SNAP_M
    x1 = math.ceil(maxx / GRID_SNAP_M) * GRID_SNAP_M
    y0 = math.floor(miny / GRID_SNAP_M) * GRID_SNAP_M
    cols = int(round((x1 - x0) / res))
    rows = int(round((y1 - y0) / res))
    return {
        "crs": spec["utm"],
        "transform": [res, 0.0, float(x0), 0.0, -res, float(y1)],
        "shape": (rows, cols),
        "bounds": (x0, y0, x1, y1),
    }


def product_dir(product: str) -> Path:
    d = CROPLAND_DIR / product
    d.mkdir(parents=True, exist_ok=True)
    return d


def rel(path: Path) -> str:
    """Path relative to the repo root, with forward slashes, for the manifest."""
    root = EXT_DATA.parent
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def raster_meta(path: Path) -> dict:
    """CRS and resolution of a raster, as strings for the manifest."""
    import rasterio

    with rasterio.open(path) as src:
        crs = src.crs.to_string() if src.crs else ""
        return {"crs": crs, "native_resolution": f"{src.res[0]:.10g} x {src.res[1]:.10g} ({'deg' if src.crs and src.crs.is_geographic else 'm'})"}


def today() -> str:
    return dt.date.today().isoformat()


def read_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@contextmanager
def _manifest_lock(timeout_s: float = 120.0):
    """Exclusive lock file so parallel download scripts don't overwrite each other's rows."""
    lock = MANIFEST.with_suffix(".lock")
    t0 = time.monotonic()
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() - t0 > timeout_s:
                raise TimeoutError(f"manifest lock held too long: {lock} (delete it if no script is running)")
            time.sleep(0.2)
    try:
        yield
    finally:
        os.close(fd)
        lock.unlink(missing_ok=True)


def upsert_manifest(row: dict) -> None:
    """Insert or replace one manifest row, keyed by (product, year, aoi, file_path, band)."""
    CROPLAND_DIR.mkdir(parents=True, exist_ok=True)
    with _manifest_lock():
        _upsert(row)


def _licence_for(product: str) -> str | None:
    name = product.removeprefix("derived: ")
    for prefix, lic in LICENCES.items():
        if name.startswith(prefix):
            return lic if not product.startswith("derived: ") else f"as source: {lic}"
    return None


def refresh_manifest() -> None:
    """Re-apply the licence table (and sorting) to every existing manifest row."""
    with _manifest_lock():
        rows = read_manifest()
        for r in rows:
            lic = _licence_for(r["product"])
            if lic:
                r["licence"] = lic
        rows.sort(key=lambda r: (r["product"], str(r["year"]), r["aoi"], r["file_path"], r["band"]))
        with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS)
            w.writeheader()
            w.writerows(rows)
    print(f"refreshed {len(rows)} manifest rows")


def _upsert(row: dict) -> None:
    row = {k: row.get(k, "") for k in MANIFEST_COLUMNS}
    lic = _licence_for(row["product"])
    if lic:
        row["licence"] = lic
    for k, v in row.items():
        if isinstance(v, (dict, list)):
            row[k] = json.dumps(v, sort_keys=True)
        elif v is None:
            row[k] = ""
    key = lambda r: (r["product"], str(r["year"]), r["aoi"], r["file_path"], r["band"])
    rows = [r for r in read_manifest() if key(r) != key(row)]
    rows.append(row)
    rows.sort(key=lambda r: (r["product"], str(r["year"]), r["aoi"], r["file_path"], r["band"]))
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS)
        w.writeheader()
        w.writerows(rows)


def file_fields(path: Path) -> dict:
    """File size, checksum and raster CRS/resolution for a delivered file."""
    out = {"file_path": rel(path), "file_size_bytes": path.stat().st_size, "checksum_sha256": sha256(path)}
    if path.suffix.lower() in {".tif", ".tiff"}:
        out.update(raster_meta(path))
    return out


if __name__ == "__main__":
    import sys

    if "--refresh" in sys.argv:
        refresh_manifest()
