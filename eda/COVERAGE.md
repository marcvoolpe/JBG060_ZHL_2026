# EDA coverage vs Data_overview

## Admin levels

- admin0 country, admin1 states, admin2 counties, admin3 payams
- Payam EDA is in `admin3_payams.ipynb` (hazard + pop exposure ranking)
- Limit: IPC is not at payam level, so impact join stays at county/state
- OSM Malakal roads in `osm_malakal.ipynb` (saved under raw_data/OSM/)

## Geography intro

- `eda/00_guide.ipynb`: 10 states, then counties in Jonglei + Unity + Upper Nile, bbox vs polygons
- `eda/admin_ipc.ipynb`: **all 79 counties first**, then zoom to those three states

## Dataset coverage

| Family | In overview | Covered in EDA? | Where |
|--------|-------------|-----------------|-------|
| flood_masks recurring/unusual | yes | yes | Wei `flood_masks_eda.py` |
| worldpop | yes | yes | `exposure_locals.ipynb` |
| asap crop | yes | yes | `exposure_locals.ipynb` |
| asap rangeland | yes | yes | `exposure_locals.ipynb` |
| cattle | yes | yes | `exposure_locals.ipynb` |
| IPC | yes | yes (state series + county flood) | `admin_ipc.ipynb` |
| admin0 | yes | yes (Wei bbox + guide map) | Wei + `00_guide.ipynb` |
| admin1 | yes | yes (10-state map) | `00_guide.ipynb` |
| admin2 counties | yes | yes 2022-2024 | `admin_ipc.ipynb` |
| admin3 payams | yes | yes 2022-2024 | `admin3_payams.ipynb` |
| adminlines / adminpoints | yes | no (drawing helpers only) | skip |
| ERA5 rain (tp) | yes | yes | `drivers_leadtime.ipynb` |
| ERA5 runoff (ro) | yes | yes | `extra_datasets.ipynb` |
| lakes Victoria/Kyoga | yes | yes | `drivers_leadtime.ipynb` |
| lake Albert | yes | yes | `extra_datasets.ipynb` |
| Dartmouth discharge | yes | yes | `extra_datasets.ipynb` |
| health facilities | yes | yes | `extra_datasets.ipynb` |
| Evapotranspiration | yes | yes (sample years) | `extra_datasets.ipynb` |
| OSM Malakal | yes | yes | `osm_malakal.ipynb` |
| GDP | yes | minimal (national series) | `extra_datasets.ipynb` |

OSM: downloaded once into `raw_data/OSM/Malakal, South Sudan/`. Useful later for Petricola-style access, not national flood totals.
