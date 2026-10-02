# Stage 31 gate — estimator, blinding and join tests

**Status: PASS.** Pre-registration `SESSION_E_HYPOTHESES.md` SHA-256 `55659458412fac15ffa0e14abfa9b25eed091e2b0d3cb1e364978c77ab60efd0` (unchanged since commit d0605c4).

No severity–outcome association was computed. All estimator tests use synthetic outcomes on real panel skeletons; the MON-2 skeleton uses only which county-seasons have ET activity.

## Tests

| test | value | pass |
|---|---|---|
| CR1 path equals statsmodels cluster SE (balanced toy, G=30, T=5) | beta 0.25701 vs 0.25701; SE 0.11067 vs 0.11067 (rel. diff 5.8e-15); CR2 SE 0.10097, BM df 17.8 | pass |
| Known-effect recovery: |bias r| < 0.02 on all skeletons, rho in {0, 0.3} | max |bias| 0.0031 | pass |
| Known-effect recovery: CR2 95% CI coverage of beta in [0.93, 0.97] | range 0.940–0.961 (r-scale CI coverage 0.952–0.964) | pass |
| Permutation null (true rho 0.3, y permuted within county, MON-2 skeleton): mean r within ±0.01 and FPR in [0.035, 0.065] | mean r -0.0002 (MC SE 0.0014); FPR 0.049 | pass |
| Season assignment on boundary dates (31 May, 1 Jun, 31 Dec, 1 Jan, missing) | JD [<NA>, 2021, 2021, <NA>, <NA>, 2020, <NA>]; JM [2020, 2021, 2021, 2021, 2021, 2020, <NA>] | pass |
| Start date missing -> assessment date used | 0 rows without start date; date_used = assessment_date for all: True | pass |
| pcode normalisation: Abyei SS1101->SS0001, whitespace, Sudan codes and names rejected | ['SS0001', 'SS0505', <NA>, <NA>, <NA>, 'SS0303'] | pass |
| Flood rows: origin pcode valid (names never used) | 4 of 1503 flood rows invalid (SD07089, SD01007, SD01001, nan); people share valid 0.9995 | pass |
| Flood rule reproduces planning counts (+1 blank/'Other' flood row in 2021 and 2022, −1 re-assessment 2024) | 2021: 417 rows / 534,626; 2022: 469 rows / 416,639; 2023: 60 rows / 27,613; 2024: 386 rows / 359,167; 2025: 171 rows / 241,584 | pass |
| 2023 'Forced return' rows never counted as flood | 579 forced-return rows, 0 flagged flood | pass |
| Blinding: confirmatory_estimate raises without permute_seed while UNBLINDED is False | UNBLINDED=False; raised=True | pass |
| fit_many (simulation path) equals twfe_cr2 | max abs diff 7.2e-17 | pass |

## Known-effect recovery (TWFE + CR2 + Bell–McCaffrey df)

DGP: county and season effects in x and y (SD 2 and 1), x and error AR(1) = 0.3 within county, county-specific error SDs (log-SD 0.3). The population within-county correlation equals ρ.

| skeleton | n_obs | n_counties | rho | mean_r | bias_r | mc_se_bias | coverage_beta | coverage_r | reject_rate |
|---|---|---|---|---|---|---|---|---|---|
| F71_balanced | 355 | 71 | 0.000 | -0.002 | -0.002 | 0.001 | 0.952 | 0.952 | 0.048 |
| F71_balanced | 355 | 71 | 0.300 | 0.301 | 0.001 | 0.001 | 0.961 | 0.964 | 0.999 |
| F71_MON2 | 332 | 71 | 0.000 | 0.000 | 0.000 | 0.001 | 0.955 | 0.955 | 0.045 |
| F71_MON2 | 332 | 71 | 0.300 | 0.298 | -0.002 | 0.001 | 0.940 | 0.954 | 0.991 |
| F71_random_drop25 | 266 | 71 | 0.000 | -0.003 | -0.003 | 0.002 | 0.953 | 0.953 | 0.047 |
| F71_random_drop25 | 266 | 71 | 0.300 | 0.297 | -0.003 | 0.002 | 0.951 | 0.957 | 0.976 |

`coverage_r` is the coverage of the slope CI rescaled to the correlation scale (sd ratio treated as fixed). It is informative only; the reporting rule 'Supported' depends only on the sign of the CI.

## Comparators under the null (synthetic, balanced F71 × 5)

- Wild cluster restricted bootstrap, Webb weights, B = 399: FPR **0.045** (400 replications, MC SE ≈ 0.011).
- Tile randomization (199 swaps within tile): FPR **0.045**. Tiles here are a synthetic split; Stage 34 repeats both on the real design and real tiles.

## ET join log

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

## Implementation notes

- `TwfeDesign` builds the full design (x, county dummies, season dummies, optional extra FE) and the CR2 adjustment `(I − H_gg)^(-1/2)` with a pseudo-inverse square root (the county block of `I − H` is singular because county FE are nested in the clusters). Bell–McCaffrey df use the Imbens–Kolesár form with a homoskedastic working model.
- Because x and the fixed effects do not change across simulated outcomes, β = wᵀy and the CR2 cluster scores are V y. Stage 34 therefore runs the identical estimator for thousands of outcome vectors (`fit_many`, checked against `twfe_cr2` above).
- Wild bootstrap: restricted residuals (β = 0 imposed), Webb six-point weights, CR1 t-statistic, symmetric p-value.
- Re-assessment rule (outcome-side): a flood row identical to an earlier one in origin, site, start date, trigger and size is dropped (one pair: Aweil West 2024, 560 people).
- The 2026 ET file is read only for 2025-season tails: it has no flood rows.

```powershell
python -m eda.impact_session_e --through 31
```