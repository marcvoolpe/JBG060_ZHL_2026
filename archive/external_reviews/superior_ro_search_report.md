# Search for a research objective that beats the current candidates

Independent review for the JBG060 group (ZOA / Zero Hunger Lab, South Sudan). 27 September 2026. Brief: `external_deep_research/prompts/superior_ro_search_prompt.md`.

**How to read the labels.** [File] = fact in a repository file; [My check] = something I computed from repository data (script `eda/ro_search_checks.py`); [External] = a source I opened; [Snippet] = seen only in a search-result summary; [Team, not reproduced] = a team result I did not recompute; [Inference] = my judgement. The within-county severity–displacement association from Session E was not computed or looked at. No check in this document joins flood severity to displacement.

## 1. Verdict

A superior RO was found. **C1-R** asks how much growing-season flooding of cropland public satellite data can see in ZOA's areas (the Aweil counties and Bor South, 2021–2025). It uses one stratified point sample, labelled for cropland by two blind interpreters and for inundation by Sentinel-1 radar and the optical masks. It meets the superiority rule against both baselines: 38 points against 31 (v2) and 29 (A), and it is lower on no criterion. The case rests on the data: the current method (masks × ASAP) gives about 3,700 ha of flooded cropland for June–November 2022; CFSAM reports 130,000 ha damaged. **C3** (optical vs radar detection by month) also meets the rule and is the fallback if the team cannot afford the labelling. C1-R gives no lead time and no yield loss, and depends on a labelling pilot passing.

## 2. Verification of team claims

Status labels: **Verified (file)** = I found it in a repository file or reproduced it from repository data; **Verified (external)** = confirmed in an external source I opened; **Team claim, not reproduced** = documented by the team but I did not recompute it; **Corrected** = the claim is wrong or needs rewording; **Not verified**.

| # | Claim | Status | Source |
|---|---|---|---|
| 1 | ZOA works along the Lol (NBeG) and in flood-prone Bor South; decisions at community level | Verified (file) | Slides 3, 4 |
| 2 | ZOA needs 3–14 days of lead time | Verified (file) | Slide 8 ("14 days: definitely enough; 10 days: suffices; 3 days: minimum") |
| 3 | Priority impact is harvest failure, but all groups count (IDPs, returnees, hosts, pastoralists) | Verified (file) | Slides 6, 7, 38 |
| 4 | Transparent, interpretable results with certainty; rigorous small sub-problem | Verified (file) | Slides 5, 9, 11, 19, 29, 40 |
| 5 | First need: data risks; second: flood dynamics | Verified (file) | Slide 2 (a, b) |
| 6 | ZHL ranks conditions > precursors > early warning | Verified (file) | Slide 28 ("likely 1 → 2 → 3") |
| 7 | ZOA's own trigger wording | Verified (file), with a correction | Slide 31. The x% is the probability that the flood occurs; it is not the measurement uncertainty of flooded cropland. Baseline A's purpose statement conflates the two. |
| 8 | ET has no flood record in 38% of county-seasons with OCHA ≥ 10,000 affected | Verified (file) | `eda/STAGE32_GATE.md` l. 34: 0.617 of 115 (Wilson 95% CI 0.526–0.701), so 38.3% have none |
| 9 | OCHA and ET are not independent | Verified (file + external), partial | ET Readme sheets say findings are "triangulated with secondary sources, such as reports by other humanitarian actors" (`data/IOM_DTM_event_tracking/*2022*`, `*2023*`, `*2025*` Readme). OCHA 2025 displaced equals the ET 2025 flood total exactly in 2 of 20 counties with non-zero OCHA displacement (Aweil North 16,820; Mayendit 6,122) and diverges elsewhere (my comparison of `ss_people_affected_and_displaced_by_floods_20251130.xlsx` with `stage32_et_origin_season.csv`). Review 2 cites OCHA 2024 Flash Update No. 5 attributing displacement figures to IOM (not opened by me). |
| 10 | "No record" is not "no displacement" | Verified (file) | ET Readme (2022–2026 files): "movement over 50 households … IOM cannot guarantee comprehensive coverage of displacement or return events countrywide." |
| 11 | Within-county ET–OCHA r = 0.11 | Verified (file) | `eda/STAGE32_GATE.md` l. 40: r_w = 0.111, county-bootstrap 95% CI −0.180 to 0.395, n = 133, 48 counties |
| 12 | Within-county test detects only large effects under the simulated recording model | Verified (file) | `eda/STAGE34_GATE.md` l. 12, 20–21: MDE80 = ∞ at Rx 0.6 / Ry 0.24; l. 45: MDE80 ≈ 0.47–0.48 only at Rx 0.8 |
| 13 | That conclusion depends on the simulation's assumptions | Verified (file + reviews), with a caveat | `STAGE34_GATE.md` l. 106–113 lists assumptions not fixed by the pre-registration (κ = 0.5, rank-matched detection heterogeneity); the 300-person recording threshold is at l. 96. Review 2 is right that the 0.24 cap is not a general consequence of π = 0.617. Review 1's closed-form derivation (R_y = π / (1 + (1−π)/CV²) = 0.243) is algebraically correct for independent Bernoulli thinning, but it assumes CV ≈ 0.5, which is implausible for zero-inflated, right-skewed counts (CV > 1 is typical). With CV = 2 the same formula gives 0.56. So the reviews disagree, and Review 1 overstates. |
| 14 | Annual flood extent shows no relation with FEWS harvested area | Team claim, not reproduced | `eda/SESSION_A_CLOSEOUT.md` l. 12 (SA-H1 falsified); `eda/HANDOFF.md` l. 61 |
| 15 | The only cropland layer in the pack is a static ASAP mask at ~500 m | Verified (file) | `Data_overview.xlsx` row 10; raster resolution 0.004464° (my read of `asap_mask_crop_v04.tif`) |
| 16 | Stakeholders suspect cropland is undercounted | Verified (file), and supported by data | Slide 33. My comparison: ASAP cropland totals ~407,000 ha nationally vs CFSAM harvested cereal area 1.03–1.18 M ha (2021–2024); ASAP is below CFSAM in 70 of 77 matched counties (median ratio 0.03); Bor South 181 ha vs 15,673 ha; Aweil Centre 391 ha vs 15,798 ha |
| 17 | Masks are internally consistent (split-half 0.91), which is not accuracy | Verified (file) | `eda/STAGE33_GATE.md` l. 11, 34–35 (0.906); both reviews agree it is not accuracy |
| 18 | Detections concentrate in Nov–Feb; low in Jul–Sep | Verified (file) | `STAGE33_GATE.md` l. 54–55 (median county-season Jul–Sep share 0.039; Nov–Dec 0.785); `HANDOFF.md` l. 27 (peak Dec–Feb) |
| 19 | Cause of low Jul–Sep detection unresolved | Verified (file) | The course loader removed cloud information: `Data_overview.xlsx` row 7 says `cloud_frac` was "Removed by github load function", so `cloud_frac = 0` is a preprocessing artefact, not "no cloud" |
| 20 | "Recurring" class uses 2003–2024 (future years) | Verified (external) | NASA Earthdata blog: recurring = flooded in ≥ 7 of 22 years, added December 2025; reprocessed MODIS archive 2003–2025. The course overview's "at least once every three years" (`Data_overview.xlsx` row 7) is consistent. The course files start in 2000, before the documented archive; their 2000–2002 source is undocumented |
| 21 | Detected volume jumps after 2020; hydrology vs product unclear | Verified (file); partly resolved | My sum of Jun–Dec unusual detections: 5.2k km²·dekads/season (2001–2020) vs 45.8k (2021–2025). The jump is concentrated in Unity (27×) and Jonglei (10×), then Lakes (4.2×, on the Sudd margin); the other seven states rose 0.8–2.3× (NBeG 1.8×). A product-wide change would be expected to lift all states, so the pattern favours hydrology (Sudd expansion) for most of the jump, without excluding a smaller product effect. 2019, the first of four consecutive flood years named by CFSAM 2022 (p. 10), is below the 2001–2020 mean. |
| 22 | Aweil Centre / North masks record almost no flooding (2–33, 0–125 km²·dekads per Jun–Dec season, 2021–2025) | Verified (file) | `stage33_severity_season.csv`, combined class: Aweil Centre 2.1–32.8; Aweil North 0.0–124.5. Unusual class: 2.1–25.3 and 0.0–117.8. Aweil East and South are not near zero (hundreds, except 2023) |
| 23 | OCHA reports 45,288 and 48,864 affected in Aweil Centre in 2022 and 2024 | Verified (file) | `ssd_flood_response_211022.xlsx` / `ssd_flood_response_301122.xlsx` (45,288; 59.5% of county population); `ssd_flood_response_20122024.xlsx` (48,864) |
| 24 | Lagged county-month correlations with upstream signals are weak | Verified (file) | `SESSION_A_CLOSEOUT.md` l. 14 (best |ρ| 0.21 hydro, 0.27 precipitation) |
| 25 | January Lake Victoria predicts national flood peak, LOYO skill 0.64, only with post-2019 years in training | Team claim, not reproduced | Team brief artifact "Sudd Flood Research Route", §"short version" and §5 (teammate computation on INFLOW-AI's WFP series); not in this repository |
| 26 | The Lol is a separate basin from the lake-driven Sudd | Supported (external, weak sources) | The Lol joins the Kiir (Bahr el Arab) in the Bahr el Ghazal basin, fed from the Ironstone Plateau, not the equatorial lakes (§4.5; encyclopedia-level sources). No hydrological study of Lol flood drivers found. The IFRC sEAP nevertheless covers Aweil Centre and Aweil East with a Sudd-extent trigger (§4.6) |
| 27 | ConvLSTM ties persistence at one dekad; lead time unresolved; Unity/Jonglei corridor | Team claim, not reproduced | Team brief artifact §2 (F1 0.846 vs 0.842 in 2023; "6 dekads" vs "next dekad"); training script `11_train_convlstm.py` not in this repository |
| 28 | Conflict data sparse; no ACLED | Verified (file) | `SESSION_E_HYPOTHESES.md` l. 18 (67 UCDP type-2 events 2021–25); `data/ACLED_aggregated_african/` is state × week; `data/ACLED_conflict_events/` holds UCDP GED, not ACLED |
| 29 | Exposure-coupled county rankings duplicate existing tools | Verified (external) for the cropland overlay | WFP ADAM reports flooded cropland per county from VIIRS/Floodscan × NASA GFSAD30 with WorldPop (ADAM report 2 May 2024). Flood-PROOFS and REACH claims come from the earlier reviews and were not re-checked |
| 30 | OCHA flood data are a single 2025 snapshot for 36 counties (`HANDOFF.md` l. 36) | **Corrected** | `data/OCHA_flood_data/` holds files for 2021, 2022 (two), 2024 and 2025; Stage 32 used four seasons |
| 31 | Lake Victoria / Kyoga series end in 2002 (`deliverables/REVISED_EDA_REPORT.md`, lake table) | **Corrected** | The course files run to May 2026 (Sentinel-6A rows at the end of `water_level_victoria.txt` and `water_level_Kyoga.txt`); the report's parser read only part of the file |
| 32 | "Floods hit rangeland more than cropland (87% vs 13%)" (`HANDOFF.md` l. 64) | **Needs rewording** | The split uses ASAP, which records ~3% of CFSAM harvested area in the median county (row 16). It describes the mask, not where crops are |
| 33 | Review 1: optical products "capture only 4% of seasonal flood water in July–September" | **Corrected** | 0.039 is the median share of Jun–Dec detections that fall in Jul–Sep (`STAGE33_GATE.md` l. 54), not a capture rate; no capture rate has been measured |
| 34 | SLE extract gives Jasanoff (2017) DOI 10.1177/205395171772447 | **Corrected** | Correct DOI: 10.1177/2053951717724477 (SAGE page) |
| 35 | Review 1: GFM Bentiu validation "CSI of 76.9% and systematic underestimation (bias = 0.88) under dense emergent swamp vegetation" | **Partly corrected** | Numbers verified (JRC131351, pp. 33–34, Table 17: CSI 76.9%, bias 0.879). The report does not attribute the underestimation to vegetation |
| 36 | Prompt and SLE extract: "Eason-Calabria" | **Corrected** | The author is Evan Easton-Calabria (Feinstein International Center; *Disasters* 2025, doi:10.1111/disa.12654) |
| 37 | Review 1: ZOA works in "Aweil Centre, Aweil North, Aweil West" and needs 14 days for "pre-positioning grain stores" | **Not supported** | Slides 3 and 8 name the Lol and Bor South and give 3/10/14-day implementation times only; slide 35 says ZOA has no warehouses |

## 3. Data inventory

### 3a. In the repository (checked on disk, 27 Sep 2026)

| Dataset | Where | Coverage | Grain | Access | Limitation (source) |
|---|---|---|---|---|---|
| Flood masks, "unusual" and "recurring" | Course pack `flood_masks/compact_*` (52 + 52 parquet files) | 2000–2025; tiles h20v08, h21v08 (0–10°N, 20–40°E) | Daily event rows (lat, lon, date) on a 1/480° (~232 m) grid; only flooded pixel-days are stored | In hand | No cloud or no-observation information (`cloud_frac` = 0 because the loader removed it, `Data_overview.xlsx` row 7); "recurring" uses 2003–2024 (§4); blind Jul–Sep (`STAGE33_GATE.md` l. 54); ~9× jump after 2020 concentrated in Unity/Jonglei (my check 4); north of 10°N missing (`deliverables/REVISED_EDA_REPORT.md`) |
| ASAP crop and rangeland masks v04 | Course pack `farmland/` | Static; global | ~500 m (0.004464°), 0–100% cover | In hand | Records ~407,000 ha of cropland nationally vs CFSAM 1.03–1.18 M ha harvested (my check 1) |
| Cattle raster (GHA, ~2010) | Course pack `farmland/` | ~2010 | Raster | In hand | Old (`eda/AA_DATA_ROLES.md`) |
| WorldPop R2025A | Course pack `worldpop/` | 2015–2025, annual | 100 m | In hand | Modelled from 2008 census; see external review on county discrepancies |
| ERA5 precipitation and runoff | Course pack `rainfall and runoff/` | 2000–2025, hourly | 0.25°, 3°S–33°N, 23–37°E | In hand | Reanalysis, not gauges |
| AgERA5 reference ET | Inside `data-JBG060-2026.zip` only | 2000–2025, daily (9,497 files in the zip) | 0.1° | Unzipped folders are empty (0 files) | Needs unzipping |
| Lake levels (Victoria, Kyoga, Albert) | Course pack `Water levels lakes/` | Victoria/Kyoga 1992–May 2026; Albert 2002–2026 | Altimetry passes, ~10-day | In hand | `REVISED_EDA_REPORT.md` wrongly lists Victoria/Kyoga as ending 2002 |
| Discharge (Dartmouth Flood Observatory) | Course pack | 1998–2026 | 12 stations; only 100205 (9.6°N, 31.6°E, near Malakal) in South Sudan; none on the Lol | In hand | Satellite-derived river discharge estimates at few points |
| Admin boundaries (COD-AB) | Course pack | Current | admin0–3 (79 admin2 incl. Abyei; 512 payams) | In hand | — |
| Health facilities | Course pack | Static | Points (1,747 in SSD) | In hand | Completeness unknown |
| IPC acute food insecurity | Course pack `IPC/` | 5 analyses, 2022–2025 | County (current and projected) | In hand | Multi-causal (conflict, prices) |
| CFSAM county crop statistics (FEWS NET data warehouse) | `data/FEWS_crop_data/crop_data.csv` | 2011–2024 (no 2016), main harvest | County × year: harvested area, production, yield of mixed cereals (76–79 counties per year) | In hand | Estimated from population × farming share × area per household, not measured; inaccessible areas by phone (CFSAM 2022 summary pp. 2–3) |
| IOM DTM Event Tracking | `data/IOM_DTM_event_tracking/` | 2020 – Apr 2026 | Event rows: origin and site pcodes, trigger, individuals | In hand | Records moves > 50 households; "cannot guarantee comprehensive coverage" (Readme); 2023 collapse (`STAGE32_GATE.md`) |
| IOM DTM Mobility Tracking | `data/IOM_DTM_mobility/` | Baseline rounds 2–16 (R13–R16 = 2022–2024) | Location/county stocks by arrival year and reason | In hand | Stock, not flow; test-retest 0.00–0.49 (`SESSION_E_HYPOTHESES.md` l. 16) |
| IOM DTM Flow Monitoring | `data/IOM_DTM_flow/` | Jan 2020 – Oct 2023 (34 files) | Flow monitoring points, monthly | In hand | Border/transit points, not flood displacement |
| OCHA flood affected / displaced | `data/OCHA_flood_data/` | 2021 (Dec), 2022 (Oct, Nov), 2024 (Dec), 2025 (Nov) | County snapshots | In hand | "Assessed and verified … might not be a reflection of all those affected" (2022 Readme sheet); shares sources with ET (row 9 of §2) |
| UCDP GED v26.1 and Non-State | `data/ACLED_conflict_events/` (misnamed) | 2011–2025 (1,054 SSD events) | Geocoded events | In hand | 67 type-2 events 2021–25 (`SESSION_E_HYPOTHESES.md` l. 18) |
| ACLED aggregated | `data/ACLED_aggregated_african/` | to week of 5 Sep 2026 | State × week | In hand | No event-level ACLED |
| FEWS NET livelihood zones 2018 | `data/SS_LHZ_2018/` | 2018 | Polygons | In hand | Static typology |
| GeoEPR 2021 | `data/GeoEPR_2021/` | 2021 | Ethnic group polygons | In hand | Not used |

### 3b. External datasets (checked online, 27 Sep 2026)

"Verified" means I opened the producer's page or document. "Snippet" means I saw the fact only in a search-result summary. Items I did not check are marked "not verified" and are not used by the recommended RO unless stated.

| Dataset | Coverage | Grain | Access (verified?) | Limitation |
|---|---|---|---|---|
| **Copernicus EMS Global Flood Monitoring (GFM)**, Sentinel-1 | 1 Jan 2015 – present (GFM Product User Manual 2023, p. 9) | 20 m (PUM pp. 23–24); layers: observed flood extent, observed water extent, reference water mask, exclusion mask, likelihood, advisory flags (PUM pp. 7–9) | Free; portal with login (gfm.portal.geoville.com), WMS with time queries, API, openEO (openEO docs list observed flood extent and reference water mask) — **verified** | Misses floods "in urban areas, densely vegetated areas, or under … strong winds or heavy rainfall" (PUM p. 36); exclusion mask removes no-sensitivity areas incl. dense vegetation (p. 26). Bentiu test (22 Nov 2021): CSI 76.9%, bias 0.879, i.e. underestimation; seasonal-water CSI 10–20% (JRC131351, 2023, pp. 33–34, Table 17) — **verified** |
| **Sentinel-1 GRD** (for own thresholding) | 2014 – present | 10 m | Earth Engine catalogue (asset ID `COPERNICUS/S1_GRD`, not opened this session); Copernicus Data Space | Sentinel-1B lost 23 Dec 2021 → 12-day repeat with one satellite; Sentinel-1C data open from 26 Mar 2025 (Copernicus Data Space news, 25 Mar 2025) — **verified**. Number of acquisitions over the Aweil and Bor areas per season: **not verified** (check on day 1, kill criterion K3) |
| **Google Earth Engine** (platform) | — | — | Free for noncommercial academic use via a registered Cloud project; since 27 Apr 2026 the Community Tier gives 150 EECU-hours/month, and work continues at reduced speed when exhausted (Earth Engine "Noncommercial tiers" page) — **verified** | Registration questionnaire per project |
| **ESA WorldCereal 2021 v100** (temporary crops) | 2021 | 10 m, global, per agro-ecological zone | Earth Engine `ESA/WorldCereal/2021/MODELS/v100`, CC-BY-4.0 — **verified** | Global UA 88.5% / PA 92.1% (snippet, ESSD 2023); no South Sudan figure found |
| **ESA WorldCover 2021 v200** | 2021 | 10 m | Earth Engine `ESA/WorldCover/v200` and direct download (not opened this session) | Africa cropland UA 71.4%, PA 50.8%, "under-represented" in Africa (snippet citing WorldCover PVR v2.0; PDF would not load) |
| **Esri / Impact Observatory 10 m annual land cover** | 2017–2024 (v3) | 10 m, 9 classes incl. Crops | Earth Engine community catalogue, Planetary Computer, AWS (snippet) | "Average accuracy over 75%" (snippet); evaluated in Kerner et al. 2024 |
| **Dynamic World V1** | 2015 – present | 10 m, near-real-time class probabilities | Earth Engine (not opened this session) | Evaluated in Kerner et al. 2024 (F1 varies by country) |
| **NASA GFSAD30** cropland (used by WFP ADAM) | ~2015 | 30 m | Not opened | Used by ADAM (below) |
| **NASA MODIS NRT flood product / reprocessed archive** | Reprocessed MODIS archive 2003–2025; recurring class added Dec 2025 = pixels flooded in ≥ 7 of 22 years (NASA Earthdata blog) — **verified** | ~250 m | Earthdata | Course pack says 2000–2025; the source of the 2000–2002 files is not documented |
| **GMV / ESA-GDA VIIRS flood frequency and duration, South Sudan 2012–2024** | 2012–2024 | 5-day composites; 375 m input, 90 m output (HAND-downscaled) | Zenodo record 18196949, CC-BY-4.0 — **verified** | Stated bounding box starts at 28.59°E, so it appears to exclude the Aweil counties (~26.5–28.3°E) [inference]; VIIRS cannot see through cloud (record text) |
| **WFP ADAM flood impact reports** | Event-based (e.g., 2 May 2024) | Admin2 tables of flooded area, flooded cropland (ha), population | PDF per event (static.gis.wfp.org) — **verified** | Flood = maximum of VIIRS and Floodscan detections; cropland = NASA GFSAD30; population = WorldPop 2022; no accuracy statement |
| **INFLOW-AI** | White Nile basin | Code, trained weights, outputs | GitHub `algorithmicgovernance/INFLOW-AI`, MIT licence — **verified**; forecasts public on JASMIN (IFRC sEAP p. 13) | Target is basin inundation (VIIRS or MODIS configurable); not Lol-specific |
| **GloFAS v4.0 reanalysis** | 1980 – 31 Jul 2022 (EU Data Portal entry) | 0.05° daily discharge | Early Warning Data Store (`cems-glofas-historical`) — **verified (portal entry)** | Model, not observation; not needed by C1-R |
| **CFSAM reports** | Annual | County tables (production, area) and national flood-damage figures | 2022 summary on CLiMIS — **verified** (130,000 ha damaged, 65,000 t lost, p. 1). 2024: "75,000 hectares of cropland impacted by flooding" attributed to FAO (ESSIC news, 26 Nov 2024) — **secondary only** | Estimates, not measurements |
| **Rustowicz et al. crop-type labels** (maize, groundnut, rice, sorghum) | 2016–2017 | Field labels with S1/S2/PlanetScope chips | GitHub link from the paper; Radiant MLHub page — location in South Sudan **not verified** | Five years older than the study period |
| CHIRPS, TAMSAT, ESA CCI / SMAP soil moisture, WaPOR | — | — | **Not verified this session** | Not needed by C1-R (needed by C4) |
| River gauges on the Lol (Aweil, Nyamlell) | — | — | **None found**; the Dartmouth set has no Lol station (course `information.xlsx`) | Absence not proven |
| Planet NICFI basemaps, Esri Wayback, Google Earth historical imagery | — | — | **Not verified this session** | Would help interpretation; Kerner et al. used PlanetScope via Collect Earth Online |
| IOM transhumance tracking for South Sudan; Logistics Cluster access-map archive | — | — | **Not verified** | Needed only by dropped candidates C9, C10 |

## 4. Literature and precedent findings

Search limits: I searched with a general web search engine and opened pages directly. I did not have Scopus or Web of Science, and three planned parallel searches failed on a rate limit. The search is therefore not exhaustive. "Not found" below means not found in this search, not proven absent.

### 4.1 Satellite flood mapping in South Sudan and the Sudd
- **GFM pre-operational quality report** (EFMA/JRC 2023, JRC131351, doi:10.2760/362585). Use case 2, Bentiu, 22 Nov 2021: observed-flood CSI 76.9%, bias 0.879 (underestimation against an independent reference); seasonal-water masks CSI 10–20% for most months (pp. 33–34, Table 17). [External, opened.] Review 1 attributes the underestimation to emergent swamp vegetation; the report does not say that.
- **Downs et al. 2023**, *IEEE TGRS*, doi:10.1109/TGRS.2023.3237461: in South Sudan, GNSS-R (CYGNSS) detected 35.4% more surface water than Sentinel-1; VIIRS and MODIS products underestimated by 4.8% and 83.7%. [Snippet of the abstract; the same figures are cited in `within_county_deep_research_1.md`.] Precedent for "optical MODIS products miss much of the water in South Sudan".
- **EGU24-18873**, *A Comparative Analysis of Flood Frequency Mapping Approaches for Climate-Resilience in South Sudan* (B. Revilla-Romero among the authors): Sentinel-1 vs downscaled VIIRS 5-day flood fraction; VIIRS gave the largest extents and frequencies, which the authors link to its higher imaging frequency; Sentinel-1 lower because of longer revisits. [Snippet of the abstract.] The related GMV dataset (Zenodo 18196949) covers 2012–2024 but appears to exclude the Aweil counties.
- **Chol et al. 2026**, *J. Flood Risk Management* 19(1), doi:10.1111/jfr3.70168: 0.8–2.9 million people exposed to the 100-year flood in the Sudd, "depending on the flood model and population dataset used". [Snippet.] Precedent for "the spread across datasets is large" — for population, in the Sudd, not for cropland in Aweil.
- **NASA Earthdata (2025/26)**: recurring class = flooded in ≥ 7 of 22 years, added December 2025; reprocessed MODIS archive 2003–2025. [External, opened.]
- Not found: any study of optical-mask performance month by month in Northern Bahr el Ghazal or along the Lol.

### 4.2 Radar detection of flooded vegetation and crops
- **Tsyganskaya et al. 2018**, *Int. J. Remote Sensing* 39(8), doi:10.1080/01431161.2017.1420938: flooded vegetation can act as a corner reflector (double bounce), which cannot be identified in single-polarised images; C-band is less suited than L-band under canopies. [Snippet.]
- **GFM Product User Manual 2023**, §5.2 p. 36: missed alarms in densely vegetated areas and under strong wind or heavy rain. [External, opened.]
- Consequence for all radar-referenced candidates: Sentinel-1 measures open-water inundation; it gives a lower bound for flooding under tall sorghum or grass.

### 4.3 Cropland map accuracy for smallholder Africa
- **Kerner et al. 2024**, *Scientific Data* (published 10 May 2024), doi:10.1038/s41597-024-03306-z: 11 maps (including ASAP, WorldCover, Dynamic World, Esri, GLAD, GFSAD, Digital Earth Africa) in eight countries (Kenya, Malawi, Mali, Rwanda, Tanzania, Togo, Uganda, Zambia; **not South Sudan**, Table 4). F1 from 0.21 ± 0.22 (Mali) to 0.71 ± 0.16 (Rwanda); user's accuracy 0.15–0.93, producer's 0.09–0.98; "all maps unanimously agree on a cropland prediction in fewer than 0.5% of pixels in each of the 8 countries"; "no single map can be considered optimal". Reference points were labelled by at least two annotators "blind to the map category" on PlanetScope composites in Collect Earth Online (Methods). [External, opened.] This is the closest method precedent for C1-R/C2 and lowers their novelty; it also shows the labelling design is feasible.
- **ESA WorldCover 2021 validation**: Africa cropland UA 71.4%, PA 50.8% (snippet; PDF would not load). **WorldCereal 2021**: global temporary-crop UA 88.5%, PA 92.1% (snippet).
- **Elmes et al. 2020**, *Remote Sensing* 12(6), 1034, doi:10.3390/rs12061034: inter-interpreter agreement averaged 86% (46–92% by land cover); basemap dates can be out of step with the ground. [Snippet.]
- **Olofsson et al. 2014**, *Remote Sensing of Environment* 148:42–57, doi:10.1016/j.rse.2014.02.015: sampling, response and analysis design for area estimation from a reference sample. [External.]
- My own check (§2 row 16): ASAP holds ~3% of CFSAM harvested area in the median county. Not found: any published accuracy assessment of cropland maps in South Sudan.

### 4.4 Flooded cropland and crop damage estimates
- **WFP ADAM** (e.g., report of 2 May 2024): flooded cropland (ha) per county from VIIRS/Floodscan × NASA GFSAD30, with no accuracy statement. [External, opened.] Duplicates Baseline A's overlay.
- **FEWS NET / University of Maryland / NASA** (ESSIC news, 26 Nov 2024): VIIRS and Landsat flood mapping and 3–6-month flood outlooks with estimated impacts on cropland. [External, opened; news, not a paper.]
- **CFSAM 2022 summary** (FAO/WFP/GoSS, CLiMIS): 130,000 ha of cultivated land damaged by floods, 65,000 t cereals lost; Unity, Jonglei, Upper Nile and NBeG most affected (p. 1); floods affected about one million people, over 70% in NBeG, Unity and Upper Nile; NBeG harvested area −2.3% "mainly due to flooding" (p. 4). Harvested area is computed from population, household size, farming share and area per household (p. 2). [External, opened.]
- **FAO 2024** figure of 75,000 ha impacted (secondary source only).
- Not found: an accuracy assessment of any flooded-cropland figure for South Sudan.

### 4.5 Flood drivers of the Bahr el Ghazal and Lol
- The Lol forms west of Nyamlell and flows past Aweil to the Kiir (Bahr el Arab), within the Bahr el Ghazal basin, which drains the Ironstone Plateau and the Nile–Congo divide rather than the equatorial lakes (Wikipedia "Lol River"; Springer *Encyclopedia of Wetlands* entry "Bahr el Ghazal"). [Snippets; weak sources.] Bahr el Ghazal basin rainfall: June–August about half the annual total (MDPI *Remote Sensing* 16(9):1638, 2024; snippet, page blocked).
- Aweil South: floods historically October–November from river overflow (CSRF county profile; one source).
- Sutcliffe and Parks, *The Hydrology of the Nile* (IAHS 1999) covers the basin; the PDF host refused the connection. **Not verified.**
- Conclusion: "the Lol is outside the lake-driven Sudd" is supported by basin geography, but its flood drivers and warning times have no study I could find. This is why C4 is open in principle and weak in data.

### 4.6 Anticipatory action for floods in South Sudan
- **OCHA Centre for Humanitarian Data (Katch, Jan 2024)**, *Lessons from the 2022 South Sudan floods on acting ahead*: USD 15 M (CERF) + 4 M (SSHF) for Unity; over 55 km of dykes; "no reliable forecast to trigger time-bound actions for a framework". [External, opened.]
- **IFRC sEAP2024SS01 (MDRSS017)**, approved 23 Oct 2025: triggers in June when INFLOW-AI forecasts the Sudd extent rising more than 5 percentage points above the seasonal minimum within two months; 20,000 people, CHF 220,000; target areas include **Bor South, Aweil Centre and Aweil East** (pp. 1–2, 12–14). [External, opened.] So ZOA's Aweil counties already sit under a trigger driven by White Nile / Sudd conditions — a basin they are not in (inference from §4.5).
- **Easton-Calabria 2025**, *Disasters*, doi:10.1111/disa.12654, and the 2023 Feinstein report (listed in the SLE file as "Eason-Calabria"; the author's name is Easton-Calabria): forecast-informed early action is possible where trigger-based AA is not. [Snippet.]
- **Rapson et al. 2026**, INFLOW-AI v2.1, EGUsphere preprint doi:10.5194/egusphere-2026-66 (cited by both reviews and the team brief; not opened by me).

### 4.7 Impact-data gaps in AA
- **OCHA CHD (Feb 2022)**, *Data requirements for anticipatory action*: "Access to impact data is one of the main limitations in implementing anticipatory action in countries with humanitarian operations." [External, opened.]
- IOM ET Readme (in the repository files) and OCHA 2022 Readme: coverage and "assessed and verified" caveats (§2 rows 9–10).
- Diepeveen et al. 2025 and Clausen et al. 2025 (*Big Data & Society*), cited by Review 2, not opened by me.

### 4.8 Precedents that lower novelty, by candidate
| Candidate | Closest precedents | Effect |
|---|---|---|
| v2 | OCHA CHD 2022; Downs 2023; EGU24-18873; JRC131351 | Parts answered; the use-by-use audit is not |
| A | WFP ADAM (same overlay, per county); Chol et al. 2026 (spread across datasets, population) | Core estimate exists operationally |
| C1-R | ADAM; FEWS NET cropland impact outlooks; Kerner et al. 2024 (method, not South Sudan); Downs 2023 | Accuracy of flooded-cropland figures in South Sudan not found |
| C2 | Kerner et al. 2024 | Same question elsewhere |
| C3 | Downs 2023 (MODIS −83.7% in South Sudan); EGU24-18873 | Headline partly answered for South Sudan |
| C4 | none found for the Lol | Open, but untested |

## 5. Candidate list and screening

Baseline scores were fixed before this list was written (§7). Screening rules from the prompt: drop a candidate that breaks the template (one objective; supporting objectives may not add an approach, outcome or need), needs data I could not verify, needs the blinded within-county severity–displacement association, or duplicates an existing tool.

| # | Candidate (short form) | Source of the idea | Screening decision | Reason |
|---|---|---|---|---|
| C1 | **Flooded-cropland measurement in ZOA's areas**: how much growing-season inundation of cropland public satellite data can see in the Aweil counties and Bor South, 2021–2025, against a photo-interpreted cropland sample and Sentinel-1 | Limitations "crop impact", "cropland undercount", "masks blind Jul–Sep", "Aweil near-zero"; slides 6, 17, 31, 33 | **Keep → finalist** | Data verified (§3); no displacement; not an existing tool (ADAM overlays flood × cropland but reports no accuracy; §4) |
| C2 | **Cropland representation audit**: accuracy of five public cropland maps in ZOA's counties against a photo-interpreted sample and CFSAM harvested area; flood exposure shown as the range across maps | Slide 33; my check 1 (ASAP ≪ CFSAM) | **Keep → finalist** | As C1, narrower |
| C3 | **Seasonal flood detectability**: by month (Jun–Nov), what share of radar-observed flooding the course optical masks detect in ZOA's areas, and whether low Jul–Sep detection is cloud or hydrology | Limitation "cause of Jul–Sep low unresolved"; slides 2, 26, 32 | **Keep → finalist** | Data verified; precedent exists for South Sudan in general (§4), not for this product, season split and area |
| C4 | **Flood drivers and warning time, Lol vs Bor South**: which signals (local rain, upstream Lol catchment rain, lake levels, GloFAS reanalysis) precede radar-observed flooding in each area, and by how long | Slides 5, 28, 30; lake-level strand; Lol ≠ Sudd | Keep, not top three | Feasible, but only ~9 seasons (Sentinel-1 from 2017) and a handful of flood onsets per area; many lags make chance findings likely; scores below the finalists (§7) |
| C5 | **GloFAS / Google Flood Hub skill at 3–14 days** for the Lol and Bor | Slide 8 lead time | **Drop** | No gauge on the Lol for verification (§3b); the GloFAS v4 reanalysis ends July 2022 (EU Data Portal entry), so any "truth" would be another model; reforecast download is slow; the Red Cross sEAP already uses INFLOW-AI rather than GloFAS for these areas (§4.6) |
| C6 | **Inundation duration on farmland**: days under water per season on cropland from radar + optical | Slide 26; team brief (duration changed most) | **Merge into C1/C3** | No independent reference for duration; 12-day radar sampling gives bounds only; adds most value as a metric inside C1 or C3 |
| C7 | **Post-2020 product-change test**: is the ~9× jump in detections hydrology or product change, using an independent sensor record | Limitation "post-2020 jump" | **Drop as an RO** (keep as a check) | Mainly a data-risk item for the team's ConvLSTM, not a ZOA decision; my check 4 already narrows it (jump concentrated in Unity/Jonglei) |
| C8 | **Displacement recording completeness in ZOA's counties** (ET vs MT vs OCHA, capture–recapture style) | v2's displacement strand | **Drop** | Capture–recapture needs independent lists; ET and OCHA share sources (§2 row 9); reviews already cover it; displacement is not ZOA's priority impact |
| C9 | **Pastoral exposure**: rangeland inundation and cattle mobility | Slides 13–14, 38 | **Drop** | Only a ~2010 cattle raster in hand; no verified public transhumance tracking for South Sudan (§3); no reference for livestock impact |
| C10 | **Last-mile access loss** (roads/boats) in ZOA's areas during floods | Slides 25, 34; road-access strand | **Drop** | Reference (Logistics Cluster access maps) not verified as an archived dataset; ZOA has "no experience" with them (slide 36); team strand targets WFP hubs, which ZOA does not use (slide 35) |
| C11 | **Trigger error budget**: measurability of each term of ZOA's slide-31 trigger (flood probability, cropland inundated, yield reduction) | Slide 31 | **Drop** | Three terms need three different data sources and methods (template breach); the yield term has no verified data |
| C12 | **Flood timing vs CFSAM yield anomalies** | Slide 20 | **Drop** | Prior null (SA-H1, `SESSION_A_CLOSEOUT.md` l. 12); masks blind in the growing season; CFSAM yields are rounded estimates |
| C13 | **Repeat-flood map by payam** with uncertainty | Slides 21, 43 | **Drop** | Duplicates existing flood-frequency and duration maps (GMV/ESA-GDA VIIRS product 2012–2024, §3b; REACH/World Bank maps cited in the earlier reviews); masks near-zero in Aweil Centre/North, so the map would be wrong exactly in ZOA's area |
| C14 | **Local knowledge vs satellite flood timing** (ZOA staff / community recall) | Slides 4, 24; SLE Lecture 3 p. 21 | **Drop** | Needs new data collection with communities; not possible or ethically cleared in four weeks |

## 6. Finalists in detail

Dates: today is Sunday 27 September 2026. Week 1 = 28 Sep–4 Oct, week 2 = 5–11 Oct, week 3 = 12–18 Oct, week 4 = 19–25 Oct (essay deadline, `SLE_aspects_capstone_extracted.md` §1). Plans assume four to six team members and that the SLE essay is written separately, without AI.

### Finalist C1 — Flooded-cropland measurement in ZOA's areas (recommended, in revised form C1-R)

**First version (before critique).** Two pipelines: (a) a cropland-map accuracy assessment on a stratified reference sample; (b) a wall-to-wall comparison of the optical masks with Sentinel-1 flood rasters; then combine (a) and (b) into flooded-cropland estimates.

**Strongest case against the first version (hostile reviewer).**
1. *Two studies glued together.* A land-cover accuracy assessment and a flood-map validation have different units (points vs rasters), estimators and error models. Combining them multiplies two uncertain factors without a joint error model, so the final interval is not defined. This breaks the one-approach rule in spirit.
2. *Radar is not truth for flooded crops.* C-band Sentinel-1 loses open-water contrast under emergent vegetation and standing crops (sorghum is tall by August–September), and GFM misses floods in densely vegetated areas (GFM user manual p. 36; §4.2). Twelve-day revisits after December 2021 miss short pluvial floods. So "radar-corrected" flooded cropland is still a lower bound, and the optical omission rate measured against radar understates the true omission.
3. *Photo-interpreted cropland is not ground truth.* Smallholder fields are small, intercropped and fallowed; high-resolution basemaps have uncertain dates; interpreter agreement in published smallholder studies ranges from 46% to 92% by land cover (Elmes et al. 2020, *Remote Sensing* 12(6):1034). Some maps (WorldCover, WorldCereal, Dynamic World) are built from the same Sentinel-2 imagery the interpreters look at, which inflates agreement for those maps.
4. *CFSAM is modelled.* Harvested area is population × share of farming households × area per household, not a measurement (CFSAM 2022 summary, p. 2); in inaccessible areas it relies on telephone interviews (p. 3). It is not a reference for area.
5. *No lead time and no yield.* ZOA needs 3–14 days and y% yield reduction (slides 8, 31). The RO delivers neither.
6. *Too big for four weeks* with labelling, two radar pipelines and an essay.
7. *Novelty.* WFP ADAM already reports flooded cropland per county (§4); cropland-map accuracy in Africa has been assessed (Kerner et al. 2024, §4).

**Revision (C1-R).** Points 1 and 6 are fixed by using **one stratified random sample of points as the unit for both terms**. Each point gets a cropland label (two interpreters) and a flood history (radar and optical, every observation date, June–November 2021–2025). One design-based estimator then gives cropland area, flooded-cropland area and the optical omission rate, each with a confidence interval, and the error splits cleanly into "cropland the maps miss" and "flooding the optical masks miss". The only wall-to-wall layer needed is a stratifier (a seasonal radar water-frequency map, or height above nearest drainage as a sensor-independent alternative); everything else is extracted at the points, which removes most of the processing. Points 2–4 are not fixable; they are stated as bounds: radar gives a lower bound on inundation (open water only); interpreters are blind to map labels and double-labelled, with agreement reported and results shown per interpreter; CFSAM is used only as an order-of-magnitude check, never as the reference. Point 3's shared-imagery bias is reported by splitting accuracy into points with and without very-high-resolution imagery. Point 5 is accepted and stated in the RO as out of scope. Point 7 lowers novelty to 3 (§7) but does not remove the contribution: no public product reports the accuracy of flooded-cropland figures in ZOA's areas (§4).

**C1-R in the template's final form.**

> The objective of this project is to evaluate how accurately public satellite data measure cropland inundated during the June–November growing season in ZOA's operating areas (the five Aweil counties along the Lol in Northern Bahr el Ghazal, and Bor South), 2021–2025, using the course's MODIS/VIIRS flood masks, Sentinel-1 radar flood observations and five public cropland maps (ASAP, ESA WorldCover, ESA WorldCereal, Esri Land Cover and Dynamic World). The current estimate (optical flood masks × ASAP cropland) will be compared with a design-based estimate from a stratified random sample of about 900 points, each labelled for cropland by two independent interpreters and for inundation on every radar and optical observation date, and evaluated using the maps' user's and producer's accuracy for cropland, cropland and flooded-cropland area with 95% confidence intervals, the optical masks' omission rate against radar by month, and the ratio of each estimate to CFSAM harvested and flood-damaged area. The results are intended to support ZOA and ZHL in defining the "inundates cropland" condition of ZOA's trigger by stating how much flooding of farmland in its areas public data can observe, in which months, whether missing cropland or missed flooding causes most of the error, and with what certainty.

Supporting objectives (both use the same sample, estimator and outcome):
- SO1: cropland term — accuracy of each cropland map and error-adjusted cropland area at the sample points.
- SO2: flood term — agreement of optical and radar flood observations at the same points, by month and land cover, with each optical miss classed as "under cloud" or "clear sky" from MODIS cloud flags (this absorbs C3's cloud-versus-hydrology question).

**Data.**
- In hand: course flood masks 2021–2025 (both classes, daily, ~232 m); ASAP crop mask v04; admin2/admin3; WorldPop 2021 (settlement stratum); CFSAM county harvested area 2021–2024 (`data/FEWS_crop_data/crop_data.csv`).
- External (§3b): ESA WorldCereal 2021 temporary crops (Earth Engine `ESA/WorldCereal/2021/MODELS/v100`); ESA WorldCover 2021; Esri/IO 10 m land cover 2021–2024; Dynamic World (crop probability composited per season); Sentinel-1 GRD in Earth Engine for point histories and the stratifier, with GFM observed-flood extent (portal/API/openEO) as the alternative radar source; MODIS daily surface-reflectance cloud flags at the points, to split optical misses into "under cloud" and "clear sky" (Earth Engine; asset not opened this session). Labelling in an Earth Engine app or Collect Earth Online (the platform Kerner et al. 2024 used).
- Interpretation imagery: Sentinel-2 monthly composites and NDVI time series 2021–2024; very-high-resolution basemaps (Google Earth Pro historical imagery, Esri World Imagery Wayback) where dated imagery exists.

**Evaluation design.**
- Frame: 20 m cells in the six counties (Aweil counties 30,852 km²; Bor South 13,963 km²; areas from `ssd_admin2.geojson`).
- Strata: number of the five maps calling the cell cropland (0; 1–2; ≥ 3) × flood propensity (cell water in any June–November radar observation 2021–2025, from a seasonal minimum-backscatter layer; if radar access fails, height above nearest drainage < 5 m); the large "0 maps, low propensity" stratum is split by distance to settlement (WorldPop > 0 within 1 km). Stratifiers only change efficiency, not bias, because the estimator weights by stratum.
- Allocation: about 550 points in the Aweil counties and 350 in Bor South, oversampling the flood-propensity strata so that enough flooded cropland points exist.
- Response design: cropland = cultivated in at least one season 2021–2024 (primary; "cultivated in 2022" and "in 2024" as secondary, the two years with the largest OCHA figures in Aweil Centre). Two interpreters label each point blind to the map labels, with a confidence score; disagreements go to a third member. Inundation on each radar date = GFM observed flood (or a documented backscatter threshold in a 3 × 3 window) at the point; optical inundation = the point's mask pixel flagged on the same day ± 1.
- Estimators: stratified estimators for proportions and areas with 95% CIs (Olofsson et al. 2014, *Remote Sensing of Environment* 148:42–57, doi:10.1016/j.rse.2014.02.015); omission rate = share of radar-flooded point-dates without an optical detection, bootstrapped by point.
- Baseline: optical masks × ASAP, the method behind the team's Session B figures (my check 2: 0–470 ha per ZOA county-season; 0 ha in Bor South every year).
- Sensitivity: cropland definition (any year / single year / including fallow); radar flood definition (GFM vs threshold, VV vs VH); matching window (0, ±1, ±3 days); each interpreter alone vs adjudicated labels; settlement-stratum threshold.

**Sample sizes and expected precision (planning assumptions, not data).** With stratum shares and cropland proportions guessed from the maps and CFSAM (Aweil: 3% / 12% / 20% / 65% of area with cropland shares 0.70 / 0.35 / 0.10 / 0.02; 100/150/150/150 points), the cropland share is estimated to about ±0.02 around 0.10 (±21% relative), with about 140 cropland points; the share of cropland that all maps miss would be known to about ±18 percentage points. That is coarse, but the question is whether ASAP's ~1% cropland share in the Aweil counties is off by a factor of ten, which this resolves. Bor South with 350 points: about ±32% relative. For the optical omission rate, 100 radar-flooded point-dates give about ±0.14 and 200 give about ±0.10 (design effect 2).

**Week-by-week plan.**
- Week 1: Earth Engine access for two members (day 1); cropland maps and radar record for both areas (days 1–3); strata and sample drawn (day 3); labelling interface (Sentinel-2 composites, NDVI chart, basemap) (days 2–4); 100-point pilot by two interpreters (day 5). Kill checks K1–K3.
- Week 2: label all points (about 15 hours per interpreter); adjudicate; extract radar and optical histories at the points; first estimates.
- Week 3: final estimators and intervals; error split; CFSAM checks; sensitivity runs; ZOA-facing tables (per county and season) and a month-by-month detectability chart.
- Week 4: write-up; check with ZOA/ZHL and instructors.

**Kill criteria.**
- K1 (day 3): no working radar source (Earth Engine or GFM) → fall back to GFM downloads for 6–10 dates in 2022 and 2024; if that also fails, drop the flood term and run C2 (which does not meet the superiority rule; tell the team).
- K2 (day 5): pilot Cohen's κ for cropland < 0.4 → cropland cannot be verified from public imagery here; report that as the finding, keep only the CFSAM comparison for the cropland term, and continue the flood term (SO2) at the same points, which turns the project into C3. κ 0.4–0.6 → continue, but report both interpreters' estimates as bounds.
- K3 (day 5): fewer than 6 usable radar dates per season in either area → report the gap and restrict the flood term to covered seasons.
- K4 (end of week 2): fewer than 30 cropland points with any radar-observed flooding → flooded-cropland area not estimable with useful precision; report the two terms separately.

**What each result would mean for ZOA and ZHL.**
- Maps miss most cropland → every flood-exposure figure built on ASAP (including the team's "87% rangeland / 13% cropland") understates farmland at risk; ZOA gets the best-performing map for its areas with its measured accuracy.
- Optical masks miss most radar-observed flooding in July–September → optical products cannot monitor farmland flooding during crop growth; in-season triggers need radar, gauges or community reports.
- Radar also sees little flooding in Aweil Centre while OCHA reports 45,288 affected (2022) → impact there comes from flooding no public product records (short, shallow, under crops, or rain damage), and ZOA should build its Aweil trigger on rainfall and local observation rather than satellite extent.
- Estimates approach CFSAM's flood-damage magnitude → public data can support the cropland term, with the stated interval.
- K2 fails → a satellite-based cropland condition in ZOA's trigger cannot be verified without field data; that is a direct answer to slide 33.

**SLE aspect raised.** Representation and classification: the technical choices of which map counts as "cropland" and treating "no optical detection" as "no flood" decide whose fields and whose floods become visible to a trigger (Lecture 1 pp. 7, 10; Lecture 3 p. 11; §19.2; §20 "data understanding"). See §9.

### Finalist C2 — Cropland representation audit

> The objective of this project is to evaluate how completely five public cropland maps (ASAP, ESA WorldCover, ESA WorldCereal, Esri Land Cover and Dynamic World) represent cultivated land in ZOA's counties (the five Aweil counties and Bor South), 2021–2024, using a stratified random sample of about 700 points labelled by two independent interpreters from Sentinel-2 time series and high-resolution imagery. The maps will be compared with each other and with CFSAM county harvested area, and evaluated using user's and producer's accuracy for cropland, error-adjusted cropland area with 95% confidence intervals and the ratio of map area to CFSAM harvested area. The results are intended to tell ZOA which cropland data, if any, can support the cropland part of its flood trigger in its own areas, and how far current flood-exposure figures understate farmland.

- Data, design, estimators, sample size: as C1-R's SO1 (about 700 points).
- Plan: week 1 maps, sample, interface, pilot; week 2 labelling; week 3 estimates, CFSAM comparison nationally for the map-to-CFSAM ratio (77 counties), exposure range using the course masks; week 4 write-up.
- Kill criteria: K2 as in C1-R.
- Results for ZOA: which map to use and how much cropland public maps miss; flood exposure only as a range.
- SLE: as C1-R.

**Strongest case against.** It is a land-cover accuracy study. It does not improve anyone's understanding of flood dynamics, which ZOA lists as a disappointing outcome (slide 9) and ZHL ranks first (slide 28); the flood data enter only as a fixed layer. Cropland-map accuracy in sub-Saharan Africa has been assessed before (§4). **Decision:** drop as a standalone RO; keep as C1-R's fallback if the radar term fails (K1).

### Finalist C3 — Seasonal flood detectability of the optical masks

> The objective of this project is to evaluate how completely the course's MODIS/VIIRS flood masks detect flooding during the June–November season in ZOA's two areas (the Aweil counties and Bor South), 2021–2025, using date-matched Sentinel-1 radar flood observations (Copernicus GFM) as the reference and MODIS cloud flags to separate cloud gaps from absence of water. The masks will be compared with the radar record and evaluated using omission and commission rates and the critical success index by month and land cover, and the bias in detected flood duration. The results are intended to tell ZOA and ZHL in which months public optical flood data can and cannot be used to monitor or trigger action in ZOA's areas, and what that implies for any forecast trained on these masks.

- Data: course masks; GFM or Sentinel-1 GRD; MODIS daily surface-reflectance state flags for cloud (Earth Engine; asset not opened this session; §3b).
- Design: all radar dates June–November 2021–2025 over each area; a stratified random sample of 232 m pixels per date (by land cover and radar water/no water); matching window ± 1 day; cloud-free optical opportunities counted from the MODIS flags; block bootstrap by date.
- Sample: about 15 radar dates per season per area (12-day revisit) × 5 seasons × 2 areas ≈ 150 area-dates.
- Plan: week 1 radar and cloud extraction; week 2 matching and metrics; week 3 sensitivity (threshold, window, GFM vs own threshold), duration bias; week 4 write-up.
- Kill: K1 and K3 as in C1-R.
- Results: a month-by-month table of what the masks see; a cloud-vs-hydrology answer for the July–September gap; guidance for the ConvLSTM strand on what its training target misses.
- SLE: visibility and blind spots (Lecture 1 p. 10; Lecture 3 p. 17, data are "not self-explanatory").

**Strongest case against.** (1) It does not touch harvest, ZOA's priority (slide 6). (2) Sentinel-1 versus optical products has already been compared for South Sudan (§4), so novelty is limited to this product, season split and area. (3) Radar is not truth under vegetation and between passes, so omission is understated. (4) The headline (optical masks are blind in the rains) is expected; only its size is new. **Decision:** keep as the strongest fallback. Its flood-term design is absorbed into C1-R's SO2, which measures the same omission at cropland points and so answers point (1).

## 7. Scores

### 7.1 How the scores were produced
The two baselines were scored after the repository and review reading and before any candidate was scored; that table was saved separately. One revision was made afterwards, for a fact that changed: both baselines had feasibility 3 because they "depend on an unverified access route" (rubric wording). I then verified that GFM and Earth Engine are free and quick to access (§3b), so both move to 4. This raises the bar for the candidates, since the rule requires candidates to match the baselines on feasibility. No other baseline score changed.

### 7.2 Scores table

| RO | 1 Stakeholder | 2 SLE | 3 Novelty | 4 Validity | 5 Soundness | 6 Bias | 7 Coherence | 8 Feasibility | 9 Negative result | Total | Superior to v2? | Superior to A? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **v2** (baseline) | 3 | 5 | 3 | 3 | 3 | 3 | 3 | 4 (was 3) | 4 | **31** (was 30) | — | — |
| **A** (baseline) | 4 | 5 | 3 | 2 | 2 | 2 | 4 | 4 (was 3) | 3 | **29** (was 28) | — | — |
| **C1-R** flooded-cropland measurement | 5 | 5 | 3 | 4 | 4 | 3 | 5 | 4 | 5 | **38** | **Yes** (+7; 1, 2, 7, 8 ≥; no criterion lower) | **Yes** (+9; 1, 2, 7, 8 ≥; no criterion lower) |
| **C2** cropland representation | 3 | 5 | 3 | 4 | 4 | 3 | 5 | 5 | 4 | **36** | Yes (+5) | **No**: criterion 1 is 3 < 4 |
| **C3** seasonal detectability | 4 | 5 | 2 | 4 | 4 | 3 | 5 | 4 | 4 | **35** | Yes (+4; novelty −1 allowed) | Yes (+6; novelty −1 allowed) |
| C4 Lol vs Bor drivers (not a finalist) | 4 | 4 | 3 | 3 | 2 | 3 | 4 | 3 | 3 | 29 | No: criterion 2 (4 < 5), 8 (3 < 4), total −2 | No: criterion 2, 8 |

**Robustness of the verdict.** C1-R stays superior to both baselines if any one of its scores on criteria 3–6 or 9 is one point lower. It fails the rule if its feasibility is judged 3 (below the baselines' 4). If the team thinks roughly 30 person-hours of double labelling is not affordable, the rule fails for C1-R, and C3, which needs no labelling, becomes the recommendation.

### 7.3 Justification per score

**Baseline v2 (fitness-for-purpose audit)**
1. *Stakeholder 3.* It answers ZOA's first stated need ("understand risks associated with data used", slide 2) and names ZOA's areas as case studies. Its centre is displacement, while ZOA's priority is harvest failure (slide 6). It works at county level, while ZOA decides at community scale (slide 3). No finding maps to lead time (slide 8). One stated need, partly met.
2. *SLE 5.* Its own technical choice, treating "no record" as zero versus unobserved, is a representation and visibility question covered in Lecture 1 pp. 7 and 10 and §19.4. Listed sources apply directly (Jasanoff 2017; Haas 2025; Iazzolino and Dhungana 2025).
3. *Novelty 3.* Impact-data gaps in AA are documented (OCHA CHD 2022), and optical-vs-radar comparisons exist for South Sudan (Downs 2023; EGU24-18873). A use-by-use fitness audit of these particular sources is not published; both reviews agree on that.
4. *Validity 3.* The mask strand has a physically independent reference (Sentinel-1/GFM). The displacement strand has none by design, and OCHA and ET share sources (§2 row 9). Usable with major caveats.
5. *Soundness 3.* MDEs over a pre-specified range of recording assumptions is planned sensitivity. The judgement that displacement data are "sufficient" or not still rests on an unidentifiable recording model (Review 2; `STAGE34_GATE.md` l. 106–113).
6. *Bias 3.* Shared sourcing inflates ET–OCHA agreement; "affected" versus "displaced" deflates it; the net direction is unknown. These biases can be bounded, not removed.
7. *Coherence 3.* One product, a source × use matrix, but two data families with different references and methods, plus a simulation strand. Loosely attached parts.
8. *Feasibility 4 (revised from 3).* The displacement analyses are largely built (Stages 31–34), and radar access is verified free (§3b). Three strands still load four weeks.
9. *Negative result 4.* Every cell of the matrix is usable. Part of the displacement verdict is already known, though (r_w = 0.111; detection 0.617), so part of the result is fixed in advance.

**Baseline A (flooded cropland from map spread)**
1. *Stakeholder 4.* It addresses the priority impact (slide 6) in ZOA's areas in ZOA's words ("inundates cropland", slide 31; slide 33). Its stated purpose misreads the x% in slide 31, which is forecast probability, not measurement uncertainty. It gives nothing on lead time or yield.
2. *SLE 5.* The choice of cropland map decides which smallholder fields exist for a trigger: classification and its consequences (Lecture 3 p. 11, Bowker and Star; §19.2).
3. *Novelty 3.* WFP ADAM already publishes flooded cropland per county (flood × GFSAD30), without accuracy. Chol et al. 2026 shows large spread across datasets, but for population in the Sudd. Spread for cropland in ZOA's areas is not published.
4. *Validity 2.* There is no reference for cropland or for flooded cropland. Map spread measures precision, not accuracy. Kerner et al. 2024 found maps unanimously agree on under 0.5% of cropland pixels, so agreement cannot be taken as correctness.
5. *Soundness 2.* The result depends on which maps and sensors are put in the ensemble and on thresholds, with no sampling-based uncertainty.
6. *Bias 2.* WorldCover, WorldCereal and Dynamic World share Sentinel-2 inputs. If they all miss the same smallholder fields, the spread would be small regardless of the truth. My check 2 shows the current overlay is about 35× below CFSAM's flood-damage figure for 2022.
7. *Coherence 4.* One outcome, inundated cropland with its uncertainty.
8. *Feasibility 4 (revised from 3).* Access is verified, and overlays are simple. The fallback is the optical masks × maps.
9. *Negative result 3.* A large spread is informative. A small spread would give false comfort, so one outcome teaches the wrong lesson.

**C1-R (flooded-cropland measurement, single-sample design)**
1. *Stakeholder 5.* It addresses the stated priority (harvest failure, slide 6) in ZOA's two areas (slide 3), in ZOA's own terms: "inundates cropland" (slide 31), "the dataset might not capture agricultural land" (slide 33), "duration and extent … with what reliability" (slide 32), "given a flood, estimating crop damage … relevant" (slide 17). Each finding maps to a decision (§6). It does not give lead time or yield (stated gaps).
2. *SLE 5.* The RO's own choices (what counts as cropland; "no detection" as "no flood") raise representation and classification (Lecture 1 pp. 7, 10; Lecture 3 p. 11), with listed sources (§9).
3. *Novelty 3.* ADAM and FEWS NET produce flooded-cropland figures, Kerner et al. assessed map accuracy elsewhere, and Downs et al. showed MODIS undercounting in South Sudan. The accuracy of flooded-cropland estimates in South Sudan was not found.
4. *Validity 4.* It has two independent references: blind, double photo-interpretation for cropland, and radar (a different physical measurement) for inundation, plus CFSAM as an institutional order-of-magnitude check. Metrics match the outcome (area, UA/PA, omission). Caveat: radar gives only a lower bound under vegetation.
5. *Soundness 4.* A design-based estimator with confidence intervals; sensitivity is planned for definitions, thresholds, matching window and interpreter. The order-of-magnitude conclusion is robust. Precise hectares are not (wide intervals).
6. *Bias 3.* Interpreter bias is measured (κ, per-interpreter results). Shared-imagery bias is bounded by the split between points with and without very-high-resolution imagery. The radar under-detection bias has a known direction but is not removed.
7. *Coherence 5.* One sample, one estimator, one outcome. Both supporting objectives are terms of that outcome.
8. *Feasibility 4.* Access is verified. Point extraction fits in the free tier. There is a fallback chain (K1–K4). About 30 person-hours of labelling and the essay make it tight, not comfortable.
9. *Negative result 5.* Every outcome is usable, including failure of the labelling pilot, which would itself tell ZOA that the cropland condition in its trigger cannot be verified from public imagery (§6).

**C2 (cropland representation audit)**
1. *Stakeholder 3.* Directly answers slide 33 and serves the cropland term of slide 31. It does not improve understanding of flood dynamics, which ZOA lists as a disappointing outcome (slide 9) and ZHL ranks first (slide 28).
2. *SLE 5.* As C1-R.
3. *Novelty 3.* Kerner et al. 2024 did the same elsewhere.
4. *Validity 4.* Blind double labels plus CFSAM.
5. *Soundness 4.* Same estimator as C1-R.
6. *Bias 3.* Shared-imagery and interpreter biases are bounded, not removed.
7. *Coherence 5.* Single outcome.
8. *Feasibility 5.* No radar needed; labelling only.
9. *Negative result 4.* Usable, but says nothing about floods.

**C3 (seasonal detectability of the optical masks)**
1. *Stakeholder 4.* It addresses data risk and flood dynamics (slide 2) in ZOA's areas, and when optical data can support monitoring (slides 26, 32). It does not address harvest.
2. *SLE 5.* Visibility and blind spots; data "not self-explanatory" (Lecture 1 p. 10; Lecture 3 p. 17).
3. *Novelty 2.* Downs et al. 2023 already show a large MODIS undercount in South Sudan, and EGU24-18873 compares Sentinel-1 and VIIRS there. Only the month split, the area and this product are new.
4. *Validity 4.* Radar is a physically independent reference; MODIS cloud flags separate cloud from absence.
5. *Soundness 4.* A simple matched design with planned sensitivity.
6. *Bias 3.* Radar under-detection under vegetation and between passes means omission is understated.
7. *Coherence 5.* One outcome.
8. *Feasibility 4.* One pipeline; access verified.
9. *Negative result 4.* Informative either way, but the headline is expected.

**C4 (Lol vs Bor South drivers and warning time)**, scored because it passed screening: stakeholder 4 (slides 5, 28, 30; not harvest); SLE 4 (the link to Sen's "do not use one factor" and "what is a flood?" is real but indirect); novelty 3 (no Lol study found, search limited); validity 3 (radar target, reanalysis predictors, no gauges); soundness 2 (about nine seasons and a handful of onsets, many lags); bias 3; coherence 4; feasibility 3 (radar time series from 2017 plus rainfall and GloFAS); negative result 3.

## 8. Stakeholder mapping for the recommended RO

| Slide | What the stakeholder said | How the RO responds | Fit |
|---|---|---|---|
| 2 | Start: "a) Understand risks associated with data used; b) help us understand flood dynamics" | (a) is the RO's core: how much cropland flooding the public data can see, with intervals. (b) partly: when in the season flooding on farmland is and is not observed, and for how long | Direct (a); partial (b) |
| 3 | Locally led; decisions at community scale; active along the Lol (NBeG) and in flood-prone Bor South | Scope is exactly these two areas; the unit is the sample point (10–20 m), aggregated to payam and county | Direct |
| 5 | "What is the specific impact of this flood locally?"; "what is the reliability of our prediction?"; "all findings should be transparent: why this finding, at what certainty?" | Every estimate carries a sampling interval and a stated reference; the method is a simple stratified estimator | Direct (certainty); partial (impact: exposure, not loss) |
| 5, 28 | Understand "what can cause a flood" and "at what time scale can we predict"; ZHL ranks conditions > precursors > early warning | Measures the flood condition on cropland; does not study causes or lead time | Partial / gap on precursors |
| 6 | Priority impact: harvest failed due to flooding; small-holder farms dominate | Outcome is inundated cropland in smallholder areas, the physical precondition of harvest failure | Direct |
| 8 | Lead time 3–14 days | Not addressed. The RO measures the quantity a 3–14-day trigger would have to predict and be checked against | Gap (stated) |
| 9 | Disappointing: not improving understanding of flood dynamics; non-nuanced results; "how certain are you?" | Seasonal detectability calendar and intervals; no single-number claims | Partial (dynamics) / direct (nuance) |
| 11 | "Transfer the reliability and risk associated with your recommendation" | Error decomposition: how much of the gap is missing cropland, how much is missed flooding | Direct |
| 17 | "Given a flood, we are estimating the crop damage. Good approach?" "Yes: this is relevant" | The RO estimates flooded cropland given observed flooding, the first half of that approach | Direct |
| 19, 40 | Simple and interpretable over black-box; triggers must be transparent | Stratified sampling and a ratio estimator; no model to explain | Direct |
| 20 | Most relevant: harvest loss per household in kg; change in food insecurity | Not measured; flooded area is not loss. Stated as the next step | Gap |
| 21 | "The more detailed, the better" | Point-level evidence, reported by payam where sample size allows | Partial (sample, not a wall-to-wall map) |
| 22 | "We don't know" where crop-damage data are; start with literature and FAO | Uses FAO/WFP CFSAM (county harvested area; flood-damaged area where reported) as the institutional check | Direct |
| 23 | "What damage is expected where, when, and how certain are you?" | Answers "where and when floods on cropland are observable, and how certain"; not damage | Partial |
| 24 | Local staff should be able to operate and interpret the system | Output is a table and a calendar, not a system; no dependency created | Partial |
| 26, 32 | Duration and extent of inundation matter; "with what reliability?" | Extent on cropland, and observed duration bounds from the radar/optical record, with reliability | Direct (extent); partial (duration, 12-day radar sampling) |
| 31 | Trigger: "with at least x% certainty, flood will take place which inundates cropland resulting in at least y% yield reduction" | Defines and measures the "inundates cropland" condition and its observation error; x% (forecast probability) and y% (yield) stay outside the RO | Partial (one of three terms) |
| 33 | "The dataset might not capture agricultural land fully" | Tests this directly against a reference sample and CFSAM | Direct |
| 43 | Keep repeat floods in mind | Five seasons at the same points show which fields flood repeatedly | Partial |

## 9. SLE mapping for the recommended RO (C1-R)

This section only points to lecture material and listed sources. It contains no essay text; the course forbids AI for SLE reading, literature review and writing (`SLE_aspects_capstone_extracted.md` §1, Lecture 3 p. 13).

Suggested single aspect: **representation and classification — whose fields and whose floods become visible in the data that would drive a trigger.** The other rows show where the same technical choices touch other lecture themes; the essay should pick one.

| Technical choice in C1-R | SLE aspect | Lecture and section | Listed sources that relate (SLE file §22) |
|---|---|---|---|
| Which map defines "cropland" (ASAP vs 10 m maps), and the interpreters' rule for "cultivated" (fallow, intercropping, fields near homesteads) | Classification and its consequences; categories imposed on smallholder land | Lecture 3 p. 11 (normative character of design; Bowker and Star); §19.2; §20 "data preparation" | Bowker and Star, *Sorting Things Out*; Jasanoff (2017) |
| Treating "no optical detection" as "no flood" (the masks store only detections; cloud information removed by the loader) | Data as socially constructed; "what are we measuring… whose way of seeing counts?"; blind spots from unrepresentative data | Lecture 1 pp. 7, 10; §2; §19.9 ("is the data interpreted as if it were self-explanatory?"); Lecture 3 p. 17 (Letz and Maxwell) | Jasanoff (2017); Haggart and Tusikov (2023); Haas (2025); Letz and Maxwell |
| Aweil Centre: near-zero satellite flooding vs 45,288 people affected (OCHA 2022) | Who is visible to a data-driven trigger, and who is excluded | §19.4 (inclusion and exclusion); Lecture 3 pp. 6–7 (technosolutionism; success defined by the easy-to-reach) | Madianou (2025); Iazzolino and Dhungana (2025) |
| Using CFSAM (a government–FAO–WFP estimate) as the institutional check | "Who writes what, and for what reason?"; audit and accountability metrics | Lecture 3 p. 18; Lecture 2 p. 4 (logic of audit) | Madianou (2025); Power (audit) |
| Reporting intervals and error sources instead of a single hectare figure | Documenting unknowns, risks and assumptions in AA | Lecture 3 p. 16 (Chavez-Gonzalez et al.) | Chavez-Gonzalez et al. (2022) |
| "Flooded cropland" as a proxy for harvest failure | Sen: food production and entitlements are not the same as availability; "what is a flood?" | Lecture 2 pp. 8–11 | Sen, "Food, Economics, and Entitlements" |

Checks before the team uses any of these sources: the lecture instruction to verify repeatedly ("one source = no source", Lecture 3 p. 22) applies to them too. Jasanoff's DOI in the course extract is missing a digit; the correct DOI is 10.1177/2053951717724477.

## 10. Risks, kill criteria and what to confirm before committing

### Risks for C1-R

| Risk | Likelihood | Effect | Mitigation / kill criterion |
|---|---|---|---|
| Earth Engine or GFM access is slow or blocked | Low–medium (see §3b) | No radar term | K1 (day 3); GFM portal downloads for 6–10 dates; last resort C2 (does not meet the superiority rule) |
| Interpreters cannot label smallholder cropland reliably | Medium (published agreement 46–92% by land cover; Elmes et al. 2020) | Cropland reference fails | K2 on a 100-point pilot (κ < 0.4 stop; 0.4–0.6 report bounds) |
| Radar sees little in Aweil (vegetated or short floods) | Medium–high | Flooded-cropland area is a weak lower bound | Report as a finding (it is decision-relevant); K4 if < 30 flooded cropland points |
| Sample too small for payam-level results | High | Results by county and area only | State this; do not report payam estimates below ~30 points |
| Scope creep (adding a forecast, yield model or displacement) | Medium | Breaks the template and the timeline | Freeze the protocol in week 1; anything else goes to "future work" |
| Other team strands (ConvLSTM, lake outlook, roads, displacement) lose their place | High | Team friction; wasted work | Decide explicitly with the team and instructors (below); SO2's results feed the ConvLSTM strand as a statement of what its training target misses |
| Essay time | High | Less time for analysis | The labelling can be split across all members; the analysis is a single estimator |

### Confirm with ZOA (via ZHL) before week 2
1. Which payams along the Lol and in Bor South they mean by their areas; whether all five Aweil counties are relevant.
2. Whether open-water inundation of cultivated land is the condition they mean by "inundates cropland" (slide 31), or whether waterlogging and rain damage matter as much. If the latter, the RO measures only part of the hazard, and they should know that from the start.
3. The crop calendar in their areas (planting and harvest months for sorghum and other crops), to fix the "growing season" window.
4. Whether ZOA field staff have dated flood observations for 2022 or 2024 in Aweil that could serve as a spot check (useful, not required).
5. That a result without lead time is useful to them now (slide 17 suggests yes).

### Confirm with the instructors before week 1 ends
1. That a measurement-validation RO with a design-based estimator (rather than a predictive model) is acceptable as the capstone's technical core.
2. That team-produced photo-interpreted labels are an acceptable reference, provided double labelling and agreement statistics are reported.
3. How the team should handle strands that fall outside the group RO (forecast, lake outlook, roads, displacement).

### Confirm inside the team
1. Who holds Earth Engine access (two people, day 1).
2. Who labels (at least two interpreters; ideally four, paired) and who adjudicates.
3. That the Session E within-county association stays blinded. Nothing in C1-R needs it.

## 11. Claims I could not verify, and references

### 11.1 Not verified
- ConvLSTM scores, lead-time ambiguity and training split (team brief; script `11_train_convlstm.py` not in the repository).
- January Lake Victoria → national flood peak, LOYO skill 0.64 (team brief §5).
- SA-H1 null (annual flood vs FEWS harvested area) — team result, not recomputed.
- Where in South Sudan the Rustowicz et al. crop-type labels were collected.
- Number of Sentinel-1 acquisitions per season over the Aweil and Bor areas after December 2021 (check on day 1, K3).
- WorldCover 2021 Africa cropland accuracy (snippet only); WorldCereal accuracy (global snippet only).
- FAO's 75,000 ha flood-impacted cropland for 2024 (secondary news source only).
- Lol flood drivers, timing and any gauge record; Sutcliffe and Parks (1999) could not be opened.
- CHIRPS, TAMSAT, soil-moisture products, Planet NICFI, Dynamic World and Esri asset IDs (not opened this session).
- OCHA's use of IOM figures in the 2024 flash update (cited by Review 2; not opened).
- Flood-PROOFS and REACH details (from the earlier reviews; not re-checked).
- Rapson et al. 2026 (INFLOW-AI v2.1 preprint) content (cited by the reviews and the team brief; not opened).
- Whether ADAM's flooded-cropland figures have ever been validated (no statement found).

### 11.2 References
Repository files are cited in place with path and line. Course material: `good_research_objective.txt`; `course_content/Stakeholder Q&A 2 Slides.pdf` (ZOA and ZHL, 21 Sep 2026; slide numbers as printed); `course_content/SLE_aspects_capstone_extracted.md`.

- Chol, D. M., et al. (2026). Geospatial analysis of population exposure to flooding in the Sudd region, South Sudan. *Journal of Flood Risk Management* 19(1). https://doi.org/10.1111/jfr3.70168 [Snippet]
- Copernicus Data Space Ecosystem (2025, 25 Mar). Sentinel-1C user data opening from 26th of March. https://dataspace.copernicus.eu/news/2025-3-25-sentinel-1c-user-data-opening-26th-march [Snippet]
- Copernicus EMS / EODC et al. (2023). *Global Flood Monitoring (GFM) Product User Manual*, v20231005. https://extwiki.eodc.eu/gfm_assets/gfm_pum_v20231005_compressed.pdf (pp. 7–9, 23–26, 36) [External]
- Downs, B., Kettner, A. J., Chapman, B., Brakenridge, G. R., O'Brien, A., & Zuffada, C. (2023). Assessing the relative performance of GNSS-R flood extent observations: case study in South Sudan. *IEEE Transactions on Geoscience and Remote Sensing*. https://doi.org/10.1109/TGRS.2023.3237461 [Snippet]
- Easton-Calabria, E. (2025). Possibilities and limitations of anticipatory action in complex crises: acting in advance of flooding in South Sudan. *Disasters*. https://doi.org/10.1111/disa.12654 [Snippet]; and Easton-Calabria (2023), *Acting in Advance of Flooding: Early action in South Sudan*, Feinstein International Center. https://fic.tufts.edu/wp-content/uploads/05.10.23-ActingInAdvanceFinal.pdf (listed in the SLE file)
- EFMA / JRC (2023). *Global Flood Monitoring: product and service quality assessment* (JRC131351, EUR 31425 EN). https://doi.org/10.2760/362585 (pp. 33–34, Table 17) [External]
- Elmes, A., et al. (2020). Accounting for training data error in machine learning applied to Earth observations. *Remote Sensing* 12(6), 1034. https://doi.org/10.3390/rs12061034 [Snippet]
- EGU General Assembly 2024, abstract EGU24-18873. A comparative analysis of flood frequency mapping approaches for climate-resilience in South Sudan. https://ui.adsabs.harvard.edu/abs/2024EGUGA..2618873B/abstract [Snippet]
- ESSIC, University of Maryland (2024, 26 Nov). Scientists get ahead of South Sudan floods. https://essic.umd.edu/scientists-get-ahead-of-south-sudan-floods-we-need-to-save-peoples-livelihoods/ [External; news]
- FAO, WFP & Government of South Sudan (2023). *South Sudan 2022 Crop and Food Security Assessment Mission: summary of findings*. https://climis-southsudan.org/uploads/publications/CFSAM_2022_-_Summary_of_Findings.pdf (pp. 1–4, 7) [External]
- FEWS NET data warehouse extract of CFSAM county statistics, 2011–2024: `data/FEWS_crop_data/crop_data.csv` [File]
- GMV (2026). *EO-based hazard flooding maps – South Sudan, 2012–2024* [dataset]. Zenodo record 18196949. https://zenodo.org/records/18196949 [External]
- Google (2026). Earth Engine noncommercial tiers. https://developers.google.com/earth-engine/guides/noncommercial_tiers [External]
- Google Earth Engine Data Catalog. ESA WorldCereal 10 m v100. https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCereal_2021_MODELS_v100 [External]
- IFRC / South Sudan Red Cross (2025). *Simplified Early Action Protocol sEAP2024SS01 (MDRSS017), floods*, approved 23 Oct 2025. https://go-api.ifrc.org/api/downloadfile/93644/MDRSS017sEAP (pp. 1–2, 12–14) [External]
- INFLOW-AI repository (MIT licence). https://github.com/algorithmicgovernance/INFLOW-AI [External]
- IOM DTM South Sudan. Event Tracking datasets 2020–2026, Readme sheets. `data/IOM_DTM_event_tracking/` [File]
- Jasanoff, S. (2017). Virtual, visible, and actionable: data assemblages and the sightlines of justice. *Big Data & Society* 4(2). https://doi.org/10.1177/2053951717724477 [External]
- Iazzolino, G., & Dhungana, N. (2025). Prediction and data curation in digital humanitarianism. *Big Data & Society* 12(3). https://doi.org/10.1177/20539517251361111 [External]
- Haas, M. (2025, 14 Aug). How AI learns, and what it misses: why data selection matters in humanitarian action. ICRC *Humanitarian Law & Policy* blog. https://blogs.icrc.org/law-and-policy/2025/08/14/how-ai-learns-and-what-it-misses-why-data-selection-matters-in-humanitarian-action/ [External]
- Kerner, H., Nakalembe, C., Yang, A., Zvonkov, I., McWeeny, R., Tseng, G., & Becker-Reshef, I. (2024). How accurate are existing land cover maps for agriculture in Sub-Saharan Africa? *Scientific Data*. https://doi.org/10.1038/s41597-024-03306-z (Methods; Tables 1, 3, 4) [External]
- Katch, K. / OCHA Centre for Humanitarian Data (2024, Jan). Lessons from the 2022 South Sudan floods on acting ahead. https://centre.humdata.org/lessons-from-the-2022-south-sudan-floods-on-acting-ahead/ [External]
- NASA Earthdata (2025/2026). NASA enhances global flood products: smarter detection of flooding, release of 23-year archive. https://www.earthdata.nasa.gov/news/blog/nasa-enhances-global-flood-products-smarter-detection-flooding-release-23-year-archive [External]
- OCHA Centre for Humanitarian Data, Predictive Analytics Team (2022, 17 Feb). Data requirements for anticipatory action. https://centre.humdata.org/data-requirements-for-anticipatory-action/ [External]
- OCHA South Sudan. Flood-affected people, 2021, 2022 (Oct, Nov), 2024, 2025 files and Readme sheets. `data/OCHA_flood_data/` [File]
- Olofsson, P., Foody, G. M., Herold, M., Stehman, S. V., Woodcock, C. E., & Wulder, M. A. (2014). Good practices for estimating area and assessing accuracy of land change. *Remote Sensing of Environment* 148, 42–57. https://doi.org/10.1016/j.rse.2014.02.015 [External]
- Rustowicz, R., Cheong, R., Wang, L., Ermon, S., Burke, M., & Lobell, D. (2020). *Semantic Segmentation of Crop Type in South Sudan* [dataset]. https://doi.org/10.34911/rdnt.v6kx6n [Snippet]
- Tsyganskaya, V., Martinis, S., Marzahn, P., & Ludwig, R. (2018). SAR-based detection of flooded vegetation – a review of characteristics and approaches. *International Journal of Remote Sensing* 39(8). https://doi.org/10.1080/01431161.2017.1420938 [Snippet]
- WFP (2024, 2 May). *ADAM Flood Impact Analysis, South Sudan*. https://static.gis.wfp.org/adam_fl/event/20240502/ADAM_SSD_FloodReport_20240502.pdf [External]
- Wagner, W., et al. (2025). The fully-automatic Sentinel-1 Global Flood Monitoring service: scientific challenges and future directions. *Remote Sensing of Environment* 333, 115108. https://doi.org/10.1016/j.rse.2025.115108 [cited by Review 2; not opened]
- Team material: `eda/HANDOFF.md`, `eda/SESSION_E_HYPOTHESES.md`, `eda/STAGE31_GATE.md`–`STAGE34_GATE.md`, `eda/SESSION_A_CLOSEOUT.md`–`SESSION_D_CLOSEOUT.md`, `external_deep_research/*.md`, and the team brief "Sudd Flood Research Route" (claude.ai artifact, 23 Sep 2026).
- SLE sources listed in `SLE_aspects_capstone_extracted.md` §22 (Bowker and Star; Chavez-Gonzalez et al. 2022; Haggart and Tusikov 2023; Letz and Maxwell; Madianou 2025; Power; Sen) are pointers only; I did not read them.
