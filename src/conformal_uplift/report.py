"""Markdown reports. All sentences are generated from computed numbers."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .data import REPO_ROOT

README = REPO_ROOT / "README.md"
MARKERS = {"sim": ("<!-- SIM:START -->", "<!-- SIM:END -->"),
           "real": ("<!-- REAL:START -->", "<!-- REAL:END -->")}


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def pct(x, d=1):
    return "n/a" if x is None or x != x else f"{100 * x:.{d}f}%"


def pp(x, d=2):
    return f"{100 * x:+.{d}f} pp"


# --------------------------------------------------------------------------- simulation
def sim_headline(summary: pd.DataFrame, alpha: float) -> str:
    n_max = summary["n"].max()
    s = summary[(summary["n"] == n_max) & (summary["treat_share"] == 0.85)]
    worst = s["cov_ite"].min()
    ind = s[s["coupling"] == "independent"].sort_values("base_rate")
    target = 1 - alpha
    below = summary[summary["cov_ite"] + 2 * summary["cov_ite_se"] < target]
    verdict = ("**Validity holds.** No cell's mean ITE coverage is below the target by more than "
               "two Monte Carlo standard errors" if below.empty else
               f"**Validity fails in {len(below)} cell(s)** (mean coverage more than two Monte Carlo "
               f"standard errors below target; see reports/simulation.md)")
    lines = [
        f"*Simulation: {int(summary['reps'].iloc[0])} replications per cell; "
        f"target ITE coverage {pct(target, 0)}.*", "",
        f"- {verdict}. Lowest mean coverage across all cells: {pct(summary['cov_ite'].min())}; "
        f"at n = {n_max:,} with an 85/15 split: {pct(worst)}.",
    ]
    rows = []
    for _, r in ind.iterrows():
        rows.append([pct(r["base_rate"], 1), pct(r["set_{0}"]), pct(r["share_full_set"]),
                     pct(r["share_excludes_zero"], 2), pct(r["share_empty"], 1),
                     pct(r["decile_ci_excludes_zero"], 0), pct(r["decile_ci_coverage"], 0)])
    lines += [
        f"- **How informative are the sets?** With n = {n_max:,} and an 85/15 split "
        f"(independent coupling):", "",
        md_table(pd.DataFrame(rows, columns=["Base rate", "ITE set = {0}", "ITE set = {-1,0,1}",
                                             "Set excludes 0", "Empty set",
                                             "Decile CIs excluding 0",
                                             "Decile CI coverage (target 95%)"])), "",
        "- An ITE set of {0} is *valid* but is not evidence of no effect: it appears because almost "
        "nobody has the outcome in either arm. "
        f"The largest share of sets that certify a benefit ({{1}}) in any cell is "
        f"{pct(summary['share_certified_benefit'].max(), 2)}. The \"Decile CIs excluding 0\" column shows how often decile-level difference-in-means intervals, the "
        "group-level alternative, exclude zero.",
        f"- The group-level alternative has its own failure mode: the decile intervals are Wald "
        f"intervals, and their mean coverage of the true decile effect ranges from "
        f"{pct(summary['decile_ci_coverage'].min(), 0)} to {pct(summary['decile_ci_coverage'].max(), 0)} "
        f"across cells (target 95%). Low values occur where a decile's control group has very few "
        f"events (rare outcomes, small holdouts).",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- real data
def real_headline(audit: dict | None, res: dict) -> str:
    lines = []
    if audit:
        srm = audit["srm"]
        lines += [
            f"*Criteo Uplift v2.1: {audit['n_rows']:,} rows; treatment share "
            f"{pct(srm['observed_share'], 2)} (SRM p = {srm['p_value']:.3f}); max |SMD| across "
            f"features {audit['max_abs_smd']:.4f}.*", ""]
        rows = [[e["metric"], pct(e["treated"], 3), pct(e["control"], 3), pp(e["ate"], 3),
                 f"[{pp(e['ate_ci_low'], 3)}, {pp(e['ate_ci_high'], 3)}]", pct(e["relative_lift"])]
                for e in audit["itt_effects"]]
        lines += [md_table(pd.DataFrame(rows, columns=["Outcome", "Treated", "Control", "ITT effect",
                                                       "95% CI", "Relative lift"])), ""]
    for out, r in res["outcomes"].items():
        c, cv = r["conformal"], r["curve"]
        lo, hi = cv.get("auuc_gain_ci", (np.nan, np.nan))
        top = r["policy"].iloc[0]
        lines += [
            f"**{out.capitalize()}**",
            f"- Conformal sets: factual coverage {pct(c['factual_coverage_treated'], 2)} (treated) and "
            f"{pct(c['factual_coverage_control'], 2)} (control), target {pct(c['target_per_arm'], 0)} each. "
            f"ITE sets: {pct(c['set_shares'].get('{0}', 0))} are {{0}}, "
            f"{pct(c['share_excludes_zero'], 2)} exclude 0, {pct(c['share_empty'], 1)} are empty.",
            f"- Ranking: AUUC gain over random (x1,000) {cv['auuc_gain'] * 1000:.3f} "
            f"(95% CI [{lo * 1000:.3f}, {hi * 1000:.3f}]). Treating the top "
            f"{pct(top['share_treated'], 0)} captures {pct(top['share_of_total_effect'], 0)} of the "
            f"total effect (random: {pct(top['share_treated'], 0)}).",
            "",
        ]
    return "\n".join(lines)


def write_sim_report(summary: pd.DataFrame, alpha: float, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    keep = ["n", "base_rate", "treat_share", "coupling", "cov_y1", "cov_y0", "cov_ite",
            "share_true_ite_nonzero", "set_{0}", "share_full_set", "share_excludes_zero",
            "share_empty", "decile_ci_coverage", "decile_ci_excludes_zero", "reps"]
    tab = summary[keep].copy()
    for c in keep[4:-1]:
        tab[c] = tab[c].map(lambda v: f"{v:.3f}")
    text = ["# Simulation study", "", sim_headline(summary, alpha), "", "## All cells", "", md_table(tab)]
    (out_dir / "simulation.md").write_text("\n".join(text) + "\n")


def write_real_report(audit: dict | None, res: dict, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = ["# Criteo Uplift v2.1: results", "", real_headline(audit, res)]
    if audit:
        parts += ["## Audit", "",
                  f"- Integrity: {json.dumps(audit['integrity'])}",
                  f"- Exposure rate among treated: {pct(audit['exposure_rate_treated'], 2)}", "",
                  md_table(pd.DataFrame(audit["balance"]).round(5)), ""]
    for out, r in res["outcomes"].items():
        ex = r["exposure"]
        parts += [f"## {out.capitalize()}", "", "### Conformal ITE set types (test set)", "",
                  md_table(pd.DataFrame([{k: pct(v, 2) for k, v in r["conformal"]["set_shares"].items()}])), "",
                  "### Decile calibration", "",
                  md_table(r["deciles"].assign(**{c: r["deciles"][c].map(lambda v: f"{100 * v:.3f}")
                                                  for c in ["predicted_uplift", "observed_uplift",
                                                            "ci_low", "ci_high"]})), "",
                  "(uplift columns in percentage points)", "",
                  "### Targeting policy", "",
                  md_table(r["policy"].round(4)), "",
                  "### Holdout size", "",
                  md_table(r["holdout"].round(6)), "",
                  "### Exposure (non-randomized) vs. assignment (randomized)", "",
                  f"- ITT effect: {pp(ex['itt'], 3)}; naive exposed-vs-control: "
                  f"{pp(ex['naive_exposed_vs_control'], 3)}; exposed share in treated: "
                  f"{pct(ex['share_exposed_in_treated'], 1)}; complier (Wald/IV) effect: "
                  f"{pp(ex['complier_effect_wald'], 3)} (95% CI [{pp(ex['complier_effect_ci'][0], 3)}, "
                  f"{pp(ex['complier_effect_ci'][1], 3)}], assumes the exclusion restriction).", ""]
    (out_dir / "results.md").write_text("\n".join(parts) + "\n")


def update_readme(key: str, block: str, readme: Path = README) -> bool:
    start, end = MARKERS[key]
    if not readme.exists():
        return False
    text = readme.read_text(encoding="utf-8")
    if start not in text or end not in text:
        return False
    new = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: f"{start}\n{block}\n{end}",
                 text, flags=re.S)
    readme.write_text(new, encoding="utf-8")
    return True
