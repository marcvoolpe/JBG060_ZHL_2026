"""
Step 5 - one table of every driver, one row per dekad.

"Drivers" are the things upstream that could tell us about flooding in the
corridor before it happens:

  lake levels   Victoria, Kyoga, Albert (satellite altimetry, metres).
                Lake Victoria feeds the White Nile; water leaving it takes
                roughly 9-17 months to reach the Sudd (HESS 2026). So a high
                lake today is a strong hint about floods next year, long
                before local rain says anything.
  DMI           Dipole Mode Index: the Indian Ocean temperature see-saw
                that drives East African short-rains. Monthly, so all three
                dekads of a month get the same value.
  ERA5          rainfall and runoff per region (from step 4).
  flood volume  how many domain pixels were flooded that dekad - the thing
                Stage 1 predicts, and also a feature (today's flood extent
                is the best single clue about next dekad's).

This table holds RAW values only. Anomalies, z-scores and seasonal averages
are computed later, inside each fold, from that fold's training years only
(06_stage1_volume.py). Computing them here, over the whole record, would let
the test years leak into training.

Rows start in 1998, two years before the flood record, so lake features can
look back up to 18 months from the first forecasts. Those early rows have
no flood volume and no ERA5 (NaN); their t index is negative.

Gaps: lake altimetry passes are roughly every 10 days but irregular. A dekad
with no pass takes the last known level, for at most MAX_FILL dekads; beyond
that it stays empty. We fill FORWARD ONLY - filling backward would copy a
future measurement into the past.
Lake Albert's record only starts in July 2002, so its early rows are empty.

Output: raw_data/prediction/driver_table.csv
~1 min.

Run: /usr/bin/python3 prediction/05_driver_table.py
"""

import contextlib
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common as C  # noqa: E402
from processing_data.loading import load_lake_stations  # noqa: E402

FIRST_YEAR = 1998
MAX_FILL = 6          # dekads (2 months) a lake level may be carried forward


def parse_dmi(path: Path) -> pd.Series:
    """NOAA PSL format: a header line, then 'year v1 .. v12' rows, then
    trailing notes. -99.99 marks missing. Returns a monthly series."""
    values = {}
    for line in path.read_text().splitlines()[1:]:
        parts = line.split()
        if len(parts) != 13 or not parts[0].isdigit():
            continue
        year = int(parts[0])
        for month, raw in enumerate(parts[1:], start=1):
            v = float(raw)
            values[(year, month)] = np.nan if v <= -99 else v
    return pd.Series(values)


def lake_dekadal(series: pd.Series, index: pd.Index) -> pd.Series:
    """Irregular altimetry passes -> mean level per dekad, forward-filled."""
    dates = pd.DatetimeIndex(series.index).normalize()   # Albert stamps carry a time of day
    t = C.t_index(dates.year, C.dekad_of_year(dates))
    per_dekad = pd.Series(series.to_numpy(dtype=float), index=t).dropna().groupby(level=0).mean()
    return per_dekad.reindex(index).ffill(limit=MAX_FILL)


def flood_volume(index: pd.Index) -> pd.DataFrame:
    """Flooded domain pixels per dekad, total and by NASA type. Dekads with
    no row in dekadal_labels had no flood at all, so they get 0 - not NaN."""
    lab = pd.read_parquet(C.OUT / "dekadal_labels.parquet", columns=["year", "dekad", "label"])
    lab["t"] = C.t_index(lab["year"].to_numpy(), lab["dekad"].to_numpy())
    counts = lab.groupby(["t", "label"]).size().unstack(fill_value=0)
    out = pd.DataFrame(index=index)
    in_record = (index >= 0) & (index < C.N_DEKADS)
    for name, labels in (("volume", [1, 2]), ("volume_recurring", [1]), ("volume_unusual", [2])):
        col = counts[[c for c in labels if c in counts.columns]].sum(axis=1)
        out[name] = np.where(in_record, col.reindex(index).fillna(0), np.nan)
    return out


def main() -> None:
    index = pd.Index(np.arange(C.t_index(FIRST_YEAR, 1), C.N_DEKADS), name="t")
    years, dekads = C.year_dekad(index.to_numpy())
    table = pd.DataFrame({"year": years, "dekad": dekads}, index=index)

    with C.repo_cwd(), contextlib.redirect_stdout(io.StringIO()):   # the loader prints a lot
        lakes = load_lake_stations()
    for name, key, col in (("victoria", "victoria", "height_egm2008"),
                           ("kyoga", "Kyoga", "height_egm2008"),
                           ("albert", "Albert", "water_level")):
        table[f"lake_{name}"] = lake_dekadal(lakes[key][col], index)

    dmi = parse_dmi(C.DMI_FILE)
    month = (table["dekad"] - 1) // 3 + 1
    table["dmi"] = [dmi.get((y, m), np.nan) for y, m in zip(table["year"], month)]

    era5 = pd.read_csv(C.OUT / "era5_regions_dekadal.csv", index_col="t").drop(columns=["year", "dekad"])
    table = table.join(era5)
    table = table.join(flood_volume(index))
    table.to_csv(C.OUT / "driver_table.csv")

    rec = table.loc[0:]
    print(f"{len(table)} rows ({FIRST_YEAR}-{C.YEAR1}); {len(rec)} inside the flood record")
    print("missing values inside 2000-2025, per column:")
    print(rec.isna().sum()[rec.isna().sum() > 0].to_string() or "  none")
    print("\nsanity - mean Lake Victoria level by year (should jump ~1 m in 2020):")
    print(rec.groupby("year")["lake_victoria"].mean().loc[2017:2022].round(2).to_string())
    print("\nflood volume by year (flooded pixel-dekads; should jump ~16x after 2019):")
    print(rec.groupby("year")["volume"].sum().astype(int).to_string())


if __name__ == "__main__":
    main()
