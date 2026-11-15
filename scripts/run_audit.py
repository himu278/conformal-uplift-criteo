"""Audit the experiment: integrity, sample-ratio mismatch, balance, ITT effects, exposure."""
import json

import _path  # noqa: F401
from _path import ROOT

from conformal_uplift.audit import audit
from conformal_uplift.data import PARQUET_FILE

if __name__ == "__main__":
    res = audit(parquet=PARQUET_FILE)
    out = ROOT / "reports" / "audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2, default=float))
    print(json.dumps({k: res[k] for k in ("n_rows", "srm", "integrity", "itt_effects",
                                         "exposure_rate_treated", "max_abs_smd")}, indent=2, default=float))
    print(f"\nWritten to {out}")
