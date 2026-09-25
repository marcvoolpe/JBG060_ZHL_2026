"""
Step 8 - Stage 2: WHERE will it be flooded, L dekads ahead.

For every ~232 m pixel in a 32 x 32 patch, the model outputs the probability
that the pixel is flooded at t + L, given what is known at issue time t.

Architecture: a ConvLSTM, the same family as INFLOW-AI v2.1's spatial model.
A ConvLSTM is an LSTM (a network with memory, reading a sequence step by
step) whose internal state is an image rather than a list of numbers, so it
can learn how flood patterns spread, persist and drain across space.

  INFLOW v2.1 (from its saved config):  ConvLSTM 64 -> 128 -> 128, then
      Conv2D 64 -> Conv2D 1 with sigmoid; 64 x 64 patches, 6 input steps.
  Ours:  ConvLSTM 32 -> 64, then Conv2D 32 -> Conv2D 1 with sigmoid;
      32 x 32 patches, 6 input steps. Smaller because we have one corridor
      and a 6 GB laptop GPU. The sigmoid output (one flooded/not-flooded
      probability per pixel) is exactly INFLOW's.

Input: 6 consecutive dekads, t-5 .. t, each with these channels (INFLOW
stacks 5 channels too: inundation, rain, soil moisture, elevation, basin):

  flood     that dekad's observed flood map (0/1)
  rain      ERA5 rainfall on the pixel's ~27 km cell, log-scaled
  runoff    ERA5 runoff, log-scaled (we have no soil-moisture data)
  domain    1 inside the flood domain (INFLOW's "basin" channel)
  stage1    Stage 1's forecast of total corridor flooding at t + L, the
            same value over the whole patch. Comes from walk-forward
            predictions, so it was never fitted to the answer.

We have no elevation map. The Sudd is extremely flat (~1:10,000), so a
global elevation model's error would be larger than the real relief.

Loss: focal loss (it focuses training on the pixels the model finds hard,
down-weighting the many easy dry ones), counted only on flood-domain pixels
away from patch edges. Unlike INFLOW's version, whose mask is all ones and
so only trims the border, ours really skips pixels outside the domain.

Sampling. There are ~3 million (patch, dekad) training pairs; a full pass
would take hours per epoch on this GPU, and most pairs are entirely dry.
So each batch is half pairs whose target patch contains flooding, half
drawn uniformly, and we log how many distinct pairs were actually seen.
Evaluation always uses every test pair, unweighted.

Outputs (raw_data/prediction/stage2/): model .keras, metrics CSV, training log JSON.

Run:  /usr/bin/python3 prediction/08_train_stage2.py --lead 3 --fold 8
      ... --no-stage1   (ablation: drop the Stage 1 channel)
      ... --no-era5     (ablation: drop the rain and runoff channels)

GPU: TensorFlow needs the CUDA-12 libraries on LD_LIBRARY_PATH, e.g.
     LD_LIBRARY_PATH=~/.local/share/nvidia-cu12-shim/lib /usr/bin/python3 ...
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

STAGE2_OUT = C.OUT / "stage2"
FOLD_YEARS = {f: (y0, y1) for f, y0, y1 in C.FOLDS}


# --------------------------------------------------------------------------
# Samples
# --------------------------------------------------------------------------

def sample_window(flood, p: int, t: int, lead: int):
    """The raw data for one forecast: patch p, issued at dekad t.

    Returns (inputs, target):
      inputs  flood maps for t-5 .. t        shape (6, 32, 32)
      target  flood map at t + lead           shape (32, 32)

    This is the only place the lead is applied (checked in test_pipeline.py).
    """
    window = np.asarray(flood[p, t - C.SEQ_LEN + 1: t + lead + 1])   # one contiguous read
    return window[:C.SEQ_LEN], window[C.SEQ_LEN + lead - 1]


class Features:
    """Builds the model's input tensor for any (patch, issue time)."""

    def __init__(self, flood, meta, lead, train_issue, use_era5=True, use_stage1=True):
        self.flood, self.lead = flood, lead
        self.domain = meta["domain"].astype(np.float32)
        self.keep = C.border_mask(meta["domain"])
        self.channels = ["flood"] + (["rain", "runoff"] if use_era5 else []) + ["domain"] \
            + (["stage1"] if use_stage1 else [])

        if use_era5:
            era = np.load(C.OUT / "era5_corridor_grid.npz")
            self.iy, self.ix = meta["era5_iy"], meta["era5_ix"]
            # log(1 + mm), then z-scored with statistics from training dekads only
            self.era = {}
            for name, var in (("rain", "tp"), ("runoff", "ro")):
                g = np.log1p(np.maximum(era[var], 0.0))
                used = g[np.unique(np.concatenate([train_issue - k for k in range(C.SEQ_LEN)]))]
                self.era[name] = ((g - used.mean()) / (used.std() or 1.0)).astype(np.float32)

        if use_stage1:
            wf = load_walkforward(lead)
            s1 = np.full(C.N_DEKADS, np.nan)
            s1[wf["t_issue"].to_numpy()] = np.log1p(wf["pred_volume"].to_numpy())
            mu, sd = np.nanmean(s1[train_issue]), np.nanstd(s1[train_issue]) or 1.0
            self.stage1 = np.nan_to_num((s1 - mu) / sd).astype(np.float32)

    def build(self, windows: np.ndarray, patches: np.ndarray, issue: np.ndarray) -> np.ndarray:
        """Stack the input channels for a batch, all at once.

        windows: (B, 6, 32, 32) flood maps t-5..t; patches, issue: (B,).
        Returns (B, 6, 32, 32, n_channels) float32.
        """
        planes = [windows.astype(np.float32)]
        if "rain" in self.channels:
            steps = issue[:, None] + np.arange(-C.SEQ_LEN + 1, 1)[None, :]           # (B, 6)
            iy = self.iy[patches][:, None]                                          # (B, 1, 32, 32)
            ix = self.ix[patches][:, None]
            for name in ("rain", "runoff"):
                planes.append(self.era[name][steps[:, :, None, None], iy, ix])     # (B, 6, 32, 32)
        planes.append(np.broadcast_to(self.domain[patches][:, None], windows.shape))
        if "stage1" in self.channels:
            planes.append(np.broadcast_to(self.stage1[issue][:, None, None, None], windows.shape))
        return np.stack(planes, axis=-1)

    def batch(self, pairs):
        """Training / validation batch from (issue time, patch) pairs."""
        pairs = np.asarray(pairs)
        issue, patches = pairs[:, 0], pairs[:, 1]
        windows, targets = zip(*(sample_window(self.flood, p, t, self.lead) for t, p in pairs))
        X = self.build(np.stack(windows), patches, issue)
        return (X, np.stack(targets).astype(np.float32)[..., None],
                self.keep[patches].astype(np.float32)[..., None])


def load_walkforward(lead: int) -> pd.DataFrame:
    """Stage 1 walk-forward forecasts (default "change" target) for one lead."""
    path = C.OUT / "stage1" / "walkforward.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing; run 06_stage1_volume.py first")
    wf = pd.read_csv(path)
    wf = wf[wf["lead"] == lead]
    if wf.empty:
        raise ValueError(f"no Stage 1 forecasts for lead {lead} in {path}")
    return wf


class Sampler:
    """Half the batch from pairs whose target contains flooding, half uniform."""

    def __init__(self, issue, flood_count, lead, rng):
        self.issue, self.rng = np.asarray(issue), rng
        n_patches = flood_count.shape[0]
        wet_p, wet_i = np.nonzero(flood_count[:, self.issue + lead] > 0)
        self.wet = np.stack([self.issue[wet_i], wet_p], axis=1)
        self.n_patches = n_patches
        self.total_pairs = len(self.issue) * n_patches
        self.seen = set()

    def draw(self, n):
        half = n // 2
        wet = self.wet[self.rng.integers(0, len(self.wet), half)]
        uni = np.stack([self.rng.choice(self.issue, n - half), self.rng.integers(0, self.n_patches, n - half)], axis=1)
        pairs = np.concatenate([wet, uni])
        self.seen.update(map(tuple, pairs.tolist()))
        return pairs

    def uniform(self, n):
        return np.stack([self.rng.choice(self.issue, n), self.rng.integers(0, self.n_patches, n)], axis=1)


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

def build_model(tf, n_channels: int, filters=(32, 64)):
    L = tf.keras.layers
    inp = tf.keras.Input((C.SEQ_LEN, C.PATCH, C.PATCH, n_channels))
    x = L.ConvLSTM2D(filters[0], 3, padding="same", return_sequences=True)(inp)
    x = L.BatchNormalization()(x)
    x = L.ConvLSTM2D(filters[1], 3, padding="same", return_sequences=False)(x)
    x = L.BatchNormalization()(x)
    x = L.Dropout(0.3)(x)
    x = L.Conv2D(32, 3, padding="same", activation="relu")(x)
    out = L.Conv2D(1, 1, activation="sigmoid")(x)
    return tf.keras.Model(inp, out)


def focal_loss(tf, gamma=2.0):
    """Binary focal loss averaged over the pixels that count (weight 1).
    Class balance is handled by the sampler, so no extra alpha weighting."""
    def loss(y, prob, w):
        prob = tf.clip_by_value(prob, 1e-7, 1 - 1e-7)
        p_t = y * prob + (1 - y) * (1 - prob)
        per_pixel = -tf.pow(1 - p_t, gamma) * tf.math.log(p_t)
        return tf.reduce_sum(per_pixel * w) / (tf.reduce_sum(w) + 1e-7)
    return loss


# --------------------------------------------------------------------------
# Evaluation over every test pair
# --------------------------------------------------------------------------

def evaluate(predict, feats, meta, test_issue, threshold, chunk=128):
    """Score every (patch, test dekad) pair.

    Reads each group of patches' whole test period from disk in one go and
    slides the 6-dekad window along it, instead of reading pair by pair.
    """
    scores = {g: C.BinaryScores(threshold) for g in C.GROUPS}
    keep_groups = {g: feats.keep if c is None else feats.keep & (meta["class_map"] == c)
                   for g, c in C.GROUPS.items()}
    lo = int(test_issue.min()) - C.SEQ_LEN + 1
    hi = int(test_issue.max()) + feats.lead + 1
    n_patches = feats.flood.shape[0]
    for p0 in range(0, n_patches, chunk):
        patches = np.arange(p0, min(p0 + chunk, n_patches))
        block = np.asarray(feats.flood[p0:patches[-1] + 1, lo:hi])               # (P, T, 32, 32)
        for t in test_issue:
            i = int(t) - lo
            windows = block[:, i - C.SEQ_LEN + 1: i + 1]
            target = block[:, i + feats.lead]
            X = feats.build(windows, patches, np.full(len(patches), t))
            prob = predict(X).numpy()[..., 0]
            for g, keep in keep_groups.items():
                scores[g].update(prob, target, keep[patches])
    return {g: s.result() for g, s in scores.items()}


def best_threshold(predict, feats, pairs):
    """Decision threshold that maximises F1 on validation pairs drawn
    uniformly (the real mix of wet and dry), never on the test block."""
    X, Y, W = feats.batch(pairs)
    prob = np.concatenate([predict(X[i:i + 128]).numpy() for i in range(0, len(X), 128)])
    keep = W[..., 0] > 0
    p, y = prob[..., 0][keep], Y[..., 0][keep].astype(bool)
    best, best_f1 = 0.5, -1.0
    for th in np.linspace(0.05, 0.95, 19):
        tp = np.sum((p >= th) & y); fp = np.sum((p >= th) & ~y); fn = np.sum((p < th) & y)
        f1 = 2 * tp / (2 * tp + fp + fn) if tp else 0.0
        if f1 > best_f1:
            best, best_f1 = float(th), float(f1)
    return best, best_f1


# --------------------------------------------------------------------------

def run_name(args, lead, fold):
    tag = "convlstm" + ("_no-era5" if args.no_era5 else "") + ("_no-stage1" if args.no_stage1 else "")
    return tag, f"{tag}_L{lead}_f{fold}"


def train_one(args, lead, fold, tf):
    determinism = C.set_seed(C.SEED, tf)
    rng = np.random.default_rng(C.SEED)
    tag, run = run_name(args, lead, fold)
    y0, y1 = FOLD_YEARS[fold]
    s = C.split(y0, y1, lead, min_issue=C.SEQ_LEN - 1, val_years=C.VAL_YEARS)

    flood, meta = C.load_dense()
    feats = Features(flood, meta, lead, s["train"], not args.no_era5, not args.no_stage1)
    sampler = Sampler(s["train"], meta["flood_count"], lead, rng)
    val_sampler = Sampler(s["val"], meta["flood_count"], lead, np.random.default_rng(C.SEED + 1))
    Xv, Yv, Wv = feats.batch(val_sampler.draw(1024))

    print(f"{run}: test {y0}-{y1}, {len(s['train'])} train / {len(s['val'])} val / {len(s['test'])} test issue dekads")
    print(f"channels {feats.channels}; GPUs {tf.config.list_physical_devices('GPU')}; {determinism}")

    model = build_model(tf, len(feats.channels))
    loss_fn = focal_loss(tf)
    opt = tf.keras.optimizers.Adam(1e-3)

    @tf.function
    def train_step(x, y, w):
        with tf.GradientTape() as tape:
            loss = loss_fn(y, model(x, training=True), w)
        opt.apply_gradients(zip(tape.gradient(loss, model.trainable_variables), model.trainable_variables))
        return loss

    def val_loss():
        return float(np.mean([loss_fn(Yv[i:i + 128], model(Xv[i:i + 128], training=False), Wv[i:i + 128]).numpy()
                              for i in range(0, len(Xv), 128)]))

    t0, history, best, best_weights, waited = time.time(), [], np.inf, None, 0
    for epoch in range(args.max_epochs):
        e0 = time.time()
        losses = [float(train_step(*feats.batch(sampler.draw(args.batch)))) for _ in range(args.steps)]
        vl = val_loss()
        history.append({"epoch": epoch + 1, "train_loss": float(np.mean(losses)), "val_loss": vl,
                        "seconds": time.time() - e0})
        print(f"  epoch {epoch + 1:2d}: train {np.mean(losses):.4f}  val {vl:.4f}  ({time.time() - e0:.0f}s)")
        if vl < best - 1e-5:
            best, best_weights, waited = vl, model.get_weights(), 0
        else:
            waited += 1
            if waited >= args.patience:
                break
    model.set_weights(best_weights)
    # Compiled forward pass: evaluation is ~280,000 samples, and compiling
    # roughly halves the time per batch compared with calling the model directly.
    predict = tf.function(lambda x: model(x, training=False),
                          input_signature=[tf.TensorSpec((None, C.SEQ_LEN, C.PATCH, C.PATCH, len(feats.channels)), tf.float32)])
    coverage = len(sampler.seen) / sampler.total_pairs

    threshold, val_f1 = best_threshold(predict, feats, val_sampler.uniform(2048))
    print(f"trained {len(history)} epochs in {time.time() - t0:.0f}s; saw {len(sampler.seen):,} of "
          f"{sampler.total_pairs:,} training pairs ({coverage:.2%}); threshold {threshold:.2f} (val F1 {val_f1:.3f})")

    e0 = time.time()
    results = evaluate(predict, feats, meta, s["test"], threshold)
    rows = [{"model": tag, "lead": lead, "fold": fold, "test_years": f"{y0}-{y1}", "group": g, **r}
            for g, r in results.items()]
    pd.DataFrame(rows).to_csv(STAGE2_OUT / f"metrics_{run}.csv", index=False)
    model.save(STAGE2_OUT / f"{run}.keras")
    (STAGE2_OUT / f"log_{run}.json").write_text(json.dumps({
        "run": run, "channels": feats.channels, "determinism": determinism, "history": history,
        "threshold": threshold, "val_f1": val_f1, "pairs_seen": len(sampler.seen),
        "pairs_total": sampler.total_pairs, "coverage": coverage,
        "train_issue_range": [int(s["train"].min()), int(s["train"].max())],
        "test_issue_range": [int(s["test"].min()), int(s["test"].max())],
    }, indent=1))
    r = results["all"]
    print(f"test ({time.time() - e0:.0f}s): F1 {r['f1']:.3f}  CSI {r['csi']:.3f}  PR-AUC {r['pr_auc']:.3f}  "
          f"Brier {r['brier']:.4f}  (unusual F1 {results['unusual']['f1']:.3f}, recurring F1 {results['recurring']['f1']:.3f})")




def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", type=int, nargs="+", required=True, choices=C.LEADS)
    ap.add_argument("--fold", type=int, nargs="+", required=True, choices=sorted(FOLD_YEARS))
    ap.add_argument("--no-era5", action="store_true")
    ap.add_argument("--no-stage1", action="store_true")
    ap.add_argument("--max-epochs", type=int, default=30)
    ap.add_argument("--steps", type=int, default=300, help="batches per epoch")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--patience", type=int, default=4)
    ap.add_argument("--redo", action="store_true", help="retrain runs that already have results")
    args = ap.parse_args()

    import tensorflow as tf
    for gpu in tf.config.list_physical_devices("GPU"):
        tf.config.experimental.set_memory_growth(gpu, True)
    C.ensure_dirs(STAGE2_OUT)

    # Runs one after another on the same GPU. Finished runs are skipped, so
    # an interrupted sweep can simply be started again.
    for lead in args.lead:
        for fold in args.fold:
            _, run = run_name(args, lead, fold)
            if (STAGE2_OUT / f"metrics_{run}.csv").exists() and not args.redo:
                print(f"{run}: already done, skipping")
                continue
            train_one(args, lead, fold, tf)
            tf.keras.backend.clear_session()


if __name__ == "__main__":
    main()
