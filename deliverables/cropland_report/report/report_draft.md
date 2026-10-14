<!-- Generated from report_draft.tex by draft_to_markdown.py: edit the .tex, then rerun. -->

# Which cropland is under water? Checking the public maps behind a flood trigger in South Sudan

*Group 1, JBG060. Draft, 14 October 2026.* Marks: **[...]** still to write or make; *(pending decision N)* waits for the group (REVIEW_PLAN.md); > **Idea.** suggestions for cutting.

## 1. Context / Problem Background / Motivation of Analysis

Floods hit South Sudan every year, and since 2019 they have been the largest in the satellite record. ZOA International wants to act before a flood damages livelihoods: anticipatory action. It works in two flood-prone areas, the five Aweil counties along the Lol river and Bor South on the White Nile (ZOA International and Zero Hunger Lab, 2026). About 80% of rural communities there live mainly from farming, and the impact ZOA names first is a harvest lost to flooding. Its example trigger is "a flood which inundates cropland resulting in at least y% of total yield reduction".

Such a trigger multiplies two maps: where the water will be, and where the fields are (Pacetti et al., 2017). Most effort goes into the first. The second is taken from one of several free, global cropland maps, and ZOA itself suspects that the data "might not capture agricultural land fully". Nobody has checked these maps in South Sudan: the two largest accuracy studies of African cropland maps leave the country out (Kerner et al., 2024; Adebayo et al., 2026). Where those studies did look, maps often failed exactly where crop is rare. In Mali, the Esri map reaches an overall accuracy of 0.97 with an F1 of 0.00, because it calls almost nothing crop.

In ZOA's areas the maps disagree so much that the cropland map, not the flood, decides whether a trigger fires. For the 2022 flood, the same overlay gives 432 or 5,805 ha of flooded cropland in Aweil, depending only on which map is used. A trigger built on such a number cannot be trusted until someone measures how much cropland there is, with an honest error bar, and how wrong each map is there. That is what this project does.

## 2. Business and Data Understanding

**The decision.** ZOA's anticipatory action follows a chain: a forecast, a pre-agreed trigger, and early action such as cash transfers, temporary flood defences and early harvesting (ZOA International and Zero Hunger Lab, 2026; Anticipation Hub, 2023). Cropland enters at three points. It sets whether the trigger fires (how much cropland lies under the forecast water), how large a funding request is (hectares to households to cash), and who is reached (whose fields are on the map). ZOA asks for numbers with a stated certainty, and warns about both kinds of error: a miss leaves people without help on time, and a false alarm spends scarce resources and costs trust. Zero Hunger Lab supports ZOA with data analysis and asked what public data can and cannot tell them.

**Prior work.** Kerner et al. (2024) scored 11 public cropland maps against labelled points in eight African countries. Mean F1 per country ranged from 0.21 to 0.71, land that all maps call crop covered under 0.5% of every country, and overall accuracy misled wherever crop was rare. Adebayo et al. (2026) turned map accuracy into the number of labelled points an area estimate needs (relative efficiency) and showed that, for a rare class, a map's recall matters most. Both studies estimate area from a stratified probability sample (Olofsson et al., 2014; Stehman, 2014): a design that stays unbiased whatever the quality of the maps, unlike counting a map's pixels.

**Data.** Table 1 lists the data. The course provided NASA MCDWD flood masks (NASA LANCE, 2025), the ASAP crop mask (Fritz et al., 2024) and county boundaries. We added seven public cropland maps (Zanaga et al., 2022; Potapov et al., 2022; Burton et al., 2022; Van Tricht et al., 2023; Karra et al., 2021; Brown et al., 2022; Thenkabail et al., 2021), Sentinel-1 and Sentinel-2 images and dated sub-metre imagery to label points, and the FAO/WFP crop assessments (FAO and WFP, 2023; FAO and WFP, 2026), whose cereal area is modelled from population and household figures, not observed.

**What the data show.** The maps tell seven stories. In the Aweil counties they call between 0.22% and 1.92% of the land crop, all below the crop assessment's cereal area (3.6%). In Bor South, Dynamic World calls 9.0% crop while no other map exceeds 0.25%. Where two maps do call crop, it is mostly different land: the best pair shares 0.16 of its crop area, the median pair 0.04 (Figure 1), and all seven agree on about 0.5 ha out of 3,085,318 ha. The same pairs agree on 97-99% of all pixels, because most land is "not crop" everywhere. This is the problem in one number: agreement on empty land hides disagreement on fields.

**Terms.** *Precision* (user's accuracy) is the share of a map's crop that is really crop; *recall* (producer's accuracy) is the share of real crop the map finds; *F1* combines the two. A *stratum* is a part of the area sampled separately. *Cropland* means a box with a cropped or a fallow field; *cropped in 2025* counts cropped fields only.

*Table 1. Data used. Course data from Zero Hunger Lab; the rest collected by us.*

| Data | Use | Source |
|---|---|---|
| NASA MCDWD flood masks, 2000-2025, about 232 m | flooded cropland, 2025 and earlier floods | course |
| ASAP crop mask v04, about 500 m | one of the maps scored | course |
| County boundaries | study areas, totals | course |
| WorldCover 2021, GLAD 2019, DE Africa 2019, WorldCereal 2021, Esri 2025, Dynamic World 2025, GFSAD 2015 | strata, maps scored | Earth Engine |
| Sentinel-2 L2A, Sentinel-1, Esri sub-metre imagery | labelling, features | Earth Engine, Esri |
| Google Open Buildings v3, Satellite Embedding 2025 | features | Earth Engine |
| 450 points, two blind labels each, 2025 | reference sample | ours |
| FAO/WFP crop assessments 2022, 2025 | outside check | FAO/WFP |

![Figure 1](../figures/03_pairwise_iou_aweil.png)

*Figure 1. Aweil counties: overlap of the crop class of every two public maps (intersection over union). The same pairs agree on 97-99% of all pixels, because most land is "not crop" in every map.*

## 3. Research Objective

We estimate how much land in ZOA's two areas was cropland in the 2025 season, with a 95% interval that does not depend on any map; measure how accurately seven public maps, the course's ASAP mask and a readable map of our own capture that cropland there; and show how the choice of map changes the flooded-cropland number a trigger would use.

This breaks down into four measurable sub-objectives: (1) the cropland area of each study area, for cropland and for cropped in 2025, with a 95% interval; (2) precision, recall and F1 of every public map on held-out points, per area; (3) the same scores for a map built from rules a person can read; (4) flooded cropland under each map against the labelled sample, whether a trigger would fire, and how many points a yearly check needs.

**Scope and assumptions.** The reference is what two trained people see on satellite images; there were no field visits. One season (2025), two areas; results hold there only. A point stands for the 210 m box around it. Flood masks are taken as given; we do not forecast floods.

**An adequate solution** states its uncertainty, reports misses and false alarms separately, is readable and repeatable by local staff, and is judged where ZOA works (ZOA International and Zero Hunger Lab, 2026). Table 2 turns these into measures. The objective was feasible within the course: the sample was drawn, labelled twice and scored in four weeks.

## 4. Approach

The approach has four steps (Figure 2): draw a probability sample where the maps disagree, label it twice, build a readable map from it, and estimate area, accuracy and flooded cropland. The protocol was written and frozen before labelling; every later change is dated, with its reason, in a change log.

### Reference sample

We stacked the seven public maps on a 10 m grid and split each area by how many call a pixel crop: no map (stratum A, 95.0% of Aweil), one or two (B), three or more (C). Such agreement strata put points where the maps disagree and trust no single map (Kerner et al., 2024). We drew 450 random points at least 100 m apart: 150, 90 and 90 in Aweil's strata, 60 and 60 in Bor South (its stratum C was too small and was merged into B). Before anyone labelled, each stratum was split at random into one third calibration points (to build our map) and two thirds test points (to score every map).

### Labelling

Each point stands for the 210 m box around it: in a pilot of 30 points, five labellers could not judge a single 10 m pixel (kappa 0.00-0.38). Two of the five group members label every box, independently and blind to all maps. They see monthly Sentinel-2 images of 2025, a radar curve for the cloudy months and the most recent sub-metre image with its date. A written key asks for four cues: bare soil before sowing, green-up, harvest earlier than the surrounding grass, and field shape. A box is *crop* if any field in it was cropped in 2025, *fallow* if it holds a field that was not, and *not crop* otherwise; the labeller also estimates the share of the box that is cropland (none, under 10%, 10-25%, 25-50%, over 50%). Disagreements are kept, not settled by a third person: a split point counts half in the area and is left out of accuracy.

### Our readable map

For every box we computed 18 features in Google Earth Engine, each summarising the box by its most crop-like part: the cues above as numbers (minimum greenness and bare-soil index in April-May, green-up, the drop at harvest compared with the 500 m surroundings, texture and edge density), dry-season greenness for trees, water occurrence, four months of radar, burned area, and the distance to the nearest building from Google Open Buildings.

*Rule 1* is a decision tree fitted on the 125 calibration points where both labellers agree (41 of them crop). Its depth (2, 3 or 4) was chosen by 5-fold cross-validation, taking the smallest depth within 0.02 F1 of the best; it was then frozen in a dated file before any test label was read. The result has one rule with two conditions: *crop if there is a building within 333 m and the box has field edges*. The same file is applied in Python for scoring and in Earth Engine for the map (10 m in the study areas, 30 m for the country); a test checks that both give the same label at every calibration point. Two random forests, on the 18 features and on Google's Satellite Embedding, show what a black box gains over readable rules. Two logistic regressions answer the group's question "trees or logistic regression?": they were chosen by repeated cross-validation on the calibration points only, frozen, and scored once. *(pending decision 2)*

### Estimation

*Area*: the stratified mean of the labelled share of each box, weighted by stratum area (Olofsson et al., 2014), using the mean of the two labellers. The share of boxes that hold any cropland is reported as an upper bound. *Accuracy* of every map on the test points: precision, recall and F1 with standard errors, using estimators for strata that are not map classes (Stehman, 2014); a public map says crop at a point when any pixel of the box is crop. *Flooded cropland*: the 2025 flood extent (June-December) laid over every map and over the labelled sample. Because our labels describe today's cropland, we also laid the floods of 2000-2025 over it, as a scenario: how much of today's cropland would a flood like that one put under water? *(pending decision 8c)* For those years the sample's flooded cropland is estimated as the cropland share of the sample boxes on flooded land times the flooded area, which the flood mask gives exactly (a ratio estimator), and only when at least five points lie on flooded land.

**[figure to make: method diagram: seven public maps, agreement strata, 450 random points, calibration and test split, two blind labels, then area with interval, scores of every map, Rule 1 and the flood overlay]**

*Figure 2. The approach, from the public maps to the area estimate, the scores and the flood overlay.*

## 5. Evaluation Methodology

Each part is judged on its own terms (Table 2). *Labels*: agreement and Cohen's kappa between the two labellers, with positive and negative specific agreement because crop is rare and kappa then misleads (Cohen, 1960; Cicchetti and Feinstein, 1990). *Area*: the estimate with its standard error and a 95% interval. *Maps*: precision, recall and F1 on test points only; maps whose intervals overlap are not ranked. Overall accuracy is never used to rank, because it rewards a map that finds nothing where crop is rare (Figure 3). *Use*: whether each map's flooded cropland gives the same trigger decision as the sample.

We checked the interval itself by simulating our exact design. The usual ±1.96 SE interval held the true area only 47%-94% of the time, every miss below the truth, because stratum A often holds no cropland point at all. We therefore also report an adjusted upper bound: per stratum at least the variance the stratum would have with one more cropland and one more empty box. It reached 94%-100% coverage in Aweil. *(pending decision 1)* The trigger check uses the same cautious bound, capped at the land that flooded. *(pending decision 8b)*

Two further measures address ZOA's wish for a cheap, local check: the number of points needed for a 20% coefficient of variation with our strata and with strata built from a single map (Adebayo et al., 2026), and the hours the labelling took. Qualitatively, we broke each map's errors down by what the labellers saw (land cover, crop cues, distance to buildings, share of the box) and looked at images of the worst errors.

*Table 2. Criteria for an adequate solution and how we measure them.*

| Criterion (from ZOA and ZHL) | Measure |
|---|---|
| State how certain we are | 95% intervals on area, standard errors on scores, simulated coverage |
| Misses and false alarms both cost | recall and precision reported separately |
| Relevant to the decision | trigger decisions per map against the sample |
| Transparent, interpretable | conditions and features of Rule 1; F1 lost against a black box |
| Local, and cheap to repeat | scores per area; points and hours a yearly check needs |
| Whose farmland is seen | recall per map; errors by distance to buildings and field size |

![Figure 3](../figures/09_published_accuracy_of_our_maps.png)

*Figure 3. F1 and recall of the maps we compare, as published for other African countries (Kerner et al., 2024; Adebayo et al., 2026). Ringed: Mali, where Esri has 0.97 accuracy and an F1 of 0.00.*

## 6. Results

**Labels.** On all 450 points the two blind labellers agreed on cropland versus not at 85.6% (Cohen's kappa 0.70; Aweil 83.3%, kappa 0.68). In Bor South agreement was high but almost only on "not crop" (kappa 0.14): the few boxes anyone called cropland were rarely confirmed. At 41 of the 53 points where they split, one labeller saw field shapes and the other did not. They disagreed about whether a field is there, hardly ever about the land cover. Fallow was used 7 times in 900 labels, so "cropland" and "cropped in 2025" differ by less than 0.1 percentage point; we report cropland.

**Cropland area.** In the Aweil counties, 3.8% of the land is cropland: 116,500 ha, with a 95% interval of 76,700-183,100 ha (Table 3). Every public map counts less: between 0.22% and 1.92% of the land, or 6%-51% of the sample's estimate (Figure 4). In Bor South, cropland is rare: 0.38% of the land, 5,400 ha (1,000-16,500). There the maps scatter around it, from almost none to Dynamic World's 9.0%, 23 times the sample's estimate. Boxes that hold any cropland cover 14.3% of Aweil and 1.5% of Bor South: fields are small and scattered, which is why pixel counts and box counts differ so much.

**Map accuracy.** On the 186 Aweil test points (Figure 5), F1 ranges from 0.03 (Dynamic World 2025) and 0.06 (Esri 2025) to 0.55 (WorldCereal 2021). Esri, WorldCover, GLAD and ASAP have a precision of 1.00 but a recall of only 0.03-0.28: when they say crop they are right, but they miss most fields. Dynamic World is low on both (precision 0.10, recall 0.02). The recall of WorldCover, GLAD, GFSAD and Dynamic World is below every value published for them elsewhere in Africa. Rule 1 reaches an F1 of 0.72 (0.55-0.90; precision 0.70, recall 0.75). Its interval overlaps those of WorldCereal, DE Africa, ASAP, GLAD and WorldCover, so by our own rule it is not ranked above them; it is clearly above Esri, Dynamic World and GFSAD. The random forests (0.71-0.76) are not clearly better, and the logistic regressions are not better either (0.61-0.66): they find more fields (recall 0.84) but call more empty land crop (precision 0.48-0.54). *(pending decision 2)* In cross-validation on the calibration points, trees (0.85-0.86) and logistic regressions (0.87-0.88) were just as close. In Bor South none of the 74 test points both labellers agree on is cropland, so recall cannot be computed; Dynamic World calls crop on 44 of the 74 boxes where the labellers saw no field, and the other maps on at most one.

**Where maps fail.** Rule 1's false crop lies within 250 m of buildings and its missed crop mostly farther away: it is, in effect, a "fields around homesteads" rule. The logistic models make more false crop in stratum A (9-12 of 122 empty test boxes, against 5 for Rule 1), where most of the land is, which is why their precision drops. Dynamic World's false crop in Bor South is open land where the labellers saw no field: grassland.

**Flooded cropland.** In 2025, 10,314 ha of the Aweil counties flooded at least one day, and the public maps put 10-307 ha of cropland under water. In Bor South 29,419 ha flooded; every public map shows at most 10 ha of flooded cropland except Dynamic World, with 1,606 ha. The sample cannot say which is right: only 1 of the 330 Aweil points and 2 of the 120 Bor South points lie on flooded land, so in 2025 it "cannot tell" at any trigger threshold from 100 to 5,000 ha. *(pending decision 8b)* This is a negative result about our design, not about the maps.

Past floods give the sample more to work with (Figure 6). *(pending decision 8c)* In 9 of the 26 years enough sample points lie on flooded land in Aweil, and in every one of them the sample puts 4-16 times more of today's cropland under water than the median public map. For a flood like 2022 (53,646 ha flooded; 9 of the 11 sample points on flooded land hold cropland) the sample estimates 7,263 ha (639-14,336), against 331-3,572 ha by the public maps. Played back as a trigger, the sample confirms a 500 ha trigger in 2008 and 2022; with Esri, GLAD or WorldCover that trigger would have stayed silent in 2022. Figure 7 shows where: WorldCereal shows crop in 1,646 of the 10,184 flooded cells of 2022, and our map adds 3,627, along the Lol and in the east of the area.

**Cost of a check.** With our strata, a 20% coefficient of variation on Aweil's area needs about 124 points; strata from a single public map need 112-149, depending on the map. Our design is not clearly cheaper than one built on the best single map, but it does not depend on choosing that map beforehand. Bor South would need about 1,240 points under any design: cropland is too rare there for a sample of 120. Labelling took a median of 0.5-1.0 minutes per point and 2.7-7.3 hours per person for 180 points.

*Table 3. Cropland area in 2025 from the labelled sample: estimate and 95% interval (lower bound as usual, upper bound adjusted).*

|  | Aweil counties (3,085,318 ha) share of land | ha | Bor South (1,396,328 ha) share of land | ha |
|---|---|---|---|---|
| Cropland (cropped or fallow) | 3.8% (2.5%-5.9%) | 116,500 | 0.38% (0.07%-1.2%) | 5,400 |
| Upper bound: box holds cropland | 14.3% |  | 1.5% |  |
| CFSAM 2025 cereal area (modelled) | 3.6% | 111,500 | 1.9% | 26,000 |

![Figure 4](../figures/14_area_vs_maps.png)

*Figure 4. Share of the land that is cropland: each public map (pixel count, blue) against our labelled sample (estimate and 95% interval, orange).*

![Figure 5](../figures/15_scorecard.png)

*Figure 5. Precision, recall and F1 of every map on the Aweil test points, with 95% intervals. Orange: our models; blue: public maps; dashed: agreement between the two labellers (0.86).*

![Figure 6](../figures/12_flood_history.png)

*Figure 6. Today's cropland under every flood of 2000-2025: the public maps as a range with their median, our labelled sample with 95% intervals in the years with at least five sample points on flooded land.*

![Figure 7](../figures/13_flood_map_aweil_2022.png)

*Figure 7. The 2022 flood in the Aweil counties, cell by cell (232 m). Left: flooded cells where WorldCereal 2021, the best public map on our test points, shows crop. Right: the cells our map adds, and the sample points on flooded land.*

> **Idea.** Too many figures for 2,000 words: keep 5 and 6, and Table 3; move 4 and 7 to the poster, 1 and 3 to the appendix or cut.

## 7. Discussion

**What it means for ZOA.** The public maps miss most fields in Aweil, and a trigger built on them would stay silent in exactly the floods that matter: the 2022 scenario shows a 500 ha trigger that Esri, GLAD or WorldCover would not have fired. Overall accuracy would not have warned anyone; recall does. For ZOA this gives three practical rules: never choose a map by its overall accuracy; in Aweil use WorldCereal or our map and avoid Esri and Dynamic World; in Bor South avoid Dynamic World, which calls open grassland crop. The cropland area itself should come from a labelled sample with its interval, not from any map.

**An outside check.** The FAO/WFP crop assessment models cereal area from population and household figures, independently of any image. In Aweil its 111,500 ha fall inside our interval and close to our estimate of 116,500 ha, while every public map is below both. In Bor South its 26,000 ha lie above our upper bound. Possible reasons: flood-recession plots planted after the water drops, which a 2025 image may not show as fields; few cropland points in a sample of 120; and an assessment that models rather than measures. Bor South needs more points before any number there is firm.

**Strengths and weaknesses.** The estimates rest on a probability sample with known inclusion probabilities, labelled twice and blind, with a protocol frozen before labelling and a model frozen before testing. The weaknesses are as clear. The reference is what people see on images, not on the ground; two careful labellers disagree on one point in seven, mostly on whether a small field is there. One season and two areas. Few cropland test points in Bor South and in stratum A, which widens every interval. The 210 m box makes our map an upper bound on location: it shows where fields are near, not their exact edges. Some analyses were added after the first results were known (logistic models, the flood scenario and its minimum of five points); they are marked as such and never changed a frozen result.

**Is the objective met?** Sub-objective 1 is met: an area with an interval that does not depend on any map. Sub-objective 2 is met in Aweil and only partly in Bor South, where recall cannot be computed. Sub-objective 3 is met: a two-condition rule that local staff can read scores as well as the black boxes. Sub-objective 4 is met for the maps and for big past floods, but not for the small 2025 flood, where the sample has almost no points on flooded land.

**Positive and negative impacts.** Used well, the check means fewer silent misses where maps under-count fields, fewer false alarms where a map calls grassland crop, numbers with a stated uncertainty, and a check cheap enough to repeat each season. It also carries risks. A checked number for two areas can be read as valid everywhere; our national map is not checked outside them. The sample gives area, not location, so targeting still needs a map and local knowledge. Improving the map in ZOA's areas does nothing for farmers elsewhere. In a conflict setting, maps of who farms where can touch land claims, so they should be shared at the level ZOA needs and no further.

## 8. Conclusion

In ZOA's two areas, the public cropland maps do not show the farmland a flood trigger depends on. In the Aweil counties, 3.8% of the land is cropland (116,500 ha, 76,700-183,100), while every public map shows 0.22%-1.92%. Most maps find only a small part of the fields, and two of them, Esri and Dynamic World, find almost none. In big floods, a trigger built on such maps would see a fraction of the cropland under water and stay silent. A small labelled sample, labelled twice and blind, gives an honest number and tells which map to trust where; a two-condition rule built from it does as well as the best alternatives we tried.

We recommend that ZOA (1) base the cropland part of a trigger on a labelled sample with its interval, with extra points on flood-prone land so that flooded cropland gets its own estimate; (2) choose maps by recall and precision in its own areas, never by overall accuracy: WorldCereal or our map in Aweil, not Esri or Dynamic World, and not Dynamic World in Bor South; (3) repeat the check each season, about 150 points or a few hours per labeller, with the tool and configuration we provide for other areas; and (4) collect a few field points with its own staff to check the labels. Next steps for research are crop stage and flood duration, which decide how much of a flooded field is lost.

## References

- ZOA International; Zero Hunger Lab (2026). JBG060 Q&A 2: Flood dynamics in South Sudan. Stakeholder slides, 21 September 2026
- Pacetti, Tommaso; Caporali, Enrica; Rulli, Maria Cristina (2017). Floods and food security: A method to estimate the effect of inundation on crops availability. Advances in Water Resources
- Kerner, Hannah; Nakalembe, Catherine; Yang, Adam; Zvonkov, Ivan; McWeeny, Ryan; Tseng, Gabriel; Becker-Reshef, Inbal (2024). How accurate are existing land cover maps for agriculture in Sub-Saharan Africa?. Scientific Data
- Adebayo, Adebowale Daniel; Nakalembe, Catherine; Skakun, Sergii; Frimpong, Diana Botchway; Ginsburg, Alana; Gadhiya, Yash Hitesh; Adjei, Monica; Kerner, Hannah; Becker-Reshef, Inbal (2026). Optimizing satellite-based cropland area estimation through integrated map accuracy assessment and stratified sampling design across six African countries. International Journal of Applied Earth Observation and Geoinformation
- Anticipation Hub (2023). A short overview of anticipatory action. Anticipation Hub, German Red Cross
- Olofsson, Pontus; Foody, Giles M.; Herold, Martin; Stehman, Stephen V.; Woodcock, Curtis E.; Wulder, Michael A. (2014). Good practices for estimating area and assessing accuracy of land change. Remote Sensing of Environment
- Stehman, Stephen V. (2014). Estimating area and map accuracy for stratified random sampling when the strata are different from the map classes. International Journal of Remote Sensing
- NASA LANCE (2025). MODIS Aqua+Terra Global Flood Product MCDWD L3 NRT.
- Fritz, Steffen et al. (2024). Development of a new cropland and rangeland area fraction image at 500 m for the ASAP system. Publications Office of the European Union
- Zanaga, Daniele et al. (2022). ESA WorldCover 10 m 2021 v200. Zenodo
- Potapov, Peter; Turubanova, Svetlana; Hansen, Matthew C.; Tyukavina, Alexandra; Zalles, Viviana; Khan, Ahmad; Song, Xiao-Peng; Pickens, Amy; Shen, Quan; Cortez, Jocelyn (2022). Global maps of cropland extent and change show accelerated cropland expansion in the twenty-first century. Nature Food
- Burton, Chad et al. (2022). Co-production of a 10-m cropland extent map for continental Africa using Sentinel-2, cloud computing, and the open-data-cube. Authorea preprint
- Van Tricht, Kristof et al. (2023). WorldCereal: a dynamic open-source system for global-scale, seasonal, and reproducible crop and irrigation mapping. Earth System Science Data
- Karra, Krishna et al. (2021). Global land use/land cover with Sentinel 2 and deep learning.
- Brown, Christopher F. et al. (2022). Dynamic World, near real-time global 10 m land use land cover mapping. Scientific Data
- Thenkabail, Prasad S. et al. (2021). Global cropland-extent product at 30-m resolution (GCEP30) derived from Landsat satellite time-series data for the year 2015 using multiple machine-learning algorithms on Google Earth Engine cloud. U.S. Geological Survey
- FAO; WFP (2023). Special Report: 2022 FAO/WFP Crop and Food Security Assessment Mission to the Republic of South Sudan. FAO
- FAO; WFP (2026). Special Report: 2025 FAO/WFP Crop and Food Security Assessment Mission to the Republic of South Sudan. FAO
- Cohen, Jacob (1960). A coefficient of agreement for nominal scales. Educational and Psychological Measurement
- Cicchetti, Domenic V.; Feinstein, Alvan R. (1990). High agreement but low kappa: II. Resolving the paradoxes. Journal of Clinical Epidemiology
