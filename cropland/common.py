"""
Shared settings for the cropland scripts: Earth Engine project, study areas,
the public maps (and how each is turned into crop / not crop), and the
Sentinel-2 monthly composites. Every script imports this, so a change here
changes all of them.

Where, when and how much come from a config file in config/ (REUSE.md):
CROPLAND_CONFIG=<name> picks config/<name>.toml (or a path to a .toml file);
unset, it is config/south_sudan_2025.toml, the settings of our study.
"""

import csv
import json
import os
import tomllib
from pathlib import Path

import geopandas as gpd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
RAW = REPO / "raw_data"
OUT = RAW / "cropland"                      # large outputs, not in git
OUT.mkdir(parents=True, exist_ok=True)
# course data: raw_data/ in the repo, or the course folder next to the repo when raw_data/ only holds outputs
COURSE = next((p for p in (RAW, REPO.parent / "data-JBG060-2026") if (p / "flood_masks").exists()), RAW)


def load_config(name: str | None = None) -> dict:
    name = name or os.environ.get("CROPLAND_CONFIG", "south_sudan_2025")
    path = Path(name) if name.endswith(".toml") else HERE / "config" / f"{name}.toml"
    return tomllib.loads(path.read_text(encoding="utf-8"))


CONFIG = load_config()
GROUP_PROJECT = "grand-loop-457810-a1"      # Google Cloud project registered for Earth Engine; holds our assets
# Run on your own Earth Engine project with: set CROPLAND_EE_PROJECT=<your-project-id> (steps 04 and 05 only need public data)
EE_PROJECT = os.environ.get("CROPLAND_EE_PROJECT", GROUP_PROJECT)
ASSETS = f"projects/{EE_PROJECT}/assets/sample-points"      # in the project you run on (group project by default)
YEAR = CONFIG["study"]["year"]
SEED = CONFIG["study"]["seed"]
BOX_M = CONFIG["study"]["box_m"]             # the labelled unit: the outer yellow box, 210 m x 210 m (21 x 21 Sentinel-2 pixels) centred on a point

AREAS = CONFIG["areas"]                      # study areas: sampled, labelled and scored -> their admin-2 units
ALLOCATION = CONFIG["allocation"]            # points per stratum (METHODOLOGY.md section 3)
CALENDAR = CONFIG["calendar"]                # months of the crop season (features.py, the labelling tool)
BOUNDARIES = CONFIG["boundaries"]
ADMIN2 = COURSE / BOUNDARIES.get("admin2_file", "")      # an absolute path in the config stays absolute
ADMIN2_NAME = BOUNDARIES.get("admin2_name_column", "adm2_name")

if (HERE / "sample.csv").exists():                       # never write a new area's outputs over another study's
    with open(HERE / "sample.csv", newline="", encoding="utf-8") as f:
        if not {r["area"] for r in csv.DictReader(f)} <= set(AREAS):
            raise SystemExit(f"{HERE} holds another study (sample.csv); start {CONFIG['study']['name']} in a clean copy: "
                             "python cropland/make_new_area.py <folder> (REUSE.md)")


def ee_init():
    import ee
    ee.Initialize(project=EE_PROJECT)
    return ee


def _gaul(ee, level: int):
    return ee.FeatureCollection(f"FAO/GAUL/2015/level{level}").filter(
        ee.Filter.eq("ADM0_NAME", CONFIG["study"]["country"]))


def area_geometry(ee, area: str, simplify_deg: float = 0.0):
    """Earth Engine geometry of one study area (union of its counties)."""
    if BOUNDARIES["source"] == "gaul":
        geom = _gaul(ee, 2).filter(ee.Filter.inList("ADM2_NAME", AREAS[area])).geometry()
        return geom.simplify(simplify_deg * 111_000) if simplify_deg else geom
    admin = gpd.read_file(ADMIN2)
    geom = admin[admin[ADMIN2_NAME].isin(AREAS[area])].dissolve().geometry.iloc[0]
    if simplify_deg:
        geom = geom.simplify(simplify_deg)
    return ee.Geometry(json.loads(gpd.GeoSeries([geom], crs=4326).to_json())["features"][0]["geometry"])


def box(ee, lon: float, lat: float):
    """The BOX_M square centred on a point: the unit labellers label."""
    return ee.Geometry.Point(lon, lat).buffer(BOX_M / 2).bounds()


def country_geometry(ee):
    if BOUNDARIES["source"] == "gaul":
        return _gaul(ee, 0).geometry().simplify(1000)
    admin0 = gpd.read_file(COURSE / BOUNDARIES["admin0_file"])
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
        f"esri_{YEAR}": (esri.eq(5), YEAR),
        f"dynamicworld_{YEAR}": (dw.eq(4), YEAR),
        "gfsad_2015": (ee.ImageCollection("projects/sat-io/open-datasets/GFSAD/GCEP30").mosaic().eq(2), 2015),
    }
    return {k: (img.unmask(0).rename(k).toByte(), y) for k, (img, y) in maps.items()
            if k in CONFIG["strata"]["maps"]}                 # the maps the config chooses


def agreement(ee):
    """Number of the public maps (7 in our study) that call each pixel crop."""
    return ee.Image.cat([img for img, _ in public_maps(ee).values()]).reduce(ee.Reducer.sum()).rename("n_maps")


def strata(ee):
    """1 = A (0 maps say crop), 2 = B (1-2 maps), 3 = C (3 or more); the cuts come from the config."""
    n, s = agreement(ee), CONFIG["strata"]
    return ee.Image(1).where(n.gte(s["b_from"]), 2).where(n.gte(s["c_from"]), 3).rename("stratum").toByte()


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
