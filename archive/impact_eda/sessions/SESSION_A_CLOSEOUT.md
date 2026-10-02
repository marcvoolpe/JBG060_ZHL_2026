# Session A close-out — measurement integrity

## 1. What was tested

- **SA-H1 (H2 robustness):** county-year FEWS × unusual flood; specs `full`, `pre2022`, `anomaly`, `full_cov95`. See `stage15_join_counts.csv`.
- **SA-H2 (H3 seasonal):** planting 4–6 vs harvest 9–11 unusual pixel-days; same specs.
- **SA-H3 (H5 lags):** county-month unusual pixel-days vs ERA5 precip and national 1541 / Victoria at 0–3 month lags; `full` vs `pre2022`.
- **SA-H4 (H6):** WorldPop at unusual flood pixels → `flood_exposed_pop`; OCHA 20251130 assessed regression and missingness logit with county facility counts.

## 2. Outcomes

- **SA-H1:** **falsified** for loss language — no spec yields significant negative unusual term at p<0.05.
- **SA-H2:** harvest-window p full = **0.0174**, pre2022 = **0.0046** — **tentative** (survives pre-2022 cut; dry-season detection caveat).
- **SA-H3:** best |Spearman| hydro ≈ **0.2073041518860685** (dartmouth_1541, lag 3); best county precip ≈ **0.2692091423923425**.
- **SA-H4:** missingness logit `log_exposed` p = **0.0010** (`stage17_h6_regressions.csv`).

## 3. Issues remaining

- Post-2020 unusual mask regime jump; `cloud_frac` still unusable.
- OCHA snapshot is cross-sectional; exposed pop is county-year panel — alignment is approximate.
- Stage 16 ERA5 extraction is heavy; cached in `stage16_era5_county_month.csv`.

## 4. Branch decision

- **Crop exposure (Session B):** KEEP exposure-only (annual H2 null); KEEP tentative harvest-window calendar branch.
- **Hydro lead-time (Session B):** CUT forecast narrative.
- **Assessment gap (Session B/C):** KEEP.
- **Conflict seasonality (Session C):** KEEP scheduled — H7/H8 not run in A.

## 5. External data ask

| Dataset | Grain | Gap | Unblocks | Search prompt |
|---------|-------|-----|----------|---------------|
| FEWS livelihood zones | payam/county static | Toic vs upland crop interpretation | Exposure stratification without loss claims | `FEWS NET South Sudan livelihood zones shapefile` |
| CHIRPS or NDVI (MODIS) | monthly raster | Sep–Nov flood timing vs crop phenology | Test H3 without trusting flood detection month | `HDX South Sudan CHIRPS precipitation` |
| Recent livestock density | county raster >2015 | Cattle raster ~2010 for H8 pasture pressure | Session C seasonal conflict covariate | `FAO Gridded Livestock South Sudan` |

## 6. Next-session prompt

```text
Implement Session B (cropland exposure and calendar) per SESSION_A_CLOSEOUT.md branch decisions.
Read: eda/SESSION_A_CLOSEOUT.md, eda/SESSION_PROTOCOL.md, stage15–17 CSVs in eda/outputs/impact_eda/.
Do not reopen: ASAP Manyo/Renk artefact; combined crop+conflict model (Stage 8 no_go).
Figures: argued exposure overlays; skip harvest-loss language if SA-H1 falsified.
```
