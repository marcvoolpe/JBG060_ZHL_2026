# Deliverables

This folder contains the compact outputs that are useful for quick review without
re-running the full EDA workflow.

## Figures

- `figures/observation_locations_context_map.png`: observation locations, major
  rivers, lakes, South Sudan boundaries, and flood mask extent.
- `figures/climate_grid_points_context_map.png`: ERA5 rainfall/runoff and AgERA5
  ET grid points in the regional context.
- `figures/10_primary_discharge_monthly_vs_flood.png`: station 100205 monthly
  mean discharge vs monthly South Sudan flood pixel-day count.
- `figures/11_primary_discharge_flood_monthly_relationship.png`: station 100205
  discharge-flood scatter and monthly lag correlations.
- `figures/12_albert_lake_monthly_water_level_vs_flood.png`: Lake Albert monthly
  mean water level vs monthly South Sudan flood pixel-day count.
- `figures/13_albert_lake_flood_monthly_relationship.png`: Lake Albert
  water-level-flood scatter and monthly lag correlations.
- `figures/09_primary_discharge_monthly_hydrograph_by_year.png`: station 100205
  monthly mean discharge by recent complete years.
- `figures/1541_monthly_discharge_hydrograph_recent_10_years.png`: station 1541
  monthly mean discharge by recent complete years.
- `figures/08_upstream_lake_levels_vs_flood.png`: upstream lake water levels and
  flood counts.

## Tables

The `tables/` folder contains compact CSVs used by the figures and summary
checks. Large intermediate EDA tables are intentionally not committed.

## Reproducibility

Processed data are committed in `processed-data/`. The original raw datasets are
not committed because they are large; place them in `raw_data/` and run:

```bash
python -m processing_data.process_all_data
python -m eda.revised_spatial_eda
```

The first command rebuilds `processed-data/`. The second command rebuilds the
larger EDA outputs under `eda/outputs/`.
