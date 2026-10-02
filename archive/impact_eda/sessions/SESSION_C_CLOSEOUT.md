# Session C close-out — conflict seasonality and displacement

## 1. What was tested

- **SC-H1:** wet-season (months 6–10) concurrent flood vs type-2; dry-window lead (`stage24_h8_seasonal_ols.csv`).
- **SC-H2:** DTM site distance to unusual flood 2022–2024; county disaster share vs flood (`stage25_*.csv`).
- **Joins:** FEWS LHZ 2018 dominant zone per county (`stage23_admin2_lhz.csv`).

## 2. Outcomes

- **SC-H1:** **tentative** (see wet_concurrent and dry_lead coefs for spec=all).
- **SC-H2:** median km disaster=2.5, conflict=5.3; county disaster-share vs flood Spearman=0.617 — **supported**.

## 3. Issues remaining

- DTM disaster bucket is not flood-only (Stage 2 gate).
- Distance analysis needs coordinates (R16-heavy).
- AGLW livestock not available — see `DEFERRED_DATASETS.md`.
- Post-2020 flood regime may affect wet/dry splits.

## 4. Branch decision

- **Seasonal conflict mechanism:** TENTATIVE — wet negative, dry-lead positive not significant at spec=all; no causal claim.
- **Session D (joint crop×conflict):** HOLD (SC-H1 not fully supported).
- **Livelihood zones:** KEEP for exposure stratification in maps (Session B product).

## 5. External data ask

| Dataset | Grain | Gap | Unblocks | Search prompt |
|---------|-------|-----|----------|---------------|
| AGLW gridded livestock 1961–2021 | raster, annual | No pasture pressure time series | H8 dry-season control | `FAO AGLW download cattle South Sudan` |
| Event-level ACLED (optional) | geo events | Folder duplicate is UCDP only | Cattle-raid coding | `ACLED South Sudan export API` |
| CHIRPS/NDVI | monthly raster | Calendar vs detection | Crop session only | `HDX CHIRPS South Sudan` |

## 6. Next-session prompt

```text
Session D only if SESSION_C_CLOSEOUT SC-H1 supported: co-location maps of stage21_exposure_product
and seasonal conflict pattern — no combined causal model (Stage 8 no_go).
Otherwise: finalize capstone synthesis using exposure product + descriptive conflict/flood co-occurrence.
```
