"""
Checks for the cropland pipeline.

Fast (no Earth Engine):
  - the area estimator returns the true share when every stratum has it;
  - accuracy in one stratum equals the plain confusion-matrix values;
  - a decision tree turned into rules predicts exactly like the tree.
Slow (needs Earth Engine, run with --ee):
  - the Earth Engine map from a rules file gives the same label as the Python
    rules at the pilot points;
  - distance to buildings at a pilot point matches the distance to the
    nearest Open Buildings polygon (within 15 m).

Run from group_repo: python cropland/test_cropland.py [--ee]
"""

import sys

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

import common as C
import estimators as E
import features as F
import rules as R


def test_area():
    strata = np.array(list("A" * 50 + "B" * 50))
    ref = np.array([1] * 10 + [0] * 40 + [1] * 10 + [0] * 40, float)       # 20% in both strata
    est, se = E.area(ref, strata, {"A": 0.9, "B": 0.1})
    assert abs(est - 0.2) < 1e-12 and se > 0


def test_accuracy_one_stratum():
    m = np.array([1, 1, 1, 0, 0, 0, 0, 1])
    r = np.array([1, 1, 0, 0, 0, 1, 0, 1])
    a = E.accuracy(m, r, np.array(["A"] * 8), {"A": 1.0}, n_boot=50)
    assert abs(a["ua"] - 3 / 4) < 1e-12 and abs(a["pa"] - 3 / 4) < 1e-12 and abs(a["oa"] - 6 / 8) < 1e-12


def fake_ruleset():
    d = pd.read_csv(C.HERE / "features_pilot.csv")
    y = (d.drop_vs_500m > d.drop_vs_500m.median()).astype(int)            # made-up labels, test only
    fill = {f: float(d[f].median()) for f in F.FEATURES}
    X = d[F.FEATURES].fillna(fill).to_numpy()
    tree = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, y)
    return d, tree, X, R.from_tree(tree, F.FEATURES, fill, "test")


def test_tree_equals_rules():
    d, tree, X, rs = fake_ruleset()
    assert (tree.predict(X) == R.predict(rs, d)).all()


def test_ee_equals_python():
    ee = C.ee_init()
    _, _, _, rs = fake_ruleset()
    pts = pd.read_csv(C.HERE / "pilot_points.csv")
    feats = pd.read_csv(C.HERE / "features_pilot.csv")
    py = R.predict(rs, pts.merge(feats, on="id"))
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(r.lon, r.lat), {"id": r.id}) for r in pts.itertuples()])
    img = R.to_ee(ee, rs, F.feature_image(ee, fc.geometry().buffer(2000)))
    got = {f["properties"]["id"]: f["properties"].get("crop")
           for f in img.reduceRegions(fc, ee.Reducer.first().setOutputs(["crop"]), scale=10).getInfo()["features"]}
    bad = [i for i, p in zip(pts.id, py) if got[i] != p]
    assert not bad, f"Earth Engine and Python differ at {bad}"


def test_building_distance():
    ee = C.ee_init()
    p = pd.read_csv(C.HERE / "pilot_points.csv").iloc[0]
    pt = ee.Geometry.Point(float(p.lon), float(p.lat))
    ob = ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons").filterBounds(pt.buffer(2500))
    true = ob.map(lambda f: f.set("d", f.geometry().distance(pt))).aggregate_min("d").getInfo()
    img = F.feature_image(ee, pt.buffer(2000)).select("dist_buildings_m")
    got = img.reduceRegion(ee.Reducer.first(), pt, 10).getInfo()["dist_buildings_m"]
    assert abs(got - true) <= 15, f"feature {got:.0f} m, nearest building {true:.0f} m"


if __name__ == "__main__":
    tests = [test_area, test_accuracy_one_stratum, test_tree_equals_rules]
    if "--ee" in sys.argv:
        tests += [test_ee_equals_python, test_building_distance]
    for t in tests:
        t()
        print("ok  ", t.__name__)
