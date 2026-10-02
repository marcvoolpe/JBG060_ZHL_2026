# Prompt: download and document all public cropland data for the Aweil / Bor South cropland audit

## Your role

You are a careful geospatial data engineer working in this repository (JBG060 capstone, South Sudan, ZOA / Zero Hunger Lab). Your job is to **obtain, document and sanity-check** every public cropland dataset the team needs for its research objective. You do not analyse results and you do not assess map accuracy; that comes later from the team's hand-labelled sample.

Ground rules:
1. **Never invent** a dataset, version, asset ID, class code, URL, licence or resolution. Open the producer's page or catalogue entry and record what it says. If something cannot be obtained or confirmed, write "not obtained" / "not verified" in the manifest and move on. Do not substitute a different product silently.
2. **Keep the native data.** Do not reproject, resample or reclassify the delivered files. Derived products (binary crop layers, 30 m aggregates) go in a separate `derived/` folder and are made by a script.
3. **Stop and report** if a download needs payment, a licence you cannot accept on the user's behalf, or credentials you do not have. Ask the user instead of working around it.
4. Write every step as a re-runnable Python script in the repo; no manual-only steps except account sign-ups.
5. Plain language in all notes; define class codes explicitly.

## Context

- Research objective: evaluate how accurately public satellite data measure cropland and cropland flooding in ZOA's areas, and which conditions go with flooding of farmland. Reference season 2022; flood record 2017–2025.
- **Areas of interest (AOI):**
  - Primary: the five counties of Northern Bahr el Ghazal (Aweil Centre SS0501, Aweil East SS0502, Aweil North SS0503, Aweil South SS0504, Aweil West SS0505), about 30,852 km².
  - Secondary: Bor South, Jonglei (SS0303), about 13,963 km².
  - National (all of South Sudan) only where the file is small or already national (≤ ~1 GB per product), or as an aggregated 30 m / 100 m version.
- AOI polygons: `data-JBG060-2026/data-JBG060-2026/Administrative boundaries/ssd_admin2.geojson` (column `adm2_pcode`). Buffer each AOI by 2 km before clipping so edge points have context.
- Paths: use `processing_data/paths.py` (`EXT_DATA = data/`). Write to `data/cropland/<product>/`. Large rasters must not be committed: add `data/cropland/**/*.tif` to `.gitignore` and commit only scripts, the manifest and small CSVs.
- Python: the repo `.venv` lacks rasterio; the global Python 3.13 (`C:\Users\marcv\AppData\Local\Programs\Python\Python313\python.exe`) has rasterio, geopandas, numpy, pandas. Add `earthengine-api` and `geemap` if Earth Engine is used, and record versions.
- Google Earth Engine: the team uses a noncommercial Cloud project (Community tier: 150 EECU-hours per month, then reduced speed). Ask the user for the project ID; run `ee.Authenticate()` interactively only with the user present.

## Datasets to obtain

Priority A are required. Priority B are useful comparisons. Priority C are the non-cropland layers the sampling design needs; get them if time allows.

| # | Product | Year(s) | Known access route (verify) | Class / band to record | Priority |
|---|---|---|---|---|---|
| 1 | ESA WorldCereal temporary crops v100 | 2021 | Earth Engine `ESA/WorldCereal/2021/MODELS/v100`, filter `product == "temporarycrops"`, band `classification` (100 = crop, 0 = other), plus `confidence`; also the producer's download (Zenodo / ESA WorldCereal site) | classification, confidence | A |
| 2 | ESA WorldCover v200 | 2021 (and v100 2020 if easy) | Earth Engine `ESA/WorldCover/v200`, band `Map`, 40 = cropland; or the 3° × 3° tiles on the ESA WorldCover AWS bucket | Map | A |
| 3 | Esri / Impact Observatory 10 m annual land cover | 2021, 2022, 2023, 2024 | Earth Engine community catalogue `projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS` (crops = 4 after the catalogue's remap; 5 in Esri's original coding: **confirm which coding the asset uses**); or Esri Living Atlas / Planetary Computer `io-lulc-annual-v02` | class raster | A |
| 4 | Google Dynamic World V1 | Jun–Nov 2022 (and full year 2022) | Earth Engine `GOOGLE/DYNAMICWORLD/V1`; export two composites per AOI: mode of `label` (4 = crops) and mean of the `crops` probability band | label mode, crops mean | A |
| 5 | ASAP crop and rangeland masks v04 | static | Already in the course pack: `farmland/asap_mask_crop_v04.tif`, `asap_mask_rangeland_v04.tif`. Do not download again; record provenance from the JRC ASAP documentation | % cover 0–100 | A (document only) |
| 6 | Digital Earth Africa cropland extent | 2019 | Digital Earth Africa (S3 COGs / DE Africa Maps / product docs). Record which validation zone covers South Sudan and the accuracy the docs give | crop mask, probability | B |
| 7 | GLAD global cropland extent (Potapov et al. 2022) | 2019 (and 2015 if easy) | GLAD / UMD download page; check whether an Earth Engine copy exists | crop / non-crop | B |
| 8 | NASA GFSAD30 cropland (used by WFP ADAM) | ~2015 | LP DAAC (Earthdata login required: ask the user) | crop / non-crop | B |
| 9 | Google Open Buildings v3 | 2023 | Earth Engine `GOOGLE/Research/open-buildings/v3/polygons` (confidence 0.65–1.0). Export polygons with confidence ≥ 0.70 per AOI, plus a distance-to-building raster capped at 1.5 km. **Check that South Sudan is actually covered** and report building counts per county | confidence | C |
| 10 | MERIT Hydro | static | Earth Engine `MERIT/Hydro/v1_0_1`, bands `hnd` (height above nearest drainage, m) and `upa` (upstream area, km²); ~93 m | hnd, upa | C |
| 11 | HydroSHEDS free-flowing rivers | static | Earth Engine `WWF/HydroSHEDS/v1/FreeFlowingRivers` (lines; `UPLAND_SKM`, `RIV_ORD`) | river lines | C |

Out of scope unless the user asks: CFSAM/FEWS county statistics (already in `data/FEWS_crop_data/`), crop-type maps, Planet imagery (the NICFI programme ended on 1 April 2025).

## How to export

- **Earth Engine products (1–4, 9–11):** export per AOI at native resolution (10 m for 1–4) in the product's native CRS, `uint8` where possible, as Cloud-Optimised GeoTIFF to Google Drive or a Cloud bucket, then download to `data/cropland/<product>/`. Use `tileScale` or split AOIs if tasks fail. Expected size is roughly 0.3 GB per 10 m product for the Aweil AOI; confirm before starting and warn the user if the total exceeds 10 GB.
- **National versions:** only as 30 m (or 100 m) aggregates of the binary crop layer, computed as the mean of the 0/1 layer (a crop fraction), not by nearest-neighbour resampling.
- **Direct downloads (6–8, WorldCover tiles if used):** script the tile list from the AOI bounds, download with retries, and verify file sizes or checksums the producer publishes.
- Record the Earth Engine task IDs and the exact export parameters in the manifest.

## Derived layers (script `derived_cropland_layers.py`)

Only after all downloads are logged:
1. One 0/1 crop layer per product (1–4, 6–8), using the class codes recorded in the manifest.
2. Aggregation to the 30 m assessment grid aligned to the Sentinel-2 10 m grid: crop if at least 5 of 9 pixels are crop; also keep the 0–1 crop fraction.
3. A "number of maps saying crop" layer from products 1–4 (0–4).
4. A per-county table: cropland area (ha) per product, next to CFSAM 2022 harvested area from `data/FEWS_crop_data/crop_data.csv` and ASAP area. Label CFSAM as a modelled estimate (context only, not a reference).

## Checks before you finish

- Open each raster: CRS, resolution, extent covers the buffered AOI, no-data value, class values present (print a value count).
- Class-code check by overlay: at 5 locations (Aweil town outskirts, a Lol floodplain stretch, a toich wetland, a woodland patch, a village cluster), print each product's value and confirm it matches the documented meaning. Report any product whose codes don't behave as documented.
- Compare per-county areas across products; flag any product that differs from the others by more than 10× and say whether that is plausible or an error.
- Confirm no large raster is staged in git.

## Deliverables

1. `data/cropland/MANIFEST.csv` with one row per file: product, version, year, AOI, file path, source URL or asset ID, access date, licence, native resolution, CRS, band, class codes, file size, checksum, Earth Engine task ID, status (obtained / not obtained / not verified), notes.
2. `data/cropland/README.md`: one paragraph per product in plain language (what it is, who made it, how cropland is defined, known accuracy in Africa with source and page, limitations), and a list of anything not obtained and why.
3. Scripts: `processing_data/cropland/download_*.py`, `processing_data/cropland/derived_cropland_layers.py`, runnable from the repo root.
4. `data/cropland/county_cropland_areas.csv` from the derived step.
5. A short final report to the user: what was obtained, what failed, total disk use, the class-code check results, and any decision the user must make (for example Earthdata login for GFSAD30).

Do not compute any accuracy statistic, do not touch the hand-labelled sample, and do not show map values to anyone labelling points: the labelling must stay blind to these maps.
