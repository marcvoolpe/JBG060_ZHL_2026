# Stage 33 gate — severity audit (SE-H2)

**Status: PASS.**

Severity-side only: no ET outcome values were read (only the list of panel seasons from Stage 32).

## Kill criterion

| criterion | value | pass |
|---|---|---|
| Split-half ceiling on Rx (F71, panel seasons, unusual) >= 0.4 | 0.906 | pass |

## Split-half reliability (odd vs even June–December dekads)

| frame | class_set | seasons | n_counties | n | r_half | spearman_brown |
|---|---|---|---|---|---|---|
| F71 | combined | panel | 71 | 284 | 0.809 | 0.894 |
| F71 | combined | all_2021_2025 | 71 | 355 | 0.830 | 0.907 |
| F71 | unusual | panel | 71 | 284 | 0.829 | 0.906 |
| F71 | unusual | all_2021_2025 | 71 | 355 | 0.840 | 0.913 |
| exposed_1km2 | combined | panel | 63 | 252 | 0.803 | 0.891 |
| exposed_1km2 | combined | all_2021_2025 | 63 | 315 | 0.828 | 0.906 |
| exposed_1km2 | unusual | panel | 63 | 252 | 0.825 | 0.904 |
| exposed_1km2 | unusual | all_2021_2025 | 63 | 315 | 0.838 | 0.912 |
| exposed_5km2 | combined | panel | 47 | 188 | 0.804 | 0.891 |
| exposed_5km2 | combined | all_2021_2025 | 47 | 235 | 0.833 | 0.909 |
| exposed_5km2 | unusual | panel | 47 | 188 | 0.832 | 0.908 |
| exposed_5km2 | unusual | all_2021_2025 | 47 | 235 | 0.846 | 0.916 |
| exposed_25km2 | combined | panel | 18 | 72 | 0.810 | 0.895 |
| exposed_25km2 | combined | all_2021_2025 | 18 | 90 | 0.837 | 0.911 |
| exposed_25km2 | unusual | panel | 18 | 72 | 0.843 | 0.915 |
| exposed_25km2 | unusual | all_2021_2025 | 18 | 90 | 0.854 | 0.921 |

- Mask class chosen by the pre-registered rule (higher split-half, F71, panel seasons): **unusual**, ceiling **0.906**.
- This is a ceiling on Rx only: alternating dekads share the same flood, the same cloud regime and the same season-wide omission errors (masks are blind under persistent cloud, `cloud_frac` = 0 everywhere).

## Convergence with ERA5 June–December precipitation (within county, log precip)

| seasons | spearman_resid | r | r_ci | n |
|---|---|---|---|---|
| panel | 0.150 | 0.193 | [0.039, 0.346] | 280 |
| all_2021_2025 | 0.154 | 0.156 | [0.022, 0.29] | 350 |
| 2001_2025 | -0.111 | -0.104 | [-0.161, -0.047] | 1750 |

- ERA5 convergence fails (≤ 0 on panel seasons)? **False** → planning Rx = **0.60**.

## Tile artefacts

- Counties per majority tile (F71): {'h21v08': 41, 'h20v08': 30}.
- Share of county-and-season-demeaned severity variance explained by tile × season dummies: **0.023** (rule: add tile × season FE if ≥ 0.1) → **do not add tile × season FE**.

## Blind-season profile (parameter φ)

- Median county-season share of June–December pixel-dekads in Jul–Sep: 0.039 (IQR 0.000–0.207); Nov–Dec median 0.785. Jul–Sep = 9 of 21 June–December dekads (0.43 if detections were uniform).
- National Jul–Sep share by season: {2021: 0.145, 2022: 0.216, 2023: 0.338, 2024: 0.278, 2025: 0.221}; Nov–Dec: {2021: 0.622, 2022: 0.581, 2023: 0.416, 2024: 0.479, 2025: 0.509}.
- ET flood events start mostly July–October (Stage 32), when the masks see least. Severity therefore leans on the post-peak recession; the simulation carries this as error correlated with truth (φ = −0.2).

## Frame options

- Frame sizes: {'F71': 71, 'exposed_1km2': 63, 'exposed_5km2': 47, 'exposed_25km2': 18} (flood-exposed = unusual-class June–December extent ≥ threshold in at least 10 of the 2001–2020 seasons, within F71).
- F71 county-seasons with zero detected severity (panel seasons): 8.
- Within-county SD of log1p severity after county and season effects: 0.878.

## Join log

Severity read from cache `stage33_severity_raw.csv` (delete it to rebuild from the parquets).

```powershell
python -m eda.impact_session_e --only 33
```