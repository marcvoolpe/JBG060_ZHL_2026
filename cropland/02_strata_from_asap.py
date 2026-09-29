"""
Step 2 (preview) - How much of each study area the ASAP crop mask calls crop.

This is a first look with the one cropland map we already have on disk, ASAP
v04 (~500 m, value = percent of the cell that is crop). The real strata come
from the 7-map agreement map in Earth Engine; this only gives a first idea of
how small the "crop" stratum is, so the sample-size numbers are not guesses.

Output: cropland/asap_crop_share_by_county.csv
Run from group_repo: python cropland/02_strata_from_asap.py
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw_data"
COUNTIES = ["Aweil North", "Aweil East", "Aweil Centre", "Aweil South", "Aweil West", "Bor South"]


def main() -> None:
    admin = gpd.read_file(RAW / "Administrative boundaries" / "ssd_admin2.geojson")
    admin = admin[admin.adm2_name.isin(COUNTIES)]
    area_ha = admin.to_crs(6933).area / 1e4          # equal-area projection for hectares
    rows = []
    with rasterio.open(RAW / "farmland" / "asap_mask_crop_v04.tif") as src:
        for (_, c), ha in zip(admin.iterrows(), area_ha):
            arr, _ = mask(src, [c.geometry], crop=True, filled=True, nodata=255)
            v = arr[0][arr[0] != 255].astype(float)
            v = v[v <= 100]
            rows.append({"county": c.adm2_name, "area_ha": round(ha),
                         "asap_crop_pct": round(v.mean(), 2),                 # mean crop fraction of the county
                         "cells_any_crop_pct": round((v > 0).mean() * 100, 1),  # cells ASAP says have some crop
                         "cells": v.size})
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "asap_crop_share_by_county.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
