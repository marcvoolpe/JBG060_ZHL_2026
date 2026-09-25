"""
Step 1 - the flood domain: which pixels in the corridor have EVER flooded.

The corridor is Unity + Jonglei + Upper Nile, cut out with the real county
(admin-2) polygons. An earlier version used a longitude bounding box that
silently dropped most of Unity state; do not go back to a bbox.

Why a domain at all: about 76% of corridor pixels never flooded once in
2000-2025. A model trained on them would learn "predict dry" and look
excellent while telling us nothing. We keep only the ~1.08 million pixels
that flooded at least once, as INFLOW-AI keeps only its basin. This uses
the whole 2000-2025 record, so it is a fixed study-area definition, not a
model input.

Coverage limit: the NASA flood tiles (h20v08, h21v08) cover 0-10 N only.
Upper Nile reaches ~12 N, so its northern counties are not in the data.

Outputs (in raw_data/prediction/):
  ever_flooded_pixels.parquet   gx, gy (grid column/row), lon, lat
  never_flooded_fraction.csv    the 76% figure

Slow (~1 h: reads every flood mask 2000-2025).

Run: python prediction/01_domain_mask.py
"""

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common as C  # noqa: E402
from processing_data.loading import load_flood_masks  # noqa: E402


def corridor_polygons() -> gpd.GeoDataFrame:
    admin2 = gpd.read_file(C.ADMIN2)
    corridor = admin2[admin2["adm1_name"].isin(C.STATES)][["adm1_name", "adm2_name", "geometry"]].copy()
    assert set(corridor["adm1_name"]) == set(C.STATES), "a state is missing - check adm1_name spelling"
    return corridor


def flood_pixels_in_corridor(year: int, corridor: gpd.GeoDataFrame) -> pd.DataFrame:
    """All flood detections of one year that fall inside the corridor, with
    their grid column/row. Shared with 02_extract_pixels.py."""
    with C.repo_cwd():
        df = load_flood_masks(np.array([year]))
    if df.empty:
        return df
    inside = shapely.contains_xy(corridor.union_all(), df["lon"].to_numpy(), df["lat"].to_numpy())
    df = df[inside].copy()
    lon_min, lat_min, _, _ = corridor.total_bounds
    df["gx"] = np.round((df["lon"].to_numpy() - lon_min) / C.RES).astype(np.int64)
    df["gy"] = np.round((df["lat"].to_numpy() - lat_min) / C.RES).astype(np.int64)
    return df


def main() -> None:
    C.ensure_dirs(C.OUT)
    corridor = corridor_polygons()
    lon_min, lat_min, lon_max, lat_max = corridor.total_bounds

    ever = set()
    for year in range(C.YEAR0, C.YEAR1 + 1):
        df = flood_pixels_in_corridor(year, corridor)
        ever.update(zip(df["gx"].tolist(), df["gy"].tolist()))
        print(f"{year}: {len(ever):,} ever-flooded pixels so far")

    # Denominator: every corridor land pixel on the same grid.
    xs = lon_min + C.RES * np.arange(int(round((lon_max - lon_min) / C.RES)) + 1)
    ys = lat_min + C.RES * np.arange(int(round((lat_max - lat_min) / C.RES)) + 1)
    xx, yy = np.meshgrid(xs, ys)
    n_land = int(shapely.contains_xy(corridor.union_all(), xx.ravel(), yy.ravel()).sum())

    out = pd.DataFrame(sorted(ever), columns=["gx", "gy"])
    out["lon"] = lon_min + out["gx"] * C.RES
    out["lat"] = lat_min + out["gy"] * C.RES
    out.to_parquet(C.OUT / "ever_flooded_pixels.parquet", index=False)

    frac = len(out) / n_land
    pd.DataFrame([{"corridor_land_pixels": n_land, "ever_flooded_pixels": len(out),
                   "fraction_ever_flooded": frac, "fraction_never_flooded": 1 - frac}]
                 ).to_csv(C.OUT / "never_flooded_fraction.csv", index=False)
    print(f"corridor land pixels {n_land:,}; ever flooded {len(out):,} ({frac:.1%}); never flooded {1 - frac:.1%}")


if __name__ == "__main__":
    main()
