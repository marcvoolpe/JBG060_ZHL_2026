# 1. Context, problem and the need (report: "Context / Problem Background / Motivation", 3 points)

Long notes, 10 Oct 2026. Every number comes from `cropland/eda_public_maps.ipynb`; the CSV next to each claim is in `deliverables/cropland_report/tables/`. Figure numbers refer to `deliverables/cropland_report/figures/` (captions in `README.md`).

> Labelling finished on 12 Oct 2026 (all 450 points labelled twice), so this folder can be shared with the whole group.

---

## 1.1 Draft paragraphs (tight, for the report)

**Problem context.** Floods hit South Sudan every year, and since 2019 they have been the largest in the satellite record (unusual flooding about twelve times the 2003-2019 level, our Sprint 1 EDA). ZOA International wants to act *before* a flood damages livelihoods (anticipatory action), and the Zero Hunger Lab studies what public data can tell them. ZOA works in two places: along the Lol river in the five Aweil counties (Northern Bahr el Ghazal) and in flood-prone Bor South (Jonglei) (Q&A 2, slide 3). There, the impact ZOA names first is a failed harvest because of flooding (slide 6), and the example trigger it gives is a flood that "inundates cropland" (slide 31). About 80% of rural communities live mainly from farming, yet ZOA itself suspects that "the dataset might not capture agricultural land fully" (slide 33).

**Why that is a problem.** A trigger on flooded cropland multiplies two maps: a flood map and a cropland map (the overlay method of Pacetti et al. 2017). The flood side is well studied. The cropland side is not checked anywhere in South Sudan: the largest accuracy study of African cropland maps (Kerner et al. 2024, 11 maps, 8 countries) and its follow-up on area estimation (Adebayo et al. 2026, 6 countries) both leave South Sudan out. Where they did look, the maps often fail on rare crop: in Mali, where only about 2% of the labelled points were crop, the Esri map scores 97% accuracy and an F1 of 0, because it calls no point crop. Pacetti et al. themselves warn that remote sensing "by itself lacks the level of accuracy necessary in a comprehensive food security assessment".

**What our exploration shows.** We put the seven public cropland maps that cover South Sudan, plus the ASAP crop mask from the course data, on one grid (Section 1.2). In the Aweil counties they call between 0.22% and 1.92% of the land crop: a factor 9 (Figure 1). Where two maps call crop, it is mostly not the same land: the best pair shares 16% of its crop area, the median pair 4% (Figure 3), and all seven maps agree on half a hectare out of 3.09 million. In Bor South one map (Dynamic World) calls 9% of the county crop, while the other seven call at most 0.25%. And when we lay the 2022 flood over each map, Aweil's "flooded cropland" ranges from 432 to 5,805 ha, and the national figure from 1,193 to 21,353 ha, against 130,000 ha of flood-damaged cropland in the FAO/WFP crop assessment (Figure 7). A trigger set at 1,000 ha would have fired in Aweil in 2022 under four maps and stayed silent under the other four.

**Motivation.** Whether ZOA's trigger fires, and for whom, therefore depends more on which cropland map someone picked than on the flood. Before any forecast of floods on cropland can be trusted, someone has to measure how much cropland there is in ZOA's areas, with an honest error bar, and how wrong each public map is there. That is what this project does (research objective, file 03).

(~370 words; trim the third paragraph first if the context section must stay near 250.)

---

## 1.2 The exploration in detail (evidence for the paragraphs above)

### How we compared the maps

- **Maps.** The 7 maps we also use to stratify the sample (METHODOLOGY.md section 3): ESA WorldCover 2021, GLAD 2019, Digital Earth Africa 2019, ESA WorldCereal 2021 (temporary crops), Esri Land Cover 2025, Dynamic World 2025 (most common class over the year), GFSAD 2015. Each is turned into crop / not crop exactly as in Kerner et al. (2024). Plus ASAP v04 (course data, crop % per ~500 m cell), and the 2022 versions of Esri and Dynamic World for the 2022 flood year.
- **Grid.** Each map is evaluated on a fine grid (~10 m in the study areas, ~15 m nationally) and the crop pixels are counted inside every cell of the NASA flood grid (1/480 degree, ~232 m). Counting on the fine grid is not a detail: reading a map at a coarse scale in Earth Engine uses its pyramids, which under-count a rare class such as crop.
- **Check.** The share of Aweil land on which 0 / 1-2 / 3+ maps say crop comes out at 94.97% / 4.71% / 0.32%, the same as `cropland/strata_areas.csv`, which Matteo computed separately at 10 m for the sample. The county areas match too (Aweil 3.09 M ha, Bor South 1.40 M ha).
- **Sprint 2 numbers.** Our recomputation reproduces the Sprint 2 slide values for every map except Dynamic World 2022 in Aweil: 0.79% here, against 0.1% on the slide. The slide value was most likely read at a coarse scale (the pyramid problem above). Use 0.8% from now on. ASAP's national flooded cropland in 2022 comes out at 3,884 ha, close to the ~3,700 ha on the slides.

### Finding 1: the maps disagree on how much (Figure 1; `crop_share_by_county.csv`, `national_crop_share.csv`)

Crop share of the land, % (hectares in brackets):

| map (year) | Aweil counties | Bor South | South Sudan |
|---|---|---|---|
| GFSAD 2015 | 1.92 (59,200) | 0.22 | 1.15 (0.74 Mha) |
| GLAD 2019 | 1.00 (30,700) | 0.25 | 0.62 (0.40 Mha) |
| DE Africa 2019 | 1.77 (54,700) | 0.00 | 1.36 (0.87 Mha) |
| WorldCover 2021 | 0.35 (10,800) | 0.00 | 0.38 (0.24 Mha) |
| WorldCereal 2021 | 1.00 (30,800) | 0.01 | 0.68 (0.44 Mha) |
| Esri 2025 | 0.39 (12,000) | 0.03 | 0.35 (0.22 Mha) |
| Dynamic World 2025 | 0.22 (6,700) | **8.99** | 2.80 (1.80 Mha) |
| ASAP v04 (course data) | 0.97 (29,800) | 0.01 | 0.63 (0.41 Mha) |
| *CFSAM 2025, cereals only* | *3.6 (111,500)* | *1.9 (26,000)* | *2.0 (1.26 Mha)* |
| *CFSAM 2022, cereals only* | *5.4 (166,800)* | *1.0 (14,600)* | *1.7 (1.08 Mha)* |
| *FAOSTAT arable land* | | | *3.7 (2.39 Mha)* |

- Aweil: a factor 9 between the lowest (Dynamic World 2025) and the highest map (GFSAD 2015). Aweil East holds the most crop in every map.
- No map reaches even CFSAM's *cereal* area in Aweil, although cropland also includes groundnut, sesame, cassava and fallow. Nationally only Dynamic World comes near, and for the wrong reasons (finding 3).
- The newest maps (Esri, Dynamic World 2025, WorldCover 2021) find the least crop in Aweil; the oldest (GFSAD 2015) the most.
- **CFSAM is modelled, not measured:** cereal area = population x share of households farming x area per farming household (CFSAM 2025, section on methods). Its Aweil figure fell by a third from 2022 (166,843 ha) to 2025 (111,530 ha) while its national figure rose 17%. The drop follows a revision of the state population (1.59 M to 0.99 M), not fewer fields. CFSAM is the best official reference there is, but it is not ground truth. FAOSTAT's arable land for South Sudan is the same number every year from 2021 to 2024 (carried forward); Adebayo et al. (2026) note that FAO imputes about 84% of African land-use data.

### Finding 2: the maps disagree on where (Figures 2 and 3; `agreement_share_of_land.csv`, `agreement_at_least_k.csv`, `pairwise_*.csv`)

- Share of Aweil land called crop by at least *k* of the 7 maps: k = 1: 5.0%, k = 2: 1.2%, k = 3: 0.32%, k = 4 (a majority): 0.07%, all 7: 0.00002% (about half a hectare). Nationally, all 7 agree on 0.00002% of the land.
- Kerner et al. (2024, Table 2) found unanimous crop on less than 0.5% of each of their 8 countries. Aweil is far below even that.
- **Pixel agreement hides it.** Two maps give the same class to 96.7-99.5% of Aweil pixels, which sounds reassuring. It only means that both call most land "not crop". Measured on the crop class itself (intersection over union, IoU), the overlap is 0.01-0.16, median 0.04. Cohen's kappa between maps is 0.01-0.27. WorldCover and WorldCereal overlap most (both ESA, both 2021); Dynamic World overlaps with nothing (IoU 0.01 with every map).
- Bor South: 9.4% of the land has exactly one map calling crop, and that map is Dynamic World; on 0.07% two maps agree.

### Finding 3: the national pattern does not follow the crop assessment (Figures 4 and 5; `state_crop_area_vs_cfsam_kha.csv`, `state_rank_correlation_with_cfsam.csv`)

- Rank correlation (Spearman, 11 states incl. Abyei) between each map's crop area per state and CFSAM 2025's cereal area: GFSAD +0.59, ASAP +0.25, GLAD +0.22, Esri +0.01, WorldCereal -0.08, WorldCover -0.15, Dynamic World -0.17, DE Africa -0.36. Only the oldest map ranks the states roughly as CFSAM does.
- **Western Equatoria**, the state with the largest cereal area in CFSAM 2025 (196,000 ha), is almost empty in every map (100-35,000 ha). Its farms sit in the tree-and-crop mosaic of the green belt, which the maps probably cannot separate from forest.
- **Upper Nile** goes the other way: maps show 28,000-627,000 ha against CFSAM's 89,000 ha. CFSAM covers the traditional smallholder sector only, so the mechanised schemes around Renk are not in it; Dynamic World and DE Africa probably also count wetland grass.
- **Dynamic World's** national total (1.8 Mha) sits close to the statistics, but it comes from Jonglei, Unity, Upper Nile and Eastern Equatoria, where CFSAM records little crop. In Jonglei it shows 625,000 ha against CFSAM's 92,000 ha. A right total for the wrong reasons.

### Finding 4: the same product changes from year to year (Figure 6; `same_map_every_year.csv`)

Esri (2017-2025) and Dynamic World (2016-2025) are remade every year from new images. Evaluated every year on a ~19 m grid (the 2022 and 2025 values match the ~10 m numbers above):

| Aweil counties | Esri | Dynamic World |
|---|---|---|
| crop share, lowest and highest year | 0.32% (2023) - 0.77% (2019) | 0.21% (2025) - 2.09% (2019) |
| largest jump between two years | 0.77% -> 0.36% (2019 -> 2020) | 2.09% -> 0.42% (2019 -> 2020) |
| share of one year's crop still crop the next year | 36-68% | 14-63% |
| land called crop in at least one year | 1.61% | 3.83% |
| land called crop in every year | 0.06% | 0.01% |

- Dynamic World's crop area changes by a factor 10 between years, Esri's by 2.4. A drop to a fifth of the crop area from one year to the next (Dynamic World 2019 -> 2020) is not what happens on the ground; CFSAM's Aweil cereal area moved by a third between 2022 and 2025, and that through a population revision.
- Fields do move and lie fallow, so some turnover is real. But "crop in every year" is almost empty (0.01-0.06% of the land), so neither product has a stable core of fields that a trigger could rely on from season to season.
- Bor South is worse: Esri calls 0.00-0.10% crop every year, Dynamic World between 0.57% (2020) and 21.3% (2022), a factor 37. Only 6% of its 2022 crop is crop again in 2023 (21.3% -> 2.0%); 38% of Bor South is crop in at least one year, 0.01% in every year. The swings do not follow the yearly flooded area either (rank correlation about -0.2 with the NASA flood extent, 2016-2025; 2022 had both the most flood days and the most "crop"), so the flood masks do not explain them. A likely cause is confusion with grassland, whose greenness changes from year to year; the labels confirm it (14 Oct: the 44 test boxes Dynamic World calls crop but the labellers do not are open land without a field, JRC water occurrence 0) (in Bor South only 10 of 120 boxes were called cropland by anyone, and the second labeller rarely confirmed them: positive agreement 0.18), but we cannot prove it.
- Kerner et al. (2024) found map year only weakly related to accuracy. For a yearly trigger the instability matters anyway: a product that changes this much between years cannot show real change, and a map that scores well in one season is not automatically right in the next (one reason to repeat a small check every season, file 05).

### Finding 5: the choice of map moves flooded cropland, and so the trigger (Figure 7; `flooded_cropland_per_map.csv`, `trigger_check.csv`)

NASA MCDWD flood masks (course data), recurring + unusual, cells flooded on at least one day between June and December. The yearly products are taken from the same year as the flood.

| area, year | flooded land | flooded cropland, lowest map | highest map | factor |
|---|---|---|---|---|
| Aweil, 2022 | 53,600 ha | 432 ha (WorldCover) | 5,805 ha (Dynamic World 2022) | 13 |
| Aweil, 2025 | 10,300 ha | 10 ha (Esri) | 306 ha (DE Africa) | 31 |
| Bor South, 2022 | 17,200 ha | 0 ha (3 maps) | 541 ha (Dynamic World); others at most 29 ha | |
| Bor South, 2025 | 29,400 ha | 0 ha (4 maps) | 1,600 ha (Dynamic World); others at most 10 ha | |
| South Sudan south of 10 N, 2022 | 1.11 M ha | 1,193 ha (WorldCover) | 21,353 ha (GFSAD) | 18 |
| South Sudan south of 10 N, 2025 | 0.70 M ha | 170 ha (WorldCover) | 16,010 ha (Dynamic World) | 94 |

- **Against CFSAM 2022:** 130,000 ha of cultivated land damaged by floods (and 65,000 t of cereals lost). Every map puts 1-16% of that under the satellite flood extent. Part of the gap is the flood map (MODIS misses short floods and flooding under cloud, and waterlogging from rain), part is the cropland map. ASAP, the course data, gives 3,884 ha: the "35 times less" on the Sprint 2 slides.
- **Share of a map's cropland that flooded** (the trigger form "y% of the yield", slide 31) also depends on the map: in Aweil in 2022 it is 1.6% (GLAD, DE Africa) to 23.7% (Dynamic World 2022).
- **Duration.** With at least 10 flood days instead of 1, Aweil 2022 drops to 35-1,917 ha: the spread between maps grows to a factor 55.
- **Trigger check** (illustrative hard trigger on hectares, the "pre-determined condition" of slide 31): Aweil 2022, 1,000 ha: fires under WorldCereal, Dynamic World 2022, GFSAD and ASAP, silent under WorldCover, GLAD, DE Africa and Esri. Bor South 2025, 500 ha: fires only under Dynamic World. A 5,000 ha national trigger in 2025 fires only under Dynamic World.

### Finding 6: along the Lol, where ZOA works (Figure 8; `lol_strip_crop_share.csv`, `lol_strip_flooded_cropland.csv`)

Proxy for ZOA's communities: land within 5 km of the Lol river (OpenStreetMap), 246,900 ha or 8% of the Aweil counties.

- 46% of all land that flooded in the Aweil counties in 2022 lies in this strip (24,900 of 53,600 ha).
- Seven of eight maps put relatively more crop in the strip than elsewhere (factor 1.3 to 11); Esri puts less. The strip shares range from 0.25% (Esri) to 4.47% (DE Africa): a factor 18 in exactly the land a flood trigger is about.
- Flooded cropland in the strip in 2022: 31-48 ha (Esri) to 3,575 ha (Dynamic World 2022).

### Finding 7: what the two papers found for these maps, and what that predicts here (Figures 9 and 10; `published_accuracy_of_our_maps.csv`, `published_recall_vs_crop_share_rank_correlation.csv`)

Kerner et al. (2024) and Adebayo et al. (2026) scored six of our seven strata maps (all but WorldCereal) and ASAP on labelled points in 8 and 6 African countries (table in file 02).

- **Accuracy hides failure when crop is rare.** In Mali (about 2% of the labelled points were crop) Esri has 0.97 accuracy and an F1 of 0.00: it called every reference point "not crop". Every map struggles there (mean F1 over 11 maps 0.21). Aweil is a rare-crop landscape too, so we report precision, recall and F1, never accuracy alone.
- **The papers predict Aweil's ranking.** The maps that miss most crop elsewhere (lowest published recall: Dynamic World 0.30, Esri 0.38) are the ones that show the least crop in Aweil (0.22% and 0.39%); the ones that find most (DE Africa 0.81, GFSAD 0.74) show the most (1.77%, 1.92%). Rank correlation +0.89 over 7 maps (Kerner), +1.00 over the 4 maps Adebayo scored. So in Aweil the maps probably differ mainly in how much crop they miss, which points to under-counting, as in both papers.
- **The papers do not predict Bor South.** There the correlation turns negative (-0.39 and -0.80): Dynamic World, with the lowest published recall, shows the most crop (9%), grassland called crop (confirmed by the labels on 14 Oct: open land without a field, no regular open water). A failure that published scores cannot warn about is exactly why a local check is needed.
- **A majority vote is no way out.** Kerner's majority vote of 11 maps was among the best on average (mean F1 0.65); in Aweil, land where at least 4 of our 7 maps say crop is 0.07% of the land.
- Caution: the papers scored other versions of Esri, Dynamic World, WorldCover and ASAP, in other countries and years. The comparison says what to expect, not how accurate the maps are here; our scorecard (SO2) measures that.

### What this means (for the motivation)

1. The number ZOA's trigger needs does not exist yet for its areas: public maps give anything from 0.2% to 9% crop, the official statistic is modelled, and nobody has checked any of them here.
2. Disagreement is not noise around a common answer: the maps put crop in different places, so even a "conservative" choice of map excludes different farmers.
3. The disagreement is largest where it matters: along the river and in flood years.
4. Agreement between maps is not accuracy. Maps trained on similar data can share the same errors, so a majority vote does not settle it either (Kerner et al. 2024 found the majority vote better than most, but not all, single maps; in Aweil it would leave almost no cropland). Only an independent, labelled sample says which map is right. That is the gap our method fills (file 04).
5. Published accuracy elsewhere is a guide, not an answer: it predicts which maps under-count in Aweil, but not Dynamic World's failure in Bor South.

## 1.3 Caveats to keep in the report

- Flood masks: MODIS 250 m, daily, cloud gaps (`cloud_frac` is 0 on every row of the course data, so "no flood" can mean "not seen"); they stop at 10 N. The flood overlay is therefore a lower bound on flooded land, the same for every map, so it does not affect the comparison between maps.
- Exposure is not damage: a flooded field can survive a short or late flood (CFSAM 2025: floods came late, crops were mature, losses limited).
- The Lol strip is a proxy for ZOA's communities; we do not have their sites.
- CFSAM is cereals in the traditional sector only; FAOSTAT is carried forward. Neither is a reference for accuracy, only for order of magnitude.
