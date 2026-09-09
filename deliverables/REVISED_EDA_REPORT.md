# Revised Spatial EDA

This EDA supersedes earlier first-pass outputs that used whole-rectangle climate averages or a single ET grid cell.

## Analysis scope

- Flood mask local coverage: h20v08 + h21v08, approximately lon 20E-40E and lat 0N-10N.
- South Sudan extends north to about 12.24N, so the local flood mask misses northern South Sudan above 10N.
- Main flood panel grain: admin2-date, using flood pixels spatially joined to South Sudan admin2 polygons.
- ERA5 rainfall/runoff are gridded hourly fields and are aggregated by admin2 and by heuristic hydro-climate regions.
- ET is a gridded daily field and is aggregated by admin2 and by the same heuristic hydro-climate regions.
- Discharge main variable is station 100205; unrelated Omo, Blue Nile, and Atbara stations are excluded from main EDA.
- Lake levels are treated as upstream context: Victoria -> Kyoga -> Albert -> White Nile -> South Sudan. Victoria outflow is regulated, so it is not a purely natural upstream signal.

## Key tables

- admin2_daily_flood_climate_panel.csv
- hydro_region_daily_panel.csv
- flood_admin_coverage_summary.csv
- discharge_station_relevance.csv
- upstream_lake_water_levels_daily.csv
- national_daily_flood_climate_admin2_mean.csv

## Key checks

- Admin2 daily panel rows: 750,263
- Date range: 2000-01-01 to 2025-12-31
- Admin2 units: 79
- Hydro-climate regions: 6
- Highest annual admin2-clipped flood year: 2023

## Lowest admin1 flood-mask coverage

| admin_name | flood_tile_coverage_share |
| --- | --- |
| Upper Nile | 0.5955 |
| Unity | 0.9484 |
| Western Bahr el Ghazal | 0.953 |

## Discharge station treatment

| area_id | country | hydrological_relevance | use_in_main_eda |
| --- | --- | --- | --- |
| 100205 | South Sudan; Sudan | primary_white_nile_near_south_sudan | True |
| 1505 | Ethiopia | Omo to Lake Turkana, not White Nile path | False |
| 1541 | Sudan | downstream_white_nile_context | False |
| 1542 | Sudan | downstream_white_nile_context | False |
| 1543 | Sudan | downstream_white_nile_context | False |
| 1544 | Sudan | Blue Nile system, not South Sudan upstream | False |
| 1545 | Sudan | Blue Nile system, not South Sudan upstream | False |
| 1547 | Sudan | downstream_white_nile_context | False |
| 1548 | Sudan | downstream_main_nile_context | False |
| 11808 | Sudan | downstream_main_nile_context | False |
| 11842 | Sudan | downstream_main_nile_context | False |
| 28546 | Sudan | Atbara system, not South Sudan upstream | False |

## Upstream lake time coverage

| lake | date_min | date_max | records |
| --- | --- | --- | --- |
| Albert | 2002-07-10 | 2026-04-25 | 796 |
| Kyoga | 1992-09-27 | 2002-07-27 | 156 |
| Victoria | 1992-10-07 | 2002-08-06 | 329 |

## Climate region definitions

| region_id | label | notes |
| --- | --- | --- |
| ssd_full | South Sudan full boundary | Climate cells inside the full South Sudan admin0 polygon. |
| ssd_flood_tile_overlap | South Sudan area covered by local flood tiles | Climate cells inside South Sudan and inside h20v08+h21v08 flood tile latitude coverage. |
| victoria_kyoga_albert_upstream | Lake Victoria-Kyoga-Albert upstream corridor | Heuristic upstream lake corridor: Victoria -> Kyoga -> Albert -> White Nile. |
| bahr_el_jebel_south | Bahr el Jebel southern inflow corridor | Heuristic corridor from Albert Nile/Bahr el Jebel into southern South Sudan. |
| sobat_pibor_east | Sobat-Pibor eastern tributary corridor | Heuristic eastern tributary corridor including Sobat/Pibor/Akobo influence. |
| western_floodplain | Western South Sudan floodplain context | Heuristic western South Sudan rainfall/runoff context. |

## Strongest admin2-mean climate lag per feature

| feature | lag_days | correlation | n |
| --- | --- | --- | --- |
| precipitation_90d_sum_mm | 102 | 0.2443 | 9395 |
| runoff_60d_sum_mm | 95 | 0.1866 | 9402 |
| runoff_90d_sum_mm | 79 | 0.18 | 9418 |
| runoff_mm_day | 1 | -0.1994 | 9496 |
| runoff_30d_sum_mm | 0 | -0.2163 | 9497 |
| runoff_14d_sum_mm | 0 | -0.2398 | 9497 |
| runoff_7d_sum_mm | 0 | -0.2435 | 9497 |
| precipitation_60d_sum_mm | 0 | -0.2529 | 9497 |
| precipitation_mm_day | 1 | -0.2605 | 9496 |
| reference_et_mm_day | 132 | -0.268 | 9365 |
| et_30d_mean_mm_day | 125 | -0.2863 | 9372 |
| et_60d_mean_mm_day | 109 | -0.2904 | 9388 |
| et_90d_mean_mm_day | 93 | -0.2908 | 9404 |
| precipitation_30d_sum_mm | 0 | -0.3015 | 9497 |
| precipitation_7d_sum_mm | 0 | -0.3177 | 9497 |
| precipitation_14d_sum_mm | 0 | -0.3182 | 9497 |

## Strongest hydro-region climate lag correlations

| feature | lag_days | correlation | n | abs_correlation |
| --- | --- | --- | --- | --- |
| precipitation_mm_day__bahr_el_jebel_south__30d_sum | 0 | -0.3082 | 9497 | 0.3082 |
| precipitation_mm_day__ssd_flood_tile_overlap__30d_sum | 0 | -0.3075 | 9497 | 0.3075 |
| precipitation_mm_day__ssd_full__30d_sum | 0 | -0.3059 | 9497 | 0.3059 |
| precipitation_mm_day__ssd_flood_tile_overlap__30d_sum | 1 | -0.3035 | 9496 | 0.3035 |
| precipitation_mm_day__bahr_el_jebel_south__30d_sum | 1 | -0.3028 | 9496 | 0.3028 |
| precipitation_mm_day__ssd_full__30d_sum | 1 | -0.3019 | 9496 | 0.3019 |
| precipitation_mm_day__ssd_flood_tile_overlap__30d_sum | 2 | -0.299 | 9495 | 0.299 |
| reference_et_mm_day__sobat_pibor_east__30d_mean | 128 | -0.2975 | 9369 | 0.2975 |
| precipitation_mm_day__ssd_full__30d_sum | 2 | -0.2975 | 9495 | 0.2975 |
| reference_et_mm_day__sobat_pibor_east__30d_mean | 127 | -0.2975 | 9370 | 0.2975 |
| reference_et_mm_day__sobat_pibor_east__30d_mean | 126 | -0.2975 | 9371 | 0.2975 |
| reference_et_mm_day__sobat_pibor_east__30d_mean | 129 | -0.2973 | 9368 | 0.2973 |
| reference_et_mm_day__sobat_pibor_east__30d_mean | 125 | -0.2973 | 9372 | 0.2973 |
| precipitation_mm_day__western_floodplain__30d_sum | 0 | -0.2972 | 9497 | 0.2972 |
| reference_et_mm_day__sobat_pibor_east__30d_mean | 124 | -0.2972 | 9373 | 0.2972 |
| reference_et_mm_day__sobat_pibor_east__30d_mean | 130 | -0.2971 | 9367 | 0.2971 |
| reference_et_mm_day__sobat_pibor_east__30d_mean | 123 | -0.297 | 9374 | 0.297 |
| precipitation_mm_day__bahr_el_jebel_south__30d_sum | 2 | -0.297 | 9495 | 0.297 |
| reference_et_mm_day__sobat_pibor_east__30d_mean | 122 | -0.2969 | 9375 | 0.2969 |
| reference_et_mm_day__sobat_pibor_east__30d_mean | 131 | -0.2968 | 9366 | 0.2968 |

## Interpretation cautions

- Correlations are exploratory and not causal evidence.
- Flood mask data are event records, not full daily no-flood/flood maps; zeros in the panel mean no flood event record in that admin2-date after spatial joining.
- Flooded area is approximated as pixel_count x 0.0625 km2, using the rough 250m grid size from the data description.
- Hydro-climate regions are pragmatic boxes, not formal watershed polygons.
- Upstream rainfall/runoff outside South Sudan may matter, so the regional climate features are intentionally retained alongside South Sudan-only aggregates.
