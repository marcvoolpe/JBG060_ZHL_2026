# cropland/

**Question.** How much of ZOA's two areas (the five Aweil counties, Bor South) was cropland in 2025, and how accurate are the public cropland maps there? We also make our own rule-based cropland map of the whole country.

This file covers what to do and why. The binding rules of the study are in `METHODOLOGY.md`. It was fixed before labelling, and every change since is listed in its change log. Background and literature: `deliverables/CROPLAND_PLAN.html`.

---

## 1. Labellers: what to do

**Once:**

1. `git pull`
2. Get `cropland_images.zip` from Matteo (~80 MB; the images are not in git). Unzip it **inside `cropland/label_tool/`**, so that you get

   ```
   group_repo/cropland/label_tool/img/S001_2025_tc.webp
   group_repo/cropland/label_tool/img/...          (1,920 files)
   ```

   Don't create an extra `img/img/` level.
3. Python 3 is enough; the server uses no extra packages.

**Each session:**

```
cd group_repo
python cropland/label_server.py
```

Open **http://localhost:8765**, choose the set and your name, and label. Every point is saved to `cropland/labels/<set>_labels_<name>.csv` when you press Enter. You can close the browser any time. If the server prints a WARNING about images, the zip is in the wrong place.

**At the end of each session**, commit only your own file:

```
git add cropland/labels/*_<name>.csv
git commit -m "labels: <name>"
git pull --rebase
git push
```

How to label a point, the shortcuts and the traps: `LABELLING_GUIDE.md`. The short version:

- `W` / `B` / `T` / `O` for what covers the pixel (water / buildings / trees / open land).
- Then `Y` / `N` / `K` for each cue.
- The label fills itself in. `C` / `F` / `X` / `U` change it.
- `Enter` saves.

**Deadlines:**

| by | what |
|---|---|
| 3 Oct | pilot set (30 points) labelled by at least two people |
| 9 Oct | your 180 sample points labelled |
| 12 Oct | Rule 1 frozen (Matteo) |
| 15 Oct | results and dashboard |
| 21 Oct | poster |
| 25 Oct | report |

**Never** look at a cropland map (WorldCover, GLAD, ASAP...) or at anyone else's labels while labelling.

---

## 2. The method, in short

1. **Definition.** For each 10 m pixel in 2025:
   - **crop:** sown and grown in 2025;
   - **fallow:** a field not sown in 2025;
   - **not crop:** grass, bush, trees, water, settlement.

   **Cropland = crop + fallow**: the main area number. **Cropped in 2025** (crop only) is the second number, closest to ZOA's trigger "flood inundating cropland".

2. **Where the points go (stratified sample).** Crop is rare (a few % of the land), so random points would hit it only a handful of times. We count how many of 7 public maps call each pixel crop, and draw points separately from each group:

   | area | A: 0 maps | B: 1-2 maps | C: 3+ maps |
   |---|---|---|---|
   | Aweil, share of land | 95.0% | 4.7% | 0.3% |
   | Aweil, points | 150 | 90 | 90 |
   | Bor South, share of land | 90.6% | 9.4% (B+C; C was 0.004%, merged) | |
   | Bor South, points | 60 | 60 | |

   The maps only decide **where** points go; they are never the truth. The area estimate weights each group by its real share of the land, so extra points in a group do not bias it.

3. **Truth from people.** Each point is labelled by **two** of us independently, from monthly Sentinel-2 images of 2025 (2024 alongside, only to recognise fallow), the greenness (NDVI) curve, and a high-resolution image. The labelling key asks:
   - **first:** what covers the pixel (water / buildings / trees / open land);
   - **then, for open land:**
     - a. bare soil in April-May;
     - b. green-up in June-August;
     - c. harvest earlier than the grass around;
     - d. field shapes;
     - e. cropped in 2024.

   When the two labels differ, a third person decides. **Disagreements are kept and reported**, not dropped.

4. **Calibration vs test.** The 450 points were split before labelling: **150 calibration** (to build the rules) and **300 test** (to score them). The test points are never used to build anything.

5. **Rule 1, our map.** Earth Engine measures, at every pixel, the same things the labellers look at. For example: lowest greenness in April-May, the green-up, the September-October drop compared with the surroundings, texture, distance to buildings, water, burn scars, and radar in the cloudy months. A **decision tree** (2-4 levels) learns thresholds from the calibration points and prints them as if-then rules ("crop if the harvest drop is above X and..."). It maps **cropped in 2025**, because a fallow field looks like grass in a single year. Fallow enters the area through the sample only. The rules are frozen in `rule1_<date>.json` and the same file drives the Earth Engine map, so the map and the scores can't drift apart. A random forest on the same features (and one on Google's Satellite Embedding) is run as a black-box **benchmark** only.

6. **Results.**
   - **Area:** cropland area per study area, in ha with a **95% confidence interval**, from all labelled points. It does not depend on any map.
   - **Accuracy:** for each map (our Rule 1, the 7 public maps, ASAP, the benchmarks), on the test points: user's accuracy (precision), producer's accuracy (recall) and F1 with error bars, per area and for both definitions. Maps whose intervals overlap are not ranked.
   - **National:** cropland area per map and per state. Our map is marked "not checked" outside the two areas.
   - **Flood:** flooded cropland in 2025 per map. Aweil barely flooded in 2025 and Bor South flooded widely, so we see both cases.

7. **Regional differences.** Bor South has flood-recession plots: under water in August-October, green in December-February, and they count as crop. The tool shows a short note on each area's farming with every point. Accuracy is reported per area.

**What we can claim:** cropland area in the two areas in 2025 with an interval, and which maps are more or less accurate **there, in 2025**. Not that our map is better anywhere else.

**Why this design:** it follows the good-practice rules for accuracy and area (Olofsson et al. 2014; Stehman 2014; Stehman & Foody 2019), and extends Kerner et al. (2024), which evaluated 11 maps in 8 African countries but not South Sudan.

---

## 3. Running the pipeline (Matteo / whoever runs the analysis)

Setup:
- `pip install -r requirements.txt earthengine-api`
- `earthengine authenticate` once, with a Google account added to the Cloud project `grand-loop-457810-a1`.
- Run every script from `group_repo`.

| step | command | what it does | output |
|---|---|---|---|
| 0 | `python cropland/00_pilot_points.py` | 30 pilot points in Twic county (outside the study areas) | `pilot_points.csv` |
| 1 | `python cropland/01_compare_pilot.py` | pilot agreement (Cohen's kappa), share of confident labels; **go if ≥ 70%** | printed |
| 2 | `python cropland/02_strata_from_asap.py` | first look: ASAP crop share per county | `asap_crop_share_by_county.csv` |
| 3 | `... 03_agreement_and_sample.py export`, then `... sample` | strata map (Earth Engine asset), stratum areas, 450-point sample, split, two labellers per point | `strata_areas.csv`, `sample.csv` |
| 4 | `python cropland/04_image_strips.py sample` | image strips 2025 + 2024 and NDVI for the tool | `label_tool/img/` (zip it), `label_tool/data_*.js` |
| 5 | `python cropland/05_features.py sample` | the 18 features + Satellite Embedding at each point | `features_sample.csv`, `embedding_sample.csv` |
| – | `python cropland/label_server.py` | the labelling tool, saving to disk | `labels/*.csv` |
| 6 | `python cropland/06_merge_labels.py` | pairs the two labels; disagreements go to `adjudication.csv` for a third person; run again after | `labels_final.csv` |
| 7 | `python cropland/07_fit_rules.py` | Rule 1 + benchmarks on calibration points; **freezes the rules** | `rule1_<date>.json` |
| 8 | `python cropland/08_run_map.py cropland/rule1_<date>.json` | checks map = rules, exports our map (10 m areas, 30 m country) | Earth Engine assets |
| 9 | `python cropland/09_score.py cropland/rule1_<date>.json` | accuracy and area ± 95% CI | `results/accuracy.csv`, `results/area.csv` |
| 10 | `python cropland/10_flood.py cropland/rule1_<date>.json` | flooded cropland 2025, Aweil vs Bor South | `results/flooded_cropland.csv` |

Shared code:
- `common.py`: settings, areas, public maps.
- `features.py`: the 18 features.
- `rules.py`: the rules in Python and in Earth Engine.
- `estimators.py`: the stratified estimators.

Checks: `python cropland/test_cropland.py`, with `--ee` to also check that Earth Engine and Python agree, and the building-distance feature.

**What's in git:** code, points, features, labels, rules, results. **Not in git:** the images (`label_tool/img/`, shared as a zip) and large outputs in `raw_data/cropland/`.
