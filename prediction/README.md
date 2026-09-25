# prediction/

Flood forecasting for the Unity / Jonglei / Upper Nile corridor: how far ahead can we forecast flooding, per pixel, better than forecasts that need no model at all?

Two stages, following the design of INFLOW-AI v2.1 but trained from scratch on our own data and target (their weights are not used):

| stage | question | model | INFLOW-AI v2.1 part |
|---|---|---|---|
| 1 | how much of the corridor floods, L dekads ahead | gradient boosting, ElasticNet, transformer | temporal model |
| 2 | which pixels (~232 m) flood | ConvLSTM on 32 x 32 patches | spatial model |

Stage 1's forecast is one of Stage 2's inputs.

## Setup

- Python: run everything with `/usr/bin/python3`, after `pip install -r requirements.txt`. On the dev laptop the pyenv `python3` lacks tensorflow and xarray.
- GPU (step 8): `export LD_LIBRARY_PATH=~/.local/share/nvidia-cu12-shim/lib:$LD_LIBRARY_PATH`. Without it step 8 runs on CPU, about 10x slower.
- Data: everything is read from and written to `raw_data/` (not tracked by git):
  - inputs: the shared data download, plus `raw_data/DMI/dmi.had.long.data` from [NOAA PSL](https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data)
  - intermediate files: `raw_data/prediction/` (about 3.6 GB)
- Checks: `/usr/bin/python3 prediction/test_pipeline.py` (a few seconds).

## Steps

| # | script | output | time |
|---|---|---|---|
| 1 | `01_domain_mask.py` | pixels that flooded at least once | ~1 h |
| 2 | `02_extract_pixels.py` | all flood detections in those pixels | ~1 h |
| 3 | `03_dekadal_labels.py` | one label per pixel per dekad | ~5 min |
| 4 | `04_era5_basin_features.py` | ERA5 rain and runoff per dekad | ~1 min |
| 5 | `05_driver_table.py` | lakes, DMI, ERA5 and flood volume per dekad | ~1 min |
| 6 | `06_stage1_volume.py` | Stage 1 forecasts, scores, SHAP | ~5 min |
| 7 | `07_dense_arrays.py` | flood maps as patches | ~1 min |
| 8 | `08_train_stage2.py --lead 3 6 --fold 5 6 7 8` | Stage 2 models, one per lead and fold | ~15 min each |
| 9 | `09_baselines.py` | persistence and climatology per pixel | ~5 min |
| 10 | `10_evaluate.py` | tables in `deliverables/tables/`, figures in `deliverables/figures/` | seconds |

Step 8 skips runs that already have results, so it can be restarted after an interruption. Ablations: add `--no-stage1` or `--no-era5`.

Each script starts with a short description. `common.py` holds the shared definitions (paths, time index, folds, scores).

## Terms

**Dekad**: a 10-day period (days 1-10, 11-20, 21-end of each month), 36 per year. The record runs from 2000 to 2025, 936 dekads.

**Issue time, lead**: a forecast is made at dekad t with data up to t, for dekad t + L. L is the lead: 1 is about 10 days, 3 about a month, 36 about a year.

**Flood domain**: the ~1.08 million pixels that flooded at least once in 2000-2025. About 76% of the corridor never flooded and is left out.

**Recurring / unusual**: NASA's flood types. Recurring pixels flood in at least about a third of years, unusual ones less often. In this corridor 99% of domain pixels are always "unusual". We forecast flooded / not flooded and report scores for each type separately.

**Persistence**: forecast "same as now". Strong at short leads because water drains slowly.

**Climatology**: forecast "same as usual for this time of year", from the training years. Strong at long leads because flooding is seasonal.

**Seasonal persistence**: today's departure from normal carries on, and the season does the rest. The strictest free forecast; at a lead of one year it means "same as a year ago".

**Skill vs the better baseline**: per fold, 1 minus the model's error divided by the error of the better free forecast. Above 0 means the model beats it.

**Rolling origin**: training always comes before testing. Train 2000-2009 and test 2010-11, train 2000-2011 and test 2012-13, and so on up to a test on 2024-25: 8 folds. Fold 6 trains only on 2000-2019 and tests on the 2020-21 floods.

**Embargo**: 6 dekads left out between the last training sample and the first test sample, so input windows do not overlap.

**Walk-forward**: Stage 1 values given to Stage 2 always come from Stage 1 models trained on earlier years only.

**Anomaly**: a value minus its usual value for that dekad of the year.

**Lag**: a feature taken k dekads before the issue time. Lake levels go back 54 dekads (18 months), since water from Lake Victoria takes roughly 9-17 months to reach the Sudd.

**ConvLSTM**: a recurrent neural network whose memory is an image. It reads a sequence of flood maps.

**Patch, border**: 32 x 32 pixel squares (~7.4 km). The outer 2 pixels of each are not scored.

**Focal loss**: a training loss that down-weights easy pixels (mostly dry ones).

**Scores**: precision (share of forecast floods that happened), recall (share of floods that were forecast), F1 (combines the two), CSI (hits / (hits + misses + false alarms)), PR-AUC (quality across all thresholds), Brier (squared error of the probability; lower is better).

**SHAP**: how much each input moved each forecast up or down. Exact for tree models (TreeSHAP); summed per driver and per lag.

## Limitations

- NASA's product does not separate "dry" from "not observed" (e.g. clouds); no detection is treated as dry.
- The flood tiles stop at 10 N; the northern tip of Upper Nile is not covered.
- ERA5 regions are rectangles, not catchment boundaries.
- There is no elevation input.
- The recurring / unusual map is built from the full 2000-2025 record, so it is only used for reporting, never as an input.
- Stage 2 trains on a sample of (patch, dekad) pairs; the share used is written to each run's log. Test scores use all pairs.

## Rebuilding the report

`deliverables/MODEL_REPORT.html` is generated from `deliverables/MODEL_REPORT.md` (after running step 10, so the figures are current):

```
cd deliverables
pandoc MODEL_REPORT.md -s --toc --toc-depth=2 --embed-resources -o MODEL_REPORT.html
```
