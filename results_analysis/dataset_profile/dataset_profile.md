# Dataset Profile — `flight_data_2024.csv`

## Source and scale

| Item | Value |
|---|---|
| File | `flight_data_2024.csv` |
| Size | 1,309,010,752 bytes (1.22 GiB) |
| Rows | 7,079,081 |
| Columns | 35 |
| Date range | 2024-01-01 to 2024-12-31 |
| Calendar days represented | 366 |
| Exact duplicate rows | 0 |
| Distinct rows | 7,079,081 |
| Airline codes | 15 |
| Origin airports | 348 |
| Destination airports | 348 |
| Origin-destination routes | 6,805 |
| Cancellation reason codes | 4 |
| Cancelled flights | 96,315 (1.3606%) |
| Diverted flights | 17,499 (0.2472%) |
| SHA-256 | `9456ed0695855469cf4c07f8c0b2365a93339ae841b100d9612ea842090670c0` |

The file is an annual BTS-format airline on-time performance extract. The source
CSV was read with an explicit 35-field schema; it was never modified.

## Column profile

Null percentages are calculated over all 7,079,081 rows.

| Column | Type | Role | Nulls | Null % | Example | Meaning |
|---|---|---|---:|---:|---|---|
| `year` | int | date | 0 | 0.0000 | 2024 | Flight year |
| `month` | int | date | 0 | 0.0000 | 1 | Month number |
| `day_of_month` | int | date | 0 | 0.0000 | 1 | Day of month |
| `day_of_week` | int | date | 0 | 0.0000 | 1 | BTS day code, 1=Monday |
| `fl_date` | date | date | 0 | 0.0000 | 2024-01-01 | Scheduled flight date |
| `op_unique_carrier` | string | airline | 0 | 0.0000 | 9E | Operating carrier code |
| `op_carrier_fl_num` | double | identifier | 1 | 0.0000 | 4814.0 | Operating flight number |
| `origin` | string | airport | 0 | 0.0000 | JFK | Origin IATA code |
| `origin_city_name` | string | airport | 0 | 0.0000 | New York, NY | Origin city/state |
| `origin_state_nm` | string | airport | 0 | 0.0000 | New York | Origin state |
| `dest` | string | airport | 0 | 0.0000 | DTW | Destination IATA code |
| `dest_city_name` | string | airport | 0 | 0.0000 | Detroit, MI | Destination city/state |
| `dest_state_nm` | string | airport | 0 | 0.0000 | Michigan | Destination state |
| `crs_dep_time` | int | time | 0 | 0.0000 | 1252 | Scheduled local departure, HHMM |
| `dep_time` | double | time | 92,659 | 1.3089 | 1247.0 | Actual local departure, HHMM |
| `dep_delay` | double | delay | 92,970 | 1.3133 | -5.0 | Departure delay, minutes |
| `taxi_out` | double | operational | 95,734 | 1.3524 | 31.0 | Taxi-out minutes |
| `wheels_off` | double | time | 95,734 | 1.3524 | 1318.0 | Wheels-off local time, HHMM |
| `wheels_on` | double | time | 97,856 | 1.3823 | 1442.0 | Wheels-on local time, HHMM |
| `taxi_in` | double | operational | 97,856 | 1.3823 | 7.0 | Taxi-in minutes |
| `crs_arr_time` | int | time | 0 | 0.0000 | 1508 | Scheduled local arrival, HHMM |
| `arr_time` | double | time | 97,854 | 1.3823 | 1449.0 | Actual local arrival, HHMM |
| `arr_delay` | double | delay | 113,814 | 1.6078 | -19.0 | Arrival delay, minutes |
| `cancelled` | int | outcome | 0 | 0.0000 | 0 | Cancellation indicator |
| `cancellation_code` | string | outcome | 6,982,766 | 98.6394 | — | Reason code A/B/C/D if cancelled |
| `diverted` | int | outcome | 0 | 0.0000 | 0 | Diversion indicator |
| `crs_elapsed_time` | double | operational | 1 | 0.0000 | 136.0 | Scheduled elapsed minutes |
| `actual_elapsed_time` | double | operational | 113,814 | 1.6078 | 122.0 | Actual elapsed minutes |
| `air_time` | double | operational | 113,814 | 1.6078 | 84.0 | Time in air, minutes |
| `distance` | double | operational | 0 | 0.0000 | 509.0 | Great-circle distance, miles |
| `carrier_delay` | int | delay cause | 0 | 0.0000 | 0 | Carrier-attributed minutes |
| `weather_delay` | int | delay cause | 0 | 0.0000 | 0 | Weather-attributed minutes |
| `nas_delay` | int | delay cause | 0 | 0.0000 | 0 | National Airspace System minutes |
| `security_delay` | int | delay cause | 0 | 0.0000 | 0 | Security-attributed minutes |
| `late_aircraft_delay` | int | delay cause | 0 | 0.0000 | 0 | Late inbound aircraft minutes |

## Null semantics

- `dep_delay` is null for cancelled flights and for a small number of other
  records. It is **not** imputed as zero.
- `arr_delay` is null for cancelled and diverted flights and for a small number
  of other records. It is **not** imputed as zero.
- `cancellation_code` is null for every non-cancelled flight, which explains its
  98.6394% null rate. This is structural, not a data-quality defect.
- The five delay-cause columns are zero-filled in the source when attribution is
  unavailable. Positive attribution is therefore required before a record is
  counted as cause-available; zero is not automatically interpreted as "no
  cause".
- Time fields are local HHMM integers or numeric values. Scheduled-hour analysis
  derives the hour from `crs_dep_time`; one invalid value is retained with a null
  derived hour.

## Data-quality checks

| Check | Count / value | Severity | Action taken |
|---|---:|---|---|
| Exact duplicate rows | 0 | High | No rows removed |
| Invalid month | 0 | High | No action needed |
| Invalid day of month | 0 | High | No action needed |
| Invalid scheduled departure time | 1 | Medium | Derived hour set to null; record retained |
| Non-positive distance | 0 | High | No action needed |
| Negative taxi-out | 0 | Medium | Retained; not a delay target |
| Negative taxi-in | 0 | Medium | Retained; not a delay target |
| Negative air time | 0 | Medium | Retained; not a delay target |
| Invalid cancelled flag | 0 | High | No action needed |
| Invalid diverted flag | 0 | High | No action needed |
| Cancelled flights with recorded departure delay | 3,345 | Low | Excluded from delay-rate denominators |
| Flown flights with missing departure delay | 0 | High | Excluded from departure-delay metrics; not imputed |
| Flown/non-diverted flights with missing arrival delay | 0 | High | Excluded from arrival-delay metrics; not imputed |
| Departure delays > 12 hours | 7,707 | Low | Retained; sensitivity analysis reported |
| Departure delays > 24 hours | 566 | Low | Retained; sensitivity analysis reported |
| Arrival delays > 12 hours | 7,548 | Low | Retained; tail reported |
| Arrival delays > 24 hours | 567 | Low | Retained; tail reported |
| Null scheduled elapsed time | 1 | Low | Excluded from elapsed-time/model calculations |
| Negative scheduled elapsed time | 1 | Medium | Excluded from elapsed-time/model calculations |
| Delayed departures with cause data | 1,155,299 | Low | Cause analysis restricted to this subset |

## Derived-cardinality notes

- 15 operating carriers are retained; no carrier is dropped.
- 348 origin airports and 348 destination airports appear.
- 6,805 unique `origin-dest` routes appear at least once.
- The four cancellation reason codes map to Weather (B), Carrier (A),
  National Airspace System (C), and Security (D).
- The longest delay tail is retained because extreme operational events are valid
  flights. Their effect is quantified separately in
  `detailed_analysis/advanced_analytics_report.md`.

## Related outputs

- `dataset_profile.csv` — machine-readable 35-column profile.
- `data_quality_summary.csv` — machine-readable 20-check summary.
- `../detailed_analysis/data_cleaning_report.md` — cleaning rules and derived fields.
- `../execution_logs/metrics.json` — source hash, row counts, and summary metrics.
