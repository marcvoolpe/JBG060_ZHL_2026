"""
Step 1 - Compare two people's pilot labels.

Reads every pilot_labels_<name>.csv in cropland/ (not the TEMPLATE) and reports,
for each pair of labellers:
  - how many points both labelled crop / not crop (unsure counts as its own label);
  - raw agreement and Cohen's kappa (agreement beyond chance);
  - the share of points each person marked confidence 3 (sure);
  - median minutes per point.

The go / no-go rule (METHODOLOGY.md section 4): if fewer than 70% of points
get a confident (2 or 3) crop / fallow / not-crop label from both people, a
10 m point label is too hard here and we switch to "share of crop in a 30 m cell".

Run from group_repo: python cropland/01_compare_pilot.py
"""

from itertools import combinations
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

HERE = Path(__file__).resolve().parent
LABELS = ("crop", "fallow", "not crop", "unsure")
CROPLAND = {"crop": "cropland", "fallow": "cropland", "not crop": "not cropland", "unsure": "unsure"}


def load() -> dict[str, pd.DataFrame]:
    sheets = {}
    for f in sorted([*HERE.glob("pilot_labels_*.csv"), *(HERE / "labels").glob("pilot_labels_*.csv")]):
        if f.stem.endswith("TEMPLATE"):
            continue
        df = pd.read_csv(f).set_index("id")
        df["label"] = df["label"].str.strip().str.lower()
        bad = set(df["label"].dropna()) - set(LABELS)
        if bad:
            raise ValueError(f"{f.name}: labels must be one of {LABELS}, found {bad}")
        sheets[f.stem.removeprefix("pilot_labels_")] = df
    return sheets


def main() -> None:
    sheets = load()
    if not sheets:
        print("No pilot labels yet. Label the pilot set in the tool (python cropland/label_server.py).")
        return
    for name, df in sheets.items():
        done = df["label"].notna()
        confident = done & df["label"].isin(["crop", "fallow", "not crop"]) & (pd.to_numeric(df["confidence"], errors="coerce") >= 2)
        print(f"{name}: {done.sum()} labelled, {df.label.eq('crop').sum()} crop, "
              f"{confident.mean():.0%} confident crop/not-crop, median {pd.to_numeric(df['minutes'], errors='coerce').median()} min/point")
    for a, b in combinations(sheets, 2):
        both = sheets[a]["label"].dropna().index.intersection(sheets[b]["label"].dropna().index)
        la, lb = sheets[a].loc[both, "label"], sheets[b].loc[both, "label"]
        ca, cb = la.map(CROPLAND), lb.map(CROPLAND)
        print(f"\n{a} vs {b}: {len(both)} points")
        print(f"  cropland vs not (what the estimates use): agreement {(ca == cb).mean():.0%}, kappa {cohen_kappa_score(ca, cb):.2f}")
        print(f"  all four labels: agreement {(la == lb).mean():.0%}, kappa {cohen_kappa_score(la, lb):.2f}")
        print(pd.crosstab(la.rename(a), lb.rename(b)))


if __name__ == "__main__":
    main()
