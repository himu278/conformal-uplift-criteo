from conformal_uplift import real_study, report
from conformal_uplift.audit import audit
from conformal_uplift.simulate import make_synthetic_criteo


def test_audit_on_synthetic():
    df = make_synthetic_criteo(30_000, seed=0)
    a = audit(df=df)
    assert a["n_rows"] == 30_000
    assert a["integrity"]["conversion_without_visit"] == 0
    assert a["integrity"]["exposed_controls"] == 0
    assert a["srm"]["p_value"] > 0.001
    assert a["max_abs_smd"] < 0.1


def test_real_study_end_to_end(tmp_path):
    df = make_synthetic_criteo(40_000, seed=1)
    res = real_study.run(df, train_rows=None, n_boot=20, model="logistic", verbose=False)
    for out in ("visit", "conversion"):
        c = res["outcomes"][out]["conformal"]
        assert 0.9 < c["factual_coverage_treated"] <= 1.0
        assert abs(sum(c["set_shares"].values()) - 1) < 1e-9
    report.write_real_report(audit(df=df), res, tmp_path)
    assert (tmp_path / "results.md").exists()
