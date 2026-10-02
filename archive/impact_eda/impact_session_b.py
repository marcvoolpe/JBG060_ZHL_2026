"""
Session B — Stages 19–22: cropland exposure and calendar falsification.

Prerequisites: `python -m archive.impact_eda.impact_panel --through 14`, `python -m archive.impact_eda.impact_session_a --through 17`

Run from repo root:
    python -m archive.impact_eda.impact_session_b --through 22
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from processing_data.paths import COURSE_RAW, ROOT, ensure_impact_eda_out

from archive.impact_eda.impact_panel import (
    HARVEST_MONTHS,
    PLANT_MONTHS,
    _coord_keys,
    _fews_ha,
    _flood_parquet_paths,
    _within_ols_cluster,
    build_pixel_lookup,
)

OUT = ensure_impact_eda_out()


def _coverage() -> pd.DataFrame:
    cov = pd.read_csv(OUT / "flood_tile_coverage_admin2.csv")
    return cov[["adm2_pcode", "flood_tile_coverage_share"]]


def _spearman(x: pd.Series, y: pd.Series) -> float:
    frame = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(frame) < 5:
        return np.nan
    return float(frame["x"].rank().corr(frame["y"].rank()))


def _estimate_pixel_area_km2(sample_lats: np.ndarray, sample_lons: np.ndarray) -> float:
    """Approximate flood-pixel cell area from median spacing (degrees → km)."""
    lats = np.sort(np.unique(sample_lats))
    lons = np.sort(np.unique(sample_lons))
    if len(lats) < 2 or len(lons) < 2:
        return np.nan
    dlat = float(np.median(np.diff(lats)))
    dlon = float(np.median(np.diff(lons)))
    mid_lat = float(np.median(lats))
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * np.cos(np.radians(mid_lat))
    return dlat * km_per_deg_lat * dlon * km_per_deg_lon


def _flood_pixels_all_years(force: bool = False) -> pd.DataFrame:
    cache = OUT / "stage19_flood_pixels_all_years.csv"
    if cache.exists() and not force:
        return pd.read_csv(cache)

    lookup = pd.read_csv(build_pixel_lookup())
    by_mask_year: dict[tuple[str, int], list[Path]] = defaultdict(list)
    for mask_type, year, _tile, path in _flood_parquet_paths():
        by_mask_year[(mask_type, year)].append(path)

    frames: list[pd.DataFrame] = []
    for (mask_type, year), files in sorted(by_mask_year.items()):
        parts = [pd.read_parquet(p, columns=["lat", "lon"]) for p in files]
        df = pd.concat(parts, ignore_index=True)
        df = _coord_keys(df)
        df = df.merge(lookup, on=["lat_k", "lon_k"], how="inner")
        uniq = df[["adm2_pcode", "lat_k", "lon_k"]].drop_duplicates()
        uniq["mask_type"] = mask_type
        uniq["year"] = int(year)
        frames.append(uniq)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    out.to_csv(cache, index=False)
    return out


def _asap_values_at_coords(coords_df: pd.DataFrame) -> pd.DataFrame:
    import rasterio

    crop_tif = COURSE_RAW / "farmland" / "asap_mask_crop_v04.tif"
    range_tif = COURSE_RAW / "farmland" / "asap_mask_rangeland_v04.tif"
    uniq = coords_df[["lat_k", "lon_k"]].drop_duplicates()
    coord_list = list(zip(uniq["lon_k"].astype(float), uniq["lat_k"].astype(float)))
    with rasterio.open(crop_tif) as src:
        crop_s = [v[0] for v in src.sample(coord_list)]
        nodata_c = src.nodata
    with rasterio.open(range_tif) as src:
        range_s = [v[0] for v in src.sample(coord_list)]
        nodata_r = src.nodata
    uniq = uniq.copy()
    uniq["crop_pct"] = pd.to_numeric(crop_s, errors="coerce")
    uniq["range_pct"] = pd.to_numeric(range_s, errors="coerce")
    if nodata_c is not None:
        uniq.loc[uniq["crop_pct"] == nodata_c, "crop_pct"] = np.nan
    if nodata_r is not None:
        uniq.loc[uniq["range_pct"] == nodata_r, "range_pct"] = np.nan
    uniq["crop_pct"] = uniq["crop_pct"].fillna(0.0)
    uniq["range_pct"] = uniq["range_pct"].fillna(0.0)
    return uniq


def run_stage19_exposure(force_pixels: bool = False) -> Path:
    pix = _flood_pixels_all_years(force=force_pixels)
    asap_lut = _asap_values_at_coords(pix)
    merged = pix.merge(asap_lut, on=["lat_k", "lon_k"], how="left")
    merged["crop_unit"] = merged["crop_pct"] / 100.0
    merged["range_unit"] = merged["range_pct"] / 100.0

    area_km2 = _estimate_pixel_area_km2(merged["lat_k"].values, merged["lon_k"].values)

    agg = (
        merged.groupby(["adm2_pcode", "year", "mask_type"], observed=True)
        .agg(
            n_flood_pixels=("lat_k", "count"),
            crop_exposed_units=("crop_unit", "sum"),
            range_exposed_units=("range_unit", "sum"),
        )
        .reset_index()
    )
    agg = agg.merge(_coverage(), on="adm2_pcode", how="left")
    agg["low_tile_coverage"] = agg["flood_tile_coverage_share"].fillna(0) < 0.95
    agg["crop_share"] = agg["crop_exposed_units"] / (
        agg["crop_exposed_units"] + agg["range_exposed_units"] + 1e-9
    )
    agg.to_csv(OUT / "stage19_crop_exposure_county_year.csv", index=False)

    comp_rows: list[dict] = []
    u = agg[agg.mask_type == "unusual"]
    r = agg[agg.mask_type == "recurring"]
    pair = u.merge(r, on=["adm2_pcode", "year"], suffixes=("_u", "_r"))
    comp_rows.append(
        {
            "metric": "mean_crop_share_unusual",
            "value": float(u["crop_share"].mean()),
            "n_county_years": len(u),
        }
    )
    comp_rows.append(
        {
            "metric": "mean_crop_share_recurring",
            "value": float(r["crop_share"].mean()),
            "n_county_years": len(r),
        }
    )
    if len(pair):
        comp_rows.append(
            {
                "metric": "paired_mean_diff_crop_share_u_minus_r",
                "value": float((pair["crop_share_u"] - pair["crop_share_r"]).mean()),
                "n_county_years": len(pair),
            }
        )
    comp_rows.append({"metric": "approx_pixel_area_km2", "value": area_km2, "n_county_years": np.nan})
    pd.DataFrame(comp_rows).to_csv(OUT / "stage19_exposure_composition.csv", index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE19_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 19 gate — ASAP crop/rangeland at flood pixels",
                "",
                f"- Approx. pixel area from coord spacing: **{area_km2:.4f} km²** (documented; not used to scale units).",
                "- Exposure units = sum of ASAP %/100 at unique flood pixels per county-year-mask.",
                "",
                "- `stage19_flood_pixels_all_years.csv`",
                "- `stage19_crop_exposure_county_year.csv`",
                "- `stage19_exposure_composition.csv` (SB-H1)",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_b --through 19",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return OUT / "stage19_crop_exposure_county_year.csv"


def _seasonal_pixel_sums(mask_type: str, months: tuple[int, ...]) -> pd.DataFrame:
    month = pd.read_csv(OUT / "flood_admin2_month.csv")
    sub = month[(month.mask_type == mask_type) & (month.month.isin(months))]
    return (
        sub.groupby(["adm2_pcode", "year"], observed=True)
        .agg(pixel_days=("pixel_days", "sum"), obs_days=("obs_days", "sum"))
        .reset_index()
    )


def _county_peak_rain_month() -> pd.Series:
    era5 = pd.read_csv(OUT / "stage16_era5_county_month.csv")
    clim = era5[(era5.year >= 2000) & (era5.year <= 2021)]
    idx = clim.groupby("adm2_pcode", observed=True)["precip_sum_m"].idxmax()
    peaks = clim.loc[idx, ["adm2_pcode", "month"]].set_index("adm2_pcode")["month"]
    return peaks


def _months_window(center: int, start_off: int, end_off: int) -> tuple[int, ...]:
    out = []
    for off in range(start_off, end_off + 1):
        m = ((center - 1 + off) % 12) + 1
        out.append(int(m))
    return tuple(sorted(set(out)))


def _rain_defined_seasonal(mask_type: str) -> pd.DataFrame:
    peaks = _county_peak_rain_month()
    month = pd.read_csv(OUT / "flood_admin2_month.csv")
    sub = month[month.mask_type == mask_type].copy()

    plant_parts: list[pd.DataFrame] = []
    harv_parts: list[pd.DataFrame] = []
    for pcode, peak in peaks.items():
        pm = int(peak)
        p_months = set(_months_window(pm, -2, 0))
        h_months = set(_months_window(pm, 3, 5))
        s = sub[sub.adm2_pcode == pcode]
        if s.empty:
            continue
        plant_parts.append(s[s.month.isin(p_months)])
        harv_parts.append(s[s.month.isin(h_months)])

    plant = (
        pd.concat(plant_parts, ignore_index=True)
        .groupby(["adm2_pcode", "year"], observed=True)["pixel_days"]
        .sum()
        .reset_index(name="plant_px")
    )
    harv = (
        pd.concat(harv_parts, ignore_index=True)
        .groupby(["adm2_pcode", "year"], observed=True)["pixel_days"]
        .sum()
        .reset_index(name="harv_px")
    )
    return plant.merge(harv, on=["adm2_pcode", "year"], how="outer")


def _detection_share_harvest(mask_type: str = "unusual") -> pd.DataFrame:
    month = pd.read_csv(OUT / "flood_admin2_month.csv")
    sub = month[(month.mask_type == mask_type) & (month.month.isin(HARVEST_MONTHS))]
    cy = (
        sub.groupby(["adm2_pcode", "year"], observed=True)
        .agg(obs_days=("obs_days", "sum"), pixel_days=("pixel_days", "sum"))
        .reset_index()
    )
    cy["detection_share_harvest"] = cy["obs_days"] / cy["pixel_days"].replace(0, np.nan)
    return cy[["adm2_pcode", "year", "detection_share_harvest"]]


def _run_calendar_ols(
    panel: pd.DataFrame,
    plant_col: str,
    harv_col: str,
    spec: str,
    test_id: str,
) -> list[dict]:
    sub = panel.copy()
    if spec == "pre2022":
        sub = sub[sub.year < 2022]
    sub["log_ha"] = np.log1p(sub["ha_harvested"])
    sub[f"log_{plant_col}"] = np.log1p(sub[plant_col].fillna(0))
    sub[f"log_{harv_col}"] = np.log1p(sub[harv_col].fillna(0))
    x_cols = [f"log_{plant_col}", f"log_{harv_col}"]
    if "detection_share_harvest" in sub.columns:
        sub["log_det"] = np.log1p(sub["detection_share_harvest"].fillna(0))
        x_cols.append("log_det")
    ols = _within_ols_cluster(sub, "log_ha", x_cols)
    rows = []
    for _, r in ols.iterrows():
        rows.append(
            {
                "test_id": test_id,
                "spec": spec,
                "term": r["term"],
                "coef": r["coef"],
                "pvalue": r["pvalue"],
                "n": int(r["n"]),
            }
        )
    return rows


def run_stage20_falsification() -> Path:
    fews = _fews_ha()
    rows: list[dict] = []

    # Baseline unusual fixed windows (replication)
    month = pd.read_csv(OUT / "flood_admin2_month.csv")
    u_plant = _seasonal_pixel_sums("unusual", PLANT_MONTHS).rename(columns={"pixel_days": "u_plant"})
    u_harv = _seasonal_pixel_sums("unusual", HARVEST_MONTHS).rename(columns={"pixel_days": "u_harv"})
    base = u_plant.merge(u_harv, on=["adm2_pcode", "year"]).merge(fews, on=["adm2_pcode", "year"])

    for spec in ("full", "pre2022"):
        rows.extend(_run_calendar_ols(base, "u_plant", "u_harv", spec, "unusual_fixed"))

    # Recurring placebo
    r_plant = _seasonal_pixel_sums("recurring", PLANT_MONTHS).rename(columns={"pixel_days": "r_plant"})
    r_harv = _seasonal_pixel_sums("recurring", HARVEST_MONTHS).rename(columns={"pixel_days": "r_harv"})
    placebo = r_plant.merge(r_harv, on=["adm2_pcode", "year"]).merge(fews, on=["adm2_pcode", "year"])
    for spec in ("full", "pre2022"):
        rows.extend(_run_calendar_ols(placebo, "r_plant", "r_harv", spec, "recurring_placebo"))

    # Rain-defined windows (unusual)
    rain = _rain_defined_seasonal("unusual")
    rain = rain.merge(fews, on=["adm2_pcode", "year"], how="inner")
    for spec in ("full", "pre2022"):
        rows.extend(_run_calendar_ols(rain, "plant_px", "harv_px", spec, "rain_defined_unusual"))

    # Detection control
    det = _detection_share_harvest("unusual")
    ctrl = base.merge(det, on=["adm2_pcode", "year"], how="left")
    for spec in ("full", "pre2022"):
        rows.extend(_run_calendar_ols(ctrl, "u_plant", "u_harv", spec, "unusual_fixed_plus_detection"))

    out_p = OUT / "stage20_calendar_falsification.csv"
    pd.DataFrame(rows).to_csv(out_p, index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE20_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 20 gate — calendar falsification (SB-H2)",
                "",
                f"- `{out_p.name}` — unusual fixed, recurring placebo, rain-defined, detection control",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_b --through 20",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return out_p


def run_stage21_product() -> Path:
    crop = pd.read_csv(OUT / "stage19_crop_exposure_county_year.csv")
    crop_u = crop[crop.mask_type == "unusual"][
        ["adm2_pcode", "year", "crop_exposed_units", "range_exposed_units", "n_flood_pixels", "low_tile_coverage"]
    ]
    pop_path = OUT / "stage17_flood_exposed_pop_county_year.csv"
    if not pop_path.exists():
        raise FileNotFoundError("Run Session A stage 17 first for flood_exposed_pop")
    pop = pd.read_csv(pop_path)
    prod = crop_u.merge(pop, on=["adm2_pcode", "year"], how="outer")
    prod = prod.merge(_coverage(), on="adm2_pcode", how="left")
    ocha = pd.read_csv(OUT / "stage6_ocha_20251130_county.csv").rename(columns={"Admin2_PCODE": "adm2_pcode"})
    prod = prod.merge(ocha[["adm2_pcode", "people_affected"]], on="adm2_pcode", how="left")
    prod["ocha_assessed"] = prod["people_affected"].notna()
    prod["post_2020_regime"] = prod["year"] >= 2022

    overlap = prod.dropna(subset=["crop_exposed_units", "flood_exposed_pop"])
    rho = _spearman(overlap["crop_exposed_units"], overlap["flood_exposed_pop"])

    for col in ("crop_exposed_units", "range_exposed_units", "flood_exposed_pop"):
        prod[f"pct_{col}"] = prod[col].rank(pct=True)

    prod.to_csv(OUT / "stage21_exposure_product.csv", index=False)
    pd.DataFrame(
        [{"spearman_crop_vs_pop": rho, "n_overlap": len(overlap), "redundant_if_rho_gt": 0.9}]
    ).to_csv(OUT / "stage21_exposure_redundancy.csv", index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE21_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 21 gate — joint exposure product",
                "",
                f"- Spearman crop vs pop exposure: **{rho:.3f}** (n={len(overlap)})",
                "- `stage21_exposure_product.csv`, `stage21_exposure_redundancy.csv`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_b --through 21",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return OUT / "stage21_exposure_product.csv"


def write_session_b_closeout() -> Path:
    comp = pd.read_csv(OUT / "stage19_exposure_composition.csv")
    fals = pd.read_csv(OUT / "stage20_calendar_falsification.csv")
    red = pd.read_csv(OUT / "stage21_exposure_redundancy.csv")

    diff = comp.loc[comp.metric == "paired_mean_diff_crop_share_u_minus_r", "value"]
    diff_v = float(diff.iloc[0]) if len(diff) else np.nan
    rho = float(red["spearman_crop_vs_pop"].iloc[0])

    def harv_p(test_id: str, spec: str) -> float:
        sub = fals[(fals.test_id == test_id) & (fals.spec == spec)]
        sub = sub[sub.term.str.contains("harv", case=False)]
        return float(sub.pvalue.iloc[0]) if len(sub) else np.nan

    path = ROOT / "archive" / "impact_eda" / "sessions" / "SESSION_B_CLOSEOUT.md"
    lines = [
        "# Session B close-out — cropland exposure and calendar",
        "",
        "## 1. What was tested",
        "",
        "- **SB-H1:** crop vs rangeland share at flood pixels, unusual vs recurring (`stage19_exposure_composition.csv`).",
        "- **SB-H2:** calendar falsification — recurring placebo, rain-defined windows, detection control (`stage20_calendar_falsification.csv`).",
        "- **SB-H3:** redundancy of crop vs population exposure (`stage21_exposure_redundancy.csv`).",
        "",
        "## 2. Outcomes",
        "",
        f"- **SB-H1:** paired mean crop-share unusual − recurring = **{diff_v:.4f}** "
        f"({'unusual lower crop share' if diff_v < 0 else 'not rangeland-heavy'}).",
        f"- **SB-H2:** unusual fixed harvest p (pre2022) = **{harv_p('unusual_fixed', 'pre2022'):.4f}**; "
        f"recurring placebo harvest p (pre2022) = **{harv_p('recurring_placebo', 'pre2022'):.4f}**; "
        f"rain-defined harvest p (pre2022) = **{harv_p('rain_defined_unusual', 'pre2022'):.4f}**; "
        f"with detection control = **{harv_p('unusual_fixed_plus_detection', 'pre2022'):.4f}**.",
        f"- **SB-H3:** Spearman crop vs pop = **{rho:.3f}** "
        f"({'redundant — one layer may suffice' if rho > 0.9 else 'joint product justified'}).",
        "",
        "## 3. Issues remaining",
        "",
        "- ASAP static; exposure units are pixel-sum of %, not hectares.",
        "- Rain-defined windows depend on ERA5 county zonal climatology.",
        "- Harvest-calendar claims still subject to dry-season detection artefact (Session A).",
        "",
        "## 4. Branch decision",
        "",
        "- **Exposure deliverable:** KEEP `stage21_exposure_product.csv` for ZOA/ZHL maps.",
        "- **Harvest-calendar narrative:** "
        + (
            "TENTATIVE — unusual-specific (placebo clean) but weakened by rain-defined windows; do not use for loss claims."
            if harv_p("rain_defined_unusual", "pre2022") >= 0.05
            else "KEEP cautious calendar wording."
        ),
        "- **Session C (conflict):** KEEP scheduled (H7/H8).",
        "- **Session D (joint):** HOLD unless Session C produces seasonal pattern.",
        "",
        "## 5. External data ask",
        "",
        "| Dataset | Grain | Gap | Unblocks | Search prompt |",
        "|---------|-------|-----|----------|---------------|",
        "| FEWS livelihood zones | static vector | Toic vs upland without loss claims | Stratify exposure maps | `FEWS NET South Sudan livelihood zones shapefile` |",
        "| CHIRPS or MODIS NDVI | monthly raster | Phenology vs flood-detection month | Definitive SB-H2 test | `HDX South Sudan CHIRPS precipitation` |",
        "| Recent livestock density | raster >2015 | Pasture pressure for H8 | Session C covariate | `FAO Gridded Livestock South Sudan` |",
        "",
        "## 6. Next-session prompt",
        "",
        "```text",
        "Implement Session C (conflict seasonality and displacement) per SESSION_PROTOCOL.md.",
        "Read: SESSION_B_CLOSEOUT.md, stage14 outputs, SESSION_A close-out.",
        "Run H8 wet/dry sign reversal on GED type-2; H7 DTM distance-to-flood by arrival reason.",
        "Do not stack GED type-2 + Non-State; DTM disaster tag is outcome only.",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_stage22_figures_and_closeout() -> dict:
    write_session_b_closeout()
    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE22_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 22 gate — Session B figures and close-out",
                "",
                "- Notebook: `session_b_figures.ipynb` → `figures/session_b/`",
                "- Close-out: `SESSION_B_CLOSEOUT.md`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_b --through 22",
                "# then execute session_b_figures.ipynb",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return {"closeout": str(ROOT / "archive" / "impact_eda" / "sessions" / "SESSION_B_CLOSEOUT.md")}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Session B stages 19–22")
    parser.add_argument("--through", type=int, default=22, choices=range(19, 23))
    parser.add_argument("--force-pixels", action="store_true", help="Rebuild stage19 pixel cache")
    args = parser.parse_args()

    results: dict[str, object] = {}
    if args.through >= 19:
        results["stage19"] = str(run_stage19_exposure(force_pixels=args.force_pixels))
    if args.through >= 20:
        results["stage20"] = str(run_stage20_falsification())
    if args.through >= 21:
        results["stage21"] = str(run_stage21_product())
    if args.through >= 22:
        results["stage22"] = run_stage22_figures_and_closeout()

    (OUT / "session_b_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
