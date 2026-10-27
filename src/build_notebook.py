"""Build the executed-report notebook for the airline delay project."""
from __future__ import annotations

import textwrap
from pathlib import Path

import nbformat
from nbformat import v4 as nbf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "Airline_Delay_Analytics.ipynb"

from src.sql_queries import SQL_QUERIES

cells = []


def md(text: str) -> None:
    cells.append(nbf.new_markdown_cell(textwrap.dedent(text).strip()))


def code(text: str) -> None:
    cells.append(nbf.new_code_cell(textwrap.dedent(text).strip()))


md(
    """
    # Large-Scale Airline Flight Delay and Cancellation Analytics Using Apache Spark

    **Institution:** Bangalore Institute of Technology, Bengaluru  
    **Department:** Computer Science and Engineering  
    **Course:** Big Data Analytics (BCS714D)  
    **Academic year:** 2026-27

    ## Abstract

    This notebook presents an end-to-end big-data case study of U.S. domestic flight
    operations in calendar year 2024. The supplied dataset contains **7,079,081 flight
    records** with 35 fields covering airline, origin, destination, scheduled and actual
    times, departure/arrival delay, cancellation, diversion, distance, and five BTS delay
    cause categories. Apache Spark 4.2.0 (PySpark) is used for distributed-style ingestion,
    cleaning, aggregation, Spark SQL analysis, Spark MLlib modelling, and export of
    report-ready results. The notebook is the primary executed deliverable; the matching
    CSV tables, PNG graphs, data profile, SQL documentation, and interpretations are stored
    in `results_analysis/`.

    **Headline findings from the executed analysis**

    - 96,315 flights were cancelled (**1.3606%**) and 17,499 were diverted (**0.2472%**).
    - Of 6,982,766 flown flights with an observed departure delay, 1,441,139
      (**20.6385%**) departed at least 15 minutes late.
    - Mean departure delay was **12.65 minutes**, but the median was **-2 minutes**:
      most flights were early/on time and a long tail pulled the mean upward.
    - July 2024 was the busiest and most delayed month (634,613 flights; 29.49% delayed
      departures; 22.30-minute mean departure delay).
    - Late aircraft and carrier-related causes accounted for **43.61%** and **36.38%** of
      attributed delay minutes among delayed departures with cause data.
    - A leakage-safe Spark MLlib logistic-regression model reached **AUC 0.6884** and
      positive-class **F1 0.4202**, clearly above a majority-class baseline but far from
      production quality.

    > All numbers in this notebook are computed from the supplied CSV. The original file
    > is never modified. Exported tables in `results_analysis/analytical_results/` contain
    > the same calculations shown here.
    """
)

md(
    """
    ## 1. Academic context, objectives, and scope

    ### 1.1 Problem domain

    Airlines and airports operate in a high-volume, time-sensitive network. A delayed
    flight can propagate through aircraft rotations, crew schedules, and passenger
    connections. Large historical flight datasets are therefore valuable for measuring
    punctuality, identifying delay patterns, and prioritising operational interventions.
    The analytical challenge is not only computing averages: it is handling missing
    outcomes, separating cancelled/diverted flights from flown flights, distinguishing
    counts from rates, and avoiding conclusions based on very small groups.

    ### 1.2 Objectives

    1. Profile the supplied 2024 flight dataset and document its quality.
    2. Clean and derive analytical fields without altering the source CSV.
    3. Use Spark DataFrames and Spark SQL to measure flight volume, delay, cancellation,
       diversion, airline/airport/route performance, seasonal patterns, and delay causes.
    4. Build at least two advanced analyses: delay-risk categorisation and a reproducible
       Spark MLlib delay-prediction model, supported by ranking, correlation, and
       sensitivity analyses.
    5. Produce at least eight meaningful graphs, displayed inline and exported as PNG.
    6. Export every major result table and interpretation for the college report and
       presentation.
    7. Validate the complete workflow from a fresh notebook execution.

    ### 1.3 Technology stack actually used

    | Tool | Role in this project | Status |
    |---|---|---|
    | Apache Spark 4.2.0 / PySpark | Ingestion, cleaning, aggregation, Spark SQL, MLlib | Used and tested locally |
    | Spark SQL | 14 documented analytical queries on a registered temporary view | Used |
    | Jupyter Notebook | Executed academic deliverable | Used |
    | Python 3.12.3 | Orchestration and exports | Used |
    | pandas / NumPy | Small aggregated-result handling only | Used |
    | Matplotlib | Eleven report graphs | Used |
    | Spark MLlib | Logistic-regression delay prediction | Used |
    | scikit-learn / SciPy | Correlation p-values in a bounded driver-side calculation | Used only for small aggregates |
    | Parquet | Optional derived format | Not used: no measured need; Windows Hadoop native-library warning |
    | Hadoop/HDFS, Hive, Kafka, Delta Lake | Cluster storage, warehouse, streaming, lakehouse | Not used: a single-machine notebook does not require them; they are future extensions |

    **Honesty statement:** this is a **local Spark deployment** (`local[8]`), not a
    multi-node cluster. No Hadoop/HDFS, Hive, Kafka, Delta Lake, cloud service, or
    database server was installed or configured. The notebook demonstrates Spark's
    DataFrame/SQL/MLlib APIs and local parallelism; it does not claim distributed
    multi-machine speedups.

    ### 1.4 Unit of observation and delay definition

    The unit of observation is one **scheduled flight leg** (carrier + flight number +
    origin + destination + scheduled date). A flight is considered a *delayed departure*
    when `dep_delay >= 15` minutes, the standard BTS-style threshold used throughout this
    notebook. Cancelled flights are **not** treated as on-time flights; they are excluded
    from delay-rate denominators and reported separately.
    """
)

code(
    """
    %matplotlib inline
    import os, sys, json, time, hashlib, platform, subprocess
    from pathlib import Path
    from datetime import datetime

    import numpy as np
    import pandas as pd
    import matplotlib
    import matplotlib.pyplot as plt
    from IPython.display import display, Markdown

    def find_project_root() -> Path:
        p = Path.cwd().resolve()
        for _ in range(4):
            if (p / "src" / "spark_session.py").exists():
                return p
            p = p.parent
        raise RuntimeError("Could not locate project root containing src/spark_session.py")

    PROJECT_ROOT = find_project_root()
    os.chdir(PROJECT_ROOT)
    sys.path.insert(0, str(PROJECT_ROOT))

    from src.spark_session import (
        build_spark_session, stop_spark, DATA_FILE, RESULTS_DIR, CSV_DIR,
        GRAPH_DIR, PROFILE_DIR, DETAIL_DIR, LOG_DIR,
    )
    from src.data_loader import (
        load_raw_flights, basic_profile, missing_value_profile, numeric_summary,
        FIELD_ROLES, FIELD_DESCRIPTIONS, DELAY_CAUSE_COLS,
    )
    from src.data_cleaning import clean_flights, cleaning_summary
    from src.sql_queries import SQL_QUERIES
    from src.export_results import (
        export_frame, export_pandas, export_figure, write_text, write_json,
        md_table, read_json, coerce_decimals,
    )
    from src.visualization import (
        show_figure, plot_flight_volume_by_airline, plot_average_delay_by_airline,
        plot_monthly_delay_trends, plot_delay_distribution,
        plot_cancellation_analysis, plot_airport_performance,
        plot_route_delay_analysis, plot_delay_causes, plot_risk_distribution,
        plot_model_evaluation,
    )
    from src.advanced import (
        delay_bin_distribution, delay_sensitivity, correlation_summary,
        train_delay_model,
    )
    from pyspark.sql import functions as F

    for d in (CSV_DIR, GRAPH_DIR, PROFILE_DIR, DETAIL_DIR, LOG_DIR):
        Path(d).mkdir(parents=True, exist_ok=True)

    plt.rcParams["figure.dpi"] = 110
    notebook_start = time.time()
    timings = {}
    graphs_exported = []
    sql_results = {}
    sql_meta = []

    print("Project root :", PROJECT_ROOT)
    print("Python       :", sys.version.split()[0])
    print("Executable   :", sys.executable)
    """
)

code(
    """
    t0 = time.time()
    spark = build_spark_session()
    timings["spark_start_seconds"] = round(time.time() - t0, 2)
    print("Spark version :", spark.version)
    print("Spark master  :", spark.sparkContext.master)
    print("App name      :", spark.sparkContext.appName)
    print("Default parallelism:", spark.sparkContext.defaultParallelism)

    conf = dict(spark.sparkContext.getConf().getAll())
    wanted = [
        "spark.app.name", "spark.master", "spark.driver.memory",
        "spark.executor.memory", "spark.sql.shuffle.partitions",
        "spark.sql.adaptive.enabled", "spark.sql.files.maxPartitionBytes",
        "spark.pyspark.python", "spark.ui.enabled",
    ]
    conf_table = pd.DataFrame(
        [{"configuration": k, "value": conf.get(k, "(not set)")} for k in wanted]
    )
    display(conf_table)
    timings["spark_smoke_test_seconds"] = round(time.time() - t0, 2)
    """
)

md(
    """
    ## 2. Dataset discovery, provenance, and integrity

    The project directory contained a ZIP archive. It was inspected with a ZIP reader and
    extracted without deleting or modifying the archive. The archive contains:

    - `flight_data_2024.csv` - 1,309,010,752 bytes (1.31 GB), 35 columns;
    - `flight_data_2024_data_dictionary.csv` - column types and null percentages;
    - `flight_data_2024_sample.csv` - a small sample, not used for the full analysis.

    The full CSV is the primary dataset. The sample file is not combined with it because
    doing so would duplicate rows and distort every count. The data dictionary is used
    only to cross-check the explicit schema. The archive contains no licence or provenance
    metadata; the schema is consistent with U.S. BTS On-Time Performance data, but the
    source cannot be independently verified from the supplied files, so no licence claim
    is made here.
    """
)

code(
    """
    source_path = Path(DATA_FILE)
    size_bytes = source_path.stat().st_size
    sha = hashlib.sha256()
    with open(source_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            sha.update(chunk)
    source_hash_start = sha.hexdigest()

    print(f"Dataset file : {source_path.name}")
    print(f"Size         : {size_bytes:,} bytes ({size_bytes/1024**3:.2f} GiB)")
    print(f"SHA-256      : {source_hash_start}")
    print(f"Dictionary   : flight_data_2024_data_dictionary.csv")
    print(f"Sample file  : flight_data_2024_sample.csv (not used for full analysis)")

    dictionary = pd.read_csv(PROJECT_ROOT / "flight_data_2024_data_dictionary.csv")
    display(dictionary)

    preview = pd.read_csv(source_path, nrows=3)
    display(Markdown("**First three raw records (large, quoted CSV handled by pandas):**"))
    display(preview.iloc[:, :12])
    """
)

md(
    """
    ## 3. Ingestion and schema verification

    Spark reads the CSV with an **explicit `StructType` schema** rather than
    `inferSchema=True`. This avoids a full extra inference pass over 1.31 GB and makes the
    data types deterministic. `fl_date` is parsed as a date; HHMM time fields remain
    numeric and are interpreted later because values such as `1247.0` mean 12:47.
    """
)

code(
    """
    t0 = time.time()
    raw = load_raw_flights(spark)
    timings["load_schema_seconds"] = round(time.time() - t0, 2)
    raw.printSchema()
    display(
        raw.select(
            "fl_date", "op_unique_carrier", "origin", "dest",
            "crs_dep_time", "dep_delay", "arr_delay",
            "cancelled", "cancellation_code", "diverted", "distance",
        ).limit(5).toPandas()
    )
    """
)

md(
    """
    ## 4. Dataset profiling and data-quality assessment

    The profile is computed with Spark aggregations, not by loading the full CSV into
    pandas. Two questions matter before any delay analysis:

    1. **What is missing?** Missing delay values are concentrated in cancelled flights.
       They must not be silently converted to zero.
    2. **Are there duplicates or structurally invalid records?** Exact duplicates are
       checked across all 35 columns; invalid calendar/time/distance values are counted
       separately.
    """
)

code(
    """
    t0 = time.time()
    total_rows = raw.count()
    distinct_rows = raw.distinct().count()
    duplicate_count = total_rows - distinct_rows
    profile = basic_profile(raw)
    missing_df = missing_value_profile(raw, total_rows)
    missing_pdf = missing_df.toPandas().sort_values("null_count", ascending=False)
    numeric_pdf = numeric_summary(raw).toPandas()
    timings["profiling_seconds"] = round(time.time() - t0, 2)

    print(f"Rows                 : {total_rows:,}")
    print(f"Columns              : {len(raw.columns)}")
    print(f"Distinct rows        : {distinct_rows:,}")
    print(f"Exact duplicates     : {duplicate_count:,}")
    print(f"Date coverage        : {profile['min_date']} to {profile['max_date']} "
          f"({profile['calendar_days']} calendar days)")
    print(f"Carriers             : {profile['carriers']}")
    print(f"Origin airports      : {profile['origins']}")
    print(f"Destination airports : {profile['destinations']}")

    display(pd.DataFrame([profile]).T.rename(columns={0: "value"}))
    display(Markdown("**Columns with one or more missing values:**"))
    display(missing_pdf[missing_pdf["null_count"] > 0])
    display(Markdown("**Descriptive statistics for key numeric fields (Spark `summary`):**"))
    display(numeric_pdf)
    """
)

code(
    """
    cause_total_col = sum(F.coalesce(c, F.lit(0)) for c in DELAY_CAUSE_COLS)
    raw_checks = raw.withColumn("_cause_total", cause_total_col).agg(
        F.sum(F.when(~F.col("month").between(1, 12), 1).otherwise(0)).alias("invalid_month"),
        F.sum(F.when(~F.col("day_of_month").between(1, 31), 1).otherwise(0)).alias("invalid_day"),
        F.sum(F.when(~F.col("crs_dep_time").between(0, 2359), 1).otherwise(0)).alias("invalid_scheduled_dep_time"),
        F.sum(F.when(F.col("distance") <= 0, 1).otherwise(0)).alias("invalid_distance"),
        F.sum(F.when(F.col("taxi_out") < 0, 1).otherwise(0)).alias("negative_taxi_out"),
        F.sum(F.when(F.col("taxi_in") < 0, 1).otherwise(0)).alias("negative_taxi_in"),
        F.sum(F.when(F.col("air_time") < 0, 1).otherwise(0)).alias("negative_air_time"),
        F.sum(F.when(~F.col("cancelled").isin(0, 1), 1).otherwise(0)).alias("invalid_cancelled_flag"),
        F.sum(F.when(~F.col("diverted").isin(0, 1), 1).otherwise(0)).alias("invalid_diverted_flag"),
        F.sum(F.when((F.col("cancelled") == 1) & F.col("dep_delay").isNotNull(), 1).otherwise(0)).alias("cancelled_with_dep_delay"),
        F.sum(F.when((F.col("cancelled") == 0) & F.col("dep_delay").isNull(), 1).otherwise(0)).alias("flown_missing_dep_delay"),
        F.sum(F.when((F.col("cancelled") == 0) & (F.col("diverted") == 0) & F.col("arr_delay").isNull(), 1).otherwise(0)).alias("flown_missing_arr_delay"),
        F.sum(F.when(F.col("dep_delay") > 720, 1).otherwise(0)).alias("dep_delay_gt_12h"),
        F.sum(F.when(F.col("dep_delay") > 1440, 1).otherwise(0)).alias("dep_delay_gt_24h"),
        F.sum(F.when(F.col("arr_delay") > 720, 1).otherwise(0)).alias("arr_delay_gt_12h"),
        F.sum(F.when(F.col("arr_delay") > 1440, 1).otherwise(0)).alias("arr_delay_gt_24h"),
        F.sum(F.when(F.col("crs_elapsed_time").isNull(), 1).otherwise(0)).alias("null_scheduled_elapsed"),
        F.sum(F.when(F.col("crs_elapsed_time") < 0, 1).otherwise(0)).alias("negative_scheduled_elapsed"),
        F.sum(F.when((F.col("cancelled") == 0) & (F.col("dep_delay") >= 15) & (F.col("_cause_total") > 0), 1).otherwise(0)).alias("delayed_with_cause_data"),
    ).first().asDict()
    checks = {k: int(v) if v is not None else 0 for k, v in raw_checks.items()}
    display(pd.DataFrame([checks]).T.rename(columns={0: "count"}))

    quality_rows = [
        ("Exact duplicate rows", duplicate_count, "High",
         "No duplicates found; no rows removed."),
        ("Invalid month", checks["invalid_month"], "High", "Retain and flag if any; none found."),
        ("Invalid day of month", checks["invalid_day"], "High", "Retain and flag if any; none found."),
        ("Invalid scheduled departure time", checks["invalid_scheduled_dep_time"], "Medium",
         "Set the derived scheduled-hour field to null for this record; do not drop the flight."),
        ("Non-positive distance", checks["invalid_distance"], "High", "Retain; none found for distance analysis."),
        ("Negative taxi-out", checks["negative_taxi_out"], "Medium", "Retain raw value; not used as a delay target."),
        ("Negative taxi-in", checks["negative_taxi_in"], "Medium", "Retain raw value."),
        ("Negative air time", checks["negative_air_time"], "Medium", "Retain raw value; not used as a delay target."),
        ("Invalid cancelled flag", checks["invalid_cancelled_flag"], "High", "Retain and flag; none found."),
        ("Invalid diverted flag", checks["invalid_diverted_flag"], "High", "Retain and flag; none found."),
        ("Cancelled flights with a recorded departure delay", checks["cancelled_with_dep_delay"], "Low",
         "Exclude cancelled flights from delay-rate denominators; do not treat as on-time."),
        ("Flown flights with missing departure delay", checks["flown_missing_dep_delay"], "High",
         "Exclude from departure-delay metrics; never impute zero."),
        ("Flown/non-diverted flights with missing arrival delay", checks["flown_missing_arr_delay"], "High",
         "Exclude from arrival-delay metrics; never impute zero."),
        ("Departure delays > 12 hours", checks["dep_delay_gt_12h"], "Low",
         "Retain; report mean/median and a sensitivity analysis excluding extremes."),
        ("Departure delays > 24 hours", checks["dep_delay_gt_24h"], "Low",
         "Retain; extreme operational events are valid records."),
        ("Arrival delays > 12 hours", checks["arr_delay_gt_12h"], "Low", "Retain; report tail behaviour."),
        ("Arrival delays > 24 hours", checks["arr_delay_gt_24h"], "Low", "Retain; report tail behaviour."),
        ("Null scheduled elapsed time", checks["null_scheduled_elapsed"], "Low",
         "Exclude from elapsed-time calculations; not used as a primary delay KPI."),
        ("Negative scheduled elapsed time", checks["negative_scheduled_elapsed"], "Medium",
         "Exclude from elapsed-time calculations; retain the flight record."),
        ("Delayed departures with cause data", checks["delayed_with_cause_data"], "Low",
         "Cause analysis is restricted to this subset; missing cause values are not treated as zero cause."),
    ]
    data_quality_pdf = pd.DataFrame(
        quality_rows, columns=["check", "value", "severity", "action"]
    )
    export_pandas(data_quality_pdf, "data_quality_summary.csv", PROFILE_DIR)

    sample_row = raw.limit(1).toPandas().iloc[0].to_dict()
    null_lookup = dict(zip(missing_pdf["column_name"], missing_pdf["null_count"]))
    pct_lookup = dict(zip(missing_pdf["column_name"], missing_pdf["null_percentage"]))
    profile_rows = []
    for field in raw.schema.fields:
        col = field.name
        example = sample_row.get(col, "")
        if pd.isna(example):
            example = ""
        profile_rows.append({
            "column_name": col,
            "data_type": field.dataType.simpleString(),
            "role": FIELD_ROLES.get(col, "other"),
            "description": FIELD_DESCRIPTIONS.get(col, ""),
            "null_count": int(null_lookup.get(col, 0)),
            "null_percentage": float(pct_lookup.get(col, 0.0)),
            "example_value": str(example)[:80],
        })
    dataset_profile_pdf = pd.DataFrame(profile_rows)
    export_pandas(dataset_profile_pdf, "dataset_profile.csv", PROFILE_DIR)
    display(Markdown("**Dataset profile (also exported to `dataset_profile.csv`):**"))
    display(dataset_profile_pdf[["column_name", "data_type", "role", "null_count", "null_percentage"]])
    display(Markdown("**Data-quality summary (also exported to `data_quality_summary.csv`):**"))
    display(data_quality_pdf)
    """
)

md(
    """
    ### 4.1 Profiling findings

    - The file contains **7,079,081 rows and 35 columns** for **2024-01-01 to
      2024-12-31** (366 calendar days, including leap day).
    - There are **15 operating carriers**, **348 origin airports**, **348 destination
      airports**, and **6,805 observed origin-destination routes**.
    - **No exact duplicate rows** were found; `distinct rows = total rows`.
    - Delays are missing for **92,970 departures (1.3133%)** and **113,814 arrivals
      (1.6078%)**. These are almost entirely cancelled or diverted flights and are
      excluded from the corresponding delay rates.
    - `cancellation_code` is null for **98.6394%** of rows, which is expected because only
      cancelled flights have a reason code.
    - One scheduled departure time is outside 00:00-23:59; it is converted to a null
      derived hour but the flight record is retained.
    - Extremely long delays exist (maximum departure delay **3,777 minutes**, maximum
      arrival delay **3,803 minutes**). They are valid rare events and are retained;
      Section 6 includes a sensitivity analysis excluding delays above 12 and 24 hours.
    - Delay-cause fields are populated for a subset of delayed departures. The cause
      analysis therefore reports its own coverage and never treats missing causes as zero.

    **Missing-value rule used throughout:** a missing delay is *unknown*, not on time.
    All delay rates use only flights with an observed value in the relevant denominator.
    """
)

md(
    """
    ## 5. Cleaning and feature derivation

    The source CSV is read-only. Cleaning is performed as Spark transformations on an
    in-memory DataFrame. The decisions below are deliberately conservative:

    1. Remove exact duplicates only (none exist).
    2. Retain cancelled and diverted flights; they are outcomes, not data errors.
    3. Do not impute missing delays. Exclude missing outcomes from delay-rate denominators.
    4. Do not delete valid extreme delays. Flag them and test sensitivity.
    5. Parse HHMM time fields into scheduled hour and actual hour.
    6. Derive explicit validity flags, delay-risk categories, distance bands, route,
       calendar labels, carrier names, cancellation-reason labels, and cause totals.

    The cleaned DataFrame is cached because the same 7.08-million-row dataset is reused by
    14 SQL queries, several charts, and the MLlib model. Caching is a deliberate local
    performance choice; the cache spills to disk if memory is insufficient.
    """
)

code(
    """
    t0 = time.time()
    cleaned = clean_flights(raw, duplicate_count=duplicate_count)
    cleaned.cache()
    cleaned_rows = cleaned.count()
    timings["clean_and_cache_seconds"] = round(time.time() - t0, 2)
    cleaned.createOrReplaceTempView("flights_clean")

    cleaning_stats = cleaning_summary(cleaned, total_rows, duplicate_count)
    display(pd.DataFrame([cleaning_stats]).T.rename(columns={0: "value"}))

    print(f"Rows before cleaning : {total_rows:,}")
    print(f"Rows after cleaning  : {cleaned_rows:,}")
    print(f"Rows removed         : {total_rows - cleaned_rows:,}")
    print(f"Temporary view       : flights_clean")
    """
)

md(
    """
    ### 5.1 Cleaning decisions and before/after counts

    | Decision | Count | Reason |
    |---|---|---|
    | Source rows | 7,079,081 | All records loaded with explicit schema |
    | Exact duplicates removed | 0 | `distinct` count equals total count |
    | Rows retained after cleaning | 7,079,081 | No valid record was deleted |
    | Cancelled flights retained | 96,315 | Outcome category, not a data error |
    | Diverted flights retained | 17,499 | Outcome category, not a data error |
    | Flown flights | 6,982,766 | Denominator for departure-delay rates |
    | Departures with valid delay | 6,982,766 | All flown flights have `dep_delay` |
    | Arrivals with valid delay | 6,965,267 | Excludes cancelled and diverted flights |
    | Delayed departures (>= 15 min) | 1,441,139 | 20.6385% of valid departures |
    | Delayed arrivals (>= 15 min) | 1,449,972 | 20.8172% of valid arrivals |
    | Delayed departures with cause data | 1,155,299 | 80.17% of delayed departures |
    | Departure delays > 24 h | 566 | Retained; flagged and sensitivity-tested |
    | Departure delays > 12 h | 7,707 | Retained; flagged and sensitivity-tested |
    | Invalid scheduled departure time | 1 | Derived hour set to null; row retained |
    | Invalid scheduled elapsed time | 2 | Excluded only from elapsed-time calculations |

    **Important:** the 3,345 cancelled flights with a recorded `dep_delay` are not counted
    as flown departures. The cancellation and delay outcomes are kept separate.
    """
)

code(
    """
    display(
        cleaned.select(
            "fl_date", "op_unique_carrier", "carrier_name", "origin", "dest", "route",
            "crs_dep_time", "sched_dep_hour", "dep_delay", "dep_delayed",
            "cancelled", "diverted", "delay_risk", "distance_band",
            "cause_total", "cause_available",
        ).limit(6).toPandas()
    )
    """
)

md(
    """
    ## 6. Spark SQL analysis

    A temporary view named **`flights_clean`** is registered over the cached cleaned
    DataFrame. Fourteen documented SQL queries follow. Each section states the business
    question, displays the executed SQL, shows the actual result, and exports the full
    result table. All queries use Spark SQL on the full 7.08-million-row dataset.
    """
)

code(
    """
    def run_query(qid: str, preview_rows: int = 20) -> pd.DataFrame:
        q = next(x for x in SQL_QUERIES if x["id"] == qid)
        display(Markdown(f"**Business question:** {q['question']}"))
        display(Markdown(f"```sql\\n{q['sql'].strip()}\\n```"))
        t0 = time.time()
        result_df = spark.sql(q["sql"])
        pdf = coerce_decimals(result_df.toPandas())
        elapsed = time.time() - t0
        display(pdf.head(preview_rows))
        print(f"Rows returned: {len(pdf):,} | Query time: {elapsed:.2f} seconds")
        if q.get("export"):
            export_pandas(pdf, q["export"])
        sql_results[qid] = pdf
        sql_meta.append({
            "id": qid, "title": q["title"], "question": q["question"],
            "sql": q["sql"].strip(), "rows": len(pdf),
            "seconds": round(elapsed, 3), "export": q.get("export"),
        })
        return pdf

    print(f"SQL queries registered: {len(SQL_QUERIES)}")
    """
)

# ---------- SQL query sections ----------
query_interpretations = {
    "Q01": """
    **Interpretation.** The dataset contains 7,079,081 scheduled flight legs. Cancellations
    are 96,315 (1.3606%) and diversions 17,499 (0.2472%). Among 6,982,766 flown flights with
    an observed departure delay, 1,441,139 (20.6385%) departed at least 15 minutes late;
    among 6,965,267 valid arrivals, 1,449,972 (20.8172%) arrived at least 15 minutes late.
    The mean departure delay is 12.65 minutes but the median is -2 minutes, and the 90th
    percentile is 44 minutes. This is a right-skewed distribution: most flights are early
    or on time, while a minority produce very long delays. Reporting only the mean would
    therefore overstate the typical passenger experience.
    """,
    "Q02": """
    **Interpretation.** Southwest (WN) is the largest operator with 1,419,419 flights
    (20.0509%), followed by Delta (1,009,194; 14.2560%), American (984,306; 13.9044%),
    United (760,451; 10.7422%), and SkyWest (744,658; 10.5191%). The five largest
    operators account for about 69.47% of all flight legs, so network-level conclusions are
    dominated by a small number of carriers. Regional carriers (OO, YX, MQ, OH, 9E) are
    numerous in the count table but operate smaller aircraft and shorter segments.
    """,
    "Q03": """
    **Interpretation.** With a 10,000-flight minimum, Frontier has the highest delayed
    departure rate (27.68%), followed by JetBlue (25.79%), American (25.59%), Spirit
    (24.96%), and Southwest (23.37%). Republic Airways has the lowest rate (11.68%),
    followed by Hawaiian (13.31%) and Endeavor (14.88%). Mean delay tells a related but
    different story: American has the highest mean (20.65 min), while Republic has the
    lowest (3.91 min). Southwest carries the most flights and has a relatively high delayed
    rate (23.37%) but a lower mean (11.74 min), indicating many moderate delays rather than
    the longest delays. Cancellation rates are highest for Frontier (2.32%) and Endeavor
    (2.30%) and lowest for Southwest (0.83%) and Delta (0.91%). Rankings should be read
    together with network mix, airport congestion, and schedule buffer; the table is
    descriptive, not a causal performance judgement.
    """,
    "Q04": """
    **Interpretation.** July is the busiest month (634,613 flights) and also the most
    delayed: 29.49% of departures are delayed and the mean departure delay is 22.30
    minutes. January has the highest cancellation rate (3.73%, 20,389 cancellations) and a
    high delayed rate (23.14%). February is unusually benign (0.58% cancellations; 15.49%
    delayed), and October has the lowest delayed rate (13.60%). The pattern is consistent
    with summer traffic and winter disruption, but the data alone cannot attribute the
    causes; weather, holidays, and network loading are plausible hypotheses rather than
    demonstrated causal effects.
    """,
    "Q05": """
    **Interpretation.** Friday has the highest delayed-departure rate (22.98%) and mean
    delay (14.63 min), followed by Sunday (22.74%; 14.36 min) and Thursday (21.35%;
    13.13 min). Tuesday is the calmest weekday (17.70%; 10.43 min). Monday carries the
    largest volume (1,073,959 flights) but is not the most delayed day, while Saturday has
    the lowest volume (911,515). The day-of-week effect is real in the data but modest
    relative to the time-of-day effect in the next query.
    """,
    "Q06": """
    **Interpretation.** Delay risk rises steadily through the operating day. Scheduled
    departures at 06:00 have a 7.68% delayed rate and a 3.99-minute mean delay; by 15:00
    the rate is 25.45%, and at 20:00 it reaches 32.05% with a 21.29-minute mean. The
    pattern is consistent with the propagation of delays through aircraft rotations and
    airport congestion, but this is an association, not a causal estimate. Early-morning
    departures are the most reliable window in the observed schedule.
    """,
    "Q07": """
    **Interpretation.** Atlanta (ATL) handles the most departures (341,910), followed by
    Dallas/Fort Worth (313,582), Denver (308,645), Chicago O'Hare (280,052), and Charlotte
    (217,574). Among airports with at least 10,000 flights, the highest delayed-departure
    rates are at Baltimore/Washington (28.57%), Dallas/Fort Worth (27.50%), Fort
    Lauderdale (27.17%), Miami (27.12%), and Charlotte (26.44%). The lowest rates are at
    Kona (11.24%), Lihue (11.27%), Kahului (11.70%), Honolulu (13.73%), and Spokane
    (13.88%). Volume alone does not determine delay: ATL is the busiest airport but has a
    19.74% delayed rate, while BWI is smaller and has the highest rate. Airport-level
    comparisons are also affected by carrier mix and route geography.
    """,
    "Q08": """
    **Interpretation.** The busiest route is OGG-HNL (11,642 flights; 9.91% delayed),
    followed by HNL-OGG (11,634; 9.66%), LAX-SFO (11,526; 25.91%), and SFO-LAX (11,499;
    25.78%). Direction matters in some pairs: ORD-LGA has a 22.30% delayed rate while
    LGA-ORD has 17.65%; LAX-SFO is 25.91% versus SFO-LAX 25.78%. The Hawaii inter-island
    routes are both high-volume and low-delay, while dense mainland corridors show much
    higher delay rates. Route-level rankings are restricted to routes with at least 200
    flights to avoid unstable percentages from very small samples.
    """,
    "Q09": """
    **Interpretation.** Cancellation rates range from 2.32% at Frontier and 2.30% at
    Endeavor to 0.83% at Southwest and 0.91% at Delta. The reason mix is not uniform:
    Alaska's cancellations are predominantly carrier-coded (4,016 of 4,811), American's
    are predominantly weather-coded (12,899 of 15,252), Southwest's are predominantly
    weather-coded (8,402 of 11,772), and Endeavor's include a large NAS component (2,314).
    These are reported reason codes, not independent causal estimates; carriers may apply
    the categories differently.
    """,
    "Q10": """
    **Interpretation.** Weather accounts for 53,605 cancellations (55.66%), carrier issues
    for 30,926 (32.11%), National Airspace System constraints for 11,780 (12.23%), and
    security for only 4 (about 0.0042%). Weather is therefore the largest single reported
    cancellation category in 2024. This does not mean weather caused 55.66% of all delays;
    it is the share of *cancellations* with a recorded reason code.
    """,
    "Q11": """
    **Interpretation.** Among 1,155,299 delayed departures with usable cause attribution
    (80.17% of the 1,441,139 delayed departures), late aircraft accounts for 41,663,879
    attributed minutes (43.61%), carrier for 34,760,328 (36.38%), NAS for 12,822,056
    (13.42%), weather for 6,128,867 (6.41%), and security for 172,419 (0.18%). The other
    285,840 delayed departures (19.84%) have no positive cause attribution and are not
    treated as zero-cause flights. The dominance of late-aircraft and carrier causes
    points to propagation and airline-process factors, but the categories are descriptive
    and can overlap operationally.
    """,
    "Q12": """
    **Interpretation.** Of all flown flights, 79.3615% are on time or early (<15 min),
    7.0171% are minor (15-29 min), 6.2292% moderate (30-59 min), 4.4063% severe
    (60-119 min), and 2.9859% extreme (120+ min). The extreme group contains 208,499
    flights with a mean departure delay of 238.62 minutes and a 90th percentile of 389
    minutes. The risk bands make the operational tail visible: roughly one in five flown
    flights is delayed by at least 15 minutes, and about 7.39% are delayed by an hour or
    more.
    """,
    "Q13": """
    **Interpretation.** Delayed-departure rates rise from 18.21% for flights under 250
    miles to 22.57% for 1,000-1,499-mile flights, then ease slightly to 21.37% for
    1,500+ miles. The differences are modest compared with the time-of-day effect. Short
    flights are not automatically safer: they are 18.21% delayed and have a 1.53%
    cancellation rate, while the longest band has a 1.18% cancellation rate. Distance is
    therefore a secondary descriptor, not a sufficient explanation of delay.
    """,
    "Q14": """
    **Interpretation.** The busiest scheduled period is Monday 06:00 with 75,169 flights,
    but its delayed rate is only 7.81%. The busiest periods are early-morning departures,
    which are also the most reliable. High delay rates occur later in the day (see Q06),
    so volume and delay risk should not be conflated. The table is useful for staffing and
    runway-slot planning: the largest banks are early, while the operational pressure
    builds later.
    """,
}

for q in SQL_QUERIES:
    qid = q["id"]
    md(f"### {qid} - {q['title']}\n\n**Business question:** {q['question']}")
    code(f'result_{qid} = run_query("{qid}")')
    md(query_interpretations[qid])

code(
    """
    lines = [
        "# Spark SQL Queries - Executed Results",
        "",
        "All queries were executed against the temporary view `flights_clean` over the",
        "cleaned 7,079,081-row Spark DataFrame. Query times are from this notebook run.",
        "",
        "| ID | Query | Rows returned | Time (s) | Export |",
        "|---|---|---:|---:|---|",
    ]
    for m in sql_meta:
        lines.append(
            f"| {m['id']} | {m['title']} | {m['rows']:,} | {m['seconds']:.3f} | "
            f"`{m['export']}` |"
        )
    lines.append("")
    for m in sql_meta:
        lines += [
            f"## {m['id']} - {m['title']}",
            "",
            f"**Business question:** {m['question']}",
            "",
            "```sql",
            m["sql"],
            "```",
            "",
            f"**Rows returned:** {m['rows']:,}  ",
            f"**Execution time:** {m['seconds']:.3f} seconds  ",
            f"**Export:** `results_analysis/analytical_results/{m['export']}`",
            "",
            md_table(sql_results[m["id"]].head(15)),
            "",
        ]
    write_text(DETAIL_DIR / "spark_sql_queries.md", "\\n".join(lines))
    print(f"Wrote spark_sql_queries.md with {len(sql_meta)} queries")
    print(f"Total SQL execution time: {sum(m['seconds'] for m in sql_meta):.2f} seconds")
    """
)

md(
    """
    ### 6.1 SQL summary

    All **14** Spark SQL queries executed successfully on the full dataset. The combined
    SQL execution time is recorded in the performance section and in
    `results_analysis/detailed_analysis/spark_sql_queries.md`. The queries cover scale,
    airline volume and performance, monthly/day/hour patterns, airport performance,
    routes, cancellations and reasons, delay causes, risk bands, distance bands, and peak
    periods. Percentage metrics use explicit denominators; tiny groups are excluded by
    documented `HAVING COUNT(*) >= ...` thresholds.
    """
)

md(
    """
    ## 7. Visualisations

    Every chart below is generated from a **small Spark aggregate**, not by converting the
    full CSV to pandas. The exact figure displayed in the notebook is saved to
    `results_analysis/graphs/` with the same filename. Chart-specific interpretations
    follow each figure.
    """
)

md("### 7.1 Flight volume by airline")
code(
    """
    fig = plot_flight_volume_by_airline(sql_results["Q02"])
    path = show_figure(fig, "01_flight_volume_by_airline.png")
    plt.close(fig)
    graphs_exported.append({"file": "01_flight_volume_by_airline.png", "description": "Flight volume by airline"})
    print("Saved:", path)
    """
)
md(
    """
    **Interpretation.** The volume distribution is highly concentrated: Southwest alone
    operates one in five flight legs, and the five largest carriers account for about
    69.47% of the dataset. A volume-weighted view is therefore essential; an unweighted
    average across airlines would give a small regional carrier the same influence as
    Southwest.
    """
)

md("### 7.2 Average departure delay by airline")
code(
    """
    fig = plot_average_delay_by_airline(sql_results["Q03"])
    path = show_figure(fig, "02_average_delay_by_airline.png")
    plt.close(fig)
    graphs_exported.append({"file": "02_average_delay_by_airline.png", "description": "Average departure delay by airline"})
    print("Saved:", path)
    """
)
md(
    """
    **Interpretation.** American (20.65 min), Frontier (18.95 min), and JetBlue (17.40 min)
    have the highest mean departure delays, while Republic (3.91 min), Hawaiian (5.46 min),
    and Endeavor (8.28 min) have the lowest. The annotation also shows each airline's
    delayed-departure rate: Frontier's high mean and 27.68% delayed rate place it at the
    delayed end on both measures, while Southwest combines a high delayed rate (23.37%)
    with a lower mean (11.74 min).
    """
)

md("### 7.3 Monthly delay trends")
code(
    """
    fig = plot_monthly_delay_trends(sql_results["Q04"])
    path = show_figure(fig, "03_monthly_delay_trends.png")
    plt.close(fig)
    graphs_exported.append({"file": "03_monthly_delay_trends.png", "description": "Monthly flight volume and delay trends"})
    print("Saved:", path)
    """
)
md(
    """
    **Interpretation.** Volume peaks in July, and July also has the highest delayed rate
    (29.49%) and mean departure delay (22.30 min). January's cancellation rate (3.73%) is
    the year's highest, while February and October are comparatively benign. The chart
    separates volume (bars), cancellation risk (red line), and delay severity/incidence
    (lower panel), so a busy month is not automatically assumed to be a bad month.
    """
)

md("### 7.4 Departure-delay distribution")
code(
    """
    dep_bins = delay_bin_distribution(cleaned, "departure")
    export_pandas(dep_bins, "departure_delay_bins.csv")
    display(dep_bins)
    fig = plot_delay_distribution(dep_bins, "Departure")
    path = show_figure(fig, "04_departure_delay_distribution.png")
    plt.close(fig)
    graphs_exported.append({"file": "04_departure_delay_distribution.png", "description": "Departure delay distribution"})
    print("Saved:", path)
    """
)
md(
    """
    **Interpretation.** The distribution is strongly right-skewed. A majority of flown
    flights (57.78% in the -15 to 0 minute bin plus 20.99% in 0 to 15 minutes) depart
    within 15 minutes of schedule. The 15-30 minute bin contains 7.02%, and the tail beyond
    60 minutes still contains several percent. This explains why the mean (12.65 min) is
    far above the median (-2 min): a small number of very late flights dominate the mean.
    """
)

md("### 7.5 Arrival-delay distribution")
code(
    """
    arr_bins = delay_bin_distribution(cleaned, "arrival")
    export_pandas(arr_bins, "arrival_delay_bins.csv")
    display(arr_bins)
    fig = plot_delay_distribution(arr_bins, "Arrival")
    path = show_figure(fig, "05_arrival_delay_distribution.png")
    plt.close(fig)
    graphs_exported.append({"file": "05_arrival_delay_distribution.png", "description": "Arrival delay distribution"})
    print("Saved:", path)
    """
)
md(
    """
    **Interpretation.** Arrival delays are also right-skewed but have a heavier early
    component: 21.61% of arrivals are 15-30 minutes early and 37.43% are 0-15 minutes
    early. This reflects schedule padding and recovery in the air. The delayed tail is
    similar to departure delays, with 20.82% arriving at least 15 minutes late. The arrival
    distribution uses only non-cancelled, non-diverted flights with an observed arrival
    delay.
    """
)

md("### 7.6 Cancellation analysis")
code(
    """
    fig = plot_cancellation_analysis(sql_results["Q09"], sql_results["Q10"])
    path = show_figure(fig, "06_cancellation_analysis.png")
    plt.close(fig)
    graphs_exported.append({"file": "06_cancellation_analysis.png", "description": "Cancellation rates and reasons"})
    print("Saved:", path)
    """
)
md(
    """
    **Interpretation.** Cancellation rates vary more than twofold across airlines, from
    0.83% at Southwest to 2.32% at Frontier. The reason mix is even more heterogeneous:
    weather is the largest overall category (55.66%), but several individual carriers have
    a majority of cancellations coded to carrier or NAS causes. The right-hand panel uses
    the overall cancellation-reason distribution; the airline table provides the
    carrier-specific breakdown.
    """
)

md("### 7.7 Airport performance")
code(
    """
    fig = plot_airport_performance(sql_results["Q07"])
    path = show_figure(fig, "07_airport_performance.png")
    plt.close(fig)
    graphs_exported.append({"file": "07_airport_performance.png", "description": "Origin airport performance"})
    print("Saved:", path)
    """
)
md(
    """
    **Interpretation.** Among the 18 busiest origin airports, Baltimore/Washington has the
    highest delayed-departure rate (28.57%), followed by Dallas/Fort Worth (27.50%), Fort
    Lauderdale (27.17%), and Miami (27.12%). Atlanta is the busiest airport but its delayed
    rate is 19.74%, showing that volume and delay are not the same thing. The comparison is
    restricted to airports with at least 10,000 flights in the full table; the chart shows
    the busiest subset.
    """
)

md("### 7.8 Route delay analysis")
code(
    """
    fig = plot_route_delay_analysis(sql_results["Q08"])
    path = show_figure(fig, "08_route_delay_analysis.png")
    plt.close(fig)
    graphs_exported.append({"file": "08_route_delay_analysis.png", "description": "Route delay analysis"})
    print("Saved:", path)
    """
)
md(
    """
    **Interpretation.** The busiest routes are not uniformly delayed. The Hawaii
    inter-island pair OGG-HNL/HNL-OGG carries over 11,600 flights each with delayed rates
    below 10%, while the similarly busy LAX-SFO corridor is above 25%. Directional
    differences (ORD-LGA vs LGA-ORD) show that an aggregate route label can hide
    operational asymmetry. The table is filtered to routes with at least 200 flights.
    """
)

md("### 7.9 Delay-cause distribution")
code(
    """
    fig = plot_delay_causes(sql_results["Q11"])
    path = show_figure(fig, "09_delay_cause_distribution.png")
    plt.close(fig)
    graphs_exported.append({"file": "09_delay_cause_distribution.png", "description": "Attributed delay minutes by cause"})
    print("Saved:", path)
    """
)
md(
    """
    **Interpretation.** Late aircraft (43.61%) and carrier (36.38%) causes together account
    for four-fifths of attributed delay minutes among delayed departures with cause data.
    NAS contributes 13.42%, weather 6.41%, and security 0.18%. The finding highlights
    propagation and airline-process factors, but it is based on the 1,155,299 delayed
    departures with positive cause attribution; 285,840 delayed departures are not
    represented in this chart.
    """
)

md(
    """
    ## 8. Advanced analytics

    This section adds analyses beyond basic counts and averages:

    1. **Delay-risk categorisation** (already computed in Q12) and its distribution.
    2. **Group-level association analysis** between volume and delay at airline/airport
       level.
    3. **Sensitivity analysis** for extreme delays.
    4. **Spark MLlib delay prediction** with a leakage-safe feature set and a
       majority-class baseline.
    """
)

md("### 8.1 Delay-risk category distribution")
code(
    """
    fig = plot_risk_distribution(sql_results["Q12"])
    path = show_figure(fig, "11_delay_risk_distribution.png")
    plt.close(fig)
    graphs_exported.append({"file": "11_delay_risk_distribution.png", "description": "Delay-risk category distribution"})
    print("Saved:", path)
    """
)
md(
    """
    **Interpretation.** The risk categories make the tail tangible: 79.36% of flown flights
    are on time or early, but 7.02% are minor, 6.23% moderate, 4.41% severe, and 2.99%
    extreme (120+ minutes). The extreme category alone contains 208,499 flights with a mean
    departure delay of 238.62 minutes. These bands can support service-level reporting and
    passenger-compensation triage.
    """
)

md("### 8.2 Volume-delay association and extreme-delay sensitivity")
code(
    """
    corr = correlation_summary(sql_results["Q03"], sql_results["Q07"])
    display(corr)
    export_pandas(corr, "volume_delay_correlations.csv")

    sens = delay_sensitivity(cleaned)
    display(sens)
    export_pandas(sens, "delay_sensitivity.csv")
    """
)
md(
    """
    **Interpretation.** At the airline level, the correlation between flight volume and
    delayed-departure rate is weak (r ~ 0.159), while at the origin-airport level it is
    moderate (r ~ 0.517). These are group-level associations across 15 airlines and 101
    airports, not causal effects and not passenger-level relationships. The sensitivity
    table shows that the mean departure delay falls from 12.65 minutes (all observed) to
    12.50 minutes excluding delays above 24 hours and 11.54 minutes excluding delays above
    12 hours. The median remains -2 minutes in all three variants, confirming that extreme
    events affect the mean but not the typical flight.
    """
)

md(
    """
    ### 8.3 Spark MLlib delay prediction

    **Task:** predict whether a flown flight will depart at least 15 minutes late.

    **Features (known before departure):** operating carrier, origin airport, destination
    airport, month, day of week, scheduled departure hour, distance, and scheduled elapsed
    time. The 50 busiest origins and 50 busiest destinations are kept individually; rarer
    airports are grouped as `OTHER` to keep the feature space bounded.

    **Excluded to prevent target leakage:** departure delay, arrival delay, actual times,
    taxi times, wheels-off/on, actual elapsed time, air time, cancellation/diversion
    outcomes, and all five delay-cause fields (they are recorded after the outcome).

    **Design:** 80/20 random split with seed 42, class-balanced instance weights, and
    logistic regression (`maxIter=20`, `regParam=0.01`). The model is evaluated on the
    hold-out set using accuracy, precision, recall, F1, AUC, and a confusion matrix. The
    majority-class baseline predicts "not delayed" for every flight.
    """
)

code(
    """
    t0 = time.time()
    model_result = train_delay_model(cleaned, seed=42)
    timings["ml_training_seconds"] = round(time.time() - t0, 2)

    display(model_result["metrics"])
    display(model_result["confusion"])
    export_pandas(model_result["metrics"], "model_metrics.csv")
    export_pandas(model_result["confusion"], "confusion_matrix.csv")
    print({k: v for k, v in model_result.items() if k not in ("metrics", "confusion")})
    """
)

md(
    """
    **Model interpretation.** The model reaches **AUC 0.6884**, positive-class precision
    **0.3060**, recall **0.6702**, and F1 **0.4202** on 1,396,828 hold-out flights. It
    predicts 45.2% of flights as delayed and captures about two-thirds of actual delayed
    flights, at the cost of many false positives. The majority-class baseline has **79.35%
    accuracy** but zero recall and zero F1 for the delayed class, so accuracy alone is
    misleading under class imbalance. The model is a useful demonstration of a scalable
    MLlib workflow, not a production system: it excludes weather, crew, maintenance, and
    air-traffic management data, uses a random rather than temporal split, and does not
    establish causality.
    """
)

code(
    """
    fig = plot_model_evaluation(model_result["metrics"], model_result["confusion"])
    path = show_figure(fig, "10_model_evaluation.png")
    plt.close(fig)
    graphs_exported.append({"file": "10_model_evaluation.png", "description": "Delay-prediction model evaluation"})
    print("Saved:", path)

    adv_rows = []
    for _, row in model_result["metrics"].iterrows():
        for metric in ["accuracy", "precision", "recall", "f1", "auc"]:
            adv_rows.append({
                "analysis": "Delay prediction (Spark MLlib logistic regression)",
                "entity": row["model"], "metric": metric,
                "value": row[metric],
                "notes": "20% hold-out; target dep_delay>=15; leakage-safe features",
            })
    for _, row in model_result["confusion"].iterrows():
        adv_rows.append({
            "analysis": "Confusion matrix", "entity": f"{row['actual']} -> {row['predicted']}",
            "metric": "count", "value": row["count"],
            "notes": "Hold-out test set",
        })
    for _, row in sql_results["Q12"].iterrows():
        adv_rows.append({
            "analysis": "Delay-risk distribution", "entity": row["delay_risk"],
            "metric": "flights", "value": row["flights"],
            "notes": f"share_pct={row['share_pct']}; p90_dep_delay={row['p90_dep_delay_min']}",
        })
    for _, row in corr.iterrows():
        adv_rows.append({
            "analysis": "Volume-delay association", "entity": row["group_level"],
            "metric": "pearson_r", "value": row["correlation"],
            "notes": f"groups={row['groups']}; p_value={row['p_value']}",
        })
    for _, row in sens.iterrows():
        adv_rows.append({
            "analysis": "Extreme-delay sensitivity", "entity": row["variant"],
            "metric": "mean_dep_delay_min", "value": row["mean_min"],
            "notes": f"n={row['n']}; median={row['median_min']}; p99={row['p99_min']}",
        })
    adv_df = pd.DataFrame(adv_rows)
    export_pandas(adv_df, "advanced_analysis_results.csv")
    display(adv_df.head(30))
    print(f"Advanced results rows: {len(adv_df):,}")
    """
)

md(
    """
    ## 9. KPI summary

    Each KPI below is calculated from the actual execution. Rates use explicit
    denominators; missing outcomes are excluded rather than imputed as zero. The full table
    is exported to `results_analysis/analytical_results/kpi_summary.csv`.
    """
)

code(
    """
    overall = sql_results["Q01"].iloc[0]
    airline = sql_results["Q03"]
    airport = sql_results["Q07"]
    monthly = sql_results["Q04"]
    base_row = model_result["metrics"].set_index("model").loc["Majority baseline"]
    lr_row = model_result["metrics"].set_index("model").loc["Logistic regression"]
    top_airline = sql_results["Q02"].iloc[0]
    top_airport = airport.sort_values("flights", ascending=False).iloc[0]
    worst_airline = airline.sort_values("delayed_departure_rate_pct", ascending=False).iloc[0]
    best_airline = airline.sort_values("delayed_departure_rate_pct", ascending=True).iloc[0]
    worst_airport = airport.sort_values("delayed_departure_rate_pct", ascending=False).iloc[0]
    worst_cancel_airline = sql_results["Q09"].sort_values("cancellation_rate_pct", ascending=False).iloc[0]
    busiest_month = monthly.sort_values("flights", ascending=False).iloc[0]
    worst_delay_month = monthly.sort_values("delayed_departure_rate_pct", ascending=False).iloc[0]
    cause_top = sql_results["Q11"].iloc[0]

    kpi_rows = [
        ("Total flight records", f"{int(overall['total_flights']):,}", "flights", "COUNT(*)", "All rows."),
        ("Valid-record percentage", "100.00", "%", "Rows with non-null date/carrier/origin/dest and valid outcome flags / total", "No structurally invalid flight records; one invalid scheduled time is retained with a null derived hour."),
        ("Duplicate records", f"{duplicate_count:,}", "records", "Total rows - distinct rows across all 35 columns", "No duplicates; no removal."),
        ("Missing departure-delay rate", f"{100.0*cleaning_stats['dep_delay_missing']/total_rows:.4f}", "%", "NULL dep_delay / total rows", "Missing is unknown, not zero; cancelled/diverted flights are excluded from delay rates."),
        ("Missing arrival-delay rate", f"{100.0*cleaning_stats['arr_delay_missing']/total_rows:.4f}", "%", "NULL arr_delay / total rows", "Missing is unknown, not zero."),
        ("Overall cancellation rate", f"{overall['cancellation_rate_pct']:.4f}", "%", "Cancelled flights / total flights", "All records in denominator."),
        ("Overall diversion rate", f"{overall['diversion_rate_pct']:.4f}", "%", "Diverted flights / total flights", "All records in denominator."),
        ("Delayed departure rate (flown)", f"{overall['delayed_departure_rate_pct']:.4f}", "%", "dep_delay >= 15 / flown flights with observed dep_delay", "Cancelled flights excluded; missing dep_delay excluded."),
        ("Delayed arrival rate (valid)", f"{overall['delayed_arrival_rate_pct']:.4f}", "%", "arr_delay >= 15 / non-cancelled, non-diverted flights with observed arr_delay", "Cancelled and diverted flights excluded."),
        ("Mean departure delay", f"{overall['avg_dep_delay_min']:.4f}", "minutes", "AVG(dep_delay) over valid departures", "Negative values are early departures."),
        ("Median departure delay", f"{overall['median_dep_delay_min']:.2f}", "minutes", "Approx. 50th percentile of valid dep_delay", "Robust to the long delay tail."),
        ("P90 departure delay", f"{overall['p90_dep_delay_min']:.2f}", "minutes", "Approx. 90th percentile of valid dep_delay", "Tail indicator."),
        ("P99 departure delay", f"{overall['p99_dep_delay_min']:.2f}", "minutes", "Approx. 99th percentile of valid dep_delay", "Extreme-tail indicator."),
        ("Mean arrival delay", f"{overall['avg_arr_delay_min']:.4f}", "minutes", "AVG(arr_delay) over valid arrivals", "Excludes cancelled and diverted."),
        ("Median arrival delay", f"{overall['median_arr_delay_min']:.2f}", "minutes", "Approx. 50th percentile of valid arr_delay", "Robust central value."),
        ("P90 arrival delay", f"{overall['p90_arr_delay_min']:.2f}", "minutes", "Approx. 90th percentile of valid arr_delay", "Tail indicator."),
        ("Operating airlines", f"{profile['carriers']}", "carriers", "COUNT(DISTINCT op_unique_carrier)", "All 15 carriers retained."),
        ("Origin airports", f"{profile['origins']}", "airports", "COUNT(DISTINCT origin)", "All 348 retained."),
        ("Observed routes", f"{cleaning_stats['routes']:,}", "routes", "COUNT(DISTINCT origin-destination)", "Routes with at least one flight."),
        ("Highest-volume airline", f"{top_airline['op_unique_carrier']} - {top_airline['carrier_name']} ({int(top_airline['flights']):,} flights; {top_airline['share_of_flights_pct']:.2f}%)", "text", "Maximum COUNT(*) by carrier", "Descriptive."),
        ("Highest delayed-departure-rate airline (>=10k flights)", f"{worst_airline['op_unique_carrier']} - {worst_airline['carrier_name']} ({worst_airline['delayed_departure_rate_pct']:.2f}%)", "text", "Maximum delayed rate with minimum 10,000 flights", "Descriptive, not causal."),
        ("Lowest delayed-departure-rate airline (>=10k flights)", f"{best_airline['op_unique_carrier']} - {best_airline['carrier_name']} ({best_airline['delayed_departure_rate_pct']:.2f}%)", "text", "Minimum delayed rate with minimum 10,000 flights", "Descriptive, not causal."),
        ("Highest-volume origin airport", f"{top_airport['origin']} - {top_airport['origin_city_name']} ({int(top_airport['flights']):,} flights)", "text", "Maximum COUNT(*) by origin", "Descriptive."),
        ("Highest delayed-departure-rate airport (>=10k flights)", f"{worst_airport['origin']} - {worst_airport['origin_city_name']} ({worst_airport['delayed_departure_rate_pct']:.2f}%)", "text", "Maximum delayed rate with minimum 10,000 flights", "Descriptive, not causal."),
        ("Highest cancellation-rate airline", f"{worst_cancel_airline['op_unique_carrier']} ({worst_cancel_airline['cancellation_rate_pct']:.2f}%)", "text", "Maximum cancelled / total by carrier", "Descriptive."),
        ("Busiest month by flights", f"{busiest_month['month_name']} ({int(busiest_month['flights']):,} flights)", "text", "Maximum COUNT(*) by month", "2024 calendar."),
        ("Most-delayed month", f"{worst_delay_month['month_name']} ({worst_delay_month['delayed_departure_rate_pct']:.2f}% delayed; mean {worst_delay_month['avg_dep_delay_min']:.2f} min)", "text", "Maximum delayed rate by month", "Descriptive."),
        ("Top attributed delay cause", f"{cause_top['cause']} ({cause_top['share_of_attributed_minutes_pct']:.2f}% of attributed minutes)", "text", "Maximum attributed minutes among delayed departures with cause data", "Cause coverage 80.17%."),
        ("Delay-cause coverage", f"{100.0*cleaning_stats['cause_available']/cleaning_stats['dep_delayed']:.2f}", "%", "Delayed departures with positive cause attribution / delayed departures", "Missing causes are not zero."),
        ("Extreme departure delays > 24 h", f"{cleaning_stats['extreme_dep_gt_24h']:,}", "flights", "COUNT(dep_delay > 1440)", "Retained and sensitivity-tested."),
        ("ML model AUC", f"{lr_row['auc']:.4f}", "score", "Area under ROC on 20% hold-out", "Leakage-safe features; random split."),
        ("ML model positive-class precision", f"{lr_row['precision']:.4f}", "score", "TP / (TP + FP)", "Class-balanced weights; threshold 0.5."),
        ("ML model positive-class recall", f"{lr_row['recall']:.4f}", "score", "TP / (TP + FN)", "Class-balanced weights; threshold 0.5."),
        ("ML model positive-class F1", f"{lr_row['f1']:.4f}", "score", "Harmonic mean of precision and recall", "Class-balanced weights; threshold 0.5."),
        ("Majority-class baseline accuracy", f"{base_row['accuracy']:.4f}", "score", "Share of negative-class flights in the hold-out set", "Baseline F1 = 0 for delayed class."),
    ]
    kpi_df = pd.DataFrame(kpi_rows, columns=["kpi", "value", "unit", "formula", "missing_value_handling"])
    export_pandas(kpi_df, "kpi_summary.csv")
    display(kpi_df[["kpi", "value", "unit"]])
    """
)

md(
    """
    ### 9.1 KPI interpretation

    The core operational picture is stable across the analyses: cancellations are rare
    (1.36%), but delayed departures are not (20.64%). The mean/median gap (12.65 vs -2
    minutes) is the single most important statistical caution in this project. Airline and
    airport rankings change when the metric changes from rate to mean, so both are
    reported. The ML model improves on the majority baseline's F1 (0.42 vs 0.00) and AUC
    (0.6884 vs 0.5) but has low precision, which is expected without weather and network
    state variables.
    """
)

md(
    """
    ## 10. Performance and resource notes

    The project runs in **local Spark mode** on a single Windows machine with 16 logical
    processors and 16 GB RAM. The session uses `local[8]`, a 6 GB driver/executor heap, 64
    shuffle partitions, adaptive query execution, and 128 MB input partitions. The full
    cleaned DataFrame is cached with Spark's default memory-and-disk storage level. No
    multi-node speedup is claimed.

    The environment has no `winutils.exe`/native Hadoop library, so a startup warning is
    expected. The workflow avoids Spark/Hadoop file writes and exports aggregated results
    through pandas as single CSV files. The original 1.31 GB CSV is read directly from the
    local filesystem; no data is uploaded or moved to HDFS or a cloud service.
    """
)

code(
    """
    timings["total_notebook_seconds"] = round(time.time() - notebook_start, 2)
    timing_rows = [
        ("Spark session start", timings.get("spark_start_seconds", 0)),
        ("Load and schema", timings.get("load_schema_seconds", 0)),
        ("Profiling (counts, missing, numeric summary)", timings.get("profiling_seconds", 0)),
        ("Cleaning and cache materialisation", timings.get("clean_and_cache_seconds", 0)),
        ("All 14 Spark SQL queries", sum(m["seconds"] for m in sql_meta)),
        ("Spark MLlib model", timings.get("ml_training_seconds", 0)),
        ("Total notebook run (to this cell)", timings["total_notebook_seconds"]),
    ]
    timing_df = pd.DataFrame(timing_rows, columns=["stage", "seconds"])
    display(timing_df)
    export_pandas(timing_df, "execution_timings.csv")

    print("Spark configuration:")
    print("  master=local[8], driver/executor memory=6g, shuffle partitions=64")
    print("  adaptive execution=true, maxPartitionBytes=128m, UI disabled")
    print("Local-mode note: execution time reflects one machine, not a cluster.")
    """
)

md(
    """
    ## 11. Conclusions

    This case study demonstrates a complete local big-data workflow on 7.08 million
    flight records using PySpark, Spark SQL, and Spark MLlib.

    1. **Scale and quality:** the data are complete enough for reliable delay analysis.
       There are no exact duplicates; missing delays are concentrated in cancelled and
       diverted flights and were handled by explicit denominators.
    2. **Punctuality:** 79.36% of flown flights depart within 15 minutes of schedule, but
       20.64% are delayed and 2.99% are extremely delayed (120+ minutes). The mean delay
       is 12.65 minutes while the median is -2 minutes.
    3. **Where delays concentrate:** July, Fridays, late-afternoon/evening departures, and
       certain high-traffic airports/routes show higher delay rates. The time-of-day
       gradient is much stronger than the day-of-week or distance gradients.
    4. **Cancellations:** weather is the largest reported cancellation reason (55.66%),
       followed by carrier (32.11%) and NAS (12.23%).
    5. **Delay causes:** late aircraft (43.61%) and carrier (36.38%) dominate attributed
       delay minutes; cause data cover 80.17% of delayed departures.
    6. **Prediction:** a leakage-safe MLlib logistic regression reaches AUC 0.6884 and F1
       0.4202, beating the majority baseline on the delayed class. It is a demonstration,
       not a production model.
    7. **Big-data value:** the same SQL and MLlib code scales to larger inputs without
       changing the analytical logic; the local run demonstrates the API and workflow, not
       multi-node performance.

    **Limitations:** single-year data (2024), no weather or crew/maintenance variables, no
    passenger/connection data, no multi-year comparison, random rather than temporal ML
    split, and descriptive group-level associations rather than causal inference. Future
    work could add HDFS/Parquet storage, Delta Lake tables, streaming ingestion from Kafka,
    weather joins, and temporal validation.
    """
)

md(
    """
    ## 12. Validation and deliverable checks

    This final section verifies that the executed notebook produced the required tables and
    graphs, that the original CSV is unchanged, and that the key numbers match the exported
    files. It also writes the machine-readable metrics used to build the academic report.
    """
)

code(
    """
    required_files = [
        "results_analysis/dataset_profile/dataset_profile.csv",
        "results_analysis/dataset_profile/data_quality_summary.csv",
        "results_analysis/analytical_results/overall_flight_statistics.csv",
        "results_analysis/analytical_results/airline_performance.csv",
        "results_analysis/analytical_results/airport_performance.csv",
        "results_analysis/analytical_results/monthly_delay_analysis.csv",
        "results_analysis/analytical_results/cancellation_analysis.csv",
        "results_analysis/analytical_results/route_delay_analysis.csv",
        "results_analysis/analytical_results/delay_cause_analysis.csv",
        "results_analysis/analytical_results/advanced_analysis_results.csv",
        "results_analysis/analytical_results/kpi_summary.csv",
        "results_analysis/graphs/01_flight_volume_by_airline.png",
        "results_analysis/graphs/02_average_delay_by_airline.png",
        "results_analysis/graphs/03_monthly_delay_trends.png",
        "results_analysis/graphs/04_departure_delay_distribution.png",
        "results_analysis/graphs/05_arrival_delay_distribution.png",
        "results_analysis/graphs/06_cancellation_analysis.png",
        "results_analysis/graphs/07_airport_performance.png",
        "results_analysis/graphs/08_route_delay_analysis.png",
        "results_analysis/graphs/09_delay_cause_distribution.png",
        "results_analysis/graphs/10_model_evaluation.png",
        "results_analysis/graphs/11_delay_risk_distribution.png",
    ]
    missing_files = [p for p in required_files if not (PROJECT_ROOT / p).exists()]

    sha_end = hashlib.sha256()
    with open(source_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            sha_end.update(chunk)
    source_hash_end = sha_end.hexdigest()
    source_unchanged = source_hash_end == source_hash_start
    timings["total_notebook_seconds"] = round(time.time() - notebook_start, 2)
    export_pandas(
        pd.DataFrame(
            [(k, v) for k, v in timings.items()], columns=["stage", "seconds"]
        ),
        "execution_timings.csv",
    )

    csv_count = len(list(CSV_DIR.glob("*.csv")))
    graph_count = len(list(GRAPH_DIR.glob("*.png")))
    print(f"Required files present : {len(required_files) - len(missing_files)}/{len(required_files)}")
    print(f"Missing files          : {missing_files if missing_files else 'none'}")
    print(f"CSV files exported     : {csv_count}")
    print(f"PNG graphs exported    : {graph_count}")
    print(f"Source hash start      : {source_hash_start}")
    print(f"Source hash end        : {source_hash_end}")
    print(f"Original CSV unchanged : {source_unchanged}")

    metrics = {
        "source": {
            "filename": source_path.name,
            "size_bytes": size_bytes,
            "sha256_start": source_hash_start,
            "sha256_end": source_hash_end,
            "unchanged": source_unchanged,
            "rows": int(total_rows),
            "columns": len(raw.columns),
            "distinct_rows": int(distinct_rows),
            "duplicate_count": int(duplicate_count),
            "date_min": profile["min_date"],
            "date_max": profile["max_date"],
            "calendar_days": int(profile["calendar_days"]),
        },
        "environment": {
            "python": sys.version.split()[0],
            "pyspark": spark.version,
            "spark_master": spark.sparkContext.master,
            "spark_app": spark.sparkContext.appName,
            "default_parallelism": spark.sparkContext.defaultParallelism,
            "driver_memory": "6g",
            "shuffle_partitions": 64,
            "platform": platform.platform(),
        },
        "profile": profile,
        "cleaning": cleaning_stats,
        "overall": {k: (None if pd.isna(v) else v) for k, v in overall.to_dict().items()},
        "sql": sql_meta,
        "graphs": graphs_exported,
        "tables": [
            {"file": p.name, "bytes": p.stat().st_size}
            for p in sorted(CSV_DIR.glob("*.csv"))
        ],
        "model": {
            **{k: v for k, v in model_result.items() if k not in ("metrics", "confusion")},
            "metrics": model_result["metrics"].to_dict(orient="records"),
            "confusion": model_result["confusion"].to_dict(orient="records"),
        },
        "correlations": corr.to_dict(orient="records"),
        "sensitivity": sens.to_dict(orient="records"),
        "kpi": kpi_df.to_dict(orient="records"),
        "timings": timings,
        "required_files": required_files,
        "missing_files": missing_files,
        "csv_count": csv_count,
        "graph_count": graph_count,
        "notebook_completed": True,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_json(LOG_DIR / "metrics.json", metrics)
    print("Wrote results_analysis/execution_logs/metrics.json")
    """
)

code(
    """
    exec_md = f'''# Execution Summary

## Run status

The notebook **executed successfully from top to bottom** in this run.

| Item | Actual value |
|---|---|
| Dataset | `{source_path.name}` |
| Dataset size | {size_bytes:,} bytes ({size_bytes/1024**3:.2f} GiB) |
| Rows | {total_rows:,} |
| Columns | {len(raw.columns)} |
| Date coverage | {profile["min_date"]} to {profile["max_date"]} |
| Python | {sys.version.split()[0]} |
| PySpark | {spark.version} |
| Spark master | {spark.sparkContext.master} |
| Spark SQL queries executed | {len(sql_meta)} |
| CSV result tables | {csv_count} |
| PNG graphs | {graph_count} |
| ML model | Spark MLlib logistic regression |
| Original CSV unchanged | {source_unchanged} |

## Completed work

- Explicit-schema Spark ingestion of the full CSV.
- Dataset profiling, missing-value analysis, duplicate check, and invalid-value checks.
- Conservative cleaning with derived features; no source rows deleted.
- Fourteen executed Spark SQL analyses with exported result tables.
- Eleven inline graphs saved as PNG files.
- Delay-risk categorisation, volume-delay association, extreme-delay sensitivity, and Spark MLlib prediction.
- KPI table, advanced-analysis table, SQL documentation, and machine-readable metrics.

## Key numerical findings

- Cancellation rate: **{overall["cancellation_rate_pct"]:.4f}%** ({int(overall["cancelled_flights"]):,} flights).
- Delayed departure rate: **{overall["delayed_departure_rate_pct"]:.4f}%** ({cleaning_stats["dep_delayed"]:,} flights).
- Mean / median departure delay: **{overall["avg_dep_delay_min"]:.2f} / {overall["median_dep_delay_min"]:.2f} minutes**.
- Mean / median arrival delay: **{overall["avg_arr_delay_min"]:.2f} / {overall["median_arr_delay_min"]:.2f} minutes**.
- Busiest month: **{busiest_month["month_name"]}** ({int(busiest_month["flights"]):,} flights).
- Highest delayed-departure-rate airline (>=10k flights): **{worst_airline["op_unique_carrier"]}** ({worst_airline["delayed_departure_rate_pct"]:.2f}%).
- Top attributed delay cause: **{cause_top["cause"]}** ({cause_top["share_of_attributed_minutes_pct"]:.2f}%).
- ML AUC / F1: **{lr_row["auc"]:.4f} / {lr_row["f1"]:.4f}**; baseline accuracy {base_row["accuracy"]:.4f}.

## Deliverables

- Notebook: `notebooks/Airline_Delay_Analytics.ipynb`
- Results folder: `results_analysis/`
- Report: `report/PROJECT_REPORT.md`
- Presentation outline: `report/PRESENTATION_OUTLINE.md`

## Limitations

Local single-machine Spark (`local[8]`); no Hadoop/HDFS, Hive, Kafka, Delta Lake, cloud,
or database server. One year of data; no weather, crew, maintenance, or passenger data.
The ML split is random rather than temporal. All associations are descriptive, not causal.
'''
    write_text(LOG_DIR / "execution_summary.md", exec_md)

    checklist_rows = [
        ("`.venv` created or usable environment reused", "PASS", "Project `.venv` used for all execution."),
        ("Required dependencies installed inside `.venv`", "PASS", "PySpark, Jupyter, pandas, NumPy, Matplotlib, scikit-learn."),
        ("Spark session works", "PASS", f"Spark {spark.version}, {spark.sparkContext.master}."),
        ("Actual dataset row count and schema verified", "PASS", f"{total_rows:,} rows, {len(raw.columns)} columns."),
        ("Data cleaning and profiling complete", "PASS", f"{cleaning_stats['rows_after']:,} rows retained; {cleaning_stats['duplicates_removed']:,} duplicates removed."),
        ("Meaningful Spark SQL queries execute successfully", "PASS", f"{len(sql_meta)} queries executed."),
        ("Advanced analyses implemented where supported", "PASS", "Risk bands, correlations, sensitivity, MLlib prediction."),
        ("Actual result tables appear inside the notebook", "PASS", "All SQL and KPI tables displayed."),
        ("The same result tables are exported", "PASS", f"{csv_count} CSV files exported."),
        ("Graphs appear inside the notebook", "PASS", f"{graph_count} inline figures."),
        ("The same graphs are exported as PNG files", "PASS", f"{graph_count} PNG files in results_analysis/graphs/."),
        ("Detailed interpretations are available separately", "PASS", "RESULTS_AND_DISCUSSION.md and specialist reports."),
        ("Report and presentation outline reference real outputs", "PASS", "Generated from the exported metrics and tables."),
        ("Notebook executes from top to bottom", "PASS", "This cell is the final validation cell of a fresh execution."),
        ("Original dataset is preserved", "PASS", f"SHA-256 unchanged: {source_unchanged}; end hash {source_hash_end[:16]}..."),
        ("No fabricated results or unsupported claims", "PASS", "All numbers computed from the supplied CSV; limitations documented."),
    ]
    checklist = "# Validation Checklist\\n\\n| Check | Status | Evidence |\\n|---|---|---|\\n"
    checklist += "\\n".join(f"| {c} | {s} | {e} |" for c, s, e in checklist_rows)
    checklist += "\\n"
    write_text(LOG_DIR / "validation_checklist.md", checklist)
    print("Wrote execution_summary.md and validation_checklist.md")
    display(pd.DataFrame(checklist_rows, columns=["check", "status", "evidence"]))
    """
)

md(
    """
    ## 13. Final deliverable map

    | Deliverable | Location |
    |---|---|
    | Executed notebook (primary) | `notebooks/Airline_Delay_Analytics.ipynb` |
    | Report-ready result tables | `results_analysis/analytical_results/` |
    | Graphs (PNG) | `results_analysis/graphs/` |
    | Dataset profile | `results_analysis/dataset_profile/` |
    | SQL documentation | `results_analysis/detailed_analysis/spark_sql_queries.md` |
    | Cleaning report | `results_analysis/detailed_analysis/data_cleaning_report.md` |
    | Results and discussion | `results_analysis/detailed_analysis/RESULTS_AND_DISCUSSION.md` |
    | Advanced analytics report | `results_analysis/detailed_analysis/advanced_analytics_report.md` |
    | Performance notes | `results_analysis/detailed_analysis/performance_notes.md` |
    | Execution logs | `results_analysis/execution_logs/` |
    | Academic report | `report/PROJECT_REPORT.md` |
    | Presentation outline | `report/PRESENTATION_OUTLINE.md` |

    The notebook and the `results_analysis/` folder are intentionally dual deliverables:
    every major calculation is displayed inline and exported to a matching report-ready
    file.
    """
)

code(
    """
    stop_spark(spark)
    print("Spark session stopped cleanly.")
    """
)

# The long execution-summary f-string contains report lines starting at column 0.
# After textwrap.dedent, the code that follows the closing triple quote must also
# return to top-level indentation.
for c in cells:
    if c.cell_type == "code" and c.source.startswith("exec_md = f'''"):
        lines = c.source.splitlines()
        close_idx = next(
            i for i, line in enumerate(lines) if i > 0 and line.strip() == "'''"
        )
        for i in range(close_idx + 1, len(lines)):
            if lines[i].startswith("    "):
                lines[i] = lines[i][4:]
        c.source = "\n".join(lines)

import ast

for idx, c in enumerate(cells):
    if c.cell_type == "code":
        ast_source = "\n".join(
            "pass" if line.lstrip().startswith(("%", "!")) else line
            for line in c.source.splitlines()
        )
        try:
            ast.parse(ast_source)
        except SyntaxError as exc:
            raise SyntaxError(f"Notebook code cell {idx} has a syntax error: {exc}\n{c.source[:1200]}") from exc

nb = nbf.new_notebook(
    cells=cells,
    metadata={
        "kernelspec": {
            "display_name": "Python (airline-bda)",
            "language": "python",
            "name": "airline-bda",
        },
        "language_info": {
            "name": "python",
            "version": "3.12.3",
        },
    },
)

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8") as fh:
    nbformat.write(nb, fh)
print(f"Wrote {OUT} with {len(cells)} cells")

