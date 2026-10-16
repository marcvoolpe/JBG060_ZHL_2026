"""
Figures for the EDA of the public cropland maps (report and poster).

Static PNGs for a printed report, so no hover layer: every figure has a CSV
twin in deliverables/cropland_report/tables/ with the exact values. Colours follow
one rule: maps are categories on an axis, so they share one colour; a second
colour only appears when a second series is plotted (validated palette:
blue, orange, aqua).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap

import eda_maps as D

INK, INK2, MUTED, GRID_C, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]                     # categorical slots 1-3, in this order
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]   # sequential, light -> dark
ORDER = ["gfsad_2015", "glad_2019", "deafrica_2019", "worldcover_2021", "worldcereal_2021",
         "esri_2025", "dynamicworld_2025", "asap_v04"]          # by map year, oldest first

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "semibold",
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2,
    "axes.facecolor": SURFACE, "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False, "figure.dpi": 110})


def _save(fig, name):
    D.FIGURES.mkdir(parents=True, exist_ok=True)
    path = D.FIGURES / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def _hgrid(ax):
    ax.xaxis.grid(True, color=GRID_C, linewidth=0.8)
    ax.set_axisbelow(True)


def _name(m):
    return D.NAMES.get(m, m)


def crop_share(panels, refs):
    """Horizontal bars: % of land each map calls crop, one panel per area, CFSAM / FAOSTAT as reference lines.

    panels: {title: Series map -> crop %}; refs: {title: [(label, value %), ...]}.
    """
    fig, axes = plt.subplots(1, len(panels), figsize=(3.3 * len(panels), 3.4), sharey=True)
    for ax, (title, s) in zip(np.atleast_1d(axes), panels.items()):
        s = s.reindex(ORDER)
        y = np.arange(len(s))[::-1]
        ax.barh(y, s.values, height=0.55, color=SERIES[0])
        top = max(s.max(), max(v for _, v in refs.get(title, [("", 0)])))
        for yi, v in zip(y, s.values):
            ax.text(v + top * 0.02, yi, f"{v:.2f}%", va="center", fontsize=8, color=INK2, zorder=4,
                    bbox=dict(facecolor=SURFACE, edgecolor="none", pad=0.4))
        for k, (label, v) in enumerate(refs.get(title, [])):          # labels in their own rows above the bars
            ax.axvline(v, color=INK2, linewidth=1)
            ax.text(v + top * 0.015, len(s) - 0.25 + 0.6 * k, f"{label}: {v:.1f}%", fontsize=7, color=INK2,
                    va="center", ha="left", zorder=4, bbox=dict(facecolor=SURFACE, edgecolor="none", pad=0.4))
        ax.set_ylim(-0.6, len(s) + 0.4 + 0.6 * max(len(refs.get(title, [])) - 1, 0))
        ax.set_xlim(0, top * 1.35)
        ax.set_title(title, loc="left", pad=8)
        ax.set_xlabel("crop, % of land")
        _hgrid(ax)
    ax0 = np.atleast_1d(axes)[0]
    ax0.set_yticks(np.arange(len(ORDER))[::-1], [_name(m) for m in ORDER])
    fig.tight_layout()
    return _save(fig, "01_crop_share_per_map")


def agreement_curves(curves):
    """Share of land called crop by at least k of the 7 maps, k = 1..7 (log scale), one line per area."""
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    k = np.arange(1, 8)
    for i, (label, vals) in enumerate(curves.items()):
        v = np.maximum(np.asarray(vals, float), 1e-5)
        ax.plot(k, v, color=SERIES[i], linewidth=2, marker="o", markersize=5, markeredgecolor=SURFACE,
                markeredgewidth=1.5, label=label)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: np.format_float_positional(v, trim="-")))
    ax.set_xticks(k)
    ax.set_xlabel("at least k of the 7 strata maps say crop")
    ax.set_ylabel("% of land")
    ax.set_ylim(1e-5, 20)
    ax.yaxis.grid(True, color=GRID_C, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_title("Cropland that several maps agree on is almost absent", loc="left")
    fig.tight_layout()
    return _save(fig, "02_agreement_curve")


def pairwise_iou(iou, title, name):
    """Heatmap: of the land two maps call crop, the share both call crop (intersection over union)."""
    m = iou.copy().astype(float)
    labels = [_name(c) for c in m.columns]
    fig, ax = plt.subplots(figsize=(5.0, 4.2))
    bounds = [0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 1.0]
    cmap = ListedColormap(BLUES)
    im = ax.imshow(np.ma.masked_invalid(m.values), cmap=cmap, norm=BoundaryNorm(bounds, cmap.N))
    for i in range(len(m)):
        for j in range(len(m)):
            if i != j and np.isfinite(m.values[i, j]):
                v = m.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                        color="white" if v >= 0.15 else INK)
    ax.set_xticks(range(len(m)), labels, rotation=40, ha="right")
    ax.set_yticks(range(len(m)), labels)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.8, ticks=bounds)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=7, color=MUTED)
    cb.set_label("overlap of the crop class (IoU)", fontsize=8, color=INK2)
    ax.set_title(title, loc="left")
    fig.tight_layout()
    return _save(fig, name)


def flooded(tab, refs=None):
    """Small multiples: flooded cropland (ha) per map, rows = areas, columns = years, log scale.

    tab: columns unit, year, map, flooded_crop_ha, flooded_land_ha.
    """
    units, years = list(dict.fromkeys(tab.unit)), sorted(tab.year.unique())
    fig, axes = plt.subplots(len(units), len(years), figsize=(3.6 * len(years), 2.7 * len(units)), sharey=True)
    axes = np.atleast_2d(axes)
    for r, u in enumerate(units):
        for c, yr in enumerate(years):
            ax = axes[r, c]
            t = tab[(tab.unit == u) & (tab.year == yr)].set_index("map")
            order = [m.replace("_2025", f"_{yr}") if m.startswith(("esri", "dynamicworld")) else m for m in ORDER]
            v = t.flooded_crop_ha.reindex(order).fillna(0).to_numpy()
            y = np.arange(len(order))[::-1]
            ax.barh(y, np.maximum(v, 1), height=0.55, color=SERIES[0])
            for yi, vi in zip(y, v):
                ax.text(max(vi, 1) * 1.15, yi, f"{vi:,.0f}", va="center", fontsize=7.5, color=INK2)
            ax.set_xscale("log")
            ax.set_xlim(1, 1e6)
            for label, val in (refs or {}).get((u, yr), []):
                ax.axvline(val, color=INK2, linewidth=1)
                ax.text(val * 1.25, (len(order) - 1) / 2, label, rotation=90, fontsize=7, color=INK2, ha="left", va="center")
            land = t.flooded_land_ha.iloc[0] if len(t) else np.nan
            ax.set_title(f"{u}\n{yr}: {land:,.0f} ha flooded", loc="left", fontsize=9)
            _hgrid(ax)
            if c == 0:
                ax.set_yticks(y, [_name(m).replace(" (course data)", "") for m in order], fontsize=8)
            if r == len(units) - 1:
                ax.set_xlabel("flooded cropland, ha (log scale)")
    fig.tight_layout()
    return _save(fig, "07_flooded_cropland_per_map")


def flood_history(h, min_days=1):
    """Past floods on today's cropland: the public maps as one range band, our sample as dots with 95% intervals.

    h: results/flood_history.csv (10b_flood_history.py). Rule 1 is left out on purpose: its hectares
    count land whose 210 m box holds crop, not comparable with the maps' pixels (it is in the table).
    Writes the figure and its CSV twin (tables/flood_history.csv).
    """
    h = h[h.min_days == min_days]
    maps = h[h.layer.isin(ORDER)].pivot_table(index=["area", "year"], columns="layer", values="flooded_crop_ha")
    s = h[(h.layer == "sample (ratio)") & (h.measure == "share of box")].set_index(["area", "year"])
    twin = pd.DataFrame({"maps_min": maps.min(axis=1), "maps_median": maps.median(axis=1), "maps_max": maps.max(axis=1)}) \
        .join(s[["flooded_land_ha", "points_in_flood", "of_them_cropland", "flooded_crop_ha", "low_ha", "high_ha"]]
              .rename(columns={"flooded_crop_ha": "sample_ha", "low_ha": "sample_low_ha", "high_ha": "sample_high_ha"}))
    D.TABLES.mkdir(parents=True, exist_ok=True)
    twin.round(0).to_csv(D.TABLES / "flood_history.csv")
    areas = {"aweil": "Aweil counties", "bor_south": "Bor South"}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    for ax, (area, title) in zip(axes, areas.items()):
        t = twin.loc[area]
        yrs = t.index.to_numpy()
        ax.fill_between(yrs, t.maps_min, t.maps_max, color=GRID_C, linewidth=0, label="public maps, range of 8")
        ax.plot(yrs, t.maps_median, color=MUTED, linewidth=1.5, label="public maps, median")
        ok = t.sample_ha.notna()
        ax.vlines(yrs[ok], t.sample_low_ha[ok], t.sample_high_ha[ok], color=SERIES[0], linewidth=2)
        ax.plot(yrs[ok], t.sample_ha[ok], "o", color=SERIES[0], markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5,
                label="our sample, 95% interval (5+ points on flooded land)")
        ax.set_title(f"{title}: {int(ok.sum())} of {len(t)} years with enough sample points", loc="left")
        ax.set_xlim(1999.5, 2025.5)
        ax.set_ylim(0, None)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.yaxis.grid(True, color=GRID_C, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_ylabel("cropland under water, ha")
    top = h[h.layer.isin(ORDER)].loc[lambda d: d.groupby(["area", "year"]).flooded_crop_ha.idxmax()]
    if (top[top.area == "bor_south"].layer == "dynamicworld_2025").mean() > 0.9:        # name the edge where one map is it
        t = twin.loc["bor_south"]
        axes[1].annotate("upper edge: Dynamic World 2025", (2010, t.maps_max.loc[2010]), xytext=(2012, t.maps_max.loc[2010] * 0.9),
                         fontsize=7.5, color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.8))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=8, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    return _save(fig, "12_flood_history")


OURS = {"rule1": "Rule 1, our 2-question map", "logistic_l2": "logistic regression, 18 inputs",
        "logistic_rule1_inputs": "logistic regression, Rule 1's 2 inputs",
        "rf_features": "random forest (benchmark)", "rf_embedding": "random forest on embedding (benchmark)"}


def area_vs_maps(bias, area_adj):
    """Cropland share of the land: each public map (pixel count, blue) against our labelled sample (orange band).

    bias: results/pixel_count_bias.csv; area_adj: results/area_adjusted.csv. Log scale (Bor South spans 0.01-9%).
    Writes figure 14 and its CSV twin.
    """
    titles = {"aweil": "Aweil counties", "bor_south": "Bor South"}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    twin = []
    for ax, (area, title) in zip(axes, titles.items()):
        r = area_adj[(area_adj.area == area) & (area_adj.definition == "cropland") & (area_adj.measure == "share of box")].iloc[0]
        lo, est, hi = 100 * r.low, 100 * r.estimate, 100 * r.high_adjusted
        m = bias[bias.area == area].set_index("map").map_pct.reindex(ORDER)
        y = np.arange(len(m))[::-1]
        floor = 0.01
        ax.axvspan(max(lo, floor), hi, color=SERIES[1], alpha=0.18, linewidth=0)
        ax.axvline(est, color=SERIES[1], linewidth=2)
        ax.scatter(np.maximum(m.values, floor), y, s=42, color=SERIES[0], zorder=3, edgecolor=SURFACE, linewidth=1)
        for yi, v in zip(y, m.values):
            ax.text(max(v, floor) * 1.25, yi, "0" if v < floor else f"{v:.2f}%", va="center", fontsize=7.5, color=INK2)
        ax.set_xscale("log")
        ax.set_xlim(floor * 0.8, 40)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}%"))
        ax.set_title(f"{title}: our sample {est:.1f}% ({lo:.1f}-{hi:.1f}%)", loc="left")
        ax.set_xlabel("share of the land that is cropland (log scale)")
        _hgrid(ax)
        twin += [{"area": area, "map": k, "map_pct": v, "sample_pct": est, "sample_low_pct": lo, "sample_high_adjusted_pct": hi}
                 for k, v in m.items()]
    axes[0].set_yticks(np.arange(len(ORDER))[::-1], [_name(m).replace(" (course data)", "") for m in ORDER], fontsize=8)
    fig.text(0.01, 0.005, "Blue: each public map, share of its pixels. Orange: our labelled sample, estimate and 95% interval "
             "(adjusted upper bound).", fontsize=7.5, color=INK2)
    pd.DataFrame(twin).round(3).to_csv(D.TABLES / "area_vs_maps.csv", index=False)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, "14_area_vs_maps")


def scorecard(acc, area="aweil", definition="cropland", agreement=None, precision_lower=None):
    """Precision, recall and F1 of every map on the test points, 95% intervals; public maps blue, ours orange.

    acc: results/accuracy.csv. agreement: F1 of one labeller scored against the other with the same stratum
    weights (evaluation.labeller_f1). Not a ceiling: the maps are scored only on points both labellers agree on.
    Maps whose intervals overlap are not ranked (METHODOLOGY section 7). Writes figure 15 and its CSV twin.
    """
    a = acc[(acc.area == area) & (acc.definition == definition)].sort_values("f1").reset_index(drop=True)
    y = np.arange(len(a))
    colours = [SERIES[1] if m in OURS else SERIES[0] for m in a["map"]]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 4.4), sharey=True)
    for ax, (col, title) in zip(axes, (("ua", "Precision: right when it says crop"),
                                       ("pa", "Recall: share of the fields it finds"), ("f1", "F1: both together"))):
        v, se = a[col].to_numpy(), a[f"{col}_se"].to_numpy()
        ax.hlines(y, np.clip(v - 1.96 * se, 0, 1), np.clip(v + 1.96 * se, 0, 1), color=colours, linewidth=2)
        if col == "ua" and precision_lower:            # right on every crop call: SE 0, so draw the exact lower bound
            for i, m in enumerate(a["map"]):
                if m in precision_lower:
                    ax.hlines(i, precision_lower[m], 1, color=colours[i], linewidth=1.2, linestyle=(0, (2, 1.5)))
        ax.scatter(v, y, s=40, color=colours, zorder=3, edgecolor=SURFACE, linewidth=1)
        ax.set_xlim(0, 1)
        ax.set_title(title, loc="left", fontsize=9)
        _hgrid(ax)
    if agreement is not None:
        axes[2].axvline(agreement, color=INK2, linewidth=1, linestyle=(0, (3, 2)))
        axes[2].text(agreement + 0.02, -0.4, f"labeller against\nlabeller: {agreement:.2f}", fontsize=7.5, color=INK2, ha="left", va="bottom")
    axes[0].set_yticks(y, [OURS.get(m, _name(m).replace(" (course data)", "")) for m in a["map"]], fontsize=8)
    for t, c in zip(axes[0].get_yticklabels(), colours):
        t.set_color(INK if c == SERIES[1] else INK2)
    fig.text(0.01, 0.005, f"{area.replace('_', ' ').title()}, {definition}, test points both labellers agree on; lines: 95% intervals. "
             "Orange: our models; blue: public maps. Overlapping intervals are not ranked. Dashed: one labeller scored against "
             "the other with the same weights (all test points, so not a ceiling)."
             + ("\nPrecision 1.00: right on every crop call; the thin dashes reach the 95% lower bound (Clopper-Pearson)."
                if precision_lower else ""), fontsize=7.5, color=INK2)
    a[["map", "test_points", "ua", "ua_se", "pa", "pa_se", "f1", "f1_se"]].round(3).to_csv(D.TABLES / "scorecard.csv", index=False)
    fig.tight_layout(rect=(0, 0.07 if precision_lower else 0.04, 1, 1))
    return _save(fig, "15_scorecard")


def states_vs_cfsam(st, cfsam, maps, year):
    """Small multiples: crop area per state, each map against CFSAM's cereal harvested area (log-log)."""
    from scipy.stats import spearmanr
    n = len(maps)
    cols = 4
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(2.4 * cols, 2.3 * rows), sharex=True, sharey=True)
    lim = (1e2, 3e6)
    for ax, m in zip(axes.ravel(), maps):
        x, y = cfsam.reindex(st.index).to_numpy(), st[m].to_numpy()
        ax.plot(lim, lim, color=AXIS, linewidth=1)
        ax.scatter(x, np.maximum(y, lim[0]), s=22, color=SERIES[0], edgecolor=SURFACE, linewidth=1, zorder=3)
        rho = spearmanr(x, y).correlation
        ax.set_title(f"{_name(m).replace(' (course data)', '')}\nrank corr. {rho:+.2f}", fontsize=8.5, loc="left")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlim(lim); ax.set_ylim(lim)
        ax.grid(True, color=GRID_C, linewidth=0.6)
        ax.set_axisbelow(True)
    for ax in axes.ravel()[n:]:
        ax.axis("off")
    fig.supxlabel(f"CFSAM {year} cereal harvested area per state, ha", fontsize=8.5, color=INK2)
    fig.supylabel("map crop area per state, ha", fontsize=8.5, color=INK2)
    fig.tight_layout()
    return _save(fig, f"05_states_vs_cfsam_{year}")


def national_choropleths(cty, counties, maps, cfsam_state=None):
    """Small multiples: % of each county each map calls crop (same classes everywhere), plus CFSAM per state."""
    bounds = [0, 0.1, 0.5, 1, 2, 5, 10, 100]
    cmap = ListedColormap(BLUES)
    norm = BoundaryNorm(bounds, cmap.N)
    panels = [(m, 100 * cty[m] / cty.land_ha) for m in maps]
    n = len(panels) + (cfsam_state is not None)
    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(3.0 * cols, 2.6 * rows))
    g = counties.copy()
    for ax, (m, share) in zip(axes.ravel(), panels):
        g["v"] = share.to_numpy()
        g.plot(column="v", ax=ax, cmap=cmap, norm=norm, edgecolor=SURFACE, linewidth=0.2)
        ax.set_title(_name(m).replace(" (course data)", ""), loc="left", fontsize=9)
        ax.set_axis_off()
    if cfsam_state is not None:
        ax = axes.ravel()[len(panels)]
        states = D.admin(2).dissolve("adm1_name").reset_index()
        states["v"] = states.adm1_name.map(cfsam_state)
        states.plot(column="v", ax=ax, cmap=cmap, norm=norm, edgecolor=SURFACE, linewidth=0.4,
                    missing_kwds={"color": GRID_C})
        ax.set_title("CFSAM 2025 cereal area (per state)", loc="left", fontsize=9)
        ax.set_axis_off()
    for ax in axes.ravel()[n:]:
        ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cb = fig.colorbar(sm, ax=axes.ravel().tolist(), shrink=0.6, ticks=bounds[:-1] + [100])
    cb.ax.set_yticklabels(["0", "0.1", "0.5", "1", "2", "5", "10", "100"])
    cb.set_label("crop, % of county land", fontsize=8, color=INK2)
    cb.outline.set_visible(False)
    return _save(fig, "04_national_crop_share_per_county")


def lol_strip(tab):
    """Dot plot: crop % of land within 5 km of the Lol river against the rest of the Aweil counties."""
    t = tab.reindex(ORDER)
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    y = np.arange(len(t))[::-1]
    for yi, (a, b) in zip(y, t[["rest", "strip"]].to_numpy()):
        ax.plot([a, b], [yi, yi], color=AXIS, linewidth=2, zorder=1)
    ax.scatter(t.rest, y, s=40, color=SERIES[0], edgecolor=SURFACE, linewidth=1.5, zorder=3, label="rest of the Aweil counties")
    ax.scatter(t.strip, y, s=40, color=SERIES[1], edgecolor=SURFACE, linewidth=1.5, zorder=3, label="within 5 km of the Lol")
    ax.set_yticks(y, [_name(m).replace(" (course data)", "") for m in t.index])
    ax.set_xlabel("crop, % of land")
    _hgrid(ax)
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.set_title("Along the Lol, where ZOA works and fields flood", loc="left")
    fig.tight_layout()
    return _save(fig, "08_lol_strip")


LIT_KEY = {"esri": "esri_2025", "dynamicworld": "dynamicworld_2025", "deafrica": "deafrica_2019",
           "worldcover": "worldcover_2021", "gfsad": "gfsad_2015", "glad": "glad_2019", "asap": "asap_v04"}
PAPERS = [("Kerner et al. 2024", "Kerner et al. 2024, 8 countries"), ("Adebayo et al. 2026", "Adebayo et al. 2026, 6 countries")]


def published_accuracy(lit):
    """Dots: F1 and recall the two papers found for our maps, one dot per country; ticks: their mean.

    lit: reference_accuracy_literature.csv. Mali (2% crop, most like Aweil) gets a dark ring.
    """
    from matplotlib.lines import Line2D
    pos = dict(zip(ORDER, np.arange(len(ORDER))[::-1]))
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.9), sharey=True)
    for ax, metric, title in zip(axes, ("f1", "recall"), ("F1", "Recall: share of real crop the map finds")):
        for i, (src, label) in enumerate(PAPERS):
            off = 0.15 if i == 0 else -0.15
            t = lit[(lit.source == src) & (lit.metric == metric) & lit["map"].isin(LIT_KEY)]
            per = t[t.country != "Mean"]
            y = per["map"].map(lambda m: pos[LIT_KEY[m]]) + off
            mali = (per.country == "Mali").to_numpy()
            ax.scatter(per.value[~mali], y[~mali], s=24, color=SERIES[i], edgecolor=SURFACE, linewidth=0.8, zorder=3, label=label)
            ax.scatter(per.value[mali], y[mali], s=30, color=SERIES[i], edgecolor=INK, linewidth=1.2, zorder=4)
            for m, v in zip(t[t.country == "Mean"]["map"], t[t.country == "Mean"].value):
                yy = pos[LIT_KEY[m]] + off
                ax.plot([v, v], [yy - 0.14, yy + 0.14], color=INK, linewidth=1.8, zorder=5)
        if metric == "recall":                                  # left panel: this row holds the Esri note
            ax.text(0.5, pos["worldcereal_2021"], "WorldCereal: not scored in either paper", ha="center", va="center",
                    fontsize=7.5, color=MUTED)
        ax.set_xlim(-0.04, 1.04)
        ax.set_title(title, loc="left")
        _hgrid(ax)
    # product names only: the papers scored their own versions (e.g. Esri and Dynamic World of 2019-2020)
    axes[0].set_yticks(list(pos.values()), [_name(m).replace(" (course data)", "").rsplit(" ", 1)[0] for m in pos])
    y_esri = pos["esri_2025"] + 0.15
    axes[0].annotate("Esri in Mali: F1 0.00 with 0.97 accuracy\n(it calls no point crop)", xy=(0, y_esri),
                     xytext=(0.12, pos["worldcereal_2021"]), va="center", fontsize=7.5, color=INK2,
                     arrowprops=dict(arrowstyle="-", color=INK2, linewidth=0.8))
    handles, labels = axes[0].get_legend_handles_labels()
    handles += [Line2D([], [], color=INK, linewidth=1.8), Line2D([], [], marker="o", linestyle="", markerfacecolor="white",
                                                                  markeredgecolor=INK, markersize=5)]
    labels += ["mean over the paper's countries", "Mali (about 2% of points crop; most like Aweil)"]
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, fontsize=7.5, bbox_to_anchor=(0.55, -0.08))
    fig.tight_layout()
    return _save(fig, "09_published_accuracy_of_our_maps")


def recall_vs_share(tab):
    """Two panels: each map's mean recall in Kerner et al. against the crop share it shows in Aweil and in Bor South.

    tab: index = map, columns recall, aweil, bor_south (crop % of land).
    """
    from scipy.stats import spearmanr
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.2))
    for ax, col, title in zip(axes, ("aweil", "bor_south"), ("Aweil counties", "Bor South")):
        ax.scatter(tab.recall, tab[col], s=40, color=SERIES[0], edgecolor=SURFACE, linewidth=1.5, zorder=3)
        rho = spearmanr(tab.recall, tab[col]).correlation
        ax.set_title(f"{title}: rank correlation {rho:+.2f}", loc="left")
        nudge = {"glad_2019": 0.06, "asap_v04": -0.06} if col == "aweil" else {}   # these two points nearly touch
        for m, r in tab.iterrows():
            if col == "aweil" or r[col] > 1:
                ax.text(r.recall + 0.012, r[col] + nudge.get(m, 0), _name(m).split(" (")[0], fontsize=7.5, color=INK2,
                        va="center")
        if col == "bor_south":
            ax.text(0.62, tab[col].max() * 0.12, "the six other maps: 0.00-0.25%", fontsize=7.5, color=INK2)
        ax.set_xlabel("mean recall in Kerner et al. 2024 (8 countries)")
        ax.set_ylabel("crop, % of land in 2025 maps")
        ax.set_xlim(0.25, 0.95)
        ax.set_ylim(bottom=0)
        ax.grid(True, color=GRID_C, linewidth=0.6)
        ax.set_axisbelow(True)
    fig.tight_layout()
    return _save(fig, "10_published_recall_vs_crop_share")


def annotation_summary(labels, agreement, causes):
    """Three panels: how often each label was given, agreement per area and stratum, what splits are about.

    labels: Series label -> count (all judgements); agreement: rows with group, points, cropland_agree,
    cropland_pos_agree; causes: Series from eda_labels.disagreement_causes.
    """
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.4), gridspec_kw={"width_ratios": [0.8, 1.2, 1.1]})
    ax = axes[0]
    order = ["crop", "not crop", "fallow", "unsure"]
    v = labels.reindex(order).fillna(0)
    y = np.arange(len(v))[::-1]
    ax.barh(y, v.values, height=0.55, color=SERIES[0])
    for yi, vi in zip(y, v.values):
        ax.text(vi + v.max() * 0.02, yi, f"{vi:,.0f}", va="center", fontsize=8, color=INK2)
    ax.set_yticks(y, order)
    ax.set_xlim(0, v.max() * 1.25)
    ax.set_title(f"{int(v.sum())} labels, 2 per point", loc="left")
    ax.set_xlabel("labels")
    _hgrid(ax)

    ax = axes[1]
    a = agreement.reset_index(drop=True)
    y = np.arange(len(a))[::-1]
    ax.scatter(100 * a.cropland_agree, y, s=36, color=SERIES[0], edgecolor=SURFACE, linewidth=1.2, zorder=3,
               label="agree: cropland or not")
    ax.scatter(100 * a.cropland_pos_agree, y, s=36, color=SERIES[1], edgecolor=SURFACE, linewidth=1.2, zorder=3,
               label="when one says cropland, the other too")
    ax.set_yticks(y, [f"{g} ({n})" for g, n in zip(a.group, a.points)], fontsize=8)
    ax.set_xlim(0, 105)
    ax.set_xlabel("%")
    ax.set_title("Agreement between the two labellers", loc="left")
    ax.legend(frameon=False, fontsize=7.5, loc="lower left", bbox_to_anchor=(0, -0.42))
    _hgrid(ax)

    ax = axes[2]
    c = causes.drop("split points").rename(lambda k: k.replace("cue differs: ", "").replace("different cover class", "cover class"))
    c = c.sort_values()
    y = np.arange(len(c))
    ax.barh(y, c.values, height=0.55, color=SERIES[0])
    for yi, vi in zip(y, c.values):
        ax.text(vi + 0.6, yi, f"{vi}", va="center", fontsize=8, color=INK2)
    ax.set_yticks(y, c.index, fontsize=8)
    ax.set_xlim(0, causes["split points"] * 1.1)
    ax.set_xlabel(f"of the {causes['split points']} points where they split")
    ax.set_title("Which answers differ when they split", loc="left")
    _hgrid(ax)
    fig.tight_layout()
    return _save(fig, "11_annotation_statistics")


def stability(tab):
    """Lines: % of land Esri and Dynamic World call crop, every year, one panel per study area."""
    areas = list(dict.fromkeys(tab.area))
    fig, axes = plt.subplots(1, len(areas), figsize=(3.6 * len(areas), 3.0))
    for ax, a in zip(np.atleast_1d(axes), areas):
        for i, (p, label) in enumerate((("esri", "Esri"), ("dw", "Dynamic World"))):
            t = tab[(tab.area == a) & (tab["product"] == p) & tab.year.apply(lambda y: str(y).isdigit())]
            if not len(t):
                continue
            x, v = t.year.astype(int).to_numpy(), t.crop_pct.to_numpy()
            ax.plot(x, v, color=SERIES[i], linewidth=2, marker="o", markersize=4.5, markeredgecolor=SURFACE,
                    markeredgewidth=1.2, label=label)
            ax.text(x[-1] + 0.2, v[-1], label, fontsize=7.5, color=INK2, va="center")
        ax.set_title({"aweil": "Aweil counties", "bor_south": "Bor South"}.get(a, a), loc="left")
        ax.set_ylabel("crop, % of land")
        ax.set_ylim(bottom=0)
        ax.set_xlim(2015.5, 2027.2)
        ax.yaxis.grid(True, color=GRID_C, linewidth=0.8)
        ax.set_axisbelow(True)
    np.atleast_1d(axes)[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    return _save(fig, "06_same_map_every_year")
