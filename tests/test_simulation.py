import numpy as np

from conformal_uplift import sim_study
from conformal_uplift.simulate import COUPLINGS, potential_outcomes, simulate_experiment


def test_couplings_share_marginals():
    _, _, mu0, mu1, _ = simulate_experiment(200_000, 0.2, 0.5, seed=1)
    for c in COUPLINGS:
        y0, y1 = potential_outcomes(mu0, mu1, c, np.random.default_rng(2))
        assert abs(y0.mean() - mu0.mean()) < 0.005
        assert abs(y1.mean() - mu1.mean()) < 0.005


def test_base_rate_is_hit():
    _, _, mu0, _, _ = simulate_experiment(100_000, 0.01, 0.85, seed=3)
    assert abs(mu0.mean() - 0.01) < 0.001


def test_ite_coverage_meets_target_under_every_coupling():
    grid = {"base_rate": [0.3], "treat_share": [0.85], "n": [8000]}
    raw = sim_study.run(grid, reps=30, alpha=0.2, verbose=False)
    summ = sim_study.summarize(raw)
    for _, r in summ.iterrows():
        assert r["cov_ite"] >= 0.8 - 2.5 * r["cov_ite_se"], r["coupling"]
