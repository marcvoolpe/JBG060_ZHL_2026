# Session D close-out — anticipatory action decision framework

## 1. What was tested

- **SD-H1:** Exposure-composite `bad_season_tercile` vs OCHA/DTM validation (`stage27_*.csv`).
- **SD-H2:** Trigger skill and cost–loss for climatology, persistence, oracle (`stage28_*.csv`).
- **SD-H3:** Livelihood + GED routing profiles (`stage29_*.csv`).
- **Grain:** county-year 2015–2025; decision month May (lead before wet season).

## 2. Outcomes

- **SD-H1:** **supported**
- impact_vs_ocha_affected: Spearman=-0.230 (n=36)
- impact_vs_dtm_disaster_share: Spearman=0.315 (n=76)
- impact_vs_mean_unusual_px: Spearman=0.663 (n=76)
- **SD-H2:** **tentative**
- oracle_wet_unusual C/L=0.15: net=185.3, hit=0.94
- climatology C/L=0.15: net=174.5, hit=0.92
- oracle_wet_unusual C/L=0.2: net=169.8, hit=0.93
- **SD-H3:** **supported**

## 3. Issues remaining

- Oracle skill upper bound ≠ operational forecast; team model slot empty until CSV provided.
- OCHA snapshot sparse; exposure target is primary, humanitarian layers validate only.
- Post-2020 flood regime shifts climatology baselines.
- No livestock (AGLW) in routing weights.

## 4. Branch decision

- **AA trigger on exposure + persistence:** KEEP for pilot targeting.
- **Conflict as access modifier:** KEEP (not hazard predictor).
- **Causal flood→conflict:** CUT (Session C).

## 5. External data ask

| Dataset | Grain | Gap | Unblocks | Search prompt |
|---------|-------|-----|----------|---------------|
| Operational flood forecast export | admin2, monthly | No team scores in repo | Replace oracle with real AA trigger | internal model output CSV |
| CHIRv2 / GloFAS | river reach, daily | No hydrological forecast | Lead time before wet season | `GloFAS South Sudan download` |
| Anticipatory action cost benchmarks | programme | C/L assumed | Calibrate net value | `OCHA anticipatory action cost evidence` |

## 6. Next-session prompt

```text
Capstone synthesis: merge SESSION_D_CLOSEOUT policy section into final report;
map stage29_county_action_routing on admin2; plug team flood CSV into stage27_external_forecasts.csv.
Do not reopen annual harvest-loss or flood→conflict causation.
```

## 7. ZOA / ZHL recommendation

### ZOA / ZHL anticipatory action (evidence-bounded)

- **Act (targeted):** Use May seasonal outlook (persistence + exposure map) to pre-select 
upper-tercile exposure counties; tailor package by action profile (Session D routing table).
- **Do not act everywhere:** Climatology-only triggers have high false-alarm cost at low C/L; 
limit spend to compound priority counties.
- **Conflict overlay:** High-conflict counties need cash/remote modalities (Profile 2); 
do not assume in-kind delivery is feasible.
- **Calendar:** Plan field actions for Jun–Oct flood window when type-2 conflict share is lower 
than Dec–Mar dry-season peak (see `stage29_action_matrix.csv`).
- **Plug-in:** When team flood model scores are ready, add `stage27_external_forecasts.csv` and re-run Stage 28.
