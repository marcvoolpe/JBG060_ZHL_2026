"""
Step 3 - daily detections -> one label per pixel per dekad.

A pixel counts as flooded in a dekad if it was detected as flooded on any
day of that dekad. Each flooded (pixel, dekad) keeps NASA's type:

  label 1 = recurring  (flood_type 0 in the raw data)
  label 2 = unusual    (flood_type 1)

If both occur in the same dekad, unusual wins, as in loading.py. This
happens in only ~0.004% of flooded pixel-dekads.

The model itself predicts only flooded / not flooded. The recurring vs
unusual label is kept so results can be reported separately for each type
(see 07_dense_arrays.py, class_map).

Dry pixel-dekads are not stored: absent means dry. That keeps the file at
~11 million rows instead of ~1 billion.

Output: raw_data/prediction/dekadal_labels.parquet (gx, gy, year, dekad, label)
~5 min.

Run: /usr/bin/python3 prediction/03_dekadal_labels.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def main() -> None:
    parts, both_total, total = [], 0, 0
    for f in sorted((C.OUT / "pixels_by_year").glob("corridor_pixels_*.parquet")):
        df = pd.read_parquet(f, columns=["date", "gx", "gy", "flood_type"])
        dates = pd.to_datetime(df["date"])
        df["year"] = dates.dt.year.to_numpy()
        df["dekad"] = C.dekad_of_year(dates)
        g = df.groupby(["gx", "gy", "year", "dekad"])["flood_type"].agg(["min", "max"]).reset_index()
        both = (g["min"] == 0) & (g["max"] == 1)
        g["label"] = np.where(g["max"] == 1, 2, 1).astype(np.int8)
        parts.append(g[["gx", "gy", "year", "dekad", "label"]])
        both_total += int(both.sum())
        total += len(g)
        print(f"{f.name}: {len(g):,} flooded pixel-dekads")

    labels = pd.concat(parts, ignore_index=True)
    labels.to_parquet(C.OUT / "dekadal_labels.parquet", index=False)
    print(f"total {total:,}; recurring and unusual in the same dekad: {both_total:,} ({both_total / total:.3%})")
    print(labels["label"].value_counts().rename({1: "recurring", 2: "unusual"}))


if __name__ == "__main__":
    main()
