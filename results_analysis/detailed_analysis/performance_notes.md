# Performance Notes

## Environment

| Item | Value |
|---|---|
| Platform | Windows 11 (build 10.0.26200) |
| Python | 3.12.3 (64-bit) |
| PySpark | 4.2.0 |
| Java | 21.0.1 LTS |
| Spark master | `local[8]` |
| Driver / executor memory | 6 GB / 6 GB |
| Shuffle partitions | 64 |
| Adaptive query execution | Enabled |
| Max partition bytes | 128 MB |
| Driver max result size | 512 MB |
| Serializer | Kryo |
| Spark UI | Disabled |
| Arrow | Disabled |
| Input | 1,309,010,752-byte CSV (1.22 GiB) |
| Output | 23 CSV tables and 11 PNG graphs |

Spark ran as a single local process; no cluster, Hadoop, Hive, Kafka, Delta Lake,
cloud service, or database server was used.

## End-to-end timing

| Stage | Seconds |
|---|---:|
| Spark session start | 5.46 |
| Spark smoke test | 5.50 |
| Explicit-schema load | 0.79 |
| Dataset profiling | 59.20 |
| Cleaning and caching | 24.68 |
| ML training/evaluation | 51.48 |
| **Total notebook** | **206.75** |

Profiling is the largest non-ML stage because it performs several full-dataset
scans: row count, distinct-row check, date range, cardinality, null profiling,
numeric summaries, and invalid-value checks. The cleaned DataFrame is cached
before the analytical queries.

## Query runtimes

Times are from the executed run and are measured around each Spark SQL action
plus result collection.

| Query | Rows returned | Seconds |
|---|---:|---:|
| Q01 Overall statistics | 1 | 5.602 |
| Q02 Airline volume | 15 | 0.821 |
| Q03 Airline performance | 15 | 4.829 |
| Q04 Monthly trends | 12 | 2.462 |
| Q05 Day of week | 7 | 0.621 |
| Q06 Scheduled hour | 24 | 0.562 |
| Q07 Origin airports | 101 | 10.685 |
| Q08 Routes | 4,744 | 8.305 |
| Q09 Cancellation by airline/reason | 15 | 0.882 |
| Q10 Cancellation reasons | 4 | 0.343 |
| Q11 Delay causes | 5 | 0.816 |
| Q12 Delay-risk bands | 5 | 1.630 |
| Q13 Distance bands | 5 | 0.560 |
| Q14 Peak periods | 15 | 0.753 |

The 14 query times sum to about 38.9 seconds; this is not additive with the stage
table because the queries are part of the overall notebook run and execute after
the profiling and caching stages.

## Why the timings are reasonable

- The dataset is 1.22 GiB and 7.08 million rows, which fits in the 6 GB local
  driver. No distributed shuffle-heavy join is required.
- All analyses are aggregate `GROUP BY` operations over a cached DataFrame.
- The largest result tables are bounded aggregates: 4,744 routes and 101 airports.
- Only aggregated results are collected to pandas; the full 7.08-million-row
  dataset is never collected to the driver.
- The ML model uses a bounded feature space: top 50 origins and destinations,
  with all others grouped as `OTHER`.
- `spark.sql.shuffle.partitions=64` is modest for eight cores and keeps small
  aggregates from creating excessive tasks.

## Window / execution warnings

The following warnings appeared in the console during execution and did not stop
the notebook:

| Message | Meaning / impact |
|---|---|
| `Did not find winutils.exe` | Hadoop native Windows helper is absent. Local CSV processing and Spark SQL completed normally. |
| `Unable to load native-hadoop library` | Spark used its built-in Java implementation. No effect on the results. |
| `Missing Python executable ... defaulting ...` | Spark's launcher probe warning. `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` were explicitly pinned to the project `.venv`; the notebook completed. |
| `netlib-blas: JNI_OnLoad ... libopenblas.dll` | Native BLAS probe warning from the local numeric stack. The logistic-regression pipeline completed. |
| `The process ... not found` at shutdown | Process-cleanup message after Spark stopped; not an analysis error. |

## Reproducibility and scaling

To reproduce on the same machine:

```powershell
.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace `
  --ExecutePreprocessor.kernel_name=airline-bda `
  --ExecutePreprocessor.timeout=7200 `
  notebooks\Airline_Delay_Analytics.ipynb
```

For larger inputs, the same code would need a cluster master, more shuffle
partitions, and a columnar intermediate format (for example Parquet) to avoid
re-reading the CSV. Those changes were intentionally not made here because the
task is a local, single-machine analysis and the source must remain unchanged.

