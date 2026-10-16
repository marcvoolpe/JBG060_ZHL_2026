<!-- Generated from report_draft.tex by draft_to_markdown.py: edit the .tex, then rerun. -->

# Which cropland is under water? Checking the public maps behind a flood trigger in South Sudan

*Group 1, JBG060. Long version, 15 October 2026.* Marks: **[...]** still to write or make; *(pending decision N)* waits for the group (REVIEW_PLAN.md); > **Idea.** suggestions for cutting.

## 1. Context / Problem Background / Motivation of Analysis

Floods hit South Sudan every year, and since 2019 they have been the largest in the satellite record. ZOA International wants to act before a flood damages livelihoods, which is called anticipatory action. It works in two flood-prone areas: the five Aweil counties along the Lol river and Bor South on the White Nile (ZOA International and Zero Hunger Lab, 2026). About 80% of rural communities there live mainly from farming, and the harm ZOA names first is a harvest lost to flooding. Its example trigger reads: "a flood which inundates cropland resulting in at least y% of total yield reduction".

Such a trigger multiplies two maps: where the water is, and where the fields are (Pacetti et al., 2017). Most effort goes into the first. The second usually comes from one of several free, global cropland maps, and ZOA itself suspects that this data "might not capture agricultural land fully". Nobody has checked these maps in South Sudan: the two largest accuracy studies of African cropland maps leave the country out (Kerner et al., 2024; Adebayo et al., 2026). Where those studies did look, the maps often failed exactly where crop is rare. In Mali, the Esri map scores 0.97 overall accuracy and yet 0.00 on F1, the score that rewards finding the fields.

In ZOA's areas the maps disagree so much that the choice of map, not the flood, decides whether a trigger fires. Laid over the same 2022 flood, eight maps put between 331 and 3,572 ha of Aweil's cropland under water. A trigger cannot rest on such a number until someone measures how much cropland there is, with an honest error bar, and how wrong each map is. This report does that and follows the answer through to the trigger: from the decision ZOA faces (Section 2) to what our check changes for it (Sections 6 and 7).

## 2. Business and Data Understanding

To know what a better cropland number is worth, we first look at where it enters ZOA's decision, what is known about the maps, and what the maps themselves show.

**The decision.** ZOA's anticipatory action is a chain: a forecast, a trigger agreed in advance, and early action such as cash transfers, temporary flood defences and early harvesting (ZOA International and Zero Hunger Lab, 2026; Anticipation Hub, 2023). Cropland enters this chain three times. It decides whether the trigger fires (how much cropland lies under the water), how large a funding request is (hectares, then households, then cash), and who is reached (whose fields are on the map). ZOA asks for numbers with a stated certainty and warns about both kinds of error: a miss leaves people without help in time, while a false alarm spends scarce money and costs trust. Zero Hunger Lab supports ZOA with data analysis and asked us what public data can and cannot tell them.

**What is known.** Kerner et al. (2024) scored 11 public cropland maps against labelled points in eight African countries. Mean F1 per country ranged from 0.21 to 0.71, and overall accuracy misled wherever crop was rare. Adebayo et al. (2026) showed that a map's quality decides how many labelled points an area estimate needs, and that for a rare class the map's recall matters most. Both studies estimate area from a stratified probability sample (Olofsson et al., 2014; Stehman, 2014). Such a sample stays unbiased however good or bad the maps are, which counting a map's pixels does not. Neither study covers South Sudan.

**The data.** The course provided the NASA MCDWD flood masks (NASA LANCE, 2025), the ASAP crop mask (Fritz et al., 2024) and county boundaries (Table 1). We added seven public cropland maps (Zanaga et al., 2022; Potapov et al., 2022; Burton et al., 2022; Van Tricht et al., 2023; Karra et al., 2021; Brown et al., 2022; Thenkabail et al., 2021), Sentinel-1 and Sentinel-2 images and dated sub-metre imagery to label points, and the FAO/WFP crop assessments (FAO and WFP, 2023; FAO and WFP, 2026). The assessments model cereal area from population and household figures rather than observing it, so we use them only as an outside check.

**Why the maps differ.** The seven maps answer different questions (Table 2). They show different years, from 2015 to 2025, so a field opened or left since then is right in one map and wrong in another. They define crop differently: GLAD, GFSAD and Esri count fallow plots, while WorldCover, DE Africa and WorldCereal count land sown and harvested within a year. And they are built differently. Five of them train classifiers per region on a whole year of images, so a field's seasonal rhythm (bare, green, harvested) can enter the model. Esri and Dynamic World run one global deep network on single images and combine the answers over the year, which suits large rectangular fields better than small plots that look like grass in any one image. ASAP merges older maps at about 500 m. As far as we found, none was trained or checked on fields in South Sudan.

**What the maps show.** In the Aweil counties the maps call between 0.22% and 1.92% of the land crop, all below the crop assessment's cereal area (3.6%). In Bor South, Dynamic World calls 9.0% crop while no other map exceeds 0.25%. Where two maps do call crop, it is mostly different land: the best pair shares 0.16 of its crop area and the median pair 0.04 (Figure 1); all seven agree on about 0.5 ha of Aweil's 3,085,318 ha. In one 6 by 6 km window north of Aweil town, they call between 0.0% and 21.7% of the land crop, each in different places (Figure 2). Yet the same pairs agree on 97-99% of all pixels, because most land is "not crop" everywhere. Agreement on empty land hides disagreement on fields. No map can therefore serve as the reference; it has to come from labelled points that do not depend on any map. Appendix F shows the maps by county, by state and year by year.

**Terms.** *Precision* (user's accuracy) is the share of a map's crop that is really crop; *recall* (producer's accuracy) is the share of real crop that the map finds; *F1* combines the two. *Cropland* is land with a cropped or a fallow field, while *cropped in 2025* counts cropped fields only. A *stratum* is a part of an area that is sampled separately.

*Table 1. Data used: course data from Zero Hunger Lab, the rest collected by us.*

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

*Table 2. What each public map calls crop and how it is made, from each map's documentation; the last column shows how we read it as crop.*

| Map | Year | Pixel | Built with | Counts as crop | Crop when |
|---|---|---|---|---|---|
| ESA WorldCover v200 | 2021 | 10 m | Sentinel-1 and -2 over a year, gradient-boosted trees per region, expert rules | annual crops sown and harvested within 12 months | class 40 |
| GLAD cropland | 2019 | 30 m | Landsat metrics of 2016-2019, bagged decision trees per 1° tile | herbaceous crops; fallow up to four years counts | value >0.5 |
| Digital Earth Africa | 2019 | 10 m | Sentinel-2 over a year, random forest per agro-ecological zone | at least 0.01 ha sown and harvested within 12 months | value 1 |
| ESA WorldCereal | 2021 | 10 m | Sentinel-1 and -2 and weather, gradient-boosted trees per region and season | temporary crops | class 100 |
| Esri / Impact Observatory | 2025 | 10 m | single Sentinel-2 images, one global deep network | planted crops, fallow plots included | class 5 |
| Google Dynamic World | 2025 | 10 m | single Sentinel-2 images, one global deep network; we take the most frequent label of the year | planted crops | label 4 |
| GFSAD GCEP30 | 2015 | 30 m | Landsat, an ensemble of classifiers per zone | cultivated land, fallow and plantations | class 2 |
| ASAP crop mask v04 | 2017-23 | about 500 m | a merge of older maps | share of crop per cell | 5% or more |

![Figure 1](../figures/03_pairwise_iou_aweil.png)

*Figure 1. The public maps rarely call the same land crop: overlap (intersection over union) of the crop class of every two maps in the Aweil counties. The same pairs agree on 97-99% of all pixels, because most land is "not crop" in every map.*

![Figure 2](../figures/16_same_window_every_map.png)

*Figure 2. Seven maps, seven answers: the same 6 by 6 km window north of Aweil town in every map, 2025. Blue: the public map says crop; orange: our map (pixels whose 210 m box holds a field); dots: labelled points, all with cropland. The window has the most labelled points and lies where several maps see crop, so the maps look better here than over Aweil as a whole.*

## 3. Research Objective

Our objective follows from this gap. We estimate how much of ZOA's two areas was cropland in the 2025 season, with a 95% interval that does not depend on any map; we measure how well seven public maps, the course's ASAP mask and a readable map of our own find that cropland; and we show how the choice of map changes the flooded cropland a trigger would see. Four measurable sub-objectives follow:

- the cropland area of each study area, with a 95% interval;

- the precision, recall and F1 of every public map on held-out points, per area;

- the same scores for a map built from rules a person can read;

- the flooded cropland under each map and under the labelled sample, and whether a trigger would fire.

**Scope.** The reference is what two trained people see on satellite images; we made no field visits. We study one season (2025) and two areas, take the flood masks as given and do not forecast floods. A point stands for the 210 m box around it.

**What counts as adequate.** An adequate answer states its uncertainty, reports misses and false alarms separately, can be read by local staff and repeated by them each season at low cost, and is judged where ZOA works (ZOA International and Zero Hunger Lab, 2026). Table 3 turns these demands into measures. The objective fitted the course: we drew, labelled and scored the sample in four weeks.

## 4. Approach

One labelled sample serves all four sub-objectives (Figure 3). We draw it where the maps disagree, label every point twice and blind, and use the labels three ways: to estimate the area (sub-objective 1), to score every map on held-out points (2 and 3), and to train our own map on the rest. Laying the flood masks over the maps and the sample then gives the flooded cropland (4). We wrote the protocol down and froze it before labelling; every later change is dated, with its reason, in a change log (Appendix J).

### Sample

We stacked the seven public maps on a 10 m grid and split each area by how many maps call a pixel crop: none (stratum A, 95.0% of Aweil), one or two (B), three or more (C). Such strata put points where the maps disagree without trusting any single map (Kerner et al., 2024). We drew 450 random points at least 100 m apart: 150, 90 and 90 in Aweil's strata, and 60 and 60 in Bor South, whose stratum C was too small and was merged into B. The closest two points ended up 209 m apart, so the distance rule hardly changed the design. Before anyone labelled, each stratum was split at random into one third calibration points, to build our map, and two thirds test points, to score every map.

### Labels

Each point stands for the 210 m box around it, because in a pilot of 30 points five labellers could not judge a single 10 m pixel (kappa 0.00-0.38). Two of the five group members label every box, independently and blind to all maps. They see monthly Sentinel-2 images of 2025, a radar curve for the cloudy months and the most recent sub-metre image with its date; links open older images (Esri Wayback) and Google's imagery, whose date is not shown. A written key asks for four cues: bare soil before sowing, green-up, a harvest earlier than the surrounding grass, and field shape. A box is *crop* if any field in it was cropped in 2025, *fallow* if it holds a field that was not, and *not crop* otherwise. The labeller also estimates the share of the box that is cropland, in classes: none, under 10%, 10-25%, 25-50% and over 50%. When the two labellers disagree on whether a box holds cropland, nobody overrules them. In the area estimate the box takes the average of their two answers, so it counts as half a cropland box, with half the share the one labeller saw. In precision, recall and F1 it is left out, so the maps are scored only on boxes both labellers agree on. Where one labeller answered "unsure", the other's answer counts alone.

### Features

For every box we computed 18 features in Google Earth Engine (Table 9), so each feature describes the same box the labeller judged. The satellite layers come at 10 m: cloud-masked monthly Sentinel-2 composites of 2025 (Cloud Score+), Sentinel-1 radar (descending passes, the only ones over South Sudan in 2025), JRC surface water, MODIS burned area and Google Open Buildings. Each feature is first computed for every 10 m pixel and then summarised over the box's 21 × 21 pixels by its most crop-like part: the 10th percentile for the lowest spring greenness and the distance to buildings, the 90th percentile for bare soil, green-up, the harvest drops, texture and edges, and the mean for the rest. Together the features turn the labelling cues into numbers and add trees, water, burn scars, radar for the cloudy months and the distance to homesteads (Figure 14).

### Models

*Training data.* Every model learns from the same 125 calibration points on which both labellers agree whether a field was cropped in 2025; 41 of them are crop. We train on "cropped in 2025" rather than on cropland, because a fallow field looks like grass from space; fallow enters the area through the sample only. Missing feature values are filled with the calibration medians, which are stored with the model. The test points are never used to fit or to choose anything.

*Rule 1, a decision tree.* A decision tree asks yes-or-no questions about the features and ends in "crop" or "not crop". We fitted one with balanced class weights, since crop is the minority, and at least five points per leaf. We chose its depth (2, 3 or 4) by 5-fold cross-validation on F1, taking the smallest depth within 0.02 of the best; the depths scored alike, so depth 2 was kept. The tree is written out as if-then rules in a dated file and was frozen on 12 October (Figure 7). The same file runs in Python for scoring and in Earth Engine for the map, and a test checks that both give the same answer at all 150 calibration points.

*Trees or logistic regression?* *(pending decision 2)* The group asked which of the two to use. We compared trees of depth 1 to 4, logistic regressions with an L2 and an L1 penalty, a logistic regression on Rule 1's two inputs and a random forest, all by 5-fold cross-validation repeated 20 times on the calibration points only. Two logistic regressions were then frozen and scored once: one on all 18 features, and one on Rule 1's two inputs, which sets a linear rule against a tree on the same information. Two random forests of 500 trees, one on the 18 features and one on Google's Satellite Embedding, show what a black box would gain; they are scored but never mapped.**[Wei, Matei: your trees, if any, frozen by 16 Oct]**

*Our map.* Earth Engine applies Rule 1 to every 10 m pixel of the two areas and, at 30 m, to the whole country. Because the features summarise the box around a pixel, a pixel of our map means "the 210 m box around this pixel holds a cropped field". The map therefore shows where fields are near, not their exact edges, and the cropland area always comes from the sample, never from counting the map.

### Estimation

*Weights.* The strata received different numbers of points for their size: stratum A covers 95.0% of Aweil but got 150 of its 330 points. Every box is therefore weighted by the land its stratum stands for, about 19,500 ha for a box in Aweil's stratum A against 110 ha in stratum C. *Area.* The cropland share of an area is the weighted mean of the labelled share of each box, using the mean of the two labellers (Olofsson et al., 2014). We also report the share of boxes that hold any cropland, which is larger by design because fields are small and scattered. *Accuracy.* Precision, recall and F1 of every map on the test points use the same weights. The textbook formulas assume that the strata are the map's own classes, crop and not crop; ours are strata of map agreement, so we use the formulas of Stehman (2014) for strata that differ from the map's classes, with standard errors. A public map says crop at a point when any of its pixels in the box is crop. *Flooded cropland.* We lay the 2025 flood extent (June to December) over every map and over the sample. Because the labels describe today's cropland, we also lay the floods of 2000-2025 over it as a scenario: how much of today's cropland would a flood like that one put under water? *(pending decision 8c)* For those years the sample's flooded cropland is the cropland share of the sample boxes on flooded land times the flooded area, which the mask measures exactly (a ratio estimator). We use it only when at least five points lie on flooded land.

![Figure 3](../figures/17_method_diagram.png)

*Figure 3. One sample, three uses. Drawn from strata of map agreement and labelled twice, it gives the area, trains our models (calibration points) and scores every map (test points); flood masks are laid over all of them. The protocol was frozen before labelling (Appendix J).*

## 5. Evaluation Methodology

Each sub-objective has its own measure (Table 3). For the labels we report agreement and Cohen's kappa, with positive and negative agreement beside it, because kappa misleads when one class is rare (Cohen, 1960; Cicchetti and Feinstein, 1990). For the area (sub-objective 1) we report the estimate with its standard error and a 95% interval. For the maps (2 and 3) we report precision, recall and F1 on test points only, and we rank two maps only when their intervals do not overlap. We never rank by overall accuracy, because where crop is rare a map that finds nothing still scores high (Figure 4). For the trigger (4) we ask whether each map's flooded cropland leads to the same decision as the sample's.

We checked the interval itself by simulating our exact design. The usual interval of ±1.96 standard errors held the true area only 47%-94% of the time, every miss lying below the truth, because stratum A often holds no cropland point at all. We therefore also report an adjusted upper bound that gives each stratum at least the variance it would have with one more cropland box and one more empty box; it reached 94%-100% coverage in Aweil. *(pending decision 1)* The trigger check uses the same cautious bound, capped at the land that flooded. *(pending decision 8b)*

ZOA wants a check that its own staff can repeat each season with our tools: draw new boxes with our sampling scripts, label them in our labelling tool and rerun the scoring. We therefore measure what one round costs: the number of boxes needed for a 20% coefficient of variation on the area (a standard error of a fifth of the estimate), with our strata and with strata from a single map (Adebayo et al., 2026), and the hours the labelling took. Finally, we broke each map's errors down by what the labellers saw (land cover, crop cues, distance to buildings, share of the box) and looked at images of the worst ones.

*Table 3. What ZOA and Zero Hunger Lab need from an answer, and how we measure it.*

| Criterion (from ZOA and ZHL) | Measure |
|---|---|
| State how certain we are | 95% intervals on area, standard errors on scores, simulated coverage |
| Misses and false alarms both cost | recall and precision reported separately |
| Relevant to the decision | trigger decisions per map against the sample |
| Transparent, interpretable | conditions and features of Rule 1; F1 lost against a black box |
| Local, and cheap to repeat | scores per area; points and hours a yearly check needs |
| Whose farmland is seen | recall per map; errors by distance to buildings and field size |

![Figure 4](../figures/09_published_accuracy_of_our_maps.png)

*Figure 4. Elsewhere in Africa, high accuracy hides low recall: published F1 and recall of the maps we compare (Kerner et al., 2024; Adebayo et al., 2026). Ringed: Mali, where Esri has 0.97 accuracy and an F1 of 0.00.*

## 6. Results

The results follow the four sub-objectives. Before them we check the labels, since every later number rests on them.

**The labels are consistent enough to judge the maps.** On all 450 points the two blind labellers agreed on cropland versus not at 85.6% (Cohen's kappa 0.70; Aweil 83.3%, kappa 0.68). Scored the way we score the maps, one labeller reaches an F1 of 0.71 against the other. They disagreed about whether a small field is there, hardly ever about the land cover: at 41 of the 53 split points, one labeller saw field shapes and the other did not. In Bor South they agreed almost only on "not crop" (kappa 0.14), because the few boxes anyone called cropland were rarely confirmed. Fallow was used 7 times in 900 labels, so cropland and "cropped in 2025" differ by less than 0.1 percentage point (3.78% against 3.72% in Aweil); we report cropland.

**Every public map shows less cropland in Aweil than the sample (sub-objective 1).** The sample puts 3.8% of the Aweil counties under cropland: 116,500 ha, with a 95% interval of 76,700-183,100 ha (Table 5). The maps call 0.22%-1.92% of the land crop. That is 6%-51% of the sample's estimate and below the lower end of its interval (2.5%; Figure 5). Bor South holds little cropland, 0.38% of the land or 5,400 ha (1,000-16,500), and the maps scatter around it, from almost none to Dynamic World's 9.0%, 23 times the sample's estimate. Fields are small and scattered: boxes that hold any cropland cover 14.3% of Aweil and 1.5% of Bor South.

**The public maps miss most fields (sub-objective 2).** On the 186 Aweil test points (Figure 6), the best public map, WorldCereal, reaches an F1 of 0.55 and finds 0.41 of the fields. Esri, WorldCover, GLAD and ASAP are right on every crop call they make but find only 0.03-0.28 of the fields. Their perfect precision rests on 17 to 66 calls, almost all in strata B and C, so its 95% lower bound is 0.80-0.94. Dynamic World is weak on both counts (precision 0.10, recall 0.02), and Esri and Dynamic World reach F1 scores of only 0.06 and 0.03. The recall of WorldCover, GLAD, GFSAD and Dynamic World is lower here than every value published for them elsewhere in Africa. In Bor South no test box that both labellers agree on holds cropland, so we cannot measure how many fields a map misses there. We can count false alarms: Dynamic World calls crop on 44 of the 74 boxes where the labellers saw no field, mostly open grassland, and every other map on at most one.

**A rule with two questions finds most fields (sub-objective 3).** Rule 1 asks two questions (Figure 7): is there a building within 333 m of the box, and does the box show field edges? On the Aweil test points it reaches an F1 of 0.72 (0.55-0.90), with precision 0.70 and recall 0.75. That is clearly above Esri, Dynamic World and GFSAD, whose intervals do not overlap with it, but not clearly above WorldCereal, DE Africa, ASAP, GLAD and WorldCover. The random forests (0.71-0.76) are not clearly better. The logistic regressions (0.61-0.66) find more fields (recall 0.84) but call more empty land crop (precision 0.48-0.54). *(pending decision 2)* The ranking does not depend on the boxes the labellers disagreed on, which the main scores leave out: counting those 29 test boxes all as cropland, or all as empty, still leaves our models above every public map (Table 12). Rule 1 also agrees with the labels about as well as one labeller agrees with the other (0.71).

**The test scores are lower than cross-validation suggested.** In cross-validation on the calibration points all models scored alike: trees 0.85-0.86, logistic regressions 0.87-0.88 and the random forest 0.92 (Figure 8). The test scores are lower for three reasons. First, cross-validation counts every point alike, while the test weighs each point by the land it stands for: a box in stratum A stands for about 19,500 ha, one in stratum C for 110 ha. 7 of Rule 1's 9 test errors lie in stratum A, and unweighted its test F1 would be 0.96. Second, the calibration set held only 2 crop boxes in Aweil's stratum A, so no model saw many such fields. Third, a check we made after the scores were known shows that the recipe itself varies. Refitting Rule 1's recipe in 20 rounds of five-fold cross-validation on all 381 agreed points gives a weighted F1 of 0.61 on average (0.54-0.69), so the frozen rule's 0.72 is a favourable draw.

**Cropland in Aweil sits near homesteads.** Every refitted tree asks about the distance to buildings, while its second question varies between field edges, June radar and texture. The other models agree (Figure 16). Distance to buildings is the strongest input of the logistic model (-0.85 log-odds per standard deviation), followed by June radar (-0.85; lower over freshly sown, bare fields) and the harvest drop (+0.64); in the random forest it carries 0.23 of the importance, against 0.14 for field edges. Our answer to "trees or logistic regression?" is therefore that it matters little here. We keep the two-question tree because local staff can read and check it. *(pending decision 2)* The flip side is that Rule 1 cannot find fields far from homesteads. Only 5 of the 138 cropland boxes in the sample lie more than 333 m from a building, but most of them are in stratum A. Weighted by land, they make up about 25% of Aweil's boxes with cropland (31% of its cropland area, a rough figure from few points). The logistic models show the opposite weakness: they call crop on 9-12 of the 122 empty test boxes in stratum A, against 5 for Rule 1.

**Our map marks more than the cropland it finds, and is unchecked beyond our areas.** Counted over its pixels, our map marks 22.6% of the Aweil counties, more than the 14.3% of land whose box holds cropland in the sample: it also marks boxes near homesteads that hold no field, as its precision of 0.70 says. Applied to all of South Sudan at 30 m, it marks 6.8% of the country (Figure 27). The coarser run keeps its recall on our test points (0.75) but marks more empty boxes, so precision falls to 0.50 and F1 to 0.60. Outside our two areas there are no labels, so we can only compare our map with the public maps, at 20,000 random points (Table 18). Of the land at least two public maps call crop, our map marks 29%. That share is 96% in Warrap, Aweil's neighbour, and 83% in Lakes, but only 2% in Upper Nile and 7% in Eastern Equatoria, where fields lie in large schemes, along rivers or follow two rainy seasons. Per state, its ranking agrees with the crop assessment second best of all maps (rank correlation 0.52, after GFSAD's 0.59), though ten states make every such correlation imprecise.

**The 2025 flood was too small for the sample to judge (sub-objective 4).** In 2025, 10,314 ha of the Aweil counties flooded for at least a day, and the public maps put 10-307 ha of cropland under water. In Bor South 29,419 ha flooded; every public map shows at most 10 ha of flooded cropland there except Dynamic World, with 1,606 ha. Only 1 of the 330 Aweil points and 2 of the 120 Bor South points lie on flooded land, so the sample cannot tell which map is right at any trigger threshold from 100 to 5,000 ha. *(pending decision 8b)* This is a lesson about our design rather than about the maps.

**In past floods the sample finds more flooded cropland than the maps, clearly so in 2008.** Laid over today's cropland, past floods give the sample more points to work with (Figure 9). *(pending decision 8c)* In 9 of the 26 years at least five sample points lie on flooded land in Aweil. In all of them the sample's estimate is higher than the median public map, but with 5-17 points on flooded land its interval includes the median map in 8 of the 9 years. Only in 2008 does it lie above 7 of the 8 maps (Table 14). In 2022, 53,646 ha flooded and 9 of the 11 sample points on flooded land hold cropland. The sample then estimates 7,263 ha of flooded cropland (639-14,336), against 331-3,572 ha by the public maps. Figure 10 shows where: WorldCereal shows crop in 1,646 of the 10,184 flooded cells, and our map adds 3,627, along the Lol and in the east of the area.

**For three maps the difference reaches the trigger.** Played back as a 500 ha trigger, the sample says "fire" in 2008 and 2022 (Table 4). Esri, GLAD and WorldCover would have stayed silent in 2022, because even the lower end of the sample's interval lies above them; for the other five maps the interval is too wide to say. The same holds for the size of a response. As an illustration, we divide the flooded hectares by the 0.77 ha of cereal per farming household that the 2025 crop assessment gives for Aweil, and count every flooded field as lost. The maps then point to 430-4,660 farming households in 2022, the sample to about 9,470 (830-18,700). In Bor South the error runs the other way: in 2007 none of the five sample points on flooded land held cropland, while Dynamic World put enough cropland under water to fire even a 5,000 ha trigger. All of these are upper bounds on exposure, since the loss depends on when the flood comes and how long it stays.

*Table 4. Flooded cropland before and after our check, on today's cropland: the public maps against the labelled sample (ratio estimator, 95% interval; judged only with at least five sample points on flooded land). Households: hectares divided by the cereal hectares per farming household in the 2025 crop assessment (illustrative and an upper bound: every flooded field counted as lost). Trigger: flooded cropland of at least 500 ha.*

| Area | Year | Flooded | Maps, ha | Sample, ha | Hh., maps | Hh., sample | Maps fire | Sample |
|---|---|---|---|---|---|---|---|---|
| Aweil | 2008 | 83,017 | 585-4,335 | 10,795 (1,862-19,729) | 760-5,650 | 14,080 | 8 of 8 | fire |
| Aweil | 2022 | 53,646 | 331-3,572 | 7,263 (639-14,336) | 430-4,660 | 9,470 | 5 of 8 | fire |
| Aweil | 2025 | 10,322 | 10-306 | cannot tell (1 point) | 10-400 | - | 0 of 8 | cannot tell |
| Bor South | 2007 | 35,057 | 0-9,479 | 0 (0-2,096) | 0-12,150 | 0 | 1 of 8 | cannot tell |
| Bor South | 2025 | 29,435 | 0-1,600 | cannot tell (2 points) | 0-2,050 | - | 1 of 8 | cannot tell |

**The check can be repeated each season at low cost.** With our sampling scripts, labelling tool and scoring code, ZOA's staff can redo the whole check next season: from the new labels the scripts update the area and the map scores, and can refit and redraw our map. With our strata, about 124 new boxes give Aweil's area with a 20% coefficient of variation; strata from a single public map need 112-149, depending on the map. Our design is therefore not clearly cheaper than one built on the best map, but it does not need that map to be known in advance. Bor South would need about 1,240 boxes under any design, because its cropland is too rare. Labelling took a median of 0.5-1.0 minutes per box for each labeller, or 2.7-7.3 hours per person for 180 boxes.

*Table 5. Cropland area in 2025 from the labelled sample: estimate and 95% interval (lower bound as usual, upper bound adjusted).*

|  | Aweil counties (3,085,318 ha) share of land | ha | Bor South (1,396,328 ha) share of land | ha |
|---|---|---|---|---|
| Cropland (cropped or fallow) | 3.8% (2.5%-5.9%) | 116,500 | 0.38% (0.07%-1.2%) | 5,400 |
| Upper bound: box holds cropland | 14.3% |  | 1.5% |  |
| CFSAM 2025 cereal area (modelled) | 3.6% | 111,500 | 1.9% | 26,000 |

![Figure 5](../figures/14_area_vs_maps.png)

*Figure 5. Every public map shows less cropland in Aweil than the labelled sample: each map's share of the land (pixel count, blue) against the sample's estimate and 95% interval (orange).*

![Figure 6](../figures/15_scorecard.png)

*Figure 6. Rule 1 finds most fields, the public maps miss most: precision, recall and F1 of every map on the Aweil test points, with 95% intervals (orange: ours; blue: public maps). Dashed: one labeller scored against the other with the same weights (F1 0.71), not a ceiling, because the maps are scored only on points both labellers agree on. Thin dashes: the 95% lower bound where a map was right on every crop call.*

![Figure 7](../figures/18_rule1_tree.png)

*Figure 7. Rule 1 asks two questions: the calibration points it learned from and the test points it was scored on (both areas; unweighted counts). Frozen on 12 October 2026, before any test label was read.*

![Figure 8](../figures/20_models_cv_vs_test.png)

*Figure 8. All models score alike in cross-validation and lower on the test points: F1 in repeated cross-validation on the calibration points (blue) and on the Aweil test points (orange, frozen models only, 95% intervals). The levels differ because cross-validation counts every point alike, while the test weighs points by the land they stand for.*

![Figure 9](../figures/12_flood_history.png)

*Figure 9. Today's cropland under every flood of 2000-2025: the public maps as a range with their median, the sample with 95% intervals in years with at least five sample points on flooded land. The sample's estimate is higher in every year, but its interval clears the median map only in 2008.*

![Figure 10](../figures/13_flood_map_aweil_2022.png)

*Figure 10. Where our map adds flooded cropland: the 2022 flood in the Aweil counties, cell by cell (232 m). Left: flooded cells where WorldCereal 2021, the best public map on our test points, shows crop. Right: the cells our map adds, and the sample points on flooded land.*

## 7. Discussion

We now return to the four sub-objectives and ask what each answer means for ZOA.

**How much cropland? (sub-objective 1)** Met. The sample gives an area with an interval that does not depend on any map, and it shows that every public map under-counts Aweil's cropland. ZOA should therefore take the cropland area from a labelled sample with its interval, not from a map. The FAO/WFP crop assessment, which models cereal area from population and household figures, offers an outside check. In Aweil its 111,500 ha fall inside our interval and close to our 116,500 ha, while every map is below both. In Bor South its 26,000 ha lie above our upper bound. Flood-recession plots, planted after the water drops, may not look like fields in a 2025 image; 120 points hold few cropland boxes; and the assessment models rather than measures.

**Which map to trust? (sub-objective 2)** Met in Aweil, and only partly in Bor South, where misses cannot be measured. The practical rules are simple. Never choose a map by its overall accuracy, because recall warned where accuracy did not. In Aweil use WorldCereal or our map and avoid Esri and Dynamic World, which find almost no fields. In Bor South avoid Dynamic World, which calls open grassland crop.

**Can a readable rule do as well? (sub-objective 3)** Met. Two questions that local staff can check on an image score as well as the black boxes we tried, and better than three public maps. The robust lesson is where the rule looks, near homesteads; its exact thresholds are one good choice among several, and fields far from homes need labels of their own.

**What changes for the trigger? (sub-objective 4)** Met in part. The 2025 flood was too small for a sample spread over the whole area. In past floods the sample confirms a 500 ha trigger in 2008 and 2022 that the three maps finding the fewest fields would have missed; for the other maps its intervals are too wide to tell. A sample with extra points on flood-prone land would turn "cannot tell" into an answer.

**Limits.** We collect the caveats here; Appendix B lists every known error. The reference is what people see on images, not on the ground. The labellers judged fields partly on sub-metre images of other years or of unknown date (Esri Wayback, Google Maps), did not all use the same extra sources, and one counted cropland just outside the box in a few early labels before stopping. A label counts only when the second labeller confirms it. If all 44 split points in Aweil were in truth empty, the share of land whose box holds cropland would fall from 14.3% to 10.3%; if all held cropland, it would rise to 18.3%. The share of a box comes in classes: had every labeller picked the lowest value of each class, Aweil's cropland would be 2.3% (71,500 ha), and with the highest 5.2% (161,600 ha). These are worst cases, not an interval, but the class is the least consistent part of a label: the two labellers chose the same class for only 35% of the boxes both called cropland. Fallow looks like grass from space, so some fallow is likely labelled "not crop". The study covers one season and two areas, with few cropland points in Bor South and in stratum A, which widens every interval, and our map is unchecked elsewhere. Some analyses were added after the first results (the logistic models, the flood scenario with its five-point minimum, the checks of the recipe); they are marked as such and changed no frozen result.

**Positive and negative impacts.** Used well, the check means fewer silent triggers where maps under-count fields, fewer false alarms where a map calls grassland crop, numbers with a stated uncertainty, and a check cheap enough to repeat each season. It also carries risks. A number checked in two areas can be read as valid everywhere. The sample gives area, not location, so targeting still needs a map and local knowledge, and better maps for ZOA's areas do nothing for farmers elsewhere. In a conflict setting, maps of who farms where can touch land claims, so they should be shared at the level ZOA needs and no further.

**What we hand over.** We deliver the means to repeat and extend the check (Appendix I): the labelling tool and its key, with which two people label a box blind in about a minute; a configuration file and a guide that move the pipeline to another area, country or season; the sampling, scoring and flood scripts; a workbench in which a next group fits and freezes a model on calibration points only; a results dashboard in one HTML file that opens without internet; and the 450 labelled boxes with their features and every map's value.

## 8. Conclusion

In ZOA's two areas, the public cropland maps do not show the farmland a flood trigger depends on. In the Aweil counties 3.8% of the land is cropland (116,500 ha), and every public map shows less than the lowest value our interval allows (2.5%). Most maps find only a small part of the fields, and Esri and Dynamic World find almost none. In the 2008 and 2022 floods the sample finds more flooded cropland than most maps, and a 500 ha trigger built on Esri, GLAD or WorldCover would have stayed silent in 2022. In Bor South, where cropland is rare, the sample can only count false alarms, and Dynamic World raises many. A small sample, labelled twice and blind, gives an honest number and shows which map to trust where, and a two-question rule built from it does as well as the best alternatives we tried.

We recommend that ZOA (1) base the cropland part of a trigger on a labelled sample with its interval, with extra points on flood-prone land so that flooded cropland gets its own estimate; (2) choose maps by recall and precision in its own areas, never by overall accuracy: WorldCereal or our map in Aweil, not Esri or Dynamic World, and not Dynamic World in Bor South; (3) repeat the check each season with the tools we hand over, about 124 boxes for Aweil or a few hours per labeller; (4) collect a few field points with its own staff to check the labels; and (5) use our map outside Aweil only where new labels confirm it, and not at all in landscapes unlike Aweil's, such as Upper Nile. The next research step is crop stage and flood duration, which decide how much of a flooded field is lost.

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

## Appendix A. Data, sample and labels

![Figure 11](../figures/23_strata_and_sample.png)

*Figure 11. The strata and the 450 sample points. Shading: share of each 232 m cell where at least one of the seven public maps sees crop (stratum A where none does). Markers: sample points by stratum. In Bor South stratum C was smaller than 0.1% of the area and was merged into B before drawing.*

![Figure 12](../figures/24_labelling_examples.png)

*Figure 12. What the labellers see: twelve monthly Sentinel-2 images of 2025 around a point, with the 210 m box to label (yellow), for a box both called crop, a box both called not crop, and a box on which they disagreed. In the tool, each point also has a radar curve, a greenness curve per patch of the box and a dated sub-metre image.*

![Figure 13](../figures/11_annotation_statistics.png)

*Figure 13. Our labels: the 900 labels, agreement between the two labellers per area and stratum, and which answers differ when they split (mostly whether field shapes are visible).*

*Table 6. Strata and sample. Cropland: points both labellers call cropland; split: the two labellers disagree.*

| Area | Stratum | ha | Share | Points | Calib. | Test | Cropland | Split |
|---|---|---|---|---|---|---|---|---|
| Aweil | A | 2,929,918 | 95.0% | 150 | 50 | 100 | 10 | 13 |
| Aweil | B | 145,327 | 4.7% | 90 | 30 | 60 | 53 | 26 |
| Aweil | C | 9,934 | 0.3% | 90 | 30 | 60 | 74 | 16 |
| Bor South | A | 1,264,445 | 90.6% | 60 | 20 | 40 | 0 | 1 |
| Bor South | B | 131,838 | 9.4% | 60 | 20 | 40 | 1 | 9 |

*Table 7. Agreement between the two blind labellers on cropland versus not, per area and stratum.*

| Group | Points | Agree | Kappa | Pos. agr. | Neg. agr. |
|---|---|---|---|---|---|
| All | 450 | 85.6% | 0.70 | 0.84 | 0.90 |
| Aweil | 330 | 83.3% | 0.68 | 0.86 | 0.86 |
| Bor South | 120 | 91.7% | 0.14 | 0.18 | 0.96 |
| Aweil A | 150 | 91.3% | 0.58 | 0.65 | 0.96 |
| Aweil B | 90 | 71.1% | 0.32 | 0.84 | 0.52 |
| Aweil C | 90 | 82.2% | -0.07 | 0.92 | 0.00 |
| Bor South A | 60 | 98.3% | 0.00 | 0.00 | 0.99 |
| Bor South B | 60 | 85.0% | 0.16 | 0.20 | 0.93 |

## Appendix B. Known errors in the data

We asked the labellers after labelling how they worked. Table 8 lists every error source we know of in the reference labels and the other data, the direction it pushes the results, and how the method contains it. None of them was corrected after the fact: changing labels after the scores are known would bias the check more than the errors themselves.

*Table 8. Known errors in the data, their likely effect, and how the method contains them.*

| Source | What happened | Likely effect | How it is contained |
|---|---|---|---|
| Image dates | Sub-metre images were often not from 2025: the tool flags Esri's date, Esri Wayback shows older captures, and Google Maps (used for its sharper images and zoom) shows no date at all. | A field opened or left since then can be read as a 2025 field, or missed. | The key: older images for field shapes only, the 2025 decision from the Sentinel-2 cues. The labellers called Google "not binding". Not measurable. |
| Different sources | Some labellers also opened single Sentinel-2 scenes in a browser (more dates per month) or Esri Wayback; others mostly used the tool's monthly images. | Two labellers do not always see the same evidence; more disagreement. | Disagreements are kept: left out of scoring, counted half in the area. Kappa 0.70 includes this. |
| Box edge | In a few early labels one labeller counted cropland just outside the box, then stopped (notes on two labels: one became a split, one inflated the share of an agreed calibration box). | Cropland presence and share too high. | Counts only if the second labeller agrees. Bound: Aweil box share 10.3%-18.3% if all splits were empty or cropland. |
| Share classes | The share of the box is a class (none, under 10, 10-25, 25-50, over 50%), turned into its middle. The two labellers chose the same class for 35% of the boxes both called cropland. | Rounding either way: in Aweil 2.3% to 5.2% if every label sat at the bottom or top of its class (worst cases). | Averaged over two labellers and many boxes; the presence measure does not use it. |
| Fallow | In 2025 a fallow field looks like grass; "fallow" was used 7 times in 900 labels. | Cropland area too low; maps that count fallow look less precise. | Reported for both definitions; they differ by under 0.1 percentage point. |
| Clouds | Few clear Sentinel-2 images in June-September; no radar pass over Aweil in January-April 2025. | The green-up cue is harder to see. | A radar curve for the cloudy months; "unsure" allowed and left out. |
| No ground visit | The reference is what five students see on images, after a written key and a 30-point pilot. | Unknown; small fields in grass are the hardest. | Two blind labellers per box; a field check by ZOA staff recommended. |
| Labeller drift | Practice changed during labelling (the box-edge case). | Early labels a little different from late ones. | Labeller pairs balanced over areas, strata and splits, so drift does not pile up in one stratum. |
| Flood masks | MODIS cells of 232 m, daily; cloud gaps are not flagged; short floods and rain waterlogging can be missed. | Flooded land, and so every exposure number, too low. | The same flood layer for every map and the sample, so comparisons are fair; absolute hectares are a lower bound on flooded land. |
| Cropland in past years | Past floods are overlaid on today's cropland (labels and our map of 2025; public maps of their own year). | A scenario, not a hindcast of real cropland. | Said wherever past floods are used. |

## Appendix C. Features and models

![Figure 14](../figures/22_feature_distributions.png)

*Figure 14. The 18 features for boxes with and without cropland (all points both labellers agree on). Cropland boxes are near buildings, have field edges and texture, a stronger harvest drop and lower radar in June, and are rarely burned.*

![Figure 15](../figures/19_rule1_decision_space.png)

*Figure 15. Every agreed point on Rule 1's two inputs. Orange area: where Rule 1 says crop (a building within 333 m and field edges above 0.094). Left: the calibration points it was fitted on; right: the test points it was scored on after freezing.*

![Figure 16](../figures/21_what_models_learned.png)

*Figure 16. What the models learned from the same 18 inputs: the logistic regression's coefficients (change in log-odds of crop per standard deviation; orange: more crop) and the random forest's importances.*

*Table 9. The 18 features of a 210 m box. Each is first computed for every 10 m pixel of 2025 and then summarised over the box's 21 × 21 pixels by its most crop-like part (last column), so the model sees one value per feature per box.*

| Feature | What it measures | Cue | Over the box |
|---|---|---|---|
| ndvi_min_am | greenness, lowest April-May | a: bare soil before sowing | 10th pct. |
| bsi_max_am | bare-soil index, highest April-May | a: bare soil before sowing | 90th pct. |
| ndvi_peak_jja | greenness, peak June-August | b: green-up | mean |
| greenup | peak minus spring greenness | b: green-up | 90th pct. |
| drop_son | drop from the peak to September-November | c: harvest | 90th pct. |
| drop_vs_500m | that drop minus the 500 m surroundings' | c: harvest earlier than the grass | 90th pct. |
| texture_jja | texture (GLCM contrast) at the peak | d: field shape | 90th pct. |
| edge_density | edge density (Canny edges) at the peak | d: field shape | 90th pct. |
| ndvi_min_jfm | greenness, lowest January-March | trees and shrub | mean |
| water_occurrence | JRC surface water occurrence | water | mean |
| s1_vv_min | radar VV, lowest month | water | mean |
| dist_buildings_m | distance to the nearest building (m) | homesteads | 10th pct. |
| burned | burned November-April | burn scars | mean |
| vh_jun | radar VH, June | cloudy months | mean |
| vh_jul | radar VH, July | cloudy months | mean |
| vh_aug | radar VH, August | cloudy months | mean |
| vh_sep | radar VH, September | cloudy months | mean |
| vh_range | radar VH, range over the year | cloudy months | mean |

*Table 10. Models: F1 in repeated cross-validation on the 125 calibration points (every point alike; 2.5-97.5% of 20 repeats) and on the Aweil test points (stratum weights; 95% interval; frozen models only).*

| Model | Cross-validation | Test |
|---|---|---|
| tree, depth 1 | 0.86 (0.81-0.88) | - |
| tree, depth 2 (= Rule 1) | 0.85 (0.80-0.90) | 0.72 (0.55-0.90) |
| tree, depth 3 | 0.85 (0.80-0.88) | - |
| tree, depth 4 | 0.85 (0.80-0.88) | - |
| logistic regression, 18 inputs | 0.88 (0.85-0.91) | 0.66 (0.49-0.83) |
| logistic regression, L1 (not frozen) | 0.87 (0.83-0.92) | - |
| logistic regression, Rule 1's 2 inputs | 0.87 (0.85-0.89) | 0.61 (0.44-0.78) |
| random forest, 18 inputs (benchmark) | 0.92 (0.90-0.93) | 0.76 (0.58-0.94) |
| random forest, embedding (benchmark) | - | 0.71 (0.53-0.89) |

## Appendix D. Map accuracy in detail

![Figure 17](../figures/10_published_recall_vs_crop_share.png)

*Figure 17. Published recall of each map against the crop share it shows in our areas. The published scores predict which maps show least crop in Aweil, not in Bor South.*

*Table 11. Accuracy of every map on the Aweil test points (cropland; stratified estimators; ± one standard error). Precision 1.00 means right on every crop call; in brackets the 95% Clopper-Pearson lower bound, because a standard error of 0 would overstate the certainty.*

| Map | Year | Precision | Recall | F1 | Overall acc. |
|---|---|---|---|---|---|
| random forest, 18 inputs | 2025 (benchmark) | 0.88 ± 0.10 | 0.67 ± 0.12 | 0.76 ± 0.09 | 0.95 |
| Rule 1 (ours) | 2025 (ours) | 0.70 ± 0.12 | 0.75 ± 0.12 | 0.72 ± 0.09 | 0.93 |
| random forest, embedding | 2025 (benchmark) | 0.77 ± 0.11 | 0.66 ± 0.12 | 0.71 ± 0.09 | 0.93 |
| logistic regression, 18 inputs | 2025 (model) | 0.54 ± 0.10 | 0.84 ± 0.10 | 0.66 ± 0.09 | 0.89 |
| logistic regression, 2 inputs | 2025 (model) | 0.48 ± 0.10 | 0.84 ± 0.10 | 0.61 ± 0.09 | 0.86 |
| WorldCereal 2021 | 2021 | 0.83 ± 0.14 | 0.41 ± 0.11 | 0.55 ± 0.11 | 0.91 |
| DE Africa 2019 | 2019 | 0.40 ± 0.09 | 0.66 ± 0.12 | 0.50 ± 0.08 | 0.83 |
| ASAP v04 | 2017-23 | 1.00 (≥0.94) | 0.28 ± 0.09 | 0.43 ± 0.11 | 0.91 |
| GLAD 2019 | 2019 | 1.00 (≥0.94) | 0.26 ± 0.09 | 0.41 ± 0.10 | 0.91 |
| WorldCover 2021 | 2021 | 1.00 (≥0.94) | 0.22 ± 0.08 | 0.36 ± 0.11 | 0.90 |
| GFSAD 2015 | 2015 | 0.48 ± 0.16 | 0.18 ± 0.05 | 0.26 ± 0.06 | 0.87 |
| Esri 2025 | 2025 | 1.00 (≥0.80) | 0.03 ± 0.02 | 0.06 ± 0.03 | 0.88 |
| Dynamic World 2025 | 2025 | 0.10 ± 0.08 | 0.02 ± 0.01 | 0.03 ± 0.02 | 0.85 |

*Table 12. Every map on the Aweil test points, F1 three ways: on the points both labellers agree on (the main score), and with the 29 test points they split on counted all as cropland, or all as not cropland. Our models stay above every public map in each reading.*

| Map | Agreed points only | Splits as cropland | Splits as not cropland |
|---|---|---|---|
| random forest, 18 inputs | 0.76 | 0.62 | 0.62 |
| Rule 1 (ours) | 0.72 | 0.72 | 0.61 |
| random forest, embedding | 0.71 | 0.55 | 0.61 |
| logistic regression, 18 inputs | 0.66 | 0.71 | 0.56 |
| logistic regression, 2 inputs | 0.61 | 0.67 | 0.52 |
| WorldCereal 2021 | 0.55 | 0.52 | 0.51 |
| DE Africa 2019 | 0.50 | 0.54 | 0.40 |
| ASAP v04 | 0.43 | 0.39 | 0.44 |
| GLAD 2019 | 0.41 | 0.27 | 0.36 |
| WorldCover 2021 | 0.36 | 0.30 | 0.41 |
| GFSAD 2015 | 0.26 | 0.24 | 0.30 |
| Esri 2025 | 0.06 | 0.04 | 0.06 |
| Dynamic World 2025 | 0.03 | 0.03 | 0.03 |

*Table 13. Our scores in Aweil against the range published for the same maps in other African countries (Kerner et al.\ 2024; Adebayo et al.\ 2026).*

| Map | Recall, ours | Recall, published | F1, ours | F1, published |
|---|---|---|---|---|
| ASAP v04 | 0.28 | 0.27-0.92 | 0.43 | 0.21-0.74 |
| DE Africa 2019 | 0.66 | 0.59-0.96 | 0.50 | 0.43-0.85 |
| Dynamic World 2025 | 0.02 | 0.12-0.65 | 0.03 | 0.12-0.63 |
| Esri 2025 | 0.03 | 0.00-0.73 | 0.06 | 0.00-0.75 |
| GFSAD 2015 | 0.18 | 0.37-0.95 | 0.26 | 0.15-0.76 |
| GLAD 2019 | 0.26 | 0.52-0.83 | 0.41 | 0.33-0.75 |
| WorldCover 2021 | 0.22 | 0.34-0.83 | 0.36 | 0.43-0.82 |

## Appendix E. Area, interval and sampling design

![Figure 18](../figures/25_interval_simulation.png)

*Figure 18. How often the interval holds the true area, in 20,000 simulated samples of our exact design per scenario. The usual interval falls short when cropland is rare in stratum A; with the adjusted upper bound coverage is close to or above 95%. *(pending decision 1)**

![Figure 19](../figures/26_points_per_design.png)

*Figure 19. Points needed for a 20% coefficient of variation of the area: our agreement strata (orange) against strata built from a single public map (blue), estimated from our sample.*

## Appendix F. The public maps

![Figure 20](../figures/01_crop_share_per_map.png)

*Figure 20. Share of the land each public map calls crop, in the five Aweil counties, in Bor South and in South Sudan. Lines: FAO/WFP cereal harvested area (modelled) and FAOSTAT arable land.*

![Figure 21](../figures/02_agreement_curve.png)

*Figure 21. Share of the land that at least k of the seven maps call crop (log scale). Bor South has no land where four or more agree.*

![Figure 22](../figures/04_national_crop_share_per_county.png)

*Figure 22. Where each map puts South Sudan's cropland: crop share per county per map, and the crop assessment's 2025 cereal area per state.*

![Figure 23](../figures/05_states_vs_cfsam_2025.png)

*Figure 23. Crop area per state by each map against the 2025 crop assessment (line: 1 to 1), with each map's rank correlation.*

![Figure 24](../figures/06_same_map_every_year.png)

*Figure 24. The same product in different years: Esri (2017-2025) and Dynamic World (2016-2025). Dynamic World changes by a factor of 10 in Aweil and 37 in Bor South.*

## Appendix G. Floods

![Figure 25](../figures/07_flooded_cropland_per_map.png)

*Figure 25. Cropland under the NASA flood extent (June-December) per map, 2022 and 2025; line: the 2022 crop assessment's flood-damaged area.*

![Figure 26](../figures/08_lol_strip.png)

*Figure 26. Along the Lol: crop share within 5 km of the river against the rest of the Aweil counties, per map.*

*Table 14. Past floods on today's cropland: the years with at least five sample points on flooded land (1+ flood day, June-December). Maps: lowest / median / highest of the 8 public layers; sample: ratio estimator, 95% interval. Below: how many of the 8 maps lie below the sample's interval; in all other cases the interval is too wide to tell.*

| Area | Year | Flooded ha | Points | Cropland | Maps (ha) | Sample (ha) | Below |
|---|---|---|---|---|---|---|---|
| Aweil | 2007 | 43,871 | 6 | 4 | 122 / 364 / 2,900 | 4,811 (0-12,679) | 0 |
| Aweil | 2008 | 83,017 | 17 | 13 | 585 / 1,226 / 4,335 | 10,795 (1,862-19,729) | 7 |
| Aweil | 2010 | 58,939 | 12 | 10 | 225 / 585 / 3,215 | 6,093 (0-15,419) | 0 |
| Aweil | 2013 | 23,991 | 7 | 3 | 9 / 151 / 817 | 818 (0-4,564) | 0 |
| Aweil | 2014 | 31,438 | 5 | 3 | 51 / 215 / 1,068 | 913 (0-7,028) | 0 |
| Aweil | 2019 | 16,787 | 6 | 3 | 15 / 87 / 2,604 | 1,105 (0-4,016) | 0 |
| Aweil | 2020 | 62,569 | 9 | 5 | 186 / 417 / 1,645 | 6,817 (0-16,978) | 0 |
| Aweil | 2021 | 41,636 | 9 | 6 | 169 / 489 / 2,123 | 1,879 (0-7,984) | 0 |
| Aweil | 2022 | 53,646 | 11 | 9 | 331 / 869 / 3,572 | 7,263 (639-14,336) | 3 |
| Bor South | 2007 | 35,057 | 5 | 0 | 0 / 1 / 9,479 | 0 (0-2,096) | 0 |
| Bor South | 2010 | 115,198 | 11 | 1 | 0 / 0 / 18,094 | 358 (0-5,154) | 0 |

*Table 15. Trigger hindcast, Aweil, 2000-2025: years in which each layer's flooded cropland reaches the threshold (fires), and in how many of the years the sample can judge it agrees with the sample.*

| Layer | 100 ha: fires | agrees | 500 ha: fires | agrees | 1,000 ha: fires | agrees |
|---|---|---|---|---|---|---|
| ASAP v04 | 10 | 2/2 | 5 | 2/2 | 2 | 1/1 |
| DE Africa 2019 | 12 | 2/2 | 5 | 2/2 | 1 | 1/1 |
| Dynamic World 2022 | 24 | 2/2 | 20 | 2/2 | 20 | 1/1 |
| Dynamic World 2025 | 19 | 2/2 | 7 | 2/2 | 2 | 1/1 |
| Esri 2022 | 16 | 2/2 | 6 | 1/2 | 3 | 1/1 |
| Esri 2025 | 14 | 2/2 | 4 | 1/2 | 0 | 0/1 |
| GFSAD 2015 | 18 | 2/2 | 10 | 2/2 | 9 | 1/1 |
| GLAD 2019 | 7 | 2/2 | 1 | 1/2 | 0 | 0/1 |
| Rule 1 (ours) | 23 | - | 17 | - | 15 | - |
| WorldCereal 2021 | 8 | 2/2 | 4 | 2/2 | 2 | 1/1 |
| WorldCover 2021 | 8 | 2/2 | 1 | 1/2 | 0 | 0/1 |

## Appendix H. Our map over the whole country

Rule 1 was run over all of South Sudan at 30 m (Earth Engine export of 12 October), as a map of land whose 210 m box holds a field. Table 16 compares it on the Aweil test points with the 10 m map and the public maps; Table 17 gives its share per state. Outside the study areas there are no labels, so the map's accuracy there is unknown. Table 18 compares it with the public maps instead, at 20,000 points drawn uniformly at random (by area, seed 42) over the country without the six study counties. At each point we read our map's 30 m pixel and each public map's 10 m pixel. Because our map means "a field within 210 m" and a public map "this pixel is crop", ours marks more land by design; the useful number is the share of the land the public maps agree is crop that our map also marks. This is agreement between maps, not accuracy: where they all miss the same fields, agreement is high and all are wrong.

![Figure 27](../figures/27_national_map.png)

*Figure 27. Our map applied to all of South Sudan (30 m), shown as the share of each 1 km cell where a 210 m box holds a field. Only the outlined areas have labels; elsewhere the map is not checked. Right: per state against the crop assessment's modelled cereal area.*

*Table 16. Our map at 10 m and its 30 m national run on the 186 Aweil test points, next to the public maps (cropland; stratified estimators; ± one standard error).*

| Map | Precision | Recall | F1 |
|---|---|---|---|
| Rule 1, 10 m map | 0.70 ± 0.12 | 0.75 ± 0.12 | 0.72 ± 0.09 |
| Rule 1, 30 m national run | 0.50 ± 0.10 | 0.75 ± 0.12 | 0.60 ± 0.09 |
| WorldCereal 2021 | 0.83 ± 0.14 | 0.41 ± 0.11 | 0.55 ± 0.11 |
| DE Africa 2019 | 0.40 ± 0.09 | 0.66 ± 0.12 | 0.50 ± 0.08 |
| ASAP v04 | 1.00 ± 0.00 | 0.28 ± 0.09 | 0.43 ± 0.11 |
| GLAD 2019 | 1.00 ± 0.00 | 0.26 ± 0.09 | 0.41 ± 0.10 |
| WorldCover 2021 | 1.00 ± 0.00 | 0.22 ± 0.08 | 0.36 ± 0.11 |
| GFSAD 2015 | 0.48 ± 0.16 | 0.18 ± 0.05 | 0.26 ± 0.06 |
| Esri 2025 | 1.00 ± 0.00 | 0.03 ± 0.02 | 0.06 ± 0.03 |
| Dynamic World 2025 | 0.10 ± 0.08 | 0.02 ± 0.01 | 0.03 ± 0.02 |

*Table 17. Our map over South Sudan per state (land whose 210 m box holds a field; an upper bound, not checked outside Aweil and Bor South) against the 2025 crop assessment's modelled cereal area.*

| State | Our map, % | Our map, ha | CFSAM cereal, % | CFSAM cereal, ha |
|---|---|---|---|---|
| Warrap | 28.0 | 1,005,557 | 5.1 | 181,463 |
| Northern Bahr el Ghazal | 23.6 | 727,425 | 3.6 | 111,530 |
| Unity | 9.0 | 333,378 | 0.5 | 19,698 |
| Lakes | 8.0 | 344,345 | 4.3 | 186,953 |
| Central Equatoria | 7.0 | 299,372 | 2.8 | 120,600 |
| Eastern Equatoria | 4.3 | 317,193 | 2.1 | 155,634 |
| Upper Nile | 4.0 | 310,106 | 1.1 | 88,816 |
| Western Bahr el Ghazal | 3.6 | 331,245 | 1.0 | 91,504 |
| Jonglei | 3.2 | 393,768 | 0.6 | 70,829 |
| Western Equatoria | 2.7 | 215,620 | 2.5 | 196,380 |

*Table 18. Without labels: our national map against the public maps at 20,000 uniform random points outside the study areas (our map's 30 m pixel; each public map's 10 m pixel at the point). Agreement, not accuracy. Shares in % of the land; "of 2+ maps": of the land at least two public maps call crop, the share our map marks (- with fewer than five such points).*

| State | Points | Our map | Any public map | Ours, of any | Ours, of 2+ maps | Any, of ours |
|---|---|---|---|---|---|---|
| All (outside our areas) | 20,000 | 5.7 | 5.5 | 21 | 29 | 21 |
| Abyei Region | 338 | 0.0 | 2.4 | 0 | - | - |
| Central Equatoria | 1,432 | 6.6 | 4.7 | 33 | 67 | 23 |
| Eastern Equatoria | 2,447 | 4.2 | 8.4 | 11 | 7 | 21 |
| Jonglei | 3,630 | 3.2 | 6.2 | 8 | - | 17 |
| Lakes | 1,442 | 7.8 | 2.6 | 63 | 83 | 21 |
| Unity | 1,212 | 9.2 | 4.5 | 28 | 60 | 13 |
| Upper Nile | 2,626 | 3.1 | 13.3 | 5 | 2 | 21 |
| Warrap | 1,188 | 29.6 | 9.2 | 87 | 96 | 27 |
| Western Bahr el Ghazal | 3,010 | 3.5 | 0.8 | 56 | 71 | 13 |
| Western Equatoria | 2,675 | 2.5 | 0.5 | 54 | - | 10 |

## Appendix I. Tools for future work

Everything is in the repository: the pipeline in the folder `cropland/`, the report kit next to this report. `METHODOLOGY.md` holds the protocol with its dated change log, `REUSE.md` the guide for a new area, country or season.

*Table 19. What we hand over, what it is for, and where to start.*

| Tool | What it is for | Files, and how to start |
|---|---|---|
| Labelling tool | two people label each 210 m box blind, from monthly Sentinel-2 strips, a radar curve and a dated sub-metre image, with a written key; one CSV per person | `label_tool/`, `label_server.py`, `LABELLING_GUIDE.md`; run `label_server.py` |
| Reuse kit | the whole pipeline for another area, country or season from one configuration file (boundaries, crop calendar, maps, points per stratum, cue texts) | `config/TEMPLATE.toml`, `make_new_area.py`, `REUSE.md` |
| Sampling and estimates | strata from map agreement, the stratified sample, labeller pairs, and estimators with an interval for every area and score | steps `03`-`11`, `estimators.py`, `evaluation.py` |
| Model workbench | fit a tree or a logistic model on calibration points only, freeze it as a JSON file, map it in Earth Engine, score it once | `tree_workbench.ipynb`, `07_fit_rules.py`, `12_other_models.py`, `rules.py` |
| Flood overlay | any frozen model against NASA's flood masks 2000-2025: flooded cropland per year, the trigger hindcast, the before / after map | `10_flood.py`, `10b_flood_history.py`, `10c_flood_map.py` |
| National map | our map over South Sudan, its accuracy on our test points and its agreement with the public maps | `national_map.py`, `national_check.py` (the random points) |
| Results dashboard | one HTML file with the results story (area, map accuracy, exposure, trigger, country, tools); opens without internet | `14_dashboard.py`, `dashboard/template.html`; output `dashboard.html` |
| Report kit | every number and table of this report generated from the result files | `build_report_inputs.py` |
| Labelled data | 450 boxes, two blind labels each, 18 features and every map's value per box: training and test data | `sample.csv`, `labels_final.csv`, `model_table.csv` |

A next group can build on this in five steps. (1) Label boxes outside our two areas, drawn as a stratified sample with the same tool and key, to measure our map and every public map there. (2) Add a flood-prone stratum of about 100 boxes on land that floods often, so that flooded cropland gets its own estimate. (3) Fit better models on the larger set of calibration points, for example one per region with a two-season calendar for Greater Equatoria; freeze each before scoring it, and log it. (4) Repeat the check each season: about 150 boxes, one working day for two people. (5) Rebuild the dashboard and these tables with one command each. What stays fixed is what makes the numbers trustworthy: two blind labellers per box, no third person settling their disagreements, the presence rule on the 210 m box, models fitted on calibration points only and frozen before the test labels are read, and stratified estimators with an interval for every number.

## Appendix J. Protocol and its changes

The protocol (`cropland/METHODOLOGY.md`) was frozen before labelling on 3 October 2026. Every later change is dated there with its reason; in short:

- 30 September (when the sample was drawn): season 2025; fallow counts as cropland; one readable model (Rule 1) instead of hand-written rules; strata from seven maps.

- 4-5 October (before any point was labelled): the unit became the 210 m box; the share of the box was added; disagreements are kept, never settled by a third person; labeller pairs balanced per stratum and split.

- 12 October, after Rule 1 was frozen and before any test label was read: the adjusted upper bound of the area interval *(pending decision 1)* and the evaluation additions (error analysis, trigger agreement, published scores, design efficiency).

- 12 October, after the first test scores: the two logistic regressions, chosen on the calibration points only *(pending decision 2)*; a fix for months without radar passes, which changed no feature value; the configuration for other areas.

- 14 October: the flood results; the cautious bound for the sample's flooded cropland *(pending decision 8b)*; past floods on today's cropland with a ratio estimator and at least five points on flooded land *(pending decision 8c)*.

- 14 October, evening: the 30 m national map scored on the test points (a check, no model changed); our map compared with the public maps at 20,000 random points outside our areas, without labels (agreement, not accuracy); the group decided not to label further.
