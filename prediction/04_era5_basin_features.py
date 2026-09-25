"""
Step 4 - ERA5 rainfall and runoff, summed per dekad.

ERA5 is the European weather reanalysis: a consistent hourly record of the
atmosphere since 1940, at 0.25 degrees (~27 km). Our download covers the
Nile basin (3 S - 33 N, 23 - 37 E), 2000-2025, with two variables:

  tp  total precipitation (rain)
  ro  runoff: water that runs off the land surface instead of soaking in

Both are stored in metres, each hourly value being the amount that fell in
that hour. We checked this by summing a year: 816 mm/yr over the Sudd,
2824 mm/yr over Lake Victoria, 3287 mm/yr over the Ethiopian highlands -
realistic numbers. (If the values were running totals, the Sudd would come
out at ~10,000 mm/yr.)

ERA5 stamps each hour at its END, so 00:00 on 2 Jan holds rain from 23:00-
24:00 on 1 Jan. We shift every stamp back one hour before assigning it to a
dekad. The one hour before 2000 and the last hour of 2025 fall outside the
files and are dropped.

Two outputs:

1. era5_regions_dekadal.csv - one row per dekad, rain and runoff (mm)
   averaged over five regions. These feed Stage 1.
   Why these five: floodwater reaching the Sudd comes from the White Nile
   (Lake Victoria -> Kyoga -> Albert -> Bahr el Jabal) and from the Sobat
   draining the Ethiopian highlands; the corridor's own rain adds local
   flooding. Each region is a lat/lon box - a rough stand-in for a real
   catchment boundary, chosen because it needs no extra data. Treat the
   region names as approximate.

2. era5_corridor_grid.npz - the ERA5 grid cells over the corridor, per
   dekad. These feed Stage 2 as rain / runoff maps.

~10-15 min.

Run: /usr/bin/python3 prediction/04_era5_basin_features.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

ERA5_DIR = C.RAW / "rainfall and runoff"
VARS = ("tp", "ro")

# (lat_south, lat_north, lon_west, lon_east)
REGIONS = {
    "victoria": (-3.0, 1.0, 29.0, 35.0),      # Lake Victoria and its catchment
    "kyoga_albert": (0.5, 3.0, 29.0, 34.0),   # Lakes Kyoga and Albert, upper White Nile
    "jabal": (3.0, 6.0, 29.0, 33.0),          # Bahr el Jabal / Equatoria, White Nile into the Sudd
    "sobat": (6.0, 10.0, 33.0, 37.0),         # Sobat river / Ethiopian highlands
    "corridor": (6.0, 12.0, 28.0, 34.0),      # rain on the study area itself
}

# Covers the flood domain (5.7 - 10.0 N, 28.7 - 35.0 E) with a margin.
CORRIDOR_GRID = (5.5, 10.25, 28.5, 35.25)


def box_slices(lat, lon, box):
    """Index ranges of the grid cells inside a box. ERA5 latitudes run
    north to south, so we search on the sorted values."""
    s, n, w, e = box
    ilat = np.where((lat >= s) & (lat <= n))[0]
    ilon = np.where((lon >= w) & (lon <= e))[0]
    assert ilat.size and ilon.size, f"box {box} outside the ERA5 grid"
    return slice(ilat.min(), ilat.max() + 1), slice(ilon.min(), ilon.max() + 1)


def main() -> None:
    C.ensure_dirs(C.OUT)
    t0 = time.time()

    with xr.open_dataset(ERA5_DIR / f"ERA5_{C.YEAR0}.nc") as ds0:
        lat = ds0["latitude"].to_numpy()
        lon = ds0["longitude"].to_numpy()
    region_idx = {name: box_slices(lat, lon, box) for name, box in REGIONS.items()}
    glat, glon = box_slices(lat, lon, CORRIDOR_GRID)
    grid_lat, grid_lon = lat[glat], lon[glon]

    # Running totals, filled year by year. Units: metres, converted at the end.
    region_sum = np.zeros((C.N_DEKADS, len(REGIONS), len(VARS)))
    grid_sum = np.zeros((C.N_DEKADS, len(VARS), grid_lat.size, grid_lon.size))
    hours_seen = np.zeros(C.N_DEKADS, dtype=np.int64)

    for year in range(C.YEAR0, C.YEAR1 + 1):
        with xr.open_dataset(ERA5_DIR / f"ERA5_{year}.nc") as ds:
            stamps = pd.DatetimeIndex(ds["valid_time"].to_numpy())
            # Shift back one hour: each value belongs to the hour that ENDS at its stamp.
            hours = stamps - pd.Timedelta(hours=1)
            t = C.t_index(hours.year, C.dekad_of_year(hours))
            ok = (t >= 0) & (t < C.N_DEKADS)
            t = t[ok]
            np.add.at(hours_seen, t, 1)
            for v, var in enumerate(VARS):
                values = ds[var].to_numpy()[ok]                       # (hours, lat, lon), metres
                assert np.isfinite(values).all(), f"{year} {var}: NaNs in ERA5"
                for r, (sl_lat, sl_lon) in enumerate(region_idx.values()):
                    np.add.at(region_sum[:, r, v], t, values[:, sl_lat, sl_lon].mean(axis=(1, 2)))
                np.add.at(grid_sum[:, v], t, values[:, glat, glon])
        print(f"{year}: done ({time.time() - t0:.0f}s)")

    # Every dekad should hold 240 hours (10 days); the last dekad of a month
    # 192-264 depending on month length. Anything else is a gap in the files.
    days = []
    for y, d in zip(*C.year_dekad(np.arange(C.N_DEKADS))):
        month, part = (int(d) - 1) // 3 + 1, (int(d) - 1) % 3
        start = pd.Timestamp(int(y), month, [1, 11, 21][part])
        end = (start + pd.offsets.MonthEnd(0)) if part == 2 else start + pd.Timedelta(days=9)
        days.append((end - start).days + 1)
    expected = np.array(days) * 24
    short = np.flatnonzero(hours_seen != expected)
    print(f"dekads with an unexpected hour count: {short.size} "
          f"(expected 1: the last dekad of 2025 misses its final hour, which is stored in a 2026 file)")
    if short.size > 1:
        print("  WARNING - gaps in ERA5 at t =", short[:20])

    mm = 1000.0
    years, dekads = C.year_dekad(np.arange(C.N_DEKADS))
    table = pd.DataFrame({"t": np.arange(C.N_DEKADS), "year": years, "dekad": dekads})
    for r, name in enumerate(REGIONS):
        for v, var in enumerate(VARS):
            table[f"era5_{var}_{name}"] = region_sum[:, r, v] * mm
    table.to_csv(C.OUT / "era5_regions_dekadal.csv", index=False)

    np.savez_compressed(C.OUT / "era5_corridor_grid.npz",
                        tp=(grid_sum[:, 0] * mm).astype(np.float32),
                        ro=(grid_sum[:, 1] * mm).astype(np.float32),
                        lat=grid_lat, lon=grid_lon)

    annual = table.groupby("year")[[f"era5_tp_{n}" for n in REGIONS]].sum().mean()
    print("\nmean annual rainfall per region (mm/yr) - sanity check:")
    print(annual.round(0).to_string())
    print(f"\nwrote era5_regions_dekadal.csv and era5_corridor_grid.npz ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
