"""
Shared settings and helpers for the prediction scripts: paths, the dekad
time index, the train/test folds, seeding and scoring. Every script imports
these, so all of them use the same definitions.

Run the scripts with /usr/bin/python3.

Terms (more in README.md):
  dekad       10-day period; 3 per month (1-10, 11-20, 21-end), 36 per year
  t           dekad index: 0 = 1-10 Jan 2000, 935 = 21-31 Dec 2025
  issue time  the dekad a forecast is made; only data up to t may be used
  lead L      the forecast is for t + L (1 ~ 10 days, 3 ~ 1 month, 36 ~ 1 year)
  fold        one train/test split; training years always come before test years
"""

import contextlib
import os
import random
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------
# Paths. Resolved from this file's location, so scripts work no matter which
# directory they are launched from.
# --------------------------------------------------------------------------

REPO = Path(__file__).resolve().parents[1]          # group_repo/
PRED = REPO / "prediction"
RAW = REPO / "raw_data"                              # symlink to the data download
OUT = RAW / "prediction"                             # intermediate files (~3.6 GB), kept with the data
DELIVERABLES = REPO / "deliverables"                 # small shareable results
TABLES = DELIVERABLES / "tables"
FIGURES = DELIVERABLES / "figures"

ADMIN2 = RAW / "Administrative boundaries" / "ssd_admin2.geojson"
# Dipole Mode Index, monthly, from NOAA PSL: https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data
DMI_FILE = RAW / "DMI" / "dmi.had.long.data"


@contextlib.contextmanager
def repo_cwd():
    """Temporarily run inside group_repo/.

    The shared loaders in processing_data/loading.py open files with relative
    paths like './raw_data/...'. Rather than edit a file the whole group uses,
    we wrap each loader call in this, and put the working directory back
    afterwards so nothing else depends on where the script was started.
    """
    old = os.getcwd()
    os.chdir(REPO)
    try:
        yield
    finally:
        os.chdir(old)


def ensure_dirs(*dirs: Path) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Study area and grid
# --------------------------------------------------------------------------

STATES = ("Unity", "Jonglei", "Upper Nile")

# Native NASA MODIS/VIIRS flood-mask pixel size in degrees (~232 m).
RES = 0.0020833

# Stage 2 cuts the corridor into square patches, like INFLOW-AI v2.1 does.
# INFLOW uses 64 px with a 4 px border; we use 32 px with 2 px, the same 6.25%
# ratio. Border pixels are excluded from loss and metrics because a
# convolution near a patch edge cannot see its neighbours.
PATCH = 32
BORDER = 2

# --------------------------------------------------------------------------
# Time index
# --------------------------------------------------------------------------

YEAR0, YEAR1 = 2000, 2025
DEKADS_PER_YEAR = 36
N_DEKADS = (YEAR1 - YEAR0 + 1) * DEKADS_PER_YEAR    # 936


def dekad_of_year(dates) -> np.ndarray:
    """Calendar dekad 1..36 for each date. Same convention as INFLOW-AI's
    group_dates_by_decade: day 1-10 -> 1, 11-20 -> 2, 21-end -> 3 in the month."""
    import pandas as pd
    dates = pd.DatetimeIndex(dates)
    in_month = np.where(dates.day <= 10, 1, np.where(dates.day <= 20, 2, 3))
    return (dates.month.to_numpy() - 1) * 3 + in_month


def t_index(year, dekad):
    """(year, dekad-of-year 1..36) -> t. Works on scalars and arrays.
    Years before 2000 give negative t, which the driver table uses for
    lake history older than the flood record."""
    return (np.asarray(year) - YEAR0) * DEKADS_PER_YEAR + (np.asarray(dekad) - 1)


def year_dekad(t):
    """t -> (year, dekad-of-year 1..36)."""
    t = np.asarray(t)
    return YEAR0 + t // DEKADS_PER_YEAR, t % DEKADS_PER_YEAR + 1


def doy_index(t):
    """t -> dekad-of-year as 0..35, for indexing seasonal climatologies."""
    return np.asarray(t) % DEKADS_PER_YEAR


# --------------------------------------------------------------------------
# Forecast setup
# --------------------------------------------------------------------------

LEADS = (1, 3, 6, 9)                       # Stage 2 (per pixel)
# Stage 1 also goes much further ahead: 6, 9 and 12 months. Water leaving
# Lake Victoria takes ~9-17 months to reach the Sudd, so if the lakes carry
# a real early warning, it should show at these leads - where persistence
# is useless and seasonal climatology is the only serious competitor.
STAGE1_LEADS = LEADS + (18, 27, 36)
SEQ_LEN = 6            # Stage 2 looks at the last 6 dekads of flood maps
SEED = 42

# Rolling-origin folds: (fold id, first test year, last test year).
# Each fold trains on everything from 2000 up to the year before its test
# block, minus the embargo below. Fold 6 is the key one: trained only on
# the calm pre-2020 record, asked to forecast the 2020-2021 crisis.
FOLDS = (
    (1, 2010, 2011),
    (2, 2012, 2013),
    (3, 2014, 2015),
    (4, 2016, 2017),
    (5, 2018, 2019),
    (6, 2020, 2021),
    (7, 2022, 2023),
    (8, 2024, 2025),
)

# Extra two-year blocks before fold 1. They are not reported as folds; they
# exist only so Stage 1 can produce out-of-sample predictions for the
# early years that Stage 2 trains on (see 06_stage1_volume.py).
WALKFORWARD_BLOCKS = ((0, 2004, 2005), (0, 2006, 2007), (0, 2008, 2009)) + FOLDS

VAL_YEARS = 2          # tail of each training range used for early stopping


def block_bounds(first_year: int, last_year: int):
    """First and last t of a block of whole years."""
    return int(t_index(first_year, 1)), int(t_index(last_year, DEKADS_PER_YEAR))


def split(first_test_year: int, last_test_year: int, lead: int,
          min_issue: int = 0, embargo: int = SEQ_LEN, val_years: int = 0) -> dict:
    """Issue times for training, validation and testing in one fold.

    A sample is one forecast: issued at time t, predicting t + lead.

    TEST samples are those whose TARGET t + lead falls inside the test block.
    Defining the test set by target (not by issue time) means every lead is
    scored on exactly the same observed dekads, so the skill-vs-lead curve
    compares like with like.

    TRAIN samples must have their target strictly before the first test
    ISSUE time, with an extra gap of `embargo` dekads. Without this, a model
    could be trained on the flood map of, say, 5 Jan 2020, and then be
    "forecasting" 5 Jan 2020 from 26 Dec 2019 - it would already know the
    answer. The gap between the last training target and the first test
    target is therefore lead + embargo + 1 dekads.

    VALIDATION (optional) is the last `val_years` of the training range,
    separated from the remaining training data by the same rule. It is used
    for early stopping and choosing a decision threshold - never the test block.

    min_issue: earliest usable issue time (e.g. SEQ_LEN - 1 for Stage 2, which
    needs 6 past dekads; later for Stage 1, whose features have long lags).
    """
    test_lo, test_hi = block_bounds(first_test_year, last_test_year)

    test_targets = np.arange(test_lo, test_hi + 1)
    test_issue = test_targets - lead
    test_issue = test_issue[test_issue >= min_issue]

    # Last training target: before the first test issue time, minus embargo.
    last_train_target = test_lo - lead - 1 - embargo

    out = {"test": test_issue}
    if val_years:
        val_lo = last_train_target - val_years * DEKADS_PER_YEAR + 1
        val_targets = np.arange(val_lo, last_train_target + 1)
        out["val"] = val_targets - lead
        last_train_target = val_lo - lead - 1 - embargo

    train_targets = np.arange(min_issue + lead, last_train_target + 1)
    out["train"] = train_targets - lead
    out["last_train_target"] = last_train_target
    return out


# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------

def set_seed(seed: int = SEED, tf=None) -> str:
    """Seed Python, numpy and (if given) TensorFlow.

    Returns a note on whether TensorFlow's op-level determinism could be
    switched on. Some GPU kernels (possibly ConvLSTM's) refuse it; we then
    fall back to seed-only and log that, rather than claim results that
    are not actually bit-for-bit reproducible.
    """
    random.seed(seed)
    np.random.seed(seed)
    if tf is None:
        return "seeded (numpy/python)"
    tf.keras.utils.set_random_seed(seed)
    try:
        tf.config.experimental.enable_op_determinism()
        return "seeded + op determinism ON"
    except Exception as exc:  # noqa: BLE001 - report whatever TF says
        return f"seeded, op determinism UNAVAILABLE ({exc.__class__.__name__}); reruns may differ slightly"


# --------------------------------------------------------------------------
# Scoring a binary flood / no-flood forecast
# --------------------------------------------------------------------------

N_BINS = 200


class BinaryScores:
    """Accumulates scores for a probabilistic binary forecast over many
    pixels, without keeping every pixel in memory.

    A test set here is up to ~30 million pixel-dekads per fold, too many to
    hold as a list. Instead we keep a histogram of forecast probabilities,
    split by whether the pixel was actually flooded. From that histogram we
    can recover every metric we report:

    - precision: of the pixels we said would flood, how many did
    - recall: of the pixels that flooded, how many we caught
    - F1: balance of the two
    - CSI (critical success index): hits / (hits + misses + false alarms).
      The standard score in operational flood forecasting.
    - PR-AUC (average precision): quality across all thresholds, not just
      one. Useful when ~97% of pixels are dry and accuracy says little.
    - Brier score: mean squared error of the probability. Lower is better.
      Measures whether "70% chance" really means 70%.

    Forecasts that are just 0 or 1 (persistence, for example) work too; they
    simply land in the first and last bins.
    """

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.pos = np.zeros(N_BINS, dtype=np.int64)   # flooded pixels, by forecast prob
        self.neg = np.zeros(N_BINS, dtype=np.int64)   # dry pixels, by forecast prob
        self.tp = self.fp = self.fn = self.tn = 0
        self.brier_sum = 0.0

    def update(self, prob: np.ndarray, truth: np.ndarray, keep: np.ndarray) -> None:
        """prob: forecast probability; truth: 0/1 observed; keep: bool mask of
        pixels that count (in the flood domain, away from patch borders)."""
        p = prob[keep].astype(np.float64).ravel()
        y = truth[keep].astype(bool).ravel()
        if p.size == 0:
            return
        bins = np.minimum((p * N_BINS).astype(np.int64), N_BINS - 1)
        self.pos += np.bincount(bins[y], minlength=N_BINS)
        self.neg += np.bincount(bins[~y], minlength=N_BINS)
        yhat = p >= self.threshold
        self.tp += int(np.count_nonzero(yhat & y))
        self.fp += int(np.count_nonzero(yhat & ~y))
        self.fn += int(np.count_nonzero(~yhat & y))
        self.tn += int(np.count_nonzero(~yhat & ~y))
        self.brier_sum += float(np.sum((p - y) ** 2))

    def counts_at(self, threshold: float):
        """(tp, fp, fn) if the decision threshold were `threshold`, read off
        the histogram. Exact for thresholds on the 1/N_BINS grid."""
        first = int(round(threshold * N_BINS))
        tp = int(self.pos[first:].sum())
        fp = int(self.neg[first:].sum())
        fn = int(self.pos[:first].sum())
        return tp, fp, fn

    def best_threshold(self) -> float:
        """Threshold with the highest F1. Call this on VALIDATION scores,
        then apply the answer to test scores with at_threshold()."""
        best, best_f1 = 0.5, -1.0
        for th in np.arange(1, N_BINS) / N_BINS:
            tp, fp, fn = self.counts_at(th)
            f1 = 2 * tp / (2 * tp + fp + fn) if tp else 0.0
            if f1 > best_f1:
                best, best_f1 = float(th), f1
        return best

    def at_threshold(self, threshold: float) -> dict:
        """result(), but with the binary metrics recomputed at `threshold`."""
        tp, fp, fn = self.counts_at(threshold)
        n = self.tp + self.fp + self.fn + self.tn
        saved = (self.tp, self.fp, self.fn, self.tn, self.threshold)
        self.tp, self.fp, self.fn, self.tn, self.threshold = tp, fp, fn, n - tp - fp - fn, threshold
        try:
            return self.result()
        finally:
            self.tp, self.fp, self.fn, self.tn, self.threshold = saved

    def result(self) -> dict:
        n = self.tp + self.fp + self.fn + self.tn
        precision = self.tp / (self.tp + self.fp) if self.tp + self.fp else np.nan
        recall = self.tp / (self.tp + self.fn) if self.tp + self.fn else np.nan
        f1 = (2 * precision * recall / (precision + recall)
              if precision + recall > 0 else np.nan)
        csi_den = self.tp + self.fp + self.fn
        csi = self.tp / csi_den if csi_den else np.nan

        # Average precision: sweep the threshold from high to low bin by bin.
        tp_cum = np.cumsum(self.pos[::-1])
        fp_cum = np.cumsum(self.neg[::-1])
        total_pos = tp_cum[-1] if tp_cum.size else 0
        if total_pos:
            prec_curve = tp_cum / np.maximum(tp_cum + fp_cum, 1)
            rec_curve = tp_cum / total_pos
            rec_step = np.diff(np.concatenate([[0.0], rec_curve]))
            pr_auc = float(np.sum(rec_step * prec_curve))
        else:
            pr_auc = np.nan

        return {
            "n_cells": n,
            "n_flooded": self.tp + self.fn,
            "base_rate": (self.tp + self.fn) / n if n else np.nan,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "csi": csi,
            "pr_auc": pr_auc,
            "brier": self.brier_sum / n if n else np.nan,
            "threshold": self.threshold,
        }


# Groups every Stage 2 metric is reported for. The class map (built in
# 07_dense_arrays.py) labels each flood-capable pixel by NASA's own rule:
# 1 = "recurring" (floods in at least ~1/3 of years), 2 = "unusual" (rarer).
# It is a REPORTING lens only - never a model input - because NASA derives it
# from the full 2000-2025 record, which includes the future of early folds.
GROUPS = {"all": None, "unusual": 2, "recurring": 1}


def border_mask(domain: np.ndarray) -> np.ndarray:
    """Domain mask with the outer BORDER pixels of every patch switched off.
    domain: (..., PATCH, PATCH). Returns a bool array of the same shape."""
    keep = domain.astype(bool).copy()
    keep[..., :BORDER, :] = False
    keep[..., -BORDER:, :] = False
    keep[..., :, :BORDER] = False
    keep[..., :, -BORDER:] = False
    return keep


# --------------------------------------------------------------------------
# Loading the Stage 2 arrays built by 07_dense_arrays.py
# --------------------------------------------------------------------------

DENSE_META = OUT / "dense_meta.npz"
DENSE_FLOOD = OUT / "dense_flood.u8"


def load_dense():
    """Returns (flood, meta).

    flood: read-only memory map, shape (n_patches, 936, 32, 32), uint8 0/1.
    Stored patch-first so that one training sample - one patch over a run of
    consecutive dekads - is a single contiguous read from disk. The file is
    ~3.7 GB, so it is never loaded into RAM whole.

    meta: dict of the small static arrays (domain mask, class map, patch
    coordinates, ERA5 lookup indices, per-patch flood counts).
    """
    meta = dict(np.load(DENSE_META))
    n_patches = int(meta["patch_ids"].shape[0])
    flood = np.memmap(DENSE_FLOOD, dtype=np.uint8, mode="r",
                      shape=(n_patches, N_DEKADS, PATCH, PATCH))
    return flood, meta
