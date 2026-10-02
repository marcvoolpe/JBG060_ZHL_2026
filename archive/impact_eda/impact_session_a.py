"""
Session A — Stages 15–18: measurement integrity (crop/conflict EDA series).

Prerequisites: `python -m archive.impact_eda.impact_panel --through 14`

Run from repo root:
    python -m archive.impact_eda.impact_session_a --through 18
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

from archive.impact_eda.impact_panel import (
    H2_BASELINE_END,
    HARVEST_MONTHS,
    PLANT_MONTHS,
    _admin2_gdf,
    _coord_keys,
    _era5_grid_to_counties,
    _fews_ha,
    _flood_parquet_paths,
    _parse_flood_dates,
    _within_ols_cluster,
    build_flood_panels,
    build_pixel_lookup,
)

OUT = ensure_impact_eda_out()
CROSS = OUT / "crosswalks"
BASELINE_END = H2_BASELINE_END
WORLDPOP_YEARS = range(2015, 2026)


def _coverage() -> pd.DataFrame:
    cov = pd.read_csv(OUT / "flood_tile_coverage_admin2.csv")
    return cov[["adm2_pcode", "flood_tile_coverage_share"]]


def _build_harvest_panel() -> pd.DataFrame:
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
    baseline = (
        u[(u.year >= 2000) & (u.year <= BASELINE_END)]
        .groupby("adm2_pcode", observed=True)["unusual_px"]
        .mean()
        .rename("unusual_baseline_mean")
    )
    panel = panel.merge(baseline, on="adm2_pcode", how="left")
    panel["unusual_baseline_mean"] = panel["unusual_baseline_mean"].fillna(1.0).clip(lower=1.0)
    panel["log_unusual_anomaly"] = np.log1p(panel["unusual_px"].fillna(0) / panel["unusual_baseline_mean"])
    panel = panel.merge(_coverage(), on="adm2_pcode", how="left")
    return panel


def _build_seasonal_panel() -> pd.DataFrame:
    month = pd.read_csv(OUT / "flood_admin2_month.csv")
    fews = _fews_ha()
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
    seasonal = plant.add_suffix("_plant").join(harv.add_suffix("_harvest"), how="outer").reset_index()
    seasonal = seasonal.merge(fews, on=["adm2_pcode", "year"], how="inner")
    seasonal["log_ha"] = np.log1p(seasonal["ha_harvested"])
    if "unusual_plant" not in seasonal.columns:
        return seasonal
    seasonal["log_u_plant"] = np.log1p(seasonal["unusual_plant"].fillna(0))
    seasonal["log_u_harv"] = np.log1p(seasonal["unusual_harvest"].fillna(0))
    u_y = pd.read_csv(OUT / "flood_admin2_year.csv")
    u_only = u_y[u_y.mask_type == "unusual"][["adm2_pcode", "year", "unique_px"]]
    baseline_p = (
        month[(month.mask_type == "unusual") & (month.month.isin(PLANT_MONTHS))]
        .groupby(["adm2_pcode", "year"], observed=True)["pixel_days"]
        .sum()
        .reset_index()
    )
    baseline_h = (
        month[(month.mask_type == "unusual") & (month.month.isin(HARVEST_MONTHS))]
        .groupby(["adm2_pcode", "year"], observed=True)["pixel_days"]
        .sum()
        .reset_index()
    )
    bl_p = (
        baseline_p[(baseline_p.year >= 2000) & (baseline_p.year <= BASELINE_END)]
        .groupby("adm2_pcode", observed=True)["pixel_days"]
        .mean()
        .rename("plant_baseline")
    )
    bl_h = (
        baseline_h[(baseline_h.year >= 2000) & (baseline_h.year <= BASELINE_END)]
        .groupby("adm2_pcode", observed=True)["pixel_days"]
        .mean()
        .rename("harv_baseline")
    )
    seasonal = seasonal.merge(bl_p, on="adm2_pcode", how="left").merge(bl_h, on="adm2_pcode", how="left")
    seasonal["plant_baseline"] = seasonal["plant_baseline"].fillna(1.0).clip(lower=1.0)
    seasonal["harv_baseline"] = seasonal["harv_baseline"].fillna(1.0).clip(lower=1.0)
    seasonal["log_u_plant_anom"] = np.log1p(seasonal["unusual_plant"].fillna(0) / seasonal["plant_baseline"])
    seasonal["log_u_harv_anom"] = np.log1p(seasonal["unusual_harvest"].fillna(0) / seasonal["harv_baseline"])
    seasonal = seasonal.merge(_coverage(), on="adm2_pcode", how="left")
    return seasonal


def _filter_spec(df: pd.DataFrame, spec: str) -> pd.DataFrame:
    if spec == "full":
        return df
    if spec == "pre2022":
        return df[df.year < 2022].copy()
    if spec == "anomaly":
        return df
    if spec == "full_cov95":
        return df[df.flood_tile_coverage_share.fillna(0) >= 0.95].copy()
    raise ValueError(spec)


def _h2_xcols(spec: str) -> list[str]:
    return ["log_unusual_anomaly"] if spec == "anomaly" else ["log_unusual"]


def _h3_xcols(spec: str) -> list[str]:
    if spec == "anomaly":
        return ["log_u_plant_anom", "log_u_harv_anom"]
    return ["log_u_plant", "log_u_harv"]


def _append_ols(rows: list[dict], spec: str, ols: pd.DataFrame, hypothesis: str) -> None:
    if ols.empty:
        return
    for _, r in ols.iterrows():
        rows.append(
            {
                "hypothesis": hypothesis,
                "spec": spec,
                "term": r["term"],
                "coef": r["coef"],
                "pvalue": r["pvalue"],
                "n": int(r["n"]),
            }
        )


def run_stage15_robustness() -> Path:
    panel = _build_harvest_panel()
    seasonal = _build_seasonal_panel()
    specs = ("full", "pre2022", "anomaly", "full_cov95")
    h2_rows: list[dict] = []
    h3_rows: list[dict] = []
    join_n: list[dict] = []

    for spec in specs:
        sub = _filter_spec(panel, spec)
        join_n.append({"spec": spec, "grain": "county_year_h2", "n": len(sub)})
        ols = _within_ols_cluster(sub, "log_ha", _h2_xcols(spec))
        _append_ols(h2_rows, spec, ols, "SA-H1")

    for spec in specs:
        sub = _filter_spec(seasonal, spec)
        join_n.append({"spec": spec, "grain": "county_year_h3", "n": len(sub)})
        if "log_u_plant" in sub.columns:
            ols = _within_ols_cluster(sub, "log_ha", _h3_xcols(spec))
            _append_ols(h3_rows, spec, ols, "SA-H2")

    h2_out = OUT / "stage15_h2_robustness.csv"
    h3_out = OUT / "stage15_h3_robustness.csv"
    pd.DataFrame(h2_rows).to_csv(h2_out, index=False)
    pd.DataFrame(h3_rows).to_csv(h3_out, index=False)
    pd.DataFrame(join_n).to_csv(OUT / "stage15_join_counts.csv", index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE15_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 15 gate — H2/H3 robustness (Session A)",
                "",
                "Pre-registered: `SESSION_A_HYPOTHESES.md` (SA-H1, SA-H2).",
                "",
                f"- `{h2_out.name}` — within-county OLS across specs",
                f"- `{h3_out.name}` — seasonal windows (plant 4–6, harvest 9–11)",
                f"- `stage15_join_counts.csv` — n per spec",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_a --through 15",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return h2_out


def _era5_county_month() -> pd.DataFrame:
    cache = OUT / "stage16_era5_county_month.csv"
    if cache.exists():
        return pd.read_csv(cache)
    grid_map = _era5_grid_to_counties().copy()
    rows: list[dict] = []
    rain_dir = COURSE_RAW / "rainfall and runoff"
    sample_path = next(iter(sorted(rain_dir.glob("ERA5_*.nc"))))
    with xr.open_dataset(sample_path) as ds0:
        lat_i = {float(v): i for i, v in enumerate(ds0["latitude"].values)}
        lon_i = {float(v): j for j, v in enumerate(ds0["longitude"].values)}
    gm = grid_map.copy()
    gm["li"] = gm["latitude"].astype(float).map(lat_i)
    gm["lj"] = gm["longitude"].astype(float).map(lon_i)
    gm = gm.dropna(subset=["li", "lj"])
    li = gm["li"].astype(int).values
    lj = gm["lj"].astype(int).values
    for path in sorted(rain_dir.glob("ERA5_*.nc")):
        year = int(re.search(r"ERA5_(\d{4})", path.name).group(1))
        with xr.open_dataset(path) as ds:
            tp = ds["tp"]
            times = pd.to_datetime(tp["valid_time"].values)
            month_coord = times.month
            tp = tp.assign_coords(month=("valid_time", month_coord))
            monthly = tp.groupby("month").sum("valid_time")
            for month in range(1, 13):
                if month not in set(monthly["month"].values):
                    continue
                slab = monthly.sel(month=month).values
                gm_m = gm.copy()
                gm_m["precip_sum_m"] = slab[li, lj]
                agg = gm_m.groupby("adm2_pcode", observed=True)["precip_sum_m"].sum()
                for pcode, precip in agg.items():
                    rows.append(
                        {"adm2_pcode": pcode, "year": year, "month": month, "precip_sum_m": float(precip)}
                    )
    out = pd.DataFrame(rows)
    out.to_csv(cache, index=False)
    return out


def _national_monthly_hydro() -> pd.DataFrame:
    cache = OUT / "stage16_hydro_monthly.csv"
    if cache.exists():
        return pd.read_csv(cache)

    frames: list[pd.DataFrame] = []
    disc = pd.read_csv(
        PROCESSED_DIR / "Darthmouth Flood Observatory" / "dartmouth_discharge_all_processed_with_station_info.csv",
        parse_dates=["Date"],
        usecols=["area_id", "Date", "Discharge (m3/s)"],
    )
    sub = disc[disc.area_id == 1541].copy()
    sub["year"] = sub.Date.dt.year
    sub["month"] = sub.Date.dt.month
    d1541 = (
        sub.groupby(["year", "month"], observed=True)["Discharge (m3/s)"]
        .mean()
        .reset_index()
        .rename(columns={"Discharge (m3/s)": "dartmouth_1541"})
    )
    frames.append(d1541)

    lakes = pd.read_csv(
        PROCESSED_DIR / "Water levels lakes" / "water_levels_all_processed.csv",
        parse_dates=["date"],
    )
    vic = lakes[lakes.lake.str.contains("Victoria", case=False, na=False)].copy()
    vic["year"] = vic.date.dt.year
    vic["month"] = vic.date.dt.month
    vlev = (
        vic.groupby(["year", "month"], observed=True)["water_level_m"]
        .mean()
        .reset_index()
        .rename(columns={"water_level_m": "lake_victoria"})
    )
    frames.append(vlev)

    hydro = d1541.merge(vlev, on=["year", "month"], how="outer")
    hydro.to_csv(cache, index=False)
    return hydro


def _spearman(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    frame = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(frame) < 30:
        return np.nan, len(frame)
    r = float(frame["x"].rank().corr(frame["y"].rank()))
    return r, len(frame)


def run_stage16_lags() -> Path:
    flood_m = pd.read_csv(OUT / "flood_admin2_month.csv")
    flood_u = flood_m[flood_m.mask_type == "unusual"].copy()
    flood_u["log_pixel_days"] = np.log1p(flood_u["pixel_days"])

    era5_cm = _era5_county_month()
    hydro = _national_monthly_hydro()

    base = flood_u.merge(era5_cm, on=["adm2_pcode", "year", "month"], how="inner")
    base = base.merge(hydro, on=["year", "month"], how="left")

    hydro_sorted = hydro.sort_values(["year", "month"]).reset_index(drop=True)
    hydro_lagged: dict[tuple[int, str], pd.DataFrame] = {}
    for lag in (0, 1, 2, 3):
        hlag = hydro_sorted.copy()
        for hcol in ("dartmouth_1541", "lake_victoria"):
            hlag[f"{hcol}_v"] = hlag[hcol].shift(lag)
        hydro_lagged[(lag, "hydro")] = hlag[["year", "month", "dartmouth_1541_v", "lake_victoria_v"]].rename(
            columns={"dartmouth_1541_v": "dartmouth_1541", "lake_victoria_v": "lake_victoria"}
        )

    lag_rows: list[dict] = []
    for period, filt in (("full", lambda d: d), ("pre2022", lambda d: d[d.year <= 2021])):
        sub = filt(base).copy()
        sub = sub.sort_values(["adm2_pcode", "year", "month"])
        for lag in (0, 1, 2, 3):
            sub[f"precip_lag{lag}"] = sub.groupby("adm2_pcode", observed=True)["precip_sum_m"].shift(lag)
            r, n = _spearman(sub[f"precip_lag{lag}"], sub["log_pixel_days"])
            lag_rows.append(
                {
                    "driver": "era5_county_precip",
                    "lag_months": lag,
                    "period": period,
                    "spearman_r": r,
                    "n": n,
                    "grain": "county_month",
                }
            )
            sub_h = sub.drop(columns=["dartmouth_1541", "lake_victoria"], errors="ignore").merge(
                hydro_lagged[(lag, "hydro")], on=["year", "month"], how="left"
            )
            for hcol, label in (("dartmouth_1541", "dartmouth_1541"), ("lake_victoria", "lake_victoria")):
                r, n = _spearman(sub_h["log_pixel_days"], sub_h[hcol])
                lag_rows.append(
                    {
                        "driver": label,
                        "lag_months": lag,
                        "period": period,
                        "spearman_r": r,
                        "n": n,
                        "grain": "county_month",
                    }
                )

    out_p = OUT / "stage16_monthly_lag_correlations.csv"
    pd.DataFrame(lag_rows).to_csv(out_p, index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE16_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 16 gate — H5 lag repair (Session A)",
                "",
                "County-month unusual `pixel_days` vs lagged ERA5 precip and national hydro (1541, Victoria).",
                "",
                f"- `stage16_era5_county_month.csv` (cache)",
                f"- `stage16_hydro_monthly.csv` (cache)",
                f"- `{out_p.name}`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_a --through 16",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return out_p


def _county_health_facilities() -> pd.DataFrame:
    cache = OUT / "stage17_health_facilities_admin2.csv"
    if cache.exists():
        return pd.read_csv(cache)
    hf = pd.read_csv(PROCESSED_DIR / "health facilities" / "south_sudan_health_facilities_processed.csv")
    gdf_hf = gpd.GeoDataFrame(
        hf.dropna(subset=["latitude", "longitude"]),
        geometry=gpd.points_from_xy(hf.longitude, hf.latitude),
        crs="EPSG:4326",
    )
    admin2 = _admin2_gdf()
    joined = gpd.sjoin(gdf_hf, admin2[["adm2_pcode", "geometry"]], how="inner", predicate="within")
    counts = joined.groupby("adm2_pcode", observed=True).size().reset_index(name="n_facilities_county")
    counts.to_csv(cache, index=False)
    return counts


def _flood_pixels_county_year() -> pd.DataFrame:
    """Unique unusual-flood pixel keys per county-year (for WorldPop sampling)."""
    cache = OUT / "stage17_unusual_pixels_county_year.csv"
    if cache.exists():
        return pd.read_csv(cache)

    lookup = pd.read_csv(build_pixel_lookup())
    by_mask_year: dict[tuple[str, int], list[Path]] = defaultdict(list)
    for mask_type, year, _tile, path in _flood_parquet_paths():
        if mask_type != "unusual":
            continue
        by_mask_year[(mask_type, year)].append(path)

    rows: list[pd.DataFrame] = []
    for (_mask, year), files in sorted(by_mask_year.items()):
        if year not in WORLDPOP_YEARS:
            continue
        parts = [pd.read_parquet(p, columns=["lat", "lon"]) for p in files]
        if not parts:
            continue
        df = pd.concat(parts, ignore_index=True)
        df = _coord_keys(df)
        df = df.merge(lookup, on=["lat_k", "lon_k"], how="inner")
        uniq = df[["adm2_pcode", "lat_k", "lon_k"]].drop_duplicates()
        uniq["year"] = year
        rows.append(uniq)
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    out.to_csv(cache, index=False)
    return out


def _flood_exposed_population() -> pd.DataFrame:
    cache = OUT / "stage17_flood_exposed_pop_county_year.csv"
    if cache.exists():
        return pd.read_csv(cache)

    import rasterio

    pixels = _flood_pixels_county_year()
    wp_dir = COURSE_RAW / "worldpop"
    pop_rows: list[dict] = []
    for year in WORLDPOP_YEARS:
        tifs = list(wp_dir.glob(f"ssd_pop_{year}*.tif"))
        if not tifs:
            continue
        tif = tifs[0]
        pts = pixels[pixels.year == year]
        if pts.empty:
            continue
        coords = list(zip(pts["lon_k"].astype(float), pts["lat_k"].astype(float)))
        with rasterio.open(tif) as src:
            samples = [v[0] for v in src.sample(coords)]
        pts = pts.copy()
        pts["pop_cell"] = samples
        pts["pop_cell"] = pts["pop_cell"].where(pts["pop_cell"] != src.nodata, 0.0).fillna(0.0)
        agg = pts.groupby("adm2_pcode", observed=True)["pop_cell"].sum().reset_index()
        agg["year"] = year
        agg = agg.rename(columns={"pop_cell": "flood_exposed_pop"})
        pop_rows.extend(agg.to_dict("records"))

    out = pd.DataFrame(pop_rows)
    out.to_csv(cache, index=False)
    return out


def run_stage17_h6() -> Path:
    exposed = _flood_exposed_population()
    hf = _county_health_facilities()
    ocha = pd.read_csv(OUT / "stage6_ocha_20251130_county.csv").rename(
        columns={"Admin2_PCODE": "adm2_pcode"}
    )
    ocha_cols = ocha[["adm2_pcode", "people_affected"]].copy()

    # Latest unusual year per county for snapshot join (20251130 same-season proxy: use 2024/2025 flood year)
    exp = exposed.copy()
    exp = exp.merge(ocha_cols, on="adm2_pcode", how="left")
    exp = exp.merge(hf, on="adm2_pcode", how="left")
    exp["n_facilities_county"] = exp["n_facilities_county"].fillna(0)
    exp["ocha_assessed"] = exp["people_affected"].notna()
    exp.to_csv(OUT / "stage17_exposure_ocha_panel.csv", index=False)

    reg_rows: list[dict] = []
    assessed = exp[exp.ocha_assessed & exp["people_affected"].notna()].copy()
    assessed = assessed[assessed.year == assessed.year.max()] if len(assessed) else assessed
    # Use max year available per county for cross-section with OCHA snapshot
    snap = (
        exp.sort_values("year")
        .groupby("adm2_pcode", observed=True)
        .tail(1)
        .dropna(subset=["flood_exposed_pop"])
    )
    assessed_snap = snap[snap.ocha_assessed & snap.people_affected.notna()].copy()
    if len(assessed_snap) >= 10:
        y = np.log1p(assessed_snap["people_affected"].astype(float))
        X = sm.add_constant(np.log1p(assessed_snap["flood_exposed_pop"].astype(float)))
        m = sm.OLS(y, X).fit()
        for term, coef, pval in zip(m.params.index, m.params, m.pvalues):
            reg_rows.append(
                {
                    "model": "ocha_affected_log_vs_exposed_pop",
                    "term": term,
                    "coef": float(coef),
                    "pvalue": float(pval),
                    "n": len(assessed_snap),
                }
            )

    miss = snap.copy()
    miss["ocha_assessed_int"] = miss.ocha_assessed.astype(int)
    if len(miss) >= 20:
        X = sm.add_constant(
            pd.DataFrame(
                {
                    "log_exposed": np.log1p(miss["flood_exposed_pop"].astype(float)),
                    "n_facilities": miss["n_facilities_county"].astype(float),
                }
            )
        )
        m = sm.Logit(miss["ocha_assessed_int"], X).fit(disp=0)
        for term, coef, pval in zip(m.params.index, m.params, m.pvalues):
            reg_rows.append(
                {
                    "model": "ocha_assessed_logit",
                    "term": term,
                    "coef": float(coef),
                    "pvalue": float(pval),
                    "n": len(miss),
                }
            )

    reg_out = OUT / "stage17_h6_regressions.csv"
    pd.DataFrame(reg_rows).to_csv(reg_out, index=False)

    blind = snap[(snap.flood_exposed_pop > snap.flood_exposed_pop.median()) & (~snap.ocha_assessed)]
    blind = blind.sort_values("flood_exposed_pop", ascending=False)
    blind.to_csv(OUT / "stage17_h6_blind_spots_exposed_pop.csv", index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE17_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 17 gate — flood ∩ WorldPop (Session A)",
                "",
                f"- `stage17_flood_exposed_pop_county_year.csv`",
                f"- `stage17_exposure_ocha_panel.csv`",
                f"- `{reg_out.name}`",
                f"- `stage17_h6_blind_spots_exposed_pop.csv`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_a --through 17",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return reg_out


def write_session_a_closeout() -> Path:
    """Populate close-out from artefacts (call after stages 15–17)."""
    h2 = pd.read_csv(OUT / "stage15_h2_robustness.csv")
    h3 = pd.read_csv(OUT / "stage15_h3_robustness.csv")
    lags = pd.read_csv(OUT / "stage16_monthly_lag_correlations.csv")
    reg = pd.read_csv(OUT / "stage17_h6_regressions.csv") if (OUT / "stage17_h6_regressions.csv").exists() else pd.DataFrame()

    def _sig_h2() -> bool:
        terms = h2[h2.term.str.contains("unusual|anom", case=False, regex=True)]
        return bool((terms.pvalue < 0.05).any())

    def _harv_pre2022() -> tuple[float, float]:
        sub = h3[(h3.spec == "pre2022") & (h3.term.str.contains("harv", case=False))]
        sub_f = h3[(h3.spec == "full") & (h3.term.str.contains("harv", case=False))]
        p_pre = float(sub.pvalue.iloc[0]) if len(sub) else np.nan
        p_full = float(sub_f.pvalue.iloc[0]) if len(sub_f) else np.nan
        return p_pre, p_full

    hydro_best = lags[lags.driver != "era5_county_precip"].copy()
    hydro_best = hydro_best.loc[hydro_best["spearman_r"].abs().idxmax()] if len(hydro_best) else None
    rain_best = lags[lags.driver == "era5_county_precip"].copy()
    rain_best = rain_best.loc[rain_best["spearman_r"].abs().idxmax()] if len(rain_best) else None

    miss_p = np.nan
    if len(reg):
        logit = reg[(reg.model == "ocha_assessed_logit") & (reg.term == "log_exposed")]
        if len(logit):
            miss_p = float(logit.pvalue.iloc[0])

    path = ROOT / "archive" / "impact_eda" / "sessions" / "SESSION_A_CLOSEOUT.md"
    lines = [
        "# Session A close-out — measurement integrity",
        "",
        "## 1. What was tested",
        "",
        "- **SA-H1 (H2 robustness):** county-year FEWS × unusual flood; specs `full`, `pre2022`, `anomaly`, `full_cov95`. See `stage15_join_counts.csv`.",
        "- **SA-H2 (H3 seasonal):** planting 4–6 vs harvest 9–11 unusual pixel-days; same specs.",
        "- **SA-H3 (H5 lags):** county-month unusual pixel-days vs ERA5 precip and national 1541 / Victoria at 0–3 month lags; `full` vs `pre2022`.",
        "- **SA-H4 (H6):** WorldPop at unusual flood pixels → `flood_exposed_pop`; OCHA 20251130 assessed regression and missingness logit with county facility counts.",
        "",
        "## 2. Outcomes",
        "",
        f"- **SA-H1:** {'tentative negative within-county signal in at least one spec' if _sig_h2() else '**falsified** for loss language — no spec yields significant negative unusual term at p<0.05'}.",
        f"- **SA-H2:** harvest-window p full = **{_harv_pre2022()[1]:.4f}**, pre2022 = **{_harv_pre2022()[0]:.4f}** — "
        f"{'**tentative** (survives pre-2022 cut; dry-season detection caveat)' if _harv_pre2022()[0] < 0.05 else 'falsified or weakened in pre2022'}.",
        f"- **SA-H3:** best |Spearman| hydro ≈ **{hydro_best['spearman_r'] if hydro_best is not None else 'n/a'}** ({hydro_best['driver'] if hydro_best is not None else ''}, lag {hydro_best['lag_months'] if hydro_best is not None else ''}); "
        f"best county precip ≈ **{rain_best['spearman_r'] if rain_best is not None else 'n/a'}**.",
        f"- **SA-H4:** missingness logit `log_exposed` p = **{miss_p:.4f}** (`stage17_h6_regressions.csv`).",
        "",
        "## 3. Issues remaining",
        "",
        "- Post-2020 unusual mask regime jump; `cloud_frac` still unusable.",
        "- OCHA snapshot is cross-sectional; exposed pop is county-year panel — alignment is approximate.",
        "- Stage 16 ERA5 extraction is heavy; cached in `stage16_era5_county_month.csv`.",
        "",
        "## 4. Branch decision",
        "",
        f"- **Crop exposure (Session B):** KEEP exposure-only (annual H2 null); "
        f"{'KEEP tentative harvest-window calendar branch' if _harv_pre2022()[0] < 0.05 else 'CUT harvest-window claims'}.",
        f"- **Hydro lead-time (Session B):** {'CUT forecast narrative' if hydro_best is not None and rain_best is not None and abs(rain_best['spearman_r']) >= abs(hydro_best['spearman_r']) else 'KEEP tentative hydro branch'}.",
        f"- **Assessment gap (Session B/C):** {'KEEP' if miss_p < 0.1 else 'CUT inferential bias; KEEP descriptive blind-spot map'}.",
        "- **Conflict seasonality (Session C):** KEEP scheduled — H7/H8 not run in A.",
        "",
        "## 5. External data ask",
        "",
        "| Dataset | Grain | Gap | Unblocks | Search prompt |",
        "|---------|-------|-----|----------|---------------|",
        "| FEWS livelihood zones | payam/county static | Toic vs upland crop interpretation | Exposure stratification without loss claims | `FEWS NET South Sudan livelihood zones shapefile` |",
        "| CHIRPS or NDVI (MODIS) | monthly raster | Sep–Nov flood timing vs crop phenology | Test H3 without trusting flood detection month | `HDX South Sudan CHIRPS precipitation` |",
        "| Recent livestock density | county raster >2015 | Cattle raster ~2010 for H8 pasture pressure | Session C seasonal conflict covariate | `FAO Gridded Livestock South Sudan` |",
        "",
        "## 6. Next-session prompt",
        "",
        "```text",
        "Implement Session B (cropland exposure and calendar) per SESSION_A_CLOSEOUT.md branch decisions.",
        "Read: eda/SESSION_A_CLOSEOUT.md, eda/SESSION_PROTOCOL.md, stage15–17 CSVs in eda/outputs/impact_eda/.",
        "Do not reopen: ASAP Manyo/Renk artefact; combined crop+conflict model (Stage 8 no_go).",
        "Figures: argued exposure overlays; skip harvest-loss language if SA-H1 falsified.",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_stage18_figures_and_closeout() -> dict:
    write_session_a_closeout()
    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE18_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 18 gate — Session A figures and close-out",
                "",
                "- Notebook: `session_a_figures.ipynb` → `figures/session_a/`",
                "- Close-out: `SESSION_A_CLOSEOUT.md`",
                "",
                "Execute notebook after stages 15–17:",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_a --through 18",
                "jupyter nbconvert --execute archive/impact_eda/notebooks/session_a_figures.ipynb",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return {"closeout": str(ROOT / "archive" / "impact_eda" / "sessions" / "SESSION_A_CLOSEOUT.md")}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Session A stages 15–18")
    parser.add_argument("--through", type=int, default=18, choices=range(15, 19))
    args = parser.parse_args()

    results: dict[str, object] = {}
    if args.through >= 15:
        results["stage15"] = str(run_stage15_robustness())
    if args.through >= 16:
        results["stage16"] = str(run_stage16_lags())
    if args.through >= 17:
        results["stage17"] = str(run_stage17_h6())
    if args.through >= 18:
        results["stage18"] = run_stage18_figures_and_closeout()

    (OUT / "session_a_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
