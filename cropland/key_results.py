"""
Every number our report and poster quote, recomputed from the result tables, with the file it comes from.

Nothing is estimated anew here: the values come from the steps before (cropland/results/ and the EDA tables
in deliverables/cropland_report/tables/). This file only collects them, rounds them the way the report and
the poster show them, and writes two tables to deliverables/cropland_report/tables/:

  key_results.csv            one row per number: its name, what it is, its value, how the report shows it,
                             how the poster shows it (empty where one of them does not use it), its source file
  exposure_before_after.csv  the report's exposure table: flooded cropland on today's cropland under the
                             public maps (before our check) and from the labelled sample (after), as farming
                             households, and whether each would fire a 500 ha trigger

Households: flooded hectares divided by the cereal hectares per farming household in the study area's
counties (FAO/WFP crop assessment, CFSAM 2025). Illustrative and an upper bound: every flooded field counts as lost.

Run from group_repo (after the pipeline): python cropland/key_results.py
"""

import numpy as np
import pandas as pd

import common as C
import features as F

RES = C.HERE / "results"
TABLES = C.REPO / "deliverables" / "cropland_report" / "tables"
PUBLIC = ["gfsad_2015", "glad_2019", "deafrica_2019", "worldcover_2021", "worldcereal_2021", "esri_2025",
          "dynamicworld_2025", "asap_v04"]                      # the 8 public layers, as in the figures
SHORT = {"gfsad_2015": "GFSAD", "glad_2019": "GLAD", "deafrica_2019": "DE Africa", "worldcover_2021": "WorldCover",
         "worldcereal_2021": "WorldCereal", "esri_2025": "Esri", "dynamicworld_2025": "Dynamic World", "asap_v04": "ASAP"}
EXPOSURE_YEARS = [("aweil", 2008), ("aweil", 2022), ("aweil", 2025), ("bor_south", 2007), ("bor_south", 2025)]
TRIGGER_HA = 500


def pct(v, decimals=1):
    return f"{v:.{decimals}f}%"


def ha100(v):                                                    # hectares to the nearest 100
    return f"{round(v, -2):,.0f}"


def whole(v):
    return f"{v:,.0f}"


def two(v):
    return f"{v:.2f}"


def ha_per_household(area):
    """Cereal hectares per farming household in the study area's counties, CFSAM 2025."""
    c = pd.read_csv(C.HERE / "reference_statistics.csv").drop_duplicates()
    c = c[(c.source == "CFSAM") & (c.year == 2025) & (c.level == "county") & c.name.isin(C.AREAS[area])]
    return c.cereal_harvested_ha.sum() / c.farming_households.sum()


def exposure(threshold_ha=TRIGGER_HA):
    """Flooded cropland before (the 8 public layers) and after (the sample, ratio estimator) in the report's years.

    The sample is judged only with at least 5 sample points on flooded land (10b_flood_history.py); otherwise
    its columns stay empty and sample_says is "cannot tell"."""
    h = pd.read_csv(RES / "flood_history.csv")
    h = h[h.min_days == 1]
    t = pd.read_csv(RES / "trigger_hindcast.csv")
    t = t[(t.min_days == 1) & (t.threshold_ha == threshold_ha)]
    rows = []
    for area, year in EXPOSURE_YEARS:
        g = h[(h.area == area) & (h.year == year)]
        maps = g[g.layer.isin(PUBLIC)].set_index("layer").flooded_crop_ha
        s = g[(g.layer == "sample (ratio)") & (g.measure == "share of box")].iloc[0]
        points = 0 if pd.isna(s.points_in_flood) else int(s.points_in_flood)
        judged = pd.notna(s.flooded_crop_ha) and points >= 5
        hh = ha_per_household(area)
        fired = t[(t.area == area) & (t.year == year) & t.layer.isin(PUBLIC)]
        rows.append({"area": area, "year": year, "flooded_land_ha": g.flooded_land_ha.iloc[0],
                     "maps_min_ha": maps.min(), "maps_max_ha": maps.max(), "sample_points_on_flooded_land": points,
                     "sample_ha": s.flooded_crop_ha if judged else None,
                     "sample_low_ha": s.low_ha if judged else None, "sample_high_ha": s.high_ha if judged else None,
                     "ha_per_household": hh, "households_maps_min": maps.min() / hh, "households_maps_max": maps.max() / hh,
                     "households_sample": s.flooded_crop_ha / hh if judged else None,
                     f"maps_firing_{threshold_ha}_ha": int((fired.layer_says == "fire").sum()), "maps_scored": len(fired),
                     "sample_says": t[(t.area == area) & (t.year == year) & (t.compared_with == "share of box")].sample_says.iloc[0]})
    return pd.DataFrame(rows)


def numbers():
    """The numbers in the report and on the poster: (name, what, value, report, poster, source).

    report and poster hold the number as each shows it, empty where one does not use it."""
    out = []

    def add(name, what, value, report, poster, source):
        out.append({"name": name, "what": what, "value": value, "report": report, "poster": poster, "source": source})

    # the public maps and the labels (EDA, part 1 of the notebook)
    key = pd.read_csv(TABLES / "key_numbers.csv", index_col=0).value
    src = "tables/key_numbers.csv"
    k = lambda name: float(key[name])
    v = k("Aweil crop share, lowest map (%)")
    add("AwCropMin", "Aweil crop share, lowest public map", v, pct(v, 2), pct(v), src)
    v = k("Aweil crop share, highest map (%)")
    add("AwCropMax", "Aweil crop share, highest public map", v, pct(v, 2), pct(v), src)
    win = pd.read_csv(TABLES / "window_aweil_s020.csv")                 # figure 16 (eda_window.py)
    win = win[win["map"] != "rule1"]
    src = "tables/window_aweil_s020.csv"
    v = win.crop_share_of_window_pct
    add("WindowMin", "6 km window north of Aweil town: crop share, lowest public map", v.min(), pct(v.min()), f"{v.min():.0f}", src)
    add("WindowMax", "the same window: crop share, highest public map", v.max(), pct(v.max()), pct(v.max(), 0), src)
    numbers_word = {2: "two", 7: "seven"}
    v = int(win.labelled_cropland_points.max())
    add("WindowLabelled", "the same window: labelled boxes, all holding cropland", v, numbers_word.get(v, whole(v)), "", src)
    v = int((win.found == 0).sum())
    add("WindowMissAll", "the same window: public maps that find none of them", v, numbers_word.get(v, whole(v)), "", src)
    for w_ in win.itertuples():
        add(f"Window_{w_.map}", f"the same window: {SHORT[w_.map]}'s crop share, and the labelled cropland boxes it finds",
            w_.crop_share_of_window_pct, "", f"{w_.crop_share_of_window_pct:.1f}% · {w_.found} of {w_.labelled_cropland_points} fields", src)
    src = "tables/key_numbers.csv"
    v = k("Aweil land no map calls crop (%)")
    add("AwNoMap", "Aweil land no map calls crop", v, pct(v), "", src)
    v = k("Aweil pairwise IoU, best pair")
    add("AwIoUMax", "Aweil, overlap of two maps' crop (IoU), best pair", v, "", "", src)
    v = k("Labelled twice so far (points)")
    add("LabTwice", "points labelled by two of us", v, whole(v), whole(v), src)
    v = k("Labels given (judgements)")
    add("LabelsGiven", "labels given", v, "", whole(v), src)
    v = k("Labellers agree cropland vs not (%)")
    add("LabAgree", "the two labellers agree on cropland or not", v, pct(v), pct(v), src)
    v = k("Cohen's kappa cropland vs not")
    add("LabKappa", "Cohen's kappa, cropland or not", v, two(v), "", src)
    v = k("Cohen's kappa cropland vs not, Bor South")
    add("LabKappaBs", "Cohen's kappa, cropland or not, Bor South", v, two(v), "", src)
    effort = pd.read_csv(TABLES / "label_effort.csv")
    src = "tables/label_effort.csv"
    add("PointsPerLabeller", "points each of us labelled", effort.points.max(), "", whole(effort.points.max()), src)
    add("LabHoursMin", "hours one labeller took for them, fastest", effort.total_hours.min(), "", whole(effort.total_hours.min()), src)
    add("LabHoursMax", "hours one labeller took for them, slowest", effort.total_hours.max(), "", whole(effort.total_hours.max()), src)
    v = effort.median_min.max()
    add("LabMinutesPerBox", "minutes per box (median), the slowest of us", v, "", "", src)
    v = len(pd.read_csv(C.HERE / "pilot_points.csv"))
    add("PilotPoints", "points in the pilot (step 00)", v, whole(v), "", "pilot_points.csv")

    # the cropland area (share of box, adjusted upper bound)
    a = pd.read_csv(RES / "area_adjusted.csv")
    r = a[(a.area == "aweil") & (a.definition == "cropland") & (a.measure == "share of box")].iloc[0]
    src = "results/area_adjusted.csv"
    add("AwAreaPct", "Aweil cropland, share of the land", 100 * r.estimate, pct(100 * r.estimate), pct(100 * r.estimate), src)
    add("AwAreaLowPct", "Aweil cropland, lower end of the 95% interval", 100 * r.low, pct(100 * r.low), pct(100 * r.low), src)
    add("AwAreaHighPct", "Aweil cropland, adjusted upper bound (cautious; a heuristic, not a guaranteed 95% bound)",
        100 * r.high_adjusted, "", pct(100 * r.high_adjusted), src)
    add("AwAreaHighUsualPct", "Aweil cropland, upper end of the usual 95% interval", 100 * r.high, "", "", src)
    add("AwAreaHa", "Aweil cropland (ha)", r.ha, ha100(r.ha), "", src)
    add("AwAreaLowHa", "Aweil cropland, lower end of the 95% interval (ha)", r.low_ha, ha100(r.low_ha), "", src)
    add("AwAreaHighHa", "Aweil cropland, adjusted upper bound (ha)", r.high_adjusted_ha, ha100(r.high_adjusted_ha), "", src)
    add("AwAreaHighUsualHa", "Aweil cropland, upper end of the usual 95% interval (ha)", r.high_ha, "", "", src)
    b = a[(a.area == "bor_south") & (a.definition == "cropland") & (a.measure == "share of box")].iloc[0]
    add("BsAreaPct", "Bor South cropland, share of the land", 100 * b.estimate,
        pct(100 * b.estimate, 1 if b.estimate >= 0.01 else 2), "", src)
    add("BsAreaHighHa", "Bor South cropland, adjusted upper bound (ha)", b.high_adjusted_ha,
        ha100(b.high_adjusted_ha), "", src)
    cf = pd.read_csv(C.HERE / "reference_statistics.csv")
    cf = cf[(cf.source == "CFSAM") & (cf.year == 2025) & (cf.level == "county")]
    v = cf[cf.name.str.startswith("Aweil")].cereal_harvested_ha.sum()
    add("AwCfsamHa", "Aweil cereal harvested area, CFSAM 2025 (ha)", v, ha100(v), "", "reference_statistics.csv")
    v = cf[cf.name == "Bor South"].cereal_harvested_ha.sum()
    add("BsCfsamHa", "Bor South cereal harvested area, CFSAM 2025 (ha)", v, ha100(v), "", "reference_statistics.csv")

    # the design (typed in the text, recomputed here)
    s = pd.read_csv(C.HERE / "sample.csv")
    src = "sample.csv"
    add("AwPoints", "sample points in Aweil", (s.area == "aweil").sum(), whole((s.area == "aweil").sum()), "", src)
    add("BsPoints", "sample points in Bor South", (s.area == "bor_south").sum(), whole((s.area == "bor_south").sum()), "", src)
    test = (s.split == "test").sum()
    add("TestPoints", "test points, set aside in every stratum before labelling", test,
        "two thirds" if 3 * test == 2 * len(s) else whole(test), "", src)
    add("Features", "features computed for every box", len(F.FEATURES), whole(len(F.FEATURES)), "", "features.py")
    agree = pd.read_csv(TABLES / "pairwise_pixel_agreement_aweil.csv", index_col=0).to_numpy()
    pairs = agree[~np.eye(len(agree), dtype=bool)]                  # every pair of maps, not a map with itself
    lo, hi = 100 * np.nanmin(pairs), 100 * np.nanmax(pairs)
    add("PixelAgreeMin", "Aweil: pixels on which two maps agree, lowest pair", lo, pct(lo, 0), "",
        "tables/pairwise_pixel_agreement_aweil.csv")
    add("PixelAgreeMax", "the same, highest pair", hi, pct(hi, 0), "", "tables/pairwise_pixel_agreement_aweil.csv")

    # Rule 1 and the scores on the Aweil test points (cropland)
    cv = pd.read_csv(RES / "model_cv.csv")
    used = int(pd.read_csv(RES / "rule_complexity.csv").features_used.iloc[0])
    add("CalPoints", "calibration points Rule 1 learned from (both labellers agree)", cv.points.iloc[0],
        whole(cv.points.iloc[0]), whole(cv.points.iloc[0]), "results/model_cv.csv")
    add("InputsUsed", f"inputs Rule 1 uses, of the {len(F.FEATURES)}", used, "", f"{used} of the {len(F.FEATURES)}",
        "results/rule_complexity.csv")
    sv = pd.read_csv(RES / "sensitivity_summary.csv").set_index("key").value
    v = float(sv["rule1_building_threshold_m"])
    add("BuildingThreshold", "Rule 1's first question: a building within (m)", v, f"{v:.0f} m", f"{v:.0f} m",
        "results/sensitivity_summary.csv")
    acc = pd.read_csv(RES / "accuracy.csv")
    ac = acc[(acc.area == "aweil") & (acc.definition == "cropland")].set_index("map")
    src = "results/accuracy.csv"
    add("AwTestPoints", "Aweil test points both labellers agree on", ac.loc["rule1"].test_points,
        whole(ac.loc["rule1"].test_points), "", src)
    rule = ac.loc["rule1"]
    add("RuleOneFone", "Rule 1, F1", rule.f1, two(rule.f1), "", src)
    add("RuleOneFoneLow", "Rule 1, F1, lower end of the 95% interval", max(0, rule.f1 - 1.96 * rule.f1_se),
        two(max(0, rule.f1 - 1.96 * rule.f1_se)), "", src)
    add("RuleOneFoneHigh", "Rule 1, F1, upper end of the 95% interval", min(1, rule.f1 + 1.96 * rule.f1_se),
        two(min(1, rule.f1 + 1.96 * rule.f1_se)), "", src)
    add("RuleOnePrec", "Rule 1, precision", rule.ua, two(rule.ua), "", src)
    add("RuleOneRecall", "Rule 1, recall (share of the real fields it finds)", rule.pa, two(rule.pa), pct(100 * rule.pa, 0), src)
    for name, m, what in [("WorldCerealFone", "worldcereal_2021", "WorldCereal 2021, F1"),
                          ("EsriFone", "esri_2025", "Esri 2025, F1"), ("DwFone", "dynamicworld_2025", "Dynamic World 2025, F1"),
                          ("LogitFone", "logistic_l2", "logistic regression (18 inputs), F1"),
                          ("LogitTwoFone", "logistic_rule1_inputs", "logistic regression (Rule 1's 2 inputs), F1"),
                          ("RfFone", "rf_features", "random forest benchmark, F1"),
                          ("RfEmbFone", "rf_embedding", "random forest on the Satellite Embedding, F1")]:
        add(name, what, ac.loc[m].f1, two(ac.loc[m].f1), "", src)
    add("WorldCerealRecall", "WorldCereal 2021, recall", ac.loc["worldcereal_2021"].pa, two(ac.loc["worldcereal_2021"].pa), "", src)
    perfect = ac.loc[["esri_2025", "worldcover_2021", "glad_2019", "asap_v04"]].pa       # the maps with precision 1.00
    add("PerfectPrecRecallMin", "lowest recall of the maps with precision 1.00", perfect.min(), two(perfect.min()), "", src)
    add("PerfectPrecRecallMax", "highest recall of the maps with precision 1.00", perfect.max(), two(perfect.max()), "", src)
    vals = pd.read_csv(RES / "map_values.csv")
    empty = vals[(vals.split == "test") & (vals.area == "bor_south") & (vals.cropland == 0)]
    add("BsEmptyTest", "Bor South test boxes both labellers saw as empty", len(empty), whole(len(empty)), "", "results/map_values.csv")
    add("BsDwFalseCrop", "of them, Dynamic World 2025 calls crop", empty.dynamicworld_2025.sum(),
        whole(empty.dynamicworld_2025.sum()), "", "results/map_values.csv")
    pb = pd.read_csv(RES / "pixel_count_bias.csv")
    v = pb[(pb.area == "bor_south") & (pb["map"] == "dynamicworld_2025")].ratio_to_sample.iloc[0]
    add("BsDwTimesSample", "Bor South: Dynamic World's crop pixels, times the sample's cropland", v, f"{v:.0f}", "",
        "results/pixel_count_bias.csv")

    # models, sample size
    trees = cv[cv.model.str.startswith("tree")].f1
    add("CvTreeMin", "trees of depth 1-4, cross-validated F1 on the calibration points, lowest", trees.min(),
        two(trees.min()), "", "results/model_cv.csv")
    add("CvTreeMax", "trees of depth 1-4, cross-validated F1, highest", trees.max(), two(trees.max()), "", "results/model_cv.csv")
    add("CvModelsMin", "every model, cross-validated F1 on the calibration points, lowest", cv.f1.min(), "", "",
        "results/model_cv.csv")
    add("CvModelsMax", "every model, cross-validated F1, highest", cv.f1.max(), "", "", "results/model_cv.csv")
    de = pd.read_csv(RES / "design_efficiency.csv")
    v = de[de.area == "aweil"].n_opt.iloc[0]
    add("NoptOurs", "Aweil: points for a 20% coefficient of variation of the area, our strata", v, "", "",
        "results/design_efficiency.csv")

    # floods
    fb = pd.read_csv(RES / "flooded_cropland_bounds.csv")
    for name, area, what in [("AwFloodPoints", "aweil", "Aweil"), ("BsFloodPoints", "bor_south", "Bor South")]:
        v = fb[fb.area == area].points_in_flood_cells.iloc[0]
        add(name, f"{what}: sample points in the 2025 flood cells", v, whole(v), "", "results/flooded_cropland_bounds.csv")
    h = pd.read_csv(RES / "flood_history.csv")
    add("FloodYears", "years of floods laid over today's cropland", h.year.nunique(), "", whole(h.year.nunique()),
        "results/flood_history.csv")
    h = h[h.min_days == 1]
    s = h[(h.layer == "sample (ratio)") & (h.measure == "share of box")]
    judged = s[s.flooded_crop_ha.notna()].set_index(["area", "year"])
    maps = h[h.layer.isin(PUBLIC)].pivot_table(index=["area", "year"], columns="layer", values="flooded_crop_ha")
    src = "results/flood_history.csv"
    add("HistYearsAw", "Aweil flood years 2000-2025 the sample can judge (5+ points on flooded land)",
        len(judged.loc["aweil"]), whole(len(judged.loc["aweil"])), "", src)
    fic = pd.read_csv(RES / "flood_interval_check.csv")
    clear = fic[(fic.area == "aweil") & (fic.min_days == 1) & ~fic.median_inside.astype(bool)].year
    add("FloodClearYears", "those years in which the sample's interval clears the median public map", len(clear),
        ", ".join(map(str, clear)), "", "results/flood_interval_check.csv")
    r, mp = judged.loc[("aweil", 2022)], maps.loc[("aweil", 2022)]
    add("HistTwentyTwoEst", "Aweil 2022 flood on today's cropland: the sample (ha)", r.flooded_crop_ha, whole(r.flooded_crop_ha), "", src)
    add("HistTwentyTwoLow", "the same, lower end of the 95% interval (ha)", r.low_ha, whole(r.low_ha), "", src)
    add("HistTwentyTwoHigh", "the same, upper end of the 95% interval (ha)", r.high_ha, whole(r.high_ha), "", src)
    add("HistTwentyTwoMapsMin", "Aweil 2022: the public maps, lowest (ha)", mp.min(), whole(mp.min()), "", src)
    add("HistTwentyTwoMapsMax", "Aweil 2022: the public maps, highest (ha)", mp.max(), whole(mp.max()), "", src)
    t = pd.read_csv(RES / "trigger_hindcast.csv")
    silent = t[(t.area == "aweil") & (t.year == 2022) & (t.min_days == 1) & (t.threshold_ha == TRIGGER_HA)
               & t.layer.isin(PUBLIC) & (t.layer_says != "fire")].layer
    names = sorted(SHORT[m] for m in silent)
    listed = lambda word: ", ".join(names[:-1]) + f" {word} " + names[-1] if len(names) > 1 else "".join(names)
    add("SilentTwentyTwo", f"Aweil 2022: public maps under which a {TRIGGER_HA} ha trigger stays silent", len(names),
        listed("and"), listed("and"), "results/trigger_hindcast.csv")
    add("SilentTwentyTwoCount", "the same, how many of the public layers", len(names), "", f"{len(names)} of {len(PUBLIC)}",
        "results/trigger_hindcast.csv")
    hh = ha_per_household("aweil")
    tens = lambda v: f"{round(v / hh, -1):,.0f}"
    src = "results/flood_history.csv, reference_statistics.csv"
    add("HhTwentyTwoEst", "Aweil 2022: the sample's flooded cropland as farming households", r.flooded_crop_ha / hh,
        tens(r.flooded_crop_ha), "", src)
    add("HhTwentyTwoLow", "the same, lower end of the 95% interval", r.low_ha / hh, "", "", src)
    add("HhTwentyTwoHigh", "the same, upper end of the 95% interval", r.high_ha / hh, "", "", src)
    add("HhTwentyTwoMapsMin", "Aweil 2022: the public maps, lowest, as farming households", mp.min() / hh, tens(mp.min()), "", src)
    add("HhTwentyTwoMapsMax", "Aweil 2022: the public maps, highest, as farming households", mp.max() / hh, tens(mp.max()), "", src)

    # robustness checks (sensitivity.py)
    n = lambda key_: float(sv[key_])
    src = "results/sensitivity_summary.csv"
    add("ThreeWaySplits", "Aweil test points the two labellers split on", n("three_ways_splits"), "", "", src)
    for name, key_, what, fmt in [
            ("ShareLowPct", "share_class_lowest_pct", "Aweil cropland, every share class at its lowest value", pct),
            ("ShareHighPct", "share_class_highest_pct", "Aweil cropland, every share class at its highest value", pct),
            ("RuleOneErrors", "rule1_test_errors", "Rule 1's errors on the Aweil test points", None),
            ("RuleOneErrorsAwA", "rule1_errors_aweil_A", "of them in stratum A (no map calls crop)", None),
            ("CalCropAwA", "calibration_crop_boxes_aweil_A", "crop boxes among the calibration points of Aweil's stratum A",
             None),
            ("HaPerBoxAwA", "ha_per_box_aweil_A", "hectares one box stands for, Aweil stratum A", ha100),
            ("HaPerBoxAwC", "ha_per_box_aweil_C", "hectares one box stands for, Aweil stratum C", whole),
            ("FarBoxesPct", "cropland_boxes_far_pct_aweil", "Aweil boxes holding cropland more than 333 m from a building",
             lambda v: f"{v:.0f}%"),
            ("RecipeFone", "recipe_f1_mean", "Rule 1's recipe refitted 20 x 5 times, mean F1", two)]:
        add(name, what, n(key_), fmt(n(key_)) if fmt else "", "", src)        # None: computed, not quoted
    return pd.DataFrame(out)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    k = numbers()
    k.to_csv(TABLES / "key_results.csv", index=False)
    e = exposure()
    e.to_csv(TABLES / "exposure_before_after.csv", index=False)
    print(f"key_results.csv: {len(k)} numbers ({(k.report != '').sum()} in the report, {(k.poster != '').sum()} on the poster); "
          f"exposure_before_after.csv: {len(e)} rows")


if __name__ == "__main__":
    main()
