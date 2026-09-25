# prediction/

Flood forecasting for the Unity / Jonglei / Upper Nile corridor: how far ahead can we forecast flooding, per pixel, better than forecasts that need no model at all?

Two stages, following the design of INFLOW-AI v2.1 but trained from scratch on our own data and target (their weights are not used):

| stage | question | model | INFLOW-AI v2.1 part |
|---|---|---|---|
| 1 | how much of the corridor floods, L dekads ahead | gradient boosting, ElasticNet, transformer | temporal model |
| 2 | which pixels (~232 m) flood | ConvLSTM on 32 x 32 patches | spatial model |

Stage 1's forecast is one of Stage 2's inputs.

## Setup

Works on Windows, macOS and Linux. Commands below are run from the repository root with the virtual environment from the main `README.md` active, so `python` is that environment's Python (3.12 or 3.13).

1. **Install:** `python -m pip install -r requirements.txt` (main `README.md`, step 2).
2. **Shared data:** unzip the SURFdrive download into `raw_data/` (main `README.md`). The pipeline uses `flood_masks/`, `rainfall and runoff/`, `Water levels lakes/` and `Administrative boundaries/`.
3. **One extra file:** save the NOAA Indian Ocean Dipole series as `raw_data/DMI/dmi.had.long.data`. Download it from [NOAA PSL](https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data) (right-click, save as; keep the file name exactly).
4. **Check:** `python prediction/test_pipeline.py`. Tests that need files you have not built yet are reported as `skip`, not as failures.

Everything the scripts write goes to `raw_data/prediction/` (about 3.6 GB, not tracked by git) and to `deliverables/tables/` and `deliverables/figures/`.

### Two ways to reproduce the results

**A. Quick check (minutes).** Ask Matteo for his `raw_data/prediction/` folder (it contains the intermediate files and the trained Stage 2 models), put it in your `raw_data/`, then:

```
python prediction/test_pipeline.py
python prediction/10_evaluate.py
```

Step 10 rebuilds every table and figure in the report from the saved results, so they should match the repository exactly. To also rerun a model from scratch, Stage 1 (`python prediction/06_stage1_volume.py`) takes about 5 minutes on any laptop.

**B. Full rebuild (a day on a laptop CPU).** Run steps 1 to 11 below in order. Steps 1-7 and 9-10 run on any machine; steps 1 and 2 take about an hour each. Steps 8 and 11 use TensorFlow:

| your machine | steps 8 and 11 |
|---|---|
| Linux with NVIDIA GPU | GPU, ~15 min per Stage 2 run |
| Windows | CPU only (TensorFlow dropped native Windows GPU support), roughly 10x slower, i.e. a few hours per run. GPU is possible through WSL2. |
| Mac with Apple silicon (M1-M4) | CPU, roughly 10x slower. |
| Mac with Intel processor | TensorFlow does not install; skip 8 and 11, use route A for Stage 2. |

Stage 2 numbers from a retrain on another machine will be close but not identical: GPU and CPU arithmetic differ in the last digits, and that changes which training pairs are drawn. Everything else (steps 1-7, 9, 10, and Stage 1) is deterministic.

About 16 GB RAM is comfortable; steps 1-2 are the heaviest.

*Matteo's laptop only:* the system Python is `/usr/bin/python3`, and the GPU needs `LD_LIBRARY_PATH=~/.local/share/nvidia-cu12-shim/lib`.

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
| 11 | `11_calibrate_stage2.py --lead 3 6 --fold 5 6 7 8` | calibrated Stage 2 probabilities (no retraining); then run step 10 again | ~8 min each |

Step 8 skips runs that already have results, so it can be restarted after an interruption. Ablations: add `--no-stage1` or `--no-era5`.

Step 11 was added after the sweep, so it runs after step 8 and before a final run of step 10, which then also writes `tables/stage2_calibration.csv` and `figures/stage2_reliability.png`. It refuses to run if the reloaded model does not pick the same decision threshold as in training (a check that the inputs are rebuilt exactly).

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

**Calibration**: making the probabilities honest, so that of all pixels given "60%", about 60% flood. Step 11 fits two numbers (Platt scaling) on the validation years; it changes the probability values but not their order, so F1 and PR-AUC stay the same and the Brier score moves. A **reliability diagram** plots forecast probability against how often the pixel actually flooded; perfect is the diagonal.

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
