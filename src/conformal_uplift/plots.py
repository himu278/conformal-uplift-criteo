"""Static figures for the README and reports (matplotlib, PNG).

Palette: validated categorical order (blue, orange, aqua, yellow, magenta). Three slots
sit below 3:1 contrast on the light surface, so every figure carries a legend or direct
labels and every number is also in a table in reports/results.md.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
NEUTRAL = "#8a8985"
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT2 = "#52514e"
GRID = "#e6e5e0"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": TEXT2, "xtick.color": TEXT2, "ytick.color": TEXT2,
    "text.color": TEXT, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
    "axes.titlesize": 11, "axes.titleweight": "bold", "legend.frameon": False,
})

SET_ORDER = ["{0}", "{0,1}", "{-1,0}", "{-1,0,1}", "{}"]
SET_LABEL = {"{0}": "{0}", "{0,1}": "{0, 1}", "{-1,0}": "{-1, 0}",
             "{-1,0,1}": "{-1, 0, 1}: anything", "{}": "empty (abstain)"}


def _save(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def set_type_bars(shares: pd.DataFrame, xcol: str, path: Path, title: str, xlabel: str):
    """Stacked horizontal bars: share of ITE sets of each type, one bar per row of `shares`."""
    fig, ax = plt.subplots(figsize=(8, 0.6 * len(shares) + 1.6))
    left = np.zeros(len(shares))
    ylabels = [str(v) for v in shares[xcol]]
    for i, s in enumerate(SET_ORDER):
        col = f"set_{s}"
        vals = shares[col].to_numpy() if col in shares else np.zeros(len(shares))
        ax.barh(ylabels, vals, left=left, color=SERIES[i], edgecolor=SURFACE, linewidth=2,
                height=0.6, label=SET_LABEL[s])
        for y, (l, v) in enumerate(zip(left, vals)):
            if v > 0.08:
                ax.text(l + v / 2, y, f"{v:.0%}", ha="center", va="center", color=TEXT, fontsize=9)
        left += vals
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlabel("Share of customers")
    ax.set_ylabel(xlabel)
    ax.set_title(title, loc="left")
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.32), fontsize=9)
    _save(fig, path)


def coverage_lines(summary: pd.DataFrame, path: Path, alpha: float, title: str):
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, (c, g) in enumerate(summary.groupby("coupling")):
        g = g.sort_values("base_rate")
        ax.errorbar(g["base_rate"], g["cov_ite"], yerr=1.96 * g["cov_ite_se"], marker="o",
                    markersize=6, lw=2, capsize=3, color=SERIES[i], label=c)
    ax.axhline(1 - alpha, color=NEUTRAL, lw=1.2, ls="--")
    ax.annotate(f"target {1 - alpha:.0%}", xy=(1.0, 1 - alpha), xycoords=("axes fraction", "data"),
                xytext=(-4, 4), textcoords="offset points", ha="right", va="bottom",
                color=TEXT2, fontsize=9)
    ax.set_xscale("log")
    ax.set_xlabel("Base rate of the outcome (log scale)")
    ax.set_ylabel("Coverage of the true ITE")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_title(title, loc="left")
    ax.legend(title="Coupling of Y(0), Y(1)")
    _save(fig, path)


def uplift_curve_plot(res: dict, path: Path, title: str, ylabel: str):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    g = res["grid"]
    if "curve_lo" in res:
        ax.fill_between(g, res["curve_lo"], res["curve_hi"], color=SERIES[0], alpha=0.18, lw=0,
                        label="95% bootstrap band")
    ax.plot(g, res["curve"], color=SERIES[0], lw=2, label="Rank by predicted uplift")
    ax.plot(g, g * res["ate"], color=NEUTRAL, lw=1.5, ls="--", label="Random targeting")
    ax.set_xlabel("Share of customers treated (highest predicted uplift first)")
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_title(title, loc="left")
    ax.legend(loc="upper left")
    _save(fig, path)


def calibration_plot(cal: pd.DataFrame, path: Path, title: str, unit: float = 100.0, ylab="pp"):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = cal["bin"].to_numpy()
    ax.errorbar(x, unit * cal["observed_uplift"],
                yerr=[unit * (cal["observed_uplift"] - cal["ci_low"]),
                      unit * (cal["ci_high"] - cal["observed_uplift"])],
                fmt="o", color=SERIES[0], markersize=6, capsize=3, lw=1.5,
                label="Observed (difference in means, 95% CI)")
    ax.plot(x, unit * cal["predicted_uplift"], color=SERIES[1], marker="s", markersize=6, lw=2,
            label="Predicted (model average)")
    ax.axhline(0, color=NEUTRAL, lw=1)
    ax.set_xticks(x)
    ax.set_xlabel("Decile of predicted uplift (1 = lowest)")
    ax.set_ylabel(f"Uplift ({ylab})")
    ax.set_title(title, loc="left")
    ax.legend(loc="upper left")
    _save(fig, path)


def holdout_plot(tab: pd.DataFrame, path: Path, title: str):
    fig, ax = plt.subplots(figsize=(7, 4))
    x = 100 * tab["control_share"].to_numpy()
    ax.plot(x, tab["auuc_ci_width"], marker="o", markersize=7, lw=2, color=SERIES[0])
    for xi, yi, n in zip(x, tab["auuc_ci_width"], tab["n_control"]):
        ax.annotate(f"{n:,} controls", (xi, yi), textcoords="offset points", xytext=(6, 6),
                    fontsize=9, color=TEXT2)
    ax.set_xlabel("Control (holdout) share of the evaluation set, %")
    ax.set_ylabel("Width of 95% CI for AUUC gain")
    ax.set_title(title, loc="left")
    ax.invert_xaxis()
    _save(fig, path)
