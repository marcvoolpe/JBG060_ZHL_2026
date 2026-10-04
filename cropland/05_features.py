"""
Step 5 - Machine features at the labelled points (METHODOLOGY.md section 5).

Writes cropland/features_<set>.csv with one row per point and one column per
feature in features.FEATURES. Also writes the 64-band Google Satellite
Embedding for 2025 at the same points (embedding_<set>.csv), used only for the
black-box benchmark. Both describe the 210 m box around the point (the unit
labellers label): features are box summaries (features.py), the embedding is
the mean over the box.

Run from group_repo: python cropland/05_features.py pilot   (or: sample)
"""

import sys

import pandas as pd

import common as C
import features as F


def embedding(ee, df):
    emb = (ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
           .filterDate(f"{C.YEAR}-01-01", f"{C.YEAR + 1}-01-01").mosaic())
    fc = ee.FeatureCollection([ee.Feature(C.box(ee, r.lon, r.lat), {"id": r.id}) for r in df.itertuples()])
    got = emb.reduceRegions(fc, ee.Reducer.mean(), scale=10).getInfo()
    return pd.DataFrame([f["properties"] for f in got["features"]])


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    pts = pd.read_csv(C.HERE / ("pilot_points.csv" if which == "pilot" else "sample.csv"))
    ee = C.ee_init()
    feats = F.sample_points(ee, pts)
    missing = feats[F.FEATURES].isna().sum()
    feats.to_csv(C.HERE / f"features_{which}.csv", index=False)
    embedding(ee, pts).to_csv(C.HERE / f"embedding_{which}.csv", index=False)
    print(f"{len(feats)} points; missing values per feature:\n{missing[missing > 0].to_string() or 'none'}")
    print(feats[F.FEATURES].describe().T[["mean", "min", "max"]].round(3).to_string())


if __name__ == "__main__":
    main()
