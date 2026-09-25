"""
Step 6 - Stage 1: how much of the corridor will be flooded, L dekads ahead.

Target: number of flood-domain pixels flooded in dekad t + L, forecast at
issue time t from data up to t. Same role as the temporal model in INFLOW-AI
v2.1, which forecasts total inundated area. Stage 2 (08_train_stage2.py)
then forecasts where.

Forecasts compared on the same test dekads:
  persistence           volume at t
  climatology           mean volume for that dekad of the year (training years)
  seasonal_persistence  today's departure from normal carries on, the season
                        does the rest; at 36 dekads = "same as a year ago"
  elasticnet            regularised linear regression (the FEWS NET approach)
  gbt                   gradient-boosted trees; explained with SHAP
  transformer           (--transformer) INFLOW-AI v2.1's temporal architecture:
                        one attention block, 8 heads, 36-dekad window, trained
                        from scratch. With ~700 training dekads it is expected
                        to overfit; a large win would point to a leak.

Features (built per fold in build_features, all lagged, never forward):
  lakes    Victoria / Kyoga / Albert: anomaly vs usual level for the dekad of
           year, and change since the previous dekad; lags up to 54 dekads
           (18 months), since Victoria water needs ~9-17 months to reach the Sudd
  DMI      Indian Ocean Dipole index
  ERA5     rain / runoff anomaly per region, plus 6- and 18-dekad rain totals
  volume   log of the current flooded area and its recent history
  season   sine / cosine of the dekad of the year
Seasonal means and scalings come from the fold's training years only.

What the models learn (--target):
  change   log volume at t+L minus log volume now (default; INFLOW also
           predicts a change). Learning nothing gives persistence.
  anomaly  change minus the usual seasonal change between t and t+L.
           Learning nothing gives seasonal persistence, so any skill shown is
           on top of both season and current state.
  level    log volume at t+L. Trees cannot predict above the highest value
           seen in training, so this fails in the 2022-23 floods, which were
           2-3x larger than anything before.
All three are saved, so they can be compared.

Stage 2 uses Stage 1 as an input. Those values come from walk-forward runs:
each one is predicted by a model trained only on earlier years.

Outputs (raw_data/prediction/stage1/, suffix _target-<name> for anomaly and level):
  metrics.csv          model x lead x fold scores
  predictions.csv      every test forecast
  walkforward.csv      out-of-sample predictions used by Stage 2
  shap_by_feature.csv  mean |SHAP| per feature, lead and fold

Run:  python prediction/06_stage1_volume.py              leads 1-36, ~5 min
      python prediction/06_stage1_volume.py --leads 3
      python prediction/06_stage1_volume.py --target anomaly
      python prediction/06_stage1_volume.py --transformer  adds the transformer, ~1 h on CPU
"""

import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

STAGE1_OUT = C.OUT / "stage1"

LAKES = ("victoria", "kyoga", "albert")
LAKE_LAGS = (0, 1, 2, 3, 6, 9, 12, 18, 24, 30, 36, 42, 48, 54)
DMI_LAGS = (0, 3, 6, 12, 18, 24)
ERA5_LAGS = (0, 1, 2, 3, 6, 9, 12, 18)
VOLUME_LAGS = (0, 1, 2, 3, 6, 9, 12, 18)

# ERA5 and the flood record both start in Jan 2000. The longest lag on them
# is 18 dekads, so the first issue time with every feature defined is t = 18.
MIN_ISSUE = 18
TRANSFORMER_WINDOW = 36               # INFLOW-AI v2.1's lookback
MIN_ISSUE_TRANSFORMER = TRANSFORMER_WINDOW - 1

N_DOMAIN = 1_082_347                  # flood-domain pixels: the most that can flood


# --------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------

def seasonal_anomaly(values: pd.Series, doy: pd.Series, cutoff: int) -> pd.Series:
    """Value minus its usual level for that dekad of the year. "Usual" is the
    mean over rows up to `cutoff` only - never later - so test years cannot
    shape their own anomalies."""
    train = values.index <= cutoff
    usual = values[train].groupby(doy[train]).mean()
    return values - doy.map(usual)


def base_series(table: pd.DataFrame, cutoff: int) -> pd.DataFrame:
    """The unlagged, fold-local driver series. Shared by the lagged-feature
    models and the transformer."""
    doy = table["dekad"]
    base = pd.DataFrame(index=table.index)
    for lake in LAKES:
        level = table[f"lake_{lake}"]
        base[f"{lake}_anom"] = seasonal_anomaly(level, doy, cutoff)
        base[f"{lake}_change"] = level.diff()
    base["dmi"] = table["dmi"]
    for col in [c for c in table.columns if c.startswith("era5_")]:
        base[f"{col[5:]}_anom"] = seasonal_anomaly(table[col], doy, cutoff)
    base["log_volume"] = np.log1p(table["volume"])
    return base


def build_features(table: pd.DataFrame, cutoff: int) -> pd.DataFrame:
    """Lagged feature matrix, one row per issue time t. A lag of k dekads
    uses the value from t - k, so nothing here looks forward in time."""
    base = base_series(table, cutoff)
    cols = {}
    for lake in LAKES:
        for kind in ("anom", "change"):
            for k in LAKE_LAGS:
                cols[f"{lake}_{kind}_lag{k}"] = base[f"{lake}_{kind}"].shift(k)
    for k in DMI_LAGS:
        cols[f"dmi_lag{k}"] = base["dmi"].shift(k)
    for col in [c for c in base.columns if c.startswith(("tp_", "ro_"))]:
        for k in ERA5_LAGS:
            cols[f"{col}_lag{k}"] = base[col].shift(k)
        if col.startswith("tp_"):
            # Accumulated rain matters more than any one dekad (INFLOW uses it too).
            cols[f"{col}_sum6"] = base[col].rolling(6).sum()
            cols[f"{col}_sum18"] = base[col].rolling(18).sum()
    for k in VOLUME_LAGS:
        cols[f"log_volume_lag{k}"] = base["log_volume"].shift(k)
    angle = 2 * np.pi * (table["dekad"] - 1) / C.DEKADS_PER_YEAR
    cols["season_sin"] = np.sin(angle)
    cols["season_cos"] = np.cos(angle)
    return pd.DataFrame(cols, index=table.index)


def feature_source(name: str) -> tuple:
    """'victoria_anom_lag24' -> ('victoria_anom', 24); 'tp_sobat_anom_sum6' -> ('tp_sobat_anom', 'sum6')."""
    head, _, tail = name.rpartition("_")
    if tail.startswith("lag"):
        return head, int(tail[3:])
    if tail.startswith("sum"):
        return head, tail
    return name, "-"


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------

def fit_gbt(X: pd.DataFrame, y: np.ndarray) -> HistGradientBoostingRegressor:
    # Small, heavily regularised trees: ~700 rows and ~200 features is a
    # setting where a big model memorises. No early stopping, so a fit is
    # fully deterministic for a given seed.
    model = HistGradientBoostingRegressor(
        max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=20,
        l2_regularization=1.0, random_state=C.SEED)
    return model.fit(X, y)


def fit_elasticnet(X: pd.DataFrame, y: np.ndarray):
    # Linear models cannot take missing values. A missing anomaly (mostly
    # Lake Albert before July 2002) is set to 0, i.e. "normal level".
    # The penalty strength is picked by time-ordered cross-validation inside
    # the training years.
    model = make_pipeline(
        StandardScaler(),
        ElasticNetCV(l1_ratio=(0.1, 0.5, 0.9), cv=TimeSeriesSplit(5), max_iter=20000,
                     alphas=30, random_state=C.SEED))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")      # convergence chatter on tiny alphas
        return model.fit(X.fillna(0.0), y)


def to_volume(log_pred: np.ndarray) -> np.ndarray:
    """Models are fitted on log(1 + volume), because flood volume spans four
    orders of magnitude (tens of pixels in a dry 2000s dekad, ~500,000 in
    2023). Convert back, and keep inside what is physically possible."""
    return np.clip(np.expm1(log_pred), 0, N_DOMAIN)


def seasonal_shift(volume: pd.Series, lead: int, cutoff: int) -> pd.Series:
    """How much the season alone moves the flood between t and t + lead:
    usual log-volume at t + lead minus usual log-volume at t, where "usual"
    is the dekad-of-year mean over training rows up to `cutoff` only.
    Example: issued in July, 3 dekads ahead - the season says floods grow
    from July to August by this much, in a normal year."""
    train = volume.loc[0:cutoff]
    usual = np.log1p(train).groupby(C.doy_index(train.index.to_numpy())).mean()
    t = volume.index.to_numpy()
    return pd.Series(usual.reindex(C.doy_index(t + lead)).to_numpy()
                     - usual.reindex(C.doy_index(t)).to_numpy(), index=volume.index)


def make_target(volume: pd.Series, lead: int, kind: str, shift: pd.Series) -> pd.Series:
    """What the model learns, indexed by issue time t. See --target above."""
    future = np.log1p(volume.shift(-lead))
    if kind == "change":
        return future - np.log1p(volume)
    if kind == "anomaly":
        return future - np.log1p(volume) - shift
    return future


def from_target(pred: np.ndarray, volume_now: np.ndarray, kind: str, shift_now: np.ndarray) -> np.ndarray:
    """Model output -> forecast volume at t + lead."""
    if kind == "change":
        return to_volume(np.log1p(volume_now) + pred)
    if kind == "anomaly":
        return to_volume(np.log1p(volume_now) + shift_now + pred)
    return to_volume(pred)


def fit_transformer(base: pd.DataFrame, s: dict, lead: int, table: pd.DataFrame, kind: str):
    """INFLOW-AI v2.1's temporal model, as read from its saved config.json:
    positional encoding -> MultiHeadAttention(8 heads, key_dim 36) ->
    dropout 0.1 -> residual + LayerNorm -> Dense 128 -> Dense 36 -> residual
    + LayerNorm -> Flatten -> Dense 100 -> Dense 50 -> output.
    Differences, both forced by our setup: INFLOW's input already has 36
    features, ours are first projected to 36; and INFLOW outputs 6 dekads
    at once, we fit one model per lead with one output."""
    import tensorflow as tf
    note = C.set_seed(C.SEED, tf)

    cols = list(base.columns)
    train_rows = s["train"]
    mu = base.loc[train_rows, cols].mean()
    sd = base.loc[train_rows, cols].std().replace(0, 1.0)
    z = ((base[cols] - mu) / sd).fillna(0.0).to_numpy(np.float32)

    target = np.log1p(table["volume"].to_numpy())
    t_of_row = base.index.to_numpy()
    pos = {t: i for i, t in enumerate(t_of_row)}

    def windows(issue):
        idx = np.array([pos[t] for t in issue])
        X = np.stack([z[i - TRANSFORMER_WINDOW + 1:i + 1] for i in idx])
        y = target[idx + lead] - (target[idx] if kind == "change" else 0.0)
        return X, y

    Xtr, ytr = windows(s["train"])
    Xva, yva = windows(s["val"])
    y_mu, y_sd = ytr.mean(), ytr.std() or 1.0

    d = 36
    inp = tf.keras.Input((TRANSFORMER_WINDOW, len(cols)))
    x = tf.keras.layers.Dense(d)(inp)
    position = np.arange(TRANSFORMER_WINDOW)[:, None]
    div = np.exp(np.arange(0, d, 2) * -(np.log(10000.0) / d))
    pe = np.zeros((TRANSFORMER_WINDOW, d), np.float32)
    pe[:, 0::2], pe[:, 1::2] = np.sin(position * div), np.cos(position * div)
    x = x + pe
    attn = tf.keras.layers.MultiHeadAttention(num_heads=8, key_dim=36)(x, x)
    x = tf.keras.layers.LayerNormalization()(x + tf.keras.layers.Dropout(0.1)(attn))
    ff = tf.keras.layers.Dense(d)(tf.keras.layers.Dropout(0.1)(tf.keras.layers.Dense(128, activation="relu")(x)))
    x = tf.keras.layers.LayerNormalization()(x + ff)
    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dropout(0.1)(tf.keras.layers.Dense(100, activation="relu")(x))
    x = tf.keras.layers.Dropout(0.1)(tf.keras.layers.Dense(50, activation="relu")(x))
    out = tf.keras.layers.Dense(1)(x)
    model = tf.keras.Model(inp, out)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse")
    stop = tf.keras.callbacks.EarlyStopping(patience=20, restore_best_weights=True)
    model.fit(Xtr, (ytr - y_mu) / y_sd, validation_data=(Xva, (yva - y_mu) / y_sd),
              epochs=300, batch_size=32, verbose=0, callbacks=[stop], shuffle=True)

    def predict(issue):
        X, _ = windows(issue)
        return model.predict(X, verbose=0).ravel() * y_sd + y_mu
    return predict, note


# --------------------------------------------------------------------------
# One fold
# --------------------------------------------------------------------------

def run_block(table, lead, block, reported, use_transformer, do_shap, kind):
    fold, y0, y1 = block
    s = C.split(y0, y1, lead, min_issue=MIN_ISSUE)
    X = build_features(table, s["last_train_target"])
    volume = table["volume"]
    shift = seasonal_shift(volume, lead, s["last_train_target"])
    target = make_target(volume, lead, kind, shift)

    tr, te = s["train"], s["test"]
    # Drop features with no information in this block's training rows: a
    # column that is empty or constant cannot be learned from. This happens
    # for Lake Albert's long lags in the early blocks (its record starts
    # July 2002, so an 18-month lag has no values until 2004).
    informative = X.loc[tr].nunique(dropna=True) > 1
    X = X.loc[:, informative]
    y_true = volume.loc[te + lead].to_numpy()
    gbt = fit_gbt(X.loc[tr], target.loc[tr].to_numpy())
    now = volume.loc[te].to_numpy()
    shift_now = shift.loc[te].to_numpy()
    preds = {"gbt": from_target(gbt.predict(X.loc[te]), now, kind, shift_now)}
    if not reported:
        return {"walkforward": pd.Series(preds["gbt"], index=te)}

    preds["persistence"] = volume.loc[te].to_numpy()
    train_targets = tr + lead
    usual = volume.loc[train_targets].groupby(C.doy_index(train_targets)).mean()
    preds["climatology"] = usual.reindex(C.doy_index(te + lead)).to_numpy()
    enet = fit_elasticnet(X.loc[tr], target.loc[tr].to_numpy())
    preds["elasticnet"] = from_target(enet.predict(X.loc[te].fillna(0.0)), now, kind, shift_now)
    # Third free forecast, stricter than the other two: "today's anomaly
    # persists, the season does the rest". Standard in seasonal forecasting.
    # At 12 months ahead it equals "same as this time last year".
    preds["seasonal_persistence"] = to_volume(np.log1p(now) + shift_now)

    notes = ""
    if use_transformer and kind != "anomaly":
        s_tf = C.split(y0, y1, lead, min_issue=MIN_ISSUE_TRANSFORMER, val_years=C.VAL_YEARS)
        predict, notes = fit_transformer(base_series(table, s_tf["last_train_target"]), s_tf, lead, table, kind)
        preds["transformer"] = from_target(predict(te), now, kind, shift_now)

    metrics = []
    mae_persist = np.mean(np.abs(preds["persistence"] - y_true))
    mae_clim = np.mean(np.abs(preds["climatology"] - y_true))
    for name, p in preds.items():
        err = p - y_true
        mae = float(np.mean(np.abs(err)))
        metrics.append({
            "model": name, "target": kind, "lead": lead, "fold": fold, "test_years": f"{y0}-{y1}",
            "n_test": len(te), "n_train": len(tr),
            "mae": mae, "rmse": float(np.sqrt(np.mean(err ** 2))),
            "mae_log": float(np.mean(np.abs(np.log1p(p) - np.log1p(y_true)))),
            # 1 = perfect, 0 = no better than the baseline, negative = worse
            "skill_vs_persistence": 1 - mae / mae_persist if mae_persist else np.nan,
            "skill_vs_climatology": 1 - mae / mae_clim if mae_clim else np.nan,
            "note": notes if name == "transformer" else "",
        })

    rows = pd.DataFrame({"lead": lead, "fold": fold, "t_issue": te, "t_target": te + lead,
                         "observed": y_true, **preds})

    shap_rows = None
    if do_shap:
        import shap
        explainer = shap.TreeExplainer(gbt)
        values = explainer.shap_values(X.loc[te])
        shap_rows = pd.DataFrame({"feature": X.columns, "mean_abs_shap": np.abs(values).mean(axis=0),
                                  "lead": lead, "fold": fold})

    return {"metrics": metrics, "predictions": rows, "shap": shap_rows,
            "walkforward": pd.Series(preds["gbt"], index=te)}


# --------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--leads", type=int, nargs="+", default=list(C.STAGE1_LEADS))
    ap.add_argument("--transformer", action="store_true", help="also fit INFLOW's transformer (slower)")
    ap.add_argument("--no-shap", action="store_true")
    ap.add_argument("--target", choices=("change", "level", "anomaly"), default="change")
    args = ap.parse_args()

    C.set_seed()
    C.ensure_dirs(STAGE1_OUT)
    table = pd.read_csv(C.OUT / "driver_table.csv", index_col="t")
    reported_ids = {f[0] for f in C.FOLDS}
    t0 = time.time()

    metrics, predictions, shap_tables, walkforward = [], [], [], []
    for lead in args.leads:
        wf = []
        for block in C.WALKFORWARD_BLOCKS:
            reported = block[0] in reported_ids
            r = run_block(table, lead, block, reported, args.transformer, reported and not args.no_shap, args.target)
            wf.append(r["walkforward"])
            if reported:
                metrics += r["metrics"]
                predictions.append(r["predictions"])
                if r["shap"] is not None:
                    shap_tables.append(r["shap"])
            print(f"lead {lead} block {block[1]}-{block[2]} done ({time.time() - t0:.0f}s)")

        # Walk-forward series for Stage 2: at every issue time, the forecast
        # for t + lead from a model that only saw earlier data. Issue times
        # before the first block have no such model; they get persistence
        # (today's volume), which is also only past data.
        issue = np.arange(0, C.N_DEKADS - lead)
        pred = pd.concat(wf).reindex(issue).to_numpy(copy=True)
        missing = np.isnan(pred)
        pred[missing] = table["volume"].reindex(issue).to_numpy()[missing]
        walkforward.append(pd.DataFrame({
            "lead": lead, "t_issue": issue, "pred_volume": pred,
            "source": np.where(missing, "persistence", "stage1_gbt")}))

    m = pd.DataFrame(metrics)
    tag = ("" if set(args.leads) == set(C.STAGE1_LEADS) else "_leads" + "-".join(map(str, args.leads))) \
        + ("" if args.target == "change" else f"_target-{args.target}")
    m.to_csv(STAGE1_OUT / f"metrics{tag}.csv", index=False)
    pd.concat(predictions).to_csv(STAGE1_OUT / f"predictions{tag}.csv", index=False)
    pd.concat(walkforward).to_csv(STAGE1_OUT / f"walkforward{tag}.csv", index=False)
    if shap_tables:
        pd.concat(shap_tables).to_csv(STAGE1_OUT / f"shap_by_feature{tag}.csv", index=False)

    pd.set_option("display.width", 160)
    print("\n=== Stage 1: mean over the 8 folds (MAE in flooded pixels; skill > 0 beats the baseline) ===")
    summary = m.groupby(["lead", "model"])[["mae", "skill_vs_persistence", "skill_vs_climatology"]].mean()
    print(summary.round(3).to_string())
    print("\n=== skill vs persistence, per fold (fold 6 = trained pre-2020, tested on the 2020-21 crisis) ===")
    print(m.pivot_table(index=["lead", "model"], columns="fold", values="skill_vs_persistence").round(2).to_string())
    if shap_tables:
        sh = pd.concat(shap_tables)
        sh["source"] = [feature_source(f)[0] for f in sh["feature"]]
        # SHAP values add up, so a source's importance is the SUM over its
        # lags. (Averaging would make a lake with 14 lags look 14x less
        # important than the single season feature.)
        top = (sh.groupby(["lead", "fold", "source"])["mean_abs_shap"].sum()
               .groupby(["lead", "source"]).mean().sort_values(ascending=False))
        print("\n=== top 12 driver sources by |SHAP| summed over lags (gbt) ===")
        for lead in args.leads:
            print(f"lead {lead}:", ", ".join(f"{k} {v:.3f}" for k, v in top.loc[lead].head(12).items()))
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
