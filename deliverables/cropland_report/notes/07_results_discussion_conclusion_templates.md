# 7. Templates: Results, Discussion, Conclusion

11 Oct 2026. Prepared before the results exist, so the write-up is quick and the interpretation is not bent to fit the outcome: for each result there is a table layout, a sentence template with `[placeholders]`, and pre-written branches for the likely outcomes. Rubric points: Results 3, Discussion 4, Conclusion 3 (about 300 + 200 + 150 words). In `report.tex` these sections hold the placeholders; the long versions are here.

**Rules for every result sentence:** a number with its interval or standard error; the comparison it supports; one clause of meaning for ZOA. Negative results are written as plainly as positive ones (rubric: "including negative results").

## 7.0 Results in so far (12 Oct 2026, steps 09, 11, 12; flood overlay still running)

Tables in `cropland/results/`. Accuracy on test points both labellers agree on, stratified estimators. "±" is one standard error; 95% intervals are ± 1.96 SE.

**R2. Cropland area 2025** (`area_adjusted.csv`, share of box, all 450 points):

| area | share of land | hectares | 95% interval (ha) | adjusted upper bound (ha) | public maps, pixel count |
|---|---|---|---|---|---|
| Aweil counties | 3.8% | 116,500 | 76,700-156,400 | 183,100 | 0.2-1.9% of the land, i.e. 6-51% of the sample figure, all under |
| Bor South | 0.4% | 5,400 | 1,000-9,700 | 16,500 | 0.0-9.0% (Dynamic World 2025: 23 times the sample; GLAD and GFSAD inside the interval) |

"Box holds cropland" (upper bound): Aweil 14.3% (10.3-18.3% if all splits are none / all cropland), Bor South 1.5%. "Cropped in 2025" is within 0.1 percentage point of "cropland" (fallow 7 of 900 labels).

**R3. Map accuracy, Aweil** (`accuracy.csv`, 186 test points; cropland; F1 ± SE): Dynamic World 2025 0.03 ± 0.02, Esri 2025 0.06 ± 0.03, GFSAD 0.26 ± 0.06, WorldCover 0.36 ± 0.11, GLAD 0.41 ± 0.11, ASAP 0.43 ± 0.11, Digital Earth Africa 0.50 ± 0.09, WorldCereal 0.55 ± 0.11, **Rule 1 0.72 ± 0.09** (precision 0.70, recall 0.75), logistic (18 features) 0.66 ± 0.09, logistic (Rule 1's 2 inputs) 0.61 ± 0.09, random forest 0.76 ± 0.09 (features) and 0.71 ± 0.09 (embedding). Precision of Esri, WorldCover, GLAD and ASAP is 1.00 with recall 0.03-0.28: **they are right when they say crop, but miss most fields**. Dynamic World has both low precision (0.10) and low recall (0.02). Rule 1's 95% interval (0.55-0.90) overlaps those of WorldCereal, Digital Earth Africa, ASAP, GLAD and WorldCover, so by our rule it is not ranked above them; it is clearly above Esri, Dynamic World and GFSAD. Against the papers (`published_vs_ours.csv`): WorldCover, GLAD, GFSAD and Dynamic World recall fall below the range Kerner et al. and Adebayo et al. found anywhere in Africa.

**Bor South:** no agreed crop point among the 80 test points, so recall and F1 cannot be computed. False crop: Dynamic World calls crop in 44 of 74 boxes the labellers saw no field in (overall accuracy 0.70); Rule 1 and the logistic models in 1; all other maps in 0 or 1.

**R4. Where maps fail** (`error_analysis.csv`, unweighted counts, Aweil test): Rule 1's 5 false-crop boxes are all within 250 m of a building (5 of 15 such boxes); its missed crop is mostly far from buildings (3 of 4 boxes over 250 m). Rule 1 is in effect a "fields around homesteads" rule. The logistic models make more false crop in stratum A (9-12 of 122 against 5), which costs them precision where most of the land is.

**R5. Flooded cropland 2025** (`flooded_cropland.csv`, `flooded_cropland_bounds.csv`, `trigger_agreement.csv`; added 14 Oct):

| area | flooded land (June-Dec 2025) | public maps | our map (box holds crop) | sample |
|---|---|---|---|---|
| Aweil counties | 10,314 ha (0.3% of the area) | 10 (Esri 2025) to 307 ha (Digital Earth Africa); ASAP 77 | 3,588 ha | 606 ha, but from **1** point in a flood cell: cannot tell |
| Bor South | 29,419 ha (2.1%) | 0-10 ha, except Dynamic World 1,606 ha | 126 ha | 0 ha from **2** points in flood cells, neither with cropland: cannot tell |

- **The maps disagree by a factor of 30 in Aweil** (10 to 307 ha among the public maps). In Bor South Dynamic World alone puts 1,606 ha of cropland under water, where every other map sees almost none: the same wetland it calls crop at 44 of 74 empty test boxes. So "the map decides the trigger" (notes 01, finding 5) holds for 2025 too.
- **The sample cannot say which map is right about the flooded part.** A random sample over the whole area puts almost no points on the 0.3-2.1% of land that floods. The usual interval (Bor South "0 to 0 ha") would look precise without being so; with the cautious upper bound, capped at the flooded land, the sample says "cannot tell" at every trigger threshold from 100 to 5,000 ha. This is a negative result to report plainly.
- **What we can still say:** which maps are accurate on cropland in general (R3), and that Dynamic World's flooded cropland in Bor South comes from a class that is wrong on dry test boxes. **Next time:** a stratum on flood-prone land (e.g. the recurring flood mask) with its own points, so flooded cropland gets its own estimate (Discussion; REUSE).
- Our map's 3,588 ha in Aweil counts land whose 210 m box holds crop near a flood cell, so it is an upper bound; it is not comparable with the public maps' pixel counts.

**R6. Sampling design** (`design_efficiency.csv`, points for a 20% CV of the area): agreement strata 124 points in Aweil; one-map strata 112 (WorldCereal) to 149 (Dynamic World): **our design is not clearly more efficient than stratifying on the best single map**, but it never depends on picking that map beforehand. Bor South needs about 1,240 points for 20% CV under any design: cropland is too rare there for a sample of 120.

**Models, "logistic regression or trees"** (`model_cv.csv`, 12 Oct): chosen without test labels. In cross-validation on the 125 calibration points, logistic regression (F1 0.87-0.88) and trees (0.85-0.86) were close, and the random forest was higher (0.92). On the test points the order changed (tree 0.72, logistic 0.61-0.66). All intervals overlap. Conclusion for the report: with 41 crop calibration points, the model family matters less than the inputs (distance to buildings is the strongest input of the tree and of the logistic models). The readable tree is as good as the alternatives we tried.

---

## 7.1 Results

### R1. Label quality (inputs: `label_agreement.csv`, `label_disagreement_causes.csv`; already written into `report.tex` with the final numbers)

Template: "The two labellers agreed on cropland versus not at [x]% of the [n] points (Cohen's kappa [k]); in Aweil [x_aw]% (kappa [k_aw]), in Bor South [x_bs]% (positive agreement [pa_bs]). Most disagreements concerned [cause 1] and [cause 2]."

| outcome | branch |
|---|---|
| kappa >= 0.8 in both areas | "Agreement was almost perfect (Landis and Koch 1977), so the reference is reliable enough to score maps whose recall differs by more than about [x] points." |
| kappa 0.6-0.8 | "Agreement was substantial; the [n_d] disagreed points (counted half in the area, left out of the scores) mark where any map will struggle." |
| Bor South positive agreement low (likely) | "In Bor South the labellers rarely agreed on cropland ([n] of [m] cropland calls confirmed): fields there are few and hard to tell from wetland grass, so its area has a wide interval and its scores are indicative only." |

### R2. Cropland area (inputs: `results/area.csv` + `evaluation.area_interval`)

Table (in `report.tex`, Table "area"): rows cropland / cropped in 2025 / upper bound; columns Aweil and Bor South, share of land and hectares, with the usual interval and the adjusted upper bound; last row CFSAM (modelled).

Template: "Cropland covered [p]% of the Aweil counties in 2025 ([lo]-[hi]%, adjusted upper bound [hi_adj]%), or [ha] ha; cropped land [p_c]%. In Bor South: [p_bs]% ([lo]-[hi_adj]%)."

| outcome | branch |
|---|---|
| sample estimate above every map (expected: maps under-count) | "Every public map shows less cropland than the sample: from [a]% (Dynamic World) to [b]% (GFSAD) of the estimate. Pixel counting with any of them would under-state the crop at risk." |
| sample between the maps | "The estimate lies between the maps: [maps] over-state, [maps] under-state; no map is right by default." |
| sample close to CFSAM | "Our estimate is close to CFSAM's modelled cereal area ([x]%), which supports CFSAM's order of magnitude, from independent data." |
| sample far below CFSAM | "CFSAM's modelled area is [x] times our estimate; its population-based model may over-state cropland in [area] (its Aweil area fell by a third between 2022 and 2025 through a population revision)." |
| interval wide (likely in Bor South) | "With [n] points, the interval spans [lo]-[hi_adj]%: enough to tell [1%] from [5%], not enough for a hectare-precise trigger." |

### R3. Map accuracy (inputs: `results/accuracy.csv`; figure "scorecard"; `evaluation.published_vs_ours`)

Figure to make: for each area, precision (x) and recall (y) per map with 95% error bars, or a dot plot of recall with intervals (recall is the number ZOA's trigger needs). One colour per area (two series), maps on the axis.

Template: "On the [n_test] test points in Aweil, recall ranged from [r_min] ([map]) to [r_max] ([map]) and precision from [p_min] to [p_max]; [map] and [map] cannot be told apart (overlapping intervals)."

| outcome | branch |
|---|---|
| one map clearly best on recall | "[Map] finds the most cropland ([r] ± [se]); for a trigger that must not miss farmers, it is the public map to use in [area]." |
| no map separable | "No map is significantly better than the others in [area]; with [n] test points the differences that matter for ZOA (factor [x] in flooded cropland) come from where the maps put crop, not from small score differences." |
| Rule 1 beats the best public map | "Rule 1 reaches F1 [f] against [f_best] for [map] (intervals [overlap / do not overlap]), with [k] readable rules on [m] features." |
| Rule 1 ties | "Rule 1 performs like the best public map (F1 [f] vs [f_best]) while every rule can be read and checked." |
| Rule 1 loses | "Rule 1 does not reach the best public map (F1 [f] vs [f_best]): [k] rules from about [n_cal] calibration points do not capture [what the error analysis shows]. Readability costs [F1 gap] against our random forest." |
| ours vs published | "In Aweil, [maps] score within their published range, [maps] below it: published accuracy [does / does not] transfer to South Sudan." |

### R4. Where maps fail (inputs: `evaluation.error_analysis`; image strips of 5 false-crop and 5 missed-crop points per map)

Template: "False crop concentrates on [open land without crop cues / wetland / trees] ([x] of [n] false-crop points for [map]); missed crop on [small fields / boxes within 250 m of homesteads / fallow] ([x] of [n])."

Expected patterns to confirm or reject: Dynamic World false crop on wetland grass in Bor South; Esri and Dynamic World missing small fields near homesteads; GLAD and GFSAD counting fallow as crop (fine for "cropland", not for "cropped").

### R5. Flooded cropland and the trigger (inputs: `results/flooded_cropland.csv`; `evaluation.trigger_agreement`)

Template: "In 2025, [ha] ha of cropland flooded in Bor South according to the sample ([lo]-[hi] ha), against [0]-[1,600] ha by map. At a threshold of [T] ha the sample says [fire / no fire / cannot tell]; [k] of [m] maps agree."

| outcome | branch |
|---|---|
| sample decisive, maps split | "Whether the trigger fires depends on the map: [maps] agree with the sample, [maps] do not." |
| sample "cannot tell" over a wide band | "For thresholds between [a] and [b] ha the sample cannot tell; a trigger set inside that band is a coin flip with any map, so thresholds need a margin or a larger sample." |
| Aweil 2025 hardly flooded | "In Aweil 2025 floods touched little cropland under any definition ([range]); the case shows the method, not a trigger event." |

### R6. Sampling design (inputs: `evaluation.design_efficiency`; `sample_size_planning_aweil.csv`)

Template: "For a 20% coefficient of variation, our agreement strata need [n_ours] points against [n_best] with [map]'s strata ([relative efficiency])."

| outcome | branch |
|---|---|
| ours most efficient | "Stratifying on map agreement needs the fewest points; a yearly check of about [n] points (about [h] hours for two labellers) keeps the precision." |
| a single map more efficient | "[Map] alone would have needed [x]% fewer points, in line with Adebayo et al. (2026): its high recall leaves little crop hidden in the 'not crop' stratum. Next year, stratify on [map]." |

---

## 7.2 Discussion (about 200 words; rubric 4 points)

Order: what the results mean -> why (quantitative linked to qualitative) -> strengths and weaknesses of the method and the evaluation -> how assumptions shaped the outcome -> to what extent the objective is met -> impacts or, where it failed, why and how to improve.

1. **Meaning.** "[One sentence: how much cropland, and which map is closest where.] For ZOA this means [use map X / do not use map Y / use the sample-based figure] when [action]."
2. **Why (link numbers to what the labellers saw).** "The maps disagree most [along the river / in Bor South] because [wetland grass greens up with the crops; small fields near homesteads; fallow], which the error analysis shows as [pattern]."
3. **Strengths.** Probability sample, unbiased whatever the maps' quality; blind double labelling with every disagreement kept; rules frozen before test; interval checked by simulation; same metrics as the reference studies.
4. **Weaknesses and their direction.**
   - imagery labels (likely miss small fields under trees: the area is more likely too low than too high);
   - few crop test points (wide intervals, many maps unrankable);
   - 210 m presence unit (favours scattered maps; checked with the share comparison);
   - map years 2015-2025 (older maps disadvantaged, shown with each score);
   - one season, two areas (no claim elsewhere).
5. **Assumptions.** Fallow counted as cropland changes [map ranking] by [x] (compare the two definitions); the adjusted interval is conservative in Aweil, so the true uncertainty lies between the usual and the adjusted bound.
6. **Objective met?** "The area estimate and the map scores are delivered [with intervals]; Rule 1 [does / does not] beat the public maps; the trigger analysis shows [that and how much] the map choice matters."
7. **Impacts.** Positive: fewer silent misses, triggers with a stated uncertainty, a check ZOA can repeat. Negative: false precision outside the two areas, a sample gives area not location, field maps can be sensitive in a conflict setting (file 05, 5.9).
8. **If parts failed** (e.g. Rule 1 loses, Bor South unlabelable): reasons + concrete fixes (more calibration points in rare strata; radar-based cues for recession plots; ask ZOA for field points; split stratum A with our map next year).

---

## 7.3 Conclusion (about 150 words; rubric 3 points)

Answer first, then recommendations, each with its evidence in a clause.

- "**Answer.** In 2025 cropland covered [p]% of ZOA's Aweil counties ([interval]) and [p]% of Bor South; the public maps capture [x-y]% of it, and the choice of map changes flooded cropland by a factor [f]."
- "**Recommendations to ZOA:**"
  1. "Use [map] (or our rule-based map) in [area], and never choose a map by its overall accuracy, which rewards finding nothing where crop is rare [R3; Kerner et al.]."
  2. "Set a flooded-cropland trigger on the sample-based estimate with its interval, and keep thresholds outside the band where the sample cannot tell [R5]."
  3. "Repeat a check of about [n] points each season, about [h] hours for two staff; maps change from year to year [EDA, finding 4; R6]."
  4. "Ask partners for field points or photos to check the imagery labels [limitation]."
- "**Recommendations to ZHL (research):** add crop stage and flood duration to turn exposure into damage; extend the check to [other areas]; test whether accuracy transfers [R3 ours vs published]."

---

## 7.4 Sentence bank (already true, from the EDA)

- "Seven public maps call between 0.22% and 1.92% of the Aweil counties crop."
- "Where two maps call crop, it is mostly different land: the best pair shares 16% of its crop area."
- "All seven maps agree on about half a hectare of the 3.09 million hectares of the Aweil counties."
- "For the 2022 flood, the same overlay gives 432 or 5,805 ha of flooded cropland in Aweil, depending only on the cropland map."
- "In Mali, the Esri map reaches 0.97 accuracy with an F1 of 0: it calls nothing crop."
- "The usual 95% interval would hold the true area only 47-94% of the time in our design."

(In LaTeX use the macros from `numbers.tex`, not these typed numbers.)
