# 3. Inputs for the research objective (report: "Research Objective", 5 points)

Long notes, 10 Oct 2026. Not asked for in this round, but the rubric gives this section 5 points and the context (file 01) has to lead into it, so here are the pieces. Wording builds on the RO on the methodological feedback slides (6) and METHODOLOGY.md section 1, updated to 2025.

---

## 3.1 Draft objective

> Estimate how much land in ZOA's two areas (the five Aweil counties and Bor South county) was cropland in the 2025 season, with a 95% confidence interval that does not depend on any map; measure how accurately seven public cropland maps, the ASAP mask from the course data and a readable rule-based map of our own capture that cropland there; and show how the choice of map changes the flooded-cropland figure that a "flood inundating cropland" trigger would use.

Sub-objectives, each with its measure:

| | sub-objective | measured as | done when |
|---|---|---|---|
| SO1 | cropland area | ha and % of land, 95% CI, per area; for cropland (cropped + fallow) and for cropped in 2025 | all 450 points labelled twice |
| SO2 | accuracy of the public maps | precision (UA), recall (PA), F1 with standard errors on the 300 test points, per area and definition; maps whose intervals overlap are not ranked; set against the published scores of the same maps (Kerner et al. 2024, Adebayo et al. 2026) | after SO1 |
| SO3 | a readable map of our own | the same scores for Rule 1 (decision tree, depth 2-4) and the black-box benchmarks | rules frozen on calibration points |
| SO4 | does the choice matter for anticipatory action? | flooded cropland 2022 and 2025 per map and from the sample (with CI); would a trigger fire; points needed for a yearly check (relative efficiency) | after SO1-SO3 |

## 3.2 Why this objective (link to context and data)

- ZOA's priority impact is harvest failure from flooding (Q&A 2, slide 6) and its trigger form is "a flood which inundates cropland resulting in at least y% of total yield reduction" (slide 31). The cropland term is the one nobody has checked (file 01).
- ZHL wants "rigorous answer small sub-problem > superficial answer full problem" (slides 5, 29). Measuring one input of the trigger properly is that sub-problem.
- It is feasible in the time: the sample was drawn and all 450 points were labelled twice by 12 Oct 2026.

## 3.3 Assumptions and scope limits (to state explicitly)

1. **Reference = what trained people see on imagery.** No field visits (access, security, time). Labels come from monthly Sentinel-2, Sentinel-1 and sub-metre Esri imagery; two people per point.
2. **One season, 2025.** The maps are from 2015-2025 and are compared as they are; their year is shown with every score.
3. **Checked in two areas.** Area, accuracy and the reference flood estimate hold for the Aweil counties and Bor South; our national map is labelled "not checked" elsewhere.
4. **Definition.** Cropland = cropped in 2025 or fallow; labelled on a 210 m box (presence + share-of-box class). Maps define cropland differently (fallow in or out), so each is also scored against cropped-only labels.
5. **Flood masks taken as given.** We do not evaluate the NASA masks; flooded cropland is exposure, not damage.
6. **No forecast.** The trigger analysis uses observed floods. A forecast would sit in front of it (the prediction track of Sprint 1-2 is documented in `prediction/`).

## 3.4 What an adequate solution must satisfy (stakeholder requirements -> criteria)

| ZOA / ZHL said (Q&A 2) | criterion for our solution | how we meet it |
|---|---|---|
| "All findings should be transparent: why this finding, at what certainty?" (slide 5); "How certain are you?" (9); "where, when, and how certain" (23) | every number has an error bar or a stated range | design-based CI for the area; SE for every accuracy score; ranges across maps |
| "Simple and interpretable is better than complex and black-box" (19); trigger must be "transparent, interpretable" (40) | the method and our map can be read and checked | written labelling key; Rule 1 prints as if-then rules; the black box only as a benchmark |
| "Local decisions > country-wide assessment"; Lol river and Bor South (3); "the more detailed, the better" (21) | results for ZOA's areas, as local as the data allow | sample and scores in the two areas; county and Lol-strip numbers; 10 m map |
| Local staff should operate it without external technical organisations (24) | rerunnable with free tools, cheap to repeat | open data, Earth Engine + Python; labelling tool runs on a laptop; a yearly check of ~150 points takes about a day for two people (file 05) |
| Misses: people without assistance; false alarms: wasted resources, lost trust (10, 11) | report both error types | recall (missed fields) and precision (false crop) separately, per map |
| "Rigorous answer small sub-problem" (5, 29) | one input of the trigger, done properly | cropland area and map accuracy, not a full impact forecast |
| Fair: understand the impact on all individuals (6); target the most vulnerable households (7) | show whose farmland the maps miss | where maps miss crop (stratum A, Lol strip, green belt); SLE essay |

Measurable targets fixed before labelling (METHODOLOGY.md): pilot go / no-go at 70% confident labels (met: each person was confident on 87-100% of the 30 pilot points, but crop agreement on the 10 m pixel was poor, which led to the 210 m box, file 04); 150 calibration / 300 test points split before labelling; Rule 1 frozen in a dated file before any test point is used; maps with overlapping 95% intervals not ranked.
