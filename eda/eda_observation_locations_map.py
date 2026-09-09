from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw_data"
PROCESSED_DIR = ROOT / "processed-data"
OUT_DIR = ROOT / "eda" / "outputs" / "observation_locations_map"

ADMIN0_PATH = RAW_DIR / "Administrative boundaries" / "ssd_admin0.geojson"
ADMIN1_PATH = RAW_DIR / "Administrative boundaries" / "ssd_admin1.geojson"
DISCHARGE_PATH = (
    PROCESSED_DIR
    / "Darthmouth Flood Observatory"
    / "dartmouth_discharge_all_processed_with_station_info.csv"
)
WATER_LEVEL_PATH = PROCESSED_DIR / "Water levels lakes" / "water_levels_all_processed.csv"
ERA5_SAMPLE_PATH = RAW_DIR / "rainfall and runoff" / "ERA5_2000.nc"
ET_SAMPLE_PATH = next((RAW_DIR / "evapotranspiration" / "ET_2000").glob("*.nc"))
NATURAL_EARTH_DIR = RAW_DIR / "external_geography" / "natural_earth"
COUNTRIES_PATH = NATURAL_EARTH_DIR / "ne_10m_admin_0_countries.zip"
RIVERS_PATH = NATURAL_EARTH_DIR / "ne_10m_rivers_lake_centerlines.zip"
LAKES_PATH = NATURAL_EARTH_DIR / "ne_10m_lakes.zip"
MAP_BBOX = (19.5, -3.5, 40.5, 22.2)
FLOOD_MASK_EXTENT = {
    "lon_min": 20.0,
    "lon_max": 40.0,
    "lat_min": 0.0,
    "lat_max": 10.0,
}


def netcdf_extent(path: Path, lat_name: str, lon_name: str) -> dict:
    with xr.open_dataset(path) as ds:
        lat = ds[lat_name].values
        lon = ds[lon_name].values
        return {
            "lat_min": float(lat.min()),
            "lat_max": float(lat.max()),
            "lon_min": float(lon.min()),
            "lon_max": float(lon.max()),
            "lat_count": int(len(lat)),
            "lon_count": int(len(lon)),
        }


def netcdf_grid_points(
    path: Path,
    lat_name: str,
    lon_name: str,
    lat_step: int = 1,
    lon_step: int = 1,
) -> pd.DataFrame:
    with xr.open_dataset(path) as ds:
        lat = ds[lat_name].values[::lat_step]
        lon = ds[lon_name].values[::lon_step]
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    return pd.DataFrame(
        {"longitude": lon_grid.ravel(), "latitude": lat_grid.ravel()}
    )


def load_station_points() -> pd.DataFrame:
    stations = pd.read_csv(
        DISCHARGE_PATH,
        usecols=["area_id", "station_nr", "country", "latitude", "longitude"],
    )
    stations = stations.drop_duplicates().sort_values("area_id").reset_index(drop=True)
    stations["dataset"] = "Dartmouth discharge station"
    stations["label"] = stations["area_id"].astype(str)
    return stations


def load_lake_points() -> pd.DataFrame:
    water = pd.read_csv(
        WATER_LEVEL_PATH,
        usecols=["lake", "country", "target_latitude", "target_longitude", "date"],
    )
    lakes = (
        water.groupby(["lake", "country", "target_latitude", "target_longitude"])
        .agg(date_min=("date", "min"), date_max=("date", "max"), record_count=("date", "size"))
        .reset_index()
    )
    lakes = lakes.rename(
        columns={"target_latitude": "latitude", "target_longitude": "longitude"}
    )
    lakes["dataset"] = "Lake water level point"
    lakes["label"] = lakes["lake"]
    return lakes


def read_natural_earth_zip(path: Path) -> gpd.GeoDataFrame:
    return gpd.read_file(f"zip://{path.resolve()}", bbox=MAP_BBOX).to_crs("EPSG:4326")


def load_surrounding_countries() -> gpd.GeoDataFrame:
    countries = read_natural_earth_zip(COUNTRIES_PATH)
    name_col = "NAME" if "NAME" in countries.columns else "name"
    keep = [
        "South Sudan",
        "Sudan",
        "Ethiopia",
        "Uganda",
        "Kenya",
        "Democratic Republic of the Congo",
        "Central African Republic",
    ]
    return countries[countries[name_col].isin(keep)].copy()


def load_major_rivers() -> gpd.GeoDataFrame:
    rivers = read_natural_earth_zip(RIVERS_PATH)
    names = {
        "Nile",
        "White Nile",
        "Bahr el Jebel",
        "Albert Nile",
        "Victoria Nile",
        "El Bahr el Abyad",
        "Sobat",
        "Pibor",
        "Akobo",
        "Bahr el Zeraf",
        "Bahr el  Zeraf",
    }
    name_cols = [col for col in ["name", "name_en", "label"] if col in rivers.columns]
    mask = pd.Series(False, index=rivers.index)
    for col in name_cols:
        mask = mask | rivers[col].isin(names)
    return rivers[mask].copy()


def load_major_lakes() -> gpd.GeoDataFrame:
    lakes = read_natural_earth_zip(LAKES_PATH)
    names = {
        "Lake Albert",
        "Lake Kyoga",
        "Lake Victoria",
        "Lake Turkana",
        "Lake Tana",
        "Lake Edward",
        "Lake Kivu",
    }
    name_cols = [col for col in ["name", "name_en", "label"] if col in lakes.columns]
    mask = pd.Series(False, index=lakes.index)
    for col in name_cols:
        mask = mask | lakes[col].isin(names) | lakes[col].map(lambda x: f"Lake {x}" in names if pd.notna(x) else False)
    return lakes[mask].copy()


def add_extent_rectangle(ax, extent: dict, edgecolor: str, label: str, linestyle: str) -> None:
    ax.add_patch(
        Rectangle(
            (extent["lon_min"], extent["lat_min"]),
            extent["lon_max"] - extent["lon_min"],
            extent["lat_max"] - extent["lat_min"],
            fill=False,
            edgecolor=edgecolor,
            linewidth=1.5,
            linestyle=linestyle,
            label=label,
        )
    )


def save_observation_summary(
    stations: pd.DataFrame,
    lakes: pd.DataFrame,
    era5_extent: dict,
    et_extent: dict,
) -> None:
    rows = []
    for _, row in stations.iterrows():
        rows.append(
            {
                "dataset": row["dataset"],
                "name": row["label"],
                "country": row["country"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "notes": f"station_nr={row['station_nr']}",
            }
        )
    for _, row in lakes.iterrows():
        rows.append(
            {
                "dataset": row["dataset"],
                "name": row["lake"],
                "country": row["country"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "notes": f"{row['date_min']} to {row['date_max']}; n={row['record_count']}",
            }
        )
    rows.append(
        {
            "dataset": "ERA5 rainfall/runoff grid extent",
            "name": "ERA5 domain",
            "country": "",
            "latitude": "",
            "longitude": "",
            "notes": (
                f"lon {era5_extent['lon_min']:.2f}-{era5_extent['lon_max']:.2f}; "
                f"lat {era5_extent['lat_min']:.2f}-{era5_extent['lat_max']:.2f}; "
                f"{era5_extent['lat_count']}x{era5_extent['lon_count']} grid"
            ),
        }
    )
    rows.append(
        {
            "dataset": "ET raw grid extent",
            "name": "AgERA5 ET domain",
            "country": "",
            "latitude": "",
            "longitude": "",
            "notes": (
                f"lon {et_extent['lon_min']:.2f}-{et_extent['lon_max']:.2f}; "
                f"lat {et_extent['lat_min']:.2f}-{et_extent['lat_max']:.2f}; "
                f"{et_extent['lat_count']}x{et_extent['lon_count']} grid"
            ),
        }
    )
    pd.DataFrame(rows).to_csv(OUT_DIR / "observation_locations_summary.csv", index=False)


def add_context_layers(ax, countries, geography_lakes, admin0, admin1, rivers) -> None:
    countries.plot(ax=ax, color="#f3efe6", edgecolor="#b6aa98", linewidth=0.8, zorder=1)
    geography_lakes.plot(ax=ax, color="#b9d9e8", edgecolor="#4f8bad", linewidth=0.7, zorder=2)
    admin0.plot(ax=ax, color="#efe7d6", edgecolor="#242424", linewidth=1.3, zorder=3)
    admin1.boundary.plot(ax=ax, color="#8a8a8a", linewidth=0.55, zorder=4)
    rivers.plot(ax=ax, color="#2777b8", linewidth=1.35, alpha=0.82, zorder=5)


def add_labels(ax, countries, geography_lakes, admin1) -> None:
    for _, row in admin1.iterrows():
        point = row.geometry.representative_point()
        ax.text(
            point.x,
            point.y,
            row["adm1_name"],
            fontsize=7,
            color="#565656",
            ha="center",
            va="center",
            alpha=0.85,
            zorder=6,
        )

    country_name_col = "NAME" if "NAME" in countries.columns else "name"
    for _, row in countries.iterrows():
        if row[country_name_col] == "South Sudan":
            continue
        point = row.geometry.representative_point()
        ax.text(
            point.x,
            point.y,
            row[country_name_col],
            fontsize=8,
            color="#7a6f61",
            ha="center",
            va="center",
            alpha=0.8,
            zorder=2,
        )

    for _, row in geography_lakes.iterrows():
        label = row.get("label") or row.get("name") or row.get("name_en")
        if pd.isna(label):
            continue
        point = row.geometry.representative_point()
        ax.text(
            point.x,
            point.y,
            str(label).replace("Lake ", ""),
            fontsize=7.5,
            color="#245e7a",
            ha="center",
            va="center",
            alpha=0.95,
            zorder=6,
        )


def add_observation_points(ax, stations, lakes) -> None:
    ax.scatter(
        stations["longitude"],
        stations["latitude"],
        s=52,
        c="#d34b30",
        edgecolors="white",
        linewidths=0.7,
        zorder=7,
        label="Dartmouth discharge stations",
    )
    ax.scatter(
        lakes["longitude"],
        lakes["latitude"],
        s=95,
        marker="^",
        c="#1e8b76",
        edgecolors="white",
        linewidths=0.7,
        zorder=8,
        label="Lake water-level points",
    )
    for _, row in stations.iterrows():
        ax.annotate(
            row["label"],
            (row["longitude"], row["latitude"]),
            xytext=(4, 3),
            textcoords="offset points",
            fontsize=7.5,
            color="#5f1f18",
            zorder=10,
        )
    for _, row in lakes.iterrows():
        ax.annotate(
            row["lake"],
            (row["longitude"], row["latitude"]),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=8,
            color="#0b5c50",
            zorder=10,
        )

def format_map(ax, title: str) -> None:
    ax.set_xlim(MAP_BBOX[0], MAP_BBOX[2])
    ax.set_ylim(MAP_BBOX[1], MAP_BBOX[3])
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(color="#d6d6d6", linewidth=0.45, alpha=0.7)


def plot_map() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    admin0 = gpd.read_file(ADMIN0_PATH)
    admin1 = gpd.read_file(ADMIN1_PATH)
    countries = load_surrounding_countries()
    rivers = load_major_rivers()
    geography_lakes = load_major_lakes()
    stations = load_station_points()
    lakes = load_lake_points()
    era5_extent = netcdf_extent(ERA5_SAMPLE_PATH, "latitude", "longitude")
    et_extent = netcdf_extent(ET_SAMPLE_PATH, "lat", "lon")
    save_observation_summary(stations, lakes, era5_extent, et_extent)

    fig, ax = plt.subplots(figsize=(11, 12))
    add_context_layers(ax, countries, geography_lakes, admin0, admin1, rivers)

    add_extent_rectangle(ax, era5_extent, "#7b6fd0", "ERA5 rainfall/runoff grid", "--")
    add_extent_rectangle(ax, et_extent, "#8b8b8b", "ET raw grid", ":")
    add_extent_rectangle(ax, FLOOD_MASK_EXTENT, "#d05a2f", "Flood mask h20v08+h21v08 extent", "-.")

    add_observation_points(ax, stations, lakes)
    add_labels(ax, countries, geography_lakes, admin1)
    format_map(ax, "South Sudan Regional Hydro-Geography and Observation Coverage")

    handles = [
        Patch(facecolor="#f3efe6", edgecolor="#b6aa98", label="Surrounding countries"),
        Patch(facecolor="#efe7d6", edgecolor="#242424", label="South Sudan admin0"),
        Line2D([0], [0], color="#9d9d9d", linewidth=0.8, label="Admin1 boundaries"),
        Patch(facecolor="#b9d9e8", edgecolor="#4f8bad", label="Major lakes"),
        Line2D([0], [0], color="#2777b8", linewidth=1.8, label="Major rivers"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#d34b30", markersize=7, label="12 discharge stations"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#1e8b76", markersize=8, label="3 lake water-level points"),
        Patch(facecolor="none", edgecolor="#7b6fd0", linestyle="--", label="ERA5 rainfall/runoff grid"),
        Patch(facecolor="none", edgecolor="#8b8b8b", linestyle=":", label="ET raw grid"),
        Patch(facecolor="none", edgecolor="#d05a2f", linestyle="-.", label="Flood mask h20v08+h21v08 extent"),
    ]
    ax.legend(handles=handles, loc="lower left", frameon=True, framealpha=0.94, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "observation_locations_context_map.png", dpi=220)
    plt.close(fig)

    era5_points = netcdf_grid_points(ERA5_SAMPLE_PATH, "latitude", "longitude")
    et_points = netcdf_grid_points(ET_SAMPLE_PATH, "lat", "lon")
    fig, ax = plt.subplots(figsize=(11, 12))
    add_context_layers(ax, countries, geography_lakes, admin0, admin1, rivers)
    ax.scatter(
        et_points["longitude"],
        et_points["latitude"],
        s=1.4,
        c="#6f6f6f",
        alpha=0.16,
        linewidths=0,
        zorder=4.5,
        label="ET grid nodes",
    )
    ax.scatter(
        era5_points["longitude"],
        era5_points["latitude"],
        s=7,
        marker="s",
        c="#795fd0",
        alpha=0.38,
        linewidths=0,
        zorder=4.8,
        label="ERA5 rainfall/runoff grid nodes",
    )
    add_extent_rectangle(ax, era5_extent, "#7b6fd0", "ERA5 rainfall/runoff grid", "--")
    add_extent_rectangle(ax, et_extent, "#8b8b8b", "ET raw grid", ":")
    add_extent_rectangle(ax, FLOOD_MASK_EXTENT, "#d05a2f", "Flood mask h20v08+h21v08 extent", "-.")
    add_observation_points(ax, stations, lakes)
    add_labels(ax, countries, geography_lakes, admin1)
    format_map(ax, "ERA5 Rainfall/Runoff and ET Grid Nodes Around South Sudan")

    grid_handles = [
        Patch(facecolor="#f3efe6", edgecolor="#b6aa98", label="Surrounding countries"),
        Patch(facecolor="#efe7d6", edgecolor="#242424", label="South Sudan admin0"),
        Patch(facecolor="#b9d9e8", edgecolor="#4f8bad", label="Major lakes"),
        Line2D([0], [0], color="#2777b8", linewidth=1.8, label="Major rivers"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#795fd0", markersize=5, label="ERA5 nodes: 145 x 57"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#6f6f6f", alpha=0.5, markersize=4, label="ET nodes: 360 x 140"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#d34b30", markersize=7, label="Discharge stations"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#1e8b76", markersize=8, label="Lake water-level points"),
        Patch(facecolor="none", edgecolor="#d05a2f", linestyle="-.", label="Flood mask h20v08+h21v08 extent"),
    ]
    ax.legend(handles=grid_handles, loc="lower left", frameon=True, framealpha=0.94, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "climate_grid_points_context_map.png", dpi=220)
    plt.close(fig)

    notes = """# Observation Locations Map

This map is a spatial sanity check for the hydrological and climate data used in the EDA.

- Dartmouth discharge data contain 12 station points. Only station 100205 is inside/near South Sudan; most others are downstream in Sudan or upstream in Ethiopia.
- Lake water-level data contain three representative lake points: Albert, Kyoga, and Victoria. All are outside South Sudan, so they should be treated as upstream/regional context rather than local South Sudan lake gauges.
- ERA5 rainfall/runoff raw data are gridded over a broad domain, but the processed file currently stores one daily spatial mean.
- ET raw data are also gridded. The previous single-cell ET marker is intentionally not shown because it is not a meaningful observation location for the main analysis.
- The local flood mask data cover h20v08 and h21v08, approximately lon 20E-40E and lat 0N-10N; this misses northern South Sudan above 10N.
- Major river, lake, and surrounding-country layers come from Natural Earth 1:10m data downloaded into raw_data/external_geography/natural_earth.
- climate_grid_points_context_map.png shows all ERA5 grid nodes and all ET grid nodes to make the difference in spatial resolution visible.
"""
    (OUT_DIR / "README.md").write_text(notes)


if __name__ == "__main__":
    plot_map()
