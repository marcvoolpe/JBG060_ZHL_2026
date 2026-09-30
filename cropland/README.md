# cropland/

How much of ZOA's areas (five Aweil counties, Bor South) was cropland in 2025, and how accurate are public cropland maps there? Our own rule-based map covers the whole country.

- **Rules of the study:** `METHODOLOGY.md` (fixed before labelling; changes go in its change log).
- **Plan and background:** `deliverables/CROPLAND_PLAN.html`.
- **For labellers:** `LABELLING_GUIDE.md` and `label_tool/index.html`.

## Setup

- Project environment: `pip install -r requirements.txt`, plus `pip install earthengine-api`.
- Earth Engine: a Google account with access to the Cloud project `grand-loop-457810-a1` (ask Matteo). Run `earthengine authenticate` once.
- Run every script from `group_repo`, e.g. `python cropland/01_compare_pilot.py`.

## Steps

| step | script | what it does | output |
|---|---|---|---|
| 0 | `00_pilot_points.py` | 30 random pilot points in Twic county (outside the study areas) | `pilot_points.csv`, `.kml` |
| 1 | `01_compare_pilot.py` | labeller agreement (Cohen's kappa) and share of confident labels; go / no-go | printed |
| 2 | `02_strata_from_asap.py` | first look: ASAP crop share per county | `asap_crop_share_by_county.csv` |
| 3 | `03_agreement_and_sample.py export`, then `... sample` | 7-map agreement strata (Earth Engine asset), stratum areas, the 450-point sample, calibration/test split, two labellers per point | `strata_areas.csv`, `sample.csv` |
| 4 | `04_image_strips.py pilot` / `sample` | monthly Sentinel-2 strips 2025 + 2024 and NDVI curves for the tool | `label_tool/img/`, `label_tool/data_*.js` |
| 5 | `05_features.py pilot` / `sample` | the 18 machine features + Satellite Embedding at the points | `features_*.csv`, `embedding_*.csv` |
| 6 | `06_merge_labels.py` | pairs the two labels per point; disagreements to a third person | `labels_merged.csv`, `adjudication.csv`, `labels_final.csv` |
| 7 | `07_fit_rules.py` | Rule 1 (decision tree) on calibration points, and the random-forest benchmarks; **freezes the rules** | `rule1_<date>.json` |
| 8 | `08_run_map.py cropland/rule1_<date>.json` | checks that the Earth Engine map equals the rules, then exports our map (10 m study areas, 30 m country) | Earth Engine assets |
| 9 | `09_score.py cropland/rule1_<date>.json` | accuracy of every map on test points, cropland area ± 95% CI | `results/accuracy.csv`, `results/area.csv` |
| 10 | `10_flood.py cropland/rule1_<date>.json` | flooded cropland 2025 per map and from the sample (Aweil vs Bor South) | `results/flooded_cropland.csv` |

Shared code: `common.py` (settings, study areas, the public maps), `features.py` (the features), `rules.py` (rules JSON in Python and in Earth Engine), `estimators.py` (stratified estimators, Stehman 2014).

Checks: `python cropland/test_cropland.py` (fast), or add `--ee` to also check Earth Engine against Python and the building-distance feature.

Large files go to `raw_data/cropland/`, outside git. Points, labels, rules and results are small and stay in `cropland/`.
