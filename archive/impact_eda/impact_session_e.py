"""
Session E — Stages 31–35: blinded go/no-go verification of the within-county flood-impact RO.

Pre-registration: eda/SESSION_E_HYPOTHESES.md (commit d0605c4). This runner never computes the
within-county association between severity and flood displacement unless UNBLINDED is True,
which may only be set after STAGE35_GATE.md records GO (or an accepted team decision) and the
frozen spec hash has been emailed to the supervisor.

Severity-side and outcome-side tables are written to separate files:
    stage32_et_origin_season.csv   (outcome; never joined to severity by county-season)
    stage33_severity_season.csv    (severity)
The Stage 34 simulation reads outcome information only through stage32_outcome_marginals.json.

Run from repo root:
    python -m archive.impact_eda.impact_session_e --through 35
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from processing_data.paths import COURSE_RAW, EXT_DATA, ROOT, ensure_impact_eda_out

from archive.impact_eda.impact_panel import _coord_keys, _flood_parquet_paths, build_pixel_lookup
from archive.impact_eda.within_county_demo import _dekad_codes, _ocha_affected_county_year

OUT = ensure_impact_eda_out()
FIG_DIR = OUT / "figures" / "session_e"
SPEC_PATH = ROOT / "archive" / "impact_eda" / "sessions" / "SESSION_E_HYPOTHESES.md"

# Blinding switch (pre-registered). Do not flip before STAGE35_GATE.md records GO.
UNBLINDED = False

SEASONS = (2021, 2022, 2023, 2024, 2025)
JM_SEASONS = (2021, 2022, 2023, 2024)  # June–May 2021/22 … 2024/25
FRAME_YEARS = range(2001, 2021)
MIN_COVERAGE = 0.95
PIXEL_DEG = 1 / 480
ABYEI_ET, ABYEI_COD = "SS1101", "SS0001"
MIN_RECORDED_PEOPLE = 300  # ~50 households, ET recording threshold
ZOA_COUNTIES = {"SS0303": "Bor South", "SS0501": "Aweil Centre", "SS0502": "Aweil East",
                "SS0503": "Aweil North", "SS0504": "Aweil South", "SS0505": "Aweil West"}

ET_DIR = EXT_DATA / "IOM_DTM_event_tracking"
ET_FILES = {
    2021: ("iom_dtm_ssd_eventtracking_dataset_jan_dec_2021_hdx.xlsx", "ET_Dataset_Private"),
    2022: ("iom_dtm_ssd_eventtracking_dataset_jan_dec-2022_0_hdx.xlsx", "DTMEvent Tracking_Jan-Dec 2022"),
    2023: ("iom_dtm_ssd_eventtracking_dataset_january_december-2023_hdx.xlsx", "DTMEvent Tracking_Jan-Dec 2023"),
    2024: ("iom-ssd-dtm_event-tracking_jan-dec_2024_public_hdx.xlsx", "DTM_Event Tracking_JAN-DEC_2024"),
    2025: ("iom_dtm_ssd_eventtracking_dataset_january-november-2025_20251215_hdx.xlsx", "DTM_Event Tracking_Dataset"),
    # Read only for 2025-season tails (none are flood rows); not part of the 2021–2025 spec otherwise
    2026: ("iom_dtm_ssd_eventtracking_dataset_jan-apr-2026.xlsx", "DTM_Event Tracking_Dataset"),
}
OTHER_TRIGGER_LABELS = {"natural disaster (other)", "disaster (other)", "others (specify)"}
FLOOD_RE = re.compile("flood", re.I)
OTHER_FLOOD_RE = re.compile("flood|rain", re.I)
FORCED_RE = re.compile(r"^\s*forced return", re.I)

WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])


def spec_hash() -> str:
    return hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest()


def _log(log: list[dict], step: str, n_in: int, n_out: int, note: str = "") -> None:
    log.append({"step": step, "n_in": int(n_in), "n_out": int(n_out), "note": note})


def _frame() -> pd.DataFrame:
    """F71: counties with >= 95% flood-tile coverage, with state codes."""
    cov = pd.read_csv(OUT / "flood_tile_coverage_admin2.csv")
    cov = cov[cov["flood_tile_coverage_share"] >= MIN_COVERAGE]
    return cov[["adm2_pcode", "adm2_name", "adm1_pcode", "adm1_name"]].reset_index(drop=True)


def _admin2_pcodes() -> set[str]:
    cov = pd.read_csv(OUT / "flood_tile_coverage_admin2.csv")
    return set(cov["adm2_pcode"].astype(str))


# ---------------------------------------------------------------- season assignment


def assign_season(dates: pd.Series, window: str = "JD") -> pd.Series:
    """Season year per date. JD: June–December of year Y (Jan–May -> NA). JM: June Y – May Y+1."""
    d = pd.to_datetime(pd.Series(dates), errors="coerce")
    year, month = d.dt.year, d.dt.month
    if window == "JD":
        out = year.where(month >= 6)
    elif window == "JM":
        out = year.where(month >= 6, year - 1)
    else:
        raise ValueError(window)
    return out.astype("Int64")


# ---------------------------------------------------------------- ET outcome


def normalise_pcode(values: pd.Series, valid: set[str]) -> pd.Series:
    """Admin-2 pcode from the pcode column only (names are never used). Abyei SS1101 -> SS0001."""
    s = values.astype("string").str.strip().replace({ABYEI_ET: ABYEI_COD})
    return s.where(s.isin(valid))


def _pick(cols: list[str], pattern: str) -> str:
    hits = [c for c in cols if re.search(pattern, c)]
    if len(hits) != 1:
        raise KeyError(f"{pattern!r} matched {hits}")
    return hits[0]


def flood_flag(trigger: pd.Series, other: pd.Series, category: pd.Series) -> pd.Series:
    """Pre-registered flood rule: IDPs, trigger ~ /flood/i, or 'Other'/blank trigger with Other ~ /flood|rain/i."""
    t = trigger.astype("string")
    o = other.astype("string").fillna("")
    is_other = t.str.lower().str.strip().isin(OTHER_TRIGGER_LABELS) | t.isna() | (t.str.strip() == "")
    flood = t.fillna("").str.contains(FLOOD_RE) | (is_other & o.str.contains(OTHER_FLOOD_RE))
    forced = t.fillna("").str.contains(FORCED_RE)
    idp = category.astype("string").str.strip() == "IDPs"
    return (flood & ~forced & idp).fillna(False).astype(bool)


def load_et_events(log: list[dict] | None = None) -> pd.DataFrame:
    """Harmonised ET rows for 2021–2025 (+ 2026 file for tails), one row per ET record."""
    log = [] if log is None else log
    valid = _admin2_pcodes() | {ABYEI_COD}
    frames = []
    for fy, (fname, sheet) in ET_FILES.items():
        raw = pd.read_excel(ET_DIR / fname, sheet_name=sheet)
        n0 = len(raw)
        hxl = raw.astype(str).apply(lambda c: c.str.startswith("#")).any(axis=1)
        raw = raw[~hxl]
        _log(log, f"ET {fy}: drop HXL tag row", n0, len(raw))
        cols = list(raw.columns)
        ocol = _pick(cols, r"^Arrival (from|Location|From Location): Admin 2 PCODE$")
        ecol = _pick(cols, r"^Event Location:\s+County PCODE$")
        a3col = _pick(cols, r"^Arrival (from|Location|From Location): Admin 3 PCODE$")
        lcol = _pick(cols, r"^(Event )?Location SSID$")
        ncol = "Total number of individuals" if "Total number of individuals" in cols else "No. of Individuals"
        start = pd.to_datetime(raw["Event Started On (From date)"], errors="coerce", format="mixed")
        assess = pd.to_datetime(raw["Assessment Date"], errors="coerce", format="mixed")
        df = pd.DataFrame(
            {
                "file_year": fy,
                "event_ssid": raw["Event SSID"].astype(str).to_numpy(),
                "location_ssid": raw[lcol].astype(str).to_numpy(),
                "start_date": start.to_numpy(),
                "assessment_date": assess.to_numpy(),
                "trigger": raw["Movement Trigger"].to_numpy(),
                "other_trigger": raw["Other Trigger"].to_numpy(),
                "category": raw["Affected population category"].to_numpy(),
                "individuals": pd.to_numeric(raw[ncol], errors="coerce").to_numpy(),
                "origin_raw": raw[ocol].to_numpy(),
                "origin_adm3": raw[a3col].astype("string").to_numpy(),
                "event_raw": raw[ecol].to_numpy(),
            }
        )
        df["date_used"] = df["start_date"].fillna(df["assessment_date"])
        df["origin_pcode"] = normalise_pcode(df["origin_raw"], valid).to_numpy()
        df["event_pcode"] = normalise_pcode(df["event_raw"], valid).to_numpy()
        df["is_flood"] = flood_flag(df["trigger"], df["other_trigger"], df["category"]).to_numpy()
        df["is_forced_return"] = df["trigger"].astype("string").fillna("").str.contains(FORCED_RE).to_numpy()
        df["season_jd"] = assign_season(df["date_used"], "JD").to_numpy()
        df["season_jm"] = assign_season(df["date_used"], "JM").to_numpy()
        _log(log, f"ET {fy}: flood-triggered IDP rows", len(df), int(df["is_flood"].sum()),
             f"people={df.loc[df.is_flood, 'individuals'].sum():,.0f}")
        frames.append(df)
    ev = pd.concat(frames, ignore_index=True)
    n = len(ev)
    ev = ev.drop_duplicates(subset=["event_ssid"])
    _log(log, "ET all: unique Event SSID", n, len(ev))
    # Re-assessment: the same group (origin payam, site, start date, trigger, size) assessed again on a
    # later date. Same-day identical rows are kept (they cannot be told apart from two groups).
    key = ["origin_pcode", "origin_adm3", "location_ssid", "start_date", "individuals", "trigger"]
    ev = ev.sort_values(["assessment_date", "event_ssid"])
    first_assess = ev.groupby(key, dropna=False)["assessment_date"].transform("min")
    dup = ev["is_flood"] & ev.duplicated(subset=key, keep="first") & (ev["assessment_date"] > first_assess)
    _log(log, "ET flood: drop exact re-assessment duplicates", int(ev["is_flood"].sum()),
         int((ev["is_flood"] & ~dup).sum()), ", ".join(ev.loc[dup, "event_ssid"]))
    ev = ev[~dup].sort_values(["file_year", "event_ssid"]).reset_index(drop=True)
    return ev


def mon2_mask(events: pd.DataFrame, frame: pd.DataFrame, window: str = "JD") -> pd.DataFrame:
    """MON-2 observed flag per frame county-season: a non-flood ET event there, or any ET event
    elsewhere in the same state, that season (event location)."""
    col = "season_jd" if window == "JD" else "season_jm"
    seasons = SEASONS if window == "JD" else JM_SEASONS
    ev = events.dropna(subset=["event_pcode", col]).copy()
    ev["season"] = ev[col].astype(int)
    ev["state"] = ev["event_pcode"].str[:4]
    nonflood = set(zip(ev.loc[~ev["is_flood"], "event_pcode"], ev.loc[~ev["is_flood"], "season"]))
    any_ev = ev.groupby(["state", "season"])["event_pcode"].agg(lambda s: set(s)).to_dict()
    rows = []
    for p, st in zip(frame["adm2_pcode"], frame["adm1_pcode"]):
        for s in seasons:
            others = any_ev.get((st, s), set()) - {p}
            rows.append({"adm2_pcode": p, "season": s, "mon2_observed": ((p, s) in nonflood) or bool(others)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- estimator


def _pinv_sqrt(b: np.ndarray, tol: float = 1e-10) -> np.ndarray:
    vals, vecs = np.linalg.eigh((b + b.T) / 2)
    inv = np.where(vals > tol, 1.0 / np.sqrt(np.clip(vals, tol, None)), 0.0)
    return (vecs * inv) @ vecs.T


def _onehot(codes: np.ndarray, drop_first: bool = False) -> np.ndarray:
    k = int(codes.max()) + 1
    m = np.zeros((len(codes), k))
    m[np.arange(len(codes)), codes] = 1.0
    return m[:, 1:] if drop_first else m


@dataclass
class TwfeDesign:
    """TWFE design with x fixed: county + season (+ extra) dummies, full-design CR2 by county.

    beta = w @ y and the CR2 cluster scores are V @ y, so any number of outcome vectors can be
    fitted with the same pre-registered code path (Stage 34 uses fit_many)."""

    x: np.ndarray
    cluster: np.ndarray
    w: np.ndarray
    V: np.ndarray
    df: float
    MD: np.ndarray
    x_res: np.ndarray
    n: int
    G: int
    k: int
    vcov: str

    @classmethod
    def build(cls, x, county, season, extra_fe=None, vcov: str = "CR2") -> "TwfeDesign":
        x = np.asarray(x, dtype=float)
        c_codes, _ = pd.factorize(pd.Series(county).astype(str), sort=True)
        s_codes, _ = pd.factorize(pd.Series(season).astype(str), sort=True)
        blocks = [_onehot(c_codes), _onehot(s_codes, drop_first=True)]
        if extra_fe is not None:
            e_codes, _ = pd.factorize(pd.Series(extra_fe).astype(str), sort=True)
            blocks.append(_onehot(e_codes, drop_first=True))
        D = np.hstack(blocks)
        X = np.column_stack([x, D])
        n = len(x)
        M = np.linalg.pinv(X.T @ X)
        IH = np.eye(n) - X @ M @ X.T
        m = M[0]
        w = X @ m
        G = int(c_codes.max()) + 1
        V = np.zeros((G, n))
        for g in range(G):
            idx = np.flatnonzero(c_codes == g)
            A = _pinv_sqrt(IH[np.ix_(idx, idx)]) if vcov == "CR2" else np.eye(len(idx))
            V[g] = IH[:, idx] @ (A @ (X[idx] @ m))
        VVt = V @ V.T
        df = float(np.trace(VVt) ** 2 / np.sum(VVt * VVt)) if vcov == "CR2" else float(G - 1)
        MD = np.eye(n) - D @ np.linalg.pinv(D)
        return cls(x=x, cluster=c_codes, w=w, V=V, df=df, MD=MD, x_res=MD @ x, n=n, G=G,
                   k=int(np.linalg.matrix_rank(X)), vcov=vcov)

    def fit_many(self, Y: np.ndarray, level: float = 0.95) -> dict[str, np.ndarray]:
        Y = np.asarray(Y, dtype=float)
        if Y.ndim == 1:
            Y = Y[:, None]
        beta = self.w @ Y
        se = np.sqrt(np.sum((self.V @ Y) ** 2, axis=0))
        if self.vcov == "CR1":
            se = se * np.sqrt(self.G / (self.G - 1) * (self.n - 1) / (self.n - self.k))
        with np.errstate(divide="ignore", invalid="ignore"):
            t = beta / se
            p = 2 * stats.t.sf(np.abs(t), self.df)
            q2, q1 = stats.t.ppf(0.5 + level / 2, self.df), stats.t.ppf(level, self.df)
            y_res = self.MD @ Y
            scale = self.x_res.std() / y_res.std(axis=0)
        return {
            "beta": beta, "se": se, "t": t, "p": p, "df": np.full(beta.shape, self.df),
            "ci_lo": beta - q2 * se, "ci_hi": beta + q2 * se,
            "r": beta * scale, "r_ci_lo": (beta - q2 * se) * scale, "r_ci_hi": (beta + q2 * se) * scale,
            "r_upper_1s": (beta + q1 * se) * scale,
        }

    def fit(self, y: np.ndarray) -> dict[str, float]:
        return {k: float(v[0]) for k, v in self.fit_many(np.asarray(y, dtype=float)[:, None]).items()}


def twfe_cr2(y, x, county, season, extra_fe=None, vcov: str = "CR2") -> dict:
    """Pre-registered estimator: TWFE (county + season FE), CR2 by county, Bell–McCaffrey df.

    The reported effect size r is the standardized slope on the two-way residualized variables
    (= within-county partial correlation); its CI is the slope CI on the same scale."""
    design = TwfeDesign.build(x, county, season, extra_fe, vcov)
    res = design.fit(y)
    y_res = design.MD @ np.asarray(y, dtype=float)
    res.update({"n": design.n, "n_clusters": design.G,
                "spearman_resid": float(pd.Series(design.x_res).rank().corr(pd.Series(y_res).rank()))})
    return res


def wild_bootstrap_webb(design: TwfeDesign, y: np.ndarray, B: int = 999, seed: int = 0) -> dict:
    """Wild cluster restricted bootstrap (null beta = 0 imposed), Webb 6-point weights, CR1 t."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y, dtype=float)
    xr, ssx = design.x_res, design.x_res @ design.x_res
    oh = _onehot(design.cluster)
    adj = design.G / (design.G - 1) * (design.n - 1) / (design.n - design.k)

    def tstat(U: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        b = U @ xr / ssx
        E = U - b[:, None] * xr
        S = (E * xr) @ oh
        return b, b / (np.sqrt(adj * np.sum(S * S, axis=1)) / ssx)

    u = design.MD @ y
    b_obs, t_obs = tstat(u[None, :])
    W = rng.choice(WEBB, size=(B, design.G))
    _, t_star = tstat((W[:, design.cluster] * u) @ design.MD)
    p = float(np.mean(np.abs(t_star) >= np.abs(t_obs[0])))
    return {"beta": float(b_obs[0]), "t_cr1": float(t_obs[0]), "p_boot": p, "B": B}


def wild_bootstrap_webb_many(design: TwfeDesign, Y: np.ndarray, B: int = 399, seed: int = 0) -> np.ndarray:
    """Bootstrap p-values for many outcome columns (same weights per column; Stage 34 calibration)."""
    rng = np.random.default_rng(seed)
    xr, ssx = design.x_res, design.x_res @ design.x_res
    oh = _onehot(design.cluster)
    adj = design.G / (design.G - 1) * (design.n - 1) / (design.n - design.k)
    W = rng.choice(WEBB, size=(B, design.G))[:, design.cluster]
    U = design.MD @ np.asarray(Y, dtype=float)  # n x R restricted residuals
    out = np.empty(U.shape[1])
    for j in range(U.shape[1]):
        u = U[:, j]
        Us = np.vstack([u, (W * u) @ design.MD])
        b = Us @ xr / ssx
        E = Us - b[:, None] * xr
        S = (E * xr) @ oh
        t = b / (np.sqrt(adj * np.sum(S * S, axis=1)) / ssx)
        out[j] = np.mean(np.abs(t[1:]) >= np.abs(t[0]))
    return out


def randomization_test_tile(y, x, county, season, tile, n_perm: int = 999, seed: int = 0) -> dict:
    """Swap whole severity series between counties of the same MODIS tile (balanced panels only)."""
    df = pd.DataFrame({"y": y, "x": x, "c": pd.Series(county).astype(str).to_numpy(),
                       "s": pd.Series(season).astype(str).to_numpy()})
    xw = df.pivot(index="c", columns="s", values="x")
    if xw.isna().any().any():
        return {"p_rand": np.nan, "note": "unbalanced panel: randomization test not defined"}
    tiles = pd.Series(tile, index=df["c"]).groupby(level=0).first().reindex(xw.index)
    design = TwfeDesign.build(df["x"], df["c"], df["s"])
    y_res = design.MD @ df["y"].to_numpy(float)
    b_obs = design.x_res @ y_res / (design.x_res @ design.x_res)
    rng = np.random.default_rng(seed)
    row_of = {c: i for i, c in enumerate(xw.index)}
    ri = df["c"].map(row_of).to_numpy()
    ci = df["s"].map({s: j for j, s in enumerate(xw.columns)}).to_numpy()
    groups = [np.flatnonzero(tiles.to_numpy() == t) for t in tiles.unique()]
    xmat = xw.to_numpy()
    Xp = np.empty((len(df), n_perm))
    for k in range(n_perm):
        perm = np.arange(len(xw))
        for g in groups:
            perm[g] = rng.permutation(g)
        Xp[:, k] = xmat[perm][ri, ci]
    Xr = design.MD @ Xp
    b_perm = (Xr * y_res[:, None]).sum(0) / (Xr * Xr).sum(0)
    p = (1 + np.sum(np.abs(b_perm) >= abs(b_obs))) / (1 + n_perm)
    return {"beta": float(b_obs), "p_rand": float(p), "n_perm": n_perm}


def permute_within_county(y: pd.Series, county: pd.Series, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y = pd.Series(np.asarray(y, dtype=float))
    out = y.copy()
    for _, idx in pd.Series(np.arange(len(y))).groupby(pd.Series(county).astype(str).to_numpy()):
        out.iloc[idx.to_numpy()] = rng.permutation(y.iloc[idx.to_numpy()].to_numpy())
    return out.to_numpy()


def confirmatory_estimate(panel: pd.DataFrame, permute_seed: int | None = None, extra_fe: str | None = None,
                          n_boot: int = 999) -> dict:
    """SE-H4 estimate. Refuses to run on the real pairing unless UNBLINDED (set only after GO).

    panel columns: adm2_pcode, season, y (log1p outcome), x (log1p severity), tile."""
    if not UNBLINDED and permute_seed is None:
        raise PermissionError(
            "Blinded: confirmatory_estimate needs permute_seed until STAGE35_GATE.md records GO "
            "and the frozen spec hash has been sent to the supervisor."
        )
    y = panel["y"].to_numpy(float)
    if permute_seed is not None:
        y = permute_within_county(y, panel["adm2_pcode"], permute_seed)
    fe = panel[extra_fe] if extra_fe else None
    res = twfe_cr2(y, panel["x"], panel["adm2_pcode"], panel["season"], fe)
    design = TwfeDesign.build(panel["x"], panel["adm2_pcode"], panel["season"], fe)
    res["bootstrap"] = wild_bootstrap_webb(design, y, B=n_boot)
    if "tile" in panel:
        res["randomization"] = randomization_test_tile(y, panel["x"], panel["adm2_pcode"], panel["season"],
                                                       panel["tile"])
    res["permuted"] = permute_seed is not None
    return res


# ---------------------------------------------------------------- Stage 31: estimator and blinding tests


def _synthetic_panel(skel: pd.DataFrame, rng: np.random.Generator, rho: float, ar: float = 0.3,
                     n_rep: int = 1) -> tuple[np.ndarray, np.ndarray, float]:
    """Known-effect DGP on a skeleton (adm2_pcode, season). x and e share AR(1) within county, so
    two-way demeaning shrinks both alike and the population within-county correlation is rho."""
    counties = skel["adm2_pcode"].astype(str).to_numpy()
    seasons = skel["season"].astype(int).to_numpy()
    uc, ci = np.unique(counties, return_inverse=True)
    us, si = np.unique(seasons, return_inverse=True)
    T = len(us)

    def ar_series(sd_c: np.ndarray) -> np.ndarray:
        z = rng.standard_normal((len(uc), T, n_rep))
        out = np.empty_like(z)
        out[:, 0] = z[:, 0]
        for t in range(1, T):
            out[:, t] = ar * out[:, t - 1] + np.sqrt(1 - ar**2) * z[:, t]
        return (out * sd_c[:, None, None])[ci, si]

    x_w = ar_series(np.ones(len(uc)))
    sd_e = np.exp(rng.normal(0, 0.3, len(uc)))
    sd_e = sd_e / np.sqrt(np.mean(sd_e**2))
    e = ar_series(sd_e)
    beta = rho / np.sqrt(1 - rho**2)
    fe_x = rng.normal(0, 2, len(uc))[ci][:, None] + rng.normal(0, 1, T)[si][:, None]
    fe_y = rng.normal(0, 2, len(uc))[ci][:, None] + rng.normal(0, 1, T)[si][:, None]
    return fe_x + x_w, fe_y + beta * x_w + e, beta


def _stage31_recovery(skel: pd.DataFrame, rho: float, n_rep: int, seed: int) -> dict:
    """Bias of r and CI coverage for beta and r, on a fixed x per skeleton draw set."""
    rng = np.random.default_rng(seed)
    X, Y, beta = _synthetic_panel(skel, rng, rho, n_rep=n_rep)
    r_hat, cov_b, cov_r, rej = [], [], [], []
    for j in range(n_rep):
        design = TwfeDesign.build(X[:, j], skel["adm2_pcode"], skel["season"])
        f = design.fit(Y[:, j])
        r_hat.append(f["r"])
        cov_b.append(f["ci_lo"] <= beta <= f["ci_hi"])
        cov_r.append(f["r_ci_lo"] <= rho <= f["r_ci_hi"])
        rej.append(f["ci_lo"] > 0 or f["ci_hi"] < 0)
    r_hat = np.array(r_hat)
    return {
        "n_obs": len(skel), "n_counties": skel["adm2_pcode"].nunique(), "rho": rho, "n_rep": n_rep,
        "mean_r": float(r_hat.mean()), "bias_r": float(r_hat.mean() - rho),
        "mc_se_bias": float(r_hat.std() / np.sqrt(n_rep)),
        "coverage_beta": float(np.mean(cov_b)), "coverage_r": float(np.mean(cov_r)),
        "reject_rate": float(np.mean(rej)),
    }


def run_stage31(n_rep: int = 2000) -> dict:
    import statsmodels.api as sm

    results: dict[str, object] = {"spec_sha256": spec_hash()}
    checks: list[dict] = []

    # 1. CR2 code path vs statsmodels cluster SEs (balanced toy panel, CR0 path + CR1 correction)
    rng = np.random.default_rng(31)
    toy = pd.DataFrame([(f"C{i:02d}", t) for i in range(30) for t in range(5)], columns=["adm2_pcode", "season"])
    X, Y, _ = _synthetic_panel(toy, rng, 0.3)
    x, y = X[:, 0], Y[:, 0]
    dummies = pd.get_dummies(toy[["adm2_pcode"]].assign(season=toy.season.astype(str)), drop_first=False,
                             dtype=float)
    dummies = dummies.drop(columns=["season_0"])
    exog = np.column_stack([x, dummies.to_numpy()])
    sm_fit = sm.OLS(y, exog).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(toy.adm2_pcode)[0]})
    ours_cr1 = TwfeDesign.build(x, toy.adm2_pcode, toy.season, vcov="CR1").fit(y)
    ours_cr2 = TwfeDesign.build(x, toy.adm2_pcode, toy.season, vcov="CR2").fit(y)
    rel = abs(ours_cr1["se"] - sm_fit.bse[0]) / sm_fit.bse[0]
    checks.append({"test": "CR1 path equals statsmodels cluster SE (balanced toy, G=30, T=5)",
                   "value": f"beta {ours_cr1['beta']:.5f} vs {sm_fit.params[0]:.5f}; SE {ours_cr1['se']:.5f} vs "
                            f"{sm_fit.bse[0]:.5f} (rel. diff {rel:.1e}); CR2 SE {ours_cr2['se']:.5f}, "
                            f"BM df {ours_cr2['df']:.1f}",
                   "pass": bool(rel < 1e-6 and abs(ours_cr1["beta"] - sm_fit.params[0]) < 1e-8)})

    # Skeletons: real F71 x 5 seasons (balanced), real MON-2 mask (unbalanced), random 25% drop
    log: list[dict] = []
    events = load_et_events(log)
    frame = _frame()
    grid = frame[["adm2_pcode"]].merge(pd.DataFrame({"season": SEASONS}), how="cross")
    m2 = mon2_mask(events, frame)
    skel_mon2 = m2[m2["mon2_observed"]][["adm2_pcode", "season"]].reset_index(drop=True)
    skel_drop = grid.sample(frac=0.75, random_state=7).sort_values(["adm2_pcode", "season"]).reset_index(drop=True)
    skel_drop = skel_drop[skel_drop.groupby("adm2_pcode")["season"].transform("size") >= 2]
    skeletons = {"F71_balanced": grid, "F71_MON2": skel_mon2, "F71_random_drop25": skel_drop}
    recov = []
    for i, (name, sk) in enumerate(skeletons.items()):
        for k, rho in enumerate((0.0, 0.3)):
            r = _stage31_recovery(sk, rho, n_rep, seed=310 + 10 * i + k)
            r["skeleton"] = name
            recov.append(r)
    recov_df = pd.DataFrame(recov)
    recov_df.to_csv(OUT / "stage31_recovery.csv", index=False)
    ok_bias = bool((recov_df["bias_r"].abs() < 0.02).all())
    ok_cov = bool(recov_df["coverage_beta"].between(0.93, 0.97).all())
    checks.append({"test": "Known-effect recovery: |bias r| < 0.02 on all skeletons, rho in {0, 0.3}",
                   "value": f"max |bias| {recov_df['bias_r'].abs().max():.4f}", "pass": ok_bias})
    checks.append({"test": "Known-effect recovery: CR2 95% CI coverage of beta in [0.93, 0.97]",
                   "value": f"range {recov_df['coverage_beta'].min():.3f}–{recov_df['coverage_beta'].max():.3f} "
                            f"(r-scale CI coverage {recov_df['coverage_r'].min():.3f}–"
                            f"{recov_df['coverage_r'].max():.3f})",
                   "pass": ok_cov})

    # 2. Permutation null: a real effect, outcome seasons permuted within county
    rng = np.random.default_rng(3131)
    Xp, Yp, _ = _synthetic_panel(skel_mon2, rng, 0.3, n_rep=n_rep)
    rs, rej = [], []
    for j in range(n_rep):
        yp = permute_within_county(Yp[:, j], skel_mon2["adm2_pcode"], seed=j)
        f = TwfeDesign.build(Xp[:, j], skel_mon2["adm2_pcode"], skel_mon2["season"]).fit(yp)
        rs.append(f["r"])
        rej.append(f["ci_lo"] > 0 or f["ci_hi"] < 0)
    mean_r, fpr = float(np.mean(rs)), float(np.mean(rej))
    checks.append({"test": "Permutation null (true rho 0.3, y permuted within county, MON-2 skeleton): "
                           "mean r within ±0.01 and FPR in [0.035, 0.065]",
                   "value": f"mean r {mean_r:+.4f} (MC SE {np.std(rs) / np.sqrt(n_rep):.4f}); FPR {fpr:.3f}",
                   "pass": bool(abs(mean_r) < 0.01 and 0.035 <= fpr <= 0.065)})

    # Comparators under the null (informative; Stage 34 repeats this on the real design)
    rng = np.random.default_rng(3132)
    n_cmp = 400
    Xc, Yc, _ = _synthetic_panel(grid, rng, 0.0, n_rep=n_cmp)
    tiles = np.where(grid["adm2_pcode"].str[2:4].astype(int) <= 5, "h20v08", "h21v08")
    boot_rej, rand_rej = [], []
    for j in range(n_cmp):
        d = TwfeDesign.build(Xc[:, j], grid["adm2_pcode"], grid["season"])
        boot_rej.append(wild_bootstrap_webb(d, Yc[:, j], B=399, seed=j)["p_boot"] < 0.05)
        rand_rej.append(randomization_test_tile(Yc[:, j], Xc[:, j], grid["adm2_pcode"], grid["season"], tiles,
                                                n_perm=199, seed=j)["p_rand"] < 0.05)
    results["comparator_null_fpr"] = {"wild_webb": float(np.mean(boot_rej)), "tile_randomization": float(np.mean(rand_rej)),
                                      "n_rep": n_cmp}

    # 3. Season assignment on boundary dates
    dates = pd.Series(pd.to_datetime(["2021-05-31", "2021-06-01", "2021-12-31", "2022-01-01", "2022-05-31",
                                      "2020-11-15", None]))
    jd = assign_season(dates, "JD").tolist()
    jm = assign_season(dates, "JM").tolist()
    exp_jd = [pd.NA, 2021, 2021, pd.NA, pd.NA, 2020, pd.NA]
    exp_jm = [2020, 2021, 2021, 2021, 2021, 2020, pd.NA]
    same = lambda a, b: all((pd.isna(u) and pd.isna(v)) or u == v for u, v in zip(a, b))  # noqa: E731
    checks.append({"test": "Season assignment on boundary dates (31 May, 1 Jun, 31 Dec, 1 Jan, missing)",
                   "value": f"JD {jd}; JM {jm}", "pass": bool(same(jd, exp_jd) and same(jm, exp_jm))})
    ev_fallback = events[events["start_date"].isna()]
    checks.append({"test": "Start date missing -> assessment date used",
                   "value": f"{len(ev_fallback)} rows without start date; date_used = assessment_date for all: "
                            f"{bool((ev_fallback['date_used'] == ev_fallback['assessment_date']).all())}",
                   "pass": bool((ev_fallback["date_used"].fillna(pd.Timestamp(0)) ==
                                 ev_fallback["assessment_date"].fillna(pd.Timestamp(0))).all())})

    # 4. pcode joins
    valid = _admin2_pcodes()
    test_in = pd.Series(["SS1101", " SS0505 ", "SD07089", "Other Admin 2", None, "SS0303"])
    got = normalise_pcode(test_in, valid | {ABYEI_COD}).tolist()
    exp = [ABYEI_COD, "SS0505", pd.NA, pd.NA, pd.NA, "SS0303"]
    checks.append({"test": "pcode normalisation: Abyei SS1101->SS0001, whitespace, Sudan codes and names rejected",
                   "value": str(got), "pass": bool(same(got, exp))})
    fl = events[events["is_flood"]]
    bad = fl[fl["origin_pcode"].isna()]
    share_valid = 1 - bad["individuals"].sum() / fl["individuals"].sum()
    checks.append({"test": "Flood rows: origin pcode valid (names never used)",
                   "value": f"{len(bad)} of {len(fl)} flood rows invalid ({', '.join(map(str, bad['origin_raw']))}); "
                            f"people share valid {share_valid:.4f}",
                   "pass": bool(share_valid >= 0.99)})
    by_year = events[events["is_flood"]].groupby("file_year").agg(rows=("is_flood", "size"),
                                                                  people=("individuals", "sum"))
    # Planning counts used /flood/i only; the frozen rule adds blank/'Other' triggers whose Other text says
    # flood: 2021 +1 row (blank trigger, 'Floods', 910), 2022 +1 ('Flood', 444). 2024 −1 re-assessment (560).
    planned = {2021: (417, 534626), 2022: (469, 416639), 2023: (60, 27613), 2024: (386, 359167), 2025: (171, 241584)}
    results["flood_rows_by_file"] = by_year.reset_index().to_dict("records")
    checks.append({"test": "Flood rule reproduces planning counts (+1 blank/'Other' flood row in 2021 and 2022, −1 re-assessment 2024)",
                   "value": "; ".join(f"{y}: {int(r.rows)} rows / {r.people:,.0f}" for y, r in by_year.iterrows()),
                   "pass": bool(all(tuple(map(int, by_year.loc[y])) == v for y, v in planned.items()))})
    forced = events[(events["file_year"] == 2023) & events["is_forced_return"]]
    checks.append({"test": "2023 'Forced return' rows never counted as flood",
                   "value": f"{len(forced)} forced-return rows, {int(forced['is_flood'].sum())} flagged flood",
                   "pass": bool(len(forced) > 0 and forced["is_flood"].sum() == 0)})

    # 5. Blinding guard
    try:
        confirmatory_estimate(pd.DataFrame({"adm2_pcode": ["a"], "season": [1], "y": [0.0], "x": [0.0]}))
        blocked = False
    except PermissionError:
        blocked = True
    checks.append({"test": "Blinding: confirmatory_estimate raises without permute_seed while UNBLINDED is False",
                   "value": f"UNBLINDED={UNBLINDED}; raised={blocked}", "pass": bool(blocked and not UNBLINDED)})

    # 6. fit_many equals twfe_cr2 column by column (Stage 34 uses fit_many)
    d = TwfeDesign.build(Xc[:, 0], grid["adm2_pcode"], grid["season"])
    many = d.fit_many(Yc[:, :5])
    single = [twfe_cr2(Yc[:, j], Xc[:, 0], grid["adm2_pcode"], grid["season"]) for j in range(5)]
    diff = max(abs(many["se"][j] - single[j]["se"]) + abs(many["beta"][j] - single[j]["beta"]) for j in range(5))
    checks.append({"test": "fit_many (simulation path) equals twfe_cr2", "value": f"max abs diff {diff:.1e}",
                   "pass": bool(diff < 1e-10)})

    checks_df = pd.DataFrame(checks)
    checks_df.to_csv(OUT / "stage31_tests.csv", index=False)
    pd.DataFrame(log).to_csv(OUT / "stage31_join_log.csv", index=False)
    results["all_pass"] = bool(checks_df["pass"].all())
    results["skeleton_sizes"] = {k: int(len(v)) for k, v in skeletons.items()}
    (OUT / "stage31_summary.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    _write_stage31_gate(checks_df, recov_df, results, log)
    return results


def _md_table(df: pd.DataFrame, floatfmt: str = "{:.3f}") -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)) and ("season" in str(c) or str(c) == "year") and np.isfinite(v):
                cells.append(str(int(v)))
            elif isinstance(v, (float, np.floating)):
                cells.append(floatfmt.format(v) if np.isfinite(v) else "—")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _write_stage31_gate(checks: pd.DataFrame, recov: pd.DataFrame, results: dict, log: list[dict]) -> None:
    status = "PASS" if results["all_pass"] else "FAIL"
    cmp_ = results["comparator_null_fpr"]
    rec = recov[["skeleton", "n_obs", "n_counties", "rho", "mean_r", "bias_r", "mc_se_bias", "coverage_beta",
                 "coverage_r", "reject_rate"]]
    text = [
        "# Stage 31 gate — estimator, blinding and join tests",
        "",
        f"**Status: {status}.** Pre-registration `SESSION_E_HYPOTHESES.md` SHA-256 `{results['spec_sha256']}` "
        "(unchanged since commit d0605c4).",
        "",
        "No severity–outcome association was computed. All estimator tests use synthetic outcomes on real "
        "panel skeletons; the MON-2 skeleton uses only which county-seasons have ET activity.",
        "",
        "## Tests",
        "",
        _md_table(checks.assign(**{"pass": checks["pass"].map({True: "pass", False: "**FAIL**"})})),
        "",
        "## Known-effect recovery (TWFE + CR2 + Bell–McCaffrey df)",
        "",
        "DGP: county and season effects in x and y (SD 2 and 1), x and error AR(1) = 0.3 within county, "
        "county-specific error SDs (log-SD 0.3). The population within-county correlation equals ρ.",
        "",
        _md_table(rec),
        "",
        "`coverage_r` is the coverage of the slope CI rescaled to the correlation scale (sd ratio treated as "
        "fixed). It is informative only; the reporting rule 'Supported' depends only on the sign of the CI.",
        "",
        "## Comparators under the null (synthetic, balanced F71 × 5)",
        "",
        f"- Wild cluster restricted bootstrap, Webb weights, B = 399: FPR **{cmp_['wild_webb']:.3f}** "
        f"({cmp_['n_rep']} replications, MC SE ≈ {np.sqrt(0.05 * 0.95 / cmp_['n_rep']):.3f}).",
        f"- Tile randomization (199 swaps within tile): FPR **{cmp_['tile_randomization']:.3f}**. Tiles here are "
        "a synthetic split; Stage 34 repeats both on the real design and real tiles.",
        "",
        "## ET join log",
        "",
        _md_table(pd.DataFrame(log)),
        "",
        "## Implementation notes",
        "",
        "- `TwfeDesign` builds the full design (x, county dummies, season dummies, optional extra FE) and the CR2 "
        "adjustment `(I − H_gg)^(-1/2)` with a pseudo-inverse square root (the county block of `I − H` is "
        "singular because county FE are nested in the clusters). Bell–McCaffrey df use the Imbens–Kolesár "
        "form with a homoskedastic working model.",
        "- Because x and the fixed effects do not change across simulated outcomes, β = wᵀy and the CR2 cluster "
        "scores are V y. Stage 34 therefore runs the identical estimator for thousands of outcome vectors "
        "(`fit_many`, checked against `twfe_cr2` above).",
        "- Wild bootstrap: restricted residuals (β = 0 imposed), Webb six-point weights, CR1 t-statistic, "
        "symmetric p-value.",
        "- Re-assessment rule (outcome-side): a flood row identical to an earlier one in origin, site, start date, "
        "trigger and size is dropped (one pair: Aweil West 2024, 560 people).",
        "- The 2026 ET file is read only for 2025-season tails: it has no flood rows.",
        "",
        "```powershell",
        "python -m archive.impact_eda.impact_session_e --through 31",
        "```",
    ]
    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE31_GATE.md").write_text("\n".join(text), encoding="utf-8")


# ---------------------------------------------------------------- Stage 32: ET outcome audit (outcome-only)

MT_FIRST_ROUND = {2021: 13, 2022: 14, 2023: 15, 2024: 16}
OCHA_MIN_AFFECTED = 10_000
MT_MIN_ARRIVALS = 1_000
USABLE_MIN_PCODED = 0.95
USABLE_MIN_NONZERO = 15
MIN_VARYING = 35
MIN_DETECTION = 0.40


def _origin_season_table(events: pd.DataFrame, log: list[dict], window: str) -> pd.DataFrame:
    """Origin county x season for every admin2 (MON-0: no record = 0), plus event-location activity."""
    col = "season_jd" if window == "JD" else "season_jm"
    seasons = SEASONS if window == "JD" else JM_SEASONS
    counties = sorted(_admin2_pcodes())
    fl = events[events["is_flood"] & events[col].isin(seasons)].copy()
    n = len(fl)
    flv = fl.dropna(subset=["origin_pcode"])
    _log(log, f"{window}: flood rows in seasons -> valid origin pcode", n, len(flv),
         f"people {fl['individuals'].sum():,.0f} -> {flv['individuals'].sum():,.0f}")
    flv = flv.assign(season=flv[col].astype(int))
    agg = flv.groupby(["origin_pcode", "season"]).agg(flood_ind=("individuals", "sum"),
                                                      flood_rows=("individuals", "size")).reset_index()
    agg = agg.rename(columns={"origin_pcode": "adm2_pcode"})
    grid = pd.DataFrame([(c, s) for c in counties for s in seasons], columns=["adm2_pcode", "season"])
    out = grid.merge(agg, on=["adm2_pcode", "season"], how="left", indicator=True)
    lost = agg.merge(grid, on=["adm2_pcode", "season"], how="left", indicator=True)
    _log(log, f"{window}: origin x season aggregated -> admin2 grid", len(agg),
         int((out["_merge"] == "both").sum()),
         f"not in grid: {int((lost['_merge'] == 'left_only').sum())} (Abyei is in grid, outside F71)")
    out = out.drop(columns="_merge")
    out[["flood_ind", "flood_rows"]] = out[["flood_ind", "flood_rows"]].fillna(0)
    ev = events.dropna(subset=["event_pcode"]).loc[lambda d: d[col].isin(seasons)]
    ev = ev.assign(season=ev[col].astype(int))
    nf = ev[~ev["is_flood"]].groupby(["event_pcode", "season"]).size().rename("nonflood_records")
    anyr = ev.groupby(["event_pcode", "season"]).size().rename("any_records")
    act = pd.concat([nf, anyr], axis=1).reset_index().rename(columns={"event_pcode": "adm2_pcode"})
    out = out.merge(act, on=["adm2_pcode", "season"], how="left")
    out[["nonflood_records", "any_records"]] = out[["nonflood_records", "any_records"]].fillna(0)
    out["y"] = np.log1p(out["flood_ind"])
    out["window"] = window
    f71 = set(_frame()["adm2_pcode"])
    out["in_f71"] = out["adm2_pcode"].isin(f71)
    return out


def _mon1_counties(events: pd.DataFrame) -> set[str]:
    ev = events.dropna(subset=["event_pcode", "date_used"])
    yr = pd.to_datetime(ev["date_used"]).dt.year
    ev = ev[yr.between(2021, 2025)].assign(yr=yr)
    n_years = ev.groupby("event_pcode")["yr"].nunique()
    return set(n_years[n_years >= 3].index)


def _county_bootstrap_r(df: pd.DataFrame, ycol: str, xcol: str, n_boot: int = 1000, seed: int = 0) -> tuple:
    rng = np.random.default_rng(seed)
    groups = [g for _, g in df.groupby("adm2_pcode")]
    rs = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        s = pd.concat([groups[i].assign(adm2_pcode=f"b{j}") for j, i in enumerate(pick)], ignore_index=True)
        if s[ycol].std() == 0 or s[xcol].std() == 0:
            continue
        rs.append(TwfeDesign.build(s[xcol], s["adm2_pcode"], s["season"]).fit(s[ycol].to_numpy())["r"])
    lo, hi = np.nanpercentile(rs, [2.5, 97.5])
    return float(lo), float(hi)


def _two_way_r(a: np.ndarray, b: np.ndarray, county, season) -> float:
    d = TwfeDesign.build(b, county, season)
    return d.fit(a)["r"]


def _season_marginals(tab: pd.DataFrame, frame: pd.DataFrame, seasons: list[int], mon1: set[str],
                      mon2: pd.DataFrame) -> dict:
    """Outcome marginals only: per-county and per-season summaries, never county x season values."""
    t = tab[tab["adm2_pcode"].isin(frame["adm2_pcode"]) & tab["season"].isin(seasons)]
    nz = t[t["flood_ind"] > 0]
    logs = np.log(nz["flood_ind"])
    cm = logs.groupby(nz["adm2_pcode"]).transform("mean")
    k = nz.groupby("adm2_pcode").size()
    within = (logs - cm)[nz["adm2_pcode"].map(k) >= 2]
    counties = {}
    for p, st in zip(frame["adm2_pcode"], frame["adm1_pcode"]):
        sub = t[t["adm2_pcode"] == p]
        nzs = sub[sub["flood_ind"] > 0]
        counties[p] = {
            "state": st,
            "n_seasons": int(len(sub)),
            "n_nonzero": int(len(nzs)),
            "mean_log_nonzero": float(np.log(nzs["flood_ind"]).mean()) if len(nzs) else None,
            "mon1": p in mon1,
            "nonflood_records_mean": float(sub["nonflood_records"].mean()),
        }
    per_season = {}
    for s in seasons:
        sub = t[t["season"] == s]
        nzs = sub[sub["flood_ind"] > 0]
        per_season[str(s)] = {"share_nonzero": float((sub["flood_ind"] > 0).mean()),
                              "n_nonzero": int(len(nzs)),
                              "mean_log_nonzero": float(np.log(nzs["flood_ind"]).mean()) if len(nzs) else None}
    m2 = mon2[mon2["season"].isin(seasons) & mon2["mon2_observed"]]
    nf = np.log1p(t["nonflood_records"])
    nf_within = nf - nf.groupby(t["adm2_pcode"]).transform("mean")
    return {
        "seasons": seasons,
        "counties": counties,
        "seasons_summary": per_season,
        "log_nonzero_mean": float(logs.mean()),
        "log_nonzero_sd": float(logs.std()),
        # pooled within-county SD of log sizes among counties with >= 2 non-zero seasons
        "log_nonzero_within_sd": float(np.sqrt(np.sum(within**2) / (len(within) - int((k >= 2).sum()))))
        if len(within) > int((k >= 2).sum()) else None,
        "n_nonzero_total": int(len(nz)),
        "nonflood_log1p_within_sd": float(nf_within.std()),
        "mon2_observed": [[p, int(s)] for p, s in zip(m2["adm2_pcode"], m2["season"])],
    }


def run_stage32() -> dict:
    log: list[dict] = []
    events = load_et_events(log)
    frame = _frame()
    f71 = set(frame["adm2_pcode"])
    ev_out = events.drop(columns=["other_trigger"]).copy()
    ev_out.to_csv(OUT / "stage32_et_events.csv", index=False)

    jd = _origin_season_table(events, log, "JD")
    jm = _origin_season_table(events, log, "JM")
    tab = pd.concat([jd, jm], ignore_index=True)
    tab.to_csv(OUT / "stage32_et_origin_season.csv", index=False)

    fl = events[events["is_flood"]].copy()
    fl["lag_days"] = (fl["assessment_date"] - fl["start_date"]).dt.days
    # Tails and out-of-window rows
    tails = {
        "flood_rows_2020_season_in_2021_file": int(((fl.file_year == 2021) & (fl.season_jd == 2020)).sum()),
        "flood_people_2020_season": float(fl.loc[fl.season_jd == 2020, "individuals"].sum()),
        "flood_rows_jan_may_by_year": fl[fl.season_jd.isna()].groupby(fl["date_used"].dt.year).size().to_dict(),
        "flood_people_jan_may_by_year": fl[fl.season_jd.isna()].groupby(fl["date_used"].dt.year)["individuals"]
        .sum().to_dict(),
    }
    lag = fl[fl.season_jd.isin(SEASONS)].groupby("season_jd")["lag_days"].describe(percentiles=[0.5, 0.9])[
        ["count", "50%", "90%"]].rename(columns={"50%": "median_lag", "90%": "p90_lag"})

    # Usable seasons (JD)
    use_rows = []
    for s in SEASONS:
        f = fl[fl.season_jd == s]
        share = f.loc[f.origin_pcode.notna(), "individuals"].sum() / f["individuals"].sum() if len(f) else np.nan
        sub = jd[(jd.season == s) & jd.in_f71]
        nnz = int((sub.flood_ind > 0).sum())
        use_rows.append({"season": s, "flood_rows": len(f), "flood_people": f["individuals"].sum(),
                         "share_people_pcoded": share, "f71_nonzero": nnz,
                         "f71_people": sub["flood_ind"].sum(),
                         "usable": bool(share >= USABLE_MIN_PCODED and nnz >= USABLE_MIN_NONZERO)})
    usable = pd.DataFrame(use_rows).merge(lag, left_on="season", right_index=True, how="left")

    # Detection rate vs OCHA (outcome-only)
    ocha = _ocha_affected_county_year().rename(columns={"year": "season"})
    det_o = ocha[ocha["ocha_affected"] >= OCHA_MIN_AFFECTED].merge(
        jd[["adm2_pcode", "season", "flood_rows", "flood_ind", "any_records"]], on=["adm2_pcode", "season"], how="left")
    _log(log, "OCHA >=10k county-seasons -> ET JD table", len(ocha[ocha.ocha_affected >= OCHA_MIN_AFFECTED]),
         int(det_o["flood_rows"].notna().sum()))
    det_o["detected"] = det_o["flood_rows"] > 0
    det_o["in_f71"] = det_o["adm2_pcode"].isin(f71)
    det_ocha = {
        "n": int(len(det_o)), "rate": float(det_o["detected"].mean()),
        "n_f71": int(det_o["in_f71"].sum()), "rate_f71": float(det_o.loc[det_o.in_f71, "detected"].mean()),
        "by_season": det_o.groupby("season")["detected"].agg(["size", "mean"]).round(3).to_dict("index"),
        "wilson_ci": _wilson(int(det_o["detected"].sum()), len(det_o)),
    }
    # Detection rate vs Mobility Tracking first-round disaster arrivals (arrival county)
    from archive.impact_eda.within_county_reliability import _cohorts_by_round

    mt = _cohorts_by_round()
    mt = pd.concat([mt[(mt["round"] == r) & (mt["cohort"] == c)] for c, r in MT_FIRST_ROUND.items()])
    mt = mt[mt["idps"] >= MT_MIN_ARRIVALS].rename(columns={"cohort": "season"})
    det_m = mt.merge(jd[["adm2_pcode", "season", "flood_rows"]], on=["adm2_pcode", "season"], how="left")
    ev_loc = fl[fl.season_jd.isin(SEASONS)].dropna(subset=["event_pcode"])
    loc_set = set(zip(ev_loc["event_pcode"], ev_loc["season_jd"].astype(int)))
    det_m["detected"] = det_m["flood_rows"] > 0
    det_m["detected_event_loc"] = [(p, s) in loc_set for p, s in zip(det_m["adm2_pcode"], det_m["season"])]
    _log(log, "MT first-round disaster arrivals >=1000 -> ET JD table", len(mt), int(det_m["flood_rows"].notna().sum()))
    by_s = det_m.groupby("season")["detected"].agg(["size", "mean"])
    det_mt = {
        "n": int(len(det_m)), "rate": float(det_m["detected"].mean()),
        "rate_event_location": float(det_m["detected_event_loc"].mean()),
        "by_season": by_s.round(3).to_dict("index"),
        "by_season_event_location": det_m.groupby("season")["detected_event_loc"].mean().round(3).to_dict(),
    }
    others = [by_s.loc[s, "mean"] for s in (2021, 2022, 2024) if s in by_s.index]
    rate_2023 = float(by_s.loc[2023, "mean"]) if 2023 in by_s.index else np.nan
    keep_2023 = not (rate_2023 < 0.5 * float(np.median(others)))
    rule_2023 = {"mt_rate_2023": rate_2023, "median_other": float(np.median(others)),
                 "threshold": 0.5 * float(np.median(others)), "keep_2023": bool(keep_2023)}

    usable_seasons = [int(s) for s in usable.loc[usable.usable, "season"]]
    panel_seasons = sorted(set(usable_seasons) | ({2023} if keep_2023 else set()))
    panel_seasons = [s for s in panel_seasons if keep_2023 or s != 2023]

    def varying(seasons: list[int]) -> int:
        t = jd[jd.in_f71 & jd.season.isin(seasons)]
        return int((t.groupby("adm2_pcode")["y"].nunique() > 1).sum())

    n_vary_usable, n_vary_panel = varying(usable_seasons), varying(panel_seasons)
    nz_count = jd[jd.in_f71 & jd.season.isin(panel_seasons)].groupby("adm2_pcode")["flood_ind"].apply(
        lambda s: int((s > 0).sum())).value_counts().sort_index()

    # Outcome reliability floor (ET vs OCHA, within county) and split-half ceiling
    rw = ocha.merge(jd[jd.season.isin(panel_seasons)][["adm2_pcode", "season", "y"]], on=["adm2_pcode", "season"])
    rw = rw[rw["ocha_affected"] > 0].assign(y_ocha=lambda d: np.log1p(d["ocha_affected"]))
    rw = rw[rw.groupby("adm2_pcode")["season"].transform("size") >= 2]
    floor = twfe_cr2(rw["y"], rw["y_ocha"], rw["adm2_pcode"], rw["season"])
    floor_ci = _county_bootstrap_r(rw, "y", "y_ocha")
    floor_f71 = rw[rw.adm2_pcode.isin(f71)]
    floor_f71_r = twfe_cr2(floor_f71["y"], floor_f71["y_ocha"], floor_f71["adm2_pcode"], floor_f71["season"])["r"]

    rng = np.random.default_rng(32)
    fp = fl[fl.season_jd.isin(panel_seasons) & fl.origin_pcode.isin(f71)].assign(season=lambda d: d.season_jd.astype(int))
    grid = frame[["adm2_pcode"]].merge(pd.DataFrame({"season": panel_seasons}), how="cross")
    sh = []
    for _ in range(200):
        half = rng.random(len(fp)) < 0.5
        parts = []
        for h in (half, ~half):
            a = fp[h].groupby(["origin_pcode", "season"])["individuals"].sum().rename("v").reset_index()
            parts.append(grid.merge(a.rename(columns={"origin_pcode": "adm2_pcode"}), on=["adm2_pcode", "season"],
                                    how="left")["v"].fillna(0).pipe(np.log1p).to_numpy())
        r = _two_way_r(parts[0], parts[1], grid["adm2_pcode"], grid["season"])
        sh.append(2 * r / (1 + r))
    ceiling = {"median_sb": float(np.median(sh)), "p2_5": float(np.percentile(sh, 2.5)),
               "p97_5": float(np.percentile(sh, 97.5)), "n_splits": 200}

    # Plausibility
    totals = usable[["season", "flood_people", "f71_people"]].merge(
        ocha.groupby("season")["ocha_affected"].sum().rename("ocha_affected_total").reset_index(), on="season", how="left")
    top = fl[fl.season_jd.isin(SEASONS)].nlargest(10, "individuals")[
        ["season_jd", "event_ssid", "origin_pcode", "event_pcode", "start_date", "individuals"]]
    zoa = jd[jd.adm2_pcode.isin(ZOA_COUNTIES)].pivot(index="adm2_pcode", columns="season", values="flood_ind")
    zoa.index = [f"{ZOA_COUNTIES[p]} ({p})" for p in zoa.index]
    origin_eq_event = fl[fl.season_jd.isin(SEASONS)].assign(same=lambda d: d.origin_pcode == d.event_pcode)
    same_share = origin_eq_event.groupby("season_jd").apply(
        lambda d: d.loc[d.same, "individuals"].sum() / d["individuals"].sum()).round(3).to_dict()

    # Marginals JSON (the only outcome input to the Stage 34 simulation)
    mon1 = _mon1_counties(events)
    mon2_jd, mon2_jm = mon2_mask(events, frame, "JD"), mon2_mask(events, frame, "JM")
    no23 = [s for s in panel_seasons if s != 2023]
    marg = {
        "spec_sha256": spec_hash(),
        "note": "Outcome-side marginals only. No county x season outcome values. Built by Stage 32.",
        "min_recorded_people": MIN_RECORDED_PEOPLE,
        "detection_rate_ocha": det_ocha["rate"], "detection_rate_ocha_n": det_ocha["n"],
        "detection_rate_mt": det_mt["rate"],
        "reliability_floor_rw": floor["r"], "reliability_floor_rw_ci": floor_ci,
        "reliability_ceiling_split_half": ceiling["median_sb"],
        "panel_seasons": panel_seasons, "usable_seasons": usable_seasons,
        "sets": {
            "JD_primary": _season_marginals(jd, frame, panel_seasons, mon1, mon2_jd),
            "JD_no2023": _season_marginals(jd, frame, no23, mon1, mon2_jd),
            "JD_all5": _season_marginals(jd, frame, list(SEASONS), mon1, mon2_jd),
            "JM": _season_marginals(jm, frame, list(JM_SEASONS), mon1, mon2_jm),
        },
    }
    (OUT / "stage32_outcome_marginals.json").write_text(json.dumps(marg, indent=2), encoding="utf-8")
    pd.DataFrame(log).to_csv(OUT / "stage32_join_log.csv", index=False)
    usable.to_csv(OUT / "stage32_usable_seasons.csv", index=False)
    det_o.to_csv(OUT / "stage32_detection_ocha.csv", index=False)
    det_m.to_csv(OUT / "stage32_detection_mt.csv", index=False)

    # Kill criteria
    det_for_kill = det_ocha["rate"] if det_ocha["n"] >= 10 else det_mt["rate"]
    kills = [
        {"criterion": "Usable seasons >= 3", "value": len(usable_seasons), "pass": len(usable_seasons) >= 3},
        {"criterion": f"F71 counties with varying outcome across usable seasons >= {MIN_VARYING}",
         "value": n_vary_usable, "pass": n_vary_usable >= MIN_VARYING},
        {"criterion": f"Detection rate (OCHA >= 10k; MT if OCHA n < 10) >= {MIN_DETECTION}",
         "value": round(det_for_kill, 3), "pass": det_for_kill >= MIN_DETECTION},
    ]
    kills_df = pd.DataFrame(kills).astype({"value": str})
    result = {
        "pass": bool(kills_df["pass"].all()), "usable_seasons": usable_seasons, "panel_seasons": panel_seasons,
        "n_varying_usable": n_vary_usable, "n_varying_panel": n_vary_panel,
        "nonzero_seasons_per_county": {int(k): int(v) for k, v in nz_count.items()},
        "detection_ocha": det_ocha, "detection_mt": det_mt, "rule_2023": rule_2023,
        "reliability_floor": {"r_w": floor["r"], "ci_boot": floor_ci, "n": floor["n"], "n_counties": floor["n_clusters"],
                              "r_w_f71": floor_f71_r, "R_ET_floor": floor["r"] ** 2 if floor["r"] > 0 else 0.0},
        "reliability_ceiling": ceiling, "tails": tails, "origin_equals_event_share": same_share,
        "mon1_counties_in_f71": len(mon1 & f71),
        "mon2_observed_share_jd": float(mon2_jd["mon2_observed"].mean()),
    }
    (OUT / "stage32_summary.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    _write_stage32_gate(result, kills_df, usable, totals, top, zoa, log)
    return result


def _wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [np.nan, np.nan]
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(float(c - h), 3), round(float(c + h), 3)]


def _write_stage32_gate(res: dict, kills: pd.DataFrame, usable: pd.DataFrame, totals: pd.DataFrame,
                        top: pd.DataFrame, zoa: pd.DataFrame, log: list[dict]) -> None:
    status = "PASS" if res["pass"] else "FAIL — NO-GO (SE-H1 falsified)"
    do, dm, r23 = res["detection_ocha"], res["detection_mt"], res["rule_2023"]
    fl, ce = res["reliability_floor"], res["reliability_ceiling"]
    text = [
        "# Stage 32 gate — Event Tracking outcome audit (SE-H1)",
        "",
        f"**Status: {status}.**",
        "",
        "Outcome-side only: no severity data were read in this stage.",
        "",
        "## Kill criteria",
        "",
        _md_table(kills.assign(**{"pass": kills["pass"].map({True: "pass", False: "**FAIL**"})})),
        "",
        "## Seasons (June–December, F71 frame)",
        "",
        _md_table(usable.rename(columns={"count": "n_lag"}), "{:,.2f}"),
        "",
        f"- Usable seasons: **{res['usable_seasons']}**. Primary panel seasons after the 2023 rule: "
        f"**{res['panel_seasons']}**.",
        f"- 2023 rule (Mobility Tracking detection): 2023 rate {r23['mt_rate_2023']:.3f} vs threshold "
        f"{r23['threshold']:.3f} (half the median of 2021/2022/2024 = {r23['median_other']:.3f}) → "
        f"**{'keep' if r23['keep_2023'] else 'drop'} 2023**.",
        f"- F71 counties whose outcome varies: {res['n_varying_usable']} across usable seasons, "
        f"{res['n_varying_panel']} across panel seasons.",
        f"- Non-zero seasons per F71 county (panel seasons): {res['nonzero_seasons_per_county']}.",
        f"- Share of flood people whose origin = event county, by season: {res['origin_equals_event_share']}.",
        f"- MON-1 counties in F71: {res['mon1_counties_in_f71']}. MON-2 observed share of F71 county-seasons: "
        f"{res['mon2_observed_share_jd']:.3f}.",
        "",
        "## Detection",
        "",
        f"- **OCHA** (county-seasons with ≥ 10,000 affected; OCHA files 2021, 2022, 2024, 2025): "
        f"**{do['rate']:.3f}** of {do['n']} have any ET flood record from that origin county "
        f"(Wilson 95% CI {do['wilson_ci']}); F71 only {do['rate_f71']:.3f} of {do['n_f71']}. "
        f"By season: {do['by_season']}.",
        f"- **Mobility Tracking** (first-round disaster arrivals ≥ 1,000; R13–R16 for 2021–2024): "
        f"**{dm['rate']:.3f}** of {dm['n']} (origin rule); event-location rule {dm['rate_event_location']:.3f}. "
        f"By season: {dm['by_season']}.",
        "- Caveats: OCHA 'affected' is not 'displaced'; Mobility Tracking arrivals are all disaster types, by "
        "calendar arrival year and host county. Both rates are therefore lower bounds on ET's recording of "
        "flood displacement large enough to count.",
        "",
        "## Outcome reliability (informative only, not kill criteria)",
        "",
        f"- Floor: within-county ET–OCHA correlation r_w = **{fl['r_w']:.3f}** (county bootstrap 95% CI "
        f"{fl['ci_boot'][0]:.3f} to {fl['ci_boot'][1]:.3f}; n = {fl['n']}, {fl['n_counties']} counties; "
        f"F71 only {fl['r_w_f71']:.3f}). R_ET ≥ r_w² = **{fl['R_ET_floor']:.3f}** if errors are independent. "
        "OCHA snapshots stacked (declared deviation).",
        f"- Ceiling: random split-half of ET rows, Spearman–Brown corrected: median **{ce['median_sb']:.3f}** "
        f"(2.5–97.5%: {ce['p2_5']:.3f}–{ce['p97_5']:.3f}; {ce['n_splits']} splits). Inflated because one "
        "flood episode is spread across many rows.",
        "",
        "## Plausibility",
        "",
        _md_table(totals, "{:,.0f}"),
        "",
        "Largest ET flood rows (June–December):",
        "",
        _md_table(top.assign(start_date=top["start_date"].dt.date), "{:,.0f}"),
        "",
        "ZOA counties, ET flood displacement by origin (people; descriptive only):",
        "",
        _md_table(zoa.reset_index().rename(columns={"index": "county"}), "{:,.0f}"),
        "",
        f"- Out-of-window flood rows: {res['tails']}.",
        "",
        "## Join log",
        "",
        _md_table(pd.DataFrame(log)),
        "",
        "## Questions for IOM (team to send via ZOA or ISSDTM@iom.int; interpretation only)",
        "",
        "1. Is ET coverage national in every year 2021–2025, or limited to counties with active DTM teams?",
        "2. Does the absence of an ET record for a county-season mean no displacement over 50 households?",
        "3. Were ET enumerators redeployed in 2023 (Sudan returnee response at Renk), reducing flood coverage?",
        "4. Does OCHA's flood 'affected/displaced' reporting use ET figures (shared-source error)?",
        "5. In the 2025 file, do `Arrival Location:*` columns mean the origin (as `Arrival from:*` in 2021–2024)?",
        "",
        "```powershell",
        "python -m archive.impact_eda.impact_session_e --only 32",
        "```",
    ]
    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE32_GATE.md").write_text("\n".join(text), encoding="utf-8")


# ---------------------------------------------------------------- Stage 33: severity audit (severity-only)

SEV_RAW = OUT / "stage33_severity_raw.csv"
SEV_YEARS = range(2001, 2026)
JD_FIRST_DEKAD = 15  # 1 June
MIN_SPLIT_HALF = 0.4
TILE_FE_SHARE = 0.10
EXPOSED_THRESHOLDS = (1, 5, 25)  # km², unusual class, June–December


def build_severity_raw(force: bool = False, log: list[dict] | None = None) -> pd.DataFrame:
    """County x calendar-year x part (JD / JanMay) pixel-dekad aggregates for both class sets.

    exd = Σ over detected pixel-dekads of pixel area (km² × dekads) = extent × mean duration."""
    log = [] if log is None else log
    if SEV_RAW.exists() and not force:
        return pd.read_csv(SEV_RAW)
    lookup = pd.read_csv(build_pixel_lookup())
    files: dict[int, list[tuple[str, str, Path]]] = {}
    for kind, year, tile, path in _flood_parquet_paths():
        if year in SEV_YEARS:
            files.setdefault(year, []).append((kind, tile, path))
    rows = []
    for year in sorted(files):
        parts = []
        for kind, tile, path in files[year]:
            df = pd.read_parquet(path, columns=["date", "lat", "lon"])
            dek = _dekad_codes(df["date"])
            keep = dek >= JD_FIRST_DEKAD if year < 2022 else np.ones(len(dek), bool)
            d = pd.DataFrame({"lat": df["lat"].to_numpy()[keep], "lon": df["lon"].to_numpy()[keep], "dekad": dek[keep]})
            d = _coord_keys(d)[["lat_k", "lon_k", "dekad"]].drop_duplicates()
            parts.append(d.assign(cls=kind, tile=tile))
        px = pd.concat(parts, ignore_index=True)
        n0 = len(px)
        px = px.merge(lookup, on=["lat_k", "lon_k"], how="inner")
        _log(log, f"masks {year}: pixel-dekads -> admin2 lookup", n0, len(px), "outside admin2 dropped")
        px["area"] = (PIXEL_DEG * 111.32) ** 2 * np.cos(np.radians(px["lat_k"]))
        for class_set in ("unusual", "combined"):
            sub = px[px["cls"] == "unusual"] if class_set == "unusual" else px
            sub = sub.drop_duplicates(subset=["lat_k", "lon_k", "dekad"])
            for part, mask in (("JD", sub["dekad"] >= JD_FIRST_DEKAD), ("JanMay", sub["dekad"] < JD_FIRST_DEKAD)):
                if part == "JanMay" and year < 2022:
                    continue
                q = sub[mask]
                a = q["area"]
                agg = pd.DataFrame({
                    "exd": a.groupby(q["adm2_pcode"]).sum(),
                    "exd_odd": a.where(q["dekad"] % 2 == 1, 0).groupby(q["adm2_pcode"]).sum(),
                    "exd_julsep": a.where(q["dekad"].between(18, 26), 0).groupby(q["adm2_pcode"]).sum(),
                    "exd_novdec": a.where(q["dekad"] >= 30, 0).groupby(q["adm2_pcode"]).sum(),
                    "exd_h20v08": a.where(q["tile"] == "h20v08", 0).groupby(q["adm2_pcode"]).sum(),
                    "extent_km2": q.drop_duplicates(["lat_k", "lon_k"]).groupby("adm2_pcode")["area"].sum(),
                }).reset_index()
                agg["exd_even"] = agg["exd"] - agg["exd_odd"]
                rows.append(agg.assign(year=year, class_set=class_set, part=part))
    raw = pd.concat(rows, ignore_index=True)
    raw.to_csv(SEV_RAW, index=False)
    return raw


def severity_season_table(raw: pd.DataFrame) -> pd.DataFrame:
    """Season severity for every admin2: JD 2001–2025 and June–May 2021/22–2024/25 (0 if no detection)."""
    counties = sorted(_admin2_pcodes())
    vals = ["exd", "exd_odd", "exd_even", "exd_julsep", "exd_novdec", "exd_h20v08", "extent_km2"]
    jd = raw[raw["part"] == "JD"].rename(columns={"year": "season"}).assign(window="JD")
    jan = raw[raw["part"] == "JanMay"].assign(season=lambda d: d["year"] - 1)
    jm_parts = []
    for cs in ("unusual", "combined"):
        a = jd[(jd.class_set == cs) & jd.season.isin(JM_SEASONS)].set_index(["adm2_pcode", "season"])[vals[:-1]]
        b = jan[(jan.class_set == cs) & jan.season.isin(JM_SEASONS)].set_index(["adm2_pcode", "season"])[vals[:-1]]
        s = a.add(b, fill_value=0).reset_index().assign(class_set=cs, window="JM", extent_km2=np.nan)
        jm_parts.append(s)
    out = []
    for window, df, seasons in (("JD", jd, SEV_YEARS), ("JM", pd.concat(jm_parts), JM_SEASONS)):
        for cs in ("unusual", "combined"):
            grid = pd.DataFrame([(c, s) for c in counties for s in seasons], columns=["adm2_pcode", "season"])
            sub = df[df.class_set == cs][["adm2_pcode", "season"] + vals]
            g = grid.merge(sub, on=["adm2_pcode", "season"], how="left")
            fillcols = vals if window == "JD" else vals[:-1]
            g[fillcols] = g[fillcols].fillna(0.0)
            out.append(g.assign(class_set=cs, window=window))
    sev = pd.concat(out, ignore_index=True)
    sev["x"] = np.log1p(sev["exd"])
    return sev


def county_tiles(sev: pd.DataFrame) -> pd.Series:
    """Majority MODIS tile per county, by detections 2001–2025 (combined classes, JD)."""
    s = sev[(sev.window == "JD") & (sev.class_set == "combined")].groupby("adm2_pcode")[["exd", "exd_h20v08"]].sum()
    return pd.Series(np.where(s["exd_h20v08"] >= s["exd"] / 2, "h20v08", "h21v08"), index=s.index, name="tile")


def _split_half(sev: pd.DataFrame, counties: set[str], seasons: list[int], class_set: str) -> dict:
    t = sev[(sev.window == "JD") & (sev.class_set == class_set) & sev.adm2_pcode.isin(counties)
            & sev.season.isin(seasons)]
    r = twfe_cr2(np.log1p(t["exd_odd"]), np.log1p(t["exd_even"]), t["adm2_pcode"], t["season"])["r"]
    return {"r_half": r, "spearman_brown": 2 * r / (1 + r), "n": int(len(t))}


def run_stage33(force: bool = False) -> dict:
    log: list[dict] = []
    raw = build_severity_raw(force, log)
    sev = severity_season_table(raw)
    tiles = county_tiles(sev)
    sev = sev.merge(tiles.rename("tile").reset_index(), on="adm2_pcode", how="left")
    frame = _frame()
    f71 = set(frame["adm2_pcode"])
    sev["in_f71"] = sev["adm2_pcode"].isin(f71)

    # Frame flags from 2001–2020 unusual-class June–December extent
    hist = sev[(sev.window == "JD") & (sev.class_set == "unusual") & sev.season.isin(FRAME_YEARS)]
    flags = {}
    for thr in EXPOSED_THRESHOLDS:
        n_ok = hist.assign(ok=hist.extent_km2 >= thr).groupby("adm2_pcode")["ok"].sum()
        flags[f"exposed_{thr}km2"] = n_ok >= len(FRAME_YEARS) / 2
    flag_df = pd.DataFrame(flags).reset_index()
    sev = sev.merge(flag_df, on="adm2_pcode", how="left")
    sev.to_csv(OUT / "stage33_severity_season.csv", index=False)

    s32 = json.loads((OUT / "stage32_summary.json").read_text())
    panel = s32["panel_seasons"]
    frames = {"F71": f71}
    for thr in EXPOSED_THRESHOLDS:
        frames[f"exposed_{thr}km2"] = f71 & set(flag_df.loc[flag_df[f"exposed_{thr}km2"], "adm2_pcode"])

    # Split-half ceiling on Rx (odd vs even dekads, two-way residuals, Spearman–Brown)
    sh = []
    for fname, cset in frames.items():
        for cs in ("combined", "unusual"):
            for label, seasons in (("panel", panel), ("all_2021_2025", list(SEASONS))):
                d = _split_half(sev, cset, seasons, cs)
                sh.append({"frame": fname, "class_set": cs, "seasons": label, "n_counties": len(cset), **d})
    sh_df = pd.DataFrame(sh)
    prim = sh_df[(sh_df.frame == "F71") & (sh_df.seasons == "panel")].set_index("class_set")
    chosen = str(prim["spearman_brown"].idxmax())
    ceiling = float(prim.loc[chosen, "spearman_brown"])

    # Tile x season fixed-effects rule (severity-side)
    t = sev[(sev.window == "JD") & (sev.class_set == chosen) & sev.in_f71 & sev.season.isin(panel)].reset_index(drop=True)
    base = TwfeDesign.build(np.zeros(len(t)), t.adm2_pcode, t.season)
    res_base = base.MD @ t["x"].to_numpy()
    ts = t["tile"] + "_" + t["season"].astype(str)
    full = TwfeDesign.build(np.zeros(len(t)), t.adm2_pcode, t.season, extra_fe=ts)
    res_full = full.MD @ t["x"].to_numpy()
    tile_share = float(1 - res_full @ res_full / (res_base @ res_base))
    use_tile_fe = tile_share >= TILE_FE_SHARE

    # Convergence with ERA5 June–December precipitation (within county)
    era = pd.read_csv(OUT / "stage16_era5_county_month.csv")
    era = era[era.month >= 6].groupby(["adm2_pcode", "year"])["precip_sum_m"].sum().rename("precip_jd").reset_index()
    conv = {}
    for label, seasons in (("panel", panel), ("all_2021_2025", list(SEASONS)), ("2001_2025", list(SEV_YEARS))):
        c = sev[(sev.window == "JD") & (sev.class_set == chosen) & sev.in_f71 & sev.season.isin(seasons)]
        c = c.merge(era.rename(columns={"year": "season"}), on=["adm2_pcode", "season"], how="inner")
        f = twfe_cr2(c["x"], np.log(c["precip_jd"]), c["adm2_pcode"], c["season"],
                     c["tile"] + "_" + c["season"].astype(str) if use_tile_fe else None)
        conv[label] = {"spearman_resid": round(f["spearman_resid"], 3), "r": round(f["r"], 3),
                       "r_ci": [round(f["r_ci_lo"], 3), round(f["r_ci_hi"], 3)], "n": f["n"]}
    era_fail = conv["panel"]["spearman_resid"] <= 0
    planning_rx = 0.4 if era_fail else min(0.6, ceiling)

    # Blind-season profile (share of June–December pixel-dekads in Jul–Sep vs Nov–Dec)
    b = sev[(sev.window == "JD") & (sev.class_set == chosen) & sev.in_f71 & sev.season.isin(SEASONS) & (sev.exd > 0)]
    prof = b.assign(julsep=b.exd_julsep / b.exd, novdec=b.exd_novdec / b.exd)
    blind = {
        "county_season_julsep_share_median": float(prof.julsep.median()),
        "county_season_julsep_share_iqr": [float(prof.julsep.quantile(0.25)), float(prof.julsep.quantile(0.75))],
        "county_season_novdec_share_median": float(prof.novdec.median()),
        "national_julsep_share_by_season": prof.groupby("season").apply(
            lambda d: d.exd_julsep.sum() / d.exd.sum()).round(3).to_dict(),
        "national_novdec_share_by_season": prof.groupby("season").apply(
            lambda d: d.exd_novdec.sum() / d.exd.sum()).round(3).to_dict(),
        "note": "Jul–Sep = 9 of 21 June–December dekads (0.43 if detections were uniform).",
    }
    zero_seasons = int((sev[(sev.window == "JD") & (sev.class_set == chosen) & sev.in_f71 & sev.season.isin(panel)]
                        .exd == 0).sum())
    within_sd = float(res_base.std())

    kills = pd.DataFrame([{"criterion": f"Split-half ceiling on Rx (F71, panel seasons, {chosen}) >= {MIN_SPLIT_HALF}",
                           "value": f"{ceiling:.3f}", "pass": ceiling >= MIN_SPLIT_HALF}])
    rel = {
        "spec_sha256": spec_hash(), "chosen_class_set": chosen, "split_half_ceiling": ceiling,
        "split_half": sh_df.to_dict("records"), "tile_season_share": tile_share, "use_tile_season_fe": bool(use_tile_fe),
        "era5_convergence": conv, "era5_fail": bool(era_fail), "planning_rx": planning_rx,
        "blind_season": blind, "tiles": tiles.value_counts().to_dict(),
        "tiles_f71": tiles[tiles.index.isin(f71)].value_counts().to_dict(),
        "frame_sizes": {k: len(v) for k, v in frames.items()},
        "f71_zero_severity_county_seasons_panel": zero_seasons, "within_sd_x_panel": within_sd,
        "pass": bool(kills["pass"].all()),
    }
    (OUT / "stage33_reliability.json").write_text(json.dumps(rel, indent=2, default=str), encoding="utf-8")
    pd.DataFrame(log).to_csv(OUT / "stage33_join_log.csv", index=False)
    _write_stage33_gate(rel, kills, sh_df, log)
    return {k: v for k, v in rel.items() if k != "split_half"}


def _write_stage33_gate(rel: dict, kills: pd.DataFrame, sh: pd.DataFrame, log: list[dict]) -> None:
    status = "PASS" if rel["pass"] else "FAIL — NO-GO (SE-H2 falsified)"
    conv, bl = rel["era5_convergence"], rel["blind_season"]
    text = [
        "# Stage 33 gate — severity audit (SE-H2)",
        "",
        f"**Status: {status}.**",
        "",
        "Severity-side only: no ET outcome values were read (only the list of panel seasons from Stage 32).",
        "",
        "## Kill criterion",
        "",
        _md_table(kills.assign(**{"pass": kills["pass"].map({True: "pass", False: "**FAIL**"})})),
        "",
        "## Split-half reliability (odd vs even June–December dekads)",
        "",
        _md_table(sh[["frame", "class_set", "seasons", "n_counties", "n", "r_half", "spearman_brown"]]),
        "",
        f"- Mask class chosen by the pre-registered rule (higher split-half, F71, panel seasons): "
        f"**{rel['chosen_class_set']}**, ceiling **{rel['split_half_ceiling']:.3f}**.",
        "- This is a ceiling on Rx only: alternating dekads share the same flood, the same cloud regime and the "
        "same season-wide omission errors (masks are blind under persistent cloud, `cloud_frac` = 0 everywhere).",
        "",
        "## Convergence with ERA5 June–December precipitation (within county, log precip)",
        "",
        _md_table(pd.DataFrame(conv).T.reset_index().rename(columns={"index": "seasons"})),
        "",
        f"- ERA5 convergence fails (≤ 0 on panel seasons)? **{rel['era5_fail']}** → planning Rx = "
        f"**{rel['planning_rx']:.2f}**.",
        "",
        "## Tile artefacts",
        "",
        f"- Counties per majority tile (F71): {rel['tiles_f71']}.",
        f"- Share of county-and-season-demeaned severity variance explained by tile × season dummies: "
        f"**{rel['tile_season_share']:.3f}** (rule: add tile × season FE if ≥ {TILE_FE_SHARE}) → "
        f"**{'add' if rel['use_tile_season_fe'] else 'do not add'} tile × season FE**.",
        "",
        "## Blind-season profile (parameter φ)",
        "",
        f"- Median county-season share of June–December pixel-dekads in Jul–Sep: {bl['county_season_julsep_share_median']:.3f} "
        f"(IQR {bl['county_season_julsep_share_iqr'][0]:.3f}–{bl['county_season_julsep_share_iqr'][1]:.3f}); "
        f"Nov–Dec median {bl['county_season_novdec_share_median']:.3f}. {bl['note']}",
        f"- National Jul–Sep share by season: {bl['national_julsep_share_by_season']}; Nov–Dec: "
        f"{bl['national_novdec_share_by_season']}.",
        "- ET flood events start mostly July–October (Stage 32), when the masks see least. Severity therefore "
        "leans on the post-peak recession; the simulation carries this as error correlated with truth (φ = −0.2).",
        "",
        "## Frame options",
        "",
        f"- Frame sizes: {rel['frame_sizes']} (flood-exposed = unusual-class June–December extent ≥ threshold in "
        "at least 10 of the 2001–2020 seasons, within F71).",
        f"- F71 county-seasons with zero detected severity (panel seasons): {rel['f71_zero_severity_county_seasons_panel']}.",
        f"- Within-county SD of log1p severity after county and season effects: {rel['within_sd_x_panel']:.3f}.",
        "",
        "## Join log",
        "",
        _md_table(pd.DataFrame(log)) if log else "Severity read from cache `stage33_severity_raw.csv` "
        "(delete it to rebuild from the parquets).",
        "",
        "```powershell",
        "python -m archive.impact_eda.impact_session_e --only 33",
        "```",
    ]
    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE33_GATE.md").write_text("\n".join(text), encoding="utf-8")


# ---------------------------------------------------------------- Stage 34: realistic power, controls, gap register
#
# Simulation (reads severity + stage32_outcome_marginals.json only; never county x season outcomes):
#   x~   observed severity, two-way residualized on the skeleton, standardized (fixed across replications)
#   x*   true severity (within part, SD 1): sqrt(Rx_eff) x~ + sqrt(1 - Rx_eff) z~,  z~ residualized N(0, 1)
#        Rx_eff = Rx, or lower when the error is correlated with truth (phi, see _rx_effective)
#   L    latent index = a_i + b_t + c x* + e,  e = s_i (sqrt(1-tau) u + sqrt(tau) v_state,t),  u AR(1)
#   P    true displaced = exp(m_i + sigma_s (kappa L_w + sqrt(1-kappa^2) zeta)) if L > 0 else 0
#   rec  recorded if P >= 300 and detected; detection ~ Bernoulli(expit(logit pi + h_i + psi x~))
#   y    log1p(P exp(sigma_c eps - sigma_c^2 / 2)) if recorded else 0
#   a_i, b_t matched (probit IPF) to each county's share of recorded non-zero seasons and each
#   season's share of recorded non-zero counties; c bisected to the target within-county
#   correlation rho between x* and log1p(P); sigma_c bisected to the target outcome reliability
#   Ry = corr(y~, log1p(P)~)^2 (capped by detection when sigma_c = 0 already falls short).

RHO_GRID = (0.0, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60)
RX_GRID = (0.4, 0.6, 0.8)
RY_GRID = (0.3, 0.5, 0.7)
KAPPA = 0.5          # share of log-size SD driven by the latent index
COUNTY_SD_LOGSD = 0.3
DETECT_HET_SD = 0.5  # county heterogeneity in detection (logit scale), rank-matched to recorded share
PHI = -0.2
TAU_ALT, AR_ALT = 0.2, 0.3
R_CELL, R_PLAN, R_OFAT, R_CAL = 1000, 2000, 500, 300
GO_MDE, NOGO_MDE = 0.35, 0.50
FPR_BAND = (0.035, 0.065)
MAX_PSI_FPR = 0.10
MIN_POSITIVE_CONTROL = 0.3


def _rx_effective(rx: float, phi: float) -> float:
    """Observed = true + error with corr(error, true) = phi and the error variance of the phi = 0 case."""
    if phi == 0:
        return rx
    sd_t, sd_u = np.sqrt(rx), np.sqrt(1 - rx)
    cov = rx + phi * sd_t * sd_u
    var_obs = rx + (1 - rx) + 2 * phi * sd_t * sd_u
    return float(cov**2 / (rx * var_obs))


@dataclass
class Skeleton:
    name: str
    county: np.ndarray
    season: np.ndarray
    ci: np.ndarray
    si: np.ndarray
    sti: np.ndarray
    x_obs: np.ndarray
    xs: np.ndarray            # standardized two-way residual of x_obs
    design: TwfeDesign
    q_county: np.ndarray      # target recorded-nonzero share per county (length G)
    q_season: np.ndarray      # target per season (length T)
    m_obs: np.ndarray         # county mean log size per obs
    sigma_s: float
    lam_obs: np.ndarray       # county mean non-flood records per obs
    nf_within_sd: float
    pi_detect: float
    G: int
    T: int
    S: int


def make_skeleton(name: str, sev: pd.DataFrame, marg: dict, counties: set[str], set_name: str,
                  window: str = "JD", mon2: bool = False, extra_fe=None) -> Skeleton:
    ms = marg["sets"][set_name]
    seasons = ms["seasons"]
    t = sev[(sev.window == window) & sev.adm2_pcode.isin(counties) & sev.season.isin(seasons)]
    t = t.sort_values(["adm2_pcode", "season"]).reset_index(drop=True)
    if mon2:
        obs = {(p, s) for p, s in ms["mon2_observed"]}
        t = t[[(p, s) in obs for p, s in zip(t.adm2_pcode, t.season)]].reset_index(drop=True)
        t = t[t.groupby("adm2_pcode")["season"].transform("size") >= 2].reset_index(drop=True)
    cinfo = ms["counties"]
    ci, cu = pd.factorize(t["adm2_pcode"], sort=True)
    si, su = pd.factorize(t["season"], sort=True)
    sti, _ = pd.factorize(t["adm2_pcode"].map(lambda p: cinfo[p]["state"]), sort=True)
    design = TwfeDesign.build(t["x"], t["adm2_pcode"], t["season"], extra_fe)
    xs = design.x_res / design.x_res.std()
    T_i = np.array([cinfo[p]["n_seasons"] for p in cu], float)
    k_i = np.array([cinfo[p]["n_nonzero"] for p in cu], float)
    q_c = np.clip(k_i / T_i, 0.03, 0.97)
    q_s = np.array([ms["seasons_summary"][str(s)]["share_nonzero"] for s in su])
    q_s = np.clip(q_s, 0.03, 0.97)
    gmean = ms["log_nonzero_mean"]
    m_c = np.array([cinfo[p]["mean_log_nonzero"] if cinfo[p]["mean_log_nonzero"] is not None else gmean for p in cu])
    lam_c = np.array([max(cinfo[p]["nonflood_records_mean"], 0.05) for p in cu])
    return Skeleton(name=name, county=t["adm2_pcode"].to_numpy(), season=t["season"].to_numpy(), ci=ci, si=si,
                    sti=sti, x_obs=t["x"].to_numpy(), xs=xs, design=design, q_county=q_c, q_season=q_s,
                    m_obs=m_c[ci], sigma_s=float(ms["log_nonzero_within_sd"]), lam_obs=lam_c[ci],
                    nf_within_sd=float(ms["nonflood_log1p_within_sd"]), pi_detect=float(marg["detection_rate_ocha"]),
                    G=len(cu), T=len(su), S=int(sti.max()) + 1)


def _probit(p):
    return stats.norm.ppf(np.clip(p, 0.002, 0.998))


def _colcorr(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return (A * B).sum(0) / np.sqrt((A * A).sum(0) * (B * B).sum(0))


class OutcomeSim:
    """Hurdle outcome simulation on one skeleton with fixed county heterogeneity."""

    def __init__(self, sk: Skeleton, rx: float, tau: float = 0.0, ar: float = 0.0, psi: float = 0.0,
                 phi: float = 0.0, seed: int = 0, pi: float | None = None):
        self.sk, self.tau, self.ar, self.psi = sk, tau, ar, psi
        self.rx_eff = _rx_effective(rx, phi)
        rng = np.random.default_rng(seed)
        s = np.exp(rng.normal(0, COUNTY_SD_LOGSD, sk.G))
        self.s_i = s / np.sqrt(np.mean(s**2))
        h = np.sort(rng.normal(0, DETECT_HET_SD, sk.G))
        order = np.argsort(np.argsort(sk.q_county + 1e-9 * rng.random(sk.G)))
        self.h_i = h[order]
        # mean detection over counties equals the OCHA-based detection rate
        from scipy.optimize import brentq

        target = sk.pi_detect if pi is None else pi
        self.logit_pi = brentq(lambda l: np.mean(1 / (1 + np.exp(-(l + self.h_i)))) - target, -10, 10)
        self.a = _probit(sk.q_county) + 0.5
        self.b = np.zeros(sk.T)

    def draw(self, R: int, c: float, sigma_c: float, seed: int, parts: bool = False) -> dict:
        sk = self.sk
        rng = np.random.default_rng(seed)
        n = len(sk.ci)
        z = sk.design.MD @ rng.standard_normal((n, R))
        z /= z.std(axis=0, keepdims=True)
        xstar = np.sqrt(self.rx_eff) * sk.xs[:, None] + np.sqrt(1 - self.rx_eff) * z
        u = rng.standard_normal((sk.G, sk.T, R))
        for t in range(1, sk.T):
            u[:, t] = self.ar * u[:, t - 1] + np.sqrt(1 - self.ar**2) * u[:, t]
        v = rng.standard_normal((sk.S, sk.T, R))
        e = self.s_i[sk.ci][:, None] * (np.sqrt(1 - self.tau) * u[sk.ci, sk.si] + np.sqrt(self.tau) * v[sk.sti, sk.si])
        dev = c * xstar + e
        L = self.a[sk.ci][:, None] + self.b[sk.si][:, None] + dev
        lw = dev / np.sqrt(c**2 + 1)
        logsize = sk.m_obs[:, None] + sk.sigma_s * (KAPPA * lw + np.sqrt(1 - KAPPA**2) * rng.standard_normal((n, R)))
        P = np.where(L > 0, np.exp(logsize), 0.0)
        p_det = 1 / (1 + np.exp(-(self.logit_pi + self.h_i[sk.ci][:, None] + self.psi * sk.xs[:, None])))
        rec = (P >= MIN_RECORDED_PEOPLE) & (rng.random((n, R)) < p_det)
        count = P * np.exp(sigma_c * rng.standard_normal((n, R)) - sigma_c**2 / 2)
        y = np.where(rec, np.log1p(count), 0.0)
        out = {"y": y, "y_true": np.log1p(P), "rec": rec}
        if parts:
            out["xstar"] = xstar
        return out

    def match(self, c: float, iters: int = 12, R: int = R_CAL, seed: int = 11) -> dict:
        sk = self.sk
        for _ in range(iters):
            rec = self.draw(R, c, 0.0, seed)["rec"]
            qc = np.array([rec[sk.ci == g].mean() for g in range(sk.G)])
            self.a += _probit(sk.q_county) - _probit(qc)
            rec = self.draw(R, c, 0.0, seed)["rec"]
            qs = np.array([rec[sk.si == t].mean() for t in range(sk.T)])
            self.b += _probit(sk.q_season) - _probit(qs)
        rec = self.draw(R, c, 0.0, seed)["rec"]
        qc = np.array([rec[sk.ci == g].mean() for g in range(sk.G)])
        qs = np.array([rec[sk.si == t].mean() for t in range(sk.T)])
        return {"county_mae": float(np.mean(np.abs(qc - sk.q_county))),
                "season_mae": float(np.mean(np.abs(qs - sk.q_season)))}

    def rho_of(self, c: float, R: int = R_CAL, seed: int = 12) -> float:
        d = self.draw(R, c, 0.0, seed, parts=True)
        MD = self.sk.design.MD
        return float(np.nanmean(_colcorr(MD @ d["xstar"], MD @ d["y_true"])))

    def ry_of(self, c: float, sigma_c: float, R: int = R_CAL, seed: int = 13) -> float:
        d = self.draw(R, c, sigma_c, seed)
        MD = self.sk.design.MD
        return float(np.nanmean(_colcorr(MD @ d["y"], MD @ d["y_true"])) ** 2)

    def calibrate(self, rho: float, ry: float) -> dict:
        """Bisect c to rho (re-matching marginals at each step) and sigma_c to Ry."""
        if rho == 0:
            c = 0.0
            fit = self.match(0.0)
        else:
            lo, hi = 0.0, 6.0
            for _ in range(22):
                c = (lo + hi) / 2
                fit = self.match(c, iters=6)
                if self.rho_of(c) < rho:
                    lo = c
                else:
                    hi = c
            c = (lo + hi) / 2
            fit = self.match(c)
            for _ in range(3):  # secant-style correction after the full re-match
                r_now = self.rho_of(c)
                if abs(r_now - rho) < 0.003:
                    break
                c *= rho / r_now
                fit = self.match(c)
        rho_ach = self.rho_of(c) if rho > 0 else 0.0
        cap = self.ry_of(c, 0.0)
        if cap <= ry:
            sigma_c, ry_ach = 0.0, cap
        else:
            lo, hi = 0.0, 6.0
            for _ in range(22):
                sigma_c = (lo + hi) / 2
                if self.ry_of(c, sigma_c) > ry:
                    lo = sigma_c
                else:
                    hi = sigma_c
            sigma_c = (lo + hi) / 2
            ry_ach = self.ry_of(c, sigma_c)
        return {"c": c, "sigma_c": sigma_c, "rho_achieved": rho_ach, "ry_cap": cap, "ry_achieved": ry_ach, **fit}


def run_cell(sk: Skeleton, rx: float, ry: float, rho: float, R: int, seed: int, **kw) -> dict:
    sim = OutcomeSim(sk, rx, seed=seed, **kw)
    cal = sim.calibrate(rho, ry)
    d = sim.draw(R, cal["c"], cal["sigma_c"], seed=seed + 1)
    f = sk.design.fit_many(d["y"])
    ok = np.isfinite(f["ci_lo"])
    power = float(np.mean(f["ci_lo"][ok] > 0))
    two = float(np.mean((f["ci_lo"][ok] > 0) | (f["ci_hi"][ok] < 0)))
    return {"skeleton": sk.name, "n_obs": len(sk.ci), "n_counties": sk.G, "rx": rx, "rx_eff": sim.rx_eff, "ry": ry,
            "rho": rho, "R": int(ok.sum()), "power": power, "power_mcse": float(np.sqrt(power * (1 - power) / ok.sum())),
            "reject_two_sided": two, "mean_r_obs": float(np.nanmean(f["r"])),
            "share_y_constant": float(np.mean(~ok)), "bm_df": float(sk.design.df), **cal,
            **{k: v for k, v in kw.items()}}


def mde80(rows: pd.DataFrame, n_draw: int = 2000, seed: int = 0) -> dict:
    """Smallest rho with power >= 0.8 (logit interpolation) and a parametric Monte Carlo CI."""
    # interpolate on the achieved true within-county correlation (high targets can be unreachable
    # under the hurdle model; the achieved value is what the power refers to)
    r = rows.assign(rho_eff=rows["rho_achieved"].where(rows["rho"] > 0, 0.0)).sort_values("rho_eff")
    rhos, pw, ns = r["rho_eff"].to_numpy(), r["power"].to_numpy(), r["R"].to_numpy()

    def solve(p: np.ndarray) -> float:
        p = np.maximum.accumulate(np.clip(p, 1e-4, 1 - 1e-4))
        idx = np.flatnonzero(p >= 0.8)
        if len(idx) == 0:
            return np.inf
        j = idx[0]
        if j == 0:
            return float(rhos[0])
        lg = np.log(p / (1 - p))
        target = np.log(4.0)
        return float(rhos[j - 1] + (target - lg[j - 1]) * (rhos[j] - rhos[j - 1]) / (lg[j] - lg[j - 1]))

    est = solve(pw)
    rng = np.random.default_rng(seed)
    draws = np.array([solve(rng.binomial(ns, pw) / ns) for _ in range(n_draw)])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {"mde80": est, "ci_lo": float(lo), "ci_hi": float(hi)}


def band(m: dict) -> str:
    """Decision band; if the MC CI straddles a cut-off, the worse band applies."""
    worst = max(m["mde80"], m["ci_hi"])
    if worst <= GO_MDE:
        return "GO"
    if worst <= NOGO_MDE:
        return "TEAM DECISION"
    return "NO-GO"


def _calibrate_psi(sk: Skeleton, r_target: float, R: int = 400, seed: int = 21) -> dict:
    """Map the circularity control (within r of severity vs log1p non-flood records) to a log-intensity
    slope psi on x~, with overdispersion matched to the observed within-county SD of log1p records."""
    rng = np.random.default_rng(seed)
    n = len(sk.ci)
    eps = rng.standard_normal((n, R))
    unif = rng.random((n, R))
    MD = sk.design.MD

    def sim(psi: float, sd_eta: float) -> np.ndarray:
        # median-preserving overdispersion: within-county SD then rises monotonically with sd_eta
        mu = sk.lam_obs[:, None] * np.exp(psi * sk.xs[:, None] + sd_eta * eps)
        return np.log1p(stats.poisson.ppf(unif, mu))

    lo, hi = 0.0, 4.0
    for _ in range(20):
        sd = (lo + hi) / 2
        w = MD @ sim(0.0, sd)
        if np.mean(w.std(axis=0)) < sk.nf_within_sd:
            lo = sd
        else:
            hi = sd
    sd_eta = (lo + hi) / 2
    lo, hi = -3.0, 3.0
    for _ in range(22):
        psi = (lo + hi) / 2
        r = np.nanmean(_colcorr(MD @ sim(psi, sd_eta), sk.xs[:, None] * np.ones((1, R))))
        if r < r_target:
            lo = psi
        else:
            hi = psi
    psi = (lo + hi) / 2
    w = MD @ sim(0.0, sd_eta)
    r_ach = float(np.nanmean(_colcorr(MD @ sim(psi, sd_eta), sk.xs[:, None] * np.ones((1, R)))))
    return {"psi": psi, "sd_eta": sd_eta, "within_sd_achieved": float(np.mean(w.std(axis=0))),
            "within_sd_target": sk.nf_within_sd, "r_target": float(r_target), "r_achieved": r_ach}


def _gap_register(res: dict) -> pd.DataFrame:
    g = [
        ("Survey timing, Mobility Tracking", "outcome switch", "fatal for MT; resolved by switching to ET",
         "within_county_dtm_reliability.json (0.00–0.49)"),
        ("Survey timing, ET", "test + rule", "start-date assignment; assessment lag by season",
         "Stage 32 lag table (median 11–19 d, p90 up to 75 d in 2025)"),
        ("Survey timing, OCHA", "clause", "OCHA used only for detection and the reliability floor",
         "snapshots Oct–Dec; 2024 file undated"),
        ("Masks blind Jul–Sep while ET peaks Jul–Oct", "parameter phi",
         f"phi = {PHI}: Rx_eff {res['rx_eff_phi']:.2f} at planning Rx", "Stage 33 blind-season profile"),
        ("Monitoring effort and circularity", "parameter psi + control",
         f"psi = {res['psi']['psi']:.3f} from control r = {res['circularity']['r']:.3f}",
         f"FPR at psi {res['psi_fpr']:.3f}"),
        ("Hubs (origin vs event county)", "clause", "origin = event county for 92–100% of people", "Stage 32"),
        ("2023 mislabelled returns", "label rule", "forced returns never flood", "Stage 31 test"),
        ("2023 coverage collapse", "rule", "2023 dropped by pre-registered MT-detection rule", "Stage 32"),
        ("2025 garbled names", "rule", "join on pcodes only", "Stage 31 test"),
        ("No ET data for December 2025", "window + sensitivity", "June–December window; season-set sensitivity",
         "Stage 34 OFAT"),
        ("2020-season tails in the 2021 file", "rule", "start-date assignment (3 rows, out of panel)", "Stage 32"),
        ("Split totals across sites", "rule", "summed by origin and season", "Stage 32"),
        ("Sub-threshold rows", "rule + parameter", "kept; simulation records only P >= 300", "Stage 34"),
        ("Spatially correlated shocks", "parameter tau + LOSO", f"tau = {TAU_ALT}", "Stage 34 OFAT; SE-H4 LOSO"),
        ("Sudd dominance", "test (SE-H4)", "leave-one-state-out", "only after GO"),
        ("Tile seam", "test", f"tile x season share {res['tile_share']:.3f} < 0.10", "Stage 33"),
        ("Post-2020 regime only", "clause", "scope limited to 2021–2025", "—"),
        ("Rain-fed vs river-fed counties", "clause", "described, not tested", "—"),
        ("Outcome reliability unknown (ET–OCHA floor weak)", "parameter Ry grid", "Ry in {0.3, 0.5, 0.7}",
         f"floor r_w = {res['floor_rw']:.3f}"),
        ("Severity reliability only bounded above", "parameter Rx grid + GEE check",
         "Rx in {0.4, 0.6, 0.8}; Sentinel-1 check before any null claim", "Stage 33 ceiling"),
        ("Severity product regime change (2001–2020 vs 2021–2025 detection volume)", "clause",
         "panel restricted to 2021–2025; long-run ERA5 convergence negative", "Stage 33"),
    ]
    return pd.DataFrame(g, columns=["gap", "handling", "detail", "evidence"])


def run_stage34(quick: bool = False) -> dict:
    marg = json.loads((OUT / "stage32_outcome_marginals.json").read_text())
    rel = json.loads((OUT / "stage33_reliability.json").read_text())
    sev_all = pd.read_csv(OUT / "stage33_severity_season.csv")
    cs = rel["chosen_class_set"]
    sev = sev_all[sev_all.class_set == cs]
    frame = _frame()
    f71 = set(frame["adm2_pcode"])
    exposed = f71 & set(sev.loc[sev["exposed_5km2"].fillna(False).astype(bool), "adm2_pcode"])
    tiles = sev.groupby("adm2_pcode")["tile"].first()
    rx_plan = rel["planning_rx"]
    scale = 0.1 if quick else 1.0
    rc, rp, ro = (max(int(r * scale), 100) for r in (R_CELL, R_PLAN, R_OFAT))
    global RHO_GRID
    RHO_GRID = (0.0, 0.3, 0.6) if quick else (0.0, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60)

    # Primary-frame choice: planning-cell power curve on F71 and the 5 km² exposed frame
    sk = {"F71": make_skeleton("F71", sev, marg, f71, "JD_primary"),
          "exposed_5km2": make_skeleton("exposed_5km2", sev, marg, exposed, "JD_primary")}
    caps = {}
    for name, s in sk.items():
        sim = OutcomeSim(s, rx_plan, seed=1)
        caps[name] = sim.calibrate(0.35, 0.99)["ry_cap"]
    ry_plan = {k: min(0.5, v) for k, v in caps.items()}
    rows = []
    frame_mde = {}
    for name, s in sk.items():
        cur = [run_cell(s, rx_plan, ry_plan[name], rho, rp, seed=3400 + i) for i, rho in enumerate(RHO_GRID)]
        for r in cur:
            r.update({"variant": "planning", "frame": name})
        rows += cur
        frame_mde[name] = mde80(pd.DataFrame(cur))
    primary = min(frame_mde, key=lambda k: frame_mde[k]["mde80"])
    s0 = sk[primary]
    ryp = ry_plan[primary]

    # Full grid on the primary frame
    for rx in RX_GRID:
        rx_c = min(rx, rel["split_half_ceiling"])
        for ry in RY_GRID:
            if rx_c == rx_plan and ry == ryp:
                continue
            for i, rho in enumerate(RHO_GRID):
                r = run_cell(s0, rx_c, ry, rho, rc, seed=5000 + 100 * int(rx * 10) + 10 * int(ry * 10) + i)
                r.update({"variant": "grid", "frame": primary})
                rows.append(r)

    # Controls (pre-registered; allowed before unblinding)
    et = pd.read_csv(OUT / "stage32_et_origin_season.csv")
    et = et[(et.window == "JD") & et.season.isin(marg["panel_seasons"]) & et.adm2_pcode.isin(s0.county)]
    sv = sev[(sev.window == "JD") & sev.season.isin(marg["panel_seasons"]) & sev.adm2_pcode.isin(s0.county)]
    cm_y = et.groupby("adm2_pcode")["y"].mean().rename("mean_y")       # county means only
    cm_x = sv.groupby("adm2_pcode")["x"].mean().rename("mean_x")
    cmeans = pd.concat([cm_x, cm_y], axis=1)
    pos = float(cmeans["mean_x"].rank().corr(cmeans["mean_y"].rank()))
    cmeans.to_csv(OUT / "stage34_positive_control_county_means.csv")
    nf = et[["adm2_pcode", "season", "nonflood_records"]]           # flood columns dropped before the join
    circ_df = sv[["adm2_pcode", "season", "x"]].merge(nf, on=["adm2_pcode", "season"], how="inner")
    circ = twfe_cr2(np.log1p(circ_df["nonflood_records"]), circ_df["x"], circ_df["adm2_pcode"], circ_df["season"])
    psi = _calibrate_psi(s0, circ["r"])
    psi_hi = _calibrate_psi(s0, circ["r_ci_hi"])

    # One factor at a time on the planning cell
    ofat_specs = {
        "tau_0.2": dict(tau=TAU_ALT), "ar_0.3": dict(ar=AR_ALT), "phi_-0.2": dict(phi=PHI),
        "psi_hat": dict(psi=psi["psi"]), "psi_ci_hi": dict(psi=psi_hi["psi"]),
        "all_nuisance": dict(tau=TAU_ALT, ar=AR_ALT, phi=PHI, psi=psi["psi"]),
        # declared extra (not pre-registered, not decisive): detection if OCHA 'affected' overstates events
        "pi_0.8_extra": dict(pi=0.8),
    }
    ofat_sk = {
        "frame_alt": sk["exposed_5km2" if primary == "F71" else "F71"],
        "MON-1": make_skeleton("MON-1", sev, marg, {p for p in s0.county
                                                     if marg["sets"]["JD_primary"]["counties"][p]["mon1"]},
                               "JD_primary"),
        "MON-2": make_skeleton("MON-2", sev, marg, set(s0.county), "JD_primary", mon2=True),
        "with_2023": make_skeleton("with_2023", sev, marg, set(s0.county), "JD_all5"),
        "june_may": make_skeleton("june_may", sev, marg, set(s0.county), "JM", window="JM"),
    }
    for vname, kw in ofat_specs.items():
        for i, rho in enumerate(RHO_GRID):
            r = run_cell(s0, rx_plan, ryp, rho, ro, seed=7000 + 17 * i + len(vname), **kw)
            r.update({"variant": vname, "frame": primary})
            rows.append(r)
    for vname, s in ofat_sk.items():
        cap = OutcomeSim(s, rx_plan, seed=1).calibrate(0.35, 0.99)["ry_cap"]
        for i, rho in enumerate(RHO_GRID):
            r = run_cell(s, rx_plan, min(0.5, cap), rho, ro, seed=8000 + 17 * i + len(vname))
            r.update({"variant": vname, "frame": s.name})
            rows.append(r)
    grid = pd.DataFrame(rows)
    grid.to_csv(OUT / "stage34_power_grid.csv", index=False)

    # Inference calibration under the all-nuisance null (CR2 vs wild bootstrap vs tile randomization)
    sim = OutcomeSim(s0, rx_plan, tau=TAU_ALT, ar=AR_ALT, phi=PHI, seed=99)
    cal = sim.calibrate(0.0, ryp)
    n_null = max(int(1000 * scale), 100)
    Y = sim.draw(n_null, cal["c"], cal["sigma_c"], seed=100)["y"]
    f = s0.design.fit_many(Y)
    ok = np.isfinite(f["ci_lo"])
    fpr_cr2 = float(np.mean((f["ci_lo"][ok] > 0) | (f["ci_hi"][ok] < 0)))
    p_boot = wild_bootstrap_webb_many(s0.design, Y[:, ok], B=399, seed=101)
    fpr_boot = float(np.mean(p_boot < 0.05))
    tile_vec = pd.Series(s0.county).map(tiles).to_numpy()
    n_rand = min(n_null, 500)
    p_rand = [randomization_test_tile(Y[:, j], s0.x_obs, s0.county, s0.season, tile_vec, n_perm=199, seed=j)["p_rand"]
              for j in np.flatnonzero(ok)[:n_rand]]
    fpr_rand = float(np.mean(np.array(p_rand) < 0.05))
    fpr = {"CR2": fpr_cr2, "wild_webb": fpr_boot, "tile_randomization": fpr_rand, "n_rep": int(ok.sum()),
           "n_rep_randomization": len(p_rand), "mcse": float(np.sqrt(0.05 * 0.95 / ok.sum()))}
    in_band = {k: FPR_BAND[0] <= v <= FPR_BAND[1] for k, v in fpr.items() if k in ("CR2", "wild_webb",
                                                                                   "tile_randomization")}
    switch_to_boot = (not in_band["CR2"]) and in_band["wild_webb"]

    # psi-induced false positives (rho = 0, psi at the control estimate)
    psi_row = grid[(grid.variant == "psi_hat") & (grid.rho == 0)].iloc[0]
    psi_fpr = float(psi_row["reject_two_sided"])
    psi_hi_fpr = float(grid[(grid.variant == "psi_ci_hi") & (grid.rho == 0)].iloc[0]["reject_two_sided"])

    # MDE80 per variant
    mdes = []
    for (variant, fr), g in grid.groupby(["variant", "frame"]):
        if variant == "grid":
            continue
        m = mde80(g)
        mdes.append({"variant": variant, "frame": fr, "rx": g.rx.iloc[0], "ry": g.ry.iloc[0], **m, "band": band(m),
                     "fpr_rho0": float(g.loc[g.rho == 0, "reject_two_sided"].iloc[0])})
    for (rx, ry), g in pd.concat([grid[grid.variant == "grid"],
                                  grid[(grid.variant == "planning") & (grid.frame == primary)]]).groupby(["rx", "ry"]):
        m = mde80(g)
        mdes.append({"variant": "grid", "frame": primary, "rx": rx, "ry": ry, **m, "band": band(m),
                     "fpr_rho0": float(g.loc[g.rho == 0, "reject_two_sided"].iloc[0])})
    mde_df = pd.DataFrame(mdes)
    mde_df.to_csv(OUT / "stage34_mde.csv", index=False)
    plan = mde_df[(mde_df.variant == "planning") & (mde_df.frame == primary)].iloc[0]

    kills = pd.DataFrame([
        {"criterion": f"MDE80 (planning cell) <= {NOGO_MDE}", "value": f"{plan.mde80:.3f} [{plan.ci_lo:.3f}, {plan.ci_hi:.3f}]",
         "pass": bool(max(plan.mde80, plan.ci_hi) <= NOGO_MDE)},
        {"criterion": "Some inference method has FPR in [0.035, 0.065] (all-nuisance null)",
         "value": ", ".join(f"{k} {fpr[k]:.3f}" for k in in_band), "pass": bool(any(in_band.values()))},
        {"criterion": f"Positive control (between-county Spearman of means) >= {MIN_POSITIVE_CONTROL}",
         "value": f"{pos:.3f}", "pass": bool(pos >= MIN_POSITIVE_CONTROL)},
        {"criterion": f"FPR at psi-hat <= {MAX_PSI_FPR}", "value": f"{psi_fpr:.3f}", "pass": bool(psi_fpr <= MAX_PSI_FPR)},
    ])
    res = {
        "primary_frame": primary, "frame_mde": frame_mde, "ry_cap": caps, "planning_rx": rx_plan, "planning_ry": ryp,
        "planning_mde80": plan.to_dict(), "planning_band": plan["band"], "fpr_null": fpr, "in_band": in_band,
        "switch_to_bootstrap": bool(switch_to_boot), "positive_control": pos,
        "circularity": {k: circ[k] for k in ("r", "r_ci_lo", "r_ci_hi", "p", "n", "n_clusters")},
        "psi": psi, "psi_ci_hi": psi_hi, "psi_fpr": psi_fpr, "psi_ci_hi_fpr": psi_hi_fpr,
        "rx_eff_phi": _rx_effective(rx_plan, PHI), "tile_share": rel["tile_season_share"],
        "floor_rw": marg["reliability_floor_rw"], "pass": bool(kills["pass"].all()), "quick": quick,
    }
    gaps = _gap_register(res)
    gaps.to_csv(OUT / "stage34_gap_register.csv", index=False)
    (OUT / "stage34_summary.json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    _write_stage34_gate(res, kills, mde_df, grid, gaps)
    return res


def _write_stage34_gate(res: dict, kills: pd.DataFrame, mde: pd.DataFrame, grid: pd.DataFrame,
                        gaps: pd.DataFrame) -> None:
    status = "PASS" if res["pass"] else "FAIL — NO-GO (SE-H3 kill criterion)"
    p = res["planning_mde80"]
    prim = res["primary_frame"]
    plan_rows = grid[(grid.variant == "planning") & (grid.frame == prim)][
        ["rho", "R", "power", "power_mcse", "reject_two_sided", "mean_r_obs", "rho_achieved", "ry_achieved",
         "county_mae", "season_mae", "c", "sigma_c"]]
    gm = mde[mde.variant == "grid"].copy()
    gm["ry"] = gm["ry"].map(lambda v: f"Ry target {v:.2f}")
    tab = gm.pivot(index="rx", columns="ry", values="mde80")
    ry_ach = grid[grid.variant.isin(["grid", "planning"]) & (grid.frame == prim)].groupby("ry")["ry_achieved"].mean()
    ci = res["circularity"]
    text = [
        "# Stage 34 gate — realistic power, controls and gap register (SE-H3)",
        "",
        f"**Status: {status}.** Planning-cell decision band: **{res['planning_band']}**.",
        "" if not res["quick"] else "**QUICK RUN (reduced replications) — not for decisions.**",
        "",
        "The simulation reads only observed severity and `stage32_outcome_marginals.json`. The positive "
        "control outputs county means only; the circularity control uses ET non-flood records (flood "
        "columns dropped before the join).",
        "",
        "## Kill criteria",
        "",
        _md_table(kills.assign(**{"pass": kills["pass"].map({True: "pass", False: "**FAIL**"})})),
        "",
        "## Planning cell",
        "",
        f"- Primary frame (lower simulated MDE80, pre-registered rule): **{prim}**; MDE80 by frame: "
        + "; ".join(f"{k} {v['mde80']:.3f} [{v['ci_lo']:.3f}, {v['ci_hi']:.3f}]" for k, v in res["frame_mde"].items()) + ".",
        f"- Rx = {res['planning_rx']:.2f} (min(0.6, split-half ceiling); ERA5 convergence > 0). "
        f"Ry = {res['planning_ry']:.2f} (min(0.5, detection cap); caps at σ_c = 0: "
        + ", ".join(f"{k} {v:.3f}" for k, v in res["ry_cap"].items()) + ").",
        f"- **MDE80 = {p['mde80']:.3f}** (Monte Carlo 95% CI {p['ci_lo']:.3f}–{p['ci_hi']:.3f}) → **{p['band']}** "
        f"(GO ≤ {GO_MDE}; team decision ≤ {NOGO_MDE}; worse band if the CI straddles a cut-off).",
        "",
        _md_table(plan_rows),
        "",
        f"- Highest reachable true within-county ρ under the hurdle model (target 0.60): "
        f"{plan_rows['rho_achieved'].max():.3f}. MDE80 is interpolated on the achieved ρ; if power never "
        "reaches 0.80 it is reported as ∞ (above the reachable range).",
        "",
        "`mean_r_obs` is the average estimated within-county r on observed data (attenuated by √(Rx·Ry) and "
        "zeros); `county_mae`/`season_mae` are the absolute errors of the matched recorded-non-zero shares.",
        "",
        "## MDE80 across the Rx × Ry grid (primary frame)",
        "",
        _md_table(tab.reset_index().rename(columns={"rx": "Rx \\ Ry"})),
        "",
        "- Achieved Ry by target: " + ", ".join(f"{k:.2f} → {v:.3f}" for k, v in ry_ach.items()) + ". Detection "
        "(π = OCHA rate, 300-person threshold) caps outcome reliability, so every Ry target above the cap runs "
        "at the cap: the Ry columns are not distinct designs. Pre-registered: 'if π alone caps Ry below the "
        "target, report that cap as a finding'.",
        "- '—' = power never reaches 0.80 within the reachable ρ range (MDE80 > max achieved ρ).",
        "- OFAT rows with fpr_rho0 well above 0.05 (ψ at the CI upper bound, all-nuisance) have power inflated by "
        "circularity bias; their MDE80 does not measure detectability.",
        "",
        "## One factor at a time (planning cell, 500 replications per ρ)",
        "",
        _md_table(mde[mde.variant != "grid"][["variant", "frame", "rx", "ry", "mde80", "ci_lo", "ci_hi", "band",
                                              "fpr_rho0"]]),
        "",
        "## Inference calibration (ρ = 0 with τ = 0.2, AR = 0.3, φ = −0.2, county heterogeneity)",
        "",
        f"- Two-sided 5% false-positive rates: CR2 **{res['fpr_null']['CR2']:.3f}**, wild bootstrap (Webb, B = 399) "
        f"**{res['fpr_null']['wild_webb']:.3f}**, tile randomization (199 swaps; {res['fpr_null']['n_rep_randomization']} "
        f"replications) **{res['fpr_null']['tile_randomization']:.3f}**; {res['fpr_null']['n_rep']} replications, "
        f"MC SE ≈ {res['fpr_null']['mcse']:.3f}.",
        f"- Switch to bootstrap (CR2 outside band while bootstrap inside)? **{res['switch_to_bootstrap']}**.",
        "",
        "## Controls",
        "",
        f"- Positive control: between-county Spearman of county-mean severity vs county-mean ET flood "
        f"displacement = **{res['positive_control']:.3f}** (county means in `stage34_positive_control_county_means.csv`).",
        f"- Circularity control: within-county r of severity with log1p ET non-flood records = **{ci['r']:.3f}** "
        f"(95% CI {ci['r_ci_lo']:.3f} to {ci['r_ci_hi']:.3f}; n = {ci['n']}, {ci['n_clusters']} counties). "
        f"Mapped to ψ = {res['psi']['psi']:.3f} (logit detection shift per SD of observed severity); simulated FPR at "
        f"ψ̂ = **{res['psi_fpr']:.3f}**, at the CI upper bound (ψ = {res['psi_ci_hi']['psi']:.3f}) {res['psi_ci_hi_fpr']:.3f}. "
        f"Calibration fit: within-SD {res['psi']['within_sd_achieved']:.3f} vs target {res['psi']['within_sd_target']:.3f}; "
        f"r {res['psi']['r_achieved']:.3f} vs target {res['psi']['r_target']:.3f}.",
        "",
        "## Validation-gap register (`stage34_gap_register.csv`)",
        "",
        _md_table(gaps),
        "",
        "## Simulation assumptions not fixed by the pre-registration (declared here)",
        "",
        f"- κ = {KAPPA}: share of the within-county log-size SD driven by the latent index.",
        f"- County error SDs log-normal (log-SD {COUNTY_SD_LOGSD}); county detection heterogeneity N(0, {DETECT_HET_SD}²) "
        "on the logit scale, rank-matched to each county's recorded share (always-recorded counties get the "
        "highest detection); mean detection = OCHA-based rate.",
        "- φ enters as an effective reliability: the error keeps its φ = 0 variance but correlates −0.2 with truth.",
        "- ψ: non-flood records ~ Poisson(λ_i · exp(ψ x~ + η)), η matched to the observed within-county SD of "
        "log1p records; the same ψ shifts detection of flood displacement on the logit scale.",
        "- Target recorded-non-zero shares are clipped to [0.03, 0.97].",
        "",
        "```powershell",
        "python -m archive.impact_eda.impact_session_e --only 34",
        "```",
    ]
    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE34_GATE.md").write_text("\n".join(text), encoding="utf-8")


# ---------------------------------------------------------------- Stage 35: scorecard and decision


def run_stage35() -> dict:
    """Scorecard from the gate summaries. Never unblinds: flipping UNBLINDED needs GO (or an accepted
    team decision) recorded here AND the frozen spec hash emailed to the supervisor by the user."""
    s31 = json.loads((OUT / "stage31_summary.json").read_text())
    s32 = json.loads((OUT / "stage32_summary.json").read_text())
    s33 = json.loads((OUT / "stage33_reliability.json").read_text())
    s34 = json.loads((OUT / "stage34_summary.json").read_text())
    p = s34["planning_mde80"]
    rows = [
        ("31", "Estimator, blinding and join tests", "all pass", s31["all_pass"]),
        ("32", "Usable seasons >= 3", str(s32["usable_seasons"]), len(s32["usable_seasons"]) >= 3),
        ("32", f"Varying F71 counties >= {MIN_VARYING}", str(s32["n_varying_usable"]), s32["n_varying_usable"] >= MIN_VARYING),
        ("32", f"Detection rate (OCHA) >= {MIN_DETECTION}", f"{s32['detection_ocha']['rate']:.3f}",
         s32["detection_ocha"]["rate"] >= MIN_DETECTION),
        ("33", f"Split-half ceiling >= {MIN_SPLIT_HALF}", f"{s33['split_half_ceiling']:.3f}", s33["pass"]),
        ("34", f"MDE80 <= {NOGO_MDE} (planning cell, worse band if CI straddles)",
         f"{p['mde80']:.3f} [{p['ci_lo']:.3f}, {p['ci_hi']:.3f}]", max(p["mde80"], p["ci_hi"]) <= NOGO_MDE),
        ("34", "An inference method with FPR in [0.035, 0.065]",
         ", ".join(f"{k} {s34['fpr_null'][k]:.3f}" for k in s34["in_band"]), any(s34["in_band"].values())),
        ("34", f"Positive control >= {MIN_POSITIVE_CONTROL}", f"{s34['positive_control']:.3f}",
         s34["positive_control"] >= MIN_POSITIVE_CONTROL),
        ("34", f"FPR at psi-hat <= {MAX_PSI_FPR}", f"{s34['psi_fpr']:.3f}", s34["psi_fpr"] <= MAX_PSI_FPR),
    ]
    card = pd.DataFrame(rows, columns=["stage", "criterion", "value", "pass"])
    kills_pass = bool(card["pass"].all())
    b = s34["planning_band"]
    decision = b if kills_pass else "NO-GO"
    card.loc[len(card)] = ["35", "Decision (GO: MDE80 <= 0.35 and all kills pass)", decision, decision == "GO"]
    card.to_csv(OUT / "stage35_scorecard.csv", index=False)
    res = {"decision": decision, "planning_band": b, "all_kill_criteria_pass": kills_pass, "spec_sha256": spec_hash(),
           "unblinded": UNBLINDED}
    text = [
        "# Stage 35 gate — scorecard and decision",
        "",
        f"**Decision: {decision}.**",
        "",
        _md_table(card.assign(**{"pass": card["pass"].map({True: "pass", False: "**FAIL**"})})),
        "",
        f"- Frozen spec SHA-256: `{res['spec_sha256']}`.",
        f"- `UNBLINDED` = {UNBLINDED}. The within-county severity–outcome association has **not** been computed.",
        "- GO or an accepted team decision still requires the user to email the spec hash to the supervisor "
        "before `UNBLINDED` is set and SE-H4 is run once.",
        "- NO-GO → pivot to the measurement-validity RO (detection rates, reliability ceilings/floors, MDE curves).",
        "",
        "```powershell",
        "python -m archive.impact_eda.impact_session_e --through 35",
        "```",
    ]
    (ROOT / "archive" / "impact_eda" / "gates" / "STAGE35_GATE.md").write_text("\n".join(text), encoding="utf-8")
    return res


# ---------------------------------------------------------------- main


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Session E stages 31–35")
    parser.add_argument("--through", type=int, default=35, choices=range(31, 36))
    parser.add_argument("--only", type=int, choices=range(31, 36), help="run a single stage")
    parser.add_argument("--quick", action="store_true", help="Stage 34 with 10%% replications (debug only)")
    parser.add_argument("--continue-after-fail", action="store_true",
                        help="keep running after a failed gate (default: stop, as a kill criterion ends the RO)")
    args = parser.parse_args()
    stages = [args.only] if args.only else list(range(31, args.through + 1))
    runners = {31: run_stage31, 32: run_stage32, 33: run_stage33, 34: lambda: run_stage34(quick=args.quick),
               35: run_stage35}
    results: dict[str, object] = {}
    for s in stages:
        results[f"stage{s}"] = runners[s]()
        print(json.dumps({f"stage{s}": results[f"stage{s}"]}, indent=2, default=str))
        r = results[f"stage{s}"]
        failed = isinstance(r, dict) and (r.get("pass") is False or r.get("all_pass") is False)
        if failed and not args.continue_after_fail and s < 35:
            print(f"Stage {s} gate failed: stopping (see STAGE{s}_GATE.md).")
            break
    summary = OUT / "session_e_summary.json"
    old = json.loads(summary.read_text()) if summary.exists() else {}
    old.update(results)
    summary.write_text(json.dumps(old, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
