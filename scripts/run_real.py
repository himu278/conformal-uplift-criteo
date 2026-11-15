"""Real-data study on Criteo Uplift v2.1 (run download_data.py first).

    python scripts/run_real.py                      # all rows (needs about 4 GB of free RAM)
    python scripts/run_real.py --max-rows 3000000   # random sample, for smaller machines
    python scripts/run_real.py --synthetic          # schema-identical fake data, for testing only
"""
import argparse
import json

import _path  # noqa: F401
from _path import ROOT

from conformal_uplift import plots, real_study, report
from conformal_uplift.audit import audit
from conformal_uplift.data import PARQUET_FILE, load
from conformal_uplift.simulate import make_synthetic_criteo

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--train-rows", type=int, default=3_000_000)
    ap.add_argument("--n-boot", type=int, default=200)
    ap.add_argument("--alpha", type=float, default=0.10)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.synthetic:
        df = make_synthetic_criteo(200_000, seed=1)
        aud = audit(df=df)
        out = ROOT / (a.out or "reports_synthetic")
    else:
        df = load(PARQUET_FILE, max_rows=a.max_rows)
        aud = audit(parquet=PARQUET_FILE) if a.max_rows is None else audit(df=df)
        out = ROOT / (a.out or "reports")
    print(f"Loaded {len(df):,} rows.")
    res = real_study.run(df, alpha=a.alpha, train_rows=a.train_rows, n_boot=a.n_boot)

    fig = out / "figures"
    for o, r in res["outcomes"].items():
        plots.uplift_curve_plot(r["curve"], fig / f"uplift_curve_{o}.png",
                                f"Uplift curve: {o} (test set)", f"Incremental {o}s per customer")
        plots.calibration_plot(r["deciles"], fig / f"calibration_{o}.png",
                               f"Predicted vs. observed {o} uplift by decile")
        plots.holdout_plot(r["holdout"], fig / f"holdout_{o}.png",
                           f"Precision of the {o} ranking evaluation vs. holdout size")
    shares = [{"outcome": o, **{f"set_{k}": v for k, v in r["conformal"]["set_shares"].items()}}
              for o, r in res["outcomes"].items()]
    import pandas as pd
    plots.set_type_bars(pd.DataFrame(shares), "outcome", fig / "real_set_types.png",
                        "Conformal ITE sets on the real experiment", "Outcome")
    report.write_real_report(aud, res, out)

    def _clean(o):
        if isinstance(o, dict):
            return {k: _clean(v) for k, v in o.items() if k not in ("curve", "deciles", "policy", "holdout")}
        return o
    (out / "results.json").write_text(json.dumps(_clean(res), indent=2, default=float))
    for o, r in res["outcomes"].items():
        (out / "tables").mkdir(parents=True, exist_ok=True)
        r["deciles"].to_csv(out / "tables" / f"deciles_{o}.csv", index=False)
        r["policy"].to_csv(out / "tables" / f"policy_{o}.csv", index=False)
        r["holdout"].to_csv(out / "tables" / f"holdout_{o}.csv", index=False)
    block = report.real_headline(aud, res)
    print(block)
    if not a.synthetic and a.out is None and a.max_rows is None:
        print("README updated." if report.update_readme("real", block) else "README markers not found.")
    print(f"Reports written to {out}")
