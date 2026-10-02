# Stage 8 gate — synthesis and go/no-go

## Artefacts

| Output | Path |
|--------|------|
| Synthesis narrative | `outputs/impact_eda/synthesis.md` |
| Go / no-go table | `outputs/impact_eda/go_no_go.csv` |
| Run summary | `outputs/impact_eda/stages_summary.json` |

## Regenerate

```powershell
python -m eda.impact_stages --through 8
```

Stage 8 reads Stage 5–7 outputs; re-run after any join or cross-dataset change.

## Gate checklist

- [x] `synthesis.md` references join gates and Stage 7 metrics (not static stub).
- [x] `go_no_go.csv` aligned with synthesis table.
- [x] Combined end-to-end model remains **no-go** unless redundancy rules change.
- [ ] **Team review:** agree go/no-go with supervisors before modelling sprint.

## After this gate

Use synthesis to scope the cropland and conflict impact layers only — not a full-team unified model.
