"""
How many labelled points does a cropland area estimate need, and which strata
need the fewest? (Olofsson et al. 2014, eq. 13; Skakun 2025; Adebayo et al. 2026)

For a stratified random sample with Neyman allocation, the number of points
needed to reach a target coefficient of variation gamma for the crop share f is

    n_opt = (sum_h W_h * sqrt(p_h (1 - p_h)))^2 / (gamma * f)^2

with W_h the share of the area in stratum h and p_h the crop share inside it.
Strata that put the crop into small, pure strata need fewer points. The
relative efficiency of design A against design B is n_B / n_A (Adebayo et al.
2026, eq. 4): above 1, A needs fewer points for the same precision.

A one-map design has two strata, "map says crop" and "map says not crop". With
the map's user's accuracy (UA, precision) and producer's accuracy (PA, recall)
and the true crop share f, p is UA in the crop stratum and the missed crop
f (1 - PA) / (1 - W_crop) in the other, with W_crop = f PA / UA.

Our design stratifies on how many of 7 maps say crop (0 / 1-2 / 3+). After
labelling, p_h comes from the labels and each map's UA / PA from 09_score.py,
so both designs can be compared on the same points.
"""

import numpy as np


def n_opt(W, p, cv):
    """Points needed (Neyman allocation) for a coefficient of variation cv of the crop share."""
    W, p = np.asarray(W, float), np.asarray(p, float)
    f = (W * p).sum()
    return float((W * np.sqrt(p * (1 - p))).sum() ** 2 / (cv * f) ** 2)


def neyman(W, p, n):
    """Neyman allocation of n points: n_h proportional to W_h sqrt(p_h (1 - p_h))."""
    W, p = np.asarray(W, float), np.asarray(p, float)
    s = W * np.sqrt(p * (1 - p))
    return n * s / s.sum()


def se_share(W, p, n_h):
    """Standard error of the crop share for a given allocation (p(1-p)/n per stratum; n_h - 1 for small n)."""
    W, p, n_h = (np.asarray(x, float) for x in (W, p, n_h))
    return float(np.sqrt((W ** 2 * p * (1 - p) / np.maximum(n_h - 1, 1)).sum()))


def one_map_strata(f, ua, pa):
    """Weights and crop shares of the two strata a single binary map makes (crop, not crop)."""
    w_crop = f * pa / ua
    return np.array([w_crop, 1 - w_crop]), np.array([ua, f * (1 - pa) / (1 - w_crop)])


def relative_efficiency(n_a, n_b):
    """n_B / n_A: how many times fewer points design A needs than design B for the same precision."""
    return n_b / n_a


if __name__ == "__main__":
    # check against Adebayo et al. (2026) Table 4, Kenya with GLAD: f = 0.09, PA 0.630, UA 0.575 -> n_opt 616
    W, p = one_map_strata(0.09, 0.575, 0.630)
    print(f"Kenya GLAD: n_opt = {n_opt(W, p, 0.10):.0f} (paper: 616; the paper's f and weights come from its own sample)")
    print("Neyman split crop / not crop:", neyman(W, p, 616).round(0), "(paper: 134 / 482)")
