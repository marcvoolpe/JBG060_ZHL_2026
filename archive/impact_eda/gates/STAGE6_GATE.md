# Stage 6 gate — independent EDA per family

## Artefacts

| Output | Path |
|--------|------|
| Narrative (observation-only) | `outputs/impact_eda/stage6_independent.md` |
| FEWS harvest by state-year | `outputs/impact_eda/stage6_fews_harvest_by_state_year.csv` |
| FEWS national year + 2016 gap | `outputs/impact_eda/stage6_fews_harvest_national_year.csv` |
| FEWS yield vs area | `outputs/impact_eda/stage6_fews_yield_vs_area.csv` |
| ASAP zonal all admin2 | `outputs/impact_eda/stage6_asap_zonal_admin2.csv` |
| UCDP GED by year/type | `outputs/impact_eda/stage6_ucdp_events_by_year_type.csv` |
| UCDP GED type-2 sides | `outputs/impact_eda/stage6_ucdp_ged_type2_sides.csv` |
| UCDP Non-State dyads | `outputs/impact_eda/stage6_ucdp_nonstate_dyads.csv` |
| ACLED by year / admin1 | `outputs/impact_eda/stage6_acled_events_by_year_type.csv`, `stage6_acled_events_by_admin1_type.csv` |
| DTM R16 county stock | `outputs/impact_eda/stage6_dtm_r16_county_stock.csv` |
| OCHA 20251130 county | `outputs/impact_eda/stage6_ocha_20251130_county.csv` |
| IPC window totals | `outputs/impact_eda/stage6_ipc_window_totals.csv` |
| GeoEPR groups | `outputs/impact_eda/stage6_geoepr_groups.csv` |
| Figures | `outputs/impact_eda/figures/stage6/` |
| Walkthrough | `stage6_independent.ipynb` |

## Regenerate

```powershell
python -m eda.impact_stages --through 6
```

This re-runs Stages 2–6. ASAP zonal is cached at `stage6_asap_zonal_admin2.csv`. Flood parquets are not resampled. Flood × crop / flood × conflict is **not** this stage.

## Gate checklist

- [x] Each family described without a flood-association test.
- [x] FEWS: state/year, 2016 gap, yield vs area.
- [x] ASAP zonal stats for **all** admin2 (not only unusual pixels).
- [x] Recurring vs unusual flood-on-cropland deferred to Stage 7 (documented).
- [x] UCDP type mix + Non-State dyad list; ACLED event-type mix at admin1 (not ethnic/county).
- [x] DTM R16 IDP stocks by county; disaster bucket still not flood-only.
- [x] OCHA 20251130 as a snapshot map; NaN = unassessed.
- [x] Plots labelled **Observation (not interpreted)**.
- [ ] **Team review:** confirm the independent pictures before Stage 7 stress-tests.

## Next step

Stage 7 — pre-registered cross-dataset checks, only after this gate is reviewed:

```powershell
python -m eda.impact_stages --through 7
```
