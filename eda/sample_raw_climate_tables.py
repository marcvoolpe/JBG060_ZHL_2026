from pathlib import Path

import pandas as pd
import xarray as xr


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw_data"
OUT_DIR = ROOT / "eda" / "outputs" / "raw_climate_grid_samples"

ERA5_PATH = RAW_DIR / "rainfall and runoff" / "ERA5_2000.nc"
ET_DIR = RAW_DIR / "evapotranspiration" / "ET_2000"
ET_VARIABLE = "ReferenceET_PenmanMonteith_FAO56"

SAMPLE_DATE = "2000-08-01"
SAMPLE_TIME = "2000-08-01T12:00:00"
SAMPLE_LATS = [4.0, 6.0, 8.0, 10.0, 12.0]
SAMPLE_LONS = [28.0, 30.0, 32.0, 34.0, 36.0]
POINT_LAT = 9.5
POINT_LON = 31.5


def write_schema_summary() -> Path:
    rows = []
    with xr.open_dataset(ERA5_PATH) as ds:
        for var in ["tp", "ro"]:
            da = ds[var]
            rows.append(
                {
                    "source": "ERA5 rainfall/runoff",
                    "variable": var,
                    "long_name": da.attrs.get("long_name"),
                    "units": da.attrs.get("units"),
                    "dimensions": " x ".join(da.dims),
                    "shape": " x ".join(str(i) for i in da.shape),
                    "latitude_range": f"{float(ds.latitude.min()):.2f} to {float(ds.latitude.max()):.2f}",
                    "longitude_range": f"{float(ds.longitude.min()):.2f} to {float(ds.longitude.max()):.2f}",
                    "time_range": f"{pd.Timestamp(ds.valid_time.min().values)} to {pd.Timestamp(ds.valid_time.max().values)}",
                }
            )

    et_path = ET_DIR / f"ReferenceET-PenmanMonteith-FAO56_C3S-glob-agric_AgERA5_{SAMPLE_DATE.replace('-', '')}_final-v2.0.0.area-subset.33.37.-3.23.nc"
    with xr.open_dataset(et_path) as ds:
        da = ds[ET_VARIABLE]
        rows.append(
            {
                "source": "AgERA5 reference ET",
                "variable": ET_VARIABLE,
                "long_name": da.attrs.get("long_name"),
                "units": da.attrs.get("units"),
                "dimensions": " x ".join(da.dims),
                "shape": " x ".join(str(i) for i in da.shape),
                "latitude_range": f"{float(ds.lat.min()):.2f} to {float(ds.lat.max()):.2f}",
                "longitude_range": f"{float(ds.lon.min()):.2f} to {float(ds.lon.max()):.2f}",
                "time_range": f"{pd.Timestamp(ds.time.min().values)} to {pd.Timestamp(ds.time.max().values)}",
            }
        )

    out = OUT_DIR / "raw_netcdf_schema_summary.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def write_era5_spatial_grid_sample() -> Path:
    rows = []
    with xr.open_dataset(ERA5_PATH) as ds:
        slice_ds = ds[["tp", "ro"]].sel(valid_time=SAMPLE_TIME)
        for lat in SAMPLE_LATS:
            for lon in SAMPLE_LONS:
                point = slice_ds.sel(latitude=lat, longitude=lon, method="nearest")
                grid_lat = float(point.latitude.values)
                grid_lon = float(point.longitude.values)
                tp_m = float(point.tp.values)
                ro_m = float(point.ro.values)
                rows.append(
                    {
                        "valid_time": SAMPLE_TIME,
                        "requested_latitude": lat,
                        "requested_longitude": lon,
                        "grid_latitude": grid_lat,
                        "grid_longitude": grid_lon,
                        "tp_precipitation_m": tp_m,
                        "tp_precipitation_mm": tp_m * 1000,
                        "ro_runoff_m": ro_m,
                        "ro_runoff_mm": ro_m * 1000,
                    }
                )
    out = OUT_DIR / "era5_raw_spatial_grid_sample_2000_08_01_12utc.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def write_era5_hourly_point_sample() -> Path:
    with xr.open_dataset(ERA5_PATH) as ds:
        point = ds[["tp", "ro"]].sel(
            latitude=POINT_LAT, longitude=POINT_LON, method="nearest"
        )
        point = point.sel(valid_time=slice(f"{SAMPLE_DATE}T00:00:00", f"{SAMPLE_DATE}T23:00:00"))
        df = point.to_dataframe().reset_index()
        df = df.rename(columns={"tp": "tp_precipitation_m", "ro": "ro_runoff_m"})
        df["tp_precipitation_mm"] = df["tp_precipitation_m"] * 1000
        df["ro_runoff_mm"] = df["ro_runoff_m"] * 1000
        df = df[
            [
                "valid_time",
                "latitude",
                "longitude",
                "tp_precipitation_m",
                "tp_precipitation_mm",
                "ro_runoff_m",
                "ro_runoff_mm",
            ]
        ]
    out = OUT_DIR / "era5_raw_hourly_point_sample_2000_08_01.csv"
    df.to_csv(out, index=False)
    return out


def et_path_for_date(date: str) -> Path:
    return ET_DIR / f"ReferenceET-PenmanMonteith-FAO56_C3S-glob-agric_AgERA5_{date.replace('-', '')}_final-v2.0.0.area-subset.33.37.-3.23.nc"


def write_et_spatial_grid_sample() -> Path:
    rows = []
    with xr.open_dataset(et_path_for_date(SAMPLE_DATE)) as ds:
        da = ds[ET_VARIABLE].squeeze()
        for lat in SAMPLE_LATS:
            for lon in SAMPLE_LONS:
                point = da.sel(lat=lat, lon=lon, method="nearest")
                rows.append(
                    {
                        "date": SAMPLE_DATE,
                        "requested_latitude": lat,
                        "requested_longitude": lon,
                        "grid_latitude": float(point.lat.values),
                        "grid_longitude": float(point.lon.values),
                        "reference_et_mm_day": float(point.values),
                    }
                )
    out = OUT_DIR / "et_raw_spatial_grid_sample_2000_08_01.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def write_et_daily_point_sample() -> Path:
    rows = []
    for date in pd.date_range(SAMPLE_DATE, periods=10, freq="D"):
        date_text = date.strftime("%Y-%m-%d")
        with xr.open_dataset(et_path_for_date(date_text)) as ds:
            da = ds[ET_VARIABLE].squeeze()
            point = da.sel(lat=POINT_LAT, lon=POINT_LON, method="nearest")
            rows.append(
                {
                    "date": date_text,
                    "requested_latitude": POINT_LAT,
                    "requested_longitude": POINT_LON,
                    "grid_latitude": float(point.lat.values),
                    "grid_longitude": float(point.lon.values),
                    "reference_et_mm_day": float(point.values),
                }
            )
    out = OUT_DIR / "et_raw_daily_point_sample_2000_08_01_to_2000_08_10.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def write_readme(paths: list[Path]) -> Path:
    text = """# Raw Climate Grid Samples

These files are small table views extracted directly from the original NetCDF files.
They are not final processed datasets.

- ERA5 rainfall/runoff raw files are hourly grids over latitude and longitude.
- `tp` is total precipitation in meters; `ro` is runoff in meters.
- AgERA5 ET raw files are daily grids over latitude and longitude.
- `ReferenceET_PenmanMonteith_FAO56` is reference evapotranspiration in mm/day.
- The samples use 2000-08-01 because it is in the regional wet season.

Generated sample files:
"""
    for path in paths:
        text += f"\n- {path.name}"
    out = OUT_DIR / "README.md"
    out.write_text(text + "\n")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = [
        write_schema_summary(),
        write_era5_spatial_grid_sample(),
        write_era5_hourly_point_sample(),
        write_et_spatial_grid_sample(),
        write_et_daily_point_sample(),
    ]
    write_readme(paths)
    print(f"Saved raw climate sample tables to {OUT_DIR}")
    for path in paths:
        print(path.name)


if __name__ == "__main__":
    main()
