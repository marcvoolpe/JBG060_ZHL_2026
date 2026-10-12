# Counting South Sudan's cropland: code and data (DRAFT of the submission README)

Draft, 11 Oct 2026. To finish once Rule 1 is frozen and the final notebook exists: fill the `[...]` parts, check every command on a fresh clone, and copy this file into the submission zip as `README.md`. The course asks for: one Jupyter notebook that runs the whole analysis, supporting `.py` files (one per functionality, commented), and a readme with the software and versions, the code organisation, the input and output folders, and how to run it.

## 1. What this code does

For ZOA International's two areas in South Sudan (the five Aweil counties and Bor South) it:
1. compares seven public cropland maps and the course's ASAP mask with each other, with the FAO/WFP crop assessment and with the 2022 and 2025 floods (EDA);
2. draws a stratified random sample of 450 points, which two group members label blind from satellite imagery;
3. estimates the cropland area of 2025 with a 95% interval, and scores every map (precision, recall, F1) on held-out points;
4. builds a readable rule-based cropland map (a small decision tree) and scores it the same way;
5. lays the 2025 flood over every map and over the sample, to show what the choice of map does to a "flood inundating cropland" trigger.

## 2. Software

- Python 3.12 (tested with 3.12.5 on Windows 11). Packages and versions: `cropland/requirements-cropland.txt`
  (`python -m pip install -r cropland/requirements-cropland.txt`).
- Google Earth Engine: a Google account and a Cloud project registered for non-commercial Earth Engine use; once: `earthengine authenticate`; then set the project: `set CROPLAND_EE_PROJECT=<your-project>` (Windows) or `export CROPLAND_EE_PROJECT=<your-project>` (macOS, Linux).
- The labelling tool needs only Python (no extra packages) and a browser.
- Optional for the report: an Overleaf account (`deliverables/cropland_report/report/`).

## 3. Data

| folder | what | in git? |
|---|---|---|
| `data-JBG060-2026/` (next to the repo) or `raw_data/` | course data from Zero Hunger Lab: admin boundaries, ASAP crop mask, NASA flood masks | no (download from Canvas) |
| `raw_data/cropland/eda/` | Earth Engine counts of every map on the flood grid (`*.npz`, ~55 MB), written by `eda_maps.py download` | no |
| `raw_data/cropland/` | other large outputs (benchmark models, exported maps) | no |
| `cropland/sample.csv`, `strata_areas.csv` | the 450 sample points (stratum, split, labellers) and the stratum areas | yes |
| `cropland/labels/` | every label, one file per labeller | yes |
| `cropland/features_sample.csv`, `embedding_sample.csv` | the 18 cue features and the Satellite Embedding per point | yes |
| `cropland/reference_*.csv` | CFSAM and FAOSTAT figures, published map accuracies (transcribed with table and page) | yes |
| `cropland/lol_river_osm.geojson` | the Lol river line (OpenStreetMap, ODbL) | yes |
| `cropland/results/` | scores, areas, flooded cropland (written by steps 09-10) | yes |
| `deliverables/cropland_report/tables/`, `deliverables/cropland_report/figures/` | EDA tables (CSV) and figures (PNG, not in git: rebuilt by the notebook) | CSV yes |

## 4. Code organisation (`cropland/`)

| file | functionality |
|---|---|
| `[pipeline.ipynb]` | **the notebook that runs everything** (to build; outline in section 6) |
| `eda_public_maps.ipynb` | EDA of the public maps (sections 1-10), labeller agreement, sample size, interval check |
| `common.py` | settings, study areas, the seven public maps as crop / not crop, Sentinel-2 monthly composites |
| `eda_maps.py` | EDA: Earth Engine export of map counts on the flood grid; crop shares, agreement, overlap, flood overlay, national and yearly analyses |
| `eda_figures.py` | all EDA figures |
| `eda_labels.py` | agreement between labellers (read-only) |
| `efficiency.py` | sample size and relative efficiency of sampling designs |
| `evaluation.py` | area interval (usual and adjusted), coverage simulation, error analysis, trigger agreement, ours vs published, design efficiency, rule readability |
| `00_pilot_points.py`, `01_compare_pilot.py` | pilot points in Twic county and the pilot agreement check |
| `02_strata_from_asap.py` | first look: ASAP crop share per county |
| `03_agreement_and_sample.py` | agreement map, strata, the 450-point sample, the split, labeller pairs |
| `04_image_strips.py` | image strips and curves for the labelling tool |
| `05_features.py`, `features.py` | the 18 cue features per point (and per pixel for the map) |
| `label_server.py`, `label_tool/` | the labelling tool (saves to `labels/`) |
| `06_merge_labels.py`, `model_data.py` | merge the two labels per point; the one table all models read |
| `07_fit_rules.py`, `rules.py` | Rule 1 (decision tree) and the benchmarks; rules as JSON, in Python and in Earth Engine |
| `08_run_map.py` | our cropland map in Earth Engine |
| `09_score.py`, `estimators.py` | accuracy of every map and the area estimate (stratified estimators) |
| `10_flood.py` | flooded cropland 2025 per map and from the sample |
| `test_cropland.py`, `test_evaluation.py` | checks (run before submitting) |

Report inputs: `deliverables/cropland_report/report/build_report_inputs.py` (numbers from the notebook into LaTeX, figures, Overleaf zip).

## 5. How to run

**Quick route (cached Earth Engine outputs, a few minutes):**
1. Put the course data next to the repo (`data-JBG060-2026/`) and the cached `raw_data/cropland/eda/*.npz` in place `[shared via ...]`.
2. `python -m pip install -r cropland/requirements-cropland.txt`
3. Open `cropland/[pipeline.ipynb]` in Jupyter or VS Code and run all cells (`RUN_EARTH_ENGINE = False`).
4. Checks: `python cropland/test_cropland.py` and `python cropland/test_evaluation.py`.

**Full route (from scratch, Earth Engine batch tasks, hours):** set `RUN_EARTH_ENGINE = True` and your project; the notebook starts the exports (`eda_maps.py export`), waits (`status`) and downloads them (`download`); the sampling, image, feature and map steps also run in Earth Engine. Labelling is done by people with the tool and cannot be rerun; the labels are in `labels/`.

## 6. Outline of the single notebook (to build)

| section | runs | output |
|---|---|---|
| 0. setup | paths, Earth Engine project, flags `RUN_EARTH_ENGINE`, `USE_CACHE` | |
| 1. the public maps (EDA) | `eda_maps.py`, `eda_figures.py` (as in `eda_public_maps.ipynb` 1-7) | figures 1-10, tables |
| 2. sampling design | `03_agreement_and_sample.py` (cached: `strata_areas.csv`, `sample.csv`) | strata areas, allocation |
| 3. what labellers see | `04_image_strips.py`, `05_features.py` (cached) | example strip, features |
| 4. labels | `06_merge_labels.py`, `eda_labels.py` | agreement, kappa, disagreements |
| 5. Rule 1 | `07_fit_rules.py` (frozen file `rule1_<date>.json`, printed as rules) | rules, cross-validation |
| 6. our map | `08_run_map.py` (cached assets) | map, national area per state |
| 7. scores and area | `09_score.py` + `evaluation.py` (adjusted interval, error analysis, ours vs published, readability) | area table, scorecard |
| 8. flood and trigger | `10_flood.py` + `evaluation.trigger_agreement` | flooded cropland, trigger table |
| 9. design and interval | `efficiency.py`, `evaluation.design_efficiency`, coverage simulation | points needed, coverage |
| 10. key numbers | `key_numbers.csv`, `deliverables/cropland_report/report/build_report_inputs.py` | `numbers.tex` |

Scripts with numbers in their names are run from the notebook with `%run cropland/09_score.py cropland/rule1_<date>.json` (or `importlib.import_module("09_score")`).

## 7. Reproducibility

- Fixed seeds (42) for the sample, the split and the labeller pairs; the methodology was frozen before labelling and every change is dated in `cropland/METHODOLOGY.md`.
- Rule 1 is frozen in a dated JSON file before any test label is used; the same file drives the scores and the Earth Engine map (`test_cropland.py --ee` checks they agree).
- Earth Engine collections can be reprocessed by their providers; we used them on `[dates]`. Cached exports reproduce our numbers exactly.
- Labels are human judgements: they are data, not code, and are kept as recorded (disagreements included).
