# Prompt: can a flood forecast × verified cropland data give anticipatory-action advice whose limits are set by a prior uncertainty test?

## Your role

You are an independent expert reviewer in flood forecasting, satellite cropland and flood mapping, and humanitarian anticipatory action (AA). A student team is considering the research idea described below. Your job:

1. Find out what AA advice this idea can honestly deliver to the stakeholders in about four weeks.
2. Judge whether it holds together as one research objective (RO).
3. Say what it would take for the advice to be truly bounded by a measured uncertainty, rather than decorated with one.

You may conclude that the idea should be narrowed, changed or dropped. It was drafted by an AI assistant working with one team member. Do not assume it is good, and do not assume the team's numbers are right.

Ground rules:
1. **Evidence.** Cite a source for every factual claim: author, year, title, link or DOI, and page, table or section where possible. If you cannot verify a claim, write "not verified". Load-bearing claims need two independent sources.
2. **Kinds of statement.** Keep apart: facts from external sources, team claims you could not check, and your own inference. Label each one.
3. **Data.** Do not invent datasets, resolutions, lead times, coverage periods or access routes. For any dataset you recommend, check that it exists, covers South Sudan for 2021–2025, is free, and can be obtained in days.
4. **Methods.** Do not assume a method is feasible because it is standard. Check it against the real sample sizes, forecast skill, spatial units and four-week timeline described here.
5. **Plain language.** Define every technical term the first time you use it (for example: lead time, persistence baseline, producer's accuracy, reliability diagram, cost–loss ratio). Give one concrete example for each key idea.
6. **Tone.** Report weaknesses and strengths with equal care. No promotional language.

## The idea to test

The idea has two linked steps.

**Step 1: an uncertainty test in ZOA's areas.** Measure how reliable the public data are in the five Aweil counties (Northern Bahr el Ghazal, along the Lol river) and in Bor South (Jonglei):
- **Cropland data:** how much cultivated land each public cropland map misses or wrongly includes. The check uses a stratified random sample of points. Each point is labelled **manually** by two team members working independently, from Sentinel-2 time series and high-resolution imagery. They follow a written labelling rubric that is frozen before labelling starts, and it sets:
  - the unit: a 20 × 20 m box;
  - the evidence to check, in order;
  - the labels: cropland / not cropland / fallow-or-uncertain / cannot judge;
  - a confidence score for every label.
  Labellers do not see the maps' values. A third person settles disagreements, and agreement between labellers is reported. This follows the "response design" in Olofsson et al. (2014).
- **Flood data:** how often the optical flood masks agree with Sentinel-1 radar, month by month, and whether disagreements happen under cloud. This part is **computed, not labelled by hand**. Radar and masks are compared as two imperfect sensors; neither is treated as the truth.

The outputs are error rates with confidence intervals, for example "map X misses 40–70% of cropland in Aweil" or "the masks record 10–30% of the flooding radar sees in July–September".

**Step 2: forecast × cropland → AA advice, bounded by step 1.** Overlay the group's flood forecast (described below) on cropland data to produce advice for anticipatory action, for example:
- which areas or communities are likely to have farmland flooded;
- how much;
- how early;
- which action type this supports.

The key rule: **the advice may never claim more precision than step 1 allows.** For example, if cropland maps miss half the fields, a forecast of "2,000 ha of cropland flooded" must be reported as a range, or turned into a coarser statement ("high / medium / low exposure"). If the forecast or the flood data cannot be trusted in a given month or area, no advice is given there, and that is stated.

**The AA type is not yet decided.** Part of your job is to find which action types, if any, the data and forecast can support.

## Context (team claims unless marked; verify what you can)

### Project
- TU Eindhoven data-science capstone (JBG060), South Sudan.
- About four weeks remain (27 Sep – 25 Oct 2026), with a group essay in parallel. The team has four to six members.
- The course template requires **one** RO. Supporting objectives may not introduce a separate approach, outcome or stakeholder need. Template form:

  > The objective of this project is to [develop/evaluate/compare] a [model, method or analytical framework] for [specific outcome] in [geographic and temporal scope], using [data or predictor groups]. The proposed approach will be compared with [baseline or alternative method] and evaluated using [performance metrics]. The results are intended to support [specific stakeholder or decision context] by providing [defined output, insight or lead time].

### Stakeholders (Q&A with ZOA and Zero Hunger Lab, 21 Sep 2026; slide numbers in brackets)
- **Where ZOA works:** along the Lol river in Northern Bahr el Ghazal, and in flood-prone Bor South. It is a locally led NGO: decisions are made at community level, with communities, and "no decision taken solely based on a model" [3, 4].
- **Starting point:** no experience yet with AA or with data. The first need is to "understand risks associated with data used"; the second is to understand flood dynamics [2].
- **What they want to understand:** what causes floods locally, the local impact, how drivers differ per impact, at what time scale prediction is possible, and how reliable it is. A rigorous answer to a small sub-problem is preferred, and every finding should state its certainty [5].
- **Impact:** the priority impact in the active region is harvest failure from flooding, but impact on all groups matters [6]. The team has since been told harvest is not binding for grading.
- **Actions and timing:** the choice of action depends on exposure, vulnerability and anticipated impact. An action is only included if it can mitigate the impact, for example migrating cattle. Implementation time: 14 days is definitely enough, 10 days suffices, 3 days is the minimum [8].
- **Errors:** misses and false alarms both have costs, for example early harvesting causing reduced yield. They want the reliability and risk transferred to them so they can decide the trade-off [10, 11].
- **Specific actions:**
  - Before moving livestock: an inundation prediction, whether cattle can be moved to a safe location, food access, and waterborne-disease risk [13].
  - Cash contributions for cropland damage: "Yes" [15].
- **Crop damage:** "Given a flood, we are estimating the crop damage" is relevant, and combining it with flood prediction "improves our knowledge" [17]. Most relevant damage measures are harvest loss per household in kg and change in food insecurity [20].
- **Detail and certainty:**
  - "The more detailed, the better" [21].
  - What they need is "what damage is expected to take place where, when, and how certain are you?" [23].
  - Local staff must be able to operate and interpret the system [24].
- **Logistics:** last-mile distribution via roads or boats, not WFP-scale operations [25]. No warehouses or distribution points [35].
- **Duration** of inundation matters [26].
- **Trigger wording:** "with at least x% certainty, flood will take place which inundates cropland resulting in at least y% of total yield reduction" [31].
- **Information 14 days before a major flood:** inundation duration and extent, the effect on crop yield and on access to critical infrastructure, "with what reliability" [32].
- **Farmland data:** "the dataset might not capture agricultural land fully" [33].
- **Trigger rules:** triggers must be transparent and interpretable [40]. Multiple triggers for different actions and time frames would be useful [42]. Repeat floods matter [43].
- **ZHL's ranking of outcomes:** understanding flood conditions, then precursors, then early warning [28].

### The group's flood forecast model (team claims; the code is not public)
- A ConvLSTM (a neural network for image sequences) inspired by INFLOW-AI. It outputs a flood prediction per ~252 m pixel per dekad (10-day period).
- **Lead time is unresolved.** One document says 6 dekads (about 2 months) ahead; another says "the next dekad". At a one-dekad lead, the model scores about the same as persistence, meaning "next dekad = this dekad". Unusual-flood F1 is 0.846 vs 0.842 in 2023, 0.772 vs 0.767 in 2025, and 0.519 vs 0.506 in 2019.
- **Spatial domain:** trained and evaluated on a corridor in Unity and Jonglei (possibly Upper Nile). It is **not known whether it covers the Aweil counties at all.**
- **Training target:** the course optical flood masks. Their "recurring" class is defined using 2003–2024, so it looks into the future relative to many training years. Test years sit between training years.
- A separate team analysis found that January Lake Victoria levels predicted the national seasonal flood peak (leave-one-year-out skill 0.64), but only when post-2019 years were in the training data. The Lol basin is not fed by the equatorial lakes.

### Data in hand (team claims)
- **Course flood masks:** described as NASA MODIS/VIIRS-based, ~232 m, daily, 2000–2025, "unusual" and "recurring" classes. Only flooded pixel-days are stored, and cloud information was removed by the course loader. Detections cluster in November–December: the median share of June–December detections in July–September is 0.04.
- **Cropland:** the ASAP crop mask v04 (~500 m, fraction per cell, static).
- **Other:** FAO/WFP CFSAM county crop statistics 2011–2024, WorldPop, ERA5 rain and runoff, lake levels, IPC, and IOM DTM and OCHA impact data.

### Findings so far (verify)
1. **ASAP undercounts cropland.** It totals about 407,000 ha nationally, against 1.03–1.18 M ha of CFSAM harvested cereal area; it is below CFSAM in 70 of 77 counties.
2. **The current flooded-cropland estimate is far too low.** Masks × ASAP gives about 3,700 ha flooded nationally for June–November 2022, against CFSAM's 130,000 ha of cultivated land damaged.
3. **The masks miss the flood season in Aweil.** In Aweil Centre they show almost no flooding (2–33 km²·dekads per season, 2021–2025), while OCHA reports 45,288 people affected (2022). Field reports put Aweil flooding in June–September; the masks see mostly November–December.
4. **An earlier independent review of the step-1 design found:**
   - Radar bias runs both ways (missed water under tall crops; false water on bare, smooth soil), so radar is not a reference.
   - In Africa, ASAP is derived from WorldCereal, and Esri and Dynamic World share training data, so the maps are not independent.
   - Digital Earth Africa's 2019 cropland map is the only one validated in a zone that includes South Sudan.
   - Double labelling about 600–900 points takes 80–180 person-hours.
   - Per-county-by-season intervals are not attainable with that sample.
   - FAO field assessments give about 17,700 ha of cereal damaged in Northern Bahr el Ghazal in 2021, and over 15,000 ha affected in 2024.
5. **Existing tools and protocols:**
   - WFP ADAM reports flooded cropland per county (VIIRS/Floodscan × GFSAD30), with no accuracy statement.
   - The IFRC simplified Early Action Protocol sEAP2024SS01 (approved 23 Oct 2025) covers Bor South, Aweil Centre and Aweil East. It triggers when INFLOW-AI forecasts the Sudd inundation to rise more than 5 percentage points within two months.

## Questions to answer

### A. Which AA types exist, and what does each need?
1. **Action types.** List the anticipatory actions for floods that are documented in South Sudan or in comparable settings (the Sahel, East Africa, Bangladesh, and others where evidence is strong), and that fit ZOA's profile: small NGO, community-led, no warehouses, last-mile, 3–14-day implementation. Consider at least:
   - cash transfers;
   - early or protective harvest;
   - livestock moves and vaccination;
   - seed and input protection;
   - dyke and drainage work;
   - community warnings;
   - health and WASH items;
   - reserving land or safe sites.
   For each, find evidence of effect (for example Weiffen et al. on cash in South Sudan; FAO anticipatory action reports; IFRC early action protocols; the Anticipation Hub; Easton-Calabria 2023/2025).
2. **Information needs.** For each action type, what information is required, and how good must it be? State:
   - the lead time needed (days or weeks);
   - the spatial detail needed (county, payam, community, field);
   - the variable needed (flood onset, extent, duration, depth, cropland flooded);
   - the tolerable false-alarm and miss rates, or the cost–loss ratio, if any evidence exists.
3. **"No-regret" and staged options.** Which actions are low-regret, meaning worth doing even if the flood does not come? Which are high-regret, like early harvest reducing yield? How do staged triggers work, for example a seasonal "ready" signal followed by an in-season "set/go" signal? Give documented examples (Kenya, Bangladesh, Nepal, Somalia, Mali, Uganda, South Sudan).

### B. What can the data and the forecast actually deliver?
4. **Forecast skill.** What skill must a flood forecast show before it can support each action type in question 2? For which lead times? Against which baselines: persistence, climatology, and "same dekad last year"? Which metrics show real anticipatory value (for example skill on newly flooded pixels, hit rate and false-alarm ratio, reliability of probabilities)? Cite verification literature, INFLOW-AI (Rapson et al. 2026, doi:10.5194/egusphere-2026-66) and its public review, and GloFAS/Google Flood Hub verification studies.
5. **Coverage.** The model's domain is a Unity–Jonglei corridor. What can be said for Aweil, where the model may not run and the flood regime is rain- and river-fed from the Bahr el Ghazal basin? Is any public forecast skilful there at 3–14 days (GloFAS, Google Flood Hub, ICPAC rainfall forecasts, ECMWF extended range)? If none, is the honest deliverable for Aweil "monitoring and seasonal readiness, no forecast-based trigger"?
6. **Training-label blindness.** A model trained on optical masks that see little July–September flooding learns the recession, not the onset. What does that imply for any advice about crop-season flooding? Can Sentinel-1 or GFM (Copernicus Global Flood Monitoring) be used to re-verify the forecast in July–September within four weeks?
7. **Cropland.** Given published accuracies of cropland maps in Africa (Kerner et al. 2024; WorldCover and WorldCereal validation reports; Digital Earth Africa), which map, if any, is fit to turn "flooded pixels" into "flooded cropland" in Aweil and Bor South?

### C. How should the uncertainty test bound the advice?
8. **Propagating error.** What methods exist for carrying map error and forecast error into an exposure estimate? Consider at least:
   - error-adjusted area estimation (Olofsson et al. 2014);
   - probabilistic exposure (forecast probability × probability that a pixel is cropland);
   - Monte Carlo sampling;
   - confidence classes;
   - "no advice where reliability is below threshold" rules.
   Give precedents in impact-based forecasting: 510 / Netherlands Red Cross, Flood-PROOFS East Africa, WFP ADAM, IFRC impact-based forecasting guidance, the OCHA Centre for Humanitarian Data trigger work.
9. **Setting the bounds.** How should the thresholds be set so the rule is transparent and pre-registered? For example: "give area advice only if cropland producer's accuracy ≥ X and forecast hit rate ≥ Y at that lead time, otherwise give a coarser category or none". Is there literature on setting such minimum-quality rules for triggers?
10. **Combined error.** When both the forecast and the cropland map have large, possibly correlated errors, is a combined interval still meaningful? Or is it better to report the two error sources separately and let ZOA decide (slide 11: "provide us the knowledge such that we can decide this trade-off")?
11. **An example.** Work through one example with plausible numbers. Say a forecast hit rate of 0.6 at one dekad, a false-alarm ratio of 0.4, cropland producer's accuracy of 0.5 and user's accuracy of 0.7. What bounded statement could be given to ZOA for one county? Show the arithmetic and state its assumptions.

### D. Is this one RO, and is it feasible?
12. **Coherence.** Is "uncertainty test → bounded advice" one objective with one outcome (the bounded advice) and step 1 as a supporting objective, or two projects? Propose the strongest single-objective wording that satisfies the template. If it cannot be one RO, say which half to keep.
13. **Feasibility.** In four weeks, with 4–6 people and an essay, is the full chain feasible? Consider the labelling (80–180 person-hours), radar extraction, resolving the forecast's lead time and domain, re-verifying the forecast, and building the advice. What is the minimum viable version? Name the step most likely to fail.
14. **Baselines.** What should the advice be compared with? Possibilities:
    - current practice (masks × ASAP, or ADAM);
    - "same places every year" (flood frequency maps);
    - the IFRC sEAP trigger;
    - "no forecast" (seasonal readiness only).
    Which metrics show that bounded advice is better, or at least more honest?
15. **Novelty.** Check for precedents: studies that deliver forecast-based AA advice with explicit input-data uncertainty bounds in South Sudan or similar settings.

### E. Unit mismatch and analytical soundness
The products work at different grain sizes:
- the manual labels: a 20 m box;
- WorldCover, WorldCereal, Dynamic World and Esri: 10 m;
- ASAP: a 500 m cropland fraction;
- the optical masks: ~232 m;
- the forecast: ~252 m;
- radar: 10–20 m.

The team proposes the following. Critique each point, and say what is missing.
- **Assess each product at its own grain:**
  - point labels against the 10 m maps, at the point;
  - ASAP at area level only: the stratified estimate of cropland area per area or county against ASAP's summed area (fraction × cell area), optionally with a small subsample of ASAP cells labelled as a 3 × 3 grid;
  - radar aggregated to the 232 m mask grid as a flooded fraction per pixel, called "flooded" above a pre-set threshold (0.3, with 0.1 and 0.5 as sensitivities);
  - the forecast and masks compared on the forecast's own 252 m grid.
- **Exposure:** compute flooded cropland at the finest reliable unit, then aggregate to the reporting unit.
- **Reporting:** report only at units the sample supports: pooled per area (Aweil counties; Bor South), with county results descriptive, and no payam results below about 30 reference points.
- **Soundness:**
  - freeze the analysis plan before labelling (thresholds, strata, estimators, stop rules);
  - carry stratum weights through every estimate;
  - use at least 50 points per stratum;
  - count ASAP and WorldCereal once, and Esri and Dynamic World once, when building agreement strata;
  - use a stratifier that does not come from radar (height above nearest drainage, JRC surface-water seasonality);
  - run the pilot on raw agreement and κ, both with intervals, and stop only if the upper bound of κ is below 0.4;
  - use two cropland labels (cultivated in 2021; cultivated in the flood season assessed);
  - report radar–optical disagreement in both directions.

16. Is this handling of unit mismatch sound? Where do mixed pixels (a 232 m or 252 m pixel that is only partly flooded or partly cropland) still bias results, and in which direction? Is there a better assessment unit for the flood comparison and for the exposure overlay?
17. How should a 252 m forecast probability be combined with a 10 m cropland map whose accuracy is known only as an area-level user's and producer's accuracy, so the exposure estimate and its interval are valid?
18. Given the sample sizes above, which estimates are statistically defensible, which are descriptive only, and which should not be reported? Are the stratum sizes and allocation adequate?
19. Which remaining threats to analytical soundness are not handled by the list above (for example spatial autocorrelation among points, dependence between repeated dates at the same point, multiple comparisons across months, forecast and masks sharing errors because the masks are the forecast's training target)? How should each be handled or bounded?

### F. SLE link (pointers only, no essay text)
20. The SLE essay must focus on one aspect, and the course forbids AI for SLE reading and writing. Which one aspect does this idea raise most clearly through its own technical choices? Candidates:
    - "documenting unknowns and bounding claims" (Chavez-Gonzalez et al. 2022);
    - "representation: whose fields and floods are visible" (Jasanoff 2017; Bowker and Star);
    - "technosolutionism and problem redefinition" (Madianou 2025).
    Point to sources only.

## Output format

1. **Verdict** (at most 150 words): proceed / proceed with changes / narrow / drop. State the single most important change.
2. **AA option matrix:** action type | evidence of effect (with source) | lead time needed | spatial detail needed | variable needed | tolerable error | can our data and forecast support it now? (yes / only as a range or category / no) | why.
3. **What we can honestly deliver**, separately for Bor South and for the Aweil counties, at 3–14 days and at seasonal lead.
4. **Recommended method for bounding advice by the uncertainty test:** the rule, the thresholds and how to set them, a worked example, and what to report when a threshold fails.
5. **Unit-mismatch and soundness plan:** for each comparison (labels vs 10 m maps; labels vs ASAP; radar vs masks; forecast vs masks; forecast × cropland), give the assessment unit, the rule for mixed pixels, and the estimate that is defensible. Then give a table: threat | handled by the team's proposal? | fix.
6. **Scores (1–5) with one-line reasons:** stakeholder alignment, SLE relevance, novelty, validity of references and metrics, analytical soundness, robustness to bias and circularity, coherence, feasibility in four weeks, informativeness of a negative result.
7. **Revised RO text** in the template form, with supporting objectives only if they meet the template rule.
8. **Minimum viable plan:** week by week, with kill criteria. For example: the forecast does not cover Aweil; no lead time beats persistence; the labelling pilot fails.
9. **Verification of the team claims** in "Context": claim | status | source.
10. **Data and forecast access table:** dataset or forecast | coverage | resolution | lead time | access route | time to obtain | limitation.
11. **Evidence that would reverse your verdict.**
12. **Claims you could not verify**, and full references.
