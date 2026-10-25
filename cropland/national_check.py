"""
Random points over South Sudan outside the study areas, with our national map and the seven public maps at each.

These 20,000 uniform random points (equal-area, seed 42) feed `national_map.py compare`: without labels, how our map
relates to the public maps outside Aweil and Bor South (agreement, not accuracy). A labelled check sample drawn from
them was planned on 14 Oct and dropped the same day: the group does not label further.

    python cropland/national_check.py points cropland/rule1_2026-10-12.json      (Earth Engine, point reads only)

Writes cropland/national_check/candidates.csv: order, lon, lat, county, state, one column per public map (0/1 at the
point's 10 m pixel), ours (0/1 at its 30 m pixel), n_maps and stratum (M: ours marks it, P: only a public map, N: neither).
"""

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

import common as C

DIR = C.HERE / "national_check"
CANDIDATES = 20_000
CHUNK = 500


def domain():
    """South Sudan without the study areas' counties, one row per county, with the state."""
    adm = gpd.read_file(C.ADMIN2)
    ours = [c for cs in C.AREAS.values() for c in cs]
    state = [c for c in adm.columns if c.startswith("adm1_name")][0]
    d = adm[~adm[C.ADMIN2_NAME].isin(ours)][[C.ADMIN2_NAME, state, "geometry"]]
    return d.rename(columns={C.ADMIN2_NAME: "county", state: "state"})


def random_points(d, n, seed=C.SEED):
    """Uniform random points by area (drawn in an equal-area projection), in random order."""
    eq = d.to_crs(6933)
    shape = eq.union_all()
    shapely.prepare(shape)
    x0, y0, x1, y1 = eq.total_bounds
    rng, out = np.random.default_rng(seed), []
    while sum(len(o) for o in out) < n:
        x, y = rng.uniform(x0, x1, 4 * n), rng.uniform(y0, y1, 4 * n)
        inside = shapely.contains_xy(shape, x, y)
        out.append(np.c_[x[inside], y[inside]])
    xy = np.vstack(out)[:n]
    p = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xy[:, 0], xy[:, 1]), crs=6933).to_crs(4326)
    p = gpd.sjoin(p, d, predicate="within", how="left").drop(columns="index_right")
    return pd.DataFrame({"lon": p.geometry.x.round(6), "lat": p.geometry.y.round(6), "county": p.county, "state": p.state})


def read_strata(ee, pts, stem):
    """Our national map and the seven public maps at every point."""
    maps = C.public_maps(ee)
    img = ee.Image.cat([i for i, _ in maps.values()] + [ee.Image(f"{C.ASSETS}/{stem}_south_sudan").unmask(0).rename("ours")])

    def chunk(i):
        part = pts.iloc[i:i + CHUNK]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {"k": int(k)}) for k, r in part.iterrows()])
        return [f["properties"] for f in img.reduceRegions(fc, ee.Reducer.first(), scale=10, tileScale=4).getInfo()["features"]]

    with ThreadPoolExecutor(4) as pool:
        rows = [r for part in pool.map(chunk, range(0, len(pts), CHUNK)) for r in part]
    v = pd.DataFrame(rows).set_index("k").sort_index()
    out = pts.join(v)
    n_public = out[list(maps)].fillna(0).sum(axis=1)
    out["n_maps"] = n_public.astype(int)
    out["ours"] = out.ours.fillna(0).astype(int)
    out["stratum"] = np.where(out.ours == 1, "M", np.where(out.n_maps > 0, "P", "N"))
    return out


def points(rule_file: Path) -> None:
    DIR.mkdir(exist_ok=True)
    ee = C.ee_init()
    cand = read_strata(ee, random_points(domain(), CANDIDATES), rule_file.stem)
    cand.to_csv(DIR / "candidates.csv", index_label="order")
    print(cand.stratum.value_counts(normalize=True).round(4).to_string())


if __name__ == "__main__":
    if sys.argv[1:2] == ["points"] and len(sys.argv) == 3:
        points(Path(sys.argv[2]))
    else:
        raise SystemExit(__doc__)
