"""
Step 7 - turn the flood labels into image patches for Stage 2.

Stage 2 is a ConvLSTM: a neural network that reads a short "video" of flood
maps and predicts the next frame. It needs the data as images, not a table.
We cut the corridor into 32 x 32 pixel squares (~7.4 km a side) and keep
the 3,834 squares that contain at least one flood-domain pixel.

Outputs (in raw_data/prediction/):

  dense_flood.u8   (3834, 936, 32, 32) uint8 memory map: 1 = flooded that
                   dekad, 0 = not. ~3.7 GB on disk; scripts read slices of
                   it and never load it whole. Stored patch-first, so one
                   training sample (one patch, consecutive dekads) is one
                   contiguous read.

  dense_meta.npz   small static arrays:
    patch_ids    (3834, 2)       patch column / row in the corridor grid
    domain       (3834, 32, 32)  1 = pixel is in the flood domain
    class_map    (3834, 32, 32)  NASA type: 1 recurring, 2 unusual, 0 outside
                                 the domain. For REPORTING results by flood
                                 type only - never given to the model.
    flood_count  (3834, 936)     flooded pixels per patch per dekad. Used to
                                 find flood-containing samples quickly.
    era5_iy/ix   (3834, 32, 32)  for each pixel, the ERA5 grid cell it sits
                                 in (ERA5 cells are ~27 km, so a 7 km patch
                                 falls in one or two cells).
    grid_origin  (2,)            lon, lat of grid cell (0, 0)

~5 min.

Run: python prediction/07_dense_arrays.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

CHUNK = 256          # patches built in RAM at a time (~250 MB)


def main() -> None:
    t0 = time.time()
    ever = pd.read_parquet(C.OUT / "ever_flooded_pixels.parquet")
    lon0 = float(np.median(ever["lon"] - ever["gx"] * C.RES))
    lat0 = float(np.median(ever["lat"] - ever["gy"] * C.RES))

    # Patch key: one integer per (patch column, patch row).
    stride = 10_000
    def patch_key(gx, gy):
        return (np.asarray(gx) // C.PATCH) * stride + np.asarray(gy) // C.PATCH

    keys = np.unique(patch_key(ever["gx"], ever["gy"]))
    n_patches = keys.size
    patch_ids = np.stack([keys // stride, keys % stride], axis=1).astype(np.int32)
    print(f"{n_patches} non-empty patches")

    domain = np.zeros((n_patches, C.PATCH, C.PATCH), np.uint8)
    p_ever = np.searchsorted(keys, patch_key(ever["gx"], ever["gy"]))
    domain[p_ever, ever["gy"].to_numpy() % C.PATCH, ever["gx"].to_numpy() % C.PATCH] = 1

    lab = pd.read_parquet(C.OUT / "dekadal_labels.parquet")
    t = C.t_index(lab["year"].to_numpy(), lab["dekad"].to_numpy())
    p = np.searchsorted(keys, patch_key(lab["gx"], lab["gy"]))
    ly = lab["gy"].to_numpy() % C.PATCH
    lx = lab["gx"].to_numpy() % C.PATCH
    label = lab["label"].to_numpy()
    assert (keys[p] == patch_key(lab["gx"], lab["gy"])).all(), "a flooded pixel lies outside every patch"
    del lab

    # Recurring vs unusual, per pixel: whichever NASA label it carried more
    # often. 99.1% of domain pixels only ever carry one of the two.
    pix = (p * C.PATCH + ly) * C.PATCH + lx
    n_rec = np.bincount(pix[label == 1], minlength=n_patches * C.PATCH * C.PATCH)
    n_unu = np.bincount(pix[label == 2], minlength=n_patches * C.PATCH * C.PATCH)
    class_map = np.where(n_rec + n_unu == 0, 0, np.where(n_rec > n_unu, 1, 2)).astype(np.uint8)
    class_map = class_map.reshape(n_patches, C.PATCH, C.PATCH) * domain

    # Flood array, written chunk by chunk so RAM use stays small.
    flood = np.memmap(C.DENSE_FLOOD, dtype=np.uint8, mode="w+",
                      shape=(n_patches, C.N_DEKADS, C.PATCH, C.PATCH))
    flood_count = np.zeros((n_patches, C.N_DEKADS), np.int16)
    order = np.argsort(p, kind="stable")
    bounds = np.searchsorted(p[order], np.arange(0, n_patches + CHUNK, CHUNK))
    for i, start in enumerate(range(0, n_patches, CHUNK)):
        stop = min(start + CHUNK, n_patches)
        rows = order[bounds[i]:bounds[i + 1]]
        block = np.zeros((stop - start, C.N_DEKADS, C.PATCH, C.PATCH), np.uint8)
        block[p[rows] - start, t[rows], ly[rows], lx[rows]] = 1
        flood[start:stop] = block
        flood_count[start:stop] = block.sum(axis=(2, 3))
    flood.flush()
    print(f"flood array written ({time.time() - t0:.0f}s)")

    # Nearest ERA5 cell for every pixel.
    era = np.load(C.OUT / "era5_corridor_grid.npz")
    gx = patch_ids[:, 0, None, None] * C.PATCH + np.arange(C.PATCH)[None, None, :]
    gy = patch_ids[:, 1, None, None] * C.PATCH + np.arange(C.PATCH)[None, :, None]
    lon = lon0 + gx * C.RES
    lat = lat0 + gy * C.RES
    era5_ix = np.abs(lon[..., None] - era["lon"]).argmin(-1).astype(np.int16)
    era5_iy = np.abs(lat[..., None] - era["lat"]).argmin(-1).astype(np.int16)
    era5_ix = np.broadcast_to(era5_ix, (n_patches, C.PATCH, C.PATCH)).copy()
    era5_iy = np.broadcast_to(era5_iy, (n_patches, C.PATCH, C.PATCH)).copy()

    np.savez_compressed(C.DENSE_META, patch_ids=patch_ids, domain=domain, class_map=class_map,
                        flood_count=flood_count, era5_iy=era5_iy, era5_ix=era5_ix,
                        grid_origin=np.array([lon0, lat0]))

    # Checks: every label landed exactly once, and totals match step 5.
    total = int(flood_count.sum(dtype=np.int64))
    assert total == len(t), f"{total:,} flooded cells written, {len(t):,} labels"
    assert not (flood_count.sum(axis=1) > 0)[domain.reshape(n_patches, -1).sum(1) == 0].any()
    drivers = pd.read_csv(C.OUT / "driver_table.csv", index_col="t")
    assert np.array_equal(flood_count.sum(axis=0), drivers.loc[0:, "volume"].to_numpy().astype(int)), \
        "patch totals disagree with driver_table volume"
    in_domain = domain.astype(bool)
    print(f"domain pixels {in_domain.sum():,}; recurring {(class_map == 1).sum():,}, unusual {(class_map == 2).sum():,}")
    print(f"flooded pixel-dekads {total:,}; checks passed ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
