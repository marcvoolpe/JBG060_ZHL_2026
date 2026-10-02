"""
Stage 1: machine-readable inventory of external data/ families and selected processed course tables.

No joins. Run from repo root:
    python -m archive.impact_eda.impact_inventory
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from processing_data.paths import (
    EXT_DATA,
    IMPACT_EDA_OUT,
    PROCESSED_DIR,
    ensure_impact_eda_out,
)

HXL_PREFIX = re.compile(r"^#")

# DTM mobility: sample rounds for schema drift (not full parse of all 14).
DTM_MOBILITY_SAMPLE = {
    "dtm-south-sudan-baseline-assessment-round-2.xlsx",
    "dtm-south-sudan-baseline-assessment-round-8.xlsx",
    "ssd-dtm-mobility-tracking-r12-baseline-locations-dataset.xlsx",
    "ssd-dtm-mobility-tracking-r16-baseline-assessment-dataset_updated_20250507.xlsx",
}

# FMR: clean DB + two monthly files.
FMR_SAMPLE = [
    "fmr_db_clean_nov2022_oct2023_public_nov21.xlsx",
    "dtm-south-sudan-flow-monitoring-mar20.xlsx",
    "hdx_ssd_fmr_summary_202210.xlsx",
]


@dataclass
class CatalogueRow:
    family: str
    source_path: str
    sheet_or_table: str
    file_format: str
    n_rows_sampled: int | None
    n_cols: int | None
    column_names: str
    spatial_fields: str
    temporal_fields: str
    grain: str
    time_min: str
    time_max: str
    south_sudan_scope: str
    missingness_note: str
    schema_drift_note: str
    read_error: str = ""


def _cols_str(cols: list[str], max_len: int = 2000) -> str:
    s = "; ".join(str(c) for c in cols)
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _detect_spatial(cols: list[str]) -> list[str]:
    keys = (
        "lat",
        "lon",
        "longitude",
        "latitude",
        "pcode",
        "admin",
        "adm",
        "state",
        "county",
        "payam",
        "geom",
        "fnid",
    )
    out = []
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in keys):
            out.append(c)
    return out


def _detect_temporal(cols: list[str]) -> list[str]:
    keys = ("date", "time", "week", "year", "month", "season", "period", "round")
    out = []
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in keys):
            out.append(c)
    return out


def _drop_hxl_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    first_col = df.columns[0]
    mask = df[first_col].astype(str).str.match(HXL_PREFIX, na=False)
    if mask.any():
        return df.loc[~mask].copy()
    # Some sheets use HXL in any string cell of row 0
    row0 = df.iloc[0].astype(str)
    if row0.str.contains(HXL_PREFIX).any():
        return df.iloc[1:].copy()
    return df


def _profile_dataframe(
    family: str,
    path: Path,
    sheet: str,
    df: pd.DataFrame,
    grain: str,
    south_sudan_scope: str,
    schema_note: str = "",
) -> CatalogueRow:
    df = _drop_hxl_rows(df)
    cols = [str(c) for c in df.columns]
    spatial = _detect_spatial(cols)
    temporal = _detect_temporal(cols)
    time_min, time_max = "", ""
    for tc in temporal:
        if tc not in df.columns:
            continue
        ser = pd.to_datetime(df[tc], errors="coerce")
        if ser.notna().any():
            tmin = ser.min()
            tmax = ser.max()
            if pd.notna(tmin):
                time_min = str(tmin)[:10] if time_min == "" else min(time_min, str(tmin)[:10])
            if pd.notna(tmax):
                time_max = str(tmax)[:10] if time_max == "" else max(time_max, str(tmax)[:10])
    miss = df.isna().mean()
    high_miss = miss[miss > 0.5]
    miss_note = ""
    if len(high_miss) > 0:
        top = high_miss.sort_values(ascending=False).head(5)
        miss_note = "cols >50% NA: " + ", ".join(f"{k}={v:.0%}" for k, v in top.items())

    return CatalogueRow(
        family=family,
        source_path=str(path),
        sheet_or_table=sheet,
        file_format=path.suffix.lstrip("."),
        n_rows_sampled=len(df),
        n_cols=len(cols),
        column_names=_cols_str(cols),
        spatial_fields=_cols_str(spatial),
        temporal_fields=_cols_str(temporal),
        grain=grain,
        time_min=time_min,
        time_max=time_max,
        south_sudan_scope=south_sudan_scope,
        missingness_note=miss_note,
        schema_drift_note=schema_note,
    )


def _fix_relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def profile_excel_sheet(
    family: str,
    path: Path,
    sheet: str,
    root: Path,
    nrows: int | None = 5000,
    grain: str = "unknown",
    south_sudan_scope: str = "South Sudan (assumed from product)",
    schema_note: str = "",
) -> CatalogueRow:
    try:
        df = pd.read_excel(path, sheet_name=sheet, nrows=nrows)
        row = _profile_dataframe(family, path, sheet, df, grain, south_sudan_scope, schema_note)
        row.source_path = _fix_relative_path(path, root)
        return row
    except Exception as exc:  # noqa: BLE001
        return CatalogueRow(
            family=family,
            source_path=_fix_relative_path(path, root),
            sheet_or_table=sheet,
            file_format=path.suffix.lstrip("."),
            n_rows_sampled=None,
            n_cols=None,
            column_names="",
            spatial_fields="",
            temporal_fields="",
            grain=grain,
            time_min="",
            time_max="",
            south_sudan_scope=south_sudan_scope,
            missingness_note="",
            schema_drift_note=schema_note,
            read_error=str(exc),
        )


def profile_csv(
    family: str,
    path: Path,
    root: Path,
    chunk_filter: str | None = None,
    grain: str = "unknown",
) -> list[CatalogueRow]:
    rows: list[CatalogueRow] = []
    try:
        df = pd.read_csv(path, nrows=10000)
        if chunk_filter and "country" in df.columns:
            sub = df[df["country"].astype(str).str.contains("South Sudan", case=False, na=False)]
            scope = f"filtered SSD rows in sample: {len(sub)}/{len(df)}"
        else:
            scope = "full file sample (first 10k rows)"
        row = _profile_dataframe(family, path, path.name, df, grain, scope)
        row.source_path = _fix_relative_path(path, root)
        if family == "FEWS_crop_data" and "indicator" in df.columns:
            row.grain = "county x season_year x indicator (Cereal Mixed, Main harvest)"
            if "season_year" in df.columns:
                sy = df["season_year"].dropna().unique()
                row.time_min = str(min(sy)) if len(sy) else ""
                row.time_max = str(max(sy)) if len(sy) else ""
        rows.append(row)
    except Exception as exc:  # noqa: BLE001
        rows.append(
            CatalogueRow(
                family=family,
                source_path=_fix_relative_path(path, root),
                sheet_or_table=path.name,
                file_format="csv",
                n_rows_sampled=None,
                n_cols=None,
                column_names="",
                spatial_fields="",
                temporal_fields="",
                grain=grain,
                time_min="",
                time_max="",
                south_sudan_scope="",
                missingness_note="",
                schema_drift_note="",
                read_error=str(exc),
            )
        )
    return rows


def _profile_ged_ssd_chunked(path: Path, root: Path) -> list[CatalogueRow]:
    usecols = [
        "year",
        "type_of_violence",
        "country",
        "adm_1",
        "adm_2",
        "latitude",
        "longitude",
        "date_start",
        "date_end",
        "date_prec",
        "best",
        "where_prec",
    ]
    chunks = []
    for ch in pd.read_csv(path, usecols=usecols, chunksize=100_000):
        s = ch[ch["country"].astype(str).str.contains("South Sudan", case=False, na=False)]
        if len(s):
            chunks.append(s)
    if not chunks:
        return []
    ssd = pd.concat(chunks, ignore_index=True)
    row = _profile_dataframe(
        "UCDP_GED",
        path,
        "GEDEvent_v26_1.csv (South Sudan filter, full file scan)",
        ssd,
        "event (geolocated), >=1 death",
        f"South Sudan: {len(ssd)} events",
    )
    row.source_path = _fix_relative_path(path, root)
    if "date_start" in ssd.columns:
        ds = pd.to_datetime(ssd["date_start"], errors="coerce")
        row.time_min = str(ds.min())[:10]
        row.time_max = str(ds.max())[:10]
    return [row]


def _profile_geoepr_ssd(path: Path, root: Path) -> CatalogueRow:
    geo = pd.read_csv(path, usecols=["gwid", "statename", "from", "to", "group", "type", "sqkm"])
    ssd = geo[geo["statename"].astype(str).str.contains("South Sudan", case=False, na=False)]
    row = _profile_dataframe(
        "GeoEPR_2021",
        path,
        "GeoEPR-2021.csv (South Sudan rows; geometry not loaded)",
        ssd,
        "ethnic group x country x time window (polygon in the_geom, not profiled)",
        f"South Sudan: {len(ssd)} group polygons",
    )
    row.source_path = _fix_relative_path(path, root)
    row.time_min = str(ssd["from"].min()) if len(ssd) else ""
    row.time_max = str(ssd["to"].max()) if len(ssd) else ""
    row.schema_drift_note = "WKT in the_geom omitted from inventory load"
    return row


def _profile_nonstate_ssd(path: Path, root: Path) -> CatalogueRow:
    ns = pd.read_csv(path)
    ssd = ns[
        ns["location"].astype(str).str.contains("South Sudan", case=False, na=False)
        | ns["gwno_location"].astype(str).str.contains("626", na=False)
    ]
    row = _profile_dataframe(
        "UCDP_NonState",
        path,
        "NonState_v26_1.csv (South Sudan filter)",
        ssd,
        "conflict-year dyad (>=25 battle deaths/year)",
        f"South Sudan-related: {len(ssd)} rows",
    )
    row.source_path = _fix_relative_path(path, root)
    if "year" in ssd.columns:
        row.time_min = str(int(ssd["year"].min()))
        row.time_max = str(int(ssd["year"].max()))
    return row


def profile_acled(root: Path) -> list[CatalogueRow]:
    path = EXT_DATA / "ACLED_aggregated_african" / "Africa_aggregated_data_up_to_week_of-2026-09-05.xlsx"
    rows: list[CatalogueRow] = []
    usecols = [
        "WEEK",
        "COUNTRY",
        "ADMIN1",
        "EVENT_TYPE",
        "SUB_EVENT_TYPE",
        "EVENTS",
        "FATALITIES",
    ]
    try:
        ac = pd.read_excel(path, usecols=usecols)
        ssd = ac[ac["COUNTRY"].astype(str).str.contains("South Sudan", case=False, na=False)]
        row = _profile_dataframe(
            "ACLED_aggregated",
            path,
            "Sheet1 (South Sudan filter, full Africa file loaded)",
            ssd,
            "admin1 x week x event_type x sub_event_type",
            f"South Sudan: {len(ssd)} rows",
        )
        row.source_path = _fix_relative_path(path, root)
        if "WEEK" in ssd.columns:
            w = pd.to_datetime(ssd["WEEK"], errors="coerce")
            row.time_min = str(w.min())[:10]
            row.time_max = str(w.max())[:10]
        row.schema_drift_note = "Weekly aggregates only; no actors or admin2"
        rows.append(row)
    except Exception as exc:  # noqa: BLE001
        rows.append(
            CatalogueRow(
                family="ACLED_aggregated",
                source_path=_fix_relative_path(path, root),
                sheet_or_table="Sheet1",
                file_format="xlsx",
                n_rows_sampled=None,
                n_cols=None,
                column_names="",
                spatial_fields="",
                temporal_fields="",
                grain="admin1-week aggregates",
                time_min="",
                time_max="",
                south_sudan_scope="",
                missingness_note="",
                schema_drift_note="",
                read_error=str(exc),
            )
        )
    return rows


def profile_dtm_mobility(root: Path) -> tuple[list[CatalogueRow], list[str]]:
    rows: list[CatalogueRow] = []
    drift: list[str] = []
    mob_dir = EXT_DATA / "IOM_DTM_mobility"
    all_files = sorted(mob_dir.glob("*.xlsx"))
    drift.append(f"IOM_DTM_mobility: {len(all_files)} xlsx files on disk")
    layouts: dict[str, list[str]] = {}
    for f in all_files:
        try:
            xl = pd.ExcelFile(f)
            layouts[f.name] = xl.sheet_names
        except Exception as exc:  # noqa: BLE001
            drift.append(f"Could not open {f.name}: {exc}")

    for name, sheets in layouts.items():
        drift.append(f"{name}: sheets={sheets}")

    for f in all_files:
        if f.name not in DTM_MOBILITY_SAMPLE:
            rows.append(
                CatalogueRow(
                    family="IOM_DTM_mobility",
                    source_path=_fix_relative_path(f, root),
                    sheet_or_table="(file listed, not fully profiled)",
                    file_format="xlsx",
                    n_rows_sampled=None,
                    n_cols=None,
                    column_names="",
                    spatial_fields="",
                    temporal_fields="",
                    grain="round snapshot; layout varies by round",
                    time_min="",
                    time_max="",
                    south_sudan_scope="South Sudan product",
                    missingness_note="",
                    schema_drift_note=f"Sheets: {layouts.get(f.name, [])}",
                )
            )
            continue
        xl = pd.ExcelFile(f)
        for sheet in xl.sheet_names:
            grain = "location/payam/county snapshot"
            if "Baseline" in sheet or "Loc" in sheet or "locations" in sheet.lower():
                grain = "location-level baseline (ssid, lat/lon, admin pcodes)"
            elif "Summary" in sheet or "summary" in sheet.lower():
                grain = "aggregated summary table"
            elif sheet == "Note":
                grain = "metadata / narrative"
            rows.append(
                profile_excel_sheet(
                    "IOM_DTM_mobility",
                    f,
                    sheet,
                    root,
                    nrows=8000,
                    grain=grain,
                    schema_note=f"Round file; all round layouts differ ({len(layouts)} files)",
                )
            )
    return rows, drift


def profile_dtm_flow(root: Path) -> tuple[list[CatalogueRow], list[str]]:
    rows: list[CatalogueRow] = []
    drift: list[str] = []
    flow_dir = EXT_DATA / "IOM_DTM_flow"
    all_files = sorted(flow_dir.glob("*.xlsx"))
    drift.append(f"IOM_DTM_flow: {len(all_files)} xlsx files")
    profiled = set(FMR_SAMPLE)
    for f in all_files:
        if f.name not in profiled:
            rows.append(
                CatalogueRow(
                    family="IOM_DTM_flow",
                    source_path=_fix_relative_path(f, root),
                    sheet_or_table="(file listed, not fully profiled)",
                    file_format="xlsx",
                    n_rows_sampled=None,
                    n_cols=None,
                    column_names="",
                    spatial_fields="",
                    temporal_fields="",
                    grain="monthly FMR summary or flow record",
                    time_min="",
                    time_max="",
                    south_sudan_scope="South Sudan FMR",
                    missingness_note="",
                    schema_drift_note="Monthly naming varies; see sampled files",
                )
            )
            continue
        xl = pd.ExcelFile(f)
        for sheet in xl.sheet_names:
            nrows = 15000 if "Data" in sheet else 500
            grain = "FMP group-flow records" if sheet == "Data" else "documentation"
            rows.append(
                profile_excel_sheet(
                    "IOM_DTM_flow",
                    f,
                    sheet,
                    root,
                    nrows=nrows,
                    grain=grain,
                    schema_note="FMR not nationally representative (per file Notes)",
                )
            )
    return rows, drift


def profile_ocha(root: Path) -> list[CatalogueRow]:
    rows: list[CatalogueRow] = []
    ocha_dir = EXT_DATA / "OCHA_flood_data"
    for f in sorted(ocha_dir.glob("*.xlsx")):
        xl = pd.ExcelFile(f)
        for sheet in xl.sheet_names:
            rows.append(
                profile_excel_sheet(
                    "OCHA_flood_data",
                    f,
                    sheet,
                    root,
                    nrows=500,
                    grain="county or state snapshot (assessed affected/displaced)",
                    schema_note="Schemas differ across files; READ ME: assessed-only",
                )
            )
    return rows


def profile_processed_course(root: Path) -> list[CatalogueRow]:
    rows: list[CatalogueRow] = []
    candidates = [
        (PROCESSED_DIR / "Administrative boundaries" / "ssd_admin2_processed.csv", "course_admin2", "admin2 polygon attributes"),
        (PROCESSED_DIR / "IPC" / "ipc_phase3plus_county_long_processed.csv", "course_IPC", "county x IPC window"),
        (PROCESSED_DIR / "farmland" / "farmland_and_cattle_raster_summary_processed.csv", "course_farmland", "national raster summary"),
        (PROCESSED_DIR / "flood_masks" / "flood_masks_daily_counts_processed.csv", "course_flood_masks", "daily counts by tile and flood_type"),
    ]
    for path, family, grain in candidates:
        if not path.exists():
            rows.append(
                CatalogueRow(
                    family=family,
                    source_path=_fix_relative_path(path, root),
                    sheet_or_table=path.name,
                    file_format="csv",
                    n_rows_sampled=None,
                    n_cols=None,
                    column_names="",
                    spatial_fields="",
                    temporal_fields="",
                    grain=grain,
                    time_min="",
                    time_max="",
                    south_sudan_scope="South Sudan",
                    missingness_note="",
                    schema_drift_note="",
                    read_error="file not found",
                )
            )
            continue
        df = pd.read_csv(path)
        row = _profile_dataframe(family, path, path.name, df, grain, "South Sudan")
        row.source_path = _fix_relative_path(path, root)
        rows.append(row)
    return rows


def build_catalogue(root: Path) -> tuple[pd.DataFrame, list[str]]:
    all_rows: list[CatalogueRow] = []
    drift_notes: list[str] = []

    fews_path = EXT_DATA / "FEWS_crop_data" / "crop_data.csv"
    if fews_path.exists():
        all_rows.extend(profile_csv("FEWS_crop_data", fews_path, root))

    ucdp_dir = EXT_DATA / "UCDP_georeferenced_and_nonstate"
    ged = ucdp_dir / "ged261-csv" / "GEDEvent_v26_1.csv"
    if ged.exists():
        all_rows.extend(_profile_ged_ssd_chunked(ged, root))

    ns = ucdp_dir / "ucdp-nonstate-261-csv" / "NonState_v26_1.csv"
    if ns.exists():
        all_rows.append(_profile_nonstate_ssd(ns, root))

    geo = EXT_DATA / "GeoEPR_2021" / "GeoEPR-2021.csv"
    if geo.exists():
        all_rows.append(_profile_geoepr_ssd(geo, root))

    all_rows.extend(profile_acled(root))
    mob_rows, mob_drift = profile_dtm_mobility(root)
    all_rows.extend(mob_rows)
    drift_notes.extend(mob_drift)
    flow_rows, flow_drift = profile_dtm_flow(root)
    all_rows.extend(flow_rows)
    drift_notes.extend(flow_drift)
    all_rows.extend(profile_ocha(root))
    all_rows.extend(profile_processed_course(root))

    df = pd.DataFrame([asdict(r) for r in all_rows])
    return df, drift_notes


def main() -> None:
    from processing_data.paths import ROOT

    out_dir = ensure_impact_eda_out()
    catalogue, drift_notes = build_catalogue(ROOT)
    catalogue_path = out_dir / "catalogue.csv"
    catalogue.to_csv(catalogue_path, index=False)

    drift_path = out_dir / "schema_drift_notes.txt"
    drift_path.write_text("\n".join(drift_notes), encoding="utf-8")

    errors = catalogue[catalogue["read_error"].astype(str).str.len() > 0]
    summary = {
        "n_catalogue_rows": len(catalogue),
        "n_families": catalogue["family"].nunique(),
        "n_read_errors": len(errors),
        "catalogue_csv": str(catalogue_path),
        "schema_drift_notes": str(drift_path),
    }
    (out_dir / "inventory_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    if len(errors):
        print("Read errors:")
        print(errors[["source_path", "sheet_or_table", "read_error"]].to_string())


if __name__ == "__main__":
    main()
