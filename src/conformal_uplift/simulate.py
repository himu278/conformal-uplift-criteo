"""Simulated randomized experiments with binary potential outcomes.

The data an experiment reveals (X, T, Y = Y(T)) identify only the two marginals
P(Y(1) = 1 | x) and P(Y(0) = 1 | x). The joint law of (Y(0), Y(1)) -- the "coupling" --
is not identified, yet the individual treatment effect Y(1) - Y(0) depends on it.
The simulator therefore draws potential outcomes from fixed marginals under three
couplings that are all consistent with the same observed data:

- "comonotone":      Y(t) = 1{U < mu_t(x)} with one shared U  (no one is harmed when mu1 >= mu0)
- "independent":     Y(0) and Y(1) use independent uniforms
- "countermonotone": Y(0) = 1{U < mu0}, Y(1) = 1{1 - U < mu1}  (most harm and benefit)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit

COUPLINGS = ("comonotone", "independent", "countermonotone")
N_FEATURES = 6


def _beta(d: int) -> np.ndarray:
    return np.array([0.8, -0.6, 0.5, 0.0, 0.3, 0.0][:d])


def response_surfaces(X: np.ndarray, base_rate: float, rel_lift: float,
                      heterogeneity: float, intercept: float | None = None):
    """Return mu0(x), mu1(x) and the intercept that hits the target base rate.

    Treatment acts on the log-odds scale: logit mu1 = logit mu0 + tau(x) with
    tau(x) = log(1 + rel_lift) * (1 + heterogeneity * tanh(x_2)).
    """
    lin = X @ _beta(X.shape[1])
    if intercept is None:
        intercept = brentq(lambda a: expit(a + lin).mean() - base_rate, -30, 30)
    mu0 = expit(intercept + lin)
    tau = np.log1p(rel_lift) * (1 + heterogeneity * np.tanh(X[:, 1]))
    mu1 = expit(intercept + lin + tau)
    return mu0, mu1, intercept


def potential_outcomes(mu0, mu1, coupling: str, rng: np.random.Generator):
    u = rng.uniform(size=mu0.shape)
    y0 = (u < mu0).astype(np.int8)
    if coupling == "comonotone":
        y1 = (u < mu1).astype(np.int8)
    elif coupling == "independent":
        y1 = (rng.uniform(size=mu0.shape) < mu1).astype(np.int8)
    elif coupling == "countermonotone":
        y1 = ((1 - u) < mu1).astype(np.int8)
    else:
        raise ValueError(f"unknown coupling {coupling!r}")
    return y0, y1


def simulate_experiment(n: int, base_rate: float, treat_share: float, rel_lift: float = 0.5,
                        heterogeneity: float = 1.0, seed: int = 0, intercept: float | None = None):
    """One randomized experiment. Returns X, T, mu0, mu1 and the intercept used.

    Potential outcomes are drawn separately per coupling (see `potential_outcomes`), so
    the same fitted models can be evaluated under every coupling.
    """
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, N_FEATURES))
    T = (rng.uniform(size=n) < treat_share).astype(np.int8)
    mu0, mu1, a = response_surfaces(X, base_rate, rel_lift, heterogeneity, intercept)
    return X, T, mu0, mu1, a


def make_synthetic_criteo(n: int = 20000, seed: int = 0) -> pd.DataFrame:
    """Small synthetic table with the Criteo Uplift v2.1 schema, for tests and CI only.

    Rates are chosen to resemble the published averages (treatment share 0.85, visit rate
    near 5%, conversion near 0.3%) but the data are NOT the real dataset.
    """
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 12)).astype(np.float32)
    t = (rng.uniform(size=n) < 0.85).astype(np.int8)
    lin = 0.9 * X[:, 0] - 0.5 * X[:, 2] + 0.4 * X[:, 8]
    p_visit = expit(-3.3 + lin + t * (0.25 + 0.3 * np.tanh(X[:, 9])))
    visit = (rng.uniform(size=n) < p_visit).astype(np.int8)
    p_conv_given_visit = expit(-2.8 + 0.5 * X[:, 0] + 0.3 * t)
    conversion = (visit & (rng.uniform(size=n) < p_conv_given_visit)).astype(np.int8)
    exposure = (t & (rng.uniform(size=n) < expit(0.5 * X[:, 1] - 0.8))).astype(np.int8)
    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(12)])
    df["treatment"], df["conversion"], df["visit"], df["exposure"] = t, conversion, visit, exposure
    return df
