import numpy as np

from conformal_uplift.uplift import decile_calibration, diff_in_means, policy_table, uplift_curve


def _data(n=40_000, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.uniform(size=n)
    t = (rng.uniform(size=n) < 0.85).astype(int)
    p = 0.05 + t * 0.10 * x          # effect grows with x
    y = (rng.uniform(size=n) < p).astype(int)
    return x, y, t


def test_curve_ends_at_ate_and_good_ranking_beats_random():
    x, y, t = _data()
    good = uplift_curve(x, y, t)
    bad = uplift_curve(-x, y, t)
    assert abs(good["curve"][-1] - diff_in_means(y, t)["diff"]) < 1e-12
    assert good["auuc_gain"] > 0 > bad["auuc_gain"]


def test_bootstrap_ci_contains_estimate():
    x, y, t = _data()
    r = uplift_curve(x, y, t, n_boot=50, seed=1)
    lo, hi = r["auuc_gain_ci"]
    assert lo < r["auuc_gain"] < hi


def test_deciles_and_policy_tables():
    x, y, t = _data()
    cal = decile_calibration(x, y, t)
    assert len(cal) == 10 and cal["observed_uplift"].iloc[-1] > cal["observed_uplift"].iloc[0]
    pol = policy_table(x, y, t)
    assert abs(pol["share_of_total_effect"].iloc[-1] - 1.0) < 1e-12
    assert pol["share_of_total_effect"].iloc[0] > 0.1
