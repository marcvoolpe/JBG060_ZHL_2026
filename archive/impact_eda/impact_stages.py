"""
Stages 2–8 of the cropland / conflict impact EDA (after Stage 1 inventory).

Run from repo root:
    python -m archive.impact_eda.impact_stages
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkt as shapely_wkt
from shapely.geometry import box

from processing_data.paths import COURSE_RAW, EXT_DATA, PROCESSED_DIR, ROOT, ensure_impact_eda_out

OUT = ensure_impact_eda_out()
CROSS = OUT / "crosswalks"
CROSS.mkdir(parents=True, exist_ok=True)

HXL = re.compile(r"^#")

# Aligned with eda/revised_spatial_eda.py (do not resample flood parquets here).
FLOOD_PIXEL_AREA_KM2 = 0.25 * 0.25
FLOOD_TILE_EXTENT = {"lon_min": 20.0, "lon_max": 40.0, "lat_min": 0.0, "lat_max": 10.0}

# Predeclared Stage 5 sample-size floors. Below these, the join direction stops.
MIN_N_COUNTY_YEAR = 30
MIN_N_SNAPSHOT = 20
MIN_N_EVENTS = 50
MIN_N_ADMIN1_WEEK = 50
MIN_N_GEOEPR_GROUPS = 5

CLASS_TEST = "technically possible AND meaningful to test"
CLASS_OVER = "technically possible but easy to over-interpret"
CLASS_AVOID = "avoid unless a specific audit question"

DTM_R13_16_FILES = {
    13: "ssd-dtm-mobility-tracking-r13-baseline-assessment-dataset_hdx.xlsx",
    14: "ssd-dtm-mobility-tracking-r14-baseline-assessment-dataset.xlsx",
    15: "ssd-dtm-mobility-tracking-r15-baseline-assessment-dataset_publish_hdx.xlsx",
    16: "ssd-dtm-mobility-tracking-r16-baseline-assessment-dataset_updated_20250507.xlsx",
}

GED_PATH = EXT_DATA / "UCDP_georeferenced_and_nonstate" / "ged261-csv" / "GEDEvent_v26_1.csv"
GEOEPR_PATH = EXT_DATA / "GeoEPR_2021" / "GeoEPR-2021.csv"
ACLED_PATH = (
    EXT_DATA / "ACLED_aggregated_african" / "Africa_aggregated_data_up_to_week_of-2026-09-05.xlsx"
)


def _norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower().strip())


# Normalized source name -> COD admin2 norm (manual fixes after exact_norm fails).
MANUAL_COUNTY_NORM: dict[str, str] = {
    _norm_name("Yei county"): _norm_name("Yei"),
    _norm_name("Wau (rural only)"): _norm_name("Wau"),
    _norm_name("Kajo keji"): _norm_name("Kajo-keji"),
    _norm_name("Lopa/Lafon"): _norm_name("Lafon"),
    _norm_name("Raga"): _norm_name("Raja"),
    _norm_name("Canal Pigi"): _norm_name("Canal/Pigi"),
    _norm_name("Mayiendit"): _norm_name("Mayendit"),
    _norm_name("Panyijar"): _norm_name("Panyijiar"),
    _norm_name("Pariang (Ruweng)"): _norm_name("Pariang"),
    _norm_name("Luakpiny (Nasir)"): _norm_name("Luakpiny/Nasir"),
    _norm_name("Kajo Keji"): _norm_name("Kajo-keji"),
    _norm_name("Raga county"): _norm_name("Raja"),
    _norm_name("Pigi county"): _norm_name("Canal/Pigi"),
    _norm_name("Payinjar county"): _norm_name("Panyijiar"),
    _norm_name("Cueibit county"): _norm_name("Cueibet"),
}


def _resolve_admin2_row(
    row: dict,
    cod: pd.DataFrame,
    pcode_to_name: dict[str, str],
) -> dict:
    """Fill cod_pcode/cod_name/match_method using pcode, manual alias, or UCDP suffix strip."""
    if row.get("cod_pcode"):
        return row
    sp = str(row.get("source_pcode") or "").strip()
    if sp and sp in pcode_to_name:
        row["cod_pcode"] = sp
        row["cod_name"] = pcode_to_name[sp]
        row["match_method"] = "pcode"
        return row
    norm = _norm_name(row["source_name"])
    if norm in MANUAL_COUNTY_NORM:
        target = MANUAL_COUNTY_NORM[norm]
        hit = cod[cod["norm"] == target]
        if len(hit):
            row["cod_pcode"] = hit["pcode"].iloc[0]
            row["cod_name"] = hit["name"].iloc[0]
            row["match_method"] = "manual_alias"
            return row
    if row.get("source") == "UCDP_GED":
        stripped = _norm_name(str(row["source_name"]).replace(" county", ""))
        hit = cod[cod["norm"] == stripped]
        if len(hit):
            row["cod_pcode"] = hit["pcode"].iloc[0]
            row["cod_name"] = hit["name"].iloc[0]
            row["match_method"] = "ucdp_strip_county"
            return row
    hit = cod[cod["norm"] == norm]
    if len(hit):
        row["cod_pcode"] = hit["pcode"].iloc[0]
        row["cod_name"] = hit["name"].iloc[0]
        row["match_method"] = "exact_norm"
    return row


def run_stage2_semantics() -> Path:
    """Write semantics.md and semantics_outliers.csv from codebooks, Notes, READ ME, and data."""
    fews = pd.read_csv(EXT_DATA / "FEWS_crop_data" / "crop_data.csv")
    yld = fews[fews["indicator"] == "Yield"]["value"]
    yld_at_cap = int((yld == 2.0).sum())

    o24 = pd.read_excel(
        EXT_DATA / "OCHA_flood_data" / "ssd_flood_response_20122024.xlsx",
        sheet_name="Floods_affected_People",
    )
    o24c = o24[o24["Admin2"].notna() & (o24["Admin2"].astype(str).str.lower() != "total")]
    ocha_max = o24c.loc[o24c["People_Affected"].idxmax()]
    ocha_total_row = o24[o24["Admin2"].astype(str).str.lower() == "total"]
    ocha_total_val = (
        float(ocha_total_row["People_Affected"].iloc[0]) if len(ocha_total_row) else np.nan
    )

    ocha25 = pd.read_excel(
        EXT_DATA / "OCHA_flood_data" / "ss_people_affected_and_displaced_by_floods_20251130.xlsx"
    )
    aff_col = [c for c in ocha25.columns if "ffected" in c and "Peaple" not in c][0]
    dis_col = [c for c in ocha25.columns if "isplaced" in c][0]
    ocha25_aff = ocha25[aff_col].notna().sum()
    ocha25_dis = ocha25[dis_col].notna().sum()

    r16 = EXT_DATA / "IOM_DTM_mobility" / (
        "ssd-dtm-mobility-tracking-r16-baseline-assessment-dataset_updated_20250507.xlsx"
    )
    dtm = pd.read_excel(r16, sheet_name="MT R16 Baseline_Loc_Dataset")
    dtm = dtm[dtm["Country"].astype(str) != "#adm0+name"]
    dtm["a_idp_inds_ssd"] = pd.to_numeric(dtm["a_idp_inds_ssd"], errors="coerce")
    dtm_max = dtm.loc[dtm["a_idp_inds_ssd"].idxmax()]

    dis_2024 = pd.to_numeric(dtm["e_idp_arrival_2024_ind_disaster"], errors="coerce").sum()
    note = pd.read_excel(r16, sheet_name="Note", header=None)
    idp_def = " ".join(
        str(note.iloc[i, 1])
        for i in range(37, 41)
        if pd.notna(note.iloc[i, 1])
    ).strip()

    reason_sheet = pd.read_excel(r16, sheet_name="MT R16 IDPs By Reason State", header=None)
    stock_disaster = reason_sheet.iloc[5, 1]  # row "a- Disaster" total individuals

    ocha_readme = pd.read_excel(
        EXT_DATA / "OCHA_flood_data" / "ssd_flood_response_211022.xlsx",
        sheet_name="READ ME",
        header=None,
    ).iloc[:, 0].astype(str).tolist()

    fmr_notes = pd.read_excel(
        EXT_DATA / "IOM_DTM_flow" / "fmr_db_clean_nov2022_oct2023_public_nov21.xlsx",
        sheet_name="Notes",
        header=None,
    )
    fmr_positioning = str(fmr_notes.iloc[1, 1])[:400]

    fmr_dd = pd.read_excel(
        EXT_DATA / "IOM_DTM_flow" / "fmr_db_clean_nov2022_oct2023_public_nov21.xlsx",
        sheet_name="Data Dictionary",
    )
    forced_disp = fmr_dd.loc[fmr_dd["Variable name"] == "forced.displacement", "Description"]
    forced_disp_text = forced_disp.iloc[0] if len(forced_disp) else ""

    ged = pd.read_csv(
        EXT_DATA / "UCDP_georeferenced_and_nonstate" / "ged261-csv" / "GEDEvent_v26_1.csv",
        usecols=["country", "date_prec"],
    )
    ssd_ged = ged[ged["country"].astype(str).str.contains("South Sudan", case=False, na=False)]
    imprecise_dates = int(ssd_ged["date_prec"].isin([4, 5]).sum())

    outliers = pd.DataFrame(
        [
            {
                "dataset": "IOM_DTM_mobility_R16",
                "variable": "a_idp_inds_ssd",
                "value": dtm_max["a_idp_inds_ssd"],
                "unit": "individuals",
                "location": f"{dtm_max['village_idp_settlement_name']}, {dtm_max['county_name']}",
                "note": "max stock at one location",
            },
            {
                "dataset": "OCHA_flood_20122024",
                "variable": "People_Affected",
                "value": ocha_total_val,
                "unit": "people",
                "location": "Total row",
                "note": "aggregate row; do not treat as county",
            },
            {
                "dataset": "OCHA_flood_20122024",
                "variable": "People_Affected",
                "value": ocha_max["People_Affected"],
                "unit": "people",
                "location": str(ocha_max["Admin2"]),
                "note": "max county in partial file",
            },
            {
                "dataset": "FEWS_crop",
                "variable": "Yield",
                "value": 2.0,
                "unit": "MT/ha",
                "location": f"{yld_at_cap} county-season rows",
                "note": "file maximum; verify whether cap or data",
            },
        ]
    )
    outliers.to_csv(OUT / "semantics_outliers.csv", index=False)

    path = OUT / "semantics.md"
    lines = [
        "# Stage 2 — Data quality and semantics",
        "",
        "Definitions below are taken from **files in this repository**, not from modelling assumptions.",
        "",
        "## Candidate variables (impact / exposure)",
        "",
        "| Variable (family) | Claimed meaning | Safe use in flood-impact work |",
        "|-------------------|-----------------|-------------------------------|",
        "| `a_idp_inds_ssd` (DTM) | IDP individuals present at location at assessment | Displacement **stock**; not flood-specific |",
        "| `*_ind_disaster` (DTM) | IDPs attributed to reason category **Disaster** | **Not flood-only** (see gate below) |",
        "| `*_ind_conflict` / `*_ind_clashes` (DTM) | Conflict vs communal clashes (separate categories) | Displacement context; not hydrology |",
        "| OCHA People affected / displaced | Flood-season assessed people (definition shifts by file) | **Validation** snapshots; NaN ≠ 0 |",
        "| FEWS Area Harvested / Yield | CFSAM main-harvest cereals | Outcome **proxy**; 2016 missing |",
        "| ASAP crop % (course) | Static cropland fraction per cell | **Exposure**; not yield |",
        "| IPC Phase 3+ pop (course) | Committee food-insecurity classification | Context; not measured loss |",
        "| UCDP GED `best` | Battle-related deaths per event (≥1) | Violence **events**; join with date_prec care |",
        "| ACLED EVENTS / FATALITIES | Weekly admin1 aggregates | State-level tempo only |",
        "| unusual_flood_pixel_count | NASA unusual inundation label | **Hazard**; ≠ damage |",
        "",
        "## IOM DTM mobility (R16 baseline)",
        "",
        "- **Grain:** location / settlement snapshot per mobility round (`location_ssid`, lat/lon, admin P-codes).",
        "- **Stock:** `a_idp_inds_ssd` = IDP individuals present (location-level).",
        "- **Arrival-by-reason:** `*_ind_conflict`, `*_ind_clashes`, `*_ind_disaster` by arrival period.",
        "",
        "**IDP definition (Note sheet, rows 37–40, verbatim):**",
        f"> {idp_def}",
        "",
        "- **Reason categories (MT R16 IDPs By Reason State):** `a- Conflict`, `a- Communal clashes`, `a- Disaster`, `a- Other reason` (stock totals).",
        f"- **Observation:** national stock attributed to **Disaster** = {stock_disaster:,.0f} individuals (sheet total, not location sum).",
        f"- **Observation:** sum of location-level `e_idp_arrival_2024_ind_disaster` = {dis_2024:,.0f} (2024 arrival cohort only).",
        "",
        "### Stage 2 gate — `disaster` vs flood",
        "",
        "- **Observation:** DTM groups **natural or human-made disasters** in the IDP definition, but the coded reason is a single bucket **Disaster** (no flood/drought split in R16 files reviewed).",
        "- **Decision:** Do **not** use `*_ind_disaster` as a **flood-only** impact label. It may include drought, fire, or other hazards unless disaggregated elsewhere.",
        "- **Allowed:** Use as broad **natural-disaster-related displacement** with explicit caveat; pair with OCHA flood snapshots for flood-specific validation only.",
        "",
        "## IOM DTM flow (FMR)",
        "",
        "- **Grain:** group-flow records at Flow Monitoring Points; clean DB Nov 2022–Oct 2023.",
        "- **Notes (FMR clean DB, Positioning of FMPs, excerpt):**",
        f"> {fmr_positioning}…",
        "- **`forced.displacement` (Data Dictionary):**",
        f"> {forced_disp_text}",
        "- **`reason` / `reason.subtype`:** reported reason for travel (not expanded to flood in dictionary).",
        "- **Stocks vs flows:** FMR = **flows** at selected FMPs; mobility baseline = **stocks** — not additive.",
        "",
        "## OCHA flood snapshots",
        "",
        "- **Grain:** county (admin2) snapshots; five incompatible schemas.",
        "- **READ ME (ssd_flood_response_211022.xlsx):**",
    ]
    for t in ocha_readme[:4]:
        lines.append(f"  - {t}")
    lines.extend(
        [
            f"- **Observation (20251130 file):** {ocha25_aff}/79 counties with non-null affected; "
            f"{ocha25_dis}/79 with non-null displaced.",
            "- **NaN interpretation:** unassessed county in that snapshot, **not** zero affected.",
            f"- **Outlier:** 20122024 **Total** row People_Affected = {ocha_total_val:,.0f}; "
            f"max county row: {ocha_max['Admin2']} ({ocha_max['People_Affected']:,.0f}).",
            "",
            "## FEWS CFSAM crop (`crop_data.csv`)",
            "",
            "- **Source:** FAO/WFP/GoSS CFSAM special reports (`source_document` column).",
            "- **Product:** Cereal Crops (Mixed); **Main harvest** only.",
            "- **Indicators:** Area Harvested (ha), Quantity Produced (t), Yield (MT/ha).",
            f"- **Observation:** Yield max = {yld.max()} MT/ha on {yld_at_cap} rows; 2016 season absent in `season_year`.",
            "- **Not verified from file:** whether 2.0 is a hard cap or observed maximum.",
            "",
            "## ACLED (weekly Africa aggregate)",
            "",
            "- **Grain:** admin1 × week × event_type × sub_event_type.",
            "- **EVENTS:** count of events in bucket; **FATALITIES:** associated deaths.",
            "- **Not** event-level ACLED; no actors; no admin2. Events need not be lethal.",
            "- **Violence against civilians** ≠ UCDP type 3 one-sided (different ontologies).",
            "",
            "## UCDP GED v26.1 (`ged261_codebook.md`)",
            "",
            "- **Event:** ≥1 direct death; `type_of_violence` 1=state-based, 2=non-state, 3=one-sided.",
            f"- **Observation (SSD):** {imprecise_dates} events with `date_prec` 4 or 5 (month/year or longer uncertainty).",
            "- **`where_prec`:** geographic precision (see codebook); no `geo_precision` column in v26.1 CSV.",
            "",
            "## UCDP Non-State (`ucdp-nonstate-261.md`)",
            "",
            "- **Unit:** conflict-year dyad; **≥25 battle-related deaths/year**.",
            "- **`org`:** 1=formal groups, 2=informal non-communal, **3=communal/ethnic identity** conflicts.",
            "",
            "## GeoEPR 2021 (`EPR_2021_Codebook_GeoEPR.md`)",
            "",
            "- Politically relevant **settlement** polygons; SSD groups 2011–2021; overlaps allowed.",
            "- Not violence events; not individual ethnicity.",
            "",
            "## Course pack — IPC (`loading_impact_data.py`, `AA_DATA_ROLES.md`)",
            "",
            "- **Phase 3+ population** per county per analysis window.",
            "- Expert **consensus** classification (IPC technical manual); not a direct measurement of flood damage.",
            "",
            "## Course pack — flood masks (`AA_DATA_ROLES.md`)",
            "",
            "- **Unusual:** pixel floods less often than usual for that calendar month.",
            "- **Recurring:** often floods in that month historically.",
            "- Neither label equals severity, depth, or agricultural loss.",
            "",
            "## Outliers",
            "",
            "See `semantics_outliers.csv` in this folder.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_stage3_crosswalks() -> tuple[Path, Path]:
    admin2 = pd.read_csv(PROCESSED_DIR / "Administrative boundaries" / "ssd_admin2_processed.csv")
    admin1 = pd.read_csv(PROCESSED_DIR / "Administrative boundaries" / "ssd_admin1_processed.csv")
    ipc = pd.read_csv(PROCESSED_DIR / "IPC" / "ipc_phase3plus_county_long_processed.csv")
    fews = pd.read_csv(EXT_DATA / "FEWS_crop_data" / "crop_data.csv")
    ged = pd.read_csv(
        EXT_DATA / "UCDP_georeferenced_and_nonstate" / "ged261-csv" / "GEDEvent_v26_1.csv",
        usecols=["country", "adm_1", "adm_2", "date_prec"],
    )
    ged = ged[ged["country"].astype(str).str.contains("South Sudan", case=False, na=False)]
    ged = ged[ged["adm_2"].notna() & ged["adm_2"].astype(str).str.strip().astype(bool)]

    r16 = pd.read_excel(
        EXT_DATA
        / "IOM_DTM_mobility"
        / "ssd-dtm-mobility-tracking-r16-baseline-assessment-dataset_updated_20250507.xlsx",
        sheet_name="MT R16 Baseline_Loc_Dataset",
    )
    r16 = r16[r16["Country"].astype(str) != "#adm0+name"]
    dtm_pc = set(r16["County_INT_PCode"].dropna().astype(str))
    cod_pc = set(admin2["pcode"].astype(str))

    ocha = pd.read_excel(
        EXT_DATA / "OCHA_flood_data" / "ss_people_affected_and_displaced_by_floods_20251130.xlsx"
    )

    rows: list[dict] = []
    cod = admin2[["pcode", "name"]].copy()
    cod["norm"] = cod["name"].map(_norm_name)
    pcode_to_name = dict(zip(admin2["pcode"].astype(str), admin2["name"]))

    def add_source(source: str, frame: pd.DataFrame, name_col: str, pcode_col: str | None = None):
        for _, r in frame.drop_duplicates(subset=[name_col]).iterrows():
            raw = r[name_col]
            pcode = r[pcode_col] if pcode_col and pcode_col in r.index else ""
            norm = _norm_name(raw)
            match = cod[cod["norm"] == norm]
            rows.append(
                {
                    "admin_level": "admin2",
                    "source": source,
                    "source_name": raw,
                    "source_pcode": pcode,
                    "cod_pcode": match["pcode"].iloc[0] if len(match) else "",
                    "cod_name": match["name"].iloc[0] if len(match) else "",
                    "match_method": "exact_norm" if len(match) else "unmatched",
                }
            )

    add_source("IPC", ipc, "county")
    add_source("FEWS", fews.drop_duplicates("admin_2"), "admin_2")
    add_source("UCDP_GED", ged.drop_duplicates("adm_2"), "adm_2")
    add_source(
        "DTM_R16",
        r16.drop_duplicates("county_name"),
        "county_name",
        "County_INT_PCode",
    )
    add_source(
        "OCHA_20251130",
        ocha.drop_duplicates("Admin2"),
        "Admin2",
        "Admin2_PCODE",
    )

    xw = pd.DataFrame(rows)
    xw = pd.DataFrame(
        [_resolve_admin2_row(r, cod, pcode_to_name) for r in xw.to_dict(orient="records")]
    )
    xw_path = CROSS / "admin2_names.csv"
    xw.to_csv(xw_path, index=False)

    # FEWS fnid -> county (two vintages; map via crosswalk).
    fnid_map = (
        fews[["fnid", "admin_2"]]
        .drop_duplicates()
        .merge(
            xw[xw["source"] == "FEWS"][["source_name", "cod_pcode", "cod_name", "match_method"]],
            left_on="admin_2",
            right_on="source_name",
            how="left",
        )
        .rename(columns={"admin_2": "fews_admin_2"})
    )
    fnid_path = CROSS / "fews_fnid_to_admin2.csv"
    fnid_map.to_csv(fnid_path, index=False)

    # Admin1: ACLED vs COD (for state-level joins).
    ac = pd.read_excel(
        EXT_DATA / "ACLED_aggregated_african" / "Africa_aggregated_data_up_to_week_of-2026-09-05.xlsx",
        usecols=["COUNTRY", "ADMIN1"],
    )
    ac = ac[ac["COUNTRY"].astype(str).str.contains("South Sudan", case=False, na=False)]
    a1 = admin1[["pcode", "name"]].copy()
    a1["norm"] = a1["name"].map(_norm_name)
    a1_rows = []
    for admin1_name in sorted(ac["ADMIN1"].dropna().unique()):
        norm = _norm_name(admin1_name)
        hit = a1[a1["norm"] == norm]
        a1_rows.append(
            {
                "admin_level": "admin1",
                "source": "ACLED",
                "source_name": admin1_name,
                "cod_pcode": hit["pcode"].iloc[0] if len(hit) else "",
                "cod_name": hit["name"].iloc[0] if len(hit) else "",
                "match_method": "exact_norm" if len(hit) else "unmatched",
            }
        )
    pd.DataFrame(a1_rows).to_csv(CROSS / "admin1_names.csv", index=False)

    rates = (
        xw.groupby("source")["match_method"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )
    rates["n_total"] = xw.groupby("source").size().values
    rates["n_matched"] = xw.groupby("source")["cod_pcode"].apply(lambda s: (s.astype(str).str.len() > 0).sum()).values
    rates.to_csv(CROSS / "crosswalk_match_rates.csv", index=False)

    unmatched = xw[xw["cod_pcode"].astype(str).str.len() == 0][
        ["source", "source_name", "source_pcode"]
    ].drop_duplicates()
    unmatched.to_csv(CROSS / "admin2_unmatched.csv", index=False)

    ipc_dates = sorted(ipc["start_date"].unique().tolist())
    ged_imprecise = int(ged["date_prec"].isin([4, 5]).sum())

    tpath = OUT / "temporal_alignment.md"
    tlines = [
        "# Stage 3 — Temporal alignment (observation)",
        "",
        "| Dataset | Native time unit | Notes |",
        "|---------|------------------|-------|",
        "| Flood masks | daily | Aggregate to season/year for joins; unusual vs recurring separate |",
        "| FEWS crop | Main harvest season_year (annual) | 2016 missing; end-of-year period_date |",
        "| IPC | irregular 2–3 month windows | See IPC start dates below |",
        "| OCHA flood | snapshot per file | Do not stack as continuous series |",
        "| DTM mobility | round snapshot | Rounds 2,4–16 irregular; R16 collected Dec 2024–Feb 2025 |",
        "| DTM FMR | month (group flows) | Clean DB 11.2022–10.2023 |",
        "| ACLED aggregate | ISO week | Admin1 only — use `crosswalks/admin1_names.csv` |",
        "| UCDP GED | event day (with date_prec uncertainty) | Filter date_prec for precision-sensitive joins |",
        "| UCDP Non-State | calendar year | Dyad-year fatalities |",
        "| GeoEPR | 2011–2021 window | Static for SSD groups in extract |",
        "",
        "## IPC analysis windows (processed long file)",
        "",
    ]
    for d in ipc_dates:
        tlines.append(f"- {d}")
    tlines.extend(
        [
            "",
            "## OCHA snapshot files (observation)",
            "",
            "- ss_floodsaffected_people_20211213.xlsx (mixed layout)",
            "- ssd_flood_response_211022.xlsx (as of 21 Oct 2022)",
            "- ssd_flood_response_301122.xlsx (end Nov 2022)",
            "- ssd_flood_response_20122024.xlsx (partial county list)",
            "- ss_people_affected_and_displaced_by_floods_20251130.xlsx (79 counties, P-codes)",
            "",
            "## P-code observation (DTM R16 vs COD admin2)",
            "",
            f"- DTM county P-codes: {len(dtm_pc)}; COD: {len(cod_pc)}.",
            f"- In DTM not in COD: {sorted(dtm_pc - cod_pc)}.",
            f"- In COD not in DTM: {sorted(cod_pc - dtm_pc)}.",
            "",
            "## UCDP GED date precision (South Sudan events)",
            "",
            f"- Events with `date_prec` 4 or 5 (month/year or longer): **{ged_imprecise}** of {len(ged)}.",
            "",
            "## ACLED vs county flood",
            "",
            "- County-level flood exposure requires **aggregating flood metrics up to admin1**; cannot disaggregate ACLED to county.",
            "",
            "## Crosswalk artefacts",
            "",
            "- `crosswalks/admin2_names.csv` — name/P-code to COD admin2",
            "- `crosswalks/fews_fnid_to_admin2.csv` — FEWS `fnid` mapping",
            "- `crosswalks/admin1_names.csv` — ACLED states",
            "- `crosswalks/crosswalk_match_rates.csv` — match counts by source",
            "- `crosswalks/admin2_unmatched.csv` — rows still without `cod_pcode`",
            "",
        ]
    )
    tpath.write_text("\n".join(tlines), encoding="utf-8")
    return xw_path, tpath


def run_stage4_redundancy() -> Path:
    """Overlap / redundancy matrix plus light empirical check on UCDP non-state vs GED type-2."""
    pairs = [
        # Conflict / violence channel — pick one primary series per model
        (
            "ACLED_weekly_admin1_events",
            "UCDP_GED_admin1_agg",
            "overlapping",
            "Both measure disorder/violence tempo; different event definitions and geography (admin1 week vs points). Do not sum fatalities.",
        ),
        (
            "UCDP_NonState_year_dyad",
            "UCDP_GED_type2_events_year",
            "derived",
            "Non-state dataset is annual dyads with >=25 deaths; GED type-2 events are >=1 death. Same channel; do not use both as independent predictors.",
        ),
        (
            "ACLED_fatalities_admin1",
            "UCDP_GED_best_deaths",
            "overlapping",
            "Fatality counts are not comparable units; never add in one outcome variable.",
        ),
        # Displacement channel
        (
            "DTM_mobility_IDP_stock",
            "DTM_FMR_group_flows",
            "independent",
            "Stock at settlements vs flows at FMPs; not nationally representative FMR.",
        ),
        (
            "DTM_mobility_IDP_stock",
            "OCHA_flood_affected",
            "overlapping",
            "Both population impact; OCHA is flood-assessed snapshot, DTM is IDP stock (all reasons).",
        ),
        (
            "DTM_arrival_disaster",
            "OCHA_flood_affected",
            "overlapping",
            "Disaster bucket is not flood-only (Stage 2); OCHA is flood-specific but sparse.",
        ),
        (
            "DTM_mobility_IDP_stock",
            "DTM_arrival_disaster",
            "overlapping",
            "Same DTM round; stock vs period-of-arrival attribution — related, not duplicate rows.",
        ),
        (
            "OCHA_flood_affected",
            "OCHA_flood_displaced",
            "overlapping",
            "Same file; displaced subset of affected per READ ME — do not double-count.",
        ),
        (
            "OCHA_snapshot_2022",
            "OCHA_snapshot_2025",
            "overlapping",
            "Different seasons and schemas; not a continuous panel without harmonisation.",
        ),
        # Food / agriculture channel
        (
            "ASAP_crop_pct_static",
            "FEWS_area_harvested_annual",
            "independent",
            "Land-cover fraction vs CFSAM harvested hectares; complementary exposure/outcome.",
        ),
        (
            "FEWS_quantity_produced",
            "FEWS_area_harvested",
            "derived",
            "Same CFSAM source; yield links them — one primary crop outcome per analysis.",
        ),
        (
            "IPC_phase3plus_pop",
            "FEWS_production",
            "overlapping",
            "Both food-security related; IPC is consensus classification, FEWS is CFSAM measurement.",
        ),
        (
            "IPC_phase3plus_pop",
            "DTM_IDP_stock",
            "overlapping",
            "Displacement and food insecurity co-occur; correlation is not causal.",
        ),
        # Hazard channel
        (
            "flood_unusual_pixel_count",
            "flood_recurring_pixel_count",
            "related_same_source",
            "Same NASA mask product; different labels. Test separately; do not treat as independent hazards without justification.",
        ),
        (
            "flood_mask_hazard",
            "OCHA_flood_affected",
            "overlapping",
            "Remote sensing extent vs assessed people; validation pair, not duplicate information.",
        ),
        # Ethnicity / actors — not join keys
        (
            "GeoEPR_settlement_polygon",
            "UCDP_GED_side_a_side_b",
            "overlapping",
            "Shared ethnic strings (Dinka, Nuer, …); settlement area vs event actors — not a valid merge key.",
        ),
        (
            "GeoEPR_settlement_polygon",
            "UCDP_NonState_dyad_names",
            "overlapping",
            "Dyad names sometimes ethnic; ecological fallacy if used as ethnicity prediction.",
        ),
        # Course drivers (reference)
        (
            "ERA5_precipitation",
            "CHIRPS_precipitation",
            "overlapping",
            "CHIRPS not in data/ folder; if added, same hydrological driver — one rain product per model.",
        ),
        (
            "WorldPop_exposure",
            "ASAP_crop_exposure",
            "independent",
            "People vs cropland fraction; joint exposure layer OK if roles defined.",
        ),
    ]
    df = pd.DataFrame(
        pairs,
        columns=["series_a", "series_b", "relation", "modelling_rule"],
    )
    csv_path = OUT / "redundancy_matrix.csv"
    df.to_csv(csv_path, index=False)

    # Empirical: UCDP non-state dyad-years vs GED type-2 event counts by year (SSD).
    ged = pd.read_csv(
        EXT_DATA / "UCDP_georeferenced_and_nonstate" / "ged261-csv" / "GEDEvent_v26_1.csv",
        usecols=["country", "year", "type_of_violence"],
    )
    ged = ged[ged["country"].astype(str).str.contains("South Sudan", case=False, na=False)]
    ged_t2 = ged[ged["type_of_violence"] == 2].groupby("year").size().reset_index(name="ged_type2_events")
    ns = pd.read_csv(
        EXT_DATA / "UCDP_georeferenced_and_nonstate" / "ucdp-nonstate-261-csv" / "NonState_v26_1.csv"
    )
    ns = ns[
        ns["location"].astype(str).str.contains("South Sudan", case=False, na=False)
        | ns["gwno_location"].astype(str).str.contains("626", na=False)
    ]
    ns_y = ns.groupby("year").size().reset_index(name="nonstate_dyad_years")
    emp = ged_t2.merge(ns_y, on="year", how="outer").sort_values("year")
    if len(emp) >= 5 and emp["nonstate_dyad_years"].notna().sum() >= 5:
        ucdp_spearman = float(
            emp["ged_type2_events"].rank().corr(emp["nonstate_dyad_years"].rank())
        )
    else:
        ucdp_spearman = np.nan
    emp_path = OUT / "redundancy_ucdp_type2_vs_nonstate_by_year.csv"
    emp.to_csv(emp_path, index=False)

    by_channel = (
        df.groupby("relation")
        .size()
        .reset_index(name="n_pairs")
        .sort_values("n_pairs", ascending=False)
    )

    md_path = OUT / "redundancy.md"
    lines = [
        "# Stage 4 — Overlap and redundancy",
        "",
        "Goal: avoid **double-counting** information in one model. Relations are documented judgements "
        "from Stage 2 semantics and dataset design, plus one empirical check on UCDP.",
        "",
        "## Relation types",
        "",
        "| Relation | Meaning | Modelling rule |",
        "|----------|---------|----------------|",
        "| `independent` | Different constructs | May appear together if roles differ (exposure vs outcome) |",
        "| `overlapping` | Same topic, different measurement | At most one primary series per channel, or explicit validation only |",
        "| `derived` | One is aggregated/thresholded from similar events | Do not use both as independent predictors |",
        "| `related_same_source` | Same product, different fields | Do not stack without testing marginal value |",
        "",
        "## Pairs per relation (count)",
        "",
        by_channel.to_string(index=False),
        "",
        "## UCDP empirical check (observation)",
        "",
        "South Sudan: annual count of GED `type_of_violence==2` events vs count of Non-State dyad-year rows.",
        f"See `{emp_path.name}`.",
        "",
    ]
    if len(emp) and pd.notna(ucdp_spearman):
        lines.append(
            f"- Rank correlation across years (Spearman): **{ucdp_spearman:.3f}** — "
            "supports treating Non-State and GED type-2 as same channel, not independent predictors."
        )
    lines.extend(
        [
            "",
            "## One series per channel (recommended)",
            "",
            "| Channel | Pick one primary | Keep second only for… |",
            "|---------|------------------|----------------------|",
            "| Hazard | unusual **or** recurring flood extent | Sensitivity / validation |",
            "| Crop exposure | ASAP % **or** FEWS hectares (role-dependent) | Joint layer with clear labels |",
            "| Food impact | FEWS production **or** IPC Phase 3+ | Context vs outcome |",
            "| Violence | UCDP GED events **or** ACLED weekly (admin1) | Cross-check, not sum |",
            "| Communal violence | UCDP Non-State **or** GED type-2 aggregates | Not both in one model |",
            "| Displacement stock | DTM IDP stock | OCHA for flood validation |",
            "",
            "Full pair list: `redundancy_matrix.csv`.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path


def _drop_hxl(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    first = df.iloc[0].astype(str)
    if first.str.startswith("#").any():
        return df.iloc[1:].reset_index(drop=True)
    return df


def _find_col(df: pd.DataFrame, *needles: str, exclude: tuple[str, ...] = ()) -> str | None:
    for col in df.columns:
        text = str(col).replace("\n", " ").lower()
        if any(n.lower() in text for n in needles) and not any(e.lower() in text for e in exclude):
            return col
    return None


def _is_matched_pcode(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    return s.ne("") & s.ne("nan") & s.ne("None")


def _gate_from_n(classification: str, n: int | float | None, min_n: int) -> str:
    if classification == CLASS_AVOID:
        return "avoid"
    if n is None or pd.isna(n) or int(n) < min_n:
        return "stop_n_too_small"
    if classification == CLASS_OVER:
        return "proceed_with_caveat"
    return "proceed"


def _flood_parquet_years() -> dict[str, list[int]]:
    """Years present as compact parquet files. Does not read pixel rows."""
    out: dict[str, list[int]] = {}
    for kind in ("unusual", "recurring"):
        folder = COURSE_RAW / "flood_masks" / f"compact_{kind}"
        years = sorted(
            {
                int(path.stem.rsplit("_", 1)[-1])
                for path in folder.glob("flood_events_*.parquet")
            }
        )
        out[kind] = years
    return out


def _admin2_flood_tile_coverage() -> pd.DataFrame:
    """Admin2 ∩ h20v08+h21v08 tile bbox. Same extent/area units as revised_spatial_eda.py."""
    admin2 = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson").to_crs(
        "EPSG:4326"
    )
    tile = gpd.GeoDataFrame(
        {"tile_extent": ["h20v08+h21v08"]},
        geometry=[
            box(
                FLOOD_TILE_EXTENT["lon_min"],
                FLOOD_TILE_EXTENT["lat_min"],
                FLOOD_TILE_EXTENT["lon_max"],
                FLOOD_TILE_EXTENT["lat_max"],
            )
        ],
        crs="EPSG:4326",
    )
    metric = admin2.to_crs("EPSG:6933")
    tile_metric = tile.to_crs("EPSG:6933")
    clipped = gpd.overlay(metric, tile_metric, how="intersection")
    covered = clipped[["adm2_pcode"]].copy()
    covered["flood_tile_covered_km2"] = clipped.area / 1_000_000
    covered = covered.groupby("adm2_pcode", as_index=False)["flood_tile_covered_km2"].sum()
    table = admin2[["adm2_name", "adm2_pcode", "adm1_name", "adm1_pcode"]].copy()
    table["area_km2"] = metric.area.values / 1_000_000
    table = table.merge(covered, on="adm2_pcode", how="left").fillna({"flood_tile_covered_km2": 0.0})
    table["flood_tile_coverage_share"] = table["flood_tile_covered_km2"] / table["area_km2"]
    table["flood_observed"] = table["flood_tile_coverage_share"] > 0
    table["flood_well_covered"] = table["flood_tile_coverage_share"] >= 0.9
    return table


def _load_ged_ssd() -> pd.DataFrame:
    usecols = [
        "country",
        "year",
        "type_of_violence",
        "latitude",
        "longitude",
        "date_prec",
        "where_prec",
        "adm_1",
        "adm_2",
        "date_start",
        "id",
        "side_a",
        "side_b",
    ]
    chunks = []
    for chunk in pd.read_csv(GED_PATH, usecols=usecols, chunksize=100_000):
        ssd = chunk[chunk["country"].astype(str).str.contains("South Sudan", case=False, na=False)]
        if len(ssd):
            chunks.append(ssd)
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=usecols)


def _load_geoepr_ssd() -> pd.DataFrame:
    usecols = ["statename", "from", "to", "group", "type", "sqkm", "the_geom"]
    chunks = []
    for chunk in pd.read_csv(GEOEPR_PATH, usecols=usecols, chunksize=20_000):
        ssd = chunk[chunk["statename"].astype(str).str.contains("South Sudan", case=False, na=False)]
        if len(ssd):
            chunks.append(ssd)
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=usecols)


def _parse_wkt(value: object):
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return None
    if text.upper().startswith("SRID") and ";" in text:
        text = text.split(";", 1)[1]
    return shapely_wkt.loads(text)


def _md_table(df: pd.DataFrame, columns: list[str] | None = None) -> str:
    frame = df if columns is None else df[columns]
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    sep = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = []
    for _, row in frame.iterrows():
        cells = []
        for col in frame.columns:
            val = row[col]
            if pd.isna(val):
                cells.append("")
            elif isinstance(val, float) and val.is_integer():
                cells.append(str(int(val)))
            else:
                cells.append(str(val))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep, *rows])


def _join_row(
    join_id: str,
    left: str,
    right: str,
    grain: str,
    keys: str,
    n: int | float | None,
    n_definition: str,
    min_n: int,
    classification: str,
    coverage_note: str,
    caveat: str,
    stage4_rule: str,
) -> dict:
    gate = _gate_from_n(classification, n, min_n)
    return {
        "join_id": join_id,
        "left": left,
        "right": right,
        "grain": grain,
        "keys": keys,
        "n": "" if n is None or pd.isna(n) else int(n),
        "n_definition": n_definition,
        "min_n": min_n,
        "coverage_note": coverage_note,
        "classification": classification,
        "gate": gate,
        "stage4_channel_rule": stage4_rule,
        "caveat": caveat,
    }


def _profile_ocha_snapshots(cod_pc: set[str]) -> pd.DataFrame:
    records = []
    specs = [
        {
            "join_id": "OCHA_20211213",
            "file": "ss_floodsaffected_people_20211213.xlsx",
            "sheet": "Sheet1",
            "snapshot_date": "2021-12-13",
            "date_source": "filename",
        },
        {
            "join_id": "OCHA_211022",
            "file": "ssd_flood_response_211022.xlsx",
            "sheet": "2022 floods",
            "snapshot_date": "2022-10-21",
            "date_source": "filename 211022 + READ ME 'as of 21 Oct 2022'",
        },
        {
            "join_id": "OCHA_301122",
            "file": "ssd_flood_response_301122.xlsx",
            "sheet": "As of November 2022",
            "snapshot_date": "2022-11-30",
            "date_source": "filename 301122 + sheet title",
        },
        {
            "join_id": "OCHA_20122024",
            "file": "ssd_flood_response_20122024.xlsx",
            "sheet": "Floods_affected_People",
            "snapshot_date": "2024-12-20",
            "date_source": "filename 20122024",
        },
        {
            "join_id": "OCHA_20251130",
            "file": "ss_people_affected_and_displaced_by_floods_20251130.xlsx",
            "sheet": "Summary",
            "snapshot_date": "2025-11-30",
            "date_source": "filename 20251130",
        },
    ]
    ocha_dir = EXT_DATA / "OCHA_flood_data"
    for spec in specs:
        df = pd.read_excel(ocha_dir / spec["file"], sheet_name=spec["sheet"])
        df = _drop_hxl(df)
        pcode_col = _find_col(df, "admin2_pcode", "admin2 pcode", "p code.1")
        if pcode_col is None:
            pcode_col = _find_col(df, "pcode")
        name_col = _find_col(df, "admin2", "county")
        aff_col = _find_col(df, "affected", exclude=("percentage", "%", "peaple", "proplr", "prople"))
        assessed_col = _find_col(df, "is the county assessed")
        if assessed_col is None:
            assessed_col = _find_col(
                df, "assessed?", exclude=("number", "people", "affected", "flood")
            )
        if name_col is None:
            records.append({**spec, "n_rows": len(df), "error": "no county column"})
            continue
        # Drop total / blank county rows.
        names = df[name_col].astype(str).str.strip()
        work = df[names.notna() & names.ne("") & names.str.lower().ne("total") & names.ne("nan")].copy()
        n_rows = len(work)
        n_unique_names = int(work[name_col].astype(str).str.strip().nunique())
        n_with_pcode = 0
        n_pcode_in_cod = 0
        if pcode_col:
            pc = work[pcode_col].astype(str).str.strip()
            n_with_pcode = int((pc.ne("") & pc.ne("nan")).sum())
            n_pcode_in_cod = int(pc.isin(cod_pc).sum())
        n_affected_nonnull = int(pd.to_numeric(work[aff_col], errors="coerce").notna().sum()) if aff_col else 0
        n_assessed_yes = np.nan
        if assessed_col:
            flag = work[assessed_col].astype(str).str.strip().str.lower()
            n_assessed_yes = int(flag.eq("yes").sum())
        records.append(
            {
                **spec,
                "n_county_rows": n_rows,
                "n_unique_county_names": n_unique_names,
                "pcode_col": pcode_col or "",
                "name_col": name_col,
                "affected_col": aff_col or "",
                "n_with_pcode": n_with_pcode,
                "n_pcode_in_cod": n_pcode_in_cod,
                "n_affected_nonnull": n_affected_nonnull,
                "n_assessed_yes": n_assessed_yes,
                "has_cod_pcode_key": bool(pcode_col) and n_pcode_in_cod > 0,
            }
        )
    return pd.DataFrame(records)


def _profile_dtm_r13_16(cod_pc: set[str]) -> pd.DataFrame:
    rows = []
    mob = EXT_DATA / "IOM_DTM_mobility"
    wanted = {
        "County_INT_PCode",
        "county_name",
        "latitude",
        "longitude",
        "a_idp_inds_ssd",
    }
    for rnd, filename in DTM_R13_16_FILES.items():
        path = mob / filename
        xl = pd.ExcelFile(path)
        sheet = next(s for s in xl.sheet_names if "Loc_Dataset" in s)
        header = pd.read_excel(path, sheet_name=sheet, nrows=0)
        usecols = [c for c in header.columns if c in wanted or str(c).endswith("_ind_disaster")]
        df = pd.read_excel(path, sheet_name=sheet, usecols=usecols)
        df = _drop_hxl(df)
        pc = df["County_INT_PCode"].astype(str).str.strip() if "County_INT_PCode" in df.columns else pd.Series(dtype=str)
        n_loc = len(df)
        n_pc = int((pc.ne("") & pc.ne("nan")).sum()) if len(pc) else 0
        counties = set(pc[pc.ne("") & pc.ne("nan")].unique()) if len(pc) else set()
        n_counties = len(counties)
        n_in_cod = len(counties & cod_pc)
        n_not_in_cod = len(counties - cod_pc)
        has_xy = "latitude" in df.columns and "longitude" in df.columns
        n_xy = 0
        if has_xy:
            n_xy = int(
                (
                    pd.to_numeric(df["latitude"], errors="coerce").notna()
                    & pd.to_numeric(df["longitude"], errors="coerce").notna()
                ).sum()
            )
        dis_cols = [c for c in df.columns if str(c).endswith("_ind_disaster")]
        n_counties_disaster_gt0 = 0
        if dis_cols and "County_INT_PCode" in df.columns:
            tmp = df.copy()
            tmp["_dis"] = 0.0
            for col in dis_cols:
                tmp["_dis"] = tmp["_dis"] + pd.to_numeric(tmp[col], errors="coerce").fillna(0)
            by_c = tmp.groupby("County_INT_PCode")["_dis"].sum()
            n_counties_disaster_gt0 = int((by_c > 0).sum())
        rows.append(
            {
                "round": rnd,
                "file": filename,
                "sheet": sheet,
                "n_locations": n_loc,
                "n_locations_with_pcode": n_pc,
                "n_counties": n_counties,
                "n_counties_in_cod": n_in_cod,
                "n_counties_pcode_not_in_cod": n_not_in_cod,
                "has_lat_lon": has_xy,
                "n_locations_with_lat_lon": n_xy,
                "n_disaster_columns": len(dis_cols),
                "n_counties_disaster_gt0": n_counties_disaster_gt0,
                "cod_counties_missing_this_round": len(cod_pc - counties),
            }
        )
    return pd.DataFrame(rows)


def run_stage5_join_feasibility() -> Path:
    """Classify intended joins with grain, keys, coverage, and minimum n."""
    admin2 = pd.read_csv(PROCESSED_DIR / "Administrative boundaries" / "ssd_admin2_processed.csv")
    admin1 = pd.read_csv(PROCESSED_DIR / "Administrative boundaries" / "ssd_admin1_processed.csv")
    xw = pd.read_csv(CROSS / "admin2_names.csv")
    fnid_map = pd.read_csv(CROSS / "fews_fnid_to_admin2.csv")
    a1_xw = pd.read_csv(CROSS / "admin1_names.csv")
    ipc = pd.read_csv(PROCESSED_DIR / "IPC" / "ipc_phase3plus_county_long_processed.csv")
    fews = pd.read_csv(EXT_DATA / "FEWS_crop_data" / "crop_data.csv")

    cod_pc = set(admin2["pcode"].astype(str))
    n_cod = len(cod_pc)

    flood_years = _flood_parquet_years()
    unusual_years = flood_years["unusual"]
    recurring_years = flood_years["recurring"]
    flood_year_set = set(unusual_years) & set(recurring_years)

    coverage = _admin2_flood_tile_coverage()
    coverage_path = OUT / "flood_tile_coverage_admin2.csv"
    coverage.to_csv(coverage_path, index=False)
    n_flood_obs = int(coverage["flood_observed"].sum())
    n_flood_well = int(coverage["flood_well_covered"].sum())
    zero_cov = coverage.loc[~coverage["flood_observed"], ["adm2_name", "adm2_pcode", "adm1_name"]]
    low_cov = coverage.loc[
        coverage["flood_observed"] & (coverage["flood_tile_coverage_share"] < 0.5),
        ["adm2_name", "adm2_pcode", "adm1_name", "flood_tile_coverage_share"],
    ]
    observed_pc = set(coverage.loc[coverage["flood_observed"], "adm2_pcode"].astype(str))
    well_pc = set(coverage.loc[coverage["flood_well_covered"], "adm2_pcode"].astype(str))

    ocha_prof = _profile_ocha_snapshots(cod_pc)
    ocha_path = OUT / "join_feasibility_ocha_snapshots.csv"
    ocha_prof.to_csv(ocha_path, index=False)

    dtm_prof = _profile_dtm_r13_16(cod_pc)
    dtm_path = OUT / "join_feasibility_dtm_r13_16.csv"
    dtm_prof.to_csv(dtm_path, index=False)

    # FEWS county-years after fnid/name crosswalk.
    harvest = fews[fews["indicator"] == "Area Harvested"].copy()
    harvest["year"] = harvest["season_year"].str.extract(r"(\d{4})").astype("Int64")
    fnid_ok = fnid_map.copy()
    fnid_ok["matched"] = _is_matched_pcode(fnid_ok["cod_pcode"])
    harvest = harvest.merge(
        fnid_ok[["fnid", "cod_pcode", "cod_name", "match_method", "matched"]],
        on="fnid",
        how="left",
    )
    harvest["matched"] = harvest["matched"].fillna(False)
    harvest["in_flood_years"] = harvest["year"].isin(flood_year_set)
    harvest["flood_observed"] = harvest["cod_pcode"].astype(str).isin(observed_pc)
    harvest["flood_well_covered"] = harvest["cod_pcode"].astype(str).isin(well_pc)
    fews_cy = harvest[harvest["matched"]].drop_duplicates(["cod_pcode", "year"])
    n_fews_cy_matched = int(fews_cy.groupby(["cod_pcode", "year"]).ngroups)
    n_fews_cy_both = int(
        fews_cy[fews_cy["flood_observed"] & fews_cy["in_flood_years"]]
        .groupby(["cod_pcode", "year"])
        .ngroups
    )
    n_fews_cy_well = int(
        fews_cy[fews_cy["flood_well_covered"] & fews_cy["in_flood_years"]]
        .groupby(["cod_pcode", "year"])
        .ngroups
    )
    fews_years = sorted(int(y) for y in harvest["year"].dropna().unique())
    fews_missing_years = sorted(set(range(min(fews_years), max(fews_years) + 1)) - set(fews_years))
    n_fews_admin2 = int(fews["admin_2"].nunique())
    n_fews_fnid_matched = int(fnid_ok["matched"].sum())
    n_fews_fnid = int(fnid_ok["fnid"].nunique())
    fews_unmatched_names = sorted(
        fnid_ok.loc[~fnid_ok["matched"], "fews_admin_2"].dropna().astype(str).unique().tolist()
    )
    fews_year_tbl = (
        fews_cy[fews_cy["flood_observed"] & fews_cy["in_flood_years"]]
        .groupby("year")
        .size()
        .reset_index(name="n_counties_matched_flood_observed")
    )
    fews_year_path = OUT / "join_feasibility_fews_years.csv"
    fews_year_tbl.to_csv(fews_year_path, index=False)

    # OCHA 20251130 × flood coverage among assessed (non-null) counties.
    ocha_latest = ocha_prof[ocha_prof["join_id"] == "OCHA_20251130"].iloc[0]
    ocha25 = pd.read_excel(
        EXT_DATA / "OCHA_flood_data" / "ss_people_affected_and_displaced_by_floods_20251130.xlsx"
    )
    aff_col = _find_col(ocha25, "affected", exclude=("peaple",))
    ocha25["Admin2_PCODE"] = ocha25["Admin2_PCODE"].astype(str).str.strip()
    ocha25["affected_nonnull"] = pd.to_numeric(ocha25[aff_col], errors="coerce").notna()
    ocha25 = ocha25.merge(
        coverage[["adm2_pcode", "flood_observed", "flood_well_covered"]],
        left_on="Admin2_PCODE",
        right_on="adm2_pcode",
        how="left",
    )
    n_ocha25_assessed_flood = int(
        (ocha25["affected_nonnull"] & ocha25["flood_observed"].fillna(False)).sum()
    )
    n_ocha25_all_flood = int(ocha25["flood_observed"].fillna(False).sum())

    # DTM R16 counties with flood observation.
    dtm16 = dtm_prof[dtm_prof["round"] == 16].iloc[0]
    r16_path = EXT_DATA / "IOM_DTM_mobility" / DTM_R13_16_FILES[16]
    r16 = pd.read_excel(
        r16_path,
        sheet_name="MT R16 Baseline_Loc_Dataset",
        usecols=["County_INT_PCode", "latitude", "longitude"],
    )
    r16 = _drop_hxl(r16)
    r16_pc = set(r16["County_INT_PCode"].dropna().astype(str).str.strip())
    n_dtm_counties_flood = len(r16_pc & observed_pc)
    n_dtm_xy = int(
        (
            pd.to_numeric(r16["latitude"], errors="coerce").notna()
            & pd.to_numeric(r16["longitude"], errors="coerce").notna()
        ).sum()
    )

    # UCDP GED sjoin to admin2 polygons (not UCDP adm_2 names).
    admin2_gdf = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson").to_crs(
        "EPSG:4326"
    )
    ged = _load_ged_ssd()
    ged_pts = gpd.GeoDataFrame(
        ged,
        geometry=gpd.points_from_xy(ged["longitude"], ged["latitude"]),
        crs="EPSG:4326",
    )
    ged_join = gpd.sjoin(
        ged_pts,
        admin2_gdf[["adm2_pcode", "adm2_name", "adm1_pcode", "adm1_name", "geometry"]],
        how="left",
        predicate="intersects",
    )
    if "id" in ged_join.columns:
        ged_join = ged_join.drop_duplicates("id", keep="first")
    ged_join["in_admin2"] = ged_join["adm2_pcode"].notna()
    n_ged = len(ged)
    n_ged_in_poly = int(ged_join["in_admin2"].sum())
    # where_prec <= 3 is ADM2 or better (codebook); date_prec <= 4 is month or better.
    admin2_ok = ged_join["in_admin2"] & (ged_join["where_prec"] <= 3)
    seasonal_ok = admin2_ok & (ged_join["date_prec"] <= 4)
    monthly_ok = admin2_ok & (ged_join["date_prec"] <= 3)
    n_ged_admin2_ok = int(admin2_ok.sum())
    n_ged_seasonal = int(seasonal_ok.sum())
    n_ged_monthly = int(monthly_ok.sum())
    n_ged_misleading_pip = int(
        ((ged_join["where_prec"] >= 4) & ged_join["in_admin2"]).sum()
    )
    ged_ok = ged_join[seasonal_ok].copy()
    ged_ok["date_start"] = pd.to_datetime(ged_ok["date_start"], errors="coerce")
    ged_ok["year"] = pd.to_numeric(ged_ok["year"], errors="coerce")
    ged_ok["in_flood_years"] = ged_ok["year"].isin(flood_year_set)
    ged_ok["flood_observed"] = ged_ok["adm2_pcode"].astype(str).isin(observed_pc)
    n_ged_events_vs_flood = int((ged_ok["in_flood_years"] & ged_ok["flood_observed"]).sum())
    n_ged_admin2_with_events = int(ged_ok["adm2_pcode"].nunique())
    n_ged_county_years = int(
        ged_ok[ged_ok["in_flood_years"] & ged_ok["flood_observed"]]
        .drop_duplicates(["adm2_pcode", "year"])
        .shape[0]
    )
    n_ged_type2_seasonal = int((ged_ok["type_of_violence"] == 2).sum())
    n_panel_county_years_ged = n_flood_obs * len([y for y in range(2011, 2026) if y in flood_year_set])
    ucdp_prec = (
        ged.assign(n=1)
        .groupby(["where_prec", "date_prec"], as_index=False)
        .size()
        .rename(columns={"size": "n_events"})
    )
    ucdp_prec_path = OUT / "join_feasibility_ucdp_filters.csv"
    ucdp_prec.to_csv(ucdp_prec_path, index=False)
    ged_sjoin_path = OUT / "join_feasibility_ucdp_sjoin_summary.csv"
    pd.DataFrame(
        [
            {
                "n_ssd_events": n_ged,
                "n_sjoin_inside_admin2": n_ged_in_poly,
                "n_where_prec_le3_in_admin2": n_ged_admin2_ok,
                "n_where_prec_le3_date_prec_le4": n_ged_seasonal,
                "n_where_prec_le3_date_prec_le3": n_ged_monthly,
                "n_where_prec_ge4_still_inside_a_polygon": n_ged_misleading_pip,
                "n_events_flood_observed_county_and_flood_year": n_ged_events_vs_flood,
                "n_admin2_with_filtered_events": n_ged_admin2_with_events,
                "n_admin2_years_with_filtered_events": n_ged_county_years,
                "n_type2_filtered_events": n_ged_type2_seasonal,
                "n_admin2_year_panel_flood_observed_2011_2025": n_panel_county_years_ged,
            }
        ]
    ).to_csv(ged_sjoin_path, index=False)

    # GeoEPR settlement polygons ∩ admin2 / flood tile (exposure only).
    geo_n_groups = 0
    geo_n_intersect_tile = np.nan
    geo_n_admin2_overlap = np.nan
    geo_n_admin2_flood_overlap = np.nan
    geo_error = ""
    geo_groups_tbl = pd.DataFrame()
    try:
        geo = _load_geoepr_ssd()
        geo["geometry"] = geo["the_geom"].map(_parse_wkt)
        geo = geo[geo["geometry"].notna()].copy()
        geo_n_groups = len(geo)
        geo_gdf = gpd.GeoDataFrame(geo.drop(columns=["the_geom"]), geometry="geometry", crs="EPSG:4326")
        geo_gdf["geometry"] = geo_gdf.geometry.buffer(0)
        admin2_overlay = admin2_gdf[["adm2_pcode", "adm2_name", "geometry"]].copy()
        admin2_overlay["geometry"] = admin2_overlay.geometry.buffer(0)
        tile_poly = box(
            FLOOD_TILE_EXTENT["lon_min"],
            FLOOD_TILE_EXTENT["lat_min"],
            FLOOD_TILE_EXTENT["lon_max"],
            FLOOD_TILE_EXTENT["lat_max"],
        )
        geo_gdf["intersects_flood_tile"] = geo_gdf.intersects(tile_poly)
        geo_n_intersect_tile = int(geo_gdf["intersects_flood_tile"].sum())
        overlap = gpd.overlay(
            geo_gdf[["group", "geometry"]],
            admin2_overlay,
            how="intersection",
            keep_geom_type=False,
        )
        geo_n_admin2_overlap = int(overlap["adm2_pcode"].nunique())
        geo_n_admin2_flood_overlap = int(
            overlap[overlap["adm2_pcode"].astype(str).isin(observed_pc)]["adm2_pcode"].nunique()
        )
        geo_groups_tbl = (
            overlap.groupby("group", as_index=False)
            .agg(n_admin2=("adm2_pcode", "nunique"))
            .merge(geo_gdf[["group", "intersects_flood_tile", "sqkm", "type"]], on="group", how="left")
        )
        geo_groups_tbl.to_csv(OUT / "join_feasibility_geoepr_admin2.csv", index=False)
    except Exception as exc:  # noqa: BLE001
        geo_error = str(exc)

    # ACLED admin1-week.
    ac = pd.read_excel(ACLED_PATH, usecols=["WEEK", "COUNTRY", "ADMIN1", "EVENTS", "FATALITIES"])
    ac = ac[ac["COUNTRY"].astype(str).str.contains("South Sudan", case=False, na=False)].copy()
    ac["WEEK"] = pd.to_datetime(ac["WEEK"], errors="coerce")
    ac["year"] = ac["WEEK"].dt.year
    n_acled_rows = len(ac)
    n_acled_weeks = int(ac["WEEK"].nunique())
    n_acled_admin1 = int(ac["ADMIN1"].nunique())
    n_acled_admin1_weeks = int(ac.groupby(["ADMIN1", "WEEK"]).ngroups)
    a1_matched = a1_xw[_is_matched_pcode(a1_xw["cod_pcode"])]
    n_acled_admin1_matched = int(a1_matched["source_name"].nunique())
    # Flood must aggregate UP: admin1 with any flood-observed county.
    a1_flood = coverage.groupby("adm1_pcode", as_index=False).agg(
        n_counties=("adm2_pcode", "nunique"),
        n_flood_observed=("flood_observed", "sum"),
        mean_coverage=("flood_tile_coverage_share", "mean"),
    )
    n_admin1_with_flood = int((a1_flood["n_flood_observed"] > 0).sum())
    acled_years_in_flood = sorted(set(ac["year"].dropna().astype(int)) & flood_year_set)
    n_acled_state_weeks_flood_years = int(
        ac[ac["year"].isin(flood_year_set)].groupby(["ADMIN1", "WEEK"]).ngroups
    )

    # IPC name-join county-windows.
    ipc_map = xw[xw["source"] == "IPC"][["source_name", "cod_pcode", "match_method"]].drop_duplicates()
    ipc_map["matched"] = _is_matched_pcode(ipc_map["cod_pcode"])
    ipc_m = ipc.merge(ipc_map, left_on="county", right_on="source_name", how="left")
    ipc_m["start_date"] = pd.to_datetime(ipc_m["start_date"], errors="coerce", utc=True)
    ipc_m["year"] = ipc_m["start_date"].dt.year
    ipc_m["matched"] = ipc_m["matched"].fillna(False)
    ipc_m["flood_observed"] = ipc_m["cod_pcode"].astype(str).isin(observed_pc)
    n_ipc_windows = int(ipc_m["start_date"].nunique())
    n_ipc_county_windows = len(ipc_m)
    n_ipc_matched = int(ipc_m["matched"].sum())
    n_ipc_matched_flood = int((ipc_m["matched"] & ipc_m["flood_observed"]).sum())
    n_ipc_unmatched_names = int((~ipc_map["matched"]).sum())

    # FEWS × IPC overlap (name-joined county-windows where FEWS harvest year exists).
    ipc_fews_years = set(fews_years)
    n_ipc_with_fews_year = int(
        ipc_m[ipc_m["matched"] & ipc_m["year"].isin(ipc_fews_years)].shape[0]
    )

    joins: list[dict] = []

    joins.append(
        _join_row(
            join_id="flood_admin2_season__ocha_20251130",
            left="Flood masks (unusual/recurring) aggregated to admin2 for 2025",
            right="OCHA 20251130 snapshot",
            grain="admin2 × one snapshot (2025 season only)",
            keys="COD adm2_pcode = Admin2_PCODE",
            n=n_ocha25_assessed_flood,
            n_definition="counties with non-null People affected AND flood tile coverage_share>0",
            min_n=MIN_N_SNAPSHOT,
            classification=CLASS_TEST,
            coverage_note=(
                f"OCHA file has {int(ocha_latest['n_county_rows'])} county rows, "
                f"{int(ocha_latest['n_pcode_in_cod'])} COD P-codes, "
                f"{int(ocha_latest['n_affected_nonnull'])} non-null affected; "
                f"{n_ocha25_all_flood}/{n_cod} counties have flood tile overlap."
            ),
            caveat="Validation only, not training. NaN ≠ 0 (unassessed). Sparse affected cells are a selection process.",
            stage4_rule="OCHA for flood validation; DTM remains displacement stock.",
        )
    )
    # Other OCHA snapshots as one-date validation if they have P-codes.
    for _, row in ocha_prof.iterrows():
        if row["join_id"] == "OCHA_20251130":
            continue
        has_key = bool(row.get("has_cod_pcode_key"))
        n_snap = int(row["n_affected_nonnull"]) if pd.notna(row.get("n_affected_nonnull")) else 0
        if has_key:
            klass = CLASS_TEST
            caveat = (
                "Same-file snapshot validation only. Do not bind to 20251130 or other OCHA files. "
                "Assessed/verified figures; NaN ≠ 0."
            )
        else:
            klass = CLASS_OVER
            caveat = "No COD P-code column in this file; name join only. Mixed layout. Easy to over-interpret."
        joins.append(
            _join_row(
                join_id=f"flood_admin2_season__{row['join_id']}",
                left="Flood masks aggregated to admin2 for that snapshot year",
                right=f"{row['join_id']} ({row['file']})",
                grain=f"admin2 × snapshot {row['snapshot_date']} ({row['date_source']})",
                keys="Admin2 P-code" if has_key else f"county name via Stage 3 ({row.get('name_col')})",
                n=n_snap,
                n_definition="county rows with non-null affected count in that file (not yet intersected with tile coverage)",
                min_n=MIN_N_SNAPSHOT,
                classification=klass,
                coverage_note=(
                    f"n_county_rows={row.get('n_county_rows')}; "
                    f"n_unique_county_names={row.get('n_unique_county_names')}; "
                    f"n_pcode_in_cod={row.get('n_pcode_in_cod')}; "
                    f"n_affected_nonnull={row.get('n_affected_nonnull')}; assessed_yes={row.get('n_assessed_yes')}"
                ),
                caveat=caveat,
                stage4_rule="OCHA snapshots are not a continuous panel (Stage 4: overlapping, schema drift).",
            )
        )
    joins.append(
        _join_row(
            join_id="stack_five_ocha_as_timeseries",
            left="OCHA snapshot files (all five)",
            right="each other / flood panel",
            grain="incompatible county snapshots (not a panel)",
            keys="none reliable across files",
            n=5,
            n_definition="number of incompatible Excel snapshots",
            min_n=1,
            classification=CLASS_AVOID,
            coverage_note=f"Schemas differ; latest is 79 P-coded counties, 20122024 is a partial list ({int(ocha_prof.loc[ocha_prof['join_id']=='OCHA_20122024','n_county_rows'].iloc[0])} rows).",
            caveat="Definition drift and assessed-only missingness. Do not stack as a time series.",
            stage4_rule="OCHA_snapshot_2022 vs 2025: overlapping, not a continuous panel.",
        )
    )

    n_dtm_min_counties = int(dtm_prof["n_counties_in_cod"].min()) if len(dtm_prof) else 0
    joins.append(
        _join_row(
            join_id="flood_admin2__dtm_r13_16_pcode",
            left="Flood masks at admin2 (round-year window)",
            right="DTM mobility R13–R16 location stocks rolled to county",
            grain="admin2 × DTM round (location stock aggregated by County_INT_PCode)",
            keys="County_INT_PCode = COD adm2_pcode (P-codes from ~R13)",
            n=n_dtm_counties_flood,
            n_definition="R16 counties with P-code in COD and flood tile coverage_share>0",
            min_n=MIN_N_SNAPSHOT,
            classification=CLASS_TEST,
            coverage_note=(
                f"R13–R16 each have {n_dtm_min_counties} COD counties; "
                f"Abyei SS0001 missing. R16 locations={int(dtm16['n_locations'])}. "
                f"Point-in-polygon possible only in R16 (lat/lon on {n_dtm_xy} locations); R13–R15 have no coordinate columns."
            ),
            caveat=(
                "Stage 2 gate: *_ind_disaster is NOT flood-only (single Disaster bucket). "
                "Allowed as broad disaster-related displacement; flood-specific validation via OCHA snapshots."
            ),
            stage4_rule="Displacement stock = DTM IDP stock; OCHA for flood validation only.",
        )
    )
    joins.append(
        _join_row(
            join_id="flood_admin2_year__fews_harvest_ha",
            left="Flood masks aggregated to admin2-year (unusual and recurring kept separate)",
            right="FEWS CFSAM Area Harvested (ha), main harvest",
            grain="admin2 × harvest year (season_year)",
            keys="FEWS fnid → Stage 3 fews_fnid_to_admin2.csv → COD adm2_pcode",
            n=n_fews_cy_both,
            n_definition="distinct COD counties × FEWS harvest years with fnid matched and flood tile coverage_share>0",
            min_n=MIN_N_COUNTY_YEAR,
            classification=CLASS_TEST,
            coverage_note=(
                f"FEWS {n_fews_admin2} admin_2 names / {n_fews_fnid} fnids; "
                f"{n_fews_fnid_matched} fnids matched. Matched county-years={n_fews_cy_matched}; "
                f"well-covered (share>=0.9) county-years={n_fews_cy_well}. "
                f"Harvest years={fews_years}; calendar years with no FEWS row={fews_missing_years}. "
                f"Unmatched FEWS names={fews_unmatched_names}."
            ),
            caveat=(
                "2016 hole. 82 FEWS units vs 79 COD counties. Counties with coverage_share=0 are unobserved flood, "
                "not proven zero flood. Unusual ≠ severity. Pairing is admin2-year, not daily flood vs annual harvest."
            ),
            stage4_rule="Crop exposure: ASAP % OR FEWS ha (label roles if both). Food impact: FEWS production OR IPC.",
        )
    )
    joins.append(
        _join_row(
            join_id="daily_flood__annual_fews_without_window",
            left="Flood masks at native daily grain",
            right="FEWS annual main harvest",
            grain="mismatched (daily × annual)",
            keys="would still use fnid crosswalk",
            n=n_fews_cy_both,
            n_definition="same county-years as the annual join; grain is the problem, not n",
            min_n=MIN_N_COUNTY_YEAR,
            classification=CLASS_AVOID,
            coverage_note="n is large enough; the forbidden step is joining daily pixels to annual CFSAM without a predeclared seasonal window.",
            caveat="If a window is predeclared (e.g. calendar year or wet-season months), use flood_admin2_year__fews_harvest_ha instead.",
            stage4_rule="Same FEWS series; grain mismatch is the issue.",
        )
    )
    joins.append(
        _join_row(
            join_id="ucdp_ged_points__admin2_flood_seasonal",
            left="UCDP GED v26.1 events (SSD)",
            right="COD admin2 polygons, then flood admin2-month/season",
            grain="event → admin2 × month/season (then counts)",
            keys="sjoin(lat,lon) to admin2 polygons; NOT UCDP adm_2 names",
            n=n_ged_events_vs_flood,
            n_definition=(
                "SSD events with sjoin inside admin2, where_prec<=3 (ADM2 or better), "
                "date_prec<=4 (month or better), county flood-observed, year in flood parquet years"
            ),
            min_n=MIN_N_EVENTS,
            classification=CLASS_TEST,
            coverage_note=(
                f"SSD events={n_ged}; inside polygons={n_ged_in_poly}; "
                f"where_prec<=3={n_ged_admin2_ok}; +date_prec<=4={n_ged_seasonal}; "
                f"+date_prec<=3 (week or better)={n_ged_monthly}. "
                f"where_prec>=4 but point still falls in a county={n_ged_misleading_pip} (do not use as county events). "
                f"Filtered type-2 events={n_ged_type2_seasonal}. "
                f"Admin2-years with ≥1 filtered event={n_ged_county_years}; "
                f"zero-inflated panel size (flood-observed counties × 2011–2025 flood years)={n_panel_county_years_ged}."
            ),
            caveat=(
                "Filter date_prec and where_prec before any county model. Type 1/2/3 are different ontologies; "
                "communal channel is GED type-2 OR Non-State, not both (Stage 4 Spearman ~0.77)."
            ),
            stage4_rule="Violence: UCDP GED OR ACLED weekly admin1 (cross-check, do not sum).",
        )
    )
    joins.append(
        _join_row(
            join_id="geoepr_polygons__flood_admin2_exposure",
            left="GeoEPR 2021 SSD settlement polygons (n groups)",
            right="admin2 polygons and flood-tile footprint",
            grain="group polygon ∩ admin2 (static 2011–2021)",
            keys="spatial overlay; not UCDP side_a/side_b strings",
            n=geo_n_admin2_flood_overlap if pd.notna(geo_n_admin2_flood_overlap) else geo_n_groups,
            n_definition="admin2 with flood tile overlap that intersect at least one GeoEPR SSD group polygon",
            min_n=MIN_N_GEOEPR_GROUPS,
            classification=CLASS_TEST,
            coverage_note=(
                f"SSD groups={geo_n_groups}; groups intersecting flood tile bbox={geo_n_intersect_tile}; "
                f"admin2 intersecting any group={geo_n_admin2_overlap}; "
                f"of those with flood observation={geo_n_admin2_flood_overlap}. "
                + (f"ERROR: {geo_error}" if geo_error else "Polygons can overlap (codebook).")
            ),
            caveat="Settlement-area exposure only. Not ethnicity of conflict. Frozen 2011–2021.",
            stage4_rule="GeoEPR vs UCDP actors: overlapping strings, not a merge key.",
        )
    )
    joins.append(
        _join_row(
            join_id="geoepr_flood_as_ethnic_conflict_risk",
            left="GeoEPR ∩ flood share",
            right="interpreted as ethnic conflict risk / UCDP",
            grain="ecological (group area, not events)",
            keys="none valid",
            n=geo_n_groups,
            n_definition="SSD GeoEPR groups (universe, not a sample)",
            min_n=1,
            classification=CLASS_AVOID,
            coverage_note="Same overlay as exposure join; the forbidden step is the interpretation.",
            caveat="Ecological fallacy if paired with UCDP. Do not treat flooded settlement share as conflict risk.",
            stage4_rule="GeoEPR is settlement, not a conflict-event dataset.",
        )
    )
    joins.append(
        _join_row(
            join_id="acled_admin1_week__flood_state_week",
            left="ACLED weekly Africa aggregate (SSD)",
            right="Flood pixel counts aggregated UP to admin1-week",
            grain="admin1 × ISO week",
            keys="ACLED ADMIN1 → COD adm1 via crosswalks/admin1_names.csv; never disaggregate ACLED to county",
            n=n_acled_state_weeks_flood_years,
            n_definition="SSD ADMIN1-week rows in years that have flood parquet files",
            min_n=MIN_N_ADMIN1_WEEK,
            classification=CLASS_OVER,
            coverage_note=(
                f"ACLED SSD rows={n_acled_rows}; distinct weeks={n_acled_weeks}; "
                f"admin1={n_acled_admin1} (matched {n_acled_admin1_matched}/{len(admin1)}); "
                f"admin1-weeks={n_acled_admin1_weeks}; admin1 with ≥1 flood-observed county={n_admin1_with_flood}. "
                f"No actors, no admin2, no event coordinates."
            ),
            caveat="Loses county targeting. Not an ethnic dataset. Sensitivity / tempo only.",
            stage4_rule="Do not add ACLED fatalities to UCDP best. One violence series per model.",
        )
    )
    joins.append(
        _join_row(
            join_id="add_acled_fatalities_plus_ucdp_best",
            left="ACLED FATALITIES (admin1-week)",
            right="UCDP GED best deaths",
            grain="incompatible fatality accounting",
            keys="none",
            n=n_acled_admin1_weeks,
            n_definition="ACLED admin1-weeks (UCDP is a different event universe)",
            min_n=1,
            classification=CLASS_AVOID,
            coverage_note="Both series are non-empty; non-additivity is the Stage 4 rule, not a sample-size issue.",
            caveat="Different inclusion rules (lethal vs any event; ≥1 vs weekly aggregates). Do not sum.",
            stage4_rule="ACLED fatalities vs UCDP best: overlapping, never add.",
        )
    )
    joins.append(
        _join_row(
            join_id="ipc_name_join__flood_or_fews",
            left="IPC Phase 3+ county-window (course processed long file)",
            right="Flood admin2 and/or FEWS harvest year",
            grain="county × 5 irregular windows",
            keys="IPC county name → Stage 3 admin2_names.csv → COD adm2_pcode",
            n=n_ipc_matched_flood,
            n_definition="IPC county-window rows with matched COD pcode and flood tile coverage_share>0",
            min_n=MIN_N_COUNTY_YEAR,
            classification=CLASS_OVER,
            coverage_note=(
                f"windows={n_ipc_windows}; rows={n_ipc_county_windows}; matched={n_ipc_matched}; "
                f"unmatched IPC names={n_ipc_unmatched_names}; rows whose window year exists in FEWS={n_ipc_with_fews_year}."
            ),
            caveat="Committee consensus, not measured crop loss. Five dates only. Context, not an outcome to fit.",
            stage4_rule="Food impact: FEWS production OR IPC Phase 3+ (not both as independent outcomes).",
        )
    )
    joins.append(
        _join_row(
            join_id="fmr_reason_as_county_impact",
            left="DTM FMR (flow monitoring)",
            right="Flood / county impact layer",
            grain="FMP survey groups (not a county census)",
            keys="FMP geography, not nationally representative",
            n=None,
            n_definition="not computed (full FMR DB not re-read); Stage 1: 268,925 clean-DB rows",
            min_n=MIN_N_SNAPSHOT,
            classification=CLASS_AVOID,
            coverage_note="FMR Notes: FMP surveys are not nationally representative. Schema drifts across 34 monthly files.",
            caveat="Do not treat FMR reason as county flood impact. Do not add FMR flows to DTM mobility stocks.",
            stage4_rule="DTM stock vs FMR flows: independent constructs, not additive people.",
        )
    )
    joins.append(
        _join_row(
            join_id="dtm_fmr_plus_mobility_stocks_additive",
            left="DTM FMR group flows",
            right="DTM mobility IDP stock",
            grain="incompatible (flow vs stock)",
            keys="none",
            n=None,
            n_definition="not a valid sample; constructs differ",
            min_n=1,
            classification=CLASS_AVOID,
            coverage_note="Both families exist under data/; adding them would double-count or mix sampling frames.",
            caveat="Stocks ≠ flows. FMR is FMP-sampled.",
            stage4_rule="Independent constructs; do not add.",
        )
    )

    joins_df = pd.DataFrame(joins)
    joins_path = OUT / "join_feasibility.csv"
    joins_df.to_csv(joins_path, index=False)

    proceed = joins_df[joins_df["gate"] == "proceed"]
    caveat_rows = joins_df[joins_df["gate"] == "proceed_with_caveat"]
    stopped = joins_df[joins_df["gate"] == "stop_n_too_small"]
    avoided = joins_df[joins_df["gate"] == "avoid"]

    xw_counts = (
        xw.assign(matched=_is_matched_pcode(xw["cod_pcode"]))
        .groupby("source", as_index=False)
        .agg(n_names=("source_name", "nunique"), n_matched=("matched", "sum"))
    )

    md_path = OUT / "join_feasibility.md"
    lines = [
        "# Stage 5 — Join feasibility",
        "",
        "Goal: classify each intended join as **technically possible and meaningful to test**, "
        "**technically possible but easy to over-interpret**, or **avoid unless a specific audit question**. "
        "Counts below are **observation** from files plus Stage 3 crosswalks. Classifications are **interpretation** "
        "using Stage 2 semantics, Stage 4 channel rules, and predeclared minimum-n floors.",
        "",
        "Working Stage 4 channel picks (team review still open): unusual **or** recurring flood; "
        "ASAP % **or** FEWS ha; FEWS production **or** IPC; UCDP GED **or** ACLED admin1; "
        "Non-State **or** GED type-2; DTM IDP stock with OCHA as flood validation only.",
        "",
        "## Minimum-n floors (predeclared)",
        "",
        f"- County-year / county-season panel: **n ≥ {MIN_N_COUNTY_YEAR}**",
        f"- Snapshot (OCHA / DTM round): **n ≥ {MIN_N_SNAPSHOT}** assessed or matched counties",
        f"- Event-level after precision filters: **n ≥ {MIN_N_EVENTS}**",
        f"- Admin1-week: **n ≥ {MIN_N_ADMIN1_WEEK}**",
        f"- GeoEPR overlay: **n ≥ {MIN_N_GEOEPR_GROUPS}** groups or admin2 overlaps",
        "",
        "If n is below the floor, `gate=stop_n_too_small` and that direction **stops** until more coverage exists.",
        "",
        "## Flood coverage used for every flood join",
        "",
        "**Observation:** flood pixel rows are **not** resampled here. Coverage is admin2 ∩ the h20v08+h21v08 tile bbox "
        f"(lon {FLOOD_TILE_EXTENT['lon_min']}–{FLOOD_TILE_EXTENT['lon_max']}, "
        f"lat {FLOOD_TILE_EXTENT['lat_min']}–{FLOOD_TILE_EXTENT['lat_max']}), same as `eda/revised_spatial_eda.py`. "
        f"Pixel area constant for later pixel-day sums: **{FLOOD_PIXEL_AREA_KM2} km²**. "
        "Unusual and recurring stay separate; unusual ≠ severity.",
        "",
        f"- Compact parquet years unusual: {unusual_years[0]}–{unusual_years[-1]} ({len(unusual_years)} years).",
        f"- Compact parquet years recurring: {recurring_years[0]}–{recurring_years[-1]} ({len(recurring_years)} years).",
        f"- COD admin2 units: **{n_cod}**.",
        f"- Counties with flood tile coverage_share > 0 (**flood observed**): **{n_flood_obs}**.",
        f"- Counties with coverage_share ≥ 0.9 (**well covered**): **{n_flood_well}**.",
        "",
        "**Interpretation:** coverage_share = 0 means the mask does not see that county, not that flood is zero.",
        "",
        "Counties with coverage_share = 0:",
        "",
        _md_table(zero_cov.reset_index(drop=True)) if len(zero_cov) else "- none",
        "",
        "Counties with 0 < coverage_share < 0.5:",
        "",
        _md_table(low_cov.round({"flood_tile_coverage_share": 3}).reset_index(drop=True))
        if len(low_cov)
        else "- none",
        "",
        f"Full table: `{coverage_path.name}`.",
        "",
        "## Stage 3 match reminder (names, not joins)",
        "",
        _md_table(xw_counts),
        "",
        "Unmatched units stay unmatched (`crosswalks/admin2_unmatched.csv`). Do not force-join.",
        "",
        "## Master classification",
        "",
        _md_table(
            joins_df,
            [
                "join_id",
                "classification",
                "gate",
                "n",
                "min_n",
                "grain",
            ],
        ),
        "",
        f"- **proceed** (meaningful, n ok): {len(proceed)}",
        f"- **proceed_with_caveat** (over-interpret, n ok): {len(caveat_rows)}",
        f"- **stop_n_too_small**: {len(stopped)}",
        f"- **avoid**: {len(avoided)}",
        "",
        "CSV: `join_feasibility.csv`.",
        "",
        "## Meaningful to test (if gate=proceed)",
        "",
    ]
    for _, row in proceed.iterrows():
        lines.extend(
            [
                f"### `{row['join_id']}`",
                "",
                f"- **Class:** {row['classification']}",
                f"- **Grain:** {row['grain']}",
                f"- **Keys:** {row['keys']}",
                f"- **n = {row['n']}** ({row['n_definition']}); min_n={row['min_n']}; **gate={row['gate']}**",
                f"- **Coverage:** {row['coverage_note']}",
                f"- **Caveat:** {row['caveat']}",
                f"- **Stage 4 rule:** {row['stage4_channel_rule']}",
                "",
            ]
        )
    if len(stopped):
        lines.extend(["## Stopped: n below floor", ""])
        for _, row in stopped.iterrows():
            lines.extend(
                [
                    f"### `{row['join_id']}`",
                    "",
                    f"- n={row['n']} < min_n={row['min_n']} — **this direction stops**.",
                    f"- {row['n_definition']}",
                    f"- {row['coverage_note']}",
                    "",
                ]
            )
    lines.extend(
        [
            "## Technically possible but easy to over-interpret",
            "",
        ]
    )
    for _, row in caveat_rows.iterrows():
        lines.extend(
            [
                f"### `{row['join_id']}`",
                "",
                f"- **Grain:** {row['grain']}",
                f"- **Keys:** {row['keys']}",
                f"- **n = {row['n']}** ({row['n_definition']}); gate={row['gate']}",
                f"- **Coverage:** {row['coverage_note']}",
                f"- **Why over-interpret:** {row['caveat']}",
                "",
            ]
        )
    lines.extend(["## Avoid unless a specific audit question", ""])
    for _, row in avoided.iterrows():
        lines.extend(
            [
                f"### `{row['join_id']}`",
                "",
                f"- **Grain:** {row['grain']}",
                f"- **n / note:** {row['n']} — {row['n_definition']}",
                f"- **Why avoid:** {row['caveat']}",
                f"- {row['coverage_note']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Supporting tables",
            "",
            f"- `{coverage_path.name}` — admin2 flood-tile coverage share",
            f"- `{ocha_path.name}` — five OCHA snapshots (P-codes, assessed counts)",
            f"- `{dtm_path.name}` — DTM R13–R16 location/P-code/coordinate coverage",
            f"- `{fews_year_path.name}` — FEWS matched county counts by harvest year",
            f"- `{ucdp_prec_path.name}` — UCDP GED SSD counts by where_prec × date_prec",
            f"- `{ged_sjoin_path.name}` — UCDP point-in-polygon filter summary",
            "- `join_feasibility_geoepr_admin2.csv` — GeoEPR group × admin2 overlap counts (if overlay succeeded)",
            "",
            "## Uncertainty",
            "",
            "- Flood **pixel-day** county totals are not computed in this stage; n uses tile overlap × year files. "
            "Stage 6–7 should reuse `eda/revised_spatial_eda.py` (`flood_admin2_daily`) rather than resampling parquets again.",
            "- OCHA snapshot dates are taken from filenames / sheet titles, not a date column inside every workbook.",
            "- DTM R13–R15 have P-codes but **no lat/lon**; PIP is R16-only.",
            "- GeoEPR overlay reports intersection counts, not flooded area shares (that would be Stage 7 exposure, still not conflict).",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def _asap_zonal_admin2(force: bool = False) -> tuple[pd.DataFrame, str]:
    """Mean/median ASAP crop and rangeland % for every COD admin2. Cached; no flood join."""
    cache = OUT / "stage6_asap_zonal_admin2.csv"
    if cache.exists() and not force:
        return pd.read_csv(cache), ""
    try:
        import rasterio
        from rasterio.mask import mask as rio_mask
        from shapely.geometry import mapping
    except ImportError as exc:
        return pd.DataFrame(), f"rasterio not importable: {exc}"

    crop_tif = COURSE_RAW / "farmland" / "asap_mask_crop_v04.tif"
    range_tif = COURSE_RAW / "farmland" / "asap_mask_rangeland_v04.tif"
    if not crop_tif.exists() or not range_tif.exists():
        return pd.DataFrame(), f"ASAP tif missing (crop={crop_tif.exists()}, rangeland={range_tif.exists()})"

    admin2 = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson").to_crs(
        "EPSG:4326"
    )

    def zonal_one(tif_path: Path, prefix: str) -> pd.DataFrame:
        rows = []
        with rasterio.open(tif_path) as src:
            nodata = src.nodata
            gdf = admin2.to_crs(src.crs) if src.crs else admin2
            for _, row in gdf.iterrows():
                rec = {
                    "adm2_pcode": row["adm2_pcode"],
                    "adm2_name": row["adm2_name"],
                    "adm1_name": row["adm1_name"],
                    f"{prefix}_mean_pct": np.nan,
                    f"{prefix}_median_pct": np.nan,
                    f"{prefix}_frac_gt0": np.nan,
                    f"{prefix}_n_pixels": 0,
                }
                try:
                    arr, _ = rio_mask(src, [mapping(row.geometry)], crop=True, filled=False)
                    data = arr[0]
                    vals = (
                        np.array(data.compressed(), dtype=float)
                        if np.ma.isMaskedArray(data)
                        else np.asarray(data, dtype=float).ravel()
                    )
                    if nodata is not None:
                        vals = vals[vals != nodata]
                    vals = vals[np.isfinite(vals)]
                    if len(vals):
                        rec[f"{prefix}_mean_pct"] = float(np.mean(vals))
                        rec[f"{prefix}_median_pct"] = float(np.median(vals))
                        rec[f"{prefix}_frac_gt0"] = float(np.mean(vals > 0))
                        rec[f"{prefix}_n_pixels"] = int(len(vals))
                except Exception:  # noqa: BLE001
                    pass
                rows.append(rec)
        return pd.DataFrame(rows)

    crop = zonal_one(crop_tif, "crop")
    rang = zonal_one(range_tif, "rangeland")
    out = crop.merge(
        rang.drop(columns=["adm2_name", "adm1_name"]),
        on="adm2_pcode",
        how="outer",
    )
    out.to_csv(cache, index=False)
    return out, ""


def _stage6_figdir() -> Path:
    d = OUT / "figures" / "stage6"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_obs_fig(fig, name: str, title: str) -> Path:
    import matplotlib.pyplot as plt

    fig.suptitle(f"Observation (not interpreted): {title}", fontsize=11)
    fig.tight_layout()
    path = _stage6_figdir() / name
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return path


def _flood_county_year(years: list[int], kind: str = "unusual") -> pd.DataFrame:
    """Unique flood pixel counts per admin2-year (unusual or recurring)."""
    if kind not in {"unusual", "recurring"}:
        raise ValueError(kind)
    col = f"{kind}_unique_px"
    admin2 = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson").to_crs(
        "EPSG:4326"
    )
    tiles = ["h20v08", "h21v08"]
    out = []
    folder = COURSE_RAW / "flood_masks" / f"compact_{kind}"
    for year in years:
        parts = []
        for tile in tiles:
            p = folder / f"flood_events_{tile}_{year}.parquet"
            if not p.exists():
                continue
            parts.append(pd.read_parquet(p, columns=["lat", "lon"]))
        if not parts:
            continue
        pts = pd.concat(parts, ignore_index=True).drop_duplicates()
        gdf = gpd.GeoDataFrame(
            pts,
            geometry=gpd.points_from_xy(pts["lon"], pts["lat"]),
            crs="EPSG:4326",
        )
        joined = gpd.sjoin(
            gdf,
            admin2[["adm2_name", "adm2_pcode", "geometry"]],
            how="inner",
            predicate="within",
        )
        cnt = (
            joined.groupby(["adm2_pcode", "adm2_name"], as_index=False)
            .size()
            .rename(columns={"size": col})
        )
        cnt["year"] = year
        out.append(cnt)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def _flood_unusual_by_county_year(years: list[int]) -> pd.DataFrame:
    return _flood_county_year(years, kind="unusual")


def _spearman_rank(x: pd.Series, y: pd.Series) -> float:
    frame = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(frame) < 5:
        return np.nan
    return float(frame["x"].rank().corr(frame["y"].rank()))


def _fews_harvest_admin2_year() -> pd.DataFrame:
    fews = pd.read_csv(EXT_DATA / "FEWS_crop_data" / "crop_data.csv")
    xw = pd.read_csv(CROSS / "admin2_names.csv")
    fews_map = xw[xw["source"] == "FEWS"][["source_name", "cod_pcode"]].drop_duplicates()
    fews_map = fews_map[_is_matched_pcode(fews_map["cod_pcode"])]
    harvest = fews[fews["indicator"] == "Area Harvested"].copy()
    produced = fews[fews["indicator"] == "Quantity Produced"].copy()
    harvest["year"] = harvest["season_year"].str.extract(r"(\d{4})").astype(int)
    produced["year"] = produced["season_year"].str.extract(r"(\d{4})").astype(int)
    harvest = harvest.merge(fews_map, left_on="admin_2", right_on="source_name", how="left")
    produced = produced.merge(fews_map, left_on="admin_2", right_on="source_name", how="left")
    ha = harvest.groupby(["cod_pcode", "year"], as_index=False)["value"].sum().rename(
        columns={"cod_pcode": "adm2_pcode", "value": "ha_harvested"}
    )
    qty = produced.groupby(["cod_pcode", "year"], as_index=False)["value"].sum().rename(
        columns={"cod_pcode": "adm2_pcode", "value": "qty_produced_t"}
    )
    return ha.merge(qty, on=["adm2_pcode", "year"], how="outer")


def _ged_admin2_year_counts(
    ged: pd.DataFrame,
    type_filter: set[int] | None = None,
    date_prec_max: int | None = 3,
) -> pd.DataFrame:
    """Event counts per admin2-year after point-in-polygon (lat/lon)."""
    if ged.empty:
        return pd.DataFrame(columns=["adm2_pcode", "year", "n_events"])
    work = ged.copy()
    if type_filter is not None:
        work = work[work["type_of_violence"].isin(type_filter)]
    if date_prec_max is not None and "date_prec" in work.columns:
        work = work[pd.to_numeric(work["date_prec"], errors="coerce") <= date_prec_max]
    work = work[pd.to_numeric(work["latitude"], errors="coerce").notna()]
    work = work[pd.to_numeric(work["longitude"], errors="coerce").notna()]
    if work.empty:
        return pd.DataFrame(columns=["adm2_pcode", "year", "n_events"])
    admin2 = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson").to_crs(
        "EPSG:4326"
    )
    gdf = gpd.GeoDataFrame(
        work,
        geometry=gpd.points_from_xy(work["longitude"], work["latitude"]),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(gdf, admin2[["adm2_pcode", "geometry"]], how="inner", predicate="within")
    return (
        joined.groupby(["adm2_pcode", "year"], as_index=False)
        .size()
        .rename(columns={"size": "n_events"})
    )


def _asap_mean_on_flood_pixels(
    years: list[int],
    kind: str = "unusual",
    max_points_per_year: int = 25_000,
) -> tuple[pd.DataFrame, str]:
    """
    Mean ASAP crop % at unique flood pixel locations (not county zonal).
    Returns admin2-year and national-year aggregates.
    """
    try:
        import rasterio
    except ImportError as exc:
        return pd.DataFrame(), f"rasterio not importable: {exc}"
    crop_tif = COURSE_RAW / "farmland" / "asap_mask_crop_v04.tif"
    if not crop_tif.exists():
        return pd.DataFrame(), "ASAP crop tif missing"

    admin2 = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson").to_crs(
        "EPSG:4326"
    )
    folder = COURSE_RAW / "flood_masks" / f"compact_{kind}"
    tiles = ["h20v08", "h21v08"]
    rows = []
    with rasterio.open(crop_tif) as src:
        nodata = src.nodata
        for year in years:
            parts = []
            for tile in tiles:
                p = folder / f"flood_events_{tile}_{year}.parquet"
                if p.exists():
                    parts.append(pd.read_parquet(p, columns=["lat", "lon"]))
            if not parts:
                continue
            pts = pd.concat(parts, ignore_index=True).drop_duplicates()
            if len(pts) > max_points_per_year:
                pts = pts.sample(max_points_per_year, random_state=year)
            gdf = gpd.GeoDataFrame(
                pts,
                geometry=gpd.points_from_xy(pts["lon"], pts["lat"]),
                crs="EPSG:4326",
            )
            joined = gpd.sjoin(
                gdf,
                admin2[["adm2_pcode", "geometry"]],
                how="inner",
                predicate="within",
            )
            if joined.empty:
                continue
            coords = [(float(r.lon), float(r.lat)) for r in joined.itertuples()]
            samples = [v[0] for v in src.sample(coords)]
            joined = joined.reset_index(drop=True)
            joined["crop_pct"] = pd.to_numeric(samples, errors="coerce")
            if nodata is not None:
                joined.loc[joined["crop_pct"] == nodata, "crop_pct"] = np.nan
            joined["year"] = year
            joined["flood_kind"] = kind
            rows.append(joined[["adm2_pcode", "year", "flood_kind", "crop_pct"]])
    if not rows:
        return pd.DataFrame(), "no flood pixels sampled"
    long = pd.concat(rows, ignore_index=True)
    by_cy = (
        long.groupby(["adm2_pcode", "year", "flood_kind"], as_index=False)["crop_pct"]
        .mean()
        .rename(columns={"crop_pct": "mean_crop_pct_on_flood_px"})
    )
    by_cy.to_csv(OUT / f"stage7_asap_on_{kind}_flood_px_admin2_year.csv", index=False)
    return by_cy, ""


def _five_part_block(
    title: str,
    observation: str,
    interpretation: str,
    alternatives: str,
    contradicting: str,
    next_test: str,
) -> list[str]:
    return [
        f"### {title}",
        "",
        f"1. **Observation:** {observation}",
        f"2. **Interpretation (tentative):** {interpretation}",
        f"3. **Alternative explanations:** {alternatives}",
        f"4. **Contradicting evidence:** {contradicting}",
        f"5. **Next test:** {next_test}",
        "",
    ]


def run_stage6_independent() -> Path:
    """Each family alone. Plots labelled observation-only. No flood-association tests."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xw = pd.read_csv(CROSS / "admin2_names.csv")
    admin2 = pd.read_csv(PROCESSED_DIR / "Administrative boundaries" / "ssd_admin2_processed.csv")
    admin2_gdf = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson").to_crs(
        "EPSG:4326"
    )

    fews = pd.read_csv(EXT_DATA / "FEWS_crop_data" / "crop_data.csv")
    fews["year"] = fews["season_year"].str.extract(r"(\d{4})").astype("Int64")
    harvest = fews[fews["indicator"] == "Area Harvested"].copy()
    produced = fews[fews["indicator"] == "Quantity Produced"].copy()
    yld = fews[fews["indicator"] == "Yield"].copy()
    by_state = (
        harvest.groupby(["season_year", "year", "admin_1"], as_index=False)["value"]
        .sum()
        .rename(columns={"value": "ha_harvested"})
    )
    by_state.to_csv(OUT / "stage6_fews_harvest_by_state_year.csv", index=False)

    nat = harvest.groupby("year")["value"].sum()
    year_index = pd.Index(
        range(int(harvest["year"].min()), int(harvest["year"].max()) + 1), name="year"
    )
    nat_tbl = nat.reindex(year_index).reset_index(name="ha_harvested")
    nat_tbl.to_csv(OUT / "stage6_fews_harvest_national_year.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(nat_tbl["year"].astype(int), nat_tbl["ha_harvested"].fillna(0), color="#4a7ba7")
    missing = nat_tbl[nat_tbl["ha_harvested"].isna()]
    if len(missing):
        ax.scatter(
            missing["year"].astype(int),
            np.zeros(len(missing)),
            marker="x",
            color="#c75b39",
            s=60,
            label="no rows (gap)",
        )
        ax.legend()
    ax.set_xlabel("harvest year")
    ax.set_ylabel("Area harvested (ha), national sum")
    _save_obs_fig(fig, "fews_harvest_national_year.png", "FEWS CFSAM mixed-cereal harvested area")

    area_y = harvest.rename(columns={"value": "ha_harvested"})[
        ["fnid", "admin_1", "admin_2", "year", "ha_harvested"]
    ]
    yld_y = yld.rename(columns={"value": "yield_mt_ha"})[["fnid", "year", "yield_mt_ha"]]
    prod_y = produced.rename(columns={"value": "qty_produced_t"})[["fnid", "year", "qty_produced_t"]]
    ay = area_y.merge(yld_y, on=["fnid", "year"], how="inner").merge(
        prod_y, on=["fnid", "year"], how="left"
    )
    ay.to_csv(OUT / "stage6_fews_yield_vs_area.csv", index=False)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(ay["ha_harvested"], ay["yield_mt_ha"], alpha=0.35, s=12, c="#2f6f9f")
    ax.set_xlabel("Area harvested (ha)")
    ax.set_ylabel("Yield (MT/ha)")
    _save_obs_fig(fig, "fews_yield_vs_area.png", "FEWS county-year yield vs harvested area")

    n_fews_years = sorted(int(y) for y in harvest["year"].dropna().unique())
    fews_gap = sorted(set(range(min(n_fews_years), max(n_fews_years) + 1)) - set(n_fews_years))

    asap, asap_err = _asap_zonal_admin2(force=False)
    if len(asap):
        fig, ax = plt.subplots(figsize=(8, 8))
        g = admin2_gdf.merge(asap, on="adm2_pcode", how="left")
        g.plot(
            column="crop_mean_pct",
            ax=ax,
            legend=True,
            cmap="YlGn",
            missing_kwds={"color": "lightgrey", "label": "no data"},
        )
        ax.set_axis_off()
        _save_obs_fig(fig, "map_asap_crop_mean.png", "ASAP crop % mean, all COD admin2")
        top = asap.sort_values("crop_mean_pct", ascending=False).head(20)
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.barh(top["adm2_name"][::-1], top["crop_mean_pct"][::-1], color="#3b8f55")
        ax.set_xlabel("mean crop % of pixel")
        _save_obs_fig(fig, "asap_crop_mean_top20.png", "Highest ASAP mean crop % counties")

    type_map = {1: "state-based (1)", 2: "non-state (2)", 3: "one-sided (3)"}
    ged = _load_ged_ssd()
    ged["type_label"] = ged["type_of_violence"].map(type_map)
    ged_y = (
        ged.groupby(["year", "type_of_violence", "type_label"], as_index=False)
        .size()
        .rename(columns={"size": "n_events"})
    )
    ged_y.to_csv(OUT / "stage6_ucdp_events_by_year_type.csv", index=False)
    type_totals = ged["type_of_violence"].value_counts().sort_index()
    pivot = ged_y.pivot_table(index="year", columns="type_label", values="n_events", fill_value=0)
    fig, ax = plt.subplots(figsize=(8, 4))
    pivot.plot(kind="bar", stacked=True, ax=ax, width=0.85)
    ax.set_ylabel("events")
    ax.set_xlabel("year")
    _save_obs_fig(fig, "ucdp_ged_type_by_year.png", "UCDP GED SSD events by type_of_violence")

    type2 = ged[ged["type_of_violence"] == 2]
    dyad_ged = (
        type2.groupby(["side_a", "side_b"], as_index=False)
        .size()
        .rename(columns={"size": "n_events"})
        .sort_values("n_events", ascending=False)
    )
    dyad_ged.to_csv(OUT / "stage6_ucdp_ged_type2_sides.csv", index=False)

    ns = pd.read_csv(
        EXT_DATA / "UCDP_georeferenced_and_nonstate" / "ucdp-nonstate-261-csv" / "NonState_v26_1.csv"
    )
    ns_ssd = ns[
        ns["location"].astype(str).str.contains("South Sudan", case=False, na=False)
        | ns["gwno_location"].astype(str).str.contains("626", na=False)
    ].copy()
    ns_cols = [
        c
        for c in [
            "year",
            "org",
            "side_a_name",
            "side_b_name",
            "best_fatality_estimate",
            "location",
        ]
        if c in ns_ssd.columns
    ]
    ns_ssd[ns_cols].sort_values(["year", "best_fatality_estimate"], ascending=[True, False]).to_csv(
        OUT / "stage6_ucdp_nonstate_dyads.csv", index=False
    )
    ns_dyad_n = (
        ns_ssd.groupby(["side_a_name", "side_b_name"], as_index=False)
        .size()
        .rename(columns={"size": "n_dyad_years"})
        .sort_values("n_dyad_years", ascending=False)
    )
    ns_dyad_n.to_csv(OUT / "stage6_ucdp_nonstate_dyad_counts.csv", index=False)
    n_ns_org3 = int((ns_ssd["org"] == 3).sum()) if "org" in ns_ssd.columns else np.nan

    ac = pd.read_excel(
        ACLED_PATH,
        usecols=["WEEK", "COUNTRY", "ADMIN1", "EVENT_TYPE", "EVENTS", "FATALITIES"],
    )
    ssd = ac[ac["COUNTRY"].astype(str).str.contains("South Sudan", case=False, na=False)].copy()
    ssd["WEEK"] = pd.to_datetime(ssd["WEEK"], errors="coerce")
    ssd["year"] = ssd["WEEK"].dt.year
    ac_y = ssd.groupby(["year", "EVENT_TYPE"], as_index=False)["EVENTS"].sum()
    ac_y.to_csv(OUT / "stage6_acled_events_by_year_type.csv", index=False)
    ac_state = ssd.groupby(["ADMIN1", "EVENT_TYPE"], as_index=False)["EVENTS"].sum()
    ac_state.to_csv(OUT / "stage6_acled_events_by_admin1_type.csv", index=False)
    ac_pivot = ac_y.pivot_table(index="year", columns="EVENT_TYPE", values="EVENTS", fill_value=0)
    fig, ax = plt.subplots(figsize=(8, 4))
    ac_pivot.plot(kind="bar", stacked=True, ax=ax, width=0.85)
    ax.set_ylabel("EVENTS (weekly aggregate sum)")
    _save_obs_fig(fig, "acled_event_type_by_year.png", "ACLED SSD weekly aggregates by EVENT_TYPE")

    r16_path = EXT_DATA / "IOM_DTM_mobility" / DTM_R13_16_FILES[16]
    header = pd.read_excel(r16_path, sheet_name="MT R16 Baseline_Loc_Dataset", nrows=0)
    wanted = {"County_INT_PCode", "county_name", "a_idp_inds_ssd"}
    usecols = [
        c
        for c in header.columns
        if c in wanted or str(c).endswith(("_ind_disaster", "_ind_conflict", "_ind_clashes"))
    ]
    r16 = pd.read_excel(r16_path, sheet_name="MT R16 Baseline_Loc_Dataset", usecols=usecols)
    r16 = _drop_hxl(r16)
    r16["a_idp_inds_ssd"] = pd.to_numeric(r16["a_idp_inds_ssd"], errors="coerce")
    r16["County_INT_PCode"] = r16["County_INT_PCode"].astype(str).str.strip()
    dis_cols = [c for c in r16.columns if str(c).endswith("_ind_disaster")]
    con_cols = [c for c in r16.columns if str(c).endswith("_ind_conflict")]
    cla_cols = [c for c in r16.columns if str(c).endswith("_ind_clashes")]
    for cols, name in [(dis_cols, "_dis_arr"), (con_cols, "_con_arr"), (cla_cols, "_cla_arr")]:
        r16[name] = 0.0
        for col in cols:
            r16[name] = r16[name] + pd.to_numeric(r16[col], errors="coerce").fillna(0)
    dtm_c = r16.groupby(["County_INT_PCode", "county_name"], as_index=False).agg(
        n_locations=("a_idp_inds_ssd", "size"),
        idp_stock=("a_idp_inds_ssd", "sum"),
        disaster_arrival_ind=("_dis_arr", "sum"),
        conflict_arrival_ind=("_con_arr", "sum"),
        clashes_arrival_ind=("_cla_arr", "sum"),
    )
    dtm_c = dtm_c.merge(
        admin2[["pcode", "name"]].rename(columns={"pcode": "County_INT_PCode", "name": "cod_name"}),
        on="County_INT_PCode",
        how="left",
    )
    dtm_c.to_csv(OUT / "stage6_dtm_r16_county_stock.csv", index=False)
    top_idp = dtm_c.sort_values("idp_stock", ascending=False).head(20)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top_idp["county_name"][::-1], top_idp["idp_stock"][::-1], color="#6b4c7a")
    ax.set_xlabel("IDP individuals (location stock sum)")
    _save_obs_fig(fig, "dtm_r16_idp_stock_top20.png", "DTM R16 IDP stock by county")
    fig, ax = plt.subplots(figsize=(8, 8))
    g = admin2_gdf.merge(
        dtm_c.rename(columns={"County_INT_PCode": "adm2_pcode"}),
        on="adm2_pcode",
        how="left",
    )
    g.plot(
        column="idp_stock",
        ax=ax,
        legend=True,
        cmap="Purples",
        missing_kwds={"color": "lightgrey", "label": "no DTM county"},
    )
    ax.set_axis_off()
    _save_obs_fig(fig, "map_dtm_r16_idp_stock.png", "DTM R16 IDP stock (Abyei absent)")

    ocha25 = pd.read_excel(
        EXT_DATA / "OCHA_flood_data" / "ss_people_affected_and_displaced_by_floods_20251130.xlsx"
    )
    aff_col = _find_col(ocha25, "affected", exclude=("peaple",))
    dis_col = _find_col(ocha25, "displaced", "peaple")
    ocha25["Admin2_PCODE"] = ocha25["Admin2_PCODE"].astype(str).str.strip()
    ocha25["people_affected"] = pd.to_numeric(ocha25[aff_col], errors="coerce") if aff_col else np.nan
    ocha25["people_displaced"] = pd.to_numeric(ocha25[dis_col], errors="coerce") if dis_col else np.nan
    ocha25["assessed_affected"] = ocha25["people_affected"].notna()
    ocha_out = ocha25[
        ["Admin1", "Admin2", "Admin2_PCODE", "people_affected", "people_displaced", "assessed_affected"]
    ]
    ocha_out.to_csv(OUT / "stage6_ocha_20251130_county.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 8))
    g = admin2_gdf.merge(
        ocha_out.rename(columns={"Admin2_PCODE": "adm2_pcode"}),
        on="adm2_pcode",
        how="left",
    )
    g.plot(
        column="people_affected",
        ax=ax,
        legend=True,
        cmap="OrRd",
        missing_kwds={"color": "lightgrey", "label": "unassessed (NaN ≠ 0)"},
    )
    ax.set_axis_off()
    _save_obs_fig(fig, "map_ocha_20251130_affected.png", "OCHA 20251130 people affected (NaN = unassessed)")
    n_ocha_aff = int(ocha25["assessed_affected"].sum())
    n_ocha_dis = int(ocha25["people_displaced"].notna().sum())

    ipc = pd.read_csv(PROCESSED_DIR / "IPC" / "ipc_phase3plus_county_long_processed.csv")
    ipc["start_date"] = pd.to_datetime(ipc["start_date"], errors="coerce", utc=True)
    ipc_win = ipc.groupby("start_date", as_index=False).agg(
        n_rows=("county", "size"),
        n_counties=("county", "nunique"),
        phase3plus_pop_sum=("phase3plus_population", "sum"),
    )
    ipc_win.to_csv(OUT / "stage6_ipc_window_totals.csv", index=False)

    geo = pd.read_csv(GEOEPR_PATH, usecols=["statename", "from", "to", "group", "type", "sqkm"])
    geo_ssd = geo[geo["statename"].astype(str).str.contains("South Sudan", case=False, na=False)].copy()
    geo_ssd.to_csv(OUT / "stage6_geoepr_groups.csv", index=False)
    geo_ov_path = OUT / "join_feasibility_geoepr_admin2.csv"
    geo_ov = pd.read_csv(geo_ov_path) if geo_ov_path.exists() else pd.DataFrame()

    md_path = OUT / "stage6_independent.md"
    lines = [
        "# Stage 6 — Independent EDA (observation-only)",
        "",
        "Each family is described **without** a flood-association test. Plot titles are labelled "
        "**Observation (not interpreted)**. Flood × crop and flood × conflict stay Stage 7.",
        "",
        "Figures: `outputs/impact_eda/figures/stage6/`.",
        "",
        "## Croplands — FEWS CFSAM",
        "",
        f"- **Observation:** mixed-cereal main harvest years {n_fews_years[0]}–{n_fews_years[-1]}; "
        f"calendar years with no row: **{fews_gap}**.",
        "- National harvested-area series: `stage6_fews_harvest_national_year.csv`. "
        "State-year: `stage6_fews_harvest_by_state_year.csv`.",
        f"- Yield vs area county-years: n={len(ay)}; file max yield still 2.0 MT/ha "
        f"({int((ay['yield_mt_ha']==2.0).sum())} rows at 2.0). Cap vs true max not verified (Stage 2).",
        "- **Not interpreted:** whether 2016 is a missing file year or a true agricultural zero.",
        "",
        "## Croplands — ASAP static zonal (all admin2)",
        "",
    ]
    if len(asap):
        lines.extend(
            [
                f"- **Observation:** zonal mean crop % over **{len(asap)}** COD admin2 polygons "
                "(not the unusual-pixel sample in `exposure_locals.ipynb`).",
                f"- Crop mean %: min={asap['crop_mean_pct'].min():.3f}, "
                f"median={asap['crop_mean_pct'].median():.3f}, max={asap['crop_mean_pct'].max():.3f}.",
                f"- Rangeland mean %: median={asap['rangeland_mean_pct'].median():.3f}.",
                f"- Counties with crop mean % = 0: **{int((asap['crop_mean_pct']==0).sum())}**; "
                f"with mean % > 0: **{int((asap['crop_mean_pct']>0).sum())}**.",
                "- Table: `stage6_asap_zonal_admin2.csv`. Map: `figures/stage6/map_asap_crop_mean.png`.",
                "- **Hypothesis (not tested here):** `exposure_locals.ipynb` mean crop % ≈ 0 on sampled "
                "**unusual** flood pixels may not hold for all-admin2 zonal means or for **recurring** flood. "
                "That overlay is Stage 7.",
                "",
            ]
        )
    else:
        lines.extend([f"- ASAP zonal **not computed**: {asap_err}", ""])
    lines.extend(
        [
            "## Recurring vs unusual flood area on cropland",
            "",
            "- **Not run in Stage 6.** That join is a flood×crop test (Stage 7 pre-registered check). "
            "Stage 6 only builds the all-admin2 ASAP table so Stage 7 need not unique-pixel sample.",
            "- Flood tile coverage (unobserved north) remains Stage 5: Manyo/Renk share=0.",
            "",
            "## Conflict — UCDP GED",
            "",
            f"- **Observation:** SSD events={len(ged)}. Type counts: "
            + ", ".join(f"{type_map.get(int(k), k)}={int(v)}" for k, v in type_totals.items())
            + ".",
            f"- Type-2 (non-state) events={len(type2)}; distinct side_a/side_b pairs={len(dyad_ged)}.",
            "- Top type-2 pairs (event counts):",
            "",
            _md_table(dyad_ged.head(12), ["side_a", "side_b", "n_events"]) if len(dyad_ged) else "- none",
            "",
            "- **Not interpreted** as flood co-occurrence. ACLED VAC ≠ type 3 (Stage 2).",
            "",
            "## Conflict — UCDP Non-State (annual dyads, ≥25 deaths/year)",
            "",
            f"- **Observation:** SSD-related dyad-years={len(ns_ssd)}; org=3 (communal) rows={n_ns_org3}.",
            "- Most frequent dyads (count of years present):",
            "",
            _md_table(ns_dyad_n.head(12), ["side_a_name", "side_b_name", "n_dyad_years"])
            if len(ns_dyad_n)
            else "- none",
            "",
            "- Same channel as GED type-2 (Stage 4); do not use both as independent predictors.",
            "",
            "## Conflict — ACLED weekly admin1",
            "",
            f"- **Observation:** SSD rows={len(ssd)}; EVENT_TYPE mix in `stage6_acled_events_by_year_type.csv`.",
            "- **Not** an ethnic or county actor dataset. No actors, no admin2, no coordinates.",
            "",
            "## Displacement — DTM R16 (stock, no flood)",
            "",
            f"- **Observation:** locations={len(r16)}; counties={dtm_c['County_INT_PCode'].nunique()}; "
            f"national IDP stock sum={float(dtm_c['idp_stock'].sum()):,.0f}.",
            f"- Counties with disaster-arrival individuals > 0: "
            f"**{int((dtm_c['disaster_arrival_ind']>0).sum())}** "
            f"(arrival-period attribution, **not** flood-only — Stage 2).",
            "- Abyei SS0001 not in R16. Map: `figures/stage6/map_dtm_r16_idp_stock.png`.",
            "",
            "## Displacement — OCHA 20251130 snapshot",
            "",
            f"- **Observation:** 79 P-coded counties; non-null affected=**{n_ocha_aff}**; "
            f"non-null displaced=**{n_ocha_dis}**. Grey on the map is unassessed, not zero.",
            "- Do not stack with the other four OCHA files (Stage 5 avoid).",
            "",
            "## Food insecurity context — IPC",
            "",
            "- Five windows; Phase 3+ population sums (committee product, not measured crop loss):",
            "",
            _md_table(ipc_win) if len(ipc_win) else "- none",
            "",
            "## Settlement — GeoEPR 2021",
            "",
            f"- **Observation:** {len(geo_ssd)} SSD groups, all coded "
            f"`{geo_ssd['type'].iloc[0] if len(geo_ssd) else ''}`, window 2011–2021.",
            "",
            _md_table(
                geo_ssd.sort_values("sqkm", ascending=False),
                ["group", "sqkm", "type", "from", "to"],
            )
            if len(geo_ssd)
            else "- none",
            "",
            "- Polygons can overlap (codebook). This is **not** a conflict-event dataset. "
            "Admin2 overlap counts from Stage 5: `join_feasibility_geoepr_admin2.csv`"
            + (f" ({len(geo_ov)} group rows)." if len(geo_ov) else " (file missing)."),
            "",
            "## Uncertainty",
            "",
            "- ASAP zonal is an unweighted pixel mean inside the polygon (each raster cell equal). "
            "Not yet intersected with unusual or recurring flood pixels.",
            "- DTM disaster/conflict/clashes columns are period-of-arrival, not a partition of current stock.",
            "- FEWS 82 named units vs 79 COD counties; unmatched names stay unmatched.",
            f"- Stage 3 FEWS name rows used only as reminder (n unique FEWS names in crosswalk="
            f"{int((xw['source']=='FEWS').sum())}).",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def run_stage7_cross_dataset() -> Path:
    """Pre-registered stress-tests; five-part writeups. Not confirmation-driven."""
    years = [2022, 2023, 2024]
    checks: list[dict] = []
    writeup_blocks: list[str] = [
        "# Stage 7 — Cross-dataset checks (observation-first)",
        "",
        "Pre-registered checks from the impact EDA plan. Rank correlations and group "
        "comparisons are **not** causal. Confounders: flood tile coverage north of 10°N, "
        "OCHA assessed-only counties, FEWS annual vs flood daily, conflict/displacement.",
        "",
        "## Summary table",
        "",
    ]

    cache_u = OUT / "admin2_unusual_flood_2022_2024.csv"
    if cache_u.exists():
        flood_u = pd.read_csv(cache_u)
    else:
        flood_u = _flood_unusual_by_county_year(years)
        flood_u.to_csv(cache_u, index=False)
    flood_r = _flood_county_year(years, kind="recurring")
    flood_r.to_csv(OUT / "admin2_recurring_flood_2022_2024.csv", index=False)

    fews_panel = _fews_harvest_admin2_year()
    asap_zonal, asap_err = _asap_zonal_admin2(force=False)
    ged = _load_ged_ssd()
    ged_counts = _ged_admin2_year_counts(ged, type_filter=None, date_prec_max=3)
    ged_t2 = _ged_admin2_year_counts(ged, type_filter={2}, date_prec_max=3)

    # --- FEWS vs flood (unusual + recurring) ---
    for kind, flood_df, col in [
        ("unusual", flood_u, "unusual_unique_px"),
        ("recurring", flood_r, "recurring_unique_px"),
    ]:
        for year in years:
            f_y = flood_df[flood_df["year"] == year][["adm2_pcode", col]]
            h_y = fews_panel[fews_panel["year"] == year]
            m = f_y.merge(h_y, on="adm2_pcode", how="inner")
            r = _spearman_rank(m[col], m["ha_harvested"])
            checks.append(
                {
                    "check_id": f"flood_{kind}_px_vs_fews_ha",
                    "year": year,
                    "n_units": len(m),
                    "statistic": "spearman_r",
                    "value": r,
                    "detail": f"{col} vs ha_harvested; matched counties only",
                }
            )

    # FEWS vs flood split by UCDP violence (high vs low median events), pooled years
    panel = flood_u.merge(fews_panel, on=["adm2_pcode", "year"], how="inner").merge(
        ged_counts, on=["adm2_pcode", "year"], how="left"
    )
    panel["n_events"] = panel["n_events"].fillna(0)
    if len(panel) >= 10:
        med_v = float(panel["n_events"].median())
        if panel["n_events"].nunique() <= 1:
            med_v = float(panel["n_events"].max())
        if med_v <= 0:
            hi = panel[panel["n_events"] > 0]
            lo = panel[panel["n_events"] == 0]
        else:
            hi = panel[panel["n_events"] >= med_v]
            lo = panel[panel["n_events"] < med_v]
        r_hi = _spearman_rank(hi["unusual_unique_px"], hi["ha_harvested"])
        r_lo = _spearman_rank(lo["unusual_unique_px"], lo["ha_harvested"])
        checks.append(
            {
                "check_id": "fews_ha_vs_unusual_px_split_ucdp",
                "year": "2022-2024",
                "n_units": len(panel),
                "statistic": "spearman_r_high_ucdp",
                "value": r_hi,
                "detail": f"counties-years with n_events>={med_v}; n={len(hi)}",
            }
        )
        checks.append(
            {
                "check_id": "fews_ha_vs_unusual_px_split_ucdp",
                "year": "2022-2024",
                "n_units": len(panel),
                "statistic": "spearman_r_low_ucdp",
                "value": r_lo,
                "detail": f"counties-years with n_events<{med_v}; n={len(lo)}",
            }
        )
        low_flood_high_ha = int(
            ((panel["unusual_unique_px"] <= panel["unusual_unique_px"].median()) & (panel["ha_harvested"] > panel["ha_harvested"].median())).sum()
        )
        checks.append(
            {
                "check_id": "flood_low_but_fews_ha_high",
                "year": "2022-2024",
                "n_units": len(panel),
                "statistic": "n_county_years",
                "value": low_flood_high_ha,
                "detail": "below-median unusual px AND above-median ha (challenges flood-only crop loss)",
            }
        )

    # --- ASAP on flood pixels vs zonal ---
    asap_u, err_u = _asap_mean_on_flood_pixels(years, kind="unusual")
    asap_r, err_r = _asap_mean_on_flood_pixels(years, kind="recurring")
    for kind, tbl, err in [("unusual", asap_u, err_u), ("recurring", asap_r, err_r)]:
        if len(tbl):
            nat_mean = float(tbl["mean_crop_pct_on_flood_px"].mean())
            checks.append(
                {
                    "check_id": f"asap_crop_on_{kind}_flood_px",
                    "year": "2022-2024",
                    "n_units": len(tbl),
                    "statistic": "mean_crop_pct_on_flood_px",
                    "value": nat_mean,
                    "detail": "sampled unique flood pixels; see stage7_asap_on_* csv",
                }
            )
        else:
            checks.append(
                {
                    "check_id": f"asap_crop_on_{kind}_flood_px",
                    "year": "2022-2024",
                    "n_units": 0,
                    "statistic": "error",
                    "value": np.nan,
                    "detail": err or "no data",
                }
            )
    if len(asap_u) and len(asap_r):
        cmp = asap_u.merge(
            asap_r,
            on=["adm2_pcode", "year"],
            suffixes=("_unusual", "_recurring"),
        )
        checks.append(
            {
                "check_id": "asap_on_flood_unusual_minus_recurring",
                "year": "2022-2024",
                "n_units": len(cmp),
                "statistic": "mean_diff_crop_pct",
                "value": float(
                    (
                        cmp["mean_crop_pct_on_flood_px_unusual"]
                        - cmp["mean_crop_pct_on_flood_px_recurring"]
                    ).mean()
                ),
                "detail": "positive => higher crop signal on unusual flood pixels",
            }
        )

    if len(asap_zonal) and len(flood_u):
        z = asap_zonal.merge(
            flood_u.groupby("adm2_pcode", as_index=False)["unusual_unique_px"].sum(),
            on="adm2_pcode",
            how="left",
        )
        z["unusual_unique_px"] = z["unusual_unique_px"].fillna(0)
        with_flood = z[z["unusual_unique_px"] > 0]
        without = z[z["unusual_unique_px"] == 0]
        checks.append(
            {
                "check_id": "asap_zonal_mean_crop_pct",
                "year": "2022-2024 pooled",
                "n_units": len(z),
                "statistic": "mean_crop_pct_counties_with_unusual_px",
                "value": float(with_flood["crop_mean_pct"].mean()) if len(with_flood) else np.nan,
                "detail": f"n={len(with_flood)} counties with any unusual px 2022-24",
            }
        )
        checks.append(
            {
                "check_id": "asap_zonal_mean_crop_pct",
                "year": "2022-2024 pooled",
                "n_units": len(z),
                "statistic": "mean_crop_pct_counties_without_unusual_px",
                "value": float(without["crop_mean_pct"].mean()) if len(without) else np.nan,
                "detail": f"n={len(without)} counties with zero unusual px",
            }
        )

    # --- UCDP vs flood ---
    for label, gtab in [("ged_all_types", ged_counts), ("ged_type2", ged_t2)]:
        merged = flood_u.merge(gtab, on=["adm2_pcode", "year"], how="inner")
        for year in years:
            m = merged[merged["year"] == year]
            r_pos = _spearman_rank(m["unusual_unique_px"], m["n_events"])
            checks.append(
                {
                    "check_id": f"unusual_px_vs_{label}",
                    "year": year,
                    "n_units": len(m),
                    "statistic": "spearman_r_same_year",
                    "value": r_pos,
                    "detail": "date_prec<=3 only",
                }
            )
        # lag: flood year t vs events year t+1
        lag_rows = []
        for pcode in merged["adm2_pcode"].unique():
            sub = merged[merged["adm2_pcode"] == pcode].sort_values("year")
            for i in range(len(sub) - 1):
                lag_rows.append(
                    {
                        "unusual_unique_px": sub.iloc[i]["unusual_unique_px"],
                        "n_events_next": sub.iloc[i + 1]["n_events"],
                    }
                )
        lag_df = pd.DataFrame(lag_rows)
        r_lag = _spearman_rank(lag_df["unusual_unique_px"], lag_df["n_events_next"])
        checks.append(
            {
                "check_id": f"unusual_px_vs_{label}_lag_plus1",
                "year": "2022-2024",
                "n_units": len(lag_df),
                "statistic": "spearman_r",
                "value": r_lag,
                "detail": "flood year t vs violence year t+1",
            }
        )

    # ACLED admin1 sensitivity: state-year flood vs events
    a1_xw = pd.read_csv(CROSS / "admin1_names.csv")
    admin2 = pd.read_csv(PROCESSED_DIR / "Administrative boundaries" / "ssd_admin2_processed.csv")
    a1_col = "parent_pcode" if "parent_pcode" in admin2.columns else "adm1_pcode"
    pcode_to_a1 = admin2.set_index("pcode")[a1_col].to_dict()
    flood_state = flood_u.copy()
    flood_state["adm1_pcode"] = flood_state["adm2_pcode"].map(pcode_to_a1)
    flood_state_y = flood_state.groupby(["adm1_pcode", "year"], as_index=False)["unusual_unique_px"].sum()
    ac = pd.read_excel(ACLED_PATH, usecols=["WEEK", "COUNTRY", "ADMIN1", "EVENTS"])
    ssd = ac[ac["COUNTRY"].astype(str).str.contains("South Sudan", case=False, na=False)].copy()
    ssd["WEEK"] = pd.to_datetime(ssd["WEEK"], errors="coerce")
    ssd["year"] = ssd["WEEK"].dt.year
    ssd = ssd.merge(
        a1_xw.rename(columns={"source_name": "ADMIN1", "cod_pcode": "adm1_pcode"}),
        on="ADMIN1",
        how="left",
    )
    ssd = ssd[_is_matched_pcode(ssd["adm1_pcode"])]
    ac_y = ssd.groupby(["adm1_pcode", "year"], as_index=False)["EVENTS"].sum()
    ac_m = flood_state_y.merge(ac_y, on=["adm1_pcode", "year"], how="inner")
    for year in years:
        m = ac_m[ac_m["year"] == year]
        checks.append(
            {
                "check_id": "acled_admin1_events_vs_state_unusual_px",
                "year": year,
                "n_units": len(m),
                "statistic": "spearman_r",
                "value": _spearman_rank(m["unusual_unique_px"], m["EVENTS"]),
                "detail": "sensitivity only; county targeting lost",
            }
        )

    # DTM disaster arrivals vs OCHA 2022 snapshot (rank discordance)
    dtm_path = OUT / "stage6_dtm_r16_county_stock.csv"
    if dtm_path.exists():
        dtm_c = pd.read_csv(dtm_path)
    else:
        run_stage6_independent()
        dtm_c = pd.read_csv(dtm_path)
    ocha22 = pd.read_excel(
        EXT_DATA / "OCHA_flood_data" / "ssd_flood_response_211022.xlsx",
        sheet_name="2022 floods",
    )
    ocha22 = _drop_hxl(ocha22)
    aff_col = _find_col(ocha22, "affected", exclude=("percentage",))
    pcode_col = _find_col(ocha22, "admin2_pcode", "pcode")
    if pcode_col and aff_col:
        ocha22["adm2_pcode"] = ocha22[pcode_col].astype(str).str.strip()
        ocha22["people_affected"] = pd.to_numeric(ocha22[aff_col], errors="coerce")
        ocha22 = ocha22[ocha22["adm2_pcode"].str.len() > 2]
        rank_dtm = dtm_c.set_index("County_INT_PCode")["disaster_arrival_ind"].rank()
        rank_ocha = ocha22.set_index("adm2_pcode")["people_affected"].rank()
        common = rank_dtm.index.intersection(rank_ocha.index)
        r_dtm_ocha = _spearman_rank(rank_dtm.loc[common], rank_ocha.loc[common])
        disaster_no_ocha = int(
            (
                (dtm_c["disaster_arrival_ind"] > dtm_c["disaster_arrival_ind"].median())
                & dtm_c["County_INT_PCode"].isin(ocha22["adm2_pcode"])
                & dtm_c["County_INT_PCode"].map(
                    ocha22.set_index("adm2_pcode")["people_affected"].to_dict()
                ).isna()
            ).sum()
        )
        checks.append(
            {
                "check_id": "dtm_disaster_arrival_vs_ocha_20221021",
                "year": 2022,
                "n_units": len(common),
                "statistic": "spearman_rank",
                "value": r_dtm_ocha,
                "detail": "DTM R16 disaster arrivals vs OCHA affected; different time windows",
            }
        )
        checks.append(
            {
                "check_id": "dtm_high_disaster_ocha_unassessed",
                "year": "R16 vs Oct2022",
                "n_units": len(dtm_c),
                "statistic": "n_counties",
                "value": disaster_no_ocha,
                "detail": "high disaster arrivals but OCHA affected NaN (not zero)",
            }
        )

    # GeoEPR exposure (flooded area proxy by group overlap) — descriptive only
    geo_rows = []
    geo = _load_geoepr_ssd()
    if len(geo) and len(flood_u):
        admin2_g = gpd.read_file(COURSE_RAW / "Administrative boundaries" / "ssd_admin2.geojson").to_crs(
            "EPSG:6933"
        )
        flood_y = flood_u[flood_u["year"] == 2023].rename(columns={"unusual_unique_px": "px"})
        flood_g = admin2_g.merge(flood_y[["adm2_pcode", "px"]], on="adm2_pcode", how="left").fillna({"px": 0})
        flood_g["flooded_km2_proxy"] = flood_g["px"] * FLOOD_PIXEL_AREA_KM2
        for _, grow in geo.iterrows():
            geom = _parse_wkt(grow["the_geom"])
            if geom is None:
                continue
            gpoly = gpd.GeoDataFrame({"group": [grow["group"]]}, geometry=[geom], crs="EPSG:4326").to_crs(
                "EPSG:6933"
            )
            try:
                inter = gpd.overlay(flood_g, gpoly, how="intersection")
                flooded = float(inter["flooded_km2_proxy"].sum())
            except Exception:  # noqa: BLE001
                flooded = np.nan
            geo_rows.append(
                {
                    "group": grow["group"],
                    "sqkm_settlement": grow.get("sqkm", np.nan),
                    "flooded_km2_proxy_2023": flooded,
                }
            )
        geo_exp = pd.DataFrame(geo_rows)
        geo_exp.to_csv(OUT / "stage7_geoepr_flood_exposure_2023.csv", index=False)

    fd = pd.DataFrame(checks)
    fd.to_csv(OUT / "stage7_preregistered_checks.csv", index=False)
    writeup_blocks.append(_md_table(fd.head(40)) if len(fd) else "- none")
    writeup_blocks.append("")
    writeup_blocks.append("Full metrics: `stage7_preregistered_checks.csv`.")
    writeup_blocks.append("")

    # Five-part narratives for key checks
    u_mean = float(asap_u["mean_crop_pct_on_flood_px"].mean()) if len(asap_u) else np.nan
    r_mean = float(asap_r["mean_crop_pct_on_flood_px"].mean()) if len(asap_r) else np.nan
    writeup_blocks.extend(
        _five_part_block(
            "ASAP crop on flood pixels (unusual vs recurring)",
            f"Sampled ASAP crop % at unique flood pixel locations 2022–2024: "
            f"unusual mean≈{u_mean:.4f}, recurring mean≈{r_mean:.4f} "
            f"(see `stage7_asap_on_*_flood_px_admin2_year.csv`). "
            f"Stage 6 all-admin2 zonal medians differ from pixel-on-flood sample.",
            "Low crop % on unusual flood pixels does not by itself prove no cropland impact; "
            "wetlands coded as recurring may host seasonal farming.",
            "ASAP misses small plots; flood tiles under-cover northern counties; "
            "unique-pixel sampling caps at 25k points/year.",
            "Counties with high FEWS harvested area but low unusual flood px exist in the panel "
            "(check `flood_low_but_fews_ha_high`).",
            "Area-weighted zonal overlap ASAP×flood masks; compare Jonglei/Unity/Upper Nile only "
            "with tile coverage filter.",
        )
    )

    r_fews = fd[(fd["check_id"] == "flood_unusual_px_vs_fews_ha") & (fd["year"] == 2023)]
    r_val = r_fews["value"].iloc[0] if len(r_fews) else np.nan
    writeup_blocks.extend(
        _five_part_block(
            "Flood × FEWS harvested area",
            f"County-year Spearman unusual px vs ha harvested (2023 example r={r_val:.3f}). "
            "Split by high/low UCDP activity in `stage7_preregistered_checks.csv`.",
            "Weak or mixed rank correlation is expected: conflict, displacement, rainfall, and "
            "assessment access confound a flood-only crop story.",
            "FEWS is national CFSAM hectares, not flood loss; 2016 gap; 2 unmatched FEWS counties.",
            "County-years with below-median flood but above-median harvest challenge a simple "
            "flood-damage narrative.",
            "Model harvest **change** year-on-year with explicit rainy-season window; "
            "hold conflict intensity constant.",
        )
    )

    ged_r = fd[(fd["check_id"] == "unusual_px_vs_ged_all_types") & (fd["statistic"] == "spearman_r_same_year")]
    writeup_blocks.extend(
        _five_part_block(
            "Flood × UCDP GED (positive and lagged)",
            "Same-year and lag+1 Spearman between unusual flood px and GED event counts "
            "(all types and type-2) exported in preregistered table; date_prec≤3 filter applied.",
            "Co-occurrence may reflect shared seasonality or accessibility, not flooding causing fights.",
            "Inundation might reduce fighting (negative association) in some counties — inspect sign per year.",
            "159 SSD GED events have imprecise dates; ACLED admin1 sensitivity often disagrees in magnitude.",
            "Event-level buffers around floodplains; test wet-season vs dry-season floods separately.",
        )
    )

    writeup_blocks.extend(
        _five_part_block(
            "DTM disaster arrivals vs OCHA flood affected",
            "Rank comparison DTM R16 disaster-tagged arrivals vs OCHA Oct 2022 assessed affected "
            "(see preregistered `dtm_disaster_arrival_vs_ocha_20221021`). "
            "Disaster is **not** flood-only (Stage 2).",
            "Discordance may mean drought/fire displacement, different time windows, or OCHA under-assessment.",
            "OCHA NaN means unassessed, not zero affected.",
            "Counties with high disaster arrivals but missing OCHA affected are counted explicitly.",
            "Use OCHA 20251130 only for same-season validation; never stack five OCHA files.",
        )
    )

    writeup_blocks.extend(
        _five_part_block(
            "GeoEPR settlement × flood (exposure only)",
            "Proxy flooded km² by GeoEPR group overlap with 2023 unusual flood county totals "
            "(`stage7_geoepr_flood_exposure_2023.csv`).",
            "Shows which settlement polygons sit where flood extent was observed — **not** ethnic violence risk.",
            "Polygons overlap; groups are politically relevant settlements, not battle actors.",
            "UCDP side_a/side_b strings (Lou Nuer, Murle) are not join keys to GeoEPR groups.",
            "Descriptive map overlay only; ecological fallacy if linked to clash prediction.",
        )
    )

    report = OUT / "stage7_findings.md"
    report.write_text("\n".join(writeup_blocks), encoding="utf-8")
    return report


def run_stage8_synthesis() -> Path:
    """Rewrite synthesis from Stage 5–7 artefacts (not static stub text)."""
    join_csv = OUT / "join_feasibility.csv"
    join_md = OUT / "join_feasibility.md"
    s7 = OUT / "stage7_preregistered_checks.csv"
    s6 = OUT / "stage6_independent.md"
    red = OUT / "redundancy.md"

    proceed_joins = 0
    stop_joins = 0
    if join_csv.exists():
        jdf = pd.read_csv(join_csv)
        if "gate" in jdf.columns:
            proceed_joins = int(jdf["gate"].isin(["proceed", "proceed_with_caveat"]).sum())
            stop_joins = int((jdf["gate"] == "stop_n_too_small").sum())

    s7_summary = ""
    cropland_signal = "mixed"
    conflict_signal = "mixed"
    if s7.exists():
        fd = pd.read_csv(s7)
        asap_row = fd[fd["check_id"] == "asap_crop_on_unusual_flood_px"]
        if len(asap_row) and pd.notna(asap_row["value"].iloc[0]):
            v = float(asap_row["value"].iloc[0])
            # ASAP mask values are crop % (typically 0–100 scale).
            cropland_signal = "low_on_flood_px" if v < 1.0 else "nonzero_on_flood_px"
        contra = fd[fd["check_id"] == "flood_low_but_fews_ha_high"]
        if len(contra) and float(contra["value"].iloc[0]) > 5:
            cropland_signal += "; feews_high_where_flood_low"
        ged_rows = fd[fd["check_id"].str.contains("unusual_px_vs_ged", na=False)]
        if len(ged_rows):
            mean_r = ged_rows["value"].astype(float).mean()
            conflict_signal = f"mean_spearman≈{mean_r:.2f} (not causal)"

    lines = [
        "# Stage 8 — Synthesis and modelling directions",
        "",
        "Evidence drawn from Stage 5 join gates, Stage 6 independent profiles, and Stage 7 "
        "pre-registered checks. **Not** a fitted impact model.",
        "",
        "## Stage 5 join gates (observation)",
        "",
        f"- Joins classified in `join_feasibility.csv`: **{proceed_joins}** proceed / caveat, "
        f"**{stop_joins}** stopped for small n.",
        f"- Narrative: `{join_md.name}`" if join_md.exists() else "- Narrative: missing",
        "- Canonical key: COD `adm2_pcode`; ACLED only after aggregating flood to admin1.",
        "",
        "## What the combined data can support",
        "",
        "- **Cropland exposure layer (conditional):** static ASAP crop % + unusual/recurring flood "
        "extent + FEWS harvest trends — describe **where** cereal area and flood exposure co-locate, "
        f"not tonnes lost. Stage 7 crop-on-flood signal: **{cropland_signal}**.",
        "- **Conflict / displacement context (conditional):** UCDP GED or Non-State (one channel only); "
        f"DTM IDP stock and broad disaster arrivals; OCHA snapshots for flood validation. "
        f"Stage 7 flood–violence ranks: **{conflict_signal}**.",
        "- **GeoEPR:** settlement-area flood exposure tables only; no ethnic risk scoring.",
        "",
        "## What it cannot support",
        "",
        "- Predicting ethnic-group clashes from flood pixels alone.",
        "- ACLED weekly aggregates as ethnic or county-level actor data.",
        "- National FMR destination modelling (REACH absent).",
        "- `DTM *_disaster` as a flood-only impact label (Stage 2 gate).",
        "- A single combined end-to-end model without double-counting (Stage 4 redundancy).",
        "",
        "## Go / no-go",
        "",
        "| Direction | Status | Evidence |",
        "|-----------|--------|----------|",
    ]

    cro_status = "conditional_go" if proceed_joins > 0 else "no_go"
    cro_reason = (
        "FEWS+ASAP+flood joins gated proceed; watch crosswalk, 2016 gap, tile coverage"
        if cro_status == "conditional_go"
        else "join gates failed or missing"
    )
    conf_status = "conditional_go"
    conf_reason = "UCDP+DTM+OCHA validation; ACLED admin1 sensitivity only"
    combined = "no_go"
    lines.extend(
        [
            f"| Cropland impact layer | **{cro_status.replace('_', ' ')}** | {cro_reason} |",
            f"| Conflict / displacement layer | **{conf_status.replace('_', ' ')}** | {conf_reason} |",
            f"| Combined single model | **{combined.replace('_', ' ')}** | redundancy + unit mismatch |",
            "",
            "## References",
            "",
            f"- Stage 6: `{s6.name}`" if s6.exists() else "- Stage 6: not found",
            f"- Stage 7: `stage7_findings.md`, `stage7_preregistered_checks.csv`",
            f"- Redundancy: `{red.name}`" if red.exists() else "",
            "",
            "## Next work after team review",
            "",
            "1. Resolve remaining `admin2_unmatched.csv` before county modelling.",
            "2. Pick one series per channel (Stage 4) in writing.",
            "3. If cropland layer proceeds: publish maps with unusual **and** recurring sensitivity.",
            "4. If conflict layer proceeds: keep GeoEPR descriptive; do not infer ethnicity from ACLED.",
            "",
        ]
    )
    p = OUT / "synthesis.md"
    p.write_text("\n".join(lines), encoding="utf-8")

    go = pd.DataFrame(
        [
            {"direction": "cropland_impact_layer", "status": cro_status, "reason": cro_reason},
            {"direction": "conflict_displacement_layer", "status": conf_status, "reason": conf_reason},
            {"direction": "combined_end_to_end_model", "status": combined, "reason": "redundancy and unit mismatch"},
        ]
    )
    go.to_csv(OUT / "go_no_go.csv", index=False)
    return p


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Impact EDA stages 2–8")
    parser.add_argument(
        "--through",
        type=int,
        default=8,
        choices=range(2, 9),
        help="Run stages 2 through N (default: 8). Use 2 for semantics only.",
    )
    args = parser.parse_args()
    through: int = args.through

    results: dict[str, str] = {}
    results["stage2_semantics"] = str(run_stage2_semantics())

    if through >= 3:
        xw_path, temporal_path = run_stage3_crosswalks()
        results["stage3_crosswalk"] = str(xw_path)
        results["stage3_temporal"] = str(temporal_path)
    if through >= 4:
        results["stage4_redundancy"] = str(run_stage4_redundancy())
    if through >= 5:
        results["stage5_joins"] = str(run_stage5_join_feasibility())
    if through >= 6:
        results["stage6_independent"] = str(run_stage6_independent())
    if through >= 7:
        results["stage7_findings"] = str(run_stage7_cross_dataset())
    if through >= 8:
        results["stage8_synthesis"] = str(run_stage8_synthesis())

    (OUT / "stages_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
