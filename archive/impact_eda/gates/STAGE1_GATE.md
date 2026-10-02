# Stage 1 gate — external impact EDA

Stage 1 is **complete** when the artefacts below exist and have been reviewed. **Stage 2 (semantics) should not start until review.**

## Artefacts


| Output                     | Path                                                                                     |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| Machine-readable catalogue | `[outputs/impact_eda/catalogue.csv](outputs/impact_eda/catalogue.csv)`                   |
| DTM sheet-layout drift log | `[outputs/impact_eda/schema_drift_notes.txt](outputs/impact_eda/schema_drift_notes.txt)` |
| Run summary                | `[outputs/impact_eda/inventory_summary.json](outputs/impact_eda/inventory_summary.json)` |
| Human-readable walkthrough | `[inventory_external.ipynb](inventory_external.ipynb)`                                   |




## Regenerate

From repository root:

```powershell
python -m eda.impact_inventory
```



## Gate checklist (plan)

- [x] Every external family under `data/` has catalogue rows (seven families).
- [x] Selected processed course tables included for comparison (admin2, IPC long, farmland summary, flood daily counts).
- [x] No joins in Stage 1 code.
- [x] Schema drift documented for IOM DTM mobility (14 files) and flow (34 files; sample profiled).
- [x] Read errors reported in catalogue (`read_error` column); latest run: **0 errors**.
- [x] **Team review:** confirm grain/time/spatial fields before Stage 2 (proceed to Stage 2 artefacts).



## Paths

Course pack and external data are resolved via `[processing_data/paths.py](../processing_data/paths.py)`:

- `EXT_DATA` → `data/`
- `COURSE_RAW` → `data-JBG060-2026/data-JBG060-2026/`
- `resolve_raw_data_dir()` → `raw_data/` if present, else course pack



## Next step after review

Stage 2 — data quality and semantics (`semantics.md` or notebook section), especially DTM `disaster` vs flood and OCHA assessed-only definitions.