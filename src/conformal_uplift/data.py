"""Download, verify and convert the Criteo Uplift Prediction Dataset (v2.1).

Source: Criteo AI Lab, https://ailab.criteo.com/criteo-uplift-prediction-dataset/
Mirror: https://huggingface.co/datasets/criteo/criteo-uplift (uploaded by Criteo)
License: CC BY-NC-SA 4.0. The data are NOT committed to this repository; this module
downloads them from the official locations.

Citation: Diemert, Betlei, Renaudin, Amini. "A Large Scale Benchmark for Uplift
Modeling." AdKDD & TargetAd Workshop, KDD 2018. Extended version: arXiv:2111.10106.
"""
from __future__ import annotations

import hashlib
import shutil
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
RAW_FILE = RAW_DIR / "criteo-research-uplift-v2.1.csv.gz"
PARQUET_FILE = PROCESSED_DIR / "criteo_uplift_v2.1.parquet"

URLS = [
    "https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz",
    "http://go.criteo.net/criteo-research-uplift-v2.1.csv.gz",
]
# SHA256 listed for the file on the Hugging Face mirror.
SHA256 = "2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc"

FEATURES = [f"f{i}" for i in range(12)]
LABELS = ["treatment", "conversion", "visit", "exposure"]
EXPECTED_ROWS = 13_979_592       # official v2.1 figure
EXPECTED_TREATMENT_SHARE = 0.85  # official v2.1 figure


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def download(dest: Path = RAW_FILE) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err = None
    for url in URLS:
        try:
            print(f"Downloading {url}\n  (about 300 MB; this can take several minutes) ...")
            tmp = dest.with_suffix(".part")
            with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f, length=1 << 20)
            tmp.replace(dest)
            return dest
        except Exception as e:  # try the next mirror
            last_err = e
            print(f"  failed: {e}")
    raise RuntimeError(f"All downloads failed; last error: {last_err}")


def verify(path: Path = RAW_FILE) -> bool:
    digest = sha256(path)
    ok = digest == SHA256
    print(f"SHA256 {'matches' if ok else 'DOES NOT match'} the published checksum ({digest[:16]}...).")
    return ok


def to_parquet(src: Path = RAW_FILE, dest: Path = PARQUET_FILE) -> Path:
    """Convert the gzip CSV to Parquet with compact types (float32 features, int8 labels)."""
    import duckdb
    dest.parent.mkdir(parents=True, exist_ok=True)
    cols = ", ".join([f"CAST({c} AS FLOAT) AS {c}" for c in FEATURES] +
                     [f"CAST({c} AS TINYINT) AS {c}" for c in LABELS])
    con = duckdb.connect()
    con.execute(f"COPY (SELECT {cols} FROM read_csv_auto('{src.as_posix()}')) "
                f"TO '{dest.as_posix()}' (FORMAT PARQUET)")
    con.close()
    return dest


def load(path: Path = PARQUET_FILE, max_rows: int | None = None, seed: int = 42) -> pd.DataFrame:
    """Load the Parquet file into pandas. `max_rows` takes a uniform random sample."""
    import duckdb
    con = duckdb.connect()
    q = f"SELECT * FROM read_parquet('{path.as_posix()}')"
    if max_rows:
        q += f" USING SAMPLE reservoir({int(max_rows)} ROWS) REPEATABLE ({int(seed)})"
    df = con.execute(q).df()
    con.close()
    for c in FEATURES:
        df[c] = df[c].astype(np.float32)
    for c in LABELS:
        df[c] = df[c].astype(np.int8)
    return df
