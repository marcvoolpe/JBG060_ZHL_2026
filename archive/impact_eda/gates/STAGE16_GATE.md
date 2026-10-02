# Stage 16 gate — H5 lag repair (Session A)

County-month unusual `pixel_days` vs lagged ERA5 precip and national hydro (1541, Victoria).

- `stage16_era5_county_month.csv` (cache)
- `stage16_hydro_monthly.csv` (cache)
- `stage16_monthly_lag_correlations.csv`

```powershell
python -m eda.impact_session_a --through 16
```