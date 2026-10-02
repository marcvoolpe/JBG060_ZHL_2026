# Archive: EDA for candidate research objectives we dropped

Everything here is **finished, outdated work**. It explored research objectives (ROs) that the team
dropped before choosing the current one: the rule-based cropland map in `cropland/` and
`processing_data/cropland/` (see `HANDOFF.md` §2). It is kept so findings can be cited and re-checked.
Don't build new work on it, and check `HANDOFF.md` §5 before re-proposing any of these ROs.

Archived on 2 Oct 2026. Files were moved, not rewritten. The gate, session and handoff `.md` files are
historical records: their text, including the commands and `eda/...` paths they mention, is unchanged.
The only edits were to imports and output paths in the `.py`/`.ipynb` files, so the code still runs
from the new location.

## Folders

| Folder | Candidate RO it served | Verdict | Why it was dropped |
|---|---|---|---|
| `impact_eda/` | Stages 1–8: crop + conflict impact model | NO-GO (Stage 8) | Crop impact undetectable; UCDP median ~2 events/county; no real ACLED |
| | Stages 9–14 + Session A (15–18): floods → harvest loss (FEWS), upstream hydrology as lead time | Null / cut | Within-county null under every spec; best Spearman ~0.21 |
| | Session B (19–22): cropland vs rangeland exposure + calendar | Context only | Unusual inundation ≈ 87% rangeland / 13% cropland |
| | Sessions C–D (23–30): conflict seasonality, AA decision framework (cost–loss, routing) | Rejected | Assumed cost–loss; climatology ≈ oracle; conflict too sparse; `CAPSTONE_AA_SYNTHESIS.md` is over-optimistic |
| | Session E (31–34): within-county flood-impact RO | NO-GO at Stage 34 | Power 0.70 at the highest reachable ρ. Still blinded (`UNBLINDED=False`); Stage 35 never written |
| `ro_search/` | C1-R flooded-cropland audit (900 points), the 27 Sep RO search | Superseded | Replaced by the Aweil audit plan, then by the own-map RO. Report: `external_reviews/superior_ro_search_report.md` |
| `external_reviews/` | All of the above: AI deep-research reviews and their prompts (`prompts/`), 22–27 Sep | Reference only | They judged the candidate ROs; their verdicts are summarised in `HANDOFF.md` §5 |
| `roads_flood/` | Road closure (Logistics Cluster) as a flood outcome | Not viable (27 Sep) | Within-corridor effect −4 pts (CI −12 to +3); road statuses are sticky |

Facts from this work that still hold are listed in `HANDOFF.md` §5 ("Other facts that still hold").

## Re-running (from the repo root, global Python 3.13)

```powershell
python -m archive.impact_eda.impact_session_e --help   # any stage runner; see impact_eda/README.md
python -m archive.ro_search.ro_search_checks
python -m archive.roads_flood.roads_flood_eda
python -m archive.roads_flood.roads_flood_figures
```

- Data outputs still go to the gitignored `eda/outputs/impact_eda/` and `eda/outputs/roads_eda/`
  (unchanged: `processing_data/paths.py` defines them, and the current code uses that file too).
- Gate and close-out docs are now written to `impact_eda/gates/` and `impact_eda/sessions/`.
- Open notebooks with `archive/impact_eda/notebooks/` or the repo root as the working directory.
- Analysis dependencies: `requirements-analysis.txt`.

## Old path → new path

Older documents (e.g. `external_reviews/superior_ro_search_report.md`, the gate files) cite the old paths.

| Old | New |
|---|---|
| `eda/STAGE*_GATE.md`, `eda/STAGE9_HYPOTHESES.md` | `archive/impact_eda/gates/` |
| `eda/SESSION_*_{HYPOTHESES,CLOSEOUT}.md`, `eda/SESSION_PROTOCOL.md` | `archive/impact_eda/sessions/` |
| `eda/impact_*.py`, `eda/within_county_*.py` | `archive/impact_eda/` |
| `eda/{inventory,semantics}_external.ipynb`, `eda/stage*_figures.ipynb`, `eda/stage6_independent.ipynb`, `eda/session_*_figures.ipynb` | `archive/impact_eda/notebooks/` |
| `eda/IMPACT_EDA_README.md` | `archive/impact_eda/README.md` |
| `eda/HANDOFF.md` (23 Sep) | `archive/impact_eda/HANDOFF_2026-09-23.md` |
| `eda/CAPSTONE_AA_SYNTHESIS.md`, `eda/DEFERRED_DATASETS.md` | `archive/impact_eda/` |
| `eda/ro_search_checks.py` | `archive/ro_search/` |
| `eda/roads_flood_*.py`, `eda/ROADS_FLOOD_EDA.md` | `archive/roads_flood/` |
| `external_deep_research/` | `archive/external_reviews/` |
| `deliverables/figures/roads_p*.png`, `deliverables/tables/roads_*.csv` | `archive/roads_flood/figures/`, `archive/roads_flood/tables/` |
