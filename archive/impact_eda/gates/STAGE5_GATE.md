# Stage 5 gate — join feasibility

## Artefacts

| Output | Path |
|--------|------|
| Narrative + classification | `outputs/impact_eda/join_feasibility.md` |
| One row per candidate join | `outputs/impact_eda/join_feasibility.csv` |
| Flood tile ∩ admin2 | `outputs/impact_eda/flood_tile_coverage_admin2.csv` |
| Five OCHA snapshots | `outputs/impact_eda/join_feasibility_ocha_snapshots.csv` |
| DTM R13–R16 P-code / coordinates | `outputs/impact_eda/join_feasibility_dtm_r13_16.csv` |
| FEWS matched counties by year | `outputs/impact_eda/join_feasibility_fews_years.csv` |
| UCDP precision counts | `outputs/impact_eda/join_feasibility_ucdp_filters.csv` |
| UCDP point-in-polygon filters | `outputs/impact_eda/join_feasibility_ucdp_sjoin_summary.csv` |
| GeoEPR ∩ admin2 counts | `outputs/impact_eda/join_feasibility_geoepr_admin2.csv` |

## Regenerate

```powershell
python -m eda.impact_stages --through 5
```

This re-runs Stages 2–5 by design of the CLI. Flood **parquets are not resampled**; coverage uses the same tile bbox and 0.0625 km² pixel area as `eda/revised_spatial_eda.py`.

## Gate checklist

- [x] Each candidate join has grain, keys, coverage, and a minimum **n**.
- [x] Joins classified as meaningful / over-interpret / avoid (not a static list).
- [x] Directions with n below the predeclared floor marked `stop_n_too_small`.
- [x] DTM `*_ind_disaster` still not treated as flood-only (Stage 2).
- [x] ACLED stays admin1; county flood would aggregate **up**.
- [x] GeoEPR ∩ flood classified as settlement **exposure**, and separately **avoid** as ethnic conflict risk.
- [x] Five OCHA files not stacked as a time series.
- [ ] **Team review:** agree which `proceed` joins enter Stage 6–7 tables; Stage 3 unmatched and Stage 4 channel picks remain open.

## Next step

Stage 6 — independent EDA per family, only after this gate is reviewed:

```powershell
python -m eda.impact_stages --through 6
```

Do not run `--through 8` until Stages 6–7 are requested.
