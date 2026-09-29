"""
Step 0 - Pilot points for the "can we tell crop from grass?" check.

Draws 30 random points in Twic county (Warrap), outside the five Aweil
counties and Bor South, so the pilot never uses points from the real sample.
The points are uniform over the county (no map is used to place them), with a
fixed seed so everyone gets the same list.

Each person labels all 30 on their own, without looking at any cropland map,
and fills in pilot_labels_<name>.csv. Then compare_pilot.py (later) reports how
often two people agree and how often they were confident.

Outputs (in cropland/):
  pilot_points.csv    id, lat, lon, links to Google Maps satellite and Sentinel Hub EO Browser
  pilot_points.kml    the same points for Google Earth Pro (historical imagery slider)
  pilot_labels_TEMPLATE.csv   the sheet to fill in

Run from group_repo: python cropland/00_pilot_points.py
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ADMIN2 = HERE.parent / "raw_data" / "Administrative boundaries" / "ssd_admin2.geojson"
COUNTY = "Twic"          # Warrap state; not Twic East (Jonglei)
N_POINTS = 30
SEED = 42


def random_points_in(poly, n, rng):
    """Uniform random points inside a polygon, by rejection from its bounding box."""
    x0, y0, x1, y1 = poly.bounds
    pts = []
    while len(pts) < n:
        x, y = rng.uniform(x0, x1, 4 * n), rng.uniform(y0, y1, 4 * n)
        cand = gpd.GeoSeries(gpd.points_from_xy(x, y), crs=4326)
        pts += [p for p in cand[cand.within(poly)]][: n - len(pts)]
    return pts


def main() -> None:
    admin = gpd.read_file(ADMIN2)
    county = admin[(admin.adm2_name == COUNTY) & (admin.adm1_name == "Warrap")]
    assert len(county) == 1, "expected exactly one Twic county in Warrap"
    pts = random_points_in(county.geometry.iloc[0], N_POINTS, np.random.default_rng(SEED))

    df = pd.DataFrame({"id": [f"P{i + 1:02d}" for i in range(N_POINTS)],
                       "lat": [round(p.y, 6) for p in pts], "lon": [round(p.x, 6) for p in pts]})
    df["google_maps"] = [f"https://www.google.com/maps/@{a},{o},300m/data=!3m1!1e3" for a, o in zip(df.lat, df.lon)]
    # EO Browser: Sentinel-2 true colour, zoomed to ~10 m pixels; change the date in the app
    df["eo_browser"] = [f"https://apps.sentinel-hub.com/eo-browser/?zoom=16&lat={a}&lng={o}&fromTime=2022-05-01&toTime=2022-11-30"
                        for a, o in zip(df.lat, df.lon)]
    df.to_csv(HERE / "pilot_points.csv", index=False)

    placemarks = "\n".join(
        f"<Placemark><name>{r.id}</name><Point><coordinates>{r.lon},{r.lat},0</coordinates></Point></Placemark>"
        for r in df.itertuples())
    (HERE / "pilot_points.kml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
        f"<name>Cropland pilot, Twic county</name>\n{placemarks}\n</Document></kml>\n")

    sheet = df[["id", "lat", "lon"]].copy()
    for col in ["label", "confidence", "bare_soil_apr_jun", "green_up_month", "early_harvest_drop",
                "regular_plots", "homesteads_300m", "burn_scar", "standing_water", "imagery_used",
                "imagery_date", "minutes", "notes"]:
        sheet[col] = ""
    sheet.to_csv(HERE / "pilot_labels_TEMPLATE.csv", index=False)
    print(f"{N_POINTS} points in {COUNTY} written to {HERE}")


if __name__ == "__main__":
    main()
