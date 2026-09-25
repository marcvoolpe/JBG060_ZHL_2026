"""
Step 9 - the two no-skill forecasts Stage 2 has to beat, per pixel.

A model is only worth anything if it beats the cheapest thing you could do
instead. These two cost nothing and need no training:

  persistence   "same as now". The forecast for t + L is the flood map
                observed at issue time t. Floodwater drains slowly, so at
                short leads this is very hard to beat.

  climatology   "same as usual for this time of year". For each pixel, the
                fraction of training years in which it was flooded in that
                dekad of the year. That gives a probability; like the model,
                it is turned into a yes/no forecast with a threshold chosen
                on the validation years, never on the test years.

Both are scored exactly like Stage 2: same folds, same test dekads, same
pixels (flood domain, patch borders excluded), same metrics, split by NASA
flood type. Computed for every lead and every fold, so the skill-vs-lead
curve has a complete baseline even where Stage 2 was not run.

Output: raw_data/prediction/stage2/metrics_baselines.csv
~5-10 min.

Run: /usr/bin/python3 prediction/09_baselines.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

CHUNK = 96            # patches per pass (~100 MB of flood data)
N_YEARS = C.YEAR1 - C.YEAR0 + 1


def yearly_counts(block: np.ndarray) -> np.ndarray:
    """block (P, 936, 32, 32) -> cumulative flood counts per dekad-of-year:
    out[:, y + 1, d] = number of years 0..y flooded at dekad-of-year d.
    Row 0 is all zeros. Lets us count any range of training years at once."""
    per_year = block.reshape(block.shape[0], N_YEARS, C.DEKADS_PER_YEAR, C.PATCH, C.PATCH)
    out = np.zeros((block.shape[0], N_YEARS + 1, C.DEKADS_PER_YEAR, C.PATCH, C.PATCH), np.uint16)
    np.cumsum(per_year, axis=1, dtype=np.uint16, out=out[:, 1:])
    return out


def climatology(cum: np.ndarray, first_t: int, last_t: int) -> np.ndarray:
    """Per-pixel flood frequency for each dekad of the year, over training
    targets first_t..last_t only. Returns (P, 36, 32, 32) float32."""
    d = np.arange(C.DEKADS_PER_YEAR)
    # For dekad-of-year d, which years have their dekad d inside [first_t, last_t]?
    y_first = np.ceil((first_t - d) / C.DEKADS_PER_YEAR).astype(int)
    y_last = np.floor((last_t - d) / C.DEKADS_PER_YEAR).astype(int)
    count = cum[:, y_last + 1, d] .astype(np.float32) - cum[:, y_first, d]
    n_years = np.maximum(y_last - y_first + 1, 1).astype(np.float32)
    return count / n_years[None, :, None, None]


def main() -> None:
    t0 = time.time()
    flood, meta = C.load_dense()
    n_patches = flood.shape[0]
    keep = C.border_mask(meta["domain"])
    groups = {g: keep if c is None else keep & (meta["class_map"] == c) for g, c in C.GROUPS.items()}

    splits = {(lead, f): C.split(y0, y1, lead, min_issue=C.SEQ_LEN - 1, val_years=C.VAL_YEARS)
              for lead in C.LEADS for f, y0, y1 in C.FOLDS}
    new = lambda: {g: C.BinaryScores() for g in C.GROUPS}   # noqa: E731
    scores = {key: {"persistence": new(), "climatology_val": new(), "climatology": new()} for key in splits}

    for p0 in range(0, n_patches, CHUNK):
        patches = np.arange(p0, min(p0 + CHUNK, n_patches))
        block = np.asarray(flood[patches[0]:patches[-1] + 1])            # (P, 936, 32, 32)
        cum = yearly_counts(block)
        masks = {g: m[patches] for g, m in groups.items()}
        for (lead, f), s in splits.items():
            train_targets = s["train"] + lead
            clim = climatology(cum, int(train_targets.min()), int(train_targets.max()))
            sc = scores[(lead, f)]
            for name, issue in (("climatology_val", s["val"]), ("climatology", s["test"])):
                for t in issue:
                    target = block[:, t + lead]
                    prob = clim[:, C.doy_index(t + lead)]
                    for g, m in masks.items():
                        sc[name][g].update(prob, target, m)
            for t in s["test"]:
                for g, m in masks.items():
                    sc["persistence"][g].update(block[:, t], block[:, t + lead], m)
        print(f"patches {p0}-{patches[-1]} done ({time.time() - t0:.0f}s)")

    rows = []
    for (lead, f), sc in scores.items():
        y0, y1 = dict((k, (a, b)) for k, a, b in C.FOLDS)[f]
        # One climatology threshold per fold and lead, chosen on all
        # validation pixels, then used for every reporting group.
        th = sc["climatology_val"]["all"].best_threshold()
        for g in C.GROUPS:
            base = {"lead": lead, "fold": f, "test_years": f"{y0}-{y1}", "group": g}
            rows.append({"model": "persistence", **base, **sc["persistence"][g].result()})
            rows.append({"model": "climatology", **base, **sc["climatology"][g].at_threshold(th)})
    out = pd.DataFrame(rows)
    C.ensure_dirs(C.OUT / "stage2")
    out.to_csv(C.OUT / "stage2" / "metrics_baselines.csv", index=False)

    view = out[out["group"] == "all"].pivot_table(index=["lead", "model"], columns="fold", values="f1")
    print("\nbinary flood F1, all domain pixels:")
    print(view.round(3).to_string())
    print(f"\ndone ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
