"""Download Digital Earth Africa's cropland extent 2019 (product `crop_mask`) tiles for the AOIs.

South Sudan is mapped by DE Africa's Sahel regional model. The tiles are found
through DE Africa's public STAC API, and downloaded as delivered (96 km x 96 km
tiles, 10 m, EPSG:6933) from the public S3 bucket `deafrica-services`
(af-south-1) over HTTPS. Each tile folder holds a producer `.sha1` file; every
download is checked against it and against the S3 object size.

Usage (repo root, global Python 3.13):
    python -m processing_data.cropland.download_deafrica_cropmask [--aoi aweil borsouth]
"""

from __future__ import annotations

import argparse
import hashlib
import time
import xml.etree.ElementTree as ET

import requests

from processing_data.cropland.common import AOIS, aoi_geometry, file_fields, product_dir, today, upsert_manifest

STAC_SEARCH = "https://explorer.digitalearth.africa/stac/search"
COLLECTION = "crop_mask"
BUCKET_HTTPS = "https://deafrica-services.s3.af-south-1.amazonaws.com"
DOCS = "https://docs.digitalearthafrica.org/en/latest/data_specs/Cropland_extent_specs.html"
BAND_CODES = {
    "mask": "pixel-based crop extent: 1 = crop, 0 = not crop",
    "prob": "pixel crop probability 0-100 (%)",
    "filtered": "object-based (segment-filtered) crop extent: 1 = crop, 0 = not crop",
}


def stac_items(bbox: list[float]) -> list[dict]:
    r = requests.get(STAC_SEARCH, params={"collections": COLLECTION, "bbox": ",".join(map(str, bbox)), "limit": 100},
                     timeout=120)
    r.raise_for_status()
    js = r.json()
    assert js.get("numberMatched", len(js["features"])) == len(js["features"]), "STAC paging needed"
    return js["features"]


def list_prefix(prefix: str) -> dict[str, int]:
    r = requests.get(BUCKET_HTTPS, params={"list-type": "2", "prefix": prefix}, timeout=120)
    r.raise_for_status()
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    root = ET.fromstring(r.content)
    return {c.find("s3:Key", ns).text: int(c.find("s3:Size", ns).text) for c in root.findall("s3:Contents", ns)}


def fetch(url: str, dest, size: int | None, retries: int = 5) -> None:
    if dest.exists() and (size is None or dest.stat().st_size == size):
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    for k in range(retries):
        try:
            with requests.get(url, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            if size is not None and tmp.stat().st_size != size:
                raise IOError(f"size mismatch {tmp.stat().st_size} != {size}")
            tmp.replace(dest)
            return
        except Exception as exc:
            if k == retries - 1:
                raise
            print(f"    retry {k + 1} for {dest.name}: {exc}")
            time.sleep(10 * (k + 1))


def sha1(path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while b := f.read(1 << 22):
            h.update(b)
    return h.hexdigest()


def parse_sha1_file(path) -> dict[str, str]:
    """Lines look like '<hex>\t<file name>' (sha1sum format)."""
    out = {}
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            out[parts[-1].lstrip("*")] = parts[0].lower()
    return out


def run(aoi: str) -> None:
    geom = aoi_geometry(aoi, "EPSG:4326")
    items = stac_items(list(geom.bounds))
    out = product_dir("deafrica_cropmask")
    print(f"DE Africa crop_mask ({aoi}): {len(items)} tiles")
    for it in items:
        # only tiles that touch the buffered AOI polygon (the bbox search is wider)
        from shapely.geometry import shape
        if not shape(it["geometry"]).intersects(geom):
            continue
        region = it["properties"]["odc:region_code"]
        href = it["assets"]["mask"]["href"]              # s3://deafrica-services/<prefix>/..._mask.tif
        prefix = href.replace("s3://deafrica-services/", "").rsplit("/", 1)[0] + "/"
        keys = list_prefix(prefix)
        tile_dir = out / region
        tile_dir.mkdir(exist_ok=True)
        for key, size in keys.items():
            fetch(f"{BUCKET_HTTPS}/{key}", tile_dir / key.rsplit("/", 1)[1], size)
        sums = {}
        for f in tile_dir.glob("*.sha1"):
            sums.update(parse_sha1_file(f))
        for band, codes in BAND_CODES.items():
            name = f"crop_mask_{region}_2019--P1Y_{band}.tif"
            path = tile_dir / name
            expected = sums.get(name)
            got = sha1(path)
            ok = expected is not None and expected == got
            if expected is not None and not ok:
                raise IOError(f"SHA-1 mismatch for {name}: {got} != {expected}")
            row = dict(product="Digital Earth Africa cropland extent (crop_mask)",
                       version=f"dataset {it['properties'].get('odc:dataset_version')} (Sahel regional model)",
                       year="2019", aoi=aoi, source=f"{BUCKET_HTTPS}/{prefix}{name} (STAC item {it['id']})",
                       access_date=today(), licence="CC-BY-4.0", band=band,
                       class_codes=codes + "; see README on the no-data value",
                       ee_task_id="n/a (direct download)",
                       export_params={"stac": STAC_SEARCH, "collection": COLLECTION, "tile": region,
                                      "producer_sha1": expected, "sha1_verified": ok},
                       status="obtained" if ok else "not verified",
                       notes=f"Delivered 96 km tile, unmodified. Producer SHA-1 {'matches' if ok else 'not found'}. Docs: {DOCS}")
            row.update(file_fields(path))
            upsert_manifest(row)
        print(f"  {region}: {len(keys)} files, sha1 {'ok' if all(sums.get(f'crop_mask_{region}_2019--P1Y_{b}.tif') for b in BAND_CODES) else 'MISSING'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aoi", nargs="+", default=list(AOIS), choices=list(AOIS))
    for a in ap.parse_args().aoi:
        run(a)


if __name__ == "__main__":
    main()
