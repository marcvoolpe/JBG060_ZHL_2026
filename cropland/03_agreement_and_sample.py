"""
Step 3 - Agreement map, stratum areas and the real sample (METHODOLOGY.md section 3).

For each study area:
  1. counts how many of the 7 public maps call each 10 m pixel crop;
  2. groups pixels into strata A (0 maps), B (1-2), C (3+) and measures each
     stratum's area in hectares (ee.Image.pixelArea, so areas are real);
  3. draws the allocated number of random points per stratum (seed 42),
     keeps them at least 100 m apart, and splits each stratum one third
     calibration / two thirds test;
  4. assigns every point to two of the five labellers: within each
     area x stratum x split group the points go round all 10 pairs in turn,
     so every pair shares the same number of points (45) and every labeller
     gets the same mix of areas, strata and calibration/test (180 each).

Outputs (in cropland/, small, kept in git):
  strata_areas.csv   area, stratum, hectares, share
  sample.csv         id, area, stratum, lat, lon, split, labeller_1, labeller_2

Two runs, because the agreement map is too heavy to compute on the fly
(Dynamic World's yearly mode over 4.5 M ha):
  python cropland/03_agreement_and_sample.py export   saves the strata and
      agreement map of each study area as an Earth Engine asset (batch task,
      ~30-60 min; follow it at https://code.earthengine.google.com/tasks)
  python cropland/03_agreement_and_sample.py sample   when the tasks are done:
      stratum areas, the sample and the split, from the saved assets.
  python cropland/03_agreement_and_sample.py labellers   only redoes step 4 on
      the existing sample.csv (no Earth Engine; ids, points and split stay),
      and copies the new pairs into label_tool/data_sample.js. Only before
      anyone has labelled the sample.
The labeller names are set in LABELLERS below.
"""

import json
import sys
from itertools import combinations

import numpy as np
import pandas as pd

import common as C

LABELLERS = ["Matteo", "Marc", "Yassin", "Wei", "Matei"]
MIN_DISTANCE_M = 100
OVERSAMPLE = 3                    # draw extra points so the distance rule can drop some


def asset(area):
    return f"{C.ASSETS}/strata_{area}"


def export(ee):
    try:
        ee.data.createAsset({"type": "FOLDER"}, C.ASSETS)
    except ee.EEException:
        pass                                                # folder already exists
    for area in C.AREAS:
        geom = C.area_geometry(ee, area)
        img = C.strata(ee).addBands(C.agreement(ee).toByte()).clip(geom)
        task = ee.batch.Export.image.toAsset(image=img, description=f"strata_{area}", assetId=asset(area),
                                             region=geom, scale=10, maxPixels=1e13)
        task.start()
        print(f"started export of {asset(area)} (task {task.id})")


def stratum_areas(ee, area, geom):
    img = ee.Image.pixelArea().divide(1e4).addBands(ee.Image(asset(area)).select("stratum"))
    res = img.reduceRegion(ee.Reducer.sum().group(groupField=1, groupName="stratum"),
                           geom, scale=10, maxPixels=1e13, tileScale=8).getInfo()
    rows = [{"area": area, "stratum": "ABC"[g["stratum"] - 1], "ha": g["sum"]} for g in res["groups"]]
    df = pd.DataFrame(rows)
    df["share"] = df.ha / df.ha.sum()
    return df


MIN_SHARE = 0.001            # strata smaller than 0.1% of their area are merged down (METHODOLOGY.md 3.4)


def merge_small(areas):
    """Merge C into B, then B into A, while the stratum is under MIN_SHARE; its points move with it.

    Returns (areas after merging, {old stratum code: new code}, allocation after merging).
    """
    area = areas.area.iloc[0]
    share = dict(zip(areas.stratum, areas.share))
    alloc = dict(C.ALLOCATION[area])
    target = {"A": "A", "B": "B", "C": "C"}
    for small, into in (("C", "B"), ("B", "A")):
        if share.get(small, 0) < MIN_SHARE and alloc.get(small):
            print(f"  {area}: stratum {small} is {share.get(small, 0):.4%} of the area, merged into {into}")
            share[into] = share.get(into, 0) + share.pop(small, 0)
            alloc[into] += alloc.pop(small)
            for k, v in target.items():
                if v == small:
                    target[k] = into
    merged = areas.assign(stratum=areas.stratum.map(target)).groupby(["area", "stratum"], as_index=False).ha.sum()
    merged["share"] = merged.ha / merged.ha.sum()
    codes = {"ABC".index(k) + 1: "ABC".index(v) + 1 for k, v in target.items()}
    return merged, codes, alloc


def draw(ee, area, geom, codes, alloc):
    strata = ee.Image(asset(area)).select("stratum").remap(list(codes), list(codes.values())).rename("stratum")
    kept = sorted(set(codes.values()))
    pts = strata.stratifiedSample(
        numPoints=0, classBand="stratum", region=geom, scale=10, seed=C.SEED, geometries=True,
        classValues=kept, classPoints=[OVERSAMPLE * alloc["ABC"[c - 1]] for c in kept]).getInfo()
    df = pd.DataFrame([{"stratum": "ABC"[f["properties"]["stratum"] - 1],
                        "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1]}
                       for f in pts["features"]])
    df = df.sample(frac=1, random_state=C.SEED)          # random order before thinning
    keep, xy = [], []
    for r in df.itertuples():                            # greedy thinning to >= 100 m apart
        p = np.array([r.lon * 111_320 * np.cos(np.radians(r.lat)), r.lat * 110_540])
        if all(np.hypot(*(p - q)) >= MIN_DISTANCE_M for q in xy):
            keep.append(r.Index); xy.append(p)
    df = df.loc[keep]
    parts = []
    for s in alloc:
        d = df[df.stratum == s].head(alloc[s]).copy()
        if len(d) < alloc[s]:
            print(f"  {area} stratum {s}: only {len(d)} of {alloc[s]} points available")
        n_cal = round(len(d) / 3)
        d["split"] = ["calibration"] * n_cal + ["test"] * (len(d) - n_cal)
        parts.append(d)
    out = pd.concat(parts)
    out.insert(0, "area", area)
    return out


def assign_labellers(df):
    """Shuffle the points (the ids follow this order), then give each two labellers."""
    order = np.random.default_rng(C.SEED).permutation(len(df))
    return pair_up(df.iloc[order].reset_index(drop=True))


def pair_up(df):
    """Two labellers per point: inside each area x stratum x split group (in the
    shuffled order) the points go round all 10 pairs in turn, continuing from one
    group to the next. Every group here is a multiple of 10 points, so each pair
    gets exactly 1/10 of every group."""
    pairs = list(combinations(LABELLERS, 2))
    turn = df.sort_values(["area", "stratum", "split"], kind="stable").index
    k = pd.Series(np.arange(len(df)), index=turn).sort_index()
    df["labeller_1"] = [pairs[i % len(pairs)][0] for i in k]
    df["labeller_2"] = [pairs[i % len(pairs)][1] for i in k]
    return df


def relabel_existing():
    """New pairs for the existing sample.csv (same ids, points and split), also in the tool's data file."""
    sample = pair_up(pd.read_csv(C.HERE / "sample.csv"))
    sample.to_csv(C.HERE / "sample.csv", index=False)
    js = C.HERE / "label_tool" / "data_sample.js"
    head, body = js.read_text().split(" = ", 1)
    recs = json.loads(body.rstrip().rstrip(";"))
    who = sample.set_index("id")[["labeller_1", "labeller_2"]]
    for r in recs:
        r["labellers"] = list(who.loc[r["id"]])
    js.write_text(f"{head} = " + json.dumps(recs) + ";\n")
    return sample


def report(sample):
    both = pd.concat([sample.assign(who=sample.labeller_1), sample.assign(who=sample.labeller_2)], ignore_index=True)
    print((sample.labeller_1 + " & " + sample.labeller_2).value_counts().to_string())
    print(pd.crosstab(both.who, [both.area, both.stratum, both.split]).to_string())


def main() -> None:
    if sys.argv[1:] == ["labellers"]:
        report(relabel_existing())
        return
    ee = C.ee_init()
    if sys.argv[1:] == ["export"]:
        export(ee)
        return
    areas, samples = [], []
    for area in C.AREAS:
        geom = C.area_geometry(ee, area)
        print(f"{area}: stratum areas ...")
        merged, codes, alloc = merge_small(stratum_areas(ee, area, geom))
        areas.append(merged)
        print(merged.to_string(index=False))
        print(f"{area}: drawing points {alloc} ...")
        samples.append(draw(ee, area, geom, codes, alloc))
    pd.concat(areas).to_csv(C.HERE / "strata_areas.csv", index=False)
    sample = assign_labellers(pd.concat(samples))
    sample.insert(0, "id", [f"S{i + 1:03d}" for i in range(len(sample))])
    sample = sample.round({"lat": 6, "lon": 6})
    sample.to_csv(C.HERE / "sample.csv", index=False)
    print(sample.groupby(["area", "stratum", "split"]).size().unstack())
    report(sample)


if __name__ == "__main__":
    main()
