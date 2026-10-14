"""
Step 10c - Where our results change the flood picture: a before / after map of flooded cropland.

For one study area and one flood year (default: Aweil, 2022, cells flooded 1+ day June-December)
every flooded NASA cell (232 m) gets each public map's crop share (EDA cache), the crop share of a
frozen model's map (cache from `10b_flood_history.py model ...`), and the labelled sample points
that lie on flooded land. A cell is "shown before" when the chosen public map has crop in it, and
"added by our map" when only our model has.

Our map works on the 210 m box: a pixel means "the box around it holds a cropped field". So the
map shows WHERE cropland lies under water; how MUCH comes from the labelled sample (10b, ratio
estimator), which the figure and the HTML quote next to the public map's number.

Outputs (area, year in the names):
  deliverables/cropland_report/figures/13_flood_map_<area>_<year>.png   before = the best public map
  deliverables/cropland_report/tables/flood_map_<area>_<year>.csv        per public map: cells shown, added, ...
  deliverables/cropland_report/maps/flood_<area>_<year>.html             interactive: pick the 'before' map
  cropland/results/flood_cells_<area>_<year>.csv                         one row per flooded cell (dashboard)

To use it on more land later: map the frozen model there (08_run_map.py), fill its per-cell cache
(10b ... model), make sure the EDA cache covers the area, then run this step for that area.

Run from group_repo: python cropland/10c_flood_map.py [area] [year] [model] [min_days]
                     (defaults: aweil 2022 rule1 1)
"""

import json
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import common as C
import eda_figures as FG
import eda_maps as EM

fl = __import__("importlib").import_module("10_flood")
REPORT = C.REPO / "deliverables" / "cropland_report"
LAYERS = EM.MAPS + EM.EXTRA + ["asap_v04"]
BEST = {"aweil": "worldcereal_2021", "bor_south": "gfsad_2015"}       # best-scoring public map on our test points
SHOWN, ADDED, NONE = FG.SERIES[0], FG.SERIES[1], "#d3d1c8"            # blue, orange, flooded land without crop
TITLES = {"aweil": "Aweil counties", "bor_south": "Bor South"}


def flooded_cells(area, year, model="rule1", min_days=1):
    """One row per flooded cell: position, area, county, flood days, every public layer and our model (0-1)."""
    cells = EM.zoa_cells(area)
    wet = EM.flood_cells(fl.TILES[area], year)
    t = cells.merge(wet[wet.days >= min_days][["gr", "gc", "days"]], on=["gr", "gc"])
    ours = pd.read_csv(C.OUT / f"flood_history_{model}_{area}.csv")
    t = t.merge(ours, on=["gr", "gc"], how="left").fillna({model: 0.0})
    counties = [c for c in t.columns if c.startswith("in_")]
    t["county"] = t[counties].idxmax(axis=1).str.removeprefix("in_").str.replace("_", " ")
    return t[["gr", "gc", "lat", "lon", "ha", "inside", "county", "days", *LAYERS, model]].reset_index(drop=True)


def per_map(t, model):
    """For every public layer as 'before': flooded cells it shows, cells only our map adds, and hectares."""
    rows = []
    for m in LAYERS:
        shown, ours = t[m] > 0, t[model] > 0
        rows.append({"before": m, "flooded_cells": len(t), "shown_before": int(shown.sum()),
                     "added_by_our_map": int((ours & ~shown).sum()), "shown_only_by_public_map": int((shown & ~ours).sum()),
                     "no_crop_in_either": int((~shown & ~ours).sum()),
                     "public_map_crop_ha": (t[m] * t.inside * t.ha).sum(),
                     "flooded_land_in_added_cells_ha": (t.inside * t.ha)[ours & ~shown].sum()})
    return pd.DataFrame(rows)


def sample_on_flood(area, t):
    """Labelled points whose cell is in the table, with the mean of the two labellers."""
    s = pd.read_csv(C.HERE / "sample.csv").merge(pd.read_csv(C.HERE / "labels_final.csv"), on="id")
    s = s[(s.area == area) & s.cropland_avg.notna()].copy()
    s["gr"], s["gc"] = EM.global_index(s.lat, s.lon)
    return s.merge(t[["gr", "gc"]], on=["gr", "gc"])[["id", "lat", "lon", "stratum", "cropland_avg", "share_avg"]]


def sample_estimate(area, year, min_days):
    h = pd.read_csv(C.HERE / "results" / "flood_history.csv")
    r = h[(h.area == area) & (h.year == year) & (h.min_days == min_days) & (h.layer == "sample (ratio)")
          & (h.measure == "share of box")]
    return None if r.empty or pd.isna(r.flooded_crop_ha.iloc[0]) else r.iloc[0]


def borders(area):
    admin = gpd.read_file(C.ADMIN2)
    return admin[admin[C.ADMIN2_NAME].isin(C.AREAS[area])][[C.ADMIN2_NAME, "geometry"]].rename(columns={C.ADMIN2_NAME: "name"})


def rivers(bounds):
    path = C.HERE / "lol_river_osm.geojson"
    if not path.exists():
        return None
    r = gpd.read_file(path).clip(bounds)
    return None if r.empty else r


def figure(t, pts, area, year, model, before, est, min_days):
    g0, c0 = t.gr.min(), t.gc.min()
    grid = np.full((t.gr.max() - g0 + 1, t.gc.max() - c0 + 1), np.nan)
    shown, ours = (t[before] > 0).to_numpy(), (t[model] > 0).to_numpy()
    west, east = t.lon.min() - EM.GRID / 2, t.lon.max() + EM.GRID / 2
    south, north = t.lat.min() - EM.GRID / 2, t.lat.max() + EM.GRID / 2
    b = borders(area)
    riv = rivers((west, south, east, north))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    name = FG._name(before)
    panels = ((f"Before: {name} shows crop in {shown.sum():,} of {len(t):,} flooded cells", np.where(shown, 1, 0)),
              (f"After: our map adds {(ours & ~shown).sum():,} flooded cells with crop", np.where(shown, 1, np.where(ours, 2, 0))))
    for ax, (title, code) in zip(axes, panels):
        grid[:] = np.nan
        grid[t.gr - g0, t.gc - c0] = code
        ax.imshow(grid, cmap=ListedColormap([NONE, SHOWN, ADDED]), vmin=0, vmax=2, interpolation="nearest",
                  extent=(west, east, south, north))
        b.boundary.plot(ax=ax, color=FG.MUTED, linewidth=0.6)
        if riv is not None:
            riv.plot(ax=ax, color=FG.INK2, linewidth=0.5, linestyle=(0, (2, 2)))
        for r in b.itertuples():
            p = r.geometry.representative_point()
            ax.text(p.x, p.y, r.name, fontsize=7, color=FG.INK2, ha="center", va="center")
        ax.set_xlim(west - 0.05, east + 0.05)            # frame the flooded land (Aweil Centre hardly floods)
        ax.set_ylim(south - 0.05, north + 0.05)
        ax.set_aspect(1 / np.cos(np.radians((south + north) / 2)))
        ax.set_axis_off()
        ax.set_title(title, loc="left", fontsize=9.5)
    crop = pts.cropland_avg > 0
    axes[1].scatter(pts.lon[crop], pts.lat[crop], s=30, color=FG.INK, edgecolor=FG.SURFACE, linewidth=1.2, zorder=3)
    axes[1].scatter(pts.lon[~crop], pts.lat[~crop], s=30, facecolor=FG.SURFACE, edgecolor=FG.INK, linewidth=1.2, zorder=3)
    under = f"{name}: {t[before].mul(t.inside * t.ha).sum():,.0f} ha of cropland under water"
    if est is not None:
        under += f"   |   our labelled sample: {est.flooded_crop_ha:,.0f} ha (95%: {est.low_ha:,.0f}-{est.high_ha:,.0f})"
    handles = [Patch(color=SHOWN, label=f"crop shown by {name}"), Patch(color=ADDED, label="crop added by our map (its 210 m box holds a field)"),
               Patch(color=NONE, label=f"flooded {min_days}+ day, no crop in either"),
               Line2D([], [], marker="o", linestyle="", color=FG.INK, markeredgecolor=FG.SURFACE, label="sample point: cropland"),
               Line2D([], [], marker="o", linestyle="", markerfacecolor=FG.SURFACE, color=FG.INK, label="sample point: no cropland")]
    if riv is not None:
        handles.append(Line2D([], [], color=FG.INK2, linewidth=0.8, linestyle=(0, (2, 2)), label="Lol river (OpenStreetMap)"))
    fig.legend(handles=handles, frameon=False, fontsize=7.5, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.02))
    fig.text(0.01, 0.995, f"Flooded cropland, {TITLES.get(area, area)} {year}. {under}",
             fontsize=8.5, color=FG.INK2, va="top")
    fig.tight_layout(rect=(0, 0.12, 1, 0.95))
    return FG._save(fig, f"13_flood_map_{area}_{year}")


HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Flooded cropland map</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<style>
:root { --surface:#fcfcfb; --panel:#ffffff; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781; --line:#e1e0d9;
        --shown:#2a78d6; --added:#eb6834; --none:#d3d1c8; --maponly:#9ec5f4; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --surface:#1a1a19; --panel:#232322; --ink:#f0efec;
        --ink2:#c3c2b7; --muted:#9a998f; --line:#3a3a37; --shown:#3987e5; --added:#d95926; --none:#55544f; --maponly:#256abf; } }
:root[data-theme="dark"] { --surface:#1a1a19; --panel:#232322; --ink:#f0efec; --ink2:#c3c2b7; --muted:#9a998f; --line:#3a3a37;
        --shown:#3987e5; --added:#d95926; --none:#55544f; --maponly:#256abf; }
html, body { margin:0; height:100%; background:var(--surface); color:var(--ink); font:14px/1.45 "Segoe UI", system-ui, sans-serif; }
#map { position:absolute; inset:0; }
#panel { position:absolute; z-index:1000; top:12px; right:12px; width:330px; max-width:calc(100% - 40px); max-height:calc(100% - 40px);
         overflow:auto; background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px 14px; box-shadow:0 2px 8px rgba(0,0,0,.15); }
#panel h1 { font-size:15px; margin:0 0 4px; }  #panel p { margin:6px 0; color:var(--ink2); font-size:13px; }
select { width:100%; font:inherit; padding:4px; margin:4px 0 8px; background:var(--panel); color:var(--ink); border:1px solid var(--line); border-radius:4px; }
.row { display:flex; align-items:center; gap:8px; margin:3px 0; font-size:13px; }
.sw { width:14px; height:14px; border-radius:3px; flex:none; }
.num { font-variant-numeric:tabular-nums; margin-left:auto; color:var(--ink); }
.big { font-size:13px; border-top:1px solid var(--line); padding-top:8px; margin-top:8px; }
label { font-size:13px; color:var(--ink2); }
.leaflet-tooltip { font:12px/1.4 "Segoe UI", system-ui, sans-serif; }
@media (max-width:600px) { #panel { top:auto; bottom:12px; right:12px; left:12px; width:auto; max-height:45%; } }
</style></head><body>
<div id="map"></div>
<div id="panel">
  <h1>Flooded cropland, __TITLE__</h1>
  <p>Every NASA flood cell (232 m) that was under water at least __DAYS__ day(s), June-December __YEAR__. Hover a cell or a point for details.</p>
  <label for="before">Before: the public map you would use today</label>
  <select id="before"></select>
  <div class="row"><span class="sw" style="background:var(--shown)"></span>crop shown by the map<span class="num" id="n-shown"></span></div>
  <div class="row"><span class="sw" style="background:var(--added)"></span>crop added by our map<span class="num" id="n-added"></span></div>
  <div class="row" id="r-maponly"><span class="sw" style="background:var(--maponly)"></span>of these, our map sees none<span class="num" id="n-maponly"></span></div>
  <div class="row"><span class="sw" style="background:var(--none)"></span>flooded, no crop in either<span class="num" id="n-none"></span></div>
  <label class="row"><input type="checkbox" id="split"> mark the cells only the public map shows</label>
  <label class="row"><input type="checkbox" id="pts" checked> labelled sample points on flooded land</label>
  <div class="big"><b>How much cropland was under water?</b>
    <div class="row">by the chosen map<span class="num" id="ha-map"></span></div>
    <div class="row">by our labelled sample<span class="num">__SAMPLE__</span></div></div>
  <p>Our map works on the 210 m box: an orange cell has at least one 10 m pixel whose box holds a cropped field. It shows
  <b>where</b> cropland lies under water; <b>how much</b> comes from the labelled sample. Cropland is today's (2025 labels,
  our 2025 map), so earlier years are a scenario. Public maps are as published (each of its own year).</p>
</div>
<script>
const D = __DATA__;
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const map = L.map("map", { preferCanvas: true, zoomControl: true });
const base = {
  "Satellite (Esri)": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    { maxZoom: 18, attribution: "Imagery Esri, Maxar, Earthstar Geographics" }),
  "OpenStreetMap": L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "OpenStreetMap contributors" }),
};
base["Satellite (Esri)"].addTo(map);
const renderer = L.canvas({ padding: 0.3 });
const h = D.cell / 2, pct = v => (v / 100).toFixed(v < 1000 ? 1 : 0) + "%";
const cells = D.cells.map(c => L.rectangle([[c[0] - h, c[1] - h], [c[0] + h, c[1] + h]],
  { renderer, weight: 1, opacity: 0.85, fillOpacity: 0.85 }).bindTooltip(() => tip(c), { sticky: true }));   // 1 px outline: visible when zoomed out
const cellLayer = L.layerGroup(cells).addTo(map);
function tip(c) {
  const sel = +document.getElementById("before").value;
  const rows = D.layers.map((n, i) => `${i === sel ? "<b>" : ""}${n}: ${pct(c[5 + i])}${i === sel ? "</b>" : ""}`).join("<br>");
  return `<b>${D.counties[c[2]]}</b>, flooded ${c[3]} day(s), ${c[4].toFixed(1)} ha<br>` +
         `crop share of the cell:<br>${rows}<br><b>our map: ${pct(c[5 + D.layers.length])}</b> of its pixels have a box with a field`;
}
const sel = document.getElementById("before");
D.layers.forEach((n, i) => sel.add(new Option(n, i, false, i === D.best)));
function paint() {
  const i = +sel.value, split = document.getElementById("split").checked, k = 5 + D.layers.length;
  const col = Object.fromEntries(["shown", "added", "maponly", "none"].map(x => [x, css("--" + x)]));
  const n = { shown: 0, added: 0, maponly: 0, none: 0 };
  let ha = 0;
  D.cells.forEach((c, j) => {
    const s = c[5 + i] > 0, o = c[k] > 0;
    if (s) n.shown++; else if (o) n.added++; else n.none++;
    if (s && !o) n.maponly++;
    ha += c[5 + i] / 1e4 * c[4] * c[k + 1];
    const fill = col[s ? (split && !o ? "maponly" : "shown") : o ? "added" : "none"];
    cells[j].setStyle({ fillColor: fill, color: fill });
  });
  for (const key in n) document.getElementById("n-" + key).textContent = n[key].toLocaleString();
  document.getElementById("r-maponly").style.opacity = split ? 1 : 0.55;
  document.getElementById("ha-map").textContent = Math.round(ha).toLocaleString() + " ha";
}
sel.onchange = paint; document.getElementById("split").onchange = paint;
const pts = L.layerGroup(D.points.map(p => L.circleMarker([p[0], p[1]], { radius: 6, weight: 2, color: css("--ink"),
  fillColor: p[3] > 0 ? css("--ink") : css("--panel"), fillOpacity: 1 })
  .bindTooltip(`sample point ${p[2]}<br>${p[3] > 0 ? "cropland in the box (" + Math.round(100 * p[4]) + "% of the box, mean of two labellers)" : "no cropland in the box"}`))).addTo(map);
document.getElementById("pts").onchange = e => e.target.checked ? pts.addTo(map) : pts.remove();
const counties = L.geoJSON(D.borders, { style: { color: "#ffffff", weight: 1.2, fill: false, opacity: 0.8 } }).addTo(map);
const overlays = { "flood cells": cellLayer, "county borders": counties };
if (D.rivers) overlays["Lol river (OSM)"] = L.geoJSON(D.rivers, { style: { color: "#9ec5f4", weight: 1.5, dashArray: "4 4" } }).addTo(map);
L.control.layers(base, overlays, { position: "topleft" }).addTo(map);
L.control.scale({ imperial: false }).addTo(map);
map.fitBounds(D.bounds, innerWidth > 600 ? { paddingBottomRight: [360, 0] } : {});   // keep the cells clear of the panel
paint();
</script></body></html>
"""


def html(t, pts, area, year, model, est, min_days):
    layers = LAYERS + ["any public map"]
    t = t.assign(**{"any public map": t[EM.MAPS + ["asap_v04"]].max(axis=1)})
    counties = sorted(t.county.unique())
    x = t[layers + [model]].to_numpy()
    shares = np.where(x > 0, np.maximum(1, np.rint(1e4 * x)), 0).astype(int).tolist()  # 1/10,000 of the cell; any crop stays > 0
    cells = [[round(la, 5), round(lo, 5), counties.index(cty), int(d), round(ha, 1), *sh, round(ins, 3)]
             for la, lo, cty, d, ha, sh, ins in zip(t.lat, t.lon, t.county, t.days, t.ha, shares, t.inside)]
    west, east, south, north = t.lon.min(), t.lon.max(), t.lat.min(), t.lat.max()
    riv = rivers((west, south, east, north))
    data = {"cell": EM.GRID, "layers": [FG._name(m) if m in LAYERS else m for m in layers], "best": layers.index(BEST.get(area, layers[0])),
            "counties": counties, "cells": cells, "bounds": [[south, west], [north, east]],
            "points": [[round(p.lat, 5), round(p.lon, 5), p.id, p.cropland_avg, 0 if pd.isna(p.share_avg) else p.share_avg] for p in pts.itertuples()],
            "borders": json.loads(borders(area).assign(geometry=lambda d: d.simplify(0.002)).to_json()),
            "rivers": json.loads(riv.to_json()) if riv is not None else None}
    title = f"{TITLES.get(area, area)}, {year}"
    sample = "too few points" if est is None else f"{est.flooded_crop_ha:,.0f} ha ({est.low_ha:,.0f}-{est.high_ha:,.0f})"
    page = (HTML.replace("__DATA__", json.dumps(data, separators=(",", ":"))).replace("__TITLE__", title)
            .replace("__YEAR__", str(year)).replace("__DAYS__", str(min_days)).replace("__SAMPLE__", sample))
    out = REPORT / "maps" / f"flood_{area}_{year}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def main() -> None:
    a = sys.argv[1:] + [None] * 4
    area, year, model, min_days = a[0] or "aweil", int(a[1] or 2022), a[2] or "rule1", int(a[3] or 1)
    t = flooded_cells(area, year, model, min_days)
    pts, est = sample_on_flood(area, t), sample_estimate(area, year, min_days)
    t.to_csv(C.HERE / "results" / f"flood_cells_{area}_{year}.csv", index=False)
    s = per_map(t, model)
    s.round(1).to_csv(REPORT / "tables" / f"flood_map_{area}_{year}.csv", index=False)
    print(s.round(0).to_string(index=False))
    print("figure:", figure(t, pts, area, year, model, BEST.get(area, LAYERS[0]), est, min_days))
    print("map:", html(t, pts, area, year, model, est, min_days))


if __name__ == "__main__":
    main()
