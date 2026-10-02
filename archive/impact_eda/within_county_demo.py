"""
Within-county demo for the proposed RO: does a county's flood severity *this year*,
relative to its own usual level, line up with its displacement *this year*?

Builds the county-year table (severity from the course flood masks, DTM disaster
arrivals, OCHA people affected), each county's usual level (average of its other
years, on a log scale), the deviation from it, and a category per county-year.
Descriptive only: no inference is drawn here.

Run from repo root:
    python -m archive.impact_eda.within_county_demo            # reuses the severity cache if present
    python -m archive.impact_eda.within_county_demo --force    # rebuild severity from the parquets
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from processing_data.paths import COURSE_RAW, EXT_DATA, ensure_impact_eda_out

from archive.impact_eda.impact_panel import _coord_keys, _flood_parquet_paths, build_pixel_lookup
from archive.impact_eda.impact_stages import DTM_R13_16_FILES, _drop_hxl

OUT = ensure_impact_eda_out()
FIG_DIR = OUT / "figures" / "within_county_demo"
SEVERITY_YEARS = range(2021, 2026)
# First DTM round collected after each flood season:
# R14 Mar-Apr 2023, R15 Jul-Sep 2024, R16 Dec 2024-Feb 2025
DTM_FIRST_ROUND = {2022: 14, 2023: 15, 2024: 16}
OCHA_FILES = {
    2021: ("ss_floodsaffected_people_20211213.xlsx", "Sheet1", None, "County", "Affected People"),
    2022: (
        "ssd_flood_response_301122.xlsx",
        "As of November 2022",
        "P code",
        "County",
        "Assessed number of flood-affected people",
    ),
    2024: ("ssd_flood_response_20122024.xlsx", "Floods_affected_People", "Admin2_Pcode", "Admin2", "People_Affected"),
    2025: (
        "ss_people_affected_and_displaced_by_floods_20251130.xlsx",
        "Summary",
        "Admin2_PCODE",
        "Admin2",
        "People affected",
    ),
}
PIXEL_DEG = 1 / 480  # MODIS 232 m grid spacing in degrees
MIN_COVERAGE = 0.95
USUAL_BAND = np.log(1.25)  # "about usual" = within a factor 1.25 either way (-20% to +25%)
N_BOOT = 2000

# Reference palette (dataviz skill): slots 1-2 validated, gray for context marks
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, OTHER = "#e1e0d9", "#c3c2b7", "#c3c2b7"
SERIES = ("#2a78d6", "#eb6834")


def _norm(s: object) -> str:
    return re.sub(r"[^a-z]", "", str(s).lower())


def _spearman(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    frame = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(frame) < 5:
        return np.nan, len(frame)
    return float(frame["x"].rank().corr(frame["y"].rank())), len(frame)


# ---------------------------------------------------------------- inputs


def _dekad_codes(dates: pd.Series) -> np.ndarray:
    """Dekad of the year (0-35) per row, parsed once per distinct date."""
    if not isinstance(dates.dtype, pd.CategoricalDtype):
        dates = dates.astype("category")
    cats = pd.to_datetime(dates.cat.categories.astype(str))
    dek = (cats.month.to_numpy() - 1) * 3 + np.minimum((cats.day.to_numpy() - 1) // 10, 2)
    return dek[dates.cat.codes.to_numpy()]


def _severity_county_year(force: bool = False) -> pd.DataFrame:
    """Extent, pixel-dekads and mean dekads wet per admin2-year, both mask classes combined."""
    cache = OUT / "demo_severity_county_year.csv"
    if cache.exists() and not force:
        return pd.read_csv(cache)

    lookup = pd.read_csv(build_pixel_lookup())
    by_year: dict[int, list[pd.DataFrame]] = {}
    for _kind, year, _tile, path in _flood_parquet_paths():
        if year not in SEVERITY_YEARS:
            continue
        df = pd.read_parquet(path, columns=["date", "lat", "lon"])
        df = df[["lat", "lon"]].assign(dekad=_dekad_codes(df["date"])).drop_duplicates()
        by_year.setdefault(year, []).append(df)

    frames = []
    for year, parts in sorted(by_year.items()):
        px = _coord_keys(pd.concat(parts, ignore_index=True))
        px = px.drop_duplicates(subset=["lat_k", "lon_k", "dekad"])
        px = px.merge(lookup, on=["lat_k", "lon_k"], how="inner")
        per_px = px.groupby(["adm2_pcode", "lat_k", "lon_k"], as_index=False).agg(dekads=("dekad", "size"))
        per_px["area_km2"] = (PIXEL_DEG * 111.32) ** 2 * np.cos(np.radians(per_px["lat_k"]))
        per_px["px_dekad_km2"] = per_px["dekads"] * per_px["area_km2"]
        agg = per_px.groupby("adm2_pcode", as_index=False).agg(
            extent_km2=("area_km2", "sum"),
            extent_x_duration=("px_dekad_km2", "sum"),
        )
        agg["mean_dekads_wet"] = agg["extent_x_duration"] / agg["extent_km2"]
        agg["year"] = year
        frames.append(agg)
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(cache, index=False)
    return out


def _dtm_disaster_by_round() -> pd.DataFrame:
    """Disaster-displaced IDPs still present per county, by arrival year and DTM round."""
    frames = []
    for rnd in sorted(set(DTM_FIRST_ROUND.values())):
        path = EXT_DATA / "IOM_DTM_mobility" / DTM_R13_16_FILES[rnd]
        sheet = next(s for s in pd.ExcelFile(path).sheet_names if "Loc_Dataset" in s)
        header = pd.read_excel(path, sheet_name=sheet, nrows=0)
        year_cols = {f"e_idp_arrival_{y}_ind_disaster": y for y in range(2021, 2025)}
        usecols = ["County_INT_PCode"] + [c for c in header.columns if c in year_cols]
        df = _drop_hxl(pd.read_excel(path, sheet_name=sheet, usecols=usecols))
        for col in usecols[1:]:
            agg = pd.to_numeric(df[col], errors="coerce").fillna(0).groupby(df["County_INT_PCode"]).sum()
            frames.append(
                pd.DataFrame(
                    {
                        "adm2_pcode": agg.index.astype(str),
                        "year": year_cols[col],
                        "dtm_round": rnd,
                        "disaster_idps": agg.to_numpy(),
                    }
                )
            )
    return pd.concat(frames, ignore_index=True)


def _ocha_affected_county_year() -> pd.DataFrame:
    """OCHA people affected per county-year; unassessed counties stay missing, not zero."""
    admin2 = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson")
    name_map = {_norm(n): p for n, p in zip(admin2["adm2_name"], admin2["adm2_pcode"])}
    xw = pd.read_csv(OUT / "crosswalks" / "admin2_names.csv")
    xw = xw[xw["cod_pcode"].astype(str).str.match(r"^SS\d{4}$")]
    name_map.update({_norm(n): p for n, p in zip(xw["source_name"], xw["cod_pcode"])})

    frames = []
    for year, (fname, sheet, pcode_col, name_col, aff_col) in OCHA_FILES.items():
        path = EXT_DATA / "OCHA_flood_data" / fname
        raw = pd.read_excel(path, sheet_name=sheet, header=None)
        hdr = next(i for i in range(15) if any(_norm(v) == _norm(name_col) for v in raw.iloc[i].to_numpy()))
        df = pd.read_excel(path, sheet_name=sheet, header=hdr)
        acol = next(c for c in df.columns if _norm(c).startswith(_norm(aff_col)))
        ncol = next(c for c in df.columns if _norm(c) == _norm(name_col))
        df["affected"] = pd.to_numeric(df[acol], errors="coerce")
        df = df[df["affected"] > 0]
        pcodes = []
        for _, row in df.iterrows():
            code = None
            if pcode_col:
                for c in df.columns:
                    if _norm(c).startswith(_norm(pcode_col)) and re.match(r"^SS\d{4}$", str(row[c]).strip()):
                        code = str(row[c]).strip()
            pcodes.append(code or name_map.get(_norm(row[ncol])))
        df["adm2_pcode"] = pcodes
        unmatched = df["adm2_pcode"].isna().sum()
        if unmatched:
            print(f"OCHA {year}: {unmatched} rows unmatched ({', '.join(map(str, df.loc[df.adm2_pcode.isna(), ncol]))})")
        agg = df.dropna(subset=["adm2_pcode"]).groupby("adm2_pcode", as_index=False)["affected"].sum()
        agg["year"] = year
        frames.append(agg.rename(columns={"affected": "ocha_affected"}))
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- panel


def _add_deviation(df: pd.DataFrame, col: str, prefix: str) -> pd.DataFrame:
    """Usual level = mean of the county's other years (leave-one-year-out); deviation = this year - usual."""
    g = df.groupby("adm2_pcode")[col]
    count = g.transform("count")
    usual = (g.transform("sum") - df[col]) / (count - 1)
    df[f"{prefix}_usual"] = usual.where(count > 1)
    df[f"{prefix}_dev"] = df[col] - df[f"{prefix}_usual"]
    return df


def _categorise(sev_dev: pd.Series, imp_dev: pd.Series) -> tuple[pd.Series, pd.Series]:
    worse, milder = sev_dev >= USUAL_BAND, sev_dev <= -USUAL_BAND
    up, down = imp_dev >= USUAL_BAND, imp_dev <= -USUAL_BAND
    category = np.select(
        [worse & up, worse & ~up, milder & down, milder & ~down],
        [
            "worse flood, more displaced",
            "worse flood, displacement not up",
            "milder flood, fewer displaced",
            "milder flood, displacement not down",
        ],
        default="flood about usual",
    )
    step = np.select([(worse & up) | (milder & down), worse | milder], ["in step", "out of step"], default="no test")
    missing = sev_dev.isna() | imp_dev.isna()
    return (
        pd.Series(category, index=sev_dev.index).mask(missing),
        pd.Series(step, index=sev_dev.index).mask(missing),
    )


def build_demo_panel(force: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (DTM rows 2022-2024, OCHA rows) with usual levels, deviations and categories."""
    cov = pd.read_csv(OUT / "flood_tile_coverage_admin2.csv")
    well = cov.loc[cov["flood_tile_coverage_share"] >= MIN_COVERAGE, ["adm2_pcode", "adm2_name", "adm1_name"]]
    grid = well.merge(pd.DataFrame({"year": list(SEVERITY_YEARS)}), how="cross")
    panel = grid.merge(_severity_county_year(force), on=["adm2_pcode", "year"], how="left")
    panel[["extent_km2", "extent_x_duration"]] = panel[["extent_km2", "extent_x_duration"]].fillna(0.0)

    dtm = _dtm_disaster_by_round()
    first = pd.DataFrame(list(DTM_FIRST_ROUND.items()), columns=["year", "dtm_round"])
    d_first = dtm.merge(first, on=["year", "dtm_round"]).rename(columns={"disaster_idps": "dtm_disaster_idps"})
    d_r16 = dtm[dtm["dtm_round"] == 16].rename(columns={"disaster_idps": "dtm_r16_disaster_idps"})
    panel = panel.merge(d_first[["adm2_pcode", "year", "dtm_disaster_idps"]], on=["adm2_pcode", "year"], how="left")
    panel = panel.merge(d_r16[["adm2_pcode", "year", "dtm_r16_disaster_idps"]], on=["adm2_pcode", "year"], how="left")
    panel = panel.merge(_ocha_affected_county_year(), on=["adm2_pcode", "year"], how="left")
    for c in ("extent_x_duration", "dtm_disaster_idps", "ocha_affected"):
        panel[f"log_{c}"] = np.log1p(panel[c])
    panel.to_csv(OUT / "within_county_demo_panel.csv", index=False)

    rows_dtm = panel[panel["year"].isin(DTM_FIRST_ROUND) & panel["dtm_disaster_idps"].notna()].copy()
    rows_dtm = _add_deviation(rows_dtm, "log_extent_x_duration", "sev")
    rows_dtm = _add_deviation(rows_dtm, "log_dtm_disaster_idps", "imp")
    rows_dtm["category"], rows_dtm["step"] = _categorise(rows_dtm["sev_dev"], rows_dtm["imp_dev"])
    rows_dtm.to_csv(OUT / "within_county_demo_dtm_rows.csv", index=False)

    # OCHA: deviations over the years each county was actually assessed
    rows_ocha = panel[panel["ocha_affected"].notna()].copy()
    rows_ocha = _add_deviation(rows_ocha, "log_extent_x_duration", "sev")
    rows_ocha = _add_deviation(rows_ocha, "log_ocha_affected", "imp")
    rows_ocha["category"], rows_ocha["step"] = _categorise(rows_ocha["sev_dev"], rows_ocha["imp_dev"])
    rows_ocha.to_csv(OUT / "within_county_demo_ocha_rows.csv", index=False)
    return rows_dtm, rows_ocha


def _bootstrap_within(rows: pd.DataFrame, seed: int = 0) -> tuple[float, float]:
    """95% interval for the within-county Spearman, resampling whole counties."""
    rng = np.random.default_rng(seed)
    groups = [g for _, g in rows.dropna(subset=["sev_dev", "imp_dev"]).groupby("adm2_pcode")]
    stats = []
    for _ in range(N_BOOT):
        pick = rng.integers(0, len(groups), len(groups))
        sample = pd.concat([groups[i] for i in pick], ignore_index=True)
        stats.append(_spearman(sample["sev_dev"], sample["imp_dev"])[0])
    lo, hi = np.nanpercentile(stats, [2.5, 97.5])
    return float(lo), float(hi)


def summarise(rows: pd.DataFrame, impact_log_col: str) -> dict:
    valid = rows.dropna(subset=["sev_dev", "imp_dev"])
    pooled, n_pooled = _spearman(rows["log_extent_x_duration"], rows[impact_log_col])
    within, n_within = _spearman(valid["sev_dev"], valid["imp_dev"])
    lo, hi = _bootstrap_within(valid)
    per_year = {int(y): _spearman(g["sev_dev"], g["imp_dev"])[0] for y, g in valid.groupby("year")}
    return {
        "n_counties": int(valid["adm2_pcode"].nunique()),
        "n_county_years": int(n_within),
        "pooled_spearman": round(pooled, 3),
        "pooled_n": int(n_pooled),
        "within_spearman": round(within, 3),
        "within_ci95": [round(lo, 3), round(hi, 3)],
        "within_by_year": {k: round(v, 3) for k, v in per_year.items()},
        "steps": valid["step"].value_counts().to_dict(),
        "categories": valid["category"].value_counts().to_dict(),
    }


def pick_examples(rows: pd.DataFrame, top_n: int = 12) -> tuple[pd.Series, pd.Series]:
    """Stated rule: among the top_n most flood-affected counties (usual severity) with arrivals in
    all 3 years, A = most 'in step' years, B = most 'out of step' years (ties -> higher usual severity).
    Ranking on severity, not displacement, keeps arrival hubs such as Juba out of the candidates."""
    per = (
        rows.groupby(["adm2_pcode", "adm2_name", "adm1_name"])
        .agg(
            usual_sev=("log_extent_x_duration", "mean"),
            years_with_arrivals=("dtm_disaster_idps", lambda s: int((s > 0).sum())),
            in_step=("step", lambda s: int((s == "in step").sum())),
            out_step=("step", lambda s: int((s == "out of step").sum())),
        )
        .reset_index()
    )
    cand = per[per["years_with_arrivals"] == 3].nlargest(top_n, "usual_sev")
    a = cand.sort_values(["in_step", "usual_sev"], ascending=False).iloc[0]
    b = cand[cand["adm2_pcode"] != a["adm2_pcode"]].sort_values(["out_step", "usual_sev"], ascending=False).iloc[0]
    return a, b


# ---------------------------------------------------------------- figures


def _style(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=AXIS, labelcolor=INK2, labelsize=8.5, length=0, pad=4)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _log1p_ticks(ax: plt.Axes, axis: str, values: list[float]) -> None:
    ticks = [np.log1p(v) for v in values]
    labels = [f"{v:,.0f}" for v in values]
    if axis == "x":
        ax.set_xticks(ticks, labels)
    else:
        ax.set_yticks(ticks, labels)


def _ratio_ticks(ax: plt.Axes, axis: str, ratios: list[float]) -> None:
    ticks = [np.log(r) for r in ratios]
    labels = ["usual" if r == 1 else f"{(r - 1) * 100:+.0f}%" for r in ratios]
    if axis == "x":
        ax.set_xticks(ticks, labels)
    else:
        ax.set_yticks(ticks, labels)


def plot_pooled_vs_within(rows: pd.DataFrame, examples: tuple[pd.Series, pd.Series], stats: dict) -> Path:
    plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.0), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ex_codes = {e["adm2_pcode"] for e in examples}
    valid = rows.dropna(subset=["sev_dev", "imp_dev"])

    # Left: every county-year pooled; a county's three years joined by a thin strand
    _style(ax1)
    for code, g in rows.groupby("adm2_pcode"):
        if code in ex_codes:
            continue
        g = g.sort_values("year")
        ax1.plot(g["log_extent_x_duration"], g["log_dtm_disaster_idps"], color=OTHER, lw=0.7, zorder=1)
        ax1.scatter(g["log_extent_x_duration"], g["log_dtm_disaster_idps"], s=10, color=OTHER, zorder=1)
    # Right: each county-year against the county's own usual level
    _style(ax2)
    ax2.axvspan(-USUAL_BAND, USUAL_BAND, color=GRID, alpha=0.6, lw=0, zorder=0)
    ax2.axhline(0, color=AXIS, lw=0.8, zorder=1)
    ax2.axvline(0, color=AXIS, lw=0.8, zorder=1)
    others = valid[~valid["adm2_pcode"].isin(ex_codes)]
    lim = np.log(12)
    ax2.scatter(others["sev_dev"].clip(-lim, lim), others["imp_dev"].clip(-lim, lim), s=12, color=OTHER, zorder=2)

    for ex, color in zip(examples, SERIES):
        g = rows[rows["adm2_pcode"] == ex["adm2_pcode"]].sort_values("year")
        label = f"{ex['adm2_name']} ({ex['adm1_name']})"
        ax1.plot(g["log_extent_x_duration"], g["log_dtm_disaster_idps"], color=color, lw=1.6, zorder=3)
        ax1.scatter(
            g["log_extent_x_duration"], g["log_dtm_disaster_idps"],
            s=46, color=color, edgecolor=SURFACE, linewidth=1.2, zorder=4, label=label,
        )
        for _, r in g.iterrows():
            ax1.annotate(str(r["year"]), (r["log_extent_x_duration"], r["log_dtm_disaster_idps"]),
                         xytext=(5, 4), textcoords="offset points", fontsize=7.5, color=INK2)
        ax2.scatter(
            g["sev_dev"].clip(-lim, lim), g["imp_dev"].clip(-lim, lim),
            s=46, color=color, edgecolor=SURFACE, linewidth=1.2, zorder=4, label=label,
        )
        for _, r in g.iterrows():
            ax2.annotate(str(r["year"]), (np.clip(r["sev_dev"], -lim, lim), np.clip(r["imp_dev"], -lim, lim)),
                         xytext=(5, 4), textcoords="offset points", fontsize=7.5, color=INK2)

    _log1p_ticks(ax1, "x", [10, 100, 1_000, 10_000])
    _log1p_ticks(ax1, "y", [0, 10, 100, 1_000, 10_000, 100_000])
    ax1.set_xlabel("Flood severity: km² flooded × dekads wet (log scale)", color=INK2, fontsize=9)
    ax1.set_ylabel("Disaster-displaced IDPs, DTM (log scale)", color=INK2, fontsize=9)
    ax1.set_title(
        f"All county-years pooled\nSpearman ρ = {stats['pooled_spearman']:.2f}  (n = {stats['pooled_n']})",
        loc="left", fontsize=10.5, color=INK,
    )

    ratios = [1 / 8, 1 / 4, 1 / 2, 1, 2, 4, 8]
    _ratio_ticks(ax2, "x", ratios)
    _ratio_ticks(ax2, "y", ratios)
    ax2.set_xlim(-lim * 1.05, lim * 1.05)
    ax2.set_ylim(-lim * 1.05, lim * 1.05)
    ax2.set_xlabel("Flood severity vs the county's usual level", color=INK2, fontsize=9)
    ax2.set_ylabel("Displacement vs the county's usual level", color=INK2, fontsize=9)
    lo, hi = stats["within_ci95"]
    ax2.set_title(
        f"Each county against its own usual level\nSpearman ρ = {stats['within_spearman']:.2f}  (95% CI {lo:.2f} to {hi:.2f})",
        loc="left", fontsize=10.5, color=INK,
    )
    corner = dict(fontsize=7.5, color=MUTED)
    ax2.text(lim, lim, "worse flood,\nmore displaced", ha="right", va="top", **corner)
    ax2.text(lim, -lim, "worse flood,\ndisplacement not up", ha="right", va="bottom", **corner)
    ax2.text(-lim, lim, "milder flood,\ndisplacement not down", ha="left", va="top", **corner)
    ax2.text(-lim, -lim, "milder flood,\nfewer displaced", ha="left", va="bottom", **corner)
    ax2.text(0, -lim * 0.62, "flood\nabout usual", ha="center", va="center", **corner)

    handles, labels = ax1.get_legend_handles_labels()
    handles.append(plt.Line2D([], [], marker="o", color=OTHER, lw=0.7, markersize=4))
    labels.append("Other counties")
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, fontsize=8.5,
               bbox_to_anchor=(0.5, 1.0), labelcolor=INK2)
    fig.text(
        0.01, 0.005,
        "Counties with ≥95% flood-mask coverage, 2022–2024. Severity: NASA MODIS/VIIRS masks, both classes. "
        "Displacement: IOM DTM disaster arrivals from the first round after each season (R14, R15, R16). "
        "Usual level = mean of the county's other two years (log scale); points beyond ×12 drawn at the edge.",
        fontsize=7, color=MUTED, wrap=True,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / "pooled_vs_within.png"
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
    return path


def plot_two_counties(rows: pd.DataFrame, examples: tuple[pd.Series, pd.Series]) -> Path:
    plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.6), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    panels = (
        ("extent_x_duration", "sev", "Flood severity (km² × dekads wet)"),
        ("dtm_disaster_idps", "imp", "Disaster-displaced IDPs (DTM)"),
    )
    for r, (ex, color) in enumerate(zip(examples, SERIES)):
        g = rows[rows["adm2_pcode"] == ex["adm2_pcode"]].sort_values("year")
        x = np.arange(len(g))
        for c, (col, prefix, title) in enumerate(panels):
            ax = axes[r, c]
            _style(ax)
            ax.grid(axis="x", visible=False)
            value = g[col].to_numpy(dtype=float)
            usual = np.expm1(g[f"{prefix}_usual"].to_numpy(dtype=float))
            ax.vlines(x, usual, value, color=color, lw=1.6, zorder=2)
            ax.scatter(x, usual, s=42, facecolor=SURFACE, edgecolor=color, linewidth=1.5, zorder=3,
                       label="Usual level (average of the other two years)")
            ax.scatter(x, value, s=50, color=color, edgecolor=SURFACE, linewidth=1.2, zorder=4,
                       label="This year")
            for xi, v, d in zip(x, value, g[f"{prefix}_dev"].to_numpy(dtype=float)):
                ax.annotate(f"{np.expm1(d) * 100:+.0f}%", (xi, v), xytext=(9, -3), textcoords="offset points",
                            fontsize=8, color=INK2)
            ax.set_xticks(x, [str(y) for y in g["year"]])
            ax.set_xlim(-0.5, len(g) - 0.3)
            ax.set_ylim(0, max(value.max(), np.nanmax(usual)) * 1.18)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: f"{v:,.0f}"))
            ax.set_title(f"{ex['adm2_name']}: {title}", loc="left", fontsize=10, color=INK)
            if c == 1:
                for xi, cat in zip(x, g["category"]):
                    ax.annotate(cat.replace(", ", ",\n"), (xi, 0), xytext=(0, -30), textcoords="offset points",
                                ha="center", va="top", fontsize=7.5, color=INK2, annotation_clip=False)
    axes[0, 0].legend(loc="upper left", frameon=False, fontsize=8, labelcolor=INK2)
    fig.text(
        0.01, 0.005,
        "Each panel has its own scale. Percentages compare this year with the county's usual level. "
        "Categories use a ×1.25 band: within −20%/+25% of usual counts as 'about usual'.",
        fontsize=7, color=MUTED,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1), h_pad=4.5)
    path = FIG_DIR / "two_counties.png"
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
    return path


# ---------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="rebuild the severity cache from the parquets")
    args = parser.parse_args()

    rows_dtm, rows_ocha = build_demo_panel(force=args.force)
    stats = {
        "dtm": summarise(rows_dtm, "log_dtm_disaster_idps"),
        "ocha": summarise(rows_ocha, "log_ocha_affected"),
        "ocha_years_per_county": rows_ocha.groupby("adm2_pcode").size().value_counts().sort_index().to_dict(),
    }
    examples = pick_examples(rows_dtm)
    stats["examples"] = [e[["adm2_pcode", "adm2_name", "in_step", "out_step"]].to_dict() for e in examples]
    (OUT / "within_county_demo_summary.json").write_text(json.dumps(stats, indent=2, default=str))

    p1 = plot_pooled_vs_within(rows_dtm, examples, stats["dtm"])
    p2 = plot_two_counties(rows_dtm, examples)
    cols = ["adm2_name", "year", "extent_km2", "mean_dekads_wet", "extent_x_duration", "sev_usual", "sev_dev",
            "dtm_disaster_idps", "dtm_r16_disaster_idps", "imp_usual", "imp_dev", "category"]
    show = rows_dtm[rows_dtm["adm2_pcode"].isin([e["adm2_pcode"] for e in examples])][cols].copy()
    for c in ("sev_usual", "imp_usual"):
        show[c] = np.expm1(show[c]).round(0)
    for c in ("sev_dev", "imp_dev"):
        show[c] = (np.expm1(show[c]) * 100).round(0)
    print(json.dumps(stats, indent=2, default=str))
    print(show.round(1).to_string(index=False))
    print(p1, p2, sep="\n")


if __name__ == "__main__":
    main()
