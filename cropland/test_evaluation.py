"""
Checks for evaluation.py, on made-up data only (no labels, no Earth Engine):
  - the area interval: same estimate as estimators.area, adjusted upper bound
    never below the usual one, and above zero even when a stratum holds no crop;
  - the coverage simulation: unbiased, and the adjusted interval covers at least
    as often as the usual one;
  - the error analysis counts false and missed crop correctly;
  - trigger decisions: fire / no fire / cannot tell from the sample's interval;
  - design efficiency: a perfect map needs fewer points than a random one;
  - rule complexity of a small rule file.

Run from group_repo: python cropland/test_evaluation.py
"""

import numpy as np
import pandas as pd

import estimators as ES
import evaluation as V


def test_area_interval():
    W = {"A": 0.9, "B": 0.1}
    y = np.r_[np.zeros(50), np.ones(10), np.zeros(40)]          # no crop in A, 10 of 50 in B
    s = np.r_[["A"] * 50, ["B"] * 50]
    r = V.area_interval(y, s, W)
    est, se = ES.area(y, s, W)
    assert abs(r["estimate"] - est) < 1e-12 and abs(r["se"] - se) < 1e-12
    assert r["high_adjusted"] >= r["high"]
    assert r["high_adjusted"] - r["estimate"] > 0.9 * 1.96 * np.sqrt((1 / 52) * (51 / 52) / 50)   # A still counts


def test_coverage_simulation():
    r = V.simulate_interval_coverage([0.95, 0.05], [150, 90], [0.01, 0.3], reps=4000, seed=1)
    assert abs(r["bias_pp"]) < 0.05
    assert r["coverage_adjusted"] >= r["coverage_usual"]
    assert r["coverage_adjusted"] > 0.93


def test_error_analysis():
    values = pd.DataFrame({"id": list("abcdef"), "split": ["test"] * 6, "area": ["aweil"] * 6, "stratum": list("AABBCC"),
                           "cropland": [0, 0, 1, 1, 1, 0], "map_x": [1, 0, 0, 1, 1, 1]})
    context = pd.DataFrame({"id": list("abcdef"), "cover": ["open", "trees", "open", "open", "open", "water"]})
    e = V.error_analysis(values, context, ["map_x"])
    fc = e[(e.kind == "false crop") & (e.group == "cover")].set_index("value")
    mc = e[(e.kind == "missed crop") & (e.group == "area")].iloc[0]
    assert fc.loc["open", "errors"] == 1 and fc.loc["water", "errors"] == 1 and fc.loc["trees", "errors"] == 0
    assert mc.errors == 1 and mc.points == 3


def test_trigger_agreement():
    flooded = pd.DataFrame({"area": ["aweil"] * 3,
                            "map": ["reference: cropland (share of box)", "map_low", "map_high"],
                            "flooded_crop_ha": [800, 100, 5000], "ci_low_ha": [600, np.nan, np.nan],
                            "ci_high_ha": [1200, np.nan, np.nan]})
    t = V.trigger_agreement(flooded, [500, 1000, 2000]).set_index(["threshold_ha", "map"])
    assert t.loc[(500, "map_high"), "sample_says"] == "fire" and t.loc[(500, "map_low"), "agrees"] == False
    assert t.loc[(1000, "map_low"), "sample_says"] == "cannot tell"
    assert t.loc[(2000, "map_low"), "agrees"] == True and t.loc[(2000, "map_high"), "agrees"] == False


def test_design_efficiency():
    rng = np.random.default_rng(0)
    n = 300
    s = np.r_[["A"] * 150, ["B"] * 150]
    y = np.r_[rng.random(150) < 0.02, rng.random(150) < 0.4].astype(float)
    values = pd.DataFrame({"stratum": s, "cropland": y, "perfect": y, "random": (rng.random(n) < 0.2).astype(float)})
    e = V.design_efficiency(values, {"A": 0.9, "B": 0.1}, ["perfect", "random"]).set_index("design")
    assert e.loc["perfect", "n_opt"] < e.loc["random", "n_opt"]


def test_rule_complexity():
    rs = {"rules": [{"if": [["a", ">", 1], ["b", "<=", 2]], "then": 1}, {"if": [["a", "<=", 1]], "then": 1}], "else": 0}
    c = V.rule_complexity(rs)
    assert c == {"rules": 2, "longest_rule_conditions": 2, "features_used": 2, "which": "a, b"}


if __name__ == "__main__":
    for t in (test_area_interval, test_coverage_simulation, test_error_analysis, test_trigger_agreement,
              test_design_efficiency, test_rule_complexity):
        t()
        print("ok  ", t.__name__)
