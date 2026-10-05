"""
The data every model uses: one row per sample point (METHODOLOGY.md section 6).

06_merge_labels.py writes model_table.csv; Rule 1, the benchmarks and any
other model read it with load(), so they all train and score on exactly the
same points, inputs and targets.

model_table.csv, one row per sample point (450):
  id, area, stratum, split, lat, lon, labeller_1, labeller_2
  ha_per_point     hectares of the study area this point stands for
                   (stratum area / points in the stratum): sum it for maps
                   and dashboards
  final            agreed label, "crop/fallow", "disagreed", "unsure", or
                   empty if not labelled twice yet
  crop             target: cropped in 2025 (1/0); empty unless both agree
  cropland         target: crop + fallow (1/0); empty unless both agree
  crop_share       target: share of the box that is cropland (0-1); empty unless both agree
  cropland_avg, crop_avg, share_avg, share_crop_avg   mean of the two labellers
  disagreed, crop_fallow_only, confidence
  the 18 features (features.FEATURES), then A00-A63 (Satellite Embedding)

Inputs are the features (or the embedding) only. Never use the labellers'
answers, share or confidence as inputs: they are the labels.

    import model_data as M
    X, y, info = M.load("calibration", target="crop")    # fit on this
    X, y, info = M.load("test", target="crop")           # score only, after freezing
"""

import pandas as pd

import common as C
import features as F

TABLE = C.HERE / "model_table.csv"
TARGETS = ("crop", "cropland", "crop_share")
INFO = ["id", "area", "stratum", "split", "lat", "lon", "ha_per_point", "final", "disagreed", "confidence"]


def write_table() -> pd.DataFrame:
    s = pd.read_csv(C.HERE / "sample.csv")
    W = pd.read_csv(C.HERE / "strata_areas.csv")
    n = s.groupby(["area", "stratum"]).size().rename("n").reset_index()
    per = W.merge(n, on=["area", "stratum"]).assign(ha_per_point=lambda d: d.ha / d.n)
    t = s.merge(per[["area", "stratum", "ha_per_point"]], on=["area", "stratum"], how="left")
    lab_path = C.HERE / "labels_final.csv"
    lab = pd.read_csv(lab_path) if lab_path.exists() else pd.DataFrame(columns=["id"])
    t = (t.merge(lab, on="id", how="left")
          .merge(pd.read_csv(C.HERE / "features_sample.csv"), on="id", how="left")
          .merge(pd.read_csv(C.HERE / "embedding_sample.csv"), on="id", how="left"))
    t.to_csv(TABLE, index=False)
    return t


def embedding_cols(t: pd.DataFrame) -> list[str]:
    return [c for c in t.columns if len(c) == 3 and c[0] == "A" and c[1:].isdigit()]


def load(split: str, target: str = "crop", inputs: str = "features"):
    """Inputs X (DataFrame), target y (array) and point info for one split.

    Only points where both labellers agree on the target are returned.
    inputs: "features" (the 18 features, as Rule 1) or "embedding" (A00-A63).
    Missing feature values stay missing: fill them with fill_values() of the
    calibration points, as Rule 1 does.
    """
    if split not in ("calibration", "test"):
        raise ValueError("split is 'calibration' or 'test'")
    if target not in TARGETS:
        raise ValueError(f"target is one of {TARGETS}")
    t = pd.read_csv(TABLE)
    t = t[(t.split == split) & t[target].notna()]
    cols = F.FEATURES if inputs == "features" else embedding_cols(t)
    y = t[target].to_numpy(float if target == "crop_share" else int)
    return t[cols].reset_index(drop=True), y, t[INFO].reset_index(drop=True)


def fill_values(X: pd.DataFrame) -> dict:
    """Median of each feature: the value used where a feature is missing (stored in the rules file)."""
    return {f: round(float(X[f].median()), 4) for f in X.columns}
