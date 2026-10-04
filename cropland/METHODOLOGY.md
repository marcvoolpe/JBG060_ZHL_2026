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

**Who:** all five group members. Each point is labelled by **2 people**, independently. Points are assigned in pairs so that every pair of people shares about 45 points, and each person labels about 180. The assignment is stored in the sample file.

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

**Disagreements:** points where the two labels differ on cropland vs not cropland, or one is unsure, are settled by a third person looking at both sets of answers. They are **kept** and flagged `disagreed = 1`, not dropped as in Kerner et al. Crop vs fallow differences don't count as disagreement for the main estimate, but they are reported. We report agreement as raw agreement and Cohen's kappa.

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

1. **Training data:** the calibration points only (≈150), with their adjudicated labels. Target: **cropped in 2025** (crop = 1; fallow and not crop = 0). Unsure points are left out of training. Fallow is left out of the map on purpose: in 2025 a fallow field looks like grass to the satellite, so a map can't find it reliably. Fallow enters the **cropland area** through the labelled sample only (section 7).
2. **Rule 1 (main):** a decision tree (scikit-learn `DecisionTreeClassifier`), using `class_weight="balanced"` and `min_samples_leaf=5`. The depth is chosen from **2, 3 or 4** by 5-fold cross-validation on the calibration points (F1), picking the smallest depth within 0.02 of the best. The tree is printed as if-then rules, saved as `rules_<date>.json` and then **frozen**.
3. **Benchmark (black box):** a random forest (500 trees) on the same features, and a random forest on Google's Satellite Embedding 2025. They show what readable rules cost in accuracy. They are never used for the map.
4. **Our map:** Rule 1 applied to every pixel in Earth Engine, on the box features: a pixel is crop when the 210 m box around it holds land **cropped in 2025**. Output is 10 m in the study areas and 30 m nationally (at 30 m the box is rounded to whole 30 m pixels).

The **same JSON file** is read by both the Python scoring and the Earth Engine map, so the map and the scores cannot drift apart. A test checks that both give identical labels at the calibration points.

## 7. Scoring

- **Test points only** (≈300) for map accuracy. The calibration points are never used to score anything.
- **Maps compared:**
  - Rule 1 and the two random forest benchmarks;
  - WorldCover 2021, GLAD 2019, Digital Earth Africa 2019, WorldCereal 2021, Esri 2025, Dynamic World 2025, GFSAD 2015, ASAP v04 (crop if the cell is 5% crop or more).

  **Map value at a point:** a map says crop when it calls **any** pixel of the point's 210 m box crop, the same presence rule as the labels. (Before, the map was read at the point's own pixel only.) This favours maps that call many scattered pixels crop, so each public map is also compared on **share**: its share of each test box against the labelled share (mean of each, with the stratum weights, and the mean absolute gap). ASAP cells (~1 km) are larger than the box and are read at the point. Each map's year is shown next to its score. Maps from before 2025 are expected to miss changes; that is a caveat, not a flaw in the test. The maps also define cropland differently: GLAD counts fallow up to 4 years, as we do, while WorldCover, WorldCereal and Dynamic World count only active crops. So each map is also scored against the cropped-only labels, and both scores are reported.
- **Estimators:** stratified estimators for strata that are not the map classes (Stehman 2014) give UA, PA, OA and F1, with standard errors. Maps whose 95% intervals overlap are **not ranked**.
- **Area:** from the adjudicated reference labels of **all** labelled points (calibration + test), for both definitions: **cropland** (crop + fallow, the main number) and **cropped in 2025** (crop only), each as **share of box** (main) and **box holds it** (upper bound). The estimate is Σ W_h ȳ_h per study area, with the stratified standard error (Olofsson et al. 2014; s²/n per stratum, which equals p(1-p)/(n-1) for 0/1 values), and a 95% interval of ±1.96 SE. Unsure points and points without a share are left out and their number is reported.
- **Sensitivity check:** the upper-bound estimate is repeated counting all disagreed points as crop and then all as not crop, to show how much disagreement moves the result.

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
- 1 Oct 2026: section 4b (regional differences) added. Labels now saved automatically by label_server.py into cropland/labels/, one file per labeller.
- 4 Oct 2026: **unit changed from the 10 m pixel to the outer yellow box, 210 m × 210 m**, before any sample point was labelled (group decision). Reason: at 10 m the labellers could not tell what covered a single pixel, so in practice we judged the whole outer box.
  - **Box size, checked.** The tool called the outer box "≈ 110 m", but it is **210 m**. Code (`04_image_strips.py`, first version): each month is a 51 × 51 pixel grid at 10 m, enlarged 3×; the outer box was drawn at screen pixels 44 and 108, i.e. ±10 ground pixels around the centre pixel. Measured on the labelled images (P01 2025, S001 2025, S200 2024): the yellow edges sit at rows 44 and 108 of each 153-pixel tile; inside are 63 screen pixels = 21 ground pixels × 10 m = 210 m, centred on the point (±105 m). The new tool draws the box in exactly the same place and drops the small centre-pixel square.
  - **Rule: presence.** A box is crop if any field in it was cropped in 2025, fallow if it has a field but none was cropped, not crop if there is no field (group decision). The key's first question becomes "is there open land anywhere in the box", and the cues are about the most field-like patch.
  - **Consequences.** The area estimate becomes "land whose 210 m box holds cropland", an **upper bound** on cropland area, reported under that name (section 2). Features are summarised over the box by its most crop-like part (section 5). Public maps say crop at a point when any pixel in the box is crop (section 7). The NDVI curve in the tool is the box median with a 10th-90th percentile band; the tool adds a radar curve, the Esri capture date, enlarged months and a "come back later" flag. Labels carry `unit = 210m`; 06_merge_labels.py warns about labels without it.
  - **Pilot** labels (10 m pixel) are kept as they are. No pilot point was called crop by all five; the four split points (P01, P12, P20, P24) are in the examples panel for a group discussion at box level. Yassin's pilot file had git conflict markers around two identical copies; one copy kept, labels unchanged.
  - 5 Oct 2026: **cropland share of the box added** (0 / <10 / 10-25 / 25-50 / >50%, `crop_share`), because the presence rule alone inflated the area 2.6-9× (section 2, checked on Esri and Dynamic World 2025). The share gives the main area estimate; presence stays the label, the map target and the upper bound. Public maps are also compared on box share. The high-resolution image's date is marked green when it shows the 2025 season (taken in 2025, or January-March 2026 just after the harvest: 336 of the 450 sample points) and orange otherwise. No two sample boxes overlap (section 3). 06, 09, 10 and estimators.py updated; `test_area_share` added.
  - 5 Oct 2026: the tool's greenness chart shows the box split into patches (section 4) instead of only the box median, because box and 500 m medians were nearly the same. Sample: 61 boxes stay one patch, 72 split in 2, 317 in 3 (Aweil mostly 3: scattered trees, grass, bare soil). Step 04 rerun; features unchanged.
  - Steps 04 and 05 rerun on 4 Oct 2026 for pilot (30) and sample (450), on Earth Engine project `southsudan-509222` (Yassin; same public data). The new images have the box at the same pixels as before (checked on P01). All 480 points got an Esri capture date. Radar: Aweil has no descending Sentinel-1 pass in January-April 2025 (Bor South has all months), so the tool's radar curve starts in May there; the radar features (June-September) miss only 4 points in June. `test_cropland.py --ee` passes: the Earth Engine map gives the same label as the Python rules on the new box features.
