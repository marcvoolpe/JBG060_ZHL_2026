# Dashboard plan (draft 12 Oct 2026, revised the same evening)

What we show at the poster (21 Oct, on a laptop) and hand to ZOA afterwards.
It reuses the results of steps 08-12; nothing in it changes the method or the
frozen models.

**Revision 12 Oct (evening), group wishes via Yassin:**
- The dashboard tells **one results story**: before (public maps) against after (our sample and map), what that changes for flood exposure, and what it changes for anticipatory action. Five pages instead of seven.
- **No general course data** (population, income, IPC, health facilities, markets). It is a lot of data, it is not our result, and it pulls attention away from the cropland question. Removed from the old page 5 and the code.
- The **labelling system becomes reusable** for other areas and countries: one config file per area plus a guide (section 5).
- Label statistics and the per-point model plots move to the report and the SLE essay; the dashboard keeps one "how sure are we" box.

## 1. The question it answers

**How much cropland is there in ZOA's areas, how much of it flooded in 2025, and how much does the answer depend on which cropland map you use?** For ZOA: which number to put in a trigger or a proposal, which public map to trust (or avoid) where, and how to repeat the check.

Decided with the team (unchanged):
- Audience: poster demo first, built so ZOA can keep using it.
- Flood layer: observed 2025 flooding only (NASA MCDWD, as in `10_flood.py`). No forecast.
- "Before" = the public maps ZOA would use today (ASAP + 7 maps). "After" = the area from the 450 labelled points and our Rule 1 map. Our other models (two logistic regressions, two random forests) appear only in the model comparison.
- Unit: study-area totals from the sample (with 95% interval) + counties from the maps (labelled "map estimate, not checked").
- Whole country at 30 m shown, labelled "not checked outside ZOA's areas".
- ZOA is fine with the sample points and labels being public.

## 2. Form: one HTML file, built by a script (unchanged)

| Option | For | Against |
|---|---|---|
| **A. One self-contained HTML file** (Python builds it with folium + plotly; layers pre-rendered as images) | Opens with a double click, no install, no server, works without wifi except the satellite basemap; ZOA gets one file (or a GitHub Pages link later) | Layers are images at display resolution (~30-60 m), not 10 m |
| B. Streamlit app | Easy dropdowns in Python | Needs Python and packages on every laptop, ZOA cannot just open it |
| C. Earth Engine app | Full 10 m swipe | Needs internet and an EE login at the poster, two places to maintain |

**Choice: A.** Fallback basemap: one low-resolution Sentinel-2 2025 image embedded in the file.

## 3. Pages: the results story

Numbers below are the results of 12 Oct (steps 09 and 11); the flood numbers follow when `10_flood.py` has run.

### Page 1. Headline
Two cards, one per study area, each: cropland 2025 from the sample (estimate, 95% interval, adjusted upper bound) next to the range of what the public maps say, and flooded cropland 2025 the same way.
- Aweil counties: **3.8% of the land, 116,500 ha** (76,700-156,400; adjusted upper bound 183,100). The public maps count 0.2-1.9% by pixels: **6-51% of the sample figure**, every one of them under.
- Bor South: **0.4%, 5,400 ha** (1,000-9,700; adjusted upper bound 16,500). The maps range from 0.0% to 9.0% (Dynamic World 2025, 23 times the sample).
- One sentence per card, e.g. "In Aweil every public map shows less than half the cropland the labelled sample finds."
Sources: `results/area_adjusted.csv`, `results/pixel_count_bias.csv`, `results/flooded_cropland.csv`.

### Page 2. Before vs after
- **Scorecard** (the key figure): per map, F1 with error bar on the Aweil test points, ordered, public maps in one colour and ours in another. Aweil: Dynamic World 0.03, Esri 0.06, GFSAD 0.26, WorldCover 0.36, GLAD 0.41, ASAP 0.43, Digital Earth Africa 0.50, WorldCereal 0.55, **Rule 1 0.72** (± 0.09). Maps whose intervals overlap are not ranked (METHODOLOGY section 7); say so under the chart.
- **Bor South**: no agreed crop point among the 80 test points, so no recall or F1 there; show false crop instead: Dynamic World calls crop in 44 of 74 boxes the labellers saw no field in; Rule 1 in 1.
- **Model comparison** (the "logistic regression or trees" question), Aweil test F1 with error bars: Rule 1 (tree, one rule with two conditions) 0.72, logistic regression on all 18 features 0.66, logistic regression on Rule 1's two inputs 0.61, random forest benchmarks 0.71-0.76. The logistic models find more fields (recall 0.84 against 0.75) but call more empty land crop (precision 0.48-0.54 against 0.70). The intervals overlap: no model is ranked above another. Plus Rule 1 as a two-question diagram ("Is there a building within 333 m? Are there field edges?").
- **One map view**: three layers only, with an opacity slider: the best public map in that area, Rule 1, 2025 flooding; county borders. No other layers.
Sources: `results/accuracy.csv`, `results/published_vs_ours.csv`, `rule1_2026-10-12.json`.

### Page 3. Flood exposure
- Per study area: flooded cropland 2025 (ha) under each map, as dots on one axis (Aweil: 10-307 ha among the public maps; Bor South: 0-10 ha, Dynamic World 1,606 ha). **Not against a sample band**: only 1 (Aweil) and 2 (Bor South) sample points fall in a flood cell, so the sample cannot measure flooded cropland in 2025 (notes 07, R5). Say so on the page; it is a finding, and the reason for a flood stratum next season.
- **Our map works on the 210 m box**: a pixel means "the 210 m box around it holds a cropped field". Its hectares are land whose box holds crop, so they are drawn against the sample's upper bound ("box holds it"), and the public maps (pixel counts) against the sample's share of box. Say this in the legend; the area figure ZOA should use is the sample's.
- Per county: choropleth of flooded cropland with a selector for the map used, and the county rank under each map: the map you pick changes which county looks worst. Labelled "map estimate, not checked".
- Note on 2025: Aweil flooded little and Bor South widely, so one area shows a season where the map hardly matters and one where it decides the answer.
Sources: `results/flooded_cropland.csv`, county table from `13_dashboard_data.py`.

### Page 4. Anticipatory action
- **Trigger check** with a threshold slider (flooded cropland in ha, e.g. 100-5,000): per map, does the trigger fire? The maps alone already disagree (in Bor South only Dynamic World would fire). The sample says "cannot tell" at every threshold in 2025 (`results/trigger_agreement.csv`), so the page shows the disagreement between maps plus each map's general accuracy (page 2), not a right or wrong per map.
- **What changes for ZOA**, three short boxes from report notes 05 (5.3-5.7): the trigger (map choice can flip it), targeting (missed fields are missed households), sizing a proposal (the honest range belongs in the budget). An illustrative conversion of flooded hectares to farming households (0.76 ha per household, CFSAM 2022) can sit here, marked "illustrative". No population, income or IPC layers.
- **Which map to use where**: Aweil: WorldCereal 2021 or our Rule 1 map; avoid Esri and Dynamic World (they miss almost all fields). Bor South: avoid Dynamic World (paints wetland as crop); the sample is the only reliable number there.

### Page 5. How sure are we, reuse and limits
- **How sure**: 450 points, each labelled blind by two people, 85.6% agreement (kappa 0.70); every area figure has an interval; the usual interval is too narrow when crop is rare, so we also give an adjusted upper bound (simulation in report notes 06).
- **Reuse**: how ZOA or another team repeats it next season (~150 points) or in another area or country (section 5 below), with the link to the guide.
- **Limits**: 2025 only; an outside view from images, no ground visit; Bor South has almost no cropland in the sample, so its figures are wide; county numbers from maps are unchecked; no forecast.

Moved out of the dashboard (to the report / SLE essay): label agreement per pair, the 65 disagreements, crop vs fallow, the test-point scatter and confusion tables, all course socio-economic data.

## 4. Code

```
cropland/
  10_flood.py            + also save results/flood_cells.csv (lat, lon, ha, crop fraction per map)
  13_dashboard_data.py   NEW, needs Earth Engine, run once:
                           layer images (PNG): best public map, Rule 1, 2025 flood per study area,
                           Rule 1 country (30 m); county table of flooded cropland per map
                           -> results/dashboard/
  14_dashboard.py        NEW, no Earth Engine: reads results/ -> deliverables/dashboard.html
```

(11 and 12 are taken by `11_evaluate.py` and `12_other_models.py`.) Anyone can rebuild the HTML with `python cropland/14_dashboard.py` once the results are in git. Each page is one function in `14_dashboard.py`, so people can work on pages in parallel. Counties: `ssd_admin2.geojson` from the course data (Aweil Centre/East/North/South/West, Bor South). New package: `folium` (add to `requirements-cropland.txt`). No WorldPop, IPC or health-facility inputs.

## 5. The labelling system for other areas and countries

**Decision (12 Oct): config + guide.** Still needs Python and an Earth Engine account; no hosted web app.

- **One config file per area**, `cropland/config/<name>.toml` (Python reads TOML without extra packages). `south_sudan_2025.toml` holds today's settings and must reproduce every current number; `TEMPLATE.toml` is the commented copy for a new place.
- **What a user can change there:**
  - where: country boundary and study areas (admin names from a boundary file, or FAO GAUL in Earth Engine for any country), year;
  - when: the crop calendar months behind the cues (bare soil before sowing, green-up, harvest, dry-season trees). South Sudan has one rainy season; a place with two needs other months, and this is the most important thing to change;
  - which public maps build the strata (only maps that cover the country), the points per stratum and the calibration/test split;
  - the cue texts and area notes the labelling tool shows (like the Bor South flood-recession note), and the labeller names.
- **Rules for a new area:** refit with `07_fit_rules.py` on the new calibration labels. Rule 1's thresholds (buildings within 333 m, field edges) were learned in Aweil and must not be copied elsewhere. A hand edit of a rules JSON is allowed but saved as a new dated file and checked on new labelled points, never on the test points used to choose it.
- **What stays fixed** (it is what makes the numbers trustworthy): two blind labellers per point, the presence rule and box share, calibration/test split, freeze before test, stratified estimators with intervals.
- **Guide:** `cropland/REUSE.md`, step by step: make the config, run steps 02-05, share the labelling tool (folder `label_tool/` + `label_server.py`, labels saved as CSV per labeller), merge and fit (06-07), map and score (08-11).

## 5b. Who (to confirm at the next meeting)

| Person | Part |
|---|---|
| Matteo | runs 13, page 1, puts the file together |
| Marc | page 2 map view and page 3 choropleth |
| Wei, Matei | page 2 model comparison (their per-area trees can join if frozen before scoring; Bor South has 1 crop calibration point, so no Bor South-only tree) |
| Yassin | page 4 (anticipatory action), page 5 and the reuse config + guide |
| Matteo + Marc | SLE link |

## 6. Timeline

| Date | Done when |
|---|---|
| 12 Oct | Rule 1 frozen; 09 scored; two logistic regressions frozen and scored; evaluation tables (11) |
| 13 Oct | Rule 1 map assets done (Aweil export restarted 12 Oct after a radar fix); `10_flood.py`; reuse config |
| 14-15 Oct | `13_dashboard_data.py`; results in git (milestone 15 Oct) |
| 16-18 Oct | pages built; first full HTML |
| 19 Oct | dashboard frozen; everyone opens it on their own laptop; poster figures exported from it |
| 21 Oct | poster |
| 25 Oct | report uses the same figures |

## 7. Risks

- **Flood overlay**: done 14 Oct (`results/flooded_cropland.csv`, `flooded_cropland_bounds.csv`, `trigger_agreement.csv`).
- **Map scores read as a ranking**: overlapping intervals are not ranked; write it under the scorecard.
- **County numbers read as fact**: every county value says "map estimate, not checked"; only the study-area totals carry an interval.
- **Bor South over-read**: almost no cropland in the sample; show its interval, say no recall can be computed there.
- **File too large**: three layers per area at 60 m; country layer at 100 m.
- **No wifi at the poster**: fallback basemap (section 2); test with wifi off on 19 Oct.
