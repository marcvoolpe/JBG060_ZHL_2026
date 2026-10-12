# Using the cropland check in another area or country

This folder counted cropland in two areas of South Sudan in 2025 (Aweil counties, Bor South): a
stratified sample of 210 m boxes, each labelled blind by two people from satellite images, then
a readable rule fitted on one third of the points and tested on the other two thirds. The same
pipeline can be run for another area, another country or another season. This guide says what
to change, what to keep, and in which order.

You need: Python 3.11 or newer with `requirements-cropland.txt`, an Earth Engine account with a
Cloud project, and 3-6 people to label (each labels 2/5 of the points in our design).

## What you can change, and what you should keep

| change (in your config file) | keep (it is what makes the numbers trustworthy) |
|---|---|
| country, study areas, year | two blind labellers per point, no third person settling splits |
| crop calendar months (the most important change) | the presence rule (crop if any field in the box) and the box share |
| cue texts and area notes in the labelling tool | one third calibration, two thirds test, drawn at random per stratum |
| which public maps build the strata, points per stratum | rules fitted on calibration points only and frozen before any test label is read |
| labeller names | stratified estimators with an interval for every area and score |

**Rules are local.** Our Rule 1 ("crop if a building is within 333 m and the box has field
edges") was learned in Aweil. Do not copy its thresholds: refit on your own calibration labels
(step 7). You may also edit a rules file by hand (it is plain JSON, and both the scoring and the
Earth Engine map read it), but save the edit as a new dated file and check it on newly labelled
points, never on the test points you used to choose it.

## Steps

1. **Make a clean copy** (our sample, labels and results stay where they are):
   `python cropland/make_new_area.py <folder>`. Work in `<folder>/cropland/` from now on.
   The scripts refuse to run a new config in a folder that holds another study's `sample.csv`.
2. **Write the config.** Copy `config/TEMPLATE.toml` to `config/<name>.toml` and fill in every
   line marked CHANGE. Then `set CROPLAND_CONFIG=<name>` (Windows) or `export CROPLAND_CONFIG=<name>`,
   and `set CROPLAND_EE_PROJECT=<your Earth Engine project>`.
   - Boundaries: `source = "gaul"` uses FAO GAUL 2015 in Earth Engine (any country, names as in
     GAUL; Earth Engine marks this version as deprecated but it works). Or use your own GeoJSON
     with `source = "file"`.
   - Calendar: the months of bare soil before sowing, peak green, harvest and the dry season.
     Two rainy seasons: label the main one, or make one config per season. Write the same months
     in the cue texts under `[tool.cues]`.
   - Maps: Digital Earth Africa and GFSAD cover Africa only; drop them elsewhere. Esri and
     Dynamic World follow the study year (`esri_<year>`, `dynamicworld_<year>`).
3. **Strata and sample:** `python cropland/03_agreement_and_sample.py export`, wait for the Earth
   Engine tasks, then `... sample`. Writes `strata_areas.csv` and `sample.csv`.
4. **Images for the tool:** `python cropland/04_image_strips.py sample` (also writes
   `label_tool/config.js` with your year, months and texts; `... config` rewrites only that file).
5. **Features:** `python cropland/05_features.py sample`.
6. **Label.** Share the `label_tool/` folder and `label_server.py` with each labeller (or one
   shared laptop). Start `python cropland/label_server.py`, open the address it prints, choose
   the set "sample" and your name. Labels are saved per labeller in `labels/`. Read
   `LABELLING_GUIDE.md` first and do a pilot of ~30 points together before the real sample.
7. **Merge and fit:** `python cropland/06_merge_labels.py`, then `python cropland/07_fit_rules.py`
   (Rule 1 and the benchmarks) and, if you want other models, `python cropland/12_other_models.py
   compare` then `... freeze <name>`. Everything here uses calibration points only.
8. **Map and score:** `python cropland/08_run_map.py cropland/rule1_<date>.json` (map assets in
   Earth Engine), `python cropland/09_score.py cropland/rule1_<date>.json` (first step that reads
   the test labels: accuracy of every map, area with interval), `python cropland/11_evaluate.py
   cropland/rule1_<date>.json` (adjusted interval, error analysis, efficiency).

Not included in the copy: the flood overlay (`10_flood.py` reads the course's NASA flood files
for South Sudan), ASAP (course data; scoring skips it when the file is missing), the pilot steps
00-02 and the EDA notebook. Bring your own flood layer for the overlay.

## What it costs (our study)

450 points, 900 labels; median 0.5-1.0 minutes per label, 2.7-7.3 hours per person. Earth Engine
steps: from minutes (features) to a few hours (the agreement map and the 10 m map exports). A
yearly re-check of the same areas needs about 150 points (report notes 06).

## Where things are explained

`METHODOLOGY.md` (the protocol and its change log), `LABELLING_GUIDE.md` (the key), `README.md`
(files and columns), `config/south_sudan_2025.toml` (our settings, for comparison).
