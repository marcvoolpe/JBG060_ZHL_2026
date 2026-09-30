# Cropland in ZOA's areas, 2025: declared methodology

Version 1, 30 Sep 2026. This file is fixed **before** any labelling. Every later change gets a dated line in the change log at the bottom, with the reason. Nothing in sections 1-8 may be changed after the test labels have been looked at.

## 1. Questions

1. **Area.** How much land in the five Aweil counties, and separately in Bor South, was cropland in 2025: cropped in the 2025 season **or fallow**? We also report the cropped-only part. Reported in hectares and as a share of land, with a 95% confidence interval.
2. **Map accuracy.** How accurately do public cropland maps, and our own rule-based map, show that cropland? Reported per map: user's accuracy (precision), producer's accuracy (recall) and F1, each with a standard error.
3. **National picture** (description only). How much cropland does each map, ours included, show per state of South Sudan? Our map is not checked outside the two study areas.
4. **Flood** (small). How much 2025 flooding fell on cropland under each map?

## 2. Definitions

**Study areas:** the five Aweil counties (Aweil North, East, South, West, Centre; 3.09 M ha) and Bor South county (1.40 M ha), using `raw_data/Administrative boundaries/ssd_admin2.geojson`.

**Season:** the 2025 main rainy season. For the images, the "crop year" runs from **1 January to 31 December 2025**. It covers the dry season before sowing, sowing and growth, and harvest. The crop calendar for Northern Bahr el Ghazal (FEWS NET) is: sowing done by late May; groundnuts and sesame harvested from August; short-cycle sorghum harvested in September-October.

**Unit:** the 10 m × 10 m Sentinel-2 pixel that contains the sample point.

**Cropland (what we count):** fields that were **cropped in the 2025 season, or fallow**. Fallow means a field with visible structure (edges, plots) that was not sown in 2025. Every label records which of the two it is, so we can also report the "cropped in 2025" area on its own. That is the part closest to ZOA's trigger ("flood inundating cropland").

| counts as cropland | does not count |
|---|---|
| sorghum, maize, groundnut, sesame, cassava, rice, vegetables | grassland, bush, trees, wetland, open water |
| small plots next to homesteads (home gardens) | settlement: roofs, compounds, roads |
| flood-recession plots cropped in 2025 | burned or grazed grassland with no field structure |
| **fallow**: field structure visible, not sown in 2025 | |

A pixel is cropland if **more than half** of it is cropped or fallow field.

## 3. Sample (sampling design)

1. **Maps used to build the strata:**
   - ESA WorldCover 2021;
   - GLAD 2019;
   - Digital Earth Africa 2019;
   - ESA WorldCereal 2021;
   - Esri Land Cover 2025;
   - Dynamic World 2025 (the most common class over the year);
   - GFSAD 2015.

   ASAP v04 is scored (section 7) but not used for the strata, because it is not in Earth Engine.

   Each is turned into crop / not crop exactly as in Kerner et al. (2024).
2. **Agreement map:** for each 10 m pixel, the number of those 7 maps that say crop (0-7).
3. **Strata** per study area: **A** = 0 maps say crop, **B** = 1-2 maps, **C** = 3 or more maps. Stratum areas are computed in Earth Engine with `ee.Image.pixelArea()`.
4. **Allocation** (450 points):

   | | A | B | C | total |
   |---|---|---|---|---|
   | Aweil counties | 150 | 90 | 90 | 330 |
   | Bor South | 60 | 30 | 30 | 120 |

   If a stratum covers less than 0.1% of its area, it is merged with the next stratum down, and its points move with it.
5. **Draw:** simple random points inside each stratum (`stratifiedSample`, seed 42), at 10 m scale. Points must be at least 100 m apart.
6. **Split before labelling:** within each area × stratum, one third of the points go to **calibration** and two thirds to **test** (seed 42). The split is stored in the sample file.

## 4. Labelling (response design)

**Who:** all five group members. Each point is labelled by **2 people**, independently. Points are assigned in pairs so that every pair of people shares about 45 points, and each person labels about 180. The assignment is stored in the sample file.

**Blind:** labellers never see any cropland map or anyone else's labels.

**What each labeller sees for a point** (labelling tool, `cropland/label_tool/`):
- **12 monthly Sentinel-2 L2A images for 2025** of the same ~510 m × 510 m square, centred on the point, with the 10 m pixel marked, in true colour and false colour (near-infrared shows vegetation as red). Cloud-masked parts are grey.
- **The same 12 months for 2024**, shown only to recognise fallow (cue e). The label is always about 2025.
- **The NDVI curve** for the pixel through 2025, with the 500 m neighbourhood median and the pixel's 2024 curve drawn next to it.
- **A high-resolution image** (Esri World Imagery; check its date in Wayback) and a Google Earth link, for field shapes.
- The point's coordinates.

**The labelling key (human rules).** Answer in this order. Record every answer, not only the result.

1. **What covers most of the 10 m pixel?** Choose exactly one:
   - **water:** open water (dark blue or black) in most months of 2025 → **not crop (water)**;
   - **buildings / road:** roofs, compounds, roads → **not crop (settlement)**;
   - **trees / shrub:** tree crowns visible, or green through January-March → **not crop (trees/shrub)**;
   - **open land:** field or grass → go to the cues.

   Any answer other than open land ends the key: the tool sets every cue to "no".
2. For open land, answer the **crop cues** (yes / no / can't tell):
   - **a. Bare, tilled soil** in April-May: light, even, not a dark burn scar.
   - **b. Green-up** between June and August.
   - **c. Harvest:** goes brown or is cleared in August-November **earlier than the grass around it**.
   - **d. Field shape:** straight edges, rectangles, a patchwork, on the high-resolution image or on Sentinel-2.
   - **e. Cropped in 2024:** the 2024 strip shows bare soil in spring or an early harvest. Only needed when a-d don't already say crop.
3. **Decide** (the tool fills this in from the answers):
   - **crop, confidence 3:** d and (a or c).
   - **crop, confidence 2:** a and c without a clear shape.
   - **fallow, confidence 2:** d or e, but 2025 looks like grass all year (no a, no c). Counts as cropland.
   - **not crop (grass/bush):** none of the above.
   - **unsure, confidence 1:** three or more of a-d are "can't tell", or the images are missing. Write why.

   Labels are therefore **crop / fallow / not crop / unsure**. The tool pre-fills label, reason and confidence from the key; the labeller may overrule them and says why in the notes. Overrules are recorded (`overridden = 1`).
4. The tool records the time spent.

**Disagreements:** points where the two labels differ on cropland vs not cropland, or one is unsure, are settled by a third person looking at both sets of answers. They are **kept** and flagged `disagreed = 1`, not dropped as in Kerner et al. Crop vs fallow differences don't count as disagreement for the main estimate, but they are reported. We report agreement as raw agreement and Cohen's kappa.

**Pilot:** 30 points in Twic county (Warrap, outside the study areas), labelled by at least two people. **Go on** if at least 70% of pilot points get a confident (2 or 3) crop / not-crop label from both people. Otherwise, change the unit to "share of crop in a 30 m cell" before the real sample, and log the change.

## 5. Machine features (what the computer measures)

All are computed per 10 m pixel for 2025 in Earth Engine. Sentinel-2 is Level-2A surface reflectance (`COPERNICUS/S2_SR_HARMONIZED`), with clouds masked by Cloud Score+ `cs_cdf ≥ 0.6` and summarised as monthly medians. Missing months are filled from the neighbouring months.

| cue | feature(s) |
|---|---|
| a. bare soil before sowing | NDVI minimum and BSI (bare-soil index) maximum, April-May |
| b. green-up | NDVI maximum June-August minus NDVI minimum April-May |
| c. early harvest | NDVI drop from the June-August peak to September-November, minus the same drop for the 500 m neighbourhood median |
| d. field shape | NDVI texture (GLCM contrast, 3×3) on the June-August peak; edge density |
| trees | NDVI 10th percentile January-March |
| water | JRC Global Surface Water occurrence; Sentinel-1 VV minimum |
| settlement / homesteads | distance in metres to the nearest Google Open Buildings v3 polygon, capped at 2.5 km |
| burn | MODIS MCD64A1 burned in November 2024-April 2025 |
| cloudy months | Sentinel-1 VH monthly mean, June-September, and its range over the year (descending passes only: the only ones over South Sudan in 2025) |

## 6. Rules and models (classifier)

1. **Training data:** the calibration points only (≈150), with their adjudicated labels. Target: **cropped in 2025** (crop = 1; fallow and not crop = 0). Unsure points are left out of training. Fallow is left out of the map on purpose: in 2025 a fallow field looks like grass to the satellite, so a map can't find it reliably. Fallow enters the **cropland area** through the labelled sample only (section 7).
2. **Rule 1 (main):** a decision tree (scikit-learn `DecisionTreeClassifier`), using `class_weight="balanced"` and `min_samples_leaf=5`. The depth is chosen from **2, 3 or 4** by 5-fold cross-validation on the calibration points (F1), picking the smallest depth within 0.02 of the best. The tree is printed as if-then rules, saved as `rules_<date>.json` and then **frozen**.
3. **Benchmark (black box):** a random forest (500 trees) on the same features, and a random forest on Google's Satellite Embedding 2025. They show what readable rules cost in accuracy. They are never used for the map.
4. **Our map:** Rule 1 applied to every pixel in Earth Engine: land **cropped in 2025**. Output is 10 m in the study areas and 30 m nationally.

The **same JSON file** is read by both the Python scoring and the Earth Engine map, so the map and the scores cannot drift apart. A test checks that both give identical labels at the calibration points.

## 7. Scoring

- **Test points only** (≈300) for map accuracy. The calibration points are never used to score anything.
- **Maps compared:**
  - Rule 1 and the two random forest benchmarks;
  - WorldCover 2021, GLAD 2019, Digital Earth Africa 2019, WorldCereal 2021, Esri 2025, Dynamic World 2025, GFSAD 2015, ASAP v04 (crop if the cell is 5% crop or more).

  Each map's year is shown next to its score. Maps from before 2025 are expected to miss changes; that is a caveat, not a flaw in the test. The maps also define cropland differently: GLAD counts fallow up to 4 years, as we do, while WorldCover, WorldCereal and Dynamic World count only active crops. So each map is also scored against the cropped-only labels, and both scores are reported.
- **Estimators:** stratified estimators for strata that are not the map classes (Stehman 2014) give UA, PA, OA and F1, with standard errors. Maps whose 95% intervals overlap are **not ranked**.
- **Area:** from the adjudicated reference labels of **all** labelled points (calibration + test), for both definitions: **cropland** (crop + fallow, the main number) and **cropped in 2025** (crop only). The estimate is Σ W_h p̂_h per study area, with the standard error from the stratified formula (Olofsson et al. 2014), and a 95% interval of ±1.96 SE. Unsure points are left out and their number is reported.
- **Sensitivity check:** the area estimate is repeated counting all disagreed points as crop and then all as not crop, to show how much disagreement moves the result.

## 8. Flood overlay

- **Flood data:** NASA MCDWD flood masks for 2025, all flooded pixels June-December 2025.
- **Result:** flooded cropland (ha) under each map, and under the reference sample: the share of crop points that flooded, times the estimated crop area, with an interval.
- **Two contrasting areas:** in 2025 the Aweil counties flooded very little (about 2,000 flooded pixel-days in Aweil East and South), while Bor South flooded widely (about 69,000). So the overlay shows both cases: a flood season where the choice of cropland map hardly matters, and one where it decides whether a trigger fires.
- **Caveat:** the flood masks stop at 10° N.

## 9. What we will and won't claim

- **We will claim:** cropland area in the Aweil counties and Bor South in 2025 with an interval, and which maps are more or less accurate **there, in 2025**, on our test points.
- **We won't claim:** that our map is better anywhere else or in other years. Outside the study areas, our national map is labelled "not checked".

## 10. Deadlines

| date | milestone |
|---|---|
| 3 Oct | methodology frozen, pilot done, sample drawn, labelling tool ready |
| 9 Oct | 450 points labelled twice, disagreements settled |
| 12 Oct | Rule 1 frozen; benchmarks; national map |
| 15 Oct | scores, area, flood overlay, dashboard |
| **21 Oct** | **poster presentation** |
| **25 Oct** | **methodological + SLE report submitted** |

## Change log

- 30 Sep 2026: v1. Year changed from 2022 (Sprint 2 slides) to 2025, the most recent complete season, on Matteo's decision. Fallow counts as not crop (ZOA's interest is crops in the ground). Checked: 2025 Sentinel-2 has clear observations in every month over both areas. The median of clear images per month is 2-9; the thinnest months are August in Aweil and October in Bor South.
- 30 Sep 2026, later: fallow counts as cropland (group decision); labels become crop / fallow / not crop / unsure, and the cropped-only area is also reported. Hand rules dropped for time: only Rule 1 (decision tree) and the random-forest benchmarks. Deadlines moved two days earlier: 3, 9, 12 and 15 Oct. Strata use 7 maps (GFSAD 2015 in, ASAP scored only, because ASAP is not in Earth Engine). Esri and Dynamic World are the 2025 versions.
- 30 Sep 2026, evening: labelling key starts with one exclusive cover question (water / buildings / trees / open land); cue e "cropped in 2024" added, with 2024 images shown for context only; the tool pre-fills the label from the key. Rule 1 and the map target "cropped in 2025" (option b); cropland area (crop + fallow) comes from the sample. Features fixed: texture band (was ASM, now contrast), distance to buildings in metres (was wrong: masked-image distance), Sentinel-1 descending only.
- 30 Sep 2026, sample drawn (seed 42): Aweil strata A 2,929,918 ha (95.0%), B 145,327 ha (4.7%), C 9,934 ha (0.3%), 150/90/90 points. Bor South: C was 0.0036% of the area, merged into B by the 0.1% rule, so A 1,264,445 ha (90.6%) and B 131,838 ha (9.4%), 60/60 points. 450 points, 150 calibration / 300 test, 180 per labeller.
