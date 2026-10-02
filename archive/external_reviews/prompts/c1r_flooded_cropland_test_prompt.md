# Prompt: test a proposed research objective on measuring flooded cropland in South Sudan

## Your role

You are an independent expert reviewer in satellite flood mapping, cropland mapping and humanitarian anticipatory action (AA). A student team has proposed the research objective (RO) below. Your job is to find out whether it holds up: whether it is new, valid, feasible in about four weeks, and useful to the stakeholders. You may conclude that it should be changed or dropped.

The RO was drafted by an AI assistant working with one team member. Do not assume it is good, and do not assume the team's numbers are right.

Ground rules:
1. **Evidence.** Cite a source for every factual claim: author, year, title, link or DOI, and page, table or section where possible. If you cannot verify a claim, write "not verified". Load-bearing claims need two independent sources.
2. **Kinds of statement.** Keep apart: facts from external sources, team claims you could not check, and your own inference. Label each.
3. **Data.** Do not invent datasets, resolutions, coverage periods or access routes. For every dataset, check that it exists, covers South Sudan for 2021–2025, is free, and can be obtained in days, not weeks.
4. **Methods.** Do not assume a method works because it is standard. Check it against the real sample sizes, field sizes, cloud conditions and revisit times in this setting.
5. **Tone.** Write plainly. Report weaknesses and strengths with equal care.

## Context (team claims unless marked; verify what you can)

**Project.** TU Eindhoven data-science capstone (JBG060), South Sudan. About four weeks remain (27 Sep – 25 Oct 2026), and a group essay runs in parallel. The team has four to six members.

**Stakeholders.** ZOA (a Dutch NGO) and Zero Hunger Lab (ZHL), in a Q&A on 21 Sep 2026:
- ZOA works along the Lol river in Northern Bahr el Ghazal (the Aweil counties) and in flood-prone Bor South (Jonglei). It decides at community level and needs 3–14 days to implement actions.
- Its priority impact is harvest failure from flooding, and smallholder farms dominate.
- Its first need is to "understand risks associated with data used"; the second is to understand flood dynamics.
- It wants transparent, interpretable results with stated certainty, and prefers a rigorous small sub-problem.
- It phrases its trigger as: "with at least x% certainty, flood will take place which inundates cropland resulting in at least y% of total yield reduction."
- It said "given a flood, estimating the crop damage" is relevant, and that "the dataset might not capture agricultural land fully".
- ZHL ranks the value of outcomes: understanding flood conditions, then precursors, then early warning.

**Data in hand.**
- Course flood masks: described as a NASA MODIS/VIIRS product, ~232 m, daily, 2000–2025, with "unusual" and "recurring" classes. Only flooded pixel-days are stored, and cloud information was removed.
- The ASAP crop mask, v04, at ~500 m and static.
- FAO/WFP CFSAM county statistics (harvested area, production, yield), 2011–2024.
- WorldPop and admin boundaries.

**Team findings (not independently checked).**
1. The masks detect little in July–September. The median share of June–December detections that fall in July–September is 0.04; November–December holds 0.79.
2. In Aweil Centre the masks show 2–33 km²·dekads of flooding per season (2021–2025), yet OCHA reports 45,288 people affected in 2022 and 48,864 in 2024.
3. The ASAP mask gives about 407,000 ha of cropland nationally, while CFSAM reports 1.03–1.18 M ha of harvested cereal area in 2021–2024. ASAP is below CFSAM in 70 of 77 counties, with a median ratio of 0.03.
4. The current method (masks × ASAP) gives about 3,700 ha of flooded cropland nationally for June–November 2022. The CFSAM 2022 summary (p. 1) reports 130,000 ha of cultivated land damaged by floods.
5. WFP's ADAM tool already reports flooded cropland per county (VIIRS/Floodscan × NASA GFSAD30), with no accuracy statement.
6. The IFRC simplified Early Action Protocol sEAP2024SS01 (approved 23 Oct 2025) covers Bor South, Aweil Centre and Aweil East. Its trigger is an INFLOW-AI forecast of Sudd inundation, but the Lol is in the Bahr el Ghazal basin, not the lake-fed Sudd.

## The RO to test (C1-R)

> The objective of this project is to evaluate how accurately public satellite data measure cropland inundated during the June–November growing season in ZOA's operating areas (the five Aweil counties along the Lol in Northern Bahr el Ghazal, and Bor South), 2021–2025, using the course's MODIS/VIIRS flood masks, Sentinel-1 radar flood observations and five public cropland maps (ASAP, ESA WorldCover, ESA WorldCereal, Esri Land Cover and Dynamic World). The current estimate (optical flood masks × ASAP cropland) will be compared with a design-based estimate from a stratified random sample of about 900 points, each labelled for cropland by two independent interpreters and for inundation on every radar and optical observation date, and evaluated using the maps' user's and producer's accuracy for cropland, cropland and flooded-cropland area with 95% confidence intervals, the optical masks' omission rate against radar by month, and the ratio of each estimate to CFSAM harvested and flood-damaged area. The results are intended to support ZOA and ZHL in defining the "inundates cropland" condition of ZOA's trigger by stating how much flooding of farmland in its areas public data can observe, in which months, whether missing cropland or missed flooding causes most of the error, and with what certainty.

Supporting objectives, using the same sample and estimator:
- **SO1 (cropland term):** the accuracy of each cropland map, and error-adjusted cropland area.
- **SO2 (flood term):** agreement between optical and radar flood observations at the same points, by month. Each optical miss is classed as "under cloud" or "clear sky" using MODIS cloud flags.

Planned design:
- **Strata:** the number of maps calling a cell cropland (0, 1–2, ≥3) × flood propensity (a seasonal Sentinel-1 water layer, or height above nearest drainage < 5 m). The "0 maps, low propensity" stratum is split by distance to settlement.
- **Allocation:** about 550 points in the Aweil counties and 350 in Bor South.
- **Cropland label:** "cultivated in at least one season 2021–2024", judged from Sentinel-2 time series and very-high-resolution basemaps.
- **Inundation label:** GFM observed flood, or a Sentinel-1 backscatter threshold, at the point. The optical label is the mask flag on the same day ± 1.
- **Estimation:** stratified estimators following Olofsson et al. (2014).
- **Kill criteria:**
  - K1: no radar access by day 3.
  - K2: pilot inter-interpreter κ < 0.4 on 100 points.
  - K3: fewer than 6 radar dates per season in either area.
  - K4: fewer than 30 cropland points with radar-observed flooding.

**Fallback (C3):** keep only SO2 (optical against radar by month), with no cropland labelling.

## Questions to answer

### A. Novelty
1. Has anyone assessed the accuracy of flooded-cropland estimates in South Sudan, or in comparable smallholder floodplains in the Sahel or East Africa? Check at least:
   - WFP ADAM, FAO DIEM and damage assessments, FEWS NET flood outlooks, UNOSAT;
   - Kerner et al. (2024);
   - Downs et al. (2023, IEEE TGRS);
   - EGU24-18873 (Sentinel-1 vs VIIRS in South Sudan);
   - Chol et al. (2026, J. Flood Risk Management);
   - flood-and-cropland studies from the 2022 Pakistan and Nigeria floods.
2. Has any cropland map been validated for South Sudan specifically?
3. Is anything published on flood timing and detection along the Lol / in Northern Bahr el Ghazal?

### B. Validity of the references
4. **Blind photo-interpretation of smallholder cropland:**
   - What inter-interpreter agreement is realistic in South Sudan-like landscapes, given small, intercropped or fallowed fields and mixed basemap dates?
   - Is κ ≥ 0.4 a sensible pilot threshold?
   - Some maps (WorldCover, WorldCereal, Dynamic World) are built from the same Sentinel-2 imagery the interpreters will look at. How much does that bias their accuracy upward?
5. **Sentinel-1 as the flood reference:**
   - How much flooding does C-band miss under sorghum, maize and grass, and between the 12-day passes (2022 – early 2025)?
   - Does GFM's exclusion mask cover large parts of the Aweil counties or Bor South?
   - Is "radar gives a lower bound" a fair way to state this, or can the bias go both ways (for example, false water on dry, smooth or sandy soils)?
6. **CFSAM:** how are its harvested area and "flood-damaged area" estimated? Is it usable as an order-of-magnitude check, or is it partly derived from the same satellite products, which would make the check circular?
7. **Definitions:** does "cropland = cultivated at least once in 2021–2024" match what the maps claim to represent? Should annual cultivation be labelled instead?

### C. Analytical soundness
8. **Precision:** with ~550 and ~350 points and plausible cropland shares (roughly 5–10% of area), what precision is realistic for:
   - cropland area,
   - map producer's accuracy,
   - flooded-cropland area per county-season,
   - the optical omission rate by month?
   Is 900 points enough, too many, or badly allocated?
9. **Design:** is the stratified design with these stratifiers efficient? Does using a radar-derived stratifier create any problem for estimating optical omission against radar?
10. **Matching:** is matching the 232 m optical pixel to a point-level radar label sound, given mixed pixels? Suggest a better matching unit if there is one.
11. **Planning assumption:** is the team's value for the cropland share that all maps miss (about 34% ± 18 percentage points) plausible, given published omission rates for these maps in Africa?

### D. Feasibility (about four weeks, Earth Engine free tier, a team of 4–6)
12. **Data access.** Verify, with asset IDs or download routes:
    - Sentinel-1 GRD and GFM archive access for 2021–2025;
    - WorldCereal 2021, WorldCover 2021, Esri 10 m annual land cover and Dynamic World;
    - MODIS daily cloud flags;
    - very-high-resolution imagery options for labelling (Esri Wayback, Google Earth historical imagery, Planet NICFI, Collect Earth Online).
13. **Radar coverage.** How many Sentinel-1 acquisitions per June–November season actually exist over the Aweil counties and Bor South in 2021–2025? Is kill criterion K3 likely to trigger?
14. **Effort.** Is ~30 person-hours of double labelling realistic for ~900 points with time-series interpretation?
15. **Plan.** What is the most likely failure point in the week-by-week plan?

### E. Stakeholder value and the SLE link
16. Does measuring "inundated cropland" answer ZOA's stated needs, or is it too far from harvest loss, lead time and community-level decisions to matter?
17. Would a large undercount finding change how ZOA, WFP or IFRC should use products like ADAM or the sEAP trigger in the Aweil counties?
18. The team proposes the SLE aspect "representation and classification: whose fields and floods become visible in trigger data". Is that aspect clearly raised by the RO's own technical choices? Point to sources only; do not write essay text.

### F. Coherence and comparison
19. Is this one objective, or two validation studies joined together? Would the fallback C3 (optical against radar only) be the stronger project?
20. Compare C1-R with the two earlier baselines, on the evidence you find:
    - **v2:** a fitness-for-purpose audit of flood masks and displacement data, nationally.
    - **A:** flooded cropland estimated from the disagreement across three cropland maps, with no independent reference.

## Output format

1. **Verdict** (at most 150 words): proceed / proceed with specific changes / drop, and the single most important change.
2. **Scores (1–5) with one-line reasons** on: stakeholder alignment, SLE relevance, novelty, validity of references and metrics, analytical soundness, robustness to bias and circularity, coherence, feasibility in four weeks, informativeness of a negative result.
3. **Findings by section A–F**, with citations.
4. **Verification of the team claims** listed under "Context": claim | status | source.
5. **Data access table:** dataset | coverage | resolution | access route | time to obtain | limitation.
6. **Ranked recommended changes:** each with the problem it fixes.
7. **Revised RO text** in the template form, if you recommend changes:

   > The objective of this project is to [develop/evaluate/compare] a [model, method or analytical framework] for [specific outcome] in [geographic and temporal scope], using [data or predictor groups]. The proposed approach will be compared with [baseline or alternative method] and evaluated using [performance metrics]. The results are intended to support [specific stakeholder or decision context] by providing [defined output, insight or lead time].

8. **Evidence that would reverse your verdict.**
9. **Claims you could not verify**, and full references.
