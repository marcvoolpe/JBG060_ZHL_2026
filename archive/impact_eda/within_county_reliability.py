"""
DTM test-retest reliability for the within-county RO (independent review, recommendation 1a).

The same arrival cohort (people displaced by disaster who arrived in a given year) is counted
again in later Mobility Tracking rounds. If two rounds agree on which years were worse than
usual *within* a county, the year-specific DTM signal is reliable. If they disagree, a
within-county test cannot tell a null result from noise.

Only the displacement side is tested here; no flood data are used.

Run from repo root:
    python -m archive.impact_eda.within_county_reliability
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from processing_data.paths import EXT_DATA, ensure_impact_eda_out

from archive.impact_eda.impact_stages import DTM_R13_16_FILES, _drop_hxl

OUT = ensure_impact_eda_out()
ROUNDS = (13, 14, 15, 16)
COHORTS = (2021, 2022, 2023, 2024)
# Arrival bins still open when the round was collected (partial years) are not comparable
PARTIAL = {(13, 2022), (14, 2023), (15, 2024)}
MIN_COVERAGE = 0.95
N_BOOT = 2000


def _cohorts_by_round() -> pd.DataFrame:
    """Disaster-displaced IDPs still present per county, by DTM round and arrival year."""
    frames = []
    for rnd in ROUNDS:
        path = EXT_DATA / "IOM_DTM_mobility" / DTM_R13_16_FILES[rnd]
        sheet = next(s for s in pd.ExcelFile(path).sheet_names if "Loc_Dataset" in s)
        year_cols = {f"e_idp_arrival_{y}_ind_disaster": y for y in COHORTS}
        header = pd.read_excel(path, sheet_name=sheet, nrows=0)
        usecols = ["County_INT_PCode"] + [c for c in header.columns if c in year_cols]
        df = _drop_hxl(pd.read_excel(path, sheet_name=sheet, usecols=usecols))
        for col in usecols[1:]:
            agg = pd.to_numeric(df[col], errors="coerce").fillna(0).groupby(df["County_INT_PCode"]).sum()
            frames.append(
                pd.DataFrame(
                    {"adm2_pcode": agg.index.astype(str), "round": rnd, "cohort": year_cols[col], "idps": agg.to_numpy()}
                )
            )
    out = pd.concat(frames, ignore_index=True)
    keep = [(r, c) not in PARTIAL for r, c in zip(out["round"], out["cohort"])]
    return out[keep].reset_index(drop=True)


def _two_way(wide: pd.DataFrame) -> pd.DataFrame:
    """log(1+x), then remove county and cohort-year means (the component the RO actually uses)."""
    logs = np.log1p(wide)
    out = {}
    for col in logs.columns:
        s = logs[col]
        dm = s - s.groupby(level="adm2_pcode").transform("mean")
        dm = dm - dm.groupby(level="cohort").transform("mean")
        out[col] = dm
    return pd.DataFrame(out)


def _rank_corr(a: pd.Series, b: pd.Series) -> float:
    return float(a.rank().corr(b.rank()))


def _boot_ci(dev: pd.DataFrame, a: str, b: str, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    groups = [g for _, g in dev.groupby(level="adm2_pcode")]
    stats = []
    for _ in range(N_BOOT):
        sample = pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        stats.append(_rank_corr(sample[a], sample[b]))
    lo, hi = np.nanpercentile(stats, [2.5, 97.5])
    return round(float(lo), 3), round(float(hi), 3)


def compare(long: pd.DataFrame, counties: set[str], a: str, b: str, cohorts: tuple[int, ...],
            source: dict[str, dict[int, int]]) -> dict:
    """Agreement between two versions (a, b) of the county x cohort table.

    source maps each version name to {cohort: round} so a version can mix rounds
    (e.g. the RO's 'first round after each season').
    """
    parts = []
    for name, rounds in source.items():
        rows = [
            long[(long["round"] == rounds[c]) & (long["cohort"] == c)].assign(version=name)
            for c in cohorts
        ]
        parts.append(pd.concat(rows))
    both = pd.concat(parts)
    both = both[both["adm2_pcode"].isin(counties)]
    wide = both.pivot_table(index=["adm2_pcode", "cohort"], columns="version", values="idps").dropna()
    # Drop counties that record no disaster arrivals in either version (no year pattern to compare)
    has = wide.groupby(level="adm2_pcode").transform("sum")
    wide = wide[(has[a] > 0) & (has[b] > 0)]
    n_years = wide.groupby(level="adm2_pcode")[a].transform("size")
    wide = wide[n_years == len(cohorts)]
    dev = _two_way(wide)
    levels = np.log1p(wide)
    return {
        "versions": {k: {str(c): r for c, r in v.items()} for k, v in source.items()},
        "cohorts": list(cohorts),
        "n_counties": int(wide.index.get_level_values("adm2_pcode").nunique()),
        "levels_spearman": round(_rank_corr(levels[a], levels[b]), 3),
        "within_county_spearman": round(_rank_corr(dev[a], dev[b]), 3),
        "within_county_ci95": list(_boot_ci(dev, a, b)),
    }


def main() -> None:
    long = _cohorts_by_round()
    cov = pd.read_csv(OUT / "flood_tile_coverage_admin2.csv")
    counties = set(cov.loc[cov["flood_tile_coverage_share"] >= MIN_COVERAGE, "adm2_pcode"].astype(str))

    national = long.groupby(["cohort", "round"])["idps"].sum().unstack("round")
    tests = {
        "R15_vs_R16_2021-2023": compare(
            long, counties, "R15", "R16", (2021, 2022, 2023),
            {"R15": {2021: 15, 2022: 15, 2023: 15}, "R16": {2021: 16, 2022: 16, 2023: 16}},
        ),
        "R14_vs_R16_2021-2022": compare(
            long, counties, "R14", "R16", (2021, 2022),
            {"R14": {2021: 14, 2022: 14}, "R16": {2021: 16, 2022: 16}},
        ),
        "R14_vs_R15_2021-2022": compare(
            long, counties, "R14", "R15", (2021, 2022),
            {"R14": {2021: 14, 2022: 14}, "R15": {2021: 15, 2022: 15}},
        ),
        "R13_vs_R16_2021-2022_via_R14": compare(
            long, counties, "early", "R16", (2021, 2022),
            {"early": {2021: 13, 2022: 14}, "R16": {2021: 16, 2022: 16}},
        ),
        # The RO's outcome (first round after each season) against the same years all read from R16
        "first_round_vs_R16_2021-2023": compare(
            long, counties, "first", "R16", (2021, 2022, 2023),
            {"first": {2021: 13, 2022: 14, 2023: 15}, "R16": {2021: 16, 2022: 16, 2023: 16}},
        ),
    }
    result = {
        "national_disaster_idps_by_cohort_and_round": {
            str(c): {f"R{r}": (None if pd.isna(v) else int(v)) for r, v in row.items()} for c, row in national.iterrows()
        },
        "tests": tests,
        "reading": "within_county_spearman = test-retest reliability of the county-specific year pattern "
        "(two-way demeaned log counts). Review thresholds: >=0.7 lets a null be read; <0.3 means DTM "
        "does not identify a year-specific signal.",
    }
    (OUT / "within_county_dtm_reliability.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
