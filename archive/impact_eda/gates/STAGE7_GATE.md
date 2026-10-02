# Stage 7 gate — cross-dataset stress-tests

## Artefacts

| Output | Path |
|--------|------|
| Preregistered metrics | `outputs/impact_eda/stage7_preregistered_checks.csv` |
| Five-part narrative | `outputs/impact_eda/stage7_findings.md` |
| Unusual flood county-year | `outputs/impact_eda/admin2_unusual_flood_2022_2024.csv` |
| Recurring flood county-year | `outputs/impact_eda/admin2_recurring_flood_2022_2024.csv` |
| ASAP on flood pixels | `outputs/impact_eda/stage7_asap_on_unusual_flood_px_admin2_year.csv`, `stage7_asap_on_recurring_flood_px_admin2_year.csv` |
| GeoEPR exposure proxy | `outputs/impact_eda/stage7_geoepr_flood_exposure_2023.csv` |

## Regenerate

```powershell
python -m eda.impact_stages --through 7
```

Re-runs Stages 2–7. Stage 6 ASAP zonal is cached. Flood pixel ASAP sampling caps at 25k points/year.

## Gate checklist

- [x] Unusual-flood × ASAP recomputed on flood pixels (not only `exposure_locals.ipynb` sample).
- [x] Recurring vs unusual flood ASAP comparison.
- [x] Flood × FEWS with high/low UCDP split and low-flood/high-ha contradiction count.
- [x] Flood × UCDP (same year + lag +1); type-2 subset; date_prec≤3.
- [x] ACLED admin1 state-year sensitivity (not confirmation).
- [x] DTM disaster arrivals vs OCHA Oct 2022 ranks (disaster ≠ flood-only).
- [x] GeoEPR flood exposure descriptive only.
- [x] Five-part writeups in `stage7_findings.md`.
- [ ] **Team review:** decide which directions survive critical read before Stage 8 synthesis.

## Next step

Stage 8 — evidence-based synthesis:

```powershell
python -m eda.impact_stages --through 8
```
