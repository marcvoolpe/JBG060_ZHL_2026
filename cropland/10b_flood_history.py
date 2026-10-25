"""
Step 10b - Past floods on today's cropland (2000-2025), and a trigger hindcast.

Added 14 Oct 2026, after the 2025 results. It is a scenario, not
history: our labels and Rule 1 describe cropland in 2025, so every year answers "how much of
today's cropland would a flood like that one put under water?". The public maps are used as
they are (each of its own year).

  model <rules.json>   Earth Engine, once per frozen model (Rule 1, a teammate's tree, a logistic model
                       mapped by 08_run_map.py): its crop share in every flood cell that flooded at
                       least once in 2000-2025 -> raw_data/cropland/flood_history_<name>_<area>.csv
                       (cached per chunk, so a broken run resumes)
  summary              local: per area, year and flood duration (1+ and 10+ days, June-December):
                       flooded land; flooded cropland under every public map, ASAP and Rule 1; and
                       from the labelled sample, by two estimators:
                         ratio (main): the stratum-weighted cropland share of the sample boxes on
                           flooded land x the flooded land, which the flood mask gives exactly; with a
                           cautious upper bound (as evaluation.area_interval); only with at least
                           MIN_POINTS sample points on flooded land, else "too few points"
                         expansion: as in step 10 (labelled share x flooded, stratum weights)
                       -> results/flood_history.csv, results/trigger_hindcast.csv
                       and figure 12 + its CSV twin in deliverables/cropland_report/

Public maps per flood cell come from the EDA cache (eda_maps.zoa_cells), so the numbers match
figure 07; flood days per cell as in the EDA (recurring + unusual). Everything is per 210 m box:
the sample's share of box (main) and "box holds it" (the measure Rule 1's map is compared with).

Run from group_repo: python cropland/10b_flood_history.py model cropland/rule1_2026-10-12.json
                     python cropland/10b_flood_history.py summary
"""

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import common as C
import eda_maps as EM
import evaluation as V
import rules as R

fl = importlib.import_module("10_flood")
RES = C.HERE / "results"
YEARS = range(2000, 2026)
DAYS = (1, 10)
THRESHOLDS = (100, 500, 1000, 5000)
MIN_POINTS = 5            # fewer sample points on flooded land: the ratio estimate is just those few boxes
MAPS = EM.MAPS + EM.EXTRA + ["asap_v04"]
Z = V.Z


def cache(name, area):
    return C.OUT / f"flood_history_{name}_{area}.csv"


def models(area) -> dict:
    """Every frozen model with a per-cell cache for this area: {name: table of gr, gc, share}."""
    return {f.stem.removeprefix("flood_history_").removesuffix(f"_{area}"): pd.read_csv(f)
            for f in sorted(C.OUT.glob(f"flood_history_*_{area}.csv"))}


def ever_flooded(area):
    """Flood cells of the study area that flooded at least one day in 2000-2025, and the flood days per year."""
    cells = EM.zoa_cells(area)
    floods = {y: EM.flood_cells(fl.TILES[area], y) for y in YEARS}
    ever = pd.concat([f[["gr", "gc"]] for f in floods.values()]).drop_duplicates()
    return cells, cells.merge(ever, on=["gr", "gc"]), floods


def model(rule_file: Path) -> None:
    name = R.load(rule_file)["name"]
    ee = C.ee_init()
    for area in C.AREAS:
        _, cells, _ = ever_flooded(area)
        done = pd.read_csv(cache(name, area)) if cache(name, area).exists() else pd.DataFrame(columns=["gr", "gc", name])
        todo = cells.merge(done[["gr", "gc"]], on=["gr", "gc"], how="left", indicator=True)
        todo = todo[todo._merge == "left_only"].reset_index(drop=True)
        img = ee.Image(f"{C.ASSETS}/{rule_file.stem}_{area}").unmask(0).rename(name)
        img = img.addBands(ee.Image(0).rename("zero"))        # two bands: the mean keeps the band name
        print(f"{area}: {len(cells)} cells ever flooded, {len(todo)} to do", flush=True)
        for i in range(0, len(todo), fl.CHUNK):
            part = todo.iloc[i:i + fl.CHUNK].reset_index(drop=True)
            frac = fl.map_fractions(ee, part[["lat", "lon"]], img)
            out = pd.DataFrame({"gr": part.gr, "gc": part.gc, name: frac[name].reindex(range(len(part))).to_numpy()})
            out.to_csv(cache(name, area), mode="a", header=not cache(name, area).exists(), index=False)


def sample_rows(pts, flooded, F, W, total):
    """The sample's flooded cropland by both estimators, for share of box and for 'box holds it'."""
    rows = []
    f_all = np.array([(a, b) in flooded for a, b in zip(pts.gr, pts.gc)])
    for measure, col in (("share of box", "share_avg"), ("box holds it", "cropland_avg")):
        ok = pts[col].notna().to_numpy()
        d, f = pts[ok], f_all[ok]
        y, s = d[col].to_numpy(float), d.stratum.to_numpy()
        r = V.area_interval(y * f, s, W)
        base = {"measure": measure, "points_in_flood": int(f.sum()), "of_them_cropland": int(((y > 0) & f).sum())}
        rows.append({**base, "layer": "sample (expansion)", "flooded_crop_ha": r["estimate"] * total,
                     "low_ha": r["low"] * total, "high_ha": min(r["high_adjusted"] * total, F)})
        k, x = int(f.sum()), int(((y > 0) & f).sum())
        if k < MIN_POINTS:                             # too few points on flooded land to say anything
            rows.append({**base, "layer": "sample (ratio)", "flooded_crop_ha": np.nan, "low_ha": 0.0, "high_ha": F})
            continue
        n = pd.Series(s).value_counts()
        wt = pd.Series(s).map(lambda h: W[h] * total / n[h]).to_numpy()         # hectares per point
        R = (wt * y * f).sum() / (wt * f).sum()
        e = f * (y - R)
        var = sum((W[h] * total) ** 2 * e[s == h].var(ddof=1) / (s == h).sum() for h in W if (s == h).sum() > 1)
        var /= (wt * f).sum() ** 2
        m1, m2 = (y[y > 0].mean(), (y[y > 0] ** 2).mean()) if (y > 0).any() else (1.0, 1.0)
        p = (x + 1) / (k + 2)                          # as if one more cropland and one more empty flooded box
        var_adj = max(var, (p * m2 - (p * m1) ** 2) / k)
        rows.append({**base, "layer": "sample (ratio)", "flooded_crop_ha": R * F,
                     "low_ha": max(0.0, (R - Z * np.sqrt(var)) * F), "high_ha": min((R + Z * np.sqrt(var_adj)) * F, F)})
    return rows


def summary() -> pd.DataFrame:
    s, lab, Wt = pd.read_csv(C.HERE / "sample.csv"), pd.read_csv(C.HERE / "labels_final.csv"), pd.read_csv(C.HERE / "strata_areas.csv")
    rows = []
    for area in C.AREAS:
        cells, _, floods = ever_flooded(area)
        ours = models(area)
        pts = s[s.area == area].merge(lab, on="id")
        pts = pts[pts.cropland_avg.notna()].reset_index(drop=True)
        pts["gr"], pts["gc"] = EM.global_index(pts.lat, pts.lon)
        W = Wt[Wt.area == area].set_index("stratum").share.to_dict()
        total = Wt[Wt.area == area].ha.sum()
        for year, flood in floods.items():
            for days in DAYS:
                m = EM.flooded_crop(cells, flood, maps=MAPS, min_days=days)
                F = float(m.flooded_land_ha.iloc[0])
                key = {"area": area, "year": year, "min_days": days, "flooded_land_ha": F}
                rows += [{**key, "layer": r.map, "measure": "map pixels", "flooded_crop_ha": r.flooded_crop_ha}
                         for r in m.itertuples()]
                wet = flood[flood.days >= days]
                for name, share in ours.items():       # our maps: a pixel = its 210 m box holds crop (upper bound)
                    g = wet.merge(share, on=["gr", "gc"]).merge(cells[["gr", "gc", "ha"]], on=["gr", "gc"])
                    rows.append({**key, "layer": name, "measure": "box holds it", "flooded_crop_ha": (g[name] * g.ha).sum()})
                rows += [{**key, **r} for r in sample_rows(pts, set(zip(wet.gr, wet.gc)), F, W, total)]
    out = pd.DataFrame(rows)
    out.to_csv(RES / "flood_history.csv", index=False)
    return out


def hindcast(h: pd.DataFrame) -> pd.DataFrame:
    """Per year and threshold: does each layer fire, and what does the sample say (ratio estimator)?

    Public maps are compared with the sample's share of box; our models' maps with its 'box holds it'.
    """
    rows = []
    for (area, days), g in h.groupby(["area", "min_days"]):
        for year, y in g.groupby("year"):
            ref = {m: y[(y.layer == "sample (ratio)") & (y.measure == m)].iloc[0] for m in ("share of box", "box holds it")}
            for thr in THRESHOLDS:
                if y.flooded_land_ha.iloc[0] < thr:       # less land flooded than the threshold: nothing can fire
                    says = dict.fromkeys(ref, "no fire (flooded land below threshold)")
                else:
                    says = {m: ("fire" if r.low_ha >= thr else "no fire" if r.high_ha < thr else "cannot tell")
                            for m, r in ref.items()}
                for r in y[~y.layer.str.startswith("sample")].itertuples():
                    m = "box holds it" if r.measure == "box holds it" else "share of box"
                    fire = "fire" if r.flooded_crop_ha >= thr else "no fire"
                    rows.append({"area": area, "min_days": days, "year": year, "threshold_ha": thr, "layer": r.layer,
                                 "layer_ha": r.flooded_crop_ha, "layer_says": fire, "sample_says": says[m], "compared_with": m,
                                 "agrees": fire == says[m] if says[m] in ("fire", "no fire") else np.nan})
    out = pd.DataFrame(rows)
    out.to_csv(RES / "trigger_hindcast.csv", index=False)
    return out


def main() -> None:
    if sys.argv[1:2] in (["model"], ["rule1"]) and len(sys.argv) == 3:
        model(Path(sys.argv[2]))
    elif sys.argv[1:2] == ["summary"]:
        h = summary()
        t = hindcast(h)
        import eda_figures as FG
        print("figure:", FG.flood_history(h))
        main_rows = (h.measure == "map pixels") | (h.measure == "box holds it") & ~h.layer.str.startswith("sample") | ((h.layer == "sample (ratio)") & (h.measure == "share of box"))
        aw = h[(h.area == "aweil") & (h.min_days == 1) & main_rows]
        print(aw.pivot_table(index="year", columns="layer", values="flooded_crop_ha").round(0).to_string())
        s = t.groupby(["area", "min_days", "threshold_ha", "layer"]).agg(
            years_fired=("layer_says", lambda x: int((x == "fire").sum())),
            sample_can_tell=("sample_says", lambda x: int(x.isin(["fire", "no fire"]).sum())),
            agrees=("agrees", lambda x: int(x.sum())))
        print(s.loc[("aweil", 1)].to_string())
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
