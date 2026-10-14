# Review plan: going through the cropland work before the meeting of 14 Oct

For Matteo, Marc, Wei, Matei and Yassin. About **2 hours each**, done before **Wednesday 14 Oct**. The goal is to
arrive at the meeting with the decisions in section 4 ready, so the meeting takes one hour and we can build the
dashboard, poster and report from 15 Oct.

## 0. Get the work (5 minutes)

```
git fetch
git checkout cropland-review-12oct
```

Everything to read is in `deliverables/cropland_report/` (this folder). Code is in `cropland/`. You need Python
only for the tree workbench (`pip install -r cropland/requirements-cropland.txt`). The label images are not
needed.

## 1. Everyone: the quick tour (30 minutes)

| # | read | time | what you get |
|---|---|---|---|
| 1 | `README.md`, section 1 | 5 min | where every step stands |
| 2 | `notes/07_results_discussion_conclusion_templates.md`, section 7.0 | 10 min | the results so far: area, map accuracy, where maps fail, models |
| 3 | `figures/01`, `07`, `09`, `11` | 5 min | the story in four pictures |
| 4 | `DASHBOARD_PLAN.md`, section 3 | 5 min | the five dashboard pages |
| 5 | `notes/04_method_part1_sample_and_labels.md`, section 4.4b | 5 min | what we can do with the 65 disagreements |

## 2. Your own part (about 90 minutes)

Swap parts freely; just make sure every part has someone.

| who | part | read | answer before the meeting |
|---|---|---|---|
| **Matteo** | protocol and the report frame | `cropland/METHODOLOGY.md`, the four change-log entries of 12 Oct; `notes/06`, sections 6.5-6.7; `report/report.tex` and `report/README.md`; README section 8 (word budget) | Do you confirm each 12 Oct entry (adjusted interval, logistic models, reuse config, 210 m box)? Is the report structure right, and who writes which section? |
| **Marc** | results, maps, dashboard pages 1-3 | `notes/07`, section 7.0 (R2-R4) against `cropland/results/area_adjusted.csv`, `accuracy.csv`, `error_analysis.csv`, `pixel_count_bias.csv`; figures 01-08; `DASHBOARD_PLAN.md` sections 3-4 | Does every number trace to a CSV? Which figures go in the report, which on the poster? Is the three-layer map view feasible by 18 Oct? How do we show Bor South? |
| **Wei** | models: Rule 1 and your own tree | `cropland/tree_workbench.ipynb` (run it, change the settings); `cropland/results/model_cv.csv`; the "Models" paragraph in `notes/07` 7.0; `cropland/README.md`, "Building another model" | Which tree(s) will you try (Aweil-only, fewer inputs, the embedding, another depth) and when can you freeze? Keep or drop the two logistic models in the report (decision 2)? |
| **Matei** | models and the evaluation | `tree_workbench.ipynb` (agree with Wei who tries what); `notes/06` (evaluation methodology); `notes/04`, sections 4.4-4.4b; `cropland/results/design_efficiency.csv` | Which disagreement analyses do we run (ideas 1-4 are cheap)? Is "Bor South: no recall can be computed" stated clearly enough? |
| **Yassin** | context, use for ZOA, poster, reuse | `notes/01`, `02`, `03`, `05` (draft paragraphs); `notes/08` (poster); `cropland/REUSE.md` | Is the lecturer's question (how does this help ZOA?) answered? Poster panels and owners? Prepares a 10-minute walkthrough to open the meeting. |

**The models are still open.** Rule 1 (our main tree) is frozen and scored, and so are the two logistic
regressions added on 12 Oct. Any other tree is up to Wei and Matei: change the workbench as you like, choose on
the calibration points, log it, then freeze and score it once (instructions at the top of the notebook).

## 3. How to leave comments

Write under your own name in `REVIEW_NOTES.md` (one section each, so there are no merge conflicts), then commit
and push to the same branch (`git pull` first). Start each comment with a tag:

- **[fix]** a wrong number or a claim we cannot back (say which file and line);
- **[decide]** something the group has to decide (add it to section 4 if it is missing);
- **[idea]** anything else.

## 4. Meeting 14 Oct (60 minutes): decisions

| # | decision | options | proposal | prepares |
|---|---|---|---|---|
| 1 | Adjusted area interval (in the change log as a proposal, logged before any test label was read) | confirm / reject | confirm: the usual interval held the true area in only 47-94% of simulated samples | Matteo |
| 2 | The two logistic regressions (frozen and scored 12 Oct; test F1 0.66 and 0.61 against Rule 1's 0.72) | keep as a comparison / drop | keep, as one row in the model table and one sentence. Their scores are known, so dropping them now means choosing what to report after seeing the results | Wei |
| 3 | Our own trees: what, who, freeze date | per tree | freeze by 16 Oct evening, scored 17 Oct; calibration cross-validation only, logged first | Wei, Matei |
| 4 | Disagreements: which of ideas 1-11 (notes 04, 4.4b) | any | ideas 1-4 now (no new labels); ask ZOA about idea 7 (field check of 10-20 disputed boxes) | Matei |
| 5 | Dashboard: the five pages and who builds what (`DASHBOARD_PLAN.md`, 5b) | confirm / change | confirm; build 16-18 Oct, frozen 19 Oct | Marc |
| 6 | Report: section owners, word budget, figures | per section | budget in README section 8; figures 1, 3, 7, 9 + method diagram | Matteo |
| 7 | Poster: panels and owners (`notes/08`) | per panel | figures 1, 4, 7, 9, 11 + scorecard | Yassin |
| 8 | Bor South: how to present it | | area 0.4% with a wide interval; no recall possible (no agreed crop test point); Dynamic World paints wetland as crop | Marc |
| 8b | Flooded cropland (added 14 Oct): the sample has 1-2 points in flood cells and cannot tell; keep the cautious bound ("cannot tell") and say so, or present the map numbers only | cautious bound / maps only | cautious bound, reported as a negative result plus the lesson (a flood stratum next season) | Yassin |
| 8c | Past floods on today's cropland (added 14 Oct, figure 12, notes 07 R5b): use in the report and on the poster? It is an analysis added after the results, a scenario (2025 cropland), with two rules set after a first look (5+ points; trivial years not counted) | use as scenario / appendix only / drop | use, as the anticipatory-action result, with its limits stated | Yassin |
| 9 | Merge `cropland-review-12oct` into `main` | now / after fixes | after the [fix] comments are done | whoever is last |

## 5. After the meeting

| date | done when |
|---|---|
| 15 Oct | results milestone (flood overlay already in since 14 Oct: notes 07, R5): notes 07 and the report Results drafted from section 7.0 |
| 16 Oct | own trees frozen (Wei, Matei) |
| 17 Oct | own trees scored (`09_score.py`), notes 07 updated |
| 16-18 Oct | dashboard pages built |
| 19 Oct | dashboard frozen; poster figures exported from it |
| 21 Oct | poster |
| 25 Oct | report (and SLE essay) |

## 6. Ground rules while reading

- Every number should trace to a CSV in `tables/` or `cropland/results/`. If you cannot trace one, mark it [fix].
- The test points are for scoring only. A new model is chosen on the calibration points, logged in the change
  log, then frozen and scored once.
- Everything is per **210 m box**. A pixel of our map means "the box around me holds a cropped field", so
  hectares from our map are an upper bound; the cropland area itself comes from the labelled sample.
- Differences between labellers are reported anonymously (labeller A-E).
