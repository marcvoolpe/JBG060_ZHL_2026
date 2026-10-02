"""
Figures for the road access x flood EDA (reads eda/outputs/roads_eda/, written by roads_flood_eda.py).

  figures/hidden/  exploratory diagnostics for the team (data quality, robustness, QA)
  figures/public/  explanatory figures for the team and stakeholders (one message each)

Run from repo root after `py -3.13 -m archive.roads_flood.roads_flood_eda --through 6`:
    py -3.13 -m archive.roads_flood.roads_flood_figures
"""

from __future__ import annotations

import json

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.patheffects as pe
import shapely

from processing_data.paths import COURSE_RAW, EXT_DATA, ROOT

OUT = ROOT / "eda" / "outputs" / "roads_eda"
HID = OUT / "figures" / "hidden"
PUB = OUT / "figures" / "public"
HID.mkdir(parents=True, exist_ok=True)
PUB.mkdir(parents=True, exist_ok=True)

# Reference palette (dataviz skill, light mode); validated with validate_palette.js.
SURF, INK, INK2, MUTED, GRID, BASE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
FLOOD, CLOSE, RAIN = "#2a78d6", "#eb6834", "#1baf7a"  # entity colours, fixed across figures
STATUS = {0: "#0ca30c", 1: "#fab219", 2: "#d03b3b"}  # reserved status colours, always labelled
STATUS_LAB = {0: "Passable", 1: "Passable with difficulties", 2: "Not passable"}
ORD = ["#ef8c62", "#d85a26", "#a8431c", "#6e2a0e"]  # ordinal orange ramp (validated --ordinal)
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9.5,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": BASE, "axes.linewidth": 0.8, "axes.labelcolor": INK2,
    "axes.titlesize": 11, "axes.titleweight": "semibold", "axes.titlecolor": INK, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "lines.linewidth": 2, "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
})


def _title(fig, title, sub=None, y=0.985):
    fig.text(0.015, y, title, fontsize=13.5, fontweight="semibold", color=INK, va="top")
    if sub:  # fixed 0.3 in below the title, whatever the figure height
        fig.text(0.015, y - 0.3 / fig.get_figheight(), sub, fontsize=9.5, color=INK2, va="top")


def _source(fig, text):
    fig.text(0.015, 0.008, text, fontsize=7.5, color=MUTED, va="bottom")


def _save(fig, path):
    fig.savefig(path, dpi=170)
    plt.close(fig)
    print("saved", path.relative_to(ROOT))


SRC_ROADS = "Source: Logistics Cluster access-constraint maps (WFP GIS), parsed; NASA/MODIS flood masks (course pack); ERA5; OSM."


def load():
    pan = pd.read_parquet(OUT / "r5_panel.parquet")
    gdf = gpd.read_parquet(OUT / "r3_corridors.parquet")
    summ = json.loads((OUT / "roads_eda_summary.json").read_text())
    return pan, gdf, summ


# =========================================================================== hidden
def h1_coverage():
    df = pd.read_parquet(EXT_DATA / "Infrastructure" / "access_constraints_unified.parquet")
    df["map_date"] = pd.to_datetime(df["map_date"], errors="coerce")
    m = df.drop_duplicates("map_filename").dropna(subset=["map_date"])
    m["ym"] = m["map_date"].dt.to_period("M").dt.to_timestamp()
    c = m.groupby(["ym", "layout_era"]).size().unstack(fill_value=0)
    idx = pd.date_range("2012-01-01", "2026-09-01", freq="MS")
    c = c.reindex(idx, fill_value=0)
    fig, ax = plt.subplots(figsize=(11, 3.8))
    fig.subplots_adjust(top=0.78, bottom=0.17, left=0.06, right=0.98)
    ax.axvspan(pd.Timestamp("2023-10-01"), pd.Timestamp("2025-12-31"), color=FLOOD, alpha=0.08, lw=0)
    ax.axvspan(pd.Timestamp("2022-06-01"), pd.Timestamp("2022-08-31"), color=FLOOD, alpha=0.08, lw=0)
    w = 22
    ax.bar(c.index, c.get("callout_historical", 0), width=w, color=MUTED, label="Callout maps (2012–2018, free text)")
    ax.bar(c.index, c.get("tabular_modern", 0), width=w, bottom=c.get("callout_historical", 0), color=CLOSE,
           label="Tabular maps (status per corridor)")
    ax.text(pd.Timestamp("2020-01-01"), 4.4, "no maps\n2019–2021", ha="center", color=INK2, fontsize=9)
    ax.text(pd.Timestamp("2024-11-15"), 5.6, "overlap with daily\nflood masks", ha="center", color=FLOOD, fontsize=8.5)
    ax.set_ylabel("maps per month")
    ax.set_ylim(0, 6.5)
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.legend(loc="upper left", ncol=2, fontsize=8.5)
    _title(fig, "H1 · Map coverage: two separate eras, and only ~26 months overlap the flood masks",
           "Unique map files per month (unified table, 273 maps with rows). 2017–18 tabular maps parse badly and are excluded from the panel.")
    _source(fig, SRC_ROADS)
    _save(fig, HID / "h1_map_coverage.png")


def h2_status_raster(pan, summ):
    p = pan.copy()
    order = (p.groupby("corridor").agg(state=("state", "first"), np=("np", "mean"))
             .sort_values(["state", "np"], ascending=[True, False]))
    piv = p.pivot_table(index="corridor", columns="map_date", values="status_code").reindex(order.index)
    weeks = pd.date_range(piv.columns.min() - pd.Timedelta(days=3), piv.columns.max() + pd.Timedelta(days=7), freq="7D")
    slot = np.searchsorted(weeks.values, piv.columns.values, side="right") - 1
    grid = np.full((len(piv), len(weeks) - 1), np.nan)
    grid[:, slot] = piv.values  # one map per weekly slot; weeks without a map stay empty
    cmap = ListedColormap([STATUS[0], STATUS[1], STATUS[2]])
    cmap.set_bad(SURF)
    fig, ax = plt.subplots(figsize=(11, 13))
    fig.subplots_adjust(top=0.93, bottom=0.08, left=0.2, right=0.98)
    x = mdates.date2num(weeks)
    ax.pcolormesh(x, np.arange(len(piv) + 1), np.ma.masked_invalid(grid),
                  cmap=cmap, vmin=-0.5, vmax=2.5, shading="flat")
    ax.invert_yaxis()
    st = order["state"].fillna("?").to_numpy()
    edges = np.r_[0, np.where(st[1:] != st[:-1])[0] + 1, len(st)]
    for a, b in zip(edges[:-1], edges[1:]):
        ax.axhline(a, color=SURF, lw=2)
        ax.text(x[0] - 12, (a + b) / 2, f"{st[a]} ({b - a})", ha="right", va="center", fontsize=8.5, color=INK2)
    top = pd.to_datetime(list(summ["R6"]["top_change_dates"].keys()))
    ax.plot(mdates.date2num(top) + 3.5, np.full(len(top), -1.8), "v", ms=6, color=INK, clip_on=False)
    ax.set_yticks([])
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.set_xlim(x[0], x[-1])
    ax.legend(handles=[Patch(color=STATUS[k], label=STATUS_LAB[k]) for k in STATUS] +
              [Line2D([], [], color=INK, marker="v", lw=0, label="5 largest batch-update dates")],
              loc="upper center", bbox_to_anchor=(0.4, -0.045), ncol=4, fontsize=8.5)
    _title(fig, "H2 · Every corridor, every map: status is sticky and changes arrive in batches",
           f"206 corridors (rows, grouped by state) × 138 weekly maps. {summ['R6']['weekly_unchanged_share']:.1%} of weekly statuses are unchanged; "
           f"{summ['R6']['corridors_never_changing']} corridors never change; 10 dates carry {summ['R6']['share_changes_on_top10_dates']:.0%} of all changes.",
           y=0.99)
    _source(fig, SRC_ROADS)
    _save(fig, HID / "h2_status_raster.png")


def h3_changes(summ):
    ch = pd.read_csv(OUT / "r6_status_changes.csv", parse_dates=["map_date"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.9), gridspec_kw={"width_ratios": [2.2, 1]})
    fig.subplots_adjust(top=0.76, bottom=0.16, left=0.06, right=0.98, wspace=0.18)
    d = ch.groupby(["map_date", "direction"]).size().unstack(fill_value=0)
    a1.bar(d.index, d.get("worse", 0), width=5, color=CLOSE, label="status worsened")
    a1.bar(d.index, -d.get("better", 0), width=5, color=FLOOD, label="status improved")
    a1.axhline(0, color=BASE, lw=0.8)
    a1.set_ylabel("corridors changing on this map")
    a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{abs(int(v))}"))
    a1.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    a1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    a1.yaxis.grid(True); a1.set_axisbelow(True)
    a1.legend(loc="upper left", fontsize=8.5)
    a1.set_title("By map date (2022 maps omitted)")
    a1.set_xlim(pd.Timestamp("2023-09-15"), pd.Timestamp("2026-10-01"))
    m = pd.read_csv(OUT / "r6_changes_by_month.csv", index_col=0).reindex(range(1, 13), fill_value=0)
    xs = np.arange(12)
    a2.bar(xs, m.get("worse", 0), width=0.6, color=CLOSE)
    a2.bar(xs, -m.get("better", 0), width=0.6, color=FLOOD)
    a2.axhline(0, color=BASE, lw=0.8)
    a2.set_xticks(xs, [s[0] for s in MONTHS])
    a2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{abs(int(v))}"))
    a2.yaxis.grid(True); a2.set_axisbelow(True)
    a2.set_title("By calendar month (Oct 2023–Sep 2026)")
    _title(fig, f"H3 · The {summ['R6']['status_changes']} status changes: worsening clusters in Apr–Aug, improvement in Jan–Apr",
           "Worsening above the axis, improvement below. Spikes on single dates look like batch reclassification, not week-by-week field reports.")
    _source(fig, SRC_ROADS)
    _save(fig, HID / "h3_status_changes.png")


def h4_pooled_bins(pan):
    ov = pan[pan["in_mask_period"]].copy()
    ov["bin"] = pd.cut(ov["all_f1000_max10"], [-1, 0, 0.01, 0.05, 0.2, 1.01],
                       labels=["none", "0–1%", "1–5%", "5–20%", ">20%"])
    b = ov.groupby("bin", observed=True).agg(np=("np", "mean"), n=("np", "size"))
    fig, ax = plt.subplots(figsize=(7.5, 4))
    fig.subplots_adjust(top=0.74, bottom=0.17, left=0.1, right=0.97)
    xs = np.arange(len(b))
    ax.bar(xs, b["np"] * 100, width=0.5, color=CLOSE)
    for x, (v, n) in zip(xs, b.values):
        ax.text(x, v * 100 + 2, f"{v:.0%}\nn={n:,}", ha="center", va="bottom", fontsize=8.5, color=INK2)
    ax.set_xticks(xs, b.index)
    ax.set_xlabel("share of the corridor's 1 km band with a flood detection in the previous 10 days")
    ax.set_ylabel("% of corridor-weeks not passable")
    ax.set_ylim(0, 110)
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    _title(fig, "H4 · Pooled view (misleading on its own): more flood nearby, more closures",
           "All corridor-weeks Oct 2023–Dec 2025 pooled. This mixes 'which road' with 'which week'; see H5.")
    _source(fig, SRC_ROADS)
    _save(fig, HID / "h4_pooled_flood_bins.png")


def h5_robustness(summ):
    r = pd.read_csv(OUT / "r6_within_corridor_robustness.csv")
    e = summ["R6"]["estimates"]
    extra = pd.DataFrame([
        {"spec": "placebo: same corridor, flood 52 weeks earlier", "within_b": e["placebo_lag52_corridor_ym_fe"]["b"],
         "within_lo": e["placebo_lag52_corridor_ym_fe"]["lo"], "within_hi": e["placebo_lag52_corridor_ym_fe"]["hi"]},
        {"spec": "dry season only (Dec–Apr)", "within_b": e["dry_dec_apr_corridor_ym_fe"]["b"],
         "within_lo": e["dry_dec_apr_corridor_ym_fe"]["lo"], "within_hi": e["dry_dec_apr_corridor_ym_fe"]["hi"]},
        {"spec": "wet season only (Jun–Oct)", "within_b": e["wet_jun_oct_corridor_ym_fe"]["b"],
         "within_lo": e["wet_jun_oct_corridor_ym_fe"]["lo"], "within_hi": e["wet_jun_oct_corridor_ym_fe"]["hi"]},
    ])
    r = pd.concat([r, extra], ignore_index=True)
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    fig.subplots_adjust(top=0.8, bottom=0.12, left=0.36, right=0.97)
    y = np.arange(len(r))[::-1]
    ax.axvline(0, color=BASE, lw=0.8)
    has_p = r["pooled_b"].notna()
    ax.hlines(y[has_p] + 0.17, r.loc[has_p, "pooled_lo"] * 100, r.loc[has_p, "pooled_hi"] * 100, color=MUTED, lw=2)
    ax.plot(r.loc[has_p, "pooled_b"] * 100, y[has_p] + 0.17, "o", ms=6, color=MUTED, mec=SURF, mew=1.5,
            label="across corridors (pooled)")
    ax.hlines(y - 0.17, r["within_lo"] * 100, r["within_hi"] * 100, color=CLOSE, lw=2)
    ax.plot(r["within_b"] * 100, y - 0.17, "o", ms=6, color=CLOSE, mec=SURF, mew=1.5,
            label="within the same corridor (corridor + month fixed effects)")
    ax.set_yticks(y, r["spec"])
    ax.set_xlabel("change in probability 'not passable' when flood is detected (percentage points, 95% CI, clustered by corridor)")
    ax.xaxis.grid(True); ax.set_axisbelow(True)
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=2, fontsize=8.5)
    _title(fig, "H5 · The pooled link vanishes inside each corridor, in every specification",
           "Linear probability models on corridor-weeks, Oct 2023–Dec 2025. Upper CI bound of the within-corridor effect never exceeds +10 points.")
    _source(fig, SRC_ROADS)
    _save(fig, HID / "h5_within_corridor_robustness.png")


def h6_routing(gdf, summ):
    geo = pd.read_csv(OUT / "r2_places_geocoded.csv")
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(11, 3.8))
    fig.subplots_adjust(top=0.74, bottom=0.18, left=0.1, right=0.98, wspace=0.55)
    m = geo["method"].replace({"unique": "one match", "partner": "nearest to\nneighbours", "seed": "seeded\n(low conf.)",
                               "manual": "manual\n(county)", "unresolved": "not found"}).value_counts()
    a1.barh(m.index[::-1], m.values[::-1], height=0.55, color=FLOOD)
    for i, v in enumerate(m.values[::-1]):
        a1.text(v + 1, i, str(v), va="center", fontsize=8.5, color=INK2)
    a1.set_title("Places: how each was geocoded")
    a1.set_xlabel("place names")
    d = gdf.loc[gdf["method"] == "osm", "detour"]
    a2.hist(d, bins=np.arange(1, 2.25, 0.05), color=FLOOD, rwidth=0.85)
    a2.axvline(d.median(), color=INK, lw=1)
    a2.text(d.median() + 0.03, a2.get_ylim()[1] * 0.9, f"median {d.median():.2f}", fontsize=8.5, color=INK)
    a2.set_title("OSM route length ÷ straight line")
    a2.set_xlabel("detour ratio (180 routed corridors)")
    mm = gdf["method"].replace({"osm": "OSM road", "mixed": "OSM + straight", "straight_nosnap": "straight: no road\nwithin 10 km",
                                "straight_detour": "straight: route\n>2.2× longer", "straight_nopath": "straight: road\nnot connected"}).value_counts()
    a3.barh(mm.index[::-1], mm.values[::-1], height=0.55, color=FLOOD)
    for i, v in enumerate(mm.values[::-1]):
        a3.text(v + 2, i, str(v), va="center", fontsize=8.5, color=INK2)
    a3.set_title("Corridor geometry")
    a3.set_xlabel("corridors")
    unres = summ["R2"]["unresolved"]
    _title(fig, "H6 · Geocoding and routing QA: 94% of corridor-weeks placed; 26 corridors are straight lines",
           "Not found: " + ", ".join(f"{k} ({v} rows)" for k, v in sorted(unres.items(), key=lambda kv: -kv[1])[:4]) + ", …")
    _source(fig, "Gazetteers: OSM (Geofabrik 2026-09-26), OCHA populated places 2022, IOM DTM R12/R16, GeoNames, admin points, health facilities.")
    _save(fig, HID / "h6_geocode_routing_qa.png")


def _strips(ax, pan, corridors, flood_ticks=True):
    x0 = pd.Timestamp("2023-10-01")
    for i, c in enumerate(corridors):
        s = pan[(pan["corridor"] == c) & (pan["map_date"] >= x0)].sort_values("map_date")
        for dte, st in zip(s["map_date"], s["status_code"]):
            ax.barh(i, 7, left=mdates.date2num(dte), height=0.62, color=STATUS[int(st)], lw=0)
        if flood_ticks:
            f = s[(s["all_f1000_max10"] > 0.01)]
            ax.plot(mdates.date2num(f["map_date"]) + 3.5, np.full(len(f), i - 0.45), "v", ms=5, color=FLOOD,
                    mec=SURF, mew=1)
    ax.set_yticks(range(len(corridors)), corridors)
    ax.invert_yaxis()
    ax.axvline(mdates.date2num(pd.Timestamp("2025-12-31")), color=INK2, lw=1)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.set_xlim(mdates.date2num(x0), mdates.date2num(pd.Timestamp("2026-09-30")))
    for yr in (2024, 2025, 2026):
        ax.axvspan(mdates.date2num(pd.Timestamp(f"{yr}-05-01")), mdates.date2num(pd.Timestamp(f"{yr}-10-31")),
                   color=RAIN, alpha=0.07, lw=0)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)


def h7_zoa(pan):
    z = pd.read_csv(OUT / "r6_zoa_corridors.csv")
    zb = z[z["zoa_area"] == "Bor South"].sort_values("weeks", ascending=False)["corridor"].tolist()
    za = z[z["zoa_area"] == "Aweil (Lol)"].sort_values("weeks", ascending=False)["corridor"].tolist()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 8.2), gridspec_kw={"height_ratios": [len(zb), len(za)]})
    fig.subplots_adjust(top=0.87, bottom=0.12, left=0.22, right=0.98, hspace=0.3)
    _strips(a1, pan, zb); a1.set_title("Bor South (12 corridors)")
    _strips(a2, pan, za); a2.set_title("Aweil counties / Lol river (7 corridors)")
    fig.legend(handles=[Patch(color=STATUS[k], label=STATUS_LAB[k]) for k in STATUS] +
               [Line2D([], [], color=FLOOD, marker="v", lw=0, ms=6, label="flood detected ≤1 km (10 days)"),
                Patch(color=RAIN, alpha=0.15, label="May–Oct rainy season")],
               loc="lower center", bbox_to_anchor=(0.5, 0.03), ncol=5, fontsize=8.5)
    _title(fig, "H7 · ZOA's areas: every corridor on the maps, with flood detections",
           "Vertical line: flood masks end (Dec 2025). Short rows are corridors that appear on few maps.")
    _source(fig, SRC_ROADS)
    _save(fig, HID / "h7_zoa_corridor_strips.png")


def h8_years():
    s = pd.read_csv(OUT / "r6_season_year_month.csv")
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.subplots_adjust(top=0.75, bottom=0.14, left=0.09, right=0.9)
    cols = {2024: FLOOD, 2025: CLOSE, 2026: RAIN}
    for yr, col in cols.items():
        d = s[s["year"] == yr].sort_values("month")
        ax.plot(d["month"], d["np"] * 100, color=col, marker="o", ms=4, mec=SURF, mew=1)
        last = d.iloc[-1]
        ax.text(last["month"] + 0.15, last["np"] * 100, str(yr), va="center", fontsize=9, color=INK)
    ax.set_xticks(range(1, 13), MONTHS)
    ax.set_ylabel("% of corridors not passable")
    ax.set_ylim(0, 70)
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.legend(handles=[Line2D([], [], color=c, label=str(y)) for y, c in cols.items()], loc="upper center", ncol=3, fontsize=8.5)
    _title(fig, "H8 · 2026 looks different: far fewer closures in the same months",
           "99 corridors present on ≥90% of maps since Oct 2023. Real improvement, a drier year, or a change in how maps are coded? Unknown.")
    _source(fig, SRC_ROADS)
    _save(fig, HID / "h8_year_comparison.png")


# =========================================================================== public
def _flood_density():
    cache = OUT / "fig_flood_density_005deg.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    parts = []
    for kind in ("unusual", "recurring"):
        for year in (2022, 2023, 2024, 2025):
            for tile in ("h20v08", "h21v08"):
                d = pd.read_parquet(COURSE_RAW / "flood_masks" / f"compact_{kind}" / f"flood_events_{tile}_{year}.parquet",
                                    columns=["date", "lat", "lon"])
                b = pd.DataFrame({"bi": np.floor(d["lat"].to_numpy() / 0.05).astype(np.int32),
                                  "bj": np.floor(d["lon"].to_numpy() / 0.05).astype(np.int32),
                                  "date": d["date"].astype(str).to_numpy()})
                parts.append(b.drop_duplicates())
    x = pd.concat(parts).drop_duplicates().groupby(["bi", "bj"]).size().rename("days").reset_index()
    x.to_parquet(cache)
    return x


def p1_map(pan, gdf):
    dens = _flood_density()
    a1 = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin1.geojson")
    a2 = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson")
    share = pan.groupby("corridor")["np"].mean()
    g = gdf.merge(share.rename("np_share"), left_on="corridor", right_index=True)
    fig, ax = plt.subplots(figsize=(10.5, 9.2))
    fig.subplots_adjust(top=0.88, bottom=0.08, left=0.02, right=0.98)
    a1.plot(ax=ax, color="#f3f2ee", edgecolor=BASE, lw=0.6)
    a0 = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin0.geojson").union_all()
    dd = dens[dens["days"] >= 20]
    dd = dd[shapely.contains_xy(a0, (dd["bj"] + 0.5) * 0.05, (dd["bi"] + 0.5) * 0.05)]
    bins = [20, 60, 150, 400, 900, 5000]
    for lo, hi, col in zip(bins[:-1], bins[1:], BLUES[1:]):
        s = dd[(dd["days"] >= lo) & (dd["days"] < hi)]
        ax.scatter((s["bj"] + 0.5) * 0.05, (s["bi"] + 0.5) * 0.05, s=2.2, marker="s", color=col, lw=0)
    zoa = a2[a2["adm2_pcode"].isin(["SS0501", "SS0502", "SS0503", "SS0504", "SS0505", "SS0303"])]
    zoa.dissolve(by=zoa["adm2_pcode"].str[:5]).boundary.plot(ax=ax, color=INK, lw=1.4)
    classes = [(0, 0.10, "<10% of weeks"), (0.10, 0.40, "10–40%"), (0.40, 0.70, "40–70%"), (0.70, 1.01, "≥70%")]
    for (lo, hi, _), col in zip(classes, ORD):
        s = g[(g["np_share"] >= lo) & (g["np_share"] < hi)]
        s.plot(ax=ax, color=SURF, lw=3.6)
        s.plot(ax=ax, color=col, lw=2)
    towns = {"Juba": (31.58, 4.85), "Wau": (27.99, 7.70), "Bor": (31.56, 6.21), "Bentiu": (29.79, 9.23),
             "Malakal": (31.66, 9.54), "Aweil": (27.40, 8.77), "Rumbek": (29.68, 6.81), "Kapoeta": (33.59, 4.77)}
    for t, (x, y) in towns.items():
        ax.plot(x, y, "o", ms=4, color=INK, mec=SURF, mew=1.2, zorder=5)
        ax.text(x + 0.12, y + 0.08, t, fontsize=8.5, color=INK, zorder=6,
                path_effects=[pe.withStroke(linewidth=2.5, foreground=SURF)])
    ax.text(26.2, 9.95, "Aweil counties\n(Lol river)", fontsize=9, color=INK, fontweight="semibold",
            path_effects=[pe.withStroke(linewidth=3, foreground=SURF)])
    ax.text(31.95, 5.85, "Bor South", fontsize=9, color=INK, fontweight="semibold",
            path_effects=[pe.withStroke(linewidth=3, foreground=SURF)])
    ax.set_axis_off()
    ax.set_xlim(23.4, 36.1); ax.set_ylim(3.4, 12.4)
    h1 = [Line2D([], [], color=c, lw=2.5, label=l) for (_, _, l), c in zip(classes, ORD)]
    h2 = [Patch(color=c, label=l) for c, l in zip(BLUES[1:], ["20–60", "60–150", "150–400", "400–900", "≥900"])]
    l1 = ax.legend(handles=h1, title="Road not passable", loc="lower left", bbox_to_anchor=(0.0, 0.02), fontsize=8.5,
                   title_fontsize=8.5, alignment="left")
    ax.add_artist(l1)
    ax.legend(handles=h2, title="Days with flood detected\n(5 km cells, 2022–2025)", loc="lower left",
              bbox_to_anchor=(0.2, 0.02), fontsize=8.5, title_fontsize=8.5, alignment="left")
    _title(fig, "Roads are cut off most in the east and north-east; ZOA's Aweil trunk roads rarely close",
           "Share of weekly Logistics Cluster maps (Jun 2022–Sep 2026) on which each corridor was not passable, over satellite flood detections.")
    _source(fig, SRC_ROADS + " 206 of 227 corridors mapped.")
    _save(fig, PUB / "p1_map_closure_share.png")


def p2_calendar():
    s = pd.read_csv(OUT / "r6_season_year_month.csv")
    s = s[s["year"].isin([2024, 2025])]
    ch = pd.read_csv(OUT / "r6_changes_by_month_2024_2025.csv", index_col=0).reindex(range(1, 13), fill_value=0)
    order = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2]
    xs = np.arange(12)
    agg = s.groupby("month").agg(np=("np", "mean"), np_lo=("np", "min"), np_hi=("np", "max"),
                                 fl=("fl", "mean"), rain=("rain", "mean")).reindex(order)
    fig, axs = plt.subplots(4, 1, figsize=(8.5, 9.4), sharex=True, gridspec_kw={"height_ratios": [1.2, 0.9, 1, 1]})
    fig.subplots_adjust(top=0.86, bottom=0.07, left=0.12, right=0.95, hspace=0.42)
    a = axs[0]
    a.fill_between(xs, agg["np_lo"] * 100, agg["np_hi"] * 100, color=CLOSE, alpha=0.12, lw=0)
    a.plot(xs, agg["np"] * 100, color=CLOSE)
    a.set_title("Roads not passable (% of corridors; band = 2024 vs 2025)")
    a.set_ylim(0, 65)
    b = axs[1]
    b.bar(xs, ch.loc[order, "worse"], width=0.5, color=CLOSE)
    b.bar(xs, -ch.loc[order, "better"], width=0.5, color=FLOOD)
    b.axhline(0, color=BASE, lw=0.8)
    b.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{abs(int(v))}"))
    b.set_title("Status changes: worsened (up) / improved (down)")
    ymax = max(ch["worse"].max(), ch["better"].max())
    b.set_ylim(-ymax * 1.3, ymax * 1.3)
    b.text(order.index(8) + 0.4, ch.loc[8, "worse"] + 1, "roads close", fontsize=8.5, color=INK2, va="bottom")
    b.text(order.index(4) + 0.4, -ymax * 0.7, "roads reopen", fontsize=8.5, color=INK2, va="center")
    c = axs[2]
    c.plot(xs, agg["fl"] * 100, color=FLOOD)
    c.set_title("Flood detected within 1 km of the road (% of corridor-weeks)")
    c.set_ylim(0, 15)
    d = axs[3]
    d.bar(xs, agg["rain"] * 100, width=0.5, color=RAIN)
    for x, v in zip(xs, agg["rain"] * 100):
        if v >= 10:
            d.text(x, v + 0.6, f"{v:.0f}%", ha="center", fontsize=8, color=INK2)
    d.set_ylim(0, 36)
    d.set_title("Rainfall (% of the year's total, ERA5, counties the roads cross)")
    for ax in axs:
        ax.yaxis.grid(True); ax.set_axisbelow(True)
        ax.axvspan(1.6, 7.4, color=RAIN, alpha=0.06, lw=0)
    d.set_xticks(xs, [MONTHS[m - 1] for m in order])
    _title(fig, "Roads close during the rains and stay shut well into the dry season",
           "Month-of-year profile, 2024 and 2025. Shading: May–Oct rains. Flood detections near roads peak in Dec–Jan,\nwhen roads are already closed.")
    _source(fig, "Logistics Cluster maps (parsed), MODIS flood masks, ERA5, OSM. 99 corridors present on ≥90% of maps.")
    _save(fig, PUB / "p2_calendar_close_rain_flood.png")


def p3_between_within(summ):
    gr = pd.read_csv(OUT / "r6_corridor_flood_groups.csv", index_col=0).reindex(["never", "<10% of weeks", ">=10% of weeks"])
    e = summ["R6"]["estimates"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1, 1.25]})
    fig.subplots_adjust(top=0.74, bottom=0.2, left=0.07, right=0.97, wspace=0.55)
    xs = np.arange(3)
    a1.bar(xs, gr["np"] * 100, width=0.5, color=CLOSE)
    for x, (v, n) in zip(xs, gr[["np", "n"]].values):
        a1.text(x, v * 100 + 2, f"{v:.0%}", ha="center", fontsize=10, color=INK, fontweight="semibold")
    a1.set_xticks(xs, [f"never\n({int(n)} roads)" if i == 0 else f"in {lab} of weeks\n({int(n)} roads)"
                       for i, (lab, n) in enumerate(zip(["", "<10%", "≥10%"], gr["n"]))])
    a1.set_ylim(0, 90)
    a1.set_ylabel("% of weeks not passable")
    a1.set_xlabel("flood detected near the corridor…")
    a1.set_title("Between roads: flood-prone roads close more")
    a1.yaxis.grid(True); a1.set_axisbelow(True)
    rows = [("Across all roads\n(pooled)", e["pooled"]),
            ("Same road, flooded vs\nnot-flooded weeks", e["corridor_ym_fe"]),
            ("Placebo: same road,\nlast year's flooding", e["placebo_lag52_corridor_ym_fe"])]
    y = np.arange(len(rows))[::-1]
    a2.axvline(0, color=BASE, lw=0.8)
    for yy, (lab, r) in zip(y, rows):
        col = MUTED if "Placebo" in lab else CLOSE
        a2.hlines(yy, r["lo"] * 100, r["hi"] * 100, color=col, lw=2)
        a2.plot(r["b"] * 100, yy, "o", ms=8, color=col, mec=SURF, mew=2)
        a2.text(r["hi"] * 100 + 2, yy, f"{r['b'] * 100:+.0f} pts", va="center", fontsize=9.5, color=INK)
    a2.set_yticks(y, [r[0] for r in rows])
    a2.set_xlim(-20, 70)
    a2.set_xlabel("extra chance of 'not passable' when flood is detected\n(percentage points, 95% CI)")
    a2.set_title("Within a road: no timing signal")
    a2.xaxis.grid(True); a2.set_axisbelow(True)
    _title(fig, "The flood masks tell you which roads are exposed, not when they will close",
           "Oct 2023–Dec 2025, 164 corridors. 'Same road' compares weeks of one corridor, controlling for the month (fixed effects).")
    _source(fig, SRC_ROADS)
    _save(fig, PUB / "p3_between_vs_within.png")


def p4_bor(pan):
    z = pd.read_csv(OUT / "r6_zoa_corridors.csv")
    zb = z[(z["zoa_area"] == "Bor South") & (z["weeks"] >= 100)].sort_values("not_passable", ascending=False)["corridor"].tolist()
    za = z[(z["zoa_area"] == "Aweil (Lol)") & (z["weeks"] >= 100)].sort_values("not_passable", ascending=False)["corridor"].tolist()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10.5, 6.4), gridspec_kw={"height_ratios": [len(zb), len(za)]})
    fig.subplots_adjust(top=0.83, bottom=0.17, left=0.2, right=0.98, hspace=0.45)
    _strips(a1, pan, zb); a1.set_title("Bor South")
    _strips(a2, pan, za); a2.set_title("Aweil (Lol river counties)")
    fig.legend(handles=[Patch(color=STATUS[k], label=STATUS_LAB[k]) for k in STATUS] +
               [Line2D([], [], color=FLOOD, marker="v", lw=0, ms=6, label="flood detected ≤1 km"),
                Patch(color=RAIN, alpha=0.15, label="May–Oct rains")],
               loc="lower center", bbox_to_anchor=(0.5, 0.035), ncol=5, fontsize=8.5)
    _title(fig, "In ZOA's areas, closures follow the season, and the flood masks miss them",
           "Weekly status of each corridor seen on ≥100 maps. Flood masks end Dec 2025 (vertical line).")
    _source(fig, SRC_ROADS)
    _save(fig, PUB / "p4_zoa_timelines.png")


def main():
    pan, gdf, summ = load()
    h1_coverage(); h2_status_raster(pan, summ); h3_changes(summ); h4_pooled_bins(pan)
    h5_robustness(summ); h6_routing(gdf, summ); h7_zoa(pan); h8_years()
    p1_map(pan, gdf); p2_calendar(); p3_between_within(summ); p4_bor(pan)


if __name__ == "__main__":
    main()
