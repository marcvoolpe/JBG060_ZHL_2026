"""
Step 2 - every flood detection inside the flood domain, one file per year.

Reads NASA's daily flood masks (MCDWD, 3-day composites at ~232 m), keeps
the detections that fall in the corridor AND in the flood domain from step 1,
and writes them out with their grid column/row.

flood_type follows processing_data/loading.py: 0 = recurring, 1 = unusual.

A missing pixel on a given day means "no flood detected". The NASA product
cannot tell "dry" apart from "not observed" (e.g. cloud), so heavy cloud can
show up as an apparent drop in flooding. This is a limitation of the source
data, stated in the README.

Outputs: raw_data/prediction/pixels_by_year/corridor_pixels_{year}.parquet
         (date, lat, lon, flood_type, gx, gy)

Slow (~1 h).

Run: /usr/bin/python3 prediction/02_extract_pixels.py
"""

import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

step1 = import_module("01_domain_mask")


def main() -> None:
    out_dir = C.OUT / "pixels_by_year"
    C.ensure_dirs(out_dir)
    corridor = step1.corridor_polygons()
    ever = pd.read_parquet(C.OUT / "ever_flooded_pixels.parquet", columns=["gx", "gy"])
    # Encode (gx, gy) as one integer so membership is a fast vectorised test.
    width = int(ever["gx"].max()) + 1
    domain_keys = pd.Index(ever["gy"] * width + ever["gx"])

    total = 0
    for year in range(C.YEAR0, C.YEAR1 + 1):
        df = step1.flood_pixels_in_corridor(year, corridor)
        if df.empty:
            print(year, "no detections")
            continue
        df = df[(df["gy"] * width + df["gx"]).isin(domain_keys)]
        df = df[["date", "lat", "lon", "flood_type", "gx", "gy"]]
        df.to_parquet(out_dir / f"corridor_pixels_{year}.parquet", index=False)
        total += len(df)
        print(f"{year}: {len(df):,} pixel-days")
    print(f"total {total:,} pixel-days")


if __name__ == "__main__":
    main()
