# Stage 32 gate — Event Tracking outcome audit (SE-H1)

**Status: PASS.**

Outcome-side only: no severity data were read in this stage.

## Kill criteria

| criterion | value | pass |
|---|---|---|
| Usable seasons >= 3 | 4.0 | pass |
| F71 counties with varying outcome across usable seasons >= 35 | 47.0 | pass |
| Detection rate (OCHA >= 10k; MT if OCHA n < 10) >= 0.4 | 0.617 | pass |

## Seasons (June–December, F71 frame)

| season | flood_rows | flood_people | share_people_pcoded | f71_nonzero | f71_people | usable | n_lag | median_lag | p90_lag |
|---|---|---|---|---|---|---|---|---|---|
| 2021 | 395 | 407,915.00 | 1.00 | 28 | 389,858.00 | True | 395.00 | 13.00 | 40.60 |
| 2022 | 451 | 388,916.00 | 1.00 | 23 | 325,274.00 | True | 451.00 | 19.00 | 39.00 |
| 2023 | 47 | 24,343.00 | 1.00 | 4 | 20,087.00 | False | 47.00 | 1.00 | 14.00 |
| 2024 | 386 | 359,167.00 | 1.00 | 32 | 301,242.00 | True | 386.00 | 12.00 | 39.00 |
| 2025 | 162 | 236,648.00 | 1.00 | 20 | 236,648.00 | True | 162.00 | 11.00 | 74.50 |

- Usable seasons: **[2021, 2022, 2024, 2025]**. Primary panel seasons after the 2023 rule: **[2021, 2022, 2024, 2025]**.
- 2023 rule (Mobility Tracking detection): 2023 rate 0.150 vs threshold 0.275 (half the median of 2021/2022/2024 = 0.550) → **drop 2023**.
- F71 counties whose outcome varies: 47 across usable seasons, 47 across panel seasons.
- Non-zero seasons per F71 county (panel seasons): {0: 24, 1: 15, 2: 12, 3: 16, 4: 4}.
- Share of flood people whose origin = event county, by season: {2021.0: 0.973, 2022.0: 0.919, 2023.0: 1.0, 2024.0: 0.969, 2025.0: 0.981}.
- MON-1 counties in F71: 49. MON-2 observed share of F71 county-seasons: 0.935.

## Detection

- **OCHA** (county-seasons with ≥ 10,000 affected; OCHA files 2021, 2022, 2024, 2025): **0.617** of 115 have any ET flood record from that origin county (Wilson 95% CI [0.526, 0.701]); F71 only 0.638 of 105. By season: {2021: {'size': 23, 'mean': 0.522}, 2022: {'size': 30, 'mean': 0.6}, 2024: {'size': 34, 'mean': 0.765}, 2025: {'size': 28, 'mean': 0.536}}.
- **Mobility Tracking** (first-round disaster arrivals ≥ 1,000; R13–R16 for 2021–2024): **0.522** of 136 (origin rule); event-location rule 0.515. By season: {2021: {'size': 40, 'mean': 0.55}, 2022: {'size': 35, 'mean': 0.429}, 2023: {'size': 20, 'mean': 0.15}, 2024: {'size': 41, 'mean': 0.756}}.
- Caveats: OCHA 'affected' is not 'displaced'; Mobility Tracking arrivals are all disaster types, by calendar arrival year and host county. Both rates are therefore lower bounds on ET's recording of flood displacement large enough to count.

## Outcome reliability (informative only, not kill criteria)

- Floor: within-county ET–OCHA correlation r_w = **0.111** (county bootstrap 95% CI -0.180 to 0.395; n = 133, 48 counties; F71 only 0.139). R_ET ≥ r_w² = **0.012** if errors are independent. OCHA snapshots stacked (declared deviation).
- Ceiling: random split-half of ET rows, Spearman–Brown corrected: median **0.866** (2.5–97.5%: 0.823–0.898; 200 splits). Inflated because one flood episode is spread across many rows.

## Plausibility

| season | flood_people | f71_people | ocha_affected_total |
|---|---|---|---|
| 2021 | 407,915 | 389,858 | 746,174 |
| 2022 | 388,916 | 325,274 | 1,089,604 |
| 2023 | 24,343 | 20,087 | — |
| 2024 | 359,167 | 301,242 | 1,416,678 |
| 2025 | 236,648 | 236,648 | 1,349,864 |

Largest ET flood rows (June–December):

| season_jd | event_ssid | origin_pcode | event_pcode | start_date | individuals |
|---|---|---|---|---|---|
| 2021 | et_SS0710_0006 | SS0710 | SS0710 | 2021-10-06 | 11,588 |
| 2021 | et_SS0709_0003 | SS0709 | SS0709 | 2021-10-06 | 9,875 |
| 2022 | et_SS0302_0023 | SS0306 | SS0302 | 2022-08-31 | 9,000 |
| 2024 | et_SS0711_0062 | SS0711 | SS0711 | 2024-08-16 | 8,938 |
| 2024 | et_SS0711_0068 | SS0711 | SS0711 | 2024-08-16 | 8,836 |
| 2022 | et_SS0709_0007 | SS0709 | SS0709 | 2022-10-21 | 8,590 |
| 2025 | et_SS0310_0006 | SS0310 | SS0310 | 2025-08-21 | 8,000 |
| 2021 | et_SS0710_0009 | SS0710 | SS0710 | 2021-10-06 | 7,731 |
| 2021 | et_SS0501_0003 | SS0501 | SS0501 | 2021-08-05 | 7,500 |
| 2024 | et_SS0306_0038 | SS0306 | SS0306 | 2024-08-17 | 7,270 |

ZOA counties, ET flood displacement by origin (people; descriptive only):

| county | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Bor South (SS0303) | 574 | 0 | 5,672 | 4,233 | 0 |
| Aweil Centre (SS0501) | 15,986 | 0 | 0 | 0 | 0 |
| Aweil East (SS0502) | 9,835 | 38,808 | 0 | 15,660 | 0 |
| Aweil North (SS0503) | 21,352 | 34,960 | 0 | 16,315 | 16,820 |
| Aweil South (SS0504) | 0 | 5,826 | 0 | 700 | 0 |
| Aweil West (SS0505) | 0 | 15,141 | 0 | 27,407 | 0 |

- Out-of-window flood rows: {'flood_rows_2020_season_in_2021_file': 3, 'flood_people_2020_season': 58710.0, 'flood_rows_jan_may_by_year': {2021: 19, 2022: 18, 2023: 13, 2025: 9}, 'flood_people_jan_may_by_year': {2021: 68001.0, 2022: 27723.0, 2023: 3270.0, 2025: 4936.0}}.

## Join log

| step | n_in | n_out | note |
|---|---|---|---|
| ET 2021: drop HXL tag row | 804 | 803 |  |
| ET 2021: flood-triggered IDP rows | 803 | 417 | people=534,626 |
| ET 2022: drop HXL tag row | 781 | 780 |  |
| ET 2022: flood-triggered IDP rows | 780 | 469 | people=416,639 |
| ET 2023: drop HXL tag row | 797 | 796 |  |
| ET 2023: flood-triggered IDP rows | 796 | 60 | people=27,613 |
| ET 2024: drop HXL tag row | 905 | 904 |  |
| ET 2024: flood-triggered IDP rows | 904 | 387 | people=359,727 |
| ET 2025: drop HXL tag row | 644 | 643 |  |
| ET 2025: flood-triggered IDP rows | 643 | 171 | people=241,584 |
| ET 2026: drop HXL tag row | 465 | 465 |  |
| ET 2026: flood-triggered IDP rows | 465 | 0 | people=0 |
| ET all: unique Event SSID | 4391 | 4391 |  |
| ET flood: drop exact re-assessment duplicates | 1504 | 1503 | et_SS0505_0047 |
| JD: flood rows in seasons -> valid origin pcode | 1441 | 1438 | people 1,416,989 -> 1,416,239 |
| JD: origin x season aggregated -> admin2 grid | 117 | 117 | not in grid: 0 (Abyei is in grid, outside F71) |
| JM: flood rows in seasons -> valid origin pcode | 1319 | 1315 | people 1,216,270 -> 1,215,442 |
| JM: origin x season aggregated -> admin2 grid | 99 | 99 | not in grid: 0 (Abyei is in grid, outside F71) |
| OCHA >=10k county-seasons -> ET JD table | 115 | 115 |  |
| MT first-round disaster arrivals >=1000 -> ET JD table | 136 | 136 |  |

## Questions for IOM (team to send via ZOA or ISSDTM@iom.int; interpretation only)

1. Is ET coverage national in every year 2021–2025, or limited to counties with active DTM teams?
2. Does the absence of an ET record for a county-season mean no displacement over 50 households?
3. Were ET enumerators redeployed in 2023 (Sudan returnee response at Renk), reducing flood coverage?
4. Does OCHA's flood 'affected/displaced' reporting use ET figures (shared-source error)?
5. In the 2025 file, do `Arrival Location:*` columns mean the origin (as `Arrival from:*` in 2021–2024)?

```powershell
python -m eda.impact_session_e --only 32
```