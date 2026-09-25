# JBG060-2026: Flood Dynamics in South Sudan

## Introduction and overview

This repository supports the 2026 JBG060 course project on flood dynamics in South Sudan. 
Its current scope is data loading and preprocessing: it brings hydrometeorological hazard data together with 
exposure and impact data so that they can be used in later flood-risk analyses.

The repository currently provides utilities for:

- river discharge, lake levels, rainfall, runoff, evapotranspiration, and flood masks;
- administrative boundaries, population, roads, health facilities, cattle, cropland, rangeland, GDP, and
  food-insecurity data;
- spatial subsetting by coordinate or bounding box; and
- converting selected raw inputs into pandas, GeoPandas, Xarray, or NetworkX objects.

This is not yet an end-to-end flood model or a complete reproducible analysis pipeline. The two Python files contain 
loader functions and executable demonstrations.

## Repository structure

```text
JBG060-2026/
|-- processing_data/
|   |-- loading.py                 # Hydrometeorological data loaders
|   `-- loading_impact_data.py     # Exposure and impact data loaders
|-- prediction/                    # Flood forecasting pipeline (Stage 1 + 2); see prediction/README.md
|-- literature/                    # Supporting papers and data documentation
|-- raw_data/                      # External download; ignored by Git
|-- requirements.txt               # Pinned Python dependencies
|-- .gitignore
`-- README.md
```

Running the evapotranspiration processor creates `processing_data/evapotranspiration/`. 
Both that generated directory and `raw_data/` are excluded from Git.

## Requirements and installation

- Git
- Python 3.12 or newer

All Python dependencies and their versions are listed in [`requirements.txt`](requirements.txt).

### 1. Fork and clone the repository

First, open the [course repository](https://github.com/eerandi/JBG060_ZHL_2026) on GitHub. Select **Fork** in the
top-right corner, choose your GitHub account as the owner, and create the fork. This gives you your own copy of the
course repository where you can commit and push your work.

Then clone **your fork** (replace `YOUR_GITHUB_USERNAME` with your GitHub username):

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/JBG060_ZHL_2026.git
cd JBG060_ZHL_2026
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Conda can be used instead:

```bash
conda create -n jbg060 "python>=3.12"
conda activate jbg060
python -m pip install -r requirements.txt
```

## External data setup

The data is deliberately **not stored in this Git repository**. Download it separately from SURFdrive. The SURFdrive link and Password is shared in the description of the assignment on Canvas.

Put the downloaded data in the `raw_data` folder.

The administrative-boundary loader expects the level 1 and level 2 GeoJSON files at:

```text
raw_data/
`-- Administrative boundaries/
    |-- ssd_admin1.geojson
    `-- ssd_admin2.geojson
```

These files must be present whenever `processing_data.loading_impact_data` is imported because the module loads the
administrative boundaries at import time.

An overview of the supplied datasets and files is available in `Data_overview.xlsx`.

## Usage and examples

Run Python from the repository root. The code uses relative paths such as `./raw_data/...`; running from 
another directory will cause file-not-found errors.

### Recommended: call only the functions needed

This example loads one year of flood masks for a bounding box and estimates the population within the same area:

```python
import numpy as np

from processing_data.loading import load_flood_masks
from processing_data.loading_impact_data import load_worldpop_area

bbox = {
    "lat_min": 8.5,
    "lat_max": 10.0,
    "lon_min": 29.5,
    "lon_max": 32.5,
}

flood_events = load_flood_masks(np.array([2024]), bbox=bbox)
population_by_year = load_worldpop_area(bbox)

print(flood_events.head())
print(population_by_year[2024])
```

To process reference evapotranspiration for one year and grid location:

```python
from processing_data.loading import process_ET

process_ET(
    year=2024,
    target_longitude=30.725,
    target_latitude=9.475,
)
```

This writes:

```text
processing_data/evapotranspiration/ET_2024_9.475N_30.725E_processed.csv
```

Most other functions return their results in memory and do not write files.

To load South Sudan's administrative polygons and identify the state and county containing a coordinate:

```python
from processing_data.loading_impact_data import (
    load_admin_boundaries,
    locate_coordinate,
)

admin1, admin2 = load_admin_boundaries()
admin1_name, admin2_name = locate_coordinate(long=27.386, lat=8.771)

print(f"Loaded {len(admin1)} admin-level 1 and {len(admin2)} admin-level 2 areas")
print(admin1_name, admin2_name)
```

Coordinates must be supplied as longitude followed by latitude. If a coordinate is not contained in a South Sudan
polygon, the corresponding administrative name is returned as the string `"None"` and a warning is printed.

### Full demonstration scripts

The modules also contain hard-coded examples and do not accept command-line options:

```bash
python processing_data/loading.py
python processing_data/loading_impact_data.py
```

These commands run the full demonstrations:

- `loading.py` works across 2000-2025, loads large NetCDF and Parquet datasets, and may process approximately 
9,500 daily evapotranspiration files into annual CSV files.
- `loading_impact_data.py` loads the administrative boundaries, demonstrates two coordinate lookups, runs every
impact-data example, requests a road network from OpenStreetMap, and opens interactive plots.
- The OpenStreetMap step needs an internet connection. Prefer the individual functions when working headlessly 
or with limited time or memory.

## Function and data reference

### Hydrometeorological data: `processing_data/loading.py`

| Function | Main input | Return value or generated output |
|---|---|---|
| `load_dartmouth_data()` | Station metadata and discharge CSV files | Dictionary of discharge DataFrames keyed by area ID |
| `load_lake_stations()` | Albert NetCDF and Kyoga/Victoria text files | Dictionary of lake-level DataFrames |
| `load_rainfall_runoff(years)` | Annual ERA5 NetCDF files | Daily Xarray Dataset containing precipitation (`tp`) and runoff (`ro`) |
| `process_ET(year, target_longitude, target_latitude)` | Daily AgERA5 NetCDF files | One processed annual CSV for the nearest grid cell |
| `load_processed_ET(years, ...)` | Processed annual ET CSV files | Dictionary of DataFrames keyed by year |
| `load_flood_masks(years, bbox=None)` | Recurring and unusual flood Parquet files | DataFrame with `date`, `lat`, `lon`, `tile`, and `flood_type` |
| `flood_mask_bbox(df, bbox)` | Flood DataFrame and coordinate limits | Spatially filtered DataFrame |

In flood-mask results, `flood_type == 0` denotes recurring flooding and `flood_type == 1` denotes unusual flooding. 
If both classes occur for the same date and pixel, the unusual class takes priority.

### Exposure and impact data: `processing_data/loading_impact_data.py`

| Function | Main input | Return value or generated output |
|---|---|---|
| `load_admin_boundaries()` | Admin-level 1 and 2 GeoJSON files | Two GeoDataFrames containing states and counties |
| `locate_coordinate(long, lat)` | Longitude and latitude in decimal degrees | Admin-level 1 and 2 names containing the coordinate |
| `load_worldpop_coordinate(longitude, latitude)` | WorldPop rasters for 2015-2025 | Population value by year at the selected pixel |
| `load_worldpop_area(bbox)` | WorldPop rasters for 2015-2025 | Total population by year inside the bounding box |
| `download_OSM_network(name)` | OpenStreetMap place name and live internet connection | NetworkX road graph; also attempts to save and plot nodes and edges |
| `plot_network(name)` | Existing OSM node and edge shapefiles | NetworkX graph and two GeoDataFrames; also plots the graph |
| `load_health_facilities()` | Sub-Saharan health-facility GeoJSON | South Sudan facilities as a GeoDataFrame |
| `load_cattle()` | Cattle raster | DataFrame plus longitude and latitude arrays |
| `load_farmland_mask(bbox, mask_type)` | Crop or rangeland raster | Spatially subset Xarray DataArray |
| `load_GDP()` | World Bank indicator CSV | GDP values for 2008-2015 keyed by year |
| `load_ipc_data()` | IPC Excel workbooks | County-level IPC Phase 3+ population table |

`mask_type` must be either `"crop"` or `"rangeland"`. Bounding boxes use decimal degrees and require the keys 
`lat_min`, `lat_max`, `lon_min`, and `lon_max`.

## Generated outputs

- `process_ET()` creates annual CSV files in `processing_data/evapotranspiration/`.
- `download_OSM_network()` is intended to create node and edge shapefiles in `raw_data/OSM/<place>/`.
- Plotting functions display figures but do not save image files.
- All other loader functions return Python objects in memory.

Generated ET files, downloaded data, cached files, virtual environments, and Python bytecode should not be committed.

## Credits and acknowledgements

Dataset descriptions, file overviews, provenance, and original provider information are documented in `Data_overview.xlsx`. 
Consult the original providers for licenses, citation instructions, and usage restrictions.

### Literature

- Alfieri, L., Libertino, A., Campo, L., Dottori, F., Gabellani, S., Ghizzoni, T., Masoero, A., Rossi, L., Rudari, R.,
  Testa, N., Trasforini, E., Amdihun, A., Ouma, J., Rossi, L., Tramblay, Y., Wu, H., & Massabò, M. (2024).
  Impact-based flood forecasting in the Greater Horn of Africa. *Natural Hazards and Earth System Sciences, 24*,
  199–224. [PDF](<literature/Impact-based flood forecasting in the Greater Horn of Africa.pdf>)
- Slayback, D. (2025). *MODIS/VIIRS NRT global flood products: User guide* (Rev. F). NASA Goddard Space Flight
  Center. [PDF](literature/MCDWD_VCDWD_UserGuide_RevF.pdf) | [NASA Earthdata](https://www.earthdata.nasa.gov/data/instruments/viirs/near-real-time-data/nrt-global-flood-products)
- Petricola, S., Reinmuth, M., Lautenbach, S., Hatfield, C., & Zipf, A. (2022). Assessing road criticality and loss
  of healthcare accessibility during floods: The case of Cyclone Idai, Mozambique 2019. *International Journal of
  Health Geographics, 21*, Article 14. [PDF](<literature/Assessing road crticality and loss of healthcare acessibility during floods.pdf>) |
  [DOI](https://doi.org/10.1186/s12942-022-00315-2)
- Pacetti, T., Caporali, E., & Rulli, M. C. (2017). Floods and food security: A method to estimate the effect of
  inundation on crops availability. *Advances in Water Resources, 110*, 494–504.
  [PDF](<literature/Floods and food insecurity - A method to estimate the effect of inundation on crops availability.pdf>) |
  [DOI](https://doi.org/10.1016/j.advwatres.2017.06.019)

Supporting papers and data manuals are retained in [`literature/`](literature/). The project relies on pandas, NumPy, Xarray,
Dask, GeoPandas, Shapely, Rasterio, rioxarray, NetworkX, OSMnx, and Matplotlib; see [`requirements.txt`](requirements.txt)
for the complete version-pinned environment.

## Legal and ethical considerations

- The repository is intended for educational and research use. It has not been validated for emergency response, 
resource allocation, or other operational humanitarian decisions.
- Flood detections and the `flood_type` label are data-product classifications, not direct measures of damage, 
severity, or individual exposure.
- Respect each data provider's license, attribution, access, and redistribution conditions. Access through SURFdrive 
does not replace the original provider's terms.
