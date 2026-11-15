"""Run the whole project in one command, stopping at the first failure.

    python scripts/run_all.py                       # full run
    python scripts/run_all.py --max-rows 3000000    # smaller machines (README real-data block not updated)
    python scripts/run_all.py --skip-install        # packages already installed
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--skip-install", action="store_true")
    a = ap.parse_args()

    py = sys.executable
    real = [py, "scripts/run_real.py"] + (["--max-rows", str(a.max_rows)] if a.max_rows else [])
    steps = [
        ("Install packages", [py, "-m", "pip", "install", "-r", "requirements.txt"]),
        ("Unit tests", [py, "-m", "pytest"]),
        ("Simulation study", [py, "scripts/run_simulation.py"]),
        ("Download and convert data", [py, "scripts/download_data.py"]),
        ("Experiment audit", [py, "scripts/run_audit.py"]),
        ("Real-data analysis", real),
    ]
    if a.skip_install:
        steps = steps[1:]

    start = time.time()
    for i, (name, cmd) in enumerate(steps, 1):
        print(f"\n{'=' * 70}\n[{i}/{len(steps)}] {name}\n{'=' * 70}", flush=True)
        t0 = time.time()
        code = subprocess.call(cmd, cwd=ROOT)
        if code != 0:
            print(f"\nSTOPPED: step '{name}' failed (exit code {code}). "
                  f"Fix the error above, then run this script again.")
            sys.exit(code)
        print(f"-> done in {time.time() - t0:.0f} s")
    print(f"\nALL STEPS FINISHED in {(time.time() - start) / 60:.1f} minutes.")
    print("Send reports/results.md and reports/audit.json for review.")
