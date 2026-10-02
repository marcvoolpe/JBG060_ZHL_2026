"""
Session D — Stages 27–30: anticipatory action decision framework for ZOA / ZHL.

Prerequisites: impact_session_b through 21, impact_session_a 17, impact_session_c 23–25,
impact_panel flood_admin2_month.csv.

Run from repo root:
    python -m archive.impact_eda.impact_session_d --through 30
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from processing_data.paths import ROOT, ensure_impact_eda_out

from archive.impact_eda.impact_panel import RAIN_MONTHS

OUT = ensure_impact_eda_out()
WET_MONTHS = tuple(RAIN_MONTHS)
IMPACT_YEARS = range(2015, 2026)
DECISION_MONTH = 5  # May: pre-wet-season outlook
EXTERNAL_FORECAST = OUT / "stage27_external_forecasts.csv"
COST_LOSS_RATIOS = (0.15, 0.20, 0.25, 0.33)


def _spearman(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    frame = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(frame) < 5:
        return np.nan, len(frame)
    rho = float(frame["x"].rank().corr(frame["y"].rank()))
    return rho, len(frame)


def _wet_unusual_county_year() -> pd.DataFrame:
    flood = pd.read_csv(OUT / "flood_admin2_month.csv")
    u = flood[(flood.mask_type == "unusual") & flood.month.isin(WET_MONTHS)]
    return (
        u.groupby(["adm2_pcode", "year"], observed=True)["pixel_days"]
        .sum()
        .reset_index(name="wet_unusual_pixel_days")
    )


def _impact_panel() -> pd.DataFrame:
    prod = pd.read_csv(OUT / "stage21_exposure_product.csv")
    prod = prod[prod.year.isin(IMPACT_YEARS)].copy()
    pop_pct = prod["pct_flood_exposed_pop"]
    crop_pct = prod["pct_crop_exposed_units"]
    prod["impact_score"] = np.nanmean(
        np.vstack([pop_pct.to_numpy(dtype=float), crop_pct.to_numpy(dtype=float)]),
        axis=0,
    )
    has = prod["flood_exposed_pop"].notna() | prod["crop_exposed_units"].notna()
    prod = prod[has].copy()
    prod["bad_season_tercile"] = prod.groupby("year", observed=True)["impact_score"].transform(
        lambda s: s >= s.quantile(2 / 3) if len(s) >= 3 else False
    )
    hazard = _wet_unusual_county_year()
    prod = prod.merge(hazard, on=["adm2_pcode", "year"], how="left")
    ocha = pd.read_csv(OUT / "stage6_ocha_20251130_county.csv").rename(
        columns={"Admin2_PCODE": "adm2_pcode"}
    )
    prod = prod.merge(ocha[["adm2_pcode", "people_affected"]], on="adm2_pcode", how="left", suffixes=("", "_ocha"))
    dtm = pd.read_csv(OUT / "stage25_county_dtm_flood.csv")
    prod = prod.merge(
        dtm[["adm2_pcode", "disaster_share", "mean_unusual_px"]],
        on="adm2_pcode",
        how="left",
    )
    return prod


def _build_forecasts(hazard: pd.DataFrame) -> pd.DataFrame:
    """County-year forecasts available before wet season of year Y (no leakage)."""
    rows: list[dict] = []
    for pcode in hazard.adm2_pcode.unique():
        sub = hazard[hazard.adm2_pcode == pcode].sort_values("year")
        for _, r in sub.iterrows():
            y = int(r.year)
            val = float(r.wet_unusual_pixel_days)
            hist = sub[sub.year < y]["wet_unusual_pixel_days"]
            prev = sub.loc[sub.year == y - 1, "wet_unusual_pixel_days"]
            rows.append(
                {
                    "adm2_pcode": pcode,
                    "year": y,
                    "forecast_source": "oracle_wet_unusual",
                    "forecast_score": val,
                    "lead_months": 0,
                }
            )
            rows.append(
                {
                    "adm2_pcode": pcode,
                    "year": y,
                    "forecast_source": "climatology",
                    "forecast_score": float(hist.mean()) if len(hist) >= 3 else np.nan,
                    "lead_months": DECISION_MONTH,
                }
            )
            rows.append(
                {
                    "adm2_pcode": pcode,
                    "year": y,
                    "forecast_source": "persistence",
                    "forecast_score": float(prev.iloc[0]) if len(prev) else np.nan,
                    "lead_months": DECISION_MONTH,
                }
            )
    fc = pd.DataFrame(rows)
    if EXTERNAL_FORECAST.exists():
        ext = pd.read_csv(EXTERNAL_FORECAST)
        need = {"adm2_pcode", "year", "forecast_score"}
        if need.issubset(ext.columns):
            ext = ext.copy()
            ext["forecast_source"] = ext.get("forecast_source", "external_model")
            ext["lead_months"] = ext.get("lead_months", DECISION_MONTH)
            fc = pd.concat([fc, ext[list(fc.columns)]], ignore_index=True)
    return fc


def run_stage27_target() -> Path:
    panel = _impact_panel()
    panel.to_csv(OUT / "stage27_ground_truth_target.csv", index=False)

    val_rows: list[dict] = []
    assessed = panel.dropna(subset=["people_affected", "impact_score"])
    if len(assessed) >= 10:
        snap = assessed.sort_values("year").groupby("adm2_pcode", observed=True).tail(1)
        rho, n = _spearman(snap["impact_score"], snap["people_affected"])
        val_rows.append({"pair": "impact_vs_ocha_affected", "spearman": rho, "n": n})
    dtm = panel.dropna(subset=["disaster_share", "impact_score"])
    if len(dtm) >= 10:
        snap = dtm.sort_values("year").groupby("adm2_pcode", observed=True).tail(1)
        rho, n = _spearman(snap["impact_score"], snap["disaster_share"])
        val_rows.append({"pair": "impact_vs_dtm_disaster_share", "spearman": rho, "n": n})
    snap = panel.dropna(subset=["mean_unusual_px", "impact_score"])
    if len(snap) >= 10:
        last = snap.sort_values("year").groupby("adm2_pcode", observed=True).tail(1)
        rho, n = _spearman(last["impact_score"], last["mean_unusual_px"])
        val_rows.append({"pair": "impact_vs_mean_unusual_px", "spearman": rho, "n": n})
    pd.DataFrame(val_rows).to_csv(OUT / "stage27_validation_spearman.csv", index=False)

    hazard = _wet_unusual_county_year()
    fc = _build_forecasts(hazard)
    fc.to_csv(OUT / "stage27_forecast_panel.csv", index=False)

    spec = OUT / "stage27_prediction_interface_spec.md"
    spec.write_text(
        "\n".join(
            [
                "# Stage 27 — pluggable flood forecast interface",
                "",
                "Session D evaluates anticipatory triggers against `stage27_ground_truth_target.csv`",
                "(`bad_season_tercile` from joint exposure percentiles).",
                "",
                "## Built-in sources (`stage27_forecast_panel.csv`)",
                "",
                "| `forecast_source` | Meaning |",
                "|-------------------|---------|",
                "| `climatology` | Mean wet-season (Jun–Oct) unusual `pixel_days` for years &lt; Y |",
                "| `persistence` | Prior year wet-season unusual `pixel_days` |",
                "| `oracle_wet_unusual` | Same-year wet season (skill upper bound, not operational) |",
                "| `external_model` | From optional CSV below |",
                "",
                "## External team model",
                "",
                "Drop file: `eda/outputs/impact_eda/stage27_external_forecasts.csv`",
                "",
                "Required columns:",
                "",
                "```text",
                "adm2_pcode,year,forecast_score",
                "```",
                "",
                "Optional: `forecast_source` (default `external_model`), `lead_months` (default 5).",
                "",
                "`forecast_score` must be on the same scale as wet-season unusual pixel-days",
                "(higher = worse season expected). Re-run `python -m archive.impact_eda.impact_session_d --through 28`.",
                "",
                f"Decision month assumed: **{DECISION_MONTH}** (May, before wet season).",
            ]
        ),
        encoding="utf-8",
    )

    n_panel = len(panel)
    n_bad = int(panel.bad_season_tercile.sum())
    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE27_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 27 gate — impact target and forecast interface",
                "",
                f"- Panel county-years: **{n_panel}**; bad-season tercile: **{n_bad}**",
                "- `stage27_ground_truth_target.csv`, `stage27_forecast_panel.csv`",
                "- `stage27_validation_spearman.csv`",
                "- `outputs/impact_eda/stage27_prediction_interface_spec.md`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_d --through 27",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return OUT / "stage27_ground_truth_target.csv"


def _norm_within_year(scores: pd.Series) -> pd.Series:
    if scores.notna().sum() < 2:
        return scores * 0 + 0.5
    return scores.rank(pct=True, method="average")


def run_stage28_trigger() -> Path:
    panel = pd.read_csv(OUT / "stage27_ground_truth_target.csv")
    fc = pd.read_csv(OUT / "stage27_forecast_panel.csv")
    eval_years = sorted(set(IMPACT_YEARS) & set(panel.year.unique()))
    panel = panel[panel.year.isin(eval_years)].copy()

    perf_rows: list[dict] = []
    taus = np.round(np.linspace(0.1, 0.9, 17), 3)
    for src in fc.forecast_source.unique():
        sub_fc = fc[fc.forecast_source == src].copy()
        merged = panel.merge(sub_fc, on=["adm2_pcode", "year"], how="inner")
        merged = merged.dropna(subset=["forecast_score"])
        if merged.empty:
            continue
        merged["score_norm"] = merged.groupby("year", observed=True)["forecast_score"].transform(
            _norm_within_year
        )
        for tau in taus:
            pred = merged["score_norm"] >= tau
            actual = merged["bad_season_tercile"].astype(bool)
            tp = int((pred & actual).sum())
            fp = int((pred & ~actual).sum())
            fn = int((~pred & actual).sum())
            tn = int((~pred & ~actual).sum())
            n = tp + fp + fn + tn
            hit = tp / (tp + fn) if (tp + fn) else np.nan
            far = fp / (fp + tn) if (fp + tn) else np.nan
            perf_rows.append(
                {
                    "forecast_source": src,
                    "tau": float(tau),
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "tn": tn,
                    "n": n,
                    "hit_rate": hit,
                    "false_alarm_rate": far,
                }
            )

    perf = pd.DataFrame(perf_rows)
    perf.to_csv(OUT / "stage28_trigger_performance.csv", index=False)

    cl_rows: list[dict] = []
    for src in perf.forecast_source.unique():
        sub = perf[perf.forecast_source == src]
        for c_over_l in COST_LOSS_RATIOS:
            # act if normalized score >= C/L (probability threshold)
            tau = c_over_l
            row = sub.loc[(sub.tau - tau).abs().idxmin()] if len(sub) else None
            if row is None:
                continue
            tp, fp, fn = int(row.tp), int(row.fp), int(row.fn)
            net_value = tp * 1.0 - fp * c_over_l - fn * 1.0
            cl_rows.append(
                {
                    "forecast_source": src,
                    "cost_loss_ratio": c_over_l,
                    "tau": float(row.tau),
                    "net_value_units": net_value,
                    "hit_rate": row.hit_rate,
                    "false_alarm_rate": row.false_alarm_rate,
                    "n": int(row.n),
                }
            )
    pd.DataFrame(cl_rows).to_csv(OUT / "stage28_cost_loss_curves.csv", index=False)

    # Decision window: May lead vs oracle (0 lead) hit rates at tau=0.33
    window_rows = []
    for src in ("persistence", "climatology", "oracle_wet_unusual"):
        sub = perf[(perf.forecast_source == src) & (perf.tau == 0.33)]
        if not sub.empty:
            r = sub.iloc[0]
            window_rows.append(
                {
                    "forecast_source": src,
                    "lead_months": 0 if src == "oracle_wet_unusual" else DECISION_MONTH,
                    "hit_rate_tau033": r.hit_rate,
                    "false_alarm_rate_tau033": r.false_alarm_rate,
                }
            )
    pd.DataFrame(window_rows).to_csv(OUT / "stage28_decision_window.csv", index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE28_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 28 gate — trigger evaluation and cost–loss",
                "",
                "- `stage28_trigger_performance.csv`, `stage28_cost_loss_curves.csv`",
                "- `stage28_decision_window.csv`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_d --through 28",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return OUT / "stage28_trigger_performance.csv"


def run_stage29_routing() -> Path:
    panel = pd.read_csv(OUT / "stage27_ground_truth_target.csv")
    perf = pd.read_csv(OUT / "stage28_trigger_performance.csv")
    lhz = pd.read_csv(OUT / "stage23_admin2_lhz.csv")
    ged = pd.read_csv(OUT / "stage14_ged_admin2_month.csv")
    ged_recent = (
        ged[ged.year.isin([2023, 2024])]
        .groupby("adm2_pcode", observed=True)["n_events_all"]
        .sum()
        .reset_index(name="conflict_events_23_24")
    )

    # Counties flagged by persistence at tau=0.33 in latest eval year
    latest = max(panel.year)
    fc = pd.read_csv(OUT / "stage27_forecast_panel.csv")
    pers = fc[(fc.forecast_source == "persistence") & (fc.year == latest)].copy()
    pers["score_norm"] = _norm_within_year(pers["forecast_score"])
    high_trigger = set(pers.loc[pers.score_norm >= 0.33, "adm2_pcode"])

    # Also include bad_season in last 3 years
    recent_bad = panel[(panel.year >= latest - 2) & panel.bad_season_tercile].adm2_pcode.unique()
    priority = set(high_trigger) | set(recent_bad)

    base = pd.DataFrame({"adm2_pcode": sorted(priority)})
    base = base.merge(lhz[["adm2_pcode", "LZNAMEEN", "pastoral_dominant"]], on="adm2_pcode", how="left")
    base = base.merge(ged_recent, on="adm2_pcode", how="left")
    base["conflict_events_23_24"] = base["conflict_events_23_24"].fillna(0)
    med_conf = base["conflict_events_23_24"].median()
    base["high_conflict"] = base["conflict_events_23_24"] > med_conf

    def _profile(row: pd.Series) -> str:
        if row.get("pastoral_dominant"):
            return "profile_3_pastoral"
        if row.get("high_conflict"):
            return "profile_2_high_conflict"
        return "profile_1_agro_low_conflict"

    base["action_profile"] = base.apply(_profile, axis=1)
    base["recommended_actions"] = base["action_profile"].map(
        {
            "profile_1_agro_low_conflict": "Seed/fertilizer protection; communal dyke clearing; harvest storage (ZOA field)",
            "profile_2_high_conflict": "Mobile cash; secure hub pre-positioning; remote monitoring (ZHL/partners)",
            "profile_3_pastoral": "Livestock vaccination; borehole protection; corridor evacuation timing",
        }
    )
    base.to_csv(OUT / "stage29_county_action_routing.csv", index=False)

    monthly = (
        ged[ged.year.between(2015, 2025)]
        .groupby("month", observed=True)["n_events_all"]
        .sum()
        .reset_index()
    )
    monthly["share_pct"] = 100 * monthly.n_events_all / monthly.n_events_all.sum()
    wet_share = monthly[monthly.month.isin(WET_MONTHS)].share_pct.sum()
    dry_share = monthly[monthly.month.isin((1, 2, 3, 11, 12))].share_pct.sum()

    matrix = pd.DataFrame(
        [
            {
                "action_profile": "profile_1_agro_low_conflict",
                "primary_actor": "ZOA",
                "access_risk": "low",
                "example_measures": "dykes, seeds, storage",
            },
            {
                "action_profile": "profile_2_high_conflict",
                "primary_actor": "ZHL / partners",
                "access_risk": "high",
                "example_measures": "cash, pre-positioning, remote M&E",
            },
            {
                "action_profile": "profile_3_pastoral",
                "primary_actor": "ZOA + veterinary partners",
                "access_risk": "medium",
                "example_measures": "livestock health, water points",
            },
        ]
    )
    matrix["wet_season_conflict_share_pct"] = wet_share
    matrix["dry_peak_conflict_share_pct"] = dry_share
    matrix.to_csv(OUT / "stage29_action_matrix.csv", index=False)

    compound = base[base.high_conflict & base.adm2_pcode.isin(recent_bad)]
    pd.DataFrame(
        [{"n_compound_high_conflict_bad_season": len(compound), "n_priority_counties": len(base)}]
    ).to_csv(OUT / "stage29_sd_h3_counts.csv", index=False)

    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE29_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 29 gate — conflict-informed routing",
                "",
                f"- Priority counties: **{len(base)}**; compound conflict×recent bad: **{len(compound)}**",
                "- `stage29_county_action_routing.csv`, `stage29_action_matrix.csv`",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_d --through 29",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return OUT / "stage29_county_action_routing.csv"


def _sd_h1_verdict() -> str:
    val = pd.read_csv(OUT / "stage27_validation_spearman.csv")
    ok = val[val.spearman >= 0.2]
    if len(ok) >= 1:
        return "supported" if len(ok) >= 2 else "tentative"
    return "falsified"


def _sd_h2_verdict() -> str:
    cl = pd.read_csv(OUT / "stage28_cost_loss_curves.csv")
    perf = pd.read_csv(OUT / "stage28_trigger_performance.csv")
    base = perf[perf.forecast_source == "climatology"]
    pers = perf[perf.forecast_source == "persistence"]
    if base.empty or pers.empty:
        return "broken test"
    b_hit = float(base.loc[(base.tau - 0.33).abs().idxmin(), "hit_rate"])
    p_hit = float(pers.loc[(pers.tau - 0.33).abs().idxmin(), "hit_rate"])
    positive = cl[cl.net_value_units > 0]
    if len(positive) and p_hit >= b_hit:
        return "tentative" if len(positive) < 4 else "supported"
    if len(positive):
        return "tentative"
    return "falsified"


def _sd_h3_verdict() -> str:
    c = pd.read_csv(OUT / "stage29_sd_h3_counts.csv").iloc[0]["n_compound_high_conflict_bad_season"]
    if c >= 5:
        return "supported"
    if c >= 1:
        return "tentative"
    return "falsified"


def _policy_recommendation(h1: str, h2: str, h3: str) -> str:
    lines = [
        "### ZOA / ZHL anticipatory action (evidence-bounded)",
        "",
    ]
    if h2 in ("supported", "tentative"):
        lines += [
            "- **Act (targeted):** Use May seasonal outlook (persistence + exposure map) to pre-select ",
            "upper-tercile exposure counties; tailor package by action profile (Session D routing table).",
            "- **Do not act everywhere:** Climatology-only triggers have high false-alarm cost at low C/L; ",
            "limit spend to compound priority counties.",
        ]
    else:
        lines += [
            "- **Do not scale AA on current forecasts alone:** Baselines do not beat cost–loss thresholds reliably.",
            "- **Monitor:** Near-term inundation persistence + exposure product for surge response.",
        ]
    lines += [
        "- **Conflict overlay:** High-conflict counties need cash/remote modalities (Profile 2); ",
        "do not assume in-kind delivery is feasible.",
        "- **Calendar:** Plan field actions for Jun–Oct flood window when type-2 conflict share is lower ",
        "than Dec–Mar dry-season peak (see `stage29_action_matrix.csv`).",
        "- **Plug-in:** When team flood model scores are ready, add `stage27_external_forecasts.csv` and re-run Stage 28.",
        "",
    ]
    return "\n".join(lines)


def write_session_d_closeout() -> Path:
    h1, h2, h3 = _sd_h1_verdict(), _sd_h2_verdict(), _sd_h3_verdict()
    val = pd.read_csv(OUT / "stage27_validation_spearman.csv")
    cl = pd.read_csv(OUT / "stage28_cost_loss_curves.csv")
    best = cl.sort_values("net_value_units", ascending=False).head(3)
    path = ROOT / "archive" / "impact_eda" / "sessions" / "SESSION_D_CLOSEOUT.md"
    val_lines = "\n".join(
        f"- {r.pair}: Spearman={r.spearman:.3f} (n={int(r.n)})" for _, r in val.iterrows()
    )
    best_lines = "\n".join(
        f"- {r.forecast_source} C/L={r.cost_loss_ratio}: net={r.net_value_units:.1f}, hit={r.hit_rate:.2f}"
        for _, r in best.iterrows()
    )
    lines = [
        "# Session D close-out — anticipatory action decision framework",
        "",
        "## 1. What was tested",
        "",
        "- **SD-H1:** Exposure-composite `bad_season_tercile` vs OCHA/DTM validation (`stage27_*.csv`).",
        "- **SD-H2:** Trigger skill and cost–loss for climatology, persistence, oracle (`stage28_*.csv`).",
        "- **SD-H3:** Livelihood + GED routing profiles (`stage29_*.csv`).",
        "- **Grain:** county-year 2015–2025; decision month May (lead before wet season).",
        "",
        "## 2. Outcomes",
        "",
        f"- **SD-H1:** **{h1}**",
        val_lines,
        f"- **SD-H2:** **{h2}**",
        best_lines,
        f"- **SD-H3:** **{h3}**",
        "",
        "## 3. Issues remaining",
        "",
        "- Oracle skill upper bound ≠ operational forecast; team model slot empty until CSV provided.",
        "- OCHA snapshot sparse; exposure target is primary, humanitarian layers validate only.",
        "- Post-2020 flood regime shifts climatology baselines.",
        "- No livestock (AGLW) in routing weights.",
        "",
        "## 4. Branch decision",
        "",
        "- **AA trigger on exposure + persistence:** "
        + ("KEEP for pilot targeting." if h2 != "falsified" else "CUT until external model improves skill."),
        "- **Conflict as access modifier:** KEEP (not hazard predictor).",
        "- **Causal flood→conflict:** CUT (Session C).",
        "",
        "## 5. External data ask",
        "",
        "| Dataset | Grain | Gap | Unblocks | Search prompt |",
        "|---------|-------|-----|----------|---------------|",
        "| Operational flood forecast export | admin2, monthly | No team scores in repo | Replace oracle with real AA trigger | internal model output CSV |",
        "| CHIRv2 / GloFAS | river reach, daily | No hydrological forecast | Lead time before wet season | `GloFAS South Sudan download` |",
        "| Anticipatory action cost benchmarks | programme | C/L assumed | Calibrate net value | `OCHA anticipatory action cost evidence` |",
        "",
        "## 6. Next-session prompt",
        "",
        "```text",
        "Capstone synthesis: merge SESSION_D_CLOSEOUT policy section into final report;",
        "map stage29_county_action_routing on admin2; plug team flood CSV into stage27_external_forecasts.csv.",
        "Do not reopen annual harvest-loss or flood→conflict causation.",
        "```",
        "",
        "## 7. ZOA / ZHL recommendation",
        "",
        _policy_recommendation(h1, h2, h3),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_stage30_figures_and_closeout() -> dict:
    write_session_d_closeout()
    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE30_GATE.md").write_text(
        "\n".join(
            [
                "# Stage 30 gate — Session D figures and close-out",
                "",
                "- `session_d_figures.ipynb` → `figures/session_d/`",
                "- `SESSION_D_CLOSEOUT.md` (includes ZOA/ZHL recommendation)",
                "",
                "```powershell",
                "python -m archive.impact_eda.impact_session_d --through 30",
                "jupyter nbconvert --execute archive/impact_eda/notebooks/session_d_figures.ipynb",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    return {"closeout": str(ROOT / "archive" / "impact_eda" / "sessions" / "SESSION_D_CLOSEOUT.md")}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Session D stages 27–30")
    parser.add_argument("--through", type=int, default=30, choices=range(27, 31))
    args = parser.parse_args()

    results: dict[str, object] = {}
    if args.through >= 27:
        results["stage27"] = str(run_stage27_target())
    if args.through >= 28:
        results["stage28"] = str(run_stage28_trigger())
    if args.through >= 29:
        results["stage29"] = str(run_stage29_routing())
    if args.through >= 30:
        results["stage30"] = run_stage30_figures_and_closeout()

    (OUT / "session_d_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
