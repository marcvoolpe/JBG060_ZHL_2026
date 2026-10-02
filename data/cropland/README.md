# Public cropland maps for the Aweil / Bor South cropland audit

This folder holds the public satellite maps of cropland (and a few context layers) that the team
compares against its own hand-labelled points. Everything here was downloaded and documented by
the scripts in `processing_data/cropland/`. Nothing in this folder is an accuracy result: the maps'
accuracy in ZOA's areas is what the team's blind sample will measure later.

**Keep the labelling blind.** Do not open these maps, or the derived layers, while labelling points.

## Areas and grids

| AOI | Counties (pcode) | Area | Processing grid |
|---|---|---|---|
| `aweil` | Aweil Centre SS0501, Aweil East SS0502, Aweil North SS0503, Aweil South SS0504, Aweil West SS0505 | 30,852 km2 (32,352 km2 with the 2 km buffer) | UTM 35N (EPSG:32635) |
| `borsouth` | Bor South SS0303 | 13,963 km2 (15,007 km2 buffered) | UTM 36N (EPSG:32636) |

Each AOI is the union of its counties from `ssd_admin2.geojson`, buffered by 2 km. Delivered
rasters keep the producer's own grid and values. Pixels outside the buffered AOI are set to
no-data. The derived layers use a 10 m and a 30 m grid in the AOI's UTM zone, with the origin on a
60 m lattice. That lattice is the Sentinel-2 pixel lattice, so each 30 m cell is exactly
3 x 3 Sentinel-2 10 m pixels.

## Files

- `MANIFEST.csv`: one row per file, giving the product, version, year, AOI, path, source (URL or
  Earth Engine asset), access date, licence, resolution, CRS, band, class codes, size, SHA-256,
  export parameters and status.
- `<product>/`: the delivered data (git-ignored).
- `derived/<aoi>/`: 0/1 crop layers, 30 m layers, the "number of maps saying crop" layer, and the
  distance to buildings (git-ignored).
- `county_cropland_areas.csv`: cropland area per county per product.
- `CHECKS.md`: output of the sanity checks.
- `docs/`: producer documents used for the facts below.
- `logs/`: run logs (git-ignored).

**How Earth Engine layers were fetched.** The user chose direct tiled downloads (the `geedim`
package) instead of batch exports to Google Drive. Earth Engine batch tasks therefore do not
exist, and the manifest's `ee_task_id` says "n/a". The exact request (CRS, pixel transform, shape,
data type, no-data value, software versions) is in `export_params` instead. Earth Engine project:
`southsudan-509222`. Software: earthengine-api 1.7.45, geedim 2.0.0, geemap 0.38.8, Python 3.13.

## The products

In the code lists, "no data" means the pixel has no valid value. We use **255** for
"outside the AOI" in every uint8 file we exported.

### 1. ESA WorldCereal 2021 v100, temporary crops (priority A)
A global 10 m map of temporary crops for 2021, made by the ESA WorldCereal consortium from
Sentinel-1 and Sentinel-2 time series. Separate models run per agro-ecological zone (AEZ).
"Temporary crops" means crops with a less-than-one-year growing cycle that must be sown or planted
again after harvest. Sugar cane, asparagus and cassava are included. Perennial crops and pasture
are excluded (Van Tricht et al. 2023, ESSD 15:5491, Section 2.1). Codes: `classification`
100 = temporary crops, 0 = other; `confidence` 0–100 = model confidence (%).

- **Accuracy in Africa:** user's accuracy 80.1% (±2.0) and producer's accuracy 87.3% (±1.7)
  (Van Tricht et al. 2023, Table 5, Section 5.1). The authors note that Africa has the lowest
  accuracy "due to agricultural landscape complexity in combination with large training data gaps".
- **Source:** Earth Engine `ESA/WorldCereal/2021/MODELS/v100`, filter `product == "temporarycrops"`
  (season `tc-annual`).
- **Files:** Aweil touches three AEZ images (32114, 36124, 7091) and Bor South two (32114, 36124).
  Each AEZ image has its own EPSG:4326 grid (1/12000°, about 9.3 m) with a different sub-pixel
  origin, so each is saved separately on its own grid.
- **Licence:** CC-BY-4.0.
- **Limitation:** the map year (2021) is one season before the 2022 reference season.

### 2. ESA WorldCover 2021 v200 (and 2020 v100) (priority A)
A global 10 m land-cover map with 11 classes, from the ESA WorldCover consortium. Codes (band
`Map`): 10 tree cover, 20 shrubland, 30 grassland, **40 cropland**, 50 built-up,
60 bare/sparse vegetation, 70 snow and ice, 80 permanent water bodies, 90 herbaceous wetland,
95 mangroves, 100 moss and lichen. The product's own no-data value is 0.

- **Accuracy in Africa (v200):** overall accuracy 76.5% ±1.3 (Product Validation Report V2.0,
  Table 3, p. 16). For the cropland class, user's accuracy is 71.3% and producer's accuracy is 58.9%
  (Table A2.1, p. 27). The report says cropland in Africa "tended to be under-represented" (p. 16).
  The report is in `docs/WorldCover_PVR_V2.0.pdf`.
- **Source:** Earth Engine `ESA/WorldCover/v200` and `ESA/WorldCover/v100`, on their native global
  1/12000° grid.
- **Licence:** CC-BY-4.0.
- **Limitation:** cropland in these maps is land-cover based, so fallow and very small fields are
  easily mapped as grassland or shrubland.

### 3. Esri / Impact Observatory 10 m annual land cover, 2021–2024 (priority A)
An annual global 10 m land-cover map from Impact Observatory and Esri (Sentinel-2, deep
learning; Karra et al. 2021). **We checked the class coding on the pixels themselves.** The asset
uses Esri's original codes: 1 water, 2 trees, 4 flooded vegetation, **5 crops**, 7 built area,
8 bare ground, 9 snow/ice, 10 clouds, 11 rangeland. Codes 3 and 6 never occur. The 1–9 remap
(crops = 4) exists only in the community catalogue's example script. **In this asset, 4 means
flooded vegetation, not crops.**

- **Accuracy:** the community catalogue states an average accuracy "over 75% per map". A
  class-specific accuracy for Africa was not verified.
- **Source:** Earth Engine community catalogue asset
  `projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS`. The catalogue calls it the
  version-3 model (grass and scrub merged into "rangeland"). It has one image per UTM zone and
  year: Aweil uses 35N + 35P, Bor South uses 36N. They share one 10 m lattice, so the mosaic is on
  the native grid.
- **Licence:** CC-BY-4.0, attribution to Esri / Impact Observatory.
- **Note:** 2017–2020 and 2025 also exist in the asset but were not downloaded.

### 4. Google Dynamic World V1, 2022 composites (priority A)
Near-real-time 10 m land-cover probabilities for every Sentinel-2 image, from Google with the
National Geographic Society and WRI (Brown et al. 2022, Sci Data 9:251). Dynamic World has no
annual map, so we made two composites per AOI: Jun–Nov 2022 (the main season) and all of 2022.
Bands:
- `label_mode`: the most frequent per-image top class. Codes: 0 water, 1 trees, 2 grass,
  3 flooded vegetation, **4 crops**, 5 shrub and scrub, 6 built, 7 bare, 8 snow and ice.
- `crops_mean_pct`: the mean "crops" probability × 100.
- `n_obs`: the number of cloud-free observations.

Aweil used 229 images for Jun–Nov and 539 for the year. Bor South used 91 and 180.

- **Accuracy:** not verified. The paper's page could not be read. The catalogue warns that
  probabilities for classes defined by change over time, such as crops, "can be comparatively low".
- **Source:** Earth Engine `GOOGLE/DYNAMICWORLD/V1`.
- **Licence:** CC-BY-4.0. Required attribution: "This dataset is produced for the Dynamic World
  Project by Google in partnership with National Geographic Society and the World Resources
  Institute."
- **Limitation:** the composite rule (mode, mean) is our choice, not the producer's.

### 5. JRC ASAP crop and rangeland masks v04 (priority A, documented only)
Global area-fraction images at 1/224° (about 500 m). Each pixel gives the percentage (0–100) of
its area under temporary crops (crop mask) or rangeland (rangeland mask). They were made by IIASA
and JRC for the ASAP early-warning system by combining several existing maps (Fritz et al. 2024,
doi:10.2760/32935). Version 04, last updated 01-12-2023.

- **Files:** already in the course pack (`farmland/asap_mask_crop_v04.tif`,
  `asap_mask_rangeland_v04.tif`), so they were not downloaded again. The files carry no no-data
  tag, and over South Sudan they hold only 0–100.
- **Licence:** EC reuse policy (reuse authorised if the source is acknowledged).
- **Accuracy:** no accuracy figure was found on the download page.

### 6. Digital Earth Africa cropland extent 2019 (priority B)
A 10 m map of cropland for 2019 from Digital Earth Africa, made with regional machine-learning
models. **South Sudan is covered by the Sahel model.** Bands: `mask` (pixel-based, 1 = crop,
0 = not crop), `prob` (crop probability 0–100%) and `filtered` (object-based, 1 = crop).

- **Accuracy (Sahel model):** overall accuracy 87.9%, producer's accuracy for crop 70.5%, user's
  accuracy for crop 87.3%, F-score 0.78 (DE Africa Cropland Extent specification page).
- **Files:** the delivered 96 km × 96 km tiles (EPSG:6933, 10 m), unmodified: 12 tiles for Aweil
  and 6 for Bor South, 3 bands each. Every file matches the producer's `.sha1` checksum. The
  current continental product `crop_mask` (dataset version 1.1.5) was used. The older
  `crop_mask_sahel` 1.0.0 also exists but was not used.
- **Documentation discrepancy:** the documentation lists no-data = 0, but the delivered files
  declare **255** as no-data and use 0 for "not crop". We follow the files.
- **Source:** STAC API `https://explorer.digitalearth.africa/stac/search` (collection `crop_mask`),
  bucket `deafrica-services`.
- **Licence:** CC-BY-4.0.

### 7. GLAD global cropland extent, 2016–2019 and 2012–2015 (priority B)
Global 30 m (0.00025°) cropland maps for 4-year intervals, from UMD GLAD (Potapov et al. 2022,
Nature Food 3:19–28). A pixel is cropland if a crop was detected in any year of the interval, so
fallow is allowed for up to 4 years. The definition covers annual and perennial herbaceous crops.
**Shifting cultivation, permanent pasture and woody crops are excluded** (p. 2). Codes: 1 = cropland,
0 = no cropland or no data.

- **Accuracy in Africa:** for 2016–2019, overall accuracy 96.5% (±0.8), user's accuracy 77.3%
  (±3.2), producer's accuracy 70.6% (±7.9) (Table 3, p. 23). The paper says the map underestimates
  cropland in Africa's heterogeneous landscapes (p. 25). The paper is in `docs/`.
- **Source:** the authors' own Earth Engine copy, `users/potapovpeter/Global_cropland_2019` (and
  `_2015`), named on glad.umd.edu/dataset/croplands. It is the same data as the NE quadrant file
  `Global_cropland_NE_2019.tif`.
- **Licence:** not stated for the data. The article is CC-BY-4.0. Cite the paper.

### 8. NASA GFSAD30 Africa cropland extent, nominal 2015 (priority B)
A 30 m cropland map of Africa for about 2015 (2013–2016 data), from the USGS/NASA GFSAD project
(Xiong et al. 2017). Codes, from the User Guide V1, p. 6, Section 2.1.4: **0 = water bodies /
no data, 1 = non-cropland, 2 = cropland**. Cropland includes fallow (p. 9).

- **Accuracy for the whole continent:** weighted overall accuracy 94.5%, producer's accuracy 85.9%,
  user's accuracy 68.5%, F-score 0.76 (User Guide p. 6). The guide is in `docs/`.
- **Source:** the community-catalogue copy of the LP DAAC granules,
  `projects/sat-io/open-datasets/GFSAD/GCEP30`. We used granules `GFSAD30AFCE_2015_N00E20_...`
  (Aweil) and `..._N00E30_...` (Bor South), each on its own grid. This avoided the NASA Earthdata
  login, as the user chose. DOI 10.5067/MEaSUREs/GFSAD/GFSAD30AFCE.001.
- **Licence:** open, without restriction (NASA EOSDIS policy).
- **Caution:** the NASA Earthdata catalogue page lists the codes in a different order. The user
  guide, the community catalogue and the pixel values all agree on 2 = cropland. The claim that
  WFP ADAM uses GFSAD30 was **not verified**.

### 9. Google Open Buildings v3 (priority C)
Building footprints detected from 50 cm imagery by Google Research (Sirko et al. 2021). Inference
date May 2023. South Sudan is covered. We kept footprints with confidence ≥ 0.70 (the release
covers 0.65–1.0) whose centroid lies in the buffered AOI. The derived layer
`dist_to_building_30m_<aoi>.tif` gives the distance (m) from each 30 m cell to the nearest
footprint, capped at 1,500 m. Counts per county are in
`open_buildings/open_buildings_v3_county_counts_<aoi>.csv`.

- **Source:** Earth Engine `GOOGLE/Research/open-buildings/v3/polygons`.
- **Licence:** CC-BY-4.0 (Earth Engine catalogue).

### 10. MERIT Hydro (priority C)
Global hydrography on a 3 arc-second grid (about 93 m) (Yamazaki et al. 2019). Bands:
`hnd` = height above the nearest drainage (m); `upa` = upstream drainage area (km²).
No-data = −9999.

- **Source:** Earth Engine `MERIT/Hydro/v1_0_1`.
- **Licence:** CC-BY-NC-4.0 or ODbL-1.0. Non-commercial use is fine under CC-BY-NC.

### 11. HydroSHEDS free-flowing rivers (priority C)
River lines for all of South Sudan (29,838 reaches) from WWF / McGill (Grill et al. 2019). Fields:
- `UPLAND_SKM`: upstream area (km²).
- `RIV_ORD`: river order by long-term mean discharge, 1 = largest.
- `DIS_AV_CMS`: mean discharge 1971–2000 (m³/s).
- `CSI`: connectivity status (0–100%).

- **Source:** Earth Engine `WWF/HydroSHEDS/v1/FreeFlowingRivers`.
- **Licence:** HydroSHEDS licence (free for non-commercial and commercial use, with attribution).

## Derived layers (`processing_data/cropland/derived_cropland_layers.py`)

For each crop map and AOI:
1. `<key>_crop10m_<aoi>.tif`: 1 = crop, 0 = not crop, 255 = no data, on the 10 m UTM grid.
   Maps not already on that grid are brought onto it by nearest neighbour. This copies or drops
   whole source pixels and never blends classes.
2. `<key>_crop30m_<aoi>.tif`: a 30 m cell is crop if at least 5 of its 9 pixels are crop.
   `<key>_cropfrac30m_<aoi>.tif` gives the share of crop pixels (%). Cells with fewer than 5 valid
   pixels are no-data.
3. `n_maps_crop_30m_<aoi>.tif`: how many of the four priority-A maps call the cell crop (0–4):
   WorldCereal 2021, WorldCover 2021, Esri 2022, and Dynamic World Jun–Nov 2022.
4. `county_cropland_areas.csv`: cropland hectares per county per product. Areas are measured on
   each product's **native** pixels (true pixel area for degree grids). A pixel counts for a county
   when its centre is inside it. The table also shows ASAP area (% cover × pixel area) and the CFSAM
   2022 harvested cereal area. **CFSAM is a modelled estimate from a field mission. It is context
   only, not a reference.**

## Map-to-map agreement, for stratifying the sample (`processing_data/cropland/cropland_agreement.py`)

`agreement/` compares the maps **with each other** on the 30 m grid, per county. This is not
accuracy: maps can agree and all be wrong. The folder holds:
- `county_crop_share.csv`: each map's crop share (%) and crop area (ha) per county.
- `pairwise_agreement.csv`: for every pair of maps, the overall agreement, Cohen's kappa, crop
  overlap (Jaccard), and the share of each map's crop that the other also calls crop.
- `strata_n_maps.csv`: cells and hectares per "number of maps saying crop".
- `n_maps7_crop_30m_<aoi>.tif`: the 0–7 count over WorldCereal 2021, WorldCover 2021, Esri 2022,
  Dynamic World Jun–Nov 2022, DE Africa 2019, GLAD 2016–19 and GFSAD 2015.

What the numbers show (27 Sep 2026 run):
- **Crop is rare in every map, and the maps mostly disagree on where it is.** Crop shares per
  county run from 0.01% to 5.3%. The crop overlap between two maps (Jaccard) is at most 25% and
  usually below 10%. Kappa is at most 0.39. "Overall agreement" (97–99.6%) is high only because
  almost every cell is non-crop in every map; do not use it for crop.
- **The "all maps agree" stratum is nearly empty.** In all of Aweil, all four priority-A maps call
  just 1 ha crop. With the 7-map count, 3 or more maps agree on 9,485 ha.
- **Bor South:** Dynamic World calls about 23% of the county "crops". Where it does, WorldCover says
  grassland (95%) and Esri says rangeland (84%). Dynamic World most likely confuses seasonally
  flooded grassland with crops there. Every other map puts Bor South's crop share at 0.25% or less.
  Leave Dynamic World out of Bor South's strata, or keep it as a separate stratum.
- CFSAM 2022 harvested cereal area is larger than every map's crop area in every Aweil county (for
  example, about 8.8% of Aweil East, against 0.2–4.5% in the maps). CFSAM is a modelled estimate and
  context only, but it suggests much real cropland lies in the "0 maps" stratum. The sample needs
  enough points there to measure what the maps miss.

## Viewing the rasters: overviews are not class-safe

The Earth Engine exports are Cloud-Optimised GeoTIFFs with built-in overviews (the low-resolution
copies that QGIS shows when you zoom out). For the class rasters, these overviews were built by
averaging class codes, which is meaningless (for example, 1 and 5 average to "4"). **Judge class
maps only at full resolution.** Every script here reads full-resolution pixels; the overviews
affect only zoomed-out display, and the delivered pixel values themselves are unaffected.

## Not obtained, or deviations from the brief

- **Earth Engine task IDs:** none exist, because the user chose direct downloads over Drive exports
  (see above).
- **National (all South Sudan) aggregates** of the crop layers: not produced yet. They are optional
  in the brief and would cost Earth Engine compute; the user needs to decide.
- **GFSAD30 via LP DAAC:** not needed. The Earth Engine copy of the same granules was used.
- **WorldCereal from Zenodo / the producer:** not downloaded. The Earth Engine copy was used.
- **Accuracy not verified:** Dynamic World and Esri (Africa-specific), and ASAP.
- **Licence not stated by the producer:** GLAD data.

## Re-running

From the repo root with the global Python 3.13. Earth Engine needs `ee.Authenticate()` once.

```
python -m processing_data.cropland.download_ee_products        # 1-4, 7, 8, 10
python -m processing_data.cropland.download_ee_vectors         # 9, 11
python -m processing_data.cropland.download_deafrica_cropmask  # 6
python -m processing_data.cropland.document_asap               # 5
python -m processing_data.cropland.derived_cropland_layers
python -m processing_data.cropland.check_cropland_rasters
python -m processing_data.cropland.common --refresh            # re-apply licence table to the manifest
```

The scripts skip files that already exist, so an interrupted run can simply be started again.
