"""
Session C — Stages 23–26: conflict seasonality and displacement.

Prerequisites: impact_panel through 14, impact_session_a 17, impact_session_b 19 (flood pixels cache).

Run from repo root:
    python -m archive.impact_eda.impact_session_c --through 26
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial import cKDTree
from processing_data.paths import EXT_DATA, ROOT, ensure_impact_eda_out

from archive.impact_eda.impact_panel import RAIN_MONTHS, _admin2_gdf, _within_ols_cluster
from archive.impact_eda.impact_stages import DTM_R13_16_FILES, _drop_hxl

OUT = ensure_impact_eda_out()
WET_MONTHS = tuple(RAIN_MONTHS)
DRY_MONTHS_T = (11, 12)
DRY_MONTHS_T1 = (1, 2, 3, 4, 5)
PASTORAL_RE = re.compile(r"pastoral|cattle|livestock", re.I)
LHZ_PATH = EXT_DATA / "SS_LHZ_2018" / "SS_LHZ_2018.shp"
GED_CANON = EXT_DATA / "UCDP_georeferenced_and_nonstate" / "ged261-csv" / "GEDEvent_v26_1.csv"
GED_DUP = EXT_DATA / "ACLED_conflict_events" / "ged261-csv" / "GEDEvent_v26_1.csv"


def _spearman(x: pd.Series, y: pd.Series) -> float:
    frame = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(frame) < 5:
        return np.nan
    return float(frame["x"].rank().corr(frame["y"].rank()))


def _pastoral_flag(name: str) -> bool:
    return bool(PASTORAL_RE.search(str(name)))


def run_stage23_joins() -> Path:
    admin2 = _admin2_gdf()
    lhz = gpd.read_file(LHZ_PATH).to_crs("EPSG:4326")
    a_eq = admin2.to_crs("EPSG:6933")
    l_eq = lhz.to_crs("EPSG:6933")
    inter = gpd.overlay(a_eq, l_eq, how="intersection", keep_geom_type=False)
    inter["area_m2"] = inter.geometry.area
    idx = inter.groupby("adm2_pcode", observed=True)["area_m2"].idxmax()
    dom = inter.loc[idx].copy()
    total = inter.groupby("adm2_pcode", observed=True)["area_m2"].sum()
    dom = dom.merge(total.rename("intersect_total_m2"), on="adm2_pcode")
    dom["dominant_share"] = dom["area_m2"] / dom["intersect_total_m2"].replace(0, np.nan)
    out = dom[
        [
            "adm2_pcode",
            "adm2_name",
            "LZCODE",
            "LZNAMEEN",
            "CLASS",
            "dominant_share",
        ]
    ].copy()
    out["pastoral_dominant"] = out["LZNAMEEN"].map(_pastoral_flag)
    out.to_csv(OUT / "stage23_admin2_lhz.csv", index=False)

    dup_note = []
    if GED_DUP.exists() and GED_CANON.exists():
        n_canon = sum(1 for _ in open(GED_CANON, encoding="utf-8", errors="replace")) - 1
        n_dup = sum(1 for _ in open(GED_DUP, encoding="utf-8", errors="replace")) - 1
        dup_note = [
            f"- Canonical GED: `{GED_CANON.relative_to(ROOT)}` (~{n_canon} data rows)",
            f"- `ACLED_conflict_events` copy: ~{n_dup} data rows — **UCDP duplicate, not ACLED event data**.",
            "- Session C uses canonical GED path only.",
        ]
    else:
        dup_note = ["- GED duplicate check skipped (file missing)."]

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE23_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 23 gate — livelihood join and data discipline",
                "",
                "- `stage23_admin2_lhz.csv` — dominant FEWS LHZ 2018 per admin2",
                "- Deferred livestock: eda/DEFERRED_DATASETS.md (AGLW)",
                "",
                *dup_note,
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_c --through 23",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return OUT / "stage23_admin2_lhz.csv"


def _ged_type2_county_month() -> pd.DataFrame:
    cache = OUT / "stage14_ged_admin2_month.csv"
    if cache.exists():
        return pd.read_csv(cache)
    # rebuild minimal if missing
    from archive.impact_eda.impact_panel import run_stage14_conflict

    run_stage14_conflict()
    return pd.read_csv(cache)


def _wet_flood_events_cy() -> pd.DataFrame:
    flood = pd.read_csv(OUT / "flood_admin2_month.csv")
    u = flood[flood.mask_type == "unusual"]
    wet_f = (
        u[u.month.isin(WET_MONTHS)]
        .groupby(["adm2_pcode", "year"], observed=True)["pixel_days"]
        .sum()
        .reset_index(name="wet_flood_pxdays")
    )
    ged = _ged_type2_county_month()
    wet_e = (
        ged[ged.month.isin(WET_MONTHS)]
        .groupby(["adm2_pcode", "year"], observed=True)["n_events_type2"]
        .sum()
        .reset_index(name="wet_type2_events")
    )
    return wet_f.merge(wet_e, on=["adm2_pcode", "year"], how="outer").fillna(0)


def _dry_lead_panel() -> pd.DataFrame:
    ged = _ged_type2_county_month()
    rows = []
    for pcode in ged.adm2_pcode.unique():
        g = ged[ged.adm2_pcode == pcode]
        for year in g.year.unique():
            y = int(year)
            dry_m = list(DRY_MONTHS_T) + list(DRY_MONTHS_T1)
            e_t = g[(g.year == y) & (g.month.isin(DRY_MONTHS_T))]["n_events_type2"].sum()
            e_t1 = g[(g.year == y + 1) & (g.month.isin(DRY_MONTHS_T1))]["n_events_type2"].sum()
            rows.append({"adm2_pcode": pcode, "year": y, "dry_type2_events": e_t + e_t1})
    dry = pd.DataFrame(rows)
    wet = _wet_flood_events_cy()[["adm2_pcode", "year", "wet_flood_pxdays"]]
    return dry.merge(wet, on=["adm2_pcode", "year"], how="inner")


def _apply_spec(df: pd.DataFrame, spec: str, lhz: pd.DataFrame) -> pd.DataFrame:
    sub = df.copy()
    if spec == "pre2022":
        sub = sub[sub.year < 2022]
    elif spec == "pastoral_dominant":
        past = set(lhz.loc[lhz.pastoral_dominant, "adm2_pcode"])
        sub = sub[sub.adm2_pcode.isin(past)]
    elif spec != "all":
        raise ValueError(spec)
    return sub


def _ols_row(spec: str, model: str, ols: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in ols.iterrows():
        rows.append(
            {
                "spec": spec,
                "model": model,
                "term": r["term"],
                "coef": r["coef"],
                "pvalue": r["pvalue"],
                "n": int(r["n"]),
            }
        )
    return rows


def run_stage24_h8() -> Path:
    lhz = pd.read_csv(OUT / "stage23_admin2_lhz.csv")
    wet_cy = _wet_flood_events_cy()
    dry_cy = _dry_lead_panel()
    out_rows: list[dict] = []
    join_n: list[dict] = []

    for spec in ("all", "pastoral_dominant", "pre2022"):
        w = _apply_spec(wet_cy, spec, lhz)
        d = _apply_spec(dry_cy, spec, lhz)
        join_n.append({"spec": spec, "model": "wet_concurrent", "n": len(w)})
        join_n.append({"spec": spec, "model": "dry_lead", "n": len(d)})
        w = w.copy()
        w["log_events"] = np.log1p(w["wet_type2_events"])
        w["log_flood"] = np.log1p(w["wet_flood_pxdays"])
        ols_w = _within_ols_cluster(w, "log_events", ["log_flood"])
        out_rows.extend(_ols_row(spec, "wet_concurrent", ols_w))
        d = d.copy()
        d["log_events"] = np.log1p(d["dry_type2_events"])
        d["log_flood"] = np.log1p(d["wet_flood_pxdays"])
        ols_d = _within_ols_cluster(d, "log_events", ["log_flood"])
        out_rows.extend(_ols_row(spec, "dry_lead", ols_d))

    pd.DataFrame(join_n).to_csv(OUT / "stage24_join_counts.csv", index=False)
    out_p = OUT / "stage24_h8_seasonal_ols.csv"
    pd.DataFrame(out_rows).to_csv(out_p, index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE24_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 24 gate — H8 wet vs dry-lead (SC-H1)",
                "",
                f"- `{out_p.name}` — wet months {WET_MONTHS} concurrent; dry Nov–May lead",
                f"- `stage24_join_counts.csv`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_c --through 24",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return out_p


def _load_dtm_sites() -> pd.DataFrame:
    mob = EXT_DATA / "IOM_DTM_mobility"
    frames = []
    for rnd, filename in DTM_R13_16_FILES.items():
        path = mob / filename
        xl = pd.ExcelFile(path)
        sheet = next(s for s in xl.sheet_names if "Loc_Dataset" in s)
        header = pd.read_excel(path, sheet_name=sheet, nrows=0)
        usecols = [
            c
            for c in header.columns
            if c in {"County_INT_PCode", "latitude", "longitude", "a_idp_inds_ssd"}
            or str(c).endswith(("_ind_disaster", "_ind_conflict", "_ind_clashes"))
        ]
        df = pd.read_excel(path, sheet_name=sheet, usecols=usecols)
        df = _drop_hxl(df)
        df["dtm_round"] = rnd
        frames.append(df)
    all_sites = pd.concat(frames, ignore_index=True)
    dis_cols = [c for c in all_sites.columns if str(c).endswith("_ind_disaster")]
    con_cols = [c for c in all_sites.columns if str(c).endswith("_ind_conflict")]
    cla_cols = [c for c in all_sites.columns if str(c).endswith("_ind_clashes")]
    all_sites["disaster_arr"] = 0.0
    all_sites["conflict_arr"] = 0.0
    for cols, name in [(dis_cols, "disaster_arr"), (con_cols, "conflict_arr"), (cla_cols, "conflict_arr")]:
        for col in cols:
            all_sites[name] = all_sites[name] + pd.to_numeric(all_sites[col], errors="coerce").fillna(0)
    all_sites["latitude"] = pd.to_numeric(all_sites["latitude"], errors="coerce")
    all_sites["longitude"] = pd.to_numeric(all_sites["longitude"], errors="coerce")
    return all_sites


def _flood_pts_2022_24() -> np.ndarray:
    pix = pd.read_csv(OUT / "stage19_flood_pixels_all_years.csv")
    sub = pix[(pix.mask_type == "unusual") & (pix.year >= 2022) & (pix.year <= 2024)]
    return np.column_stack([sub["lon_k"].astype(float), sub["lat_k"].astype(float)])


def _nearest_km(lon: float, lat: float, tree: cKDTree, flood_xy: np.ndarray) -> float:
    dist_deg, idx = tree.query([lon, lat], k=1)
    flon, flat = flood_xy[idx]
    dlat = np.radians(flat - lat)
    dlon = np.radians(flon - lon)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat)) * np.cos(np.radians(flat)) * np.sin(dlon / 2) ** 2
    return float(6371.0 * 2 * np.arcsin(np.sqrt(a)))


def run_stage25_h7() -> Path:
    sites = _load_dtm_sites()
    xy = sites.dropna(subset=["latitude", "longitude"]).copy()
    flood_xy = _flood_pts_2022_24()
    if len(flood_xy) == 0:
        raise FileNotFoundError("No unusual flood pixels 2022–2024; run session B stage 19")
    tree = cKDTree(flood_xy)
    xy["dist_km_nearest_unusual_flood"] = [
        _nearest_km(r.longitude, r.latitude, tree, flood_xy) for r in xy.itertuples()
    ]
    xy["any_disaster"] = xy["disaster_arr"] > 0
    xy["any_conflict"] = xy["conflict_arr"] > 0
    xy.to_csv(OUT / "stage25_dtm_site_distances.csv", index=False)

    dis = xy[xy.any_disaster]["dist_km_nearest_unusual_flood"]
    con = xy[xy.any_conflict & ~xy.any_disaster]["dist_km_nearest_unusual_flood"]
    if len(con) == 0:
        con = xy[xy.any_conflict]["dist_km_nearest_unusual_flood"]
    mw_p = np.nan
    if len(dis) > 5 and len(con) > 5:
        mw_p = float(stats.mannwhitneyu(dis, con, alternative="less").pvalue)

    summary = pd.DataFrame(
        [
            {
                "n_sites_xy": len(xy),
                "n_disaster_tag": int(xy.any_disaster.sum()),
                "n_conflict_tag": int(xy.any_conflict.sum()),
                "median_km_disaster": float(dis.median()) if len(dis) else np.nan,
                "median_km_conflict": float(con.median()) if len(con) else np.nan,
                "mannwhitney_dis_lt_con_p": mw_p,
            }
        ]
    )
    summary.to_csv(OUT / "stage25_dtm_distance_summary.csv", index=False)

    # County disaster share vs flood
    admin2 = pd.read_csv(OUT / "crosswalks/admin2_names.csv") if (OUT / "crosswalks/admin2_names.csv").exists() else None
    xy["County_INT_PCode"] = xy["County_INT_PCode"].astype(str).str.strip()
    if "a_idp_inds_ssd" in xy.columns:
        xy["a_idp_inds_ssd"] = pd.to_numeric(xy["a_idp_inds_ssd"], errors="coerce").fillna(0)
    else:
        xy["a_idp_inds_ssd"] = 0.0
    county = xy.groupby("County_INT_PCode", observed=True).agg(
        disaster_arr=("disaster_arr", "sum"),
        conflict_arr=("conflict_arr", "sum"),
        idp_stock=("a_idp_inds_ssd", "sum"),
        n_sites=("dist_km_nearest_unusual_flood", "size"),
    )
    county["disaster_share"] = county["disaster_arr"] / (
        county["disaster_arr"] + county["conflict_arr"] + 1e-9
    )
    flood_y = pd.read_csv(OUT / "flood_admin2_year.csv")
    u = flood_y[(flood_y.mask_type == "unusual") & (flood_y.year >= 2022) & (flood_y.year <= 2024)]
    u_mean = u.groupby("adm2_pcode", observed=True)["unique_px"].mean().reset_index(name="mean_unusual_px")
    county = county.reset_index().rename(columns={"County_INT_PCode": "adm2_pcode"})
    cm = county.merge(u_mean, on="adm2_pcode", how="inner")
    r_dis = _spearman(cm["disaster_share"], cm["mean_unusual_px"])
    r_stock = _spearman(cm["idp_stock"], cm["mean_unusual_px"])
    pd.DataFrame(
        [
            {
                "spearman_disaster_share_vs_flood": r_dis,
                "spearman_idp_stock_vs_flood": r_stock,
                "n_counties": len(cm),
            }
        ]
    ).to_csv(OUT / "stage25_county_disaster_vs_flood.csv", index=False)
    cm.to_csv(OUT / "stage25_county_dtm_flood.csv", index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE25_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 25 gate — H7 DTM distances (SC-H2)",
                "",
                "- Distances use sites with lat/lon (primarily R16); R13–R15 lack coordinates.",
                f"- Mann-Whitney disaster closer than conflict: p={mw_p}",
                "",
                "- `stage25_dtm_site_distances.csv`",
                "- `stage25_dtm_distance_summary.csv`",
                "- `stage25_county_disaster_vs_flood.csv`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_c --through 25",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return OUT / "stage25_dtm_site_distances.csv"


def _h8_sc1_verdict() -> str:
    ols = pd.read_csv(OUT / "stage24_h8_seasonal_ols.csv")
    w = ols[(ols.spec == "all") & (ols.model == "wet_concurrent") & ols.term.str.contains("flood")]
    d = ols[(ols.spec == "all") & (ols.model == "dry_lead") & ols.term.str.contains("flood")]
    if w.empty or d.empty:
        return "broken test"
    wc, wp, dc, dp = float(w.coef.iloc[0]), float(w.pvalue.iloc[0]), float(d.coef.iloc[0]), float(d.pvalue.iloc[0])
    if wc < 0 and wp < 0.05 and dc > 0 and dp < 0.05:
        return "supported"
    if wc < 0 and dc > 0:
        return "tentative"
    return "falsified"


def write_session_c_closeout() -> Path:
    h8 = _h8_sc1_verdict()
    summ = pd.read_csv(OUT / "stage25_dtm_distance_summary.csv").iloc[0]
    cf = pd.read_csv(OUT / "stage25_county_disaster_vs_flood.csv").iloc[0]
    med_d = summ["median_km_disaster"]
    med_c = summ["median_km_conflict"]
    sc2 = (
        "supported"
        if med_d < med_c and cf["spearman_disaster_share_vs_flood"] > 0
        else "tentative"
        if med_d < med_c
        else "falsified"
    )
    path = ROOT / "archive" / "impact_eda" / "sessions" / "SESSION_C_CLOSEOUT.md"
    lines = [
        "# Session C close-out — conflict seasonality and displacement",
        "",
        "## 1. What was tested",
        "",
        "- **SC-H1:** wet-season (months 6–10) concurrent flood vs type-2; dry-window lead (`stage24_h8_seasonal_ols.csv`).",
        "- **SC-H2:** DTM site distance to unusual flood 2022–2024; county disaster share vs flood (`stage25_*.csv`).",
        "- **Joins:** FEWS LHZ 2018 dominant zone per county (`stage23_admin2_lhz.csv`).",
        "",
        "## 2. Outcomes",
        "",
        f"- **SC-H1:** **{h8}** (see wet_concurrent and dry_lead coefs for spec=all).",
        f"- **SC-H2:** median km disaster={med_d:.1f}, conflict={med_c:.1f}; "
        f"county disaster-share vs flood Spearman={cf['spearman_disaster_share_vs_flood']:.3f} — **{sc2}**.",
        "",
        "## 3. Issues remaining",
        "",
        "- DTM disaster bucket is not flood-only (Stage 2 gate).",
        "- Distance analysis needs coordinates (R16-heavy).",
        "- AGLW livestock not available — see `DEFERRED_DATASETS.md`.",
        "- Post-2020 flood regime may affect wet/dry splits.",
        "",
        "## 4. Branch decision",
        "",
        f"- **Seasonal conflict mechanism:** "
        + (
            "CUT full reversal narrative; keep weak wet-season association only (pastoral/pre2022)."
            if h8 == "falsified"
            else "TENTATIVE — wet negative, dry-lead positive not significant at spec=all; no causal claim."
            if h8 == "tentative"
            else "KEEP cautious seasonal framing."
        ),
        "- **Session D (joint crop×conflict):** HOLD (SC-H1 not fully supported).",
        "- **Livelihood zones:** KEEP for exposure stratification in maps (Session B product).",
        "",
        "## 5. External data ask",
        "",
        "| Dataset | Grain | Gap | Unblocks | Search prompt |",
        "|---------|-------|-----|----------|---------------|",
        "| AGLW gridded livestock 1961–2021 | raster, annual | No pasture pressure time series | H8 dry-season control | `FAO AGLW download cattle South Sudan` |",
        "| Event-level ACLED (optional) | geo events | Folder duplicate is UCDP only | Cattle-raid coding | `ACLED South Sudan export API` |",
        "| CHIRPS/NDVI | monthly raster | Calendar vs detection | Crop session only | `HDX CHIRPS South Sudan` |",
        "",
        "## 6. Next-session prompt",
        "",
        "```text",
        "Session D only if SESSION_C_CLOSEOUT SC-H1 supported: co-location maps of stage21_exposure_product",
        "and seasonal conflict pattern — no combined causal model (Stage 8 no_go).",
        "Otherwise: finalize capstone synthesis using exposure product + descriptive conflict/flood co-occurrence.",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_stage26_figures_and_closeout() -> dict:
    write_session_c_closeout()
    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE26_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 26 gate — Session C figures and close-out",
                "",
                "- `session_c_figures.ipynb` → `figures/session_c/`",
                "- `SESSION_C_CLOSEOUT.md`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_c --through 26",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return {"closeout": str(ROOT / "archive" / "impact_eda" / "sessions" / "SESSION_C_CLOSEOUT.md")}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Session C stages 23–26")
    parser.add_argument("--through", type=int, default=26, choices=range(23, 27))
    args = parser.parse_args()

    results: dict[str, object] = {}
    if args.through >= 23:
        results["stage23"] = str(run_stage23_joins())
    if args.through >= 24:
        results["stage24"] = str(run_stage24_h8())
    if args.through >= 25:
        results["stage25"] = str(run_stage25_h7())
    if args.through >= 26:
        results["stage26"] = run_stage26_figures_and_closeout()

    (OUT / "session_c_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
