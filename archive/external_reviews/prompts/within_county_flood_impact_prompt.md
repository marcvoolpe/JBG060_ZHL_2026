# Deep research prompt: does year-specific flood severity explain year-to-year flood impact in South Sudan, beyond each county's usual flood level?

## Your role

You are an independent reviewer. Evaluate the research question below against (a) published and grey literature and (b) the data limitations described in this prompt. You are not asked to improve the project's prospects or to be encouraging. "Proceed", "proceed with changes" and "do not proceed" are all acceptable conclusions, and you should reach whichever one the evidence supports.

Ground rules:

1. Cite a source for every factual claim about literature, datasets, organisations or programmes (author, year, title, and a link or DOI). If you cannot find a source, write "not verified".
2. Keep three kinds of statement apart: facts from sources, facts stated in this prompt (treat these as the project team's claims and check them against public documentation where possible), and your own inference.
3. Do not invent datasets, variables, resolutions or years of coverage. If you are unsure whether a dataset exists in the form needed, say so.
4. Do not assume a method is feasible because it is standard. Check it against the sample sizes given here.
5. Where evidence conflicts, present both sides. Avoid persuasive or promotional language, and do not soften criticism or inflate strengths.
6. No results from the proposed analysis are included in this prompt, on purpose. Evaluate the question and the design, not an answer.

Out of scope: the quality of any flood forecasting model, and the rest of the project.

## Context

- **Project.** A student data science capstone (TU Eindhoven, course JBG060), with two remaining sprints. Country: South Sudan. Spatial unit: county (admin2).
- **Stakeholders.** ZOA, a Dutch NGO working on food security and livelihoods, and Zero Hunger Lab (a university research partner). In a Q&A in September 2026, the stakeholders said:
  - They have no experience with anticipatory action or with data, and first want to understand the risks of the data and the dynamics of floods.
  - ZOA works along the Lol river in Northern Bahr el Ghazal and in flood-prone areas of Bor South county. It makes decisions at community level and prefers more spatial detail.
  - Actions need 3 days minimum, 10 days is sufficient, and 14 days is a robust upper bound.
  - The priority impact in their areas is harvest failure. They also target internally displaced people (IDPs), host communities and pastoralists, and allocate aid by exposure, vulnerability and coping capacity.
  - Results should be simple, interpretable and transparent, and a rigorous answer to a small sub-problem is preferred to a superficial answer to the full problem.
  - They will decide the trade-off between false alarms and misses themselves, and want the reliability of any result stated.
  - ZOA does not run warehouses or distribution points; it sources locally and delivers last-mile by road or boat.
- **Hydrology (the project's understanding; please verify).** Bor South lies on the Bahr el Jebel, downstream of the Mongalla gauge, so its flooding may respond to upstream lake and river flows. The Lol is a river of the Bahr el Ghazal basin, where local rainfall may matter more.
- **Team context.** Other project strands forecast flood extent and duration and translate floods into displacement. This question is meant to establish how much year-specific flood information adds for explaining impact, compared with knowing which counties usually flood.

## The research question (as proposed)

> Evaluate whether year-specific flood severity (extent, duration, extent × duration) explains year-to-year variation in observed flood impact (IOM DTM disaster displacement, OCHA people affected) in South Sudan's well-covered counties, 2021–2025, beyond each county's usual flood level. Compare against a static county-susceptibility baseline using within-county rank correlation and leave-one-year-out error. The result is meant to tell ZOA how much a flood forecast adds to targeting beyond knowing where floods recur, and how reliably.

**Idea.** A county's impact in a year can be high because it is a county that always floods (a persistent component) or because this year was worse than usual for it (a year-specific component). A pooled correlation across county-years mixes the two. The question asks whether the year-specific component of severity predicts the year-specific component of impact.

**Proposed operationalisation:**

- **Unit.** The admin2 boundaries have 79 units. 71 of them have at least 95% of their area inside the flood-mask tiles; Pariang, Fashoda, Maban, Manyo, Melut, Renk, Abyei Region and Raja are excluded.
- **Severity per county and calendar year**, from the flood masks below, with both mask classes combined:
  - extent: km² flooded at least once in the year;
  - duration: mean number of dekads (10-day periods) with at least one detection, per flooded pixel;
  - extent × duration.
- **Impact:**
  - IOM DTM Mobility Tracking: IDPs displaced by "disaster" who are present at the time of assessment, by year of arrival, taken from the first round after each flood season;
  - OCHA county-level people affected by floods.
- **Usual level.** A county's mean over its other years, on a log(1 + x) scale.
- **Deviation.** This year's value minus the usual level, computed for both severity and impact.
- **Tests:**
  - within-county Spearman correlation of the two deviations, with a bootstrap over counties;
  - within each year, the rank agreement across counties between the two deviations;
  - leave-one-year-out prediction error of "usual level only" against "usual level plus this year's severity deviation".
- **Reporting.** The effect size, its interval, and the smallest effect the data could have detected.
- **Interpretation offered by the proposers:**
  - a clear link means this season's severity changes who is hit;
  - a clear null means impact follows the recurrence map, so forecasts help with timing rather than targeting;
  - an inconclusive result means current impact data cannot yet validate a flood forecast.

## Data facts, as measured by the project team (please verify where possible)

### Flood masks

- **Product.** NASA global flood product (MCDWD family), about 232 m grid, daily detections, course files for 2000–2025. There are two classes:
  - "recurring": inside monthly masks of pixels flooded in at least 7 of the 22 years 2003–2024;
  - "unusual": water outside those masks and outside the permanent-water reference.

  The recurring class is therefore defined partly with future years, and the permanent-water class is not in the files.
- **Coverage.** The course files cover MODIS tiles h20v08 and h21v08 only, so nothing north of 10°N.
- **Cloud censoring.** A detection requires a clear view, so "no detection" does not mean dry. Project analyses report that about 5–7% of detections in 2020–2025 fall in July–September, with a peak from November to February. The main rainy and cropping season is therefore the least observed.
- **Regime shift.** A teammate's analysis reports that flooded area roughly doubled after 2019 (mean unusual-class area about 5,300 → 12,800 km²), and that the share of flooded ground wet for 3 months or more rose from 1–5% to 24–31%. All impact years (2021–2025) are after the shift.
- **Variance.** The same analysis reports that county explains 71–91% of the variance in log flooded area, year 0.3–6%, and county × year 7–24%.
- **ZOA's areas in the masks:**
  - In the Aweil counties along the Lol, the masks record very little flooding: for example, Aweil Centre has 2–27 km² × dekads per year in 2022–2024, compared with 2,300–8,200 in Duk, Jonglei.
  - In Bor South, severity stayed within −20% to +25% of its usual level in each of 2022, 2023 and 2024.

### IOM DTM Mobility Tracking (baseline assessments)

- **Rounds and collection periods:**

  | Round | Collected |
  |---|---|
  | R12 | Nov–Dec 2021 |
  | R13 | Jul–Aug 2022 |
  | R14 | Mar–Apr 2023 |
  | R15 | Jul–Sep 2024 |
  | R16 | Dec 2024–Feb 2025 |

  R12 does not report arrivals by year and reason. (Correction, 25 Sep 2026: R13 does, with 2021 and January–July 2022 bins; an earlier check read the wrong sheet. The judge's report was produced from the uncorrected text.)
- **Record structure.** Each location record gives the IDPs present at assessment, by period of arrival (2021, 2022, 2023 and 2024 are separate bins from R14 onward) and by reason (conflict, clashes, disaster, other).
  - "Disaster" is not flood-specific.
  - Each location lists one main county of habitual residence per arrival period.
  - Among R14 locations with 2022 disaster arrivals, that origin county equals the location's own county at about 82% of locations and is "Unknown" at about 15%.
- **The counts are a stock of people still displaced, and they change between rounds.** National disaster-displaced IDPs present, by arrival year:

  | Arrival year | R14 | R15 | R16 |
  |---|---|---|---|
  | 2021 | 131,333 | 88,723 | 84,012 |
  | 2022 | 219,241 | 92,501 | 77,381 |
  | 2023 | 137,800 (Jan–Apr only) | 104,284 | 97,708 |
  | 2024 | – | 77,298 | 328,091 |

  County examples:
  - Rubkona's 2022 cohort is 47,772 in R14 and 13,537 in R16.
  - Juba's 2022 cohort is 28,496 in R14 and 286 in R16.
  - Some cohorts grow between rounds: Duk's 2023 cohort is 5,208 in R15 and 6,122 in R16. This suggests coverage or classification changes as well as returns.
- **Timing.** Using the first round after each season (2022 from R14, 2023 from R15, 2024 from R16) gives three usable years. Taking the flood-season peak as roughly October–December, the gap between the peak and the survey differs by year: roughly 3–6, 7–11 and 0–4 months.
- **Calendar years and seasons.** Arrivals are binned by calendar year, and flood displacement from one season continues into January–April of the next year.
- **Hubs.** Arrivals are recorded where people are, not where they came from. Destination hubs such as Juba record disaster IDPs while having little flooding of their own.
- **Sample.** Of the 78 counties in the DTM data, 60 have disaster arrivals in at least two of the three years and 51 in all three. The panel is 71 counties × 3 years = 213 county-years, about 142 within-county degrees of freedom, with many zero or near-zero values.

### OCHA flood-affected figures

- **Snapshots.** 13 Dec 2021; 30 Nov 2022 (also 21 Oct 2022); 20 Dec 2024; 30 Nov 2025. None was found for 2023.
- **Coverage.** Of the 71 covered counties, 56 appear in at least one snapshot: 12 once, 19 twice, 17 three times and 8 in all four. That gives 121 county-years in the 44 counties with at least two years, about 77 within-county degrees of freedom. The 2021 file has county names but no codes, so matching by name may miss a few rows.
- **Selection.** In one cross-section, whether a county was assessed was associated with its satellite flood-exposed population (logit p ≈ 0.001). The exposure measure used there is known to be undercounted because it samples one population cell per flood pixel.
- **Definitions.** "Affected" definitions vary. The figures include rain-fed flooding and depend on where assessors could go. Missing does not mean zero.

### Approximate power (project's calculation; please check)

Using Fisher's z with 80% power at α = 0.05, and effective n = Σ over counties of (years − 1), the smallest detectable within-county correlation is roughly 0.23–0.26 for DTM (depending on whether counties with zero arrivals are kept) and 0.31 for OCHA. This is before any correction for measurement error.

### Other data in hand

- IPC: 5 rounds, 2022–2025.
- UCDP GED conflict events: sparse, with a median of about 2 events per county.
- ERA5 rainfall and runoff.
- WorldPop, and a health-facility list.
- FEWS NET harvested area: largely modelled, and a within-county analysis found no relation with flood extent.

### Earlier review

An independent review of a related but different question (whether population or cropland exposure layers add explanatory value over raw flood extent) recommended:

- county and year fixed effects;
- count models (Poisson pseudo-maximum likelihood, negative binomial);
- Heckman-type selection correction for unassessed counties;
- conflict controls (ACLED);
- health-system outcomes (DHIS2, cholera).

Assess whether these fit this question and these sample sizes; do not assume they do.

## What to evaluate

### A. Novelty and prior work

1. Has this question (within-unit, year-to-year flood severity against humanitarian impact, beyond persistent susceptibility) been studied in South Sudan? In comparable settings (large floodplain wetlands such as the Inner Niger Delta or the Okavango, the Sahel, Somalia, Mozambique, Bangladesh)? Summarise designs, sample sizes and findings, with citations.
2. Which bodies of work bear on it? Consider panel studies of weather and flood shocks on displacement and welfare, disaster-displacement modelling, validation of impact-based forecasting, and measurement error in panel data. Do they suggest plausible effect sizes?
3. Is the question meaningfully different from (a) the pooled exposure–impact correlation and (b) the earlier-reviewed question on exposure layers? If it is effectively the same, say so.

### B. Measures

4. Is "DTM disaster IDPs present, by arrival year" a valid measure of year-specific flood displacement? Consider:
   - stock versus flow;
   - returns between flood and survey;
   - round timing and the attrition figures above;
   - cohorts that grow between rounds;
   - the non-specific "disaster" label;
   - main-origin attribution and destination hubs;
   - calendar-year binning.

   Do better DTM products exist at county level for 2021–2025, for example event tracking, flash reports or flow monitoring? Give coverage and access details.
5. Is OCHA "people affected" a valid measure? Consider definitions, access-driven assessment, and whether assessments are targeted using satellite flood maps, which would make the comparison circular.
6. Can cloud-censored optical flood masks measure year-to-year deviations within a county reliably? How large might the measurement error be relative to the within-county signal? Which independent flood products could serve as a reliability check for 2021–2025 (for example, WFP MODIS-based masks, Sentinel-1–based products such as the Copernicus Global Flood Monitoring product, or VIIRS)? Are they available at no cost at county scale?

### C. Statistical design

7. Is the design adequately powered? Is the approximate minimum detectable effect reasonable? How much would plausible measurement error in both variables attenuate the estimate, and what does that imply for interpreting a null?
8. Rank the threats and classify each as fatal, manageable (and how), or minor:
   - selection in OCHA;
   - survivorship and round timing in DTM;
   - time-varying confounders (conflict, returnees from Sudan since 2023, humanitarian response that may prevent displacement);
   - displacement across county lines;
   - only post-2020 years being available;
   - calendar-year alignment.
9. Which estimation approach fits these sample sizes: rank-based within-county correlation, two-way fixed-effects OLS on logs, Poisson pseudo-maximum likelihood with county and year effects, first differences, hierarchical Bayesian models, or selection models? Recommend one primary approach and one robustness check, with reasons.

### D. Decision relevance

10. For each possible outcome (clear link, clear null, inconclusive), what would change for an NGO like ZOA (two operating areas, community-level decisions, 3–14 day action lead time, harvest failure as the priority impact) and for the project's flood-forecasting work? Is county level too coarse to be useful to them?
11. Is displacement the right impact variable given these priorities? Suggest alternatives only if data for 2021–2025 verifiably exist, and state their limitations.

### E. Verdict

12. Score each criterion in the rubric below from 1 to 5, with one paragraph of justification each.
13. Give an overall recommendation: proceed as proposed, proceed with specific changes, or do not proceed. State the single most important change, and what evidence would reverse your recommendation.
14. List any claims in this prompt that you could not verify or believe are wrong.

## Rubric (score 1–5)

| Criterion | 1 | 3 | 5 |
|---|---|---|---|
| Novelty | Already answered for South Sudan | Answered elsewhere, not for South Sudan | Open, with no close precedent |
| Validity of measures | The measures cannot represent year-specific flood impact | Usable with major caveats | Valid with minor caveats |
| Statistical feasibility | Cannot detect plausible effects | Can detect only large effects | Adequately powered for plausible effects |
| Robustness to bias | A known bias would likely produce the result regardless of the truth | Main biases can be bounded, not removed | Main biases can be removed or tightly bounded |
| Decision relevance | No plausible result would change a decision | Some outcomes would inform a decision | Each outcome maps to a clear decision |
| Fit to remaining project time | Infeasible | Feasible only if narrowed | Comfortably feasible |

## Output format

1. Summary verdict (150 words at most).
2. Scores table: criterion | score | one-line reason.
3. Findings for sections A–D, with citations.
4. Evidence table: claim | source | how directly it applies (direct / analogous / indirect).
5. Recommended design changes, ranked, each with the problem it fixes.
6. Claims from this prompt you could not verify, or dispute.
7. Full references.
