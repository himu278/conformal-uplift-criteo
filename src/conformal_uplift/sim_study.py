"""Simulation study: when are conformal ITE sets informative for binary outcomes?

For each design cell (base rate x treatment share x experiment size) and replication:
1. simulate a randomized experiment and split it into train / calibration / test;
2. fit a T-learner (logistic regression, correctly specified on the log-odds scale);
3. build split-conformal sets for Y(1) and Y(0) at level alpha/2 each, and the naive ITE set;
4. on the test units, draw both potential outcomes under three couplings that all match
   the same observed data, and record coverage and set types;
5. as a group-level alternative, record whether decile-level difference-in-means CIs
   (ranked by predicted uplift) cover the true decile-average effect and exclude zero.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from .conformal import binary_sets, informativeness, ite_covers, ite_membership, set_type, set_type_shares
from .simulate import COUPLINGS, potential_outcomes, response_surfaces, simulate_experiment
from .uplift import TLearner, diff_in_means

DEFAULT_GRID = {
    "base_rate": [0.003, 0.01, 0.05, 0.20, 0.50],
    "treat_share": [0.50, 0.85, 0.95],
    "n": [20_000, 200_000],
}


def _intercept(base_rate: float, seed: int = 12345) -> float:
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(400_000, 6))
    return response_surfaces(X, base_rate, 0.5, 1.0)[2]


def one_replication(n, base_rate, treat_share, alpha, seed, intercept, n_bins=10) -> list[dict]:
    X, T, mu0, mu1, _ = simulate_experiment(n, base_rate, treat_share, seed=seed, intercept=intercept)
    rng = np.random.default_rng(seed + 10_000)
    y_obs = (rng.uniform(size=n) < np.where(T == 1, mu1, mu0)).astype(int)
    idx = rng.permutation(n)
    tr, ca, te = np.split(idx, [n // 2, 3 * n // 4])

    model = TLearner("logistic").fit(X[tr], y_obs[tr], T[tr])
    p1_ca, p0_ca = model.predict_arms(X[ca])
    p1_te, p0_te = model.predict_arms(X[te])
    t_ca = T[ca] == 1
    h0t, h1t, q1 = binary_sets(p1_ca[t_ca], y_obs[ca][t_ca], p1_te, alpha / 2)
    h0c, h1c, q0 = binary_sets(p0_ca[~t_ca], y_obs[ca][~t_ca], p0_te, alpha / 2)
    m1, z0, p1 = ite_membership(h0t, h1t, h0c, h1c)
    info = informativeness(m1, z0, p1)
    shares = set_type_shares(set_type(m1, z0, p1))

    # group-level alternative on the test units (factual outcomes only)
    score = p1_te - p0_te
    bins = pd.qcut(pd.Series(score).rank(method="first"), n_bins, labels=False).to_numpy()
    true_cate = mu1[te] - mu0[te]
    dec_cover, dec_excl0 = [], []
    for b in range(n_bins):
        g = bins == b
        if T[te][g].min() == T[te][g].max():
            continue
        r = diff_in_means(y_obs[te][g], T[te][g])
        tc = true_cate[g].mean()
        dec_cover.append(r["ci_low"] <= tc <= r["ci_high"])
        dec_excl0.append(r["ci_low"] > 0 or r["ci_high"] < 0)

    rows = []
    for c in COUPLINGS:
        y0, y1 = potential_outcomes(mu0[te], mu1[te], c, np.random.default_rng(seed + 20_000))
        ite = y1.astype(int) - y0.astype(int)
        rows.append({
            "n": n, "base_rate": base_rate, "treat_share": treat_share, "seed": seed, "coupling": c,
            "cov_y1": float(np.mean(np.where(y1 == 1, h1t, h0t))),
            "cov_y0": float(np.mean(np.where(y0 == 1, h1c, h0c))),
            "cov_ite": float(np.mean(ite_covers(m1, z0, p1, ite))),
            "share_true_ite_nonzero": float(np.mean(ite != 0)),
            **info, **{f"set_{k}": v for k, v in shares.items()},
            "decile_ci_coverage": float(np.mean(dec_cover)) if dec_cover else np.nan,
            "decile_ci_excludes_zero": float(np.mean(dec_excl0)) if dec_excl0 else np.nan,
        })
    return rows


def run(grid: dict | None = None, reps: int = 30, alpha: float = 0.10, seed: int = 0,
        verbose: bool = True) -> pd.DataFrame:
    grid = grid or DEFAULT_GRID
    intercepts = {b: _intercept(b) for b in grid["base_rate"]}
    rows = []
    cells = list(itertools.product(grid["base_rate"], grid["treat_share"], grid["n"]))
    for i, (b, e, n) in enumerate(cells):
        if verbose:
            print(f"  cell {i + 1}/{len(cells)}: base rate {b}, treatment share {e}, n {n:,}")
        for r in range(reps):
            rows += one_replication(n, b, e, alpha, seed + 1000 * i + r, intercepts[b])
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    keys = ["n", "base_rate", "treat_share", "coupling"]
    metrics = [c for c in df.columns if c not in keys + ["seed"]]
    g = df.groupby(keys)[metrics]
    out = g.mean()
    se = g.std(ddof=1) / np.sqrt(g.size().to_numpy()[:, None])
    for m in ("cov_ite", "cov_y1", "cov_y0"):
        out[f"{m}_se"] = se[m]
    out["reps"] = g.size()
    return out.reset_index()
