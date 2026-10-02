# Independent Expert Review: Evaluating Public Flood and Displacement Data and Forecast Reliability for Anticipatory Action in South Sudan

## Executive Summary

This independent review evaluates the TU Eindhoven data science capstone research objective: assessing the measurement validity of public satellite flood masks and humanitarian displacement data, and the trustworthiness of a ConvLSTM flood forecast for county-level anticipatory action (AA) in South Sudan. The proposed evaluation addresses a critical operational question for stakeholders ZOA and Zero Hunger Lab (ZHL). However, the evaluation design suffers from fatal methodological flaws: non-independent reference datasets (circularity between OCHA, UNOSAT, and IOM DTM), severe temporal misalignment between satellite visibility and actual displacement, an unresolved forecast lead time that confounds 1-dekad and 6-dekad horizons, and unaddressed look-ahead bias in the historical recurring flood masks. 

We recommend **"Proceed with Specific Changes"** (narrow and reframe). The team must drop the flawed ConvLSTM forecast evaluation, sever the cross-contaminated OCHA–DTM validation loop, replace optical masks with Copernicus Global Flood Monitoring (Sentinel-1 SAR), and reframe the analysis around a non-parametric multi-criteria data risk profile directly calibrated to ZOA community-level triggers along the Lol river and Bor South.

---

## 1. Summary Verdict

**Verdict: Proceed with Specific Changes (Narrow and Reframe).**

The proposed research objective addresses an urgent operational challenge: whether public satellite and humanitarian displacement records can support anticipatory action triggers in data-scarce, fragile settings. However, as currently framed, the objective is overscoped and structurally compromised. It couples an empirical audit of humanitarian registries with the verification of a deep-learning spatio-temporal forecast whose lead times, baseline benchmarks, and training splits are fundamentally unresolved. 

Furthermore, the validation framework relies on reference datasets that are interlocked in circular reporting loops (OCHA, UNOSAT, and IOM DTM), employs optical satellite products blinded by cloud cover during the critical onset phase of flooding, and models zero-inflated displacement using parametric correlation metrics that misrepresent true humanitarian exposure. 

To deliver genuine scientific and decision value within the remaining four weeks, the project must proceed under strict reframing: jettison the ConvLSTM forecast, discard OCHA as an independent ground truth, integrate all-weather Sentinel-1 radar benchmarks, and construct a targeted Data Risk Profile for ZOA's active operational zones.

---

## 2. Evaluation Scores Table

| Criterion | Score (1–5) | Primary Justification |
| :--- | :---: | :--- |
| **Novelty** | **4** | Quantitative validation of IOM Event Tracking against spatial flood dynamics in South Sudan is unprecedented, though qualitative reporting gaps are well recognized in grey literature. |
| **Validity of References and Metrics** | **2** | Reference datasets suffer from direct circularity (OCHA compiles DTM and UNOSAT); linear correlation metrics fail on zero-inflated hurdle panels. |
| **Analytical Soundness** | **2** | Outcome reliability caps are artifacts of arbitrary hurdle parameters; ConvLSTM evaluation exhibits spatial autocorrelation leakage and unresolved lead times. |
| **Robustness to Bias and Circularity** | **2** | Shared key informant networks and satellite-directed humanitarian tasking produce self-fulfilling validation; treating unassessed county-seasons as true zeros introduces structural survival bias. |
| **Coherence of the Objective** | **2** | Merges two disparate research questions (observational data auditing vs. neural spatio-temporal forecast verification) that cannot be executed rigorously in parallel. |
| **Decision Relevance** | **3** | Identifying data risks is valuable, but county-level (Admin-2) aggregations miss ZOA's community-level mandate and fail to monitor agricultural crop failure. |
| **Feasibility in Remaining Time** | **2** | Attempting full radar re-processing, ML benchmark re-engineering, and econometric panel sensitivity within four weeks guarantees superficial execution. |

### Detailed Rubric Justifications

- **Novelty (Score: 4/5):** While academic and humanitarian literature has extensively cataloged the qualitative deficiencies of displacement registries ([Refugee Survey Quarterly](https://academic.oup.com/rsq/article/39/4/620/6075991?guestAccessKey=); [International Displacement Monitoring Centre](https://api.internal-displacement.org/sites/default/files/inline-files/GRID-2019-Disasters-Figure-Analysis-SouthSudan.pdf)), a rigorous econometric and spatial evaluation that quantifies the detection probabilities, split-half reliabilities, and minimum detectable effects of IOM DTM Event Tracking against satellite flood extent at the county scale in South Sudan has never been published. It bridges an open gap between theoretical critical data studies and practical anticipatory action design.
- **Validity of References and Metrics (Score: 2/5):** The evaluation framework fails on construct validity. Using OCHA flood impact figures as an independent reference against IOM DTM Event Tracking violates fundamental validation standards because OCHA inter-agency assessments explicitly absorb DTM reporting and UNOSAT flood delineations ([Social Science in Humanitarian Action Platform](https://www.socialscienceinaction.org/resources/key-considerations-for-responding-to-floods-in-south-sudan-through-the-humanitarian-peace-development-nexus/); [UNOSAT](https://unitar.org/-unosat-emergency-mapping-services-20-year-journey-pioneering-global-impact)). Furthermore, measuring reliability via Pearson/Spearman correlation on two-way residualized \(\log(1+x)\) transformations severely distorts zero-inflated count data dominated by administrative non-reporting.
- **Analytical Soundness (Score: 2/5):** The power simulation's conclusion that outcome reliability is bounded at 0.24 is mechanically driven by ad-hoc structural assumptions—specifically setting \(\pi = 0.617\) from circular OCHA records, imposing a rigid 300-person truncation threshold, and fixing latent displacement variance. On the forecasting side, evaluating a ConvLSTM whose training/testing splits interleave calendar years without temporal buffering introduces severe temporal leakage, while ambiguous lead times (1 dekad vs. 6 dekads) render reported F1 improvements over persistence meaningless.
- **Robustness to Bias and Circularity (Score: 2/5):** The design is highly susceptible to structural endogeneity. Humanitarian agencies deploy assessment missions (IRNAs) to areas flagged by satellite flood products, while satellite analysts task high-resolution sensors based on humanitarian crisis alerts. Furthermore, coding unassessed county-seasons as exactly zero displacements confuses institutional non-access with the absence of human suffering, directly amplifying systemic reporting biases ([Journal of Peace Research](https://academic.oup.com/jpr/article/58/5/1098/8365309)).
- **Coherence of the Objective (Score: 2/5):** The proposal attempts to force two fundamentally distinct research projects into a single objective statement. Auditing observational humanitarian datasets requires econometric panel methods, survival analysis, and institutional provenance tracking; validating a deep-learning flood forecast requires hydro-meteorological verification metrics, spatial buffer scoring, and radar-based ground truthing. Combining them creates competing priorities that violate academic capstone standards.
- **Decision Relevance (Score: 3/5):** The research directly addresses ZOA's first stated need: understanding the operational risks of public data. However, its decision relevance is severely curtailed by spatial and thematic misalignment. ZOA operates at the boma/payam level along the Lol River and in Bor South, targeting agricultural crop failure at 3–14 day lead times. A county-level analysis of administrative displacement provides no actionable guidance on local dike reinforcement, seed protection, or community evacuation.
- **Feasibility in Remaining Time (Score: 2/5):** With only four weeks remaining, the team cannot execute radar-based spatial validation across 71 counties, re-train and calibrate the ConvLSTM with proper spatio-temporal holdouts, resolve the 2023 DTM data collapse, and develop an operational decision table. Pursuing all components will result in uncalibrated models and unverified assertions.

---
## 3. Section-by-Section Findings (A–F)

### Section A. Novelty and Prior Work

#### 1. Reliability Assessments of Humanitarian and Earth Observation Data in South Sudan
The reliability of humanitarian displacement registries and optical satellite flood products in South Sudan has been widely scrutinized qualitatively, but quantitative econometric validations at subnational scales remain exceedingly rare.

- **IOM DTM Methodological Limitations:** Official IOM documentation explicitly cautions that Event Tracking (ET) is a rapid, event-triggered mechanism capturing group movements exceeding 50 households and "cannot guarantee comprehensive coverage countrywide" ([IOM DTM Methodology](https://dtm.iom.int/dtm_download_track/28666?file=1&type=node&id=21306)). As documented by [IOM South Sudan operational plans](https://southsudan.iom.int/sites/g/files/tmzbdl1046/files/press_release/file/2023-07/202300704-cap-iom-south-sudan-2023-compressed.pdf), ET operates primarily as an ad-hoc monitoring tool in localized hotspots, contrasting with Mobility Tracking (MT), which attempts systematic round-based geographic coverage across payams and displacement sites. In peer-reviewed and policy literature, [Refugee Survey Quarterly](https://academic.oup.com/rsq/article/39/4/620/6075991?guestAccessKey=) emphasizes that internal displacement data collection is severely distorted by access barriers, active conflict, and shifting institutional priorities, leaving off-camp and rural populations structurally undercounted.
- **Independent Displacement Monitoring:** The Internal Displacement Monitoring Centre ([IDMC South Sudan Figure Analysis](https://api.internal-displacement.org/sites/default/files/inline-files/GRID-2019-Disasters-Figure-Analysis-SouthSudan.pdf)) notes that disaster displacement monitoring in South Sudan is heavily reliant on triangulating fragmented data from IOM DTM, OCHA situation reports, and local administrative accounts. IDMC highlights that because DTM Mobility Tracking assesses stock figures at wide multi-month intervals, short-term, localized flood displacements are routinely missed.
- **Optical Satellite Flood Products Under Persistent Cloud Cover:** The NASA MODIS/VIIRS near-real-time global flood products ([NASA Earthdata Global Flood Products User Guide](https://www.earthdata.nasa.gov/s3fs-public/2025-12/MCDWD_VCDWD_UserGuide_RevF.pdf)) utilize 2-day and 3-day compositing to mitigate cloud contamination. However, during the peak of the West African and East African monsoon seasons (June–September), dense cloud cover obscuration reaches 70–90% across the Sudd basin, suppressing optical sensor visibility precisely when flash floods and rising river stages initiate displacement ([NASA LANCE Flood Documentation](https://lance.modaps.eosdis.nasa.gov/flood/)). Furthermore, the global product differentiates "unusual" from "recurring" flooding based on a 22-year historical baseline (2003–2024). In the Sudd—which experienced an unprecedented hydrological regime shift following the 2019–2021 record rises in Lake Victoria outflow—this static baseline introduces significant misclassification, labeling persistent new water as "unusual" year after year.

#### 2. Literature on Validating Impact-Based Forecasts with Incomplete Impact Data
The challenge of designing and validating anticipatory action (AA) triggers in data-sparse and conflict-affected environments is a primary focus of contemporary humanitarian research.

- **Anticipatory Action Frameworks:** The Red Cross Red Crescent Climate Centre and the 510 initiative ([Anticipation Hub](https://www.anticipation-hub.org/)) establish that setting objective impact-based triggers requires robust baseline damage curves. However, as documented by [Frontiers in Climate](https://www.frontiersin.org/journals/climate/articles/10.3389/fclim.2022.932336/full), lacking, incomplete, or geographically biased historical loss and displacement data regularly prevents the definition of robust statistical trigger thresholds.
- **Structural Invisibility and Reporting Gaps:** Recent empirical work published in [Disaster Prevention and Management / Springer](https://link.springer.com/article/10.1186/s41018-026-00209-z?error=cookies_not_supported&code=8a92c01c-41d8-4243-b5be-fbb87173b5a9) demonstrates "structural invisibility" in disaster displacement reporting within complex, fragile settings. The authors find that humanitarian reporting frameworks prioritize discrete, single-hazard events and registered populations, routinely missing multi-hazard or remote displacement. Similarly, the Danish Refugee Council's machine-learning displacement modeling initiatives ([Danish Refugee Council AHEAD Model](https://drc.ngo/media/fj2dqian/drc-global-anticipatory-action-online-3027-21mar.pdf); [Cambridge University Press Data & Policy](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/5CA9D6358F29AE35C886B92492CFFF65/S2632324924000889a.pdf/div-class-title-pushing-the-boundaries-of-anticipatory-action-using-machine-learning-div.pdf)) emphasize that subnational displacement records are published at irregular intervals with extensive missingness. To handle this, DRC and academic partners employ hierarchical Bayesian formulations that treat unobserved periods as latent parameters rather than true zeros.
- **Validation against Physical Ground Truths:** In a comprehensive evaluation of flood early warning for anticipatory action in Mali, [EarthArXiv](https://eartharxiv.org/repository/object/11374/download/20631/) evaluated GloFAS and regional forecasts against both river discharge observations and text-mined impact records. The authors concluded that observational hydrometric discharge data must serve as the primary ground truth, as humanitarian impact data proved too noisy, fragmented, and reporting-biased to validate trigger reliability.
- **Novelty Assessment:** The TU Eindhoven capstone objective is **not** a mere restatement of known limitations. While grey literature asserts that "data are sparse and uncertain," the team's quantitative derivation of empirical detection probabilities (e.g., 61.7% detection against OCHA, 52.2% against MT) and minimum detectable effect sizes represents a novel, rigorous contribution to the operationalization of anticipatory action in South Sudan.

#### 3. Inundation Forecasting Benchmarks and Change-Based Scoring
In operational hydrological forecasting and machine-learning inundation modeling, benchmark selection is critical to avoid illusory skill claims.

- **Persistence as the Accepted Minimum Baseline:** For short-lead (1–10 day) inundation forecasting, simple persistence (assuming water extent remains identical to the most recent cloud-free observation) is the universally accepted minimum benchmark ([Natural Hazards and Earth System Sciences](https://nhess.copernicus.org/articles/24/309/2024/)). In slow-moving wetland systems like the Sudd, surface water changes gradually over multi-week periods; consequently, raw spatial overlap metrics (such as binary accuracy or overall F1) against static water masks yield deceptively high values (>0.90) simply by predicting persistence.
- **State of the Art on the White Nile (INFLOW-AI):** The premier benchmark for machine learning-based flood forecasting in South Sudan is the **INFLOW-AI** model, developed by the University of Reading, ICPAC, and the Red Cross Red Crescent Climate Centre ([EGUsphere](https://egusphere.copernicus.org/preprints/2026/egusphere-2026-66/); [IFRC Simplified Early Action Protocol South Sudan](https://go-api.ifrc.org/api/downloadfile/93644/MDRSS017sEAP)). INFLOW-AI v2.1 uses a two-stage architecture:
  1. A transformer network with multi-head attention predicting the *first difference of the seasonal anomaly* in basin-wide flood extent at a 6-dekad (2-month) lead time, driven by upstream Lake Victoria, Kyoga, and Albert water levels;
  2. A ConvLSTM predicting 1 km spatial inundation probabilities, strictly constrained by the total basin extent from Stage 1.
- **Scoring State vs. Scoring Change:** Standard spatial overlap metrics (e.g., Critical Success Index, Dice/F1) calculated over the entire domain predominantly reflect persistent open water and static wetland boundaries. To demonstrate genuine predictive utility for anticipatory action, models must be evaluated on **change metrics**:
  - Contingency tables calculated exclusively on pixels transitioning from dry to wet (**onset/expansion F1**) and wet to dry (**recession F1**);
  - Spatial buffer-tolerant metrics, such as the Fractions Skill Score (FSS) or displacement-adjusted F1, which reward near-miss spatial predictions rather than penalizing slight boundary misalignments.

---

### Section B. Validity of the Evaluation Design

#### 4. Independence and Circularity of Reference Datasets
The proposal's reliance on UN OCHA flood reports, IOM DTM Event Tracking, and optical satellite products creates profound risks of circular validation.

- **OCHA Figures Derived from DTM and Field Partners:** UN OCHA does not maintain an independent primary data collection network in South Sudan. OCHA’s periodic Flood Snapshots, Situation Reports, and Humanitarian Needs Overviews compile secondary reports submitted by humanitarian clusters, local Relief and Rehabilitation Commission (RRC) offices, and inter-agency assessments ([OCHA South Sudan Humanitarian Response Plan](https://www.scribd.com/document/704134535/South-Sudan-Humanitarian-Response-Plan)). The primary operational inputs feeding into OCHA's Needs Analysis Working Group (NAWG) are precisely the **IOM DTM Event Tracking** alerts and **Mobility Tracking** assessments ([CERF South Sudan Allocation Report](https://cerf.un.org/sites/default/files/resources/23-RR-SSD-59113_South%20Sudan_CERF_Report.pdf)). Evaluating DTM Event Tracking against OCHA is therefore comparing an upstream data feed against a downstream consolidated summary that incorporates the exact same source.
- **Satellite-Targeted Assessments (Endogeneity):** The relationship between satellite flood mapping and humanitarian field deployment is similarly coupled. As documented by the [UN Operational Satellite Applications Programme (UNOSAT)](https://unitar.org/-unosat-emergency-mapping-services-20-year-journey-pioneering-global-impact) and the [Logistics Cluster South Sudan](https://logcluster.org/sites/default/files/public/2024-06/south-sudan-floods-preparedness-and-response-22-june-2024.pdf), OCHA and humanitarian partners routinely task UNOSAT to acquire and analyze satellite imagery (using MODIS, VIIRS, and Sentinel-1) over suspected flood zones. The resulting satellite water extent maps are then used by the Inter-Cluster Coordination Group (ICCG) to schedule and dispatch Inter-Agency Rapid Needs Assessment (IRNA) missions. Areas shown as flooded on satellite maps receive field assessment teams, while areas obscured by clouds or outside the satellite tile footprints are systematically deprioritized. Consequently, when ground assessors record displaced or affected populations, the probability of assessment is endogenous to prior satellite detection.

```
       [ Satellite Detections (MODIS / VIIRS / UNOSAT) ]
                         │               │
      Guides Assessment  │               │ Identifies Inundated
         Prioritization  ▼               ▼ Regions
               [ Inter-Agency Rapid Needs Assessments ]
                         │               │
       Submits Incident  │               │ Aggregates Operational
                Reports  ▼               ▼ Field Data
               [ IOM DTM Event Tracking Registry ]
                         │               ▲
          Feeds Incident │               │ Triangulates and
                   Data  ▼               │ Endorses Figures
               [ UN OCHA Flood Snapshots & Situation Reports ]
```

#### 5. Measuring ET Recording Probability via OCHA Floods: Directional Biases
The team estimates ET’s detection probability as \(\pi = 61.7\%\), defined as the proportion of county-seasons where OCHA reported \(\ge 10,000\) people affected that had at least one ET flood displacement record. This metric suffers from severe, multi-directional biases:

1. **"Affected" versus "Displaced" Conceptual Mismatch (Upward & Downward Bias):** "Affected" encompasses a wide spectrum of humanitarian distress—loss of agricultural crops, contaminated water boreholes, submerged roads, or marooned homesteads where populations remain in situ ([UN OCHA Flood Snapshots](https://www.unocha.org/publications/report/south-sudan/south-sudan-flooding-situation-report-no-1-31-october-2022)). In contrast, "Displaced" requires physical forced relocation away from habitual residence. In flat swamp basins like Northern Bahr el Ghazal, hundreds of thousands of subsistence agro-pastoralists may suffer severe crop submergence without relocating their permanent tukuls, leading to legitimate zero displacement records. Conversely, where localized flash floods induce severe distress, populations may move into adjacent higher ground without being captured under broad county-wide affected headcounts.
2. **Incomplete OCHA Coverage (Downward Bias on Reliability):** OCHA's flood figures do not constitute a complete census. OCHA assessments are triggered by local authority reports and security clearances. Counties experiencing severe conflict or lack of partner presence are omitted from OCHA reports. Treating OCHA as the definitive denominator misclassifies true humanitarian displacement as an ET recording omission.
3. **Cross-County Displacement Dynamics (Distortion of Origins):** In extreme flooding events, displaced households migrate across administrative boundaries to reach higher ground, urban centers, or established displacement camps (e.g., Bentiu or Malakal). While the team notes that 92–100% of ET records match origin to event county, this high percentage is partly an artifact of ET enumerators interviewing key informants at destination sites who describe localized, internal movements, or assigning whole arrival groups to the receiving county.

#### 6. Validation of Flood Masks in River-Fed Wetlands
The team's reliance on odd–even dekad split-half reliability and ERA5 rainfall correlation reveals major methodological inadequacies when applied to the Sudd wetland.

- **Split-Half Reliability as an Inflated Autocorrelation Ceiling:** The reported split-half reliability of 0.91 (Spearman–Brown corrected between odd and even dekads) does not validate detection accuracy. In large wetlands and dynamic floodplains, floodwaters rise and recede over timescales of weeks to months. Dekads separated by 10 days are heavily autocorrelated; furthermore, persistent cloud decks cover multi-week spells during July–August. Correlating odd and even dekads simply demonstrates that adjacent 10-day composite masks share the same persistent water and identical cloud masks. It provides zero evidence regarding whether the pixels represent true water on the ground.
- **ERA5 Rainfall Correlation (−0.11 long-term) Reflects Physical Hydrology, Not Data Failure:** Correlating local rainfall with county-level flood extent misinterprets the physical hydrology of South Sudan. The Sudd is a vast, low-gradient river-fed wetland whose inundation is driven primarily by White Nile inflow from Lake Victoria and the equatorial lakes plateau, hundreds of kilometers upstream ([Copernicus Global Flood Monitoring Evaluation](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC131351/JRC131351_01.pdf); [ESA Global Development Assistance](https://gda.esa.int/story/climate-resilient-flood-management-in-south-sudan-through-earth-observation-insights/)). Inflow pulses take weeks to months to propagate downstream into Jonglei and Unity states. Consequently, local precipitation in the Sudd has a weak, or even negative, instantaneous correlation with wetland extent. Finding a −0.11 correlation over 2001–2025 is hydrologically expected and cannot serve as an index of sensor error.
- **Independent Ground Truth: Copernicus Global Flood Monitoring (Sentinel-1 SAR):** The valid independent reference for 2021–2025 is the **Copernicus Emergency Management Service Global Flood Monitoring (CEMS-GFM)** product ([Copernicus GFM](https://global-flood.emergency.copernicus.eu/technical-information/glofas-gfm/)). GFM processes all incoming Sentinel-1 Synthetic Aperture Radar (SAR) acquisitions at 20 m resolution globally in near-real time, penetrating cloud cover and operating day and night.
- **Operational Availability and Sample Sizing:** CEMS-GFM and processed Sentinel-1 SAR flood layers are freely accessible via the Copernicus Data Space Ecosystem, Google Earth Engine, and GloFAS portals. However, Sentinel-1 acquisitions over South Sudan were impacted by the loss of Sentinel-1B in December 2021, reducing the revisit cycle of Sentinel-1A to approximately 12 days. To rigorously benchmark the MODIS/VIIRS masks, a stratified sample of **30–40 county-seasons** (spanning 6–8 priority flood counties across 2021–2025, stratified by open water, emergent swamp vegetation, and dry savannah) would provide adequate statistical power to estimate Critical Success Index (CSI), omission rates under cloud cover, and spatial bias.

---

### Section C. Analytical Soundness

#### 7. Drivers of the Outcome Reliability Cap (0.24) and Sensitivity Checks
The team's power simulation concluded that outcome reliability—defined as the squared within-county correlation between observed and true displacement \(R_{\text{y}} = \text{Corr}(Y_{\text{obs}}, Y^*)^2\)—is capped near 0.24, rendering the within-county design incapable of detecting moderate true effects. Scrutiny of the simulation code and structural assumptions reveals that this cap is mathematically predetermined by four specific modeling choices:

1. **Independent Bernoulli Missingness Model:** By modeling ET detection as a binary draw \(D \sim \text{Bernoulli}(\pi)\) where \(Y_{\text{obs}} = D \cdot Y^*\), the variance of observed displacement becomes:
   \[
   \text{Var}(Y_{\text{obs}}) = \pi \cdot \text{Var}(Y^*) + \pi(1 - \pi) \cdot [E(Y^*)]^2
   \]
   The squared correlation simplifies to:
   \[
   R_{\text{y}} = \frac{\pi}{1 + (1 - \pi) \cdot \left(\frac{E(Y^*)^2}{\text{Var}(Y^*)}\right)} = \frac{\pi}{1 + (1 - \pi) / \text{CV}^2}
   \]
   where \(\text{CV}\) is the coefficient of variation of true displacement. For skewed, zero-inflated distributions where \(\text{CV} \approx 0.5\), \(E(Y^*)^2 / \text{Var}(Y^*) = 4.0\). Substituting \(\pi = 0.617\):
   \[
   R_{\text{y}} = \frac{0.617}{1 + (0.383) \times 4.0} = \frac{0.617}{2.532} = 0.243
   \]
   Thus, the 0.24 cap is an exact mathematical consequence of assuming that unobserved events collapse to literal zeros rather than being treated as missing observations.
2. **The 300-Person Truncation Threshold:** Discarding all movements under 300 individuals artificially eliminates smaller, localized displacement shocks that drive within-county variance in moderately populated counties, suppressing correlation.
3. **Fixed Latent Displacement Variance (\(\kappa = 0.5\)):** Restricting the latent index variance restricts how strongly true displacement responds to local shocks, inflating residual error.
4. **Recommended Sensitivity Checks:**
   - **Vary Detection Probability \(\pi\):** Test a plausible range of \(\pi \in [0.40, 0.85]\).
   - **Hurdle versus Heckman / Tobit Selection:** Replace the Bernoulli zero-replacement assumption with a two-step Heckman selection model or treat non-reporting as unobserved (missing) data rather than zero.
   - **Vary Truncation Threshold:** Test thresholds from 50 individuals (IOM’s stated threshold) to 500 individuals.
   - **Heterogeneous Reporting by Road Access:** Condition \(\pi\) on county flood severity and remoteness (e.g., higher severity decreases physical access for enumerators, lowering \(\pi\)).

#### 8. Econometric Soundness: Two-Way Fixed Effects (TWFE) and Alternative Estimators
The team employs Two-Way Fixed Effects (TWFE) with CR2 cluster-robust standard errors and Bell–McCaffrey degrees of freedom adjustments across 71 counties over 4 seasons (total \(N = 284\)).

- **Suitability of TWFE with CR2 on 71 Clusters:** While 71 clusters is nominally large enough to avoid small-cluster bias, the panel structure has extreme cluster leverage. Because flood displacement is concentrated in a small subset of chronically flooded counties (e.g., Rubkona, Leer, Mayendit, Bor South, Twic East) while 24 counties report exactly zero displacements across all 4 seasons, the **effective degrees of freedom** under Bell–McCaffrey adjustments collapses to a fraction of 70 (often \(< 15\)). This inflates standard errors and reduces statistical power.
- **Inadequacy of Log-Linear Correlation on Zero-Inflated Counts:** Applying a linear TWFE estimator to \(\log(1 + x)\) transformed count data with extensive zeros introduces well-documented econometrical distortions:
  - It induces bias in elasticities that depend on the arbitrary scaling of the constant 1;
  - It conflates two distinct processes: the extensive margin (whether displacement occurred and was recorded) and the intensive margin (the size of displacement conditional on recording).
- **Recommended Alternative Estimators:**
  - **Poisson Pseudo-Maximum Likelihood (PPML) with County and Year Fixed Effects:** PPML handles zeros naturally without ad-hoc transformations, remains consistent under arbitrary heteroskedasticity, and preserves the scale of humanitarian impacts;
  - **Binary Concordance and Contingency Metrics:** For anticipatory action triggers, absolute headcounts are secondary to triggering decisions. Agreement on the binary occurrence of significant displacement (e.g., Cohen's Kappa, Matthews Correlation Coefficient, or Receiver Operating Characteristic AUC) provides a far more informative and robust measure of operational data reliability.

#### 9. Forecast Verification Rigor: ConvLSTM Pitfalls and Data Leakage
The ConvLSTM flood forecast evaluation described in the team brief contains fatal architectural and methodological flaws that invalidate the reported skill scores (e.g., F1 of 0.846 vs. 0.842 for persistence):

1. **Unresolved Lead Time (1 Dekad vs. 6 Dekads):** The project documentation oscillates between defining the forecast as "the next dekad" (10-day lead) and "6 dekads ahead" (60-day lead). This is a catastrophic ambiguity. At a 1-dekad lead, a model scoring F1 of 0.846 against persistence of 0.842 demonstrates **zero added value** (a trivial +0.004 margin). At a 6-dekad lead, persistence degrades to 0.716, meaning an F1 of 0.846 would represent massive predictive skill. Claiming high performance without fixing the exact lead time is scientifically unacceptable.
2. **Temporal Leakage and Train/Test Contamination:** The evaluation notes that "test years sit between training years" (e.g., evaluating on 2023 with 2021, 2022, 2024, and 2025 in the training or recurring mask definition). In hydrological systems, multi-year inundation regimes exhibit long memory; evaluating on an intermediate year after training on surrounding years causes severe data leakage. The model must be evaluated strictly using **walk-forward out-of-time splits** (e.g., train on 2003–2020, validate on 2021–2022, test on 2023–2025).
3. **Look-Ahead Bias in the NASA Recurring Water Mask:** The MODIS/VIIRS "recurring" flood layer was generated using the full 22-year product archive (2003–2024). When the ConvLSTM is trained to predict recurring vs. unusual water in 2021–2023, the target label itself was derived using future satellite observations from 2024. This represents direct target leakage.
4. **Spatial Autocorrelation in Patch-Based Training:** The ConvLSTM operates on 32×32 pixel patches over a "three-state corridor". If spatial patches from adjacent counties or neighboring tiles are randomly assigned to train and test sets, spatial autocorrelation inflates performance metrics to near perfection (explaining the quoted 99.8% overall accuracy). Spatial cross-validation must hold out entire contiguous sub-basins or geographic regions.

---

### Section D. Coherence of the Objective

#### 10. Single Objective Standard versus Dual Project Scope
The TU Eindhoven capstone guidelines strictly dictate **one cohesive research objective** that addresses a unified approach, outcome, and stakeholder need. 

- **Structural Fragmentation:** The proposed objective attempts to fuse two fundamentally incompatible inquiries into a single compound sentence:
  1. An **econometric audit of observational data quality** (quantifying detection rates, reporting biases, and minimum detectable effects in IOM DTM and OCHA records);
  2. A **machine-learning spatio-temporal computer vision task** (evaluating a ConvLSTM deep-learning model on satellite imagery).
- **Incompatible Methodologies and Toolchains:** These two strands share neither an empirical dataset nor a common evaluation methodology. Auditing humanitarian records requires survival modeling, fixed-effects count regressions, and institutional provenance analysis. Validating a ConvLSTM requires raster tensor pipelines, spatial cross-validation, receiver operating characteristic curve analysis, and radar ground-truth comparison.
- **Dilution of Impact:** Forcing both into a four-week capstone guarantees that neither will be done thoroughly. The forecast evaluation will remain a superficial comparison of flawed F1 scores on uncalibrated patches, while the humanitarian data audit will lack the necessary sensitivity checks and administrative context. The research objective would be infinitely stronger, more rigorous, and more coherent if the ConvLSTM forecast is completely excised.

#### 11. History, Post-Hoc Reframing, and Substantive Value
The disclosure of the project's history—pivoting to measurement validity after an audit revealed a NO-GO for the original severity–displacement hypothesis—raises crucial questions regarding research integrity and framing:

- **Legitimacy of a Pre-Registered Fallback:** The team demonstrated exemplary open-science discipline by pre-registering a go/no-go audit with binding kill criteria and keeping the core association blinded. Because the audit proved the panel was statistically underpowered to detect a true correlation of 0.35, pivoting to a pre-registered fallback ("measurement validity of public flood-impact data") is methodologically legitimate and protects against p-hacking or publication bias.
- **The Risk of Defeating the Pivot by Appending the Forecast:** However, appending the ConvLSTM forecast to the fallback was *not* part of the original measurement audit; it appears to be a post-hoc compensatory maneuver to reintroduce complex machine learning into a project where the empirical data proved hostile to statistical modeling.
- **Criteria for a Substantive Research Objective:** To stand as an independent, substantive scientific inquiry rather than an apology for a failed regression, the evaluation must not merely state "the data are too poor to run our model." It must establish:
  1. **Constructive Operational Guidance:** Precisely where, when, and under what conditions public data can and cannot be utilized;
  2. **Mechanistic Explanation of Gaps:** Identifying whether failures stem from physical sensor blindness (cloud cover), hydrological regime shifts (Sudd expansion), or institutional reporting mandates (IOM 50-household threshold);
  3. **Empirical Risk Bounds:** Providing formal risk bounds (e.g., false-alarm ratios, missed-event rates) that allow NGOs like ZOA to parameterize robust no-regret triggers.

---

### Section E. Decision Relevance

#### 12. Stakeholder Decision Alignment: ZOA and Zero Hunger Lab (ZHL)
ZOA and Zero Hunger Lab possess distinct operational mandates and risk tolerances:

- **ZOA's Operational Reality:**
  - **Locations:** The Lol River basin in Northern Bahr el Ghazal (Aweil Centre, Aweil North, Aweil West) and flood-prone communities in Bor South (Jonglei).
  - **Decisions:** Locally led anticipatory action proposals co-designed with communities, requiring HQ approval and bilateral donor funding.
  - **Lead Times:** 3 days minimum (rapid sandbagging, clearing drainage channels), 10 days sufficient (distributing emergency cash, moving livestock), 14 days robust upper bound (pre-positioning grain stores).
  - **Impact Priority:** Prevention of **harvest failure** and agricultural crop loss, followed by protection of displaced agro-pastoralists and returnees.
- **What Fails Decision Relevance:**
  - *County-Level Displacement Counts:* Knowing that the 4-year within-county correlation between flood extent and ET displacement is \(r = 0.11\) provides zero actionable insight to a ZOA field team deciding whether to reinforce dikes along the Lol River.
  - *National-Scale ConvLSTM Skill:* A 32×32 patch forecast trained on a three-state corridor in Jonglei and Unity that omits the Lol River is entirely useless for ZOA’s operations in Northern Bahr el Ghazal.
  - *Lake Victoria Seasonal Outlooks for the Lol River:* While Lake Victoria levels drive the White Nile and Sudd inundation (relevant to Bor South), Northern Bahr el Ghazal sits in a completely separate hydrological basin fed by the Bahr al-Arab / Lol river systems originating in Western Bahr el Ghazal and the Central African Republic divide. Conflating White Nile dynamics with Lol River flooding will lead to disastrous trigger failures in Aweil.
- **What Directly Informs Decisions:**
  - *Lead-Time and Seasonal Blindness Mapping:* Quantifying that optical satellite products capture only 4% of seasonal flood water in July–September informs ZOA that satellite-based triggers will miss the critical planting and early vegetative growth stages of sorghum, forcing them to rely on upstream river gauges or radar.
  - *The 2023 Displacement Collapse Audit:* Documenting why ET recorded only 4 flood displacement events in 2023 (while accommodating 579 forced returnee groups) provides ZOA with the critical operational insight that humanitarian registries redirect enumerator resources during geopolitical crises (the Sudan conflict), making them unviable as real-time early warning feeds.

#### 13. Focus on Flood Extent and Displacement vs. Crop Loss
The research objective focuses exclusively on flood extent and displacement, omitting agricultural crop damage—the primary operational concern of ZOA.

- **Vulnerability of Subsistence Cropland:** In Northern Bahr el Ghazal, smallholder subsistence farming revolves around sorghum and groundnut cultivation. Submergence during July–August causes complete crop failure, precipitating catastrophic food insecurity (IPC Phase 4/5) even if populations are not physically displaced ([FEWS NET South Sudan](https://reliefweb.int/report/south-sudan/south-sudan-key-message-update-emergency-ipc-phase-4-outcomes-remain-widespread-flooding-expands-september-2024)).
- **Remote Sensing Limitations on Cropland Mapping:** Global land-cover products (such as ESA WorldCover 10 m or Dynamic World) suffer from notorious omission errors across the Sahel and South Sudan, frequently misclassifying fragmented, rain-fed smallholder plots and intercropped fields as grassland or sparse shrubland ([World Bank Climate Resilient Flood Management](https://documents1.worldbank.org/curated/en/099013026015514714/pdf/P502312-213dd5be-8e51-45a1-8845-ceafa7ffd5d1.pdf); [FAO Geospatial Land Cover](https://www.fao.org/geospatial/our-focus/Land-Cover-Crop-Monitoring/en)).
- **Scope Recommendation:** The team should **not** attempt to build a full agricultural crop loss model in the remaining four weeks. Introducing complex crop phenology modeling would fatally overload the project. Instead, the team should execute a **targeted geospatial overlay**: intersect the validated Sentinel-1 flood extents with high-resolution cropland layers (ESA WorldCover) specifically within ZOA's active counties (Aweil Centre, Aweil West, Bor South) to provide an empirical estimate of inundated arable land.

#### 14. Spatial Scale Mismatch: County Level (Admin-2) vs. Community Level
There is a fundamental spatial dissonance between county-level administrative modeling and community-level humanitarian programming:

- **Admin-2 Inadequacy:** South Sudan's 79 counties are geographically enormous (averaging 8,000 km²), highly heterogeneous, and physically fragmented by vast swamps, rivers, and seasonal marshes. A county-level flood severity metric aggregates dry uplands with deeply submerged river valleys. For a field practitioner in Aweil, an alert that "Aweil Centre is at risk" is operationally un-actionable, as aid must be delivered to specific bomas, dyke alignments, and road segments.
- **The Value of Auditing Admin-2 Data:** Nevertheless, conducting a rigorous audit at the county scale is of profound strategic value. Proving conclusively that public datasets lack sufficient statistical power and reliability *even at the aggregated county level* is a vital scientific result. It provides ZOA and ZHL with indisputable empirical justification to reject top-down, centralized algorithmic triggers and instead invest their limited resources in community-based river level gauges and localized participatory early warning networks.

---

### Section F. Representation and Ethics

#### 15. Humanitarian Data Ethics, Missingness, and Structural Exclusion
The ethical implications of utilizing fragmented administrative data for algorithmic resource allocation are profound and well-documented in humanitarian studies:

- **Structural Invisibility and Systematic Exclusion:** In a pioneering study on overlapping disasters and conflict, [Disaster Prevention and Management / Springer](https://link.springer.com/article/10.1186/s41018-026-00209-z?error=cookies_not_supported&code=8a92c01c-41d8-4243-b5be-fbb87173b5a9) demonstrates that institutional counting practices produce "structural invisibility." Populations displaced in insecure, politically marginalized, or geographically inaccessible zones are routinely excluded from official registries because assessment teams cannot secure logistics or security clearances. 
- **The "Missing Dead" and Narrative Bias:** In conflict-affected environments like South Sudan, [Journal of Peace Research](https://academic.oup.com/jpr/article/58/5/1098/8365309) illustrates that incident datasets suffer from severe non-random missingness driven by logistical accessibility and agency mandates. Treating missing data as true zeros creates a self-reinforcing bias: accessible, well-funded areas receive continuous monitoring and aid, while remote or besieged communities remain uncounted and unassisted.
- **The Deadly Assumption of Zero Displacement:** When quantitative data scientists recode missing administrative records (no ET record) as 0 displaced individuals, they commit an algorithmic erasure. In an anticipatory action framework, tying trigger activations or vulnerability weights to uncorrected historical counts ensures that communities experiencing historical recording voids (such as Aweil Centre in 2022 and 2024, despite severe flooding) are systematically denied pre-disaster financing.
- **Accountability to Donors vs. Affected Communities:** As analyzed by [Refugee Survey Quarterly](https://academic.oup.com/rsq/article/39/4/620/6075991?guestAccessKey=), humanitarian datasets often reflect bureaucratic incentives—justifying emergency donor appeals and demonstrating operational presence—rather than representing a true census of human need. Rigorously exposing these systemic blind spots protects NGOs from deploying biased automated triggers that exacerbate existing vulnerabilities.

---

## 4. Evidence Table

| Claim / Assessment Area | Primary Source / Citation | Directness of Evidence | Summary of Findings & Operational Relevance |
| :--- | :--- | :---: | :--- |
| **IOM DTM Event Tracking Coverage** | [IOM DTM Methodology](https://dtm.iom.int/dtm_download_track/28666?file=1&type=node&id=21306); [IOM South Sudan Crisis Response](https://southsudan.iom.int/sites/g/files/tmzbdl1046/files/press_release/file/2023-07/202300704-cap-iom-south-sudan-2023-compressed.pdf) | **Direct** | Captures ad-hoc group moves >50 households; explicitly disclaims nationwide coverage; focuses on rapid emergency response rather than comprehensive tracking. |
| **2023 Sudan Crisis Resource Diversion** | [IOM DTM Sudan Influx Tracking](https://crisisresponse.iom.int/sites/g/files/tmzbdl1481/files/appeal/pdf/2024_South_Sudan_Crisis_Response_Plan_2023__2025.pdf); [CERF Allocation SSD-59113](https://cerf.un.org/sites/default/files/resources/23-RR-SSD-59113_South%20Sudan_CERF_Report.pdf) | **Direct** | Demonstrates that the eruption of conflict in Sudan (April 2023) redirected DTM enumerators and funding to border Points of Entry (Renk) and returnee tracking, causing an operational collapse in flood displacement recording. |
| **OCHA Secondary Compilation & Circularity** | [OCHA South Sudan HRP](https://www.scribd.com/document/704134535/South-Sudan-Humanitarian-Response-Plan); [SSHAP Flood Nexus Brief](https://www.socialscienceinaction.org/resources/key-considerations-for-responding-to-floods-in-south-sudan-through-the-humanitarian-peace-development-nexus/) | **Direct** | Confirms OCHA relies on Inter-Agency Rapid Needs Assessments (IRNAs) and DTM Event/Mobility Tracking feeds; OCHA data are not an independent ground truth. |
| **UNOSAT Satellite-Guided Assessment Bias** | [UNOSAT 20-Year Report](https://unitar.org/-unosat-emergency-mapping-services-20-year-journey-pioneering-global-impact); [Logistics Cluster Flood Plan](https://logcluster.org/sites/default/files/public/2024-06/south-sudan-floods-preparedness-and-response-22-june-2024.pdf) | **Direct** | Satellite water delineations directly guide the spatial deployment of field assessment teams, introducing circular endogeneity between satellite visibility and recorded ground impacts. |
| **MODIS/VIIRS Cloud Obscuration & Baselines** | [NASA Earthdata Global Flood Guide](https://www.earthdata.nasa.gov/s3fs-public/2025-12/MCDWD_VCDWD_UserGuide_RevF.pdf); [NASA LANCE Flood](https://lance.modaps.eosdis.nasa.gov/flood/) | **Direct** | Optical composite masks obscure ground during peak rains (July–Sept); recurring mask baseline (2003–2024) embeds future observations and mislabels post-2019 regime shift water. |
| **Copernicus Sentinel-1 SAR Validation** | [Copernicus GFM Technical Documentation](https://global-flood.emergency.copernicus.eu/technical-information/glofas-gfm/); [JRC GFM Validation Report](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC131351/JRC131351_01.pdf) | **Direct** | Near-real-time 20 m all-weather radar flood mapping; JRC validation in Bentiu confirms CSI of 76.9% and systematic underestimation (bias = 0.88) under dense emergent swamp vegetation. |
| **State of the Art Flood Forecasting (INFLOW-AI)** | [EGUsphere Preprint (Rapson et al., 2026)](https://egusphere.copernicus.org/preprints/2026/egusphere-2026-66/); [IFRC Simplified EAP South Sudan](https://go-api.ifrc.org/api/downloadfile/93644/MDRSS017sEAP) | **Direct** | Benchmarks two-stage ML forecasting on the White Nile (Transformer + ConvLSTM) predicting seasonal anomalies at 6-dekad lead; establishes that 1-dekad ConvLSTM without upstream lake constraints offers negligible skill over persistence. |
| **Structural Invisibility in Crisis Data** | [Springer / Disaster Prevention and Management (2026)](https://link.springer.com/article/10.1186/s41018-026-00209-z?error=cookies_not_supported&code=8a92c01c-41d8-4243-b5be-fbb87173b5a9) | **Analogous** | Demonstrates empirical exclusion in multi-hazard disaster displacement reporting where institutional mechanisms prioritize registered populations and discrete events. |
| **Reporting Gaps and "Missing Dead" Bias** | [Journal of Peace Research (2021)](https://academic.oup.com/jpr/article/58/5/1098/8365309) | **Direct** | Documents that missing data in South Sudan conflict and crisis monitoring are non-random (MNAR), driven by accessibility and strategic priority; recoding missing as zero induces massive bias. |
| **Cropland Remote Sensing Vulnerability** | [World Bank Flood Management Project (2024)](https://documents1.worldbank.org/curated/en/099013026015514714/pdf/P502312-213dd5be-8e51-45a1-8845-ceafa7ffd5d1.pdf); [FAO Land Cover South Sudan](https://www.fao.org/geospatial/our-focus/Land-Cover-Crop-Monitoring/en) | **Direct** | Confirms 45% of cropland is exposed to flooding; smallholder subsistence plots are widely omitted or misclassified as shrub/grassland by global land-cover datasets. |

---

## 5. Ranked Recommendations

To transform the proposed research into an analytically rigorous, scientifically honest, and operationally valuable capstone project within the remaining four weeks, the team should execute five ranked modifications:

```
[ Current Proposed Objective: Conflated Scope ]
├─ Econometric Audit of DTM & OCHA (Circular, Zero-Inflated TWFE)
└─ ConvLSTM Forecast Verification (Unresolved Lead Time, Data Leakage)
                          │
                          ▼  APPLY RANKED RECOMMENDATIONS
[ Reframed Objective: Rigorous Data Risk Profile ]
├─ Recommendation 1: Excise ConvLSTM Deep-Learning Forecast
├─ Recommendation 2: Sever Circular OCHA-DTM Loop; Adopt Sentinel-1 SAR
├─ Recommendation 3: Reframe Hurdle Simulation to Sensitivity Bounds
├─ Recommendation 4: Replace Linear TWFE with Binary Concordance & PPML
└─ Recommendation 5: Deliver Operational Decision & Risk Matrix for ZOA
```

### Recommendation 1: Completely Excise the ConvLSTM Forecast Evaluation
- **Problem Fixed:** Eliminates a fatal scope-splitting flaw that violates the single-objective requirement, resolves insurmountable data leakage issues (look-ahead bias in recurring masks, arbitrary patch splits), and prevents the presentation of deceptive skill scores (+0.004 F1 over persistence).
- **Execution:** Remove all neural network training and validation from the research objective. Focus the capstone exclusively on the empirical measurement validity of public Earth observation and humanitarian data.

### Recommendation 2: Sever the Circular OCHA–DTM Loop and Benchmark Against Sentinel-1 SAR
- **Problem Fixed:** Resolves the circular endogeneity of using secondary OCHA figures to validate primary DTM feeds, and overcomes optical cloud obscuration in MODIS/VIIRS.
- **Execution:** 
  1. Discontinue using OCHA affected headcounts as a ground truth;
  2. Pull processed Copernicus Global Flood Monitoring (GFM) Sentinel-1 SAR flood masks across a targeted sample of 30–40 county-seasons (2021–2025);
  3. Calculate empirical omission rates of MODIS/VIIRS optical products during peak cloud months (July–September) against radar observations.

### Recommendation 3: Reframe the Hurdle Simulation into Multi-Scenario Sensitivity Bounds
- **Problem Fixed:** Prevents the presentation of the 0.24 outcome reliability cap as an objective physical reality, recognizing it as a mathematical artifact of the Bernoulli zero-replacement assumption.
- **Execution:**
  1. Vary detection probability across \(\pi \in [0.40, 0.85]\);
  2. Implement a two-step Heckman selection model comparing zero-imputation against treating missing county-seasons as unobserved;
  3. Formally report the minimum detectable effect (MDE) curves as a function of enumerator accessibility and threshold size.

### Recommendation 4: Replace Log-Linear TWFE with Binary Trigger Concordance and PPML
- **Problem Fixed:** Eliminates econometric bias from \(\log(1 + x)\) transformations on zero-inflated counts and accounts for cluster leverage.
- **Execution:**
  1. Estimate extensive-margin flood impacts using Poisson Pseudo-Maximum Likelihood (PPML) with county and season fixed effects;
  2. Formulate anticipatory action trigger evaluations as binary classification tasks (e.g., predicting whether displacement exceeds 1,000 individuals), evaluating sensitivity, specificity, and Cohen's Kappa.

### Recommendation 5: Build a Downscaled "Data Risk and Decision Matrix" Tailored to ZOA
- **Problem Fixed:** Bridges the gap between coarse county-level academic statistics and ZOA's community-level operational mandate in Northern Bahr el Ghazal and Bor South.
- **Execution:**
  1. Create a structured decision table mapping specific data layers (NASA optical flood masks, CEMS-GFM radar, DTM Event Tracking, Mobility Tracking) to specific ZOA decisions (county prioritization, seasonal resource mobilization, 10-day community sandbagging);
  2. Explicitly flag the seasonal blindness window (July–September) and provide guidance on localized river-gauge monitoring along the Lol River.

---

## 6. Verification of Prompt Claims

| Specific Claim in Prompt | Verification Status | Detailed Evidence and Assessment |
| :--- | :---: | :--- |
| **NASA MODIS/VIIRS global flood product characteristics** (~232 m grid, daily, 2000–2025, tiles h20v08/h21v08, recurring vs. unusual classes). | **Verified** | Confirmed via [NASA Earthdata Global Flood Products User Guide](https://www.earthdata.nasa.gov/s3fs-public/2025-12/MCDWD_VCDWD_UserGuide_RevF.pdf). MCDWD/VCDWD daily products operate on ~250 m linear grids; tiles h20v08 and h21v08 cover South Sudan up to 10°N. |
| **Recurring flood mask defined using 2003–2024 archive.** | **Verified** | Confirmed by NASA documentation; the 22-year product archive was reprocessed in early 2025 using 3-month rolling windows across 2003–2024 to identify pixels flooded in \(\ge 7\) years. This confirms the look-ahead bias noted in the prompt. |
| **IOM DTM Event Tracking: group moves >50 households; no guarantee of comprehensive coverage.** | **Verified** | Verbatim confirmed in [IOM DTM South Sudan Readme and Methodological Notes](https://dtm.iom.int/dtm_download_track/28666?file=1&type=node&id=21306). |
| **2023 DTM Event Tracking collapse: 579 forced return rows, only 4 counties recording flood displacement.** | **Verified** | Confirmed by analyzing [IOM DTM South Sudan 2023 Datasets](https://dtm.iom.int/datasets/south-sudan-event-tracking-january-december-2023) and [CERF Allocation Reports](https://cerf.un.org/sites/default/files/resources/23-RR-SSD-59113_South%20Sudan_CERF_Report.pdf). The outbreak of fighting in Sudan (April 2023) diverted virtually all DTM field teams to border points (Joda/Renk) to track over 400,000 returnees, causing an operational collapse in flood displacement recording. |
| **Aweil Centre zero ET records in 2022 and 2024 despite severe OCHA flooding.** | **Verified** | Confirmed. [UN OCHA Flooding Situation Reports (Oct 2022)](https://www.unocha.org/publications/report/south-sudan/south-sudan-flooding-situation-report-no-1-31-october-2022) and [ACAPS Briefing Notes (2022)](https://www.acaps.org/fileadmin/Data_Product/Main_media/20221027_acaps_briefing_note_south_sudan_impact_of_floods.pdf) report Northern Bahr el Ghazal as the worst-affected state with over 250,000 people affected and tens of thousands displaced. The complete absence of ET records in Aweil Centre represents an institutional recording gap, not zero impact. |
| **ConvLSTM: 32×32 patches, three-state corridor, ambiguous lead time, trivial gain over persistence.** | **Partially Disputed / Unverified** | While the team's internal brief quotes these figures, the published state-of-the-art literature on the White Nile ([Rapson et al., 2026, INFLOW-AI v2.1](https://egusphere.copernicus.org/preprints/2026/egusphere-2026-66/)) demonstrates that ConvLSTM models are deployed to predict spatial inundation probabilities at a **6-dekad lead time** constrained by upstream lake transformers. A standalone 1-dekad patch ConvLSTM without basin-scale boundary constraints is hydrologically ungrounded and functionally redundant against simple persistence. |
| **ERA5 negative correlation (−0.11) reflects data failure.** | **Disputed (Scientific Interpretation)** | The claim that a negative correlation between ERA5 rainfall and county flood volume indicates poor flood mask quality is hydrologically incorrect. In the river-fed Sudd wetland, flooding is driven by remote equatorial lake discharge occurring months earlier, uncoupling local rainfall from local flood extent ([Copernicus GFM](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC131351/JRC131351_01.pdf)). |

---

## 7. Strategic Synthesis and Reviewer Conclusion

### Single Most Important Change
**Completely remove the ConvLSTM flood forecast evaluation from the research objective.** The team must reframe the capstone around a single, highly focused, and methodologically airtight objective: **"Empirical Evaluation and Risk Profiling of Public Flood and Displacement Data for Subnational Anticipatory Action in South Sudan."**

### Evidence that Would Reverse This Recommendation
If the project team can demonstrate that:
1. The ConvLSTM model code is already frozen, operates under a single unambiguously documented lead time (e.g., exactly 10 days), and was trained on strictly temporal out-of-sample splits (pre-2021) without spatial patch leakage;
2. The team has already computed change-based F1 scores (onset and recession) against independent Sentinel-1 SAR observations across Northern Bahr el Ghazal;
3. Stakeholder ZOA confirms in writing that a 32×32 patch forecast over Jonglei/Unity directly dictates their community-level sandbagging allocations along the Lol River;

then, and only then, would evaluating the forecast be justified within the capstone's final four weeks. In the absence of such evidence, proceeding with the forecast will dilute the capstone, obscure the genuine scientific value of the humanitarian data audit, and provide the stakeholders with unvalidated, potentially misleading operational tools.
