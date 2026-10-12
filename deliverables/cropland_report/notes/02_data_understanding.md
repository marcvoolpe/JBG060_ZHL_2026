# 2. Business and data understanding (report: "Business and Data Understanding", 4 points)

Long notes, 10 Oct 2026. The rubric asks for: prior studies and models used, how the data connect to the problem, properties of every dataset (including data we collected ourselves), and every term the research objective needs.

---

## 2.1 Prior studies (what we build on, what we change)

### Kerner et al. (2024), *How accurate are existing land cover maps for agriculture in Sub-Saharan Africa?* Scientific Data 11:486

- **What.** 11 public maps scored on 3,386 labelled points in 8 countries (Kenya, Malawi, Mali, Rwanda, Tanzania, Togo, Uganda, Zambia). No South Sudan.
- **How.** Random points per country (stratified by NDVI in Mali, where crop is rare); two or more people labelled each point blind to every map, from monthly 3 m PlanetScope (NICFI), Sentinel-2 and Google Earth; crop = sowing, growth or harvest seen within 12 months. Points where labellers disagreed were **dropped**. Accuracy from the population error matrix (Stehman and Foody 2019), with standard errors.
- **Results we use.** Mean F1 per country 0.21 (Mali) to 0.71 (Rwanda); below 0.7 in 7 of 8 countries. Unanimous crop on under 0.5% of every country. No single best map; WorldCover and GLAD reasonable choices; ASAP, GlobCover, Copernicus, ESA-CCI and Dynamic World among the weakest. In Mali (2% crop) Esri scores 0.97 accuracy and finds no crop at all: **accuracy misleads when crop is rare**, so we report precision, recall and F1. Map year and resolution only weakly related to accuracy.
- **Their recommendation we follow.** "Collect samples from regions of high disagreement between maps ... using stratified sampling in which consensus levels define strata" (Discussion). Our strata are exactly that.
- **What we change.** We keep disagreements (they inflate accuracy when dropped), we label from open imagery (NICFI ended in 2025), and we add South Sudan.

### Adebayo, Nakalembe, Skakun, ... Kerner, Becker-Reshef (2026), *Optimizing satellite-based cropland area estimation through integrated map accuracy assessment and stratified sampling design across six African countries.* Int. J. Applied Earth Observation and Geoinformation 148:105223

- **What.** Same group, next step: 7 maps (DE Africa, GLAD, Esri, Dynamic World, GLC_FCS30D, Copernicus, a majority-vote ensemble) in 6 East and Southern African countries, 2019.
- **How.** (1) Score the maps on one stratified reference sample (Stehman 2014 estimators, because the strata come from another map). (2) Turn each map's user's and producer's accuracy into a **relative efficiency**: how many points an area estimate needs with that map as strata (Skakun 2025). (3) Draw a second, independent sample with the most efficient map, estimate cropland area per country with a target coefficient of variation of 10%.
- **Results we use.** Choosing the right map saves 20-40% of the points. For a **rare class such as cropland, producer's accuracy (recall) matters more than user's accuracy**: a map that misses fields leaves crop hidden in the big "not crop" stratum, which inflates the variance. GLAD and DE Africa most efficient; no map best everywhere. **Pixel counting is biased**: in Zambia DE Africa counts 8.99 Mha, the sample estimate is 6.31 ± 0.93 Mha. Sample estimates correlate with FAOSTAT arable land (R² 0.89), but the authors stress that statistics are no ground truth either.
- **Their limitations we address.** Interpreter variability was "not formally quantified" (we report kappa and specific agreement for every pair of labellers); PlanetScope is proprietary (we use Sentinel-2 and Esri imagery, open); 2019 only (we label 2025, and they name 2024-2025 as future work); no use of the estimate for a decision (we take it to a flood trigger).

### What the two papers found for the maps we compare

Both papers score most of our maps with the same metrics we will use (precision = user's accuracy, recall = producer's accuracy, F1, each with a standard error). Transcribed per country in `cropland/reference_accuracy_literature.csv` (Kerner Table 1, p. 3; Adebayo Table 3, p. 7); summary in `deliverables/cropland_report/tables/published_accuracy_of_our_maps.csv`; figure 9.

| map | Kerner: mean F1 (8 countries) | Kerner: lowest F1 | Kerner: Mali F1 (accuracy) | Kerner: mean precision / recall | Adebayo: mean F1 / recall (6 countries) |
|---|---|---|---|---|---|
| GFSAD 2015 | 0.58 | 0.15 (Mali) | 0.15 (0.91) | 0.51 / 0.74 | not scored |
| GLAD 2019 | 0.65 | 0.33 (Mali) | 0.33 (0.96) | 0.68 / 0.68 | 0.64 / 0.66 |
| DE Africa 2019 | 0.63 | 0.43 (Uganda) | 0.46 (0.96) | 0.56 / **0.81** | 0.62 / **0.73** |
| WorldCover (v100, 2020) | 0.65 | 0.43 (Kenya, Mali) | 0.43 (0.95) | 0.72 / 0.65 | not scored |
| WorldCereal 2021 | not scored | | | | not scored |
| Esri LULC | 0.43 | **0.00 (Mali)** | **0.00 (0.97)** | 0.63 / 0.38 | 0.49 / 0.40 |
| Dynamic World | 0.34 | 0.12 (Mali) | 0.12 (0.94) | 0.63 / **0.30** | 0.34 / **0.27** |
| ASAP | 0.52 | 0.21 (Mali) | 0.21 (0.95) | 0.47 / 0.69 | not scored |

- **The F1 of zero.** In Mali, where only about 2% of the reference points are crop, Esri reaches 0.97 overall accuracy and an F1 of 0.00: it called every reference point "not crop" (Kerner et al. 2024, p. 3). Every map does badly in Mali (mean F1 0.21 over 11 maps). Aweil is a rare-crop landscape like Mali (the maps call 0.2-1.9% crop; CFSAM's modelled cereal area is 3.6%), so overall accuracy would tell us almost nothing there. That is why our scorecard reports precision, recall and F1, and why a map is judged on how much of the real crop it finds.
- **Dynamic World and Esri have the lowest recall** in both papers (0.27-0.40: they miss well over half of the real crop); DE Africa the highest (0.73-0.81), with lower precision. For a trigger that must not miss farmers, recall is the number to watch (and, by Adebayo et al., the one that matters most for sampling).
- **Versions differ.** The papers scored Esri and Dynamic World for their own reference years, WorldCover v100 (2020) and ASAP v02; we use Esri and Dynamic World 2025, WorldCover v200 (2021) and ASAP v04. GLAD 2019, DE Africa 2019 and GFSAD 2015 are the same products.
- **Majority vote.** Kerner's majority vote of 11 maps had one of the best mean F1 scores (0.65). Our equivalent in Aweil (at least 4 of 7 maps say crop) covers 0.07% of the land: it would find almost no cropland, so "combine the maps" is no way out here.

### Pacetti, Caporali and Rulli (2017), *Floods and food security: a method to estimate the effect of inundation on crops availability.* Advances in Water Resources 110:494-504

- The overlay behind "flood inundating cropland": "the intersection of remote sensed flood maps with administrative and land use maps", then crop statistics turn hectares into lost food (Bangladesh 2007, Pakistan 2010).
- Their own conclusion: "the remote sensing data by itself lacks the level of accuracy necessary in a comprehensive food security assessment" unless backed by onsite information. Our labelled sample is that onsite check, done remotely.

### Methods literature (design-based area and accuracy)

- **Olofsson et al. (2014)**, *Good practices for estimating area and assessing accuracy of land change* (RSE 148): stratified estimator of area with a confidence interval; sample size formula (Eq. 13).
- **Stehman (2014)**, IJRS 35: estimators when the strata are not the classes of the map being scored. Needed because our strata are agreement levels, and we score 8+ maps on the same points.
- **Stehman and Foody (2019)**, RSE 231: good-practice checklist (map-relevant, statistically rigorous, quality-assured, reliable, transparent, reproducible). Kerner et al. follow it; we do too.
- **Potapov et al. (2022)**, Nature Food 3: GLAD's method; its map under-counts Africa (map 190 Mha against a sample estimate of 208 ± 47 Mha, as quoted in our Sprint 3-4 plan from their Table 1; check before citing), and GLAD itself uses a sample for its official areas.
- **Cohen (1960)**, kappa; **Cicchetti and Feinstein (1990)**, positive and negative specific agreement (the fix for kappa when one class is rare).

### Stakeholder and course material

- **ZOA / ZHL Q&A 2 (21 Sep 2026)**: priority impact, trigger form, what a useful result looks like (file 03 lists the requirements).
- **Assignment**: ZOA considers three anticipatory actions: cash transfers, temporary flood defences, early harvesting ("highest stakes ... needs high confidence and only works in a specific window").
- **Anticipation Hub (2023), *A short overview of anticipatory action***: triggers "usually combine forecasts with data on impacts of past events, exposure and vulnerability". Cropland is the exposure part.
- **FAO/WFP CFSAM 2022 and 2025**: the official crop numbers (Section 2.3).

---

## 2.2 How the data connect to the problem

ZOA's trigger needs: (flood extent) x (cropland) x (damage per hectare) per community, with a known reliability. The course data give the flood extent (NASA MCDWD) and one cropland layer (ASAP). Our exploration (file 01) shows the cropland layer is the weak link: the eight layers differ by a factor 9 (Aweil) to 36 or more (Bor South) in how much crop there is, and barely overlap in where. Nobody has checked any of them in South Sudan. So we collect the one thing that is missing: an independent, labelled probability sample of the land in ZOA's areas, labelled for 2025, which gives (a) cropland area with a confidence interval that does not depend on any map, and (b) the accuracy of every map on the same points. The maps themselves are used only to decide *where* to put the points.

---

## 2.3 Datasets and their properties

### Course data (from ZHL)

| data | what we use it for | properties that matter |
|---|---|---|
| NASA MCDWD flood masks (2000-2025) | flooded cropland 2022 and 2025; flood cells of the overlay | MODIS Terra+Aqua, ~232 m (1/480 degree), daily; recurring (on average at least once every three years) vs unusual floods; tiles h20v08 (Aweil) and h21v08 (Bor South) stop at 10 N; cloud gaps not flagged (`cloud_frac` = 0 on every row) |
| ASAP crop mask v04 | one of the 8 maps scored | % crop per ~500 m cell (1/224 degree); a merge of older maps (GlobCover in most of Africa); among the weakest maps in Kerner et al. |
| Administrative boundaries (OCHA COD-AB) | study areas, county and state totals | 79 counties (admin 2), 10 states; Aweil 5 counties 3.09 M ha, Bor South 1.40 M ha, country 64.3 M ha incl. Abyei |

### The public cropland maps (collected, Google Earth Engine)

| map | year | pixel | built with | counts as crop |
|---|---|---|---|---|
| ESA WorldCover v200 | 2021 | 10 m | Sentinel-1/2, CatBoost, expert rules | annual crops sown and harvestable within 12 months; Africa validation: precision 71%, recall 51% |
| GLAD cropland | 2019 (2016-2019) | 30 m | Landsat metrics, bagged trees per 1 degree tile | herbaceous crops; fallow up to 4 years counts |
| Digital Earth Africa | 2019 | 10 m | Sentinel-2, random forest per zone | at least 0.01 ha sown and harvested within 12 months |
| ESA WorldCereal (temporary crops) | 2021 | 10 m | Sentinel-1/2 + weather, CatBoost per zone and season | temporary crops |
| Esri / Impact Observatory LULC | 2025 (and 2017-2024) | 10 m | Sentinel-2, deep network (U-Net), one global model, no time series | planted crops, incl. "fallow plots of structured land" |
| Google Dynamic World | 2025 (and 2016-2024), yearly mode | 10 m | single Sentinel-2 images, deep network, one global model | planted crops |
| GFSAD GCEP30 | 2015 | 30 m | Landsat, ensemble per zone | cultivated, fallow and plantations |

Each is made crop / not crop as in Kerner et al. (2024). They differ in year (2015-2025), definition (fallow in or out), input (Landsat, Sentinel-2, single images or time series) and training (regional vs one global model). We found no accuracy assessment of any of them for South Sudan, in their documentation or in Kerner et al. (2024) and Adebayo et al. (2026).

### Collected for the labels and our own map

| data | use | note |
|---|---|---|
| Sentinel-2 L2A (`COPERNICUS/S2_SR_HARMONIZED`) + Cloud Score+ | monthly image strips for labellers (2025, 2024 for fallow); 18 features | clear observations every month of 2025 (median 2-9 per month); thinnest August in Aweil, October in Bor South |
| Sentinel-1 GRD, descending, VH | radar curve for the cloudy months | no descending pass over Aweil January-April 2025 |
| Esri World Imagery (+ Wayback, Google Earth) | field shapes at sub-metre | capture date shown; 336 of 450 points have an image from the 2025 season |
| Google Open Buildings v3 | distance to homesteads | |
| JRC Global Surface Water, MODIS MCD64A1 | water and burn-scar features | |
| Google Satellite Embedding 2025 | black-box benchmark | |
| **Our labelled sample** | area estimate, accuracy of every map | 450 points, 2 labellers each (900 labels), 2025, 210 m box; file 04 |

### Statistics (for order of magnitude only)

| source | what | values |
|---|---|---|
| FAO/WFP CFSAM 2025 (19 Mar 2026) | cereal harvested area, traditional sector, by state and county | South Sudan 1,258,886 ha; Aweil counties 111,530 ha; Bor South 25,953 ha; yields 0.6-1.5 t/ha |
| FAO/WFP CFSAM 2022 (21 Jun 2023) | same, plus flood damage | 1,078,923 ha; Aweil 166,843 ha; Bor South 14,608 ha; **130,000 ha damaged by floods, 65,000 t cereals lost** |
| FAOSTAT (via World Bank WDI) | arable land, permanent crops | 2,394,700 ha arable (same value 2021-2024); permanent crops 0.13% of land |

Both are in `cropland/reference_statistics.csv` and `cropland/reference_national.csv`, with table numbers. CFSAM's area is modelled (population x share of households farming x area per household) and covers cereals in the traditional sector only.

### Other

- OpenStreetMap Lol river line (Overpass, 10 Oct 2026; `cropland/lol_river_osm.geojson`, ODbL), for the Lol strip.
- REACH Joint Market Monitoring (2025), only for the illustrative cash sizing: survival basket about USD 142-149 per 6-person household per month (May, August 2025), sorghum about USD 0.63/kg (October 2025). **Check against the factsheet before quoting** (we could read the figures only through a search summary).

---

## 2.4 Terms the reader needs (glossary for the report)

- **Cropland / cropped / fallow.** Our cropland = fields cropped in 2025 or fallow (field structure visible, not sown in 2025). "Cropped in 2025" is the part closest to "crops in the ground" for the trigger.
- **Agreement map.** For every 10 m pixel, how many of the 7 maps call it crop (0-7).
- **Stratum, stratified random sample.** The land split into groups (here: 0, 1-2, 3+ maps say crop) with random points drawn separately in each; each point carries the weight of its group's area, so extra points in a small group do not bias anything.
- **Probability sample / design-based inference.** Every pixel has a known chance of being sampled, so area and accuracy follow from the design, whatever the maps say.
- **Reference label.** What a person sees on the imagery at a sample point; the "truth" in this study (no field visits).
- **User's accuracy (precision)** of a map: of what the map calls crop, the share that is crop. **Producer's accuracy (recall):** of the real crop, the share the map finds. **F1:** their harmonic mean. **Overall accuracy** misleads when crop is rare.
- **Intersection over union (IoU).** Overlap of two maps' crop class: land both call crop divided by land either calls crop.
- **Cohen's kappa.** Agreement corrected for chance; **specific agreement** (positive / negative) when one class is rare.
- **Pixel counting.** Area = number of crop pixels x pixel area; biased by the map's errors. The sample estimate corrects it.
- **Coefficient of variation (CV).** Standard error / estimate. **Neyman allocation:** points per stratum in proportion to its weight x its spread. **Relative efficiency:** how many times fewer points one design needs than another for the same precision.
- **Anticipatory action, trigger, lead time.** Acting before a forecast hazard hits; the pre-agreed condition that releases money; how long before the event the condition is known (ZOA: 3 days minimum, 10 enough, 14 a robust upper bound).
- **Exposure vs damage.** Cropland under water is exposure; damage depends on depth, duration and crop stage.
- **Recurring vs unusual flood** (NASA MCDWD): recurring = at least once every three years on average at that location.
