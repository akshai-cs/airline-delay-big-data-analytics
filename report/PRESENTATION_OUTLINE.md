# Presentation Outline

## 2024 Airline Delay and Cancellation Analytics

Suggested length: 12-15 minutes plus questions.

---

## Slide 1 - Title

**2024 Airline Delay and Cancellation Analytics**

A Spark-based study of 7.08 million flights

- Apache Spark 4.2.0 / PySpark
- Full 2024 BTS-format dataset
- Descriptive analytics + leakage-safe delay prediction

Speaker note: State that the source CSV was never modified and that the notebook
executed top to bottom with zero cell errors.

---

## Slide 2 - Why this matters

**Disruption is concentrated, not uniform**

- 7,079,081 flight records
- 96,315 cancellations (1.3606%)
- 1,441,139 delayed departures (20.6385%)
- Mean departure delay: 12.65 min
- Median: -2 min
- P99: 216 min

Key message: the average hides a long tail. The median flight is early, but the
tail is operationally expensive.

Visual: `results_analysis/graphs/04_departure_delay_distribution.png`

---

## Slide 3 - Data and method

**What was analyzed**

| Item | Value |
|---|---|
| Rows / columns | 7,079,081 / 35 |
| Date range | 2024-01-01 to 2024-12-31 |
| Carriers | 15 |
| Airports | 348 origins, 348 destinations |
| Routes | 6,805 |
| Duplicates | 0 |

**Pipeline**

Explicit-schema CSV read -> cleaning/flags -> cache -> 14 Spark SQL analyses -> 11
figures -> Spark MLlib -> validation.

Speaker note: No rows were deleted; missing delay is treated as unknown, not zero.

---

## Slide 4 - Overall delay profile

**Most flights are on time; the tail is heavy**

| KPI | Value |
|---|---:|
| Delayed departures (>= 15 min) | 20.6385% |
| Delayed arrivals (>= 15 min) | 20.8172% |
| Mean / median departure delay | 12.6451 / -2.00 min |
| P90 / P99 departure delay | 44 / 216 min |
| Mean / median arrival delay | 7.0982 / -6.00 min |

Visual: `results_analysis/graphs/05_arrival_delay_distribution.png`

Speaker note: Mean > median means right skew. Report both.

---

## Slide 5 - Airlines

**Delay rates differ materially**

- Highest delayed-departure rate (>=10k flights): **F9, 27.68%**
- Next: B6 25.79%, AA 25.59%, NK 24.96%, WN 23.37%
- Lowest: **YX 11.68%**, HA 13.31%, 9E 14.88%
- Highest / lowest ratio: **2.37x**
- WN carries the most flights: 1,419,419 (20.05%)

Visual: `results_analysis/graphs/02_average_delay_by_airline.png`

Speaker note: Descriptive ranking; network and scheduling are not controlled.

---

## Slide 6 - Monthly patterns

**July is the pressure point**

- Busiest month: **July, 634,613 flights**
- July delayed rate: **29.49%**
- July mean departure delay: **22.30 min**
- Least delayed month: **October, 13.60%**
- Highest cancellation rate: **January, 3.73%**
- Lowest cancellation rate: **November, 0.46%**

Visual: `results_analysis/graphs/03_monthly_delay_trends.png`

Speaker note: Weather is 55.66% of cancellations overall; January's peak is
consistent with winter disruption, but the data do not include flight-level
weather.

---

## Slide 7 - Time of day

**Delay risk builds through the day**

| Hour | Delayed rate | Mean delay |
|---:|---:|---:|
| 06:00 | 7.68% | 3.99 min |
| 12:00 | 19.58% | 11.43 min |
| 18:00 | 29.57% | 19.78 min |
| 20:00 | 32.05% | 21.29 min |

- 20:00 is about **4.2x** the 06:00 delayed rate.
- Late-night hours 0-4 have high rates but only 19,578 flights (0.28%).

Visual: `results_analysis/graphs/03_monthly_delay_trends.png` or a custom
hour-of-day chart from `departure_hour_analysis.csv`.

Speaker note: This is the clearest scheduling signal in the data.

---

## Slide 8 - Airports

**Volume and delay are not the same ranking**

| Airport | Flights | Delayed dep % |
|---|---:|---:|
| ATL | 341,910 | 19.74 |
| DFW | 313,582 | 27.50 |
| DEN | 308,645 | 23.17 |
| ORD | 280,052 | 22.15 |
| CLT | 217,574 | 26.44 |

- Highest delayed rate (>=10k): **BWI, 28.57%**
- Lowest: **KOA, 11.24%**
- Highest cancellation: **SRQ, 3.52%**

Visual: `results_analysis/graphs/07_airport_performance.png`

Speaker note: ATL handles the most flights but is not the most delayed; airport
context matters.

---

## Slide 9 - Routes and cancellations

**Route-level variation is large**

- Busiest: OGG-HNL, 11,642 flights, 9.91% delayed
- LAX-SFO: 11,526 flights, 25.91% delayed
- Highest delayed rate (>=500 flights): BDL-SJU, 44.55%
- Lowest: OGG-PHX, 3.99%
- Highest cancellation (>=500): ASE-IAH, 7.72%
- Aspen (ASE) routes dominate high-cancellation list

**Cancellation reasons**

| Reason | Share |
|---|---:|
| Weather | 55.66% |
| Carrier | 32.11% |
| National Airspace System | 12.23% |
| Security | <0.01% |

Visual: `results_analysis/graphs/08_route_delay_analysis.png` and
`06_cancellation_analysis.png`

Speaker note: Mountain-airport weather is a plausible explanation for ASE, but it
is not measured in this file.

---

## Slide 10 - Attributed delay minutes

**Late aircraft and carrier causes dominate**

| Cause | Share of attributed minutes |
|---|---:|
| Late Aircraft | 43.61% |
| Carrier | 36.38% |
| National Airspace System | 13.42% |
| Weather | 6.41% |
| Security | 0.18% |

- Cause coverage: **80.17%** of delayed departures
- 285,840 delayed departures have no positive cause attribution
- Late aircraft + carrier = **79.99%** of attributed minutes

Visual: `results_analysis/graphs/09_delay_cause_distribution.png`

Speaker note: Causes are BTS attributions, not independently verified causal
effects.

---

## Slide 11 - Delay-risk bands

**The severe and extreme bands carry the tail**

| Band | Flights | Share | Mean delay |
|---|---:|---:|---:|
| On-time / early (<15) | 5,541,627 | 79.36% | -2.87 min |
| Minor (15-29) | 489,989 | 7.02% | 21.12 min |
| Moderate (30-59) | 434,972 | 6.23% | 42.23 min |
| Severe (60-119) | 307,679 | 4.41% | 83.67 min |
| Extreme (120+) | 208,499 | 2.99% | 238.62 min |

- Severe + extreme: 516,178 flights (7.39%)
- Removing >24 h delays changes the mean from 12.6451 to 12.5042 min
- Median stays at -2 min

Visual: `results_analysis/graphs/11_delay_risk_distribution.png`

---

## Slide 12 - Prediction

**Useful screening, not deployment-ready**

| Model | Accuracy | Precision | Recall | F1 | AUC |
|---|---:|---:|---:|---:|---:|
| Majority baseline | 0.7935 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| Logistic regression | 0.6180 | 0.3060 | 0.6702 | 0.4202 | 0.6884 |

- 168 encoded features
- 80/20 random split; 5,585,937 train / 1,396,828 test
- Confusion matrix: TP 193,317; TN 669,962; FP 438,423; FN 95,126
- Predicts 45.2% of hold-out flights as delayed
- Baseline accuracy is misleading because it never predicts a delay

Visual: `results_analysis/graphs/10_model_evaluation.png`

Speaker note: Accuracy is lower than the baseline, but F1 and AUC show real
signal. A cost-sensitive threshold and temporal validation are needed.

---

## Slide 13 - Recommendations

**What to do with the findings**

1. Monitor the 16:00-22:00 bank for delay accumulation.
2. Prioritise airports/routes with both high volume and high delay.
3. Separate weather-cancellation planning from late-aircraft/carrier recovery.
4. Report cause coverage alongside cause shares.
5. Use the ML score as triage, not an automatic decision.
6. Add weather, crew, maintenance, and capacity data before causal claims.

---

## Slide 14 - Limitations

- One year of data (2024).
- No weather, crew, maintenance, passenger, or capacity variables.
- Causes are recorded attributions, not verified causal mechanisms.
- Random ML split, not temporal validation.
- Local single-machine Spark (`local[8]`, 6 GB); no cluster benchmark.
- 19.83% of delayed departures lack positive cause attribution.

---

## Slide 15 - Reproducibility and close

**Everything is in the project**

- Executed notebook: `notebooks/Airline_Delay_Analytics.ipynb`
- Results: `results_analysis/`
- Report: `report/PROJECT_REPORT.md`
- Environment: `ENVIRONMENT_AUDIT.md`
- Source hash unchanged:
  `9456ed0695855469cf4c07f8c0b2365a93339ae841b100d9612ea842090670c0`
- 42 code cells, 0 errors, 206.75 s end-to-end

**Closing message:** Most flights are on time, but the delay tail, evening
buildup, airport/route context, and cause mix are the actionable story.

---

## Backup slides (optional)

### Backup A - Query inventory

14 Spark SQL queries: overall KPIs, airline volume/performance, monthly, day,
hour, airports, routes, cancellations, reasons, causes, risk bands, distance
bands, peak periods.

### Backup B - Data quality

- 0 duplicate rows
- 1 invalid scheduled time
- 1 null + 1 negative scheduled elapsed time
- 3,345 cancelled flights with departure delay (excluded from delay rates)
- 92,970 missing departure delays; 113,814 missing arrival delays

### Backup C - Correlations and sensitivity

- Airline volume-delay r = 0.1594, p = 0.5705
- Airport volume-delay r = 0.5169, p < 0.0001 (reported 0.0000)
- Mean delay excluding >24 h: 12.5042 min
- Mean delay excluding >12 h: 11.5368 min
