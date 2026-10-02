# Stage 11 gate — observability and regime

## Findings

- `cloud_frac` in compact parquets is **constant 0.0** (see `stage11_cloud_frac_audit.csv`). Not usable as a control.
- Tile-month record counts in `stage11_tile_month_record_counts.csv` (proxy for observation intensity).
- Unusual annual pixel-days mean ≤2019: **668849**; ≥2022: **11963217** (`stage11_annual_pixel_days.csv`).
- **Baseline decision for H2:** use county demeaning with years **2011–2024**; sensitivity excluding **≥2022**.
- **H3 windows:** planting months **4–6**, harvest **9–11** (pre-declared).
- Recurring and unusual share similar dry-season peaks → interpret seasonality as shared hydrology/artefact, not mask-specific.

```powershell
python -m eda.impact_panel --through 11
```