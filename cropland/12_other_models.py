"""
Step 12 - Other models next to Rule 1: logistic regression and other trees
(METHODOLOGY.md section 6.5). Same points, inputs and target as Rule 1
(model_data.load("calibration", target="crop")).

  compare         cross-validation on the CALIBRATION points only; reads no test label.
                  -> results/model_cv.csv, results/logistic_coefficients.csv
  freeze <name>   fit one candidate on all calibration points, save it, and write
                  results/predictions_<name>.csv (all 450 points, no label read).
                  Then log the choice in METHODOLOGY.md and rerun 09_score.py.

Choose with `compare`, freeze, and only then look at the test score: a model picked
by its test score is no longer tested.

Run from group_repo: python cropland/12_other_models.py compare
                     python cropland/12_other_models.py freeze logistic_l1
"""

import json
import sys
from datetime import date

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

import common as C
import features as F
import model_data as M
import rules as R

RES = C.HERE / "results"
RULE1_INPUTS = ["dist_buildings_m", "edge_density"]
REPEATS = 20


def tree(depth):
    return DecisionTreeClassifier(max_depth=depth, min_samples_leaf=5, class_weight="balanced", random_state=C.SEED)


def logistic(penalty):
    """Standardised features; the penalty strength C is chosen by an inner 5-fold cross-validation (F1).

    liblinear shuffles the data while it fits: seeded since 16 Oct, so `compare` gives the same numbers on
    every run (before, the L1 model's penalty and coefficients changed from run to run)."""
    return make_pipeline(StandardScaler(), LogisticRegressionCV(
        Cs=10, cv=5, penalty=penalty, solver="liblinear", scoring="f1", class_weight="balanced", max_iter=5000,
        random_state=C.SEED))


CANDIDATES = {                       # name: (model, inputs)
    "tree_d1": (tree(1), F.FEATURES),
    "tree_d2": (tree(2), F.FEATURES),          # the setting Rule 1 got
    "tree_d3": (tree(3), F.FEATURES),
    "tree_d4": (tree(4), F.FEATURES),
    "logistic_l2": (logistic("l2"), F.FEATURES),
    "logistic_l1": (logistic("l1"), F.FEATURES),          # drops features it does not need
    "logistic_rule1_inputs": (logistic("l2"), RULE1_INPUTS),   # same two inputs as Rule 1
    "rf_features": (RandomForestClassifier(500, class_weight="balanced", random_state=C.SEED, n_jobs=-1), F.FEATURES),
}


def calibration():
    X, y, info = M.load("calibration", target="crop")
    fill = M.fill_values(X)
    return X.fillna(fill), y, info, fill


def compare() -> pd.DataFrame:
    """Out-of-fold predictions pooled per repeat (5 folds x 20 repeats), then scored once per repeat.

    Unweighted scores treat every point alike; weighted ones weigh each point by the hectares it
    stands for (ha_per_point), as the test scores do. Both are calibration scores: compare models
    with them, do not compare them with test scores.
    """
    X, y, info, _ = calibration()
    w = info.ha_per_point.to_numpy()
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=REPEATS, random_state=C.SEED)
    folds = list(cv.split(X, y))
    rows = []
    for name, (model, cols) in CANDIDATES.items():
        Xc = X[cols].to_numpy()
        for r in range(REPEATS):
            pred = np.zeros_like(y)
            for train, held in folds[5 * r: 5 * r + 5]:
                pred[held] = clone(model).fit(Xc[train], y[train]).predict(Xc[held])
            rows.append({"model": name, "repeat": r,
                         "f1": f1_score(y, pred), "precision": precision_score(y, pred, zero_division=0),
                         "recall": recall_score(y, pred), "f1_weighted": f1_score(y, pred, sample_weight=w)})
        print(f"{name:24s} F1 {np.mean([x['f1'] for x in rows if x['model'] == name]):.3f}")
    per = pd.DataFrame(rows)
    out = per.groupby("model", sort=False).agg(
        inputs=("model", lambda s: len(CANDIDATES[s.iloc[0]][1])),
        f1=("f1", "mean"), f1_low=("f1", lambda s: s.quantile(0.025)), f1_high=("f1", lambda s: s.quantile(0.975)),
        precision=("precision", "mean"), recall=("recall", "mean"),
        f1_weighted=("f1_weighted", "mean")).reset_index()
    ref = per[per.model == "tree_d2"].set_index("repeat").f1
    out["beats_tree_d2_in_repeats"] = [(per[per.model == m].set_index("repeat").f1 > ref).mean() for m in out.model]
    out.insert(1, "points", len(y))
    out.insert(2, "crop_points", int(y.sum()))
    out.to_csv(RES / "model_cv.csv", index=False)
    print(out.round(3).to_string(index=False))

    coefs = []
    for name in ("logistic_l2", "logistic_l1", "logistic_rule1_inputs"):
        model, cols = CANDIDATES[name]
        fit = clone(model).fit(X[cols].to_numpy(), y)
        lr = fit[-1]
        for f, b in zip(cols, lr.coef_[0]):
            coefs.append({"model": name, "feature": f, "coef_per_sd": b, "odds_ratio_per_sd": np.exp(b),
                          "C": lr.C_[0]})
    c = pd.DataFrame(coefs)
    c.to_csv(RES / "logistic_coefficients.csv", index=False)
    print(c[c.model == "logistic_l1"].round(3).to_string(index=False))
    return out


def freeze(name: str) -> None:
    out = RES / f"predictions_{name}.csv"
    if out.exists():
        raise SystemExit(f"{out.name} exists: this model is frozen already")
    model, cols = CANDIDATES[name]
    X, y, _, fill = calibration()
    fit = clone(model).fit(X[cols].to_numpy(), y)
    if name.startswith("tree"):
        print(R.as_text(R.from_tree(fit, cols, {f: fill[f] for f in cols}, name)))
        saved = R.save(R.from_tree(fit, cols, {f: fill[f] for f in cols}, name), C.HERE)  # 08_run_map.py can map it
    elif name.startswith("logistic"):
        sc, lr = fit[0], fit[-1]
        saved = C.HERE / f"{name}_{date.today()}.json"
        saved.write_text(json.dumps({
            "name": name, "frozen": str(date.today()), "features": cols, "fill": {f: fill[f] for f in cols},
            "mean": dict(zip(cols, sc.mean_.round(6).tolist())), "sd": dict(zip(cols, sc.scale_.round(6).tolist())),
            "coef_per_sd": dict(zip(cols, lr.coef_[0].round(6).tolist())), "intercept": round(float(lr.intercept_[0]), 6),
            "C": float(lr.C_[0]), "crop_if": "intercept + sum(coef * (x - mean) / sd) > 0"}, indent=2))
    else:
        saved = None
    t = pd.read_csv(M.TABLE)
    pred = fit.predict(t[cols].fillna(fill).to_numpy())
    pd.DataFrame({"id": t.id, "prediction": pred.astype(int)}).to_csv(out, index=False)
    print(f"frozen {name} on {len(y)} calibration points; saved {saved.name if saved else '(benchmark, not saved)'}; "
          f"wrote {out.name}. Log it in METHODOLOGY.md, then rerun 09_score.py.")


if __name__ == "__main__":
    if sys.argv[1:2] == ["compare"]:
        compare()
    elif sys.argv[1:2] == ["freeze"] and len(sys.argv) == 3 and sys.argv[2] in CANDIDATES:
        freeze(sys.argv[2])
    else:
        raise SystemExit(f"use: compare | freeze <{'|'.join(CANDIDATES)}>")
