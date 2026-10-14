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
| Dashboard | plan revised 12 Oct ([`DASHBOARD_PLAN.md`](DASHBOARD_PLAN.md), in this folder): five-page results story, no general course data |
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
  notes/           long notes per rubric heading (01-08)
  report/          LaTeX skeleton for Overleaf: report.tex, references.bib, numbers.tex (macros), build_report_inputs.py
  submission/      README_DRAFT.md: draft of the code-submission README and the outline of the single final notebook
  figures/         all EDA figures (PNG, tracked in git)
  tables/          the CSV behind every figure and number; key_numbers.csv = the numbers the text quotes
  sources/         Kerner 2024, Adebayo 2026, our plan (28 Sep), methodological feedback slides, sprint review (11 Oct)
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

Suggested use: report = 1, 3 (or 2), 7, 9 + a method diagram; poster = 1, 4, 7, 9, 11 (+ 8).

## 7. How to regenerate everything

```
python -m pip install -r cropland/requirements-cropland.txt
set CROPLAND_EE_PROJECT=<your Earth Engine project>     (only for Earth Engine steps)
# open cropland/eda_public_maps.ipynb and run all cells (writes tables/ and figures/ here)
python deliverables/cropland_report/report/build_report_inputs.py   (numbers.tex, Overleaf zip)
python cropland/test_cropland.py && python cropland/test_evaluation.py
```
The notebook needs the course data next to the repo (`data-JBG060-2026/`) or in `raw_data/`, and the cached Earth Engine counts in `raw_data/cropland/eda/` (about 55 MB; ask Yassin, or rerun the exports with `python cropland/eda_maps.py export`, which takes hours).

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
