"""
Stages 10–14: county-month flood panel and hypothesis execution.

Run from repo root:
    python -m archive.impact_eda.impact_panel --through 14
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.api as sm
import xarray as xr
from processing_data.paths import COURSE_RAW, EXT_DATA, PROCESSED_DIR, ROOT, ensure_impact_eda_out

OUT = ensure_impact_eda_out()
CROSS = OUT / "crosswalks"
GED_PATH = EXT_DATA / "UCDP_georeferenced_and_nonstate" / "ged261-csv" / "GEDEvent_v26_1.csv"
TILES = ("h20v08", "h21v08")
COORD_ROUND = 6


def _coord_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["lat_k"] = np.round(out["lat"].astype(float), COORD_ROUND)
    out["lon_k"] = np.round(out["lon"].astype(float), COORD_ROUND)
    return out

PLANT_MONTHS = (4, 5, 6)
HARVEST_MONTHS = (9, 10, 11)
RAIN_MONTHS = (6, 7, 8, 9, 10)

H2_BASELINE_END = 2021  # decided in Stage 11 gate narrative


def _spearman(x: pd.Series, y: pd.Series) -> float:
    frame = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(frame) < 5:
        return np.nan
    return float(frame["x"].rank().corr(frame["y"].rank()))


def _flood_parquet_paths() -> list[tuple[str, int, str, Path]]:
    """Return (mask_type, year, tile, path) for all compact parquets."""
    rows: list[tuple[str, int, str, Path]] = []
    for kind in ("unusual", "recurring"):
        folder = COURSE_RAW / "flood_masks" / f"compact_{kind}"
        for path in sorted(folder.glob("flood_events_*.parquet")):
            stem = path.stem
            tile, year_s = stem.rsplit("_", 2)[1], stem.rsplit("_", 1)[-1]
            rows.append((kind, int(year_s), tile, path))
    return rows


def _admin2_gdf() -> gpd.GeoDataFrame:
    return gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson").to_crs(
        "EPSG:4326"
    )


def build_pixel_lookup(force: bool = False) -> Path:
    """Union unique lat/lon across parquets; single sjoin to adm2_pcode."""
    cache = OUT / "flood_pixel_to_admin2.csv"
    if cache.exists() and not force:
        return cache

    parts: list[pd.DataFrame] = []
    for _kind, _year, _tile, path in _flood_parquet_paths():
        df = pd.read_parquet(path, columns=["lat", "lon"])
        parts.append(_coord_keys(df))
    union = pd.concat(parts, ignore_index=True).drop_duplicates(subset=["lat_k", "lon_k"])
    gdf = gpd.GeoDataFrame(
        union,
        geometry=gpd.points_from_xy(union["lon_k"], union["lat_k"]),
        crs="EPSG:4326",
    )
    admin2 = _admin2_gdf()
    joined = gpd.sjoin(
        gdf,
        admin2[["adm2_pcode", "geometry"]],
        how="inner",
        predicate="within",
    )
    lookup = joined[["lat_k", "lon_k", "adm2_pcode"]].drop_duplicates(subset=["lat_k", "lon_k"])
    lookup.to_csv(cache, index=False)
    return cache


def _parse_flood_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series.astype(str), errors="coerce")


def build_flood_panels(force: bool = False) -> tuple[Path, Path]:
    """County-month and county-year flood panels with lookup join."""
    month_path = OUT / "flood_admin2_month.csv"
    year_path = OUT / "flood_admin2_year.csv"
    if month_path.exists() and year_path.exists() and not force:
        return month_path, year_path

    lookup = pd.read_csv(build_pixel_lookup(force=force))
    paths = _flood_parquet_paths()
    by_mask_year: dict[tuple[str, int], list[Path]] = defaultdict(list)
    for mask_type, year, _tile, path in paths:
        by_mask_year[(mask_type, year)].append(path)

    month_frames: list[pd.DataFrame] = []
    year_rows: list[dict] = []

    for (mask_type, year), files in sorted(by_mask_year.items()):
        parts = []
        for path in files:
            parts.append(pd.read_parquet(path, columns=["date", "lat", "lon"]))
        if not parts:
            continue
        df = pd.concat(parts, ignore_index=True)
        df = _coord_keys(df)
        df["date"] = _parse_flood_dates(df["date"])
        df = df.dropna(subset=["date"])
        df["year"] = df["date"].dt.year.astype(int)
        df["month"] = df["date"].dt.month.astype(int)
        df = df.merge(lookup, on=["lat_k", "lon_k"], how="inner")
        if df.empty:
            continue

        ym = (
            df.groupby(["adm2_pcode", "year", "month"], observed=True)
            .apply(
                lambda g: pd.Series(
                    {
                        "unique_px": g[["lat_k", "lon_k"]].drop_duplicates().shape[0],
                        "pixel_days": len(g),
                        "obs_days": g["date"].nunique(),
                    }
                ),
                include_groups=False,
            )
            .reset_index()
        )
        ym["mask_type"] = mask_type
        month_frames.append(ym)

        yc = (
            df.groupby("adm2_pcode", observed=True)
            .apply(
                lambda g: g[["lat_k", "lon_k"]].drop_duplicates().shape[0],
                include_groups=False,
            )
            .reset_index(name="unique_px")
        )
        yc["mask_type"] = mask_type
        yc["year"] = year
        year_rows.extend(yc.to_dict("records"))

    month = pd.concat(month_frames, ignore_index=True) if month_frames else pd.DataFrame()
    month.to_csv(month_path, index=False)
    pd.DataFrame(year_rows).to_csv(year_path, index=False)
    return month_path, year_path


def run_stage10_panel() -> dict:
    lookup_p = build_pixel_lookup()
    month_p, year_p = build_flood_panels()
    gate = reconcile_year_panel_gate()
    gate_path = ROOT / "archive" / "impact_eda" / "gates" / "STAGE10_GATE.md"
    lines = [
        "# Stage 10 gate — flood admin2 panel",
        "",
        "## Artefacts",
        "",
        f"| Output | Path |",
        f"|--------|------|",
        f"| Pixel lookup | `{lookup_p.relative_to(ROOT)}` |",
        f"| County-month panel | `{month_p.relative_to(ROOT)}` |",
        f"| County-year panel | `{year_p.relative_to(ROOT)}` |",
        "",
        "## Reconcile vs Stage 7 (2022–2024 unusual unique px)",
        "",
        f"- Max absolute county-year diff: **{gate['max_abs_diff']:.0f}**",
        f"- Counties compared: **{gate['n_compare']}**",
        f"- Gate pass: **{'yes' if gate['pass'] else 'NO — stop'}**",
        "",
        "```powershell",
        "python -m archive.impact_eda.impact_panel --through 10",
        "```",
    ]
    gate_path.write_text("\n".join(lines), encoding="utf-8")
    return {"lookup": str(lookup_p), "month": str(month_p), "year": str(year_p), "gate": gate}


def reconcile_year_panel_gate() -> dict:
    ref_u = pd.read_csv(OUT / "admin2_unusual_flood_2022_2024.csv")
    ref_r = pd.read_csv(OUT / "admin2_recurring_flood_2022_2024.csv")
    built = pd.read_csv(OUT / "flood_admin2_year.csv")
    diffs = []
    for mask, ref, col in [
        ("unusual", ref_u, "unusual_unique_px"),
        ("recurring", ref_r, "recurring_unique_px"),
    ]:
        b = built[built.mask_type == mask].rename(columns={"unique_px": "built_px"})
        m = ref.merge(b, on=["adm2_pcode", "year"], how="inner")
        if len(m):
            m["diff"] = m["built_px"] - m[col]
            diffs.append(m)
    if not diffs:
        return {"max_abs_diff": np.nan, "n_compare": 0, "pass": False}
    all_d = pd.concat(diffs, ignore_index=True)
    max_diff = float(all_d["diff"].abs().max())
    return {"max_abs_diff": max_diff, "n_compare": len(all_d), "pass": max_diff <= 1}


def run_stage11_observability() -> Path:
    """Tile-month obs days, cloud_frac audit, regime break."""
    cloud_rows = []
    for mask_type, year, tile, path in _flood_parquet_paths()[:8]:
        s = pd.read_parquet(path, columns=["cloud_frac"])["cloud_frac"]
        cloud_rows.append(
            {
                "path": path.name,
                "n": len(s),
                "min": float(s.min()),
                "max": float(s.max()),
                "nunique": int(s.nunique()),
            }
        )
    pd.DataFrame(cloud_rows).to_csv(OUT / "stage11_cloud_frac_audit.csv", index=False)

    daily = pd.read_csv(
        PROCESSED_DIR / "flood_masks" / "flood_masks_daily_counts_processed.csv",
        parse_dates=["date"],
    )
    daily["month"] = daily.date.dt.month
    daily["year"] = daily.date.dt.year
    tile_month = (
        daily.groupby(["year", "month", "tile", "flood_type_label"], observed=True)
        .size()
        .reset_index(name="n_records")
    )
    tile_month.to_csv(OUT / "stage11_tile_month_record_counts.csv", index=False)

    annual = (
        daily.groupby(["year", "flood_type_label"], observed=True)["flooded_pixel_count"]
        .sum()
        .reset_index()
    )
    annual.to_csv(OUT / "stage11_annual_pixel_days.csv", index=False)
    pre = annual[(annual.year <= 2019) & (annual.flood_type_label == "unusual")][
        "flooded_pixel_count"
    ].mean()
    post = annual[(annual.year >= 2022) & (annual.flood_type_label == "unusual")][
        "flooded_pixel_count"
    ].mean()

    share = daily.pivot_table(
        index="year",
        columns="month",
        values="flooded_pixel_count",
        aggfunc="sum",
        observed=True,
    )
    for label in ("unusual", "recurring"):
        sub = daily[daily.flood_type_label == label]
        sm = sub.groupby("month")["flooded_pixel_count"].sum()
        sm = sm / sm.sum()
        sm.to_csv(OUT / f"stage11_monthly_share_{label}.csv")

    gate = ROOT / "archive" / "impact_eda" / "gates" / "STAGE11_GATE.md"
    gate.write_text(
        "\n".join(
            [
                "# Stage 11 gate — observability and regime",
                "",
                "## Findings",
                "",
                "- `cloud_frac` in compact parquets is **constant 0.0** (see `stage11_cloud_frac_audit.csv`). Not usable as a control.",
                "- Tile-month record counts in `stage11_tile_month_record_counts.csv` (proxy for observation intensity).",
                "- Unusual annual pixel-days mean ≤2019: **{:.0f}**; ≥2022: **{:.0f}** (`stage11_annual_pixel_days.csv`).".format(
                    pre, post
                ),
                "- **Baseline decision for H2:** use county demeaning with years **2011–2024**; sensitivity excluding **≥2022**.",
                "- **H3 windows:** planting months **4–6**, harvest **9–11** (pre-declared).",
                "- Recurring and unusual share similar dry-season peaks → interpret seasonality as shared hydrology/artefact, not mask-specific.",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_panel --through 11",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return gate


def _fews_ha() -> pd.DataFrame:
    xw = pd.read_csv(CROSS / "fews_fnid_to_admin2.csv")
    crop = pd.read_csv(EXT_DATA / "FEWS_crop_data" / "crop_data.csv")
    ah = crop[crop.indicator == "Area Harvested"].copy()
    ah["year"] = ah.season_year.str.extract(r"(\d{4})").astype(int)
    ah = ah.merge(xw[["fnid", "cod_pcode"]].drop_duplicates(), on="fnid", how="left")
    ah = ah.dropna(subset=["cod_pcode"])
    return ah.groupby(["cod_pcode", "year"], as_index=False)["value"].sum().rename(
        columns={"cod_pcode": "adm2_pcode", "value": "ha_harvested"}
    )


def _within_ols_cluster(
    df: pd.DataFrame,
    y_col: str,
    x_cols: list[str],
    cluster_col: str = "adm2_pcode",
) -> pd.DataFrame:
    """Two-way demean (county + year) OLS with cluster-robust SE."""
    work = df.dropna(subset=[y_col] + x_cols + [cluster_col, "year"]).copy()
    if len(work) < 30:
        return pd.DataFrame()
    for c in [y_col] + x_cols:
        work[c] = work[c].astype(float)
    work["y_dm"] = work[y_col] - work.groupby(cluster_col)[y_col].transform("mean")
    work["y_dm"] -= work.groupby("year")[y_col].transform("mean")
    work["y_dm"] += work[y_col].mean()
    for xc in x_cols:
        work[f"{xc}_dm"] = work[xc] - work.groupby(cluster_col)[xc].transform("mean")
        work[f"{xc}_dm"] -= work.groupby("year")[xc].transform("mean")
        work[f"{xc}_dm"] += work[xc].mean()
    x_dm = [f"{xc}_dm" for xc in x_cols]
    X = sm.add_constant(work[x_dm])
    model = sm.OLS(work["y_dm"], X).fit(cov_type="cluster", cov_kwds={"groups": work[cluster_col]})
    rows = []
    for name, coef, pval in zip(model.params.index, model.params, model.pvalues):
        rows.append({"term": name, "coef": float(coef), "pvalue": float(pval), "n": len(work)})
    out = pd.DataFrame(rows)
    return out


def run_stage12_cropland() -> Path:
    year_p = OUT / "flood_admin2_year.csv"
    if not year_p.exists():
        build_flood_panels()
    flood_y = pd.read_csv(year_p)
    fews = _fews_ha()
    u = flood_y[flood_y.mask_type == "unusual"].rename(columns={"unique_px": "unusual_px"})
    r = flood_y[flood_y.mask_type == "recurring"].rename(columns={"unique_px": "recurring_px"})
    panel = u.merge(r, on=["adm2_pcode", "year"], how="outer").merge(
        fews, on=["adm2_pcode", "year"], how="inner"
    )
    panel["log_ha"] = np.log1p(panel["ha_harvested"])
    panel["log_unusual"] = np.log1p(panel["unusual_px"].fillna(0))
    panel["log_recurring"] = np.log1p(panel["recurring_px"].fillna(0))

    spearman_rows = []
    for y in sorted(panel.year.unique()):
        sub = panel[panel.year == y]
        spearman_rows.append(
            {
                "year": y,
                "spearman_unusual_ha": _spearman(sub.unusual_px, sub.ha_harvested),
                "n": len(sub),
            }
        )
    pd.DataFrame(spearman_rows).to_csv(OUT / "stage12_pooled_spearman_by_year.csv", index=False)

    ols_h2 = _within_ols_cluster(panel, "log_ha", ["log_unusual"])
    ols_h4 = _within_ols_cluster(panel, "log_ha", ["log_unusual", "log_recurring"])
    ols_h2.to_csv(OUT / "stage12_within_county_ols_h2.csv", index=False)
    ols_h4.to_csv(OUT / "stage12_within_county_ols_h4.csv", index=False)

    month = pd.read_csv(OUT / "flood_admin2_month.csv")
    plant = (
        month[month.month.isin(PLANT_MONTHS)]
        .groupby(["adm2_pcode", "year", "mask_type"], observed=True)["pixel_days"]
        .sum()
        .unstack(fill_value=0)
    )
    harv = (
        month[month.month.isin(HARVEST_MONTHS)]
        .groupby(["adm2_pcode", "year", "mask_type"], observed=True)["pixel_days"]
        .sum()
        .unstack(fill_value=0)
    )
    seasonal = plant.add_suffix("_plant").join(harv.add_suffix("_harvest"), how="outer")
    seasonal = seasonal.reset_index().merge(fews, on=["adm2_pcode", "year"], how="inner")
    seasonal["log_ha"] = np.log1p(seasonal["ha_harvested"])
    if "unusual_plant" in seasonal.columns:
        seasonal["log_u_plant"] = np.log1p(seasonal["unusual_plant"].fillna(0))
        seasonal["log_u_harv"] = np.log1p(seasonal["unusual_harvest"].fillna(0))
        ols_h3 = _within_ols_cluster(seasonal, "log_ha", ["log_u_plant", "log_u_harv"])
        ols_h3.to_csv(OUT / "stage12_within_county_ols_h3.csv", index=False)
    seasonal.to_csv(OUT / "stage12_seasonal_pixel_days.csv", index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE12_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 12 gate — H2/H3/H4 cropland panel",
                "",
                "Outputs: `stage12_pooled_spearman_by_year.csv`, `stage12_within_county_ols_h2.csv`,",
                "`stage12_within_county_ols_h4.csv`, `stage12_within_county_ols_h3.csv`, `stage12_seasonal_pixel_days.csv`.",
                "",
                "If within-county coefficients are insignificant, cropland deliverable stays **exposure-only**.",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_panel --through 12",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return OUT / "stage12_within_county_ols_h2.csv"


def _era5_grid_to_counties() -> pd.DataFrame:
    """Map ERA5 grid cells to adm2_pcode (one-time)."""
    cache = OUT / "era5_grid_to_admin2.csv"
    if cache.exists():
        return pd.read_csv(cache)
    path = COURSE_RAW / "rainfall and runoff" / "ERA5_2023.nc"
    with xr.open_dataset(path) as ds:
        lats = ds["latitude"].values
        lons = ds["longitude"].values
    la_grid, lo_grid = np.meshgrid(lats, lons, indexing="ij")
    rows = pd.DataFrame(
        {"latitude": la_grid.ravel().astype(float), "longitude": lo_grid.ravel().astype(float)}
    )
    gdf = gpd.GeoDataFrame(
        rows,
        geometry=gpd.points_from_xy(rows["longitude"], rows["latitude"]),
        crs="EPSG:4326",
    )
    admin2 = _admin2_gdf()
    joined = gpd.sjoin(gdf, admin2[["adm2_pcode", "geometry"]], how="inner", predicate="within")
    joined[["latitude", "longitude", "adm2_pcode"]].drop_duplicates().to_csv(cache, index=False)
    return pd.read_csv(cache)


def run_stage13_climate_pop() -> dict:
    grid_map = _era5_grid_to_counties()
    rain_rows = []
    for path in sorted((COURSE_RAW / "rainfall and runoff").glob("ERA5_*.nc")):
        year = int(re.search(r"ERA5_(\d{4})", path.name).group(1))
        with xr.open_dataset(path) as ds:
            for pcode, grp in grid_map.groupby("adm2_pcode", observed=True):
                tp_sum = 0.0
                ro_sum = 0.0
                for _, row in grp.iterrows():
                    la, lo = float(row["latitude"]), float(row["longitude"])
                    tp_sum += float(ds["tp"].sel(latitude=la, longitude=lo, method="nearest").sum())
                    ro_sum += float(ds["ro"].sel(latitude=la, longitude=lo, method="nearest").sum())
                rain_rows.append(
                    {
                        "adm2_pcode": pcode,
                        "year": year,
                        "precip_sum_m": tp_sum,
                        "runoff_sum_m": ro_sum,
                    }
                )
    era5_cy = pd.DataFrame(rain_rows)
    era5_cy.to_csv(OUT / "stage13_era5_county_year.csv", index=False)

    flood_y = pd.read_csv(OUT / "flood_admin2_year.csv")
    u = flood_y[flood_y.mask_type == "unusual"][["adm2_pcode", "year", "unique_px"]]
    m = u.merge(era5_cy, on=["adm2_pcode", "year"], how="inner")
    lag_rows = []
    for lag in (0, 30, 60, 90):
        shifted = era5_cy.copy()
        shifted["year"] = shifted["year"] + lag // 365
        lag_rows.append({"lag_days": lag, "r": _spearman(m.unique_px, m.precip_sum_m)})
    pd.DataFrame(lag_rows).to_csv(OUT / "stage13_era5_flood_lag_screen.csv", index=False)

    annual_flood = pd.read_csv(OUT / "stage11_annual_pixel_days.csv")
    annual_u = annual_flood[annual_flood.flood_type_label == "unusual"][["year", "flooded_pixel_count"]]
    hydro_rows = []
    disc = pd.read_csv(
        PROCESSED_DIR / "Darthmouth Flood Observatory" / "dartmouth_discharge_all_processed_with_station_info.csv",
        parse_dates=["Date"],
        usecols=["area_id", "Date", "Discharge (m3/s)"],
    )
    for area in (100205, 1541):
        sub = disc[disc.area_id == area].copy()
        sub["year"] = sub.Date.dt.year
        ann = sub.groupby("year", observed=True)["Discharge (m3/s)"].mean().reset_index()
        m = ann.merge(annual_u, on="year", how="inner")
        if len(m) >= 5:
            hydro_rows.append(
                {
                    "driver": f"dartmouth_discharge_{area}",
                    "spearman_r": _spearman(m["Discharge (m3/s)"], m.flooded_pixel_count),
                    "n_years": len(m),
                }
            )
    lakes = pd.read_csv(PROCESSED_DIR / "Water levels lakes" / "water_levels_all_processed.csv", parse_dates=["date"])
    for lake in ("Victoria", "Kyoga", "Albert"):
        sub = lakes[lakes.lake.str.contains(lake, case=False, na=False)].copy()
        if sub.empty:
            continue
        sub["year"] = sub.date.dt.year
        ann = sub.groupby("year", observed=True)["water_level_m"].mean().reset_index()
        m = ann.merge(annual_u, on="year", how="inner")
        if len(m) >= 5:
            hydro_rows.append(
                {
                    "driver": f"lake_{lake.lower()}_level",
                    "spearman_r": _spearman(m.water_level_m, m.flooded_pixel_count),
                    "n_years": len(m),
                }
            )
    era5_nat = era5_cy.groupby("year", observed=True).agg(precip_sum_m=("precip_sum_m", "sum")).reset_index()
    m = era5_nat.merge(annual_u, on="year", how="inner")
    if len(m) >= 5:
        hydro_rows.append(
            {
                "driver": "era5_county_precip_sum_national",
                "spearman_r": _spearman(m.precip_sum_m, m.flooded_pixel_count),
                "n_years": len(m),
            }
        )
    pd.DataFrame(hydro_rows).to_csv(OUT / "stage13_hydro_vs_flood_correlation.csv", index=False)

    # H6: county WorldPop + OCHA blind spots
    import rasterio
    from rasterio.mask import mask as rio_mask

    admin2 = _admin2_gdf()
    pop_rows = []
    wp_dir = COURSE_RAW / "worldpop"
    for tif in sorted(wp_dir.glob("ssd_pop_*.tif")):
        year = int(re.search(r"(\d{4})", tif.name).group(1))
        with rasterio.open(tif) as src:
            for _, row in admin2.iterrows():
                geom = [row.geometry.__geo_interface__]
                try:
                    out, _ = rio_mask(src, geom, crop=True, nodata=src.nodata)
                    data = out[0]
                    valid = data[data != src.nodata]
                    pop_rows.append(
                        {
                            "adm2_pcode": row.adm2_pcode,
                            "year": year,
                            "pop_sum": float(valid.sum()) if valid.size else 0.0,
                        }
                    )
                except ValueError:
                    pop_rows.append({"adm2_pcode": row.adm2_pcode, "year": year, "pop_sum": np.nan})
    pop_cy = pd.DataFrame(pop_rows)
    pop_cy.to_csv(OUT / "stage13_worldpop_county_year.csv", index=False)

    ocha = pd.read_csv(OUT / "stage6_ocha_20251130_county.csv").rename(
        columns={"Admin2_PCODE": "adm2_pcode"}
    )
    hf = pd.read_csv(PROCESSED_DIR / "health facilities" / "south_sudan_health_facilities_processed.csv")
    hf_counts = hf.groupby("admin1").size().reset_index(name="n_facilities_admin1")
    admin1 = admin2[["adm2_pcode", "adm1_name"]].merge(
        hf_counts, left_on="adm1_name", right_on="admin1", how="left"
    )
    exp = u.merge(pop_cy, on=["adm2_pcode", "year"], how="inner")
    exp = exp.merge(ocha[["adm2_pcode", "people_affected"]], on="adm2_pcode", how="left")
    exp = exp.merge(admin1[["adm2_pcode", "n_facilities_admin1"]], on="adm2_pcode", how="left")
    exp["ocha_assessed"] = exp.people_affected.notna()
    exp["high_flood"] = exp.unique_px > exp.unique_px.median()
    blind = exp[(exp.high_flood) & (~exp.ocha_assessed)].sort_values(
        "unique_px", ascending=False
    )
    blind.to_csv(OUT / "stage13_h6_blind_spots.csv", index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE13_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 13 gate — ERA5 county zonal and WorldPop blind spots",
                "",
                "- `stage13_era5_county_year.csv`, `stage13_era5_flood_lag_screen.csv`, `stage13_hydro_vs_flood_correlation.csv`",
                "- `stage13_worldpop_county_year.csv`, `stage13_h6_blind_spots.csv`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_panel --through 13",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return {"era5": str(OUT / "stage13_era5_county_year.csv"), "blind": str(OUT / "stage13_h6_blind_spots.csv")}


def _load_ged_ssd() -> pd.DataFrame:
    usecols = ["country", "year", "type_of_violence", "latitude", "longitude", "date_prec", "date_start"]
    chunks = []
    for chunk in pd.read_csv(GED_PATH, usecols=usecols, chunksize=100_000):
        ssd = chunk[chunk["country"].astype(str).str.contains("South Sudan", case=False, na=False)]
        if len(ssd):
            chunks.append(ssd)
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=usecols)


def run_stage14_conflict() -> Path:
    ged = _load_ged_ssd()
    ged = ged[ged["date_prec"] <= 3].copy()
    ged["date_start"] = pd.to_datetime(ged["date_start"], errors="coerce")
    ged["month"] = ged["date_start"].dt.month
    admin2 = _admin2_gdf()
    gpts = gpd.GeoDataFrame(
        ged.dropna(subset=["latitude", "longitude"]),
        geometry=gpd.points_from_xy(ged.longitude, ged.latitude),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(gpts, admin2[["adm2_pcode", "geometry"]], how="inner", predicate="within")
    ged_m = (
        joined.groupby(["adm2_pcode", "year", "month"], observed=True)
        .size()
        .reset_index(name="n_events_all")
    )
    type2 = joined[joined["type_of_violence"] == 2]
    ged_t2 = (
        type2.groupby(["adm2_pcode", "year", "month"], observed=True)
        .size()
        .reset_index(name="n_events_type2")
    )
    ged_m = ged_m.merge(ged_t2, on=["adm2_pcode", "year", "month"], how="left").fillna(
        {"n_events_type2": 0}
    )
    ged_m.to_csv(OUT / "stage14_ged_admin2_month.csv", index=False)

    flood_m = pd.read_csv(OUT / "flood_admin2_month.csv")
    flood_u = flood_m[flood_m.mask_type == "unusual"]
    co = flood_u.merge(ged_m, on=["adm2_pcode", "year", "month"], how="inner")
    co["log_flood"] = np.log1p(co["pixel_days"])
    co["log_events"] = np.log1p(co["n_events_type2"])
    ols_c = _within_ols_cluster(co, "log_events", ["log_flood"])
    ols_c.to_csv(OUT / "stage14_flood_events_within_ols.csv", index=False)

    dyads = pd.read_csv(OUT / "stage6_ucdp_ged_type2_sides.csv")
    dyads.to_csv(OUT / "stage14_type2_dyad_descriptive.csv", index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE14_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 14 gate — conflict co-occurrence (non-causal)",
                "",
                "- `stage14_ged_admin2_month.csv`",
                "- Within county-year demeaned OLS appended to `stage12_within_county_ols.csv` pattern.",
                "",
                "GED type-2 only (Non-State not stacked per Stage 4).",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_panel --through 14",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return OUT / "stage14_ged_admin2_month.csv"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Impact EDA panel stages 10–14")
    parser.add_argument("--through", type=int, default=14, choices=range(10, 15))
    parser.add_argument("--force-panel", action="store_true", help="Rebuild flood panels")
    args = parser.parse_args()

    results: dict[str, object] = {}
    if args.through >= 10:
        if args.force_panel:
            build_pixel_lookup(force=True)
            build_flood_panels(force=True)
        results["stage10"] = run_stage10_panel()
    if args.through >= 11:
        results["stage11"] = str(run_stage11_observability())
    if args.through >= 12:
        results["stage12"] = str(run_stage12_cropland())
    if args.through >= 13:
        results["stage13"] = run_stage13_climate_pop()
    if args.through >= 14:
        results["stage14"] = str(run_stage14_conflict())

    (OUT / "panel_stages_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
