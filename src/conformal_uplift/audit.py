"""Experiment audit: integrity checks, sample-ratio mismatch, balance, exposure funnel.

Queries live in sql/ and run on DuckDB (against the Parquet file, out of core). For tests
on a small DataFrame, SQLite is used as a fallback; the SQL is standard to both.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chisquare, norm

from .data import EXPECTED_TREATMENT_SHARE, FEATURES, REPO_ROOT

SQL_DIR = REPO_ROOT / "sql"


def run_sql(query: str, parquet: Path | None = None, df: pd.DataFrame | None = None) -> pd.DataFrame:
    if parquet is not None:
        import duckdb
        con = duckdb.connect()
        con.execute(f"CREATE VIEW criteo AS SELECT * FROM read_parquet('{Path(parquet).as_posix()}')")
        out = con.execute(query).df()
        con.close()
        return out
    try:
        import duckdb
        con = duckdb.connect()
        con.register("criteo", df)
        out = con.execute(query).df()
        con.close()
        return out
    except ImportError:
        import sqlite3
        con = sqlite3.connect(":memory:")
        df.to_sql("criteo", con, index=False)
        out = pd.read_sql_query(query, con)
        con.close()
        return out


def run_sql_file(name: str, **kw) -> pd.DataFrame:
    return run_sql((SQL_DIR / name).read_text(), **kw)


def srm_test(n_treated: int, n_control: int, share: float = EXPECTED_TREATMENT_SHARE) -> dict:
    n = n_treated + n_control
    stat, p = chisquare([n_treated, n_control], [n * share, n * (1 - share)])
    return {"n_treated": n_treated, "n_control": n_control, "observed_share": n_treated / n,
            "expected_share": share, "chi2": float(stat), "p_value": float(p)}


def rate_ci(rate: float, n: int, alpha: float = 0.05):
    se = np.sqrt(rate * (1 - rate) / n)
    z = norm.ppf(1 - alpha / 2)
    return rate - z * se, rate + z * se


def audit(parquet: Path | None = None, df: pd.DataFrame | None = None) -> dict:
    kw = {"parquet": parquet, "df": df}
    arms = run_sql_file("01_arm_summary.sql", **kw)
    integ = run_sql_file("02_integrity.sql", **kw).iloc[0].to_dict()
    funnel = run_sql_file("03_exposure_funnel.sql", **kw)
    mom = run_sql_file("04_balance_moments.sql", **kw).set_index("treatment")
    distinct = run_sql_file("05_distinct_values.sql", **kw).iloc[0].to_dict()

    a = arms.set_index("treatment")
    n1, n0 = int(a.loc[1, "n"]), int(a.loc[0, "n"])
    res = {"n_rows": int(integ["n_rows"]), "srm": srm_test(n1, n0),
           "integrity": {k: int(v) for k, v in integ.items()}}

    rates = []
    for metric in ("visit", "conversion"):
        r1, r0 = float(a.loc[1, f"{metric}_rate"]), float(a.loc[0, f"{metric}_rate"])
        d = r1 - r0
        se = np.sqrt(r1 * (1 - r1) / n1 + r0 * (1 - r0) / n0)
        rates.append({"metric": metric, "treated": r1, "control": r0, "ate": d,
                      "ate_ci_low": d - 1.96 * se, "ate_ci_high": d + 1.96 * se,
                      "relative_lift": d / r0 if r0 else np.nan})
    res["itt_effects"] = rates
    res["exposure_rate_treated"] = float(a.loc[1, "exposure_rate"])

    smd = []
    for f in FEATURES:
        m1, m0 = mom.loc[1, f"mean_{f}"], mom.loc[0, f"mean_{f}"]
        v1 = mom.loc[1, f"sq_{f}"] - m1 ** 2
        v0 = mom.loc[0, f"sq_{f}"] - m0 ** 2
        pooled = np.sqrt(max((v1 + v0) / 2, 1e-12))
        smd.append({"feature": f, "smd": float((m1 - m0) / pooled),
                    "distinct_values": int(distinct[f"distinct_{f}"])})
    res["balance"] = smd
    res["max_abs_smd"] = float(max(abs(s["smd"]) for s in smd))
    res["exposure_funnel"] = funnel.to_dict(orient="records")
    return res
