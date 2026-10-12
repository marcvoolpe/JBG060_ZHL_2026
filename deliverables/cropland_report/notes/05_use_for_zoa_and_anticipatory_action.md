# 5. What our results mean for ZOA, ZHL and anticipatory action

Long notes, 10 Oct 2026. For the report's **Discussion** ("potential impacts, positive and negative, of a stakeholder using the approach") and **Conclusion** ("concrete recommendations ... linked to findings"), and for the poster. Written to answer the lecturer's feedback on the methodological session: the need is clear and the work enables better forecasts later, "but not sure how it would help ZOA".

> Numbers marked *illustrative* rest on assumptions stated next to them. Numbers on flooded cropland are exposure (land under water), not damage.

---

## 5.1 The short answer (draft paragraph)

ZOA does not need a better cropland map for its own sake. It needs to know, before a flood, **how much farmland in a community is at risk, where, and how sure that number is**, because that number decides whether a trigger fires (Q&A 2, slide 31), how large a proposal or cash budget is (slides 4, 20) and which households are reached (slides 7, 27). Today that number comes from a public map nobody has checked in South Sudan, and the choice of map moves it by a factor 13 to 94 (file 01). Our work gives ZOA three things it can use directly: a checked cropland figure for its two areas with an error bar, a scorecard saying which public map to trust there (and which to avoid, such as Dynamic World in Bor South), and a cheap, repeatable check (protocol, tool, sample-size rule) that local staff can run again next season. For ZHL it adds an exposure layer with known error to any future impact-based flood forecast.

---

## 5.2 Where cropland enters ZOA's anticipatory action

ZOA's process (Q&A 2, slide 4): local staff write an anticipatory action proposal with the community (needs, impact, how to reduce it); ZOA headquarters approves; the proposal goes to a funding call; once funded, local staff monitor early warnings, and the community carries out the actions. "No decision taken solely based on a model." Triggers "usually combine forecasts with data on impacts of past events, exposure and vulnerability" (Anticipation Hub 2023).

| stage | what ZOA needs about cropland | what our work gives |
|---|---|---|
| proposal (needs, impact) | how much farmland the community has, how much floods in past years | cropland area with a CI for its area; flooded cropland in 2022 and 2025 with a CI from the sample (10_flood.py), next to what each map says |
| trigger design | a pre-determined condition (slide 31) that is transparent (slide 40) | which cropland layer to use and how far its hectares can be off; a readable rule-based map whose logic can be explained |
| funding call | a credible budget | ranges of exposed households and cereal by map; the honest range is part of the case |
| monitoring and action | where the threatened fields are | the map that scores best on our test points in that area (recall matters most: missed fields are missed households) |
| after the season | did the trigger make sense? | a yearly check sample (~150 points) to see whether the map still holds |

---

## 5.3 Route 1: the trigger (does it fire?)

ZOA's example trigger: "with at least x% certainty, a flood will take place which inundates cropland resulting in at least y% of total yield reduction" (slide 31). Both the hectares and the y% depend on the cropland map.

From `trigger_check.csv` (observed floods June-December, cells flooded at least 1 day):

| area, season | flooded cropland across the 8 maps | a trigger at ... fires under |
|---|---|---|
| Aweil counties, 2022 | 432 - 5,805 ha | 1,000 ha: 4 of 8 maps (WorldCereal, Dynamic World, GFSAD, ASAP); 5,000 ha: 1 of 8 |
| Aweil counties, 2025 | 10 - 306 ha | 100 ha: 4 of 8; 500 ha: none |
| Bor South, 2022 | 0 - 541 ha | 500 ha: Dynamic World only |
| Bor South, 2025 | 0 - 1,600 ha | 500 or 1,000 ha: Dynamic World only; every other map at most 10 ha |
| South Sudan south of 10 N, 2022 | 1,193 - 21,353 ha (CFSAM: 130,000 ha damaged) | 5,000 ha: 3 of 8 |

- The relative form (y% of the yield) is no safer: the share of a map's cropland that flooded in Aweil in 2022 runs from 1.6% to 23.7% between maps.
- So for the same flood, **whether the trigger fires is decided by the map**, not by the water. A trigger built on a map with low recall stays silent (a miss: "vulnerable people did not receive critical assistance on time", slide 10); one built on a map that calls wetland crop fires on grass (a false alarm: "critical resources spent ... decreased trust", slide 10).
- What we add: the labelled sample gives flooded cropland **with a 95% interval** (10_flood.py, "reference" rows), independent of any map, so ZOA can set "x% certainty" on the cropland part too, and the scorecard tells which map's hectares are closest to it in each area.

## 5.4 Route 2: who is seen (targeting and exclusion)

ZOA targets "households with high exposure to anticipated hazard + limited capacity" (slide 7) and decides at community scale (slide 3). Exposure is decided by the map:

- Where two maps call crop, it is mostly different land (overlap at most 16%, median 4%, Aweil). Choosing a map is choosing which farmers exist for the analysis.
- Along the Lol (5 km strip, where 46% of Aweil's 2022 flooded land is), the maps put 0.25% to 4.47% of the land under crop: a factor 18 in exactly ZOA's working area.
- Whole farming systems drop out: Western Equatoria, with the most cereal area in CFSAM 2025, is nearly empty in every map (tree-crop mosaic). Elsewhere a map can invent farms: Dynamic World calls 9% of Bor South crop, almost certainly wetland and grass.
- How much cropland lies where no map sees any (Aweil stratum A, 95% of the land) comes out of the area estimate; any cropland there belongs to farmers who are outside every map-based targeting. Report it explicitly when the results are in.
- **Which map until our scorecard is in?** The two papers point away from the maps with the lowest recall (Dynamic World 0.27-0.30, Esri 0.38-0.40: they miss most of the real crop) and towards DE Africa and GLAD for finding fields (recall 0.66-0.81). In Aweil this matches what we see (published recall ranks the maps' crop shares, +0.89). But in Bor South, Dynamic World errs the other way and paints about 9% of the county as crop. A map that was fine elsewhere can still fail in ZOA's area; that is what our check is for.
- This is the societal-legal-ethical core: "a map is a way of seeing". Global models trained mostly elsewhere decide whose fields count. Our scorecard makes that visible; recall (producer's accuracy) per map is literally the share of real cropland, and so of farmers, that a map can see.

## 5.5 Route 3: damage and cash sizing (illustrative)

ZOA asked for "harvest loss per household in kg" and changes in food insecurity (slide 20), and says cash is a good way to compensate crop damage (slide 15). Every such number starts from hectares. Upper bound (assumes every flooded field is lost), Aweil counties 2022, from `damage_and_cash_sizing.csv`:

| | lowest map (WorldCover) | highest map (Dynamic World 2022) |
|---|---|---|
| flooded cropland | 432 ha | 5,805 ha |
| cereal at risk (CFSAM 2022 net yield 0.70 t/ha) | 302 t | 4,060 t |
| a year of cereal for (110 kg per person) | 2,700 people | 36,900 people |
| farming households (0.76 ha each, CFSAM 2022) | 570 | 7,640 |
| one month of a survival basket for them (USD 149 per household, REACH 2025, *to verify*) | USD 85,000 | USD 1.14 million |

- A proposal sized on one map can be 13 times smaller or larger than one sized on another, for the same flood. Reviewers of a funding call cannot see this unless the range is shown.
- Nationally in 2022 the maps give 1,035-18,529 t of cereal at risk under the satellite flood extent; CFSAM reports 65,000 t lost. The gap is partly the flood masks (short floods, clouds, rain waterlogging) and partly the cropland maps.
- Caveat to keep: in 2025 CFSAM found losses limited because floods came late and crops were mature. Exposure is the upper bound; damage needs timing and duration (slide 26: duration matters), which a next step can add from the daily flood masks.

## 5.6 Route 4: a cheap check ZOA and ZHL can repeat

ZOA wants local staff, and ideally community leaders, to run things without external technical organisations (slide 24).

- **Time**: labelling took a median 0.5-1.0 minutes per point per person (mean 0.9-2.4; `label_effort.csv`). A yearly check of ~150 points labelled twice is about 5-12 hours of labelling in total: one working day for two local staff, after a short training on the key.
- **Points**: with our Aweil strata and design (150 / 90 / 90) the 95% interval on the cropland share is about ±1.6-3.4 percentage points; a 20% coefficient of variation needs about 290-760 points with optimal allocation, depending on how much crop hides where no map sees it (`sample_size_planning_aweil.csv`). After all labels are in, the relative-efficiency comparison (file 04, 4.5) tells which strata need the fewest points next year.
- **Tools**: open data and code; the labelling server needs only Python; images and features need one Earth Engine run (free for non-commercial use). That Earth Engine step is the part that still needs a technical partner (ZHL or a university); it is an honest limit on "local".
- **What to re-check**: Esri and Dynamic World change a lot from year to year (file 01, finding 4), so a map that scores well in 2025 is not automatically right in 2026. The check is cheap enough to repeat every season.

## 5.7 What it means for ZOA's three actions

| action (assignment) | what the cropland part decides | our contribution |
|---|---|---|
| cash transfers | how many households and how much (budget, targeting) | the household and cereal ranges above, and which map to use per area; a CI on the exposure |
| temporary flood defences (drainage, sandbags, trenches) | where fields lie close to the river | Lol strip shows the maps disagree most there; the labelled points and Rule 1 map show where fields are |
| early harvesting ("highest stakes ... needs high confidence") | which fields hold a crop near maturity when the flood comes | labels record the harvest cue (harvest earlier than the grass, cue c) and crop stage by month; flood timing against the September-October harvest is the next analysis; without a checked cropland layer, the confidence this action needs is not there |

## 5.8 For ZHL and beyond ZOA

- **Impact-based forecasting**: ZHL's long-term aim is a forecast of impact, not of water (assignment, 2.1). Our Sprint 1-2 work showed upstream lakes carry months of signal for unusual floods; this work shows that even a perfect flood forecast would give Aweil anything from 432 to 5,805 ha of flooded cropland in 2022, depending on the cropland map. Exposure error of this size is a precondition to fix, which is what the lecturer meant by "enables more accurate forecasts in the future".
- **A reference set for South Sudan**: 450 points, labelled twice, for 2025, with every answer recorded. It can validate future maps (the role Kerner et al.'s data play for 8 other countries) and our own national map.
- **Food-security monitoring**: crop masks drive crop-condition systems (ASAP, GEOGLAM Crop Monitor); Kerner et al. show that the choice of mask changes the vegetation signal those systems read. ASAP, the course's crop mask, scores among the weakest maps there and gives 1% crop in Aweil.
- **Official statistics**: CFSAM's area is modelled from population and household figures; a design-based sample is an independent cross-check (Adebayo et al. compare their estimates with FAOSTAT the same way). In Aweil, CFSAM's area moved by a third between 2022 and 2025 because of a population revision.
- **"Understand risks associated with data used"** is the first thing ZOA asked of us (slide 2). This is a measured answer for one dataset that every flood-impact estimate in its areas depends on.

## 5.9 Positive and negative impacts of using it (for the Discussion)

Positive:
- Fewer silent misses where maps under-count fields, fewer false alarms where a map paints wetland as crop; triggers with a stated uncertainty, as ZOA asked.
- Transparent: a written key, readable rules, open data; numbers a community meeting can discuss.
- Cheap to repeat, so the check can follow the landscape (returnees expanding fields, CFSAM 2025; fields shifting after floods).

Negative or risky:
- **False precision**: a checked number for two areas can be read as valid everywhere; our national map is not checked outside them and must say so on every page.
- **The sample gives area, not location**: targeting still needs a map, and the best public map in our test may still miss many fields. Combine with community knowledge (ZOA's way of working).
- **Exclusion moves, it does not vanish**: improving the map in ZOA's areas does nothing for farmers elsewhere; a trigger tuned on Aweil may fail in other landscapes.
- **Sensitivity of field maps**: in a conflict setting, maps of who farms where can touch land claims and displacement; share maps at the level ZOA needs, not more.
- **Dependence on Google Earth Engine and on imagery that can disappear** (NICFI ended in 2025): plan for the tool to fall back to Sentinel-2 alone.

## 5.10 What it does not do

- No forecast: the trigger analysis uses observed floods.
- No damage model: exposure only; timing and duration are next steps.
- Two areas, one season. Results elsewhere and in other years need their own check sample.
