"""
Step 8 - Our cropland map from the frozen rules (METHODOLOGY.md section 6.5).

Applies a rules JSON to the 2025 features in Earth Engine and saves:
  - one asset per study area at 10 m (cropland/<rules>_<area>);
  - the whole country at 30 m (cropland/<rules>_south_sudan).
Before exporting, it checks that the Earth Engine map gives exactly the same
label as the Python rules at every calibration point.

Run from group_repo: python cropland/08_run_map.py cropland/rule1_2026-10-14.json
Follow the exports at https://code.earthengine.google.com/tasks
"""

import sys
from pathlib import Path

import pandas as pd

import common as C
import features as F
import rules as R


def check_same(ee, ruleset):
    s = pd.read_csv(C.HERE / "sample.csv")
    feats = pd.read_csv(C.HERE / "features_sample.csv")
    cal = s[s.split == "calibration"].merge(feats, on="id")
    py = R.predict(ruleset, cal)
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(r.lon, r.lat), {"id": r.id}) for r in cal.itertuples()])
    img = R.to_ee(ee, ruleset, F.feature_image(ee, fc.geometry().buffer(2000)))
    got = {f["properties"]["id"]: f["properties"].get("crop")
           for f in img.reduceRegions(fc, ee.Reducer.first().setOutputs(["crop"]), scale=10).getInfo()["features"]}
    diff = [(i, p, got[i]) for i, p in zip(cal.id, py) if got[i] != p]
    if diff:
        raise SystemExit(f"Earth Engine map differs from the Python rules at {len(diff)} points: {diff[:5]}")
    print(f"map = rules at all {len(cal)} calibration points")


def main() -> None:
    path = Path(sys.argv[1])
    ruleset = R.load(path)
    ee = C.ee_init()
    check_same(ee, ruleset)
    jobs = [(a, C.area_geometry(ee, a), 10) for a in C.AREAS] + [("south_sudan", C.country_geometry(ee), 30)]
    for name, geom, scale in jobs:
        img = R.to_ee(ee, ruleset, F.feature_image(ee, geom)).clip(geom)
        asset = f"{C.ASSETS}/{path.stem}_{name}"
        task = ee.batch.Export.image.toAsset(image=img, description=f"{path.stem}_{name}", assetId=asset,
                                             region=geom, scale=scale, maxPixels=1e13)
        task.start()
        print(f"started {asset} at {scale} m (task {task.id})")


if __name__ == "__main__":
    main()
