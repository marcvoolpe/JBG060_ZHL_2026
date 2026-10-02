# Stage 2 gate — data quality and semantics

## Artefacts

| Output | Path |
|--------|------|
| Variable definitions + source citations | `outputs/impact_eda/semantics.md` |
| Outlier list | `outputs/impact_eda/semantics_outliers.csv` |
| Walkthrough | `semantics_external.ipynb` |

## Regenerate

```powershell
python -m eda.impact_stages --through 2
```

## Gate checklist

- [x] Written definitions for candidate outcome/exposure variables.
- [x] **HARD DECISION:** DTM `*_ind_disaster` is **not** a flood-only label (single Disaster bucket: natural or human-made). Allowed only as broad disaster-related displacement; flood-specific validation via OCHA snapshots.
- [x] OCHA = assessed/verified only; NaN ≠ 0; undercount vs government possible.
- [x] FMR stocks ≠ mobility stocks; FMP surveys not nationally representative.
- [x] FEWS yield max 2.0 observed in file; cap vs true max not verified.
- [x] UCDP GED ≥1 death vs Non-State ≥25/year vs ACLED events (need not be lethal). ACLED VAC ≠ UCDP type 3.
- [x] Flood unusual ≠ severity.

## Next step

Stage 3 — crosswalks (already run): `python -m eda.impact_stages --through 3`
