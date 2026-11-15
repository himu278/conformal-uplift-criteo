"""Real-data study on the Criteo Uplift v2.1 randomized experiment.

Estimand: effects of `treatment` (randomized assignment), i.e. intention-to-treat (ITT).
`exposure` is not randomized; it is used only for the exposure / complier analysis.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .conformal import binary_sets, informativeness, ite_membership, set_type, set_type_shares
from .data import FEATURES
from .uplift import TLearner, decile_calibration, diff_in_means, policy_table, uplift_curve


def split(df: pd.DataFrame, fractions=(0.5, 0.2, 0.3), seed: int = 42):
    """Random train / calibration / test split (assignment is random, so no stratification
    is needed for validity; the split is reproducible through the seed)."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(df))
    a = int(fractions[0] * len(df))
    b = a + int(fractions[1] * len(df))
    return idx[:a], idx[a:b], idx[b:]


def exposure_analysis(df: pd.DataFrame, outcome: str) -> dict:
    """ITT, a naive exposed-vs-control comparison, and the complier (Wald / IV) effect.

    Controls are never exposed (one-sided noncompliance). Under the exclusion restriction
    (assignment affects the outcome only through exposure), the effect of exposure among
    compliers is ITT / P(exposed | treated) (Bloom 1984; Angrist, Imbens & Rubin 1996).
    The naive comparison is biased because exposure depends on auction outcomes that are
    related to the customer.
    """
    t = df["treatment"].to_numpy() == 1
    e = df["exposure"].to_numpy() == 1
    y = df[outcome].to_numpy().astype(float)
    itt = diff_in_means(y, t)
    naive = diff_in_means(y[e | ~t], t[e | ~t])
    share_exposed = e[t].mean()
    return {"outcome": outcome, "itt": itt["diff"], "itt_ci": (itt["ci_low"], itt["ci_high"]),
            "naive_exposed_vs_control": naive["diff"], "share_exposed_in_treated": float(share_exposed),
            "complier_effect_wald": itt["diff"] / share_exposed if share_exposed > 0 else np.nan,
            "complier_effect_ci": (itt["ci_low"] / share_exposed, itt["ci_high"] / share_exposed)
            if share_exposed > 0 else (np.nan, np.nan)}


def holdout_study(score, y, t, shares=(0.15, 0.05, 0.02, 0.01), n_boot: int = 100, seed: int = 0):
    """How precisely can the ranking be evaluated with a smaller control (holdout) group?

    Keeps every treated test unit and subsamples controls to reach each control share.
    """
    rng = np.random.default_rng(seed)
    t = np.asarray(t).astype(bool)
    treated, controls = np.flatnonzero(t), np.flatnonzero(~t)
    rows = []
    natural = (~t).mean()
    for s in shares:
        if s > natural + 1e-9:
            continue
        n_c = int(round(s / (1 - s) * treated.size))
        keep = np.concatenate([treated, rng.choice(controls, size=min(n_c, controls.size), replace=False)])
        r = uplift_curve(score[keep], y[keep], t[keep], n_boot=n_boot, seed=seed)
        lo, hi = r["auuc_gain_ci"]
        rows.append({"control_share": s, "n_control": int(min(n_c, controls.size)),
                     "auuc_gain": r["auuc_gain"], "auuc_ci_low": lo, "auuc_ci_high": hi,
                     "auuc_ci_width": hi - lo, "ci_excludes_zero": bool(lo > 0 or hi < 0)})
    return pd.DataFrame(rows)


def run(df: pd.DataFrame, outcomes=("visit", "conversion"), alpha: float = 0.10,
        train_rows: int | None = 3_000_000, n_boot: int = 200, seed: int = 42,
        model: str = "hgb", verbose: bool = True) -> dict:
    tr, ca, te = split(df, seed=seed)
    if train_rows and tr.size > train_rows:
        tr = np.random.default_rng(seed).choice(tr, size=train_rows, replace=False)
    X = df[FEATURES].to_numpy(np.float32)
    T = df["treatment"].to_numpy().astype(int)
    res = {"n_rows": int(len(df)), "n_train": int(tr.size), "n_calibration": int(ca.size),
           "n_test": int(te.size), "alpha": alpha, "model": model, "outcomes": {}}

    for out in outcomes:
        if verbose:
            print(f"  outcome: {out} -- fitting T-learner on {tr.size:,} rows ...")
        Y = df[out].to_numpy().astype(int)
        m = TLearner(model, seed=seed).fit(X[tr], Y[tr], T[tr])
        p1_ca, p0_ca = m.predict_arms(X[ca])
        p1_te, p0_te = m.predict_arms(X[te])

        # conformal sets: calibrate each arm on its own calibration units
        tca = T[ca] == 1
        h0t, h1t, q1 = binary_sets(p1_ca[tca], Y[ca][tca], p1_te, alpha / 2)
        h0c, h1c, q0 = binary_sets(p0_ca[~tca], Y[ca][~tca], p0_te, alpha / 2)
        tte = T[te] == 1
        y_te = Y[te]
        # factual coverage: in arm t, the set for Y(t) must contain the observed outcome
        cov1 = float(np.mean(np.where(y_te[tte] == 1, h1t[tte], h0t[tte])))
        cov0 = float(np.mean(np.where(y_te[~tte] == 1, h1c[~tte], h0c[~tte])))
        mm1, mz0, mp1 = ite_membership(h0t, h1t, h0c, h1c)

        score = p1_te - p0_te
        if verbose:
            print(f"  outcome: {out} -- evaluating ranking ({n_boot} bootstrap draws) ...")
        curve = uplift_curve(score, y_te, T[te], n_boot=n_boot, seed=seed)
        res["outcomes"][out] = {
            "ate_test": diff_in_means(y_te, T[te]),
            "conformal": {"q_treated": q1, "q_control": q0,
                          "factual_coverage_treated": cov1, "factual_coverage_control": cov0,
                          "target_per_arm": 1 - alpha / 2, "target_ite": 1 - alpha,
                          **informativeness(mm1, mz0, mp1),
                          "set_shares": set_type_shares(set_type(mm1, mz0, mp1))},
            "curve": curve,
            "deciles": decile_calibration(score, y_te, T[te]),
            "policy": policy_table(score, y_te, T[te]),
            "holdout": holdout_study(score, y_te, T[te], n_boot=max(50, n_boot // 2), seed=seed),
            "exposure": exposure_analysis(df.iloc[te], out),
            "score_summary": {"mean_predicted_uplift": float(score.mean()),
                              "share_predicted_negative": float(np.mean(score < 0))},
        }
    return res
