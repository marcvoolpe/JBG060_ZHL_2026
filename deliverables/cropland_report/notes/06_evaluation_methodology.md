# 6. Evaluation methodology (report: "Evaluation Methodology", 3 points)

Long notes, 11 Oct 2026. The rubric asks: which methods and measures (quantitative and qualitative) assess the quality of the approach, why they fit the criteria for a suitable solution (file 03, 3.4), and why they are adequate for this approach. Code: `cropland/09_score.py` and `10_flood.py` (planned scoring, already written) and `cropland/evaluation.py` (additions, tested in `cropland/test_evaluation.py` on made-up data).

> Additions to the frozen METHODOLOGY.md are marked **(addition)**. They change nothing in its sections 1-8, but they must be logged before anyone looks at the test labels: ready-to-paste change-log line in 6.7.

---

## 6.1 Draft paragraphs (tight, for the report)

**What is evaluated.** Our approach has four parts, and each is judged on its own terms: the reference labels (are they reliable?), the area estimate (is it unbiased, and is its interval honest?), the cropland maps, public and our own (how much real crop do they find, and how much of what they call crop is crop?), and the use of all this for ZOA (would a flooded-cropland trigger make the right call?).

**Quantitative measures.** Label quality: raw agreement and Cohen's kappa between the two blind labellers, with positive and negative specific agreement because crop is rare. Area: the stratified estimate with its standard error and a 95% interval (Olofsson et al. 2014). Maps: precision (user's accuracy), recall (producer's accuracy) and F1 with standard errors from the Stehman (2014) estimators, on the 300 test points only, per study area and for two definitions (cropland, cropped in 2025); maps whose intervals overlap are not ranked. Decision use: for flood-trigger thresholds, whether each map's flooded cropland gives the same decision as the sample's interval.

**Why these measures.** Overall accuracy is reported but never used to rank: where crop is rare it rewards a map that finds nothing (Esri in Mali: 0.97 accuracy, F1 0; Kerner et al. 2024). Recall and precision map onto the two costs ZOA named: a missed field is a household without assistance, a false field spends resources where they are not needed (Q&A 2, slide 10). Every number carries an interval because ZOA asked "how certain are you?" (slides 9, 23). Using the same metrics as Kerner et al. (2024) and Adebayo et al. (2026) puts South Sudan next to their 14 countries.

**Is the evaluation itself sound?** We simulated our exact design before looking at results. The estimator is unbiased, but the usual ±1.96 SE interval contains the true area only 47-94% of the time, because the stratum where no map sees crop (95% of Aweil) often holds no cropland point at all. We therefore report an adjusted interval whose upper bound allows for the crop the sample may have missed; it reaches 94-100% in Aweil and 88-100% in Bor South in the same simulation. **Qualitatively**, we look at where each map fails, using what the labellers recorded at each point (cover class, crop cues, distance to homesteads, fallow), and inspect the images of the worst errors.

(~390 words; the third paragraph can shrink to one sentence if the evaluation section must stay near 200.)

---

## 6.2 Criteria for a suitable solution -> how we measure them

| criterion (file 03, from Q&A 2) | measure | where |
|---|---|---|
| Honest uncertainty: "how certain are you?" (slides 9, 23, 31) | 95% intervals on the area; standard errors on every map score; simulated coverage of the interval | `09_score.py`, `evaluation.area_interval`, `evaluation.simulate_interval_coverage` |
| Both error types matter: misses and false alarms (slides 10, 11) | recall (missed crop) and precision (false crop) reported separately, never only accuracy | `estimators.accuracy` |
| Relevant for the decision ZOA would take (slides 17, 23, 31) | trigger decisions per map against the sample, at several thresholds | `10_flood.py`, `evaluation.trigger_agreement` |
| Transparent, interpretable (slides 19, 40) | readability of Rule 1 (rules, conditions, features); cost of readability = F1 of the black-box benchmark minus F1 of Rule 1 | `evaluation.rule_complexity`, `09_score.py` |
| Local relevance (slides 3, 21) | every score per study area; Lol strip; error analysis by local land cover | `09_score.py`, `evaluation.error_analysis` |
| Cheap to repeat, runnable locally (slide 24) | points needed for a target precision per design; labelling time per point | `evaluation.design_efficiency`, `eda_labels.effort` |
| Fair: whose farmland is seen (slides 6, 7) | recall per map = share of real cropland, and so of farmers, a map can see; errors by homestead distance and field size | `estimators.accuracy`, `evaluation.error_analysis` |
| Rigour (slides 5, 29) | probability sample, split before labelling, rules frozen before test, test points used once | METHODOLOGY.md sections 3-7 |

---

## 6.3 What is evaluated, and how

### A. The reference labels (are they a usable "truth"?)

- **Quantitative:** raw agreement, Cohen's kappa, positive and negative specific agreement (Cicchetti and Feinstein 1990), overall, per area, per stratum, per pair of labellers (`eda_labels.py`; final on 450 points: 85.6% agreement, kappa 0.70; Aweil kappa 0.68; Bor South kappa 0.14, positive agreement 0.18 on the 10 boxes anyone called cropland; per pair kappa 0.49-1.00). Share of "unsure", confidence, minutes per point. Pilot (10 m pixel): kappa 0.00-0.38, which led to the 210 m box.
- **Qualitative:** every disagreement is listed with both labellers' answers (`disagreements.csv`), and the answers that differ are counted (`eda_labels.disagreement_causes`): at 41 of the 53 split points one labeller saw field shapes and the other did not; the cover class differed at only 6. Reading those points then names the cause (field edge, fallow vs grass, recession plot, burnt land, old high-resolution image). That turns "they disagree" into "they disagree about X", which is what a reader can act on.
- **Why:** if the truth is unreliable, every map score inherits it. Kappa alone misleads when one class is rare (Aweil stratum C: kappa -0.02 while positive agreement is 0.98), so specific agreement goes next to it.
- **How used:** disagreed points count half in the area (mean of the two labels), are left out of fitting and scoring (their number is reported), and the sensitivity check counts them all one way and then the other.

### B. The area estimate (unbiased, with an honest interval?)

- **Quantitative:** stratified estimate per area with SE, coefficient of variation and 95% interval (Olofsson et al. 2014), for cropland and cropped-in-2025, as share of box (main) and box holds cropland (upper bound). Sensitivity: split points all cropland / all not.
- **(addition) Interval check by simulation** (6.5): coverage of the usual and the adjusted interval under our exact strata and allocation. Result: report the adjusted interval.
- **Context, not validation:** CFSAM's modelled cereal area and the maps' pixel-counted areas are set next to the estimate (**(addition)** `evaluation.pixel_count_bias`: ratio of each map's area to ours, and whether it falls inside our interval). Neither CFSAM nor any map is a reference.

### C. The maps, public and our own (how much real crop do they find?)

- **Quantitative:** precision, recall, F1 and overall accuracy with SE (Stehman 2014, because strata are agreement levels, not map classes), test points only, agreed labels only, per area and definition (`09_score.py`). A map says crop at a point if it calls any pixel of the 210 m box crop, the same presence rule as the labels; to check that this does not favour scattered maps, each map's share of the box is compared with the labelled share (mean and mean absolute gap).
- **Ranking rule (pre-registered):** two maps whose 95% intervals overlap are not ranked.
- **(addition) Ours against the papers** (`evaluation.published_vs_ours`): our precision, recall and F1 per map next to the published mean and range of the same product. Answers "do published accuracies transfer to South Sudan?"
- **Rule 1 specifically:** depth chosen by 5-fold cross-validation on the calibration points; frozen before the test; then scored exactly like the public maps. **Cost of readability** = F1 of the random-forest benchmark minus F1 of Rule 1 (with bootstrap SE). **(addition) Readability** (`evaluation.rule_complexity`): number of rules, conditions in the longest rule, features used. National map: area per state against CFSAM as a plausibility check only, labelled "not checked" outside the two areas.

### D. Use for ZOA (would a trigger make the right call?)

- **Quantitative:** flooded cropland 2025 per map and from the sample with an interval (`10_flood.py`). **(addition)** `evaluation.trigger_agreement`: for thresholds (e.g. 100 / 500 / 1,000 / 5,000 ha per area) the sample says "fire" (lower bound above the threshold), "no fire" (upper bound below) or "cannot tell"; each map's call is compared where the sample is decisive. Report the share of thresholds where each map agrees, and how wide the "cannot tell" band is: that band is the honest uncertainty a trigger has to live with.
- **(addition) Sampling design** (`evaluation.design_efficiency`): points needed for a target precision with our agreement strata against one-map strata, from our own labels (Adebayo et al. 2026's relative efficiency). Answers how much a yearly check would cost ZOA, and which strata to use next year.

### E. Qualitative evaluation (where and why maps fail)

- **(addition) Error analysis** (`evaluation.labeller_context` + `evaluation.error_analysis`): false crop and missed crop of every map, broken down by what the labellers recorded: cover class (water / buildings / trees / open land), "open land with no crop cue" (grass), field shape seen, fallow, share of the box (< 10% = small fields), distance to homesteads, stratum and area. Counts are unweighted: they show where errors happen, not how much area they cover.
- **Visual inspection:** for each map, the image strips of 5 false-crop and 5 missed-crop test points, picked at random, described in one line each (what the map confused). This is what turns scores into the "nuanced" story ZOA asked for (slide 9).
- **Stakeholder check:** at the poster session (ZOA and ZHL present), ask whether the scorecard and the flooded-cropland numbers with intervals answer "what, where, how certain" (slide 23). Record the answers as qualitative evaluation.

---

## 6.4 Why this evaluation is adequate for this approach

1. **Design-based inference fits a probability sample.** Every pixel had a known chance of selection, so area and accuracy are unbiased whatever the maps' quality (Stehman and Foody 2019; Olofsson et al. 2014). No assumption about the maps is needed, which matters where no map has been validated.
2. **No leakage.** Calibration and test points were split before labelling; Rule 1 is frozen in a dated file before test labels are read; maps never saw our points. The test score is therefore an honest out-of-sample score for Rule 1 and an independent one for the public maps.
3. **Same metrics, same estimators as the reference studies.** Our scores are directly comparable with Kerner et al. (2024) and Adebayo et al. (2026); differences reflect the place and the maps, not the method.
4. **Measures follow the decision.** Recall and precision are the two error costs ZOA described; the trigger-agreement check evaluates the use, not only the map.
5. **The evaluation evaluates itself.** The interval was checked by simulation, the labels by double blind labelling, and the code by tests on made-up data with known answers (`test_cropland.py`, `test_evaluation.py`).

---

## 6.5 The interval check by simulation (addition)

Our exact design (Aweil: weights 94.97 / 4.71 / 0.32%, points 150 / 90 / 90; Bor South: 90.56 / 9.44%, 60 / 60), crop rates assumed per stratum (rate in stratum A 0.5-10%, B 2-40%, C 60%), share of a cropland box drawn from the four classes (smaller fields in A), 20,000 samples per case (`evaluation.simulate_interval_coverage`; table in the notebook, section 9b, and `interval_coverage_simulation.csv`).

| | usual ±1.96 SE: how often it holds the truth | adjusted interval | extra width (upper side only) |
|---|---|---|---|
| Aweil, box holds cropland | 69-94% | 94-100% | +0.1 to +0.7 points |
| Aweil, share of box (main) | 79-89% | 99-100% | +0.4 to +0.8 points |
| Bor South, box holds cropland | 47-89% | 95-100% | +0.7 to +2.2 points |
| Bor South, share of box | 57-81% | 88-100% | +0.4 to +1.2 points |

- The estimator is unbiased (bias below 0.02 points in every case). Only the interval is the problem.
- Every miss of the usual interval lies **below** the truth: when no cropland box falls in stratum A (22-47% of samples for a crop rate of 0.5-1% there), that stratum adds nothing to the estimate or its error, although 95% of the land is in it.
- **Adjusted interval** (`evaluation.area_interval`): same estimate and lower bound; the upper bound uses, per stratum, at least the variance it would have with one more cropland and one more empty box, with the cropland shares of the whole area. It is conservative in Aweil and close to 95% in Bor South except when stratum B has almost no crop (88-96%).
- Report both: "the usual interval is X-Y; allowing for crop the sample may have missed, the upper bound is Z". That is the honest statement for ZOA.

---

## 6.6 Limits of the evaluation (for the Discussion)

- **Labels are not ground truth.** Two people agreeing on imagery can share the same blind spot (small fields under trees, recession plots). Field points from ZOA would be the only independent check.
- **Few crop test points.** With ~300 test points, the crop points per area and definition are few (tens), so precision and recall have wide errors; many maps will not be rankable. That is a finding, not a failure.
- **The 210 m presence unit** is coarser than 10 m maps; the share comparison guards against favouring maps that scatter crop pixels.
- **Map years and versions differ** (2015-2025); the scorecard shows each map's year.
- **Flood masks are taken as given**; trigger agreement evaluates the cropland term only.
- **The simulation assumes** crop rates and a share mix; the coverage numbers depend on them (we covered a wide range).

---

## 6.7 Ready-to-paste change-log line for METHODOLOGY.md (group decision, before test labels are read)

```
- <date> 2026, before any test label was looked at (proposal from the EDA and evaluation work; sections 1-8 unchanged):
  additions to the evaluation. (a) The area interval is reported both as the usual ±1.96 SE and with an adjusted
  upper bound (evaluation.area_interval): a simulation of our design showed the usual interval holds the true area
  only 47-94% of the time when crop is rare in stratum A, every miss below the truth; the adjusted interval reaches
  88-100%. (b) Error analysis of every map by the labellers' cover class, cues, homestead distance, fallow and box
  share (evaluation.error_analysis). (c) Trigger-decision agreement of every map with the sample's flooded-cropland
  interval (evaluation.trigger_agreement). (d) Our scores next to Kerner et al. 2024 and Adebayo et al. 2026
  (evaluation.published_vs_ours). (e) Points needed with agreement strata against one-map strata
  (evaluation.design_efficiency). (f) Readability of the frozen rules (evaluation.rule_complexity).
```
