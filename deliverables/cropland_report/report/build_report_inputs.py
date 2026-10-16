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
import sys
import zipfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
TABLES = HERE.parent / "tables"
FIGURES = HERE.parent / "figures"
sys.path.insert(0, str(HERE.parents[2] / "cropland"))
import key_results as K      # noqa: E402  the exposure table and the households, computed once (cropland/key_results.py)

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
    ms = R("rule1_map_share.csv").set_index("area")                     # our map counted over its pixels (national_map.py)
    st = R("rule1_national_by_state.csv")
    rc = pd.read_csv(TABLES / "state_rank_correlation_with_cfsam.csv", index_col=0)["2025"]
    pub = rc[[k for k in ORDER if k in rc.index and k != "gfsad_2015"]]
    from scipy.stats import spearmanr
    s2 = st.dropna(subset=["cfsam_pct"])
    m |= {"MapShareAw": f"{ms.loc['aweil', 'map_10m_pct']:.1f}\\%", "MapThirtyAw": f"{ms.loc['aweil', 'map_30m_national_pct']:.1f}\\%",
          "MapShareAwPoints": f"{ms.loc['aweil', 'from_labelled_points_pct']:.1f}\\%", "MapShareBs": f"{ms.loc['bor_south', 'map_10m_pct']:.1f}\\%",
          "NatMapPct": f"{100 * st.map_ha.sum() / st.ha.sum():.1f}\\%", "NatMapHa": f"{round(st.map_ha.sum(), -4):,.0f}",
          "NatMapRho": f"{spearmanr(s2.map_pct, s2.cfsam_pct)[0]:.2f}", "PubRhoMin": f"{pub.min():.2f}", "PubRhoMax": f"{pub.max():.2f}",
          "GfsadRho": f"{rc['gfsad_2015']:.2f}"}
    ar = R("area.csv")
    b = ar[(ar.area == "aweil") & (ar.definition == "cropland") & (ar.measure == "box holds it (upper bound)")].iloc[0]
    m |= {"AwSplitPoints": f"{int(b.points_split)}", "AwBoxIfSplitNo": f"{100 * b.share_if_split_all_no:.1f}\\%",
          "AwBoxIfSplitYes": f"{100 * b.share_if_split_all_yes:.1f}\\%"}
    m = write_national_check_numbers(m)
    m = write_household_numbers(m)
    m = write_sensitivity_numbers(m)
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


def _table(caption, label, colspec, header, rows, note="", wide=False, size="small", sep=None):
    body = "\n".join(" & ".join(str(c) for c in r) + r" \\" for r in rows)
    env = ("tabularx", "{\\linewidth}") if wide else ("tabular", "")         # tabularx: a column that wraps
    return ("\\begin{table}[tbp]\n\\centering\n\\caption{" + caption + "}\\label{" + label + "}\n%TC:ignore\n\\" + size + "\n"
            + (f"\\setlength{{\\tabcolsep}}{{{sep}}}\n" if sep else "")
            + "\\begin{" + env[0] + "}" + env[1] + "{@{}" + colspec + "@{}}\n\\toprule\n" + " & ".join(header) + r" \\" + "\n\\midrule\n" + body +
            "\n\\bottomrule\n\\end{" + env[0] + "}\n" + (f"\\par\\smallskip{{\\footnotesize {note}}}\n" if note else "") +
            "%TC:endignore\n\\end{table}\n")


def exposure_table(R, short=False):
    """Before (public maps) and after (labelled sample) for flooded cropland, with households and a 500 ha trigger.
    short: the caption for the 2,000-word version, where captions count."""
    rows = []
    for r in K.exposure().itertuples():          # computed in cropland/key_results.py, only formatted here
        ok, pts = pd.notna(r.sample_ha), r.sample_points_on_flooded_land
        rows.append(("Aweil" if r.area == "aweil" else "Bor South", r.year, f"{r.flooded_land_ha:,.0f}",
                     f"{r.maps_min_ha:,.0f}--{r.maps_max_ha:,.0f}",
                     f"{r.sample_ha:,.0f} ({r.sample_low_ha:,.0f}--{r.sample_high_ha:,.0f})" if ok else f"cannot tell ({pts} point{'' if pts == 1 else 's'})",
                     f"{round(r.households_maps_min, -1):,.0f}--{round(r.households_maps_max, -1):,.0f}",
                     f"{round(r.households_sample, -1):,.0f}" if ok else "--",
                     f"{r.maps_firing_500_ha} of {r.maps_scored}",
                     "fire" if r.sample_says == "fire" else "cannot tell" if r.sample_says == "cannot tell" else "no fire"))
    if short:
        return _table("Flooded cropland under the public maps and the sample (95\\% interval). Hh.: farming households if every "
                      "flooded field were lost. Trigger: 500 ha.", "tab:exposure", "llrrrrrrr",
                      ["Area", "Year", "Flooded", "Maps, ha", "Sample, ha", "Hh., maps", "Hh., sample", "Maps fire", "Sample"],
                      rows, size="footnotesize", sep="4pt")
    return _table("Flooded cropland before and after our check, on today's cropland: the public maps against the labelled sample (ratio estimator, "
                  "95\\% interval; judged only with at least five sample points on flooded land). Households: hectares divided by the cereal "
                  "hectares per farming household in the 2025 crop assessment (illustrative and an upper bound: every flooded field counted as lost). "
                  "Trigger: flooded cropland of at least 500 ha.", "tab:exposure", "llrrrrrrr",
                  ["Area", "Year", "Flooded", "Maps, ha", "Sample, ha", "Hh., maps", "Hh., sample", "Maps fire", "Sample"],
                  rows, size="footnotesize", sep="4pt")


def write_appendix_tables():
    """appendix_tables.tex: the detailed tables of the appendix, every number read from a CSV."""
    import sys
    sys.path.insert(0, str(HERE.parents[2] / "cropland"))
    import features as F                               # which summary each feature takes over the box
    R = lambda f: pd.read_csv(RESULTS / f)
    pct = lambda v: f"{100 * v:.1f}\\%"
    out = []
    summ = {f: "10th pct." for f in F.BOX_LOW} | {f: "90th pct." for f in F.BOX_HIGH} | {f: "mean" for f in F.BOX_MEAN}
    out.append(_table("The 18 features of a 210 m box. Each is first computed for every 10 m pixel of 2025 and then summarised over the "
                      "box's $21 \\times 21$ pixels by its most crop-like part (last column), so the model sees one value per feature per box.",
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
    low = pd.read_csv(RESULTS / "precision_bounds.csv").set_index("map").lower_95.to_dict()      # sensitivity.py
    prec = lambda r: f"1.00 ($\\geq${int(low[r.map] * 100) / 100:.2f})" if r.map in low else pm(r.ua, r.ua_se)   # a lower bound rounds down
    out.append(_table("Accuracy of every map on the Aweil test points (cropland; stratified estimators; $\\pm$ one standard error). "
                      "Precision 1.00 means right on every crop call; in brackets the 95\\% Clopper-Pearson lower bound, because a "
                      "standard error of 0 would overstate the certainty.",
                      "tab:accuracy", "lrrrrr", ["Map", "Year", "Precision", "Recall", "F1", "Overall acc."],
                      [(NICE.get(r.map, r.map), r.year, prec(r), pm(r.pa, r.pa_se), pm(r.f1, r.f1_se), f"{r.oa:.2f}")
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
    fic = R("flood_interval_check.csv")                                                         # sensitivity.py
    below = fic[fic.min_days == 1].set_index(["area", "year"]).n_maps_below_low
    rows = [("Aweil" if a_ == "aweil" else "Bor South", y, f"{r.flooded_land_ha:,.0f}", int(r.points_in_flood), int(r.of_them_cropland),
             f"{mp.loc[(a_, y)].min():,.0f} / {mp.loc[(a_, y)].median():,.0f} / {mp.loc[(a_, y)].max():,.0f}",
             f"{r.flooded_crop_ha:,.0f} ({r.low_ha:,.0f}--{r.high_ha:,.0f})", int(below.get((a_, y), 0))) for (a_, y), r in smp.iterrows()]
    out.append(_table("Past floods on today's cropland: the years with at least five sample points on flooded land (1+ flood day, "
                      "June--December). Maps: lowest / median / highest of the 8 public layers; sample: ratio estimator, 95\\% interval. "
                      "Below: how many of the 8 maps lie below the sample's interval; in all other cases the interval is too wide to tell.",
                      "tab:floodyears", "llrrrrrr", ["Area", "Year", "Flooded ha", "Points", "Cropland", "Maps (ha)", "Sample (ha)", "Below"],
                      rows, size="footnotesize", sep="4pt"))
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
    st = R("rule1_national_by_state.csv").sort_values("map_pct", ascending=False)
    out.append(_table("Our map over South Sudan per state (land whose 210 m box holds a field; an upper bound, not checked outside Aweil and Bor South) against the 2025 crop assessment's modelled cereal area.", "tab:national", "lrrrr",
                      ["State", "Our map, \\%", "Our map, ha", "CFSAM cereal, \\%", "CFSAM cereal, ha"],
                      [(r.state, f"{r.map_pct:.1f}", f"{r.map_ha:,.0f}", "--" if pd.isna(r.cfsam_pct) else f"{r.cfsam_pct:.1f}",
                        "--" if pd.isna(r.cfsam_2025_cereal_ha) else f"{r.cfsam_2025_cereal_ha:,.0f}") for r in st.itertuples()]))
    out.append(exposure_table(R))                                                               # 9: Results section
    t = R("rule1_national_test_points.csv")
    a = t[(t.area == "aweil") & (t.definition == "cropland")].set_index("map")
    keep = ["rule1", "map_30m_national"] + [k for k in ORDER if k in a.index]
    nice = NICE | {"rule1": "Rule 1, 10 m map", "map_30m_national": "Rule 1, 30 m national run"}
    out.append(_table("Our map at 10 m and its 30 m national run on the 186 Aweil test points, next to the public maps (cropland; "
                      "stratified estimators; $\\pm$ one standard error).", "tab:nattest", "lrrr", ["Map", "Precision", "Recall", "F1"],
                      [(nice[k], pm(a.loc[k, "ua"], a.loc[k, "ua_se"]), pm(a.loc[k, "pa"], a.loc[k, "pa_se"]), pm(a.loc[k, "f1"], a.loc[k, "f1_se"]))
                       for k in sorted(keep, key=lambda k: -a.loc[k, "f1"])]))                      # 10
    tw = R("sensitivity_three_ways.csv")
    nice3 = NICE | {"rf_features": "random forest, 18 inputs", "rf_embedding": "random forest, embedding"}
    out.append(_table(f"Every map on the Aweil test points, F1 three ways: on the points both labellers agree on (the main score), and with the "
                      f"{int(tw.splits.iloc[0])} test points they split on counted all as cropland, or all as not cropland. Our models stay "
                      "above every public map in each reading.", "tab:threeways", "lrrr",
                      ["Map", "Agreed points only", "Splits as cropland", "Splits as not cropland"],
                      [(nice3.get(r.map, r.map), f"{r.f1_agreed_only:.2f}", f"{r.f1_splits_as_cropland:.2f}", f"{r.f1_splits_as_not:.2f}")
                       for r in tw.sort_values("f1_agreed_only", ascending=False).itertuples()]))     # 11
    v = R("rule1_national_vs_public.csv")
    f = lambda x: "--" if pd.isna(x) else f"{x:.0f}"
    out.append(_table("Without labels: our national map against the public maps at 20,000 uniform random points outside the study areas "
                      "(our map's 30 m pixel; each public map's 10 m pixel at the point). Agreement, not accuracy. Shares in \\% of the land; "
                      "``of 2+ maps'': of the land at least two public maps call crop, the share our map marks (-- with fewer than five such points).",
                      "tab:natvspub", "lrrrrrr", ["State", "Points", "Our map", "Any public map", "Ours, of any", "Ours, of 2+ maps", "Any, of ours"],
                      [(r.state.replace("South Sudan without the study areas", "All (outside our areas)"), f"{r.points:,}", f"{r.ours_pct:.1f}",
                        f"{r.any_public_pct:.1f}", f(r.ours_marks_of_any_public_pct), f(r.ours_marks_of_two_public_pct), f(r.any_public_of_ours_pct))
                       for r in v.itertuples()], size="footnotesize"))                       # 12
    groups = {"app_sample": [1, 2], "app_models": [0, 4], "app_accuracy": [3, 11, 5], "app_floods": [6, 7], "app_national": [10, 8, 12],
              "res_exposure": [9]}   # one file per appendix section (res_exposure: in the Results section)
    for name, idx in groups.items():
        (HERE / f"{name}.tex").write_text("% Written by build_report_inputs.py from CSVs. Do not edit by hand.\n\n"
                                          + "\n".join(out[i] for i in idx), encoding="utf-8")
    (HERE / "res_exposure_final.tex").write_text("% Written by build_report_inputs.py from CSVs. Do not edit by hand.\n\n"
                                                 + exposure_table(R, short=True), encoding="utf-8")   # report_final.tex
    print(f"appendix tables: {len(out)} tables in {len(groups)} files")


def write_national_check_numbers(m):
    """The 30 m national run on our test points (national_map.py score) and its agreement with the public maps (national_map.py compare)."""
    t = pd.read_csv(RESULTS / "rule1_national_test_points.csv")
    a = t[(t.area == "aweil") & (t.definition == "cropland")].set_index("map")
    agree = t[(t.area == "aweil") & (t.definition == "agreement with Rule 1 at the points")].set_index("map")
    n = a.loc["map_30m_national"]
    m |= {"NatThirtyFone": f"{n.f1:.2f}", "NatThirtyFoneSe": f"{n.f1_se:.2f}", "NatThirtyPrec": f"{n.ua:.2f}",
          "NatThirtyRec": f"{n.pa:.2f}", "NatAgreeAw": f"{100 * agree.loc['map_30m_national', 'f1']:.0f}\\%"}
    v = pd.read_csv(RESULTS / "rule1_national_vs_public.csv").set_index("state")     # national_map.py compare
    al = v.loc["South Sudan without the study areas"]
    p1 = lambda x: f"{x:.0f}\\%"
    m |= {"NatOursOfAny": p1(al.ours_marks_of_any_public_pct), "NatOursOfTwo": p1(al.ours_marks_of_two_public_pct),
          "NatAnyOfOurs": p1(al.any_public_of_ours_pct), "NatVsPoints": f"{int(al.points):,}",
          "NatWarrapOfTwo": p1(v.loc["Warrap", "ours_marks_of_two_public_pct"]),
          "NatLakesOfTwo": p1(v.loc["Lakes", "ours_marks_of_two_public_pct"]),
          "NatUpperNileOfTwo": p1(v.loc["Upper Nile", "ours_marks_of_two_public_pct"]),
          "NatUpperNilePublic": p1(v.loc["Upper Nile", "any_public_pct"]),
          "NatEastEqOfTwo": p1(v.loc["Eastern Equatoria", "ours_marks_of_two_public_pct"])}
    return m


def write_household_numbers(m):
    """Illustrative: flooded hectares as farming households (CFSAM 2025 cereal ha per farming household)."""
    hh = K.ha_per_household("aweil")
    h = pd.read_csv(RESULTS / "flood_history.csv")
    h1 = h[(h.min_days == 1) & (h.area == "aweil") & (h.year == 2022)]
    smp = h1[(h1.layer == "sample (ratio)") & (h1.measure == "share of box")].iloc[0]
    mp = h1[h1.layer.isin(ORDER)].flooded_crop_ha
    r10 = lambda v: f"{round(v / hh, -1):,.0f}"
    m |= {"HaPerHhAw": f"{hh:.2f}", "HhTwentyTwoMapsMin": r10(mp.min()), "HhTwentyTwoMapsMax": r10(mp.max()),
          "HhTwentyTwoEst": r10(smp.flooded_crop_ha), "HhTwentyTwoLow": r10(smp.low_ha), "HhTwentyTwoHigh": r10(smp.high_ha)}
    return m


def write_sensitivity_numbers(m):
    """The checks of the feedback round (cropland/sensitivity.py, 15 Oct): no frozen result changes."""
    v = pd.read_csv(RESULTS / "sensitivity_summary.csv").set_index("key").value
    n = lambda k: float(v[k])
    pc = lambda k: f"{n(k):.0f}\\%"
    pb = pd.read_csv(RESULTS / "precision_bounds.csv")
    a = pd.read_csv(RESULTS / "area_adjusted.csv")
    a = a[(a.area == "aweil") & (a.measure == "share of box")].set_index("definition").estimate
    m |= {"LabFoneAw": f"{n('labeller_f1_weighted_aweil_test'):.2f}", "ThreeWaySplits": f"{n('three_ways_splits'):.0f}",
          "ShareLowPct": f"{n('share_class_lowest_pct'):.1f}\\%", "ShareLowHa": f"{round(n('share_class_lowest_ha'), -2):,.0f}",
          "ShareHighPct": f"{n('share_class_highest_pct'):.1f}\\%", "ShareHighHa": f"{round(n('share_class_highest_ha'), -2):,.0f}",
          "ShareSamePct": pc("share_class_same_pct"), "ShareWithinOnePct": pc("share_class_within_one_pct"),
          "RuleOneErrors": f"{n('rule1_test_errors'):.0f}", "RuleOneErrorsAwA": f"{n('rule1_errors_aweil_A'):.0f}",
          "RuleOneFoneUnw": f"{n('rule1_f1_unweighted_aweil_test'):.2f}", "CalCropAwA": f"{n('calibration_crop_boxes_aweil_A'):.0f}",
          "HaPerBoxAwA": f"{round(n('ha_per_box_aweil_A'), -2):,.0f}", "HaPerBoxAwC": f"{n('ha_per_box_aweil_C'):,.0f}",
          "BuildingThreshold": f"{n('rule1_building_threshold_m'):.0f}",
          "FarBoxes": f"{n('agreed_cropland_boxes_far'):.0f}", "AgreedCroplandBoxes": f"{n('agreed_cropland_boxes'):.0f}",
          "FarBoxesPct": pc("cropland_boxes_far_pct_aweil"), "FarAreaPct": pc("cropland_area_far_pct_aweil"),
          "FloodMedianInside": f"{n('flood_years_median_inside_aweil'):.0f}", "FloodPointsMin": f"{n('flood_points_min_aweil'):.0f}",
          "FloodPointsMax": f"{n('flood_points_max_aweil'):.0f}", "FloodZeroEightBelow": f"{n('flood_2008_maps_below_low'):.0f}",
          "FloodTwentyTwoBelow": f"{n('flood_2022_maps_below_low'):.0f}",
          "RecipeFone": f"{n('recipe_f1_mean'):.2f}", "RecipeLow": f"{n('recipe_f1_min'):.2f}", "RecipeHigh": f"{n('recipe_f1_max'):.2f}",
          "RecipePoints": f"{n('recipe_points'):.0f}", "ClosestPointsAw": f"{n('closest_points_m_aweil'):.0f}",
          "PrecLowMin": f"{int(pb.lower_95.min() * 100) / 100:.2f}", "PrecLowMax": f"{int(pb.lower_95.max() * 100) / 100:.2f}",   # round down
          "PrecCallsMin": f"{pb.crop_calls.min()}", "PrecCallsMax": f"{pb.crop_calls.max()}",
          "AwAreaPctTwo": f"{100 * a['cropland']:.2f}\\%", "AwCroppedPctTwo": f"{100 * a['cropped_2025']:.2f}\\%"}
    return m


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


def embed_in_draft():
    """Make report_draft.tex (long version) and report_final.tex (2,000 words) self-contained for Overleaf: numbers,
    tables and the bibliography are written into each file between marked lines (rewritten on every run); only the
    figures stay separate files. The long version must have every block; the final one gets those it asks for."""
    for name in ("report_draft.tex", "report_final.tex"):
        if (HERE / name).exists():
            embed_into(HERE / name, strict=name == "report_draft.tex")


def embed_into(p, strict):
    s = p.read_text(encoding="utf-8")
    strip = lambda t: "\n".join(l for l in t.splitlines() if not l.startswith("% Written by")).strip()
    blocks = {"numbers": (strip((HERE / "numbers.tex").read_text(encoding="utf-8")) + "\n"
                          + strip((HERE / "results.tex").read_text(encoding="utf-8")), "\\input{numbers}\n\\input{results}"),
              "bib": ("\\begin{filecontents*}[overwrite]{references.bib}\n"
                      + (HERE / "references.bib").read_text(encoding="utf-8").strip() + "\n\\end{filecontents*}", None)}
    for name in ("app_sample", "app_models", "app_accuracy", "app_floods", "app_national", "res_exposure", "res_exposure_final"):
        blocks[name] = (strip((HERE / f"{name}.tex").read_text(encoding="utf-8")), f"\\input{{{name}}}")
    for name, (content, old_input) in blocks.items():
        start, end = f"%% <<{name}>> written by build_report_inputs.py: do not edit between these lines", f"%% <</{name}>>"
        block = f"{start}\n{content}\n{end}"
        if start in s:                                                   # refresh
            i, j = s.index(start), s.index(end) + len(end)
            s = s[:i] + block + s[j:]
        elif old_input and old_input in s:                               # first time: replace the \input
            s = s.replace(old_input, block)
        elif name == "bib":                                              # first time: at the very top
            s = block + "\n" + s
        elif strict and name != "res_exposure_final":
            raise SystemExit(f"{p.name}: no place for {name}")
    p.write_text(s, encoding="utf-8")
    print(f"{p.name}: numbers, tables and references embedded (self-contained except figures/)")


def copy_figures():
    out = HERE / "figures"
    out.mkdir(exist_ok=True)
    for f in sorted(FIGURES.glob("*.png")):
        shutil.copy2(f, out / f.name)
    print(f"figures/: {len(list(out.glob('*.png')))} files")


def make_zip():
    """overleaf_upload.zip: both self-contained versions and their figures, nothing else."""
    z = HERE / "overleaf_upload.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(HERE / "report_draft.tex", "report_draft.tex")
        if (HERE / "report_final.tex").exists():
            zf.write(HERE / "report_final.tex", "report_final.tex")
        for f in sorted((HERE / "figures").glob("*.png")):
            zf.write(f, f"figures/{f.name}")
    print(f"{z.name}: report_draft.tex, report_final.tex + figures/ (Overleaf: New project > Upload project > this zip)")


if __name__ == "__main__":
    write_numbers()
    write_results()
    write_appendix_tables()
    embed_in_draft()
    copy_figures()
    make_zip()
