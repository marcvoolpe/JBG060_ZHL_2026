# Session A — measurement integrity (Stages 15–18)

Pre-registered **before** running `python -m eda.impact_session_a`. Grounded in Stage 11 gate narrative (`H2_BASELINE_END = 2021` unused), broken Stage 13 lag screen, and partial Stage 13 H6.

**Not in scope:** H7 DTM distances, H8 dry/wet reversal, cattle, rangeland, IPC inference.

---

## SA-H1 — H2 robustness (within-county harvest vs unusual flood)

- **Claim:** The Stage 12 null (`log_unusual` → `log_ha`, coef ≈ −0.026, p=0.35) is stable under post-2020 regime sensitivity and county anomaly scaling.
- **Specs (pre-declared):**
  1. `full` — years 2011–2024, `log_unusual` from annual unusual unique px.
  2. `pre2022` — drop years ≥ 2022.
  3. `anomaly` — `log1p(unusual_px / county_mean_2000_2021)` with county means from unusual mask only.
  4. `full_cov95` — spec 1 restricted to `flood_tile_coverage_share >= 0.95` (side-by-side).
- **Test:** Two-way demeaned OLS (county + year), cluster by county; same FEWS panel as Stage 12.
- **Falsified if:** any spec yields `log_unusual` (or anomaly term) significant at p<0.05 with negative coef → would reopen cautious loss language (subject to SA-H2).
- **Kill for Session B:** all specs insignificant → Session B stays **exposure-only** for harvest.

---

## SA-H2 — H3 seasonal windows under same specs

- **Claim:** Sep–Nov unusual extent predicts harvest more than Apr–Jun (Stage 12: harvest p=0.017, planting p=0.95).
- **Specs:** Same four labels as SA-H1 on seasonal pixel-day sums (`PLANT_MONTHS` 4–6, `HARVEST_MONTHS` 9–11).
- **Falsified if:** harvest-window term insignificant in all specs, or significant only in `full` but not in `pre2022` → treat as detection/regime artefact.
- **Caveat:** dry-season detection peak (Stage 11); interpret alongside spec `pre2022`.

---

## SA-H3 — H5 lag repair at county-month grain

- **Claim:** Lagged **routed** hydro (Dartmouth 1541, Lake Victoria) explains county-month unusual flood extent better than lagged local ERA5 precipitation at 0–3 month lags.
- **Test:** Panel `adm2_pcode × year × month`; outcome `log1p(pixel_days)` unusual; predictors lagged 0–3 months: county ERA5 monthly precip, national monthly 1541 discharge, national monthly Victoria level. Report Spearman and/or pooled within-county association by lag. Sensitivity: years ≤2021 vs full.
- **Falsified if:** contemporaneous or lagged county precip consistently dominates hydro at same lag (|r| or within association).
- **Kill for Session B hydro branch:** hydro does not beat local rain → no “forecastable flood” narrative from this data alone.

---

## SA-H4 — H6 flood-exposed population and OCHA assessment bias

- **Claim:** WorldPop sampled at **flood pixel** locations (`flood_pixel_to_admin2` + unusual mask parquets, years 2015–2025) predicts OCHA `people_affected` among assessed counties; **missing** assessment is predicted by low facility density and/or high flood-exposed pop.
- **Test:**
  1. `flood_exposed_pop` per county-year.
  2. OLS/log model among assessed only: `people_affected` ~ `flood_exposed_pop` (20251130 snapshot).
  3. Logistic: `ocha_assessed` ~ `flood_exposed_pop` + `n_facilities_county` (points in county polygon).
- **Falsified if:** missingness model shows no association with facilities or exposure (p>0.1 on key terms).
- **Kill:** drop “assessment access” narrative; keep blind-spot list as descriptive only.

---

## Gate checklist

- [ ] Every spec reports n county-years (or county-months for SA-H3).
- [ ] SA-H3 lag table includes pre-2022 split.
- [ ] WorldPop years aligned 2015–2025 only for exposed pop.
- [ ] Close-out written to `SESSION_A_CLOSEOUT.md` per `SESSION_PROTOCOL.md`.
