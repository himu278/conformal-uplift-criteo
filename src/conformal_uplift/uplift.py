"""Point uplift models and ranking evaluation for randomized experiments.

Uplift curve used throughout: rank units by predicted uplift and, for each fraction phi,
estimate the incremental outcome per customer (of the whole evaluated population) from
treating only the top phi:

    V(phi) = phi * ( mean(Y | T = 1, top phi) - mean(Y | T = 0, top phi) ).

Treating a random phi of customers gives phi * ATE, so the area between V and that line
("AUUC gain over random") is 0 for an uninformative ranking. Uncertainty comes from a
Poisson bootstrap over evaluation units, which needs no re-sorting.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

GRID = np.linspace(0.0, 1.0, 51)


def _trapz(y, x):
    y, x = np.asarray(y, float), np.asarray(x, float)
    return float(np.sum((y[1:] + y[:-1]) / 2 * np.diff(x)))


def make_classifier(kind: str = "hgb", seed: int = 0):
    if kind == "hgb":
        return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_leaf_nodes=31,
                                              min_samples_leaf=200, l2_regularization=1.0,
                                              early_stopping=True, validation_fraction=0.1,
                                              random_state=seed)
    if kind == "logistic":
        return LogisticRegression(max_iter=1000)
    raise ValueError(kind)


class _Constant:
    """Fallback when an arm's training outcomes are all 0 (or all 1): predict a smoothed rate."""

    def fit(self, X, y):
        self.p = (np.sum(y) + 0.5) / (len(y) + 1.0)
        return self

    def predict_proba(self, X):
        p = np.full(len(X), self.p)
        return np.column_stack([1 - p, p])


def _fit(model, X, y):
    if np.unique(y).size < 2:
        return _Constant().fit(X, y)
    return model.fit(X, y)


class TLearner:
    """One outcome model per arm; uplift = p1(x) - p0(x)."""

    def __init__(self, kind: str = "hgb", seed: int = 0):
        self.m1, self.m0 = make_classifier(kind, seed), make_classifier(kind, seed + 1)

    def fit(self, X, y, t):
        t = np.asarray(t).astype(bool)
        self.m1 = _fit(self.m1, X[t], y[t])
        self.m0 = _fit(self.m0, X[~t], y[~t])
        return self

    def predict_arms(self, X):
        return self.m1.predict_proba(X)[:, 1], self.m0.predict_proba(X)[:, 1]

    def predict_uplift(self, X):
        p1, p0 = self.predict_arms(X)
        return p1 - p0


def _curve_from_sorted(y, t, w, grid=GRID):
    """Uplift curve V(phi) given outcomes/treatment already sorted by descending score."""
    n_tot = w.sum()
    cw_t, cw_c = np.cumsum(w * t), np.cumsum(w * (1 - t))
    cy_t, cy_c = np.cumsum(w * y * t), np.cumsum(w * y * (1 - t))
    cw = np.cumsum(w)
    idx = np.searchsorted(cw, grid[1:] * n_tot, side="left").clip(0, len(y) - 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        diff = cy_t[idx] / cw_t[idx] - cy_c[idx] / cw_c[idx]
    v = np.concatenate([[0.0], grid[1:] * np.nan_to_num(diff)])
    return v


def uplift_curve(score, y, t, n_boot: int = 0, seed: int = 0, grid=GRID) -> dict:
    """Uplift curve, AUUC gain over random, and Poisson-bootstrap CIs."""
    order = np.argsort(-np.asarray(score), kind="stable")
    y = np.asarray(y, float)[order]
    t = np.asarray(t, float)[order]
    w1 = np.ones_like(y)
    v = _curve_from_sorted(y, t, w1, grid)
    ate = v[-1]
    gain = _trapz(v - grid * ate, grid)
    out = {"grid": grid, "curve": v, "ate": ate, "auuc_gain": gain}
    if n_boot:
        rng = np.random.default_rng(seed)
        gains, curves = np.empty(n_boot), np.empty((n_boot, grid.size))
        for b in range(n_boot):
            w = rng.poisson(1.0, size=y.size).astype(float)
            vb = _curve_from_sorted(y, t, w, grid)
            curves[b] = vb
            gains[b] = _trapz(vb - grid * vb[-1], grid)
        out["auuc_gain_ci"] = tuple(np.percentile(gains, [2.5, 97.5]))
        out["auuc_gain_se"] = float(gains.std(ddof=1))
        out["curve_lo"], out["curve_hi"] = np.percentile(curves, [2.5, 97.5], axis=0)
    return out


def diff_in_means(y, t, alpha: float = 0.05) -> dict:
    y, t = np.asarray(y, float), np.asarray(t).astype(bool)
    y1, y0 = y[t], y[~t]
    d = y1.mean() - y0.mean()
    se = np.sqrt(y1.var(ddof=1) / y1.size + y0.var(ddof=1) / y0.size)
    z = norm.ppf(1 - alpha / 2)
    return {"diff": d, "se": se, "ci_low": d - z * se, "ci_high": d + z * se,
            "n_treated": int(y1.size), "n_control": int(y0.size)}


def decile_calibration(score, y, t, n_bins: int = 10) -> pd.DataFrame:
    """Predicted uplift vs experimental (difference-in-means) uplift by score decile."""
    df = pd.DataFrame({"score": score, "y": y, "t": t})
    df["bin"] = pd.qcut(df["score"].rank(method="first"), n_bins, labels=False)
    rows = []
    for b, g in df.groupby("bin"):
        r = diff_in_means(g["y"], g["t"])
        rows.append({"bin": int(b) + 1, "n": len(g), "predicted_uplift": g["score"].mean(),
                     "observed_uplift": r["diff"], "ci_low": r["ci_low"], "ci_high": r["ci_high"]})
    return pd.DataFrame(rows)


def policy_table(score, y, t, fractions=(0.1, 0.2, 0.3, 0.5, 1.0)) -> pd.DataFrame:
    """Incremental outcomes per 1,000 customers when treating only the top fraction."""
    res = uplift_curve(score, y, t, grid=np.concatenate([[0.0], np.asarray(fractions)]))
    full = res["curve"][-1] if fractions[-1] == 1.0 else np.nan
    rows = []
    for f, v in zip(fractions, res["curve"][1:]):
        rows.append({"share_treated": f, "incremental_per_1000": 1000 * v,
                     "random_targeting_per_1000": 1000 * f * full,
                     "share_of_total_effect": v / full if full else np.nan})
    return pd.DataFrame(rows)
