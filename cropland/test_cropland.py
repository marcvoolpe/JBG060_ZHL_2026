"""
Checks for the cropland pipeline.

Fast (no Earth Engine):
  - the area estimator returns the true share when every stratum has it, also
    for box shares (fractions);
  - accuracy in one stratum equals the plain confusion-matrix values;
  - a decision tree turned into rules predicts exactly like the tree;
  - sample.csv: two different labellers per point, every pair shares the same
    number of points, every labeller has the same mix of area, stratum and split;
  - merging labels: agreed values only where both agree, the two-labeller mean
    everywhere, no tiebreak;
  - model_data.load never mixes calibration and test points.
Slow (needs Earth Engine, run with --ee):
  - the Earth Engine map from a rules file gives the same label as the Python
    rules at the pilot points;
  - distance to buildings at a pilot point matches the distance to the
    nearest Open Buildings polygon (within 15 m).

Run from group_repo: python cropland/test_cropland.py [--ee]
"""

import importlib
import sys
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

import common as C
import estimators as E
import features as F
import model_data as M
import rules as R

merge = importlib.import_module("06_merge_labels")
sampling = importlib.import_module("03_agreement_and_sample")
import label_server as server


def test_area():
    strata = np.array(list("A" * 50 + "B" * 50))
    ref = np.array([1] * 10 + [0] * 40 + [1] * 10 + [0] * 40, float)       # 20% in both strata
    est, se = E.area(ref, strata, {"A": 0.9, "B": 0.1})
    assert abs(est - 0.2) < 1e-12 and se > 0


def test_area_share():
    """Box shares (fractions): the mean share per stratum, weighted; 0/1 values give the old formula."""
    strata = np.array(list("A" * 4 + "B" * 4))
    ref = np.array([0, .05, .175, .375, 0, 0, .75, .75])
    est, se = E.area(ref, strata, {"A": 0.5, "B": 0.5})
    assert abs(est - (0.15 * 0.5 + 0.375 * 0.5)) < 1e-12 and se > 0
    y = np.array([1, 0, 0, 1, 1], float)
    est, se = E.area(y, np.array(["A"] * 5), {"A": 1.0})
    assert abs(se - np.sqrt(0.4 * 0.6 / 4)) < 1e-12                        # p (1 - p) / (n - 1)


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


def test_sample_pairs_balanced():
    s = pd.read_csv(C.HERE / "sample.csv")
    assert (s.labeller_1 != s.labeller_2).all()
    pairs = s.apply(lambda r: frozenset((r.labeller_1, r.labeller_2)), axis=1).value_counts()
    assert len(pairs) == len(list(combinations(sampling.LABELLERS, 2))) and pairs.nunique() == 1
    both = pd.concat([s.assign(who=s.labeller_1), s.assign(who=s.labeller_2)], ignore_index=True)
    mix = pd.crosstab(both.who, [both.area, both.stratum, both.split])
    assert (mix.nunique() == 1).all()                      # every labeller the same count in every group


def test_merge_no_tiebreak(tmp_path=None):
    import tempfile
    from pathlib import Path
    tmp = Path(tempfile.mkdtemp())
    s = pd.DataFrame({"id": ["S1", "S2", "S3", "S4"], "area": "aweil", "stratum": "A", "split": "test",
                      "lon": 0.0, "lat": 0.0, "labeller_1": "Ann", "labeller_2": "Bob"})
    s.to_csv(tmp / "sample.csv", index=False)
    (tmp / "labels").mkdir()
    rows = {"Ann": [("S1", "crop", ">50"), ("S2", "crop", "10-25"), ("S3", "crop", "<10"), ("S4", "unsure", "")],
            "Bob": [("S1", "crop", "25-50"), ("S2", "fallow", "<10"), ("S3", "not crop", "0"), ("S4", "not crop", "0")]}
    for who, rs in rows.items():
        pd.DataFrame([{"id": i, "labeller": who, "label": l, "crop_share": c, "confidence": 2, "unit": f"{C.BOX_M}m"}
                      for i, l, c in rs]).reindex(columns=server.COLUMNS).to_csv(
            tmp / "labels" / f"sample_labels_{who}.csv", index=False)       # same columns as the tool saves
    here, write = C.HERE, M.write_table
    C.HERE, M.write_table = tmp, lambda: []
    try:
        merge.main()
    finally:
        C.HERE, M.write_table = here, write
    f = pd.read_csv(tmp / "labels_final.csv").set_index("id")
    assert list(f.final) == ["crop", "crop/fallow", "disagreed", "disagreed"]
    assert f.loc["S1", "crop"] == 1 and abs(f.loc["S1", "crop_share"] - (0.75 + 0.375) / 2) < 1e-9
    assert f.loc["S2", "cropland"] == 1 and np.isnan(f.loc["S2", "crop"]) and f.loc["S2", "crop_avg"] == 0.5
    assert np.isnan(f.loc["S3", "cropland"]) and f.loc["S3", "cropland_avg"] == 0.5 and f.loc["S3", "share_avg"] == 0.025
    assert f.loc["S4", "cropland_avg"] == 0                 # "unsure" left out of the mean, not counted as no
    assert (tmp / "disagreements.csv").exists() and not (tmp / "adjudication.csv").exists()


def test_model_data_splits():
    if not M.TABLE.exists():
        return                                             # written by 06_merge_labels.py
    t = pd.read_csv(M.TABLE)
    assert len(t) == len(pd.read_csv(C.HERE / "sample.csv")) and t.id.is_unique
    for split in ("calibration", "test"):
        X, y, info = M.load(split, target="cropland")
        assert (info.split == split).all() and len(X) == len(y) == len(info)
        assert list(X.columns) == F.FEATURES
    assert abs(t.ha_per_point.sum() - pd.read_csv(C.HERE / "strata_areas.csv").ha.sum()) < 1


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
    img = F.pixel_features(ee, pt.buffer(2000)).select("dist_buildings_m")    # before the box mean
    got = img.reduceRegion(ee.Reducer.first(), pt, 10).getInfo()["dist_buildings_m"]
    assert abs(got - true) <= 15, f"feature {got:.0f} m, nearest building {true:.0f} m"


if __name__ == "__main__":
    tests = [test_area, test_area_share, test_accuracy_one_stratum, test_tree_equals_rules,
             test_sample_pairs_balanced, test_merge_no_tiebreak, test_model_data_splits]
    if "--ee" in sys.argv:
        tests += [test_ee_equals_python, test_building_distance]
    for t in tests:
        t()
        print("ok  ", t.__name__)
