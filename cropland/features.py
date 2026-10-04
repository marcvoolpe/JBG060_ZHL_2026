"""
The machine features of METHODOLOGY.md section 5, as one Earth Engine image.

Each feature measures one cue of the labelling key, so the rules the decision
tree learns can be read in the same terms as the key. 06_fit_rules.py and
07_run_map.py both use this function, so the map uses exactly the features the
rules were fitted on.

Labellers judge the 210 m box around a point (common.BOX_M), and a box is crop
when there is cropland ANYWHERE in it. So every feature is first computed per
10 m pixel (pixel_features) and then summarised over the 21 x 21 pixel box
around each pixel (feature_image) by the most crop-like part of the box: the
10th percentile where crop is low (bare soil in spring, near buildings), the
90th percentile where crop is high (bare-soil index, green-up, harvest drop,
texture, edges), and the mean for the rest (trees, water, radar). One field
covering a tenth of the box then still moves the box's features. A pixel's
features describe the same box a labeller looked at, at the sample points and
in the map.
"""

import common as C

FEATURES = [
    # a. bare soil before sowing
    "ndvi_min_am", "bsi_max_am",
    # b. green-up
    "ndvi_peak_jja", "greenup",
    # c. harvest earlier than the grass around
    "drop_son", "drop_vs_500m",
    # d. field shape
    "texture_jja", "edge_density",
    # not crop: trees, water, settlement, burn
    "ndvi_min_jfm", "water_occurrence", "s1_vv_min", "dist_buildings_m", "burned",
    # cloudy months (radar)
    "vh_jun", "vh_jul", "vh_aug", "vh_sep", "vh_range",
]


def _fill(months):
    """Fill a masked month with the mean of its neighbours, then with either neighbour."""
    out = []
    for i, m in enumerate(months):
        prev, nxt = months[max(i - 1, 0)], months[min(i + 1, 11)]
        out.append(m.unmask(prev.add(nxt).divide(2)).unmask(prev).unmask(nxt))
    return out


# how each feature is summarised over the box: the end that points to crop
BOX_LOW = ["ndvi_min_am", "dist_buildings_m"]                                   # 10th percentile
BOX_HIGH = ["bsi_max_am", "greenup", "drop_son", "drop_vs_500m", "texture_jja", "edge_density"]   # 90th
BOX_MEAN = [f for f in FEATURES if f not in BOX_LOW + BOX_HIGH]


def feature_image(ee, geom, year: int = C.YEAR):
    """All features for one year, each summarised over the 210 m box around the pixel.

    The kernel is 100 m each side of the centre pixel: 21 x 21 pixels at 10 m.
    At the 30 m national scale Earth Engine rounds it to whole 30 m pixels.
    """
    px = pixel_features(ee, geom, year)
    box = ee.Kernel.square((C.BOX_M - 10) / 2, "meters")
    parts = [px.select(BOX_LOW).reduceNeighborhood(ee.Reducer.percentile([10]), box).rename(BOX_LOW),
             px.select(BOX_HIGH).reduceNeighborhood(ee.Reducer.percentile([90]), box).rename(BOX_HIGH),
             px.select(BOX_MEAN).reduceNeighborhood(ee.Reducer.mean(), box).rename(BOX_MEAN)]
    return ee.Image.cat(parts).select(FEATURES).float()


def pixel_features(ee, geom, year: int = C.YEAR):
    """All features for one year at each 10 m pixel. Sentinel-2 is Level-2A (surface reflectance)."""
    s2 = C.s2_monthly(ee, geom, year)
    ndvi = _fill([m.normalizedDifference(["B8", "B4"]) for m in s2])
    bsi = _fill([m.expression("((b('B11') + b('B4')) - (b('B8') + b('B2'))) / ((b('B11') + b('B4')) + (b('B8') + b('B2')))")
                 for m in s2])
    mn = lambda idx: ee.ImageCollection([ndvi[i] for i in idx]).min()
    mx = lambda idx: ee.ImageCollection([ndvi[i] for i in idx]).max()

    ndvi_min_am = mn([3, 4])                         # April, May (months are 0-based here)
    bsi_max_am = ee.ImageCollection([bsi[3], bsi[4]]).max()
    peak = mx([5, 6, 7])                             # June-August
    drop = peak.subtract(mn([8, 9, 10]))             # to September-November
    hood = drop.reduceNeighborhood(ee.Reducer.median(), ee.Kernel.square(250, "meters"))
    ndvi_int = peak.multiply(100).toInt().rename("ndvi")
    texture = ndvi_int.glcmTexture(size=1).select("ndvi_contrast")          # GLCM contrast, 3x3
    edges = ee.Algorithms.CannyEdgeDetector(peak, 0.08, 1).reduceNeighborhood(
        ee.Reducer.mean(), ee.Kernel.square(30, "meters"))

    buildings = (ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons").filterBounds(geom)
                 .reduceToImage(["confidence"], ee.Reducer.max()).gt(0))
    # distance in metres, the same at any output scale (10 m study areas, 30 m national map)
    # capped at 2.5 km: the kernel may be at most 512 pixels wide at 10 m
    dist = buildings.unmask(0).distance(ee.Kernel.euclidean(2500, "meters")).unmask(2500).min(2500)
    burned = (ee.ImageCollection("MODIS/061/MCD64A1").filterDate(f"{year - 1}-11-01", f"{year}-05-01")
              .select("BurnDate").max().gt(0).unmask(0))
    water = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").unmask(0)

    s1 = (ee.ImageCollection("COPERNICUS/S1_GRD").filterBounds(geom)
          .filter(ee.Filter.eq("instrumentMode", "IW"))
          .filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))   # only pass over South Sudan in 2025
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")))
    s1m = [s1.filterDate(ee.Date.fromYMD(year, m, 1), ee.Date.fromYMD(year, m, 1).advance(1, "month"))
           .select(["VV", "VH"]).mean() for m in range(1, 13)]
    vh = [m.select("VH") for m in s1m]
    vh_all = ee.ImageCollection(vh)

    img = ee.Image.cat([
        ndvi_min_am, bsi_max_am, peak, peak.subtract(ndvi_min_am), drop, drop.subtract(hood),
        texture, edges, mn([0, 1, 2]), water, ee.ImageCollection([m.select("VV") for m in s1m]).min(),
        dist, burned, vh[5], vh[6], vh[7], vh[8], vh_all.max().subtract(vh_all.min()),
    ]).rename(FEATURES)
    return img.float()


def sample_points(ee, df, geom_buffer_m: int = 2000, chunk: int = 100):
    """Feature values (box summaries) at the points of a DataFrame with id, lat, lon."""
    import pandas as pd
    rows = []
    for i in range(0, len(df), chunk):
        part = df.iloc[i:i + chunk]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(r.lon, r.lat), {"id": r.id}) for r in part.itertuples()])
        img = feature_image(ee, fc.geometry().buffer(geom_buffer_m))
        got = img.reduceRegions(fc, ee.Reducer.first(), scale=10, tileScale=4).getInfo()
        rows += [{"id": f["properties"]["id"], **{k: f["properties"].get(k) for k in FEATURES}} for f in got["features"]]
    return pd.DataFrame(rows)
