# Stage 34 gate — realistic power, controls and gap register (SE-H3)

**Status: FAIL — NO-GO (SE-H3 kill criterion).** Planning-cell decision band: **NO-GO**.


The simulation reads only observed severity and `stage32_outcome_marginals.json`. The positive control outputs county means only; the circularity control uses ET non-flood records (flood columns dropped before the join).

## Kill criteria

| criterion | value | pass |
|---|---|---|
| MDE80 (planning cell) <= 0.5 | inf [nan, nan] | **FAIL** |
| Some inference method has FPR in [0.035, 0.065] (all-nuisance null) | CR2 0.057, wild_webb 0.055, tile_randomization 0.070 | pass |
| Positive control (between-county Spearman of means) >= 0.3 | 0.678 | pass |
| FPR at psi-hat <= 0.1 | 0.072 | pass |

## Planning cell

- Primary frame (lower simulated MDE80, pre-registered rule): **F71**; MDE80 by frame: F71 inf [nan, nan]; exposed_5km2 inf [nan, nan].
- Rx = 0.60 (min(0.6, split-half ceiling); ERA5 convergence > 0). Ry = 0.24 (min(0.5, detection cap); caps at σ_c = 0: F71 0.237, exposed_5km2 0.227).
- **MDE80 = inf** (Monte Carlo 95% CI nan–nan) → **NO-GO** (GO ≤ 0.35; team decision ≤ 0.5; worse band if the CI straddles a cut-off).

| rho | R | power | power_mcse | reject_two_sided | mean_r_obs | rho_achieved | ry_achieved | county_mae | season_mae | c | sigma_c |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 2000.000 | 0.013 | 0.003 | 0.038 | -0.008 | 0.000 | 0.237 | 0.016 | 0 | 0.000 | 1.349 |
| 0.200 | 2000.000 | 0.115 | 0.007 | 0.116 | 0.063 | 0.200 | 0.237 | 0.019 | 0 | 0.461 | 0.396 |
| 0.250 | 2000.000 | 0.202 | 0.009 | 0.203 | 0.085 | 0.250 | 0.237 | 0.014 | 0 | 0.615 | 0.723 |
| 0.300 | 2000.000 | 0.220 | 0.009 | 0.220 | 0.093 | 0.298 | 0.228 | 0.021 | 0 | 0.908 | 0.000 |
| 0.350 | 2000.000 | 0.337 | 0.011 | 0.337 | 0.118 | 0.348 | 0.237 | 0.020 | 0 | 1.046 | 1.295 |
| 0.400 | 2000.000 | 0.391 | 0.011 | 0.391 | 0.126 | 0.393 | 0.237 | 0.018 | 0 | 1.721 | 0.382 |
| 0.450 | 2000.000 | 0.477 | 0.011 | 0.477 | 0.143 | 0.430 | 0.237 | 0.016 | 0 | 2.026 | 1.041 |
| 0.500 | 2000.000 | 0.607 | 0.011 | 0.607 | 0.167 | 0.483 | 0.237 | 0.015 | 0 | 2.714 | 1.910 |
| 0.600 | 2000.000 | 0.703 | 0.010 | 0.703 | 0.183 | 0.538 | 0.237 | 0.020 | 0 | 5.478 | 1.907 |

- Highest reachable true within-county ρ under the hurdle model (target 0.60): 0.538. MDE80 is interpolated on the achieved ρ; if power never reaches 0.80 it is reported as ∞ (above the reachable range).

`mean_r_obs` is the average estimated within-county r on observed data (attenuated by √(Rx·Ry) and zeros); `county_mae`/`season_mae` are the absolute errors of the matched recorded-non-zero shares.

## MDE80 across the Rx × Ry grid (primary frame)

| Rx \ Ry | Ry target 0.24 | Ry target 0.30 | Ry target 0.50 | Ry target 0.70 |
|---|---|---|---|---|
| 0.400 | — | — | — | — |
| 0.600 | — | — | — | — |
| 0.800 | — | 0.472 | 0.476 | 0.484 |

- Achieved Ry by target: 0.24 → 0.236, 0.30 → 0.250, 0.50 → 0.248, 0.70 → 0.246. Detection (π = OCHA rate, 300-person threshold) caps outcome reliability, so every Ry target above the cap runs at the cap: the Ry columns are not distinct designs. Pre-registered: 'if π alone caps Ry below the target, report that cap as a finding'.
- '—' = power never reaches 0.80 within the reachable ρ range (MDE80 > max achieved ρ).
- OFAT rows with fpr_rho0 well above 0.05 (ψ at the CI upper bound, all-nuisance) have power inflated by circularity bias; their MDE80 does not measure detectability.

## One factor at a time (planning cell, 500 replications per ρ)

| variant | frame | rx | ry | mde80 | ci_lo | ci_hi | band | fpr_rho0 |
|---|---|---|---|---|---|---|---|---|
| MON-1 | MON-1 | 0.600 | 0.197 | — | — | — | NO-GO | 0.066 |
| MON-2 | MON-2 | 0.600 | 0.247 | — | — | — | NO-GO | 0.050 |
| all_nuisance | F71 | 0.600 | 0.237 | 0.512 | 0.497 | 0.532 | NO-GO | 0.102 |
| ar_0.3 | F71 | 0.600 | 0.237 | — | — | — | NO-GO | 0.050 |
| frame_alt | exposed_5km2 | 0.600 | 0.227 | — | — | — | NO-GO | 0.048 |
| june_may | june_may | 0.600 | 0.302 | 0.501 | 0.488 | — | NO-GO | 0.116 |
| phi_-0.2 | F71 | 0.600 | 0.237 | — | — | — | NO-GO | 0.048 |
| pi_0.8_extra | F71 | 0.600 | 0.237 | 0.564 | 0.525 | — | NO-GO | 0.040 |
| planning | F71 | 0.600 | 0.237 | — | — | — | NO-GO | 0.038 |
| planning | exposed_5km2 | 0.600 | 0.227 | — | — | — | NO-GO | 0.050 |
| psi_ci_hi | F71 | 0.600 | 0.237 | 0.180 | 0.159 | 0.202 | GO | 0.432 |
| psi_hat | F71 | 0.600 | 0.237 | 0.481 | 0.412 | 0.524 | NO-GO | 0.072 |
| tau_0.2 | F71 | 0.600 | 0.237 | — | — | — | NO-GO | 0.052 |
| with_2023 | with_2023 | 0.600 | 0.311 | 0.472 | 0.461 | 0.482 | TEAM DECISION | 0.038 |

## Inference calibration (ρ = 0 with τ = 0.2, AR = 0.3, φ = −0.2, county heterogeneity)

- Two-sided 5% false-positive rates: CR2 **0.057**, wild bootstrap (Webb, B = 399) **0.055**, tile randomization (199 swaps; 500 replications) **0.070**; 1000 replications, MC SE ≈ 0.007.
- Switch to bootstrap (CR2 outside band while bootstrap inside)? **False**.

## Controls

- Positive control: between-county Spearman of county-mean severity vs county-mean ET flood displacement = **0.678** (county means in `stage34_positive_control_county_means.csv`).
- Circularity control: within-county r of severity with log1p ET non-flood records = **0.087** (95% CI -0.053 to 0.227; n = 284, 71 counties). Mapped to ψ = 0.165 (logit detection shift per SD of observed severity); simulated FPR at ψ̂ = **0.072**, at the CI upper bound (ψ = 0.441) 0.432. Calibration fit: within-SD 0.684 vs target 0.684; r 0.087 vs target 0.087.

## Validation-gap register (`stage34_gap_register.csv`)

| gap | handling | detail | evidence |
|---|---|---|---|
| Survey timing, Mobility Tracking | outcome switch | fatal for MT; resolved by switching to ET | within_county_dtm_reliability.json (0.00–0.49) |
| Survey timing, ET | test + rule | start-date assignment; assessment lag by season | Stage 32 lag table (median 11–19 d, p90 up to 75 d in 2025) |
| Survey timing, OCHA | clause | OCHA used only for detection and the reliability floor | snapshots Oct–Dec; 2024 file undated |
| Masks blind Jul–Sep while ET peaks Jul–Oct | parameter phi | phi = -0.2: Rx_eff 0.52 at planning Rx | Stage 33 blind-season profile |
| Monitoring effort and circularity | parameter psi + control | psi = 0.165 from control r = 0.087 | FPR at psi 0.072 |
| Hubs (origin vs event county) | clause | origin = event county for 92–100% of people | Stage 32 |
| 2023 mislabelled returns | label rule | forced returns never flood | Stage 31 test |
| 2023 coverage collapse | rule | 2023 dropped by pre-registered MT-detection rule | Stage 32 |
| 2025 garbled names | rule | join on pcodes only | Stage 31 test |
| No ET data for December 2025 | window + sensitivity | June–December window; season-set sensitivity | Stage 34 OFAT |
| 2020-season tails in the 2021 file | rule | start-date assignment (3 rows, out of panel) | Stage 32 |
| Split totals across sites | rule | summed by origin and season | Stage 32 |
| Sub-threshold rows | rule + parameter | kept; simulation records only P >= 300 | Stage 34 |
| Spatially correlated shocks | parameter tau + LOSO | tau = 0.2 | Stage 34 OFAT; SE-H4 LOSO |
| Sudd dominance | test (SE-H4) | leave-one-state-out | only after GO |
| Tile seam | test | tile x season share 0.023 < 0.10 | Stage 33 |
| Post-2020 regime only | clause | scope limited to 2021–2025 | — |
| Rain-fed vs river-fed counties | clause | described, not tested | — |
| Outcome reliability unknown (ET–OCHA floor weak) | parameter Ry grid | Ry in {0.3, 0.5, 0.7} | floor r_w = 0.111 |
| Severity reliability only bounded above | parameter Rx grid + GEE check | Rx in {0.4, 0.6, 0.8}; Sentinel-1 check before any null claim | Stage 33 ceiling |
| Severity product regime change (2001–2020 vs 2021–2025 detection volume) | clause | panel restricted to 2021–2025; long-run ERA5 convergence negative | Stage 33 |

## Simulation assumptions not fixed by the pre-registration (declared here)

- κ = 0.5: share of the within-county log-size SD driven by the latent index.
- County error SDs log-normal (log-SD 0.3); county detection heterogeneity N(0, 0.5²) on the logit scale, rank-matched to each county's recorded share (always-recorded counties get the highest detection); mean detection = OCHA-based rate.
- φ enters as an effective reliability: the error keeps its φ = 0 variance but correlates −0.2 with truth.
- ψ: non-flood records ~ Poisson(λ_i · exp(ψ x~ + η)), η matched to the observed within-county SD of log1p records; the same ψ shifts detection of flood displacement on the logit scale.
- Target recorded-non-zero shares are clipped to [0.03, 0.97].

```powershell
python -m eda.impact_session_e --only 34
```