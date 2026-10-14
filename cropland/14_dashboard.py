"""
Step 14 - The results dashboard: one HTML file, no server, no Earth Engine (DASHBOARD_PLAN.md).

Reads the result tables in cropland/results/ (and a few in deliverables/cropland_report/tables/), packs them
into one JSON block and writes it into cropland/dashboard/template.html, which holds the pages, the charts and
the map (plain JavaScript and SVG/canvas, no library, so the file also opens without internet).

    python cropland/14_dashboard.py          -> deliverables/cropland_report/dashboard.html

Pages (one JavaScript function each in the template, so people can work on them separately):
  1 headline        cropland 2025 from the sample against what the public maps say
  2 maps            which map finds the fields (test points), our models, Bor South false crop
  3 exposure        flooded cropland 2000-2025 under every map and the sample; 2022 in detail; the before/after map
  4 action          trigger hindcast with a threshold, households behind the hectares, which map to use where
  5 country         our map over South Sudan, its accuracy on our test points, the national check sample
  6 hand-over       the systems we deliver for future work and groups
  7 limits          how sure we are and what the numbers cannot say

Units (as everywhere in this folder): a public map's hectares are its pixels; the sample's main measure is the
labelled share of each 210 m box ("share of box"). Our map (Rule 1) says "the 210 m box around this pixel holds a
field", so its hectares are compared with the sample's "box holds it" measure, never with the share of box.
"""

import json
from datetime import date

import geopandas as gpd
import numpy as np
import pandas as pd

import common as C
import eda_maps as EM

RES = C.HERE / "results"
KIT = C.REPO / "deliverables" / "cropland_report"
TABLES = KIT / "tables"
OUT = KIT / "dashboard.html"
TEMPLATE = C.HERE / "dashboard" / "template.html"

PUBLIC = ["worldcover_2021", "glad_2019", "deafrica_2019", "worldcereal_2021", "esri_2025", "dynamicworld_2025",
          "gfsad_2015", "asap_v04"]
EXTRA = ["esri_2022", "dynamicworld_2022"]                  # the same products in their 2022 edition (flood years)
OURS = {"rule1": "Our map (Rule 1)", "map_30m_national": "Our map, 30 m national run",
        "logistic_l2": "Logistic regression, 18 inputs", "logistic_rule1_inputs": "Logistic regression, Rule 1's 2 inputs",
        "rf_features": "Random forest, 18 inputs (benchmark)", "rf_embedding": "Random forest, embeddings (benchmark)"}
NAMES = EM.NAMES | OURS | {"asap_v04": "ASAP v04"}
TITLES = {"aweil": "Aweil counties", "bor_south": "Bor South"}
BEST = {"aweil": "worldcereal_2021", "bor_south": "gfsad_2015"}


def r(x, k=1):
    return None if x is None or pd.isna(x) else round(float(x), k)


def headline():
    aa = pd.read_csv(RES / "area_adjusted.csv")
    pcb = pd.read_csv(RES / "pixel_count_bias.csv")
    ms = pd.read_csv(RES / "rule1_map_share.csv").set_index("area")
    cf = pd.read_csv(C.HERE / "reference_statistics.csv").drop_duplicates()
    cf = cf[(cf.source == "CFSAM") & (cf.year == 2025) & (cf.level == "county")]
    W = pd.read_csv(C.HERE / "strata_areas.csv")
    out = {}
    for area, counties in C.AREAS.items():
        a = aa[(aa.area == area) & (aa.definition == "cropland")].set_index("measure")
        s, b = a.loc["share of box"], a.loc["box holds it (upper bound)"]
        c = cf[cf.name.isin(counties)]
        land = W[W.area == area].ha.sum()
        out[area] = {
            "title": TITLES[area], "land_ha": r(land, 0), "points": int(s.points),
            "sample": {"pct": r(100 * s.estimate, 2), "low": r(100 * max(s.low, 0), 2), "high": r(100 * s.high, 2),
                       "high_adj": r(100 * s.high_adjusted, 2), "ha": r(s.ha, -2), "low_ha": r(max(s.low_ha, 0), -2),
                       "high_ha": r(s.high_ha, -2), "high_adj_ha": r(s.high_adjusted_ha, -2)},
            "box": {"pct": r(100 * b.estimate, 1), "low": r(100 * max(b.low, 0), 1), "high": r(100 * b.high, 1)},
            "maps": [{"map": m, "pct": r(p.map_pct, 2), "ratio": r(p.ratio_to_sample, 2)}
                     for m in PUBLIC for p in pcb[(pcb.area == area) & (pcb["map"] == m)].itertuples()],
            "ours_pct": r(ms.loc[area, "map_10m_pct"], 1),
            "cfsam_pct": r(100 * c.cereal_harvested_ha.sum() / land, 2), "cfsam_ha": r(c.cereal_harvested_ha.sum(), -2),
            "ha_per_household": r(c.cereal_harvested_ha.sum() / c.farming_households.sum(), 2),
        }
    return out


def scores():
    acc = pd.read_csv(RES / "accuracy.csv")
    a = acc[(acc.area == "aweil") & (acc.definition == "cropland")]
    nat = pd.read_csv(RES / "rule1_national_test_points.csv")
    n = nat[(nat.area == "aweil") & (nat.definition == "cropland") & (nat["map"] == "map_30m_national")]
    rows = pd.concat([a, n])
    kind = lambda m: "public" if m in PUBLIC else "ours" if m in ("rule1", "map_30m_national") else "model"
    aweil = [{"map": m.map, "kind": kind(m.map), "f1": r(m.f1, 3), "f1_se": r(m.f1_se, 3), "ua": r(m.ua, 3),
              "ua_se": r(m.ua_se, 3), "pa": r(m.pa, 3), "pa_se": r(m.pa_se, 3), "points": int(m.test_points)}
             for m in rows.itertuples() if m.map in PUBLIC or m.map in OURS]
    v = pd.read_csv(RES / "map_values.csv")
    t = v[(v.area == "bor_south") & (v.split == "test") & (v.cropland == 0)]
    at = pd.read_csv(RES / "rule1_map_at_points.csv").set_index("id")
    t = t.assign(map_30m_national=t.id.map(at.map_30m_national))
    bor = [{"map": m, "kind": kind(m), "false_crop": int(t[m].sum()), "of": len(t)}
           for m in PUBLIC + ["rule1", "map_30m_national", "logistic_l2", "logistic_rule1_inputs", "rf_features"] if m in t]
    agree = nat[nat.definition == "agreement with Rule 1 at the points"].set_index(["area", "map"]).f1
    return {"aweil": aweil, "bor_south_false_crop": bor,
            "agree_30m": {a: r(100 * agree.loc[(a, "map_30m_national")], 1) for a in C.AREAS}}


def history():
    h = pd.read_csv(RES / "flood_history.csv")
    out = {}
    for (area, days), g in h.groupby(["area", "min_days"]):
        years = []
        for y, gy in g.groupby("year"):
            row = {"year": int(y), "land": r(gy.flooded_land_ha.iloc[0], 0), "maps": {}, "sample": {}}
            for x in gy.itertuples():
                if x.measure == "map pixels" or x.layer == "rule1":
                    row["maps"][x.layer] = r(x.flooded_crop_ha, 0)
                elif x.layer == "sample (ratio)":
                    key = "share" if x.measure == "share of box" else "box"
                    row["sample"][key] = {"est": r(x.flooded_crop_ha, 0), "low": r(x.low_ha, 0), "high": r(x.high_ha, 0),
                                          "points": None if pd.isna(x.points_in_flood) else int(x.points_in_flood),
                                          "crop_points": None if pd.isna(x.of_them_cropland) else int(x.of_them_cropland)}
            years.append(row)
        out.setdefault(area, {})[str(days)] = years
    return out


def hindcast():
    t = pd.read_csv(RES / "trigger_hindcast.csv")
    out = {}
    for (area, days, thr), g in t.groupby(["area", "min_days", "threshold_ha"]):
        years = sorted(g.year.unique())
        layers = {m: [g[(g.layer == m) & (g.year == y)].layer_says.iloc[0] for y in years] for m in g.layer.unique()}
        sample = {}
        for meas, gm in g.groupby("compared_with"):
            first = gm.drop_duplicates("year").set_index("year").sample_says
            sample["share" if meas == "share of box" else "box"] = [first.loc[y] for y in years]
        out.setdefault(area, {}).setdefault(str(days), {})[str(thr)] = {"years": [int(y) for y in years], "layers": layers,
                                                                        "sample": sample}
    return out


def flood_2025():
    f = pd.read_csv(RES / "flooded_cropland.csv")
    b = pd.read_csv(RES / "flooded_cropland_bounds.csv")
    out = {}
    for area in C.AREAS:
        g = f[f.area == area].set_index("map")
        bb = b[(b.area == area) & (b["map"] == "reference: cropland (share of box)")].iloc[0]
        out[area] = {"land": r(g.loc["all flooded land", "flooded_crop_ha"], 0),
                     "maps": {m: r(g.loc[m, "flooded_crop_ha"], 0) for m in PUBLIC + ["rule1"] if m in g.index},
                     "points": int(bb.points_in_flood_cells), "crop_points": int(bb.of_them_cropland)}
    return out


def flood_map(area="aweil", year=2022, model="rule1"):
    t = pd.read_csv(RES / f"flood_cells_{area}_{year}.csv")
    layers = PUBLIC[:-1] + EXTRA + ["asap_v04"]
    counties = sorted(t.county.unique())
    x = t[layers + [model]].to_numpy()
    shares = np.where(x > 0, np.maximum(1, np.rint(1e4 * x)), 0).astype(int)      # 1/10,000 of the cell; any crop stays > 0
    g0, c0 = int(t.gr.min()), int(t.gc.min())
    cells = [[int(gr - g0), int(gc - c0), counties.index(cty), int(d), round(ha, 2), round(ins, 3), *sh]
             for gr, gc, cty, d, ha, ins, sh in zip(t.gr, t.gc, t.county, t.days, t.ha, t.inside, shares.tolist())]
    s = pd.read_csv(C.HERE / "sample.csv").merge(pd.read_csv(C.HERE / "labels_final.csv"), on="id")
    s = s[(s.area == area) & s.cropland_avg.notna()].copy()
    s["gr"], s["gc"] = EM.global_index(s.lat, s.lon)
    pts = s.merge(t[["gr", "gc"]], on=["gr", "gc"])
    adm = gpd.read_file(C.ADMIN2)
    b = adm[adm[C.ADMIN2_NAME].isin(C.AREAS[area])][[C.ADMIN2_NAME, "geometry"]].rename(columns={C.ADMIN2_NAME: "name"})
    b = b.assign(geometry=b.simplify(0.003))
    riv = gpd.read_file(EM.LOL).clip(tuple(b.total_bounds)) if EM.LOL.exists() else None
    if riv is not None:
        riv = riv.assign(geometry=riv.simplify(0.002))
    rnd = lambda gj: json.loads(gj, parse_float=lambda f: round(float(f), 4))
    return {"area": area, "year": year, "grid": EM.GRID, "g0": g0, "c0": c0, "layers": layers, "model": model,
            "best": layers.index(BEST[area]), "counties": counties, "cells": cells,
            "points": [[round(p.lat, 4), round(p.lon, 4), p.id, r(p.cropland_avg, 2), r(p.share_avg, 3) or 0] for p in pts.itertuples()],
            "borders": rnd(b.to_json()), "river": rnd(riv.to_json()) if riv is not None and len(riv) else None,
            "table": pd.read_csv(TABLES / f"flood_map_{area}_{year}.csv").round(1).to_dict(orient="records")}


def country():
    st = pd.read_csv(RES / "rule1_national_by_state.csv")
    ms = pd.read_csv(RES / "rule1_map_share.csv").set_index("area")
    return {"states": [{"state": x.state, "map_pct": r(x.map_pct, 1), "map_ha": r(x.map_ha, -2), "cfsam_pct": r(x.cfsam_pct, 2)}
                       for x in st.itertuples()],
            "map_pct": r(100 * st.map_ha.sum() / st.ha.sum(), 1), "map_ha": r(st.map_ha.sum(), -4),
            "share_10m": {a: r(ms.loc[a, "map_10m_pct"], 1) for a in C.AREAS},
            "share_30m": {a: r(ms.loc[a, "map_30m_national_pct"], 1) for a in C.AREAS},
            "vs_public": json.loads(pd.read_csv(RES / "rule1_national_vs_public.csv").round(2).to_json(orient="records"))   # NaN -> null
            if (RES / "rule1_national_vs_public.csv").exists() else None}


def build():
    data = {"built": date.today().isoformat(), "names": NAMES, "public": PUBLIC, "extra": EXTRA,
            "headline": headline(), "scores": scores(), "history": history(), "hindcast": hindcast(),
            "flood2025": flood_2025(), "floodmap": flood_map(), "country": country()}
    blob = json.dumps(data, separators=(",", ":"), allow_nan=False)
    page = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", blob)
    OUT.write_text(page, encoding="utf-8")
    print(f"{OUT}  ({OUT.stat().st_size / 1e6:.2f} MB)")
    return OUT


if __name__ == "__main__":
    build()
