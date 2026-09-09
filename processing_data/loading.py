import pandas as pd
import xarray as xr
import io
import numpy as np
from pathlib import Path
from tqdm import tqdm

#### NOTE: FIRST DOWNLOAD THE RAW DATA FROM SURFDRIVE


def load_dartmouth_data() -> dict[int, pd.DataFrame]:
    """
    Returns a dictionary with for each station, referenced by the area id, the discharge over time.

    Also, this function loads the information Excel file, which provides for each station:
    - area id
    - station number
    - country
    - latitude
    - longitude   

    This data is downloaded from: https://floodobservatory.colorado.edu
    """
    base_path: str = './raw_data/Darthmouth Flood Observatory'
    data_info = pd.read_excel(base_path + '/information.xlsx')

    print("Information regarding each station:")
    print(data_info.head())

    area_ids = data_info['area id'].values

    # Create a dictionary with all stations data
    data = {}
    for area_id in area_ids:
        df = pd.read_csv(f'{base_path}/{area_id}_discharge.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date', drop=True).sort_index()
        data[area_id] = df

    print("Per station, we know:")
    print(data[area_ids[0]].head())

    return data


def load_lake_stations() -> dict[int, pd.DataFrame]:
    """
    Returns a dictionary with for each lake, referenced by name, the relative water level over time.

    The txt file of Kyoga and Victoria provides information of the content of this data, as well as
    the coordinates of the lakes.
    
    Attributes of lake Albert are stored in the attribute dictionary.

    The data is downloaded from:
    - Lake Albert : https://dahiti.dgfi.tum.de/85/
    - Lakes Victoria and Kyoga : https://hydroweb.next.theia-land.fr/
    """
    lake_names = ['victoria', 'Kyoga', 'Albert']
    base_path: str = './raw_data/Water levels lakes'

    # Create a dictionary with all stations data
    data = {}
    for name in lake_names:
        print("Loading lake data for: ", name)

        # Process the .nc file for Lake Albert as a dataframe
        if name == "Albert":
            ds = xr.open_dataset(f'{base_path}/water_level_altimetry_{name}.nc')
            albert_attributes = ds.attrs
            print("Attributes of Lake Albert Data:")
            for key,value in albert_attributes.items():
                print(f"{key} : {value}")
            print("")
                
            df = ds.to_dataframe().reset_index(drop=True)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime', drop = True).sort_index()

            print(df.head())

        # Process the .txt files for the other lakes as a dataframe
        else:
            fname = f'{base_path}/water_level_{name}.txt'
            # hydroweb txt uses JASN* / SEN6A; without them the series stops ~2002
            mission_names = {
                'TOPEX', 'JASON-1', 'JASON-2', 'JASON-3', 'J1', 'J2', 'J3',
                'JASN1', 'JASN2', 'JASN3', 'SEN6A', 'S6A',
                'S3A', 'S3B', 'ENVISAT', 'ERS-1', 'ERS-2',
            }

            # Names for the unnamed columns based on the column descriptions
            col_names = [
                'mission', 'cycle', 'date', 'hour', 'minute',
                'height_wrt_ref', 'height_err', 'backscatter_ku',
                'wet_tropo_corr', 'iono_corr', 'dry_tropo_corr',
                'mode1', 'mode2', 'ice_flag', 'height_egm2008', 'data_source_flag'
            ]

            # Add lines from specific missions to the dataset
            data_lines = []
            with open(fname, 'r', encoding='latin-1') as f:
                for line in f:
                    first_token = line.strip().split()[0] if line.strip() else ''
                    if first_token in mission_names:
                        data_lines.append(line.strip())

            # Convert to a dataframe and set date as the index
            df = pd.read_csv(
                io.StringIO('\n'.join(data_lines)),
                sep=r'\s+',
                names=col_names,
                na_values=['999.99', '99.999', '9999.99']
            )
            df = df.dropna()    
            df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d')
            df = df.set_index('date', drop = True).sort_index()
            
            print(df.head())        
                    
        data[name] = df
    return data


def load_rainfall_runoff(years: np.ndarray) -> xr.Dataset:
    """
    Loads and aggregates the rainfall and runoff data in the Nile Basin to a daily resolution.

    Data downloaded from : https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview

    Returns a xr.Dataset with dimensions 
    - valid_time: each day in the years provided as input (data provided for 2000-2025)
    - latitude: 145, 
    - longitude: 57, 
    covering the Nile Basin at 0.25° resolution

    Variables:
    - tp : float32 (valid_time, latitude, longitude). This represents the total precipitation per day[m/day].
    - ro : float32 (valid_time, latitude, longitude). This represents the total runoff per day[m/day].
    
    Coordinates:
    - valid_time : datetime64[ns]. Daily timestamps, one per calendar day.
    - latitude : float64. Latitude in degrees North (33.0 to -3.0, step -0.25).
    - longitude : float64. Longitude in degrees East (23.0 to 37.0, step 0.25).
    """
    variables = ['tp', 'ro']
    base_path: str = './raw_data/rainfall and runoff'

    # Load datasets with chunking to fit into memory
    datasets = []
    for year in years:
        ds = xr.open_dataset(f'{base_path}/ERA5_{year}.nc')
        ds = ds.chunk({"valid_time": 500})
        datasets.append(ds[variables])  # keep as Dataset with both variables

    # Concatenate all the data into one dataframe
    ds_all = xr.concat(datasets, dim='valid_time')
    ds_daily = ds_all.resample(valid_time='1D').sum()
    ds_daily = ds_daily.sortby('valid_time')

    # Get start and end date of the data collection
    t0 = pd.Timestamp(ds_daily.valid_time.values[0]).strftime('%Y-%m-%d')
    t1 = pd.Timestamp(ds_daily.valid_time.values[-1]).strftime('%Y-%m-%d')
    print(f"Daily total precipitation and runoff from ERA5 reanalysis loaded from dates {t0} to {t1}")
    print(ds_daily)

    return ds_daily


def process_ET(year:int, target_longitude: float = 30.725, target_latitude: float = 9.475) -> None:
    """
    Loads and processes AgERA5 reference evapotranspiration data for a single year to daily resolution.
    Data downloaded from: https://cds.climate.copernicus.eu/datasets/sis-agrometeorological-indicators?tab=overview
    Definition variable:
        "Calculated using the Penman-Monteith method as described by the FAO56 guidelines,
        it represents the rate at which a well-watered reference crop loses water to the atmosphere 
        through evapotranspiration and transpiration."

    Reads one .nc file per calendar day, extracts the evapotranspiration on that day at the target coordinate provided, 
    and saves the result to
        processing_data/evapotranspiration/ET_{year}_{target_lat}N_{target_lon}E_processed.csv 
    
    The evapotranspiration data is provided for the years 2000-2025 in the Nile basin.

    Variable written to CSV:
    - gridcell  : float64. Daily reference ET at the nearest gridpoint to the target
                    longitude and latitude provided [mm/day].

    Coordinates:
    - date      : datetime64. Daily timestamps, one per calendar day for the requested year.
    - latitude  : float64. Latitude in degrees North (33.0 to -3.0, step -0.1°).
    - longitude : float64. Longitude in degrees East (23.0 to 37.0, step -0.1°).
    """
     
    ET_dir = Path(f'./raw_data/evapotranspiration/ET_{year}')
    out_dir = Path(f'./processing_data/evapotranspiration')
    out_dir.mkdir(parents=True, exist_ok=True)
    variable = 'ReferenceET_PenmanMonteith_FAO56'

    # Check if file already exists or if year is not present
    lat_str = f"{target_latitude:.3f}N"
    lon_str = f"{target_longitude:.3f}E"
    out_path = out_dir / f'ET_{year}_{lat_str}_{lon_str}_processed.csv'

    daily_files = sorted(ET_dir.glob(f'*{year}*.nc'))

    # Condition to skip processing or warn for a missing data file
    if out_path.exists():
        print(f".nc file for year {year} already processed in {out_dir}")
        return
    elif len(daily_files) == 0:
        print(f"  WARNING: no .nc files found for year {year} in {ET_dir}")
        return

    # Processing steps
    records = []
    for f in daily_files:
        ds = xr.open_dataset(f)
        time_val = pd.Timestamp(ds['time'].values[0])
        da = ds[variable].squeeze()
        gridcell_val = float(
            da.sel(lat=target_latitude, lon=target_longitude, method='nearest').values
        )
        records.append({'date': time_val.date(), 'gridcell': gridcell_val})
        ds.close()

    # Create a dataframe and set date as the index
    df = pd.DataFrame(records).set_index('date')
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    # Save this file
    df.to_csv(out_path)

    print(f"Saved {len(df)} days to {out_path}")


def load_processed_ET(years: np.ndarray, target_longitude: float, target_latitude:  float) -> dict[int, pd.DataFrame]:
    """
    Loads the processed ET variables into a single dictionary, containing for each year a dataframe
    with the daily ET value at the given grid cell.
    """
    base_path = Path(f'./processing_data/evapotranspiration')
    lat_str = f"{target_latitude:.3f}N"
    lon_str = f"{target_longitude:.3f}E"

    # Create dictionary with all years and warn for processing gone wrong
    data = {}
    for year in years:
        try:
            df = pd.read_csv(f'{base_path}/ET_{year}_{lat_str}_{lon_str}_processed.csv')
            data[year] = df
        except:
            print(f"  WARNING: no processed .csv files found for year {year} in {base_path}")

    print(data[years[0]].head())
        
    return data


def load_flood_masks(years: np.array, bbox: dict = None) -> pd.DataFrame:
    """
    Loads the compact flood mask parquet files for all given years and both tiles (together spanning South Sudan),
    and merges the recurring and unusual flood events into a single DataFrame.

    For each (date, lat, lon) combination:
    - flood_type = 0 if recurring flood.
    - flood_type = 1 if unusual flood.
    If a pixel appears in both, unusual (1) takes priority.

    Data downloaded from:
    https://www.earthdata.nasa.gov/data/instruments/viirs/near-real-time-data/nrt-global-flood-products
    Specifically, we load post-processed 3-day flood mask MCDWD_L3_NRT data.

    The raw data is distributed in 10x10° tiles, the two tiles together span South Sudan.
    The tiles are 4800 x 4800 pixels, with pixel size of 0.0020833 degrees (~232 m at the equator). 
    It contains each location and day at which a recurring and unusual flood was detected, for the 3-day composite.

    This product sums over 3 days of data, and requires multiple water detections from all available observations 
    in the composite time window, to mark a pixel as water. This is done to minimize the impact of cloud and
    terrain shadows that are often also detected as water due to their spectral similarities.

    A flood is classified as recurrent if flood water has been detected at that location in at least roughly 1/3rd
    of the years for which data is available. Otherwise, it is classified as unusual.

    More information can be read in the user guide:
    https://www.earthdata.nasa.gov/s3fs-public/2025-12/MCDWD_VCDWD_UserGuide_RevF.pdf?VersionId=OzkHdTGLfEeQtOvKT1eti.b3Jhqa_oL2
    """
    # Load tiles in South Sudan
    tiles = ['h20v08', 'h21v08']
    base_path = f'./raw_data/flood_masks'
    
    recurring_parts = []
    unusual_parts   = []

    # Create lists of recurring and unusual floods from the parquet files
    for year in years:
        for tile in tiles:
            recurring_path = base_path + f'/compact_recurring/flood_events_{tile}_{year}.parquet'
            unusual_path = base_path + f'/compact_unusual/flood_events_{tile}_{year}.parquet'

            df = pd.read_parquet(recurring_path, engine='pyarrow', columns=['date', 'lat', 'lon', 'tile'])
            df['flood_type'] = 0
            recurring_parts.append(df)
            
            df = pd.read_parquet(unusual_path, engine='pyarrow', columns=['date', 'lat', 'lon', 'tile'])
            df['flood_type'] = 1
            unusual_parts.append(df)

    # Check that loading went smoothly
    all_parts = recurring_parts + unusual_parts
    if len(all_parts) == 0:
        print("No data found.")
        return pd.DataFrame()

    # Concatenate the lists and convert to dataframe
    combined = pd.concat(all_parts, ignore_index=True)
    combined['date'] = pd.to_datetime(combined['date'])

    # Where a pixel appears in both, unusual (1) takes priority
    combined = (
        combined
        .sort_values('flood_type', ascending=False)       # unusual first
        .drop_duplicates(subset=['date', 'lat', 'lon'])       # keep unusual if duplicate
        .sort_values(['date', 'lat', 'lon'])
        .reset_index(drop=True)
    )

    # If a bounding box is provided, filter according to it
    if bbox is not None:
        combined = flood_mask_bbox(combined, bbox)

    return combined


def flood_mask_bbox(df: pd.DataFrame, bbox: dict) -> pd.DataFrame:
    """
    Filter the flood mask data from to a given bounding box, in bbox.

    Parameters:
        - df : pd.DataFrame. This is the output of load_flood_masks().
        - bbox : dict with keys 'lat_min', 'lat_max', 'lon_min', 'lon_max'.

    Returns the flood records in the given bounding box.
    """
    mask = (
        (df['lat'] >= bbox['lat_min']) &
        (df['lat'] <= bbox['lat_max']) &
        (df['lon'] >= bbox['lon_min']) &
        (df['lon'] <= bbox['lon_max'])
    )
    return df[mask].reset_index(drop=True)



def main():
    ## Example usage of loading all data
    load_dartmouth_data()   ## Discharge stations in Nile basin
    load_lake_stations()    ## Lake water level data

    years = np.arange(2000, 2026)   ## 2000-2025
    load_rainfall_runoff(years)     ## Rainfall and runoff data from ERA5 reanalysis

    ## Evapotranspiration at a certain grid location:
    target_longitude    = 30.725
    target_latitude     = 9.475

    ## Process ET data if not done yet with a progress bar
    raw_dir = Path(f'./raw_data/evapotranspiration')
    processed_dir = Path(f'./processing_data/evapotranspiration')

    files_raw = list(raw_dir.glob("*"))
    files_processed = list(processed_dir.glob("*"))

    ## Check whether processing is needed
    if len(files_raw) != len(files_processed):
        print("Evaporation-transpiration data not processed yet - running processing")

        for year in tqdm(years):
            process_ET(year)
    else:
        print("Evaporation-transpiration data already processed - skipping processing")

    ## Then load the processed evaporation-transpiration data
    load_processed_ET(years, target_longitude, target_latitude)

    ## Flood masks at a bounding box:
    local_bbox = {'lat_min': 8.0, 'lat_max': 11.0, 'lon_min': 29.0, 'lon_max': 32.0}
    df_local = load_flood_masks(years, bbox=local_bbox)

    print(df_local.head())
    print(f"Flood events in bbox: {len(df_local)}")
    print(f"Recurring : {(df_local['flood_type'] == 0).sum()}")
    print(f"Unusual   : {(df_local['flood_type'] == 1).sum()}")


if __name__ == "__main__":
    main()