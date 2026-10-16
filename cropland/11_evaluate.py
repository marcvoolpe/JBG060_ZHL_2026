"""
Step 11 - The evaluation additions (METHODOLOGY.md change log, 12 Oct 2026), on the
outputs of 09_score.py and 10_flood.py. Writes into cropland/results/:

  area_adjusted.csv       area per study area and definition with the usual interval and the
                          adjusted upper bound (evaluation.area_interval)
  error_analysis.csv      false crop and missed crop of every map by what the labellers saw
  published_vs_ours.csv   our precision / recall / F1 next to Kerner et al. 2024 and Adebayo et al. 2026
  design_efficiency.csv   points needed for a 20% CV: agreement strata against one-map strata
  rule_complexity.csv     how readable each frozen rule file is
  pixel_count_bias.csv    each map's pixel-counted crop share against the sample estimate
  trigger_agreement.csv   (if 10_flood.py has run) trigger decisions of every map against the sample
  flooded_cropland_bounds.csv  the sample's flooded cropland: points in flood cells, usual and adjusted
                          upper bound (capped at the flooded land), used by the trigger check

Run from group_repo: python cropland/11_evaluate.py cropland/rule1_<date>.json
"""

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import common as C
import evaluation as V
import rules as R

RES = C.HERE / "results"
EDA = C.REPO / "deliverables" / "cropland_report" / "tables"
DEFS = {"cropland": ("cropland_avg", "share_avg"), "cropped_2025": ("crop_avg", "share_crop_avg")}


def areas(values, W):
    rows = []
    for area in C.AREAS:
        w = W[W.area == area].set_index("stratum").share.to_dict()
        ha = W[W.area == area].ha.sum()
        d = values[values.area == area]
        for name, (avg, share) in DEFS.items():
            for measure, col in (("share of box", share), ("box holds it (upper bound)", avg)):
                ok = d[d[col].notna()]
                r = V.area_interval(ok[col].to_numpy(float), ok.stratum.to_numpy(), w, crop=ok[avg].to_numpy(float) > 0)
                rows.append({"area": area, "definition": name, "measure": measure, "points": len(ok),
                             **{k: v for k, v in r.items()},
                             "ha": r["estimate"] * ha, "low_ha": r["low"] * ha, "high_ha": r["high"] * ha,
                             "high_adjusted_ha": r["high_adjusted"] * ha})
    return pd.DataFrame(rows)


def main() -> None:
    rule_files = [Path(f) for f in sys.argv[1:]]
    values = pd.read_csv(RES / "map_values.csv")
    accuracy = pd.read_csv(RES / "accuracy.csv")
    W = pd.read_csv(C.HERE / "strata_areas.csv")
    maps = [m for m in accuracy["map"].unique()]

    a = areas(values, W)
    a.to_csv(RES / "area_adjusted.csv", index=False)
    print(a[["area", "definition", "measure", "points", "estimate", "low", "high", "high_adjusted", "ha"]].round(4).to_string(index=False))

    labels = pd.concat([pd.read_csv(f, dtype={"crop_share": str}) for f in sorted((C.HERE / "labels").glob("sample_labels_*.csv"))])
    context = V.labeller_context(labels, pd.read_csv(C.HERE / "features_sample.csv"))
    err = pd.concat([V.error_analysis(values, context, maps, reference=ref).assign(definition=ref)
                     for ref in ("cropland", "crop")])
    err.to_csv(RES / "error_analysis.csv", index=False)

    lit = C.HERE / "reference_accuracy_literature.csv"              # our study only (Kerner 2024, Adebayo 2026)
    if lit.exists():
        V.published_vs_ours(accuracy, pd.read_csv(lit)).to_csv(RES / "published_vs_ours.csv", index=False)

    public = [m for m in C.CONFIG["strata"]["maps"] + ["asap_v04"] if m in values]   # public maps only, never our models
    eff = []
    for area in C.AREAS:
        w = W[W.area == area].set_index("stratum").share.to_dict()
        eff.append(V.design_efficiency(values[values.area == area], w, public, reference="cropland_avg").assign(area=area))
    pd.concat(eff).to_csv(RES / "design_efficiency.csv", index=False)

    pd.DataFrame([{"rules": f.name, **V.rule_complexity(R.load(f))} for f in rule_files]).to_csv(
        RES / "rule_complexity.csv", index=False)

    if not (EDA / "crop_share_by_county.csv").exists():             # from the EDA notebook (our study only)
        trigger()
        print("written to", RES)
        return
    shares = pd.read_csv(EDA / "crop_share_by_county.csv")
    bias = []
    for area, unit in (("aweil", "all counties"), ("bor_south", "Bor South")):
        ref = a[(a.area == area) & (a.definition == "cropland") & (a.measure == "share of box")].iloc[0]
        m = shares[(shares.area == area) & (shares.unit == unit)].set_index("map").crop_pct
        b = V.pixel_count_bias(m, {k: 100 * ref[k] for k in ("estimate", "low", "high_adjusted")})
        bias.append(b.assign(area=area, sample_pct=100 * ref.estimate).reset_index())
    pd.concat(bias).to_csv(RES / "pixel_count_bias.csv", index=False)
    import eda_figures as FG                         # figures 14 (area vs maps) and 15 (scorecard)
    lab = V.labeller_f1(pd.read_csv(C.HERE / "labels_merged.csv"), pd.read_csv(C.HERE / "sample.csv"),
                        W[W.area == "aweil"].set_index("stratum").share.to_dict())   # scored like the maps (15 Oct)
    pb = RES / "precision_bounds.csv"                                                   # from sensitivity.py
    low = pd.read_csv(pb).set_index("map").lower_95.to_dict() if pb.exists() else None
    print("figures:", FG.area_vs_maps(pd.concat(bias), a), FG.scorecard(accuracy, agreement=lab["weighted_f1"], precision_lower=low))
    trigger()
    print("written to", RES)


def flooded_bounds() -> pd.DataFrame:
    """The sample's flooded cropland with the adjusted upper bound, capped at the land that flooded.

    The sample points are spread over the whole study area, so very few fall in a flood cell
    (2025: 1 of 330 in Aweil, 2 of 120 in Bor South). The usual interval then looks precise
    without being so (Bor South: 0 to 0 ha); the adjusted upper bound cannot exceed the flooded land.
    """
    fl = importlib.import_module("10_flood")
    s, lab = pd.read_csv(C.HERE / "sample.csv"), pd.read_csv(C.HERE / "labels_final.csv")
    W = pd.read_csv(C.HERE / "strata_areas.csv")
    rows = []
    for area in C.AREAS:
        cells = fl.in_area(None, fl.flood_cells(area), area)
        pts = s[s.area == area].merge(lab, on="id")
        pts = pts[pts.cropland_avg.notna()]
        near = np.array([((abs(cells.lat - r.lat) <= fl.CELL / 2) & (abs(cells.lon - r.lon) <= fl.CELL / 2)).any()
                         for r in pts.itertuples()])
        w, total, flooded = W[W.area == area].set_index("stratum").share.to_dict(), W[W.area == area].ha.sum(), cells.ha.sum()
        for name, avg, share in (("reference: cropland", "cropland_avg", "share_avg"),
                                 ("reference: cropped 2025", "crop_avg", "share_crop_avg")):
            for label, col in ((f"{name} (share of box)", share), (f"{name}, upper bound (box holds it)", avg)):
                ok = pts[col].notna().to_numpy()
                y = pts[col].fillna(0).to_numpy() * near
                r = V.area_interval(y[ok], pts.stratum.to_numpy()[ok], w)
                rows.append({"area": area, "map": label, "points_in_flood_cells": int(near[ok].sum()),
                             "of_them_cropland": int((y[ok] > 0).sum()), "estimate_ha": r["estimate"] * total,
                             "high_usual_ha": r["high"] * total, "high_adjusted_ha": r["high_adjusted"] * total,
                             "flooded_land_ha": flooded, "upper_used_ha": min(r["high_adjusted"] * total, flooded)})
    return pd.DataFrame(rows)


def trigger() -> None:
    """Pixel maps against the sample's share of box; our map against the sample's 'box holds it'.

    A pixel of our map says that the 210 m box around it holds a cropped field (the unit we
    labelled), so its hectares are land whose box holds crop: an upper bound, like the sample's.
    """
    flood = RES / "flooded_cropland.csv"
    if not flood.exists():
        print("no flooded_cropland.csv yet: run 10_flood.py, then this step again")
        return
    b = flooded_bounds()
    b.to_csv(RES / "flooded_cropland_bounds.csv", index=False)
    print(b[["area", "map", "points_in_flood_cells", "of_them_cropland", "estimate_ha", "high_usual_ha",
             "high_adjusted_ha", "flooded_land_ha"]].round(0).to_string(index=False))
    f = pd.read_csv(flood).merge(b[["area", "map", "upper_used_ha"]], on=["area", "map"], how="left")
    f["ci_high_ha"] = f.upper_used_ha.fillna(f.ci_high_ha)          # the sample's cautious upper bound
    ref, ours = f["map"].str.startswith(("reference", "all flooded")), f["map"].isin(["rule1"])
    thr = [100, 500, 1000, 5000]
    upper = "reference: cropland, upper bound (box holds it)"
    pd.concat([V.trigger_agreement(f[ref | ~ours], thr).assign(compared_with="reference: cropland (share of box)"),
               V.trigger_agreement(f[ref | ours], thr, upper).assign(compared_with=upper)]
              ).to_csv(RES / "trigger_agreement.csv", index=False)


if __name__ == "__main__":
    main()
