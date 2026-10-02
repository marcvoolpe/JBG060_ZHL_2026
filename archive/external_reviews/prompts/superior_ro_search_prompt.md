# Prompt: find a research objective that is demonstrably better than the current candidates, or show that none exists

## Your role

You are an independent research designer with read access to this repository and to the internet. Your task is to search for a research objective (RO) for a student capstone project that beats the two current candidates on explicit criteria. You may also conclude that no such RO exists, and that conclusion is acceptable. You have no stake in any candidate. The two baselines were drafted by an AI assistant working with one team member, so do not assume they are good, and do not assume the team's analyses are correct.

Ground rules:

1. **Evidence.** Cite a source for every factual claim:
   - repository claims: file path, plus line, table or section;
   - internet claims: author, year, title, link or DOI, and page numbers where possible.

   If you cannot verify a claim, write "not verified". Follow the course rule that "one source = no source" for any load-bearing claim.
2. **Kinds of statement.** Keep apart facts from files, facts from external sources, team claims you could not reproduce, and your own inference.
3. **Data.** Do not invent datasets, variables, resolutions, coverage periods or access routes. For any dataset not already in the repository, verify online that it exists, covers South Sudan for the needed years, is free, and can be accessed in days, not weeks. Give the access route.
4. **Methods.** Do not assume a method is feasible because it is standard. Check it against the real sample sizes, spatial units and time available.
5. **Blinding.** Do not compute the within-county association between flood severity and displacement. A pre-registered test of it returned NO-GO and stays unrun (`eda/SESSION_E_HYPOTHESES.md`, `eda/STAGE34_GATE.md`). Exploratory data checks are allowed only where they do not reveal that association.
6. **SLE essay.** Do not write text for it. The course forbids AI use for SLE literature review, reading and writing (`course_content/SLE_aspects_capstone_extracted.md`, section 1). You may point to which SLE aspect an RO would support and which listed sources relate to it.
7. **Tone.** Write plainly. Avoid promotional language. Report weaknesses of every candidate, including your own proposal.

## Files to read first (in this order)

1. `good_research_objective.txt`: the course template (Action, Outcome, Scope, Inputs, Evaluation with baseline and metrics, Purpose). There must be one objective; supporting objectives may not introduce a separate approach, outcome or stakeholder need.
2. `course_content/Stakeholder Q&A 2 Slides.pdf`: the stakeholder answers (ZOA and Zero Hunger Lab, 21 September 2026). Cite slide numbers.
3. `course_content/SLE_aspects_capstone_extracted.md`: the SLE lecture content. Cite section numbers and lecture pages.
4. `eda/HANDOFF.md`: what was built, which findings held up, and which ideas were rejected and why. Note that `eda/CAPSTONE_AA_SYNTHESIS.md` is marked superseded and over-optimistic.
5. `eda/SESSION_E_HYPOTHESES.md` and `eda/STAGE31_GATE.md` to `eda/STAGE34_GATE.md`: the pre-registered verification and its NO-GO.
6. `external_deep_research/Independent Expert Review  South Sudan Flood and Displacement Data for Anticipatory Action.md` and `... Action 2.md`: two independent reviews of the previous RO. They disagree in places; treat each as evidence to check, not as authority. Review 2 is in Spanish.
7. The other files in `external_deep_research/`: earlier reviews of rejected directions (duplication with WFP ADAM, Flood-PROOFS, REACH; lead-time and decision mismatches), and `within_county_deep_research_1.md`.
8. `eda/SESSION_A_CLOSEOUT.md` to `eda/SESSION_D_CLOSEOUT.md`, `eda/AA_DATA_ROLES.md`, `eda/DEFERRED_DATASETS.md`, and `deliverables/*.md`.
9. Outputs in `eda/outputs/impact_eda/`, especially `stage32_*`, `stage33_*` and `stage34_*`.
10. The data actually available: `data/` (external) and `data-JBG060-2026/data-JBG060-2026/` (the course pack). Check what each folder contains before proposing its use.

## Context summary (team claims; verify against the files)

- **Project.** A TU Eindhoven data science capstone (JBG060). Country: South Sudan. About four weeks remain; the group SLE essay (2,500 words, 40% of the grade, one SLE aspect) is due on 25 October 2026.
- **Team strands.** Other members work on a ConvLSTM flood forecast (also described as reusing INFLOW-AI), a seasonal outlook from lake levels, road-access loss, and displacement. The team needs one group RO.
- **Stakeholders.**
  - ZOA works along the Lol river in Northern Bahr el Ghazal and in Bor South. It makes decisions at community level and needs 3–14 days of lead time. Its priority impact is harvest failure, but it also targets displaced people, returnees, host communities and pastoralists.
  - Both stakeholders want transparent, interpretable results, with the certainty of each finding stated, and prefer a rigorous small sub-problem.
  - Their first stated need is to understand the risks of the data used. Their second is to understand flood dynamics.
  - ZHL ranks the value of outcomes as: flood conditions, then precursors, then early warning.
  - ZOA phrases its own trigger as "with at least x% certainty, flood will take place which inundates cropland resulting in at least y% of total yield reduction" (slide 31).
- **Limitations found so far:**
  - **Displacement data.** IOM Event Tracking has no flood record in 38% of county-seasons where OCHA reports ≥ 10,000 affected. OCHA and Event Tracking are not independent, and "no record" is not "no displacement". Within-county agreement between Event Tracking and OCHA is r = 0.11.
  - **Year-to-year impact.** The within-county severity–displacement test would detect only large effects under the simulated recording model. The reviewers note that this conclusion depends on the simulation's assumptions.
  - **Crop impact.** Annual flood extent shows no relation with FEWS harvested area. The only cropland layer in the pack is a static ASAP mask at about 500 m, and the stakeholders suspect cropland is undercounted.
  - **Flood masks.**
    - They are internally consistent (split-half 0.91), but that is not accuracy.
    - Detections concentrate in November–February. The reason for low detection in July–September (cloud, or real hydrological timing) is unresolved.
    - The "recurring" class is defined with 2003–2024, so it uses future years.
    - Detected volume jumps after 2020. It is unclear whether that is hydrology or a product change, and the product's provenance is unclear.
    - In Aweil Centre and Aweil North (Lol river), the masks record almost no flooding (2–33 and 0–125 km² × dekads per June–December season, 2021–2025). Yet OCHA reports 45,288 and 48,864 people affected in Aweil Centre in 2022 and 2024.
  - **Hydrology.**
    - Lagged county-month correlations with upstream signals are weak.
    - At season scale, January Lake Victoria levels predicted the national flood peak with leave-one-year-out skill 0.64 in a teammate's analysis. That result holds only when post-2019 years are in the training data.
    - The Lol is a separate basin from the lake-driven Sudd.
  - **Forecast.** The ConvLSTM ties with persistence at a one-dekad lead; its lead time is unresolved; it covers a corridor in Unity and Jonglei.
  - **Other data.** Conflict data are sparse, and there is no ACLED. Exposure-coupled county rankings duplicate existing tools.

## The two baselines to beat

**Baseline v2 (fitness-for-purpose audit):**

> The objective of this project is to evaluate whether public flood and displacement data are fit for anticipatory-action decisions in South Sudan, for the 71 counties the flood masks cover, June–December 2021–2025, with ZOA's areas (the Aweil counties along the Lol and Bor South) as case studies. The data are NASA MODIS-based flood masks, IOM DTM Event and Mobility Tracking, and OCHA flood reports.
>
> Flood masks are compared with date-matched Sentinel-1 radar flood maps (Copernicus GFM) on a stratified sample of county-dates. The displacement sources, which have no independent ground truth, are compared with each other as incomplete recording systems, and the common practice of treating "no record" as zero is compared with treating it as unobserved.
>
> Each source is judged for four uses (detecting that an event happened, ranking counties, sizing events, tracking year-to-year change) using occurrence agreement, rank correlation, magnitude error and within-county association, with minimum detectable effects reported across a pre-specified range of recording assumptions.
>
> The results are intended to give ZOA and ZHL a data-risk profile: for each source and use, whether the data are sufficient at county level, with what certainty, and what their gaps mean for any forecast or trigger built on them.

**Baseline A (flooded cropland in ZOA's areas):**

> Evaluate how reliably public satellite data can estimate cropland inundated during the growing season in ZOA's counties (the Aweil counties and Bor South), 2021–2025, by combining the optical flood masks or Sentinel-1 radar with three cropland maps (the course's ASAP mask, ESA WorldCover, ESA WorldCereal). The spread of estimates across sensors and maps is the measure of uncertainty, compared against the current optical-mask plus ASAP estimate. The purpose is to give ZOA the "x% certainty" part of its own trigger.

Known weaknesses to check:

- **v2** is centred on displacement rather than harvest, works at county level, and has three strands.
- **A** has no reference for cropland (only map-to-map agreement). C-band radar may miss water under standing crops. Short rain-driven flooding may fall between 12-day Sentinel-1 passes. A also depends entirely on Earth Engine or GFM access.

## Evaluation criteria

Score every RO, including both baselines, from 1 to 5 on each criterion, with one justified paragraph per score. Score the baselines **before** generating new candidates, and do not revise those scores afterwards unless you find a factual error, which you must then report.

| # | Criterion | 1 | 3 | 5 |
|---|---|---|---|---|
| 1 | Stakeholder alignment | Addresses no stated need, area or lead time | Addresses one stated need, partly | Addresses a stated priority, in ZOA's areas, in terms they used, and every finding maps to a decision (cite slides) |
| 2 | SLE relevance | No SLE aspect follows from the technical choices | One aspect, loosely linked | The RO's own technical choices raise one clear SLE aspect covered by the lectures, with prescribed literature available (cite sections) |
| 3 | Novelty | Already answered for South Sudan | Answered elsewhere or in part | Open, with no close precedent (search exhaustively) |
| 4 | Validity of references and metrics | No credible reference; metrics cannot measure the outcome | Usable with major caveats | A physically or institutionally independent reference exists; metrics match the outcome |
| 5 | Analytical soundness | Conclusions depend on arbitrary assumptions | Hold under some alternatives | Robust to reasonable alternatives; sensitivity planned |
| 6 | Robustness to bias and circularity | A known bias would produce the result regardless of the truth | Main biases can be bounded | Main biases removed or tightly bounded |
| 7 | Coherence | Several projects under one sentence | One objective with loosely attached parts | One outcome; every supporting objective serves it |
| 8 | Feasibility in about 4 weeks | Infeasible | Feasible only if narrowed, or depends on an unverified access route | Comfortably feasible with data in hand or verified free access, with a fallback if a step fails |
| 9 | Informativeness of a negative result | A null or failure teaches nothing | Partly informative | Every outcome, including failure, gives ZOA/ZHL a usable finding |

**Rule for "superior".** A candidate is superior only if, against **each** baseline:

- it scores at least as high on criteria 1, 2, 7 and 8;
- no criterion is lower by more than 1 point;
- its total is at least 3 points higher.

If no candidate meets this rule, say so plainly and recommend whichever baseline scores higher, with reasons.

## Process

1. **Verify the ground.**
   - Reproduce or check the key team claims listed above from the files. Flag any that are wrong.
   - List the datasets actually in the repository, with coverage and grain.
   - Search online for other free datasets that could matter, and verify access for each. Candidates include Sentinel-1/GFM; WorldCover, WorldCereal and Dynamic World; CHIRPS, TAMSAT and soil moisture; GloFAS; FAO and WFP products; IOM DTM products beyond those in the repository; river gauges on the Lol or at Mongalla; the INFLOW-AI release; and crop-type labels such as Rustowicz et al. 2020.
2. **Search the literature exhaustively** for work on:
   - satellite flood mapping validation in South Sudan and the Sudd;
   - flooded-cropland and flooded-vegetation detection with SAR;
   - cropland map accuracy for smallholder Africa;
   - flood drivers of the Bahr el Ghazal and Lol basins;
   - anticipatory action for floods in South Sudan (OCHA Centre for Humanitarian Data, the IFRC EAP, WFP, FAO, the Anticipation Hub, Eason-Calabria);
   - impact-data gaps in anticipatory action;
   - the SLE sources listed in section 22 of the SLE file.

   Record precedents that would lower the novelty of any candidate.
3. **Generate at least eight distinct candidate ROs.** Draw on:
   - the limitations above, including ROs that turn a limitation into the object of study;
   - the stakeholder questions on slides 5 and 13–43;
   - the team strands.

   Include at least one candidate outside flood-displacement framing (for example duration, access, livelihoods, or pastoral mobility), provided its data are verified.
4. **Screen.** Drop any candidate that violates the template, needs unverified data, requires the blinded association, or duplicates existing tools. State the reason for each drop.
5. **Deepen the top three.** For each, give:
   - the exact data;
   - the evaluation design, with a baseline and metrics;
   - sample sizes;
   - a week-by-week plan;
   - kill criteria;
   - what each possible result would mean for ZOA and ZHL;
   - the SLE aspect it raises.
6. **Critique adversarially.** For each of the top three, write the strongest case against it, as a hostile reviewer would. Then revise it or drop it.
7. **Score and decide** using the rubric and the superiority rule. Show the scores table for both baselines and the finalists.

## Output format

1. **Verdict** (at most 150 words): a superior RO was found or not, and which RO to pursue.
2. **Verification of team claims**: claim | status | source.
3. **Data inventory**: dataset | in repository or external | coverage | grain | access verified | limitation.
4. **Literature and precedent findings**, with citations.
5. **Candidate list**: all candidates, with the screening decision and reason for each.
6. **Finalists in detail** (process step 5), in the template's final RO form:
   > The objective of this project is to [develop/evaluate/compare] a [model, method or analytical framework] for [specific outcome] in [geographic and temporal scope], using [data or predictor groups]. The proposed approach will be compared with [baseline or alternative method] and evaluated using [performance metrics]. The results are intended to support [specific stakeholder or decision context] by providing [defined output, insight or lead time].

   Add supporting objectives only where they meet the template rule.
7. **Scores table**: RO | the nine criteria | total, and whether the superiority rule is met against each baseline.
8. **Stakeholder mapping** for the recommended RO: slide | what the stakeholder said | how the RO responds | fit (direct / partial / gap).
9. **SLE mapping** for the recommended RO: technical choice | SLE aspect | lecture and section | relevant listed sources. No essay text.
10. **Risks and kill criteria**, and what to confirm with ZOA/ZHL or instructors before committing.
11. **Claims you could not verify**, and full references.
