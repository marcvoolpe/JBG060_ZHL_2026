"""
Figures 17-26 for the report and its appendix: the method, the models, the sample and the checks.
Same palette and style as eda_figures.py; static PNGs, each with a CSV twin where it plots numbers.

  17 method diagram                     22 feature distributions, cropland vs not
  18 Rule 1 as a tree, with counts      23 strata and sample points (map)
  19 Rule 1's decision space            24 the labelling tool for one box (images, greenness, radar, key)
  20 models: cross-validation vs test   25 interval check by simulation
  21 what the models learned            26 points needed per sampling design

Run from group_repo: python cropland/report_figures.py      (no Earth Engine; all inputs are in git)
"""

import json

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from PIL import Image

import common as C
import eda_figures as FG
import eda_maps as EM
import features as F
import rules as R

RES = C.HERE / "results"
INK, INK2, MUTED, GRID, SURF, BLUE, ORANGE = FG.INK, FG.INK2, FG.MUTED, FG.GRID_C, FG.SURFACE, FG.SERIES[0], FG.SERIES[1]
LIGHT_BLUE, LIGHT_ORANGE = "#e3eefb", "#fbe6dc"
FEATURE_NAMES = {
    "ndvi_min_am": "greenness, lowest Apr-May", "bsi_max_am": "bare soil, highest Apr-May",
    "ndvi_peak_jja": "greenness, peak Jun-Aug", "greenup": "green-up (peak minus spring)",
    "drop_son": "harvest drop to Sep-Nov", "drop_vs_500m": "harvest drop vs 500 m around",
    "texture_jja": "texture at peak", "edge_density": "field edges (edge density)",
    "ndvi_min_jfm": "dry-season greenness (trees)", "water_occurrence": "surface water occurrence",
    "s1_vv_min": "radar VV, lowest", "dist_buildings_m": "distance to nearest building",
    "burned": "burned Nov-Apr", "vh_jun": "radar VH, June", "vh_jul": "radar VH, July",
    "vh_aug": "radar VH, August", "vh_sep": "radar VH, September", "vh_range": "radar VH, range over the year"}
MODELS = {"tree_d1": "tree, depth 1", "tree_d2": "tree, depth 2 (= Rule 1)", "tree_d3": "tree, depth 3",
          "tree_d4": "tree, depth 4", "logistic_l2": "logistic regression, 18 inputs",
          "logistic_l1": "logistic regression, L1 (not frozen)", "logistic_rule1_inputs": "logistic regression, Rule 1's 2 inputs",
          "rf_features": "random forest, 18 inputs (benchmark)", "rf_embedding": "random forest, embedding (benchmark)"}
TEST_NAME = {"tree_d2": "rule1"}


def _box(ax, x, y, w, h, text, fill, edge=INK2, size=8.5, weight="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.015", facecolor=fill,
                                edgecolor=edge, linewidth=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=INK, weight=weight, wrap=True)


def _arrow(ax, x0, y0, x1, y1):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=INK2, linewidth=1.1, shrinkA=2, shrinkB=2))


def method_diagram():
    """17: one top-down flow; data enter from the left, details on the right; no arrow crosses a box."""
    fig, ax = plt.subplots(figsize=(10, 7.2))
    ax.set_xlim(0, 1), ax.set_ylim(0, 1), ax.axis("off")
    grey = "#f0f0f0"
    # main column: the three steps of the sample
    steps = [(0.83, "1. Agreement strata from the\n7 public maps (10 m)"),
             (0.645, "2. 450 random points,\nsplit before labelling"),
             (0.46, "3. Two blind labels per\n210 m box around a point")]
    for y, t in steps:
        _box(ax, 0.34, y, 0.32, 0.11, t, LIGHT_BLUE, size=9, weight="semibold")
    _arrow(ax, 0.5, 0.83, 0.5, 0.755), _arrow(ax, 0.5, 0.645, 0.5, 0.57)
    # data on the left
    for y, t in ((0.83, "WorldCover, GLAD, DE Africa,\nWorldCereal, Esri, Dynamic\nWorld, GFSAD"),
                 (0.46, "Sentinel-2 monthly 2025,\nSentinel-1 radar, dated\nsub-metre images (Esri)")):
        _box(ax, 0.02, y, 0.26, 0.11, t, grey, size=8)
        _arrow(ax, 0.28, y + 0.055, 0.34, y + 0.055)
    ax.text(0.02, 0.965, "Data", fontsize=9, weight="semibold", color=INK2)
    ax.text(0.34, 0.965, "Sample and labels", fontsize=9, weight="semibold", color=INK2)
    # details on the right (no box)
    for y, t in ((0.83, "A: no map sees crop (95% of Aweil)\nB: 1-2 maps        C: 3 or more"),
                 (0.645, "Aweil 150 / 90 / 90, Bor South 60 / 60\n1/3 calibration, 2/3 test, 100 m apart"),
                 (0.46, "crop / fallow / not crop / unsure\n+ share of the box; splits are kept")):
        ax.text(0.69, y + 0.055, t, fontsize=8.3, color=INK2, va="center")
    # three uses of the labels
    ax.text(0.02, 0.385, "Estimates", fontsize=9, weight="semibold", color=INK2)
    outs = [(0.02, "Cropland area with\n95% interval\n(all labelled points)"),
            (0.36, "Rule 1 and other models\n(calibration points only;\n18 features per box; frozen)"),
            (0.70, "Precision, recall, F1 of\nevery map, incl. ours\n(test points only)")]
    for x, t in outs:
        _box(ax, x, 0.21, 0.28, 0.13, t, LIGHT_ORANGE, size=8.5)
    _arrow(ax, 0.42, 0.46, 0.16, 0.34), _arrow(ax, 0.5, 0.46, 0.5, 0.34), _arrow(ax, 0.58, 0.46, 0.84, 0.34)
    _arrow(ax, 0.64, 0.275, 0.70, 0.275)
    _box(ax, 0.02, 0.02, 0.96, 0.11, "Flooded cropland and trigger check: NASA flood masks laid over every map, our map and the sample\n"
         "(2025, and the floods of 2000-2025 on today's cropland)  ->  which map to trust where, how much cropland, what a trigger would do",
         "#ffffff", edge=ORANGE, size=8.5)
    for x in (0.16, 0.5, 0.84):
        _arrow(ax, x, 0.21, x, 0.13)
    return FG._save(fig, "17_method_diagram")


def _rule1_counts():
    t = pd.read_csv(C.HERE / "model_table.csv")
    rs = R.load(C.HERE / "rule1_2026-10-12.json")
    X = t[rs["features"]].fillna(rs["fill"])
    near, edges = X.dist_buildings_m <= 333.4111, X.edge_density > 0.0937
    t["leaf"] = np.where(~near, "far", np.where(edges, "near_edges", "near_no_edges"))
    rows = []
    for split, target in (("calibration", "crop"), ("test", "cropland")):
        d = t[(t.split == split) & t[target].notna()]
        for leaf, g in d.groupby("leaf"):
            rows.append({"split": split, "leaf": leaf, "points": len(g), "cropland": int(g[target].sum())})
    return pd.DataFrame(rows), t


def rule1_tree():
    """18: Rule 1 as a two-question tree, with calibration and test counts in every leaf."""
    c, _ = _rule1_counts()
    c.to_csv(EM.TABLES / "rule1_leaves.csv", index=False)
    get = lambda s, l: c[(c.split == s) & (c.leaf == l)].iloc[0] if ((c.split == s) & (c.leaf == l)).any() else None
    def txt(leaf):
        out = []
        for s, name in (("calibration", "calibration"), ("test", "test")):
            r = get(s, leaf)
            out.append(f"{name}: {r.cropland} of {r.points} cropland" if r is not None else f"{name}: none")
        return "\n".join(out)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_xlim(0, 1), ax.set_ylim(0, 1), ax.axis("off")
    _box(ax, 0.3, 0.78, 0.4, 0.17, "Is there a building within 333 m\nof the box? (Google Open Buildings)", LIGHT_BLUE, size=9.5)
    _box(ax, 0.02, 0.42, 0.34, 0.2, "NOT CROP\n" + txt("far"), "#f1f0ec", size=8.5)
    _box(ax, 0.5, 0.45, 0.42, 0.17, "Does the box show field edges?\n(edge density at peak greenness > 0.094)", LIGHT_BLUE, size=9.5)
    _box(ax, 0.32, 0.06, 0.32, 0.2, "NOT CROP\n" + txt("near_no_edges"), "#f1f0ec", size=8.5)
    _box(ax, 0.66, 0.06, 0.32, 0.2, "CROP\n" + txt("near_edges"), LIGHT_ORANGE, size=8.5, weight="semibold")
    _arrow(ax, 0.4, 0.78, 0.2, 0.62), _arrow(ax, 0.6, 0.78, 0.71, 0.62)
    _arrow(ax, 0.62, 0.45, 0.48, 0.26), _arrow(ax, 0.8, 0.45, 0.82, 0.26)
    for x, y, t in ((0.27, 0.72, "no"), (0.69, 0.72, "yes"), (0.52, 0.37, "no"), (0.84, 0.37, "yes")):
        ax.text(x, y, t, fontsize=9, color=INK2, style="italic")
    ax.text(0.0, 0.0, "Fitted on the 125 calibration points both labellers agree on (target: cropped in 2025); depth chosen by "
            "cross-validation; frozen 12 Oct. Test points: scored after freezing (target: cropland).", fontsize=7.5, color=INK2)
    return FG._save(fig, "18_rule1_tree")


def rule1_space():
    """19: every agreed point on Rule 1's two inputs, with the region Rule 1 calls crop."""
    _, t = _rule1_counts()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, (split, target, title) in zip(axes, (("calibration", "crop", "Calibration points (Rule 1 learned from these)"),
                                                 ("test", "cropland", "Test points (scored after freezing)"))):
        d = t[(t.split == split) & t[target].notna()]
        x = d.dist_buildings_m.clip(lower=5)
        ax.axvspan(5, 333.4, ymin=0, ymax=1, color=GRID, alpha=0.35, linewidth=0)
        ax.fill_between([5, 333.4], 0.0937, 0.6, color=LIGHT_ORANGE, linewidth=0)
        ax.axvline(333.4, color=INK2, linewidth=0.8, linestyle=(0, (3, 2)))
        ax.axhline(0.0937, xmin=0, xmax=np.log(333.4 / 4) / np.log(3000 / 4), color=INK2, linewidth=0.8, linestyle=(0, (3, 2)))
        yes = d[target] == 1
        ax.scatter(x[~yes], d.edge_density[~yes], s=22, facecolor=SURF, edgecolor=INK2, linewidth=0.9, label="no cropland")
        ax.scatter(x[yes], d.edge_density[yes], s=22, color=INK, edgecolor=SURF, linewidth=0.6, label="cropland")
        ax.set_xscale("log"), ax.set_xlim(4, 3000), ax.set_ylim(0, 0.6)
        ax.set_xlabel("distance to the nearest building, m (10th percentile in the box; log scale)")
        ax.set_title(f"{title}: {len(d)}", loc="left", fontsize=9)
    axes[0].set_ylabel("field edges (edge density)")
    axes[0].text(6, 0.55, "Rule 1: crop", color=ORANGE, fontsize=9, weight="semibold")
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    return FG._save(fig, "19_rule1_decision_space")


def models_cv_vs_test():
    """20: every model's F1 in cross-validation on the calibration points and on the test points."""
    cv = pd.read_csv(RES / "model_cv.csv").set_index("model")
    acc = pd.read_csv(RES / "accuracy.csv")
    acc = acc[(acc.area == "aweil") & (acc.definition == "cropped_2025")].set_index("map")
    rows = []
    for m, name in MODELS.items():
        r = {"model": name}
        if m in cv.index:
            r |= {"cv_f1": cv.loc[m, "f1"], "cv_low": cv.loc[m, "f1_low"], "cv_high": cv.loc[m, "f1_high"]}
        tm = TEST_NAME.get(m, m)
        if tm in acc.index:
            r |= {"test_f1": acc.loc[tm, "f1"], "test_low": max(0, acc.loc[tm, "f1"] - 1.96 * acc.loc[tm, "f1_se"]),
                  "test_high": min(1, acc.loc[tm, "f1"] + 1.96 * acc.loc[tm, "f1_se"])}
        rows.append(r)
    t = pd.DataFrame(rows)
    t.round(3).to_csv(EM.TABLES / "models_cv_vs_test.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 4.4))
    y = np.arange(len(t))[::-1]
    for yi, r in zip(y, t.itertuples()):
        if not pd.isna(getattr(r, "cv_f1", np.nan)):
            ax.hlines(yi + 0.13, r.cv_low, r.cv_high, color=BLUE, linewidth=2)
            ax.scatter(r.cv_f1, yi + 0.13, s=36, color=BLUE, zorder=3, edgecolor=SURF)
        if not pd.isna(getattr(r, "test_f1", np.nan)):
            ax.hlines(yi - 0.13, r.test_low, r.test_high, color=ORANGE, linewidth=2)
            ax.scatter(r.test_f1, yi - 0.13, s=36, color=ORANGE, zorder=3, edgecolor=SURF)
    ax.set_yticks(y, t.model, fontsize=8.5)
    ax.set_xlim(0, 1), ax.set_xlabel("F1")
    FG._hgrid(ax)
    ax.scatter([], [], color=BLUE, label="cross-validation on the 125 calibration points (5 folds x 20; every point alike)")
    ax.scatter([], [], color=ORANGE, label="test points, Aweil (stratum weights; 95% interval); frozen models only")
    ax.legend(frameon=False, fontsize=7.5, loc="lower left", bbox_to_anchor=(0, -0.38))
    fig.tight_layout()
    return FG._save(fig, "20_models_cv_vs_test")


def what_models_learned():
    """21: logistic regression coefficients (per SD) and random-forest importances, same 18 inputs."""
    co = pd.read_csv(RES / "logistic_coefficients.csv")
    co = co[co.model == "logistic_l2"].set_index("feature").coef_per_sd
    rf = joblib.load(C.OUT / "benchmarks.joblib")["rf"]
    imp = pd.Series(rf.feature_importances_, index=F.FEATURES)
    order = co.abs().sort_values().index
    pd.DataFrame({"logistic_coef_per_sd": co, "rf_importance": imp}).round(4).to_csv(EM.TABLES / "models_learned.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.2), sharey=True)
    y = np.arange(len(order))
    axes[0].barh(y, co[order], color=[ORANGE if v > 0 else BLUE for v in co[order]], height=0.6)
    axes[0].axvline(0, color=INK2, linewidth=0.8)
    axes[0].set_title("Logistic regression (18 inputs): change in log-odds of crop\nper standard deviation (orange: more crop)",
                      loc="left", fontsize=9)
    axes[1].barh(y, imp[order], color=INK2, height=0.6)
    axes[1].set_title("Random forest (benchmark): share of the splits'\nimpurity reduction per input", loc="left", fontsize=9)
    axes[0].set_yticks(y, [FEATURE_NAMES[f] for f in order], fontsize=8)
    for ax in axes:
        FG._hgrid(ax)
    fig.tight_layout()
    return FG._save(fig, "21_what_models_learned")


def feature_distributions():
    """22: the 18 features for boxes with and without cropland (all points both labellers agree on)."""
    t = pd.read_csv(C.HERE / "model_table.csv")
    d = t[t.cropland.notna()]
    fig, axes = plt.subplots(3, 6, figsize=(11, 6))
    for ax, f in zip(axes.ravel(), F.FEATURES):
        if f in ("burned", "water_occurrence"):                  # nearly yes/no: share of boxes instead of a box plot
            v = [(d.loc[d.cropland == k, f] > 0).mean() for k in (0, 1)]
            ax.bar([1, 2], v, color=[GRID, LIGHT_ORANGE], edgecolor=INK2, width=0.55)
            ax.set_xticks([1, 2], ["no", "yes"], fontsize=7.5), ax.set_ylim(0, 1), ax.tick_params(labelsize=7)
            ax.set_title(FEATURE_NAMES[f] + " (share > 0)", fontsize=7.5)
            continue
        data = [d.loc[d.cropland == 0, f].dropna(), d.loc[d.cropland == 1, f].dropna()]
        bp = ax.boxplot(data, widths=0.55, patch_artist=True, showfliers=False, medianprops=dict(color=INK))
        for patch, col in zip(bp["boxes"], (GRID, LIGHT_ORANGE)):
            patch.set_facecolor(col), patch.set_edgecolor(INK2)
        ax.set_xticks([1, 2], ["no", "yes"], fontsize=7.5)
        ax.set_title(FEATURE_NAMES[f], fontsize=7.5)
        ax.tick_params(labelsize=7)
        if f == "dist_buildings_m":
            ax.set_yscale("log")
    fig.text(0.01, 0.005, f"Boxes both labellers agree on: {int((d.cropland == 0).sum())} without cropland (no), "
             f"{int((d.cropland == 1).sum())} with cropland (yes); calibration and test together. Boxes: middle half; line: median.",
             fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return FG._save(fig, "22_feature_distributions")


def strata_map():
    """23: share of each flood cell where at least one public map sees crop, and the 450 sample points."""
    s = pd.read_csv(C.HERE / "sample.csv")
    import geopandas as gpd
    admin = gpd.read_file(C.ADMIN2)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), gridspec_kw={"width_ratios": [1.6, 1]})
    for ax, (area, title) in zip(axes, (("aweil", "Aweil counties"), ("bor_south", "Bor South"))):
        cells = EM.zoa_cells(area)
        cells = cells[cells.inside > 0.5]
        seen = 1 - cells.agree_0
        g0, c0 = cells.gr.min(), cells.gc.min()
        grid = np.full((cells.gr.max() - g0 + 1, cells.gc.max() - c0 + 1), np.nan)
        grid[cells.gr - g0, cells.gc - c0] = seen
        ext = (cells.lon.min() - EM.GRID / 2, cells.lon.max() + EM.GRID / 2, cells.lat.min() - EM.GRID / 2, cells.lat.max() + EM.GRID / 2)
        im = ax.imshow(grid, cmap=matplotlib.colors.ListedColormap(["#f4f3ef"] + FG.BLUES[:5]),
                       norm=matplotlib.colors.BoundaryNorm([0, 0.001, 0.05, 0.15, 0.3, 0.5, 1], 6), extent=ext, interpolation="nearest")
        admin[admin[C.ADMIN2_NAME].isin(C.AREAS[area])].boundary.plot(ax=ax, color=INK2, linewidth=0.6)
        p = s[s.area == area]
        for st, mk in (("A", "o"), ("B", "s"), ("C", "^")):
            q = p[p.stratum == st]
            if q.empty:
                continue
            ax.scatter(q.lon, q.lat, s=10, marker=mk, color=ORANGE, edgecolor=INK, linewidth=0.4, label=f"stratum {st}: {len(q)}")
        ax.set_aspect(1 / np.cos(np.radians(cells.lat.mean())))
        ax.set_axis_off()
        ax.set_title(f"{title}: {len(p)} sample points", loc="left", fontsize=9.5)
        ax.legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(0, 0), ncol=3)
    cb = fig.colorbar(im, ax=axes, shrink=0.6, pad=0.02)
    cb.set_label("share of the cell where at least one public map sees crop", fontsize=8)
    cb.set_ticks([0, 0.001, 0.05, 0.15, 0.3, 0.5, 1], labels=["0", "", "5%", "15%", "30%", "50%", "100%"], fontsize=7)
    return FG._save(fig, "23_strata_and_sample")


LABEL_EXAMPLE = "S017"        # a box both labellers called crop (sure, 10-25% of the box); the poster shows the same box
PART_COLOURS = ["#b98200", "#b4332e", "#2f7d4a"]               # the labelling tool's colours for the parts of a box
COVER = {"open": "yes, some open land", "water": "no, mostly water", "settlement": "no, mostly buildings or road",
         "trees": "no, mostly trees or shrub"}
SHARES = {"0": "none", "<10": "under 10%", "10-25": "10–25%", "25-50": "25–50%", ">50": "over 50%"}
SURE = {1: "1 (a guess)", 2: "2 (fairly sure)", 3: "3 (sure)"}


def labelling_examples(pid=LABEL_EXAMPLE):
    """24: what the labelling tool shows for one box, and how the box was labelled: the monthly images, the greenness of
    the box and its parts, radar, and the key's questions (taken from the tool's config) with both labellers' answers
    and the final label. Data from label_tool/ (step 04), labels/ and labels_final.csv (step 06)."""
    js = (C.HERE / "label_tool" / "data_sample.js").read_text(encoding="utf-8")
    p = next(q for q in json.loads(js[js.index("["):js.rindex("]") + 1]) if q["id"] == pid)
    cfg = (C.HERE / "label_tool" / "config.js").read_text(encoding="utf-8")
    cfg = json.loads(cfg[cfg.index("{"):cfg.rindex("}") + 1])
    given = pd.concat([pd.read_csv(f) for f in sorted((C.HERE / "labels").glob("sample_labels_*.csv"))])
    given = given[given.id == pid].fillna("").sort_values("labeller")
    final = pd.read_csv(C.HERE / "labels_final.csv").set_index("id").loc[pid]
    months, initials = np.arange(12), list("JFMAMJJASOND")

    fig = plt.figure(figsize=(10, 11.2))
    outer = fig.add_gridspec(3, 1, height_ratios=[1.18, 1.0, 1.12], hspace=0.26)

    ax = fig.add_subplot(outer[0])                                   # 1: the twelve monthly images
    ax.imshow(np.asarray(Image.open(C.HERE / "label_tool" / "img" / f"{pid}_2025_tc.webp").convert("RGB")))
    ax.set_axis_off()
    ax.set_title(f"1  Box {pid}: monthly Sentinel-2 images of 2025 (true colour, 510 m across); yellow: the 210 m box",
                 loc="left", fontsize=10)

    mid = outer[1].subgridspec(1, 3, width_ratios=[1.4, 0.72, 1.0], wspace=0.2)
    ax = fig.add_subplot(mid[0])                                     # 2: greenness of the box, its parts and the land around
    for a, b, name, fill in cfg["season_bands"]:
        ax.axvspan(a - 0.5, b + 0.5, color=fill, zorder=0)
        ax.text((a + b) / 2, 0.87, name.replace("·", " "), ha="center", fontsize=8, color=INK2)
    ax.fill_between(months, p["ndvi_p10"], p["ndvi_p90"], color="#5d6b62", alpha=0.18, linewidth=0, label="10–90% of its pixels")
    for k, part in enumerate(p["patches"]):
        ax.plot(months, part["ndvi"], color=PART_COLOURS[k], linewidth=1.3, label=f"part {'ABC'[k]}, {part['share']:.0%} of the box")
    ax.plot(months, p["ndvi_500m"], color="#5d6b62", linewidth=1.2, linestyle=(0, (4, 2)), label="the 500 m around it (grass)")
    ax.plot(months, p["ndvi"], color="#2b3a30", linewidth=2.2, label="the box (median)")
    ax.set_xticks(months, initials, fontsize=8)
    ax.set_ylim(0, 0.95), ax.set_xlim(-0.5, 11.5)
    ax.set_ylabel("NDVI", fontsize=8)
    ax.set_title("2  Greenness (NDVI) of the box through 2025", loc="left", fontsize=10)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6), ax.set_axisbelow(True)
    handles, names = ax.get_legend_handles_labels()

    side = fig.add_subplot(mid[1])                                   # its legend, and where the parts are
    side.set_axis_off()
    side.legend(handles[::-1], names[::-1], frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(-0.02, 1.02),
                handlelength=1.6, labelspacing=0.55)
    n = int(round(len(p["patch_map"]) ** 0.5))                       # the parts on the box's 21 x 21 pixels, as the tool draws them
    grid = np.array([int(c) for c in p["patch_map"]]).reshape(n, n)
    parts = side.inset_axes([0.08, 0.0, 0.62, 0.42])
    parts.imshow(np.array([matplotlib.colors.to_rgb(PART_COLOURS[v]) for v in grid.ravel()]).reshape(n, n, 3))
    parts.set_xticks([]), parts.set_yticks([])
    parts.set_title("where the parts are", fontsize=7.5, color=INK2, pad=3)
    for s in parts.spines.values():
        s.set_color("#e6c200"), s.set_linewidth(1.5)

    ax = fig.add_subplot(mid[2])                                     # 3: radar, which sees through the clouds
    vh = np.array([np.nan if v is None else v for v in p["vh"]], dtype=float)
    ax.plot(months, vh, "o-", color="#5b4a8b", markersize=3.5, linewidth=1.6)
    ax.set_xticks(months, initials, fontsize=8)
    ax.set_ylim(-30, -5), ax.set_xlim(-0.5, 11.5)
    ax.set_ylabel("VH backscatter (dB)", fontsize=8)
    ax.set_title("3  Radar (Sentinel-1), sees through clouds", loc="left", fontsize=10)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6), ax.set_axisbelow(True)
    gap = [["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][i] for i in months if np.isnan(vh[i])]
    ax.text(0.03, 0.96, "rises as the crop grows,\ndrops at harvest" + (f";\nno radar pass {gap[0]}–{gap[-1]}" if gap else ""),
            transform=ax.transAxes, fontsize=7.5, color=INK2, va="top")

    ax = fig.add_subplot(outer[2])                                   # 4: the key, both labellers' answers, the final label
    ax.set_axis_off()
    ax.set_xlim(0, 1), ax.set_ylim(0, 1)
    ax.set_title("4  The labelling key, answered by two labellers who did not see each other's answers", loc="left", fontsize=10)
    who = list(given.labeller)
    x_q, x_a = 0.0, [0.715, 0.865]
    fs, step = 8, 0.068

    def row(y, label, values, bold=False, line=True):
        ax.text(x_q, y, label, fontsize=fs, color=INK, va="center", weight="semibold" if bold else "normal")
        for x, v in zip(x_a, values):
            ax.text(x, y, v, fontsize=fs, color=INK, va="center", weight="semibold" if bold else "normal")
        if line:
            ax.plot([0, 1], [y - step / 2, y - step / 2], color=GRID, linewidth=0.7)

    y = 0.96
    row(y, "Question in the tool", [f"labeller {w}" for w in who], bold=True)
    y -= step
    row(y, f"Is there open land (field or grass) anywhere in the {cfg['box_m']} m box?", [COVER.get(v, v) for v in given.cover])
    for col in ("cue_a_bare", "cue_b_greenup", "cue_c_harvest", "cue_d_shape", "cue_e_crop2024"):
        y -= step
        row(y, cfg["cues"][col], [v if v else "no answer" for v in given[col]])
    y -= step * 1.25
    row(y, "The key suggests", list(given.key_suggestion))
    y -= step
    row(y, "Label given (the labeller can overrule the key)", list(given.label))
    y -= step
    row(y, "Cropland in the box (crop and fallow fields together)", [SHARES.get(str(v), str(v)) for v in given.crop_share])
    y -= step
    row(y, "Confidence", [SURE.get(int(v), str(v)) for v in given.confidence], line=False)
    y -= step * 1.35
    agree = "the two agree" if final.disagreed == 0 else "the two disagree: it counts as half a cropland box"
    ax.text(x_q, y, f"Final label (step 06): {final.final}, {agree}. In the area estimate the box holds "
            f"{100 * final.share_avg:.1f}% cropland, the mid-point of their share class.", fontsize=fs, color=INK,
            va="center", weight="semibold")

    pd.DataFrame({"month": initials, "ndvi_box": p["ndvi"], "ndvi_p10": p["ndvi_p10"], "ndvi_p90": p["ndvi_p90"],
                  "ndvi_500m": p["ndvi_500m"], **{f"ndvi_part_{'ABC'[k]}": q["ndvi"] for k, q in enumerate(p["patches"])},
                  "radar_vh_db": vh}).assign(id=pid).to_csv(EM.TABLES / "labelling_examples.csv", index=False)
    return FG._save(fig, "24_labelling_examples")


def interval_simulation():
    """25: how often the usual and the adjusted interval hold the true area, in simulations of our design."""
    t = pd.read_csv(EM.TABLES / "interval_coverage_simulation.csv")
    groups = list(t.groupby(["area", "measure"], sort=False))
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.4), sharey=True)
    for ax, ((area, measure), g) in zip(axes.ravel(), groups):
        g = g.sort_values("true_share_pct").reset_index(drop=True)
        x = np.arange(len(g))
        ax.plot(x, g.coverage_usual, "o-", color=INK2, markersize=4, linewidth=1.2, label="usual: estimate ±1.96 SE")
        ax.plot(x, g.coverage_adjusted, "o-", color=ORANGE, markersize=4, linewidth=1.5, label="with the adjusted upper bound")
        ax.axhline(0.95, color=INK2, linewidth=0.8, linestyle=(0, (3, 2)))
        ax.set_xticks(x, [f"{v:.1f}" for v in g.true_share_pct], fontsize=7)
        ax.set_title(f"{area}, measure: {measure}", loc="left", fontsize=9)
        ax.set_ylim(0.4, 1.02)
        ax.yaxis.grid(True, color=GRID, linewidth=0.8), ax.set_axisbelow(True)
    for ax in axes[1]:
        ax.set_xlabel("true cropland share of the simulated area, % (one scenario each)")
    for ax in axes[:, 0]:
        ax.set_ylabel("interval holds the truth")
    axes[0, 0].legend(frameon=False, fontsize=8, loc="lower right")
    fig.text(0.01, 0.005, "20,000 simulated samples per scenario with our allocation; dashed: the 95% the interval promises.", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return FG._save(fig, "25_interval_simulation")


def design_points():
    """26: points needed for a 20% coefficient of variation: our agreement strata against strata from one map."""
    d = pd.read_csv(RES / "design_efficiency.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, (area, g) in zip(axes, d.groupby("area", sort=False)):
        g = g.sort_values("n_opt").reset_index(drop=True)
        cols = [ORANGE if s.startswith("agreement") else BLUE for s in g.design]
        y = np.arange(len(g))[::-1]
        ax.barh(y, g.n_opt, color=cols, height=0.6)
        for yi, v in zip(y, g.n_opt):
            ax.text(v * 1.01, yi, f"{v:,.0f}", va="center", fontsize=7.5, color=INK2)
        ax.set_yticks(y, ["our agreement strata" if s.startswith("agreement") else FG._name(s) for s in g.design], fontsize=8)
        ax.set_title(f"{'Aweil counties' if area == 'aweil' else 'Bor South'}: points for a 20% CV of the area", loc="left", fontsize=9)
        FG._hgrid(ax)
    fig.tight_layout()
    return FG._save(fig, "26_points_per_design")


if __name__ == "__main__":
    for f in (method_diagram, rule1_tree, rule1_space, models_cv_vs_test, what_models_learned, feature_distributions,
              strata_map, labelling_examples, interval_simulation, design_points):
        print(f.__name__, "->", f().name)
