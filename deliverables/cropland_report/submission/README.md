# Counting cropland for a flood trigger in South Sudan: code and data

JBG060 2026, group 1 (Marc, Matei, Matteo, Wei Jin and Yassin), for the Zero Hunger Lab, with ZOA International.

**To reproduce every result of our report and poster, run one notebook: `cropland/pipeline.ipynb`** (10 to 25 minutes on a laptop, no account needed).

## 1. Introduction

A flood trigger for anticipatory action fires when a flood covers enough cropland, so it depends on the cropland map. The public maps disagree widely in ZOA's two areas (the five Aweil counties and Bor South). This code:

1. compares seven public cropland maps and the course's ASAP crop mask (exploratory data analysis);
2. draws a stratified random sample of 450 boxes of 210 m, which two of us labelled blind with a labelling tool that is part of the code;
3. estimates the 2025 cropland area with a 95% interval and scores every map on held-out test points;
4. fits a readable two-question rule (Rule 1) on the calibration points and maps it with Google Earth Engine;
5. lays the floods of 2000-2025 over every map and over the sample, and checks whether a trigger would fire.

## 2. Installation

You need **Python 3.12** (tested with 3.12.5 on Windows 11). From the folder that holds this README:
```
python -m venv .venv
.venv\Scripts\activate                 (macOS, Linux: source .venv/bin/activate)
python -m pip install -r cropland/requirements-cropland.txt
python -m pip install jupyterlab       (or use VS Code with its Jupyter extension)
```
`requirements-cropland.txt` pins every version we ran (pandas 2.2.3, NumPy 2.1.2, scikit-learn 1.5.2, GeoPandas 1.2.0, rasterio 1.5.0, matplotlib 3.9.2, earthengine-api 1.7.46 and others).

**Course data** (not in the zip; from the course's SURFdrive): the folders `Administrative boundaries/`, `farmland/` (`asap_mask_crop_v04.tif`) and `flood_masks/` (`compact_recurring/`, `compact_unusual/`). Copy these three folders into the `raw_data/` folder that comes with the zip, so that `raw_data/flood_masks/` exists (`raw_data/cropland/` stays where it is). Alternatively, keep them in a folder `data-JBG060-2026/` next to the unzipped folder, or anywhere named by the environment variable `CROPLAND_COURSE_DATA` (set before starting Jupyter).

**Google Earth Engine** is optional: only to repeat the steps that query it (section 3.3). It needs a Google account with a Cloud project registered for Earth Engine, `earthengine authenticate` once, and `CROPLAND_EE_PROJECT=<your-project>`.

## 3. Usage

### 3.1 Run the notebook

Start `jupyter lab` in the activated environment (or, in VS Code, pick the `.venv` interpreter as the kernel), then open `cropland/pipeline.ipynb` and run all cells, with `RUN_EARTH_ENGINE = False` (its first code cell). Or, from the folder that holds this README:
```
python -c "import nbformat, nbclient; nb = nbformat.read('cropland/pipeline.ipynb', 4); nbclient.NotebookClient(nb, timeout=3600, resources={'metadata': {'path': 'cropland'}}).execute(); nbformat.write(nb, 'cropland/pipeline.ipynb')"
```

| part | runs | gives |
|---|---|---|
| 0 | setup | paths, a check that the inputs are there, package versions |
| 1 | `eda_maps.py`, `eda_figures.py`, `eda_labels.py`, `efficiency.py`, `eda_window.py` | the public maps compared; figures 1-11, 16, 25 |
| 2 | steps 01, 02, 06 | pilot, labels merged; figures 17, 22-24 |
| 3 | step 07 (refit, checked against the frozen file), step 12 | Rule 1 and the other models; figures 18, 19, 21 |
| 4 | step 09 | the area with its interval, every map's score; figure 20 |
| 5 | steps 10b, 10c, the exposure table | past floods, the trigger hindcast; figures 12, 13 |
| 6 | step 11, `sensitivity.py` | adjusted interval, robustness checks; figures 14, 15, 26 |
| 7 | `national_map.py` | our map over the whole country; figure 27 |
| 8 | `14_dashboard.py` | `dashboard.html` |
| 9 | `test_cropland.py`, `test_evaluation.py` | checks of the estimators, rules and code |
| 10 | `key_results.py` | every number the report and the poster quote, with its source file |

Example result (end of part 10): "Aweil: 3.8% of the land is cropland (116,500 ha; 95% interval 76,700 to 156,400 ha; adjusted upper bound 183,100 ha). Rule 1: F1 0.72 on 186 Aweil test points; the best public map, WorldCereal 2021: 0.55."

### 3.2 Run one step

Each step also runs alone from the folder that holds this README; its docstring says what it reads and writes. For example:
```
python cropland/09_score.py --cached cropland/rule1_2026-10-12.json      (scores and areas, no Earth Engine)
python cropland/10b_flood_history.py summary                             (past floods and the trigger hindcast)
python cropland/label_server.py                                          (the labelling tool, in the browser)
```

### 3.3 The Earth Engine steps (run once, saved in the zip)

Steps 03 (strata and sample), 04 (images for the labelling tool), 05 (features), 08 (our map), 10 and 10b (flood overlays), the EDA exports and the national map queried Earth Engine once; their outputs are in `raw_data/cropland/` and `cropland/results/`. The commands are in each file's docstring. **Do not rerun steps 03, 07 or `12_other_models.py freeze`** on our study: they draw a new sample or refreeze the models. For another area, see `cropland/REUSE.md`.

### 3.4 What a run reproduces

Run from a fresh copy of the zip, the notebook rewrote every result table and figure byte for byte on our machine; on other systems tables agree to rounding and figure fonts can differ. Seeds are fixed (42). Two known limits of the code: the precision bounds in figure 15 treat every crop call as an equal trial, so they are optimistic; and the adjusted upper bound of the area is a cautious heuristic, not a guaranteed 95% bound.

## 4. Organisation

```
README.md                      this file
cropland/                      code, notebook, our data and results
  results/                     result tables (output)
  labels/                      every label, one file per labeller (input)
  config/                      the study's settings
  label_tool/, dashboard/      pages of the labelling tool and the dashboard
raw_data/cropland/             saved Earth Engine outputs (input)
deliverables/cropland_report/  figures/, tables/, maps/, dashboard.html (output)
```

### 4.1 The code (`cropland/`)

| file | functionality |
|---|---|
| `pipeline.ipynb` | the notebook that runs the whole analysis |
| `common.py` | settings, paths, study areas, the public maps, Sentinel-2 composites |
| `eda_maps.py`, `eda_figures.py`, `eda_labels.py`, `eda_window.py`, `efficiency.py` | exploratory analysis of the maps, labeller agreement, sample size |
| `00`-`02` | pilot points, pilot agreement, a first look at ASAP |
| `03_agreement_and_sample.py` | strata, the 450-point sample, calibration/test split, labeller pairs |
| `04_image_strips.py`, `label_server.py`, `label_tool/` | images and the labelling tool |
| `05_features.py`, `features.py` | the 18 features per box |
| `06_merge_labels.py`, `model_data.py` | the two labels per point merged; the table every model reads |
| `07_fit_rules.py`, `rules.py`, `12_other_models.py` | Rule 1, benchmark forests, logistic regressions |
| `08_run_map.py` | our map in Earth Engine |
| `09_score.py`, `estimators.py` | scores and the area estimate |
| `10_flood.py`, `10b_flood_history.py`, `10c_flood_map.py` | flooded cropland, past floods, the 2022 flood map |
| `11_evaluate.py`, `evaluation.py`, `sensitivity.py` | adjusted interval, error analysis, robustness checks |
| `national_check.py`, `national_map.py` | our map over the whole country |
| `report_figures.py` | figures 17-26 |
| `key_results.py` | every number in the report and on the poster, with its source |
| `14_dashboard.py` | the offline results dashboard |
| `test_cropland.py`, `test_evaluation.py` | checks |
| `make_new_area.py`, `config/TEMPLATE.toml`, `REUSE.md` | reuse in another area or season |
| `METHODOLOGY.md`, `LABELLING_GUIDE.md` | the method, fixed before labelling; the labelling key |
| `tree_workbench.ipynb` | a separate tool for building another model; not part of the analysis |

### 4.2 Data

| | where | what |
|---|---|---|
| input | `cropland/sample.csv`, `strata_areas.csv` | the 450 points and the area of every stratum |
| input | `cropland/labels/` | every label; the five labellers are the letters A-E |
| input | `cropland/features_sample.csv`, `embedding_sample.csv` | the features per box |
| input | `cropland/rule1_2026-10-12.json`, `logistic_*.json` | the frozen models |
| input | `cropland/reference_*.csv` | FAO/WFP and FAOSTAT figures, published map accuracies |
| input | `raw_data/cropland/`, `cropland/results/map_values.csv` | saved Earth Engine outputs |
| output | `cropland/results/` | scores, areas, floods, evaluation tables |
| output | `deliverables/cropland_report/` | figures 1-27, tables (`key_results.csv`: every quoted number), the 2022 flood map, `dashboard.html` |

### 4.3 Not included

`raw_data/cropland/eda/national.npz` (50 MB) and the labelling images (`cropland/label_tool/img/`, 80 MB). Without them the notebook keeps the national flood rows and figure 24 as saved. Ask us for either.

## 5. Troubleshooting

- **"course data not found":** set `CROPLAND_COURSE_DATA` (section 2), then restart Jupyter.
- **`ModuleNotFoundError`:** the notebook runs in another Python; pick the `.venv` kernel.
- **Installation fails:** use Python 3.12.
- **Activation blocked in PowerShell:** run `Set-ExecutionPolicy -Scope Process Bypass` first, or use Command Prompt.
- **"DLL load failed ... too long" for rasterio (Windows):** unzip into a shorter folder, such as `C:\cropland\`.
- **Part 3 takes 5 to 20 minutes:** step 12 cross-validates eight models 20 x 5 times.
- **"national.npz: no" or "figure 24 stays as saved":** expected (section 4.3).

## 6. Credits

**Data:** the course data of the Zero Hunger Lab (NASA MCDWD flood masks, ASAP crop mask, boundaries); ESA WorldCover, GLAD, Digital Earth Africa, ESA WorldCereal, Esri land cover, Google Dynamic World and USGS GFSAD cropland maps; Copernicus Sentinel-1 and -2 with Cloud Score+, Google Open Buildings, Google Satellite Embedding, JRC Global Surface Water and MODIS burned area, all through Google Earth Engine; OpenStreetMap (Lol river); FAO/WFP crop assessments and FAOSTAT. Methods are cited in the docstrings where they are used (Olofsson et al. 2014; Stehman 2014; Cohen 1960).

**Statement on the use of AI.** This course follows the TU/e AI policy. We used Claude Code (Anthropic, model Claude Opus 5.5) and ChatGPT Astra (OpenAI) for the following purposes: brainstorming; iterative data analysis until we found the gap in the data; writing and debugging the analysis code, the labelling tool and the figures; and drafting and editing parts of the report and this README. It let us try many ideas quickly before we settled on this approach. We decided which ideas to use and checked the results. We labelled all 900 boxes ourselves, and every number in the report is computed by our code from the data. No data or labels were generated with AI.

**Acknowledgements:** the Zero Hunger Lab and ZOA International, for the question, the data and their answers.

## 7. Legal and ethical considerations

- For research and education only: not validated for operational decisions, and our map is checked only in the two study areas. The report lists the limits.
- No information on any person or household in South Sudan. The five of us who labelled appear only as the letters A-E.
- Each dataset is used under its provider's terms (WorldCover, Dynamic World, Esri land cover and Open Buildings CC BY 4.0; OpenStreetMap ODbL). The course data is not redistributed.
