# Environment Audit

Audit date: 2026-10-27

## 1. Machine and operating system

| Item | Value |
|---|---|
| Platform | Windows 11 |
| Platform string | `Windows-11-10.0.26200-SP0` |
| Architecture | 64-bit |
| Shell used for execution | PowerShell 5.1 |
| Project root | `E:\BDA Project\bda` |
| Project virtual environment | `E:\BDA Project\bda\.venv` |
| Base Python | `C:\Program Files\Python312\python.exe` |
| Project Python | `E:\BDA Project\bda\.venv\Scripts\python.exe` |
| Java executable | `C:\Program Files\Common Files\Oracle\Java\javapath\java.exe` |

## 2. Runtime versions

| Component | Version |
|---|---|
| Python | 3.12.3 |
| PySpark | 4.2.0 |
| Java | 21.0.1 LTS (build 21.0.1+12-LTS-29) |
| pandas | 2.3.3 |
| NumPy | 2.5.4 |
| Matplotlib | 3.11.2 |
| scikit-learn | 1.9.1 |
| SciPy | 1.18.1 |
| Jupyter Core | 5.9.1 |
| Jupyter metapackage | 1.1.1 |
| ipykernel | 7.4.0 |
| nbconvert | 7.17.2 |
| nbformat | 5.11.1 |
| py4j | 0.10.9.9 |

The complete installed-package list is in `requirements-used.txt`.

## 3. Jupyter kernel

| Item | Value |
|---|---|
| Kernel name | `airline-bda` |
| Display name | Python (airline-bda) |
| Kernel location | `C:\Users\Akshaipnair\AppData\Roaming\jupyter\kernels\airline-bda` |
| Kernel Python | `E:\BDA Project\bda\.venv\Scripts\python.exe` |

Registered kernels:

```text
python3        E:\BDA Project\bda\.venv\share\jupyter\kernels\python3
airline-bda    C:\Users\Akshaipnair\AppData\Roaming\jupyter\kernels\airline-bda
```

## 4. Spark configuration

| Setting | Value |
|---|---|
| Application name | `AirlineDelayAnalytics2024` |
| Master | `local[8]` |
| Driver memory | 6 GB |
| Executor memory | 6 GB |
| Shuffle partitions | 64 |
| Adaptive query execution | Enabled |
| Adaptive partition coalescing | Enabled |
| Max partition bytes | 128 MB |
| Driver max result size | 512 MB |
| Spark UI | Disabled |
| Console progress | Disabled |
| Serializer | Kryo |
| Arrow | Disabled |
| ANSI mode | Disabled |
| Network timeout | 300 s |
| Log level | ERROR |

`PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` are pinned to the project `.venv`
Python in `src/spark_session.py`.

## 5. Data and integrity

| Item | Value |
|---|---|
| Source file | `flight_data_2024.csv` |
| Source size | 1,309,010,752 bytes (1.22 GiB) |
| Source rows | 7,079,081 |
| Source columns | 35 |
| Archive | `dataset.zip` |
| Archive size | 283,545,854 bytes |
| SHA-256 at notebook start | `9456ed0695855469cf4c07f8c0b2365a93339ae841b100d9612ea842090670c0` |
| SHA-256 at notebook end | `9456ed0695855469cf4c07f8c0b2365a93339ae841b100d9612ea842090670c0` |
| Source unchanged | Yes |

Independent post-run verification recomputed the same SHA-256. The CSV is read
only; all cleaning is applied to an in-memory Spark DataFrame.

## 6. Execution verification

| Check | Result |
|---|---|
| Notebook cells | 112 total; 42 code cells |
| Code cells executed | 42 / 42 |
| Cell errors | 0 |
| Error outputs | 0 |
| Inline figures | 11 |
| Result CSVs | 23 |
| PNG graphs | 11 |
| Spark SQL queries | 14 |
| Required files present | 22 / 22 required paths |
| Notebook end-to-end time | 206.75 s |
| Source hash unchanged | PASS |
| Validation checklist | 16 PASS items |

Execution command:

```powershell
.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace `
  --ExecutePreprocessor.kernel_name=airline-bda `
  --ExecutePreprocessor.timeout=7200 `
  notebooks\Airline_Delay_Analytics.ipynb
```

The final validation cell re-checks required output paths, counts CSV/PNG files,
writes `metrics.json`, `execution_summary.md`, and `validation_checklist.md`, and
confirms the source hash.

## 7. Warnings observed

| Message | Assessment |
|---|---|
| `Did not find winutils.exe` | Hadoop native Windows helper absent. Local CSV reads and Spark SQL completed successfully. |
| `Unable to load native-hadoop library` | Spark used its built-in Java implementation. No effect on results. |
| `Missing Python executable ... defaulting ...` | Spark launcher probe warning. The project `.venv` was pinned through `PYSPARK_PYTHON`; execution completed. |
| `netlib-blas: JNI_OnLoad ... libopenblas.dll` | Native BLAS probe warning from the local numeric stack. MLlib training completed. |
| `The process ... not found` at shutdown | Process-cleanup message after Spark stopped. Not an analysis failure. |
| ZMQ Proactor event-loop warning | Jupyter transport warning on Windows. The notebook completed. |
| TCP-without-encryption kernel warning | Local kernel transport warning. No remote kernel was used. |

None of these warnings produced an error cell or changed a result.

## 8. Environment changes

The following changes were made to support the project:

- Created the project virtual environment `.venv`.
- Installed project dependencies inside `.venv` only.
- Registered the user-level Jupyter kernel `airline-bda`.
- Created project output directories and files.

No global Python packages, system environment variables, Java installation, or
Windows settings were changed. No Hadoop, Hive, Kafka, Delta Lake, Docker,
database server, or cloud service was installed or used. Spark runs as a local
single-machine process.

## 9. Reproduction checks

```powershell
# Python and Spark versions
.\.venv\Scripts\python.exe -c "import sys, pyspark; print(sys.version); print(pyspark.__version__)"

# Java version
java -version

# Kernel list
.\.venv\Scripts\python.exe -m jupyter kernelspec list

# Source hash
Get-FileHash -Algorithm SHA256 -LiteralPath flight_data_2024.csv
```

The recorded SHA-256 must match
`9456ED0695855469CF4C07F8C0B2365A93339AE841B100D9612EA842090670C0`
(case-insensitive).

## 10. Related files

- `requirements-used.txt` — installed package versions.
- `results_analysis/execution_logs/metrics.json` — machine-readable run metrics.
- `results_analysis/execution_logs/execution_summary.md` — run summary.
- `results_analysis/execution_logs/validation_checklist.md` — validation evidence.
- `results_analysis/detailed_analysis/performance_notes.md` — runtime details.
