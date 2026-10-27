# Execution Summary

## Run status

The notebook **executed successfully from top to bottom** in this run.

| Item | Actual value |
|---|---|
| Dataset | `flight_data_2024.csv` |
| Dataset size | 1,309,010,752 bytes (1.22 GiB) |
| Rows | 7,079,081 |
| Columns | 35 |
| Date coverage | 2024-01-01 to 2024-12-31 |
| Python | 3.12.3 |
| PySpark | 4.2.0 |
| Spark master | local[8] |
| Spark SQL queries executed | 14 |
| CSV result tables | 23 |
| PNG graphs | 11 |
| ML model | Spark MLlib logistic regression |
| Original CSV unchanged | True |

## Completed work

- Explicit-schema Spark ingestion of the full CSV.
- Dataset profiling, missing-value analysis, duplicate check, and invalid-value checks.
- Conservative cleaning with derived features; no source rows deleted.
- Fourteen executed Spark SQL analyses with exported result tables.
- Eleven inline graphs saved as PNG files.
- Delay-risk categorisation, volume-delay association, extreme-delay sensitivity, and Spark MLlib prediction.
- KPI table, advanced-analysis table, SQL documentation, and machine-readable metrics.

## Key numerical findings

- Cancellation rate: **1.3606%** (96,315 flights).
- Delayed departure rate: **20.6385%** (1,441,139 flights).
- Mean / median departure delay: **12.65 / -2.00 minutes**.
- Mean / median arrival delay: **7.10 / -6.00 minutes**.
- Busiest month: **July** (634,613 flights).
- Highest delayed-departure-rate airline (>=10k flights): **F9** (27.68%).
- Top attributed delay cause: **Late Aircraft** (43.61%).
- ML AUC / F1: **0.6884 / 0.4202**; baseline accuracy 0.7935.

## Deliverables

- Notebook: `notebooks/Airline_Delay_Analytics.ipynb`
- Results folder: `results_analysis/`
- Report: `report/PROJECT_REPORT.md`
- Presentation outline: `report/PRESENTATION_OUTLINE.md`

## Limitations

Local single-machine Spark (`local[8]`); no Hadoop/HDFS, Hive, Kafka, Delta Lake, cloud,
or database server. One year of data; no weather, crew, maintenance, or passenger data.
The ML split is random rather than temporal. All associations are descriptive, not causal.
