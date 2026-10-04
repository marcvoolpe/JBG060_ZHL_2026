"""
Shared settings for the cropland scripts: Earth Engine project, study areas,
the public maps (and how each is turned into crop / not crop), and the 2025
Sentinel-2 monthly composites. Every script imports this, so a change here
changes all of them.
"""

import json
import os
from pathlib import Path

import geopandas as gpd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
RAW = REPO / "raw_data"
OUT = RAW / "cropland"                      # large outputs, not in git
OUT.mkdir(parents=True, exist_ok=True)
ADMIN2 = RAW / "Administrative boundaries" / "ssd_admin2.geojson"

GROUP_PROJECT = "grand-loop-457810-a1"      # Google Cloud project registered for Earth Engine; holds our assets
# Run on your own Earth Engine project with: set CROPLAND_EE_PROJECT=<your-project-id> (steps 04 and 05 only need public data)
EE_PROJECT = os.environ.get("CROPLAND_EE_PROJECT", GROUP_PROJECT)
ASSETS = f"projects/{GROUP_PROJECT}/assets/sample-points"   # folder made in the Code Editor
YEAR = 2025
SEED = 42
BOX_M = 210                                  # the labelled unit: the outer yellow box, 210 m x 210 m (21 x 21 Sentinel-2 pixels) centred on a point

AREAS = {                                    # study areas: sampled, labelled and scored
    "aweil": ["Aweil North", "Aweil East", "Aweil South", "Aweil West", "Aweil Centre"],
    "bor_south": ["Bor South"],
}
ALLOCATION = {                               # points per stratum (METHODOLOGY.md section 3)
    "aweil": {"A": 150, "B": 90, "C": 90},
    "bor_south": {"A": 60, "B": 30, "C": 30},
}


def ee_init():
    import ee
    ee.Initialize(project=EE_PROJECT)
    return ee


def area_geometry(ee, area: str, simplify_deg: float = 0.0):
    """Earth Engine geometry of one study area (union of its counties)."""
    admin = gpd.read_file(ADMIN2)
    geom = admin[admin.adm2_name.isin(AREAS[area])].dissolve().geometry.iloc[0]
    if simplify_deg:
        geom = geom.simplify(simplify_deg)
    return ee.Geometry(json.loads(gpd.GeoSeries([geom], crs=4326).to_json())["features"][0]["geometry"])


def box(ee, lon: float, lat: float):
    """The BOX_M square centred on a point: the unit labellers label."""
    return ee.Geometry.Point(lon, lat).buffer(BOX_M / 2).bounds()


def country_geometry(ee):
    admin0 = gpd.read_file(RAW / "Administrative boundaries" / "ssd_admin0.geojson")
    geom = admin0.geometry.iloc[0].simplify(0.01)
    return ee.Geometry(json.loads(gpd.GeoSeries([geom], crs=4326).to_json())["features"][0]["geometry"])


def public_maps(ee) -> dict:
    """The 7 public maps as 0/1 crop images, following Kerner et al. (2024).

    Returns {name: (image, year)}. Kept as a function so every script builds
    them the same way.
    """
    dw = (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
          .filterDate(f"{YEAR}-01-01", f"{YEAR + 1}-01-01").select("label").mode())
    esri = (ee.ImageCollection("projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS")
            .filterDate(f"{YEAR}-01-01", f"{YEAR + 1}-01-01").mosaic())
    cereal = (ee.ImageCollection("ESA/WorldCereal/2021/MODELS/v100")
              .filter(ee.Filter.eq("product", "temporarycrops")).select("classification").mosaic())
    maps = {
        "worldcover_2021": (ee.ImageCollection("ESA/WorldCover/v200").first().eq(40), 2021),
        "glad_2019": (ee.ImageCollection("users/potapovpeter/Global_cropland_2019").mosaic().gt(0.5), 2019),
        "deafrica_2019": (ee.ImageCollection("projects/sat-io/open-datasets/DEAF/CROPLAND-EXTENT/mask").mosaic().eq(1), 2019),
        "worldcereal_2021": (cereal.eq(100), 2021),
        "esri_2025": (esri.eq(5), 2025),
        "dynamicworld_2025": (dw.eq(4), 2025),
        "gfsad_2015": (ee.ImageCollection("projects/sat-io/open-datasets/GFSAD/GCEP30").mosaic().eq(2), 2015),
    }
    return {k: (img.unmask(0).rename(k).toByte(), y) for k, (img, y) in maps.items()}


def agreement(ee):
    """Number of the 7 public maps that call each pixel crop (0-7)."""
    return ee.Image.cat([img for img, _ in public_maps(ee).values()]).reduce(ee.Reducer.sum()).rename("n_maps")


def strata(ee):
    """1 = A (0 maps say crop), 2 = B (1-2 maps), 3 = C (3 or more)."""
    n = agreement(ee)
    return ee.Image(1).where(n.gte(1), 2).where(n.gte(3), 3).rename("stratum").toByte()


def s2_monthly(ee, geom, year: int = YEAR):
    """12 cloud-masked monthly median Sentinel-2 composites (reflectance 0-1).

    Clouds masked with Cloud Score+ (cs_cdf >= 0.6). Months with no clear image
    stay masked here; features.py fills them from the neighbouring months.
    """
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(geom)
    cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")

    def month(m):
        start = ee.Date.fromYMD(year, m, 1)
        col = s2.filterDate(start, start.advance(1, "month")).linkCollection(cs, ["cs_cdf"])
        col = col.map(lambda i: i.updateMask(i.select("cs_cdf").gte(0.6))
                      .select(["B2", "B3", "B4", "B8", "B11", "B12"]).divide(10000))
        return col.median().set("month", m)

    return [month(m) for m in range(1, 13)]
