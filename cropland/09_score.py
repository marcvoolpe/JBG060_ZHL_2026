"""
Step 9 - Scores and the area estimate (METHODOLOGY.md section 7).

  1. Map values at every sample point: the 7 public maps (Earth Engine), ASAP
     (local file, crop if the cell is 5% crop or more, as in Kerner et al. 2024),
     our Rule 1 (from the frozen JSON file) and the two random-forest benchmarks.
     The reference label says whether there is cropland ANYWHERE in the 210 m
     box around the point, so a public map says crop there when it calls at
     least one pixel of that box crop (its share of the box is kept as
     <map>_share). Rule 1 and the benchmarks already work on box features.
     ASAP cells (~1 km) are larger than the box and are read at the point.
  Two reference definitions throughout: cropland (crop + fallow) and
  cropped in 2025 (crop only), because the maps define cropland differently.
  2. Accuracy of each map on the TEST points only: user's accuracy
     (precision), producer's accuracy (recall), overall accuracy and F1 with
     standard errors, per study area.
  3. Cropland area per study area from the reference labels of ALL points,
     with a 95% interval, two ways:
       measure "share of box" (main): the labellers' share of each box that is
       cropland; its mean over random boxes is the cropland share of the land.
       For cropped_2025 the share counts in boxes labelled crop only.
       measure "box holds it" (upper bound): 1 if there is any cropland in the
       box. Larger than the cropland area, the more so the more scattered the
       fields are; plus the sensitivity check (all disagreed points crop / not).
  4. For the public maps, their share of each box against the labelled share
     on the test points (cropland only): mean of each and mean absolute gap.

Outputs (cropland/results/): map_values.csv, accuracy.csv, area.csv
Run from group_repo: python cropland/09_score.py cropland/rule1_<date>.json
"""

import sys

import joblib
import numpy as np
import pandas as pd
import rasterio

import common as C
import estimators as E
import features as F
import rules as R

RES = C.HERE / "results"


def public_values(ee, s):
    maps = C.public_maps(ee)
    stack = ee.Image.cat([img for img, _ in maps.values()])
    rows = []
    for i in range(0, len(s), 200):
        part = s.iloc[i:i + 200]
        fc = ee.FeatureCollection([ee.Feature(C.box(ee, r.lon, r.lat), {"id": r.id}) for r in part.itertuples()])
        rows += [f["properties"] for f in stack.reduceRegions(fc, ee.Reducer.mean(), scale=10).getInfo()["features"]]
    df = pd.DataFrame(rows)
    for k in maps:                                  # share of the box the map calls crop -> any crop, like the labels
        df[f"{k}_share"] = df[k]
        df[k] = (df[k] > 0).astype(int)
    with rasterio.open(C.RAW / "farmland" / "asap_mask_crop_v04.tif") as src:
        v = np.array([x[0] for x in src.sample(zip(s.lon, s.lat))])
    df["asap_v04"] = ((v >= 5) & (v <= 100)).astype(int)
    return df, {k: y for k, (_, y) in maps.items()} | {"asap_v04": "2017-23"}


def main() -> None:
    rule_files = sys.argv[1:]
    RES.mkdir(exist_ok=True)
    s = pd.read_csv(C.HERE / "sample.csv")
    lab = pd.read_csv(C.HERE / "labels_final.csv")
    feats = pd.read_csv(C.HERE / "features_sample.csv")
    ee = C.ee_init()

    vals, years = public_values(ee, s)
    d = s.merge(feats, on="id").merge(vals, on="id")
    for f in rule_files:
        rs = R.load(f)
        d[rs["name"]] = R.predict(rs, d)
        years[rs["name"]] = "2025 (ours)"
    bm = joblib.load(C.OUT / "benchmarks.joblib")
    d["rf_features"] = bm["rf"].predict(d[F.FEATURES].fillna(bm["fill"]).to_numpy())
    emb = pd.read_csv(C.HERE / "embedding_sample.csv").set_index("id").loc[d.id, bm["embedding_cols"]]
    d["rf_embedding"] = bm["rf_embedding"].predict(emb.to_numpy())
    years |= {"rf_features": "2025 (benchmark)", "rf_embedding": "2025 (benchmark)"}
    d = d.merge(lab, on="id", how="left")
    d.to_csv(RES / "map_values.csv", index=False)

    W = pd.read_csv(C.HERE / "strata_areas.csv")
    maps = list(years)
    refs = {"cropland": {"crop", "fallow"}, "cropped_2025": {"crop"}}   # the two definitions we report
    acc, areas = [], []
    for area in C.AREAS:
        w = W[W.area == area].set_index("stratum").share.to_dict()
        ha = W[W.area == area].ha.sum()
        a = d[(d.area == area) & d.final.isin(["crop", "fallow", "not crop"])]
        dis = (a.disagreed == 1).to_numpy()
        for ref_name, pos in refs.items():
            unsure = int((d[d.area == area].final == "unsure").sum())
            row = lambda measure, est, se, n, **extra: {
                "area": area, "definition": ref_name, "measure": measure, "points": n, "unsure_left_out": unsure,
                "share": est, "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se,
                "ha": est * ha, "ci_low_ha": (est - 1.96 * se) * ha, "ci_high_ha": (est + 1.96 * se) * ha, **extra}
            # main: the share of each box that is cropland
            s_ok = a[a.crop_share.notna()]
            y = np.where(s_ok.final.isin(pos), s_ok.crop_share, 0.0)
            est, se = E.area(y.astype(float), s_ok.stratum.to_numpy(), w)
            areas.append(row("share of box", est, se, len(s_ok), no_share_left_out=len(a) - len(s_ok)))
            # upper bound: the box holds cropland
            ref_all = a.final.isin(pos).to_numpy()
            est, se = E.area(ref_all.astype(float), a.stratum.to_numpy(), w)
            sens = [E.area(np.where(dis, v, ref_all).astype(float), a.stratum.to_numpy(), w)[0] for v in (1, 0)]
            areas.append(row("box holds it (upper bound)", est, se, len(a),
                             share_if_disagreed_all_cropland=sens[0], share_if_disagreed_all_not=sens[1]))
            t = a[a.split == "test"]
            ref = t.final.isin(pos).astype(int).to_numpy()
            ts = t[t.crop_share.notna()]
            for m in maps:
                r = E.accuracy(t[m].to_numpy(), ref, t.stratum.to_numpy(), w)
                if ref_name == "cropland" and f"{m}_share" in ts:          # public maps: share of the box vs labelled share
                    st = ts.stratum.to_numpy()
                    r |= {"box_share_map": E.area(ts[f"{m}_share"].to_numpy(float), st, w)[0],
                          "box_share_ref": E.area(ts.crop_share.to_numpy(float), st, w)[0],
                          "box_share_mae": E.area((ts[f"{m}_share"] - ts.crop_share).abs().to_numpy(float), st, w)[0]}
                acc.append({"area": area, "definition": ref_name, "map": m, "year": years[m],
                            "test_points": len(t), **r})
    pd.DataFrame(areas).to_csv(RES / "area.csv", index=False)
    out = pd.DataFrame(acc)
    out.to_csv(RES / "accuracy.csv", index=False)
    print(pd.DataFrame(areas).round(4).to_string(index=False))
    print(out.round(3).sort_values(["area", "definition", "f1"], ascending=[True, True, False]).to_string(index=False))


if __name__ == "__main__":
    main()
