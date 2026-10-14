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
    w = pd.read_csv(TABLES / "window_aweil_s020.csv")                 # figure 16 (eda_window.py)
    pub = w[w["map"] != "rule1"].crop_share_of_window_pct
    m |= {"WindowMin": f"{pub.min():.1f}\\%", "WindowMax": f"{pub.max():.1f}\\%"}
    m = write_model_numbers(m)
    lines = ["% Written by build_report_inputs.py from cropland/results/ (steps 09-12). Do not edit by hand."]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
    (HERE / "results.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"results.tex: {len(m)} numbers")


FEATURE_ROWS = [   # input, the cue it measures (labelling key / METHODOLOGY section 5)
    ("ndvi_min_am", "greenness, lowest April-May", "a: bare soil before sowing"),
    ("bsi_max_am", "bare-soil index, highest April-May", "a: bare soil before sowing"),
    ("ndvi_peak_jja", "greenness, peak June-August", "b: green-up"),
    ("greenup", "peak minus spring greenness", "b: green-up"),
    ("drop_son", "drop from the peak to September-November", "c: harvest"),
    ("drop_vs_500m", "that drop minus the 500 m surroundings'", "c: harvest earlier than the grass"),
    ("texture_jja", "texture (GLCM contrast) at the peak", "d: field shape"),
    ("edge_density", "edge density (Canny edges) at the peak", "d: field shape"),
    ("ndvi_min_jfm", "greenness, lowest January-March", "trees and shrub"),
    ("water_occurrence", "JRC surface water occurrence", "water"),
    ("s1_vv_min", "radar VV, lowest month", "water"),
    ("dist_buildings_m", "distance to the nearest building (m)", "homesteads"),
    ("burned", "burned November-April", "burn scars"),
    ("vh_jun", "radar VH, June", "cloudy months"), ("vh_jul", "radar VH, July", "cloudy months"),
    ("vh_aug", "radar VH, August", "cloudy months"), ("vh_sep", "radar VH, September", "cloudy months"),
    ("vh_range", "radar VH, range over the year", "cloudy months")]
NICE = {"worldcover_2021": "WorldCover 2021", "glad_2019": "GLAD 2019", "deafrica_2019": "DE Africa 2019",
        "worldcereal_2021": "WorldCereal 2021", "esri_2025": "Esri 2025", "dynamicworld_2025": "Dynamic World 2025",
        "gfsad_2015": "GFSAD 2015", "asap_v04": "ASAP v04", "esri_2022": "Esri 2022", "dynamicworld_2022": "Dynamic World 2022",
        "rule1": "Rule 1 (ours)", "logistic_l2": "logistic regression, 18 inputs", "logistic_rule1_inputs": "logistic regression, 2 inputs",
        "rf_features": "random forest, 18 inputs", "rf_embedding": "random forest, embedding"}


def _table(caption, label, colspec, header, rows, note="", wide=False, size="small"):
    body = "\n".join(" & ".join(str(c) for c in r) + r" \\" for r in rows)
    env = ("tabularx", "{\\linewidth}") if wide else ("tabular", "")         # tabularx: a column that wraps
    return ("\\begin{table}[tbp]\n\\centering\n\\caption{" + caption + "}\\label{" + label + "}\n%TC:ignore\n\\" + size + "\n"
            "\\begin{" + env[0] + "}" + env[1] + "{@{}" + colspec + "@{}}\n\\toprule\n" + " & ".join(header) + r" \\" + "\n\\midrule\n" + body +
            "\n\\bottomrule\n\\end{" + env[0] + "}\n" + (f"\\par\\smallskip{{\\footnotesize {note}}}\n" if note else "") +
            "%TC:endignore\n\\end{table}\n")


def write_appendix_tables():
    """appendix_tables.tex: the detailed tables of the appendix, every number read from a CSV."""
    import sys
    sys.path.insert(0, str(HERE.parents[2] / "cropland"))
    import features as F                               # which summary each feature takes over the box
    R = lambda f: pd.read_csv(RESULTS / f)
    pct = lambda v: f"{100 * v:.1f}\\%"
    out = []
    summ = {f: "10th pct." for f in F.BOX_LOW} | {f: "90th pct." for f in F.BOX_HIGH} | {f: "mean" for f in F.BOX_MEAN}
    out.append(_table("The 18 features. Each is computed per 10 m pixel for 2025 and summarised over the 210 m box by its most crop-like part.",
                      "tab:features", "l>{\\raggedright\\arraybackslash}X>{\\raggedright\\arraybackslash}p{3.4cm}l", ["Feature", "What it measures", "Cue", "Over the box"],
                      [(f.replace("_", "\\_"), d, c, summ[f]) for f, d, c in FEATURE_ROWS], wide=True))
    s = pd.read_csv(HERE.parents[2] / "cropland" / "model_table.csv")
    W = pd.read_csv(HERE.parents[2] / "cropland" / "strata_areas.csv")
    rows = []
    for r in W.itertuples():
        d = s[(s.area == r.area) & (s.stratum == r.stratum)]
        rows.append(("Aweil" if r.area == "aweil" else "Bor South", r.stratum, f"{r.ha:,.0f}", pct(r.share), len(d),
                     int((d.split == "calibration").sum()), int((d.split == "test").sum()), int((d.cropland == 1).sum()),
                     int((d.final == "disagreed").sum())))
    out.append(_table("Strata and sample. Cropland: points both labellers call cropland; split: the two labellers disagree.",
                      "tab:strata", "llrrrrrrr", ["Area", "Stratum", "ha", "Share", "Points", "Calib.", "Test", "Cropland", "Split"], rows))
    la = pd.read_csv(TABLES / "label_agreement.csv")
    la = la[la.by.isin(["all", "area", "area x stratum"])]
    nice_group = lambda g: g.replace("('aweil', ", "Aweil ").replace("('bor_south', ", "Bor South ").replace("')", "").replace("'", "") \
        .replace("aweil", "Aweil").replace("bor_south", "Bor South").replace("all", "All")
    out.append(_table("Agreement between the two blind labellers on cropland versus not, per area and stratum.", "tab:agreement",
                      "lrrrrr", ["Group", "Points", "Agree", "Kappa", "Pos. agr.", "Neg. agr."],
                      [(nice_group(r.group), r.points, pct(r.cropland_agree), f"{r.cropland_kappa:.2f}", f"{r.cropland_pos_agree:.2f}",
                        f"{r.cropland_neg_agree:.2f}") for r in la.itertuples()]))
    acc = R("accuracy.csv")
    a = acc[(acc.area == "aweil") & (acc.definition == "cropland")].sort_values("f1", ascending=False)
    pm = lambda v, se: "--" if pd.isna(v) else f"{v:.2f} $\\pm$ {se:.2f}"
    out.append(_table("Accuracy of every map on the Aweil test points (cropland; stratified estimators; $\\pm$ one standard error).",
                      "tab:accuracy", "lrrrrr", ["Map", "Year", "Precision", "Recall", "F1", "Overall acc."],
                      [(NICE.get(r.map, r.map), r.year, pm(r.ua, r.ua_se), pm(r.pa, r.pa_se), pm(r.f1, r.f1_se), f"{r.oa:.2f}")
                       for r in a.itertuples()]))
    m = pd.read_csv(TABLES / "models_cv_vs_test.csv")
    rng = lambda v, lo, hi: "--" if pd.isna(v) else f"{v:.2f} ({lo:.2f}--{hi:.2f})"
    out.append(_table("Models: F1 in repeated cross-validation on the 125 calibration points (every point alike; 2.5--97.5\\% of 20 repeats) "
                      "and on the Aweil test points (stratum weights; 95\\% interval; frozen models only).", "tab:models", "lrr",
                      ["Model", "Cross-validation", "Test"],
                      [(r.model, rng(r.cv_f1, r.cv_low, r.cv_high), rng(r.test_f1, r.test_low, r.test_high)) for r in m.itertuples()]))
    pv = R("published_vs_ours.csv")
    pv = pv[(pv.area == "aweil") & (pv.definition == "cropland") & pv.published_min.notna()]
    pv = pv.pivot_table(index="map", columns="metric", values=["ours", "published_min", "published_max"])
    out.append(_table("Our scores in Aweil against the range published for the same maps in other African countries "
                      "(Kerner et al.\\ 2024; Adebayo et al.\\ 2026).", "tab:published", "lrrrr",
                      ["Map", "Recall, ours", "Recall, published", "F1, ours", "F1, published"],
                      [(NICE.get(k, k), f"{r[('ours', 'recall')]:.2f}", f"{r[('published_min', 'recall')]:.2f}--{r[('published_max', 'recall')]:.2f}",
                        f"{r[('ours', 'f1')]:.2f}", f"{r[('published_min', 'f1')]:.2f}--{r[('published_max', 'f1')]:.2f}")
                       for k, r in pv.iterrows()]))
    h = R("flood_history.csv")
    h1 = h[h.min_days == 1]
    smp = h1[(h1.layer == "sample (ratio)") & (h1.measure == "share of box") & h1.flooded_crop_ha.notna()].set_index(["area", "year"])
    mp = h1[h1.layer.isin(ORDER)].pivot_table(index=["area", "year"], columns="layer", values="flooded_crop_ha")
    rows = [("Aweil" if a_ == "aweil" else "Bor South", y, f"{r.flooded_land_ha:,.0f}", int(r.points_in_flood), int(r.of_them_cropland),
             f"{mp.loc[(a_, y)].min():,.0f} / {mp.loc[(a_, y)].median():,.0f} / {mp.loc[(a_, y)].max():,.0f}",
             f"{r.flooded_crop_ha:,.0f} ({r.low_ha:,.0f}--{r.high_ha:,.0f})") for (a_, y), r in smp.iterrows()]
    out.append(_table("Past floods on today's cropland: the years with at least five sample points on flooded land (1+ flood day, "
                      "June--December). Maps: lowest / median / highest of the 8 public layers; sample: ratio estimator, 95\\% interval.",
                      "tab:floodyears", "llrrrrr", ["Area", "Year", "Flooded ha", "Points", "Cropland", "Maps (ha)", "Sample (ha)"], rows, size="footnotesize"))
    t = R("trigger_hindcast.csv")
    t = t[(t.area == "aweil") & (t.min_days == 1)]
    rows = []
    for k, g in t.groupby("layer"):
        if k not in NICE:
            continue
        cells = []
        for thr in (100, 500, 1000):
            x = g[g.threshold_ha == thr]
            told = x[x.sample_says.isin(["fire", "no fire"])]
            cells += [int((x.layer_says == "fire").sum()), f"{int(told.agrees.sum())}/{len(told)}" if len(told) else "--"]
        rows.append((NICE[k], *cells))
    out.append(_table("Trigger hindcast, Aweil, 2000--2025: years in which each layer's flooded cropland reaches the threshold "
                      "(fires), and in how many of the years the sample can judge it agrees with the sample.", "tab:hindcast",
                      "lrrrrrr", ["Layer", "100 ha: fires", "agrees", "500 ha: fires", "agrees", "1,000 ha: fires", "agrees"],
                      sorted(rows), size="footnotesize"))
    groups = {"app_sample": [1, 2], "app_models": [0, 4], "app_accuracy": [3, 5], "app_floods": [6, 7]}   # one file per appendix section
    for name, idx in groups.items():
        (HERE / f"{name}.tex").write_text("% Written by build_report_inputs.py from CSVs. Do not edit by hand.\n\n"
                                          + "\n".join(out[i] for i in idx), encoding="utf-8")
    print(f"appendix tables: {len(out)} tables in {len(groups)} files")


def write_model_numbers(m):
    """Numbers for the models part of the draft (Rule 1 leaves, what the models learned)."""
    leaves = pd.read_csv(TABLES / "rule1_leaves.csv").set_index(["split", "leaf"])
    for split, S in (("calibration", "Cal"), ("test", "Test")):
        for leaf, L in (("near_edges", "Crop"), ("far", "Far"), ("near_no_edges", "NoEdge")):
            r = leaves.loc[(split, leaf)]
            m |= {f"Leaf{L}{S}N": f"{r.points}", f"Leaf{L}{S}Crop": f"{r.cropland}"}
    lr = pd.read_csv(TABLES / "models_learned.csv", index_col=0)
    m |= {"CoefBuildings": f"{lr.loc['dist_buildings_m', 'logistic_coef_per_sd']:.2f}",
          "CoefVhJun": f"{lr.loc['vh_jun', 'logistic_coef_per_sd']:.2f}",
          "CoefDrop": f"{lr.loc['drop_son', 'logistic_coef_per_sd']:.2f}",
          "ImpBuildings": f"{lr.loc['dist_buildings_m', 'rf_importance']:.2f}", "ImpEdges": f"{lr.loc['edge_density', 'rf_importance']:.2f}"}
    return m


def copy_figures():
    out = HERE / "figures"
    out.mkdir(exist_ok=True)
    for f in sorted(FIGURES.glob("*.png")):
        shutil.copy2(f, out / f.name)
    print(f"figures/: {len(list(out.glob('*.png')))} files")


def make_zip():
    z = HERE / "overleaf_upload.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ("report.tex", "report_draft.tex", "references.bib", "numbers.tex", "results.tex", "app_sample.tex", "app_models.tex", "app_accuracy.tex", "app_floods.tex"):
            zf.write(HERE / name, name)
        for f in sorted((HERE / "figures").glob("*.png")):
            zf.write(f, f"figures/{f.name}")
    print(f"{z.name}: ready for Overleaf (New project > Upload project)")


if __name__ == "__main__":
    write_numbers()
    write_results()
    write_appendix_tables()
    copy_figures()
    make_zip()
