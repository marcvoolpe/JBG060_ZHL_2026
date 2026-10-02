# Session B — cropland exposure and calendar (Stages 19–22)

Pre-registered **before** running `python -m eda.impact_session_b`. Follows [`SESSION_A_CLOSEOUT.md`](SESSION_A_CLOSEOUT.md).

**Lock-ins (do not reopen):** annual unusual flood → FEWS harvest is null (SA-H1); no loss language; hydro lead-time cut; FEWS ha descriptive only; ASAP = exposure.

**External data not in repo:** FEWS livelihood zones, CHIRPS/NDVI, recent livestock — Session B uses course-pack layers only.

---

## SB-H1 — Unusual flood exposure is rangeland-heavy vs cropland

- **Claim:** At flood-pixel locations, unusual inundation carries a lower crop share of (crop + rangeland) exposure units than recurring seasonal wetland flooding.
- **Test:** Per county-year and mask family, `crop_exposed_units = sum(crop_pct/100)`, `range_exposed_units = sum(rangeland_pct/100)` at unique flood pixels; compare crop share unusual vs recurring (paired by county-year where both exist; national means).
- **Data:** All years 2000–2025, both mask families; ASAP tifs; `flood_pixel_to_admin2.csv`.
- **Falsified if:** mean crop share does not differ between mask families (or unusual is higher).

---

## SB-H2 — Harvest-window harvest association survives falsification

- **Claim:** Negative Sep–Nov unusual → harvest link is mask-specific and not fully explained by rain climatology or detection intensity.
- **Tests (pre-declared):**
  1. **Recurring placebo** — same within-county OLS with recurring plant/harvest pixel-days.
  2. **Rain-defined windows** — plant = months M−2..M, harvest = M+3..M+5 where M is county climatological peak precip month from `stage16_era5_county_month.csv` (2000–2021 mean).
  3. **Detection control** — add county-year `detection_share_harvest = obs_days/pixel_days` summed over harvest months as extra covariate in unusual harvest-window spec.
- **Specs:** `full` and `pre2022` (years &lt; 2022).
- **Falsified if:** recurring harvest coef equally negative and significant, OR unusual harvest coef loses p&lt;0.05 under rain-defined windows or detection control in both specs.

---

## SB-H3 — Crop and population exposure layers are not redundant

- **Claim:** County-year ranking by crop-exposed units vs flood-exposed population (Stage 17) differs enough to justify a joint product.
- **Test:** Spearman ρ on overlapping county-years (2015–2025); if ρ &gt; 0.9, deliverable notes single-layer sufficiency.
- **Deliverable:** `stage21_exposure_product.csv` with percentiles and quality flags (tile coverage, post-2020, OCHA assessed).

---

## Gate checklist

- [ ] Pixel-area assumption documented in STAGE19_GATE.md.
- [ ] n reported at each join for SB-H2.
- [ ] SESSION_B_CLOSEOUT.md with six protocol sections.
