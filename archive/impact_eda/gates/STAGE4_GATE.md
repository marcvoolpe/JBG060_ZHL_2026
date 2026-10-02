# Stage 4 gate — overlap and redundancy

## Artefacts

| Output | Path |
|--------|------|
| Pairwise redundancy matrix | `outputs/impact_eda/redundancy_matrix.csv` |
| Narrative + channel rules | `outputs/impact_eda/redundancy.md` |
| UCDP type-2 vs Non-State by year | `outputs/impact_eda/redundancy_ucdp_type2_vs_nonstate_by_year.csv` |

## Regenerate

```powershell
python -m eda.impact_stages --through 4
```

## Gate checklist

- [x] Each major information channel has a **one-primary-series** recommendation.
- [x] ACLED + UCDP fatalities flagged as non-additive.
- [x] DTM stock / flow / OCHA / disaster bucket distinguished.
- [x] ASAP vs FEWS marked complementary, not duplicate.
- [x] Unusual vs recurring flood marked same-source related.
- [x] Empirical UCDP GED type-2 vs Non-State annual counts exported.
- [ ] **Team review:** agree channel picks before Stage 6–7 modelling tables.

## Next step

Stage 5 — join feasibility: `python -m eda.impact_stages --through 5`
