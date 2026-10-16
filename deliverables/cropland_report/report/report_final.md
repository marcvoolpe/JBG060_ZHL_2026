<!-- Generated from report_final.tex by draft_to_markdown.py: edit the .tex, then rerun. -->

# Which cropland is under water? Checking the public maps behind a flood trigger in South Sudan

*Group 1, JBG060. October 2026.* Marks: **[...]** still to write or make; *(pending decision N)* waits for the group (REVIEW_PLAN.md); > **Idea.** suggestions for cutting.

## 1. Context / Problem Background / Motivation of Analysis

Floods hit South Sudan every year, and since 2019 they have been the largest in the satellite record. ZOA International wants to act before they damage livelihoods in the Aweil counties and in Bor South, where most rural communities live from farming (ZOA International and Zero Hunger Lab, 2026). Its example trigger is "a flood which inundates cropland".

Such a trigger multiplies two maps: where the water is and where the fields are (Pacetti et al., 2017). The fields come from free global cropland maps, which ZOA suspects "might not capture agricultural land fully" and which nobody has checked in South Sudan (Kerner et al., 2024; Adebayo et al., 2026). In ZOA's areas they disagree widely: laid over the 2022 flood, eight maps put between 331 and 3,572 ha of Aweil's cropland under water. The choice of map, not the flood, decides whether the trigger fires. We therefore measure the cropland with an honest error bar, check each map against it, and follow the answer to the trigger.

## 2. Business and Data Understanding

**The decision.** ZOA's anticipatory action runs from forecast to agreed trigger to early action, such as cash transfers (Anticipation Hub, 2023). Cropland decides whether the trigger fires, how much money is requested and whose fields are reached, and ZOA wants it with a stated certainty: misses leave people without help, false alarms waste money and trust.

**The data.** The course provided the flood masks, the ASAP crop mask and county boundaries; we added seven public cropland maps, satellite images for labelling and the FAO/WFP crop assessment, whose cereal area is modelled, not observed (Table 1). The maps differ in year (2015-2025), in whether fallow counts as crop and in method, and none was checked in South Sudan.

*Table 1. Data used.*

| Data | Use |
|---|---|
| Course data: NASA MCDWD flood masks 2000-2025 (NASA LANCE, 2025), ASAP crop mask v04 (Fritz et al., 2024), county boundaries | flooded cropland; ASAP scored; study areas |
| WorldCover 2021 (Zanaga et al., 2022), GLAD 2019 (Potapov et al., 2022), DE Africa 2019 (Burton et al., 2022), WorldCereal 2021 (Van Tricht et al., 2023), Esri 2025 (Karra et al., 2021), Dynamic World 2025 (Brown et al., 2022), GFSAD 2015 (Thenkabail et al., 2021) | strata; maps scored |
| Sentinel-1 and Sentinel-2 images, dated sub-metre imagery (Esri), Google Open Buildings | labels and features |
| FAO/WFP crop assessment 2025 (FAO and WFP, 2026) | outside check |

**What the maps show.** In Aweil the maps call 0.22%-1.92% of the land crop, mostly on different land: the best pair of maps shares 0.16 of its crop area. Yet any two maps agree on 97-99% of the pixels, because most land is empty in all of them. Agreement on empty land hides disagreement on fields, so no map can be the reference. We judge maps by precision (the share of their crop that is real), recall (the share of real crop they find) and F1, which combines both; never by overall accuracy, which rewards a map that finds nothing where crop is rare (Kerner et al., 2024).

## 3. Research Objective

Our objective has four parts: (1) estimate the cropland area of ZOA's two areas in 2025, with a 95% interval that does not depend on any map; (2) measure the precision, recall and F1 of every public map on held-out points; (3) do the same for a map built from rules a person can read; and (4) show how the choice of map changes flooded cropland and whether a trigger would fire. An adequate answer states its uncertainty, reports misses and false alarms separately, and is a check that local staff can repeat each season.

## 4. Approach

One labelled sample serves all four sub-objectives (Figure 1). We froze the protocol before labelling.

**Sample.** We stacked the seven maps on a 10 m grid and split each area by how many call a pixel crop: none (stratum A, 95.0% of Aweil), one or two (B), or three or more (C), which puts points where the maps disagree. We drew 450 random points, 330 in Aweil and 120 in Bor South, and set two thirds of each stratum aside as test points before labelling.

**Labels.** Each point stands for the 210 m box around it, because in a pilot nobody could judge a single 10 m pixel. Two group members label every box blind to all maps, from satellite images of the 2025 season, looking for bare soil before sowing, green-up, an early harvest and field shape. A box is cropland if it holds a cropped or fallow field, and the labeller estimates its cropland share. When the two disagree on whether a box holds cropland, nobody overrules them: the box counts as half a cropland box in the area, and maps are scored only on boxes both agree on.

**Our rule.** For every box we computed 18 features in Google Earth Engine, each a 10 m layer summarised over the box, such as field edges and the distance to the nearest building. On the 125 calibration points both labellers agree on, we fitted a decision tree, chose its depth by cross-validation and froze it, as Rule 1, before reading any test label. Earth Engine applies it to every pixel, so a pixel of our map means "a field lies within this pixel's 210 m box". We compare it with random forests and logistic regressions chosen on the same points.

**Estimation.** The strata got different numbers of points for their size, so every box is weighted by the land its stratum stands for: in Aweil about 19,500 ha for a box in stratum A, 110 ha in stratum C. The area is the weighted mean of the labelled box shares (Olofsson et al., 2014). Precision, recall and F1 use the same weights, with formulas for strata that are not the map's own crop and non-crop classes (Stehman, 2014); a public map calls crop when any of its pixels in the box is crop. Flood masks over the maps and the sample give flooded cropland for 2025 and, as a scenario on today's cropland, for the floods of 2000-2025, judged by the sample only where five or more of its points lie on flooded land.

![Figure 1](../figures/17_method_diagram.png)

*Figure 1. Our approach: one sample, three uses.*

## 5. Evaluation Methodology

Each sub-objective has its own measure: agreement and Cohen's kappa for the labels (Cohen, 1960), a 95% interval for the area, and precision, recall and F1 on test points only for the maps, ranked only when their intervals do not overlap; for the trigger, whether each map's flooded cropland leads to the sample's decision. A simulation of our design showed that the usual interval is too narrow when crop is rare, so we also report an adjusted upper bound. Because ZOA's staff should repeat the check each season, we also measure its cost in new boxes and labelling time.

## 6. Results

**The labels are consistent.** The labellers agreed on cropland versus not for 85.6% of the 450 boxes (kappa 0.70).

**Every public map under-counts cropland.** In the Aweil counties 3.8% of the land is cropland, 116,500 ha (95% interval 76,700-183,100 ha). The maps call 0.22%-1.92% crop, all below the interval's lower end of 2.5% (Figure 2). Bor South holds little cropland (0.38%), and there Dynamic World shows 23 times the sample's estimate.

**The public maps miss most fields.** On the 186 Aweil test points, the best public map, WorldCereal, reaches an F1 of 0.55 and finds 0.41 of the fields (Figure 3). Esri, WorldCover, GLAD and ASAP are right on every crop call but find only 0.03-0.28 of the fields, and Esri and Dynamic World almost none (F1 0.06 and 0.03). In Bor South no agreed test box holds cropland, so misses cannot be counted, but Dynamic World calls crop on 44 of 74 empty boxes.

**Two questions find most fields.** Rule 1 asks whether a building lies within 333 m and whether the box shows field edges. It reaches an F1 of 0.72 (0.55-0.90), finding 0.75 of the fields at a precision of 0.70: clearly above Esri, Dynamic World and GFSAD, not clearly above the other maps. The random forests (0.71-0.76) and logistic regressions (0.61-0.66) score about the same, with overlapping intervals, so none is clearly better. Counting the 29 test boxes the labellers disagreed on all as cropland, or all as empty, still leaves our models above every public map. Rule 1 scores lower here than in cross-validation on its calibration points (0.85-0.86), mainly because 7 of its 9 test errors fall in the heavily weighted stratum A, where it had only 2 crop boxes to learn from; refitting its recipe on many random splits gives 0.61 on average. The robust finding is that Aweil's cropland sits near homesteads, so the rule misses fields far from them, about 25% of Aweil's boxes with cropland.

**For three maps, the difference reaches the trigger.** Only 1 Aweil and 2 Bor South points lay on flooded land in 2025, so the sample cannot judge that flood. Over today's cropland, 9 past floods put at least five points under water (Figure 4). In each, the sample estimates more flooded cropland than the median map, but its interval clears that median only in 2008. In 2022 it puts 7,263 ha under water (639-14,336), the maps 331-3,572 ha (Table 2). A 500 ha trigger fires on the sample, but Esri, GLAD and WorldCover, below even the interval's lower end, would have stayed silent. Counting every flooded field as lost, the maps imply 430-4,660 farming households and the sample about 9,470.

**The check can be repeated each season.** With our sampling scripts and labelling tool, ZOA's staff can redo it: about 124 new boxes, a minute each per labeller, give Aweil's area with a standard error of a fifth of the estimate; from the same labels our scripts re-score the maps and can refit and redraw our map.

![Figure 2](../figures/14_area_vs_maps.png)

*Figure 2. Every public map (blue) shows less cropland than the labelled sample (orange, with its 95% interval).*

![Figure 3](../figures/15_scorecard.png)

*Figure 3. Scores on the Aweil test points, with 95% intervals. Orange: ours; blue: public maps; dashed: labeller against labeller.*

*Table 2. Flooded cropland under the public maps and the sample (95% interval). Hh.: farming households if every flooded field were lost. Trigger: 500 ha.*

| Area | Year | Flooded | Maps, ha | Sample, ha | Hh., maps | Hh., sample | Maps fire | Sample |
|---|---|---|---|---|---|---|---|---|
| Aweil | 2008 | 83,017 | 585-4,335 | 10,795 (1,862-19,729) | 760-5,650 | 14,080 | 8 of 8 | fire |
| Aweil | 2022 | 53,646 | 331-3,572 | 7,263 (639-14,336) | 430-4,660 | 9,470 | 5 of 8 | fire |
| Aweil | 2025 | 10,322 | 10-306 | cannot tell (1 point) | 10-400 | - | 0 of 8 | cannot tell |
| Bor South | 2007 | 35,057 | 0-9,479 | 0 (0-2,096) | 0-12,150 | 0 | 1 of 8 | cannot tell |
| Bor South | 2025 | 29,435 | 0-1,600 | cannot tell (2 points) | 0-2,050 | - | 1 of 8 | cannot tell |

![Figure 4](../figures/12_flood_history.png)

*Figure 4. Today's cropland under the floods of 2000-2025: the public maps as a range, the sample with 95% intervals.*

## 7. Discussion

**Answers.** Sub-objectives 1 (the area) and 3 (a readable rule) are met. Sub-objective 2 is met in Aweil but only partly in Bor South, where misses cannot be measured, and sub-objective 4 in part, because the 2025 flood was too small for our sample.

**For ZOA.** Cropland area should come from a labelled sample, not a map, and maps should be chosen by recall and precision, not overall accuracy: WorldCereal or our map in Aweil, not Esri or Dynamic World, and not Dynamic World in Bor South. The FAO/WFP assessment supports the sample: its 111,500 ha for Aweil fall inside our interval.

**Limits.** The reference is image interpretation from one season, not field data: labellers also used images of other or unknown dates, and one counted crop just outside the box in a few early labels. Cropland shares come in classes (worst cases 2.3%-5.2% for Aweil), fallow is hard to see, Bor South and stratum A hold few cropland points, and our map is unchecked beyond the two areas. Checks added after the first results changed no frozen result.

**Impacts.** Used well, the check cuts silent triggers and false alarms; used badly, a number checked in two areas is read as valid everywhere, and maps of who farms where can touch land claims.

## 8. Conclusion

In ZOA's areas the public cropland maps do not show the farmland a flood trigger depends on: all under-count Aweil's cropland, most miss most fields, and in 2022 three would have kept a 500 ha trigger silent. A small sample, labelled twice and blind, gives an honest area and shows which map to trust; a two-question rule built from it does as well as the alternatives. We recommend that ZOA (1) base the cropland part of a trigger on such a sample, with extra points on flood-prone land; (2) choose maps by recall and precision in its own areas; (3) repeat the check each season with our tools; and (4) check some labels in the field before using our map beyond Aweil.

## References

- ZOA International; Zero Hunger Lab (2026). JBG060 Q&A 2: Flood dynamics in South Sudan. Stakeholder slides, 21 September 2026
- Pacetti, Tommaso; Caporali, Enrica; Rulli, Maria Cristina (2017). Floods and food security: A method to estimate the effect of inundation on crops availability. Advances in Water Resources
- Kerner, Hannah; Nakalembe, Catherine; Yang, Adam; Zvonkov, Ivan; McWeeny, Ryan; Tseng, Gabriel; Becker-Reshef, Inbal (2024). How accurate are existing land cover maps for agriculture in Sub-Saharan Africa?. Scientific Data
- Adebayo, Adebowale Daniel; Nakalembe, Catherine; Skakun, Sergii; Frimpong, Diana Botchway; Ginsburg, Alana; Gadhiya, Yash Hitesh; Adjei, Monica; Kerner, Hannah; Becker-Reshef, Inbal (2026). Optimizing satellite-based cropland area estimation through integrated map accuracy assessment and stratified sampling design across six African countries. International Journal of Applied Earth Observation and Geoinformation
- Anticipation Hub (2023). A short overview of anticipatory action. Anticipation Hub, German Red Cross
- NASA LANCE (2025). MODIS Aqua+Terra Global Flood Product MCDWD L3 NRT.
- Fritz, Steffen et al. (2024). Development of a new cropland and rangeland area fraction image at 500 m for the ASAP system. Publications Office of the European Union
- Zanaga, Daniele et al. (2022). ESA WorldCover 10 m 2021 v200. Zenodo
- Potapov, Peter; Turubanova, Svetlana; Hansen, Matthew C.; Tyukavina, Alexandra; Zalles, Viviana; Khan, Ahmad; Song, Xiao-Peng; Pickens, Amy; Shen, Quan; Cortez, Jocelyn (2022). Global maps of cropland extent and change show accelerated cropland expansion in the twenty-first century. Nature Food
- Burton, Chad et al. (2022). Co-production of a 10-m cropland extent map for continental Africa using Sentinel-2, cloud computing, and the open-data-cube. Authorea preprint
- Van Tricht, Kristof et al. (2023). WorldCereal: a dynamic open-source system for global-scale, seasonal, and reproducible crop and irrigation mapping. Earth System Science Data
- Karra, Krishna et al. (2021). Global land use/land cover with Sentinel 2 and deep learning.
- Brown, Christopher F. et al. (2022). Dynamic World, near real-time global 10 m land use land cover mapping. Scientific Data
- Thenkabail, Prasad S. et al. (2021). Global cropland-extent product at 30-m resolution (GCEP30) derived from Landsat satellite time-series data for the year 2015 using multiple machine-learning algorithms on Google Earth Engine cloud. U.S. Geological Survey
- FAO; WFP (2026). Special Report: 2025 FAO/WFP Crop and Food Security Assessment Mission to the Republic of South Sudan. FAO
- Olofsson, Pontus; Foody, Giles M.; Herold, Martin; Stehman, Stephen V.; Woodcock, Curtis E.; Wulder, Michael A. (2014). Good practices for estimating area and assessing accuracy of land change. Remote Sensing of Environment
- Stehman, Stephen V. (2014). Estimating area and map accuracy for stratified random sampling when the strata are different from the map classes. International Journal of Remote Sensing
- Cohen, Jacob (1960). A coefficient of agreement for nominal scales. Educational and Psychological Measurement


