# Criteo Uplift v2.1: results

*Criteo Uplift v2.1: 13,979,592 rows; treatment share 85.00% (SRM p = 0.999); max |SMD| across features 0.0488.*

| Outcome | Treated | Control | ITT effect | 95% CI | Relative lift |
|---|---|---|---|---|---|
| visit | 4.854% | 3.820% | +1.034 pp | [+1.006 pp, +1.063 pp] | 27.1% |
| conversion | 0.309% | 0.194% | +0.115 pp | [+0.108 pp, +0.122 pp] | 59.4% |

**Visit**
- Conformal sets: factual coverage 95.01% (treated) and 95.09% (control), target 95% each. ITE sets: 96.8% are {0}, 0.06% exclude 0, 3.2% are empty.
- Ranking: AUUC gain over random (x1,000) 3.284 (95% CI [3.076, 3.448]). Treating the top 10% captures 57% of the total effect (random: 10%).

**Conversion**
- Conformal sets: factual coverage 95.00% (treated) and 95.01% (control), target 95% each. ITE sets: 93.7% are {0}, 0.00% exclude 0, 6.3% are empty.
- Ranking: AUUC gain over random (x1,000) 0.242 (95% CI [0.188, 0.313]). Treating the top 10% captures 60% of the total effect (random: 10%).

## Audit

- Integrity: {"n_rows": 13979592, "conversion_without_visit": 0, "exposed_controls": 0, "non_binary_labels": 0}
- Exposure rate among treated: 3.60%

| feature | smd | distinct_values |
|---|---|---|
| f0 | -0.00687 | 2181959 |
| f1 | 0.02399 | 60 |
| f2 | -0.00624 | 808663 |
| f3 | -0.04884 | 552 |
| f4 | 0.00797 | 260 |
| f5 | -0.03056 | 132 |
| f6 | -0.04045 | 1645 |
| f7 | 0.02127 | 622143 |
| f8 | -0.02243 | 3743 |
| f9 | 0.024 | 1594 |
| f10 | 0.01056 | 483634 |
| f11 | -0.00516 | 136 |

## Visit

### Conformal ITE set types (test set)

| {} | {0} | {-1,0} | {0,1} | {-1,0,1} | {-1} | {1} | {-1,1} |
|---|---|---|---|---|---|---|---|
| 3.19% | 96.76% | 0.00% | 0.00% | 0.00% | 0.00% | 0.06% | 0.00% |

### Decile calibration

| bin | n | predicted_uplift | observed_uplift | ci_low | ci_high |
|---|---|---|---|---|---|
| 1 | 419388 | -0.950 | 0.824 | 0.597 | 1.050 |
| 2 | 419388 | -0.023 | -0.002 | -0.058 | 0.053 |
| 3 | 419388 | 0.003 | 0.005 | -0.030 | 0.040 |
| 4 | 419387 | 0.012 | 0.030 | 0.001 | 0.060 |
| 5 | 419388 | 0.022 | 0.036 | 0.007 | 0.065 |
| 6 | 419388 | 0.037 | 0.060 | 0.020 | 0.099 |
| 7 | 419387 | 0.083 | 0.085 | 0.023 | 0.146 |
| 8 | 419388 | 0.241 | 0.240 | 0.132 | 0.347 |
| 9 | 419388 | 1.090 | 0.911 | 0.708 | 1.113 |
| 10 | 419388 | 7.202 | 5.916 | 5.541 | 6.291 |

(uplift columns in percentage points)

### Targeting policy

| share_treated | incremental_per_1000 | random_targeting_per_1000 | share_of_total_effect |
|---|---|---|---|
| 0.1 | 5.9164 | 1.0459 | 0.5657 |
| 0.2 | 7.7656 | 2.0917 | 0.7425 |
| 0.3 | 8.6213 | 3.1376 | 0.8243 |
| 0.5 | 9.2955 | 5.2293 | 0.8888 |
| 1.0 | 10.4586 | 10.4586 | 1.0 |

### Holdout size

| control_share | n_control | auuc_gain | auuc_ci_low | auuc_ci_high | auuc_ci_width | ci_excludes_zero |
|---|---|---|---|---|---|---|
| 0.15 | 628940 | 0.003248 | 0.003104 | 0.003455 | 0.000351 | True |
| 0.05 | 187579 | 0.003129 | 0.002817 | 0.003476 | 0.000659 | True |
| 0.02 | 72735 | 0.003269 | 0.002637 | 0.003894 | 0.001257 | True |
| 0.01 | 36000 | 0.003091 | 0.002344 | 0.00378 | 0.001436 | True |

### Exposure (non-randomized) vs. assignment (randomized)

- ITT effect: +1.046 pp; naive exposed-vs-control: +37.822 pp; exposed share in treated: 3.6%; complier (Wald/IV) effect: +29.141 pp (95% CI [+27.686 pp, +30.596 pp], assumes the exclusion restriction).

## Conversion

### Conformal ITE set types (test set)

| {} | {0} | {-1,0} | {0,1} | {-1,0,1} | {-1} | {1} | {-1,1} |
|---|---|---|---|---|---|---|---|
| 6.34% | 93.66% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |

### Decile calibration

| bin | n | predicted_uplift | observed_uplift | ci_low | ci_high |
|---|---|---|---|---|---|
| 1 | 419388 | -0.383 | 0.200 | 0.135 | 0.265 |
| 2 | 419388 | 0.000 | -0.002 | -0.015 | 0.010 |
| 3 | 419388 | 0.002 | 0.003 | -0.003 | 0.009 |
| 4 | 419387 | 0.002 | 0.008 | 0.005 | 0.011 |
| 5 | 419388 | 0.003 | -0.002 | -0.012 | 0.007 |
| 6 | 419388 | 0.004 | -0.001 | -0.012 | 0.009 |
| 7 | 419387 | 0.008 | 0.009 | -0.001 | 0.018 |
| 8 | 419388 | 0.016 | 0.011 | -0.007 | 0.028 |
| 9 | 419388 | 0.056 | 0.035 | 0.007 | 0.064 |
| 10 | 419388 | 1.275 | 0.607 | 0.502 | 0.712 |

(uplift columns in percentage points)

### Targeting policy

| share_treated | incremental_per_1000 | random_targeting_per_1000 | share_of_total_effect |
|---|---|---|---|
| 0.1 | 0.6072 | 0.1009 | 0.6016 |
| 0.2 | 0.7159 | 0.2019 | 0.7092 |
| 0.3 | 0.7623 | 0.3028 | 0.7552 |
| 0.5 | 0.7947 | 0.5047 | 0.7873 |
| 1.0 | 1.0094 | 1.0094 | 1.0 |

### Holdout size

| control_share | n_control | auuc_gain | auuc_ci_low | auuc_ci_high | auuc_ci_width | ci_excludes_zero |
|---|---|---|---|---|---|---|
| 0.15 | 628940 | 0.000242 | 0.000188 | 0.000287 | 9.9e-05 | True |
| 0.05 | 187579 | 0.00025 | 0.00016 | 0.000346 | 0.000185 | True |
| 0.02 | 72735 | 0.000134 | 1.1e-05 | 0.000288 | 0.000277 | True |
| 0.01 | 36000 | 0.000266 | 4.1e-05 | 0.000436 | 0.000395 | True |

### Exposure (non-randomized) vs. assignment (randomized)

- ITT effect: +0.101 pp; naive exposed-vs-control: +5.176 pp; exposed share in treated: 3.6%; complier (Wald/IV) effect: +2.813 pp (95% CI [+2.464 pp, +3.161 pp], assumes the exclusion restriction).

