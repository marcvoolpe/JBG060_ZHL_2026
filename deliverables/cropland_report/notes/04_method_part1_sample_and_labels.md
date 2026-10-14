# 4. Approach, part 1: from the maps to a labelled reference sample (report: "Approach", 5 points)

Long notes, 10 Oct 2026. Part 1 = everything up to the labelled reference set: agreement map, strata, allocation, draw, split, labelling (response design) and its quality. Part 2 (features, Rule 1, scoring, area, flood overlay) comes later. The binding rules are in `cropland/METHODOLOGY.md` (frozen before labelling, with a dated change log); this file explains and justifies them for the report.

---

## 4.1 Draft paragraphs (tight, for the report)

**One sample, two uses.** Public maps disagree too much to be trusted or averaged (file 01), so we measure cropland directly with a probability sample: random points that people label by eye, blind to every map. The same labelled points give (1) the cropland area of each study area with a 95% confidence interval that does not depend on any map (Olofsson et al. 2014) and (2) the accuracy of every map, scored on the same points (Stehman 2014). This follows Kerner et al. (2024) and Adebayo et al. (2026) and extends them to South Sudan.

**Where the points go.** Crop is rare (a few percent of the land), so plain random points would hit it only a handful of times. We stack the seven public maps on one 10 m grid, count for every pixel how many call it crop, and split each study area into three strata: A (no map says crop: 95.0% of Aweil, 90.6% of Bor South), B (1-2 maps: 4.7% and 9.4%) and C (3 or more: 0.3% of Aweil; in Bor South only 0.004%, merged into B). Kerner et al. recommend exactly this, "stratified sampling in which consensus levels define strata". It puts points where maps disagree, so every map is tested where it claims crop, and it trusts no single map. We drew 450 points (Aweil 150 / 90 / 90; Bor South 60 / 60), at least 100 m apart (Earth Engine, seed 42), and split each stratum one third calibration, two thirds test **before** anyone labelled.

**What a label means.** Each point stands for the 210 m x 210 m box around it. In the pilot (30 points in Twic county, five labellers) people were confident, but they could not tell what covered a single 10 m pixel and agreed poorly on crop (kappa 0.00-0.38). So the unit became the box (decided before the sample was labelled). A box is "crop" if any field in it was cropped in 2025, "fallow" if it holds a field not sown in 2025, otherwise "not crop"; the labeller also estimates how much of the box is cropland in five classes. The mean share over random boxes estimates the cropland share of the land; the share of boxes holding any cropland is reported as an upper bound.

**Who labels and how.** Two of the five group members label every point independently, blind to each other and to all maps. Pairs are balanced: every pair shares 45 points and every person gets the same mix of areas, strata and calibration / test points. A labelling tool shows 12 monthly Sentinel-2 images of 2025 (and of 2024, only to recognise fallow), greenness curves of the box's patches, a radar curve for the cloudy months and a dated sub-metre Esri image. A written key turns what people see (bare soil in April-May, green-up, harvest earlier than the surrounding grass, field shapes, cropped in 2024) into a label and a confidence. Disagreements are **kept**, not settled: the area uses the mean of the two labels, model fitting and scoring use the points both agree on. On all 450 points, the two labellers agree on cropland versus not at 85.6% of points (Cohen's kappa 0.70, "substantial"); where they split, it is mostly about whether a field is there at all (field shape seen by one and not the other at 41 of 53 split points).

(~470 words; the last paragraph can lose the tool details if needed.)

---

## 4.2 The steps, with inputs, outputs and parameters

| step | script | input | output | key parameters |
|---|---|---|---|---|
| E. EDA of the maps | `eda_public_maps.ipynb` (`eda_maps.py`, `eda_figures.py`) | 7 maps + ASAP, flood masks, CFSAM, FAOSTAT | tables and figures in `deliverables/` (file 01) | fine grid 1/11520 degree (~10 m), flood grid 1/480 degree |
| 0. Pilot points | `00_pilot_points.py` | Twic county (outside the study areas) | 30 points, KML, label template | seed 42 |
| 1. Pilot check | `01_compare_pilot.py` | 5 x 30 pilot labels | agreement, kappa, share confident | go if at least 70% of points get confident labels |
| 3. Strata and sample | `03_agreement_and_sample.py` | 7 public maps (Earth Engine), county boundaries | `strata_areas.csv`, `sample.csv` (id, area, stratum, lat, lon, split, labeller_1, labeller_2) | strata A = 0, B = 1-2, C = 3+ maps; merge a stratum under 0.1% of its area; 150 / 90 / 90 and 60 / 30 / 30 points; at least 100 m apart; 1/3 calibration; seed 42; 10 balanced pairs |
| 4. Image strips | `04_image_strips.py` | Sentinel-2 L2A + Cloud Score+ (cs_cdf >= 0.6), Sentinel-1 VH, Esri imagery metadata | monthly images 2025 and 2024, patch NDVI curves, radar curve, Esri capture date (`label_tool/`) | 510 m square, box 21 x 21 pixels; k-means 2-3 patches, kept if every patch >= 5% of the box and curves differ >= 0.08 NDVI |
| (tool) | `label_server.py`, `label_tool/index.html` | the above | `labels/sample_labels_<name>.csv` | key in `LABELLING_GUIDE.md`; one row per label with cues, confidence, share class, minutes |
| 6. Merge labels | `06_merge_labels.py` | both labels per point | `labels_final.csv`, `disagreements.csv`, `model_table.csv` | agreed / disagreed / crop-vs-fallow; mean of two labellers; share class middles 0, 5, 17.5, 37.5, 75% |
| (quality) | `eda_labels.py` (in the notebook) | labels only | agreement, kappa, specific agreement, effort | read-only, no features or maps |

How they connect: the maps only decide where points go (step 3); people decide what is there (tool); the labels then feed the area estimate, the accuracy of every map and the calibration of Rule 1 (part 2). Nothing a map says enters a label.

---

## 4.3 Design choices and why

### Why a sample, and why first

- **The maps cannot be the answer**: factor 9 disagreement in Aweil, overlap of the crop class at most 16%, no South Sudan validation (file 01).
- **Pixel counting is biased** even for good maps (Adebayo et al. 2026, Table 5: Zambia 8.99 Mha by pixel count, 6.31 ± 0.93 Mha from the sample). A probability sample gives an unbiased area with an error bar whatever the maps say.
- **One sample, two uses**: the same labels score every map and give the area, and later set the thresholds of Rule 1 (calibration points only).

### Why agreement strata (not one map, as Adebayo et al. do)

- Adebayo et al. stratify on one map at a time and pick the map that needs the fewest points. That needs a credible map to start from. In South Sudan we have no accuracy information for any map, and the maps disagree too much to pick one: stratifying on Dynamic World would put Bor South's B stratum on wetland grass (file 01, finding 1).
- Kerner et al. (2024) suggest strata by consensus level. Every map's crop pixels fall in B or C, so every map gets enough "map says crop" points to estimate its precision; points in A test what all maps miss (their recall).
- **The cost**: stratum A is 95% of Aweil, so a little crop in A carries a large area. With 150 / 90 / 90 points and crop shares of 1-5% in A, 91-99% of the variance of the area estimate comes from A, and the 95% interval is about ±1.6-3.4 percentage points (`sample_size_planning_aweil.csv`). This is Adebayo's rare-class finding seen from the other side: omission (fields no map sees) drives the uncertainty. We report it, and it sets the recommendation for next year's design (file 05).

### Why this allocation

- Equal allocation would serve map accuracy, proportional allocation the area. Olofsson et al. (2014) and Adebayo et al. (2026) use a compromise: more points in the rare strata than proportional, fewer than equal. 150 / 90 / 90 is that compromise for Aweil; Bor South gets 120 points because ZOA works there too, accepting a wider interval.

### Why the 210 m box, presence plus share

- Pilot (10 m pixel, 30 points, all five people): confident labels (87-100% per person), but crop calls varied from 0 to 8 of 30 per person and pairwise kappa was 0.00-0.38. In practice people judged the whole box. Making that the unit (4 Oct 2026, before any sample label) made the label match what people can see.
- Presence alone inflates area (any field in the box counts the whole box: 2.6-9 times the cropland share, checked on two 2025 maps), so labellers also give the share of the box (5 classes). The mean share over random boxes estimates the share of land (each pixel lies in as many boxes as any other); presence is kept as the upper bound and as the label for models and map scoring.
- Map values are read on the same box (crop if any pixel in the box is crop; and as a share), and features are summarised over the box, so labels, features and maps describe the same land.

### Why these images and cues

- NICFI Planet basemaps (Kerner's main source) ended in 2025, so we label from open imagery: Sentinel-2 monthly (timing), Sentinel-1 (through clouds), Esri sub-metre (field shapes, with capture date; 336 of 450 points have an image from the 2025 season).
- Cues follow the crop calendar of Northern Bahr el Ghazal (FEWS NET: sowing by late May, groundnut and sesame from August, sorghum September-October) and the local traps: wild grass greens up with the crops, so the strongest cue is **harvest earlier than the grass around the box**; burned grass looks like tilled soil; Bor South has flood-recession plots (under water August-October, green December-February), flagged in the tool for every Bor South point.

### Why keep disagreements

- Kerner et al. dropped every point where labellers disagreed. Those are the hard cases (field edges, fallow, crops in grass), so dropping them makes every map look better than it is. Adebayo et al. settled disagreements by consensus and did not measure interpreter variability.
- We keep both labels and report the disagreement. For the area, a split point counts half (mean of the two labels); for fitting and scoring, only points both agree on are used, and the number left out is reported. A sensitivity check counts split points first as all cropland, then as none.

### Guards against leakage and tuning

- Split before labelling; labellers blind to maps and to each other; points shown in random order mixing both areas (tiredness or learning does not line up with an area); methodology frozen before labelling, every change dated with its reason; Rule 1 frozen in a dated file before test points are touched; this EDA uses labels only for agreement statistics, never with features.

---

## 4.4 Quality of the reference labels (final, all 450 points, 12 Oct 2026)

From `label_agreement.csv`, `label_confusion.csv` and `label_disagreement_causes.csv` (notebook section 8; labels only, no features or maps). For comparison, the first 135 points (three labellers) had given 92.6% and kappa 0.85: the final numbers are lower, because pairs differ (below).

| group | points | agreement, cropland vs not | Cohen's kappa | positive agreement | negative agreement | points either called cropland |
|---|---|---|---|---|---|---|
| all | 450 | 85.6% | 0.70 | 0.84 | 0.90 | 200 |
| Aweil | 330 | 83.3% | 0.68 | 0.86 | 0.86 | 190 |
| Bor South | 120 | 91.7% | 0.14 | 0.18 | 0.96 | 10 |
| Aweil A (0 maps) | 150 | 91.3% | 0.58 | 0.65 | 0.96 | 22 |
| Aweil B (1-2 maps) | 90 | 71.1% | 0.32 | 0.84 | 0.52 | 78 |
| Aweil C (3+ maps) | 90 | 82.2% | -0.07 | 0.92 | 0.00 | 90 |
| Bor South A | 60 | 98.3% | 0.00 | 0.00 | 0.99 | 1 |
| Bor South B | 60 | 85.0% | 0.16 | 0.20 | 0.93 | 9 |
| calibration / test | 150 / 300 | 83.3% / 86.7% | 0.66 / 0.73 | 0.82 / 0.85 | 0.90 / 0.90 | 64 / 136 |

Both labels side by side (points): crop-crop 134, not crop-not crop 247, **crop vs not crop 50**, crop vs fallow 4, fallow vs not crop 3, unsure with something 12, fallow-fallow 0.

- **Overall: substantial agreement** (kappa 0.70; 0.61-0.80 is "substantial", Landis and Koch 1977). When one person calls a box cropland, the other does too 84% of the time.
- **Disagreement is about whether a field is there.** At the 53 points where the two split on cropland versus not, the field-shape answer differs at 41 (77%), the early-harvest answer at 23, bare soil and "cropped in 2024" at 15 each, green-up at 12; the cover class (open land vs trees) at only 6. So people agree on the land, and disagree on spotting a field in it: small, irregular plots on a 210 m box. We expected a sub-metre image from the 2025 season to settle this, but in Aweil splits were **more** common where such an image existed (53 of 287 points, 18%) than where it did not (2 of 43, 5%; checked 12 Oct). The likely reason: without a sharp in-season image both labellers fall back on "no field visible"; with one, small plots show up and become arguable. Location may also play a part (in-season images are not spread at random).
- **Aweil B is the hardest stratum** (71% agreement): boxes where one or two maps see crop are the borderline cases, sparse fields in grass. Exactly the land where the maps also disagree.
- **Kappa misleads when one class dominates** (Cicchetti and Feinstein 1990): in Aweil C almost every box is cropland for both (positive agreement 0.92) yet kappa is -0.07; in Bor South almost every box is "not crop" for both (negative agreement 0.96) yet kappa is 0.14. Report specific agreement next to kappa.
- **Bor South**: only 10 of 120 boxes were called cropland by anyone, and positive agreement is 0.18. Its area estimate will rest on very few cropland boxes (wide interval), and map scores there are indicative only.
- **Labellers differ**: kappa per pair from 0.49 to 1.00 (agreement 73-100%). Because every pair labelled the same mix of areas, strata and splits, a stricter or looser labeller weighs the same everywhere, so this widens the uncertainty but does not bias comparisons between strata or maps.
- **Fallow was almost never used**: 7 of 900 labels, and never by both labellers on the same point. In practice "cropland" (cropped or fallow) and "cropped in 2025" will give nearly the same numbers; the fallow distinction did not work as a separate class on these images. State it as a finding about the response design.
- **Unsure was rare**: 12 labels (2.7% of points had one).
- **Effort**: median 0.5-1.0 minutes per point per person, mean 0.9-2.4; 2.7-7.3 hours per person for 180 points; confidence 3 ("sure") on 42-78% of labels (`label_effort.csv`, minutes capped at the 98th percentile against breaks left running).

## 4.4b What we can do with the disagreements (ideas, 12 Oct 2026)

The protocol stays: no third person settles a split, the area counts a split as half, accuracy uses agreed points only (METHODOLOGY, change log 5 Oct). Everything below is reporting, a sensitivity check, or an extra check logged in the change log, never a replacement of the labels. Numbers from `model_table.csv`, the label files and `results/area.csv`.

**Where the 65 splits are:** Aweil A 13 of 150 (9%), **Aweil B 26 of 90 (29%)**, Aweil C 16 of 90 (18%), Bor South A 1 of 60, Bor South B 9 of 60 (15%). Labellers were less sure on split points (mean confidence 2.24 against 2.68).

Cheap, no new labels (recommended for the report):
1. **A human ceiling on the scorecard.** Two labellers agree on cropland with positive agreement 0.84, which is the F1 of one person scored against the other. Draw it as a line on the scorecard: Rule 1 reaches 0.72 and the best public map 0.55, against labels that themselves reach about 0.84. No map can be expected to score far above that.
2. **Label uncertainty next to sampling uncertainty.** Already computed: in Aweil, the "box holds cropland" share is 14.3%, and 10.3% to 18.3% if all 44 split points are counted as none or all as cropland (Bor South 1.5%, from 0.2% to 2.9%). Show this band beside the 95% interval (dashboard page 5, poster).
3. **Score the maps three ways**: agreed points only (main), splits counted as cropland, splits counted as not cropland. The splits sit in strata B and C, where the maps differ most, so this shows whether the ranking survives the hard cases. Kerner et al. dropped such points without checking.
4. **The models as a second opinion (not a tiebreak).** On the Aweil split points the frozen models give a mean crop probability of 0.82 (logistic) and 0.74 (random forest), against 0.93 / 0.90 on agreed crop and 0.18 / 0.07 on agreed not crop. To the satellite features, the disputed boxes look mostly like cropland: small or sparse fields. Leaving them out of accuracy therefore flatters maps that miss small fields. Use this in the Discussion.
5. **Labellers lean differently.** Crop rate per labeller ranges from 0.31 to 0.48; in their own splits one labeller said crop 89% of the time, another 18%. Because every labeller had the same mix of areas, strata and splits, this widens the uncertainty but does not bias area or map comparisons. Report it **anonymously** (labeller A-E). A latent-class model (Dawid and Skene 1979: each labeller's own sensitivity and specificity, estimated without a ground truth; our five labellers in balanced pairs suit it) gives each point a probability of cropland: a model-based alternative to "count half", as a sensitivity check only.
6. **What makes a box disputed.** Field shape (41 of 53 splits), stratum B, and, against our expectation, having a sharp in-season image (section 4.4). Cross also with the box share class and the distance to homesteads. This is Discussion and SLE material: the disputed land is small, irregular plots, which may belong to the poorest farmers.

Small extra work (needs a dated change-log line first):
7. **ZOA field check of the hard cases.** Ask ZOA staff in Aweil to visit or photograph 10-20 split boxes (ZOA said the points may be public). The only independent truth on exactly the disputed land; reported separately (README open point 5).
8. **Consensus look at a random subset** (e.g. 20 splits) by the group, recorded in a separate column, to test the "count half" rule: if consensus calls most of them cropland, half is too low. Never used for the main numbers.

For the reuse kit and the next season:
9. **Hard examples for training.** Put 10-15 split boxes with both answers in the tool's examples panel, and hold a short calibration session before labelling (REUSE.md step 6).
10. **Sharpen the field-shape cue** (cue d, behind 77% of splits): a clearer definition with example images of small irregular plots, or a "field shape: can't tell" option that is then reported.
11. **Show it to ZOA:** two or three split boxes on the dashboard ("two careful people disagree here") make the uncertainty concrete.

---

## 4.5 How the sample is used next (preview of part 2)

- **Area**: share = sum over strata of W_h x (mean of the labels in stratum h); SE from the within-stratum variance (Olofsson et al. 2014); 95% CI = ±1.96 SE; per area, for cropland and for cropped in 2025, as share of box (main) and box holds it (upper bound). `estimators.area`.
- **Accuracy of every map**: user's and producer's accuracy, overall accuracy and F1 with standard errors from the Stehman (2014) ratio estimators, because the strata are not the map classes. `estimators.accuracy`. Maps whose 95% intervals overlap are not ranked.
- **Same metrics as both papers, so the numbers sit side by side.** Kerner et al. (2024) and Adebayo et al. (2026) report exactly these four metrics with standard errors for six of our seven strata maps and ASAP (`cropland/reference_accuracy_literature.csv`, file 02). Planned table for the results: per map, our precision, recall and F1 in Aweil and in Bor South next to the published range. It answers a question ZOA and ZHL cannot answer today: **do published accuracies transfer to South Sudan?** The EDA already suggests "partly": published recall predicts which maps show the least crop in Aweil (rank correlation +0.89), not what happens in Bor South (-0.39). Overall accuracy is reported but never used to rank maps: in Kerner's Mali, Esri had 0.97 accuracy with F1 = 0.
- **Relative efficiency (planned, our extension of Adebayo et al.)**: once the test labels are in, compute for each map the sample size it would need as a two-stratum design (from its own precision and recall, `efficiency.one_map_strata` and `efficiency.n_opt`), and compare it with our agreement design (crop share per stratum from the labels). This answers "which strata should ZOA use next year, and how many points" with South Sudan data. Checked against Adebayo et al. Table 4 (Kenya, GLAD: 591 points from our code against 616 in the paper, which used its own sample estimates).

---

## 4.6 Assumptions, limits, and how far it generalises

| assumption or limit | effect | how the approach handles it |
|---|---|---|
| labels from imagery, no field visits | small or shifting fields can be missed; recession plots confused with wetland | two blind labellers, confidence and share recorded, disagreement reported; ask ZOA for field points as an independent check |
| imagery dates | 114 of 450 points have no sub-metre image from 2025 | flagged in the tool ("field shapes only"); Sentinel-2 timing cues carry the label |
| clouds June-September | gaps in the optical series | monthly composites; Sentinel-1 radar curve; key cues sit in clearer months (bare soil April-May, harvest September-November) |
| 210 m box vs map pixel | a coarse unit for 10 m maps | maps read on the same box (presence and share), so the comparison is like for like |
| definitions differ (fallow) | maps without fallow look worse on "cropland" | each map also scored on "cropped in 2025" |
| one season, two areas | results do not transfer automatically | pipeline reruns for any year and area (config); every new year or area needs its own check sample (~150 points) |
| stratum A dominates the variance | wide intervals | reported; points needed for a target precision given (`efficiency.py`); next-year design can add a split of A |

Generalisation: the method (agreement strata, blind double labelling, design-based estimates) is the one Kerner et al. and Adebayo et al. use across 13 countries, so it transfers; the numbers do not. The scripts take a year and an area and rebuild strata, sample, images and features, so a new season or another ZOA area costs one Earth Engine run and a few labelling days.

---

## 4.7 What goes beyond the state of the art

1. **First reference sample and accuracy check of cropland maps in South Sudan** (absent from Kerner et al. 2024 and Adebayo et al. 2026).
2. **Multi-map agreement strata, compared with single-map strata** through Adebayo's relative efficiency, on the same labels (planned; 4.5).
3. **Labeller disagreement kept and measured**, with kappa and specific agreement per pair, area and stratum, where both earlier studies dropped or settled it.
4. **Open imagery only** (Sentinel-1/2, Esri), so the labels can be repeated after NICFI's end, which Adebayo et al. name as a need.
5. **A recent season (2025)** and the yearly products of that year, where both studies used 2019.
6. **From accuracy to a decision**: the plan was that the same sample gives flooded cropland with a confidence interval, so the trigger quantity ZOA would use gets an error bar (file 05). In 2025 too few points fell on flooded land for that (1 in Aweil, 2 in Bor South; notes 07, R5); a stratum on flood-prone land would make it work.
7. **A test of whether published accuracy transfers**: the same maps, the same metrics, a new country, set against the 14 countries of the two papers.
