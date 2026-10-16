# Counting cropland for a flood trigger in South Sudan: code and data

JBG060 2026, group 1 (Marc, Matei, Matteo, Wei Jin and Yassin), for ZOA International and the Zero Hunger Lab.

**To reproduce everything, run one notebook: `cropland/pipeline.ipynb`** (about 8 minutes, no account needed). The rest of this file says what you need, how to run it and where everything is.

## 1. Introduction and overview

ZOA plans a flood trigger for anticipatory action in South Sudan: act when a flood covers enough cropland. How much cropland a flood covers depends on the cropland map, and the public maps disagree widely in ZOA's two areas (the five Aweil counties and Bor South). Nobody had checked them there. This code checks them against a labelled sample, measures the cropland area, and shows what the choice of map does to the trigger.

What it does, in order:

1. compares seven public cropland maps and the course's ASAP crop mask with each other, with the FAO/WFP crop assessment (CFSAM) and with past floods (the exploratory data analysis, EDA);
2. draws a stratified random sample of 450 boxes of 210 m by 210 m. Two of us labelled each box blind from satellite images, with a labelling tool that is part of the code;
3. estimates the cropland area of 2025 with a 95% interval, and scores every map (precision, recall, F1) on held-out test points;
4. fits a readable two-question rule (Rule 1, a depth-2 decision tree) on the calibration points, maps it with Google Earth Engine and scores it the same way;
5. lays the floods of 2000-2025 over every map and over the sample, and asks whether each map would fire a trigger;
6. draws every figure and table of our report and poster, lists every number the report and the poster quote with the file it comes from, and builds an offline results dashboard.

Main features:
- one notebook runs the whole analysis from the data in this zip, and every step is a commented `.py` file (one per functionality);
- the model was frozen before any test label was read;
- the Earth Engine outputs are saved, so no account is needed;
- a reuse kit runs the same check in another area or country.

## 2. Installation

You need **Python 3.12** (we used 3.12.5 on Windows 11; the steps are the same on macOS and Linux). Other Python versions are untested: the pinned packages may have no build for them.

1. **Unzip** the submission. Keep the folder structure: the code finds its files relative to this README.
2. **Create an environment and install the packages** from the folder that holds this README:
   ```
   python -m venv .venv
   .venv\Scripts\activate                 (macOS, Linux: source .venv/bin/activate)
   python -m pip install -r cropland/requirements-cropland.txt
   python -m pip install jupyterlab       (or use VS Code with its Jupyter extension)
   ```
   `cropland/requirements-cropland.txt` pins every package we ran:

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

3. **Add the course data.** It is not in the zip. Download it from the course's SURFdrive (link and password on Canvas). The code needs three of its folders: `Administrative boundaries/` (`ssd_admin0.geojson`, `ssd_admin1.geojson`, `ssd_admin2.geojson`), `farmland/asap_mask_crop_v04.tif` and `flood_masks/` (`compact_recurring/` and `compact_unusual/`, files `flood_events_<tile>_<year>.parquet`). Put them in one of these places; the code looks in this order:
   - any folder, named by the environment variable `CROPLAND_COURSE_DATA`, set before you start Jupyter. Windows: `set CROPLAND_COURSE_DATA=D:\data-JBG060-2026`. macOS, Linux: `export CROPLAND_COURSE_DATA=~/data-JBG060-2026`;
   - `raw_data/` next to `cropland/` (the three folders directly inside it, as the course's own README sets it up);
   - a folder `data-JBG060-2026/` next to the unzipped folder.
4. **Optional, Google Earth Engine:** only to repeat the steps that query it (section 3.3). It needs a Google account and a Cloud project registered for non-commercial Earth Engine use. Once: `earthengine authenticate`. Then: `set CROPLAND_EE_PROJECT=<your-project>` (macOS, Linux: `export ...`).

## 3. Usage and examples

### 3.1 Run the notebook (reproduces everything)

Start Jupyter in the environment (`jupyter lab`), open `cropland/pipeline.ipynb` and run all cells. Keep `RUN_EARTH_ENGINE = False` (its first code cell). Or run it without opening it, from the folder that holds this README:
```
python -c "import nbformat, nbclient; nb = nbformat.read('cropland/pipeline.ipynb', 4); nbclient.NotebookClient(nb, timeout=3600, resources={'metadata': {'path': 'cropland'}}).execute(); nbformat.write(nb, 'cropland/pipeline.ipynb')"
```

The notebook runs every step in order, in ten parts. It shows what each step prints, its tables and its figures, and writes them to the output folders (section 4.4):

| part | runs | gives |
|---|---|---|
| 0. setup | paths, the flag `RUN_EARTH_ENGINE`, checks that the inputs are there | the package versions in use |
| 1. the public maps (EDA) | `eda_maps.py`, `eda_figures.py`, `eda_labels.py`, `efficiency.py`, `eda_window.py` | figures 1-11, 16, 25; the EDA tables |
| 2. sample, labels, features | steps 01, 02, 06 (00, 03-05 saved) | the label and model tables; figures 17, 22-24 |
| 3. models | Rule 1 refitted and checked against the frozen file (07), step 12 (08 saved) | figures 18, 19, 21 |
| 4. area and scores | step 09 | the cropland area with its interval, every map's score; figure 20 |
| 5. floods and the trigger | steps 10b, 10c (10 saved), the exposure table | past floods, the trigger hindcast, households; figures 12, 13; the interactive map |
| 6. evaluation and checks | step 11, `sensitivity.py` | the adjusted interval, error analysis, robustness checks; figures 14, 15, 26 |
| 7. the whole country | `national_map.py compare`, `figure` | figure 27 |
| 8. dashboard | `14_dashboard.py` | `dashboard.html` |
| 9. checks | `test_cropland.py`, `test_evaluation.py` | every check passes |
| 10. the numbers in the report and poster | `key_results.py` | every number the report and the poster quote, with its source file |

**Example result** (the end of part 10): "Aweil: 3.8% of the land is cropland (116,500 ha, 95% interval 76,700 to 183,100 ha). Rule 1: F1 0.72 on 186 Aweil test points; the best public map, WorldCereal 2021: 0.55." Open `deliverables/cropland_report/dashboard.html` (double click) for all results on one page.

### 3.2 Run one step

Every step also runs alone from the folder that holds this README, as the notebook runs it. Each file's docstring says what it reads, writes and how to run it. Examples:
```
python cropland/09_score.py --cached cropland/rule1_2026-10-12.json      (scores and areas; --cached: no Earth Engine)
python cropland/10b_flood_history.py summary                             (past floods and the trigger hindcast)
python cropland/10c_flood_map.py aweil 2022 rule1 1                      (area, year, model, minimum flood days)
python cropland/national_map.py compare                                  (our map against the public maps nationally)
python cropland/test_cropland.py                                         (checks; add --ee to compare Earth Engine with Python)
python cropland/label_server.py                                          (the labelling tool, in the browser)
```
Settings:
- `RUN_EARTH_ENGINE`, in the notebook;
- the environment variable `CROPLAND_COURSE_DATA` (section 2);
- `CROPLAND_EE_PROJECT`, your Earth Engine project;
- `CROPLAND_CONFIG`, another study area (see `cropland/REUSE.md`).

### 3.3 The Earth Engine steps (once, several hours)

These steps queried Earth Engine once. Their outputs are saved in the zip (section 4.2), so the notebook does not repeat them. With `RUN_EARTH_ENGINE = True` the notebook queries Earth Engine again for the maps' values at the points (step 09), the 2025 flood overlay (step 10) and any missing EDA export. The rest run from the command line, in this order:

| step | command | writes |
|---|---|---|
| EDA exports | `python cropland/eda_maps.py export`, then `status`, then `download` | `raw_data/cropland/eda/*.npz` |
| 3 | `python cropland/03_agreement_and_sample.py export`, then `... sample` | strata, `strata_areas.csv`, `sample.csv` |
| 4 | `python cropland/04_image_strips.py sample` | the images of the labelling tool |
| 5 | `python cropland/05_features.py sample` | `features_sample.csv`, `embedding_sample.csv` |
| 7 | `python cropland/07_fit_rules.py` | `rule1_<date>.json`, `raw_data/cropland/benchmarks.joblib` |
| 8 | `python cropland/08_run_map.py cropland/rule1_2026-10-12.json` | our map (Earth Engine assets) |
| 10 | `python cropland/10_flood.py cropland/rule1_2026-10-12.json` | `results/flooded_cropland.csv` (needs step 8 in your project) |
| 10b | `python cropland/10b_flood_history.py model cropland/rule1_2026-10-12.json` | `raw_data/cropland/flood_history_rule1_*.csv` |
| national | `python cropland/national_check.py points cropland/rule1_2026-10-12.json`; `python cropland/national_map.py summary cropland/rule1_2026-10-12.json` (also `score`, `fetch`) | `national_check/candidates.csv`, `results/rule1_*.csv`, `raw_data/cropland/eda/national_rule1_1km.npz` |
| window | `python cropland/eda_window.py fetch` | `raw_data/cropland/eda/window_*.npz` |

**Do not rerun steps 03, 07 or `12_other_models.py freeze` on our study.** Step 03 would draw a new sample that nobody labelled. Steps 07 and 12 freeze models, and we froze ours before reading any test label. Part 3 of the notebook refits Rule 1 without saving it and checks that it equals the frozen file. For another area or country, start from a clean copy (`cropland/REUSE.md`).

### 3.4 What a run reproduces

From the zip, the notebook rewrites every result table, EDA table and figure byte for byte. We checked this on a fresh copy, without the two files that are not included (section 4.3).
- Seeds are fixed (42) for the sample, the split, the labeller pairs and every model.
- The method was fixed in `cropland/METHODOLOGY.md` before labelling, and every later change is dated in its change log.
- Earth Engine was queried between 30 Sep and 14 Oct 2026. Providers can reprocess their collections, so a new query (section 3.3) can differ slightly.

## 4. Organisation of the code and data

```
README.md                      this file
cropland/                      all code, the notebook, our data and the results
  results/                     result tables (output)
  labels/                      every label, one file per labeller (input)
  config/                      the study's settings
  label_tool/, dashboard/      the labelling tool's page, the dashboard's page
  national_check/              20,000 random points with every map's value (input)
raw_data/cropland/             the saved Earth Engine outputs (input)
deliverables/cropland_report/  figures/, tables/, maps/ and dashboard.html (output)
```

### 4.1 The code (`cropland/`)

| file | functionality |
|---|---|
| **`pipeline.ipynb`** | **the notebook that runs the whole analysis** (section 3.1) |
| `common.py` | settings from the config, paths, study areas, the seven public maps as crop / not crop, Sentinel-2 monthly composites |
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
| `label_server.py`, `label_tool/` | the labelling tool (saves to `labels/`) |
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
| `report_figures.py` | figures 17-26 (method diagram, Rule 1, models, features, strata, labelling examples, interval simulation, points per design) |
| `key_results.py` | every number the report and the poster quote, from the result tables, with its source; the exposure table |
| `14_dashboard.py`, `dashboard/template.html` | the offline results dashboard |
| `test_cropland.py`, `test_evaluation.py` | checks of the estimators, rules, sample, label merge and evaluation code |
| `make_new_area.py`, `config/TEMPLATE.toml`, `REUSE.md` | the reuse kit: the same check in another area, country or season |
| `tree_workbench.ipynb` | a tool for building another model on the calibration points; not part of the analysis |
| `METHODOLOGY.md` | the study's rules, fixed before labelling, with a dated log of every change |
| `LABELLING_GUIDE.md`, `README.md` | the labelling key; the team's working guide to every step |

### 4.2 Input data

| where | what |
|---|---|
| the course data (not in the zip) | administrative boundaries, the ASAP crop mask, NASA flood masks (section 2) |
| `cropland/sample.csv`, `strata_areas.csv` | the 450 sample points (area, stratum, calibration or test, the two labellers) and the area of every stratum |
| `cropland/labels/` | every label as given, one file per labeller (pilot and sample); the five labellers are the letters A-E |
| `cropland/features_sample.csv`, `embedding_sample.csv` | the 18 cue features and Google's Satellite Embedding per box (also `*_pilot.csv` for the pilot) |
| `cropland/rule1_2026-10-12.json`, `logistic_*_2026-10-12.json` | the frozen models (rules in plain JSON) |
| `cropland/reference_*.csv` | CFSAM and FAOSTAT figures, and the published accuracy of the same maps, transcribed with table and page |
| `cropland/config/south_sudan_2025.toml` | our settings: areas, year, crop calendar, allocation, strata maps |
| `cropland/lol_river_osm.geojson`, `national_check/candidates.csv` | the Lol river (OpenStreetMap); 20,000 random points with every map's value |
| `cropland/results/map_values.csv`, `flooded_cropland.csv`, `predictions_*.csv`, `rule1_*.csv` | saved outputs of the Earth Engine steps and of the frozen models, read by later steps |
| `raw_data/cropland/` | the saved Earth Engine outputs: map counts on the flood grid (`eda/*.npz`, `eda/national_by_county.pkl`), Rule 1 per flood cell (`flood_history_rule1_*.csv`), the benchmark forests (`benchmarks.joblib`) |

### 4.3 Not included

- `raw_data/cropland/eda/national.npz` (about 50 MB): without it, the notebook reads the national flood rows of section 1.5 back from their saved table.
- The images the labellers saw (`cropland/label_tool/img/`, about 80 MB): without them, figure 24 stays as saved and the labelling tool shows no images.

Ask us for either. Everything else is recomputed.

### 4.4 Output data

| folder | what |
|---|---|
| `cropland/results/` | scores (`accuracy.csv`), areas (`area.csv`, `area_adjusted.csv`), floods (`flood_history.csv`, `trigger_hindcast.csv`), evaluation and sensitivity tables, model comparison |
| `cropland/` | `labels_final.csv`, `labels_merged.csv`, `disagreements.csv`, `model_table.csv` (step 06), `asap_crop_share_by_county.csv` (step 02) |
| `deliverables/cropland_report/tables/` | every EDA table, each figure's CSV twin, `key_results.csv` (every number in the report and on the poster, with its source), `exposure_before_after.csv` |
| `deliverables/cropland_report/figures/` | figures 1-27 (PNG) |
| `deliverables/cropland_report/maps/`, `dashboard.html` | the interactive 2022 flood map (its satellite background needs internet) and the results dashboard (works offline) |

## 5. Troubleshooting and FAQs

- **"course data not found" when the notebook starts.** The course data is not where the code looks (section 2, step 3). Set `CROPLAND_COURSE_DATA`, then restart Jupyter so the notebook sees it.
- **"open the notebook from the cropland/ folder".** The notebook must run with `cropland/` as its working folder. Jupyter and VS Code do this when you open it there; from the command line, use the command in section 3.1.
- **`ModuleNotFoundError` in the notebook.** The notebook runs in a different Python than the one you installed the packages into.
  - In VS Code, pick the `.venv` interpreter as the kernel.
  - In Jupyter, start `jupyter lab` from the activated environment. Or register the environment with `python -m ipykernel install --user --name cropland`, then choose the kernel "cropland".
- **The installation fails on another Python version.** Use Python 3.12: the pinned versions are the ones we tested.
- **Part 3 takes about 5 minutes.** Step 12 cross-validates eight models, 20 times 5 folds. That is normal; the other parts take seconds to a minute.
- **"national.npz: no" or "figure 24 stays as saved" in the setup output.** Expected: these two files are not in the zip (section 4.3).
- **Earth Engine errors** (only with `RUN_EARTH_ENGINE = True` or section 3.3).
  - "Project not registered": the Cloud project is not registered for Earth Engine.
  - "Too many concurrent requests": the project has hit its quota. The scripts retry; otherwise wait and run again.
  - Step 10 also needs our map in your own project: run step 8 first.
- **The dashboard's date changes after a run.** It records when it was built; the numbers stay the same.
- **Which notebook do I run?** `cropland/pipeline.ipynb`. `tree_workbench.ipynb` is a separate tool for building a new model.

## 6. Credits and acknowledgements

**Data.** The course data of the Zero Hunger Lab (JBG060): NASA MODIS/VIIRS near-real-time global flood product (MCDWD), the ASAP crop mask (JRC), administrative boundaries. In Google Earth Engine:
- the public maps: ESA WorldCover 2021, GLAD global cropland 2019 (Potapov et al.), Digital Earth Africa cropland extent 2019, ESA WorldCereal 2021, Esri / Impact Observatory 10 m land cover, Google Dynamic World, USGS GFSAD 30 m cropland extent 2015 (Esri, DE Africa and GFSAD through the awesome-gee-community-catalog, https://gee-community-catalog.org);
- imagery and features: Copernicus Sentinel-1 and Sentinel-2 with Cloud Score+, Google Open Buildings v3, Google Satellite Embedding (annual), JRC Global Surface Water, MODIS burned area (MCD64A1).

Other sources:
- the Lol river from OpenStreetMap (© OpenStreetMap contributors, ODbL);
- crop figures from the FAO/WFP Crop and Food Security Assessment Missions (CFSAM 2022, 2025) and FAOSTAT;
- published map accuracies from Kerner et al. (2024) and Adebayo et al. (2026).

To label, we also viewed Esri World Imagery (in the labelling tool) and its Wayback archive, Google Maps and single Sentinel-2 scenes. None of that imagery is redistributed.

**Methods** (named in the docstrings where they are used):
- **Sample and estimates:** stratified estimation and sample size (Olofsson et al. 2014; Stehman 2014, for strata that differ from the map classes); Neyman allocation.
- **Labeller agreement:** Cohen's kappa (Cohen 1960) and specific agreement (Cicchetti and Feinstein 1990).
- **Precision bounds:** Clopper-Pearson intervals.
- **Maps and floods:** each map read as crop / not crop as in Kerner et al. (2024); the flood overlay as in Pacetti et al. (2017).

**Software.**
- **Python** 3.12 with pandas, NumPy, SciPy, scikit-learn, matplotlib, GeoPandas, Shapely, rasterio, pyproj, pyogrio, pyarrow, joblib and Pillow;
- **Earth Engine:** the Google Earth Engine Python API (https://developers.google.com/earth-engine);
- **Notebook:** Jupyter (nbformat, nbclient, ipykernel).

We wrote the code for this project and used AI to help us with the coding. It made our progress faster while we pivoted between many ideas until we reached this one.

**Acknowledgements.** ZOA International and the Zero Hunger Lab for the question, the data and their answers in the stakeholder sessions.

## 7. Legal and ethical considerations

- **For research and education.** The code and its results have not been validated for operational humanitarian decisions. Our map is checked only in the two study areas; outside them nobody labelled, so it is not checked there.
- **Limits that matter for use** (as in the report).
  - The reference is image interpretation from one season (2025), not field data. The labellers also used images of other or unknown dates, and one of us counted crop just outside the box in a few early labels (`cropland/METHODOLOGY.md`, change log, 14 Oct 2026). No label was changed afterwards.
  - Cropland shares come in classes. At their worst cases, Aweil's cropland lies between 2.3% and 5.2% of the land instead of 3.8%. Fallow is hard to see.
  - Bor South and stratum A (where no map calls crop) hold few cropland points. In many flood years too few sample points lie on flooded land, and then the code says "cannot tell" instead of giving a number.
  - Rule 1 suits areas where fields, as in Aweil, sit near homesteads: it misses fields far from them, about a quarter of Aweil's boxes with cropland.
  - Flooded cropland is exposure, not loss: how much is lost depends on flood duration, depth and crop stage. Past floods are laid over today's cropland, a scenario, not history. Households are an illustration and an upper bound.
- **Impacts.** Used well, the check cuts silent triggers and false alarms. Used badly, a number checked in two areas is read as valid everywhere, and maps of who farms where can touch land claims. The choice of map moves "flooded cropland", and so a trigger, by one to two orders of magnitude: any use should carry the sample's interval, not a single map's number.
- **Privacy.** The code and data hold no information on any person or household in South Sudan. The five of us who labelled appear as the letters A-E; the key is not part of the code or the data.
- **Licences.** Each dataset is used under its provider's terms: ESA WorldCover, Dynamic World, Esri land cover and Open Buildings under CC BY 4.0; OpenStreetMap under ODbL. The course data is not redistributed: download it from the course (section 2). Cite the providers (section 6) when you reuse the results.
