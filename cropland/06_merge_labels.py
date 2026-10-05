"""
Step 6 - Merge the two labels of every sample point (METHODOLOGY.md section 4).

Labels are crop / fallow / not crop / unsure, for the 210 m box around the
point: crop if any field in the box was cropped in 2025, fallow if the box has
a field but none was cropped. Cropland = crop or fallow.

Reads every sample_labels_<name>.csv saved by the labelling tool and matches
the two labels per point (the two labellers in sample.csv). Nobody settles a
disagreement: both labels are kept and the disagreement is reported.
  - agreed:            same label from both people -> that label.
  - disagreed:         cropland vs not cropland, or one "unsure" -> final
                       "disagreed". Left out of fitting; in the area estimates
                       it is bounded (all cropland / all not, 09_score.py).
  - crop_fallow_only:  both say cropland, one crop and the other fallow ->
                       final "crop/fallow": cropland for sure, cropped in 2025
                       not agreed.
Every disagreement, with both people's answers side by side, is listed in
disagreements.csv for the report.

Two kinds of value per point:
  - agreed values (cropland, crop, crop_share): only where both people agree
    on that definition, empty otherwise. These train and score the models.
  - averages of the two labellers (cropland_avg, crop_avg, share_avg,
    share_crop_avg; "unsure" left out): every point labelled twice has them,
    disagreed or not, so the area estimates need no tiebreaker. For a point
    both agree on they equal the agreed values.

Each labeller also says about how much of the box is cropland (crop_share:
0, <10, 10-25, 25-50, >50 %), turned into the class middle (0, 5, 17.5, 37.5,
75 %); 0 for "not crop". share_crop_avg counts the share only where the
labeller said crop (for the cropped-in-2025 area).

Outputs (cropland/): labels_merged.csv (both labels per point), disagreements.csv,
    labels_final.csv: id, final, cropland, crop, crop_share (agreed, else empty),
    cropland_avg, crop_avg, share_avg, share_crop_avg (0-1), disagreed,
    crop_fallow_only, confidence (lower of the two),
    and model_table.csv (one row per point for models and dashboards, model_data.py).

Run from group_repo: python cropland/06_merge_labels.py
"""

import pandas as pd

import common as C
import model_data as M

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
        return "crop/fallow", 0, 1                        # cropland for sure, cropped not agreed
    return "disagreed", 1, 0


def main() -> None:
    sample = pd.read_csv(C.HERE / "sample.csv")
    sheets = [pd.read_csv(f, dtype={"crop_share": str}) for f in sorted([*C.HERE.glob("sample_labels_*.csv"), *(C.HERE / "labels").glob("sample_labels_*.csv")])]
    if not sheets:
        print("No sample_labels_<name>.csv yet (export them from the labelling tool).")
        return
    lab = pd.concat(sheets)
    lab = lab[lab.label.notna()]
    mine = lab.merge(sample[["id", "labeller_1", "labeller_2"]], on="id", how="left")
    stray = mine[(mine.labeller != mine.labeller_1) & (mine.labeller != mine.labeller_2)]
    if len(stray):                                        # a point that was not assigned to this person
        print(f"WARNING: {len(stray)} labels by someone not assigned to the point, ignored: "
              f"{', '.join(stray.labeller + ' ' + stray.id)}")
    twice = lab.duplicated(["id", "labeller"], keep=False)
    if twice.any():
        print(f"WARNING: {lab[twice].id.nunique()} points saved twice by the same person; the last one is used.")
        lab = lab.drop_duplicates(["id", "labeller"], keep="last")
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
        c = pd.to_numeric(pd.concat([a.confidence, b.confidence]), errors="coerce")
        final, dis, cf = classify(l1, l2)
        rows.append({"id": p.id, "labeller_1": p.labeller_1, "label_1": l1,
                     "labeller_2": p.labeller_2, "label_2": l2, "final": final,
                     "disagreed": dis, "crop_fallow_only": cf, "confidence": c.min() if len(c) else None})
    merged = pd.DataFrame(rows)
    merged.to_csv(C.HERE / "labels_merged.csv", index=False)

    todo = merged[(merged.disagreed == 1) | (merged.crop_fallow_only == 1)]
    if len(todo):                                         # for the report: both answers side by side
        wide = lab[lab.id.isin(todo.id)].pivot_table(index="id", columns="labeller", values=ANSWERS, aggfunc="first")
        wide.columns = [f"{c}_{w}" for c, w in wide.columns]
        wide.join(todo.set_index("id")[["labeller_1", "labeller_2", "disagreed", "crop_fallow_only"]]).to_csv(
            C.HERE / "disagreements.csv")

    both = merged.label_1.notna() & merged.label_2.notna()
    k = merged[both]
    print(f"{both.sum()} of {len(merged)} points labelled twice; "
          f"agreement on cropland vs not: {1 - k.disagreed.mean():.0%}; "
          f"{k.disagreed.sum()} disagreed, {k.crop_fallow_only.sum()} crop vs fallow (disagreements.csv)")
    if both.any():                                        # per pair, for the report
        pair = k.labeller_1 + " & " + k.labeller_2
        print(k.assign(pair=pair).groupby("pair").agg(points=("id", "size"), disagreed=("disagreed", "mean"),
                                                      crop_vs_fallow=("crop_fallow_only", "mean")).round(2).to_string())
    done = merged[merged.final != ""].copy()
    # each labeller's values (unsure = empty), then the mean of the point's two labellers
    mine = mine.drop_duplicates(["id", "labeller"], keep="last")
    mine = mine[(mine.labeller == mine.labeller_1) | (mine.labeller == mine.labeller_2)]
    sh = mine.get("crop_share", pd.Series(index=mine.index, dtype=object)).map(SHARE_MID)
    one = pd.DataFrame({"id": mine.id,
                        "cropland_avg": mine.label.map({"crop": 1, "fallow": 1, "not crop": 0}),
                        "crop_avg": mine.label.map({"crop": 1, "fallow": 0, "not crop": 0}),
                        "share_avg": sh.where(mine.label.isin(CROPLAND), mine.label.map({"not crop": 0.0})),
                        "share_crop_avg": sh.where(mine.label == "crop", mine.label.map({"fallow": 0.0, "not crop": 0.0}))})
    done = done.merge(one.groupby("id").mean(), on="id", how="left")
    ok = (done.disagreed == 0) & (done.final != "unsure")
    done["cropland"] = done.cropland_avg.where(ok)
    done["crop"] = done.crop_avg.where(ok & (done.crop_fallow_only == 0))
    done["crop_share"] = done.share_avg.where(ok)
    no_share = (done.cropland_avg > 0) & done.share_avg.isna()
    if no_share.any():
        print(f"WARNING: {no_share.sum()} cropland points have no crop share (labelled with an older tool): "
              f"{', '.join(done[no_share].id)}")
    done[["id", "final", "cropland", "crop", "crop_share", "cropland_avg", "crop_avg", "share_avg",
          "share_crop_avg", "disagreed", "crop_fallow_only", "confidence"]].to_csv(C.HERE / "labels_final.csv", index=False)
    print(f"labels_final.csv: {len(done)} points ({(done.final == 'crop').sum()} crop, "
          f"{(done.final == 'fallow').sum()} fallow, {(done.final == 'not crop').sum()} not crop, "
          f"{(done.final == 'crop/fallow').sum()} crop/fallow, {(done.final == 'unsure').sum()} unsure, "
          f"{(done.final == 'disagreed').sum()} disagreed)")
    print(f"model_table.csv: {len(M.write_table())} points")


if __name__ == "__main__":
    main()
