import itertools

import numpy as np

from conformal_uplift.conformal import (binary_sets, conformal_quantile, informativeness,
                                        ite_covers, ite_membership, set_type)


def test_quantile_small_sample_is_infinite():
    assert conformal_quantile(np.array([0.1, 0.2]), alpha=0.1) == np.inf


def test_binary_sets_marginal_coverage_is_exact():
    """Average coverage over many exchangeable draws must be >= 1 - alpha and close to it."""
    rng = np.random.default_rng(0)
    alpha, covs = 0.1, []
    for _ in range(400):
        x = rng.normal(size=600)
        p = 1 / (1 + np.exp(-(x - 1)))
        y = (rng.uniform(size=600) < p).astype(int)
        p_hat = 1 / (1 + np.exp(-(0.7 * x - 0.8)))      # deliberately misspecified model
        h0, h1, _ = binary_sets(p_hat[:500], y[:500], p_hat[500:], alpha)
        covs.append(np.mean(np.where(y[500:] == 1, h1, h0)))
    m = np.mean(covs)
    assert m >= 1 - alpha - 0.005
    assert m <= 1 - alpha + 0.03


def test_ite_membership_enumerates_all_pairs():
    for h0t, h1t, h0c, h1c in itertools.product([False, True], repeat=4):
        a = np.array
        m1, z0, p1 = ite_membership(a([h0t]), a([h1t]), a([h0c]), a([h1c]))
        c1 = [y for y, h in ((0, h0t), (1, h1t)) if h]
        c0 = [y for y, h in ((0, h0c), (1, h1c)) if h]
        expected = {y1 - y0 for y1 in c1 for y0 in c0}
        got = {v for v, h in ((-1, m1[0]), (0, z0[0]), (1, p1[0])) if h}
        assert got == expected


def test_set_type_labels_and_coverage():
    m1, z0, p1 = np.array([False, True, False]), np.array([True, True, False]), np.array([False, True, False])
    assert list(set_type(m1, z0, p1)) == ["{0}", "{-1,0,1}", "{}"]
    assert list(ite_covers(m1, z0, p1, np.array([0, -1, 1]))) == [True, True, False]
    info = informativeness(m1, z0, p1)
    assert abs(info["share_empty"] - 1 / 3) < 1e-12
    assert info["share_excludes_zero"] == 0.0     # empty sets are not counted as excluding 0


def test_tied_scores_from_constant_model_keep_coverage():
    """Regression test: a constant prediction makes every calibration score identical."""
    p = 0.5 / 251
    h0, h1, q = binary_sets(np.full(250, p), np.zeros(250, int), np.full(100, p), alpha=0.05)
    assert h0.all() and not h1.any()
