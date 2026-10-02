"""Map-to-map cropland agreement per county, for designing the stratified sample.

This compares the public maps with EACH OTHER. It is not an accuracy assessment:
maps can agree and all be wrong (they share inputs and training data).

All inputs are the derived 30 m layers on the same Sentinel-2-aligned UTM grid
(`derived/<aoi>/<key>_crop30m_<aoi>.tif`: 1 crop, 0 not crop, 255 no data, and
`<key>_cropfrac30m_<aoi>.tif`: % of 10 m pixels that are crop). A 30 m cell
belongs to a county when its centre lies inside the (unbuffered) county.

Method: each cell's state in every map in AGREEMENT_SET (0 not crop, 1 crop,
2 no data) is packed into one base-3 code, and codes are counted per county in
a single pass. All statistics below follow exactly from those counts.

Outputs (data/cropland/agreement/):
  county_crop_share.csv      per county x product: cropland share (%) and area (ha)
                             from the 10 m pixels (mean of cropfrac30m) and from
                             the 30 m majority layer
  pairwise_agreement.csv     per county x pair of maps (cells valid in both):
                             overall agreement, Cohen's kappa, crop overlap
                             (Jaccard), and the share of each map's crop cells that
                             the other also calls crop
  strata_n_maps.csv          per county: cells and ha per "number of maps saying
                             crop", for the 4 priority-A maps (0-4) and all 7 (0-7)
  n_maps7_crop_30m_<aoi>.tif the 0-7 layer (255 where any of the 7 has no data)

Usage (repo root, global Python 3.13), after derived_cropland_layers.py:
    python -m processing_data.cropland.cropland_agreement
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.windows import Window

from processing_data.cropland.common import AOIS, CROPLAND_DIR, counties, file_fields, today, upsert_manifest
from processing_data.cropland.derived_cropland_layers import NODATA, PRODUCTS, grid_profile

OUT = CROPLAND_DIR / "agreement"
# 2021-2022 maps (the reference season is 2022): the strata used for sampling
PRIMARY = ["worldcereal2021", "worldcover2021", "esri2022", "dw2022jjason"]
# plus the three older comparison maps
AGREEMENT_SET = PRIMARY + ["deafrica2019", "glad2019", "gfsad2015"]
CELL_HA = 30 * 30 / 1e4
STRIP = 1024


def county_ids(aoi: str, prof: dict):
    cty = counties(AOIS[aoi]["pcodes"]).to_crs(prof["crs"])
    ids = rasterize([(g, i + 1) for i, g in enumerate(cty.geometry)], out_shape=(prof["height"], prof["width"]),
                    transform=prof["transform"], fill=0, dtype="uint8")
    return cty, ids


def layer(aoi: str, key: str, kind: str = "crop30m"):
    return CROPLAND_DIR / "derived" / aoi / f"{key}_{kind}_{aoi}.tif"


def run(aoi: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prof = grid_profile(aoi, 30)
    cty, ids = county_ids(aoi, prof)
    n_cty = len(cty)
    all_keys = [p.key for p in PRODUCTS if layer(aoi, p.key).exists()]
    missing = [k for k in AGREEMENT_SET if k not in all_keys]
    if missing:
        raise FileNotFoundError(f"{aoi}: derived layers missing for {missing}; run derived_cropland_layers.py first")
    n_states = 3 ** len(AGREEMENT_SET)
    code_counts = np.zeros((n_cty + 1) * n_states, np.int64)
    # per product: valid cells, crop cells (30 m majority), sum of crop % (10 m pixels)
    share = {k: np.zeros((3, n_cty + 1), np.float64) for k in all_keys}
    srcs = {k: rasterio.open(layer(aoi, k)) for k in all_keys}
    fracs = {k: rasterio.open(layer(aoi, k, "cropfrac30m")) for k in all_keys}
    n7 = rasterio.open(OUT / f"n_maps7_crop_30m_{aoi}.tif", "w", **prof)
    try:
        for r0 in range(0, prof["height"], STRIP):
            h = min(STRIP, prof["height"] - r0)
            win = Window(0, r0, prof["width"], h)
            cid = ids[r0:r0 + h].astype(np.int64)
            code = np.zeros(cid.shape, np.int64)
            n7sum = np.zeros(cid.shape, np.uint8)
            n7ok = np.ones(cid.shape, bool)
            for i, k in enumerate(AGREEMENT_SET):
                a = srcs[k].read(1, window=win)
                state = np.where(a == NODATA, 2, a).astype(np.int64)
                code += state * 3 ** i
                n7sum += (a == 1).astype(np.uint8)
                n7ok &= a != NODATA
            code_counts += np.bincount((cid * n_states + code).ravel(), minlength=code_counts.size)
            n7.write(np.where(n7ok, n7sum, NODATA).astype(np.uint8), 1, window=win)
            for k in all_keys:
                a = srcs[k].read(1, window=win)
                f = fracs[k].read(1, window=win).astype(np.float64)
                v = a != NODATA
                share[k][0] += np.bincount(cid[v], minlength=n_cty + 1)
                share[k][1] += np.bincount(cid[v & (a == 1)], minlength=n_cty + 1)
                share[k][2] += np.bincount(cid[v], weights=f[v], minlength=n_cty + 1)
    finally:
        for s in (*srcs.values(), *fracs.values()):
            s.close()
        n7.close()

    counts = code_counts.reshape(n_cty + 1, n_states)[1:]            # drop "outside any county"
    digits = np.array([[(c // 3 ** i) % 3 for i in range(len(AGREEMENT_SET))] for c in range(n_states)])

    # county crop share
    rows = []
    for j, (pc, name) in enumerate(zip(cty["adm2_pcode"], cty["adm2_name"])):
        for k in all_keys:
            valid, crop30, fsum = share[k][:, j + 1]
            rows.append(dict(aoi=aoi, adm2_pcode=pc, adm2_name=name, product=k,
                             valid_cells=int(valid), valid_ha=round(valid * CELL_HA),
                             crop_share_pct_10m=round(fsum / valid, 3) if valid else np.nan,
                             crop_area_ha_10m=round(fsum / 100 * CELL_HA),
                             crop_share_pct_30m_majority=round(100 * crop30 / valid, 3) if valid else np.nan,
                             crop_area_ha_30m_majority=round(crop30 * CELL_HA)))
    shares = pd.DataFrame(rows)

    # pairwise agreement, on cells valid in both maps
    prow = []
    for j, (pc, name) in enumerate(zip(cty["adm2_pcode"], cty["adm2_name"])):
        c = counts[j]
        for (ia, ka), (ib, kb) in itertools.combinations(enumerate(AGREEMENT_SET), 2):
            da, db = digits[:, ia], digits[:, ib]
            n11 = c[(da == 1) & (db == 1)].sum()
            n10 = c[(da == 1) & (db == 0)].sum()
            n01 = c[(da == 0) & (db == 1)].sum()
            n00 = c[(da == 0) & (db == 0)].sum()
            n = n11 + n10 + n01 + n00
            if n == 0:
                continue
            po = (n11 + n00) / n
            pa, pb = (n11 + n10) / n, (n11 + n01) / n
            pe = pa * pb + (1 - pa) * (1 - pb)
            prow.append(dict(aoi=aoi, adm2_pcode=pc, adm2_name=name, map_a=ka, map_b=kb, cells_both_valid=int(n),
                             crop_share_a_pct=round(100 * pa, 3), crop_share_b_pct=round(100 * pb, 3),
                             overall_agreement_pct=round(100 * po, 2),
                             kappa=round((po - pe) / (1 - pe), 4) if pe < 1 else np.nan,
                             crop_jaccard_pct=round(100 * n11 / (n11 + n10 + n01), 2) if n11 + n10 + n01 else np.nan,
                             a_crop_also_b_pct=round(100 * n11 / (n11 + n10), 2) if n11 + n10 else np.nan,
                             b_crop_also_a_pct=round(100 * n11 / (n11 + n01), 2) if n11 + n01 else np.nan))
    pairs = pd.DataFrame(prow)

    # strata: number of maps saying crop, among cells valid in every map of the set
    srow = []
    prim_idx = [AGREEMENT_SET.index(k) for k in PRIMARY]
    for j, (pc, name) in enumerate(zip(cty["adm2_pcode"], cty["adm2_name"])):
        c = counts[j]
        for label, idx in (("4 primary maps", prim_idx), ("all 7 maps", list(range(len(AGREEMENT_SET))))):
            d = digits[:, idx]
            ok = (d != 2).all(axis=1)
            ncrop = (d == 1).sum(axis=1)
            tot = c[ok].sum()
            for m in range(len(idx) + 1):
                cells = c[ok & (ncrop == m)].sum()
                srow.append(dict(aoi=aoi, adm2_pcode=pc, adm2_name=name, map_set=label, n_maps_crop=m,
                                 cells=int(cells), area_ha=round(cells * CELL_HA),
                                 share_of_county_pct=round(100 * cells / tot, 4) if tot else np.nan))
            srow.append(dict(aoi=aoi, adm2_pcode=pc, adm2_name=name, map_set=label, n_maps_crop="no data in >= 1 map",
                             cells=int(c[~ok].sum()), area_ha=round(c[~ok].sum() * CELL_HA), share_of_county_pct=np.nan))
    strata = pd.DataFrame(srow)
    return shares, pairs, strata


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--aoi", nargs="+", default=list(AOIS), choices=list(AOIS))
    aois = ap.parse_args().aoi
    OUT.mkdir(parents=True, exist_ok=True)
    res = [run(a) for a in aois]
    outputs = {"county_crop_share.csv": pd.concat([r[0] for r in res]),
               "pairwise_agreement.csv": pd.concat([r[1] for r in res]),
               "strata_n_maps.csv": pd.concat([r[2] for r in res])}
    for name, df in outputs.items():
        path = OUT / name
        df.to_csv(path, index=False)
        row = dict(product="derived: map-to-map cropland agreement", version="derived", year="2015-2022",
                   aoi="aweil; borsouth", source="processing_data/cropland/cropland_agreement.py", access_date=today(),
                   licence="as source products", band=name,
                   class_codes="agreement between maps, NOT accuracy; maps: " + ", ".join(AGREEMENT_SET),
                   status="obtained", notes="30 m cells, cell centre in county.")
        row.update(file_fields(path))
        upsert_manifest(row)
        print(f"wrote {path}")
    for aoi in aois:
        path = OUT / f"n_maps7_crop_30m_{aoi}.tif"
        row = dict(product="derived: number of maps saying crop (7 maps)", version="derived", year="2015-2022", aoi=aoi,
                   source="processing_data/cropland/cropland_agreement.py", access_date=today(),
                   licence="as source products", band="count 0-7",
                   class_codes="0-7 maps saying crop among " + ", ".join(AGREEMENT_SET) + "; 255 = no data in any of them",
                   status="obtained", notes="Stratification aid; not accuracy.")
        row.update(file_fields(path))
        upsert_manifest(row)


if __name__ == "__main__":
    main()
