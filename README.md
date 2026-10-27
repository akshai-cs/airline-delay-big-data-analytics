# 2024 Airline Delay Analytics

End-to-end Spark/PySpark analysis of 7,079,081 flight records from
`flight_data_2024.csv`. The project profiles and cleans the data, runs 14
Spark SQL analyses, produces 11 graphs, trains a leakage-safe Spark MLlib
logistic-regression model, and exports report-ready results.

## Quick start

Requirements:

- Windows with Java 21 (tested with 21.0.1)
- Python 3.12.3
- The project virtual environment in `.venv`

Run the executed notebook:

```powershell
.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace `
  --ExecutePreprocessor.kernel_name=airline-bda `
  --ExecutePreprocessor.timeout=7200 `
  notebooks\Airline_Delay_Analytics.ipynb
```

Open the notebook interactively:

```powershell
.\.venv\Scripts\python.exe -m jupyter notebook notebooks\Airline_Delay_Analytics.ipynb
```

The notebook expects `flight_data_2024.csv` in the project root. It writes all
outputs under `results_analysis/` and does not modify the source CSV.

## Key results

| KPI | Value |
|---|---:|
| Rows / columns | 7,079,081 / 35 |
| Date coverage | 2024-01-01 to 2024-12-31 |
| Cancelled | 96,315 (1.3606%) |
| Diverted | 17,499 (0.2472%) |
| Delayed departures (>= 15 min) | 1,441,139 (20.6385%) |
| Mean / median departure delay | 12.6451 / -2.00 min |
| P90 / P99 departure delay | 44 / 216 min |
| Mean / median arrival delay | 7.0982 / -6.00 min |
| Busiest month | July (634,613 flights) |
| Highest delayed-rate airline (>=10k) | F9 (27.68%) |
| Highest-volume origin | ATL (341,910 flights) |
| Top attributed delay cause | Late Aircraft (43.61%) |
| ML hold-out AUC / F1 | 0.6884 / 0.4202 |

## Project structure

```text
bda/
├── flight_data_2024.csv              # source data (unchanged)
├── flight_data_2024_sample.csv       # 10,000-row inspection sample
├── flight_data_2024_data_dictionary.csv # 35-column quick dictionary
├── dataset.zip                       # original archive
├── notebooks/
│   └── Airline_Delay_Analytics.ipynb # executed primary deliverable
├── src/
│   ├── spark_session.py              # local Spark configuration
│   ├── data_loader.py                # explicit schema and profiling
│   ├── data_cleaning.py              # derived fields and cleaning
│   ├── sql_queries.py                # 14 documented Spark SQL queries
│   ├── export_results.py             # CSV/PNG/text/JSON helpers
│   ├── visualization.py              # 11 Matplotlib figures
│   ├── advanced.py                   # risk bands, sensitivity, MLlib
│   └── build_notebook.py             # programmatic notebook builder
├── results_analysis/
│   ├── analytical_results/           # 23 CSV result tables
│   ├── graphs/                       # 11 PNG figures
│   ├── dataset_profile/              # schema and quality profile
│   ├── detailed_analysis/            # interpretation and performance notes
│   └── execution_logs/               # metrics and validation
├── report/
│   ├── PROJECT_REPORT.md             # full academic report
│   └── PRESENTATION_OUTLINE.md       # slide-by-slide outline
├── ENVIRONMENT_AUDIT.md              # environment and integrity audit
├── requirements-used.txt             # installed package versions
└── README.md
```

## Outputs

- `notebooks/Airline_Delay_Analytics.ipynb` — 112 cells, 42 code cells, executed
  from top to bottom with 0 errors.
- `results_analysis/README.md` — index of every result table and graph.
- `results_analysis/detailed_analysis/RESULTS_AND_DISCUSSION.md` — full
  interpretation.
- `results_analysis/execution_logs/validation_checklist.md` — 16 PASS checks.
- `report/PROJECT_REPORT.md` — academic report.
- `report/PRESENTATION_OUTLINE.md` — 15-slide presentation plan.

## Method summary

1. Read the 35-column CSV with an explicit Spark schema.
2. Profile nulls, invalid values, duplicates, dates, and cardinality.
3. Derive denominator flags, risk bands, distance bands, route labels, and
   time/quarter fields. No rows are deleted.
4. Cache the cleaned DataFrame and run 14 Spark SQL queries.
5. Export each query result to CSV and render 11 inline/PNG figures.
6. Train a Spark MLlib logistic-regression model using only pre-outcome
   features; evaluate on a 20% hold-out set.
7. Validate required files and the source SHA-256 in the notebook's final validation cell.

## Data-quality and interpretation notes

- Missing delay values are unknown, not zero.
- Cancelled flights are excluded from delay-rate denominators.
- Cause analysis is restricted to delayed departures with positive attributed
  minutes (80.17% coverage); missing causes are not treated as zero.
- Self-reported cause fields are attributions, not independently verified causal
  mechanisms.
- All associations are descriptive. The ML split is random, not temporal.
- The analysis is local single-machine Spark; no Hadoop, Hive, Kafka, Delta Lake,
  cloud, or database server is used.

## Environment

| Item | Value |
|---|---|
| Python | 3.12.3 |
| PySpark | 4.2.0 |
| Java | 21.0.1 |
| Pandas | 2.3.3 |
| NumPy | 2.5.4 |
| Matplotlib | 3.11.2 |
| scikit-learn | 1.9.1 |
| Spark master | `local[8]` |
| Driver / executor memory | 6 GB / 6 GB |

See `ENVIRONMENT_AUDIT.md` and `requirements-used.txt` for details.

## Integrity

`flight_data_2024.csv` is 1,309,010,752 bytes and 7,079,081 rows. Its SHA-256 is
checked before and after execution:

```text
9456ed0695855469cf4c07f8c0b2365a93339ae841b100d9612ea842090670c0
```
