"""
The same window in every map: report figure 16, the updated version of the Sprint 2 slide "seven maps,
seven answers" (Twic county, before labelling). Now inside the study area, for 2025, with our Rule 1 map
and the labelled sample points as the reference.

    python cropland/eda_window.py fetch     Earth Engine, once: Sentinel-2 (October-December 2025), the
                                            seven public maps and Rule 1 on a 10 m grid over the window
                                            -> raw_data/cropland/eda/window_<name>.npz
    python cropland/eda_window.py figure    figure 16 + its CSV twin (no Earth Engine)

The window is the 6 x 6 km square around sample point S020, north of Aweil town: the square in Aweil
that holds the most labelled points (7). The figure shows the seven public maps in blue, as the poster
does; Rule 1 is fetched too but not drawn, because its pixels mean "a field lies within this pixel's
210 m box", a different unit. A dot is a labelled point (filled: the labellers saw cropland in its
210 m box; open: none). Under each map: its crop share of the window and how many of the labelled
cropland boxes it finds (any crop pixel in the box, the scoring rule of step 09).
"""

import sys

import numpy as np
import pandas as pd

import common as C
import eda_figures as FG
import eda_maps as EM

NAME, CENTRE, KM = "aweil_s020", ("S020", 8.937114, 27.367310), 6
MAPS = ["worldcover_2021", "glad_2019", "deafrica_2019", "worldcereal_2021", "esri_2025", "dynamicworld_2025", "gfsad_2015"]
OURS = "rule1_2026-10-12"
CACHE = EM.CACHE / f"window_{NAME}.npz"


def grid():
    _, lat, lon = CENTRE
    dy, dx = 10 / 110_540, 10 / (111_320 * np.cos(np.radians(lat)))       # 10 m in degrees
    n = int(KM * 1000 / 10)
    return {"dimensions": {"width": n, "height": n}, "crsCode": "EPSG:4326",
            "affineTransform": {"scaleX": dx, "shearX": 0, "translateX": lon - n / 2 * dx,
                                "shearY": 0, "scaleY": -dy, "translateY": lat + n / 2 * dy}}


def fetch():
    ee = C.ee_init()
    g = grid()
    t = g["affineTransform"]
    n = g["dimensions"]["width"]
    region = ee.Geometry.Rectangle([t["translateX"], t["translateY"] - n * -t["scaleY"], t["translateX"] + n * t["scaleX"], t["translateY"]])
    s2 = ee.ImageCollection(C.s2_monthly(ee, region.buffer(2000), C.YEAR)[9:12]).median().select(["B4", "B3", "B2"])
    maps = ee.Image.cat([img for k, (img, _) in C.public_maps(ee).items() if k in MAPS] +
                        [ee.Image(f"{C.ASSETS}/{OURS}_aweil").unmask(0).rename("rule1")]).toByte()
    get = lambda img: ee.data.computePixels({"expression": img, "fileFormat": "NUMPY_NDARRAY", "grid": g})
    rgb, m = get(s2.toFloat()), get(maps)
    np.savez_compressed(CACHE, rgb=np.dstack([rgb[b] for b in ("B4", "B3", "B2")]),
                        **{k: m[k] for k in m.dtype.names}, transform=np.array([t["translateX"], t["scaleX"], t["translateY"], t["scaleY"]]))
    print("saved", CACHE)


def points(transform, n):
    """Labelled points inside the window, with what each map says in their 210 m box (step 09's map_values)."""
    x0, dx, y0, dy = transform
    v = pd.read_csv(C.HERE / "results" / "map_values.csv")
    v = v[(v.lon >= x0) & (v.lon <= x0 + n * dx) & (v.lat <= y0) & (v.lat >= y0 + n * dy) & v.cropland_avg.notna()].copy()
    v["col"], v["row"] = (v.lon - x0) / dx, (v.lat - y0) / dy
    return v


def figure():
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    z = np.load(CACHE)
    rgb = np.clip(z["rgb"] * 3.2, 0, 1) ** 0.85                       # reflectance -> display
    n = rgb.shape[0]
    pts = points(z["transform"], n)
    crop = pts.cropland_avg > 0
    panels = sorted(MAPS, key=lambda k: z[k].mean())                  # least crop first, as on the poster
    fig, axes = plt.subplots(2, 4, figsize=(10, 6.1))
    axes = axes.ravel()
    axes[0].imshow(rgb, interpolation="bilinear")
    axes[0].set_title(f"Sentinel-2, Oct-Dec {C.YEAR}", fontsize=9.5)
    axes[0].set_xlabel(f"{len(pts)} labelled boxes, {int(crop.sum())} with cropland", fontsize=8.5, color=FG.INK2)
    twin = []
    for ax, k in zip(axes[1:], panels):
        ax.imshow(z[k], cmap=ListedColormap([FG.GRID_C, FG.SERIES[0]]), vmin=0, vmax=1, interpolation="nearest")
        hit = int(pts.loc[crop, k].sum()) if k in pts else 0
        ax.set_title(FG._name(k), fontsize=9.5)
        ax.set_xlabel(f"crop {100 * z[k].mean():.1f}% · finds {hit} of {int(crop.sum())}", fontsize=8.5, color=FG.INK2)
        twin.append({"map": k, "crop_share_of_window_pct": round(100 * z[k].mean(), 4), "labelled_cropland_points": int(crop.sum()),
                     "found": hit})
    for ax in axes:
        ax.scatter(pts.col[crop], pts.row[crop], s=26, color=FG.INK, edgecolor=FG.SURFACE, linewidth=1.0, zorder=3)
        ax.scatter(pts.col[~crop], pts.row[~crop], s=26, facecolor=FG.SURFACE, edgecolor=FG.INK, linewidth=1.0, zorder=3)
        ax.set_xticks([]), ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(FG.AXIS)
    axes[0].plot([n - 110, n - 10], [n - 25, n - 25], color="white", linewidth=3)
    axes[0].text(n - 60, n - 45, "1 km", color="white", ha="center", fontsize=8)
    fig.text(0.01, 0.005, f"The same {KM} x {KM} km window north of Aweil town in every map. Blue: the map says crop. Dots: labelled "
             "boxes (filled: cropland in the box); 'finds' counts the cropland boxes in which the map has any crop.",
             fontsize=8, color=FG.INK2)
    pd.DataFrame(twin).to_csv(EM.TABLES / f"window_{NAME}.csv", index=False)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return FG._save(fig, "16_same_window_every_map")


if __name__ == "__main__":
    {"fetch": fetch, "figure": lambda: print(figure())}[sys.argv[1]]()
