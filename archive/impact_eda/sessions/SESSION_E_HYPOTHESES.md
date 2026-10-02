# Session E — go/no-go verification of the within-county flood-impact RO (Stages 31–35)

Pre-registered **before** running `python -m eda.impact_session_e`. Builds on the two external reviews in `external_deep_research/` (Report 1 and `within_county_deep_research_1.md`), `eda/within_county_reliability.py` and `eda/within_county_demo.py`.

**Purpose:** decide, with numbers and before looking at the answer, whether the RO below is worth several team-days. This session does **not** estimate the RO. It checks whether an estimate would be interpretable.

**Candidate RO (confirmatory, SE-H4, run only after GO).** Does a season's *observed* flood severity explain within-county variation in *new* flood displacement, counted by origin county, beyond persistent differences between counties? Seasons 2021–2025. The RO is associational, not forecast validation.

**Disclosure (seen before this pre-registration).** Within-county correlations with earlier outcomes were already computed:
- DTM Mobility Tracking: ρ = 0.16 (95% CI −0.00 to 0.32).
- OCHA people affected: ρ = 0.04 (95% CI −0.17 to 0.25).

These cannot be un-seen. The blinding below freezes choices; it does not hide information.

**Lock-ins (do not reopen):**
- The Mobility Tracking stock outcome is rejected. Its within-county test-retest reliability is 0.00–0.49 (`within_county_dtm_reliability.json`).
- The DTM disaster tag is an outcome, not a hazard.
- ACLED (state × week only) and UCDP (67 type-2 events in 2021–25) are not used as controls.

**Declared protocol deviation:** OCHA snapshots are stacked across years, but only for the outcome-reliability floor in Stage 32.

---

## Frozen specification

### Outcome

The outcome is log1p of individuals in flood-triggered rows of IOM DTM Event Tracking (ET), summed by origin county and season.

**Which rows count as flood-triggered.** A row counts only if `Affected population category` = IDPs, and one of these holds:
- `Movement Trigger` matches `/flood/i`; or
- the trigger is an "Other" label ("Natural disaster (Other)", "Disaster (Other)", "Others (Specify)") or is blank, **and** `Other Trigger` matches `/flood|rain/i`.

"Forced return…" rows never count.

**Season assignment.** Each row is assigned by `Event Started On (From date)`; if that is missing, by `Assessment Date`.

**Origin county.** Taken from `Arrival from: Admin 2 PCODE` (2021–2024) or `Arrival Location: Admin 2 PCODE` (2025). Abyei `SS1101` is mapped to `SS0001`. Names are never used. Rows with no valid pcode are counted and excluded.

**Split totals across sites** are summed. Rows below the 50-household threshold are kept.

**Missing county-seasons.**
- **MON-0 (primary):** every frame county-season is observed, and no record means 0.
- **MON-1 (sensitivity):** only counties with any ET record (any trigger, as event location) in at least 3 of 2021–2025.
- **MON-2 (sensitivity):** a county-season counts as observed if ET recorded a non-flood event there that season, or any event in another county of the same state.

### Season window

- **Primary:** **June–December** of each year, 2021–2025. Events starting January–May are excluded from the primary panel.
- **Robustness:** June–May seasons 2021/22–2024/25, with January–May events assigned to the preceding season.
- **Ruled out:** calendar-year and July–June windows.

### Severity

Severity is log1p(extent × duration) per county, June–December, from the course NASA masks. Extent is in km² and duration in dekads with at least one detection.

- **Mask class:** combined classes vs unusual only, decided in Stage 33 by the higher split-half reliability (severity-side rule).
- **Tile × season fixed effects** are added to every model if tile × season dummies explain ≥ 10% of the county-and-season-demeaned severity variance (Stage 33, severity-side rule).

### Frame

- **F71:** the 71 counties with ≥ 95% mask coverage.
- **Alternative frames:** "flood-exposed" counties, meaning unusual-class June–December extent ≥ 5 km² in at least half of the 2001–2020 seasons. The 1 km² and 25 km² thresholds are sensitivities.
- **Choice rule:** the primary frame is whichever of F71 and the 5 km² frame gives the lower simulated MDE80 in Stage 34. This uses no outcome–severity association.

### Estimator

Two-way fixed effects (TWFE) on log1p values, with county and season effects.

**Fitting.**
- Demean y, x and the season dummies within county, then run OLS. This is correct for unbalanced panels.
- The reported effect size is the within-county correlation r. This is the standardized slope on the two-way residualized variables.

**Inference.**
- CR2 cluster-robust SE by county.
- For absorbed fixed effects, the full-design hat matrix is used with pseudo-inverse square roots.
- Bell–McCaffrey (Satterthwaite) degrees of freedom.

**Comparators:**
- a wild cluster restricted bootstrap with Webb weights;
- a randomization test that swaps severity series between counties within the same MODIS tile.

**Switch rule.** CR2 stays primary unless its false-positive rate falls outside 0.035–0.065 while the bootstrap's falls inside (Stage 34).

**Robustness:** Spearman correlation of the two-way residuals.

### Reporting rules (for SE-H4)

- **"Supported":** the 95% CI lower bound of r is above 0.
- **"No large effect":** the one-sided 95% upper bound is below 0.35·√(Rx·Ry). Allowed only after the Google Earth Engine Sentinel-1 check measures Rx.
- **"Inconclusive":** anything else.
- **National claim:** also requires leave-one-state-out. The sign must hold and every estimate must stay inside the CI.

### Blinding

- `impact_session_e.confirmatory_estimate()` raises an error unless `UNBLINDED` is True or a `permute_seed` is given. With a seed, outcome seasons are permuted within county.
- `UNBLINDED` may be set only after `STAGE35_GATE.md` records GO or an accepted team decision, and after the frozen spec hash has been emailed to the supervisor.
- The Stage 34 simulation reads only `stage32_outcome_marginals.json`. It never joins county × season outcomes to severity.

---

## SE-H1 — Event Tracking gives a usable flood-displacement panel (Stage 32)

**Claim.** ET supports a county × season panel of new flood displacement by origin, with enough seasons and within-county variation, and with credible detection.

**Tests.**
- Harmonise 2021–2025 and log n at every join.
- Count usable seasons.
- Count counties whose outcome varies.
- Detection rate against OCHA: among OCHA county-seasons with ≥ 10,000 affected, the share with any ET flood record from that origin county.
- Detection rate against Mobility Tracking, using first-round disaster arrivals ≥ 1,000.
- ET–OCHA within-county correlation r_w, giving a floor on outcome reliability R_ET ≥ r_w². Informative only.
- Random split-half of ET rows, giving a ceiling on R_ET. Informative only.
- **2023 rule:** keep 2023 unless its Mobility Tracking-based detection rate is below half the median of the other seasons.

**Falsified (NO-GO) if any of these holds:**
- Fewer than 3 usable seasons. A usable season has ≥ 95% of flood individuals with a valid origin pcode, **and** ≥ 15 F71 counties with non-zero outcome.
- Fewer than 35 F71 counties whose outcome is not constant across usable seasons.
- The OCHA-based detection rate is below 0.40. If the OCHA sample has fewer than 10 county-seasons, the Mobility Tracking-based rate is used instead.

## SE-H2 — Seasonal severity has measurable within-county variation (Stage 33)

**Claim.** June–December severity varies within counties more than detection noise does.

**Tests.**
- Split-half reliability: odd vs even dekads, correlation of two-way residuals, then Spearman–Brown correction. This is a **ceiling** on Rx.
- Within-county Spearman between severity and log June–December ERA5 precipitation (`stage16_era5_county_month.csv`).
- Tile × season variance share.
- Blind-season profile: the share of June–December detections that fall in July–September.
- Flood-exposed frame flags.

**Falsified (NO-GO) if** the split-half ceiling is below 0.4.

If ERA5 convergence is ≤ 0, that is not a kill; the planning Rx becomes 0.4.

## SE-H3 — The design can detect a true within-county correlation of 0.35 (Stage 34)

**Claim.** Given the real panel skeleton, real severity, the outcome marginals, detection and measurement error, the pre-registered estimator detects a **true** within-county correlation of 0.35 with 80% power. It must do so with a calibrated false-positive rate and without spurious association from monitoring effort.

**Tests.**
- **Hurdle simulation** (spec in `impact_session_e.py`):
  - grid ρ ∈ {0, .20, .25, .30, .35, .40, .45, .50, .60};
  - Rx ∈ {.4, .6, .8}, capped at the split-half ceiling;
  - Ry ∈ {.3, .5, .7};
  - 1,000 replications per cell, 2,000 in the planning cell;
  - one-factor-at-a-time runs (frame, MON rule, season set, τ, ψ, φ, AR).
- **Planning cell:** Rx = min(0.6, split-half ceiling); Ry = min(0.5, any detection cap).
- **MDE80:** the smallest ρ with power ≥ 0.80 for "Supported", interpolated on logit(power), with a Monte Carlo CI. If the CI straddles a cut-off, the worse band applies.
- **Positive control:** between-county Spearman of county-mean severity against county-mean outcome. Only county means are output.
- **Circularity control:** within-county TWFE association of severity with ET **non-flood** records per county-season, as event location. Its estimate ψ̂ enters the simulation.

**Decision.**
- **GO:** MDE80 ≤ 0.35.
- **Team decision ("detects large effects only"):** 0.35 < MDE80 ≤ 0.50.
- **NO-GO:** MDE80 > 0.50.

**Also NO-GO if any holds:**
- No inference method has a false-positive rate within 0.035–0.065 under the all-nuisance null.
- The positive control is below 0.3.
- The simulated false-positive rate at ψ̂ is above 0.10. The alternative is to reframe the RO as "recorded displacement".

## SE-H4 — Confirmatory (not run in this session unless GO)

Run the frozen specification once, with CI and the reporting rules above, plus the MON-1, MON-2, June–May and leave-one-state-out sensitivities.

---

## Gate checklist

- [ ] Stage 31: estimator and blinding tests pass: known-effect recovery (bias < 0.02, coverage 93–97%), permutation null, CR2 vs statsmodels, season boundaries, pcode joins.
- [ ] Stage 32: n at each join; usable seasons; varying counties; detection rates; marginals JSON.
- [ ] Stage 33: split-half ceiling; ERA5 convergence; tile rule; frame flags.
- [ ] Stage 34: MDE table; false-positive calibration; controls; gap register (each gap mapped to a test, a parameter or a clause).
- [ ] Stage 35: scorecard with GO / team decision / NO-GO; `SESSION_E_CLOSEOUT.md` with the six protocol sections.
