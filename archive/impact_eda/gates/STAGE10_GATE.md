# Stage 10 gate — flood admin2 panel

## Artefacts

| Output | Path |
|--------|------|
| Pixel lookup | `eda\outputs\impact_eda\flood_pixel_to_admin2.csv` |
| County-month panel | `eda\outputs\impact_eda\flood_admin2_month.csv` |
| County-year panel | `eda\outputs\impact_eda\flood_admin2_year.csv` |

## Reconcile vs Stage 7 (2022–2024 unusual unique px)

- Max absolute county-year diff: **1**
- Counties compared: **373**
- Gate pass: **yes**

```powershell
python -m eda.impact_panel --through 10
```