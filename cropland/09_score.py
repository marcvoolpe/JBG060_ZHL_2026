"""
Step 9 - Scores and the area estimate (METHODOLOGY.md section 7).

  1. Map values at every sample point: the 7 public maps (Earth Engine), ASAP
     (local file, crop if the cell is 5% crop or more, as in Kerner et al. 2024),
     our Rule 1 (from the frozen JSON file) and the two random-forest benchmarks.
  Two reference definitions throughout: cropland (crop + fallow) and
  cropped in 2025 (crop only), because the maps define cropland differently.
  2. Accuracy of each map on the TEST points only: user's accuracy
     (precision), producer's accuracy (recall), overall accuracy and F1 with
     standard errors, per study area.
  3. Cropland area per study area from the reference labels of ALL points,
     with a 95% interval, plus the sensitivity check (all disagreed points
     crop / all not crop).

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
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(r.lon, r.lat), {"id": r.id}) for r in part.itertuples()])
        rows += [f["properties"] for f in stack.reduceRegions(fc, ee.Reducer.first(), scale=10).getInfo()["features"]]
    df = pd.DataFrame(rows)
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
            ref_all = a.final.isin(pos).to_numpy()
            est, se = E.area(ref_all.astype(float), a.stratum.to_numpy(), w)
            sens = [E.area(np.where(dis, v, ref_all).astype(float), a.stratum.to_numpy(), w)[0] for v in (1, 0)]
            areas.append({"area": area, "definition": ref_name, "points": len(a),
                          "unsure_left_out": int((d[d.area == area].final == "unsure").sum()),
                          "share": est, "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se,
                          "ha": est * ha, "ci_low_ha": (est - 1.96 * se) * ha, "ci_high_ha": (est + 1.96 * se) * ha,
                          "share_if_disagreed_all_cropland": sens[0], "share_if_disagreed_all_not": sens[1]})
            t = a[a.split == "test"]
            ref = t.final.isin(pos).astype(int).to_numpy()
            for m in maps:
                r = E.accuracy(t[m].to_numpy(), ref, t.stratum.to_numpy(), w)
                acc.append({"area": area, "definition": ref_name, "map": m, "year": years[m],
                            "test_points": len(t), **r})
    pd.DataFrame(areas).to_csv(RES / "area.csv", index=False)
    out = pd.DataFrame(acc)
    out.to_csv(RES / "accuracy.csv", index=False)
    print(pd.DataFrame(areas).round(4).to_string(index=False))
    print(out.round(3).sort_values(["area", "definition", "f1"], ascending=[True, True, False]).to_string(index=False))


if __name__ == "__main__":
    main()
