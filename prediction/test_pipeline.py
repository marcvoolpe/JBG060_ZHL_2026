"""
Quick checks on the pipeline (a few seconds):

    python prediction/test_pipeline.py

Checks that test data never reaches training, that the forecast target is
really L dekads after the last input, that Stage 1 features use training
years only, that every model result has its baselines next to it, and that
the scores are computed correctly. Checks that need outputs of later steps
are skipped until those files exist.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

SKIPPED = []


def skip(name: str, why: str) -> None:
    SKIPPED.append(f"{name}: {why}")


# --------------------------------------------------------------------------
# 1. Folds never leak
# --------------------------------------------------------------------------

def test_folds_do_not_leak():
    """For every fold, lead and min_issue we use: training targets finish
    before the first test issue time, with the embargo in between; the three
    sets are disjoint; nothing falls outside the 2000-2025 record."""
    for _, y0, y1 in C.WALKFORWARD_BLOCKS:
        for lead in C.STAGE1_LEADS:
            for min_issue in (C.SEQ_LEN - 1, 18):
                for val_years in (0, C.VAL_YEARS):
                    s = C.split(y0, y1, lead, min_issue=min_issue, val_years=val_years)
                    train, test = s["train"], s["test"]
                    assert len(test) > 0, (y0, lead)
                    if len(train) == 0:
                        continue
                    last_train_target = train.max() + lead
                    first_test_issue = test.min()
                    assert last_train_target + C.SEQ_LEN < first_test_issue, (
                        f"block {y0}-{y1} lead {lead}: training target "
                        f"{last_train_target} is within the embargo of test issue {first_test_issue}")
                    assert np.intersect1d(train, test).size == 0
                    assert train.min() >= min_issue and test.min() >= min_issue
                    assert (test + lead).max() <= C.N_DEKADS - 1
                    if "val" in s:
                        val = s["val"]
                        assert train.max() + lead + C.SEQ_LEN < val.min(), "train leaks into val"
                        assert val.max() + lead + C.SEQ_LEN < first_test_issue, "val leaks into test"


def test_test_targets_identical_across_leads():
    """Every lead is scored on the same observed dekads, so skill can be
    compared across leads."""
    for _, y0, y1 in C.FOLDS:
        lo, hi = C.block_bounds(y0, y1)
        for lead in C.STAGE1_LEADS:
            targets = C.split(y0, y1, lead, min_issue=0)["test"] + lead
            assert targets.min() == lo and targets.max() == hi, (y0, lead)


def test_time_index_roundtrip():
    t = np.arange(C.N_DEKADS)
    y, d = C.year_dekad(t)
    assert np.array_equal(C.t_index(y, d), t)
    assert C.t_index(2000, 1) == 0 and C.t_index(2025, 36) == C.N_DEKADS - 1
    import pandas as pd
    assert list(C.dekad_of_year(pd.to_datetime(["2020-01-10", "2020-01-11", "2020-01-31", "2020-12-21"]))) == [1, 2, 3, 36]


# --------------------------------------------------------------------------
# 2. The lead is real
# --------------------------------------------------------------------------

def test_lead_is_real():
    """Build a fake flood array in which each dekad's map is filled with its
    own index t. Then the target returned for a sample issued at t must be
    exactly t + lead, and the inputs must be t-5 .. t."""
    stage2 = _import("08_train_stage2")
    if stage2 is None:
        return skip("test_lead_is_real", "08_train_stage2.py not importable yet")
    n_patches = 2
    fake = np.zeros((n_patches, C.N_DEKADS, C.PATCH, C.PATCH), dtype=np.int16)
    fake[:] = np.arange(C.N_DEKADS, dtype=np.int16)[None, :, None, None]
    for lead in C.LEADS:
        for t in (C.SEQ_LEN - 1, 100, C.N_DEKADS - 1 - lead):
            inputs, target = stage2.sample_window(fake, 1, t, lead)
            assert int(target[0, 0]) == t + lead, f"lead {lead}: target is {target[0, 0]}, want {t + lead}"
            assert list(inputs[:, 0, 0]) == list(range(t - C.SEQ_LEN + 1, t + 1))


# --------------------------------------------------------------------------
# 3. Fold-local statistics
# --------------------------------------------------------------------------

def test_stage1_features_are_fold_local():
    """Stage 1 turns raw drivers into anomalies against a seasonal
    climatology, which must come from training years only. Blank out every
    value after the training range and rebuild the features: the training
    rows must come out identical."""
    stage1 = _import("06_stage1_volume")
    if stage1 is None or not (C.OUT / "driver_table.csv").exists():
        return skip("test_stage1_features_are_fold_local", "needs 06_stage1_volume.py and raw_data/prediction/driver_table.csv")
    import pandas as pd
    table = pd.read_csv(C.OUT / "driver_table.csv", index_col="t")
    s = C.split(2020, 2021, 3, min_issue=stage1.MIN_ISSUE)
    cutoff = s["last_train_target"]
    X_full = stage1.build_features(table, cutoff)
    blanked = table.copy()
    blanked.loc[blanked.index > cutoff, [c for c in blanked.columns if c not in ("year", "dekad")]] = np.nan
    X_blank = stage1.build_features(blanked, cutoff)
    rows = s["train"]
    a, b = X_full.loc[rows].to_numpy(), X_blank.loc[rows].to_numpy()
    assert np.allclose(a, b, equal_nan=True), "training features changed when future values were removed - leak"


# --------------------------------------------------------------------------
# 4. Baselines are always reported
# --------------------------------------------------------------------------

def test_baselines_present():
    """Every model result must sit next to persistence and climatology at
    the same lead and fold."""
    path = C.TABLES / "stage2_skill.csv"
    if not path.exists():
        return skip("test_baselines_present", f"{path.name} not produced yet (run 10_evaluate.py)")
    import pandas as pd
    df = pd.read_csv(path)
    df = df[df["group"] == "all"]
    for (lead, fold), g in df.groupby(["lead", "fold"]):
        models = set(g["model"])
        if models & {"convlstm"}:
            assert {"persistence", "climatology"} <= models, f"lead {lead} fold {fold}: baselines missing"

    path1 = C.TABLES / "stage1_skill.csv"
    if path1.exists():
        s1 = pd.read_csv(path1)
        for (lead, fold), g in s1.groupby(["lead", "fold"]):
            assert {"persistence", "climatology"} <= set(g["model"]), f"stage 1 lead {lead} fold {fold}: baselines missing"


# --------------------------------------------------------------------------
# 5. Scoring maths
# --------------------------------------------------------------------------

def test_binary_scores():
    """Check the histogram-based scores against a hand-computable case."""
    s = C.BinaryScores(threshold=0.5)
    prob = np.array([0.9, 0.8, 0.2, 0.1, 0.7, 0.3])
    truth = np.array([1, 1, 1, 0, 0, 0])
    s.update(prob, truth, np.ones(6, dtype=bool))
    r = s.result()
    # predicted flood: 0.9, 0.8, 0.7 -> TP=2, FP=1; missed: 0.2 -> FN=1
    assert (s.tp, s.fp, s.fn, s.tn) == (2, 1, 1, 2)
    assert abs(r["precision"] - 2 / 3) < 1e-9 and abs(r["recall"] - 2 / 3) < 1e-9
    assert abs(r["csi"] - 0.5) < 1e-9
    expected_brier = np.mean((prob - truth) ** 2)
    assert abs(r["brier"] - expected_brier) < 1e-9
    # re-thresholding from the histogram must agree with direct counting
    assert s.counts_at(0.5) == (2, 1, 1)
    assert s.at_threshold(0.75)["recall"] == 2 / 3 and s.counts_at(0.75) == (2, 0, 1)
    assert s.result()["threshold"] == 0.5, "at_threshold must not change the stored threshold"
    # a perfect ranking has PR-AUC 1
    p = C.BinaryScores()
    p.update(np.array([0.95, 0.9, 0.1, 0.05]), np.array([1, 1, 0, 0]), np.ones(4, dtype=bool))
    assert abs(p.result()["pr_auc"] - 1.0) < 1e-9


def test_dense_arrays_shape():
    if not C.DENSE_META.exists():
        return skip("test_dense_arrays_shape", "run 07_dense_arrays.py first")
    flood, meta = C.load_dense()
    assert flood.shape[1:] == (C.N_DEKADS, C.PATCH, C.PATCH)
    assert meta["domain"].shape == meta["class_map"].shape == (flood.shape[0], C.PATCH, C.PATCH)
    assert set(np.unique(meta["class_map"][meta["domain"] == 1])) <= {1, 2}
    sample = np.asarray(flood[:, 800])
    assert set(np.unique(sample)) <= {0, 1}
    assert not sample[meta["domain"] == 0].any(), "flood outside the flood domain"


# --------------------------------------------------------------------------

def _import(name: str):
    import importlib
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if name in str(exc):
            return None
        raise


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in tests:
        try:
            n_skipped = len(SKIPPED)
            fn()
            if len(SKIPPED) == n_skipped:
                print(f"  ok    {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL  {fn.__name__}: {exc}")
    for s in SKIPPED:
        print(f"  skip  {s}")
    print(f"\n{len(tests) - failed - len(SKIPPED)} passed, {failed} failed, {len(SKIPPED)} skipped")
    sys.exit(1 if failed else 0)
