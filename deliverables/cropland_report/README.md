# Cropland report kit: START HERE

Group 1, JBG060. Everything for the methodological report (max 2,000 words, due 25 Oct), the poster (21 Oct) and the code submission, in one place. Put together on 9-12 Oct 2026 (Yassin, with Claude).

**Going through it before the meeting of 14 Oct: follow [`REVIEW_PLAN.md`](REVIEW_PLAN.md)** (about 2 hours each: a 30-minute tour for everyone, then your own part) and leave comments in [`REVIEW_NOTES.md`](REVIEW_NOTES.md).

## 1. Where we stand (12 Oct 2026, evening)

| step | status |
|---|---|
| EDA of the public cropland maps (7 maps + ASAP, flood overlay, national, year by year) | done: notes 01, figures 1-10 |
| Labelling: 450 points, two blind labels each | **done 12 Oct**: 85.6% agreement, kappa 0.70 (notes 04, figure 11) |
| 06 merge labels | done 12 Oct: 134 agreed crop, 247 agreed not crop, 65 disagreed, 4 crop vs fallow |
| 07 Rule 1, fitted on the 125 agreed calibration points and **frozen** | done 12 Oct: `crop if dist_buildings_m <= 333.4 and edge_density > 0.0937` (`cropland/rule1_2026-10-12.json`; cross-validated F1 0.86) |
| 08 our map in Earth Engine | check passed (map = rules at all 150 calibration points); Bor South and national exports queued, Aweil restarted 12 Oct after a radar fix (`features.py`, values unchanged) |
| Adjusted area interval | logged in the METHODOLOGY change log 12 Oct as a proposal by Yassin, **before** 09 read any test label: confirm at the next meeting |
| 09 scores and area | **done 12 Oct**: Aweil 3.8% cropland (116,500 ha, 76,700-156,400); Rule 1 F1 0.72 vs public maps 0.03-0.55 (notes 07, section 7.0) |
| 11 evaluation additions | **done 12 Oct** (`cropland/11_evaluate.py`): adjusted interval, where maps fail, ours vs published, points needed, pixel-count bias |
| 12 logistic regression vs trees | **done 12 Oct** (`cropland/12_other_models.py`): chosen by cross-validation on calibration points, two logistic models frozen and scored (F1 0.61-0.66); no model ranked above another |
| 10 flood overlay + trigger agreement | **done 14 Oct**: the maps disagree (Aweil 10-307 ha flooded cropland; Bor South 0-10 ha, Dynamic World 1,606); the sample has only 1-2 points in flood cells, so it **cannot tell** flooded cropland (notes 07, R5) |
| 10b past floods 2000-2025 on today's cropland | **done 14 Oct** (`cropland/10b_flood_history.py`, figure 12): in Aweil's 9 big flood years the sample puts 4-16 times more cropland under water than the median map; Esri, GLAD and WorldCover would have missed a 500 ha trigger in 2022 (notes 07, R5b) |
| Figures 13-15 and the interactive flood map | **done 14 Oct**: before/after flood map (13, `maps/flood_aweil_2022.html`, `cropland/10c_flood_map.py`), area vs maps (14), scorecard (15) |
| **Report draft** | **written 14 Oct from the results**: `report/report_draft.md` (read it on GitHub) and `report/report_draft.tex` (edit it; Overleaf). About 4,100 words, so the group cuts to 2,000; pending decisions tagged |
| Our map over the whole country | **done 14 Oct** (`cropland/national_map.py`, figure 27, notes 07 R7): 6.8% of South Sudan marked (upper bound, not checked outside our areas); state ranking like CFSAM (0.52). Correction: in Aweil our map marks 22.6%, above the sample's 14.3%: it over-marks |
| Poster | plan rewritten 14 Oct against the Canvas requirements and rubric (notes 08): A0 portrait, 20 pt minimum, 300-400 words, panels A-I, pitch and questions |
| Dashboard | **first version 14 Oct**: [`dashboard.html`](dashboard.html) (open with a double click, works offline), built by `python cropland/14_dashboard.py` from the result tables; seven sections: area, maps, flood exposure 2000-2025 with the 2022 before/after map, trigger hindcast with households, the whole country, what we hand over, limits. Page code in `cropland/dashboard/template.html`, plan in [`DASHBOARD_PLAN.md`](DASHBOARD_PLAN.md) |
| National check | **14 Oct**: the 30 m national map keeps recall 0.75 on our test points but precision falls to 0.50 (F1 0.60 against 0.72 at 10 m); A labelled check sample was planned and **dropped: the group does not label further** (14 Oct). Instead, without labels (`national_map.py compare`): of the land 2+ public maps call crop, our map marks 29% outside our areas (Warrap 96%, Lakes 83%, Upper Nile 2%) |
| Labelling errors | **reported 14 Oct** by the labellers: undated Google imagery, Wayback, extra Sentinel scenes, a few early labels counting crop just outside the box. In the report (Discussion, appendix "Known errors in the data"); guide clarified for the national round. Decision 11 |
| Own trees (Wei, Matei) | open: `cropland/tree_workbench.ipynb` (calibration points only; retrains Rule 1 exactly; writes nothing until `FREEZE = True`) |
| Reuse for other areas / countries | **done 12 Oct**: `cropland/config/*.toml`, `cropland/REUSE.md`, `cropland/make_new_area.py` |

## 2. Reading order

**Quick tour (30 minutes):** this README -> figures 1, 3, 7, 9, 11 in `figures/` -> `notes/01_context_and_need.md` (draft paragraphs at the top) -> `notes/05_use_for_zoa_and_anticipatory_action.md` (5.1) -> `report/report.tex` (open it on Overleaf, see `report/README.md`).

**Full review:** the notes in order, each written for one rubric heading:

| file | rubric heading (points) | what is in it |
|---|---|---|
| `notes/01_context_and_need.md` | Context / Problem / Motivation (3) | draft paragraphs; seven EDA findings with numbers |
| `notes/02_data_understanding.md` | Business and Data Understanding (4) | Kerner 2024, Adebayo 2026 (incl. the F1 = 0 table for our maps), Pacetti 2017; every dataset; glossary |
| `notes/03_research_objective_inputs.md` | Research Objective (5) | draft objective, sub-objectives, scope, ZOA requirements -> criteria |
| `notes/04_method_part1_sample_and_labels.md` | Approach (5), part 1 | strata, allocation, 210 m box, labelling, disagreements, **final label quality**, **what to do with the 65 disagreements (4.4b)**, beyond the state of the art |
| `notes/05_use_for_zoa_and_anticipatory_action.md` | Discussion, Conclusion | how this helps ZOA and ZHL (the lecturer's question), per action, positive and negative impacts |
| `notes/06_evaluation_methodology.md` | Evaluation Methodology (3) | criteria -> measures; interval check by simulation; **change-log line to paste** |
| `notes/07_results_discussion_conclusion_templates.md` | Results (3), Discussion (4), Conclusion (3) | **the results so far (7.0)**, table layouts, sentence templates, branches per outcome |
| `notes/08_poster_outline.md` | poster | panels, 90-second pitch, questions to expect |

## 3. Review checklist (everyone)

For every note and the LaTeX file, check:
1. **Is it true?** Every number should trace to a CSV in `tables/` (or a cited table). Mark anything you cannot trace.
2. **Do you agree with the claim?** In particular: "the map decides whether the trigger fires" (notes 01, finding 5), the use for ZOA (notes 05), the adjusted interval (notes 06), Rule 1 being about homesteads and field edges rather than season cues (what does that mean for Bor South?).
3. **Wording for the report**: plain, short, no claims we cannot back.
4. **What is missing** for your part of the report or poster.

Suggested focus (swap freely): method and Rule 1 (notes 04, 06, `cropland/METHODOLOGY.md`); sampling, estimators and the interval (notes 04, 06, `cropland/estimators.py`, `cropland/evaluation.py`); models and where maps fail (notes 06-07, `cropland/07_fit_rules.py`); context, stakeholder use, poster (notes 01, 03, 05, 08).

## 4. Decisions needed from the group

1. **Area interval (logged 12 Oct as a proposal; confirm).** A simulation of our exact design shows the usual ±1.96 SE interval (what `09_score.py` reports) would hold the true area only 47-94% of the time, every miss below the truth, because the stratum where no map sees crop (95% of Aweil) often holds no cropland point. Proposal: report the adjusted upper bound too (`cropland/evaluation.area_interval`; 88-100% in the same simulation). If agreed, paste the ready line from notes 06, 6.7 into the change log of `cropland/METHODOLOGY.md` **before step 09 runs** (09 is the first step that reads the test labels).
2. **Rule 1 was frozen on 12 Oct** on Yassin's laptop and Earth Engine project (the group project was not reachable from his account). Two small code changes made that possible, both backward compatible: `common.py` takes the course data from `../data-JBG060-2026/` when `raw_data/` is empty, and the asset folder follows `CROPLAND_EE_PROJECT`.
3. **Fallow**: used in 7 of 900 labels and never by both labellers on one point. "Cropland" and "cropped in 2025" will be nearly identical; say so in the report as a finding about the labelling design.
4. **Sprint review slide 9** (11 Oct, 720 labels) is outdated: final is 900 labels (331 crop, 550 not crop, 7 fallow, 12 unsure), 450 points labelled twice, exact agreement 84.7% (381 of 450), cropland vs not 85.6% (kappa 0.70); 53 splits on cropland vs not, 41 of them about field shapes (figure 11).

## 5. Folder map

```
deliverables/cropland_report/
  README.md        this file
  REVIEW_PLAN.md   how we go through all of this before 14 Oct, and the decisions for that meeting
  REVIEW_NOTES.md  everyone's comments, one section per person
  DASHBOARD_PLAN.md  the dashboard: five pages, code, who, when
  dashboard.html   the results dashboard (one file, opens offline; rebuild: python cropland/14_dashboard.py)
  notes/           long notes per rubric heading (01-08)
  report/          LaTeX skeleton for Overleaf: report.tex, references.bib, numbers.tex (macros), build_report_inputs.py
  submission/      README_DRAFT.md: draft of the code-submission README and the outline of the single final notebook
  figures/         all figures (PNG, tracked in git): EDA 1-11, results 12-15
  maps/            interactive maps (HTML, open in a browser; needs internet for the satellite background)
  tables/          the CSV behind every figure and number; key_numbers.csv = the numbers the text quotes
  sources/         Kerner 2024, Adebayo 2026, our plan (28 Sep), methodological feedback slides, Sprint 2 review, sprint review (11 Oct)
cropland/          all code (pipeline steps 00-12, EDA and evaluation modules, tree_workbench.ipynb), METHODOLOGY.md,
                   labels, rules, results/ (accuracy, area, evaluation tables), config/ + REUSE.md (other areas)
```

Code added in this round (in `cropland/`): `eda_public_maps.ipynb` (the EDA, runs in about 2-5 minutes), `eda_maps.py`, `eda_figures.py`, `eda_labels.py`, `efficiency.py`, `evaluation.py`, `test_evaluation.py`, `reference_statistics.csv`, `reference_national.csv`, `reference_accuracy_literature.csv`, `lol_river_osm.geojson`, `requirements-cropland.txt`.

## 6. Figures (draft captions; captions count towards the 2,000 words)

1. `01_crop_share_per_map.png`. **Seven maps, seven answers.** Share of the land each public cropland map calls crop, in the five Aweil counties, in Bor South and in South Sudan; lines: FAO/WFP cereal harvested area (modelled) and FAOSTAT arable land. Maps ordered by year.
2. `02_agreement_curve.png`. **Cropland the maps agree on is almost absent.** Share of the land that at least *k* of the seven maps call crop (log scale). Bor South has no land where four or more agree; drawn at the bottom edge.
3. `03_pairwise_iou_aweil.png`. **Same class, different land.** Overlap of the crop class of every two maps in the Aweil counties (intersection over union). The same pairs agree on 97-99% of all pixels.
4. `04_national_crop_share_per_county.png`. **Where each map puts South Sudan's cropland.** Crop share per county per map, and CFSAM 2025 cereal area per state, same classes.
5. `05_states_vs_cfsam_2025.png`. **The maps do not rank the states as the crop assessment does.** Crop area per state against CFSAM 2025; line 1:1; rank correlation per map.
6. `06_same_map_every_year.png`. **Same product, different year.** Esri (2017-2025) and Dynamic World (2016-2025) per year: Dynamic World swings by a factor 10 in Aweil and 37 in Bor South.
7. `07_flooded_cropland_per_map.png`. **The map decides how much cropland flooded.** Cropland under the NASA flood extent (June-December) per map, 2022 and 2025; line: CFSAM 2022 flood-damaged area.
8. `08_lol_strip.png`. **Along the Lol.** Crop share within 5 km of the Lol river against the rest of the Aweil counties.
9. `09_published_accuracy_of_our_maps.png`. **What earlier studies found for these maps.** F1 and recall per country in Kerner et al. (2024) and Adebayo et al. (2026); ringed: Mali, where Esri has 0.97 accuracy and F1 = 0.
10. `10_published_recall_vs_crop_share.png`. **Published recall predicts Aweil, not Bor South.**
11. `11_annotation_statistics.png`. **Our labels.** 900 labels; agreement between the two labellers per area and stratum; which answers differ when they split (mostly field shape).

12. `12_flood_history.png`. **Past floods on today's cropland.** Cropland under water in each year's flood (2000-2025, June-December), Aweil counties and Bor South: the 8 public maps as a range with their median, our labelled sample as dots with 95% intervals in the years where at least 5 sample points lay on flooded land. A scenario: the 2025 cropland under each past flood.

13. `13_flood_map_aweil_2022.png`. **Same flood, different answer.** The 2022 flood in the Aweil counties, cell by cell (232 m): left, the flooded cells where WorldCereal 2021 (the best public map on our test points) shows crop; right, the cells our map adds (its 210 m box holds a field), with our sample points on flooded land. Our map shows where; how much comes from the sample (7,263 ha against WorldCereal's 1,002). Interactive version with every public map: `maps/flood_aweil_2022.html`.
14. `14_area_vs_maps.png`. **The maps under-count cropland.** Share of the land that is cropland per public map (pixel count) against our labelled sample with its 95% interval, Aweil counties and Bor South (log scale).
15. `15_scorecard.png`. **Which map to trust.** Precision, recall and F1 of every map on the Aweil test points, with 95% intervals; our models orange, public maps blue; dashed line: how well the two labellers agree (0.86).
16. `16_same_window_every_map.png`. **The same window in every map.** A 6 x 6 km window north of Aweil town in Sentinel-2 (October-December 2025), the seven public maps (blue) and our map (orange), with the labelled points; each title gives the map's crop share of the window and how many of the labelled fields it finds. The updated version of the Sprint 2 slide "seven maps, seven answers" (Twic county, before labelling). The window has the most labelled points, all cropland, near town where several maps see crop, so the maps look better here than over Aweil as a whole. Made by `cropland/eda_window.py`.
17. `17_method_diagram.png`. **The approach.** Strata from the seven maps, 450 random points split before labelling, two blind labels per 210 m box; the labels give the area, train our models (calibration points) and score every map (test points); flood masks over all of them.
18. `18_rule1_tree.png`. **Rule 1 as a tree.** Two questions (a building within 333 m; field edges), with the calibration and test points in every leaf.
19. `19_rule1_decision_space.png`. **Why Rule 1 works.** Every agreed point on its two inputs, calibration and test, with the region Rule 1 calls crop.
20. `20_models_cv_vs_test.png`. **Trees or logistic regression?** Every model's F1 in repeated cross-validation (calibration) and on the Aweil test points.
21. `21_what_models_learned.png`. **What the models learned.** Logistic coefficients per standard deviation and random-forest importances, same 18 inputs.
22. `22_feature_distributions.png`. **The 18 features**, boxes with and without cropland.
23. `23_strata_and_sample.png`. **Strata and sample.** Share of each cell where at least one map sees crop, and the 450 points by stratum.
24. `24_labelling_examples.png`. **What the labellers see.** Twelve monthly images of 2025 for an agreed crop box, an agreed not-crop box and a disputed box.
25. `25_interval_simulation.png`. **The interval check.** Coverage of the usual and the adjusted interval in simulations of our design, per area and measure.
26. `26_points_per_design.png`. **Points needed** for a 20% CV: our strata against strata from one map.

27. `27_national_map.png`. **Our map over South Sudan.** Rule 1 applied to the whole country (30 m), as the share of each 1 km cell where a 210 m box holds a field; only Aweil and Bor South have labels (outlined). Right: per state against CFSAM 2025 (rank correlation 0.52). Drawn by `cropland/national_map.py`.

Figures 17-26 are drawn by `cropland/report_figures.py` (no Earth Engine).

Suggested use: report = 17 (method), 15, 18, 12 + table 1 in the text, the rest in the appendix (the draft does this); poster = 14, 15, 13, 12 + method diagram (notes 08: A0 portrait, 20 pt minimum, also inside figures).

## 7. How to regenerate everything

```
python -m pip install -r cropland/requirements-cropland.txt
set CROPLAND_EE_PROJECT=<your Earth Engine project>     (only for Earth Engine steps)
# open cropland/eda_public_maps.ipynb and run all cells (writes tables/ and figures/ here)
python deliverables/cropland_report/report/build_report_inputs.py   (numbers.tex, Overleaf zip)
python cropland/14_dashboard.py                                      (dashboard.html, no Earth Engine)
python cropland/test_cropland.py && python cropland/test_evaluation.py
```
The notebook needs the course data next to the repo (`data-JBG060-2026/`) or in `raw_data/`, and the cached Earth Engine counts in `raw_data/cropland/eda/`. Those are in git since 14 Oct except `national.npz` (51 MB, only for figures 4-5: ask Yassin, or rerun `python cropland/eda_maps.py export`, which takes hours). The random-forest benchmarks (`raw_data/cropland/benchmarks.joblib`, needed by step 09) and Rule 1 per flood cell (needed by step 10b) are in git too.

## 8. Open points

1. **Sprint 2 slide value to retire**: Dynamic World 2022 in Aweil is 0.8% of the land, not 0.1%. Every other Sprint 2 map value reproduces.
2. **REACH cash figures** (USD 149 basket, USD 0.63/kg sorghum): read through a search summary only; check against the JMMI factsheets before quoting.
3. **Potapov et al. 2022 numbers** (190 vs 208 ± 47 Mha): taken from our plan, not checked against the paper.
4. **WFP ADAM**: our plan says ADAM uses the Pacetti overlay; Pacetti et al. do not mention ADAM. Do not repeat it without a source.
5. **ZOA field points or photos** would be an independent check of the labels; still worth asking.
6. Kerner's text says Esri had 0.98 accuracy in Mali, their Table 1 says 0.97; we quote the table.
7. Word budget (suggestion): Context 200, Data understanding 300, Research objective 200, Approach 450, Evaluation 200, Results 300, Discussion 200, Conclusion 150.

## 9. Sources added in this round (details in notes 02 and `report/references.bib`)

- Kerner et al. (2024), *Scientific Data* 11:486 (`sources/`). Adebayo et al. (2026), *IJAEOG* 148:105223 (`sources/`). Pacetti et al. (2017), *Advances in Water Resources* 110:494-504 (`literature/`).
- FAO/WFP CFSAM 2025 (doi 10.4060/cd8719en; https://climis-southsudan.org/uploads/publications/CFSAM_2025.pdf) and CFSAM 2022 (https://openknowledge.fao.org/server/api/core/bitstreams/8704f728-da00-4c2b-941c-605a714dd7e5/content), transcribed in `cropland/reference_statistics.csv`.
- FAO land use via World Bank WDI (https://api.worldbank.org/v2/country/SSD/indicator/AG.LND.ARBL.HA).
- REACH JMMI factsheets 2025 (https://repository.impact-initiatives.org/document/impact/f6c53bf4/REACH_SSD_Factsheet_JMMI_August-2025.pdf).
- OpenStreetMap, Lol river (Overpass, 10 Oct 2026, ODbL). ZOA and ZHL, Q&A 2 slides (21 Sep 2026). Anticipation Hub (2023).
- Our own: plan (28 Sep), methodological feedback slides, sprint review (11 Oct) in `sources/`.
