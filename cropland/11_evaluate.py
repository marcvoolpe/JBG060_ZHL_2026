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

Run from group_repo: python cropland/11_evaluate.py cropland/rule1_<date>.json
"""

import sys
from pathlib import Path

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

    public = [m for m in maps if m in values and m not in ("rule1", "rf_features", "rf_embedding") and values[m].isin([0, 1]).all()]
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
    trigger()
    print("written to", RES)


def trigger() -> None:
    """Pixel maps against the sample's share of box; our map against the sample's 'box holds it'.

    A pixel of our map says that the 210 m box around it holds a cropped field (the unit we
    labelled), so its hectares are land whose box holds crop: an upper bound, like the sample's.
    """
    flood = RES / "flooded_cropland.csv"
    if not flood.exists():
        print("no flooded_cropland.csv yet: run 10_flood.py, then this step again")
        return
    f = pd.read_csv(flood)
    ref, ours = f["map"].str.startswith(("reference", "all flooded")), f["map"].isin(["rule1"])
    thr = [100, 500, 1000, 5000]
    upper = "reference: cropland, upper bound (box holds it)"
    pd.concat([V.trigger_agreement(f[ref | ~ours], thr).assign(compared_with="reference: cropland (share of box)"),
               V.trigger_agreement(f[ref | ours], thr, upper).assign(compared_with=upper)]
              ).to_csv(RES / "trigger_agreement.csv", index=False)


if __name__ == "__main__":
    main()
