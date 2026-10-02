# Critical Evaluation: County-Level Flood Decision Support for South Sudan

## Executive assessment

The proposed tool has a **real but narrower novelty than initially assumed**. No identified public operational product appears to publish exactly the proposed combination of (1) flood hazard, (2) disaggregated population/cropland/livelihood exposure, and (3) a county-level priority ranking explicitly designed to support NGO pre-positioning in South Sudan.

However, this does **not** mean that the underlying analytical problem is currently unsolved. Most components already exist across OCHA, IPC, ICPAC/IGAD, UNOSAT/Copernicus, REACH/IMPACT, WFP and Sudd monitoring products. More importantly, the evidence raises doubts about whether a dynamic county ranking is the operational bottleneck for NGOs, whether the hazard can be forecast with sufficient skill at a 2–3 month lead, and whether the proposed validation strategy can establish genuine predictive skill.

The strongest research contribution would therefore probably **not** be “build another flood-risk ranking.” A more defensible contribution would be to test whether combining existing hazard and exposure information actually produces **incremental decision value** for NGO pre-positioning, and under what forecast uncertainty and operational constraints that value exists.

---

## 1. Redundancy with existing humanitarian systems

### What already exists

South Sudan already has a substantial ecosystem of flood, food-security, humanitarian-needs and exposure information:

- **OCHA Humanitarian Needs Overview (HNO):** county/state-level severity and needs analysis, incorporating conflict, displacement, food insecurity, health, access and other factors.
- **IPC Acute Food Insecurity analyses:** projections and classifications of food insecurity at subnational level. These are not flood forecasts, but floods are among the contextual drivers considered in food-security analysis.
- **ICPAC / IGAD and Flood-PROOFS:** regional hydro-meteorological forecasting and flood early-warning information. Flood-PROOFS is oriented toward flood forecasting rather than NGO-specific exposure prioritization.
- **ICPAC seasonal outlooks:** seasonal rainfall/climate outlooks provide broad-scale forecasts, but are not equivalent to county-level flood-extent forecasts.
- **UNOSAT and Copernicus EMS:** satellite-derived flood extent and population exposure products, generally activated around significant events. These are primarily event-response/assessment products rather than seasonal county-prioritization systems.
- **REACH / IMPACT:** field-based flood and humanitarian assessments, including information on affected populations, livelihoods and infrastructure.
- **WFP seasonal monitoring:** food-security and seasonal-impact monitoring that incorporates flood impacts where relevant.
- **Sudd monitoring:** satellite and hydrological products already characterize the spatial and temporal dynamics of Sudd inundation.

### What appears genuinely absent

The distinctive element is the **integration layer**:

> forecast/observed hazard → population/cropland/livelihood exposure → county-level priority → NGO pre-positioning decision.

The research found no clear public operational system that provides precisely this complete pipeline for South Sudan.

That is a useful gap, but it should not be overstated. The novelty is mainly **integration and decision translation**, not creation of new hazard or exposure information.

### Important counter-evidence

Recent geospatial research on the Sudd indicates substantial agreement between multiple global flood models on the major flood-prone areas. A population-exposure study found that all five models examined agreed on key flood-prone areas, corroborated by satellite observations. However, estimated population exposure to a 100-year flood varied substantially depending on the flood model and population dataset: approximately **0.8–2.9 million people** in the study's comparison.

This simultaneously suggests:

1. there is substantial information already available about *where* chronic flood exposure is concentrated; and
2. the exact magnitude of exposure remains highly uncertain.

That weakens the case for a simple deterministic county ranking, while strengthening the case for an **uncertainty-aware comparison of alternative exposure estimates**.

---

## 2. Do NGOs actually make decisions through dynamic county rankings?

The operational logic of South Sudan humanitarian programming creates a major challenge for the proposed concept.

NGO geographic targeting is generally constrained by:

- existing field presence;
- established community relationships;
- government permissions and coordination;
- donor earmarking;
- cluster coordination;
- partnership arrangements;
- existing programme commitments;
- logistics infrastructure;
- security and humanitarian access;
- multi-year funding cycles.

Therefore, a ranking such as:

> County A = 1, County B = 2, County C = 3

does not automatically translate into:

> move NGO resources from County C to County A.

An NGO may have strong analytical evidence that another county is at greater flood risk while being unable to establish operations there within a few weeks.

### Consequence for the research design

The relevant question is therefore not simply:

> “Can we predict which counties will flood?”

but:

> “Can improved information change an operational decision that an NGO is actually able and willing to change?”

That distinction is crucial.

A useful tool might support **within-footprint resource allocation** rather than geographic relocation. For example, if an NGO already operates in three counties, the system could help decide:

- where to increase pre-positioned stocks;
- which roads or warehouses need contingency planning;
- which livelihood groups need additional preparedness;
- where to increase monitoring;
- which existing programme locations require earlier action.

This is considerably more plausible than assuming annual wholesale county reallocation.

---

## 3. Predictability of Sudd flooding

This is probably the largest scientific weakness in the original proposal.

The INFLOW project on the White Nile explicitly identifies insufficient hydrological forecasting capacity in the White Nile catchment as a constraint on anticipatory action. Its objective is specifically to improve early-warning and forecasting capability.

This is important because the proposed system assumes that combining:

- upstream lake levels,
- previous inundation persistence,
- seasonal rainfall,
- satellite observations

will produce sufficiently useful **2–3 month county-level flood predictions**.

The evidence does not currently justify assuming that.

### Why the Sudd is difficult

The Sudd is an enormous, spatially complex wetland. Flood dynamics depend on:

- upstream inflows;
- lake and river storage;
- routing through the White Nile;
- local rainfall;
- evapotranspiration;
- wetland storage;
- very slow hydrological response;
- interactions between permanent and seasonal wetlands.

Consequently, seasonal rainfall forecasts do not translate straightforwardly into county-level flood extent.

The long storage and routing times also mean that historical inundation patterns may contain a lot of predictive information—but that creates an important counterargument:

> if historical spatial persistence already identifies the same chronically affected counties, how much additional value does a seasonal forecast provide?

The available evidence suggests that major flood-prone areas of the Sudd are spatially persistent. The recent population-exposure/model-intercomparison work found strong agreement on the main flood-prone regions.

### Key research test

The proposed project should therefore compare at least three baselines:

**Baseline A — static vulnerability**
- historical flood frequency / chronic flood map;
- no annual forecast.

**Baseline B — seasonal forecast**
- rainfall / hydrological predictors;
- annual forecast.

**Baseline C — integrated model**
- hazard forecast + population + cropland + livelihoods.

The important result is not whether C produces a sophisticated ranking.

It is whether:

> **C materially outperforms A in predicting independent observed impacts early enough to change an operational decision.**

If it does not, the complexity is not justified.

---

## 4. “10–15 counties are affected every year”

This assumption should **not** be built into the project without explicit verification.

There is evidence of strong spatial persistence in Sudd flood-prone areas, but that is not equivalent to demonstrating that exactly 10–15 counties experience materially significant humanitarian impacts every year.

The project should distinguish:

- geographic inundation;
- population exposure;
- agricultural exposure;
- livestock exposure;
- displacement;
- infrastructure disruption;
- humanitarian needs.

A county can be chronically wet without experiencing the same humanitarian impact every year.

Therefore, the correct empirical test is:

> How much does county-level *impact* vary between years after controlling for persistent geographic flood susceptibility?

That is a much stronger research question than assuming annual variation is large or small.

---

## 5. Evaluation design: the circularity problem

This is a serious methodological issue.

Suppose the proposed predictor is:

> satellite-derived flood extent × satellite-derived population.

Then the evaluation target is:

> satellite-derived flood extent × satellite-derived population.

The model can appear highly accurate simply because it is being evaluated against a representation of the same underlying information.

This is not an independent validation.

### Better validation hierarchy

A stronger evaluation would use independent sources:

1. **DTM displacement data**
   - displaced population associated with flooding;
   - useful but spatially incomplete.

2. **OCHA affected-population figures**
   - useful for humanitarian impact;
   - affected by reporting and assessment coverage.

3. **REACH/IMPACT assessments**
   - potentially richer local information;
   - often geographically targeted rather than systematic.

4. **Government/cluster damage assessments**
   - potentially valuable;
   - variable availability and methodology.

5. **Infrastructure/road disruption**
   - potentially much more operationally relevant for pre-positioning.

6. **Agricultural impact observations**
   - crop loss / planted-area information;
   - likely to be sparse and heterogeneous.

### Fundamental problem

All humanitarian impact datasets have some degree of **access and reporting bias**.

Humanitarian organizations are more likely to collect information where:

- people are reachable;
- organizations already operate;
- security allows assessment;
- the event is considered significant;
- funding exists for assessment.

Therefore:

> “No reported impact” ≠ “no impact.”

This makes retrospective evaluation difficult, but not impossible.

The project should explicitly model missingness rather than treating missing observations as zero impact.

---

## 6. Logistics and the “6–7× cost” claim

The claim that wet-season transport can cost roughly 6–7 times as much as dry-season transport is plausible as an operational intuition, but the research did **not** establish sufficiently strong public evidence to treat 6–7× as a universal South Sudan parameter.

More importantly, even if the ratio is correct, the economic argument needs another step.

The relevant calculation is not:

> wet-season transport / dry-season transport.

It is:

> expected avoided logistics cost × probability that early information changes the procurement/pre-positioning decision.

For a small NGO, the benefit may also depend on whether transport is:

- directly contracted;
- locally procured;
- organized through WFP/Logistics Cluster;
- moved using shared logistics infrastructure;
- transported by UNHAS or another pooled service.

Therefore, savings at the humanitarian-system level do not necessarily equal savings available to an individual NGO.

### Existing practice

Dry-season pre-positioning is already a normal humanitarian logistics strategy in South Sudan.

This creates another counterfactual problem:

> if NGOs already pre-position before the rains, what exactly does the forecast cause them to do differently?

Possible incremental decisions include:

- **how much** to pre-position;
- **where within the existing footprint** to place stocks;
- **when** to move them;
- which commodities to prioritize;
- whether to expand preparedness to a marginal location.

Those are more defensible decision targets than simply “whether to pre-position.”

---

## 7. Flood-mask limitations

### MODIS / VIIRS optical imagery

Optical flood mapping has important limitations in South Sudan:

- clouds during rainy periods;
- difficulty distinguishing permanent water from newly inundated land;
- vegetation obscuring water;
- temporal gaps;
- wetland complexity.

This is particularly problematic in the Sudd.

SAR data such as Sentinel-1 are generally better suited to detecting inundation under cloud cover, although SAR also has its own challenges in vegetated wetlands.

Therefore, relying heavily on MODIS/VIIRS-derived annual flood masks risks turning data availability into apparent hydrological reality.

A better design would compare:

- optical flood observations;
- SAR observations;
- permanent-water masks;
- multi-year inundation frequency.

---

## 8. WorldPop population exposure

WorldPop should not simply be treated as ground truth.

South Sudan has:

- no recent comprehensive census comparable to many countries;
- large internally displaced populations;
- highly mobile populations;
- dispersed rural settlement;
- changing settlement patterns.

However, the evidence is more nuanced than saying WorldPop is simply unreliable.

The recent Sudd population-exposure comparison found that **WorldPop and GHSL-Pop performed relatively well in representing the clustered settlement patterns characteristic of the Sudd**, compared with other population products.

At the same time, total exposure estimates varied greatly depending on the population dataset and flood model.

Therefore, the right methodological treatment is:

> use multiple population datasets and propagate exposure uncertainty.

Not:

> choose WorldPop and call it ground truth.

---

## 9. ASAP cropland

The proposed use of a static ~500 m cropland layer is particularly questionable if the goal is to estimate **current agricultural losses**.

South Sudanese agriculture includes:

- small plots;
- dispersed cultivation;
- shifting cultivation;
- seasonal cultivation;
- changing agricultural footprints.

A static coarse-resolution cropland product can therefore be useful for broad regional characterization but is much weaker for precise annual agricultural exposure.

A more defensible question is:

> Does adding ASAP cropland improve county-level prediction of independently observed agricultural impacts compared with population + historical flood persistence alone?

If the answer is no, it should not be retained simply because it is available.

---

# Overall assessment

## (a) What is genuinely useful or novel?

The strongest potentially novel component is:

**integrating existing hazard, exposure and livelihood information into an operationally interpretable county-level decision-support layer.**

There is a real gap between:

> “Here is a flood map.”

and:

> “Given our existing operational footprint, these locations face the greatest expected humanitarian consequences, with this level of uncertainty, and these are the actions that could still be taken before access deteriorates.”

The second is much closer to an NGO decision-support product.

---

## (b) What largely duplicates existing systems?

The following are **not novel individually**:

- flood extent mapping;
- seasonal rainfall outlooks;
- hydrological monitoring;
- population exposure mapping;
- humanitarian needs/severity mapping;
- food-security projections;
- post-flood assessments;
- Sudd inundation monitoring.

The proposed contribution therefore should not be framed as creating a new flood-monitoring system.

---

## (c) Which assumptions are currently unsupported or contradicted?

| Assumption | Assessment |
|---|---|
| NGOs need a new county prioritization system | **Not established** |
| NGOs dynamically change counties every year | **Weak evidence** |
| 2–3 month county-level Sudd flood prediction is reliable | **Not established; important scientific gap** |
| Flood exposure varies enough annually to justify ranking | **Needs empirical testing** |
| ~10–15 counties are consistently affected | **Plausible in broad terms, but not demonstrated as stated** |
| Satellite exposure is valid ground truth | **No; circular if derived from same hazard data** |
| Humanitarian impact data provide unbiased validation | **No; access/reporting bias is substantial** |
| 6–7× transport premium is a robust NGO-level parameter | **Not adequately established** |
| Forecasting would change whether NGOs pre-position | **Weak assumption; pre-positioning is already standard** |
| WorldPop can be treated as ground truth | **No** |
| Static ASAP cropland accurately represents annual agricultural exposure | **Questionable** |

---

# A more defensible research contribution

Rather than asking:

> “Can we build a county-level flood priority ranking?”

I would reformulate the research question as:

> **Does integrating seasonal flood information with population and livelihood exposure provide measurable incremental value for humanitarian pre-positioning decisions in South Sudan compared with existing historical flood-risk information and operational targeting practices?**

This allows the project to discover that the answer could be:

- **yes**;
- **only for certain counties**;
- **only under certain forecast conditions**;
- **only for NGOs with an existing operational footprint**;
- or **no meaningful additional value**.

That is scientifically much stronger because the project is testing whether the proposed system is useful rather than assuming it is.

### Suggested experimental design

Compare:

**Model 0 — current practice / static baseline**
- historical flood persistence;
- existing NGO footprint;
- historical humanitarian severity.

**Model 1 — hazard only**
- rainfall / lake levels / hydrological indicators.

**Model 2 — hazard + exposure**
- population;
- cropland;
- livelihood zones.

**Model 3 — hazard + exposure + operational constraints**
- NGO footprint;
- road accessibility;
- logistics constraints;
- population/livelihood exposure.

Then evaluate:

- county ranking stability;
- lead time;
- discrimination between high/low impact counties;
- calibration;
- false positives;
- false negatives;
- performance against independent impact data;
- sensitivity to population/flood-map uncertainty.

Most importantly, compare every model against a **simple historical baseline**.

If the complex model cannot beat the historical baseline, that is itself an important research result.

---

# Bottom line

The evidence does **not** support presenting the proposed system as an obvious missing capability in South Sudan humanitarian response.

There is already extensive flood, climate, food-security, exposure and humanitarian-needs information. The strongest gap is not raw data availability but the **translation and integration of those data into an NGO-specific operational decision**.

At the same time, the scientific foundation for a 2–3 month county-level flood forecast in the Sudd is not yet strong enough to assume that a dynamic ranking will outperform a simple historical flood-persistence baseline.

The most defensible contribution is therefore an **incremental-value study**:

> **Does an integrated, uncertainty-aware flood × exposure analysis actually improve humanitarian pre-positioning decisions beyond existing information and simple historical baselines?**

That framing makes the project robust to a negative result. If the answer is no, the research has still identified an important operational and methodological limitation. If the answer is yes, the project can demonstrate precisely **where, when and why** the additional information has value.

## Key sources identified

- INFLOW / CLARE Programme — *Improved anticipation of floods on the White Nile*: identifies insufficient hydrological forecasting capability in the White Nile catchment as a constraint on anticipatory action.
- Recent study: *Geospatial Analysis of Population Exposure to Flooding in the Sudd Region, South Sudan*: compares global flood models and population datasets; reports substantial agreement in key flood-prone areas but large variation in estimated population exposure depending on model/data choice.
- OCHA South Sudan Humanitarian Needs Overview.
- IPC South Sudan Acute Food Insecurity analyses and projections.
- ICPAC / IGAD regional flood and seasonal forecasting products.
- UNOSAT and Copernicus Emergency Management Service flood mapping products.
- REACH / IMPACT South Sudan flood assessments.
- WFP seasonal and food-security monitoring products.
