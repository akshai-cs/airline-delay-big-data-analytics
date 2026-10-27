# Data Cleaning and Feature Derivation

## Principles

1. The source CSV is immutable. All changes are made to an in-memory Spark
   DataFrame; the file hash is checked again at the end of the notebook.
2. No flight row is deleted. Cancellations, diversions, invalid values, and
   extreme delays are retained and flagged or excluded only from the relevant
   denominator.
3. Missing delay values are treated as unknown, never as zero.
4. Cleaning is conservative and documented so that the raw operational record
   remains auditable.

## Cleaning summary

| Metric | Value |
|---|---:|
| Rows before | 7,079,081 |
| Rows after | 7,079,081 |
| Exact duplicates | 0 |
| Duplicates removed | 0 |
| Cancelled flights | 96,315 |
| Diverted flights | 17,499 |
| Flown (not cancelled) | 6,982,766 |
| Missing departure delay | 92,970 |
| Missing arrival delay | 113,814 |
| Valid departure-delay observations | 6,982,766 |
| Valid arrival-delay observations | 6,965,267 |
| Delayed departures (>= 15 min) | 1,441,139 |
| Delayed arrivals (>= 15 min) | 1,449,972 |
| Delayed departures with cause data | 1,155,299 |
| Delayed departures without cause data | 285,840 |
| Departure delays > 24 h | 566 |
| Departure delays > 12 h | 7,707 |
| Invalid scheduled departure time | 1 |
| Invalid scheduled elapsed time | 2 |
| Cancelled flights with recorded departure delay | 3,345 |
| Dates retained | 2024-01-01 to 2024-12-31 |
| Routes retained | 6,805 |

`Flown` is defined as `cancelled = 0`; it therefore includes diverted flights.
Arrival-delay validity additionally excludes diversions, producing
`6,982,766 - 17,499 = 6,965,267` valid arrival observations.

A further 3,345 cancelled flights have a recorded departure delay but are
excluded from the departure-delay denominator by the `cancelled = 0` validity
rule. Departure-delay records reconcile as
`6,982,766 valid + 92,970 null + 3,345 cancelled-with-delay = 7,079,081`.

## Derived fields

| Field | Definition | Purpose |
|---|---|---|
| `carrier_name` | Mapping from the 15 operating carrier codes to names | Readable airline labels |
| `cancellation_reason` | A=Carrier, B=Weather, C=National Airspace System, D=Security; otherwise "Not cancelled" | Cancellation analysis |
| `month_name` | January-December from `month` | Monthly reporting |
| `day_name` | Monday-Sunday from `day_of_week` | Day-of-week reporting |
| `route` | `origin` + "-" + `dest` | Route grouping |
| `sched_dep_hour` | Hour from valid `crs_dep_time`; null if outside 0-2359 | Hour-of-day analysis |
| `dep_hour` | Actual departure hour from valid `dep_time`, modulo 24 | Operational timing |
| `is_cancelled` | `cancelled` cast to int | KPI aggregation |
| `is_diverted` | `diverted` cast to int | KPI aggregation |
| `is_flown` | 1 when `cancelled = 0`, else 0 | Flight-outcome denominator |
| `dep_delay_valid` | `cancelled = 0` and `dep_delay` is not null | Departure-delay denominator |
| `arr_delay_valid` | `cancelled = 0`, `diverted = 0`, and `arr_delay` is not null | Arrival-delay denominator |
| `dep_delayed` | 1 when `dep_delay_valid` and delay >= 15 min; 0 when valid and below 15; null otherwise | 15-minute delay target |
| `arr_delayed` | 1 when `arr_delay_valid` and delay >= 15 min; 0 when valid and below 15; null otherwise | 15-minute arrival target |
| `delay_risk` | On-time/early (<15), Minor (15-29), Moderate (30-59), Severe (60-119), Extreme (120+) | Risk distribution |
| `distance_band` | `<250`, `250-499`, `500-999`, `1000-1499`, `1500+` miles | Distance comparison |
| `cause_total` | Sum of the five cause columns, treating null as 0 | Cause availability |
| `cause_available` | Valid departure delay >= 15 min and `cause_total > 0` | Cause-analysis subset |
| `extreme_dep_gt_24h` | 1 when `dep_delay > 1440` | Extreme-tail flag |
| `extreme_dep_gt_12h` | 1 when `dep_delay > 720` | Extreme-tail flag |
| `valid_sched_dep_time` | 1 when `crs_dep_time` is between 0 and 2359 | Time-validity flag |
| `valid_crs_elapsed` | 1 when `crs_elapsed_time > 0` | Model/time-validity flag |
| `quarter` | Calendar quarter from `fl_date` | Optional temporal grouping |

## Denominator rules

- Cancellation rate: cancelled / all records.
- Diversion rate: diverted / all records.
- Delayed-departure rate: delayed departures / flown records with observed
  departure delay.
- Delayed-arrival rate: delayed arrivals / non-cancelled, non-diverted records
  with observed arrival delay.
- Mean and percentile delay statistics: valid delay observations only.
- Cause shares: positive attributed minutes among delayed departures with cause
  data. Missing causes are not counted as zero.

This prevents cancelled or diverted flights from being interpreted as on-time
flights and prevents missing delay values from pulling averages toward zero.

## Invalid and extreme values

| Item | Treatment |
|---|---|
| 1 invalid `crs_dep_time` | Derived scheduled hour set to null; row retained |
| 1 null and 1 negative `crs_elapsed_time` | Excluded from elapsed-time calculations and model population |
| 3,345 cancelled flights with `dep_delay` | Excluded from departure-delay denominators |
| 566 departure delays > 24 h | Retained; mean/median reported with sensitivity analysis |
| 7,707 departure delays > 12 h | Retained; sensitivity analysis excludes valid extremes |
| 285,840 delayed departures without cause data | Excluded from cause-share denominators, retained in delay KPIs |

## Effect of extreme delays

| Variant | Flights | Mean departure delay (min) | Median (min) | P99 (min) |
|---|---:|---:|---:|---:|
| All observed delays | 6,982,766 | 12.6451 | -2.00 | 216 |
| Excluding > 24 h | 6,982,205 | 12.5042 | -2.00 | 215 |
| Excluding > 12 h | 6,975,091 | 11.5368 | -2.00 | 205 |

The mean falls by 0.14 minutes when delays above 24 hours are removed and by
1.11 minutes when delays above 12 hours are removed. The median is unchanged at
-2 minutes. Extreme delays therefore affect the mean and upper tail, but not the
central tendency.

## Validation

- The source SHA-256 is identical at notebook start and end:
  `9456ed0695855469cf4c07f8c0b2365a93339ae841b100d9612ea842090670c0`.
- Row count before and after cleaning is 7,079,081.
- Duplicate check across all 35 columns returns 0.
- The 20-check quality summary is exported as
  `../dataset_profile/data_quality_summary.csv`.
- The final validation cell re-checks the required output files and the source hash.

