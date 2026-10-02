# Stage 19 gate — ASAP crop/rangeland at flood pixels

- Approx. pixel area from coord spacing: **0.0534 km²** (documented; not used to scale units).
- Exposure units = sum of ASAP %/100 at unique flood pixels per county-year-mask.

- `stage19_flood_pixels_all_years.csv`
- `stage19_crop_exposure_county_year.csv`
- `stage19_exposure_composition.csv` (SB-H1)

```powershell
python -m eda.impact_session_b --through 19
```