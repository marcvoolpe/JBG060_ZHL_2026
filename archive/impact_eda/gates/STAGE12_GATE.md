# Stage 12 gate — H2/H3/H4 cropland panel

Outputs: `stage12_pooled_spearman_by_year.csv`, `stage12_within_county_ols.csv`,
`stage12_seasonal_pixel_days.csv`.

If within-county coefficients are insignificant, cropland deliverable stays **exposure-only**.

```powershell
python -m eda.impact_panel --through 12
```