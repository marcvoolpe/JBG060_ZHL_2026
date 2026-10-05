"""
Step 7 - Fit and freeze the rules (METHODOLOGY.md section 6).

Uses the CALIBRATION points only (split column of sample.csv), read with
model_data.load() so every model sees the same data. Target: cropped in 2025
(crop = 1; fallow and not crop = 0), only where both labellers agree on it
(disagreed, crop vs fallow and unsure points are left out). Fallow is
left out of the map on purpose: in 2025 a fallow field looks like grass, so a
map cannot see it reliably. Fallow enters the cropland AREA through the
labelled sample only (09_score.py).

  Rule 1 (main)   decision tree, depth 2/3/4 picked by 5-fold cross-validation
                  (smallest depth within 0.02 F1 of the best), printed as rules.
  Benchmarks      random forest (500 trees) on the same features, and on the
                  2025 Satellite Embedding. Scored only, never used for the map.

Writes rule1_<date>.json in cropland/ (kept in git) and the benchmarks in
raw_data/cropland/. After this the rules are frozen: do not rerun once the
test labels have been looked at.

Run from group_repo: python cropland/07_fit_rules.py
"""

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

import common as C
import features as F
import model_data as M
import rules as R


def fit_tree(X, y, fill):
    cv = StratifiedKFold(5, shuffle=True, random_state=C.SEED)
    tree = lambda depth: DecisionTreeClassifier(max_depth=depth, min_samples_leaf=5,
                                                class_weight="balanced", random_state=C.SEED)
    scores = {d: cross_val_score(tree(d), X, y, cv=cv, scoring="f1").mean() for d in (2, 3, 4)}
    depth = min(d for d, s in scores.items() if s >= max(scores.values()) - 0.02)
    print("cross-validated F1 by depth:", {d: round(s, 3) for d, s in scores.items()}, "-> depth", depth)
    return R.from_tree(tree(depth).fit(X, y), F.FEATURES, fill, "rule1")


def main() -> None:
    Xd, y, info = M.load("calibration", target="crop")
    print(f"{len(y)} calibration points: {y.sum()} crop, {(info.final == 'fallow').sum()} fallow, "
          f"{(info.final == 'not crop').sum()} not crop")
    fill = M.fill_values(Xd)
    X = Xd.fillna(fill).to_numpy()

    rule1 = fit_tree(X, y, fill)
    print(f"Rule 1 saved to {R.save(rule1, C.HERE).name}:\n{R.as_text(rule1)}\n")

    rf = RandomForestClassifier(500, class_weight="balanced", random_state=C.SEED, n_jobs=-1).fit(X, y)
    emb, _, _ = M.load("calibration", target="crop", inputs="embedding")
    rf_emb = RandomForestClassifier(500, class_weight="balanced", random_state=C.SEED, n_jobs=-1).fit(emb.to_numpy(), y)
    joblib.dump({"rf": rf, "rf_embedding": rf_emb, "fill": fill, "embedding_cols": list(emb.columns)},
                C.OUT / "benchmarks.joblib")
    print("benchmarks saved to raw_data/cropland/benchmarks.joblib")


if __name__ == "__main__":
    main()
