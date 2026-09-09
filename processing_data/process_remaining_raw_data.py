from pathlib import Path
import re

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import xarray as xr

from processing_data.loading import load_flood_masks
from processing_data.loading_impact_data import (
    load_GDP,
    load_health_facilities,
    load_ipc_data,
)


RAW_DIR = Path("raw_data")
PROCESSED_DIR = Path("processed-data")


def ensure_dir(name: str) -> Path:
    out_dir = PROCESSED_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def process_administrative_boundaries() -> list[Path]:
    out_dir = ensure_dir("Administrative boundaries")
    outputs = []

    for path in sorted((RAW_DIR / "Administrative boundaries").glob("ssd_admin*.geojson")):
        if "adminlines" in path.name or "adminpoints" in path.name:
            continue

        level_match = re.search(r"admin(\d+)", path.stem)
        level = int(level_match.group(1)) if level_match else None
        gdf = gpd.read_file(path)
        metric = gdf.to_crs(6933)

        rows = []
        for idx, row in gdf.iterrows():
            bounds = row.geometry.bounds if row.geometry is not None else (np.nan,) * 4
            centroid = row.geometry.centroid if row.geometry is not None else None
            props = row.drop(labels="geometry").to_dict()
            rows.append(
                {
                    "admin_level": level,
                    "feature_index": idx,
                    "name": props.get(f"adm{level}_name") or props.get("adm0_name"),
                    "pcode": props.get(f"adm{level}_pcode") or props.get("adm0_pcode"),
                    "parent_name": props.get(f"adm{level - 1}_name") if level and level > 0 else np.nan,
                    "parent_pcode": props.get(f"adm{level - 1}_pcode") if level and level > 0 else np.nan,
                    "centroid_latitude": centroid.y if centroid is not None else np.nan,
                    "centroid_longitude": centroid.x if centroid is not None else np.nan,
                    "min_longitude": bounds[0],
                    "min_latitude": bounds[1],
                    "max_longitude": bounds[2],
                    "max_latitude": bounds[3],
                    "area_km2": float(metric.geometry.iloc[idx].area / 1_000_000),
                    "source_file": path.name,
                }
            )

        out_file = out_dir / f"{path.stem}_processed.csv"
        pd.DataFrame(rows).to_csv(out_file, index=False)
        outputs.append(out_file)

    return outputs


def process_gdp() -> Path:
    out_dir = ensure_dir("GDP")
    gdp = load_GDP()
    df = pd.DataFrame(
        {
            "country": "South Sudan",
            "indicator": "GDP (current US$)",
            "year": sorted(gdp.keys()),
            "gdp_current_usd": [gdp[year] for year in sorted(gdp.keys())],
            "source_file": "API_SSD_DS2_en_csv_v2_2529.csv",
        }
    )
    out_file = out_dir / "south_sudan_gdp_current_usd_processed.csv"
    df.to_csv(out_file, index=False)
    return out_file


def process_ipc() -> list[Path]:
    out_dir = ensure_dir("IPC")
    wide = load_ipc_data()
    wide_file = out_dir / "ipc_phase3plus_county_wide_processed.csv"
    wide.to_csv(wide_file, index=False)

    long = wide.melt(
        id_vars=["Start Date", "End Date"],
        var_name="county",
        value_name="phase3plus_population",
    ).dropna(subset=["phase3plus_population"])
    long = long.rename(columns={"Start Date": "start_date", "End Date": "end_date"})
    long["source_folder"] = "raw_data/IPC"
    long_file = out_dir / "ipc_phase3plus_county_long_processed.csv"
    long.to_csv(long_file, index=False)
    return [wide_file, long_file]


def process_health_facilities() -> Path:
    out_dir = ensure_dir("health facilities")
    gdf = load_health_facilities()
    columns = {
        "Country": "country",
        "Admin1": "admin1",
        "Facility_n": "facility_name",
        "Facility_t": "facility_type",
        "Ownership": "ownership",
        "Lat": "latitude",
        "Long": "longitude",
        "LL_source": "location_source",
    }
    df = gdf[list(columns)].rename(columns=columns)
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[(df["latitude"] != 0) | (df["longitude"] != 0)]
    df["source_file"] = "Sub-Saharan_public_health_facilities.geojson"

    out_file = out_dir / "south_sudan_health_facilities_processed.csv"
    df.to_csv(out_file, index=False)
    return out_file


def raster_summary(path: Path, value_column: str, statistic_prefix: str) -> dict:
    with rasterio.open(path) as src:
        valid_pixel_count = 0
        value_sum = 0.0
        value_min = np.inf
        value_max = -np.inf

        for _, window in src.block_windows(1):
            arr = src.read(1, window=window).astype("float64")
            if src.nodata is not None:
                arr[arr == src.nodata] = np.nan

            valid = np.isfinite(arr)
            if not valid.any():
                continue

            valid_values = arr[valid]
            valid_pixel_count += int(valid_values.size)
            value_sum += float(valid_values.sum())
            value_min = min(value_min, float(valid_values.min()))
            value_max = max(value_max, float(valid_values.max()))

        value_mean = value_sum / valid_pixel_count if valid_pixel_count else np.nan
        bounds = src.bounds
        return {
            "source_file": path.name,
            "width": src.width,
            "height": src.height,
            "crs": str(src.crs),
            "min_longitude": bounds.left,
            "min_latitude": bounds.bottom,
            "max_longitude": bounds.right,
            "max_latitude": bounds.top,
            "valid_pixel_count": valid_pixel_count,
            f"{statistic_prefix}_sum": value_sum,
            f"{statistic_prefix}_mean": value_mean,
            f"{statistic_prefix}_min": value_min if valid_pixel_count else np.nan,
            f"{statistic_prefix}_max": value_max if valid_pixel_count else np.nan,
            "value_unit": value_column,
        }


def process_worldpop() -> Path:
    out_dir = ensure_dir("worldpop")
    rows = []
    for path in sorted((RAW_DIR / "worldpop").glob("ssd_pop_*_CN_100m_R2025A_v1.tif")):
        year = int(re.search(r"ssd_pop_(\d{4})", path.name).group(1))
        row = raster_summary(path, "people per pixel", "population")
        row["year"] = year
        rows.append(row)

    df = pd.DataFrame(rows).sort_values("year")
    cols = ["year"] + [col for col in df.columns if col != "year"]
    out_file = out_dir / "south_sudan_worldpop_annual_summary_processed.csv"
    df[cols].to_csv(out_file, index=False)
    return out_file


def process_farmland() -> list[Path]:
    out_dir = ensure_dir("farmland")
    rows = []

    cattle_path = RAW_DIR / "farmland/geonode__cattle_gha.tif"
    cattle = raster_summary(cattle_path, "cattle per pixel", "cattle")
    cattle["dataset"] = "cattle"
    rows.append(cattle)

    for mask_type in ["crop", "rangeland"]:
        path = RAW_DIR / f"farmland/asap_mask_{mask_type}_v04.tif"
        row = raster_summary(path, "percent of pixel area", f"{mask_type}_area_percent")
        row["dataset"] = mask_type
        rows.append(row)

    summary = pd.DataFrame(rows)
    summary_file = out_dir / "farmland_and_cattle_raster_summary_processed.csv"
    summary.to_csv(summary_file, index=False)

    metadata_file = out_dir / "cattle_population_source_notes_processed.csv"
    source_txt = RAW_DIR / "farmland/cattle-population-in-the-gha-region.txt"
    notes = source_txt.read_text(encoding="utf-8", errors="replace").splitlines()
    pd.DataFrame({"line_number": range(1, len(notes) + 1), "text": notes}).to_csv(
        metadata_file, index=False
    )
    return [summary_file, metadata_file]


def process_rainfall_runoff() -> Path:
    out_dir = ensure_dir("rainfall and runoff")
    rows = []

    for path in sorted((RAW_DIR / "rainfall and runoff").glob("ERA5_*.nc")):
        year = int(re.search(r"ERA5_(\d{4})", path.name).group(1))
        with xr.open_dataset(path) as ds:
            spatial_mean = ds[["tp", "ro"]].mean(dim=["latitude", "longitude"])
            summary = (
                spatial_mean.resample(valid_time="1D")
                .sum()
                .to_dataframe()
                .reset_index()
            )
            summary = summary.rename(
                columns={
                    "valid_time": "date",
                    "tp": "precipitation_mean_m_day",
                    "ro": "runoff_mean_m_day",
                }
            )
            summary["year"] = year
            summary["source_file"] = path.name
            summary["grid_latitude_count"] = int(ds.sizes["latitude"])
            summary["grid_longitude_count"] = int(ds.sizes["longitude"])
            rows.append(summary)

    df = pd.concat(rows, ignore_index=True)
    df = df[
        [
            "year",
            "date",
            "precipitation_mean_m_day",
            "runoff_mean_m_day",
            "grid_latitude_count",
            "grid_longitude_count",
            "source_file",
        ]
    ]
    out_file = out_dir / "era5_rainfall_runoff_daily_mean_processed.csv"
    df.to_csv(out_file, index=False)
    return out_file


def process_evapotranspiration(
    target_longitude: float = 30.725,
    target_latitude: float = 9.475,
) -> Path:
    out_dir = ensure_dir("evapotranspiration")
    variable = "ReferenceET_PenmanMonteith_FAO56"
    rows = []

    for year_dir in sorted((RAW_DIR / "evapotranspiration").glob("ET_*")):
        if not year_dir.is_dir():
            continue
        year = int(year_dir.name.split("_")[1])
        for path in sorted(year_dir.glob("*.nc")):
            with xr.open_dataset(path) as ds:
                da = ds[variable].squeeze()
                value = float(
                    da.sel(lat=target_latitude, lon=target_longitude, method="nearest").values
                )
                nearest_lat = float(da["lat"].sel(lat=target_latitude, method="nearest").values)
                nearest_lon = float(da["lon"].sel(lon=target_longitude, method="nearest").values)
                rows.append(
                    {
                        "year": year,
                        "date": pd.Timestamp(ds["time"].values[0]).date(),
                        "target_latitude": target_latitude,
                        "target_longitude": target_longitude,
                        "grid_latitude": nearest_lat,
                        "grid_longitude": nearest_lon,
                        "reference_et_mm_day": value,
                        "source_file": path.name,
                    }
                )

    df = pd.DataFrame(rows).sort_values(["date"])
    out_file = out_dir / "reference_evapotranspiration_gridcell_daily_processed.csv"
    df.to_csv(out_file, index=False)
    return out_file


def process_flood_masks(years: np.ndarray | None = None) -> Path:
    out_dir = ensure_dir("flood_masks")
    if years is None:
        years = np.arange(2000, 2026)

    rows = []
    for year in years:
        df = load_flood_masks(np.array([year]))
        if df.empty:
            continue
        grouped = (
            df.groupby(["date", "tile", "flood_type"])
            .agg(
                flooded_pixel_count=("flood_type", "size"),
                min_latitude=("lat", "min"),
                max_latitude=("lat", "max"),
                min_longitude=("lon", "min"),
                max_longitude=("lon", "max"),
            )
            .reset_index()
        )
        grouped["year"] = year
        rows.append(grouped)

    combined = pd.concat(rows, ignore_index=True)
    combined["flood_type_label"] = combined["flood_type"].map({0: "recurring", 1: "unusual"})
    combined = combined[
        [
            "year",
            "date",
            "tile",
            "flood_type",
            "flood_type_label",
            "flooded_pixel_count",
            "min_latitude",
            "max_latitude",
            "min_longitude",
            "max_longitude",
        ]
    ].sort_values(["date", "tile", "flood_type"])

    out_file = out_dir / "flood_masks_daily_counts_processed.csv"
    combined.to_csv(out_file, index=False)
    return out_file


def process_remaining_raw_data(include_slow: bool = True) -> list[Path]:
    outputs = []
    outputs.extend(process_administrative_boundaries())
    outputs.append(process_gdp())
    outputs.extend(process_ipc())
    outputs.append(process_health_facilities())
    outputs.append(process_worldpop())
    outputs.extend(process_farmland())
    outputs.append(process_rainfall_runoff())
    outputs.append(process_flood_masks())
    if include_slow:
        outputs.append(process_evapotranspiration())
    return outputs


def main() -> None:
    outputs = process_remaining_raw_data(include_slow=True)
    print("Saved processed files:")
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
