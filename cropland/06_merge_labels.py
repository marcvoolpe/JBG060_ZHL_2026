"""
Step 6 - Merge the two labels of every sample point (METHODOLOGY.md section 4).

Labels are crop / fallow / not crop / unsure, for the 210 m box around the
point: crop if any field in the box was cropped in 2025, fallow if the box has
a field but none was cropped. Cropland = crop or fallow.

Reads every sample_labels_<name>.csv exported from the labelling tool and
matches the two labels per point:
  - agreed:            same label from both people -> final label.
  - disagreed:         cropland vs not cropland, or one "unsure"; this is the
                       disagreement that counts for the estimates.
  - crop_fallow_only:  both say cropland but one says crop, the other fallow.
Both kinds of difference go to adjudication.csv, with both people's answers
side by side. A third person fills the "final" column there; running this
script again copies those into labels_final.csv.

Each labeller also says about how much of the box is cropland (crop_share:
0, <10, 10-25, 25-50, >50 %). The final share is the mean of the class
middles (0, 5, 17.5, 37.5, 75 %) of the labellers whose label agrees with the
final cropland / not cropland; 0 for a final "not crop".

Outputs (cropland/): labels_merged.csv, adjudication.csv, labels_final.csv
    labels_final.csv: id, final, cropland (1/0, empty if unsure), crop_share (0-1,
    empty if unsure), disagreed, crop_fallow_only

Run from group_repo: python cropland/06_merge_labels.py
"""

import pandas as pd

import common as C

ANSWERS = ["cover", "cue_a_bare", "cue_b_greenup", "cue_c_harvest", "cue_d_shape", "cue_e_crop2024",
           "label", "crop_share", "confidence", "notes"]
CROPLAND = {"crop", "fallow"}
SHARE_MID = {"0": 0.0, "<10": 0.05, "10-25": 0.175, "25-50": 0.375, ">50": 0.75}   # middle of each class


def classify(l1, l2):
    if l1 is None or l2 is None:
        return "", 0, 0                                   # not labelled twice yet
    if l1 == l2:
        return l1, 0, 0
    if l1 in CROPLAND and l2 in CROPLAND:
        return "", 0, 1                                   # crop vs fallow
    return "", 1, 0


def main() -> None:
    sample = pd.read_csv(C.HERE / "sample.csv")
    sheets = [pd.read_csv(f, dtype={"crop_share": str}) for f in sorted([*C.HERE.glob("sample_labels_*.csv"), *(C.HERE / "labels").glob("sample_labels_*.csv")])]
    if not sheets:
        print("No sample_labels_<name>.csv yet (export them from the labelling tool).")
        return
    lab = pd.concat(sheets)
    lab = lab[lab.label.notna()]
    old = lab[lab.get("unit", pd.Series(index=lab.index, dtype=object)).ne(f"{C.BOX_M}m")]
    if len(old):                                          # saved by a cached copy of the old 10 m tool
        print(f"WARNING: {len(old)} sample labels were not made on the {C.BOX_M} m box "
              f"({', '.join(sorted(old.labeller.unique()))}); reload the tool and relabel those points.")
    get = lambda i, who: lab[(lab.id == i) & (lab.labeller == who)]
    rows = []
    for p in sample.itertuples():
        a, b = get(p.id, p.labeller_1), get(p.id, p.labeller_2)
        l1 = a.label.iloc[0] if len(a) else None
        l2 = b.label.iloc[0] if len(b) else None
        final, dis, cf = classify(l1, l2)
        rows.append({"id": p.id, "label_1": l1, "label_2": l2, "final": final,
                     "disagreed": dis, "crop_fallow_only": cf})
    merged = pd.DataFrame(rows)
    merged.to_csv(C.HERE / "labels_merged.csv", index=False)

    adj_path = C.HERE / "adjudication.csv"
    todo = merged[(merged.disagreed == 1) | (merged.crop_fallow_only == 1)]
    if adj_path.exists():
        adj = pd.read_csv(adj_path)[["id", "final"]].dropna()
        merged = merged.set_index("id")
        merged.loc[adj.id, "final"] = adj.final.values
        merged = merged.reset_index()
        new = set(todo.id) - set(pd.read_csv(adj_path).id)
        if new:
            print(f"{len(new)} newly disagreed points are not in adjudication.csv yet; "
                  "rename the old file and run again to rebuild it.")
    elif len(todo):
        wide = lab[lab.id.isin(todo.id)].pivot_table(index="id", columns="labeller", values=ANSWERS, aggfunc="first")
        wide.columns = [f"{c}_{w}" for c, w in wide.columns]
        wide = wide.join(todo.set_index("id")[["disagreed", "crop_fallow_only"]])
        wide.assign(final="").to_csv(adj_path)
        print(f"{len(todo)} points written to adjudication.csv for a third person "
              f"({todo.disagreed.sum()} cropland vs not, {todo.crop_fallow_only.sum()} crop vs fallow).")

    both = merged.label_1.notna() & merged.label_2.notna()
    k = merged[both]
    print(f"{both.sum()} of {len(merged)} points labelled twice; "
          f"agreement on cropland vs not: {1 - k.disagreed.mean():.0%}")
    done = merged[merged.final.isin(["crop", "fallow", "not crop", "unsure"])].copy()
    done["cropland"] = done.final.map({"crop": 1, "fallow": 1, "not crop": 0})
    mid = lab.assign(mid=lab.get("crop_share", pd.Series(index=lab.index, dtype=object)).map(SHARE_MID),
                     cl=lab.label.isin(CROPLAND))

    def share(r):
        if r.final == "not crop":
            return 0.0
        if r.final not in CROPLAND:
            return float("nan")
        v = mid[(mid.id == r.id) & mid.cl].mid.dropna()
        return v.mean() if len(v) else float("nan")

    done["crop_share"] = done.apply(share, axis=1)
    no_share = done.final.isin(CROPLAND) & done.crop_share.isna()
    if no_share.any():
        print(f"WARNING: {no_share.sum()} cropland points have no crop share (labelled with an older tool): "
              f"{', '.join(done[no_share].id)}")
    done[["id", "final", "cropland", "crop_share", "disagreed", "crop_fallow_only"]].to_csv(C.HERE / "labels_final.csv", index=False)
    print(f"labels_final.csv: {len(done)} points ({(done.final == 'crop').sum()} crop, "
          f"{(done.final == 'fallow').sum()} fallow, {(done.final == 'unsure').sum()} unsure)")


if __name__ == "__main__":
    main()
