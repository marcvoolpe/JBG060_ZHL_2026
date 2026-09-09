from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import xarray as xr
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw_data"
PROCESSED_DIR = ROOT / "processed-data"
OUT_DIR = ROOT / "eda" / "outputs" / "revised_spatial_eda"
CACHE_DIR = OUT_DIR / "cache"
FIG_DIR = OUT_DIR / "figures"

ADMIN0_PATH = RAW_DIR / "Administrative boundaries" / "ssd_admin0.geojson"
ADMIN1_PATH = RAW_DIR / "Administrative boundaries" / "ssd_admin1.geojson"
ADMIN2_PATH = RAW_DIR / "Administrative boundaries" / "ssd_admin2.geojson"
FLOOD_DIR = RAW_DIR / "flood_masks"
ERA5_DIR = RAW_DIR / "rainfall and runoff"
ET_DIR = RAW_DIR / "evapotranspiration"
DISCHARGE_PATH = (
    PROCESSED_DIR
    / "Darthmouth Flood Observatory"
    / "dartmouth_discharge_all_processed_with_station_info.csv"
)
WATER_LEVEL_PATH = PROCESSED_DIR / "Water levels lakes" / "water_levels_all_processed.csv"

FLOOD_TILE_EXTENT = {"lon_min": 20.0, "lon_max": 40.0, "lat_min": 0.0, "lat_max": 10.0}
FLOOD_PIXEL_AREA_KM2 = 0.25 * 0.25
ET_VARIABLE = "ReferenceET_PenmanMonteith_FAO56"

RELEVANT_DISCHARGE = {
    100205: "primary_white_nile_near_south_sudan",
    1541: "downstream_white_nile_context",
    1542: "downstream_white_nile_context",
    1543: "downstream_white_nile_context",
    1547: "downstream_white_nile_context",
    1548: "downstream_main_nile_context",
    11808: "downstream_main_nile_context",
    11842: "downstream_main_nile_context",
}
EXCLUDED_DISCHARGE = {
    1505: "Omo to Lake Turkana, not White Nile path",
    1544: "Blue Nile system, not South Sudan upstream",
    1545: "Blue Nile system, not South Sudan upstream",
    28546: "Atbara system, not South Sudan upstream",
}


@dataclass(frozen=True)
class Region:
    region_id: str
    label: str
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float
    notes: str


HYDRO_REGIONS = [
    Region(
        "ssd_full",
        "South Sudan full boundary",
        24.0,
        36.1,
        3.4,
        12.3,
        "Climate cells inside the full South Sudan admin0 polygon.",
    ),
    Region(
        "ssd_flood_tile_overlap",
        "South Sudan area covered by local flood tiles",
        24.0,
        36.1,
        3.4,
        10.0,
        "Climate cells inside South Sudan and inside h20v08+h21v08 flood tile latitude coverage.",
    ),
    Region(
        "victoria_kyoga_albert_upstream",
        "Lake Victoria-Kyoga-Albert upstream corridor",
        29.5,
        34.5,
        -1.5,
        3.5,
        "Heuristic upstream lake corridor: Victoria -> Kyoga -> Albert -> White Nile.",
    ),
    Region(
        "bahr_el_jebel_south",
        "Bahr el Jebel southern inflow corridor",
        29.0,
        33.0,
        3.0,
        7.0,
        "Heuristic corridor from Albert Nile/Bahr el Jebel into southern South Sudan.",
    ),
    Region(
        "sobat_pibor_east",
        "Sobat-Pibor eastern tributary corridor",
        31.5,
        36.5,
        6.0,
        10.5,
        "Heuristic eastern tributary corridor including Sobat/Pibor/Akobo influence.",
    ),
    Region(
        "western_floodplain",
        "Western South Sudan floodplain context",
        24.0,
        31.0,
        6.0,
        10.5,
        "Heuristic western South Sudan rainfall/runoff context.",
    ),
]


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def read_admin(level: int) -> gpd.GeoDataFrame:
    path = {0: ADMIN0_PATH, 1: ADMIN1_PATH, 2: ADMIN2_PATH}[level]
    return gpd.read_file(path).to_crs("EPSG:4326")


def flood_extent_polygon():
    return box(
        FLOOD_TILE_EXTENT["lon_min"],
        FLOOD_TILE_EXTENT["lat_min"],
        FLOOD_TILE_EXTENT["lon_max"],
        FLOOD_TILE_EXTENT["lat_max"],
    )


def date_range() -> pd.DatetimeIndex:
    return pd.date_range("2000-01-01", "2025-12-31", freq="D")


def zscore(series: pd.Series) -> pd.Series:
    std = series.std()
    if pd.isna(std) or std == 0:
        return series * 0
    return (series - series.mean()) / std


def parse_flood_path(path: Path) -> dict:
    match = re.search(r"flood_events_(h\d+v\d+)_(\d{4})\.parquet$", path.name)
    return {
        "flood_type": path.parent.name.replace("compact_", ""),
        "tile": match.group(1),
        "year": int(match.group(2)),
    }


def build_flood_coverage_summary(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "flood_admin_coverage_summary.csv"
    if out.exists() and not force:
        return pd.read_csv(out)

    admin1 = read_admin(1)
    admin2 = read_admin(2)
    tile = gpd.GeoDataFrame({"tile_extent": ["h20v08+h21v08"]}, geometry=[flood_extent_polygon()], crs="EPSG:4326")

    rows = []
    for level, admin, name_col, pcode_col in [
        (1, admin1, "adm1_name", "adm1_pcode"),
        (2, admin2, "adm2_name", "adm2_pcode"),
    ]:
        metric = admin.to_crs("EPSG:6933")
        tile_metric = tile.to_crs("EPSG:6933")
        clipped = gpd.overlay(metric, tile_metric, how="intersection")
        covered = clipped[[pcode_col]].copy()
        covered["flood_tile_covered_km2"] = clipped.area / 1_000_000
        covered = covered.groupby(pcode_col, as_index=False)["flood_tile_covered_km2"].sum()
        table = admin[[name_col, pcode_col] + ([f"adm{level-1}_name"] if level == 2 else [])].copy()
        table["admin_level"] = level
        table["area_km2"] = metric.area.values / 1_000_000
        table = table.merge(covered, on=pcode_col, how="left").fillna({"flood_tile_covered_km2": 0})
        table["flood_tile_coverage_share"] = table["flood_tile_covered_km2"] / table["area_km2"]
        table = table.rename(columns={name_col: "admin_name", pcode_col: "admin_pcode"})
        rows.append(table)

    result = pd.concat(rows, ignore_index=True)
    result.to_csv(out, index=False)
    return result


def build_flood_pixel_admin_lookup(force: bool = False) -> pd.DataFrame:
    out = CACHE_DIR / "flood_pixel_admin2_lookup.parquet"
    if out.exists() and not force:
        return pd.read_parquet(out)

    admin2 = read_admin(2)[["adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode", "geometry"]]
    admin2 = admin2.to_crs("EPSG:4326")
    minx, miny, maxx, maxy = admin2.total_bounds
    minx = max(minx, FLOOD_TILE_EXTENT["lon_min"])
    maxx = min(maxx, FLOOD_TILE_EXTENT["lon_max"])
    miny = max(miny, FLOOD_TILE_EXTENT["lat_min"])
    maxy = min(maxy, FLOOD_TILE_EXTENT["lat_max"])

    unique_parts = []
    for path in sorted(FLOOD_DIR.glob("compact_*/*.parquet")):
        df = pd.read_parquet(path, columns=["lat", "lon"])
        df["lat"] = pd.to_numeric(df["lat"]).round(6)
        df["lon"] = pd.to_numeric(df["lon"]).round(6)
        df = df[(df["lat"] >= miny) & (df["lat"] <= maxy) & (df["lon"] >= minx) & (df["lon"] <= maxx)]
        unique_parts.append(df.drop_duplicates())

    unique = pd.concat(unique_parts, ignore_index=True).drop_duplicates().reset_index(drop=True)
    points = gpd.GeoDataFrame(
        unique,
        geometry=gpd.points_from_xy(unique["lon"], unique["lat"]),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(
        points,
        admin2,
        how="inner",
        predicate="within",
    )
    lookup = pd.DataFrame(joined.drop(columns=["geometry", "index_right"]))
    lookup = lookup[["lat", "lon", "adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode"]]
    lookup.to_parquet(out, index=False)
    lookup.to_csv(OUT_DIR / "flood_pixel_admin2_lookup_preview.csv", index=False)
    return lookup


def build_flood_admin2_daily(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "flood_admin2_daily.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"])

    lookup = build_flood_pixel_admin_lookup(force=force)
    lookup = lookup[["lat", "lon", "adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode"]]
    pieces = []
    for path in sorted(FLOOD_DIR.glob("compact_*/*.parquet")):
        info = parse_flood_path(path)
        df = pd.read_parquet(path, columns=["date", "lat", "lon"])
        df["date"] = pd.to_datetime(df["date"].astype(str))
        df["lat"] = pd.to_numeric(df["lat"]).round(6)
        df["lon"] = pd.to_numeric(df["lon"]).round(6)
        df = df.merge(lookup, on=["lat", "lon"], how="inner")
        if df.empty:
            continue
        grouped = (
            df.groupby(["date", "adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode"], observed=True)
            .size()
            .reset_index(name=f"{info['flood_type']}_flooded_pixel_count")
        )
        grouped["source_tile"] = info["tile"]
        grouped["source_year"] = info["year"]
        pieces.append(grouped)

    stacked = pd.concat(pieces, ignore_index=True)
    count_cols = [col for col in stacked.columns if col.endswith("_flooded_pixel_count")]
    daily = (
        stacked.groupby(["date", "adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode"], observed=True)[count_cols]
        .sum()
        .reset_index()
    )
    for col in ["recurring_flooded_pixel_count", "unusual_flooded_pixel_count"]:
        if col not in daily:
            daily[col] = 0
    daily["total_flooded_pixel_count"] = (
        daily["recurring_flooded_pixel_count"] + daily["unusual_flooded_pixel_count"]
    )
    daily["estimated_flooded_area_km2"] = daily["total_flooded_pixel_count"] * FLOOD_PIXEL_AREA_KM2
    daily = daily.sort_values(["date", "adm1_name", "adm2_name"])
    daily.to_csv(out, index=False)
    return daily


def build_grid_assignment(
    nc_path: Path,
    lat_name: str,
    lon_name: str,
    force: bool = False,
) -> pd.DataFrame:
    key = f"{nc_path.stem}_{lat_name}_{lon_name}_admin2_grid_assignment.parquet"
    out = CACHE_DIR / key
    if out.exists() and not force:
        return pd.read_parquet(out)

    admin0 = read_admin(0)[["geometry"]]
    admin2 = read_admin(2)[["adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode", "geometry"]]
    with xr.open_dataset(nc_path) as ds:
        lats = ds[lat_name].values
        lons = ds[lon_name].values

    lon_grid, lat_grid = np.meshgrid(lons, lats)
    assignment = pd.DataFrame(
        {
            "cell_index": np.arange(lon_grid.size),
            "grid_latitude": lat_grid.ravel(),
            "grid_longitude": lon_grid.ravel(),
        }
    )
    points = gpd.GeoDataFrame(
        assignment,
        geometry=gpd.points_from_xy(assignment["grid_longitude"], assignment["grid_latitude"]),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(points, admin2, how="left", predicate="within").drop(columns=["index_right"])
    ssd_joined = gpd.sjoin(
        points[["cell_index", "geometry"]],
        admin0,
        how="inner",
        predicate="within",
    ).drop(columns=["index_right"])
    joined["in_ssd_full"] = joined["cell_index"].isin(ssd_joined["cell_index"])
    joined["in_flood_tile_extent"] = (
        (joined["grid_longitude"] >= FLOOD_TILE_EXTENT["lon_min"])
        & (joined["grid_longitude"] <= FLOOD_TILE_EXTENT["lon_max"])
        & (joined["grid_latitude"] >= FLOOD_TILE_EXTENT["lat_min"])
        & (joined["grid_latitude"] <= FLOOD_TILE_EXTENT["lat_max"])
    )
    joined["in_ssd_flood_tile_overlap"] = joined["in_ssd_full"] & joined["in_flood_tile_extent"]
    for region in HYDRO_REGIONS:
        if region.region_id in {"ssd_full", "ssd_flood_tile_overlap"}:
            continue
        joined[f"in_{region.region_id}"] = (
            (joined["grid_longitude"] >= region.lon_min)
            & (joined["grid_longitude"] <= region.lon_max)
            & (joined["grid_latitude"] >= region.lat_min)
            & (joined["grid_latitude"] <= region.lat_max)
        )
    result = pd.DataFrame(joined.drop(columns=["geometry"]))
    result.to_parquet(out, index=False)
    return result


def stack_dataset(ds: xr.Dataset | xr.DataArray, lat_name: str, lon_name: str):
    return ds.stack(cell=(lat_name, lon_name))


def select_admin2_grid_cells(assignment: pd.DataFrame) -> pd.DataFrame:
    selected = assignment.dropna(subset=["adm2_pcode"]).copy()
    selected["climate_grid_assignment_method"] = "grid_center_within_admin2"
    selected["nearest_grid_distance_degrees"] = 0.0

    admin2 = read_admin(2)[["adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode", "geometry"]]
    missing = admin2[~admin2["adm2_pcode"].isin(selected["adm2_pcode"].astype(str))]
    if missing.empty:
        return selected

    fallback_rows = []
    grid = assignment[["cell_index", "grid_latitude", "grid_longitude"]].copy()
    for _, admin_row in missing.iterrows():
        point = admin_row.geometry.representative_point()
        lat_scale = np.cos(np.deg2rad(point.y))
        distance = np.sqrt(
            (grid["grid_latitude"] - point.y) ** 2
            + ((grid["grid_longitude"] - point.x) * lat_scale) ** 2
        )
        nearest = assignment.loc[distance.idxmin()].copy()
        for col in ["adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode"]:
            nearest[col] = admin_row[col]
        nearest["climate_grid_assignment_method"] = "nearest_grid_to_admin2_representative_point"
        nearest["nearest_grid_distance_degrees"] = float(distance.min())
        fallback_rows.append(nearest)

    return pd.concat([selected, pd.DataFrame(fallback_rows)], ignore_index=True)


def aggregate_era5_admin2(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "era5_admin2_daily.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"])

    sample = sorted(ERA5_DIR.glob("ERA5_*.nc"))[0]
    assignment = build_grid_assignment(sample, "latitude", "longitude", force=force)
    selected = select_admin2_grid_cells(assignment)
    idx = selected["cell_index"].to_numpy()
    codes = selected["adm2_pcode"].astype(str).to_numpy()
    meta = selected[
        [
            "adm1_name",
            "adm1_pcode",
            "adm2_name",
            "adm2_pcode",
            "climate_grid_assignment_method",
            "nearest_grid_distance_degrees",
        ]
    ].drop_duplicates()

    pieces = []
    for path in sorted(ERA5_DIR.glob("ERA5_*.nc")):
        year = int(re.search(r"ERA5_(\d{4})", path.name).group(1))
        with xr.open_dataset(path) as ds:
            stacked = stack_dataset(ds[["tp", "ro"]], "latitude", "longitude").isel(cell=idx)
            stacked = stacked.assign_coords(adm2_pcode=("cell", codes))
            grouped = stacked.groupby("adm2_pcode").mean(dim="cell", skipna=True)
            daily = grouped.resample(valid_time="1D").sum()
            df = daily.to_dataframe().reset_index()
        df = df.rename(
            columns={
                "valid_time": "date",
                "tp": "precipitation_m_day",
                "ro": "runoff_m_day",
            }
        )
        df["year"] = year
        df["precipitation_mm_day"] = df["precipitation_m_day"] * 1000
        df["runoff_mm_day"] = df["runoff_m_day"] * 1000
        df = df.merge(meta, on="adm2_pcode", how="left", validate="many_to_one")
        pieces.append(
            df[
                [
                    "year",
                    "date",
                    "adm1_name",
                    "adm1_pcode",
                    "adm2_name",
                    "adm2_pcode",
                    "climate_grid_assignment_method",
                    "nearest_grid_distance_degrees",
                    "precipitation_mm_day",
                    "runoff_mm_day",
                ]
            ]
        )

    result = pd.concat(pieces, ignore_index=True).sort_values(["date", "adm1_name", "adm2_name"])
    result.to_csv(out, index=False)
    return result


def aggregate_era5_regions(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "era5_hydro_regions_daily.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"])

    sample = sorted(ERA5_DIR.glob("ERA5_*.nc"))[0]
    assignment = build_grid_assignment(sample, "latitude", "longitude", force=force)
    region_cells = {}
    for region in HYDRO_REGIONS:
        if region.region_id == "ssd_full":
            mask = assignment["in_ssd_full"]
        elif region.region_id == "ssd_flood_tile_overlap":
            mask = assignment["in_ssd_flood_tile_overlap"]
        else:
            mask = assignment[f"in_{region.region_id}"]
        region_cells[region.region_id] = assignment.loc[mask, "cell_index"].to_numpy()

    pieces = []
    for path in sorted(ERA5_DIR.glob("ERA5_*.nc")):
        year = int(re.search(r"ERA5_(\d{4})", path.name).group(1))
        with xr.open_dataset(path) as ds:
            stacked = stack_dataset(ds[["tp", "ro"]], "latitude", "longitude")
            for region in HYDRO_REGIONS:
                idx = region_cells[region.region_id]
                if len(idx) == 0:
                    continue
                region_mean = stacked.isel(cell=idx).mean(dim="cell", skipna=True)
                daily = region_mean.resample(valid_time="1D").sum().to_dataframe().reset_index()
                daily = daily.rename(
                    columns={
                        "valid_time": "date",
                        "tp": "precipitation_m_day",
                        "ro": "runoff_m_day",
                    }
                )
                daily["year"] = year
                daily["region_id"] = region.region_id
                daily["region_label"] = region.label
                daily["region_cell_count"] = len(idx)
                daily["precipitation_mm_day"] = daily["precipitation_m_day"] * 1000
                daily["runoff_mm_day"] = daily["runoff_m_day"] * 1000
                pieces.append(
                    daily[
                        [
                            "year",
                            "date",
                            "region_id",
                            "region_label",
                            "region_cell_count",
                            "precipitation_mm_day",
                            "runoff_mm_day",
                        ]
                    ]
                )
    result = pd.concat(pieces, ignore_index=True).sort_values(["region_id", "date"])
    result.to_csv(out, index=False)
    return result


def aggregate_et_admin2(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "et_admin2_daily.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"])

    sample = sorted((ET_DIR / "ET_2000").glob("*.nc"))[0]
    assignment = build_grid_assignment(sample, "lat", "lon", force=force)
    selected = assignment.dropna(subset=["adm2_pcode"]).copy()
    idx = selected["cell_index"].to_numpy()
    categories = pd.Index(sorted(selected["adm2_pcode"].astype(str).unique()))
    code_map = {code: i for i, code in enumerate(categories)}
    codes = selected["adm2_pcode"].astype(str).map(code_map).to_numpy()
    meta = selected[["adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode"]].drop_duplicates()

    pieces = []
    for year_dir in sorted(ET_DIR.glob("ET_*")):
        if not year_dir.is_dir():
            continue
        year = int(year_dir.name.split("_")[1])
        year_out = CACHE_DIR / f"et_admin2_daily_{year}.csv"
        if year_out.exists() and not force:
            pieces.append(pd.read_csv(year_out, parse_dates=["date"]))
            continue
        rows = []
        for path in sorted(year_dir.glob("*.nc")):
            with xr.open_dataset(path) as ds:
                values = ds[ET_VARIABLE].squeeze().values.ravel()[idx].astype("float64")
                date = pd.Timestamp(ds["time"].values[0])
            valid = np.isfinite(values)
            sums = np.bincount(codes[valid], weights=values[valid], minlength=len(categories))
            counts = np.bincount(codes[valid], minlength=len(categories))
            means = np.divide(
                sums,
                counts,
                out=np.full(len(categories), np.nan, dtype="float64"),
                where=counts > 0,
            )
            rows.append(
                pd.DataFrame(
                    {
                        "date": date,
                        "adm2_pcode": categories,
                        "reference_et_mm_day": means,
                    }
                )
            )
        year_df = pd.concat(rows, ignore_index=True)
        year_df["year"] = year_df["date"].dt.year
        year_df = year_df.merge(meta, on="adm2_pcode", how="left", validate="many_to_one")
        year_df = year_df[
            [
                "year",
                "date",
                "adm1_name",
                "adm1_pcode",
                "adm2_name",
                "adm2_pcode",
                "reference_et_mm_day",
            ]
        ]
        year_df.to_csv(year_out, index=False)
        pieces.append(year_df)

    result = pd.concat(pieces, ignore_index=True).sort_values(["date", "adm1_name", "adm2_name"])
    result.to_csv(out, index=False)
    return result


def aggregate_et_regions(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "et_hydro_regions_daily.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"])

    sample = sorted((ET_DIR / "ET_2000").glob("*.nc"))[0]
    assignment = build_grid_assignment(sample, "lat", "lon", force=force)
    region_cells = {}
    for region in HYDRO_REGIONS:
        if region.region_id == "ssd_full":
            mask = assignment["in_ssd_full"]
        elif region.region_id == "ssd_flood_tile_overlap":
            mask = assignment["in_ssd_flood_tile_overlap"]
        else:
            mask = assignment[f"in_{region.region_id}"]
        region_cells[region.region_id] = assignment.loc[mask, "cell_index"].to_numpy()

    rows = []
    for year_dir in sorted(ET_DIR.glob("ET_*")):
        if not year_dir.is_dir():
            continue
        year = int(year_dir.name.split("_")[1])
        year_out = CACHE_DIR / f"et_hydro_regions_daily_{year}.csv"
        if year_out.exists() and not force:
            rows.append(pd.read_csv(year_out, parse_dates=["date"]))
            continue
        year_rows = []
        for path in sorted(year_dir.glob("*.nc")):
            with xr.open_dataset(path) as ds:
                values = ds[ET_VARIABLE].squeeze().values.ravel().astype("float64")
                date = pd.Timestamp(ds["time"].values[0])
                for region in HYDRO_REGIONS:
                    idx = region_cells[region.region_id]
                    if len(idx) == 0:
                        continue
                    region_values = values[idx]
                    value = float(np.nanmean(region_values))
                    year_rows.append(
                        {
                            "year": date.year,
                            "date": date,
                            "region_id": region.region_id,
                            "region_label": region.label,
                            "region_cell_count": len(idx),
                            "reference_et_mm_day": value,
                        }
                    )

        year_df = pd.DataFrame(year_rows)
        year_df.to_csv(year_out, index=False)
        rows.append(year_df)

    result = pd.concat(rows, ignore_index=True).sort_values(["region_id", "date"])
    result.to_csv(out, index=False)
    return result


def build_admin2_panel(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "admin2_daily_flood_climate_panel.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"])

    admin2 = read_admin(2)[["adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode", "area_sqkm"]]
    full_index = pd.MultiIndex.from_product(
        [date_range(), admin2["adm2_pcode"]],
        names=["date", "adm2_pcode"],
    ).to_frame(index=False)
    panel = full_index.merge(admin2, on="adm2_pcode", how="left", validate="many_to_one")

    flood = build_flood_admin2_daily(force=force)
    climate = aggregate_era5_admin2(force=force)
    et = aggregate_et_admin2(force=force)
    coverage = build_flood_coverage_summary(force=force)
    coverage2 = coverage[coverage["admin_level"] == 2][
        ["admin_pcode", "flood_tile_covered_km2", "flood_tile_coverage_share"]
    ].rename(columns={"admin_pcode": "adm2_pcode"})

    panel = panel.merge(
        flood[
            [
                "date",
                "adm2_pcode",
                "recurring_flooded_pixel_count",
                "unusual_flooded_pixel_count",
                "total_flooded_pixel_count",
                "estimated_flooded_area_km2",
            ]
        ],
        on=["date", "adm2_pcode"],
        how="left",
    )
    flood_cols = [
        "recurring_flooded_pixel_count",
        "unusual_flooded_pixel_count",
        "total_flooded_pixel_count",
        "estimated_flooded_area_km2",
    ]
    panel[flood_cols] = panel[flood_cols].fillna(0)
    panel = panel.merge(
        climate[
            [
                "date",
                "adm2_pcode",
                "precipitation_mm_day",
                "runoff_mm_day",
                "climate_grid_assignment_method",
                "nearest_grid_distance_degrees",
            ]
        ],
        on=["date", "adm2_pcode"],
        how="left",
    )
    panel = panel.merge(
        et[["date", "adm2_pcode", "reference_et_mm_day"]],
        on=["date", "adm2_pcode"],
        how="left",
    )
    panel = panel.merge(coverage2, on="adm2_pcode", how="left")
    panel["flood_area_share_of_admin2"] = panel["estimated_flooded_area_km2"] / panel["area_sqkm"]
    panel.to_csv(out, index=False)
    return panel


def build_region_daily_panel(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "hydro_region_daily_panel.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"])

    era5 = aggregate_era5_regions(force=force)
    et = aggregate_et_regions(force=force)
    panel = era5.merge(
        et[["date", "region_id", "reference_et_mm_day"]],
        on=["date", "region_id"],
        how="left",
    )
    panel.to_csv(out, index=False)
    return panel


def classify_discharge_stations(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "discharge_station_relevance.csv"
    if out.exists() and not force:
        return pd.read_csv(out)

    df = pd.read_csv(DISCHARGE_PATH, parse_dates=["Date"])
    rows = []
    for area_id, group in df.groupby("area_id"):
        if area_id in RELEVANT_DISCHARGE:
            status = RELEVANT_DISCHARGE[area_id]
            use_in_main = status == "primary_white_nile_near_south_sudan"
        else:
            status = EXCLUDED_DISCHARGE.get(area_id, "not classified")
            use_in_main = False
        rows.append(
            {
                "area_id": area_id,
                "station_nr": group["station_nr"].iloc[0],
                "country": group["country"].iloc[0],
                "latitude": group["latitude"].iloc[0],
                "longitude": group["longitude"].iloc[0],
                "date_min": group["Date"].min().date(),
                "date_max": group["Date"].max().date(),
                "record_count": len(group),
                "hydrological_relevance": status,
                "use_in_main_eda": use_in_main,
            }
        )
    result = pd.DataFrame(rows).sort_values(["use_in_main_eda", "area_id"], ascending=[False, True])
    result.to_csv(out, index=False)
    return result


def build_discharge_daily(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "relevant_discharge_daily.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"])

    relevance = classify_discharge_stations(force=force)
    keep = relevance[relevance["hydrological_relevance"].isin(RELEVANT_DISCHARGE.values())]["area_id"]
    df = pd.read_csv(DISCHARGE_PATH, parse_dates=["Date"])
    df = df[df["area_id"].isin(keep)].copy()
    df = df.rename(columns={"Date": "date", "Discharge (m3/s)": "discharge_m3_s"})
    df = df.merge(relevance[["area_id", "hydrological_relevance", "use_in_main_eda"]], on="area_id", how="left")
    df = df[
        [
            "date",
            "area_id",
            "station_nr",
            "country",
            "latitude",
            "longitude",
            "hydrological_relevance",
            "use_in_main_eda",
            "discharge_m3_s",
        ]
    ].sort_values(["area_id", "date"])
    df.to_csv(out, index=False)
    return df


def build_lake_daily(force: bool = False) -> pd.DataFrame:
    out = OUT_DIR / "upstream_lake_water_levels_daily.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"])

    water = pd.read_csv(WATER_LEVEL_PATH, parse_dates=["date"])
    order = {"Victoria": 1, "Kyoga": 2, "Albert": 3}
    notes = {
        "Victoria": "Most upstream lake in this dataset; outflow is regulated by the Nalubaale/Owen Falls dam system.",
        "Kyoga": "Downstream of Victoria, upstream of Albert.",
        "Albert": "Downstream of Kyoga/Victoria and closest upstream lake to South Sudan White Nile inflow.",
    }
    water["upstream_order_to_south_sudan"] = water["lake"].map(order)
    water["hydrological_role"] = water["lake"].map(notes)
    daily = (
        water.groupby(
            [
                "lake",
                "country",
                "target_latitude",
                "target_longitude",
                "date",
                "upstream_order_to_south_sudan",
                "hydrological_role",
            ],
            as_index=False,
        )
        .agg(
            water_level_m=("water_level_m", "mean"),
            water_level_error_m=("water_level_error_m", "mean"),
        )
        .sort_values(["upstream_order_to_south_sudan", "date"])
    )
    daily.to_csv(out, index=False)
    return daily


def lag_correlation(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
    max_lag_days: int,
    group_col: str | None = None,
) -> pd.DataFrame:
    rows = []
    groups = [(None, df)] if group_col is None else list(df.groupby(group_col))
    for group, part in groups:
        part = part.sort_values("date").copy()
        for feature in feature_cols:
            for lag in range(max_lag_days + 1):
                aligned = part[[target_col, feature]].copy()
                aligned[feature] = aligned[feature].shift(lag)
                aligned = aligned.dropna()
                if len(aligned) < 30 or aligned[target_col].std() == 0 or aligned[feature].std() == 0:
                    corr = np.nan
                else:
                    corr = aligned[target_col].corr(aligned[feature])
                row = {"feature": feature, "lag_days": lag, "correlation": corr, "n": len(aligned)}
                if group_col:
                    row[group_col] = group
                rows.append(row)
    return pd.DataFrame(rows)


def save_scope_tables(force: bool = False) -> None:
    build_flood_coverage_summary(force=force)
    classify_discharge_stations(force=force)
    regions = pd.DataFrame([region.__dict__ for region in HYDRO_REGIONS])
    regions.to_csv(OUT_DIR / "hydro_climate_region_definitions.csv", index=False)


def plot_flood_scope(panel: pd.DataFrame, coverage: pd.DataFrame) -> None:
    admin1_cov = coverage[coverage["admin_level"] == 1].sort_values("flood_tile_coverage_share")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.barh(admin1_cov["admin_name"], admin1_cov["flood_tile_coverage_share"], color="#4a7ba7")
    ax.set_xlim(0, 1.05)
    ax.set_title("Flood Mask Coverage Share by Admin1")
    ax.set_xlabel("Share of admin1 area covered by local flood tiles")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_flood_tile_coverage_by_admin1.png", dpi=180)
    plt.close(fig)

    annual = panel.groupby(panel["date"].dt.year)[
        ["recurring_flooded_pixel_count", "unusual_flooded_pixel_count", "total_flooded_pixel_count"]
    ].sum()
    annual.to_csv(OUT_DIR / "annual_admin2_clipped_flood_summary.csv")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(annual.index, annual["recurring_flooded_pixel_count"], label="recurring", color="#2f6f9f")
    ax.bar(
        annual.index,
        annual["unusual_flooded_pixel_count"],
        bottom=annual["recurring_flooded_pixel_count"],
        label="unusual",
        color="#c75b39",
    )
    ax.set_title("Annual Flood Pixel Counts Inside South Sudan Admin2 and Local Flood Tiles")
    ax.set_xlabel("Year")
    ax.set_ylabel("Flooded pixel-day count")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "02_annual_flood_admin2_clipped.png", dpi=180)
    plt.close(fig)

    monthly = panel.groupby(panel["date"].dt.month)[
        ["recurring_flooded_pixel_count", "unusual_flooded_pixel_count", "total_flooded_pixel_count"]
    ].mean()
    monthly.to_csv(OUT_DIR / "monthly_admin2_clipped_flood_summary.csv")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(monthly.index, monthly["total_flooded_pixel_count"], color="#2f2f2f", marker="o", label="total")
    ax.plot(monthly.index, monthly["unusual_flooded_pixel_count"], color="#c75b39", marker="o", label="unusual")
    ax.plot(monthly.index, monthly["recurring_flooded_pixel_count"], color="#2f6f9f", marker="o", label="recurring")
    ax.set_title("Mean Daily Admin2 Flood Pixel Count by Month")
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean flooded pixel count per admin2-day")
    ax.set_xticks(range(1, 13))
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_monthly_flood_admin2_clipped.png", dpi=180)
    plt.close(fig)

    county = (
        panel.groupby(["adm1_name", "adm2_name"], as_index=False)["total_flooded_pixel_count"]
        .sum()
        .sort_values("total_flooded_pixel_count", ascending=False)
        .head(25)
    )
    county.to_csv(OUT_DIR / "top_25_flooded_admin2.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 7))
    labels = county["adm2_name"] + " (" + county["adm1_name"] + ")"
    ax.barh(labels[::-1], county["total_flooded_pixel_count"][::-1], color="#557f5f")
    ax.set_title("Top 25 Admin2 Areas by Flood Pixel-Day Count")
    ax.set_xlabel("Flooded pixel-day count")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "04_top_flooded_admin2.png", dpi=180)
    plt.close(fig)


def plot_climate_and_lags(panel: pd.DataFrame, region_panel: pd.DataFrame) -> None:
    national = (
        panel.groupby("date", as_index=False)
        .agg(
            total_flooded_pixel_count=("total_flooded_pixel_count", "sum"),
            precipitation_mm_day=("precipitation_mm_day", "mean"),
            runoff_mm_day=("runoff_mm_day", "mean"),
            reference_et_mm_day=("reference_et_mm_day", "mean"),
        )
        .sort_values("date")
    )
    for window in [7, 14, 30, 60, 90]:
        national[f"precipitation_{window}d_sum_mm"] = national["precipitation_mm_day"].rolling(window, min_periods=1).sum()
        national[f"runoff_{window}d_sum_mm"] = national["runoff_mm_day"].rolling(window, min_periods=1).sum()
        national[f"et_{window}d_mean_mm_day"] = national["reference_et_mm_day"].rolling(window, min_periods=1).mean()
    national.to_csv(OUT_DIR / "national_daily_flood_climate_admin2_mean.csv", index=False)

    plot_df = national[
        [
            "date",
            "total_flooded_pixel_count",
            "precipitation_30d_sum_mm",
            "runoff_30d_sum_mm",
            "et_30d_mean_mm_day",
        ]
    ].copy()
    for col in plot_df.columns:
        if col != "date":
            plot_df[f"{col}_z"] = zscore(plot_df[col])

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(plot_df["date"], plot_df["total_flooded_pixel_count_z"].rolling(14, min_periods=1).mean(), color="#2f2f2f", label="flood, 14d smooth")
    ax.plot(plot_df["date"], plot_df["precipitation_30d_sum_mm_z"], color="#2f6f9f", alpha=0.85, label="admin2 rainfall, 30d")
    ax.plot(plot_df["date"], plot_df["runoff_30d_sum_mm_z"], color="#3b8f55", alpha=0.85, label="admin2 runoff, 30d")
    ax.plot(plot_df["date"], plot_df["et_30d_mean_mm_day_z"], color="#b7832f", alpha=0.75, label="admin2 ET, 30d mean")
    ax.set_title("Flood Counts vs South Sudan Admin2-Averaged Climate")
    ax.set_xlabel("Date")
    ax.set_ylabel("Standardized value")
    ax.legend(frameon=False, ncols=2)
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "05_flood_vs_admin2_climate_timeseries.png", dpi=180)
    plt.close(fig)

    feature_cols = [
        "precipitation_mm_day",
        "precipitation_7d_sum_mm",
        "precipitation_14d_sum_mm",
        "precipitation_30d_sum_mm",
        "precipitation_60d_sum_mm",
        "precipitation_90d_sum_mm",
        "runoff_mm_day",
        "runoff_7d_sum_mm",
        "runoff_14d_sum_mm",
        "runoff_30d_sum_mm",
        "runoff_60d_sum_mm",
        "runoff_90d_sum_mm",
        "reference_et_mm_day",
        "et_30d_mean_mm_day",
        "et_60d_mean_mm_day",
        "et_90d_mean_mm_day",
    ]
    corr = lag_correlation(national, "total_flooded_pixel_count", feature_cols, max_lag_days=150)
    corr.to_csv(OUT_DIR / "admin2_mean_climate_lag_correlation.csv", index=False)
    best = (
        corr.assign(abs_correlation=lambda d: d["correlation"].abs())
        .sort_values("abs_correlation", ascending=False)
        .groupby("feature")
        .head(1)
        .drop(columns="abs_correlation")
        .sort_values("correlation", ascending=False)
    )
    best.to_csv(OUT_DIR / "best_admin2_mean_climate_lags.csv", index=False)

    fig, ax = plt.subplots(figsize=(11, 6))
    selected = ["precipitation_30d_sum_mm", "runoff_30d_sum_mm", "runoff_90d_sum_mm", "et_60d_mean_mm_day"]
    colors = ["#2f6f9f", "#3b8f55", "#8abf69", "#b7832f"]
    for feature, color in zip(selected, colors):
        part = corr[corr["feature"] == feature]
        ax.plot(part["lag_days"], part["correlation"], label=feature, color=color)
    ax.axhline(0, color="#444444", linewidth=0.8)
    ax.set_title("Lag Correlation: Admin2-Averaged Climate vs Flood Counts")
    ax.set_xlabel("Lag days, climate before flood")
    ax.set_ylabel("Pearson correlation")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "06_admin2_climate_lag_correlation.png", dpi=180)
    plt.close(fig)

    regional = region_panel.pivot_table(
        index="date",
        columns="region_id",
        values=["precipitation_mm_day", "runoff_mm_day", "reference_et_mm_day"],
    )
    regional.columns = [f"{metric}__{region}" for metric, region in regional.columns]
    regional = regional.reset_index().merge(national[["date", "total_flooded_pixel_count"]], on="date", how="left")
    for col in [c for c in regional.columns if c != "date"]:
        if col != "total_flooded_pixel_count":
            if "precipitation" in col or "runoff" in col:
                regional[f"{col}__30d_sum"] = regional[col].rolling(30, min_periods=1).sum()
            if "reference_et" in col:
                regional[f"{col}__30d_mean"] = regional[col].rolling(30, min_periods=1).mean()
    region_features = [c for c in regional.columns if c.endswith("__30d_sum") or c.endswith("__30d_mean")]
    region_corr = lag_correlation(regional, "total_flooded_pixel_count", region_features, max_lag_days=150)
    region_corr.to_csv(OUT_DIR / "hydro_region_climate_lag_correlation.csv", index=False)
    region_best = (
        region_corr.assign(abs_correlation=lambda d: d["correlation"].abs())
        .sort_values("abs_correlation", ascending=False)
        .head(40)
    )
    region_best.to_csv(OUT_DIR / "top_hydro_region_climate_lag_correlations.csv", index=False)


def plot_discharge_and_lakes(panel: pd.DataFrame) -> None:
    national = panel.groupby("date", as_index=False)["total_flooded_pixel_count"].sum()
    discharge = build_discharge_daily()
    primary = discharge[discharge["area_id"] == 100205].copy()
    primary = primary.merge(national, on="date", how="inner").sort_values("date")
    for window in [7, 30, 60]:
        primary[f"discharge_{window}d_mean_m3_s"] = primary["discharge_m3_s"].rolling(window, min_periods=1).mean()
    primary.to_csv(OUT_DIR / "primary_white_nile_discharge_with_flood.csv", index=False)
    plot_primary_discharge_monthly_hydrograph(primary)
    plot_primary_discharge_monthly_vs_flood(primary)

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(primary["date"], zscore(primary["total_flooded_pixel_count"].rolling(14, min_periods=1).mean()), color="#2f2f2f", label="flood, 14d smooth")
    ax.plot(primary["date"], zscore(primary["discharge_30d_mean_m3_s"]), color="#2f6f9f", label="100205 discharge, 30d mean")
    ax.set_title("Primary White Nile Station 100205 vs Admin2-Clipped Flood Counts")
    ax.set_xlabel("Date")
    ax.set_ylabel("Standardized value")
    ax.legend(frameon=False)
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "07_primary_discharge_vs_flood.png", dpi=180)
    plt.close(fig)

    corr = lag_correlation(
        primary,
        "total_flooded_pixel_count",
        ["discharge_m3_s", "discharge_7d_mean_m3_s", "discharge_30d_mean_m3_s", "discharge_60d_mean_m3_s"],
        max_lag_days=180,
    )
    corr.to_csv(OUT_DIR / "primary_discharge_lag_correlation.csv", index=False)

    lakes = build_lake_daily()
    lake_daily_parts = []
    full_dates = pd.date_range(national["date"].min(), national["date"].max(), freq="D")
    lake_static_cols = [
        "country",
        "target_latitude",
        "target_longitude",
        "upstream_order_to_south_sudan",
        "hydrological_role",
    ]
    for lake, group in lakes.groupby("lake"):
        group = group.sort_values("date").copy()
        daily = pd.DataFrame({"date": full_dates})
        daily["lake"] = lake
        daily = daily.merge(group[["date", "water_level_m"] + lake_static_cols], on="date", how="left")
        daily["observed_water_level"] = daily["water_level_m"].notna()
        daily["water_level_m"] = daily["water_level_m"].interpolate(method="linear", limit_area="inside")
        for col in lake_static_cols:
            daily[col] = daily[col].ffill().bfill()
        daily["water_level_30d_mean_m"] = daily["water_level_m"].rolling(30, min_periods=1).mean()
        lake_daily_parts.append(daily)
    lake_panel = (
        pd.concat(lake_daily_parts, ignore_index=True)
        .merge(national, on="date", how="inner")
        .sort_values(["lake", "date"])
    )
    lake_panel.to_csv(OUT_DIR / "upstream_lake_levels_with_flood_overlap.csv", index=False)
    lake_corr = lag_correlation(
        lake_panel,
        "total_flooded_pixel_count",
        ["water_level_m", "water_level_30d_mean_m"],
        max_lag_days=365,
        group_col="lake",
    )
    lake_corr.to_csv(OUT_DIR / "upstream_lake_level_lag_correlation.csv", index=False)

    fig, ax = plt.subplots(figsize=(12, 5))
    for lake, color in [("Victoria", "#4b78a8"), ("Kyoga", "#2f8f73"), ("Albert", "#a86f2f")]:
        part = lake_panel[lake_panel["lake"] == lake]
        if part.empty:
            continue
        ax.plot(part["date"], zscore(part["water_level_m"]), label=f"{lake} water level", color=color, alpha=0.85)
    ax.plot(national["date"], zscore(national["total_flooded_pixel_count"].rolling(30, min_periods=1).mean()), label="flood, 30d smooth", color="#2f2f2f", linewidth=1.8)
    ax.set_title("Upstream Lake Water Levels and Flood Counts")
    ax.set_xlabel("Date")
    ax.set_ylabel("Standardized value")
    ax.legend(frameon=False)
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "08_upstream_lake_levels_vs_flood.png", dpi=180)
    plt.close(fig)
    plot_albert_lake_monthly_vs_flood(lake_panel)


def plot_albert_lake_monthly_vs_flood(lake_panel: pd.DataFrame) -> None:
    albert = lake_panel[lake_panel["lake"] == "Albert"].dropna(subset=["water_level_m"]).copy()
    albert["year_month"] = albert["date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        albert.groupby("year_month", as_index=False)
        .agg(
            water_level_mean_m=("water_level_m", "mean"),
            water_level_observed_days=("observed_water_level", "sum"),
            flood_pixel_count=("total_flooded_pixel_count", "sum"),
        )
        .sort_values("year_month")
    )
    monthly.to_csv(OUT_DIR / "albert_lake_monthly_water_level_vs_flood.csv", index=False)

    fig, ax1 = plt.subplots(figsize=(13, 5.8))
    ax1.plot(
        monthly["year_month"],
        monthly["water_level_mean_m"],
        color="#1f77b4",
        linewidth=1.8,
        label="Albert monthly mean water level",
    )
    ax1.set_xlabel("Date (monthly)")
    ax1.set_ylabel("Mean water level (m)", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax1.grid(alpha=0.22)

    ax2 = ax1.twinx()
    ax2.bar(
        monthly["year_month"],
        monthly["flood_pixel_count"],
        width=24,
        color="#2f2f2f",
        alpha=0.28,
        label="Monthly flood pixel count",
    )
    ax2.set_ylabel("Monthly flood pixel count", color="#2f2f2f")
    ax2.tick_params(axis="y", labelcolor="#2f2f2f")

    lines, labels = ax1.get_legend_handles_labels()
    bars, bar_labels = ax2.get_legend_handles_labels()
    ax1.legend(lines + bars, labels + bar_labels, frameon=False, loc="upper left")
    ax1.set_title("Lake Albert Monthly Mean Water Level vs Flood Pixel Counts")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "12_albert_lake_monthly_water_level_vs_flood.png", dpi=180)
    plt.close(fig)
    plot_albert_lake_flood_monthly_relationship(monthly)


def plot_albert_lake_flood_monthly_relationship(monthly: pd.DataFrame) -> None:
    monthly = monthly.sort_values("year_month").copy()
    monthly["year"] = monthly["year_month"].dt.year
    complete_years = monthly.groupby("year")["year_month"].nunique()
    years = sorted(complete_years[complete_years == 12].index)[-10:]
    recent = monthly[monthly["year"].isin(years)].copy()
    recent.to_csv(OUT_DIR / "albert_lake_monthly_water_level_flood_recent_10_years.csv", index=False)
    colors_by_year = {
        year: color
        for year, color in zip(
            years,
            [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
                "#8c564b",
                "#e377c2",
                "#7f7f7f",
                "#bcbd22",
                "#17becf",
            ],
        )
    }

    corr_rows = []
    for lag in range(13):
        aligned = recent[["year_month", "water_level_mean_m", "flood_pixel_count"]].copy()
        aligned["water_level_lagged_m"] = aligned["water_level_mean_m"].shift(lag)
        aligned = aligned.dropna()
        corr = aligned["flood_pixel_count"].corr(aligned["water_level_lagged_m"])
        corr_rows.append({"lag_months": lag, "correlation": corr, "n_months": len(aligned)})
    corr_df = pd.DataFrame(corr_rows)
    corr_df.to_csv(OUT_DIR / "albert_lake_monthly_water_level_flood_lag_correlation.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4))
    ax = axes[0]
    for year, group in recent.groupby("year"):
        ax.scatter(
            group["water_level_mean_m"],
            group["flood_pixel_count"],
            color=colors_by_year[year],
            s=34,
            alpha=0.82,
            edgecolor="white",
            linewidth=0.3,
            label=str(year),
        )
    valid = recent[["water_level_mean_m", "flood_pixel_count"]].dropna()
    if len(valid) >= 2:
        slope, intercept = np.polyfit(valid["water_level_mean_m"], valid["flood_pixel_count"], 1)
        xs = np.linspace(valid["water_level_mean_m"].min(), valid["water_level_mean_m"].max(), 100)
        ax.plot(xs, slope * xs + intercept, color="#2f2f2f", linewidth=1.8, label="linear fit")
    ax.set_title("Monthly Flood Count vs Albert Water Level, Recent 10 Complete Years")
    ax.set_xlabel("Albert monthly mean water level (m)")
    ax.set_ylabel("Monthly flood pixel count")
    ax.grid(alpha=0.22)
    ax.legend(title="Year", frameon=False, loc="upper left", ncols=2, fontsize=8)

    ax = axes[1]
    colors = ["#c0392b" if value < 0 else "#2f6f9f" for value in corr_df["correlation"]]
    ax.bar(corr_df["lag_months"], corr_df["correlation"], color=colors, alpha=0.82)
    ax.axhline(0, color="#2f2f2f", linewidth=0.9)
    ax.set_title("Lag Correlation: Flood vs Earlier Albert Water Level")
    ax.set_xlabel("Albert water level lag before flood (months)")
    ax.set_ylabel("Correlation")
    ax.set_xticks(range(13))
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "13_albert_lake_flood_monthly_relationship.png", dpi=180)
    plt.close(fig)


def plot_primary_discharge_monthly_vs_flood(primary: pd.DataFrame) -> None:
    monthly = primary.copy()
    monthly["year_month"] = monthly["date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        monthly.groupby("year_month", as_index=False)
        .agg(
            discharge_mean_m3_s=("discharge_m3_s", "mean"),
            flood_pixel_count=("total_flooded_pixel_count", "sum"),
            observation_days=("discharge_m3_s", "size"),
        )
        .sort_values("year_month")
    )
    monthly.to_csv(OUT_DIR / "primary_white_nile_100205_monthly_discharge_vs_flood.csv", index=False)

    fig, ax1 = plt.subplots(figsize=(13, 5.8))
    ax1.plot(
        monthly["year_month"],
        monthly["discharge_mean_m3_s"],
        color="#1f77b4",
        linewidth=1.7,
        label="100205 monthly mean discharge",
    )
    ax1.set_xlabel("Date (monthly)")
    ax1.set_ylabel("Mean discharge (m3/s)", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax1.grid(alpha=0.22)

    ax2 = ax1.twinx()
    ax2.bar(
        monthly["year_month"],
        monthly["flood_pixel_count"],
        width=24,
        color="#2f2f2f",
        alpha=0.28,
        label="Monthly flood pixel count",
    )
    ax2.set_ylabel("Monthly flood pixel count", color="#2f2f2f")
    ax2.tick_params(axis="y", labelcolor="#2f2f2f")

    lines, labels = ax1.get_legend_handles_labels()
    bars, bar_labels = ax2.get_legend_handles_labels()
    ax1.legend(lines + bars, labels + bar_labels, frameon=False, loc="upper left")
    ax1.set_title("Station 100205 Monthly Mean Discharge vs Flood Pixel Counts")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "10_primary_discharge_monthly_vs_flood.png", dpi=180)
    plt.close(fig)
    plot_primary_discharge_flood_monthly_relationship(monthly)


def plot_primary_discharge_flood_monthly_relationship(monthly: pd.DataFrame) -> None:
    monthly = monthly.sort_values("year_month").copy()
    monthly["year"] = monthly["year_month"].dt.year
    complete_years = monthly.groupby("year")["year_month"].nunique()
    years = sorted(complete_years[complete_years == 12].index)[-10:]
    recent = monthly[monthly["year"].isin(years)].copy()
    recent.to_csv(OUT_DIR / "primary_white_nile_100205_monthly_discharge_flood_recent_10_years.csv", index=False)
    colors_by_year = {
        year: color
        for year, color in zip(
            years,
            [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
                "#8c564b",
                "#e377c2",
                "#7f7f7f",
                "#bcbd22",
                "#17becf",
            ],
        )
    }
    corr_rows = []
    for lag in range(13):
        aligned = recent[["year_month", "discharge_mean_m3_s", "flood_pixel_count"]].copy()
        aligned["discharge_lagged_m3_s"] = aligned["discharge_mean_m3_s"].shift(lag)
        aligned = aligned.dropna()
        corr = aligned["flood_pixel_count"].corr(aligned["discharge_lagged_m3_s"])
        corr_rows.append({"lag_months": lag, "correlation": corr, "n_months": len(aligned)})
    corr_df = pd.DataFrame(corr_rows)
    corr_df.to_csv(OUT_DIR / "primary_white_nile_100205_monthly_discharge_flood_lag_correlation.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4))
    ax = axes[0]
    for year, group in recent.groupby("year"):
        ax.scatter(
            group["discharge_mean_m3_s"],
            group["flood_pixel_count"],
            color=colors_by_year[year],
            s=34,
            alpha=0.82,
            edgecolor="white",
            linewidth=0.3,
            label=str(year),
        )
    valid = recent[["discharge_mean_m3_s", "flood_pixel_count"]].dropna()
    if len(valid) >= 2:
        slope, intercept = np.polyfit(valid["discharge_mean_m3_s"], valid["flood_pixel_count"], 1)
        xs = np.linspace(valid["discharge_mean_m3_s"].min(), valid["discharge_mean_m3_s"].max(), 100)
        ax.plot(xs, slope * xs + intercept, color="#2f2f2f", linewidth=1.8, label="linear fit")
    ax.set_title("Monthly Flood Count vs 100205 Discharge, Recent 10 Complete Years")
    ax.set_xlabel("Monthly mean discharge (m3/s)")
    ax.set_ylabel("Monthly flood pixel count")
    ax.grid(alpha=0.22)
    ax.legend(title="Year", frameon=False, loc="upper right", ncols=2, fontsize=8)

    ax = axes[1]
    colors = ["#c0392b" if value < 0 else "#2f6f9f" for value in corr_df["correlation"]]
    ax.bar(corr_df["lag_months"], corr_df["correlation"], color=colors, alpha=0.82)
    ax.axhline(0, color="#2f2f2f", linewidth=0.9)
    ax.set_title("Lag Correlation: Flood vs Earlier Discharge")
    ax.set_xlabel("Discharge lag before flood (months)")
    ax.set_ylabel("Correlation")
    ax.set_xticks(range(13))
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "11_primary_discharge_flood_monthly_relationship.png", dpi=180)
    plt.close(fig)


def plot_station_discharge_monthly_hydrograph(
    station_daily: pd.DataFrame,
    area_id: int,
    output_stem: str,
    title: str,
) -> None:
    monthly = station_daily.copy()
    monthly["year"] = monthly["date"].dt.year
    monthly["month"] = monthly["date"].dt.month
    monthly = (
        monthly.groupby(["year", "month"], as_index=False)
        .agg(
            discharge_mean_m3_s=("discharge_m3_s", "mean"),
            discharge_median_m3_s=("discharge_m3_s", "median"),
            observation_days=("discharge_m3_s", "size"),
        )
        .sort_values(["year", "month"])
    )
    monthly.to_csv(OUT_DIR / f"{output_stem}_monthly_discharge_by_year.csv", index=False)

    complete_years = monthly.groupby("year")["month"].nunique()
    years = sorted(complete_years[complete_years == 12].index)[-10:]
    recent = monthly[monthly["year"].isin(years)].copy()
    recent.to_csv(OUT_DIR / f"{output_stem}_monthly_discharge_recent_10_years.csv", index=False)
    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]
    color_by_year = dict(zip(years, colors))

    fig, ax = plt.subplots(figsize=(13, 6))
    for year, group in recent.groupby("year"):
        ax.plot(
            group["month"],
            group["discharge_mean_m3_s"],
            color=color_by_year[year],
            linewidth=1.8,
            alpha=0.95,
            marker="o",
            markersize=3.5,
            label=str(year),
        )
        if not group.empty:
            last = group.sort_values("month").iloc[-1]
            ax.text(
                last["month"] + 0.1,
                last["discharge_mean_m3_s"],
                str(year),
                color=color_by_year[year],
                fontsize=8.5,
                va="center",
            )
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean discharge (m3/s)")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_xlim(1, 13.05)
    ax.grid(alpha=0.22)
    ax.legend(title="Year", frameon=False, ncols=1, loc="center left", bbox_to_anchor=(1.01, 0.5))
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{area_id}_monthly_discharge_hydrograph_recent_10_years.png", dpi=180)
    plt.close(fig)


def plot_primary_discharge_monthly_hydrograph(primary: pd.DataFrame) -> None:
    plot_station_discharge_monthly_hydrograph(
        primary,
        area_id=100205,
        output_stem="primary_white_nile_100205",
        title="Station 100205 Monthly Mean Discharge by Year, Recent 10 Years",
    )
    source = FIG_DIR / "100205_monthly_discharge_hydrograph_recent_10_years.png"
    legacy = FIG_DIR / "09_primary_discharge_monthly_hydrograph_by_year.png"
    if source.exists():
        legacy.write_bytes(source.read_bytes())


def simple_markdown_table(df: pd.DataFrame) -> str:
    display = df.copy()
    for col in display.columns:
        if pd.api.types.is_float_dtype(display[col]):
            display[col] = display[col].map(lambda value: "" if pd.isna(value) else f"{value:.4g}")
        else:
            display[col] = display[col].astype(str)
    headers = [str(col) for col in display.columns]
    rows = display.values.tolist()
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def write_report(panel: pd.DataFrame, region_panel: pd.DataFrame) -> None:
    annual = pd.read_csv(OUT_DIR / "annual_admin2_clipped_flood_summary.csv")
    coverage = pd.read_csv(OUT_DIR / "flood_admin_coverage_summary.csv")
    station_relevance = pd.read_csv(OUT_DIR / "discharge_station_relevance.csv")
    best_climate = pd.read_csv(OUT_DIR / "best_admin2_mean_climate_lags.csv")
    top_region = pd.read_csv(OUT_DIR / "top_hydro_region_climate_lag_correlations.csv")

    admin1_coverage = coverage[coverage["admin_level"] == 1].sort_values("flood_tile_coverage_share").head(3)
    lake = build_lake_daily()
    lake_summary = lake.groupby("lake").agg(date_min=("date", "min"), date_max=("date", "max"), records=("date", "size")).reset_index()
    climate_regions = pd.DataFrame([region.__dict__ for region in HYDRO_REGIONS])
    year_col = "date" if "date" in annual.columns else annual.columns[0]
    highest_flood_year = int(annual.sort_values("total_flooded_pixel_count", ascending=False).iloc[0][year_col])

    text = f"""# Revised Spatial EDA

This EDA supersedes earlier first-pass outputs that used whole-rectangle climate averages or a single ET grid cell.

## Analysis scope

- Flood mask local coverage: h20v08 + h21v08, approximately lon 20E-40E and lat 0N-10N.
- South Sudan extends north to about 12.24N, so the local flood mask misses northern South Sudan above 10N.
- Main flood panel grain: admin2-date, using flood pixels spatially joined to South Sudan admin2 polygons.
- ERA5 rainfall/runoff are gridded hourly fields and are aggregated by admin2 and by heuristic hydro-climate regions.
- ET is a gridded daily field and is aggregated by admin2 and by the same heuristic hydro-climate regions.
- Discharge main variable is station 100205; unrelated Omo, Blue Nile, and Atbara stations are excluded from main EDA.
- Lake levels are treated as upstream context: Victoria -> Kyoga -> Albert -> White Nile -> South Sudan. Victoria outflow is regulated, so it is not a purely natural upstream signal.

## Key tables

- admin2_daily_flood_climate_panel.csv
- hydro_region_daily_panel.csv
- flood_admin_coverage_summary.csv
- discharge_station_relevance.csv
- upstream_lake_water_levels_daily.csv
- national_daily_flood_climate_admin2_mean.csv

## Key checks

- Admin2 daily panel rows: {len(panel):,}
- Date range: {panel['date'].min().date()} to {panel['date'].max().date()}
- Admin2 units: {panel['adm2_pcode'].nunique()}
- Hydro-climate regions: {region_panel['region_id'].nunique()}
- Highest annual admin2-clipped flood year: {highest_flood_year}

## Lowest admin1 flood-mask coverage

{simple_markdown_table(admin1_coverage[['admin_name', 'flood_tile_coverage_share']])}

## Discharge station treatment

{simple_markdown_table(station_relevance[['area_id', 'country', 'hydrological_relevance', 'use_in_main_eda']])}

## Upstream lake time coverage

{simple_markdown_table(lake_summary)}

## Climate region definitions

{simple_markdown_table(climate_regions[['region_id', 'label', 'notes']])}

## Strongest admin2-mean climate lag per feature

{simple_markdown_table(best_climate.head(20))}

## Strongest hydro-region climate lag correlations

{simple_markdown_table(top_region.head(20))}

## Interpretation cautions

- Correlations are exploratory and not causal evidence.
- Flood mask data are event records, not full daily no-flood/flood maps; zeros in the panel mean no flood event record in that admin2-date after spatial joining.
- Flooded area is approximated as pixel_count x 0.0625 km2, using the rough 250m grid size from the data description.
- Hydro-climate regions are pragmatic boxes, not formal watershed polygons.
- Upstream rainfall/runoff outside South Sudan may matter, so the regional climate features are intentionally retained alongside South Sudan-only aggregates.
"""
    (OUT_DIR / "REVISED_EDA_REPORT.md").write_text(text)


def generate_outputs(force: bool = False) -> None:
    ensure_dirs()
    save_scope_tables(force=force)
    panel = build_admin2_panel(force=force)
    region_panel = build_region_daily_panel(force=force)
    coverage = build_flood_coverage_summary(force=force)
    plot_flood_scope(panel, coverage)
    plot_climate_and_lags(panel, region_panel)
    plot_discharge_and_lakes(panel)
    write_report(panel, region_panel)


def main() -> None:
    generate_outputs(force=False)
    print(f"Revised spatial EDA outputs saved to {OUT_DIR}")
    print(f"Figures saved to {FIG_DIR}")


if __name__ == "__main__":
    main()
