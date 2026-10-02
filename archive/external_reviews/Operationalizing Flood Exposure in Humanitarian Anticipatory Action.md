# Operationalizing Flood Exposure in Humanitarian Anticipatory Action

## Executive findings

**A population–agriculture weighted exposure index is not a standard operational trigger in humanitarian flood anticipatory action (AA).** INFORM Risk is a composite humanitarian-risk index, but its flood-exposure indicator is the annual expected population exposed—reported in absolute and relative terms—not a weighted blend of population density, cropland and livestock. Its overall score geometrically combines the three higher-level dimensions Hazard & Exposure, Vulnerability and Lack of Coping Capacity; that is different from defining *flood exposure itself* as a population–agriculture composite.[^1][^2][^3]

CERF/OCHA, IFRC, WFP, FAO and Start Network frameworks are context-specific. Operational activation usually depends on one or more forecast or observed hazard thresholds—river discharge, water level, rainfall, return period and forecast probability—sometimes plus a minimum predicted human impact. Exposure and vulnerability layers more often determine **where, whom and what to protect** after or alongside activation than enter a universally weighted cross-sector trigger.[^4][^5][^6][^7]

Where advanced impact models include population, cropland, grazing land and livestock, good operational examples calculate impacts **separately by exposure class**. Flood-PROOFS East Africa evaluates the same hazard–exposure–vulnerability model for each class rather than adding people, hectares and livestock units into one number.[^8]

A single normalized weighted index can nevertheless be built, but its weights and normalization are design choices rather than humanitarian standards. Weighted arithmetic aggregation permits full compensation: a low cropland score can reduce a high population/displacement score, and vice versa. In geographically segregated livelihood systems this can dilute a local crisis signal, particularly when results are averaged over large administrative units or divided by an administrative total.[^9][^10][^11]

The operational trend is therefore **shared hazard trigger, disaggregated impact products and sector/livelihood-specific targeting**, not necessarily two fully independent activation triggers. Separate triggers are appropriate when impact pathways, forecast sources or action windows differ; a common trigger remains useful when the same flood event drives all actions and coordination speed is paramount.[^12][^13][^14]

## Concepts that should not be conflated

| Concept | Operational meaning | Typical measure | Role in AA |
|---|---|---|---|
| Hazard | Physical flood process | Discharge, river level, rainfall, inundation depth, return period | Usually activates readiness or action |
| Exposure | People, livelihoods or assets located in the forecast inundation footprint | People, households, hectares, livestock units, roads | Estimates who or what could be affected |
| Vulnerability | Susceptibility of an exposed element to harm | Depth–damage/impact function, food insecurity, displacement status, social vulnerability | Refines predicted impact and prioritization |
| Coping capacity | Ability to manage impacts | Institutional, infrastructure and service indicators | Strategic risk ranking or impact adjustment |
| Targeting | Selection of places and recipients | Vulnerability criteria, livelihood type, operational reach | Determines delivery after/alongside activation |

OCHA describes a trigger as translating the hazard and an impact such as food insecurity or damaged housing into technical specifications. Its trigger-development requirements are historical/current hazard data, historical/expected impact data and forecast data; this does not prescribe a universal exposure composite.[^7]

## Question 1: Is a unified index standard?

### INFORM Risk

INFORM should not be read as evidence that flood AA normally combines population and agricultural land. Its flood component measures estimated average annual population exposed by combining flood hazard zones/frequency with population in those zones. Both absolute inhabitants and percentage of national population are retained, and the source documentation warns that the global data are suitable for broad risk screening rather than local land-use applications.[^15][^16][^1]

The overall INFORM Risk Index is composite:

\[
R = (H\&E)^{1/3} V^{1/3} C_{L}^{1/3}
\]

where \(H\&E\) is Hazard & Exposure, \(V\) is Vulnerability and \(C_{L}\) is Lack of Coping Capacity. This geometric mean reduces, but does not eliminate, compensation between dimensions. It does **not** imply an operational flood-exposure formula such as 50 percent population plus 50 percent cropland.[^3][^17]

### CERF/OCHA protocols

CERF provides finance to country frameworks but does not impose one cross-country population–agriculture formula. Frameworks normally pre-agree a forecasting mechanism, decision process, activities and finance; country trigger models are designed around available skill, lead time and priority impacts.[^18][^7]

Bangladesh illustrates the prevailing design. The 2020 framework used a readiness trigger when GloFAS forecast, with at least 50 percent probability, discharge above 100,000 cubic metres per second for three days—a roughly 1-in-5-year event—and an action trigger when the five-day national forecast put the Bahadurabad gauge 0.85 metres above danger level. Intervention unions were then identified using flood depth, affected-population and household-asset relationships, overlaid with a vulnerability layer.[^19]

The Bangladesh contingency context also referred to parallel impact quantities—at least 2 million people exposed, 10 percent displaced and 5,000 hectares of cropland inundated—but the documentation does not turn those unlike units into a weighted exposure score. They function as separate impact statements or thresholds.[^19]

Nepal likewise uses a two-stage hydrological trigger and separate trigger systems for the unconnected Karnali and Koshi basins. The action package is multi-sectoral—cash, WASH, protection/health services and FAO waterproof grain/seed storage—but activation is not based on averaging population and cropland exposure.[^20]

### IFRC/Red Cross

IFRC guidance requires analysis of forecasts, risk, historical impacts and vulnerability but allows quantitative or qualitative triggers developed through scientific analysis or consultation. It does not mandate a fixed exposure formula.[^6]

Uganda’s flood Early Action Protocol is concrete: GloFAS must forecast at least a 60 percent probability of a 5-year return-period flood, anticipated to affect more than 1,000 households, with a five-day lead and false-alarm ratio no greater than 0.5. Potential districts are ranked by exposed population rather than a population–cropland weighted index.[^21][^22]

### WFP and FAO

WFP guidance defines a threshold as hazard magnitude associated with impact, estimated from historical observations plus exposure and vulnerability. It calls for context-specific flood thresholds and sector-specific actions; it does not supply a standard population–agriculture weighting.[^5]

FAO guidance explicitly organizes indicators by hazard and agricultural sector, and recommends combining forecast indicators, seasonal observations and vulnerability indicators to anticipate impacts on different agricultural sectors. Inter-agency ENSO guidance then branches actions according to whether crop agriculture or livestock is important in the affected area.[^13][^23][^14]

### A relevant East African formula

Flood-PROOFS East Africa is an operational impact-based flood forecasting system supporting IGAD and African Union monitoring. It maps population, cropland, grazing land, GDP, livestock units and roads, but computes the following for **each exposure category**:

\[
I_{a,k}=C_{L}\sum_{p\in a}\sum_{c=1}^{3}H_{p,c}E_{p,k}V_{p,c}
\]

\[
RI_{a,k}=\frac{I_{a,k}}{E_{a,k}}
\]

Here \(a\) denotes an administrative region, \(k\) an exposure category, \(H\) the inundation/hazard mask, \(E\) the selected exposure class, \(V\) vulnerability and \(C_{L}\) lack of coping capacity. The equations are evaluated for every administrative region and every exposure class; the outputs preserve their natural units instead of summing people, hectares and livestock units.[^8]

### What weighting is common?

No common operational weighting such as 50:50 population–cropland or population density multiplied by agricultural share was found across the reviewed institutional protocols. The common mathematical patterns are instead:

- **Hazard threshold:** forecast probability that discharge, water level or rainfall exceeds a chosen return-period/danger threshold.[^22][^24]
- **Pixel impact by class:** \(H\times E_{k}\times V_{k}\), optionally adjusted for coping capacity, then spatially summed.[^8]
- **Absolute and relative exposure:** exposed people/assets and their share of the relevant administrative total, retained as parallel outputs.[^25][^8]
- **Composite strategic risk:** normalized indicators combined by arithmetic or geometric aggregation; weights sum to one, but choices are model-specific and require sensitivity analysis.[^11]
- **Multi-stage activation:** readiness at a longer lead time and action at a shorter, more certain lead time.[^24][^26]

## Question 2: Failure modes

### Compensability and dilution

For normalized population and agriculture scores, an arithmetic composite such as

\[
E^{*}=w_{p}P^{*}+w_{c}C^{*}+w_{l}L^{*}, \qquad w_{p}+w_{c}+w_{l}=1
\]

has full compensability. If a wetland/IDP zone has \(P^{*}=1\) but \(C^{*}=0\), equal population–cropland weights produce 0.5; a purely agricultural zone can also produce 0.5. Distinct crises become numerically indistinguishable, and a threshold above 0.5 would miss both. Composite-index literature identifies this as compensation: low values offset high ones, while aggregation causes loss of specificity and can mask important component information.[^10][^9][^11]

This is better termed **signal dilution or rank reversal** than literal cancellation because non-negative exposure values do not algebraically subtract. Actual spatial cancellation occurs only after a model averages, normalizes or ranks across unlike components or large areas; a pixel-level union or maximum rule would not have the same behavior.

### Ecological and scale effects

Administrative aggregation can hide small but severe hotspots. In the Flood-PROOFS relative-impact equation, a localized high-impact area is divided by total exposure across the first-level administrative region; if the denominator is large, the relative score can be low despite severe local harm. More broadly, global/national indices overlook subnational disparities, and global INFORM source data explicitly caution against local planning use.[^27][^15][^8]

In South Sudan this issue is acute because the Sudd is a dynamic wetland rather than a conventional river corridor. OCHA found global forecasts much less predictive there, no national forecast was available, and limited/noisy data did not establish a clear relationship between severe flooding and rainfall. A generic composite would not fix a failed hazard model.[^28]

### Unit and semantics problems

People, hectares, tropical livestock units, road kilometres and monetary assets are not commensurable. Adding raw quantities has no interpretable unit; normalization makes addition possible but embeds normative choices about scales, weights and whether one loss can compensate for another. It can also double count correlated indicators—population density, settlements and household counts—or confuse exposure with vulnerability, such as treating displacement or acute food insecurity as simply more exposure.[^10][^11]

Agricultural land is itself heterogeneous. Cropland can be fallow or at different growth stages; grazing exposure may matter where mapped cropland is zero; livestock are mobile; and seasonal calendars alter the action window. FAO therefore recommends sector-specific forecast, seasonal-observation, livelihood and vulnerability indicators rather than a static agricultural-area scalar.[^14][^13]

### Data and model failure

Exposure blending cannot repair inaccurate flood extent, biased rainfall, absent gauges or weak impact records. OCHA identifies impact data as a main AA limitation because it is often non-machine-readable, geographically incomplete or available for only one recent event. Trigger peer review also flags unclear performance benchmarks, missed activations, false alarms, insufficient impact data and the need for additional vulnerability layers.[^29][^7]

Flood-PROOFS reports limited extreme-event validation due to short gauge records, poorer performance in some smaller/equatorial basins, uncertain reservoir-release rules and coarse inputs. The South Sudan application also shows that a technically elegant regional model must not be assumed locally reliable in the Sudd without validation.[^28][^8]

### Protection invisibility

A crop-heavy index can underrepresent displacement, health, gender-based violence, disability and access risks that are not proportional to cultivated area. Protection guidance warns that standard triggers may not model lived experience and recommends soft triggers, community information and explicit inclusion of marginalized or unregistered groups.[^30]

### Threshold trade-offs

Higher trigger thresholds reduce false alarms but increase missed events; lower thresholds do the reverse. This forecast decision must be based on the relative cost of acting in vain versus failing to act, and on the lifetime and reversibility of the selected action—not hidden inside exposure weights.[^31][^32]

## Question 3: What happens in practice?

### Predominant operational architecture

The evidence supports a three-layer architecture:

1. **Activation:** a common physical or probabilistic flood trigger, sometimes with a minimum predicted human impact.
2. **Geographic prioritization:** disaggregated population, livelihood, asset and vulnerability layers identify intervention areas.
3. **Delivery:** sector- and livelihood-specific actions and beneficiary criteria.

This architecture is more common than either extreme: neither one universal exposure score nor completely independent sector triggers for every action. Asia-Pacific technical standards explicitly tell practitioners first to select priority impacts, then identify who or what is exposed, identify vulnerability indicators and generate an intervention map.[^12]

### Operational examples

| Case | Activation logic | Exposure/impact treatment | Implication |
|---|---|---|---|
| **INFORM Risk** | Strategic annual risk screening, not event activation | Flood exposure is expected annual exposed population, absolute and relative | Do not use it as evidence for a population–cropland AA trigger.[^1][^16] |
| **Bangladesh CERF/OCHA** | Two hydrological thresholds: longer-lead GloFAS readiness and shorter-lead national gauge action | Affected population, household assets, displacement and crop hectares appear as separate impacts; vulnerability ranks locations | Shared flood trigger, disaggregated impact/targeting.[^19] |
| **Bangladesh FAO delivery** | Uses the common flood activation | Separate intervention and recipient tracks for crop-dependent and livestock-dependent households | Livelihood disaggregation occurs in delivery even when activation is shared.[^33] |
| **Uganda Red Cross** | Probability/return-period trigger plus more than 1,000 households and an acceptable false-alarm ratio | Districts ordered by exposed population | Human exposure gate, not a crop-weighted composite.[^21][^22] |
| **Flood-PROOFS East Africa** | Five-day hydrological threshold and inundation model | Separate population, cropland, grazing, livestock, GDP and road impacts, each absolute and relative | Strong evidence for multi-track impact outputs.[^8] |
| **Somalia Start Ready / government framework** | Seasonal readiness, then forecast river levels crossing thresholds at seven Juba/Shabelle gauges | Multisector contingency actions; model hosted by SoDMA and aligned with WFP | Shared river trigger coordinates multiple sectors.[^34][^35] |
| **Nepal CERF/OCHA** | Separate two-stage triggers for two unconnected river basins | Multi-agency cash, WASH, health/protection and agricultural-asset protection | Geographic/basin separation where hazards are not linked.[^20] |
| **South Sudan 2022** | No formal automatic framework because forecast skill was inadequate; earlier flexible allocation based on very high standing-water risk | Flood extent, food-security projections, impact estimates, existing displacement and local expert input were triangulated | Contextual decision and separate crisis evidence replaced a false-precision composite.[^28][^18] |

### South Sudan as a decisive case

The South Sudan experience argues against forcing a unified exposure trigger. OCHA tested Nepal/Bangladesh-style forecasting but concluded that a standard formal AA trigger was not technically feasible because global performance was poor, national forecasts were absent and Sudd dynamics were complex. The analysis instead triangulated satellite flood extent, food-security projections, estimated impacts and field expertise.[^28]

CERF and the South Sudan Humanitarian Fund then advanced funding for Bentiu and surrounding areas based on persistent standing water and the high likelihood of compounding impacts. The intervention protected an IDP setting through dykes, WASH/public-health measures, infrastructure protection and targeted cash, including to female-headed households with older or mobility-impaired members. This is a displacement/protection/public-health pathway that cropland exposure would have represented poorly.[^18]

### Are true two-track triggers used?

Fully independent displacement/protection and crop-waterlogging activation triggers are **not yet the prevailing documented standard**. More often, organizations keep a common flood trigger but maintain separate impact layers, target groups and action packages. This avoids contradictory activation decisions while preserving livelihood and protection distinctions.[^26][^33][^12]

Separate triggers are nevertheless justified and used when hazards or hydrological systems are distinct. Nepal has separate basin trigger systems; Nigeria documentation reports a riverine trigger and separately monitored flash-flood trigger; FAO phased-AA guidance recommends staggered triggers linked to the timing and severity of impacts on agricultural subsectors.[^36][^37][^20]

## Recommended design for East Africa and South Sudan

### Keep an exposure vector

Use an exposure vector rather than a scalar:

\[
\mathbf{E}_{p,t}=(P,D,C,G,L,S,W)
\]

where the components can represent resident population, displaced population, cropland by crop stage, grazing land, livestock, settlements/shelters and WASH/critical infrastructure. Calculate hazard-specific impact separately for every component and retain both absolute and relative results.

### Use trigger gates

A defensible design would use:

- **Hazard gate:** locally validated probability, return period, river level or observed standing-water threshold.
- **Humanitarian impact gates:** activate if *any* critical track exceeds its threshold—for example, threatened/displaced households, inundated shelters/WASH facilities, cropland at a sensitive growth stage, or livestock/grazing exposure.
- **Convergence rule:** allow a technical committee to activate when several moderate indicators jointly show severe compounding risk, with documented reasons.
- **Safety valve:** community observations and protection information can override a model when hidden groups or rapidly changing displacement are absent from formal datasets.[^30][^12]

Logically, the sector decision can be written as:

\[
A=H\land(P\lor D\lor C\lor G\lor L\lor W)
\]

This non-compensatory rule prevents zero cropland from suppressing a severe displacement/WASH signal and prevents low resident population from suppressing major livelihood losses. Thresholds still require retrospective testing against impacts and operational costs.

### Preserve coordination

One fund-release decision can coexist with several impact tracks. CERF or Start Ready can release a common envelope when the hazard gate and at least one impact gate are met, while agencies draw down pre-agreed modules relevant to the activated tracks. This preserves speed and collective action without creating a scientifically misleading population–agriculture average.[^38][^18]

### Validate transparently

Back-test every track separately for hit rate, false-alarm ratio, missed activations, lead time and geographic error. Publish sensitivity tests for normalization, weights, administrative scale and missing data. If a summary score is retained for dashboards, it should never be the only activation evidence; component values and maps must remain visible.[^39][^11][^29]

## Bottom line

The proposition that humanitarian flood AA routinely defines exposure as a weighted blend of population density and agricultural land is not supported by the reviewed operational guidance or cases. INFORM’s flood exposure is population-based; CERF/OCHA and Red Cross protocols mostly trigger on forecast hazard thresholds; and the strongest East African impact-model example preserves population, crops, grazing and livestock as separate output classes.[^22][^1][^8]

Blending segregated livelihoods can dilute signals if normalized indicators are averaged, especially across large administrative areas. For South Sudan’s wetlands and displacement settings, the safer methodology is a locally validated hazard gate plus non-compensatory, disaggregated impact tracks for people/displacement/protection, crops, grazing/livestock and critical services, backed by a transparent expert/community override when forecast skill is inadequate.[^18][^28][^8]

---

## References

1. [Abstract](https://drmkc.jrc.ec.europa.eu/inform-index/Portals/0/InfoRM/Publications/INFORM%20Risk%20Concept%20and%20Methodology%202014.pdf)

2. [INFORM_Mid2018_v034.xlsx](https://drmkc.jrc.ec.europa.eu/inform-index/Portals/0/InfoRM/2018/INFORM_Mid2018_v034.xlsx)

3. [Multi-criteria decision analysis for site classification: assessing natural hazard risks for planning the location of educational facilities](https://unesdoc.unesco.org/ark:/48223/pf0000389073) - UNESCO Digital Library

4. [Anticipatory Pillar of the DREF brochure practice V2](https://www.ifrc.org/sites/default/files/2023-12/Anticipatory%20Pillar%20of%20the%20DREF%20brochure%20practice%20V3.pdf)

5. [[PDF] Forecast-based Financing (FbF) - Anticipatory actions for food security](https://www.anticipation-hub.org/Documents/Manuals_and_Guidelines/WFP-FbF_Anticipatory_actions_for_food_security.pdf)

6. [[PDF] INTERACTIVE GUIDANCE PACKAGE](https://ifrc.soutron.net/public/catalogue/en-GB/DownloadImageFile.ashx?objectId=30442&ownerType=0&ownerId=31681)

7. [Data Requirements for Anticipatory Action](https://centre.humdata.org/data-requirements-for-anticipatory-action/)

8. [Impact-based flood forecasting in the Greater Horn of Africa](https://nhess.copernicus.org/articles/24/199/2024/) - Abstract. Every year Africa is hit by extreme floods which, combined with high levels of vulnerabili...

9. [TYPE Original Research](https://digital.csic.es/bitstream/10261/341435/1/Melo_Introducing%20uncertainties%20in%20composite2022.pdf)

10. [This paper has benefited from the reviews and comments of Alex de Sherbinin (Senior Research](https://www.climatelinks.org/sites/default/files/asset/document/Design_Use_of_Composite_Indices.pdf)

11. [Frontiers | Introducing uncertainties in composite indicators. The case of the Impact Chain risk assessment framework](https://www.frontiersin.org/journals/climate/articles/10.3389/fclim.2022.1019888/full) - The use of composite indices is widespread in many fields of knowledge but a common problem associat...

12. [[PDF] for Anticipatory Action in Asia Pacific - Anticipation Hub](https://www.anticipation-hub.org/Documents/Manuals_and_Guidelines/TWG_AA_Technical_Standards_on_AA_in_Asia-Pacific.pdf)

13. [Course: Early Warning Indicators - FAO elearning Academy](https://elearning.fao.org/course/view.php?id=883) - Good practice shows that early warning systems should combine forecast indicators with seasonal obse...

14. [Standard Operating](https://interagencystandingcommittee.org/sites/default/files/migrated/2020-11/Inter-Agency%20Standard%20Operating%20Procedures%20for%20Early%20Action%20to%20El%20Nin%CC%83o-La%20Nin%CC%83a%20Episodes.pdf)

15. [[XLS] INFORM 2016 (az) - DRMKC](https://drmkc.jrc.ec.europa.eu/inform-index/Portals/0/InfoRM/2016/INFORM_2016_v030.xlsx)

16. [INFORM_CCA_2021_30092021.xlsx](https://drmkc.jrc.ec.europa.eu/inform-index/portals/0/InfoRM/2021/Subnational/CCA/INFORM_CCA_2021_30092021.xlsx)

17. [Data](https://thedocs.worldbank.org/en/doc/cf8eee7ff5029398f75e897b342e7320-0050122023/related/DRMKC-INFORM.xlsx)

18. [Thematic: Anticipatory Action](https://humanitarianaction.info/article/thematic-anticipatory-action)

19. [[PDF] Flood 2020, Trigger Analysis Bangladesh - Anticipation Hub](https://www.anticipation-hub.org/Documents/Reports/Anticipatory_Action_Pilot_2020__Trigger_Analysis_Bangladesh.pdf)

20. [CERF_Pamphlet-AA-Nepal_20220725](https://www.unicef.org/nepal/media/16556/file)

21. [EARLY ACTION PROTOCOL ACTIVATION FINAL REPORT - Adore](https://adore.ifrc.org/Download.aspx?FileId=839416)

22. [EARLY ACTION PROTOCOL](https://adore.ifrc.org/Download.aspx?FileId=763486)

23. [Early warning indicators](https://openknowledge.fao.org/server/api/core/bitstreams/9e2a9726-157c-4b9a-8d02-cec0d6b50e21/content)

24. [Executive Summary Bangladesh Monsoon Floods](https://www.anticipation-hub.org/Documents/Manuals_and_Guidelines/Anticipatory_Action_Framework_Bangladesh_Monsoon_Floods_OCHA.pdf)

25. [Assessing future risk of humanitarian crises using projections of climate-related hazards, population, conflict and other socioeconomic variables within the INFORM framework](https://www.tandfonline.com/doi/full/10.1080/20964471.2025.2535852) - This study uses the INFORM Climate Change model to estimate the impacts of climate change on humanit...

26. [Monitoring and evaluation of anticipatory actions for fast ...](https://www.anticipation-hub.org/Documents/Manuals_and_Guidelines/WFP-FbF-MEGuide-Oct2021.pdf)

27. [POLICYBRIEF](https://unu.edu/sites/default/files/2026-04/PB25.08_Bekaert,%20Fonton,%20Robert%20and%20Ruyssen.pdf)

28. [Flood Risk for South Sudan's 2022 Rainy Season](https://centre.humdata.org/flood-risks-for-south-sudans-2022-rainy-season/)

29. [Model Report - Chad Drought Anticipatory Action trigger](https://data.humdata.org/dataset/2048a947-5714-4220-905b-e662cbcd14c8/resource/f1ad9496-6e57-4ef8-9224-265c35ec849b/download/model-report-chad-drought-anticipatory-action-trigger.pdf)

30. [PROTECTION, GENDER AND INCLUSION IN ...](https://www.anticipation-hub.org/Documents/Manuals_and_Guidelines/PLAN-PGI_in_AA_Toolkit-Full-v2.pdf)

31. [Forecasting, thresholds, and triggers](https://iris.cnr.it/bitstream/20.500.14243/456178/1/1-s2.0-S2405880723000055-main_compressed.pdf)

32. [1](https://core.ac.uk/download/46563302.pdf)

33. [Bangladesh – Impact of Anticipatory Action](https://openknowledge.fao.org/server/api/core/bitstreams/91b0758a-f844-42f5-9736-bcbcdade652b/content)

34. [RISK](https://startnetwork.org/sites/default/files/2024-07/Start%20Ready%20Risk%20Pool%203%20Structuring%20report.pdf)

35. [World Bank Document](https://documents1.worldbank.org/curated/en/099618001282524663/pdf/IDU15a5837ca1bdbd1447118d951d68f2a5c7867.pdf)

36. [Regional mapping of anticipatory action capacities in the ...](https://www.anticipation-hub.org/Documents/Reports/Regional_Mapping_of_Anticipatory_Action_Capacities_in_the_Near_East_and_North_Africa_Agricultural_Sector.pdf)

37. [REPORT: From Triggers to Outcomes](https://www.anticipation-hub.org/Documents/Reports/From-Triggers-to-Outcomes-AAR-Nigeria.pdf)

38. [Remal](https://startnetwork.org/sites/default/files/2025-05/Remal.pdf)

39. [IMPACT-BASED FORECASTING](https://www.anticipation-hub.org/Documents/Manuals_and_Guidelines/RCCC_Impact_based_forecasting_Guide_2021-3.pdf)

