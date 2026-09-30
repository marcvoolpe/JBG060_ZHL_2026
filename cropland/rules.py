"""
Rules as a readable, ordered list, shared by the Python scoring and the Earth
Engine map (METHODOLOGY.md section 6).

Format of rules_<date>.json:
  {"name": "rule1", "frozen": "2026-10-14", "features": [...],
   "fill": {feature: value},              # used where a feature is missing
   "rules": [{"if": [["drop_vs_500m", ">", 0.08], ...], "then": 1}, ...],
   "else": 0}
The first rule whose conditions all hold decides; 1 = crop, 0 = not crop.
"""

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

OPS = {">": np.greater, "<=": np.less_equal}


def predict(ruleset: dict, df: pd.DataFrame) -> np.ndarray:
    X = df[ruleset["features"]].fillna(ruleset["fill"])
    out = np.full(len(X), ruleset["else"])
    decided = np.zeros(len(X), bool)
    for r in ruleset["rules"]:
        hit = np.ones(len(X), bool)
        for f, op, t in r["if"]:
            hit &= OPS[op](X[f].to_numpy(), t)
        new = hit & ~decided
        out[new] = r["then"]
        decided |= hit
    return out


def to_ee(ee, ruleset: dict, feature_img):
    """The same rules as an Earth Engine image (1 = crop, 0 = not crop)."""
    img = feature_img.unmask(ee.Image.constant([ruleset["fill"][f] for f in ruleset["features"]])
                             .rename(ruleset["features"]).float())
    out = ee.Image.constant(ruleset["else"])
    for r in reversed(ruleset["rules"]):                 # reversed where() = first rule wins
        cond = ee.Image.constant(1)
        for f, op, t in r["if"]:
            b = img.select(f)
            cond = cond.And(b.gt(t) if op == ">" else b.lte(t))
        out = out.where(cond, r["then"])
    return out.rename("crop").toByte()


def from_tree(tree, features: list[str], fill: dict, name: str) -> dict:
    """Every root-to-leaf path that ends in 'crop' becomes one rule."""
    t = tree.tree_
    rules = []

    def walk(node, conds):
        if t.children_left[node] == -1:                  # leaf
            if int(np.argmax(t.value[node][0])) == 1:
                rules.append({"if": conds, "then": 1})
            return
        f, thr = features[t.feature[node]], round(float(t.threshold[node]), 4)
        walk(t.children_left[node], conds + [[f, "<=", thr]])
        walk(t.children_right[node], conds + [[f, ">", thr]])

    walk(0, [])
    return {"name": name, "frozen": str(date.today()), "features": features, "fill": fill,
            "rules": rules, "else": 0}


def as_text(ruleset: dict) -> str:
    lines = []
    for r in ruleset["rules"]:
        cond = " and ".join(f"{f} {op} {t}" for f, op, t in r["if"])
        lines.append(f"{'crop' if r['then'] else 'not crop'} if {cond}")
    lines.append(f"otherwise {'crop' if ruleset['else'] else 'not crop'}")
    return "\n".join(lines)


def save(ruleset: dict, folder: Path) -> Path:
    p = folder / f"{ruleset['name']}_{ruleset['frozen']}.json"
    p.write_text(json.dumps(ruleset, indent=2))
    return p


def load(path: Path) -> dict:
    return json.loads(Path(path).read_text())
