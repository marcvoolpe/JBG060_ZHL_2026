from pathlib import Path

import pandas as pd

from processing_data.loading import load_dartmouth_data


RAW_DIR = Path("raw_data/Darthmouth Flood Observatory")
OUT_DIR = Path("processed-data/Darthmouth Flood Observatory")
OUT_FILE = OUT_DIR / "dartmouth_discharge_all_processed_with_station_info.csv"


def load_station_information() -> pd.DataFrame:
    info = pd.read_excel(RAW_DIR / "information.xlsx")
    info = info.rename(
        columns={
            "station nr": "station_nr",
            "area id": "area_id",
            "Country": "country",
        }
    )

    return (
        info.groupby("area_id", as_index=False)
        .agg(
            station_nr=("station_nr", "first"),
            country=("country", lambda s: "; ".join(pd.unique(s.dropna().astype(str)))),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            metadata_rows=("area_id", "size"),
        )
        .assign(
            has_country_conflict=lambda df: df["country"].str.contains(";", regex=False)
        )
    )


def process_dartmouth_data() -> pd.DataFrame:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    station_data = load_dartmouth_data()
    station_info = load_station_information()

    combined = pd.concat(station_data, names=["area_id", "Date"]).reset_index()
    combined["Date"] = pd.to_datetime(combined["Date"])

    merged = combined.merge(
        station_info,
        on="area_id",
        how="left",
        validate="many_to_one",
    )
    merged = merged[
        [
            "area_id",
            "station_nr",
            "country",
            "latitude",
            "longitude",
            "Date",
            "Discharge (m3/s)",
            "metadata_rows",
            "has_country_conflict",
        ]
    ].sort_values(["area_id", "Date"])

    merged.to_csv(OUT_FILE, index=False)
    return merged


def main() -> None:
    df = process_dartmouth_data()
    print(f"Saved {OUT_FILE}")
    print(f"Rows: {len(df)}, columns: {len(df.columns)}")
    print(df.groupby("area_id").size().to_string())


if __name__ == "__main__":
    main()
