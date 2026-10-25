"""
Design-based estimators for a stratified random sample (Olofsson et al. 2014;
Stehman 2014, for strata that are not the map classes). Used by 09_score.py.

W: stratum weights (share of the study area), keyed by stratum.
"""

import numpy as np
import pandas as pd


def area(ref, strata, W):
    """Share of the area that is crop, its standard error, from reference values only.

    ref is 0/1 (the box holds crop) or a fraction (the share of the box that is
    crop). The variance s^2 / n per stratum equals p (1 - p) / (n - 1) for 0/1.
    A stratum with one point adds its mean, but its variance is unknown: the
    standard error is then NaN. A stratum with no point leaves the share unknown.
    """
    est, var = 0.0, 0.0
    for h, w in W.items():
        y = ref[strata == h]
        if len(y) == 0:
            return np.nan, np.nan
        est += w * y.mean()
        var += w ** 2 * y.var(ddof=1) / len(y) if len(y) > 1 else np.nan
    return est, np.sqrt(var)


def _ratio(y, x, strata, W):
    """Ratio estimator R = sum_h W_h ybar_h / sum_h W_h xbar_h and its standard error (Stehman 2014, eq. 26-27)."""
    Y = sum(w * y[strata == h].mean() for h, w in W.items() if (strata == h).any())
    X = sum(w * x[strata == h].mean() for h, w in W.items() if (strata == h).any())
    if X == 0:
        return np.nan, np.nan
    R = Y / X
    var = 0.0
    for h, w in W.items():
        m = strata == h
        n = m.sum()
        if n < 2:
            continue
        z = y[m] - R * x[m]
        var += w ** 2 * z.var(ddof=1) / n
    return R, np.sqrt(var) / X


def _f1(ua, pa, ref, strata, W):
    """F1 from precision and recall. It is 0 when the map finds none of the cropland (or calls nothing), and
    undefined (NaN) only when the reference holds no cropland, so that misses cannot be counted."""
    if ua + pa > 0:
        return 2 * ua * pa / (ua + pa)
    holds = any((ref[strata == h] == 1).any() for h, w in W.items() if w > 0)
    return 0.0 if holds else np.nan


def accuracy(map_, ref, strata, W, n_boot=2000, seed=42):
    """User's, producer's and overall accuracy with standard errors; F1 with a bootstrap standard error."""
    map_, ref, strata = np.asarray(map_), np.asarray(ref), np.asarray(strata)
    both = (map_ == 1) & (ref == 1)
    ua, ua_se = _ratio(both.astype(float), (map_ == 1).astype(float), strata, W)
    pa, pa_se = _ratio(both.astype(float), (ref == 1).astype(float), strata, W)
    oa, oa_se = area((map_ == ref).astype(float), strata, W)
    f1 = _f1(ua, pa, ref, strata, W)

    rng = np.random.default_rng(seed)
    idx = {h: np.flatnonzero(strata == h) for h in W}
    boots = []
    for _ in range(n_boot):                                    # resample within strata
        take = np.concatenate([rng.choice(i, len(i)) for i in idx.values() if len(i)])
        m, r, s = map_[take], ref[take], strata[take]
        b = (m == 1) & (r == 1)
        u, _ = _ratio(b.astype(float), (m == 1).astype(float), s, W)
        p, _ = _ratio(b.astype(float), (r == 1).astype(float), s, W)
        boots.append(_f1(u, p, r, s, W))                      # a draw that finds no cropland counts as 0
    return {"ua": ua, "ua_se": ua_se, "pa": pa, "pa_se": pa_se, "oa": oa, "oa_se": oa_se,
            "f1": f1, "f1_se": float(np.nanstd(boots)), "map_crop_share": float(
                sum(w * (map_[strata == h] == 1).mean() for h, w in W.items() if (strata == h).any()))}
