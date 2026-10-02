# Session C — conflict seasonality and displacement (Stages 23–26)

Pre-registered **before** running `python -m eda.impact_session_c`. Follows [`SESSION_B_CLOSEOUT.md`](SESSION_B_CLOSEOUT.md) and [`SESSION_PROTOCOL.md`](SESSION_PROTOCOL.md).

**Lock-ins:** GED type-2 only; DTM disaster = outcome not flood label; no crop×conflict model; `data/ACLED_conflict_events/` is UCDP duplicate — not used.

---

## SC-H1 — H8 wet-season suppression, dry-season rebound (type-2)

- **Claim:** Within county-year FE, unusual flood extent in **wet months 6–10** associates with **fewer** type-2 events concurrently; **wet-season flood** predicts **more** type-2 in the **following dry window** (Nov year *t* – May year *t*+1).
- **Tests:** Separate within-county OLS at county-**year** grain (wet-season sums); dry outcome uses lead wet flood. Specs: `all`, `pastoral_dominant` (livelihood stratum), `pre2022` (flood years &lt; 2022).
- **Falsified if:** in spec `all`, wet coef is not negative or dry-lead coef is not positive at p&lt;0.05, or both same sign.

---

## SC-H2 — H7 DTM sites and flood proximity

- **Claim:** IDP sites with any disaster-tagged arrival are **closer** to unusual flood pixels (2022–2024) than sites with conflict-tagged arrival only; county disaster-arrival share correlates with unusual flood extent more than stock does.
- **Test:** Haversine km to nearest unusual pixel; Mann-Whitney or median comparison; county Spearman disaster share vs mean unusual px 2022–2024.
- **Falsified if:** median disaster distance ≥ median conflict distance, or county disaster share unrelated to flood (p&gt;0.1).

---

## Data joins (Stage 23)

- `data/SS_LHZ_2018/SS_LHZ_2018.shp` → dominant zone per `adm2_pcode`.
- Pastoral stratum: `LZNAMEEN` contains pastoral, cattle, or livestock (pre-declared).

---

## Deferred

- AGLW livestock: see [`DEFERRED_DATASETS.md`](DEFERRED_DATASETS.md).
