# Session B close-out — cropland exposure and calendar

## 1. What was tested

- **SB-H1:** crop vs rangeland share at flood pixels, unusual vs recurring (`stage19_exposure_composition.csv`).
- **SB-H2:** calendar falsification — recurring placebo, rain-defined windows, detection control (`stage20_calendar_falsification.csv`).
- **SB-H3:** redundancy of crop vs population exposure (`stage21_exposure_redundancy.csv`).

## 2. Outcomes

- **SB-H1:** paired mean crop-share unusual − recurring = **-0.0024** (unusual lower crop share).
- **SB-H2:** unusual fixed harvest p (pre2022) = **0.0172**; recurring placebo harvest p (pre2022) = **0.9816**; rain-defined harvest p (pre2022) = **0.1233**; with detection control = **0.0231**.
- **SB-H3:** Spearman crop vs pop = **0.379** (joint product justified).

## 3. Issues remaining

- ASAP static; exposure units are pixel-sum of %, not hectares.
- Rain-defined windows depend on ERA5 county zonal climatology.
- Harvest-calendar claims still subject to dry-season detection artefact (Session A).

## 4. Branch decision

- **Exposure deliverable:** KEEP `stage21_exposure_product.csv` for ZOA/ZHL maps.
- **Harvest-calendar narrative:** TENTATIVE — unusual-specific (placebo clean) but weakened by rain-defined windows; do not use for loss claims.
- **Session C (conflict):** KEEP scheduled (H7/H8).
- **Session D (joint):** HOLD unless Session C produces seasonal pattern.

## 5. External data ask

| Dataset | Grain | Gap | Unblocks | Search prompt |
|---------|-------|-----|----------|---------------|
| FEWS livelihood zones | static vector | Toic vs upland without loss claims | Stratify exposure maps | `FEWS NET South Sudan livelihood zones shapefile` |
| CHIRPS or MODIS NDVI | monthly raster | Phenology vs flood-detection month | Definitive SB-H2 test | `HDX South Sudan CHIRPS precipitation` |
| Recent livestock density | raster >2015 | Pasture pressure for H8 | Session C covariate | `FAO Gridded Livestock South Sudan` |

## 6. Next-session prompt

```text
Implement Session C (conflict seasonality and displacement) per SESSION_PROTOCOL.md.
Read: SESSION_B_CLOSEOUT.md, stage14 outputs, SESSION_A close-out.
Run H8 wet/dry sign reversal on GED type-2; H7 DTM distance-to-flood by arrival reason.
Do not stack GED type-2 + Non-State; DTM disaster tag is outcome only.
```
