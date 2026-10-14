# Cropland in ZOA's areas, 2025: declared methodology

Version 1, 30 Sep 2026. This file is fixed **before** any labelling. Every later change gets a dated line in the change log at the bottom, with the reason. Nothing in sections 1-8 may be changed after the test labels have been looked at.

## 1. Questions

1. **Area.** How much land in the five Aweil counties, and separately in Bor South, was cropland in 2025: cropped in the 2025 season **or fallow**? We also report the cropped-only part. Reported in hectares and as a share of land, with a 95% confidence interval. Since 5 Oct 2026 the main number comes from the labellers' estimate of **how much of each 210 m box is cropland** (section 2); the area of land whose box holds any cropland is reported next to it as an upper bound.
2. **Map accuracy.** How accurately do public cropland maps, and our own rule-based map, show that cropland? Reported per map: user's accuracy (precision), producer's accuracy (recall) and F1, each with a standard error.
3. **National picture** (description only). How much cropland does each map, ours included, show per state of South Sudan? Our map is not checked outside the two study areas.
4. **Flood** (small). How much 2025 flooding fell on cropland under each map?

## 2. Definitions

**Study areas:** the five Aweil counties (Aweil North, East, South, West, Centre; 3.09 M ha) and Bor South county (1.40 M ha), using `raw_data/Administrative boundaries/ssd_admin2.geojson`.

**Season:** the 2025 main rainy season. For the images, the "crop year" runs from **1 January to 31 December 2025**. It covers the dry season before sowing, sowing and growth, and harvest. The crop calendar for Northern Bahr el Ghazal (FEWS NET) is: sowing done by late May; groundnuts and sesame harvested from August; short-cycle sorghum harvested in September-October.

**Unit:** the **210 m × 210 m box** (21 × 21 Sentinel-2 pixels, ±105 m) centred on the sample point: the outer yellow box of the labelling tool. (Until 4 Oct 2026 the unit was the single 10 m pixel; see the change log for how the box size was checked.)

**Cropland (what we count):** fields that were **cropped in the 2025 season, or fallow**. Fallow means a field with visible structure (edges, plots) that was not sown in 2025. Every label records which of the two it is, so we can also report the "cropped in 2025" area on its own. That is the part closest to ZOA's trigger ("flood inundating cropland").

| counts as cropland | does not count |
|---|---|
| sorghum, maize, groundnut, sesame, cassava, rice, vegetables | grassland, bush, trees, wetland, open water |
| small plots next to homesteads (home gardens) | settlement: roofs, compounds, roads |
| flood-recession plots cropped in 2025 | burned or grazed grassland with no field structure |
| **fallow**: field structure visible, not sown in 2025 | |

A box is labelled by **presence**: **crop** if at least one field in it was cropped in 2025; **fallow** if it holds a field but none was cropped in 2025; **not crop** if there is no field anywhere in it. One small field or home garden is enough. The label belongs to the sample point.

**Cropland share of the box.** For every box the labeller also estimates how much of it is cropland (crop and fallow fields together): **0, under 10%, 10-25%, 25-50%, over 50%**. A "not crop" box is 0; a crop or fallow box needs a share above 0. The final share of a point is the mean of the class middles (0, 5, 17.5, 37.5, 75%) of the labellers whose label agrees with the final cropland / not cropland.

**What the area numbers mean.** The sample is a random sample of pixels, and each pixel gets the values of the 210 m box around it.
- **Main: share of box.** The mean box share over random boxes equals the cropland share of the land (every pixel sits in as many boxes as every other), so this estimates **cropland area** itself. Its error comes from the labellers' rough classes, not from the box.
- **Upper bound: box holds cropland.** The share of land whose 210 m box holds any cropland: roughly land within ~100 m of a field. It is **larger than the cropland area**, by a factor that depends on how scattered the fields are. Checked on 5 Oct 2026 with 3,000 random boxes per area on two public 2025 maps: 3.2× (Esri) and 9.2× (Dynamic World) in Aweil, 2.6-4.0× in Bor South. It is reported under that name, never as hectares of cropland.

For "cropped in 2025" the share counts only in boxes labelled crop; when such a box also holds a fallow field, its share includes that field, so the cropped-only share is slightly too high.

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
5. **Draw:** simple random points inside each stratum (`stratifiedSample`, seed 42), at 10 m scale. Points must be at least 100 m apart. Since the unit became a 210 m box, boxes could overlap for points 100-210 m apart; checked on 5 Oct 2026: no two of the 450 points are closer than 210 m (5th percentile of nearest-neighbour distance 575 m), so no boxes overlap and no calibration box touches a test box.
6. **Split before labelling:** within each area × stratum, one third of the points go to **calibration** and two thirds to **test** (seed 42). The split is stored in the sample file.

## 4. Labelling (response design)

**Who:** all five group members. Each point is labelled by **2 people**, independently: neither sees the other's label. Within each area × stratum × split group the points go round all 10 pairs of people in turn, so every pair shares exactly 45 points, everyone labels 180, and everyone gets the same mix: 20 + 40 Aweil A, 12 + 24 Aweil B, 12 + 24 Aweil C, 8 + 16 Bor South A, 8 + 16 Bor South B (calibration + test). A person who labels more or less generously therefore weighs the same on every stratum and on both splits. The assignment is stored in the sample file (`labeller_1`, `labeller_2`).

**Blind:** labellers never see any cropland map or anyone else's labels.

**What each labeller sees for a point** (labelling tool, `cropland/label_tool/`):
- **12 monthly Sentinel-2 L2A images for 2025** of the same ~510 m × 510 m square, centred on the point, with the 210 m box marked in yellow, in true colour and false colour (near-infrared shows vegetation as red). Cloud-masked parts are grey.
- **The same 12 months for 2024**, shown only to recognise fallow (cue e). The label is always about 2025.
- **The NDVI curves of the box's patches** through 2025: the box's 441 pixels are grouped by their 2025 NDVI curve (k-means, 2 or 3 groups, kept only if every group covers at least 5% of the box and every two group curves differ by at least 0.08 NDVI in some month; otherwise the box is one patch). Each patch's median curve is drawn with its share of the box and a small map of where it is, next to the 500 m neighbourhood median; the same patches' 2024 curves on request. A month counts only if at least half the box is cloud-free. Reason: the box median looked like the 500 m median at 60% of the sample points (never more than 0.05 apart), while the spread inside the box was above 0.15 at 84% of them, so the median hid the fields. Patches are what differs, not what is crop: the labeller still decides.
- **The radar curve** (Sentinel-1 VH, descending passes, mean over the box, dB) for every month of 2025: it sees through the clouds of the rainy season.
- **A high-resolution image** (Esri World Imagery, ~660 m square, with the box marked) with its **capture date, provider and resolution** from Esri's metadata; images from before 2025 are flagged ("field shapes only"). Plus Wayback and Google Earth links.
- Any month can be **enlarged**, 2025 next to 2024.
- The point's coordinates.

**The labelling key (human rules).** Answer in this order. Record every answer, not only the result.

1. **Is there open land (field or grass) anywhere in the 210 m box?** If not, what is the box mostly? Choose exactly one:
   - **water:** open water (dark blue or black) in most months of 2025 → **not crop (water)**;
   - **buildings / road:** roofs, compounds, roads → **not crop (settlement)**;
   - **trees / shrub:** tree crowns visible, or green through January-March → **not crop (trees/shrub)**;
   - **open land:** field or grass → go to the cues.

   Any answer other than open land ends the key: the tool sets every cue to "no".
2. For open land, answer the **crop cues** (yes / no / can't tell):
   Each cue is about **the most field-like patch in the box**:
   - **a. Bare, tilled soil** in April-May: light, even, not a dark burn scar.
   - **b. Green-up** between June and August.
   - **c. Harvest:** goes brown or is cleared in August-November **earlier than the grass around the box**.
   - **d. Field shape:** straight edges, rectangles, a patchwork inside the box, on the high-resolution image or on Sentinel-2.
   - **e. Cropped in 2024:** the 2024 strip shows bare soil in spring or an early harvest. Only needed when a-d don't already say crop.

   If the box holds both a cropped field and a fallow one, the label is crop.
3. **Decide** (the tool fills this in from the answers):
   - **crop, confidence 3:** d and (a or c).
   - **crop, confidence 2:** a and c without a clear shape.
   - **fallow, confidence 2:** d or e, but 2025 looks like grass all year (no a, no c). Counts as cropland.
   - **not crop (grass/bush):** none of the above.
   - **unsure, confidence 1:** three or more of a-d are "can't tell", or the images are missing. Write why.

   Labels are therefore **crop / fallow / not crop / unsure**, plus the **cropland share of the box** (section 2), which the tool requires for crop and fallow and sets to 0 for not crop. The tool pre-fills label, reason and confidence from the key; the labeller may overrule them and says why in the notes. Overrules are recorded (`overridden = 1`).
4. The tool records the time spent, the unit (`unit = 210m`) and the box corners in degrees (`box_west`, `box_south`, `box_east`, `box_north`, WGS84; the same 10 m grid as the images) with every label. A labeller can mark a hard point "come back later" (`L`); this is kept in the browser only and is not a label.

**Disagreements are not settled.** Nobody overrules either labeller and there is no third person: both labels are kept and the disagreement is reported (group decision, 5 Oct 2026). Per point (`06_merge_labels.py`):
- **agreed:** both give the same label → that label.
- **disagreed:** cropland vs not cropland, or one unsure → flagged `disagreed = 1`, not dropped as in Kerner et al.
- **crop vs fallow:** both say cropland, one crop and one fallow → cropland for sure, cropped-in-2025 not agreed.

Each point also gets the **mean of its two labellers** for each definition (cropland 0 / 0.5 / 1, cropped 0 / 0.5 / 1, and the box share; an "unsure" is left out of the mean). The area estimates use these means, so a disagreed point counts half and no tiebreaker is needed (section 7). Fitting and accuracy use only the points both agree on for that definition. We report raw agreement and Cohen's kappa, overall and per pair of labellers, and list every disagreement with both people's answers (`disagreements.csv`).

**Pilot:** 30 points in Twic county (Warrap, outside the study areas), labelled by at least two people. **Go on** if at least 70% of pilot points get a confident (2 or 3) crop / not-crop label from both people. Otherwise, change the unit to "share of crop in a 30 m cell" before the real sample, and log the change. The pilot was labelled on the 10 m pixel and is kept as it was; the sample is labelled on the 210 m box (change log, 4 Oct 2026).

## 4b. Regional differences

The two areas farm differently, so the key and the scoring take the place into account.

- **Aweil** (Northern Bahr el Ghazal): rain-fed sorghum, groundnut and sesame near homesteads; harvest September-October; an irrigated rice scheme near Aweil town.
- **Bor South** (Jonglei, White Nile floodplain): crops on higher ground, plus flood-recession plots planted when the water falls (November-February). For cue c ("harvest earlier than the grass") and the water question, recession plots look different: flooded in August-October, green in December-February. Labellers are told this in the tool for every Bor South point; these plots count as crop.
- **Order:** points reach each labeller in random order, mixing both areas, so tiredness or learning over the session does not line up with one area.
- **One Rule 1 for both areas:** the tree is trained on both areas together; area is not a feature, because the national map has no area to give it. Accuracy is reported **per area**. If Rule 1 is clearly worse in one area, we report it and say that one set of rules does not fit both landscapes. We do not re-tune it on test points.
- **National map:** outside the two areas the landscape changes (the wet south, the eastern plains). The national map is marked "not checked" there.
- **Pilot coverage:** the pilot (Twic county) resembles Aweil, not Bor South. The pilot therefore tests the tool and the key, not the floodplain case.

## 5. Machine features (what the computer measures)

All are computed per 10 m pixel for 2025 in Earth Engine and then **summarised over the 210 m box** around each pixel (21 × 21 pixels) by its most crop-like part, because one field anywhere in the box makes it crop: the 10th percentile for NDVI minimum April-May and distance to buildings, the 90th percentile for BSI, green-up, the two harvest drops, texture and edge density, and the mean for the rest (trees, water, burn, radar). A feature then describes the same box the labeller judged. Sentinel-2 is Level-2A surface reflectance (`COPERNICUS/S2_SR_HARMONIZED`), with clouds masked by Cloud Score+ `cs_cdf ≥ 0.6` and summarised as monthly medians. Missing months are filled from the neighbouring months.

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

1. **Training data:** the calibration points only (≈150) where both labellers agree on the target, read from `model_table.csv` with `model_data.load()`, so every model trains on exactly the same points, features and targets. Target: **cropped in 2025** (crop = 1; fallow and not crop = 0). Disagreed, crop-vs-fallow and unsure points are left out of training; their number is reported. Fallow is left out of the map on purpose: in 2025 a fallow field looks like grass to the satellite, so a map can't find it reliably. Fallow enters the **cropland area** through the labelled sample only (section 7).
2. **Rule 1 (main):** a decision tree (scikit-learn `DecisionTreeClassifier`), using `class_weight="balanced"` and `min_samples_leaf=5`. The depth is chosen from **2, 3 or 4** by 5-fold cross-validation on the calibration points (F1), picking the smallest depth within 0.02 of the best. The tree is printed as if-then rules, saved as `rules_<date>.json` and then **frozen**.
3. **Benchmark (black box):** a random forest (500 trees) on the same features, and a random forest on Google's Satellite Embedding 2025. They show what readable rules cost in accuracy. They are never used for the map.
4. **Our map:** Rule 1 applied to every pixel in Earth Engine, on the box features: a pixel is crop when the 210 m box around it holds land **cropped in 2025**. Output is 10 m in the study areas and 30 m nationally (at 30 m the box is rounded to whole 30 m pixels).

The **same JSON file** is read by both the Python scoring and the Earth Engine map, so the map and the scores cannot drift apart. A test checks that both give identical labels at the calibration points.

5. **Other models (Wei, Matei):** further decision trees on the 210 m box, e.g. one per study area, follow the same rules: train on `model_data.load("calibration", ...)` only, inputs = the 18 features (or the embedding), never the labellers' answers, share or confidence; choose settings by cross-validation on the calibration points; freeze before looking at the test points. A model is scored by writing `results/predictions_<name>.csv` (id, prediction 1/0 for all 450 points); `09_score.py` scores it exactly like Rule 1 and the public maps. A tree saved through `rules.from_tree` can also be mapped by `08_run_map.py`.

## 7. Scoring

- **Test points only** (≈300) for map accuracy, and only those where both labellers agree on the definition scored (cropland or cropped in 2025); the number left out is in the table. The calibration points are never used to score anything.
- **Maps compared:**
  - Rule 1 and the two random forest benchmarks;
  - WorldCover 2021, GLAD 2019, Digital Earth Africa 2019, WorldCereal 2021, Esri 2025, Dynamic World 2025, GFSAD 2015, ASAP v04 (crop if the cell is 5% crop or more).

  **Map value at a point:** a map says crop when it calls **any** pixel of the point's 210 m box crop, the same presence rule as the labels. (Before, the map was read at the point's own pixel only.) This favours maps that call many scattered pixels crop, so each public map is also compared on **share**: its share of each test box against the labelled share (mean of each, with the stratum weights, and the mean absolute gap). ASAP cells (~1 km) are larger than the box and are read at the point. Each map's year is shown next to its score. Maps from before 2025 are expected to miss changes; that is a caveat, not a flaw in the test. The maps also define cropland differently: GLAD counts fallow up to 4 years, as we do, while WorldCover, WorldCereal and Dynamic World count only active crops. So each map is also scored against the cropped-only labels, and both scores are reported.
- **Estimators:** stratified estimators for strata that are not the map classes (Stehman 2014) give UA, PA, OA and F1, with standard errors. Maps whose 95% intervals overlap are **not ranked**.
- **Area:** from the **mean of the two labellers** at **all** labelled points (calibration + test), for both definitions: **cropland** (crop + fallow, the main number) and **cropped in 2025** (crop only), each as **share of box** (main) and **box holds it** (upper bound). The estimate is Σ W_h ȳ_h per study area, with the stratified standard error (Olofsson et al. 2014; s²/n per stratum, which equals p(1-p)/(n-1) for 0/1 values), and a 95% interval of ±1.96 SE. Points both labellers called unsure, and points without a share, are left out and their number is reported.
- **Sensitivity check:** the upper-bound estimate is repeated counting every point the two labellers split on as cropland and then as not cropland, to show how much disagreement moves the result.

## 8. Flood overlay

- **Flood data:** NASA MCDWD flood masks for 2025, all flooded pixels June-December 2025.
- **Result:** flooded cropland (ha) under each map, and under the reference sample: the labelled cropland share of the boxes that lie in a flood cell (0 elsewhere), averaged with the stratum weights, times the study area, with an interval; and the upper bound from boxes that hold any cropland.
- **Two contrasting areas:** in 2025 the Aweil counties flooded very little (about 2,000 flooded pixel-days in Aweil East and South), while Bor South flooded widely (about 69,000). So the overlay shows both cases: a flood season where the choice of cropland map hardly matters, and one where it decides whether a trigger fires.
- **Caveat:** the flood masks stop at 10° N.

## 9. What we will and won't claim

- **We will claim:** cropland area in the Aweil counties and Bor South in 2025 with an interval, and which maps are more or less accurate **there, in 2025**, on our test points.
- **We won't claim:** that our map is better anywhere else or in other years. Outside the study areas, our national map is labelled "not checked".

## 10. Deadlines

| date | milestone |
|---|---|
| 3 Oct | methodology frozen, pilot done, sample drawn, labelling tool ready |
| 9 Oct | 450 points labelled twice; disagreements listed, not settled |
| 12 Oct | Rule 1 frozen; benchmarks; national map |
| 15 Oct | scores, area, flood overlay, dashboard |
| **21 Oct** | **poster presentation** |
| **25 Oct** | **methodological + SLE report submitted** |

## Change log

- 30 Sep 2026: v1. Year changed from 2022 (Sprint 2 slides) to 2025, the most recent complete season, on Matteo's decision. Fallow counts as not crop (ZOA's interest is crops in the ground). Checked: 2025 Sentinel-2 has clear observations in every month over both areas. The median of clear images per month is 2-9; the thinnest months are August in Aweil and October in Bor South.
- 30 Sep 2026, later: fallow counts as cropland (group decision); labels become crop / fallow / not crop / unsure, and the cropped-only area is also reported. Hand rules dropped for time: only Rule 1 (decision tree) and the random-forest benchmarks. Deadlines moved two days earlier: 3, 9, 12 and 15 Oct. Strata use 7 maps (GFSAD 2015 in, ASAP scored only, because ASAP is not in Earth Engine). Esri and Dynamic World are the 2025 versions.
- 30 Sep 2026, evening: labelling key starts with one exclusive cover question (water / buildings / trees / open land); cue e "cropped in 2024" added, with 2024 images shown for context only; the tool pre-fills the label from the key. Rule 1 and the map target "cropped in 2025" (option b); cropland area (crop + fallow) comes from the sample. Features fixed: texture band (was ASM, now contrast), distance to buildings in metres (was wrong: masked-image distance), Sentinel-1 descending only.
- 30 Sep 2026, sample drawn (seed 42): Aweil strata A 2,929,918 ha (95.0%), B 145,327 ha (4.7%), C 9,934 ha (0.3%), 150/90/90 points. Bor South: C was 0.0036% of the area, merged into B by the 0.1% rule, so A 1,264,445 ha (90.6%) and B 131,838 ha (9.4%), 60/60 points. 450 points, 150 calibration / 300 test, 180 per labeller.
- 1 Oct 2026: section 4b (regional differences) added. Labels now saved automatically by label_server.py into cropland/labels/, one file per labeller.
- 4 Oct 2026: **unit changed from the 10 m pixel to the outer yellow box, 210 m × 210 m**, before any sample point was labelled (group decision). Reason: at 10 m the labellers could not tell what covered a single pixel, so in practice we judged the whole outer box.
  - **Box size, checked.** The tool called the outer box "≈ 110 m", but it is **210 m**. Code (`04_image_strips.py`, first version): each month is a 51 × 51 pixel grid at 10 m, enlarged 3×; the outer box was drawn at screen pixels 44 and 108, i.e. ±10 ground pixels around the centre pixel. Measured on the labelled images (P01 2025, S001 2025, S200 2024): the yellow edges sit at rows 44 and 108 of each 153-pixel tile; inside are 63 screen pixels = 21 ground pixels × 10 m = 210 m, centred on the point (±105 m). The new tool draws the box in exactly the same place and drops the small centre-pixel square.
  - **Rule: presence.** A box is crop if any field in it was cropped in 2025, fallow if it has a field but none was cropped, not crop if there is no field (group decision). The key's first question becomes "is there open land anywhere in the box", and the cues are about the most field-like patch.
  - **Consequences.** The area estimate becomes "land whose 210 m box holds cropland", an **upper bound** on cropland area, reported under that name (section 2). Features are summarised over the box by its most crop-like part (section 5). Public maps say crop at a point when any pixel in the box is crop (section 7). The NDVI curve in the tool is the box median with a 10th-90th percentile band; the tool adds a radar curve, the Esri capture date, enlarged months and a "come back later" flag. Labels carry `unit = 210m`; 06_merge_labels.py warns about labels without it.
  - **Pilot** labels (10 m pixel) are kept as they are. No pilot point was called crop by all five; the four split points (P01, P12, P20, P24) are in the examples panel for a group discussion at box level. Yassin's pilot file had git conflict markers around two identical copies; one copy kept, labels unchanged.
  - 5 Oct 2026: **cropland share of the box added** (0 / <10 / 10-25 / 25-50 / >50%, `crop_share`), because the presence rule alone inflated the area 2.6-9× (section 2, checked on Esri and Dynamic World 2025). The share gives the main area estimate; presence stays the label, the map target and the upper bound. Public maps are also compared on box share. The high-resolution image's date is marked green when it shows the 2025 season (taken in 2025, or January-March 2026 just after the harvest: 336 of the 450 sample points) and orange otherwise. No two sample boxes overlap (section 3). 06, 09, 10 and estimators.py updated; `test_area_share` added.
  - 5 Oct 2026: the tool's greenness chart shows the box split into patches (section 4) instead of only the box median, because box and 500 m medians were nearly the same. Sample: 61 boxes stay one patch, 72 split in 2, 317 in 3 (Aweil mostly 3: scattered trees, grass, bare soil). Step 04 rerun; features unchanged.
  - Steps 04 and 05 rerun on 4 Oct 2026 for pilot (30) and sample (450), on Earth Engine project `southsudan-509222` (Yassin; same public data). The new images have the box at the same pixels as before (checked on P01). All 480 points got an Esri capture date. Radar: Aweil has no descending Sentinel-1 pass in January-April 2025 (Bor South has all months), so the tool's radar curve starts in May there; the radar features (June-September) miss only 4 points in June. `test_cropland.py --ee` passes: the Earth Engine map gives the same label as the Python rules on the new box features.
- 5 Oct 2026 (later), before any sample point was labelled (group decision):
  - **No adjudication.** Disagreements are kept and reported, never settled by a third person. Areas use the mean of the two labellers (a split point counts half); fitting and accuracy use the points both agree on. `adjudication.csv` replaced by `disagreements.csv` (report only). Sections 4, 6 and 7 updated.
  - **Labeller pairs rebalanced** inside each area × stratum × split group (`03_agreement_and_sample.py labellers`). Before, pairs were balanced only overall (each person 46-68 Aweil A points, 56-65 calibration points); now every pair has 45 points and every person the same mix (section 4). Points, ids, strata, split, images and features unchanged; only `labeller_1`/`labeller_2` in `sample.csv` and `data_sample.js` changed (410 of 450 points got a different pair).
  - **Model data in one place:** `06_merge_labels.py` also writes `model_table.csv` (one row per point: area, stratum, split, hectares per point, labels, two-labeller means, the 18 features, the embedding), read by `model_data.load()` for Rule 1, the benchmarks and Wei and Matei's trees. Other models are scored from `results/predictions_<name>.csv` (section 6.5).
- 12 Oct 2026, after all 450 points were labelled twice and Rule 1 was frozen (`rule1_2026-10-12.json`, calibration points only), **before any test label was read** (step 09 not yet run). Proposed by Yassin on behalf of the group; to confirm at the next meeting. Sections 1-8 unchanged; additions to the evaluation:
  - **Area interval.** The area is also reported with an adjusted upper bound (`evaluation.area_interval`): same estimate and lower bound; per stratum at least the variance it would have with one more cropland and one more empty box, using the cropland shares of the whole area. Reason: a simulation of our design (`evaluation.simulate_interval_coverage`; report notes 06, section 6.5) showed the usual ±1.96 SE interval holds the true area only 47-94% of the time when crop is rare in stratum A, every miss below the truth; the adjusted interval reaches 88-100%.
  - **Error analysis** of every map by the labellers' cover class, cues, homestead distance, fallow and box share (`evaluation.error_analysis`).
  - **Trigger-decision agreement** of every map with the sample's flooded-cropland interval (`evaluation.trigger_agreement`).
  - **Our scores next to the published ones** (Kerner et al. 2024, Adebayo et al. 2026; `evaluation.published_vs_ours`).
  - **Points needed** with agreement strata against one-map strata (`evaluation.design_efficiency`), and the **readability** of the frozen rules (`evaluation.rule_complexity`).
  - Run on Yassin's Earth Engine project (`southsudan-509222`); `common.py` takes the course data from `../data-JBG060-2026/` when `raw_data/` is empty, and the asset folder follows `CROPLAND_EE_PROJECT`. No change to any number or rule.
- 12 Oct 2026, later, **after step 09 had scored Rule 1 and the benchmarks on the test points**. Group question: "logistic regression or trees?" Decided by Yassin for the group; to confirm at the next meeting.
  - **Two logistic regression models added** as other models (section 6.5), chosen **without test labels**: all candidates were compared by 5-fold cross-validation repeated 20 times on the 125 agreed calibration points (`12_other_models.py compare`, `results/model_cv.csv`): trees of depth 1-4 F1 0.85-0.86, logistic regression 0.87-0.88, random forest 0.92 (unweighted calibration scores, not comparable with test scores). Frozen: `logistic_l2` (the 18 features, standardised, L2 penalty chosen by an inner cross-validation) and `logistic_rule1_inputs` (only distance to buildings and edge density, the two inputs of Rule 1, so tree against linear on the same inputs). Saved as `logistic_l2_2026-10-12.json` and `logistic_rule1_inputs_2026-10-12.json` (coefficients, means, SDs: crop if intercept + sum(coef × (x - mean) / sd) > 0); predictions in `results/predictions_<name>.csv`. Both are scored once and reported whatever the score, labelled "added after the first test scores". Rule 1 stays the main model and the map.
  - **Data limit for any per-area model:** Bor South has 1 agreed crop point among its 40 calibration points and 0 among its 80 test points, so no model can be fitted for Bor South alone and recall/F1 cannot be computed there; Bor South is scored on false crop only.
  - **`features.py`:** a month without a Sentinel-1 pass becomes a masked image instead of an image without bands. The Aweil map export of Rule 1 failed on this (no descending pass January-April 2025 over Aweil alone). Checked: all 18 features identical at 20 sample points (10 per area); Rule 1 does not use radar.
- 12 Oct 2026, evening. **Reuse for other areas and countries** (group wish, via Yassin): settings moved from `common.py` into `config/south_sudan_2025.toml` (the default; `CROPLAND_CONFIG` picks another), with `config/TEMPLATE.toml`, `make_new_area.py` (clean copy without our data), `REUSE.md` (guide) and a guard that stops a new config from writing over this study's files. Steps 03, 04, `features.py` and the labelling tool read year, crop-calendar months, strata maps, labellers and cue texts from the config (tool: `label_tool/config.js`, written by `04_image_strips.py config`). `09_score.py` skips ASAP and `11_evaluate.py` skips its study-only tables when those files are missing. **No number changes:** the Earth Engine graphs of the features, strata and public maps are identical (same hashes) under the default config; the tool renders a sample point identically; all result tables are byte-identical after rerunning step 11; tests pass (`test_config` added).
- 12 Oct 2026, evening. **Everything works on the 210 m box** (checked): features at the points and in the map are box summaries (`feature_image`); Rule 1, the logistic models and the random forests are fitted and scored on them; public maps count as crop when any pixel of the box is crop. Consequence written down: a pixel of our map means "the 210 m box around this pixel holds a cropped field", so hectares counted from our map are **land whose box holds crop** (corrected 14 Oct, see below: our map marks 22.6% of Aweil, above the sample's upper bound of 14.3%), not cropland area. `11_evaluate.py` therefore compares our map's flooded hectares with the sample's "box holds it" upper bound, and the public maps (pixel counts) with the share of box. The cropland area itself comes from the sample only (section 7).
- 13-14 Oct 2026. **Flood overlay run** (step 10, after the three Rule 1 map assets finished). Aweil: 10,314 ha flooded June-December 2025 (0.33% of the area); Bor South 29,419 ha (2.1%). **Finding: the sample cannot measure flooded cropland in 2025.** Only 1 of the 330 Aweil points and 2 of the 120 Bor South points fall in a flood cell (random points over the whole area), so the sample's flooded cropland (Aweil 606 ha, 0-1,792; Bor South 0 ha, 0-0) rests on one and two points, and its usual interval looks precise without being so. `11_evaluate.py` now writes `results/flooded_cropland_bounds.csv` (points in flood cells, usual and adjusted upper bound) and judges the trigger check against the adjusted upper bound capped at the flooded land; the sample then says "cannot tell" at every threshold (100-5,000 ha) in both areas. Decided by Yassin's session after seeing the flood numbers, to be confirmed by the group: it only widens the sample's interval, no map value changes. Map numbers stand (flooded cropland under the public maps: Aweil 10-307 ha, Bor South 0-10 ha except Dynamic World 1,606 ha; our map 3,588 and 126 ha, which count land whose 210 m box holds crop). Lesson for the next season (REUSE): a flooded-cropland estimate needs its own stratum on flood-prone land.
- 14 Oct 2026. **Past floods on today's cropland, 2000-2025** (`10b_flood_history.py`; Yassin's request, analysis added after the 2025 results). A scenario, not history: the 2025 labels and Rule 1 stand for today's cropland, the public maps are used as they are, and each year's NASA flood mask (June-December, 1+ and 10+ flood days, as in the EDA) is laid over them. Public maps per flood cell from the EDA cache (2022 values identical to figure 07); Rule 1 per flood cell computed once in Earth Engine for every cell that ever flooded (2025 check: 3,593 ha against 3,588 in step 10). Sample, two estimators chosen with Yassin before computing the final tables: **ratio** (main: the stratum-weighted cropland share of the sample boxes on flooded land times the flooded land, which the flood mask gives exactly; cautious upper bound as `evaluation.area_interval`) and **expansion** (as in step 10). Two rules set after a first look, because with 1-4 points the ratio repeats those few boxes and its lower bound is not credible: the ratio needs **at least 5 sample points on flooded land**, otherwise "too few points"; and in the trigger hindcast, years in which less land flooded than the threshold are marked, not counted as agreement. Results (Aweil, 1+ day): 9 of 26 years have enough points; in all 9 the sample's estimate is 4-16 times the median of the 8 public maps, and above all 8 in 5 of them (level with the highest in a sixth; 2022: 7,263 ha, 639-14,336, against 331-3,572). The sample confirms a trigger at 100-500 ha in 2008 and 2022 and at 1,000 ha in 2008; Esri, GLAD and WorldCover would have stayed silent at 500 ha in 2022 and at 1,000 ha in 2008. Bor South: 2 informative years (2007, 2010); in 2007 the sample's upper bound (2,096 ha) is below 5,000 ha while both Dynamic World versions would have fired. Outputs: `results/flood_history.csv`, `results/trigger_hindcast.csv`, figure 12 (`deliverables/cropland_report/figures/12_flood_history.png`, twin `tables/flood_history.csv`).
- 14 Oct 2026, later. **Where our results change the flood picture** (`10c_flood_map.py`): for one area and year (Aweil 2022), every flooded cell with each public map's crop share (EDA cache) and our map's (10b cache): figure 13 (before = WorldCereal 2021, the best public map on our test points), an interactive map (`deliverables/cropland_report/maps/flood_aweil_2022.html`, any public map as 'before') and a per-cell table. WorldCereal shows crop in 1,646 of 10,184 flooded cells; our map adds 3,627. Display only: no estimate changes; amounts stay with the sample. **Figures 14 and 15** (area vs maps; scorecard) drawn by `11_evaluate.py` from the existing tables. **Prepared for applying models to more land:** `rules.py` now also applies the logistic-regression JSON files (same predictions as frozen, 450 of 450; Earth Engine map = Python at all 150 calibration points for Rule 1 and both logistic models), and `rules.to_ee` selects the model's own features before filling missing values (it failed for any model using fewer than the 18 features); `10b_flood_history.py model <rules.json>` works for any frozen model, not only Rule 1 (outputs unchanged).
- 14 Oct 2026, later. **Correction and national map.** (1) The 12 Oct entry compared our map with the sample using 13.8%, Rule 1's share at the *agreed test points* (from `accuracy.csv`). Counted over all its pixels (from the native 10 m pixels, Earth Engine `reduceResolution`), the map marks **22.6% of the Aweil counties** and 1.2% of Bor South; the stratified estimate from all 330 labelled Aweil points is 16.3% (SE 2.6). Both are above the sample's share of boxes holding cropland (14.3%; adjusted upper bound 19.3%): **our map over-marks**, as its precision of 0.70 says (it also marks boxes near homesteads without a field). Its hectares stay an upper bound, now clearly one. (2) The **national map** (`rule1_2026-10-12_south_sudan`, 30 m, exported 12 Oct) agrees with the 10 m map where both exist (Aweil 23.6% against 22.6%; Bor South 2.1% against 1.2%). It is not checked outside the two areas. Shares must be counted from the native pixels: Earth Engine's coarser overview layers of a 0/1 map round each cell, which inflated a first 1 km read-out (e.g. Northern Bahr el Ghazal 31%). The flood numbers are unaffected (counted at 10 m).
- 14 Oct 2026, evening. **The 30 m national map on our test points** (`national_map.py score`, a check, no model changed): the 10 m map gives Rule 1's answer at all 450 points (as it should); the 30 m national run agrees at 96% of the Aweil points and keeps recall (0.75) but marks more empty boxes: precision 0.50, F1 0.60 (± 0.09) against 0.72 at 10 m. Coarser pixels see field edges less sharply. `results/rule1_national_test_points.csv`, `results/rule1_map_at_points.csv`.
- 14 Oct 2026, evening. **National check sample, drawn and frozen before labelling** (`national_check.py`; Yassin's request: how accurate is our map outside the study areas, and the public maps with it). Domain: South Sudan without the six study counties. 20,000 uniform random points (equal-area, seed 42) classed by our national map (its 30 m pixel) and the seven public maps (their 10 m pixels) into M (our map marks the point; 5.7% of the land), P (only a public map calls it crop; 4.3%) and N (neither; 90.0%); the first 80 / 60 / 60 points of each stratum in random order form the sample (a simple random sample within each stratum). Stratum weights from the same 20,000 points (SE at most 0.2 percentage points). Two labellers per box, pairs balanced (80 boxes each). All 200 are test points for Rule 1 and the public maps; one third per stratum is marked calibration for future national models only. Same tool and key (set "national"), with a two-season note for the Equatoria states. Scoring (`national_check.py score`) as in 09: precision, recall, F1 with Stehman's estimators, and the national area.
- 14 Oct 2026, evening. **How the labellers worked (their own account, after labelling).** Besides the tool's images they used Google Maps (sharper, zoomable, but undated: "not binding"), Esri Wayback (older captures) and single Sentinel-2 scenes in a browser (more dates per month); not everyone used the same sources. One labeller counted cropland just outside the box in a few early labels and then stopped; the notes of two labels say so (S019: became a split; S400: agreed crop, share inflated). **No label was changed**: correcting labels after the scores are known would bias the check more than the errors do. A label counts only when the second labeller confirms it; splits are left out of scoring and count half in the area (Aweil, box holds cropland: 10.3%-18.3% if every split were empty / cropland, against 14.3%). Reported in the report (Discussion, appendix "Known errors in the data"); `LABELLING_GUIDE.md` clarified before the national round (only the box counts; undated images for shapes only; extra sources in the notes).
- 14 Oct 2026, evening. **Dashboard, first version** (`14_dashboard.py` + `dashboard/template.html` -> `deliverables/cropland_report/dashboard.html`): reads the result tables only, changes no number.
- 14 Oct 2026, late (from a teammate's code review). **Interval lower bounds stop at 0.** `09_score.py` wrote the usual interval without a floor, so `results/area.csv` had negative lower bounds in Bor South for the box-holds-it measure (cropland -277 ha, cropped in 2025 -2,322 ha). A share cannot be negative: the code now clamps at 0 (as `area_adjusted.csv`, `10_flood.py` and the figures already did), and the four cells in `area.csv` were set to 0 by hand, which is exactly what the fixed code writes; nothing else changed. The report and dashboard read `area_adjusted.csv` and are unaffected. The same fix went into `national_check.py` before its first run. The docstring of `06_merge_labels.py` was out of date: disagreed points are not bounded in the area estimates, they take the mean of the two labels (a split counts half; with one "unsure" the other label counts), with the all-yes / all-no split counts as a sensitivity check in 09.
- 14 Oct 2026, late. **The national check sample is not labelled** (group decision, via Yassin): the group does not label further within this project. The sample, its images (`national_check.py strips`) and the clarified guide are handed over; our map stays unchecked outside Aweil and Bor South. Instead, **without labels**, `national_map.py compare` sets our map against the public maps at the 20,000 random points of the sample design (our map's 30 m pixel, each public map's 10 m pixel at the point): of the land at least two public maps call crop, our map marks 29% outside the study areas; 96% in Warrap and 83% in Lakes (homestead farming like Aweil's), 2% in Upper Nile and 7% in Eastern Equatoria (large schemes, river farming, two rainy seasons). Agreement, not accuracy. `results/rule1_national_vs_public.csv`.
- 14 Oct 2026, late. **No hand-over of the national sample either** (Yassin): the 200-box sample, its images and the "national" set of the labelling tool are removed; `national_check.py` keeps only the 20,000 random points that `national_map.py compare` uses. Our map is unchecked outside Aweil and Bor South, and the report says so.
