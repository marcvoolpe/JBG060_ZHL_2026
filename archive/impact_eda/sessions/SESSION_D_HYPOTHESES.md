# Session D — anticipatory action decision framework (Stages 27–30)

Pre-registered **before** running `python -m eda.impact_session_d`. Builds on [`SESSION_C_CLOSEOUT.md`](SESSION_C_CLOSEOUT.md), [`SESSION_B_CLOSEOUT.md`](SESSION_B_CLOSEOUT.md), and [`SESSION_A_CLOSEOUT.md`](SESSION_A_CLOSEOUT.md).

**Lock-ins (do not reopen):** annual flood → FEWS harvest null; hydro Spearman lead-time cut; DTM disaster tag is outcome not hazard; GED type-2 only (no stacked Non-State); OCHA one snapshot (20251130); Stage 8 combined crop+conflict model stays **no_go**.

**Purpose:** Define *when / where / how* ZOA and ZHL could act ahead of severe flood seasons — not whether floods displace people.

---

## SD-H1 — Exposure-anchored impact target validates against humanitarian layers

- **Claim:** County-year severity defined from joint flood exposure (WorldPop + ASAP crop, Session B product) ranks counties that humanitarian data also flag as stressed.
- **Test:** Spearman between exposure composite and (i) OCHA `people_affected` on assessed counties (snapshot), (ii) DTM county `disaster_share` vs flood extent (Session C).
- **Target rule:** `bad_season` = upper tercile of within-year composite impact score (2015–2025, unusual-flood years with exposure data).
- **Falsified if:** validation Spearman &lt; 0.2 on both overlays where n ≥ 15.

---

## SD-H2 — Trigger skill and cost–loss favour early action under realistic ratios

- **Claim:** A seasonal flood outlook (pluggable forecast slot + baselines) can beat climatology-only triggers for detecting `bad_season` counties at decision time **before** the wet season (May–June lead), with positive net value at humanitarian cost–loss ratios C/L ∈ {0.15, 0.20, 0.25, 0.33} (act if expected loss reduction exceeds cost).
- **Tests:**
  1. Confusion matrices across τ ∈ [0.1, 0.9] for **persistence**, **climatology**, **oracle** (upper bound), and optional **external** CSV.
  2. Report hit rate, false-alarm rate, and regret vs perfect foresight.
- **Falsified if:** persistence and climatology never exceed climatology hit rate at fixed false-alarm ≤ 0.35, OR no C/L in range yields positive net value for best baseline.

---

## SD-H3 — Conflict and livelihood stratification change the action menu, not the hazard trigger

- **Claim:** Among high-trigger counties, GED conflict intensity and FEWS LHZ class split operational routes (in-kind agro protection vs secure cash/pre-positioning vs pastoral livestock measures) without reopening flood→conflict causation.
- **Test:** Cross-tab high exposure × high recent conflict (2023–2024 GED); assign profiles 1–3; document seasonal conflict dip during wet-season action window vs dry-season peak.
- **Falsified if:** &lt; 5 counties fall in compound high-flood × high-conflict cells (power too low for routing table).

---

## Gate checklist

- [ ] `stage27_prediction_interface_spec.md` documents pluggable CSV schema.
- [ ] n at each join in `stage28_trigger_performance.csv`.
- [ ] `SESSION_D_CLOSEOUT.md` with ZOA/ZHL recommendation section (act / do-not-act / monitor).
- [ ] Six protocol sections in close-out.
