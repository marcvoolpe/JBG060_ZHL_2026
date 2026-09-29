# Labelling guide: pilot (Twic county)

**Goal:** find out if we can tell crop from grass by eye at a 10 m point in this region. Each of us labels the same 30 points on our own; `01_compare_pilot.py` then says how often we agree.

**Time:** about 45 minutes for 30 points.

## Before you start

1. Copy `pilot_labels_TEMPLATE.csv` to `pilot_labels_<yourname>.csv`.
2. **Do not open any cropland map** (WorldCover, GLAD, ASAP...) while labelling, and do not look at anyone else's sheet.
3. Open the points in **Google Earth Pro** (free desktop app): *File → Open → `pilot_points.kml`*. Turn on the clock icon (historical imagery) to see older, sharper images.
4. For the time series, use the `eo_browser` link in `pilot_points.csv`. It opens Sentinel-2 at the point for May–Nov 2022. No account is needed to view.

## For each point

Look at the **10 m square around the point** (about one Sentinel-2 pixel). What covers most of it in the **2022** season?

| field | fill in |
|---|---|
| `label` | `crop`, `not crop` or `unsure` |
| `confidence` | 1 = guess, 2 = fairly sure, 3 = sure |
| `bare_soil_apr_jun` | y / n: bare or tilled soil before the rains (Apr–May) |
| `green_up_month` | month it turns green (e.g. `jul`) |
| `early_harvest_drop` | y / n: goes brown in Sep–Oct while the grass around stays green |
| `regular_plots` | y / n: straight edges, small rectangles, a patchwork |
| `homesteads_300m` | y / n: huts or compounds within ~300 m |
| `burn_scar` | y / n: dark burned patch (usually Nov–Feb) |
| `standing_water` | y / n |
| `imagery_used` | e.g. `GE 2021-11`, `S2 2022-10-03` |
| `imagery_date` | date of the image you relied on most |
| `minutes` | time spent on this point |
| `notes` | anything odd |

## What counts as crop

- **Crop:** land sown and grown in 2022 (sorghum, groundnut, sesame, maize, rice), including small plots next to homesteads.
- **Not crop:** grassland, bush, trees, water, settlement, and **fallow** (not sown this year).
- Crop season in Northern Bahr el Ghazal (FEWS NET): sowing done by late May; groundnuts and sesame harvested from August; short-cycle sorghum in **September–October**.

## Traps

- **Burned grass** looks like bare, tilled soil. Burns are dark and irregular, and happen in the dry season; tilled fields are lighter and have edges.
- **Wild grass** greens up at the same time as crops. The difference is the early brown-down at harvest and the regular shapes.
- **One sharp Google Earth image may be from another year.** Always check its date; fields move.

When unsure, say `unsure`. That is useful information, not a failure.
