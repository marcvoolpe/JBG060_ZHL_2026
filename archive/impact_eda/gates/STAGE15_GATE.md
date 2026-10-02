# Stage 15 gate — H2/H3 robustness (Session A)

Pre-registered: `SESSION_A_HYPOTHESES.md` (SA-H1, SA-H2).

- `stage15_h2_robustness.csv` — within-county OLS across specs
- `stage15_h3_robustness.csv` — seasonal windows (plant 4–6, harvest 9–11)
- `stage15_join_counts.csv` — n per spec

```powershell
python -m eda.impact_session_a --through 15
```