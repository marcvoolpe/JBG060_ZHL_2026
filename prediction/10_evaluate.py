"""
Step 10 - collect every result into the tables and figures for the report.

Reads what steps 6, 8 and 9 wrote to raw_data/prediction/ and produces, in deliverables/:

  tables/stage1_skill.csv      Stage 1 (flood volume): every model, lead, fold
  tables/stage2_skill.csv      Stage 2 (per pixel): ConvLSTM runs + baselines
  tables/skill_summary.csv   the headline: skill vs the better baseline, per lead
  tables/stage1_shap.csv       which drivers matter, by family and lag
  figures/stage1_skill_by_lead.png   Stage 1 skill vs lead
  figures/stage2_skill_by_lead.png   Stage 2 F1 and PR-AUC vs lead
  figures/stage1_shap.png      driver importance by lead

"Skill vs the better baseline" is the number to quote. For each fold we take
whichever of persistence and climatology did better, and ask how much the
model improves on it: 1 = perfect, 0 = no better than the best free
forecast, negative = worse. Beating only the weaker baseline is not skill -
climatology is easy to beat at short leads, persistence at long ones.

Run: python prediction/10_evaluate.py
"""

import json
import sys
from importlib import import_module
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

stage1 = import_module("06_stage1_volume")

# Validated categorical palette (dataviz reference instance, slots 1-4, fixed
# order). Baselines are reference lines in neutral grey, not series colours.
COLOURS = {"elasticnet": "#2a78d6", "gbt": "#eb6834", "transformer": "#1baf7a", "convlstm": "#2a78d6",
           "convlstm_no-stage1": "#eb6834", "convlstm_no-era5": "#1baf7a"}
MARKERS = {"elasticnet": "o", "gbt": "s", "transformer": "^", "convlstm": "o",
           "convlstm_no-stage1": "s", "convlstm_no-era5": "^"}
GREY, INK, MUTED, SURFACE = "#52514e", "#0b0b0b", "#8a8984", "#fcfcfb"
BASELINE_STYLE = {"persistence": "--", "climatology": ":"}
BASELINES = ("persistence", "climatology", "seasonal_persistence")
LABELS = {"elasticnet": "ElasticNet", "gbt": "Gradient boosting", "transformer": "Transformer (INFLOW-style)",
          "convlstm": "ConvLSTM", "convlstm_no-stage1": "ConvLSTM, no Stage 1 input",
          "convlstm_no-era5": "ConvLSTM, no ERA5 input", "convlstm-calibrated": "ConvLSTM, calibrated",
          "persistence": "Persistence", "climatology": "Climatology"}


def style(ax, title, ylabel, leads=C.LEADS):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    ax.set_xlabel("lead (dekads ahead; 1 dekad = 10 days, 36 = 1 year)", color=GREY, fontsize=9)
    ax.set_ylabel(ylabel, color=GREY, fontsize=9)
    ax.set_xticks(leads)
    ax.set_xlim(0, max(leads) * 1.3)
    ax.tick_params(colors=GREY, labelsize=9)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#c9c8c2")


def end_label(ax, x, y, text, colour):
    ax.annotate(text, (x, y), xytext=(6, 0), textcoords="offset points", va="center",
                fontsize=8, color=INK if colour != GREY else GREY)
    ax.plot([], [])  # keeps matplotlib's colour cycle out of it


# --------------------------------------------------------------------------
# Stage 1
# --------------------------------------------------------------------------

def stage1_tables():
    parts = []
    for f in sorted((C.OUT / "stage1").glob("metrics*.csv")):
        if "_leads" in f.name:
            continue                       # partial runs (e.g. the lead-3 gate) are superseded
        parts.append(pd.read_csv(f))
    if not parts:
        raise SystemExit("no Stage 1 results - run 06_stage1_volume.py first")
    m = pd.concat(parts, ignore_index=True)
    m["target"] = m["target"].fillna("change")
    base = m[m["model"].isin(BASELINES)].drop_duplicates(["lead", "fold", "model"])
    piv = base.pivot_table(index=["lead", "fold"], columns="model", values="mae")
    # Headline bar: the better of persistence and climatology.
    m = m.join(piv[["persistence", "climatology"]].min(axis=1).rename("best_baseline_mae"), on=["lead", "fold"])
    m["skill_vs_best_baseline"] = 1 - m["mae"] / m["best_baseline_mae"]
    # Stricter bar: also seasonal persistence ("today's anomaly persists").
    if "seasonal_persistence" in piv:
        m = m.join(piv.min(axis=1).rename("best_of_three_mae"), on=["lead", "fold"])
        m["skill_vs_best_of_three"] = 1 - m["mae"] / m["best_of_three_mae"]
    m.to_csv(C.TABLES / "stage1_skill.csv", index=False)
    return m


def stage1_summary(m):
    models = m[~m["model"].isin(BASELINES)]
    g = models.groupby(["target", "model", "lead"])
    summary = pd.DataFrame({
        "folds_beating_best_baseline": g.apply(lambda d: f"{int((d['mae'] < d['best_baseline_mae']).sum())}/{len(d)}",
                                               include_groups=False),
        "median_skill_vs_best_baseline": g["skill_vs_best_baseline"].median(),
        # Pooled over folds: total error / total baseline error. Dominated by
        # the crisis years, when flood volumes are 10x larger.
        "pooled_skill_vs_best_baseline": g.apply(lambda d: 1 - d["mae"].sum() / d["best_baseline_mae"].sum(),
                                                 include_groups=False),
        "fold6_skill_2020_21_crisis": g.apply(lambda d: d.loc[d["fold"] == 6, "skill_vs_best_baseline"].mean(),
                                              include_groups=False),
    }).reset_index()
    summary.insert(0, "stage", "stage1_volume")
    return summary


def stage1_figure(m):
    targets = [t for t in ("change", "anomaly", "level") if (m["target"] == t).any()]
    fig, axes = plt.subplots(1, len(targets), figsize=(5.5 * len(targets), 4.2), facecolor=SURFACE, sharey=True)
    for ax, target in zip(np.atleast_1d(axes), targets):
        d = m[(m["target"] == target) & ~m["model"].isin(BASELINES)]
        if d.empty:
            ax.set_visible(False)
            continue
        ax.axhline(0, color=GREY, linewidth=1.2, linestyle="--")
        ax.annotate("best free forecast", (C.LEADS[0], 0), xytext=(0, 5), textcoords="offset points",
                    fontsize=8, color=GREY)
        for model, g in d.groupby("model"):
            med = g.groupby("lead")["skill_vs_best_baseline"].median()
            lo = g.groupby("lead")["skill_vs_best_baseline"].quantile(0.25)
            hi = g.groupby("lead")["skill_vs_best_baseline"].quantile(0.75)
            ax.fill_between(med.index, lo, hi, color=COLOURS[model], alpha=0.12, linewidth=0)
            ax.plot(med.index, med, color=COLOURS[model], linewidth=2, marker=MARKERS[model], markersize=7,
                    markeredgecolor=SURFACE, markeredgewidth=1.5)
            end_label(ax, med.index[-1], med.iloc[-1], LABELS[model], COLOURS[model])
        what = {"change": "predicts the change in volume", "anomaly": "predicts the change in anomaly",
                "level": "predicts the volume directly"}[target]
        style(ax, f"Stage 1 {what}", "skill vs better of persistence / climatology", sorted(set(d["lead"])))
    fig.suptitle("Stage 1: median over 8 rolling-origin folds (band = middle 50% of folds)",
                 x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(C.FIGURES / "stage1_skill_by_lead.png", dpi=160, facecolor=SURFACE)
    plt.close(fig)


def family(source):
    if source.startswith("season"):
        return "season"
    if source == "log_volume":
        return "current flood extent"
    if source.split("_")[0] in stage1.LAKES:
        return "lake levels"
    if source == "dmi":
        return "Indian Ocean Dipole"
    return "ERA5 rain & runoff"


def stage1_shap():
    f = C.OUT / "stage1" / "shap_by_feature.csv"
    if not f.exists():
        return None
    sh = pd.read_csv(f)
    src = [stage1.feature_source(x) for x in sh["feature"]]
    sh["source"] = [s for s, _ in src]
    sh["lag"] = [lag for _, lag in src]
    sh["family"] = sh["source"].map(family)
    # SHAP values add up, so a family's importance is the SUM over its features.
    fam = (sh.groupby(["lead", "fold", "family"])["mean_abs_shap"].sum()
           .groupby(["lead", "family"]).mean().rename("mean_abs_shap").reset_index())
    fam["share"] = fam["mean_abs_shap"] / fam.groupby("lead")["mean_abs_shap"].transform("sum")
    lakes = sh[sh["family"] == "lake levels"].copy()
    lakes["lag_band"] = pd.cut(lakes["lag"].astype(int), [-1, 3, 12, 27, 54],
                               labels=["0-1 month", "2-4 months", "6-9 months", "10-18 months"])
    band = (lakes.groupby(["lead", "fold", "lag_band"], observed=True)["mean_abs_shap"].sum()
            .groupby(["lead", "lag_band"], observed=True).mean().rename("mean_abs_shap").reset_index())
    band["family"] = "lake levels, by lag"
    out = pd.concat([fam.assign(kind="family"), band.rename(columns={"lag_band": "detail"}).assign(kind="lake_lag")])
    out.to_csv(C.TABLES / "stage1_shap.csv", index=False)

    order = ["lake levels", "ERA5 rain & runoff", "current flood extent", "season", "Indian Ocean Dipole"]
    colours = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
    share = fam.pivot(index="lead", columns="family", values="share").reindex(columns=order).fillna(0)
    fig, ax = plt.subplots(figsize=(8, 3.8), facecolor=SURFACE)
    left = np.zeros(len(share))
    y = np.arange(len(share))
    for fam_name, colour in zip(order, colours):
        vals = share[fam_name].to_numpy()
        ax.barh(y, vals, left=left, color=colour, height=0.6, edgecolor=SURFACE, linewidth=2, label=fam_name)
        for yi, (l, v) in enumerate(zip(left, vals)):
            if v > 0.07:
                ax.text(l + v / 2, yi, f"{v:.0%}", ha="center", va="center", fontsize=8, color=INK)
        left += vals
    ax.set_yticks(y, [f"lead {lead}" for lead in share.index])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=GREY, labelsize=9)
    ax.set_title("What Stage 1 relies on: share of total |SHAP| by driver family (gradient boosting)",
                 loc="left", fontsize=10, color=INK)
    ax.legend(ncol=5, fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    fig.savefig(C.FIGURES / "stage1_shap.png", dpi=160, facecolor=SURFACE)
    plt.close(fig)
    return out


# --------------------------------------------------------------------------
# Stage 2
# --------------------------------------------------------------------------

def stage2_tables():
    d = C.OUT / "stage2"
    runs = [pd.read_csv(f) for f in sorted(d.glob("metrics_convlstm*.csv"))]
    base = d / "metrics_baselines.csv"
    if not base.exists():
        return None
    b = pd.read_csv(base)
    m = pd.concat(runs + [b], ignore_index=True) if runs else b
    m.to_csv(C.TABLES / "stage2_skill.csv", index=False)
    return m


def stage2_summary(m):
    a = m[m["group"] == "all"]
    rows = []
    for (model, lead), g in a[a["model"].str.startswith("convlstm")].groupby(["model", "lead"]):
        wins_f1, wins_auc, sk = 0, 0, []
        for fold in g["fold"]:
            here = a[(a["lead"] == lead) & (a["fold"] == fold)].set_index("model")
            best_f1 = here.loc[["persistence", "climatology"], "f1"].max()
            best_auc = here.loc[["persistence", "climatology"], "pr_auc"].max()
            wins_f1 += here.loc[model, "f1"] > best_f1
            wins_auc += here.loc[model, "pr_auc"] > best_auc
            sk.append(here.loc[model, "f1"] - best_f1)
        rows.append({"stage": "stage2_pixel", "target": "binary", "model": model, "lead": lead,
                     "folds_beating_best_baseline": f"{wins_f1}/{len(g)} (F1), {wins_auc}/{len(g)} (PR-AUC)",
                     "median_f1_gain_vs_best_baseline": float(np.median(sk))})
    return pd.DataFrame(rows)


def stage2_figure(m):
    a = m[m["group"] == "all"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), facecolor=SURFACE)
    # calibration (step 11) keeps the order of pixels, so F1 and PR-AUC match the
    # raw ConvLSTM; it is shown in the Brier table and reliability figure instead
    runs = sorted(set(a["model"]) - {"persistence", "climatology", "convlstm-calibrated"})
    for ax, metric, name in zip(axes, ("f1", "pr_auc"), ("F1 (at the threshold tuned on validation)", "PR-AUC")):
        folds = sorted(set(a.loc[a["model"].isin(runs), "fold"])) or sorted(set(a["fold"]))
        sub = a[a["fold"].isin(folds)]
        for base, ls in BASELINE_STYLE.items():
            s = sub[sub["model"] == base].groupby("lead")[metric].median()
            ax.plot(s.index, s, color=GREY, linewidth=1.5, linestyle=ls)
            end_label(ax, s.index[-1], s.iloc[-1], LABELS[base], GREY)
        for model in runs:
            s = sub[sub["model"] == model].groupby("lead")[metric].median()
            ax.plot(s.index, s, color=COLOURS.get(model, INK), linewidth=2, marker=MARKERS.get(model, "o"),
                    markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5)
            end_label(ax, s.index[-1], s.iloc[-1], LABELS.get(model, model), COLOURS.get(model, INK))
        style(ax, name, f"median over folds {', '.join(map(str, folds))}")
        ax.set_ylim(bottom=0)
    fig.suptitle("Stage 2: will this pixel be flooded? All flood-domain pixels, patch borders excluded",
                 x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(C.FIGURES / "stage2_skill_by_lead.png", dpi=160, facecolor=SURFACE)
    plt.close(fig)


def stage2_calibration(m):
    """Brier score (quality of the probabilities) before and after step 11,
    against both free forecasts, per lead and fold. Lower is better."""
    a = m[m["group"] == "all"]
    cal = a[a["model"] == "convlstm-calibrated"]
    rows = []
    for _, r in cal.iterrows():
        here = a[(a["lead"] == r["lead"]) & (a["fold"] == r["fold"])].set_index("model")["brier"]
        best = here[["persistence", "climatology"]].min()
        rows.append({"lead": r["lead"], "fold": r["fold"], "test_years": r["test_years"],
                     "brier_raw": here["convlstm"], "brier_calibrated": here["convlstm-calibrated"],
                     "brier_persistence": here["persistence"], "brier_climatology": here["climatology"],
                     # Brier skill score: 1 - Brier / Brier of the better free forecast; > 0 means better
                     "bss_vs_best_baseline": 1 - here["convlstm-calibrated"] / best})
    t = pd.DataFrame(rows)
    t.to_csv(C.TABLES / "stage2_calibration.csv", index=False)
    return t


def reliability_figure():
    """Reliability diagram: when the model says p, how often does the pixel flood?
    Built from the probability histograms step 11 stores (all folds pooled per lead)."""
    files = sorted((C.OUT / "stage2").glob("calib_L*_f*.json"))
    if not files:
        return
    logs = [json.loads(f.read_text()) for f in files]
    leads = sorted({int(f.stem.split("_")[1][1:]) for f in files})
    fig, axes = plt.subplots(1, len(leads), figsize=(5.2 * len(leads), 4.4), facecolor=SURFACE, squeeze=False)
    edges = np.linspace(0, 1, 11)
    for ax, lead in zip(axes[0], leads):
        mine = [g for g, f in zip(logs, files) if f.stem.startswith(f"calib_L{lead}_")]
        n_bins = mine[0]["bins"]
        centre = (np.arange(n_bins) + 0.5) / n_bins
        ax.plot([0, 1], [0, 1], color=GREY, linewidth=1, linestyle=":")
        for kind, colour, name in (("raw", "#eb6834", "ConvLSTM, raw"), ("cal", "#2a78d6", "ConvLSTM, calibrated")):
            pos = np.sum([g[f"{kind}_pos"] for g in mine], axis=0)
            neg = np.sum([g[f"{kind}_neg"] for g in mine], axis=0)
            idx = np.digitize(centre, edges[1:-1])          # merge the 200 fine bins into 10
            p_sum = np.bincount(idx, (pos + neg) * centre, 10)
            n = np.bincount(idx, pos + neg, 10)
            hit = np.bincount(idx, pos, 10)
            ok = n > 1000                                   # skip nearly empty bins
            ax.plot(p_sum[ok] / n[ok], hit[ok] / n[ok], color=colour, linewidth=2, marker="o",
                    markersize=6, markeredgecolor=SURFACE, label=name)
        ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="forecast probability", ylabel="observed share flooded")
        ax.set_title(f"lead {lead} dekads (~{lead * 10} days), folds pooled", loc="left", fontsize=11, color=INK)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.suptitle("Stage 2 reliability: on the diagonal, \"60%\" means flooded 60% of the time",
                 x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(C.FIGURES / "stage2_reliability.png", dpi=160, facecolor=SURFACE)
    plt.close(fig)


# --------------------------------------------------------------------------

def main() -> None:
    C.ensure_dirs(C.TABLES, C.FIGURES)
    pd.set_option("display.width", 180)

    m1 = stage1_tables()
    summaries = [stage1_summary(m1)]
    stage1_figure(m1)
    shap = stage1_shap()

    m2 = stage2_tables()
    if m2 is not None:
        stage2_figure(m2)
        if (m2["model"].str.startswith("convlstm")).any():
            summaries.append(stage2_summary(m2))
        if (m2["model"] == "convlstm-calibrated").any():
            cal = stage2_calibration(m2)
            reliability_figure()

    summary = pd.concat(summaries, ignore_index=True)
    summary.to_csv(C.TABLES / "skill_summary.csv", index=False)
    print("=== headline: does the model beat the BETTER free forecast? ===")
    print(summary.round(3).to_string(index=False))
    if shap is not None:
        print("\n=== Stage 1 driver families, share of |SHAP| ===")
        fam = shap[shap["kind"] == "family"].pivot(index="lead", columns="family", values="share")
        print((100 * fam).round(1).to_string())
    if m2 is not None:
        print("\n=== Stage 2 binary F1 by lead, all pixels, median over folds ===")
        a = m2[m2["group"] == "all"]
        print(a.pivot_table(index="lead", columns="model", values="f1", aggfunc="median").round(3).to_string())
    if m2 is not None and (m2["model"] == "convlstm-calibrated").any():
        print("\n=== Stage 2 Brier score (lower is better), raw vs calibrated vs free forecasts ===")
        print(cal.round(4).to_string(index=False))
    print("\nwrote tables to", C.TABLES.relative_to(C.REPO), "and figures to", C.FIGURES.relative_to(C.REPO))


if __name__ == "__main__":
    main()
