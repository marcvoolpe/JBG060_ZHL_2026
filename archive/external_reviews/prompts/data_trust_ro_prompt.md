# Deep research prompt: can public flood and displacement data, and a flood forecast trained on them, be trusted for county-level anticipatory action in South Sudan?

## Your role

You are an independent reviewer. Evaluate the research objective below against (a) published and grey literature and (b) the data limitations described in this prompt. You are not asked to improve the project's prospects or to be encouraging. "Proceed", "proceed with changes", "reframe" and "do not proceed" are all acceptable conclusions. Reach whichever one the evidence supports.

Ground rules:

1. Cite a source for every factual claim about literature, datasets, organisations or programmes (author, year, title, and a link or DOI; page numbers where possible). If you cannot find a source, write "not verified".
2. Keep three kinds of statement apart:
   - facts from sources;
   - facts stated in this prompt (treat these as the project team's claims, and check them against public documentation where you can);
   - your own inference.
3. Do not invent datasets, variables, resolutions or years of coverage. If you are unsure whether a dataset exists in the form needed, say so.
4. Do not assume a method is feasible because it is standard. Check it against the sample sizes given here.
5. Where evidence conflicts, present both sides. Avoid persuasive or promotional language, and do not soften criticism or inflate strengths.
6. The team measured several of the quantities reported below and designed the objective after seeing them. Treat the numbers as claims that could be wrong, and consider whether the sequence of events could bias the objective (see "History").

Out of scope: redesigning the team's other project strands (access loss, displacement modelling, trigger design), except where they depend on the data this objective evaluates.

## Context

- **Project.** A student data science capstone (TU Eindhoven, course JBG060). About four weeks remain; a separate group essay on social, legal and ethical aspects is due on 25 October 2026. Country: South Sudan. Spatial unit: county (admin2).
- **Stakeholders.** ZOA, a Dutch NGO working on food security and livelihoods, and Zero Hunger Lab (a university research partner). In a Q&A in September 2026, the stakeholders said:
  - They have no experience yet with anticipatory action or with data. Their stated starting needs are "a) understand risks associated with data used" and "b) help us understand flood dynamics better".
  - ZOA works along the Lol river in Northern Bahr el Ghazal and in flood-prone areas of Bor South county. It follows a locally led approach, makes decisions at community level, and prefers more spatial detail.
  - No decision is taken solely on the basis of a model. AA proposals are written locally with communities, approved by ZOA headquarters, and funded through competitive project calls.
  - Required implementation time: 3 days minimum, 10 days sufficient, 14 days a robust upper bound.
  - Priority impact in the active region: harvest failure due to flooding. They also target displaced people and returnees, host communities and pastoralists, and allocate aid by exposure, vulnerability and coping capacity. Displacement and conflict data inform vulnerability and exposure.
  - Results must be interpretable and transparent ("why this finding, at what certainty?"). Simple and interpretable is preferred over complex and black-box. A rigorous answer to a small sub-problem is preferred to a superficial answer to the full problem.
  - Listed as disappointing outcomes: not improving understanding of flood dynamics; non-interpretable or non-nuanced results; information not relevant to local decision-making.
  - Zero Hunger Lab ranked the value of possible outcomes as: 1. understanding the conditions associated with flooding; 2. identifying potential flood precursors; 3. investigating whether precursors provide useful early warning.
- **Team context.** Other strands of the project forecast flood extent and duration (a ConvLSTM on satellite flood masks, and a seasonal outlook from upstream lake levels), estimate loss of road access, relate displacement to flood severity, and design triggers.

## History (disclosed so you can judge possible bias)

The team first proposed a different objective: does a season's observed flood severity explain within-county, year-to-year variation in new flood displacement, beyond persistent county differences, 2021–2025? Before testing it, they pre-registered a go/no-go audit with binding kill criteria and kept the severity–displacement association blinded.

The audit returned NO-GO. A simulation using the real panel skeleton found that the design could not detect a true within-county correlation of 0.35 with 80% power (details below). The within-county association was never computed.

The objective below was then proposed as the fallback that the pre-registered plan had named in advance ("measurement validity of public flood-impact data"), and it was extended to include the team's flood forecast. Consider whether this history makes the new objective a post-hoc reframing of a negative result, and whether that matters for its value.

## The research objective (as proposed)

> The objective of this project is to evaluate how reliably public satellite and humanitarian data measure flood severity and flood displacement in South Sudan (June–December 2021–2025), and how far a flood forecast trained on these data can be trusted. Each dataset is compared with an independent reference, and the team's ConvLSTM forecast with persistence and climatology, using detection rate, within-county reliability, change-based F1 by flood stage and season, and minimum detectable effects. The results are intended to support ZOA and ZHL with a risk profile of the data and the forecast: which information is reliable enough for which decision, at what lead time and with what certainty.

Supporting objectives, as proposed:

1. **Impact data.** How often do displacement records exist when large floods occur? How well do sources agree within counties? What is the smallest flood effect they could confirm? This part is largely done (see the facts below).
2. **Flood data and the forecast.** How reliable are the flood masks, and when in the season do they see water? Does the ConvLSTM beat persistence on new or expanding water at its true lead time, by season? Check against Sentinel-1 radar on a sample of county-seasons.
3. **Decision table.** For ZOA, which information is usable for which decision (county ranking, seasonal outlook, in-season trigger), at which lead time and spatial scale.

The course asks for one research objective. Supporting objectives are allowed only if each contributes directly to the main objective and does not introduce a separate approach, outcome or stakeholder need.

## Data facts, as measured by the project team (please verify where possible)

### Flood masks (NASA MODIS/VIIRS global flood product, course files)

- About 232 m grid, daily detections, 2000–2025, MODIS tiles h20v08 and h21v08 only (nothing north of 10°N). 71 of 79 counties have at least 95% of their area inside the tiles.
- Two classes:
  - "recurring": inside monthly masks of pixels flooded in at least 7 of the 22 years 2003–2024;
  - "unusual": all other detected flood water.

  The recurring label is therefore defined partly with future years. The permanent-water reference is not in the files, and `cloud_frac` is 0 everywhere, so there is no record of how often each pixel was actually observed.
- **Seasonal visibility, 2021–2025, nationally.**
  - Unusual-class detections (pixel-days) are concentrated in November–February; July–September holds about 7% of the annual total.
  - In IOM DTM Event Tracking, 86% of flood-displaced people in the same years were recorded with an event start in July–October.
  - For the median county-season, 4% of June–December detections fall in July–September. The spread is wide: some Northern Bahr el Ghazal county-seasons have about 40%.
- **Split-half reliability.** Severity per county-season is log(1 + km² × dekads flooded), unusual class, June–December. Its within-county, two-way-residualised split-half reliability (odd vs even dekads, Spearman–Brown corrected) is 0.91. The team treats this as a ceiling, because alternate dekads share the same flood and the same cloud regime.
- **Agreement with ERA5 June–December precipitation, within county.** Spearman +0.15 for 2021–2025, but −0.11 over 2001–2025 (95% CI excludes zero). Much Sudd flooding is river-fed rather than locally rain-fed.
- Tile × season effects explain 2.3% of within-county severity variance.
- Detected flood volume rose sharply after 2019. A teammate's analysis attributes this to a regime shift in the Sudd; the team has not separated real change from product change.

### IOM DTM Event Tracking (ET), 2021–2025

- **Record structure.** One row is one group arriving at one site, from one origin, with one trigger. Totals from one episode are often split evenly across sites.
- **What counts as flood displacement.** IDPs, with the movement trigger matching "flood", or an "other" trigger whose free text mentions flood or rain.
- **Flood rows and people by file year:**

  | File year | Rows | People |
  |---|---|---|
  | 2021 | 417 | 534,626 |
  | 2022 | 469 | 416,639 |
  | 2023 | 60 | 27,613 |
  | 2024 | 386 | 359,167 |
  | 2025 | 171 | 241,584 |

- **Origin.** The origin county pcode is valid for at least 99.5% of flood people. The origin equals the event county for 92–100% of people, depending on the year.
- **Recording rule.** ET records moves "over 50 households", and the IOM readme states it "cannot guarantee comprehensive coverage".
- **2023.** 579 rows are "Forced return" (575 of them returnees from Sudan or Ethiopia). Only 4 of the 71 counties have any flood displacement recorded in June–December 2023. The reason is unconfirmed; questions have been drafted for IOM.
- **2025.** The 2025 file ends in November, and there is no December 2025 in any file.
- **Panel.** Usable June–December seasons are 2021, 2022, 2024 and 2025. 47 of 71 counties have a non-constant outcome across them, and 24 never record flood displacement.
- **Coding choice.** A county-season with no ET record is coded as 0 displaced.

### Detection and agreement (team's measurements)

- **Detection against OCHA.** Among county-seasons where OCHA reports at least 10,000 people affected by floods (OCHA files for 2021, 2022, 2024 and 2025; n = 115), 61.7% have any ET flood record from that origin county (Wilson 95% CI 52.6–70.1%). By season: 52%, 60%, 77% and 54%. OCHA "affected" is not the same as "displaced".
- **Detection against Mobility Tracking.** Among county-cohorts with at least 1,000 disaster-displaced arrivals in the first Mobility Tracking round after the season (n = 136, 2021–2024), 52.2% have any ET flood record. For 2023 the figure is 15%. Mobility Tracking counts a stock of people still present, by host county, for all disaster types.
- **ET–OCHA agreement.** The within-county correlation (two-way fixed effects on log(1 + x)) is r = 0.11, county bootstrap 95% CI −0.18 to 0.40 (n = 133 county-seasons, 48 counties). OCHA snapshots were stacked across years for this check.
- **ET split-half.** A random split of ET rows gives within-county reliability of 0.87 (Spearman–Brown). The team treats this as inflated, because one episode spans many rows.
- **Mobility Tracking test-retest.** The same arrival cohort counted in later rounds agrees within county at only 0.00–0.49.
- **Example county (Aweil Centre, Northern Bahr el Ghazal).**

  | Season | ET flood displacement (origin) | OCHA affected | MT first-round disaster arrivals |
  |---|---|---|---|
  | 2021 | 15,986 | 1,800 | 1,565 |
  | 2022 | 0 | 45,288 | 318 |
  | 2023 | 0 | not reported | 175 |
  | 2024 | 0 | 48,864 | 3,023 |
  | 2025 | 0 | not assessed | – |

  In June–December 2022 and 2024, ET has no record of any kind located in Aweil Centre.

### Power simulation (team's design; please scrutinise the assumptions)

- **Model.** A hurdle model on the real 71-county × 4-season skeleton:
  - true severity is related to observed severity through an assumed reliability Rx;
  - displacement occurs when a latent index crosses a threshold, and log size depends partly on the index (share κ = 0.5);
  - moves under 300 people are unrecorded;
  - each displacement is recorded with probability π = 0.617 (the OCHA-based detection rate), with county heterogeneity rank-matched to how often each county appears in ET;
  - county and season effects are matched to outcome marginals only.
- **Estimator.** TWFE with CR2 standard errors and Bell–McCaffrey degrees of freedom. The false-positive rate under a null with correlated shocks is 0.057.
- **Results:**
  - Detection alone caps the outcome's reliability (the squared within-county correlation between recorded and true displacement) at about 0.24.
  - At Rx = 0.6, power is 0.34 at a true within-county correlation of 0.35, and 0.70 at 0.54, the highest correlation the model could reach.
  - At Rx = 0.8, the minimum detectable correlation is about 0.47.
- **Controls:**
  - Between-county Spearman of county-mean severity against county-mean ET displacement is 0.68.
  - The within-county association of severity with ET non-flood records is r = 0.087 (95% CI −0.05 to 0.23).

### The flood forecast (from the team's internal brief; please treat as unverified)

- **Model.** A ConvLSTM predicting 3-class dekadal flood labels (dry, recurring, unusual) on 32×32 patches, over a "three-state corridor". The brief's examples are all in Unity and Jonglei and do not mention the Lol river.
- **Lead time is unresolved.** The model's report describes the output both as "6 dekads ahead" and as "the next dekad".
- **Against persistence:**
  - At a one-dekad lead, unusual-class F1 is 0.846 for the model against 0.842 for persistence (2023), 0.772 vs 0.767 (2025), and 0.519 vs 0.506 (2019).
  - If the lead is six dekads, persistence at that lead scores 0.716 (2023) and 0.636 (2025).
- **Evaluation weaknesses.** Test years sit between training years. The original report compared against climatology only and quoted 99.8% overall accuracy.

## What to evaluate

### A. Novelty and prior work

1. Has the reliability of these specific sources been assessed for South Sudan or comparable settings? Consider IOM DTM (Event Tracking, Mobility Tracking), OCHA flood figures, and MODIS/VIIRS flood products under persistent cloud. Check IOM's own methodology documents, IDMC, REACH, academic validation studies, and flood product validation papers. Summarise designs and findings, with citations.
2. What does the literature say about validating impact-based forecasts or anticipatory action triggers when impact data are incomplete? Consider the Red Cross Red Crescent Climate Centre, the 510 initiative, WFP, the OCHA Centre for Humanitarian Data, and academic work. Is this objective's contribution new, or a restatement of known limitations?
3. Is persistence the accepted minimum baseline for short-lead inundation forecasting (for example, the INFLOW-AI work on the White Nile)? How do published studies score change (onset, expansion, recession) rather than state?

### B. Validity of the evaluation design

4. Are the proposed references independent of the data they check? Consider whether OCHA figures may draw on DTM data, and whether assessments are targeted using satellite maps (circularity).
5. Is "share of large OCHA-reported floods with any ET record" a fair measure of ET's recording probability? Which way would "affected ≠ displaced", OCHA's own gaps, and cross-county displacement bias it?
6. Are odd–even dekad split-half reliability and ERA5 rainfall agreement meaningful checks of flood mask reliability in a river-fed wetland? What would a valid independent reference be for 2021–2025? Consider Sentinel-1–based products such as Copernicus Global Flood Monitoring, WFP masks, and VIIRS. Are they freely available at county scale, and how large would a check sample need to be?

### C. Analytical soundness

7. Which simulation assumptions drive the result that outcome reliability is capped near 0.24 (π, the 300-person threshold, κ, rank-matched detection heterogeneity)? Would reasonable alternatives change the conclusion that the within-county design detects only large effects? Recommend sensitivity checks.
8. Is TWFE with CR2 and 71 clusters appropriate for the within-county reliability estimates? Is a correlation-based "reliability" definition appropriate for zero-inflated count data, or would another measure (for example agreement on the occurrence of any displacement) be more informative?
9. For the forecast, is the proposed evaluation adequate for the claim "how far the forecast can be trusted"? The proposal covers persistence and climatology baselines, change-based F1, season-stratified skill, and a Sentinel-1 check. What else is needed, given the look-ahead in the recurring label and the unresolved lead time?

### D. Coherence of the objective

10. Does including the forecast evaluation keep one objective with one outcome, as the course requires, or does it add a second approach? Would the objective be stronger with or without it?
11. Given the history, is this a substantive research objective, or a negative result presented as one? What would make it one or the other?

### E. Decision relevance

12. For ZOA (two operating areas, community-level decisions, 3–14 day lead times, harvest failure as the priority impact) and for ZHL's ranked priorities, which parts of a "data and forecast risk profile" would change a decision, and which would not?
13. The objective focuses on displacement and flood extent, not crop loss. Does this weaken its relevance? Would adding crop or cropland data (the stakeholders suspect cropland datasets undercount farmland) help, or overload the scope?
14. Is county level too coarse to be useful to an organisation that decides at community level? Or is showing that county-level public data are already weak itself useful?

### F. Representation and ethics (brief)

15. Does the literature on humanitarian data (representation, exclusion, accountability to donors) support the concern that recording gaps can bias targeting or trigger validation, for example when "no record" is treated as "no displacement"? Cite specific work. Do not speculate beyond the sources.

### G. Verdict

16. Score each criterion in the rubric below from 1 to 5, with one paragraph of justification each.
17. Give an overall recommendation: proceed as proposed, proceed with specific changes, reframe, or do not proceed. State the single most important change, and what evidence would reverse your recommendation.
18. List any claims in this prompt that you could not verify or believe are wrong.

## Rubric (score 1–5)

| Criterion | 1 | 3 | 5 |
|---|---|---|---|
| Novelty | Already answered for these sources in South Sudan | Answered elsewhere or in part | Open, with no close precedent |
| Validity of references and metrics | The references are not independent, or the metrics cannot measure reliability | Usable with major caveats | Valid with minor caveats |
| Analytical soundness | Key conclusions depend on arbitrary assumptions | Conclusions hold under some alternatives | Conclusions robust to reasonable alternatives |
| Robustness to bias and circularity | A known bias or shared source would likely produce the findings regardless of the truth | Main biases can be bounded | Main biases removed or tightly bounded |
| Coherence of the objective | Two or more separate projects under one sentence | One objective with loosely attached parts | One objective; every part serves it |
| Decision relevance | No plausible finding would change a stakeholder decision | Some findings would inform a decision | Each finding maps to a clear decision |
| Feasibility in remaining time | Infeasible | Feasible only if narrowed | Comfortably feasible |

## Output format

1. Summary verdict (150 words at most).
2. Scores table: criterion | score | one-line reason.
3. Findings for sections A–F, with citations.
4. Evidence table: claim | source | how directly it applies (direct / analogous / indirect).
5. Recommended changes, ranked, each with the problem it fixes.
6. Claims from this prompt you could not verify, or dispute.
7. Full references.
