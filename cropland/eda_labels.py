"""
How well do two labellers agree? Read-only summary of the sample labels for the
methodology section (response design). Writes nothing into cropland/.

Uses only the labels: no features, no maps, so it cannot leak anything into
Rule 1. Run it again when every point is labelled twice; until then the numbers
are preliminary and say so.

Agreement is reported three ways, like 06_merge_labels.py classifies points:
  - cropland vs not cropland (crop or fallow vs not crop): the area definition;
  - cropped in 2025 vs not (crop vs fallow or not crop): the map target;
  - the full label (crop / fallow / not crop / unsure).
Cohen's kappa corrects raw agreement for the agreement two people would reach
by chance given how often each uses each label (Cohen 1960).
"""

import numpy as np
import pandas as pd

import common as C

CROPLAND = {"crop", "fallow"}


def pairs():
    """One row per sample point with both labels side by side (points labelled twice only)."""
    sample = pd.read_csv(C.HERE / "sample.csv")
    lab = pd.concat([pd.read_csv(f, dtype={"crop_share": str})
                     for f in sorted((C.HERE / "labels").glob("sample_labels_*.csv"))])
    lab = lab[lab.label.notna()].drop_duplicates(["id", "labeller"], keep="last")
    keep = ["label", "confidence", "minutes", "overridden", "cover", "crop_share",
            "cue_a_bare", "cue_b_greenup", "cue_c_harvest", "cue_d_shape", "cue_e_crop2024"]
    out = sample
    for k in (1, 2):
        one = lab.rename(columns={"labeller": f"labeller_{k}", **{c: f"{c}_{k}" for c in keep}})
        out = out.merge(one[["id", f"labeller_{k}"] + [f"{c}_{k}" for c in keep]],
                        on=["id", f"labeller_{k}"], how="left")
    return out[out.label_1.notna() & out.label_2.notna()].reset_index(drop=True)


def kappa(a, b):
    """Cohen's kappa for two equally long label lists."""
    a, b = pd.Series(list(a)), pd.Series(list(b))
    po = (a == b).mean()
    pa, pb = a.value_counts(normalize=True), b.value_counts(normalize=True)
    pe = sum(pa.get(c, 0) * pb.get(c, 0) for c in set(pa.index) | set(pb.index))
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def definitions(d):
    """The three label versions of both labellers; 'unsure' stays its own value."""
    out = {}
    for k in (1, 2):
        lab = d[f"label_{k}"]
        out[f"cropland_{k}"] = lab.map(lambda x: x if x == "unsure" else ("cropland" if x in CROPLAND else "not"))
        out[f"cropped_{k}"] = lab.map(lambda x: x if x == "unsure" else ("cropped" if x == "crop" else "not"))
        out[f"label_{k}"] = lab
    return pd.DataFrame(out)


def specific(a, b, pos):
    """Positive and negative specific agreement (Cicchetti & Feinstein 1990), unsure left out.

    Kappa drops to 0 when one class is rare even if people almost always agree
    (Bor South: nearly every box is not crop). Positive agreement asks: when one
    labeller calls cropland, how often does the other one too?
    """
    ok = (a != "unsure") & (b != "unsure")
    a, b = a[ok] == pos, b[ok] == pos
    both, neither, split = (a & b).sum(), (~a & ~b).sum(), (a != b).sum()
    p = 2 * both / (2 * both + split) if both + split else np.nan
    n = 2 * neither / (2 * neither + split) if neither + split else np.nan
    return p, n


def summary(d, by=None):
    """Raw agreement, kappa and specific agreement per definition, overall or per group."""
    groups = [("all", d)] if by is None else list(d.groupby(by))
    rows = []
    for g, part in groups:
        defs = definitions(part)
        row = {"group": g if by else "all", "points": len(part)}
        for name, pos in (("cropland", "cropland"), ("cropped", "cropped"), ("label", None)):
            a, b = defs[f"{name}_1"], defs[f"{name}_2"]
            row[f"{name}_agree"] = (a == b).mean()
            row[f"{name}_kappa"] = kappa(a, b)
            if pos:
                row[f"{name}_pos_agree"], row[f"{name}_neg_agree"] = specific(a, b, pos)
                row[f"{name}_either_says"] = ((a == pos) | (b == pos)).sum()
        row["either_unsure"] = ((part.label_1 == "unsure") | (part.label_2 == "unsure")).mean()
        rows.append(row)
    return pd.DataFrame(rows)


def confusion(d):
    """Label of labeller 1 against labeller 2 (order does not matter, so the table is folded)."""
    lab = ["crop", "fallow", "not crop", "unsure"]
    t = pd.crosstab(pd.Categorical(d.label_1, lab), pd.Categorical(d.label_2, lab), dropna=False)
    return t + t.T - np.diag(np.diag(t))


CUES = {"cue_a_bare": "a. bare soil Apr-May", "cue_b_greenup": "b. green-up Jun-Aug", "cue_c_harvest": "c. early harvest",
        "cue_d_shape": "d. field shape", "cue_e_crop2024": "e. cropped in 2024"}


def disagreement_causes(d):
    """Where the two labellers split on cropland vs not: which of their answers differed.

    For every such point: did they pick a different cover class (water / buildings / trees / open land),
    and which crop cues one answered yes and the other no. Returns (per point, counts per cause).
    """
    defs = definitions(d)
    split = (defs.cropland_1 != defs.cropland_2) & (defs.cropland_1 != "unsure") & (defs.cropland_2 != "unsure")
    rows = []
    for i in d.index[split]:
        r = d.loc[i]
        yes1 = {c for c in CUES if r[f"{c}_1"] == "yes"}
        yes2 = {c for c in CUES if r[f"{c}_2"] == "yes"}
        rows.append({"id": r.id, "area": r.area, "stratum": r.stratum,
                     "cover_differs": r.cover_1 != r.cover_2,
                     "covers": " / ".join(sorted({str(r.cover_1), str(r.cover_2)})),
                     "cues_one_said_yes": ", ".join(CUES[c] for c in sorted(yes1 ^ yes2)),
                     "n_cues_differ": len(yes1 ^ yes2)})
    per = pd.DataFrame(rows)
    counts = {"split points": len(per), "different cover class": int(per.cover_differs.sum()) if len(per) else 0}
    for c, name in CUES.items():
        counts[f"cue differs: {name}"] = int(per.cues_one_said_yes.str.contains(name, regex=False).sum()) if len(per) else 0
    return per, pd.Series(counts, name="points")


def effort(lab_dir=None):
    """Minutes per point and confidence per labeller, from every saved sample label."""
    lab = pd.concat([pd.read_csv(f) for f in sorted((lab_dir or C.HERE / "labels").glob("sample_labels_*.csv"))])
    m = pd.to_numeric(lab.minutes, errors="coerce")
    return lab.assign(minutes=m.clip(upper=m.quantile(0.98))).groupby("labeller").agg(
        points=("id", "size"), median_min=("minutes", "median"), mean_min=("minutes", "mean"),
        total_hours=("minutes", lambda x: x.sum() / 60),
        conf3=("confidence", lambda x: (pd.to_numeric(x, errors="coerce") == 3).mean()),
        overridden=("overridden", "mean"))
