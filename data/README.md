# Data

`python scripts/download_data.py` downloads **Criteo Uplift Prediction Dataset v2.1**
(`criteo-research-uplift-v2.1.csv.gz`, about 300 MB) from the Hugging Face mirror published by
Criteo (falling back to Criteo's own URL), checks its SHA256 against the published value, and
writes `data/processed/criteo_uplift_v2.1.parquet`.

| Column | Meaning |
|---|---|
| f0–f11 | anonymized features (randomly projected by Criteo) |
| treatment | 1 = assigned to treatment (randomized), 0 = control |
| exposure | 1 = the user was actually shown the ad (not randomized) |
| visit | binary outcome |
| conversion | binary outcome (a conversion implies a visit) |

Published v2.1 figures: 13,979,592 rows, treatment ratio 0.85, average visit rate 0.046992,
average conversion rate 0.00292. Version 1 (25.3M rows) had a leak and was withdrawn by Criteo;
do not use it.

License: CC BY-NC-SA 4.0. The data are not committed to this repository.
