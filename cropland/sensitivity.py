"""
Sensitivity checks of the evaluation (15 Oct 2026, after the group's review). Post hoc and without Earth Engine:
none of them changes a frozen model, a label or a reported score. Each reads the result tables and writes its own.

  1. labellers scored like the maps: one labeller against the other on the Aweil test points, with the same stratum
     weights (the dashed line in figure 15; the unweighted positive agreement is not comparable with the maps' F1);
  2. every map scored three ways on the Aweil test points: agreed points only (the main score), the points the two
     labellers split on counted as cropland, and counted as not cropland;
  3. precision for the maps that were right on every crop call: the 95% Clopper-Pearson lower bound, which a
     standard error of 0 hides;
  4. share classes: the area if every labeller had picked the lowest, or the highest, value of each class (worst
     cases, not an interval), and how often the two labellers picked the same class;
  5. where Rule 1 errs: test errors per stratum, hectares behind one box, agreed crop boxes it was fitted on, and how
     much of Aweil's cropland lies farther from a building than its threshold (fields it misses by design);
  6. past floods: in which years the sample's interval contains the median public map, and which maps lie below it;
  7. the stability of Rule 1's recipe (depth 2-4 by inner cross-validation, balanced classes, leaves of 5 or more):
     20 x 5-fold cross-validation over all agreed points, calibration and test. A check of the recipe, not of the
     frozen rule;
  8. the closest pair of sample points (does the 100 m thinning rule matter?).

Writes cropland/results/: sensitivity_summary.csv (key, value, note), sensitivity_three_ways.csv,
precision_bounds.csv, flood_interval_check.csv, rule1_recipe_stability.csv; and redraws figure 15.

Run from group_repo: python cropland/sensitivity.py
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

import common as C
import estimators as E
import evaluation as V
import features as F

RES = C.HERE / "results"
RULE = C.HERE / "rule1_2026-10-12.json"
PUBLIC = ["gfsad_2015", "glad_2019", "deafrica_2019", "worldcover_2021", "worldcereal_2021", "esri_2025",
          "dynamicworld_2025", "asap_v04"]                                   # the 8 public layers, as in the report
OURS = ["rule1", "rf_features", "rf_embedding", "logistic_l2", "logistic_rule1_inputs"]
CLASSES = ["<10", "10-25", "25-50", ">50"]
EDGES = {"middle": {"0": 0, "<10": .05, "10-25": .175, "25-50": .375, ">50": .75},          # as in 06_merge_labels
         "lowest": {"0": 0, "<10": 0, "10-25": .10, "25-50": .25, ">50": .50},
         "highest": {"0": 0, "<10": .10, "10-25": .25, "25-50": .50, ">50": 1.0}}


def weights(area):
    W = pd.read_csv(C.HERE / "strata_areas.csv")
    return W[W.area == area].set_index("stratum").share.to_dict(), W[W.area == area].ha.sum()


def f1(m, ref, strata, w):
    return E.accuracy(np.asarray(m).astype(int), np.asarray(ref).astype(int), np.asarray(strata), w, n_boot=10)["f1"]


def three_ways(v, w):
    """F1 on the Aweil test points: agreed only, splits as cropland, splits as not cropland."""
    t = v[(v.area == "aweil") & (v.split == "test") & v.cropland_avg.notna()]
    split = (t.cropland_avg > 0) & (t.cropland_avg < 1)
    ok = t.cropland.notna()
    rows = []
    for m in OURS + PUBLIC:
        rows.append({"map": m, "kind": "ours" if m in OURS else "public",
                     "f1_agreed_only": f1(t[m][ok], t.cropland[ok], t.stratum[ok], w),
                     "f1_splits_as_cropland": f1(t[m], t.cropland_avg > 0, t.stratum, w),
                     "f1_splits_as_not": f1(t[m], t.cropland_avg >= 1, t.stratum, w),
                     "test_points": len(t), "splits": int(split.sum())})
    return pd.DataFrame(rows)


def precision_bounds(v, acc):
    """Maps that were right on every crop call: how many calls, and the 95% Clopper-Pearson lower bound."""
    t = v[(v.area == "aweil") & (v.split == "test") & v.cropland.notna()]
    a = acc[(acc.area == "aweil") & (acc.definition == "cropland")].set_index("map")
    rows = []
    for m in a.index[(a.ua == 1) & (a.ua_se == 0)]:
        calls = t[t[m] == 1]
        n, k = len(calls), int(calls.cropland.sum())
        rows.append({"map": m, "crop_calls": n, "right": k, "lower_95": beta.ppf(0.025, k, n - k + 1) if k else 0.0,
                     "calls_by_stratum": " ".join(f"{s}:{c}" for s, c in sorted(calls.stratum.value_counts().items()))})
    return pd.DataFrame(rows)


def share_classes():
    """The Aweil cropland area under the lowest / middle / highest value of each share class, and class agreement."""
    lab = pd.concat([pd.read_csv(f, dtype={"crop_share": str}) for f in sorted((C.HERE / "labels").glob("sample_labels_*.csv"))])
    lab = lab[lab.label.notna()].drop_duplicates(["id", "labeller"], keep="last").drop(columns=["area"], errors="ignore")
    s = pd.read_csv(C.HERE / "sample.csv")
    mine = lab.merge(s[["id", "area", "stratum", "labeller_1", "labeller_2"]], on="id")
    mine = mine[(mine.labeller == mine.labeller_1) | (mine.labeller == mine.labeller_2)]
    cropland = mine.label.isin(["crop", "fallow"])
    out = {}
    w, land = weights("aweil")
    for name, e in EDGES.items():
        val = mine.crop_share.map(e).where(cropland, mine.label.map({"not crop": 0.0}))
        per = mine.assign(v=val).groupby("id").agg(v=("v", "mean"), area=("area", "first"), stratum=("stratum", "first")).dropna()
        a = per[per.area == "aweil"]
        est, _ = E.area(a.v.to_numpy(float), a.stratum.to_numpy(), w)
        out[f"share_class_{name}_pct"] = 100 * est
        out[f"share_class_{name}_ha"] = est * land
    pairs = mine[cropland].groupby("id").crop_share.agg(list)
    pairs = pairs[pairs.map(lambda l: len(l) == 2 and all(c in CLASSES for c in l))]
    out["share_class_boxes_both_cropland"] = len(pairs)
    out["share_class_same_pct"] = 100 * pairs.map(lambda l: l[0] == l[1]).mean()
    out["share_class_within_one_pct"] = 100 * pairs.map(lambda l: abs(CLASSES.index(l[0]) - CLASSES.index(l[1])) <= 1).mean()
    return out


def rule1_errors(v, mt):
    """Where Rule 1 errs on the test points, the hectares one box stands for, and cropland far from buildings."""
    rule = json.loads(RULE.read_text())
    far_m = next(x for c in rule["rules"] for f, op, x in c["if"] if f == "dist_buildings_m")
    te = v[(v.split == "test") & v.cropland.notna()]
    err = te[te.rule1 != te.cropland]
    w, land = weights("aweil")
    n_per = v[v.area == "aweil"].stratum.value_counts()
    ta = te[te.area == "aweil"]
    both = int(((ta.rule1 == 1) & (ta.cropland == 1)).sum())
    a = v[(v.area == "aweil") & v.cropland_avg.notna()]
    far = (a.dist_buildings_m > far_m).astype(float)
    box_all, _ = E.area(a.cropland_avg.to_numpy(float), a.stratum.to_numpy(), w)
    box_far, _ = E.area((a.cropland_avg * far).to_numpy(float), a.stratum.to_numpy(), w)
    sh_all, _ = E.area(a.share_avg.fillna(0).to_numpy(float), a.stratum.to_numpy(), w)
    sh_far, _ = E.area((a.share_avg.fillna(0) * far).to_numpy(float), a.stratum.to_numpy(), w)
    cal = mt[(mt.split == "calibration") & (mt.area == "aweil") & mt.crop.notna()]
    agreed_crop = v[v.cropland == 1]
    out = {"rule1_test_errors": len(err), "rule1_missed": int(((te.rule1 == 0) & (te.cropland == 1)).sum()),
           "rule1_false_crop": int(((te.rule1 == 1) & (te.cropland == 0)).sum()),
           "rule1_errors_aweil_A": int(((err.area == "aweil") & (err.stratum == "A")).sum()),
           "rule1_f1_unweighted_aweil_test": 2 * both / int((ta.rule1 == 1).sum() + (ta.cropland == 1).sum()),
           "calibration_crop_boxes_aweil_A": int(((cal.stratum == "A") & (cal.crop == 1)).sum()),
           "calibration_points_aweil_A": int((cal.stratum == "A").sum()),
           "rule1_building_threshold_m": far_m,
           "agreed_cropland_boxes": len(agreed_crop),
           "agreed_cropland_boxes_far": int((agreed_crop.dist_buildings_m > far_m).sum()),
           "cropland_boxes_far_pct_aweil": 100 * box_far / box_all, "cropland_area_far_pct_aweil": 100 * sh_far / sh_all}
    for s, ha in pd.read_csv(C.HERE / "strata_areas.csv").query("area == 'aweil'").set_index("stratum").ha.items():
        out[f"ha_per_box_aweil_{s}"] = ha / n_per[s]
    return out


def flood_intervals():
    """Past floods: does the sample's interval contain the median public map, and which maps lie below its lower end?"""
    h = pd.read_csv(RES / "flood_history.csv")
    rows = []
    for (area, days, year), g in h.groupby(["area", "min_days", "year"]):
        s = g[(g.layer == "sample (ratio)") & (g.measure == "share of box")].iloc[0]
        if pd.isna(s.flooded_crop_ha) or s.points_in_flood < 5:
            continue
        maps = g[g.layer.isin(PUBLIC)].set_index("layer").flooded_crop_ha
        med = maps.median()
        rows.append({"area": area, "min_days": days, "year": year, "points": int(s.points_in_flood),
                     "sample_ha": s.flooded_crop_ha, "low_ha": s.low_ha, "high_ha": s.high_ha, "median_map_ha": med,
                     "ratio_to_median": s.flooded_crop_ha / med if med else np.nan,
                     "median_inside": bool(s.low_ha <= med <= s.high_ha),
                     "maps_below_low": " ".join(sorted(maps.index[maps < s.low_ha])), "n_maps_below_low": int((maps < s.low_ha).sum()),
                     "maps_above_high": int((maps > s.high_ha).sum())})
    return pd.DataFrame(rows)


def recipe_stability(mt, repeats=20):
    """Rule 1's recipe refitted in repeated 5-fold cross-validation over all agreed points (target: cropped in 2025)."""
    d = mt[mt.crop.notna()].reset_index(drop=True)
    X, y = d[F.FEATURES], d.crop.astype(int).to_numpy()
    tree = lambda depth: DecisionTreeClassifier(max_depth=depth, min_samples_leaf=5, class_weight="balanced", random_state=C.SEED)
    w, _ = weights("aweil")
    aweil = (d.area == "aweil").to_numpy()
    rows, used = [], []
    for rep in range(repeats):
        pred = np.zeros(len(d), int)
        for tr, te in StratifiedKFold(5, shuffle=True, random_state=rep).split(X, y):
            fill = X.iloc[tr].median()                                       # like 07: medians of the fitting points
            Xtr, Xte = X.iloc[tr].fillna(fill), X.iloc[te].fillna(fill)
            inner = StratifiedKFold(5, shuffle=True, random_state=C.SEED)
            score = {k: cross_val_score(tree(k), Xtr, y[tr], cv=inner, scoring="f1").mean() for k in (2, 3, 4)}
            m = tree(max(score, key=score.get)).fit(Xtr, y[tr])
            pred[te] = m.predict(Xte)
            used.append({F.FEATURES[i] for i in m.tree_.feature if i >= 0})
        rows.append({"repeat": rep, "aweil_weighted_f1": f1(pred[aweil], y[aweil], d.stratum[aweil], w), "points": len(d)})
    out = pd.DataFrame(rows)
    freq = {f: 100 * np.mean([f in u for u in used]) for f in F.FEATURES}
    return out, freq


def closest_points():
    s = pd.read_csv(C.HERE / "sample.csv")
    out = {}
    for area, g in s.groupby("area"):
        k = np.cos(np.radians(g.lat.mean()))
        x, y = g.lon.to_numpy() * 111_320 * k, g.lat.to_numpy() * 110_574
        dx, dy = np.abs(x[:, None] - x[None, :]), np.abs(y[:, None] - y[None, :])
        dist = np.hypot(dx, dy)
        np.fill_diagonal(dist, np.inf)
        touch = (dx < C.BOX_M) & (dy < C.BOX_M)
        np.fill_diagonal(touch, False)
        out[f"closest_points_m_{area}"] = dist.min()
        out[f"overlapping_box_pairs_{area}"] = int(touch.sum() // 2)
    return out


def main() -> None:
    warnings.filterwarnings("ignore")
    v = pd.read_csv(RES / "map_values.csv")
    mt = pd.read_csv(C.HERE / "model_table.csv")
    acc = pd.read_csv(RES / "accuracy.csv")
    w, _ = weights("aweil")
    summary = {}
    lab = V.labeller_f1(pd.read_csv(C.HERE / "labels_merged.csv"), pd.read_csv(C.HERE / "sample.csv"), w)
    summary |= {"labeller_f1_weighted_aweil_test": lab["weighted_f1"], "labeller_pos_agree_unweighted_aweil_test": lab["unweighted_pos_agree"],
                "labeller_points_aweil_test": lab["points"]}
    tw = three_ways(v, w)
    tw.round(3).to_csv(RES / "sensitivity_three_ways.csv", index=False)
    for col in ("f1_agreed_only", "f1_splits_as_cropland", "f1_splits_as_not"):
        summary[f"rule1_above_every_public_{col}"] = bool(tw.loc[tw["map"] == "rule1", col].iloc[0] > tw.loc[tw.kind == "public", col].max())
    summary["three_ways_splits"] = int(tw.splits.iloc[0])
    pb = precision_bounds(v, acc)
    pb.round(3).to_csv(RES / "precision_bounds.csv", index=False)
    summary |= share_classes()
    summary |= rule1_errors(v, mt)
    fl = flood_intervals()
    fl.round(1).to_csv(RES / "flood_interval_check.csv", index=False)
    aw = fl[(fl.area == "aweil") & (fl.min_days == 1)]
    summary |= {"flood_years_judged_aweil": len(aw), "flood_years_median_inside_aweil": int(aw.median_inside.sum()),
                "flood_points_min_aweil": int(aw.points.min()), "flood_points_max_aweil": int(aw.points.max())}
    for y in (2008, 2022):
        r = aw[aw.year == y].iloc[0]
        summary |= {f"flood_{y}_maps_below_low": int(r.n_maps_below_low), f"flood_{y}_which_below": r.maps_below_low}
    st, freq = recipe_stability(mt)
    st.round(3).to_csv(RES / "rule1_recipe_stability.csv", index=False)
    summary |= {"recipe_f1_mean": st.aweil_weighted_f1.mean(), "recipe_f1_min": st.aweil_weighted_f1.min(),
                "recipe_f1_max": st.aweil_weighted_f1.max(), "recipe_points": int(st.points.iloc[0])}
    summary |= {f"recipe_uses_{f}_pct": freq[f] for f in ("dist_buildings_m", "edge_density", "vh_jun", "texture_jja")}
    summary |= closest_points()
    out = pd.DataFrame([{"key": k, "value": v_} for k, v_ in summary.items()])
    out.to_csv(RES / "sensitivity_summary.csv", index=False)
    print(out.to_string(index=False))
    print(tw.round(2).to_string(index=False))
    print(pb.round(3).to_string(index=False))
    import eda_figures as FG
    print("figure:", FG.scorecard(acc, agreement=lab["weighted_f1"], precision_lower=dict(zip(pb["map"], pb.lower_95))))


if __name__ == "__main__":
    main()
