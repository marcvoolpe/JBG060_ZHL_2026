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

Open **http://localhost:8765**, choose the set and your name, and label. In `sample` you see only **your 180 points**. Each of them is also labelled by one other person (every pair of us shares 45 points), and you never see their label. Every point is saved to `cropland/labels/<set>_labels_<name>.csv` when you press Enter. You can close the browser any time. If the server prints a WARNING about images, the zip is in the wrong place.

**At the end of each session**, commit only your own file:

```
git add cropland/labels/*_<name>.csv
git commit -m "labels: <name>"
git pull --rebase
git push
```

How to label a point, the shortcuts and the traps: `LABELLING_GUIDE.md`. The short version:

- Label the **210 m yellow box**: crop if there is cropland anywhere in it.
- `O` if there is open land anywhere in the box; otherwise `W` / `B` / `T` for what the box mostly is (water / buildings / trees).
- Then `Y` / `N` / `K` for each cue.
- The label fills itself in. `C` / `F` / `X` / `U` change it.
- For crop or fallow: how much of the box is cropland, `6` <10% · `7` 10–25% · `8` 25–50% · `9` >50%.
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

1. **Definition.** For the 210 m × 210 m box around each point (21 × 21 Sentinel-2 pixels), in 2025:
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
   - **first:** is there open land anywhere in the box (if not: water / buildings / trees);
   - **then, for open land:**
     - a. bare soil in April-May;
     - b. green-up in June-August;
     - c. harvest earlier than the grass around;
     - d. field shapes;
     - e. cropped in 2024.

   Every pair of us shares 45 points, and everyone gets the same mix of areas, strata and calibration/test points. When the two labels differ, **nobody settles it**: both labels are kept and the disagreement is reported. The area counts such a point as half cropland (the mean of the two labels), and the models are trained and scored only on points where both agree.

4. **Calibration vs test.** The 450 points were split before labelling: **150 calibration** (to build the rules) and **300 test** (to score them). The test points are never used to build anything.

5. **Rule 1, our map.** Earth Engine measures, over the 210 m box around every pixel, the same things the labellers look at. For example: lowest greenness in April-May, the green-up, the September-October drop compared with the surroundings, texture, distance to buildings, water, burn scars, and radar in the cloudy months. A **decision tree** (2-4 levels) learns thresholds from the calibration points and prints them as if-then rules ("crop if the harvest drop is above X and..."). It maps **cropped in 2025**, because a fallow field looks like grass in a single year. Fallow enters the area through the sample only. The rules are frozen in `rule1_<date>.json` and the same file drives the Earth Engine map, so the map and the scores can't drift apart. A random forest on the same features (and one on Google's Satellite Embedding) is run as a black-box **benchmark** only.

6. **Results.**
   - **Area:** cropland area per study area, in ha with a **95% confidence interval**, from the labelled share of cropland in each box at all points. It does not depend on any map. The area of land whose box holds any cropland is reported next to it as an upper bound.
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
- Or use your own Earth Engine project: `set CROPLAND_EE_PROJECT=<project-id>` (Windows; `export` on macOS/Linux) before running. Steps 4 and 5 only need public data; steps 3, 8 and 10 read our assets in `grand-loop-457810-a1`, so they need access there.
- Run every script from `group_repo`.

| step | command | what it does | output |
|---|---|---|---|
| 0 | `python cropland/00_pilot_points.py` | 30 pilot points in Twic county (outside the study areas) | `pilot_points.csv` |
| 1 | `python cropland/01_compare_pilot.py` | pilot agreement (Cohen's kappa), share of confident labels; **go if ≥ 70%** | printed |
| 2 | `python cropland/02_strata_from_asap.py` | first look: ASAP crop share per county | `asap_crop_share_by_county.csv` |
| 3 | `... 03_agreement_and_sample.py export`, then `... sample` | strata map (Earth Engine asset), stratum areas, 450-point sample, split, two labellers per point (balanced per area × stratum × split). `... labellers` redoes only the pairs, on the existing sample, before anyone labels | `strata_areas.csv`, `sample.csv` |
| 4 | `python cropland/04_image_strips.py sample` | image strips 2025 + 2024 with the 210 m box; the box's NDVI and radar; Esri image date | `label_tool/img/` (zip it), `label_tool/data_*.js` |
| 5 | `python cropland/05_features.py sample` | the 18 features + Satellite Embedding, over each point's 210 m box | `features_sample.csv`, `embedding_sample.csv` |
| – | `python cropland/label_server.py` | the labelling tool, saving to disk | `labels/*.csv` |
| 6 | `python cropland/06_merge_labels.py` | matches the two labels per point; agreement per pair; lists disagreements (not settled); builds the one table all models use | `labels_final.csv`, `disagreements.csv`, `model_table.csv` |
| 7 | `python cropland/07_fit_rules.py` | Rule 1 + benchmarks on calibration points; **freezes the rules** | `rule1_<date>.json` |
| 7b | your own model (Wei, Matei), see below | trained on `model_data.load("calibration")` | `results/predictions_<name>.csv` |
| 8 | `python cropland/08_run_map.py cropland/rule1_<date>.json` | checks map = rules, exports our map (10 m areas, 30 m country) | Earth Engine assets |
| 9 | `python cropland/09_score.py cropland/rule1_<date>.json` | accuracy and area ± 95% CI | `results/accuracy.csv`, `results/area.csv` |
| 10 | `python cropland/10_flood.py cropland/rule1_<date>.json` | flooded cropland 2025, Aweil vs Bor South | `results/flooded_cropland.csv` |

Shared code:
- `common.py`: settings, areas, public maps.
- `features.py`: the 18 features.
- `rules.py`: the rules in Python and in Earth Engine.
- `estimators.py`: the stratified estimators.
- `model_data.py`: the one table every model reads (`model_table.csv`).

Checks: `python cropland/test_cropland.py`, with `--ee` to also check that Earth Engine and Python agree, and the building-distance feature.

### Building another model (Wei, Matei)

Everything a model needs is in **`model_table.csv`**, one row per sample point (written by step 6):

| columns | what |
|---|---|
| `id`, `area`, `stratum`, `split`, `lat`, `lon` | the point; `split` is calibration or test |
| `ha_per_point` | hectares of the study area this point stands for: sum it per group for area numbers in a dashboard |
| `crop`, `cropland`, `crop_share` | targets, filled only where both labellers agree (crop = cropped in 2025; cropland = crop + fallow; share = 0-1 of the box) |
| `cropland_avg`, `crop_avg`, `share_avg`, `share_crop_avg` | mean of the two labellers, filled for every point labelled twice |
| `final`, `disagreed`, `crop_fallow_only`, `confidence` | label status (`final` = agreed label, `crop/fallow`, `disagreed` or `unsure`) |
| `ndvi_min_am` … `vh_range` | the 18 features, each a summary of the 210 m box (`features.FEATURES`, METHODOLOGY section 5) |
| `A00` … `A63` | Google Satellite Embedding 2025, mean over the box |

```python
import model_data as M
from sklearn.tree import DecisionTreeClassifier

X, y, info = M.load("calibration", target="crop")        # Aweil only: X[info.area == "aweil"]
fill = M.fill_values(X)                                    # vh_jun is missing at 4 points
tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=5, class_weight="balanced").fit(X.fillna(fill), y)
```

Rules:
- **Inputs:** only the features or the embedding. Never the labellers' cues, share or confidence: they *are* the labels.
- **Small data:** about 150 calibration points, maybe 20-40 crop. Keep trees shallow (depth 2-4) and choose the depth by cross-validation on the calibration points, as `07_fit_rules.py` does.
- **Test points are for scoring only, after you freeze the model.** Never tune on them.
- **To be scored:** write `results/predictions_<name>.csv` with `id,prediction` (1/0) for all 450 points, and `09_score.py` adds the model to `results/accuracy.csv` next to Rule 1 and the public maps, per area and definition.
- **For a map:** save the tree with `rules.save(rules.from_tree(tree, F.FEATURES, fill, "<name>"), C.HERE)`. Then `08_run_map.py cropland/<name>_<date>.json` maps it in Earth Engine exactly as it scores. For one tree per area, save one file per area.

**What's in git:** code, points, features, labels, rules, results. **Not in git:** the images (`label_tool/img/`, shared as a zip) and large outputs in `raw_data/cropland/`.
