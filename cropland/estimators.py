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
    """
    est, var = 0.0, 0.0
    for h, w in W.items():
        y = ref[strata == h]
        if len(y) < 2:
            continue
        est += w * y.mean()
        var += w ** 2 * y.var(ddof=1) / len(y)
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


def accuracy(map_, ref, strata, W, n_boot=2000, seed=42):
    """User's, producer's and overall accuracy with standard errors; F1 with a bootstrap standard error."""
    map_, ref, strata = np.asarray(map_), np.asarray(ref), np.asarray(strata)
    both = (map_ == 1) & (ref == 1)
    ua, ua_se = _ratio(both.astype(float), (map_ == 1).astype(float), strata, W)
    pa, pa_se = _ratio(both.astype(float), (ref == 1).astype(float), strata, W)
    oa, oa_se = area((map_ == ref).astype(float), strata, W)
    f1 = 2 * ua * pa / (ua + pa) if ua + pa else np.nan

    rng = np.random.default_rng(seed)
    idx = {h: np.flatnonzero(strata == h) for h in W}
    boots = []
    for _ in range(n_boot):                                    # resample within strata
        take = np.concatenate([rng.choice(i, len(i)) for i in idx.values() if len(i)])
        m, r, s = map_[take], ref[take], strata[take]
        b = (m == 1) & (r == 1)
        u, _ = _ratio(b.astype(float), (m == 1).astype(float), s, W)
        p, _ = _ratio(b.astype(float), (r == 1).astype(float), s, W)
        if u + p > 0:
            boots.append(2 * u * p / (u + p))
    return {"ua": ua, "ua_se": ua_se, "pa": pa, "pa_se": pa_se, "oa": oa, "oa_se": oa_se,
            "f1": f1, "f1_se": float(np.nanstd(boots)), "map_crop_share": float(
                sum(w * (map_[strata == h] == 1).mean() for h, w in W.items() if (strata == h).any()))}
