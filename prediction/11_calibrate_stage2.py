"""
Step 11 - Calibrate Stage 2's probabilities, without retraining.

Why. The ConvLSTM ranks pixels well (PR-AUC beats persistence) but its
probabilities are too high: its Brier score is worse than persistence in
every fold. Two things in training cause this on purpose:
  - focal loss rewards getting the ORDER of pixels right, not honest
    percentages;
  - half of every training batch is a patch that contains flooding, so the
    model sees far more water than the real ~0.3-5% base rate.
So a "40%" from the raw model does not mean 40%.

How. Platt scaling: a logistic regression on the model's own output,
    p_calibrated = 1 / (1 + exp(-(a * logit(p_raw) + b))),
with a and b fitted on validation-year pixels (the same uniform draw that
08_train_stage2.py uses to pick the decision threshold). Never on the test
years. Because the mapping only rises, the ORDER of pixels is unchanged, so
PR-AUC and F1 (at the mapped threshold) stay the same and only the
probability values move. Brier and the reliability curve show the effect.

Two parameters is deliberate: validation is only two years, and a flexible
calibrator (isotonic) would overfit them.

A limit to keep in mind: validation is the last two training years. If the
test years are wetter or drier than those (fold 6: calm 2016-17 validation,
crisis 2020-21 test), calibration can only be as right as that history.

Outputs (raw_data/prediction/stage2/):
  metrics_convlstm-calibrated_L{lead}_f{fold}.csv   scores, same columns as step 8
  calib_L{lead}_f{fold}.json                        a, b, thresholds, reliability histograms

Run: python prediction/11_calibrate_stage2.py --lead 3 6 --fold 5 6 7 8
(GPU: same LD_LIBRARY_PATH note as step 8. Each run takes ~8 minutes.)
"""

import argparse
import importlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

S2 = importlib.import_module("08_train_stage2")   # reuse its features, sampler and threshold search
STAGE2_OUT = S2.STAGE2_OUT
TAG = "convlstm-calibrated"


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


class Platt:
    """p -> sigmoid(a * logit(p) + b), fitted on validation pixels."""

    def fit(self, p, y):
        lr = LogisticRegression(C=1e6)   # effectively unregularised; only two numbers to fit
        lr.fit(logit(p).reshape(-1, 1), y)
        self.a, self.b = float(lr.coef_[0, 0]), float(lr.intercept_[0])
        return self

    def __call__(self, p):
        return 1.0 / (1.0 + np.exp(-(self.a * logit(p) + self.b)))


def validation_pixels(predict, feats, pairs):
    """Raw probabilities and truth for every scored pixel in the validation pairs."""
    X, Y, W = feats.batch(pairs)
    prob = np.concatenate([predict(X[i:i + 128]).numpy() for i in range(0, len(X), 128)])
    keep = W[..., 0] > 0
    return prob[..., 0][keep], Y[..., 0][keep].astype(bool)


def evaluate_both(predict, calib, feats, meta, test_issue, th_raw, th_cal, chunk=128):
    """Step 8's evaluate(), scoring raw and calibrated probabilities in one pass
    over the test block (the pass is the slow part)."""
    keep_groups = {g: feats.keep if c is None else feats.keep & (meta["class_map"] == c)
                   for g, c in C.GROUPS.items()}
    raw = {g: C.BinaryScores(th_raw) for g in C.GROUPS}
    cal = {g: C.BinaryScores(th_cal) for g in C.GROUPS}
    lo = int(test_issue.min()) - C.SEQ_LEN + 1
    hi = int(test_issue.max()) + feats.lead + 1
    for p0 in range(0, feats.flood.shape[0], chunk):
        patches = np.arange(p0, min(p0 + chunk, feats.flood.shape[0]))
        block = np.asarray(feats.flood[p0:patches[-1] + 1, lo:hi])
        for t in test_issue:
            i = int(t) - lo
            X = feats.build(block[:, i - C.SEQ_LEN + 1: i + 1], patches, np.full(len(patches), t))
            prob = predict(X).numpy()[..., 0]
            target = block[:, i + feats.lead]
            for g, keep in keep_groups.items():
                raw[g].update(prob, target, keep[patches])
                cal[g].update(calib(prob), target, keep[patches])
    return raw, cal


def calibrate_one(lead, fold, tf):
    run = f"convlstm_L{lead}_f{fold}"
    log = json.loads((STAGE2_OUT / f"log_{run}.json").read_text())
    y0, y1 = S2.FOLD_YEARS[fold]
    s = C.split(y0, y1, lead, min_issue=C.SEQ_LEN - 1, val_years=C.VAL_YEARS)

    flood, meta = C.load_dense()
    feats = S2.Features(flood, meta, lead, s["train"])
    model = tf.keras.models.load_model(STAGE2_OUT / f"{run}.keras", compile=False)
    predict = tf.function(lambda x: model(x, training=False),
                          input_signature=[tf.TensorSpec((None, C.SEQ_LEN, C.PATCH, C.PATCH, len(feats.channels)), tf.float32)])

    # Rebuild the exact validation draw of step 8: same seed, same order of draws.
    val_sampler = S2.Sampler(s["val"], meta["flood_count"], lead, np.random.default_rng(C.SEED + 1))
    val_sampler.draw(1024)                 # step 8 used this draw for early stopping
    pairs = val_sampler.uniform(2048)      # ... and this one for the threshold

    # Sanity check: the reloaded model must pick the same threshold as in training,
    # otherwise the inputs are not the ones it was trained on.
    th_raw, _ = S2.best_threshold(predict, feats, pairs)
    if abs(th_raw - log["threshold"]) > 1e-9:
        raise RuntimeError(f"{run}: threshold {th_raw} != logged {log['threshold']}; inputs differ from training")

    p_val, y_val = validation_pixels(predict, feats, pairs)
    calib = Platt().fit(p_val, y_val)
    th_cal = float(calib(np.array([th_raw]))[0])   # same decision, expressed on the calibrated scale
    print(f"{run}: a={calib.a:.3f} b={calib.b:.3f}; threshold {th_raw:.2f} -> {th_cal:.3f}; "
          f"validation base rate {y_val.mean():.4f}, mean raw prob {p_val.mean():.4f}, "
          f"mean calibrated {calib(p_val).mean():.4f}")

    e0 = time.time()
    raw, cal = evaluate_both(predict, calib, feats, meta, s["test"], th_raw, th_cal)
    rows = [{"model": TAG, "lead": lead, "fold": fold, "test_years": f"{y0}-{y1}", "group": g, **cal[g].result()}
            for g in C.GROUPS]
    pd.DataFrame(rows).to_csv(STAGE2_OUT / f"metrics_{TAG}_L{lead}_f{fold}.csv", index=False)
    (STAGE2_OUT / f"calib_L{lead}_f{fold}.json").write_text(json.dumps({
        "run": run, "a": calib.a, "b": calib.b, "threshold_raw": th_raw, "threshold_calibrated": th_cal,
        "val_pixels": int(len(y_val)), "val_base_rate": float(y_val.mean()),
        # reliability histograms, all flood-domain pixels: flooded / dry counts per probability bin
        "bins": C.N_BINS,
        "raw_pos": raw["all"].pos.tolist(), "raw_neg": raw["all"].neg.tolist(),
        "cal_pos": cal["all"].pos.tolist(), "cal_neg": cal["all"].neg.tolist(),
    }))
    r, c = raw["all"].result(), cal["all"].result()
    print(f"  test ({time.time() - e0:.0f}s): raw F1 {r['f1']:.3f} PR-AUC {r['pr_auc']:.3f} Brier {r['brier']:.4f} | "
          f"calibrated F1 {c['f1']:.3f} PR-AUC {c['pr_auc']:.3f} Brier {c['brier']:.4f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", type=int, nargs="+", required=True, choices=C.LEADS)
    ap.add_argument("--fold", type=int, nargs="+", required=True, choices=sorted(S2.FOLD_YEARS))
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()

    import tensorflow as tf
    for gpu in tf.config.list_physical_devices("GPU"):
        tf.config.experimental.set_memory_growth(gpu, True)
    C.set_seed(C.SEED, tf)
    for lead in args.lead:
        for fold in args.fold:
            if (STAGE2_OUT / f"metrics_{TAG}_L{lead}_f{fold}.csv").exists() and not args.redo:
                print(f"L{lead} f{fold}: already calibrated, skipping")
                continue
            calibrate_one(lead, fold, tf)
            tf.keras.backend.clear_session()


if __name__ == "__main__":
    main()
