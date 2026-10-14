"""
Our map over the whole country: how much it marks, counted from its native pixels, per study area and per state,
and how its state ranking compares with the FAO/WFP crop assessment (CFSAM 2025).

    python cropland/national_map.py summary cropland/rule1_2026-10-12.json      (Earth Engine, about a minute)
    python cropland/national_map.py fetch cropland/rule1_2026-10-12.json        (Earth Engine: ~1 km map, cached)
    python cropland/national_map.py figure                                      (figure 27, no Earth Engine)

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


CELL, BBOX = 0.01, (23.4, 3.4, 36.0, 12.3)              # ~1.1 km cells over South Sudan (west, south, east, north)
CACHE = C.OUT / "eda" / "national_rule1_1km.npz"


def fetch(rule_file: Path, strips: int = 6) -> None:
    """Share of each ~1 km cell that our national map marks, from the native 30 m pixels, plus the share inside the country."""
    import numpy as np
    ee = C.ee_init()
    nat = ee.Image(f"{C.ASSETS}/{rule_file.stem}_south_sudan")
    img = ee.Image.cat([nat.unmask(0).toFloat().rename("share"), nat.mask().toFloat().rename("inside")])
    west, south, east, north = BBOX
    nx, ny = round((east - west) / CELL), round((north - south) / CELL)
    out = {"share": np.zeros((ny, nx), np.float32), "inside": np.zeros((ny, nx), np.float32)}
    rows = np.linspace(0, ny, strips + 1).astype(int)
    for r0, r1 in zip(rows[:-1], rows[1:]):
        top = north - r0 * CELL
        t = [CELL, 0, west, 0, -CELL, top]
        agg = img.reduceResolution(ee.Reducer.mean(), maxPixels=4096).reproject(crs="EPSG:4326", crsTransform=t)
        got = ee.data.computePixels({"expression": agg, "fileFormat": "NUMPY_NDARRAY",
                                     "grid": {"dimensions": {"width": nx, "height": int(r1 - r0)}, "crsCode": "EPSG:4326",
                                              "affineTransform": {"scaleX": CELL, "shearX": 0, "translateX": west,
                                                                  "shearY": 0, "scaleY": -CELL, "translateY": top}}})
        out["share"][r0:r1], out["inside"][r0:r1] = got["share"], got["inside"]
        print(f"  rows {r0}-{r1} of {ny}", flush=True)
    np.savez_compressed(CACHE, **out, bbox=np.array(BBOX), cell=CELL)
    print("saved", CACHE)


def figure():
    """Figure 27: the national map (share of each cell marked) and its state ranking against CFSAM 2025."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import BoundaryNorm, ListedColormap
    import eda_figures as FG
    z = np.load(CACHE)
    share = np.where(z["inside"] > 0.5, z["share"] / np.maximum(z["inside"], 1e-6), np.nan)
    west, south, east, north = z["bbox"]
    adm1 = gpd.read_file(C.ADMIN2.parent / "ssd_admin1.geojson")
    adm2 = gpd.read_file(C.ADMIN2)
    oranges = ["#f4f3ef", "#fde9df", "#f9c4ab", "#f39b74", "#eb6834", "#b84a1d"]
    bounds = [0, 0.001, 0.05, 0.15, 0.3, 0.5, 1.0001]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12, 5.6), gridspec_kw={"width_ratios": [1.45, 1]})
    im = ax.imshow(share, extent=(west, east, south, north), cmap=ListedColormap(oranges), norm=BoundaryNorm(bounds, 6),
                   interpolation="nearest")
    adm1.boundary.plot(ax=ax, color=FG.MUTED, linewidth=0.5)
    for area in C.AREAS:
        adm2[adm2[C.ADMIN2_NAME].isin(C.AREAS[area])].dissolve().boundary.plot(ax=ax, color=FG.INK, linewidth=1.6)
    ax.set_xlim(west, east), ax.set_ylim(south, north), ax.set_aspect(1 / np.cos(np.radians(8))), ax.set_axis_off()
    ax.set_title("Our map over South Sudan: share of each ~1 km cell where a 210 m box holds a field\n"
                 "(black outlines: Aweil counties and Bor South, the only areas with labels; elsewhere not checked)",
                 loc="left", fontsize=9)
    cb = fig.colorbar(im, ax=ax, shrink=0.55, pad=0.01)
    cb.set_ticks(bounds[:-1] + [1], labels=["0", "", "5%", "15%", "30%", "50%", "100%"], fontsize=7)
    t = pd.read_csv(RES / "rule1_national_by_state.csv").dropna(subset=["cfsam_pct"])
    bx.scatter(t.map_pct, t.cfsam_pct, s=36, color=FG.SERIES[1], edgecolor=FG.SURFACE, zorder=3)
    for r in t.itertuples():
        off = (4, -10) if r.state == "Western Bahr el Ghazal" else (4, 3)        # keep it clear of Upper Nile
        bx.annotate(r.state, (r.map_pct, r.cfsam_pct), xytext=off, textcoords="offset points", fontsize=7.5, color=FG.INK2)
    rho = spearmanr(t.map_pct, t.cfsam_pct)[0]
    bx.set_xlabel("our map: land whose 210 m box holds a field, % of the state")
    bx.set_ylabel("CFSAM 2025 cereal area, % of the state (modelled)")
    bx.set_title(f"States: our map against the crop assessment\nrank correlation {rho:.2f} (public maps -0.36 to 0.25; GFSAD 0.59)",
                 loc="left", fontsize=9)
    bx.set_xlim(0, None), bx.set_ylim(0, None)
    bx.grid(True, color=FG.GRID_C, linewidth=0.8), bx.set_axisbelow(True)
    fig.tight_layout()
    return FG._save(fig, "27_national_map")


if __name__ == "__main__":
    if sys.argv[1:2] == ["summary"] and len(sys.argv) == 3:
        summary(Path(sys.argv[2]))
    elif sys.argv[1:2] == ["fetch"] and len(sys.argv) == 3:
        fetch(Path(sys.argv[2]))
    elif sys.argv[1:2] == ["figure"]:
        print(figure())
    else:
        raise SystemExit(__doc__)
