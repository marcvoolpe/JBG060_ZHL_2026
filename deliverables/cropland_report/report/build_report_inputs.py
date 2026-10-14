"""
Prepare the LaTeX report for Overleaf:
  1. numbers.tex: one macro per number the report quotes, read from the notebook's
     key_numbers.csv, so no number in the text is typed by hand (rerun after the
     notebook, and the report follows);
  2. figures/: copies of the notebook's figures;
  3. overleaf_upload.zip: report.tex, references.bib, numbers.tex and figures/,
     ready for Overleaf (New project > Upload project).

Run from the repo root: python deliverables/cropland_report/report/build_report_inputs.py
"""

import shutil
import zipfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
TABLES = HERE.parent / "tables"
FIGURES = HERE.parent / "figures"

pct2, pct1, pct0 = "{:.2f}\\%", "{:.1f}\\%", "{:.0f}\\%"
ha, two, sign, one = "{:,.0f}", "{:.2f}", "{:+.2f}", "{:.1f}"
NUMBERS = {   # key in key_numbers.csv -> (macro name, format)
    "Aweil crop share, lowest map (%)": ("AwCropMin", pct2),
    "Aweil crop share, highest map (%)": ("AwCropMax", pct2),
    "Aweil CFSAM 2025 cereal area (% of land)": ("AwCfsamTwentyFive", pct1),
    "Aweil CFSAM 2022 cereal area (% of land)": ("AwCfsamTwentyTwo", pct1),
    "Bor South crop share, Dynamic World 2025 (%)": ("BsDwShare", pct1),
    "Bor South crop share, highest other map (%)": ("BsOtherMax", pct2),
    "Aweil land no map calls crop (%)": ("AwNoMap", pct1),
    "Aweil land all 7 maps call crop (ha)": ("AwAllSevenHa", one),
    "Aweil land >= 4 maps call crop (%)": ("AwMajority", pct2),
    "Aweil pairwise IoU, best pair": ("AwIoUMax", two),
    "Aweil pairwise IoU, median pair": ("AwIoUMedian", two),
    "National crop, lowest map (Mha)": ("NatCropMin", two),
    "National crop, highest map (Mha)": ("NatCropMax", two),
    "National CFSAM 2025 cereal area (Mha)": ("NatCfsam", two),
    "National FAOSTAT arable land (Mha)": ("NatFaostat", two),
    "Aweil 2022 flooded cropland, lowest map (ha)": ("AwFloodMin", ha),
    "Aweil 2022 flooded cropland, highest map (ha)": ("AwFloodMax", ha),
    "National 2022 flooded cropland, lowest map (ha)": ("NatFloodMin", ha),
    "National 2022 flooded cropland, highest map (ha)": ("NatFloodMax", ha),
    "National 2022 flooded cropland, ASAP (ha)": ("NatFloodAsap", ha),
    "CFSAM 2022 cultivated land damaged by floods (ha)": ("CfsamDamaged", ha),
    "Bor South 2025 flooded cropland, Dynamic World (ha)": ("BsFloodDw", ha),
    "Bor South 2025 flooded cropland, all other maps (ha, max)": ("BsFloodOther", ha),
    "Labelled twice so far (points)": ("LabTwice", ha),
    "Labellers agree cropland vs not (%)": ("LabAgree", pct1),
    "Cohen's kappa cropland vs not": ("LabKappa", two),
    "Labellers agree cropland vs not, Aweil (%)": ("LabAgreeAw", pct1),
    "Cohen's kappa cropland vs not, Aweil": ("LabKappaAw", two),
    "Cohen's kappa cropland vs not, Bor South": ("LabKappaBs", two),
    "Labeller splits on cropland (points)": ("LabSplits", ha),
    "Splits where field shape answers differ (points)": ("LabShapeSplits", ha),
    "Esri F1 in Mali, Kerner et al. 2024": ("EsriMaliFone", two),
    "Esri accuracy in Mali, Kerner et al. 2024": ("EsriMaliAcc", two),
    "Rank corr. published recall (Kerner) vs Aweil crop share": ("RecallRhoAw", sign),
    "Rank corr. published recall (Kerner) vs Bor South crop share": ("RecallRhoBs", sign),
    "Aweil land (ha)": ("AwLandHa", ha),
    "Bor South land (ha)": ("BsLandHa", ha),
    "Usual interval coverage, lowest (%)": ("CovUsualMin", pct0),
    "Usual interval coverage, highest (%)": ("CovUsualMax", pct0),
    "Adjusted interval coverage, lowest (%)": ("CovAdjMin", pct0),
    "Adjusted interval coverage, lowest in Aweil (%)": ("CovAdjMinAw", pct0),
}


def write_numbers():
    key = pd.read_csv(TABLES / "key_numbers.csv", index_col=0).value
    lines = ["% Written by build_report_inputs.py from key_numbers.csv. Do not edit by hand.",
             "\\providecommand{\\ph}[1]{[#1]}"]
    for k, (name, fmt) in NUMBERS.items():
        text = fmt.format(float(key[k])) if k in key else f"\\ph{{missing: {k}}}"
        lines.append(f"\\newcommand{{\\{name}}}{{{text}}}")
    (HERE / "numbers.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    missing = [k for k in NUMBERS if k not in key]
    print(f"numbers.tex: {len(NUMBERS) - len(missing)} numbers" + (f", missing: {missing}" if missing else ""))


RESULTS = HERE.parents[2] / "cropland" / "results"
ORDER = ["gfsad_2015", "glad_2019", "deafrica_2019", "worldcover_2021", "worldcereal_2021", "esri_2025",
         "dynamicworld_2025", "asap_v04"]                      # the 8 public layers, as in the figures


def write_results():
    """results.tex: one macro per result the draft report quotes, read from cropland/results/ (steps 09-12)."""
    R = lambda f: pd.read_csv(RESULTS / f)
    h100 = lambda v: f"{round(v, -2):,.0f}"                     # hectares to the nearest 100
    hx = lambda v: f"{v:,.0f}"
    p1 = lambda v: f"{100 * v:.1f}\\%"
    p0 = lambda v: f"{100 * v:.0f}\\%"
    f2 = lambda v: f"{v:.2f}"
    m = {}
    # area (share of box, adjusted upper bound)
    a = R("area_adjusted.csv")
    for area, A in (("aweil", "Aw"), ("bor_south", "Bs")):
        r = a[(a.area == area) & (a.definition == "cropland") & (a.measure == "share of box")].iloc[0]
        m |= {f"{A}AreaPct": p1(r.estimate) if r.estimate >= 0.01 else f"{100 * r.estimate:.2f}\\%",
              f"{A}AreaLowPct": p1(r.low) if r.low >= 0.01 else f"{100 * r.low:.2f}\\%", f"{A}AreaHighPct": p1(r.high_adjusted),
              f"{A}AreaHa": h100(r.ha), f"{A}AreaLowHa": h100(r.low_ha), f"{A}AreaHighHa": h100(r.high_adjusted_ha)}
        b = a[(a.area == area) & (a.definition == "cropland") & (a.measure == "box holds it (upper bound)")].iloc[0]
        m[f"{A}BoxPct"] = p1(b.estimate)
    c = a[(a.area == "aweil") & (a.definition == "cropped_2025") & (a.measure == "share of box")].iloc[0]
    m["AwCroppedPct"] = p1(c.estimate)
    # CFSAM 2025 cereal area against the sample
    cf = pd.read_csv(HERE.parents[2] / "cropland" / "reference_statistics.csv")
    cf = cf[(cf.source == "CFSAM") & (cf.year == 2025) & (cf.level == "county")]
    land = pd.read_csv(HERE.parents[2] / "cropland" / "strata_areas.csv").groupby("area").ha.sum()
    aw_cf = cf[cf.name.str.startswith("Aweil")].cereal_harvested_ha.sum()
    bs_cf = cf[cf.name == "Bor South"].cereal_harvested_ha.sum()
    m |= {"AwCfsamHa": h100(aw_cf), "BsCfsamHa": h100(bs_cf), "BsCfsamPct": p1(bs_cf / land["bor_south"])}
    # maps against the sample (pixel counts)
    pb = R("pixel_count_bias.csv")
    aw = pb[(pb.area == "aweil") & pb["map"].isin(ORDER)]
    m |= {"AwMapsOfSampleMin": p0(aw.ratio_to_sample.min()), "AwMapsOfSampleMax": p0(aw.ratio_to_sample.max()),
          "BsDwTimesSample": f"{pb[(pb.area == 'bor_south') & (pb['map'] == 'dynamicworld_2025')].ratio_to_sample.iloc[0]:.0f}"}
    # accuracy, Aweil, cropland
    acc = R("accuracy.csv")
    ac = acc[(acc.area == "aweil") & (acc.definition == "cropland")].set_index("map")
    names = {"rule1": "RuleOne", "worldcereal_2021": "WorldCereal", "esri_2025": "Esri", "dynamicworld_2025": "Dw",
             "deafrica_2019": "Dea", "asap_v04": "Asap", "glad_2019": "Glad", "worldcover_2021": "WorldCover",
             "gfsad_2015": "Gfsad", "logistic_l2": "Logit", "logistic_rule1_inputs": "LogitTwo", "rf_features": "Rf",
             "rf_embedding": "RfEmb"}
    for k, n in names.items():
        r = ac.loc[k]
        m |= {f"{n}Fone": f2(r.f1), f"{n}Prec": f2(r.ua), f"{n}Recall": f2(r.pa),
              f"{n}FoneLow": f2(max(0, r.f1 - 1.96 * r.f1_se)), f"{n}FoneHigh": f2(min(1, r.f1 + 1.96 * r.f1_se))}
    full = ac.loc[["esri_2025", "worldcover_2021", "glad_2019", "asap_v04"]]
    m |= {"PerfectPrecRecallMin": f2(full.pa.min()), "PerfectPrecRecallMax": f2(full.pa.max()),
          "AwTestPoints": hx(ac.loc["rule1"].test_points),
          "BsTestPoints": hx(acc[(acc.area == "bor_south") & (acc.definition == "cropland")].test_points.iloc[0])}
    v = R("map_values.csv")
    bs = v[(v.split == "test") & (v.area == "bor_south") & (v.cropland == 0)]
    m |= {"BsDwFalseCrop": hx(bs.dynamicworld_2025.sum()), "BsEmptyTest": hx(len(bs))}
    lab = pd.read_csv(TABLES / "label_agreement.csv").set_index("group")
    m["AwPosAgree"] = f2(lab.loc["aweil", "cropland_pos_agree"])
    cv = R("model_cv.csv").set_index("model").f1
    trees, logits = cv[[i for i in cv.index if i.startswith("tree")]], cv[[i for i in cv.index if i.startswith("logistic")]]
    m |= {"CvTreeMin": f2(trees.min()), "CvTreeMax": f2(trees.max()), "CvLogitMin": f2(logits.min()),
          "CvLogitMax": f2(logits.max()), "CvRf": f2(cv["rf_features"])}
    de = R("design_efficiency.csv")
    d_aw = de[de.area == "aweil"]
    m |= {"NoptOurs": hx(d_aw.n_opt.iloc[0]), "NoptMapMin": hx(d_aw.n_opt.iloc[1:].min()), "NoptMapMax": hx(d_aw.n_opt.iloc[1:].max()),
          "NoptBs": f"{round(de[de.area == 'bor_south'].n_opt.iloc[0], -1):,.0f}"}
    # flooding 2025
    fc = R("flooded_cropland.csv")
    for area, A in (("aweil", "Aw"), ("bor_south", "Bs")):
        t = fc[fc.area == area].set_index("map")
        maps = t.loc[[x for x in ORDER if x in t.index]].flooded_crop_ha
        m |= {f"{A}FloodLandTwentyFive": hx(t.loc["all flooded land"].flooded_crop_ha),
              f"{A}FloodMapsMinTwentyFive": hx(maps.min()), f"{A}FloodMapsMaxTwentyFive": hx(maps.max()),
              f"{A}FloodRuleOneTwentyFive": hx(t.loc["rule1"].flooded_crop_ha)}
    fb = R("flooded_cropland_bounds.csv")
    for area, A in (("aweil", "Aw"), ("bor_south", "Bs")):
        m[f"{A}FloodPoints"] = hx(fb[fb.area == area].points_in_flood_cells.iloc[0])
    m["BsFloodDwTwentyFive"] = hx(fc[(fc.area == "bor_south") & (fc["map"] == "dynamicworld_2025")].flooded_crop_ha.iloc[0])
    # past floods on today's cropland (10b)
    h = R("flood_history.csv")
    h1 = h[(h.min_days == 1)]
    s = h1[(h1.layer == "sample (ratio)") & (h1.measure == "share of box")]
    maps = h1[h1.layer.isin(ORDER)].pivot_table(index=["area", "year"], columns="layer", values="flooded_crop_ha")
    ok = s[s.flooded_crop_ha.notna()].set_index(["area", "year"])
    ratio = (ok.flooded_crop_ha / maps.median(axis=1).reindex(ok.index)).loc["aweil"]
    m |= {"HistYearsAw": hx(len(ok.loc["aweil"])), "HistYearsBs": hx(len(ok.loc["bor_south"])),
          "HistTimesMin": f"{ratio.min():.0f}", "HistTimesMax": f"{ratio.max():.0f}"}
    for year, Y in ((2022, "TwentyTwo"), (2008, "ZeroEight")):
        r = ok.loc[("aweil", year)]
        mp = maps.loc[("aweil", year)]
        m |= {f"Hist{Y}Est": hx(r.flooded_crop_ha), f"Hist{Y}Low": hx(r.low_ha), f"Hist{Y}High": hx(r.high_ha),
              f"Hist{Y}Land": hx(r.flooded_land_ha), f"Hist{Y}Points": hx(r.points_in_flood),
              f"Hist{Y}Crop": hx(r.of_them_cropland), f"Hist{Y}MapsMin": hx(mp.min()), f"Hist{Y}MapsMax": hx(mp.max()),
              f"Hist{Y}MapsMedian": hx(mp.median())}
    fm = pd.read_csv(TABLES / "flood_map_aweil_2022.csv").set_index("before")
    m |= {"MapCellsTwentyTwo": hx(fm.flooded_cells.iloc[0]), "MapShownWc": hx(fm.loc["worldcereal_2021", "shown_before"]),
          "MapAddedWc": hx(fm.loc["worldcereal_2021", "added_by_our_map"]), "MapAddedEsri": hx(fm.loc["esri_2025", "added_by_our_map"])}
    lines = ["% Written by build_report_inputs.py from cropland/results/ (steps 09-12). Do not edit by hand."]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
    (HERE / "results.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"results.tex: {len(m)} numbers")


def copy_figures():
    out = HERE / "figures"
    out.mkdir(exist_ok=True)
    for f in sorted(FIGURES.glob("*.png")):
        shutil.copy2(f, out / f.name)
    print(f"figures/: {len(list(out.glob('*.png')))} files")


def make_zip():
    z = HERE / "overleaf_upload.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ("report.tex", "report_draft.tex", "references.bib", "numbers.tex", "results.tex"):
            zf.write(HERE / name, name)
        for f in sorted((HERE / "figures").glob("*.png")):
            zf.write(f, f"figures/{f.name}")
    print(f"{z.name}: ready for Overleaf (New project > Upload project)")


if __name__ == "__main__":
    write_numbers()
    write_results()
    copy_figures()
    make_zip()
