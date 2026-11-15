"""Split conformal prediction sets for binary potential outcomes and individual treatment effects.

Setting: a completely randomized experiment. Within each arm t, calibration units and a
new unit drawn from the same population are exchangeable, so a split-conformal set for
the factual outcome Y in arm t is also a valid set for the potential outcome Y(t) of any
unit (Lei & Candes, 2021, JRSS-B). Because assignment does not depend on X, no
propensity weighting is needed.

For binary Y we use the score s(x, y) = 1 - p_hat(y | x). The set is
    C(x) = { y in {0, 1} : 1 - p_hat(y | x) <= q },
where q is the ceil((n + 1)(1 - alpha)) / n empirical quantile of calibration scores.
This gives P(Y(t) in C_t(X)) >= 1 - alpha (marginal, finite sample).

ITE sets ("naive" construction of Lei & Candes): build each arm's set at level alpha / 2
and take all differences y1 - y0. By the union bound the ITE set covers the true
Y(1) - Y(0) with probability >= 1 - alpha, whatever the (unidentified) joint law of
(Y(0), Y(1)).
"""
from __future__ import annotations

import numpy as np

SET_TYPES = ["{}", "{0}", "{-1,0}", "{0,1}", "{-1,0,1}", "{-1}", "{1}", "{-1,1}"]


def conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    """Finite-sample-corrected quantile. Returns +inf if the sample is too small."""
    scores = np.asarray(scores, dtype=float)
    n = scores.size
    k = int(np.ceil((n + 1) * (1 - alpha)))
    if n == 0 or k > n:
        return np.inf
    return float(np.sort(scores)[k - 1])


def binary_sets(p1_cal, y_cal, p1_new, alpha: float):
    """Split-conformal sets for a binary outcome.

    Parameters
    ----------
    p1_cal : predicted P(Y = 1 | x) on calibration units (one arm)
    y_cal  : observed 0/1 outcomes of those calibration units
    p1_new : predicted P(Y = 1 | x) for the units that need a set
    alpha  : miscoverage level

    Returns
    -------
    has0, has1 : boolean arrays, whether 0 / 1 is in the set; q : the threshold
    """
    p1_cal = np.asarray(p1_cal, float)
    y_cal = np.asarray(y_cal).astype(int)
    # score(x, 0) = p1 and score(x, 1) = 1 - p1, written with exactly the same floating-point
    # expressions as the set rule below; computing 1 - (1 - p1) instead can round differently
    # and silently break coverage when many scores are tied (e.g. a constant model).
    scores = np.where(y_cal == 1, 1 - p1_cal, p1_cal)
    q = conformal_quantile(scores, alpha)
    p1_new = np.asarray(p1_new, float)
    has1 = (1 - p1_new) <= q
    has0 = p1_new <= q          # 1 - p_hat(0|x) = p1
    return has0, has1, q


def ite_membership(has0_t, has1_t, has0_c, has1_c):
    """Membership of -1, 0, +1 in the ITE set {y1 - y0 : y1 in C1, y0 in C0}."""
    has_m1 = has0_t & has1_c                       # y1 = 0, y0 = 1
    has_0 = (has0_t & has0_c) | (has1_t & has1_c)  # equal outcomes
    has_p1 = has1_t & has0_c                       # y1 = 1, y0 = 0
    return has_m1, has_0, has_p1


def set_type(has_m1, has_0, has_p1) -> np.ndarray:
    """Label each ITE set, e.g. '{0}', '{0,1}', '{-1,0,1}'."""
    code = has_m1.astype(int) * 4 + has_0.astype(int) * 2 + has_p1.astype(int)
    labels = np.array(["{}", "{1}", "{0}", "{0,1}", "{-1}", "{-1,1}", "{-1,0}", "{-1,0,1}"])
    return labels[code]


def ite_covers(has_m1, has_0, has_p1, ite_true) -> np.ndarray:
    ite_true = np.asarray(ite_true)
    return np.where(ite_true == 1, has_p1, np.where(ite_true == -1, has_m1, has_0))


def set_type_shares(types: np.ndarray) -> dict:
    vals, counts = np.unique(types, return_counts=True)
    out = {t: 0.0 for t in SET_TYPES}
    out.update({v: c / types.size for v, c in zip(vals, counts)})
    return out


def informativeness(has_m1, has_0, has_p1) -> dict:
    """Summaries that say whether the ITE sets tell a decision maker anything."""
    empty = ~(has_m1 | has_0 | has_p1)
    return {
        # An empty set is an abstention (it happens with the 1 - p score when every label
        # looks unlikely), so it is counted separately and not as "excludes zero".
        "share_empty": float(np.mean(empty)),
        "share_excludes_zero": float(np.mean(~has_0 & ~empty)),  # certifies a non-zero effect
        "share_certified_benefit": float(np.mean(has_p1 & ~has_0 & ~has_m1)),
        "share_excludes_harm": float(np.mean(~has_m1 & ~empty)),  # rules out Y(1) < Y(0)
        "share_only_zero": float(np.mean(has_0 & ~has_m1 & ~has_p1)),
        "share_full_set": float(np.mean(has_m1 & has_0 & has_p1)),
    }
