"""Download Criteo Uplift v2.1, verify its checksum, and convert it to Parquet."""
import _path  # noqa: F401

from conformal_uplift.data import PARQUET_FILE, RAW_FILE, download, to_parquet, verify

if __name__ == "__main__":
    if not RAW_FILE.exists():
        download()
    else:
        print(f"{RAW_FILE.name} already present.")
    if not verify():
        raise SystemExit("Checksum mismatch: delete the file and download again.")
    if not PARQUET_FILE.exists():
        print("Converting to Parquet with DuckDB ...")
        to_parquet()
    print(f"Ready: {PARQUET_FILE}")
