# Road access × flood exposure: exploratory analysis (27 Sep 2026)

**Question.** The Logistics Cluster access-constraint maps (new data in `data/Infrastructure/`) give a weekly
status for about 140 road corridors. Joined with the flood masks, are they strong enough to become the
project's impact outcome, instead of (or next to) flooded cropland?

**Short answer.** No, not as a flood-impact outcome. The maps show *which* roads are cut off each year, and
that pattern is stable. But inside a given road, weeks with a satellite flood detection are no more likely to
be "not passable" than weeks without one. For anticipatory action, the timing link is what matters, and it
is absent. The data are still useful in two supporting roles (section 6).

Code: `eda/roads_flood_eda.py` (stages R1–R6) and `eda/roads_flood_figures.py`.
Outputs: `eda/outputs/roads_eda/` (git-ignored). Public figures are copied to `deliverables/figures/roads_*.png`.

---

## 1. What the data are

- 273 map files with rows, 21,892 rows. Two eras that don't join: free-text "callout" maps 2012–2018, and
  tabular maps 2022–2026 with one status per corridor (Passable / Passable with difficulties / Not passable)
  and truck capacity (20 or 40 tonnes). **No maps 2019–2021.** Used here: tabular maps from Jun 2022 on
  (138 weekly maps, 227 corridors after merging reversed and misspelt names).
- One producer: "WFP/Logistics Cluster GIS Unit". Status is the view of a humanitarian truck convoy on a trunk
  road between towns. It is not community access. ZOA works last-mile, by road *or boat* (Q&A 2, slide 25).
- `segment_code` is empty in every row, despite the README. 102 rows have impossible dates (e.g. "2014-00-08").
  120 rows in the tabular era are parser debris (dates, "Alternative Road", coordinates). In the 2022+ maps
  `condition_notes` and `critical_spots` are empty in every row: **no closure has a recorded cause.**
- **There are no coordinates.** Every town name had to be geocoded (section 2).

## 2. How the join was built

1. **Geocoding** (R2). Names were matched against OSM places, OCHA populated places 2022, IOM DTM village
   lists (R12, R16), GeoNames, admin points and health facilities. When a name had several candidates (there
   are 24 places called Madol), the one nearest the corridor's other towns was kept. 150 of 157 places were
   found. Not found: Kilo 30 (773 rows), Roriak, Tumor, Chandoy/Dolo2, Kainuny and two minor ones. Result:
   206 of 227 corridors, **94% of corridor-weeks**, placed on the map. Nyal–Ganyiel (each other's only
   neighbour, with two candidate pairs) was fixed to Panyijiar county; four corridors are flagged low confidence.
2. **Road geometry** (R3). Each corridor was routed along OSM motorable roads (shortest path, main roads
   preferred). 180 corridors follow a real road (median route 1.12× the straight line, so plausible); 26
   remote Jonglei/Upper Nile corridors fall back to straight lines because OSM lacks the track.
3. **Flood exposure** (R4–R5). For every day of 2022–2025, the flood-mask cells (about 230 m) within 250 m,
   1 km and 2 km of each road were counted, both masks together. The main measure: *more than 1% of the
   road's 1 km band flagged at least once in the 10 days before the map*.
4. **Rain** (R5). ERA5 monthly rainfall for the counties each road crosses, weighted by length.

Overlap of maps and flood masks: Jun–Aug 2022 and Oct 2023 – Dec 2025, i.e. 113 maps, 164 corridors,
14,368 corridor-weeks. That covers **two full rainy seasons (2024, 2025)**.

## 3. Hidden EDA: what the data really contain (`figures/hidden/`)

| Figure | Finding |
| --- | --- |
| H1 coverage | Two eras; only ~26 months overlap the daily flood masks. |
| H2 status raster | **97.9% of weekly statuses are unchanged.** 112 of 206 corridors never change. 68 of 138 maps are identical to the week before. |
| H3 status changes | 344 changes in 3 years. **10 dates carry 42% of them** (24 corridors changed on 17 Apr 2025, 22 on 31 Jul 2025). Looks like periodic reclassification, not week-by-week field reports. |
| H4 pooled bins | Pooled, closures rise with flood nearby: 43% not passable without a detection, 80% with one. This mixes "which road" with "which week". |
| H5 robustness | Inside each corridor the link vanishes (section 4): in all 7 robustness specifications, the placebo and both season splits. |
| H6 geocoding QA | 94% of corridor-weeks placed; 26 straight-line corridors. |
| H7 ZOA corridors | Every corridor in Aweil and Bor South, week by week, with flood detections marked. |
| H8 years | **2026 is different:** in Aug–Sep 2026 only 16% of stable corridors are not passable, against 39–47% in 2024–2025. A real change, a drier year or a new coding practice: the data can't tell. The raster (H2) shows many corridors changing at once in June 2026. |

## 4. The key test, explained

Picture two roads. Road A (Bentiu–Guit) runs through the Sudd and has flood detections on about 1,000 days;
road B (Juba–Nimule) never does. A is closed far more often than B. That is a **between-road** difference:
it tells you A is exposed. For an early warning you need something else: **when A floods more than usual,
does A close more than usual?** That is the **within-road** question.

The test compares the weeks of the same corridor (a *fixed effect* per corridor removes everything permanent
about it: location, soil, insecurity) and also removes each calendar month's national average (a *year-month
fixed effect*: the rainy season, national events). Standard errors are clustered by corridor, because the
weeks of one road are not independent.

| Comparison | Extra chance of "not passable" when flood is detected | 95% CI |
| --- | --- | --- |
| Across all roads (pooled) | +38 points | +21 to +54 |
| Same road, flooded vs not-flooded weeks | −4 points | −12 to +3 |
| Placebo: same road, **last year's** flooding | +3 points | −4 to +10 |
| Same road, dry season only (Dec–Apr) | +3 points | −3 to +9 |
| Same road, wet season only (Jun–Oct) | −14 points | −28 to 0 |

The within-road effect stays between −6 and 0 points whatever the band (250 m, 1 km, 2 km), window (10 or 30
days), mask (unusual only) or sample (OSM-routed only, high-confidence geocodes only). The upper confidence
limit never exceeds +10 points. Closures are not timed by detections either: 8% of worsening changes were
preceded by a detection within 30 days, the same as the 9% base rate.

**Why?** Two reasons, both visible in the figures:
- **Timing** (P2). Roads worsen from April to August as the rains build (rain peaks Jul–Aug, 22–29% of the
  annual total each), then stay closed until February–April. Flood detections near roads peak in Dec–Jan,
  when the roads are already closed. The optical masks are known to see little under rainy-season cloud.
- **Resolution** (P4). In Bor South, corridors are not passable 77–92% of the time from September to
  December, yet the masks record almost nothing within 1 km of them (near Bor–Baidit every detection sits
  1–2 km from the road). Whatever closes these roads (standing water on clay soil, flooding below the 230 m
  pixel, insecurity), the masks do not see it, and the maps do not say which it is.

## 5. ZOA's areas specifically

- **Aweil / Lol river (7 corridors).** Trunk roads out of Aweil town. Aweil–Wau is passable throughout;
  Aweil–Gossinga and Aweil–Akun–Gogrial are "with difficulties" all year with 0–1 changes in ~125 weeks;
  Aweil–Yith Pabol was not passable from late 2024 to Mar 2026. Not passable only 3–18% of the time in any month.
  Almost no flood detections. The Lol-river community roads are not on these maps at all.
- **Bor South (12 corridors).** Much more dynamic (up to 8 status changes per corridor), closed most of
  Sep–Jan every year, with near-zero flood detections. This is the one area where the maps say something the
  masks do not.

## 6. What this means for the research objective

**Verdict: not powerful enough to move the RO onto roads as a flood-impact outcome.** Keep flooded cropland
(the Aweil flooded-cropland audit) as the main line. Reasons, in the stakeholders' own terms:

1. ZOA wants to know "what damage, where, when, how certain" (Q&A 2, slide 23). Roads give *where* (a
   stable list), but the masks give no *when* inside a road. A road trigger would reduce to "these roads close
   every year", which is climatology. Session D already found that climatology nearly matches an oracle.
2. The maps answer a WFP truck question (20–40 t convoys on trunk routes). ZOA has no warehouses and works
   last-mile (slides 25, 35); ZOA also has "no experience" with these maps (slide 36). The team brief's
   "access loss to 10 WFP hubs" idea was already a misfit for the same reason.
3. Status updates come in batches and the coding changed in 2026, so any weekly timing model would partly
   learn administrative update dates.

**Two supporting uses are worth keeping (low cost):**

- **Evidence for the audit RO.** "Roads in Bor South are closed for months each year while the MODIS masks
  see no flooding within 1 km" is an independent sign that the public masks miss locally relevant water. It
  fits the fitness-for-use table of the audit. Wording must stay careful: the cause of closure is never
  recorded (`condition_notes` is empty in every 2022+ row).
- **A seasonal access layer for vulnerability and coping capacity.** ZOA says road access "informs the
  vulnerability and coping capacity of local communities… affects whether they are targeted" (slide 34).
  A months-cut-off-per-year table for Bor South corridors is descriptive, cheap and directly usable.

**What would change the verdict:** (a) Sentinel-1 radar flood maps along the corridors showing that closure
onset follows radar-detected water within the same road (radar sees through rainy-season cloud; the team
de-scoped Sentinel-1 for now); or (b) the Logistics Cluster confirming that statuses come from weekly field
reports, not periodic reclassification.

## 7. SLE pointers (leads for the team to research, not essay text)

The SLE lectures rule out AI for the essay's literature review, reading and writing (Lecture 3, p. 13).
These are only links from the findings to lecture concepts; the reading and arguing are the team's.

- **Whose access counts?** "Passable" is defined for a 20–40 t truck, by the agency that runs the convoys.
  Using it to decide which communities are "accessible" imports WFP's logistics view into ZOA's targeting
  (Jasanoff: whose way of seeing counts; Madianou's logic of audit).
- **Invisible places.** Communities off the mapped corridors (the whole Lol river area) have no status at
  all. If road status feeds targeting (slide 34), missing becomes "fine" by default.
- **Data are not self-explanatory** (Letz & Maxwell). Batch updates, a coding break in 2026 and closures
  caused by insecurity are all hidden behind the same three colours. Some closures are conflict-related,
  which touches humanitarian neutrality (slide 37).
- **Technical choices = SLE choices.** Geocoding picked one "Madol" out of 24 and one "Nyal" out of two.
  Those choices decide which people a flood-access model would count.

## 8. Limits of this analysis

Two rainy seasons of overlap; optical MODIS masks only; closure causes never recorded; 26 straight-line corridors
and 4 low-confidence corridors (excluding them changes nothing); Kilo 30 and other Unity junctions unmapped;
ERA5 is monthly, so rain timing within a month is not tested; statuses may lag reality.
