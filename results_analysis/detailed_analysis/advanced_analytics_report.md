# Advanced Analytics Report

This report covers the four advanced analyses executed in the notebook:

1. Delay-risk categorisation.
2. Group-level volume-delay association.
3. Extreme-delay sensitivity.
4. Spark MLlib departure-delay prediction.

All results are descriptive. They do not establish causal effects.

## 1. Delay-risk distribution

The target is departure delay for flown flights with a valid delay value. Bands
follow the 15-minute BTS delay threshold.

| Risk band | Flights | Share | Mean delay (min) | P90 delay (min) |
|---|---:|---:|---:|---:|
| On-time / early (<15 min) | 5,541,627 | 79.3615% | -2.87 | 6 |
| Minor (15-29 min) | 489,989 | 7.0171% | 21.12 | 27 |
| Moderate (30-59 min) | 434,972 | 6.2292% | 42.23 | 55 |
| Severe (60-119 min) | 307,679 | 4.4063% | 83.67 | 109 |
| Extreme (120+ min) | 208,499 | 2.9859% | 238.62 | 389 |
| **Total** | **6,982,766** | **100%** | | |

About four in five flown flights are on time or early. The severe and extreme
bands together contain 516,178 flights (7.39% of flown flights), but they account
for a disproportionate share of total delay minutes because their mean delays are
83.67 and 238.62 minutes.

## 2. Volume-delay association

Pearson correlations are computed across group-level aggregates, not across
individual flights.

| Group level | Groups | Pearson r | p-value | Interpretation |
|---|---:|---:|---:|---|
| Airline | 15 | 0.1594 | 0.5705 | Very weak and not statistically significant |
| Origin airport | 101 | 0.5169 | 0.0000 | Moderate positive association; reported p below display precision |

Airports with more flights tend to have higher delayed-departure rates among the
101 airports with at least 10,000 flights. This is an ecological association:
busy hubs can also differ in network structure, weather exposure, and scheduling.
The airline-level correlation is weak and should not be used to rank airline
quality. No causal mechanism is inferred.

## 3. Extreme-delay sensitivity

| Variant | Flights | Mean (min) | Median (min) | P99 (min) |
|---|---:|---:|---:|---:|
| All observed delays | 6,982,766 | 12.6451 | -2.00 | 216 |
| Excluding departures > 24 h | 6,982,205 | 12.5042 | -2.00 | 215 |
| Excluding departures > 12 h | 6,975,091 | 11.5368 | -2.00 | 205 |

The median is stable at -2 minutes. Removing the extreme tail reduces the mean by
0.14 minutes (>24 h) or 1.11 minutes (>12 h). The overall mean is therefore not
driven only by a few extreme records, although the upper tail remains materially
important for passenger experience and operational planning.

## 4. Spark MLlib delay prediction

### Setup

| Item | Value |
|---|---|
| Library | Spark MLlib |
| Algorithm | Logistic regression |
| Target | `dep_delay >= 15` minutes for flown flights |
| Population | 6,982,765 flights with valid schedule and elapsed-time fields |
| Positive class | 1,441,139 delayed departures (20.6385%) |
| Negative class | 5,541,626 (79.3615%) |
| Split | 80% train / 20% hold-out, random, seed 42 |
| Train rows | 5,585,937 |
| Test rows | 1,396,828 |
| Features after one-hot encoding | 168 |
| Class weights | positive 2.4227, negative 0.63 |
| Regularisation | L2, `regParam=0.01` |
| Max iterations | 20 |
| Decision threshold | 0.5 |
| Training/evaluation time | 51.5 s |

Features are limited to information available before the outcome:

- operating carrier;
- origin airport (top 50 by volume, otherwise `OTHER`);
- destination airport (top 50 by volume, otherwise `OTHER`);
- month;
- day of week;
- scheduled departure hour;
- distance;
- scheduled elapsed time.

Actual departure/arrival times, delay values, and cause-attribution fields are
excluded to prevent target leakage.

### Hold-out metrics

| Model | Accuracy | Precision | Recall | F1 | AUC |
|---|---:|---:|---:|---:|---:|
| Majority baseline | 0.7935 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| Logistic regression | 0.6180 | 0.3060 | 0.6702 | 0.4202 | 0.6884 |

### Confusion matrix

| Actual \ Predicted | Not delayed | Delayed |
|---|---:|---:|
| Not delayed | 669,962 | 438,423 |
| Delayed | 95,126 | 193,317 |

The model predicts 631,740 of 1,396,828 hold-out flights as delayed (45.2%).
Because the classes are imbalanced at roughly 79/21, the majority baseline gets
79.35% accuracy by never predicting a delay. The model deliberately trades
accuracy for recall: it captures 67.02% of delayed flights at 30.60% precision.
AUC 0.6884 indicates useful but moderate discrimination.

### Interpretation

- The model is a screening aid, not an operational decision system.
- Class weighting makes the model more sensitive to the minority delayed class.
- The random split tests generalization to similar flights, not to future dates.
- Temporal validation, calibration, cost-sensitive threshold selection, and
  external variables (weather, airport congestion, crew, maintenance) are needed
  before deployment.

## Reproducibility

| Artifact | Location |
|---|---|
| Long-form advanced results | `../analytical_results/advanced_analysis_results.csv` |
| Model metrics | `../analytical_results/model_metrics.csv` |
| Confusion matrix | `../analytical_results/confusion_matrix.csv` |
| Sensitivity | `../analytical_results/delay_sensitivity.csv` |
| Correlations | `../analytical_results/volume_delay_correlations.csv` |
| Risk bands | `../analytical_results/delay_risk_distribution.csv` |
| Model evaluation graph | `../graphs/10_model_evaluation.png` |
| Risk distribution graph | `../graphs/11_delay_risk_distribution.png` |
| Machine-readable metrics | `../execution_logs/metrics.json` |
