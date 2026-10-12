"""
Evaluation of the method, on top of 09_score.py and 10_flood.py
(report: "Evaluation methodology" and "Results").

  1. area_interval: the area estimate with two intervals. Crop is rare in the
     big stratum where no map says crop (95% of Aweil), so a sample often holds
     no cropland box there and the usual +/-1.96 SE interval ends below the
     truth. simulate_interval_coverage shows how often, for our exact design;
     the adjusted interval keeps the usual lower bound and takes the upper bound
     from a cautious variance: per stratum at least the variance it would have
     with one more cropland and one more empty box, using the cropland shares of
     the whole study area.
  2. error_analysis: where each map fails, by what the labellers saw (cover
     class, crop cues, homestead distance, crop vs fallow, share of the box).
  3. pixel_count_bias: each map's area by pixel counting against the area from
     the labelled sample.
  4. trigger_agreement: would each map's flooded-cropland number fire a trigger
     when the sample says it should (and not when it should not)?
  5. published_vs_ours: our precision / recall / F1 next to Kerner et al. (2024)
     and Adebayo et al. (2026).
  6. design_efficiency: points needed for a target precision with our agreement
     strata against strata from one map (Adebayo et al. 2026; efficiency.py).
  7. rule_complexity: how readable a frozen rule file is.

All of it reads the outputs of steps 06, 09 and 10 and writes nothing into
cropland/ except what a caller saves. Only test points are used for map
accuracy, as in 09_score.py.
"""

import numpy as np
import pandas as pd

import efficiency as EF
import estimators as ES

Z = 1.96


# ---------------------------------------------------------------- 1. the area interval

def area_interval(y, strata, W, crop=None):
    """Share of the area (stratified mean) with the usual and the adjusted 95% interval.

    y: per point, 0/1 (box holds cropland) or the cropland share of the box.
    crop: per point, True where the box holds cropland (defaults to y > 0).
    Returns dict: estimate, se, low, high (usual), high_adjusted (adjusted upper bound).
    """
    y, strata = np.asarray(y, float), np.asarray(strata)
    crop = (y > 0) if crop is None else np.asarray(crop, bool)
    est, se = ES.area(y, strata, W)
    m1 = y[crop].mean() if crop.any() else 1.0                 # cropland shares of the whole area (1 for 0/1 values)
    m2 = (y[crop] ** 2).mean() if crop.any() else 1.0
    var_adj = 0.0
    for h, w in W.items():
        yh, ch = y[strata == h], crop[strata == h]
        n = len(yh)
        if n < 2:
            continue
        p = (ch.sum() + 1) / (n + 2)                           # one more cropland and one more empty box
        var_adj += w ** 2 * max(yh.var(ddof=1), p * m2 - (p * m1) ** 2) / n
    return {"estimate": est, "se": se, "low": max(0.0, est - Z * se), "high": est + Z * se,
            "high_adjusted": est + Z * np.sqrt(var_adj)}


def simulate_interval_coverage(W, n, p, share_mix=None, reps=20000, seed=42):
    """How often the usual and the adjusted interval contain the true area share, for a design.

    W, n, p: stratum weights, points and crop rates (true share of boxes holding cropland).
    share_mix: per stratum, probabilities of the four share classes (5, 17.5, 37.5, 75%) of a
    cropland box; None simulates the 0/1 measure ("box holds cropland").
    """
    rng = np.random.default_rng(seed)
    mids = np.array([0.05, 0.175, 0.375, 0.75])
    W, n, p = np.asarray(W, float), np.asarray(n), np.asarray(p, float)
    vals, truth = [], 0.0
    for h in range(len(W)):
        c = rng.random((reps, n[h])) < p[h]
        if share_mix is None:
            vals.append(c.astype(float))
            truth += W[h] * p[h]
        else:
            vals.append(np.where(c, rng.choice(mids, size=(reps, n[h]), p=share_mix[h]), 0.0))
            truth += W[h] * p[h] * (mids * np.asarray(share_mix[h])).sum()
    allv = np.concatenate(vals, axis=1)
    nz = allv > 0
    m1 = np.where(nz.any(1), (allv * nz).sum(1) / np.maximum(nz.sum(1), 1), 1.0)
    m2 = np.where(nz.any(1), (allv ** 2).sum(1) / np.maximum(nz.sum(1), 1), 1.0)
    est, v, v_adj = np.zeros(reps), np.zeros(reps), np.zeros(reps)
    zero_a = None
    for h, d in enumerate(vals):
        x = (d > 0).sum(1)
        sv = d.var(1, ddof=1)
        q = (x + 1) / (n[h] + 2)
        est += W[h] * d.mean(1)
        v += W[h] ** 2 * sv / n[h]
        v_adj += W[h] ** 2 * np.maximum(sv, q * m2 - (q * m1) ** 2) / n[h]
        if h == 0:
            zero_a = (x == 0).mean()
    low = np.maximum(0, est - Z * np.sqrt(v))
    high, high_adj = est + Z * np.sqrt(v), est + Z * np.sqrt(v_adj)
    return {"true_share_pct": 100 * truth, "bias_pp": 100 * (est.mean() - truth),
            "coverage_usual": np.mean((low <= truth) & (truth <= high)),
            "below_truth_usual": np.mean(high < truth),
            "coverage_adjusted": np.mean((low <= truth) & (truth <= high_adj)),
            "halfwidth_usual_pp": 100 * Z * np.sqrt(v).mean(),
            "upper_extra_pp": 100 * (high_adj - high).mean(),
            "no_cropland_point_in_first_stratum": zero_a}


# ---------------------------------------------------------------- 2. where each map fails

def labeller_context(labels_long, features=None):
    """One row per point with what both labellers saw: shared cover class, cues seen by both, crop or fallow.

    labels_long: the sample_labels_<name>.csv files stacked (both labellers of a point).
    features: features_sample.csv (for the distance to buildings), optional.
    """
    cues = ["cue_a_bare", "cue_b_greenup", "cue_c_harvest", "cue_d_shape", "cue_e_crop2024"]
    g = labels_long.groupby("id")
    out = pd.DataFrame({
        "cover": g.cover.agg(lambda s: s.iloc[0] if s.nunique() == 1 else "labellers differ"),
        "fallow_any": g.label.agg(lambda s: (s == "fallow").any()),
        "share_class": g.crop_share.agg(lambda s: s.dropna().iloc[0] if s.dropna().nunique() == 1 else "differs"),
    })
    for c in cues:
        out[c] = g[c].agg(lambda s: (s == "yes").all())       # both labellers said yes
    out["open_no_cues"] = (out.cover == "open") & ~out[cues[:4]].any(axis=1)    # open land, no crop cue: grass
    if features is not None:
        d = features.set_index("id").dist_buildings_m
        out["homestead"] = pd.cut(d.reindex(out.index), [-1, 250, 1000, 1e9], labels=["< 250 m", "250-1000 m", "> 1 km"])
    return out.reset_index()


def error_analysis(values, context, maps, reference="cropland"):
    """False crop (commission) and missed crop (omission) of every map, by what the labellers saw.

    values: results/map_values.csv (test points; reference column agreed by both labellers).
    Returns a long table: map, kind (false crop / missed crop), group, value, points, errors, share.
    Counts are unweighted: they say where errors happen, not how much area they cover.
    """
    d = values[(values.split == "test") & values[reference].notna()].merge(context, on="id", how="left")
    ref = d[reference].astype(int)
    rows = []
    for m in maps:
        pred = d[m].astype(int)
        for kind, pool, err in (("false crop", ref == 0, pred == 1), ("missed crop", ref == 1, pred == 0)):
            for group in ("area", "stratum", "cover", "open_no_cues", "cue_d_shape", "fallow_any", "share_class", "homestead"):
                if group not in d:
                    continue
                for val, part in d[pool].groupby(group, observed=True):
                    e = err[part.index]
                    rows.append({"map": m, "kind": kind, "group": group, "value": val, "points": len(part),
                                 "errors": int(e.sum()), "share": e.mean() if len(part) else np.nan})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 3. pixel counting against the sample

def pixel_count_bias(map_shares, reference):
    """Each map's crop share by pixel counting against the sample estimate (share of box) with its interval.

    map_shares: Series map -> % of land (EDA, crop_share_by_county.csv for one area).
    reference: dict with estimate, low, high_adjusted in % of land (area_interval of the labels).
    """
    out = pd.DataFrame({"map_pct": map_shares})
    out["ratio_to_sample"] = out.map_pct / reference["estimate"]
    out["inside_interval"] = (out.map_pct >= reference["low"]) & (out.map_pct <= reference["high_adjusted"])
    out["direction"] = np.where(out.map_pct < reference["low"], "under", np.where(out.map_pct > reference["high_adjusted"], "over", "within"))
    return out


# ---------------------------------------------------------------- 4. trigger decisions

def trigger_agreement(flooded, thresholds, reference_label="reference: cropland (share of box)"):
    """For each area and threshold: what the sample says (fire / no fire / cannot tell) against each map.

    flooded: results/flooded_cropland.csv (10_flood.py): area, map, flooded_crop_ha, ci_low_ha, ci_high_ha.
    The sample says "fire" when even its lower bound is at or above the threshold, "no fire" when its
    upper bound is below it, "cannot tell" otherwise.
    """
    rows = []
    for area, t in flooded.groupby("area"):
        ref = t[t["map"] == reference_label].iloc[0]
        maps = t[~t["map"].str.startswith(("reference", "all flooded"))]
        for thr in thresholds:
            truth = "fire" if ref.ci_low_ha >= thr else ("no fire" if ref.ci_high_ha < thr else "cannot tell")
            for r in maps.itertuples():
                call = "fire" if r.flooded_crop_ha >= thr else "no fire"
                rows.append({"area": area, "threshold_ha": thr, "sample_says": truth, "map": r.map,
                             "map_ha": r.flooded_crop_ha, "map_says": call,
                             "agrees": np.nan if truth == "cannot tell" else call == truth})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 5. ours against the papers

def published_vs_ours(accuracy, literature, key=None):
    """Our precision, recall and F1 per map next to the published mean and range (both papers)."""
    key = key or {"esri": "esri_2025", "dynamicworld": "dynamicworld_2025", "deafrica": "deafrica_2019",
                  "worldcover": "worldcover_2021", "gfsad": "gfsad_2015", "glad": "glad_2019", "asap": "asap_v04"}
    lit = literature[literature["map"].isin(key)].assign(map=lambda t: t["map"].map(key))
    per = lit[lit.country != "Mean"]
    pub = per.groupby(["map", "metric"]).value.agg(published_min="min", published_max="max").reset_index()
    mean = lit[(lit.country == "Mean") & (lit.source == "Kerner et al. 2024")][["map", "metric", "value"]].rename(
        columns={"value": "kerner_mean"})
    ours = accuracy.melt(id_vars=["area", "definition", "map"], value_vars=["ua", "pa", "f1"], var_name="metric",
                         value_name="ours").replace({"metric": {"ua": "precision", "pa": "recall"}})
    se = accuracy.melt(id_vars=["area", "definition", "map"], value_vars=["ua_se", "pa_se", "f1_se"], var_name="metric",
                       value_name="ours_se").replace({"metric": {"ua_se": "precision", "pa_se": "recall", "f1_se": "f1"}})
    out = ours.merge(se, on=["area", "definition", "map", "metric"]).merge(pub, on=["map", "metric"], how="left") \
              .merge(mean, on=["map", "metric"], how="left")
    out["position"] = np.where(out.ours < out.published_min, "below published range",
                               np.where(out.ours > out.published_max, "above published range", "within published range"))
    return out


# ---------------------------------------------------------------- 6. which strata need the fewest points

def design_efficiency(values, strata_weights, maps, reference="cropland", cv=0.20):
    """Points needed for a target coefficient of variation: our agreement strata against one-map strata.

    values: results/map_values.csv for ONE area (all labelled points; reference agreed or mean).
    strata_weights: {stratum: share of the area}.
    For a one-map design, the share of land the map calls crop and the crop rate inside each map class
    are estimated from our sample with the stratified ratio estimators, then efficiency.n_opt.
    """
    d = values[values[reference].notna()]
    y = d[reference].to_numpy(float)
    s = d.stratum.to_numpy()
    p_h = np.array([y[s == h].mean() for h in strata_weights])
    W = np.array(list(strata_weights.values()))
    rows = [{"design": "agreement strata (ours)", "n_opt": EF.n_opt(W, p_h, cv)}]
    for m in maps:
        x = d[m].to_numpy(float)
        w_crop = sum(w * x[s == h].mean() for h, w in strata_weights.items())      # map's crop share of the area
        if w_crop <= 0 or w_crop >= 1:
            continue
        p_crop, _ = ES._ratio(y * x, x, s, strata_weights)                           # crop rate where the map says crop
        p_not, _ = ES._ratio(y * (1 - x), 1 - x, s, strata_weights)                  # ... and where it says not crop
        rows.append({"design": m, "n_opt": EF.n_opt([w_crop, 1 - w_crop], [p_crop, p_not], cv),
                     "map_crop_share": w_crop, "crop_rate_map_crop": p_crop, "crop_rate_map_not_crop": p_not})
    out = pd.DataFrame(rows)
    out["relative_efficiency_of_ours"] = out.n_opt / out.n_opt.iloc[0]          # > 1: ours needs fewer points
    return out


# ---------------------------------------------------------------- 7. how readable is a rule file

def rule_complexity(ruleset):
    """Number of rules, the longest rule, the features used: a readable rule is short."""
    conds = [r["if"] for r in ruleset["rules"]]
    used = sorted({f for c in conds for f, _, _ in c})
    return {"rules": len(conds), "longest_rule_conditions": max((len(c) for c in conds), default=0),
            "features_used": len(used), "which": ", ".join(used)}
