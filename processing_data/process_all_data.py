from processing_data.process_dartmouth import process_dartmouth_data
from processing_data.process_remaining_raw_data import process_remaining_raw_data
from processing_data.process_water_levels import process_water_levels


def main() -> None:
    outputs = []

    process_dartmouth_data()
    outputs.append("processed-data/Darthmouth Flood Observatory/dartmouth_discharge_all_processed_with_station_info.csv")

    process_water_levels()
    outputs.append("processed-data/Water levels lakes/water_levels_all_processed.csv")

    outputs.extend(str(path) for path in process_remaining_raw_data(include_slow=True))

    print("All processing complete.")
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
