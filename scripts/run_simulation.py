"""Simulation study of conformal ITE sets for binary outcomes.

    python scripts/run_simulation.py            # full grid (about 10-30 minutes on a laptop)
    python scripts/run_simulation.py --quick    # small grid for a smoke test
"""
import argparse

import _path  # noqa: F401
from _path import ROOT

from conformal_uplift import plots, report, sim_study

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=50)
    ap.add_argument("--alpha", type=float, default=0.10)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    grid = None
    if a.quick:
        grid = {"base_rate": [0.003, 0.05, 0.5], "treat_share": [0.5, 0.85], "n": [20_000]}
        a.reps = min(a.reps, 5)
    out = ROOT / (a.out or "reports")
    raw = sim_study.run(grid, reps=a.reps, alpha=a.alpha)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    raw.to_csv(out / "tables" / "simulation_raw.csv", index=False)
    summ = sim_study.summarize(raw)
    summ.to_csv(out / "tables" / "simulation_summary.csv", index=False)
    report.write_sim_report(summ, a.alpha, out)

    n_max = summ["n"].max()
    sel = summ[(summ["n"] == n_max) & (summ["treat_share"] == 0.85)]
    plots.coverage_lines(sel, out / "figures" / "sim_coverage.png", a.alpha,
                         f"Coverage of conformal ITE sets (n = {n_max:,}, 85/15 split)")
    shares = sel[sel["coupling"] == "independent"].sort_values("base_rate").copy()
    shares["base_rate"] = shares["base_rate"].map(lambda b: f"{100 * b:g}%")
    plots.set_type_bars(shares, "base_rate", out / "figures" / "sim_set_types.png",
                        "Conformal ITE set types by outcome base rate (independent coupling)", "Base rate")
    block = report.sim_headline(summ, a.alpha)
    print(block)
    if not a.quick and a.out is None:
        print("README updated." if report.update_readme("sim", block) else "README markers not found.")
