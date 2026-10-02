# Stage 25 gate — H7 DTM distances (SC-H2)

- Distances use sites with lat/lon (primarily R16); R13–R15 lack coordinates.
- Mann-Whitney disaster closer than conflict: p=6.023558451591696e-43

- `stage25_dtm_site_distances.csv`
- `stage25_dtm_distance_summary.csv`
- `stage25_county_disaster_vs_flood.csv`

```powershell
python -m eda.impact_session_c --through 25
```