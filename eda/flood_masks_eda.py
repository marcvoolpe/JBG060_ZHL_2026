from pathlib import Path
from collections import Counter
import json
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "raw_data"
FLOOD_DIR = DATA_DIR / "flood_masks"
ADMIN0_PATH = DATA_DIR / "Administrative boundaries" / "ssd_admin0.geojson"
OUT_DIR = ROOT / "eda" / "outputs" / "flood_masks"


def country_bbox() -> dict:
    data = json.loads(ADMIN0_PATH.read_text())
    geom = data["features"][0]["geometry"]
    coords = []
    if geom["type"] == "Polygon":
        coords = [pt for ring in geom["coordinates"] for pt in ring]
    elif geom["type"] == "MultiPolygon":
        coords = [pt for polygon in geom["coordinates"] for ring in polygon for pt in ring]
    lons = [pt[0] for pt in coords]
    lats = [pt[1] for pt in coords]
    return {
        "lon_min": min(lons),
        "lon_max": max(lons),
        "lat_min": min(lats),
        "lat_max": max(lats),
    }


def parse_file_info(path: Path) -> dict:
    match = re.search(r"flood_events_(h\d+v\d+)_(\d{4})\.parquet$", path.name)
    flood_group = path.parent.name.replace("compact_", "")
    return {
        "path": str(path.relative_to(ROOT)),
        "flood_group": flood_group,
        "tile": match.group(1),
        "year": int(match.group(2)),
        "size_mb": path.stat().st_size / 1024 / 1024,
    }


def load_flood_summaries() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    files = sorted(FLOOD_DIR.glob("compact_*/*.parquet"))
    bbox = country_bbox()
    file_rows = []
    day_counts = Counter()
    month_counts = Counter()
    tile_counts = Counter()
    ssd_bbox_day_counts = Counter()
    ssd_bbox_month_counts = Counter()
    ssd_bbox_tile_counts = Counter()
    sample_frames = []
    ssd_bbox_sample_frames = []
    sample_per_file = 2500

    for path in files:
        info = parse_file_info(path)
        parquet_file = pq.ParquetFile(path)
        row_count = parquet_file.metadata.num_rows
        df = pd.read_parquet(path, columns=["date", "lat", "lon", "tile"])
        df["date"] = pd.to_datetime(df["date"].astype(str))
        df["lat"] = pd.to_numeric(df["lat"])
        df["lon"] = pd.to_numeric(df["lon"])

        in_bbox = df[
            (df["lat"] >= bbox["lat_min"]) &
            (df["lat"] <= bbox["lat_max"]) &
            (df["lon"] >= bbox["lon_min"]) &
            (df["lon"] <= bbox["lon_max"])
        ]

        file_rows.append({
            **info,
            "row_count": row_count,
            "ssd_bbox_row_count": len(in_bbox),
            "date_min": df["date"].min(),
            "date_max": df["date"].max(),
            "lat_min": df["lat"].min(),
            "lat_max": df["lat"].max(),
            "lon_min": df["lon"].min(),
            "lon_max": df["lon"].max(),
        })
        for date, count in df["date"].value_counts().items():
            day_counts[(date, info["flood_group"])] += int(count)
        for month, count in df["date"].dt.month.value_counts().items():
            month_counts[(int(month), info["flood_group"])] += int(count)
        tile_counts[(info["tile"], info["flood_group"])] += int(row_count)
        for date, count in in_bbox["date"].value_counts().items():
            ssd_bbox_day_counts[(date, info["flood_group"])] += int(count)
        for month, count in in_bbox["date"].dt.month.value_counts().items():
            ssd_bbox_month_counts[(int(month), info["flood_group"])] += int(count)
        ssd_bbox_tile_counts[(info["tile"], info["flood_group"])] += int(len(in_bbox))

        take = min(sample_per_file, len(df))
        if take:
            sample = df.sample(take, random_state=info["year"] + (0 if info["flood_group"] == "recurring" else 10000))
            sample["flood_group"] = info["flood_group"]
            sample["year"] = info["year"]
            sample_frames.append(sample)
        take_bbox = min(sample_per_file, len(in_bbox))
        if take_bbox:
            sample_bbox = in_bbox.sample(take_bbox, random_state=info["year"] + (1 if info["flood_group"] == "recurring" else 10001))
            sample_bbox["flood_group"] = info["flood_group"]
            sample_bbox["year"] = info["year"]
            ssd_bbox_sample_frames.append(sample_bbox)

    file_summary = pd.DataFrame(file_rows)
    year_summary = (
        file_summary.pivot_table(index="year", columns="flood_group", values="row_count", aggfunc="sum", fill_value=0)
        .sort_index()
    )
    year_summary["total"] = year_summary.sum(axis=1)
    month_summary = counter_to_table(month_counts, "month")
    tile_summary = counter_to_table(tile_counts, "tile")
    daily_summary = counter_to_table(day_counts, "date")
    daily_summary.index = pd.to_datetime(daily_summary.index)
    sample_events = pd.concat(sample_frames, ignore_index=True)
    ssd_bbox_year_summary = (
        file_summary.pivot_table(index="year", columns="flood_group", values="ssd_bbox_row_count", aggfunc="sum", fill_value=0)
        .sort_index()
    )
    ssd_bbox_year_summary["total"] = ssd_bbox_year_summary.sum(axis=1)
    ssd_bbox_month_summary = counter_to_table(ssd_bbox_month_counts, "month")
    ssd_bbox_tile_summary = counter_to_table(ssd_bbox_tile_counts, "tile")
    ssd_bbox_daily_summary = counter_to_table(ssd_bbox_day_counts, "date")
    ssd_bbox_daily_summary.index = pd.to_datetime(ssd_bbox_daily_summary.index)
    ssd_bbox_sample_events = pd.concat(ssd_bbox_sample_frames, ignore_index=True)
    return (
        file_summary, year_summary, month_summary, tile_summary, daily_summary, sample_events,
        ssd_bbox_year_summary, ssd_bbox_month_summary, ssd_bbox_tile_summary, ssd_bbox_daily_summary,
        ssd_bbox_sample_events,
    )


def counter_to_table(counter: Counter, index_name: str) -> pd.DataFrame:
    rows = [
        {index_name: key[0], "flood_group": key[1], "record_count": value}
        for key, value in counter.items()
    ]
    table = pd.DataFrame(rows)
    table = table.pivot_table(index=index_name, columns="flood_group", values="record_count", aggfunc="sum", fill_value=0)
    table = table.sort_index()
    table["total"] = table.sum(axis=1)
    return table


def draw_boundary(ax) -> None:
    data = json.loads(ADMIN0_PATH.read_text())
    geom = data["features"][0]["geometry"]
    rings = []
    if geom["type"] == "Polygon":
        rings = geom["coordinates"]
    elif geom["type"] == "MultiPolygon":
        rings = [ring for polygon in geom["coordinates"] for ring in polygon]
    for ring in rings:
        xs = [pt[0] for pt in ring]
        ys = [pt[1] for pt in ring]
        ax.plot(xs, ys, color="#333333", linewidth=0.8)


def save_plots(year_summary: pd.DataFrame, month_summary: pd.DataFrame, daily_summary: pd.DataFrame, sample_events: pd.DataFrame) -> None:
    ax = year_summary.drop(columns=["total"], errors="ignore").plot(kind="bar", stacked=True, figsize=(12, 5), color=["#2C7FB8", "#F28E2B"])
    ax.set_title("Flood event records by year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Pixel-day records")
    ax.legend(title="Flood group")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "01_yearly_flood_records.png", dpi=180)
    plt.close()

    ax = month_summary.drop(columns=["total"], errors="ignore").plot(kind="bar", figsize=(9, 5), color=["#2C7FB8", "#F28E2B"])
    ax.set_title("Flood event records by month")
    ax.set_xlabel("Month")
    ax.set_ylabel("Pixel-day records")
    ax.legend(title="Flood group")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "02_monthly_seasonality.png", dpi=180)
    plt.close()

    plt.figure(figsize=(12, 4))
    daily_summary["total"].rolling(14, min_periods=1).sum().plot(color="#2C7FB8", linewidth=1)
    plt.title("14-day rolling flood record count")
    plt.xlabel("Date")
    plt.ylabel("Pixel-day records")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "03_daily_rolling_14d.png", dpi=180)
    plt.close()

    sample = sample_events
    fig, ax = plt.subplots(figsize=(8, 8))
    for group, color in [("recurring", "#2C7FB8"), ("unusual", "#F28E2B")]:
        part = sample[sample["flood_group"] == group]
        ax.scatter(part["lon"], part["lat"], s=0.3, alpha=0.18, c=color, label=group)
    draw_boundary(ax)
    ax.set_title("Spatial distribution of flood event records")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(markerscale=8)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "04_spatial_distribution_sample.png", dpi=220)
    plt.close()


def save_ssd_bbox_plots(year_summary: pd.DataFrame, month_summary: pd.DataFrame, sample_events: pd.DataFrame) -> None:
    ax = year_summary.drop(columns=["total"], errors="ignore").plot(kind="bar", stacked=True, figsize=(12, 5), color=["#2C7FB8", "#F28E2B"])
    ax.set_title("Flood event records by year - South Sudan bounding box")
    ax.set_xlabel("Year")
    ax.set_ylabel("Pixel-day records")
    ax.legend(title="Flood group")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "05_ssd_bbox_yearly_flood_records.png", dpi=180)
    plt.close()

    ax = month_summary.drop(columns=["total"], errors="ignore").plot(kind="bar", figsize=(9, 5), color=["#2C7FB8", "#F28E2B"])
    ax.set_title("Flood event records by month - South Sudan bounding box")
    ax.set_xlabel("Month")
    ax.set_ylabel("Pixel-day records")
    ax.legend(title="Flood group")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "06_ssd_bbox_monthly_seasonality.png", dpi=180)
    plt.close()

    fig, ax = plt.subplots(figsize=(8, 8))
    for group, color in [("recurring", "#2C7FB8"), ("unusual", "#F28E2B")]:
        part = sample_events[sample_events["flood_group"] == group]
        ax.scatter(part["lon"], part["lat"], s=0.35, alpha=0.20, c=color, label=group)
    draw_boundary(ax)
    ax.set_title("Spatial distribution sample - South Sudan bounding box")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(markerscale=8)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "07_ssd_bbox_spatial_distribution_sample.png", dpi=220)
    plt.close()


def write_report(
    file_summary: pd.DataFrame,
    year_summary: pd.DataFrame,
    month_summary: pd.DataFrame,
    tile_summary: pd.DataFrame,
    daily_summary: pd.DataFrame,
    sample_events: pd.DataFrame,
    ssd_bbox_year_summary: pd.DataFrame,
    ssd_bbox_month_summary: pd.DataFrame,
    ssd_bbox_tile_summary: pd.DataFrame,
    ssd_bbox_daily_summary: pd.DataFrame,
    ssd_bbox_sample_events: pd.DataFrame,
) -> None:
    pixel_frequency = (
        sample_events.groupby(["lat", "lon", "flood_group"])
        .agg(sample_record_count=("date", "size"), first_sample_date=("date", "min"), last_sample_date=("date", "max"))
        .reset_index()
        .sort_values("sample_record_count", ascending=False)
    )
    daily_top = daily_summary["total"].sort_values(ascending=False).head(20)

    file_summary.to_csv(OUT_DIR / "flood_mask_file_summary.csv", index=False)
    year_summary.to_csv(OUT_DIR / "flood_records_by_year.csv")
    month_summary.to_csv(OUT_DIR / "flood_records_by_month.csv")
    tile_summary.to_csv(OUT_DIR / "flood_records_by_tile.csv")
    ssd_bbox_year_summary.to_csv(OUT_DIR / "ssd_bbox_flood_records_by_year.csv")
    ssd_bbox_month_summary.to_csv(OUT_DIR / "ssd_bbox_flood_records_by_month.csv")
    ssd_bbox_tile_summary.to_csv(OUT_DIR / "ssd_bbox_flood_records_by_tile.csv")
    ssd_bbox_daily_summary.to_csv(OUT_DIR / "ssd_bbox_flood_records_by_day.csv")
    pixel_frequency.head(1000).to_csv(OUT_DIR / "top_flood_pixels_from_sample.csv", index=False)
    daily_top.to_csv(OUT_DIR / "top_flood_days.csv", header=["record_count"])

    start = pd.to_datetime(file_summary["date_min"].min()).date()
    end = pd.to_datetime(file_summary["date_max"].max()).date()
    lat_min = round(file_summary["lat_min"].min(), 5)
    lat_max = round(file_summary["lat_max"].max(), 5)
    lon_min = round(file_summary["lon_min"].min(), 5)
    lon_max = round(file_summary["lon_max"].max(), 5)
    group_counts = file_summary.groupby("flood_group")["row_count"].sum()
    raw_file_count = len(file_summary)
    best_year = int(year_summary["total"].idxmax())
    best_month = int(month_summary["total"].idxmax())
    ssd_best_year = int(ssd_bbox_year_summary["total"].idxmax())
    ssd_best_month = int(ssd_bbox_month_summary["total"].idxmax())
    ssd_group_counts = file_summary.groupby("flood_group")["ssd_bbox_row_count"].sum()
    bbox = country_bbox()

    report = f"""# Flood Masks EDA - 初步探索

## 数据范围

- 数据位置：`raw_data/flood_masks`
- 文件数：{raw_file_count} 个 parquet 文件
- 两类洪水：`recurring` 与 `unusual`
- 两个 MODIS tile：{", ".join(sorted(file_summary["tile"].unique()))}
- 时间范围：{start} 到 {end}
- 原始记录数：{int(file_summary["row_count"].sum()):,} 条 pixel-day 洪水记录
- 说明：本轮为轻量 EDA，年度/月度/每日统计基于原始 parquet 记录；未执行全量 `(date, lat, lon)` 去重，因为 9500 万行全量排序开销很大。课程脚本中说明，如 recurring 与 unusual 在同一日同一像素重复，最终应优先保留 unusual。

## 字段含义

- `date`：该像素被标记为洪水的日期
- `lat` / `lon`：像素中心点坐标
- `tile`：MODIS tile，当前为 `h20v08` 和 `h21v08`
- `flood_group`：洪水类型，`recurring` 表示反复发生，`unusual` 表示异常/较少发生
- `flood_type`：课程脚本中的数值编码，`0=recurring`，`1=unusual`

## 快速发现

- recurring 记录数：{group_counts.get("recurring", 0):,}
- unusual 记录数：{group_counts.get("unusual", 0):,}
- 记录最多的年份：{best_year} 年，共 {int(year_summary.loc[best_year, "total"]):,} 条
- 记录最多的月份：{best_month} 月，共 {int(month_summary.loc[best_month, "total"]):,} 条
- 纬度范围：{lat_min} 到 {lat_max}
- 经度范围：{lon_min} 到 {lon_max}

## 南苏丹外接框过滤后的结果

这里使用南苏丹国界 GeoJSON 的外接矩形过滤 tile 数据，不等同于精确国界裁剪，但能先去掉大量明显在南苏丹之外的区域。

- bbox：lat {bbox["lat_min"]:.4f} 到 {bbox["lat_max"]:.4f}，lon {bbox["lon_min"]:.4f} 到 {bbox["lon_max"]:.4f}
- bbox 内原始记录数：{int(file_summary["ssd_bbox_row_count"].sum()):,}
- bbox 内 recurring 记录数：{int(ssd_group_counts.get("recurring", 0)):,}
- bbox 内 unusual 记录数：{int(ssd_group_counts.get("unusual", 0)):,}
- bbox 内记录最多的年份：{ssd_best_year} 年，共 {int(ssd_bbox_year_summary.loc[ssd_best_year, "total"]):,} 条
- bbox 内记录最多的月份：{ssd_best_month} 月，共 {int(ssd_bbox_month_summary.loc[ssd_best_month, "total"]):,} 条

## 输出文件

- `flood_mask_file_summary.csv`：每个 parquet 文件的年份、tile、类型和大小
- `flood_records_by_year.csv`：按年份和类型统计记录数
- `flood_records_by_month.csv`：按月份和类型统计记录数
- `flood_records_by_tile.csv`：按 tile 和类型统计记录数
- `top_flood_pixels_from_sample.csv`：抽样中出现洪水记录最多的前 1000 个像素
- `top_flood_days.csv`：洪水记录最多的前 20 天
- `ssd_bbox_flood_records_by_year.csv`：南苏丹外接框内按年份统计
- `ssd_bbox_flood_records_by_month.csv`：南苏丹外接框内按月份统计
- `ssd_bbox_flood_records_by_tile.csv`：南苏丹外接框内按 tile 统计
- `ssd_bbox_flood_records_by_day.csv`：南苏丹外接框内按日统计
- `01_yearly_flood_records.png`：年度洪水记录量
- `02_monthly_seasonality.png`：月份季节性
- `03_daily_rolling_14d.png`：14 日滚动洪水记录量
- `04_spatial_distribution_sample.png`：空间分布抽样图
- `05_ssd_bbox_yearly_flood_records.png`：南苏丹外接框内年度洪水记录量
- `06_ssd_bbox_monthly_seasonality.png`：南苏丹外接框内月份季节性
- `07_ssd_bbox_spatial_distribution_sample.png`：南苏丹外接框内空间分布抽样图

## 下一步建议

1. 选一个重点区域，例如 Aweil East 或课程示例 bbox，做局部 flood mask EDA。
2. 把 flood mask 聚合成每日/每周指标，例如 flooded pixel count、flooded area proxy。
3. 与降雨、径流、河流流量做滞后相关分析，找洪水前 7/14/30 天的驱动关系。
"""
    (OUT_DIR / "flood_masks_eda_report_zh.md").write_text(report)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (
        file_summary, year_summary, month_summary, tile_summary, daily_summary, sample_events,
        ssd_bbox_year_summary, ssd_bbox_month_summary, ssd_bbox_tile_summary, ssd_bbox_daily_summary,
        ssd_bbox_sample_events,
    ) = load_flood_summaries()
    write_report(
        file_summary, year_summary, month_summary, tile_summary, daily_summary, sample_events,
        ssd_bbox_year_summary, ssd_bbox_month_summary, ssd_bbox_tile_summary, ssd_bbox_daily_summary,
        ssd_bbox_sample_events,
    )
    save_plots(year_summary, month_summary, daily_summary, sample_events)
    save_ssd_bbox_plots(ssd_bbox_year_summary, ssd_bbox_month_summary, ssd_bbox_sample_events)
    print(f"Processed {int(file_summary['row_count'].sum()):,} raw flood records.")
    print(f"Outputs written to: {OUT_DIR}")


if __name__ == "__main__":
    main()
