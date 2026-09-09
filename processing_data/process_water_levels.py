from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from processing_data.loading import load_lake_stations


RAW_DIR = Path("raw_data/Water levels lakes")
OUT_DIR = Path("processed-data/Water levels lakes")
OUT_FILE = OUT_DIR / "water_levels_all_processed.csv"


def read_txt_target_metadata(path: Path) -> dict:
    lines = path.read_text(encoding="latin-1").splitlines()[:4]
    target_line = lines[1].split(":", 1)[0].strip()
    coord_parts = lines[2].split(":", 1)[0].split()
    tokens = target_line.split()

    return {
        "target_id": tokens[0],
        "target_name": " ".join(tokens[1:]),
        "target_latitude": float(coord_parts[0]),
        "target_longitude": float(coord_parts[1]),
    }


def build_lake_metadata() -> dict:
    metadata = {
        "victoria": {
            **read_txt_target_metadata(RAW_DIR / "water_level_victoria.txt"),
            "country": "Uganda",
            "source_file": "water_level_victoria.txt",
        },
        "Kyoga": {
            **read_txt_target_metadata(RAW_DIR / "water_level_Kyoga.txt"),
            "country": "Uganda",
            "source_file": "water_level_Kyoga.txt",
        },
    }

    with xr.open_dataset(RAW_DIR / "water_level_altimetry_Albert.nc") as ds:
        metadata["Albert"] = {
            "target_id": str(ds.attrs.get("dahiti_id", "")),
            "target_name": ds.attrs.get("target_name", "Albert, Lake"),
            "target_latitude": float(ds.attrs.get("latitude", np.nan)),
            "target_longitude": float(ds.attrs.get("longitude", np.nan)),
            "country": ds.attrs.get("country", "Democratic Republic of the Congo"),
            "source_file": "water_level_altimetry_Albert.nc",
        }

    return metadata


def process_water_levels() -> pd.DataFrame:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    metadata = build_lake_metadata()
    lake_data = load_lake_stations()
    frames = []

    for lake_name, df in lake_data.items():
        lake_df = df.reset_index().copy()
        if "datetime" in lake_df.columns:
            lake_df["datetime"] = pd.to_datetime(lake_df["datetime"])
            water_level = lake_df["water_level"]
            water_level_error = lake_df["error"]
            water_level_datum = "DAHITI product datum"
        else:
            lake_df["datetime"] = (
                pd.to_datetime(lake_df["date"])
                + pd.to_timedelta(lake_df["hour"], unit="h")
                + pd.to_timedelta(lake_df["minute"], unit="m")
            )
            water_level = lake_df["height_egm2008"]
            water_level_error = lake_df["height_err"]
            water_level_datum = "EGM2008 mean sea level"

        meta = metadata[lake_name]
        lake_label = lake_name.capitalize() if lake_name.lower() == "victoria" else lake_name
        frames.append(
            pd.DataFrame(
                {
                    "lake": lake_label,
                    "country": meta["country"],
                    "datetime": lake_df["datetime"],
                    "date": lake_df["datetime"].dt.date,
                    "target_latitude": meta["target_latitude"],
                    "target_longitude": meta["target_longitude"],
                    "water_level_m": water_level,
                    "water_level_error_m": water_level_error,
                    "water_level_datum": water_level_datum,
                    "source_file": meta["source_file"],
                }
            )
        )

    combined = (
        pd.concat(frames, ignore_index=True)
        .sort_values(["lake", "datetime"])
        .reset_index(drop=True)
    )
    combined.to_csv(OUT_FILE, index=False)
    return combined


def main() -> None:
    df = process_water_levels()
    print(f"Saved {OUT_FILE}")
    print(f"Rows: {len(df)}, columns: {len(df.columns)}")
    print(
        df.groupby(["lake", "country"])
        .agg(rows=("lake", "size"), start=("datetime", "min"), end=("datetime", "max"))
        .to_string()
    )


if __name__ == "__main__":
    main()
