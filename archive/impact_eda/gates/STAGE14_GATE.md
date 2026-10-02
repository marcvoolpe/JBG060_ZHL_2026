# Stage 14 gate — conflict co-occurrence (non-causal)

- `stage14_ged_admin2_month.csv`
- Within county-year demeaned OLS appended to `stage12_within_county_ols.csv` pattern.

GED type-2 only (Non-State not stacked per Stage 4).

```powershell
python -m eda.impact_panel --through 14
```