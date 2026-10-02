# Deferred external datasets

Datasets identified as useful but not yet in the repo. Session runners should not fail if these are absent.

## AGLW — Annual global gridded livestock mapping (1961–2021)

| Field | Detail |
|-------|--------|
| Size | ~17 GB (full global download) |
| Status | **Not downloaded** — user to add later |
| Purpose | County-year cattle/pasture pressure covariate for H8 sensitivity (replace ~2010 GHA cattle raster in course pack) |
| Planned join | Zonal sum or density of cattle layer to `adm2_pcode` × year; use as control in **dry-season** conflict spec only |
| Interim substitute | FEWS livelihood pastoral/cattle stratum (`stage23_admin2_lhz.csv`) in Session C |

When added, place under `data/AGLW/` (or similar) and document path in `IMPACT_EDA_README.md`.
