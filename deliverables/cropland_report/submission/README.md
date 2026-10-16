# Counting cropland for a flood trigger in South Sudan: code and data

JBG060 2026, group 1 (Marc, Matei, Matteo, Wei Jin and Yassin), for ZOA International and the Zero Hunger Lab.

This is the code behind our methodological report. **`cropland/pipeline.ipynb` runs the whole analysis**, in order. Each step is a commented `.py` file in `cropland/`, one per functionality. The notebook calls each step the way the command line would and shows what it prints, its tables and its figures.

## 1. What the code does

For ZOA's two areas in South Sudan (the five Aweil counties and Bor South) it:

1. compares seven public cropland maps and the course's ASAP crop mask with each other, with the FAO/WFP crop assessment (CFSAM) and with past floods (the EDA);
2. draws a stratified random sample of 450 boxes of 210 m by 210 m. Two of us labelled each box blind from satellite images, with a labelling tool that is part of the code;
3. estimates the cropland area of 2025 with a 95% interval and scores every map (precision, recall, F1) on held-out test points;
4. fits a readable two-question rule (Rule 1, a depth-2 decision tree) on the calibration points, maps it with Earth Engine, and scores it the same way;
5. lays past floods (2000-2025) over every map and over the sample, to show what the choice of map does to a "flood covers cropland" trigger;
6. builds the report's figures, tables and numbers, and an offline results dashboard.

## 2. Software and versions

- **Python 3.12** (tested with 3.12.5 on Windows 11, 16 Oct 2026). The packages and the versions we ran are in `cropland/requirements-cropland.txt`:

  | package | version | package | version |
  |---|---|---|---|
  | pandas | 2.2.3 | rasterio | 1.5.0 |
  | numpy | 2.1.2 | pyarrow | 24.0.0 |
  | scipy | 1.14.1 | pyogrio | 0.13.0 |
  | scikit-learn | 1.5.2 | pyproj | 3.8.0 |
  | matplotlib | 3.9.2 | affine | 3.0.1 |
  | geopandas | 1.2.0 | joblib | 1.4.2 |
  | shapely | 2.1.2 | pillow | 11.0.0 |
  | earthengine-api | 1.7.46 | nbformat, nbclient, ipykernel | 5.11.1, 0.11.0, 6.29.5 |

  Install them in a fresh environment:

  ```
  python -m venv .venv
  .venv\Scripts\activate              (macOS, Linux: source .venv/bin/activate)
  python -m pip install -r cropland/requirements-cropland.txt
  ```

  To open the notebook you also need Jupyter (`python -m pip install jupyterlab`) or VS Code with its Jupyter extension.
- **Google Earth Engine**: only to repeat the steps that query it (section 5, full route). It needs a Google account and a Cloud project registered for non-commercial Earth Engine use. Once: `earthengine authenticate`. Then name your project: `set CROPLAND_EE_PROJECT=<your-project>` (Windows) or `export CROPLAND_EE_PROJECT=<your-project>` (macOS, Linux).
- The labelling tool needs only Python (no extra package) and a browser: `python cropland/label_server.py`.

## 3. Input data

| where | what | included? |
|---|---|---|
| the course data folder | from the course's SURFdrive download (link on Canvas): `Administrative boundaries/` (`ssd_admin0/1/2.geojson`), `farmland/asap_mask_crop_v04.tif`, `flood_masks/compact_recurring/` and `compact_unusual/` (`flood_events_<tile>_<year>.parquet`) | **no**: download it |
| `cropland/sample.csv`, `strata_areas.csv` | the 450 sample points (area, stratum, calibration or test, the two labellers) and the area of every stratum | yes |
| `cropland/labels/` | every label as given, one file per labeller (pilot and sample) | yes |
| `cropland/features_sample.csv`, `embedding_sample.csv` | the 18 cue features and Google's Satellite Embedding per box | yes |
| `cropland/rule1_2026-10-12.json`, `logistic_*_2026-10-12.json` | the frozen models (rules in plain JSON) | yes |
| `cropland/reference_*.csv` | CFSAM and FAOSTAT figures and the published accuracy of the same maps, transcribed with table and page | yes |
| `cropland/config/south_sudan_2025.toml` | our settings: areas, year, crop calendar, allocation, strata maps | yes |
| `cropland/lol_river_osm.geojson`, `national_check/candidates.csv` | the Lol river (OpenStreetMap, ODbL); 20,000 random points with every map's value | yes |
| `cropland/results/map_values.csv` | every map's value at the 450 points, as Earth Engine gave it (read by step 09 without Earth Engine) | yes |
| `raw_data/cropland/` | the saved Earth Engine outputs: map counts on the flood grid (`eda/*.npz`, `eda/national_by_county.pkl`), Rule 1 per flood cell (`flood_history_rule1_*.csv`), the benchmark forests (`benchmarks.joblib`) | yes, except `eda/national.npz` (about 50 MB) |
| `cropland/label_tool/img/` | the image strips the labellers saw (about 80 MB) | no: shared as a zip on request |

**Where the code looks for the course data**, in this order: the folder named by the environment variable `CROPLAND_COURSE_DATA`; `raw_data/` in the repository (as the course README sets it up); `data-JBG060-2026/` next to the repository. For example: `set CROPLAND_COURSE_DATA=D:\data-JBG060-2026` (Windows) or `export CROPLAND_COURSE_DATA=~/data-JBG060-2026` (macOS, Linux), before you start Jupyter.

Without `eda/national.npz` the notebook reads the national flood rows of section 1.5 back from their saved table. Without the image strips it keeps figure 24 as saved. Everything else is recomputed.

## 4. Code organisation (`cropland/`)

| file | functionality |
|---|---|
| **`pipeline.ipynb`** | **the notebook that runs everything**, parts 0-10 (below) |
| `common.py` | settings from the config, paths, study areas, the seven public maps as crop / not crop, Sentinel-2 monthly composites |
| `config/`, `make_new_area.py`, `REUSE.md` | settings of our study, a template, and how to run the same check in another area or country |
| `eda_maps.py` | EDA: Earth Engine export of every map's counts on the flood grid; crop shares, agreement, overlap, flood overlay, national and yearly analyses |
| `eda_figures.py` | the charts (figures 1-12, 14, 15) |
| `eda_labels.py` | agreement between the labellers |
| `eda_window.py` | the same 6 km window in every map (figure 16) |
| `efficiency.py` | sample size and the efficiency of sampling designs |
| `00_pilot_points.py`, `01_compare_pilot.py` | pilot points in Twic county and the pilot agreement check |
| `02_strata_from_asap.py` | first look: ASAP crop share per county |
| `03_agreement_and_sample.py` | agreement map, strata, the 450-point sample, the calibration/test split, the labeller pairs |
| `04_image_strips.py` | image strips and curves for the labelling tool |
| `05_features.py`, `features.py` | the 18 cue features per box (and per pixel for the map) |
| `label_server.py`, `label_tool/`, `LABELLING_GUIDE.md` | the labelling tool (saves to `labels/`) and its guide |
| `06_merge_labels.py`, `model_data.py` | merge the two labels per point (no tiebreak); the one table every model reads |
| `07_fit_rules.py`, `rules.py` | Rule 1 (decision tree) and the benchmark forests; rules as JSON, applied in Python and in Earth Engine |
| `12_other_models.py` | logistic regressions and other trees, chosen by cross-validation on the calibration points |
| `08_run_map.py` | our cropland map in Earth Engine (checked against Python first) |
| `09_score.py`, `estimators.py` | every map's score and the area estimate (stratified estimators) |
| `10_flood.py` | flooded cropland in 2025 per map and from the sample |
| `10b_flood_history.py` | past floods 2000-2025 on today's cropland, and a trigger hindcast |
| `10c_flood_map.py` | the 2022 flood in Aweil before and after (figure 13, interactive map) |
| `11_evaluate.py`, `evaluation.py` | adjusted area interval, error analysis, ours against published scores, points needed, rule readability, trigger agreement |
| `sensitivity.py` | robustness checks that change nothing frozen |
| `national_check.py`, `national_map.py` | our map over the whole country, against the public maps at 20,000 random points (figure 27) |
| `report_figures.py` | figures 17-26 |
| `14_dashboard.py`, `dashboard/template.html` | the offline results dashboard |
| `test_cropland.py`, `test_evaluation.py` | checks of the estimators, rules, sample, label merge and evaluation code |
| `tree_workbench.ipynb` | a workbench for teammates to build another model (not needed for the results) |
| `METHODOLOGY.md` | the study's rules, fixed before labelling, with a dated log of every change |

Outside `cropland/`: `deliverables/cropland_report/report/build_report_inputs.py` writes the numbers, tables and references into the LaTeX report.

The notebook, part by part:

| part | runs | output |
|---|---|---|
| 0. setup | paths, the flag `RUN_EARTH_ENGINE`, checks that the inputs are there | |
| 1. the public maps (EDA) | `eda_maps.py`, `eda_figures.py`, `eda_labels.py`, `efficiency.py`, `eda_window.py` | figures 1-11, 16, 25; tables; key numbers |
| 2. sample, labels, features | steps 01, 02, 06 (00, 03-05 saved) | label table, model table; figures 17, 22-24 |
| 3. models | Rule 1 refitted and checked against the frozen file (07), step 12 (08 saved) | figures 18, 19, 21 |
| 4. area and scores | step 09 | `results/area.csv`, `accuracy.csv`; figure 20 |
| 5. floods and the trigger | steps 10b and 10c (10 saved) | flood history, hindcast; figures 12, 13; interactive map |
| 6. evaluation and checks | step 11, `sensitivity.py` | adjusted interval, error analysis; figures 14, 15, 26 |
| 7. the whole country | `national_map.py compare`, `figure` | figure 27 |
| 8. dashboard and report | `14_dashboard.py`, `build_report_inputs.py` | `dashboard.html`, the report's numbers |
| 9. checks | `test_cropland.py`, `test_evaluation.py` | |
| 10. headline numbers | | the area and the best scores |

## 5. How to run

**Quick route (about 8 minutes, no Earth Engine):**
1. Clone or unzip the repository and install the packages (section 2).
2. Put the course data in place (section 3).
3. Open `cropland/pipeline.ipynb` in Jupyter or VS Code and run all cells. Keep `RUN_EARTH_ENGINE = False`.

   Without an editor, from the repository root:
   ```
   python -c "import nbformat, nbclient; nb = nbformat.read('cropland/pipeline.ipynb', 4); nbclient.NotebookClient(nb, timeout=3600, resources={'metadata': {'path': 'cropland'}}).execute(); nbformat.write(nb, 'cropland/pipeline.ipynb')"
   ```
4. The checks alone: `python cropland/test_cropland.py` and `python cropland/test_evaluation.py`.
5. One step alone, from the repository root, as the notebook runs it: for example `python cropland/09_score.py --cached cropland/rule1_2026-10-12.json` (the scores and areas, without Earth Engine) or `python cropland/10b_flood_history.py summary`. Each file's docstring says what it reads, writes and how to run it.

The quick route recomputes everything from the labels and the saved Earth Engine outputs, and writes the same files again. On our machine the rerun reproduces the scores and areas exactly.

**Full route (Earth Engine, several hours of batch tasks).** With `RUN_EARTH_ENGINE = True` the notebook also queries Earth Engine again for the maps' values at the points (step 09), the 2025 flood overlay (step 10) and any missing EDA export. The steps below ran once from the command line (repository root), in this order; their outputs are the saved files of section 3:

| step | command | writes |
|---|---|---|
| EDA exports | `python cropland/eda_maps.py export`, then `status`, then `download` | `raw_data/cropland/eda/*.npz` |
| 3 | `python cropland/03_agreement_and_sample.py export`, then `... sample` | strata asset, `strata_areas.csv`, `sample.csv` |
| 4 | `python cropland/04_image_strips.py sample` | `label_tool/img/`, `label_tool/data_sample.js` |
| 5 | `python cropland/05_features.py sample` | `features_sample.csv`, `embedding_sample.csv` |
| 7 | `python cropland/07_fit_rules.py` | `rule1_<date>.json`, `raw_data/cropland/benchmarks.joblib` |
| 8 | `python cropland/08_run_map.py cropland/rule1_2026-10-12.json` | our map (Earth Engine assets) |
| 10b | `python cropland/10b_flood_history.py model cropland/rule1_2026-10-12.json` | `raw_data/cropland/flood_history_rule1_*.csv` |
| national | `python cropland/national_check.py points cropland/rule1_2026-10-12.json`; `python cropland/national_map.py summary cropland/rule1_2026-10-12.json` (also `score`, `fetch`) | `national_check/candidates.csv`, `results/rule1_*.csv`, `raw_data/cropland/eda/national_rule1_1km.npz` |
| window | `python cropland/eda_window.py fetch` | `raw_data/cropland/eda/window_*.npz` |

**Do not rerun steps 03, 07 or `12 ... freeze` on our study.** Step 03 would draw a new sample that nobody labelled. Steps 07 and 12 freeze models, and we froze ours before reading any test label. Part 3 of the notebook refits Rule 1 without saving it and checks that it equals the frozen file. For another area or country, start from a clean copy (`REUSE.md`).

## 6. Output folders

| folder | what |
|---|---|
| `cropland/results/` | scores (`accuracy.csv`), areas (`area.csv`, `area_adjusted.csv`), map values at the points, floods (`flooded_cropland.csv`, `flood_history.csv`, `trigger_hindcast.csv`), evaluation and sensitivity tables, our map over the country |
| `cropland/` | `labels_final.csv`, `labels_merged.csv`, `disagreements.csv`, `model_table.csv` (step 06), `asap_crop_share_by_county.csv` (step 02) |
| `deliverables/cropland_report/tables/` | every EDA table, each figure's CSV twin, `key_numbers.csv` |
| `deliverables/cropland_report/figures/` | figures 1-27 of the report (PNG) |
| `deliverables/cropland_report/maps/`, `dashboard.html` | the interactive 2022 flood map (its satellite background needs internet) and the results dashboard (open with a double click, works offline) |
| `deliverables/cropland_report/report/` | the LaTeX report: its number and table blocks, `numbers.tex`, `results.tex`, `app_*.tex`, `overleaf_upload.zip` |

## 7. Reproducibility

- Fixed seeds (42) for the sample, the split, the labeller pairs and every model. The method was fixed in `cropland/METHODOLOGY.md` before labelling. Every later change is dated in its change log.
- Rule 1 was frozen in a dated JSON file before any test label was read. The same file drives the scores and the Earth Engine map (`python cropland/test_cropland.py --ee` checks that they agree).
- We queried Earth Engine between 30 Sep and 14 Oct 2026: the sample and its features first, the maps at the points on 12 Oct, the floods and the national map on 14 Oct. Providers can reprocess their collections, so a new query can differ slightly. The saved outputs reproduce our numbers exactly.
- The labels are human judgements. They are data, not code, and are kept as given, disagreements included. Their known errors are listed in the long version of the report (`report_draft.tex`, appendix B).
