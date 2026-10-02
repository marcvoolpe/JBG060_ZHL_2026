"""
Exploratory checks behind the independent RO search (archive/external_reviews/superior_ro_search_report.md).

Five checks, none of which joins flood severity to displacement (the Session E association stays blinded):

1. ASAP cropland area per county vs CFSAM harvested cereal area, 2021-2024.
2. Current flooded-cropland estimate: pixels flagged by the course masks in June-November x ASAP crop share.
3. OCHA 2025 "displaced" vs IOM DTM Event Tracking 2025 flood totals by origin county (outcome side only).
4. Post-2020 jump in June-December detections, by state (severity side only).
5. June-December detections in ZOA's counties (Aweil counties and Bor South), all seasons.

Needs rasterio (not in requirements.txt). Reads Stage 32/33 caches, so run `python -m archive.impact_eda.impact_session_e --through 33` first.

Run from repo root:
    python -m archive.ro_search.ro_search_checks
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from processing_data.paths import COURSE_RAW, EXT_DATA, ensure_impact_eda_out

OUT = ensure_impact_eda_out()
ADMIN2 = COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson"
ASAP_CROP = COURSE_RAW / "farmland" / "asap_mask_crop_v04.tif"
MASKS = COURSE_RAW / "flood_masks"
CFSAM = EXT_DATA / "FEWS_crop_data" / "crop_data.csv"
OCHA_2025 = EXT_DATA / "OCHA_flood_data" / "ss_people_affected_and_displaced_by_floods_20251130.xlsx"
ZOA = {"SS0303": "Bor South", "SS0501": "Aweil Centre", "SS0502": "Aweil East",
       "SS0503": "Aweil North", "SS0504": "Aweil South", "SS0505": "Aweil West"}
MASK_RES_DEG = 1 / 480  # ~232 m grid of the course masks


def _cell_km2(lat: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """Area of a lat/lon cell in km2 (spherical approximation)."""
    return (dx * 111.32 * np.cos(np.radians(lat))) * (dy * 110.57)


def asap_vs_cfsam() -> pd.DataFrame:
    """Check 1: cropland area implied by ASAP (sum of crop share x cell area) against CFSAM harvested area."""
    adm = gpd.read_file(ADMIN2)
    rows = []
    with rasterio.open(ASAP_CROP) as src:
        adm = adm.to_crs(src.crs)
        for _, r in adm.iterrows():
            arr, tr = mask(src, [r.geometry], crop=True, filled=False)
            share = np.ma.filled(arr[0].astype("float64"), 0.0) / 100.0
            lats = tr.f + tr.e * (np.arange(share.shape[0]) + 0.5)
            km2 = _cell_km2(lats, abs(tr.a), abs(tr.e))[:, None]
            rows.append({"adm2_pcode": r.adm2_pcode, "adm2_name": r.adm2_name,
                         "asap_crop_ha": float((share * km2).sum() * 100)})
    asap = pd.DataFrame(rows)
    crop = pd.read_csv(CFSAM, low_memory=False)
    crop["year"] = pd.to_datetime(crop["period_date"]).dt.year
    area = crop[(crop["indicator"] == "Area Harvested") & crop["year"].between(2021, 2024)]
    cfsam = area.groupby("admin_2")["value"].mean().rename("cfsam_harvested_ha_2021_24").reset_index()
    out = asap.assign(key=asap["adm2_name"].str.lower().str.strip()).merge(
        cfsam.assign(key=cfsam["admin_2"].str.lower().str.strip()), on="key", how="left")
    out["ratio_asap_to_cfsam"] = out["asap_crop_ha"] / out["cfsam_harvested_ha_2021_24"]
    out = out.drop(columns=["key", "admin_2"])
    matched = out["ratio_asap_to_cfsam"].notna()
    print(f"[1] ASAP national crop area {out['asap_crop_ha'].sum():,.0f} ha; "
          f"CFSAM harvested area by year {area.groupby('year')['value'].sum().round().to_dict()}")
    print(f"    ASAP < CFSAM in {(out.loc[matched, 'ratio_asap_to_cfsam'] < 1).sum()} of {matched.sum()} counties; "
          f"median ratio {out.loc[matched, 'ratio_asap_to_cfsam'].median():.3f} (unmatched: "
          f"{out.loc[~matched, 'adm2_name'].tolist()})")
    return out


def flooded_cropland_baseline(years=range(2021, 2026)) -> pd.DataFrame:
    """Check 2: pixels flagged at least once in June-November (either class) x ASAP crop share, by county."""
    adm = gpd.read_file(ADMIN2)[["adm2_pcode", "adm2_name", "adm1_name", "geometry"]]
    frames = []
    with rasterio.open(ASAP_CROP) as src:
        for year in years:
            parts = []
            for cls in ("compact_unusual", "compact_recurring"):
                for tile in ("h20v08", "h21v08"):
                    d = pd.read_parquet(MASKS / cls / f"flood_events_{tile}_{year}.parquet", columns=["date", "lat", "lon"])
                    month = pd.to_datetime(d["date"].astype(str)).dt.month
                    parts.append(d.loc[month.between(6, 11), ["lat", "lon"]].drop_duplicates())
            px = pd.concat(parts).drop_duplicates()
            share = np.array([v[0] for v in src.sample(zip(px["lon"], px["lat"]))], dtype=float) / 100.0
            km2 = _cell_km2(px["lat"].to_numpy(), MASK_RES_DEG, MASK_RES_DEG)
            pts = gpd.GeoDataFrame({"flooded_ha": km2 * 100, "flooded_crop_ha": share * km2 * 100},
                                   geometry=gpd.points_from_xy(px["lon"], px["lat"]), crs="EPSG:4326")
            joined = gpd.sjoin(pts, adm, predicate="within", how="inner")
            agg = joined.groupby(["adm2_pcode", "adm2_name", "adm1_name"])[["flooded_ha", "flooded_crop_ha"]].sum()
            frames.append(agg.reset_index().assign(year=year))
            print(f"[2] {year}: flooded cropland (masks x ASAP, Jun-Nov, <= 10N) {agg['flooded_crop_ha'].sum():,.0f} ha")
    return pd.concat(frames, ignore_index=True)


def ocha_vs_et_2025() -> pd.DataFrame:
    """Check 3: exact equality of OCHA 2025 displaced figures with ET June-December 2025 flood totals (outcome side only)."""
    et = pd.read_csv(OUT / "stage32_et_origin_season.csv")
    et = et[(et["window"] == "JD") & (et["season"] == 2025)][["adm2_pcode", "flood_ind"]]
    ocha = pd.read_excel(OCHA_2025)
    ocha.columns = ["adm1_name", "adm1_pcode", "adm2_name", "adm2_pcode", "affected", "displaced"]
    out = ocha.dropna(subset=["adm2_pcode"]).merge(et, on="adm2_pcode", how="left")
    nonzero = out[out["displaced"].fillna(0) > 0]
    exact = nonzero[nonzero["displaced"] == nonzero["flood_ind"]]
    print(f"[3] OCHA 2025 non-zero displaced counties: {len(nonzero)}; exactly equal to ET flood total: "
          f"{len(exact)} {exact['adm2_name'].tolist()}")
    return out


def detection_jump_by_state() -> pd.DataFrame:
    """Check 4: mean June-December detections (km2 x dekads, combined classes, F71) per season, by period and state."""
    sev = pd.read_csv(OUT / "stage33_severity_season.csv")
    sev = sev[(sev["window"] == "JD") & (sev["class_set"] == "combined") & sev["in_f71"]]
    states = gpd.read_file(ADMIN2)[["adm2_pcode", "adm1_name"]]
    sev = sev.merge(states, on="adm2_pcode")
    sev["period"] = np.where(sev["season"] <= 2019, "2001_2019", np.where(sev["season"] == 2020, "2020", "2021_2025"))
    n_seasons = sev.groupby("period")["season"].nunique()
    out = sev.groupby(["adm1_name", "period"])["exd"].sum().unstack() / n_seasons
    out["ratio_2021_25_vs_2001_19"] = out["2021_2025"] / out["2001_2019"]
    print("[4] ratio of mean seasonal detections, 2021-25 vs 2001-19, by state:")
    print(out["ratio_2021_25_vs_2001_19"].round(1).sort_values(ascending=False).to_string())
    return out.reset_index()


def zoa_detections() -> pd.DataFrame:
    """Check 5: June-December detections (km2 x dekads) for ZOA's counties, both class sets, all seasons."""
    sev = pd.read_csv(OUT / "stage33_severity_season.csv")
    sev = sev[(sev["window"] == "JD") & sev["adm2_pcode"].isin(ZOA)]
    out = sev.pivot_table(index=["class_set", "adm2_pcode"], columns="season", values="exd").round(1)
    print("[5] ZOA counties, 2021-2025 (combined):")
    print(out.loc["combined"].rename(index=ZOA).loc[:, 2021:2025].to_string())
    return out.reset_index()


def main() -> None:
    asap_vs_cfsam().to_csv(OUT / "ro_search_asap_vs_cfsam.csv", index=False)
    flooded_cropland_baseline().to_csv(OUT / "ro_search_flooded_cropland_baseline.csv", index=False)
    ocha_vs_et_2025().to_csv(OUT / "ro_search_ocha_vs_et_2025.csv", index=False)
    detection_jump_by_state().to_csv(OUT / "ro_search_detection_jump_by_state.csv", index=False)
    zoa_detections().to_csv(OUT / "ro_search_zoa_detections.csv", index=False)


if __name__ == "__main__":
    main()
