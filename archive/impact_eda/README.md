# Cropland / conflict impact EDA (Stages 1–34, Sessions A–E) — archived

Outdated: see [`../README.md`](../README.md) for why each candidate RO was dropped.
Layout: runners (`*.py`) here; `gates/` = `STAGE*_GATE.md` + `STAGE9_HYPOTHESES.md`; `sessions/` = session hypotheses, close-outs and protocol; `notebooks/` = figure and walkthrough notebooks.

## Commands (repo root)

```powershell
python -m archive.impact_eda.impact_inventory          # Stage 1: catalogue.csv
python -m archive.impact_eda.impact_stages --through 2 # Stage 2: semantics.md only
python -m archive.impact_eda.impact_stages --through 6 # Stages 2–6 (stop for independent-EDA review)
python -m archive.impact_eda.impact_stages --through 8 # Stages 2–8 (do not run until later gates pass)
python -m archive.impact_eda.impact_panel --through 14  # Stages 10–14 panel + hypotheses (needs requirements-analysis.txt)
python -m archive.impact_eda.impact_session_a --through 18  # Session A: Stages 15–18 measurement integrity
python -m archive.impact_eda.impact_session_b --through 22  # Session B: Stages 19–22 cropland exposure + calendar
python -m archive.impact_eda.impact_session_c --through 26  # Session C: Stages 23–26 conflict seasonality + displacement
python -m archive.impact_eda.impact_session_d --through 30  # Session D: Stages 27–30 anticipatory action decision framework
python -m archive.impact_eda.impact_session_e --through 34  # Session E: Stages 31–34 within-county verification (NO-GO at 34)
```

Outputs: `eda/outputs/impact_eda/` (gitignored).

Session protocol: [`sessions/SESSION_PROTOCOL.md`](sessions/SESSION_PROTOCOL.md).

## Key artefacts

| Stage | File |
|-------|------|
| 1 | `catalogue.csv`, `inventory_external.ipynb`, `STAGE1_GATE.md` |
| 2 | `semantics.md`, `semantics_outliers.csv`, `STAGE2_GATE.md`, `semantics_external.ipynb` |
| 3 | `crosswalks/admin2_names.csv`, `fews_fnid_to_admin2.csv`, `admin1_names.csv`, `crosswalk_match_rates.csv`, `admin2_unmatched.csv`, `temporal_alignment.md`, `STAGE3_GATE.md` |
| 4 | `redundancy_matrix.csv`, `redundancy.md`, `redundancy_ucdp_type2_vs_nonstate_by_year.csv`, `STAGE4_GATE.md` |
| 5 | `join_feasibility.md`, `join_feasibility.csv`, `flood_tile_coverage_admin2.csv`, `join_feasibility_*.csv`, `STAGE5_GATE.md` |
| 6 | `stage6_independent.md`, `stage6_*.csv`, `figures/stage6/`, `STAGE6_GATE.md`, `stage6_independent.ipynb` |
| 7 | `stage7_preregistered_checks.csv`, `stage7_findings.md`, `admin2_*_flood_2022_2024.csv`, `stage7_asap_on_*_flood_px_*.csv`, `stage7_geoepr_flood_exposure_2023.csv`, `STAGE7_GATE.md` |
| 8 | `synthesis.md`, `go_no_go.csv`, `STAGE8_GATE.md` |
| 9 | `STAGE9_HYPOTHESES.md`, `stage9_figures.ipynb`, `figures/stage9/` (argued figures) |
| 10–14 | `impact_panel.py`, `flood_admin2_month.csv`, `flood_admin2_year.csv`, `STAGE10_GATE.md`–`STAGE14_GATE.md`, `stage10_14_figures.ipynb` |
| Session A (15–18) | `SESSION_A_HYPOTHESES.md`, `impact_session_a.py`, `SESSION_A_CLOSEOUT.md`, `STAGE15_GATE.md`–`STAGE18_GATE.md`, `session_a_figures.ipynb`, `figures/session_a/` |
| Session B (19–22) | `SESSION_B_HYPOTHESES.md`, `impact_session_b.py`, `SESSION_B_CLOSEOUT.md`, `STAGE19_GATE.md`–`STAGE22_GATE.md`, `session_b_figures.ipynb`, `figures/session_b/`, `stage21_exposure_product.csv` |
| Session C (23–26) | `SESSION_C_HYPOTHESES.md`, `DEFERRED_DATASETS.md`, `impact_session_c.py`, `SESSION_C_CLOSEOUT.md`, `STAGE23_GATE.md`–`STAGE26_GATE.md`, `session_c_figures.ipynb`, `figures/session_c/`, `stage23_admin2_lhz.csv` |
| Session D (27–30) | `SESSION_D_HYPOTHESES.md`, `impact_session_d.py`, `SESSION_D_CLOSEOUT.md`, `STAGE27_GATE.md`–`STAGE30_GATE.md`, `session_d_figures.ipynb`, `figures/session_d/`, `stage27_ground_truth_target.csv`, `stage27_prediction_interface_spec.md` |
| Session E (31–34) | `SESSION_E_HYPOTHESES.md` (pre-registration, committed), `impact_session_e.py`, `within_county_demo.py`, `within_county_reliability.py`, `STAGE31_GATE.md`–`STAGE34_GATE.md` |

Paths: [`processing_data/paths.py`](../../processing_data/paths.py). Analysis deps: [`requirements-analysis.txt`](../../requirements-analysis.txt).
