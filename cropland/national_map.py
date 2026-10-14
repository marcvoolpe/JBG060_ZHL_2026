"""
Our map over the whole country: how much it marks, counted from its native pixels, per study area and per state,
and how its state ranking compares with the FAO/WFP crop assessment (CFSAM 2025).

    python cropland/national_map.py summary cropland/rule1_2026-10-12.json      (Earth Engine, about a minute)

Writes results/rule1_map_share.csv (study areas: 10 m map, 30 m national map, and the stratified estimate of the
map's share from the labelled points) and results/rule1_national_by_state.csv (share and hectares per state, CFSAM
2025 cereal area, rank correlation in the file name's notes column).

Counting rule: a 0/1 map must be averaged from its native pixels (reduceResolution). Earth Engine's coarser overview
layers round every cell to 0 or 1, which distorts shares read at 1 km (Northern Bahr el Ghazal: 31% instead of 23.6%).
A pixel of our map means "the 210 m box around it holds a cropped field": its hectares are an upper bound, and outside
the two study areas the map is not checked.
"""

import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from scipy.stats import spearmanr

import common as C
import estimators as E
import rules as R

RES = C.HERE / "results"


def exact_share(ee, img, geom, out_m=300):
    """Mean of a 0/1 image over a region, from its native pixels."""
    agg = img.unmask(0).toFloat().reduceResolution(ee.Reducer.mean(), maxPixels=4096).reproject(crs=img.projection().crs(), scale=out_m)
    return agg.reduceRegion(ee.Reducer.mean(), geom, scale=out_m, tileScale=8, maxPixels=1e11).getInfo()


def summary(rule_file: Path) -> None:
    ee = C.ee_init()
    name = R.load(rule_file)["name"]
    nat = ee.Image(f"{C.ASSETS}/{rule_file.stem}_south_sudan")
    v, W = pd.read_csv(RES / "map_values.csv"), pd.read_csv(C.HERE / "strata_areas.csv")
    rows = []
    for area in C.AREAS:
        g = C.area_geometry(ee, area, simplify_deg=0.002)
        w = W[W.area == area].set_index("stratum").share.to_dict()
        d = v[v.area == area]
        est, se = E.area(d[name].to_numpy(float), d.stratum.to_numpy(), w)
        rows.append({"area": area, "map_10m_pct": 100 * list(exact_share(ee, ee.Image(f"{C.ASSETS}/{rule_file.stem}_{area}"), g).values())[0],
                     "map_30m_national_pct": 100 * list(exact_share(ee, nat, g).values())[0],
                     "from_labelled_points_pct": 100 * est, "from_labelled_points_se": 100 * se, "points": len(d)})
    pd.DataFrame(rows).round(2).to_csv(RES / "rule1_map_share.csv", index=False)
    print(pd.DataFrame(rows).round(1).to_string(index=False))

    adm1 = gpd.read_file(C.ADMIN2.parent / "ssd_admin1.geojson")
    col = [c for c in adm1.columns if c.startswith("adm1_name")][0]
    adm1["ha"] = adm1.to_crs(6933).area / 1e4
    fc = ee.FeatureCollection(json.loads(adm1[[col, "geometry"]].assign(geometry=adm1.geometry.simplify(0.01)).to_json()))
    agg = nat.unmask(0).toFloat().reduceResolution(ee.Reducer.mean(), maxPixels=4096).reproject(crs=nat.projection().crs(), scale=300)
    got = agg.reduceRegions(fc, ee.Reducer.mean(), scale=300, tileScale=16).getInfo()["features"]
    t = pd.DataFrame([{"state": f["properties"][col], "map_share": f["properties"].get("mean") or 0} for f in got])
    t = t.merge(adm1[[col, "ha"]].rename(columns={col: "state"}), on="state")
    cf = pd.read_csv(C.HERE / "reference_statistics.csv")
    cf = cf[(cf.source == "CFSAM") & (cf.year == 2025) & (cf.level == "state")].set_index("name").cereal_harvested_ha
    t = t.join(cf.rename("cfsam_2025_cereal_ha"), on="state")
    t["map_pct"], t["map_ha"] = 100 * t.map_share, t.map_share * t.ha
    t["cfsam_pct"] = 100 * t.cfsam_2025_cereal_ha / t.ha
    rho = spearmanr(t.map_pct, t.cfsam_pct, nan_policy="omit")[0]
    t["notes"] = f"rank correlation with CFSAM 2025 (share of land): {rho:.2f}; map hectares = land whose 210 m box holds crop (upper bound), not checked outside Aweil and Bor South"
    t.drop(columns="map_share").round(2).to_csv(RES / "rule1_national_by_state.csv", index=False)
    print(t[["state", "map_pct", "cfsam_pct"]].round(1).sort_values("map_pct", ascending=False).to_string(index=False))
    print(f"South Sudan: {100 * t.map_ha.sum() / t.ha.sum():.1f}% of the land, {t.map_ha.sum():,.0f} ha; rank correlation with CFSAM {rho:.2f}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["summary"] and len(sys.argv) == 3:
        summary(Path(sys.argv[2]))
    else:
        raise SystemExit(__doc__)
