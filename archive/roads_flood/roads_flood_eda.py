"""
Road access x flood exposure EDA (Logistics Cluster access-constraint maps, 2022-2026).

The corridor table in data/Infrastructure/ has town names but no coordinates, so this
module geocodes the waypoints, routes each corridor along OSM motorable roads, and counts
daily flood-mask detections near each corridor.

Stages
  R1  clean the weekly corridor-status table (tabular maps, 2022 onwards)
  R2  geocode corridor waypoints (OSM, OCHA, IOM DTM, GeoNames, admin points, health facilities)
  R3  corridor geometry: shortest path on OSM motorable roads, straight line as fallback
  R4  daily flood detections (unusual + recurring masks, 2022-2025) within 250/1000/2000 m
  R5  analysis panel: corridor x map date with status, flood exposure and county rainfall
  R6  numbers behind the figures (dynamics, seasonality, between vs within corridor, placebo, ZOA)

Run from repo root (global Python 3.13; the repo .venv lacks rasterio/scipy):
    py -3.13 -m archive.roads_flood.roads_flood_eda --through 6
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

from processing_data.paths import COURSE_RAW, EXT_DATA, ROOT

OUT = ROOT / "eda" / "outputs" / "roads_eda"
OUT.mkdir(parents=True, exist_ok=True)
INFRA = EXT_DATA / "Infrastructure"
GAZ = EXT_DATA / "Gazetteers_OSM"
DTM = EXT_DATA / "IOM_DTM_mobility"
ERA5_CM = ROOT / "eda" / "outputs" / "impact_eda" / "stage16_era5_county_month.csv"

STATUS_CODE = {"PASSABLE": 0, "PASSABLE_WITH_DIFFICULTIES": 1, "NOT_PASSABLE": 2}
ZOA_COUNTIES = {  # Q&A 2 slide 3: Lol river (NBeG) and Bor South
    "SS0501": "Aweil Centre", "SS0502": "Aweil East", "SS0503": "Aweil North",
    "SS0504": "Aweil South", "SS0505": "Aweil West", "SS0303": "Bor South",
}
FLOOD_YEARS = (2022, 2023, 2024, 2025)
TILES = ("h20v08", "h21v08")
CELLS_PER_DEG = 480  # flood-mask grid: cell centres at (k + 0.5) / 480 degrees
BANDS_M = (250, 1000, 2000)

# Spelling variants on the maps -> name found in a gazetteer (checked against corridor partners).
ALIASES = {
    "Yaui": "Yuai", "Wullu": "Wulu", "Dim Zubeir": "Deim Zubeir", "Duk Padiat": "Duk Padiet",
    "Abienhom": "Abiemnhom", "Kiech Kon": "Kiech Kuon", "Kiech kon": "Kiech Kuon", "Moto": "Motot",
    "Labarab": "Labrab", "Jemaam": "Jamam Town", "Maruwa": "Maruwa Hills", "Maper (Lakes": "Maper",
    "Maper (Lakes)": "Maper", "Vertet": "Verteth", "Verthet": "Verteth", "Amok Piny": "Amongpiny",
    "Kilo30": "Kilo 30", "Mingkman": "Mingkaman", "Rubkoona": "Rubkona", "Mankiem": "Mankien",
    "Nyaruop puop": "Nyaruop Puop", "Nyaruop port": "Nyaruop Puop", "Nyaruop Port": "Nyaruop Puop",
    "Thar Kueng": "Tharkueng", "Bunj/Maban": "Bunj", "Yith Pabol (SDN Border": "Yith Pabol",
    "Bentiu": "Bentiu", "BenƟu": "Bentiu",
}
# Places with two equally plausible gazetteer matches whose only map partner is each other.
MANUAL_PICK = {
    "Nyal": (7.723339, 30.246859, "OCHA 2022, Nyal payam, Panyijiar (county HQ)"),
    "Ganyiel": (7.404217, 30.4739, "IOM DTM R16, Ganyliel payam, Panyijar"),
}
JUNK = re.compile(r"^(\d|alternative road|to the border|wfp|iom|unmiss|unmas|lc$|mlo|sp$|sci$|[a-z]\d\d$)", re.I)

# Lower = preferred when several gazetteers agree on a place.
SRC_PRIORITY = {
    ("osm", "city"): 0, ("osm", "town"): 0, ("osm", "national_capital"): 0,
    ("ocha", None): 1, ("dtm", None): 2, ("geonames", "P"): 3,
    ("osm", "village"): 4, ("osm", "hamlet"): 4, ("osm", "locality"): 4, ("osm", "suburb"): 4,
    ("osm", None): 5, ("adminpt", None): 6, ("health", None): 7, ("geonames", None): 8,
}
ROAD_FACTOR = {  # routing penalty per OSM class (prefer the main network)
    "motorway": 1.0, "trunk": 1.0, "trunk_link": 1.0, "primary": 1.0, "primary_link": 1.0,
    "secondary": 1.1, "secondary_link": 1.1, "tertiary": 1.2, "tertiary_link": 1.2,
    "unclassified": 1.4, "track_grade1": 1.4, "track_grade2": 1.5, "track": 1.6,
    "track_grade3": 1.6, "track_grade4": 1.8, "track_grade5": 1.9, "residential": 1.5,
    "service": 1.7, "living_street": 1.7, "unknown": 1.8,
}
LAEA = "+proj=laea +lat_0=7.5 +lon_0=30 +datum=WGS84 +units=m"
TO_M = Transformer.from_crs("EPSG:4326", LAEA, always_xy=True)
TO_LL = Transformer.from_crs(LAEA, "EPSG:4326", always_xy=True)


def _norm(s: str) -> str:
    s = str(s).lower().strip()
    s = re.sub(r"[\-_/,.()']", " ", s)
    return re.sub(r"\s+", "", s)


def _clean_name(s):
    if s is None or s != s:
        return None
    s = str(s).replace("Ɵ", "ti")
    s = re.sub(r'"?alternative road"?', "", s, flags=re.I)
    s = re.sub(r"\).*$", "", s)  # '(Kaikang - Roriak )(Mayom' parse debris
    s = s.strip(' )("')
    return s or None


def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


# --------------------------------------------------------------------------- R1
def stage_r1() -> dict:
    df = pd.read_parquet(INFRA / "access_constraints_unified.parquet")
    df["map_date"] = pd.to_datetime(df["map_date"], errors="coerce")  # e.g. "2014-00-08"
    n_all, n_bad_date = len(df), int(df["map_date"].isna().sum())
    mod = df[(df["layout_era"] == "tabular_modern") & (df["map_year"] >= 2022)].copy()
    n_mod = len(mod)
    for col in ("origin", "destination"):
        mod[col] = mod[col].map(_clean_name)
    mod["via"] = mod["via_waypoints"].map(
        lambda v: [x for x in (_clean_name(p) for p in v.split(";")) if x] if isinstance(v, str) else []
    )
    bad = (
        mod["origin"].isna() | mod["destination"].isna()
        | mod["origin"].str.match(JUNK, na=True) | mod["destination"].str.match(JUNK, na=True)
        | ~mod["status"].isin(STATUS_CODE)
    )
    dropped = mod[bad]
    mod = mod[~bad].copy()
    raw_seq = [[ALIASES.get(n, n) for n in [o, *v, d]]
               for o, v, d in zip(mod["origin"], mod["via"], mod["destination"])]
    # one spelling per place ignoring case/spaces ("Ding ding" = "Ding Ding"): most frequent wins
    spell = pd.Series([n for s in raw_seq for n in s]).value_counts()
    canon = {}
    for n in spell.index:
        canon.setdefault(_norm(n), n)
    mod["seq"] = [tuple(canon[_norm(n)] for n in s) for s in raw_seq]
    mod["seq"] = mod["seq"].map(lambda s: s if s[0] <= s[-1] else tuple(reversed(s)))
    mod["corridor"] = mod["seq"].map(" - ".join)
    mod["status_code"] = mod["status"].map(STATUS_CODE)
    mod["cap_mt"] = mod["truck_capacity_mt"]

    per = (
        mod.groupby(["map_date", "corridor"], as_index=False)
        .agg(status_code=("status_code", "max"), n_rows=("status_code", "size"),
             n_status=("status_code", "nunique"), cap_mt=("cap_mt", "max"),
             seq=("seq", "first"), note=("condition_notes", "first"))
    )
    per.to_parquet(OUT / "r1_corridor_map_status.parquet")
    summary = {
        "rows_unified": n_all, "rows_invalid_map_date": n_bad_date, "rows_tabular_2022plus": n_mod, "rows_dropped_junk": int(bad.sum()),
        "dropped_examples": dropped["corridor_raw"].value_counts().head(8).to_dict(),
        "maps": int(per["map_date"].nunique()), "corridors": int(per["corridor"].nunique()),
        "corridor_map_cells": len(per),
        "duplicate_rows_within_map": int((per["n_rows"] > 1).sum()),
        "conflicting_status_within_map": int((per["n_status"] > 1).sum()),
        "first_map": str(per["map_date"].min().date()), "last_map": str(per["map_date"].max().date()),
    }
    return summary


# --------------------------------------------------------------------------- R2
def _gazetteer() -> pd.DataFrame:
    cache = OUT / "r2_gazetteer.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    parts = []
    osm = gpd.read_parquet(GAZ / "osm_named_points.parquet")
    pt = osm.geometry.representative_point()
    parts.append(pd.DataFrame({"src": "osm", "name": osm["name"], "type": osm["fclass"],
                               "lat": pt.y, "lon": pt.x}))
    g = pd.read_csv(GAZ / "geonames_SS.txt", sep="\t", header=None, low_memory=False,
                    names=["gid", "name", "ascii", "alt", "lat", "lon", "fcl", "fcode", "cc", "cc2",
                           "a1", "a2", "a3", "a4", "pop", "elev", "dem", "tz", "mod"])
    rows = []
    for r in g.itertuples():
        names = {r.name, r.ascii} | (set(r.alt.split(",")) if isinstance(r.alt, str) else set())
        rows += [("geonames", n, r.fcl, r.lat, r.lon) for n in names if isinstance(n, str) and n]
    parts.append(pd.DataFrame(rows, columns=["src", "name", "type", "lat", "lon"]))
    oc = gpd.read_file(GAZ / "ocha_populated_places_2022" / "ssd_pppls_ocha_20221216.shp")
    parts.append(pd.DataFrame({"src": "ocha", "name": oc["featureNam"], "type": None,
                               "lat": oc["POINT_Y"], "lon": oc["POINT_X"]}))
    for f, sheet in (("ssd-dtm-mobility-tracking-r16-baseline-assessment-dataset_updated_20250507.xlsx",
                      "MT R16 Baseline_Loc_Dataset"),
                     ("ssd-dtm-mobility-tracking-r12-baseline-locations-dataset.xlsx",
                      "R12_Baseline_Locations")):
        d = pd.read_excel(DTM / f, sheet_name=sheet, usecols=["village_idp_settlement_name", "latitude", "longitude"])
        parts.append(pd.DataFrame({"src": "dtm", "name": d["village_idp_settlement_name"], "type": None,
                                   "lat": pd.to_numeric(d["latitude"], errors="coerce"),
                                   "lon": pd.to_numeric(d["longitude"], errors="coerce")}))
    ap = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_adminpoints.geojson")
    parts.append(pd.DataFrame({"src": "adminpt", "name": ap["name"], "type": None,
                               "lat": ap["y_coord"], "lon": ap["x_coord"]}))
    hf = gpd.read_file(COURSE_RAW / "health facilities" / "Sub-Saharan_public_health_facilities.geojson")
    hf = hf[hf["Country"].str.contains("South Sudan", na=False)]
    parts.append(pd.DataFrame({"src": "health", "name": hf["Facility_n"], "type": None,
                               "lat": hf["Lat"], "lon": hf["Long"]}))
    gaz = pd.concat(parts, ignore_index=True).dropna(subset=["name", "lat", "lon"])
    gaz = gaz[gaz["lat"].between(3, 13) & gaz["lon"].between(23, 36)]
    gaz["key"] = gaz["name"].map(_norm)

    def prio(r):
        return SRC_PRIORITY.get((r.src, r.type), SRC_PRIORITY.get((r.src, None), 9))

    gaz["prio"] = [prio(r) for r in gaz.itertuples()]
    gaz.to_parquet(cache)
    return gaz


def stage_r2() -> dict:
    per = pd.read_parquet(OUT / "r1_corridor_map_status.parquet")
    seqs = per.drop_duplicates("corridor")["seq"].map(tuple)
    names = sorted({n for s in seqs for n in s})
    partners: dict[str, set] = {n: set() for n in names}
    for s in seqs:
        for a, b in zip(s[:-1], s[1:]):
            partners[a].add(b)
            partners[b].add(a)
    gaz = _gazetteer()
    by_key = {k: g for k, g in gaz.groupby("key")}

    cand: dict[str, pd.DataFrame] = {}
    for n in names:
        g = by_key.get(_norm(n))
        if g is None:
            continue
        g = g.assign(rlat=g["lat"].round(2), rlon=g["lon"].round(2)).sort_values("prio")
        cand[n] = g.drop_duplicates(["rlat", "rlon"])

    fixed: dict[str, dict] = {
        n: {"lat": la, "lon": lo, "src": "manual", "gaz_name": note, "n_cand": len(cand.get(n, [])),
            "spread_km": np.nan, "method": "manual"}
        for n, (la, lo, note) in MANUAL_PICK.items() if n in names
    }
    for n, g in cand.items():
        if n in fixed:
            continue
        best = g.iloc[0]
        spread = _haversine_km(best.lat, best.lon, g["lat"].values, g["lon"].values).max()
        if spread <= 15:
            fixed[n] = {"lat": best.lat, "lon": best.lon, "src": best.src, "gaz_name": best["name"],
                        "n_cand": len(g), "spread_km": round(float(spread), 1), "method": "unique"}
    n_rows = per.explode("seq")["seq"].value_counts()
    while True:
        for _ in range(4):  # ambiguous names: nearest to already-placed partners
            for n, g in cand.items():
                if n in fixed and fixed[n]["method"] in ("unique", "seed", "manual"):
                    continue
                pts = [fixed[p] for p in partners[n] if p in fixed]
                if not pts:
                    continue
                plat = np.array([p["lat"] for p in pts]); plon = np.array([p["lon"] for p in pts])
                score = [np.median(_haversine_km(r.lat, r.lon, plat, plon)) + 5 * r.prio for r in g.itertuples()]
                best = g.iloc[int(np.argmin(score))]
                spread = _haversine_km(best.lat, best.lon, g["lat"].values, g["lon"].values).max()
                fixed[n] = {"lat": best.lat, "lon": best.lon, "src": best.src, "gaz_name": best["name"],
                            "n_cand": len(g), "spread_km": round(float(spread), 1), "method": "partner"}
        left = [n for n in cand if n not in fixed]
        if not left:
            break
        # a cluster of mutually ambiguous names: seed the most-reported one with its best source
        n = max(left, key=lambda k: n_rows.get(k, 0))
        best = cand[n].iloc[0]
        fixed[n] = {"lat": best.lat, "lon": best.lon, "src": best.src, "gaz_name": best["name"],
                    "n_cand": len(cand[n]), "spread_km": np.nan, "method": "seed"}

    geo = pd.DataFrame([{"name": n, **fixed.get(n, {"method": "unresolved"})} for n in names])
    geo["alias_used"] = geo["name"].isin(set(ALIASES.values()) - set(ALIASES.keys()))
    part_d = []
    for r in geo.itertuples():
        ds = [
            _haversine_km(r.lat, r.lon, fixed[p]["lat"], fixed[p]["lon"])
            for p in partners[r.name] if p in fixed and r.name in fixed
        ]
        part_d.append(float(np.median(ds)) if ds else np.nan)
    geo["partner_median_km"] = part_d
    geo["confidence"] = np.where(
        geo["method"].isin(["seed", "manual"]) | (geo["partner_median_km"] > 160), "low",
        np.where(geo["method"] == "unresolved", "none", "high"))
    geo.to_csv(OUT / "r2_places_geocoded.csv", index=False)

    rows_by_name = per.explode("seq")["seq"].value_counts()
    unresolved = geo.loc[geo["method"] == "unresolved", "name"].tolist()
    ok_corr = per.drop_duplicates("corridor")
    ok_corr = ok_corr[ok_corr["seq"].map(lambda s: all(x in fixed for x in s))]
    return {
        "places": len(names), "resolved": int((geo["method"] != "unresolved").sum()),
        "unresolved": {n: int(rows_by_name.get(n, 0)) for n in unresolved},
        "methods": geo["method"].value_counts().to_dict(),
        "sources": geo["src"].value_counts().to_dict(),
        "corridors_fully_geocoded": len(ok_corr), "corridors_total": int(per["corridor"].nunique()),
        "corridor_map_cells_geocoded_share": round(
            float(per["corridor"].isin(set(ok_corr["corridor"])).mean()), 3),
        "partner_distance_km_p50_p95_max": [round(float(x), 1) for x in
                                            geo["partner_median_km"].quantile([0.5, 0.95, 1.0])],
    }


# --------------------------------------------------------------------------- R3
def _road_graph():
    roads = gpd.read_parquet(GAZ / "osm_roads_motorable.parquet").explode(index_parts=False)
    coords, idx = shapely.get_coordinates(roads.geometry.values, return_index=True)
    fac = roads["fclass"].map(ROAD_FACTOR).fillna(1.8).to_numpy()[idx]
    x, y = TO_M.transform(coords[:, 0], coords[:, 1])
    keys = np.round(coords[:, 0] * 1e6).astype(np.int64) * 10_000_000_000 + np.round(coords[:, 1] * 1e6).astype(np.int64)
    uniq, node = np.unique(keys, return_inverse=True)
    same = idx[:-1] == idx[1:]
    u, v = node[:-1][same], node[1:][same]
    seglen = np.hypot(x[1:] - x[:-1], y[1:] - y[:-1])[same]
    w = seglen * fac[:-1][same]
    e = pd.DataFrame({"u": np.minimum(u, v), "v": np.maximum(u, v), "w": w, "l": seglen})
    e = e[e["u"] != e["v"]].groupby(["u", "v"], as_index=False).min()
    n = len(uniq)
    nx_, ny_ = np.zeros(n), np.zeros(n)
    nx_[node], ny_[node] = x, y
    lon_, lat_ = np.zeros(n), np.zeros(n)
    lon_[node], lat_[node] = coords[:, 0], coords[:, 1]
    g = coo_matrix((e["w"].to_numpy(), (e["u"].to_numpy(), e["v"].to_numpy())), shape=(n, n)).tocsr()
    lmat = coo_matrix((e["l"].to_numpy(), (e["u"].to_numpy(), e["v"].to_numpy())), shape=(n, n)).tocsr()
    ncomp, lab = connected_components(g, directed=False)
    size = np.bincount(lab)
    big = np.where(size[lab] >= 2000)[0]
    tree = cKDTree(np.c_[nx_[big], ny_[big]])
    return g, lmat, nx_, ny_, lon_, lat_, big, tree


def _route(gr, a, b):
    g, lmat, nx_, ny_, lon_, lat_, big, tree = gr
    (ax, bx), (ay, by) = TO_M.transform([a[1], b[1]], [a[0], b[0]])
    straight = float(np.hypot(bx - ax, by - ay))
    line_ll = shapely.LineString([(a[1], a[0]), (b[1], b[0])])
    da, ia = tree.query([ax, ay]); db, ib = tree.query([bx, by])
    if max(da, db) > 10_000 or straight < 1_000:
        return line_ll, straight, straight, "straight_nosnap"
    s, t = big[ia], big[ib]
    dist, pred = dijkstra(g, directed=False, indices=s, return_predecessors=True,
                          limit=3.0 * 1.9 * straight + 40_000)
    if not np.isfinite(dist[t]):
        return line_ll, straight, straight, "straight_nopath"
    path = [t]
    while path[-1] != s:
        path.append(pred[path[-1]])
    path = path[::-1]
    plen = float(sum(lmat[min(p, q), max(p, q)] for p, q in zip(path[:-1], path[1:]))) + da + db
    ratio = plen / straight
    if ratio > 2.2:
        return line_ll, straight, plen, "straight_detour"
    pts = [(a[1], a[0])] + list(zip(lon_[path], lat_[path])) + [(b[1], b[0])]
    return shapely.LineString(pts), straight, plen, "osm"


def stage_r3() -> dict:
    per = pd.read_parquet(OUT / "r1_corridor_map_status.parquet")
    geo = pd.read_csv(OUT / "r2_places_geocoded.csv").set_index("name")
    geo = geo[geo["method"] != "unresolved"]
    corr = per.drop_duplicates("corridor")[["corridor", "seq"]]
    corr = corr[corr["seq"].map(lambda s: all(x in geo.index for x in s))]
    gr = _road_graph()
    recs = []
    for c, seq in zip(corr["corridor"], corr["seq"]):
        legs, s_len, p_len, meth = [], 0.0, 0.0, []
        for a, b in zip(seq[:-1], seq[1:]):
            la, lb = geo.loc[a], geo.loc[b]
            line, st, pl, m = _route(gr, (la.lat, la.lon), (lb.lat, lb.lon))
            legs.append(line); s_len += st; p_len += pl; meth.append(m)
        geom = shapely.line_merge(shapely.MultiLineString(legs)) if len(legs) > 1 else legs[0]
        recs.append({"corridor": c, "geo_conf": "low" if (geo.loc[list(seq), "confidence"] == "low").any() else "high",
                     "n_legs": len(legs), "straight_km": s_len / 1000,
                     "path_km": p_len / 1000, "method": "osm" if all(m == "osm" for m in meth)
                     else ("mixed" if "osm" in meth else meth[0]), "geometry": geom})
    gdf = gpd.GeoDataFrame(recs, crs="EPSG:4326")
    gdf["detour"] = gdf["path_km"] / gdf["straight_km"]
    a2 = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson").to_crs("EPSG:4326")
    # length-weighted county shares from points every ~1 km
    pts = []
    for c, geom in zip(gdf["corridor"], gdf.geometry):
        gm = shapely.transform(geom, lambda xy: np.c_[TO_M.transform(xy[:, 0], xy[:, 1])])
        dens = shapely.get_coordinates(shapely.segmentize(gm, 1000))
        lon, lat = TO_LL.transform(dens[:, 0], dens[:, 1])
        pts.append(pd.DataFrame({"corridor": c, "lon": lon, "lat": lat}))
    pts = pd.concat(pts)
    pts = gpd.sjoin(gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts.lon, pts.lat), crs="EPSG:4326"),
                    a2[["adm2_pcode", "adm2_name", "adm1_name", "geometry"]], predicate="within")
    w = pts.groupby(["corridor", "adm2_pcode"]).size().rename("n").reset_index()
    w["w"] = w["n"] / w.groupby("corridor")["n"].transform("sum")
    w.to_csv(OUT / "r3_corridor_county_weights.csv", index=False)
    main = (pts.groupby(["corridor", "adm1_name"]).size().rename("n").reset_index()
            .sort_values("n").drop_duplicates("corridor", keep="last").set_index("corridor")["adm1_name"])
    gdf["state"] = gdf["corridor"].map(main)
    zoa = w[w["adm2_pcode"].isin(ZOA_COUNTIES)].groupby("corridor")["w"].sum()
    gdf["zoa_share"] = gdf["corridor"].map(zoa).fillna(0.0)
    gdf["zoa_area"] = np.where(
        gdf["corridor"].isin(w.loc[w["adm2_pcode"].str.startswith("SS050"), "corridor"]), "Aweil (Lol)",
        np.where(gdf["corridor"].isin(w.loc[w["adm2_pcode"] == "SS0303", "corridor"]), "Bor South", ""))
    gdf.to_parquet(OUT / "r3_corridors.parquet")
    return {
        "corridors_routed": len(gdf), "methods": gdf["method"].value_counts().to_dict(),
        "detour_p50_p95": [round(float(x), 2) for x in gdf.loc[gdf["method"] == "osm", "detour"].quantile([0.5, 0.95])],
        "path_km_total": round(float(gdf["path_km"].sum())),
        "zoa_corridors": gdf.loc[gdf["zoa_area"] != "", ["corridor", "zoa_area"]].values.tolist(),
    }


# --------------------------------------------------------------------------- R4
def _corridor_cells(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    rmax = BANDS_M[-1]
    step = 111_320 / CELLS_PER_DEG
    rc = int(np.ceil((rmax + 300) / (step * 0.98)))
    di, dj = np.meshgrid(np.arange(-rc, rc + 1), np.arange(-rc, rc + 1), indexing="ij")
    keep = np.hypot(di * step, dj * step * 0.99) <= rmax + 300
    di, dj = di[keep], dj[keep]
    out = []
    for cid, geom in enumerate(gdf.geometry):
        gm = shapely.transform(geom, lambda xy: np.c_[TO_M.transform(xy[:, 0], xy[:, 1])])
        dens = shapely.get_coordinates(shapely.segmentize(gm, 100))
        lon, lat = TO_LL.transform(dens[:, 0], dens[:, 1])
        i0 = np.floor(np.asarray(lat) * CELLS_PER_DEG).astype(np.int64)
        j0 = np.floor(np.asarray(lon) * CELLS_PER_DEG).astype(np.int64)
        ij = np.unique(np.c_[(i0[:, None] + di).ravel(), (j0[:, None] + dj).ravel()], axis=0)
        cx, cy = TO_M.transform((ij[:, 1] + 0.5) / CELLS_PER_DEG, (ij[:, 0] + 0.5) / CELLS_PER_DEG)
        d = shapely.distance(gm, shapely.points(np.c_[cx, cy]))
        m = d <= rmax
        out.append(pd.DataFrame({"cid": cid, "key": ij[m, 0] * 100_000 + ij[m, 1], "dist": d[m].astype(np.float32)}))
    return pd.concat(out, ignore_index=True)


def stage_r4() -> dict:
    gdf = gpd.read_parquet(OUT / "r3_corridors.parquet")
    cells = _corridor_cells(gdf)
    cells["band"] = np.searchsorted(np.array(BANDS_M), cells["dist"].to_numpy(), side="left")
    ncell = cells.groupby(["cid", "band"]).size().unstack(fill_value=0).cumsum(axis=1)
    ncell.columns = [f"ncell_{b}" for b in BANDS_M]
    ncell.index = gdf["corridor"].to_numpy()[ncell.index]
    ncell.to_csv(OUT / "r4_corridor_ncells.csv")
    ukeys = np.unique(cells["key"].to_numpy())
    frames = []
    for kind in ("unusual", "recurring"):
        for year in FLOOD_YEARS:
            for tile in TILES:
                p = COURSE_RAW / "flood_masks" / f"compact_{kind}" / f"flood_events_{tile}_{year}.parquet"
                d = pd.read_parquet(p, columns=["date", "lat", "lon"])
                key = (np.floor(d["lat"].to_numpy(np.float64) * CELLS_PER_DEG).astype(np.int64) * 100_000
                       + np.floor(d["lon"].to_numpy(np.float64) * CELLS_PER_DEG).astype(np.int64))
                m = np.isin(key, ukeys)
                sub = pd.DataFrame({"date": pd.to_datetime(d["date"].astype(str).to_numpy()[m]), "key": key[m]})
                sub = sub.drop_duplicates()
                j = sub.merge(cells[["cid", "key", "band"]], on="key")
                c = j.groupby(["cid", "date", "band"]).size().rename("n").reset_index()
                c["kind"] = kind
                frames.append(c)
    fl = pd.concat(fr for fr in frames)
    fl = fl.groupby(["cid", "date", "kind", "band"], as_index=False)["n"].sum()
    wide = fl.pivot_table(index=["cid", "date", "kind"], columns="band", values="n", fill_value=0)
    wide = wide.reindex(columns=range(len(BANDS_M)), fill_value=0).cumsum(axis=1)
    wide.columns = [f"n_{b}" for b in BANDS_M]
    wide = wide.reset_index()
    wide["corridor"] = gdf["corridor"].to_numpy()[wide["cid"]]
    wide.drop(columns="cid").to_parquet(OUT / "r4_corridor_day_flood.parquet")
    return {"corridor_cells_2km": len(cells), "unique_cells": int(len(ukeys)),
            "corridor_day_rows": len(wide), "dates": int(wide["date"].nunique())}


# --------------------------------------------------------------------------- R5
def stage_r5() -> dict:
    per = pd.read_parquet(OUT / "r1_corridor_map_status.parquet")
    gdf = gpd.read_parquet(OUT / "r3_corridors.parquet")
    ncell = pd.read_csv(OUT / "r4_corridor_ncells.csv", index_col=0)
    fl = pd.read_parquet(OUT / "r4_corridor_day_flood.parquet")
    per = per[per["corridor"].isin(gdf["corridor"])].copy()
    # daily flooded share of corridor cells, all kinds together and by kind
    tot = fl.groupby(["corridor", "date"], as_index=False)[[f"n_{b}" for b in BANDS_M]].sum()
    tot["kind"] = "all"
    fl = pd.concat([fl, tot], ignore_index=True)
    for b in BANDS_M:
        fl[f"f_{b}"] = fl[f"n_{b}"] / fl["corridor"].map(ncell[f"ncell_{b}"])
    maps = per[["map_date"]].drop_duplicates()
    rows = []
    for kind in ("all", "unusual", "recurring"):
        k = fl[fl["kind"] == kind]
        for win in (10, 30):
            for b in (250, 1000, 2000):
                # max daily share over the window [t - win + 1, t]
                piv = k.pivot_table(index="date", columns="corridor", values=f"f_{b}", fill_value=0.0)
                full = pd.date_range("2022-01-01", "2025-12-31", freq="D")
                piv = piv.reindex(index=full, columns=gdf["corridor"], fill_value=0.0)  # no detection = 0
                piv = piv.rolling(win, min_periods=1).max()
                s = piv.reindex(maps["map_date"]).stack().rename(f"{kind}_f{b}_max{win}")
                rows.append(s)
    expo = pd.concat(rows, axis=1).reset_index()
    expo.columns = ["map_date", "corridor", *expo.columns[2:]]
    pan = per.merge(expo, on=["map_date", "corridor"], how="left")
    pan["in_mask_period"] = pan["map_date"] <= pd.Timestamp("2025-12-31")
    # county-weighted monthly rainfall (ERA5, m) for the map month and the month before
    w = pd.read_csv(OUT / "r3_corridor_county_weights.csv")
    era = pd.read_csv(ERA5_CM)
    era["ym"] = era["year"] * 12 + era["month"] - 1
    pan["ym"] = pan["map_date"].dt.year * 12 + pan["map_date"].dt.month - 1
    rain = w.merge(era, on="adm2_pcode")
    rain = (rain.assign(p=rain["precip_sum_m"] * rain["w"]).groupby(["corridor", "ym"])["p"].sum()
            .rename("rain_m").reset_index())
    pan = pan.merge(rain, on=["corridor", "ym"], how="left")
    prev = rain.assign(ym=rain["ym"] + 1).rename(columns={"rain_m": "rain_prev_m"})
    pan = pan.merge(prev, on=["corridor", "ym"], how="left")
    pan = pan.merge(gdf[["corridor", "state", "zoa_area", "zoa_share", "path_km", "method"]], on="corridor")
    pan["month"] = pan["map_date"].dt.month
    pan["np"] = (pan["status_code"] == 2).astype(int)
    pan.drop(columns=["seq"]).to_parquet(OUT / "r5_panel.parquet")
    ov = pan[pan["in_mask_period"]]
    return {"panel_rows": len(pan), "rows_with_flood_overlap": int(len(ov)),
            "maps_with_flood_overlap": int(ov["map_date"].nunique()),
            "corridors": int(pan["corridor"].nunique()),
            "np_share_overlap": round(float(ov["np"].mean()), 3)}


# --------------------------------------------------------------------------- R6
def _lpm(df: pd.DataFrame, formula: str, term: str) -> dict:
    import statsmodels.formula.api as smf

    m = smf.ols(formula, data=df).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df["corridor"])[0]})
    lo, hi = m.conf_int().loc[term]
    return {"b": float(m.params[term]), "lo": float(lo), "hi": float(hi), "p": float(m.pvalues[term]),
            "n": int(m.nobs), "corridors": int(df["corridor"].nunique())}


def stage_r6() -> dict:
    """Numbers behind the figures: dynamics, seasonality, between vs within, placebo, ZOA."""
    pan = pd.read_parquet(OUT / "r5_panel.parquet").sort_values(["corridor", "map_date"])
    gdf = gpd.read_parquet(OUT / "r3_corridors.parquet")[["corridor", "geo_conf"]]
    pan = pan.merge(gdf, on="corridor")
    pan["prev"] = pan.groupby("corridor")["status_code"].shift()
    pan["gap"] = (pan["map_date"] - pan.groupby("corridor")["map_date"].shift()).dt.days
    pan["changed"] = (pan["gap"] <= 21) & pan["prev"].notna() & (pan["prev"] != pan["status_code"])
    ch = pan[pan["changed"]].assign(direction=lambda d: np.where(d["status_code"] > d["prev"], "worse", "better"))
    ch[["map_date", "corridor", "state", "prev", "status_code", "direction", "all_f1000_max30"]].to_csv(
        OUT / "r6_status_changes.csv", index=False)
    stay = pan[(pan["gap"] <= 21) & pan["prev"].notna()]
    per_map = ch.groupby("map_date").size().sort_values(ascending=False)

    ov = pan[pan["in_mask_period"]].copy()
    ov["fl"] = (ov["all_f1000_max10"] > 0.01).astype(int)
    ov["ym"] = ov["map_date"].dt.to_period("M").astype(str)
    # placebo: the same corridor's flood exposure 364 days earlier
    fl = pd.read_parquet(OUT / "r4_corridor_day_flood.parquet")
    ncell = pd.read_csv(OUT / "r4_corridor_ncells.csv", index_col=0)
    t = fl.groupby(["corridor", "date"])["n_1000"].sum().reset_index()
    t["f"] = t["n_1000"] / t["corridor"].map(ncell["ncell_1000"])
    piv = (t.pivot_table(index="date", columns="corridor", values="f", fill_value=0.0)
           .reindex(index=pd.date_range("2022-01-01", "2025-12-31"), columns=ov["corridor"].unique(), fill_value=0.0)
           .rolling(10, min_periods=1).max())
    lagd = ov["map_date"] - pd.Timedelta(days=364)
    ok = lagd >= pd.Timestamp("2022-01-10")
    ov["fl_lag52"] = np.nan
    ov.loc[ok, "fl_lag52"] = [float(piv.at[d, c] > 0.01) for d, c in zip(lagd[ok], ov.loc[ok, "corridor"])]
    ov2 = ov.dropna(subset=["fl_lag52"])

    est = {
        "pooled": _lpm(ov, "np ~ fl", "fl"),
        "corridor_fe": _lpm(ov, "np ~ fl + C(corridor)", "fl"),
        "corridor_ym_fe": _lpm(ov, "np ~ fl + C(corridor) + C(ym)", "fl"),
        "placebo_lag52_corridor_ym_fe": _lpm(ov2, "np ~ fl_lag52 + C(corridor) + C(ym)", "fl_lag52"),
        "dry_dec_apr_corridor_ym_fe": _lpm(ov[ov["month"].isin([12, 1, 2, 3, 4])], "np ~ fl + C(corridor) + C(ym)", "fl"),
        "wet_jun_oct_corridor_ym_fe": _lpm(ov[ov["month"].isin([6, 7, 8, 9, 10])], "np ~ fl + C(corridor) + C(ym)", "fl"),
    }
    rob = []
    for lab, col, sub in (
        ("main: 1 km band, 10-day window", "all_f1000_max10", ov),
        ("on-road pixels (250 m)", "all_f250_max10", ov),
        ("2 km band", "all_f2000_max10", ov),
        ("30-day window", "all_f1000_max30", ov),
        ("unusual mask only", "unusual_f1000_max10", ov),
        ("OSM-routed corridors only", "all_f1000_max10", ov[ov["method"] == "osm"]),
        ("high-confidence geocodes only", "all_f1000_max10", ov[ov["geo_conf"] == "high"]),
    ):
        d = sub.assign(fl=(sub[col] > 0.01).astype(int))
        rob.append({"spec": lab, **{f"pooled_{k}": v for k, v in _lpm(d, "np ~ fl", "fl").items()},
                    **{f"within_{k}": v for k, v in _lpm(d, "np ~ fl + C(corridor) + C(ym)", "fl").items()}})
    pd.DataFrame(rob).to_csv(OUT / "r6_within_corridor_robustness.csv", index=False)

    cs = ov.groupby("corridor").agg(np=("np", "mean"), fl=("fl", "mean"), state=("state", "first"))
    cs["group"] = np.where(cs["fl"] == 0, "never", np.where(cs["fl"] < 0.10, "<10% of weeks", ">=10% of weeks"))
    groups = cs.groupby("group").agg(np=("np", "mean"), n=("np", "size"))
    groups.to_csv(OUT / "r6_corridor_flood_groups.csv")
    from scipy.stats import spearmanr

    rho = spearmanr(cs["np"], cs["fl"])
    # seasonality by month of year, on corridors present in >= 90% of maps of the window
    win = pan[(pan["map_date"] >= "2023-10-01")]
    pres = win.groupby("corridor").size() / win["map_date"].nunique()
    stable = pres[pres >= 0.9].index
    w = win[win["corridor"].isin(stable)].copy()
    w["year"] = w["map_date"].dt.year
    season = w.groupby(["year", "month"]).agg(np=("np", "mean"), fl=("all_f1000_max10", lambda s: (s > 0.01).mean()),
                                              n=("np", "size")).reset_index()
    # rain share of the calendar year, from one value per corridor-month (not one per weekly map)
    rm = w.drop_duplicates(["corridor", "year", "month"])[["corridor", "year", "month", "rain_m"]]
    rm["share"] = rm["rain_m"] / rm.groupby(["corridor", "year"])["rain_m"].transform("sum")
    season = season.merge(rm.groupby(["year", "month"])["share"].mean().rename("rain").reset_index(),
                          on=["year", "month"], how="left")
    season.loc[~season["year"].isin([2024, 2025]), ["fl", "rain"]] = np.nan  # complete years only
    season.to_csv(OUT / "r6_season_year_month.csv", index=False)
    chm = (ch[ch["map_date"].dt.year.isin([2024, 2025])].assign(month=lambda d: d["map_date"].dt.month)
           .groupby(["month", "direction"]).size().unstack(fill_value=0))
    chm.to_csv(OUT / "r6_changes_by_month_2024_2025.csv")
    ch.assign(month=ch["map_date"].dt.month).groupby(["month", "direction"]).size().unstack(fill_value=0).to_csv(
        OUT / "r6_changes_by_month.csv")
    zoa = (pan[pan["zoa_area"] != ""].groupby(["zoa_area", "corridor"])
           .agg(weeks=("np", "size"), not_passable=("np", "mean"),
                difficulties=("status_code", lambda s: float((s == 1).mean())),
                flood_weeks=("all_f1000_max10", lambda s: float((s > 0.01).mean())),
                changes=("changed", "sum")).reset_index())
    zoa.to_csv(OUT / "r6_zoa_corridors.csv", index=False)
    cm = ch[ch["map_date"] <= "2025-12-31"]
    return {
        "weekly_unchanged_share": round(float((stay["prev"] == stay["status_code"]).mean()), 3),
        "status_changes": len(ch), "changes_by_direction": ch["direction"].value_counts().to_dict(),
        "corridors_never_changing": int((pan.groupby("corridor")["changed"].sum() == 0).sum()),
        "maps_identical_to_previous": int((pan.groupby("map_date")["changed"].sum() == 0).sum()),
        "share_changes_on_top10_dates": round(float(per_map.head(10).sum() / per_map.sum()), 3),
        "top_change_dates": {str(k.date()): int(v) for k, v in per_map.head(5).items()},
        "worse_changes_preceded_by_flood_30d": round(float((cm.loc[cm["direction"] == "worse", "all_f1000_max30"] > 0.01).mean()), 3),
        "base_rate_flood_30d": round(float((ov["all_f1000_max30"] > 0.01).mean()), 3),
        "corridors_ever_flooded_1km": int((cs["fl"] > 0).sum()), "corridors_in_overlap": len(cs),
        "corridor_spearman_np_vs_flood_weeks": [round(float(rho[0]), 3), float(rho[1])],
        "estimates": {k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in est.items()},
        "stable_corridors_for_season": int(len(stable)),
    }


STAGES = {1: stage_r1, 2: stage_r2, 3: stage_r3, 4: stage_r4, 5: stage_r5, 6: stage_r6}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--through", type=int, default=6)
    ap.add_argument("--only", type=int)
    args = ap.parse_args()
    todo = [args.only] if args.only else [k for k in STAGES if k <= args.through]
    summ_path = OUT / "roads_eda_summary.json"
    summ = json.loads(summ_path.read_text()) if summ_path.exists() else {}
    for k in todo:
        print(f"== R{k}")
        res = STAGES[k]()
        summ[f"R{k}"] = res
        print(json.dumps(res, indent=1, default=str)[:3000])
        summ_path.write_text(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()
