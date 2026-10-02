# Stage 9 — Pre-registered hypotheses (post-Stage 8)

Written **before** any of the tests below are run, so that a null result counts as a result.
Grounded in Stage 5 join gates, Stage 6 independent profiles, Stage 7 pre-registered checks,
and the Stage 8 `conditional_go` verdicts in `outputs/impact_eda/go_no_go.csv`.

Nothing here is a conclusion. Each hypothesis states the claim, the test, the data and grain,
and **what would falsify it**.

## Why Stage 9 exists — two Stage 7 numbers are artefacts

Verified against the raw tables before drafting:

1. **The ASAP crop contrast is an observability artefact.**
   `stage7_preregistered_checks.csv` reports `mean_crop_pct_counties_without_unusual_px = 9.733`
   (n=2) versus `0.519` (n=77). The two counties with zero unusual pixels are **Manyo (SS0708)**
   and **Renk (SS0711)** — the only two counties with `flood_tile_coverage_share = 0.0` in
   `flood_tile_coverage_admin2.csv`. They are also the #3 and #1 cropland counties nationally
   (`crop_mean_pct` 4.562 and 14.904 in `stage6_asap_zonal_admin2.csv`). The statistic says
   *the two counties where floods cannot be observed are the breadbasket*, not that cropland
   avoids flooding.

2. **The high/low UCDP split is vacuous as run.**
   `fews_ha_vs_unusual_px_split_ucdp` thresholds at `n_events >= 0.0`, putting all 220
   county-years in the "high" group and **n=0** in "low". The flood × UCDP checks ran on
   4–24 units per year, which is why most Spearman cells in the table are blank.

Both follow from one line: `run_stage7_cross_dataset()` in `eda/impact_stages.py` hardcodes
`years = [2022, 2023, 2024]`. FEWS has **1,019** Area-Harvested county-years over 2011–2024
(2016 absent) and the flood masks span **2000–2025**, so the available panel is ~4.5× the
220 county-years used.

---

## Group A — Repair and extend what Stage 7 measured

### H1 — Tile coverage manufactures part of the negative flood–harvest association

- **Claim:** restricting to `flood_tile_coverage_share >= 0.95` (71 of 79 counties; drops Manyo,
  Renk, Melut, Maban, Fashoda, Pariang, Abyei Region) attenuates the pooled
  `flood_unusual_px_vs_fews_ha` correlation (2022–2024: −0.287 / −0.303 / −0.290) and collapses
  the ASAP crop contrast entirely.
- **Test:** re-run the Stage 7 crop checks with the coverage filter applied; report both filtered
  and unfiltered so the delta is visible.
- **Data:** `flood_tile_coverage_admin2.csv`, `admin2_unusual_flood_2022_2024.csv`,
  `stage6_asap_zonal_admin2.csv`, FEWS via `crosswalks/fews_fnid_to_admin2.csv`.
- **Falsified if:** the correlation survives at similar magnitude on the well-covered subset —
  which would make it a *stronger* result than it is today.
- **Priority:** first. It is cheap and it gates every cropland claim downstream.

**Measured (Stage 9 figures notebook, pre-registered test run):**

| Year | n (all) | r unusual (all) | n (cov ≥ 0.95) | r unusual (cov) |
|------|---------|-----------------|----------------|-----------------|
| 2022 | 73 | −0.287 | 68 | −0.286 |
| 2023 | 73 | −0.303 | 68 | −0.302 |
| 2024 | 74 | −0.290 | 69 | −0.302 |

The coverage filter **does not** attenuate the flood–harvest Spearman (falsifier for the correlation part of the original H1 claim). The ASAP crop group contrast **is** an artefact (Manyo/Renk only; see `figures/stage9/fig01_*`). **Revised reading:** observability explains the ASAP means, not the negative rank correlation — prioritize H2 (within-county panel), not dismissing Stage 7 crop ranks.

### H2 — The −0.29 is between-county structure, not a within-county flood effect

- **Claim:** floodplain counties (Sudd, Jonglei, Unity) are structurally low-cereal pastoral
  counties irrespective of any single year's flood. With county and year effects absorbed on the
  full 2011–2024 panel, the within-county association is materially weaker than the pooled
  cross-section; a county's flood extent **relative to its own 2000–2021 baseline** is the term
  that should still predict a fall in harvested area.
- **Test:** rebuild the flood county-year panel for all years present in both mask families
  (`_flood_parquet_years()` already enumerates them); join FEWS 2011–2024; compare pooled
  Spearman against within-county demeaned association; report n at each step.
- **Data:** flood parquets 2000–2025, FEWS 1,019 county-years, COD `adm2_pcode`.
- **Falsified if:** the within-county term is indistinguishable from zero — in which case the
  cropland deliverable must stay an **exposure map** and drop any loss language.
- **Priority:** highest leverage. 220 → ~950 county-years is what makes the question answerable.

**Measured (Stage 12, `stage12_within_county_ols_h2.csv`, n=967 county-years):** two-way demeaned OLS, cluster-robust by county: `log_unusual` coef **−0.026**, **p=0.35** (not significant). **Conclusion:** within-county flood–harvest link not supported; cropland deliverable stays **exposure map** (no loss language).

**Caveat (Fig 4 / Stage 11):** national unusual flooded pixel-days jump ~10× after 2020 and peak in **Dec–Feb** detections (mean monthly share ~24% Dec, ~22% Jan) rather than Jun–Oct rains. A county “own 2000–2021 baseline” may mix product/regime change with hydrology — document baseline choice and sensitivity excluding post-2020 years.

### H3 — Timing inside the cropping calendar beats annual flood volume

- **Claim:** Sep–Nov flooded extent (grain-fill and harvest) carries a stronger negative
  association with harvested area than Apr–Jun extent (planting); early-season flooding may be
  neutral or positive via soil moisture.
- **Test:** aggregate the daily masks into pre-declared seasonal windows instead of annual totals;
  same panel and key as H2. Windows are declared **here**, before looking.
- **Data:** `flood_masks_daily_counts_processed.csv` / flood parquets, FEWS annual.
- **Falsified if:** the windows are interchangeable, which would suggest the annual pixel count is
  only proxying "this is a wetland county" (and therefore supports H2's null).

**Caveat (Fig 4):** if dry-season detection peaks reflect **cloud masking** during the rains rather than true inundation timing, Sep–Nov vs Apr–Jun windows must be interpreted alongside a **detection-frequency** control (e.g. clear-sky proxy or monthly observation-day counts from `flood_masks_daily_counts_processed.csv`), not raw pixel totals alone. Stage 11: **`cloud_frac` constant 0.0** in parquets; tile-month observation counts near-uniform (not usable as clear-sky control).

**Measured (Stage 12, `stage12_within_county_ols_h3.csv`, n=896):** Sep–Nov unusual `log_u_harv` coef **−0.036**, **p=0.017**; Apr–Jun planting **p=0.95**. Harvest-window signal only (tentative; same dry-season detection caveat).

### H4 — Recurring and unusual flooding are opposite constructs, not two severities

- **Claim:** recurring inundation marks productive seasonal wetland (*toic*) that sustains
  agro-pastoral use, while unusual inundation is the damaging signal. Stage 7 already shows the
  sign flip: unusual −0.287/−0.303/−0.290 versus recurring +0.126/+0.067/+0.084.
- **Contradicting evidence already in hand:** ASAP crop % is **higher** on unusual flood pixels
  than on recurring ones (`mean_diff_crop_pct = +0.098`), which cuts against the wetland-farming
  explanation offered in `stage7_findings.md`.
- **Test:** both terms in one within-county specification (H2 panel); keep the two mask families
  separate everywhere, never summed.
- **Falsified if:** the two families carry the same sign and magnitude once county effects are
  absorbed.

**Measured (Stage 12, `stage12_within_county_ols_h4.csv`):** unusual coef **−0.031** (p=0.37), recurring **+0.021** (p=0.61) — sign flip retained but neither significant within FE.

---

## Group B — Course-pack data the impact EDA has not touched

### H5 — South Sudan's floods are routed, not pluvial — therefore forecastable

- **Claim:** county flood extent is better predicted by lagged upstream drivers (Lake Victoria,
  Kyoga, Albert levels; Dartmouth discharge on the White Nile and Sobat) than by contemporaneous
  local rainfall.
- **Why this is invisible today:** `era5_rainfall_runoff_daily_mean_processed.csv` is a single
  **national** daily mean. The raw NetCDFs (`rainfall and runoff/ERA5_2000.nc` … `ERA5_2025.nc`,
  26 files, ~145×57 grid) support proper county zonal rainfall and runoff.
  `reference_evapotranspiration_gridcell_daily_processed.csv` is likewise a single grid cell.
- **Test:** county zonal ERA5 precipitation and runoff by season; compare lead-lag explanatory
  power against `water_levels_all_processed.csv` and
  `dartmouth_discharge_all_processed_with_station_info.csv` at 0–12 week lags.
- **Falsified if:** local county rainfall accumulation dominates the lagged lake and discharge
  terms.
- **Why it matters:** if it holds, the cropland work stops being retrospective damage description
  and gains a lead time.

**Measured (Stage 13, `stage13_hydro_vs_flood_correlation.csv`):** annual Spearman vs unusual pixel-days — discharge 1541 **r≈0.62**, Lake Victoria **r≈0.55**, Albert **r≈0.36**, discharge 100205 **r≈−0.38**, Kyoga **r≈0.06**. County ERA5 in `stage13_era5_county_year.csv`.

### H6 — OCHA "people affected" measures assessment access as much as hazard

- **Claim:** WorldPop-weighted flooded population predicts OCHA affected among accessible
  counties and systematically under-reports elsewhere. Only **38 of 79** counties have a non-null
  affected figure in the Nov 2025 snapshot, and **31 of 79** a displaced figure; NaN is
  unassessed, not zero (Stage 2).
- **Test:** intersect flood masks with WorldPop annual 100m rasters (2015–2025, 11 files) for a
  flood-exposed population per county-year; regress OCHA affected on it; test whether the
  **missingness** pattern is predicted by health-facility density
  (`south_sudan_health_facilities_processed.csv`) and remoteness.
- **Falsified if:** OCHA missingness is unrelated to the access proxies.
- **Deliverable if it holds:** ranked list of counties with high modelled flood-exposed population
  and **no** OCHA assessment — i.e. where response is likely blind. Directly operational.
- **Constraint:** use the 20251130 snapshot for same-season validation only; never stack the five
  OCHA files (Stage 5 avoid list).

**Measured (Stage 13):** `stage13_worldpop_county_year.csv` (zonal pop); **153** county-years flagged in `stage13_h6_blind_spots.csv` (high unusual flood, OCHA unassessed). Top blind spots include Upper Nile / Unity counties (e.g. Baliet, Tonj North).

---

## Group C — Conflict and displacement

### H7 — Flood displacement is short-distance and within-county


- **Claim:** IDP sites with disaster-tagged arrivals sit closer to flood pixels than
  conflict-tagged sites, and disaster-arrival share rises with county flood extent while county
  IDP **stock** barely moves.
- **Test:** DTM R13–R16 location points; distance-to-flood-pixel distributions by arrival reason;
  county-level disaster share versus flood extent.
- **Falsified if:** disaster-arrival counties are no more flooded than conflict-arrival counties —
  which would vindicate the Stage 2 gate directly.
- **Discipline:** flood extent and OCHA are the flood signal; DTM `*_ind_disaster` is the
  **outcome**, never the label (Stage 2).

**Not run in Stages 10–14** (DTM point distances deferred).

### H8 — Flooding suppresses violence in-season and displaces it into the dry season

- **Claim:** inundation restricts cattle raiding by making terrain impassable, then concentrates
  herds on shrinking pasture, raising dry-season risk. Testable as a **within-county seasonal sign
  reversal**: negative in the concurrent rainy season, positive in the following dry season.
- **Test:** full 2011–2025 GED panel (1,054 SSD events, `date_prec <= 3`, sjoin to admin2), split
  by season rather than calendar year; cattle raster as pasture-pressure covariate; county and
  year effects absorbed.
- **Falsified if:** no sign reversal survives the fixed effects.
- **Note:** Stage 7's n=4–24 units per year cannot distinguish any of this from noise. This
  hypothesis is untestable without the panel extension in H2.
- **Redundancy rule (Stage 4):** GED type-2 **or** Non-State, one channel, never both as
  independent predictors.

**Measured (Stage 14, `stage14_ged_admin2_month.csv`, `stage14_flood_events_within_ols.csv`, n=321 county-months):** within FE, `log_flood` → type-2 events coef **+0.022**, **p=0.001** (positive co-occurrence, **not causal**). Dry/wet season sign reversal **not** tested here. Dyads: `stage14_type2_dyad_descriptive.csv`. Stage 7 UCDP high/low split fixed in `impact_stages.py` (use `>0` vs `==0` when median is 0).

---

## Explicitly low-power — do not over-invest

- **Flood-year harvest shortfall → next lean-season IPC Phase 3+.** Five windows only
  (2022-02, 2022-10, 2023-09, 2024-09, 2025-09) and IPC is a committee consensus product, not a
  measurement (Stage 2). Acceptable as a descriptive overlay; it will not carry an inferential
  claim.
- **GeoEPR × flood as anything but settlement-area exposure.** Unchanged from Stage 7.

---

## Priority order

| # | Hypothesis | Rationale |
|---|------------|-----------|
| 1 | H1 coverage filter | cheap; may invalidate the current Stage 7 cropland narrative |
| 2 | H2 panel extension | 220 → ~950 county-years; prerequisite for H3, H4, H8 |
| 3 | H5 routed floods | new variable (county ERA5); potential lead-time finding |
| 4 | H6 exposure vs assessment | new variable (WorldPop × flood); operational output |
| 5 | H3, H4 | ride on the H2 panel |
| 6 | H7, H8 | highest confounding; last |

## Gate checklist

- [ ] H1 re-run reported with **both** filtered and unfiltered statistics.
- [ ] H2 panel n reported at every join step; no silent row loss.
- [ ] Seasonal windows (H3) fixed in writing before the first run.
- [ ] County zonal ERA5 (H5) validated against the existing national daily mean.
- [ ] WorldPop × flood (H6) states the year-alignment rule (rasters 2015–2025 only).
- [ ] Every result gets the five-part writeup: observation / interpretation / alternatives /
      contradicting evidence / next test.
- [ ] **Team review:** agree this list with supervisors before any code is written.

## Figures

- Stage 9: [`stage9_figures.ipynb`](stage9_figures.ipynb) → `figures/stage9/`
- Stages 10–14: [`stage10_14_figures.ipynb`](stage10_14_figures.ipynb) → `figures/stage10_14/`

## References

- Stage 7: `outputs/impact_eda/stage7_findings.md`, `stage7_preregistered_checks.csv`
- Stage 8: `outputs/impact_eda/synthesis.md`, `go_no_go.csv`
- Coverage: `outputs/impact_eda/flood_tile_coverage_admin2.csv`
- Redundancy rules: `outputs/impact_eda/redundancy.md`
- Crosswalks: `outputs/impact_eda/crosswalks/`
