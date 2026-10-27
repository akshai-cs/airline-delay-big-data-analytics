"""Dataset loading and profiling helpers for the 2024 BTS-style flight data."""
from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from .spark_session import DATA_FILE

FLIGHT_SCHEMA = StructType(
    [
        StructField("year", IntegerType(), True),
        StructField("month", IntegerType(), True),
        StructField("day_of_month", IntegerType(), True),
        StructField("day_of_week", IntegerType(), True),
        StructField("fl_date", DateType(), True),
        StructField("op_unique_carrier", StringType(), True),
        StructField("op_carrier_fl_num", DoubleType(), True),
        StructField("origin", StringType(), True),
        StructField("origin_city_name", StringType(), True),
        StructField("origin_state_nm", StringType(), True),
        StructField("dest", StringType(), True),
        StructField("dest_city_name", StringType(), True),
        StructField("dest_state_nm", StringType(), True),
        StructField("crs_dep_time", IntegerType(), True),
        StructField("dep_time", DoubleType(), True),
        StructField("dep_delay", DoubleType(), True),
        StructField("taxi_out", DoubleType(), True),
        StructField("wheels_off", DoubleType(), True),
        StructField("wheels_on", DoubleType(), True),
        StructField("taxi_in", DoubleType(), True),
        StructField("crs_arr_time", IntegerType(), True),
        StructField("arr_time", DoubleType(), True),
        StructField("arr_delay", DoubleType(), True),
        StructField("cancelled", IntegerType(), True),
        StructField("cancellation_code", StringType(), True),
        StructField("diverted", IntegerType(), True),
        StructField("crs_elapsed_time", DoubleType(), True),
        StructField("actual_elapsed_time", DoubleType(), True),
        StructField("air_time", DoubleType(), True),
        StructField("distance", DoubleType(), True),
        StructField("carrier_delay", IntegerType(), True),
        StructField("weather_delay", IntegerType(), True),
        StructField("nas_delay", IntegerType(), True),
        StructField("security_delay", IntegerType(), True),
        StructField("late_aircraft_delay", IntegerType(), True),
    ]
)

DELAY_CAUSE_COLS = [
    "carrier_delay",
    "weather_delay",
    "nas_delay",
    "security_delay",
    "late_aircraft_delay",
]

KEY_NUMERIC_COLS = [
    "dep_delay",
    "arr_delay",
    "taxi_out",
    "taxi_in",
    "crs_elapsed_time",
    "actual_elapsed_time",
    "air_time",
    "distance",
]

FIELD_ROLES = {
    "year": "date",
    "month": "date",
    "day_of_month": "date",
    "day_of_week": "date",
    "fl_date": "date",
    "op_unique_carrier": "airline",
    "op_carrier_fl_num": "identifier",
    "origin": "airport",
    "origin_city_name": "airport",
    "origin_state_nm": "airport",
    "dest": "airport",
    "dest_city_name": "airport",
    "dest_state_nm": "airport",
    "crs_dep_time": "time",
    "dep_time": "time",
    "dep_delay": "delay",
    "taxi_out": "operational",
    "wheels_off": "time",
    "wheels_on": "time",
    "taxi_in": "operational",
    "crs_arr_time": "time",
    "arr_time": "time",
    "arr_delay": "delay",
    "cancelled": "outcome",
    "cancellation_code": "outcome",
    "diverted": "outcome",
    "crs_elapsed_time": "operational",
    "actual_elapsed_time": "operational",
    "air_time": "operational",
    "distance": "operational",
    "carrier_delay": "delay_cause",
    "weather_delay": "delay_cause",
    "nas_delay": "delay_cause",
    "security_delay": "delay_cause",
    "late_aircraft_delay": "delay_cause",
}

FIELD_DESCRIPTIONS = {
    "year": "Flight year (constant 2024 in this file).",
    "month": "Month number (1-12).",
    "day_of_month": "Day of month (1-31).",
    "day_of_week": "BTS day-of-week code (1=Monday ... 7=Sunday).",
    "fl_date": "Scheduled flight date.",
    "op_unique_carrier": "Reporting/operating carrier code.",
    "op_carrier_fl_num": "Operating carrier flight number.",
    "origin": "Origin airport IATA code.",
    "origin_city_name": "Origin city and state name.",
    "origin_state_nm": "Origin state name.",
    "dest": "Destination airport IATA code.",
    "dest_city_name": "Destination city and state name.",
    "dest_state_nm": "Destination state name.",
    "crs_dep_time": "Scheduled local departure time in HHMM integer form.",
    "dep_time": "Actual local departure time in HHMM numeric form.",
    "dep_delay": "Departure delay in minutes; negative means early.",
    "taxi_out": "Taxi-out time in minutes.",
    "wheels_off": "Wheels-off local time in HHMM numeric form.",
    "wheels_on": "Wheels-on local time in HHMM numeric form.",
    "taxi_in": "Taxi-in time in minutes.",
    "crs_arr_time": "Scheduled local arrival time in HHMM integer form.",
    "arr_time": "Actual local arrival time in HHMM numeric form.",
    "arr_delay": "Arrival delay in minutes; negative means early.",
    "cancelled": "Cancellation indicator (1=cancelled, 0=not cancelled).",
    "cancellation_code": "Cancellation reason code A/B/C/D when cancelled.",
    "diverted": "Diversion indicator (1=diverted, 0=not diverted).",
    "crs_elapsed_time": "Scheduled elapsed flight time in minutes.",
    "actual_elapsed_time": "Actual elapsed flight time in minutes.",
    "air_time": "Time in the air in minutes.",
    "distance": "Great-circle distance between airports in miles.",
    "carrier_delay": "Minutes attributed to carrier-related delay.",
    "weather_delay": "Minutes attributed to extreme weather delay.",
    "nas_delay": "Minutes attributed to National Airspace System delay.",
    "security_delay": "Minutes attributed to security delay.",
    "late_aircraft_delay": "Minutes attributed to a late inbound aircraft.",
}


def load_raw_flights(
    spark: SparkSession, path: str | Path = DATA_FILE
) -> DataFrame:
    """Read the source CSV with an explicit schema (no inferSchema full scan)."""
    path = str(path)
    df = (
        spark.read.option("header", True)
        .option("mode", "PERMISSIVE")
        .option("dateFormat", "yyyy-MM-dd")
        .option("nullValue", "")
        .option("emptyValue", "")
        .schema(FLIGHT_SCHEMA)
        .csv(path)
    )
    return df


def basic_profile(df: DataFrame) -> dict:
    """Collect a compact set of profiling facts using Spark aggregations."""
    agg_row = df.agg(
        F.count(F.lit(1)).alias("rows"),
        F.min("fl_date").alias("min_date"),
        F.max("fl_date").alias("max_date"),
        F.countDistinct("fl_date").alias("calendar_days"),
        F.countDistinct("op_unique_carrier").alias("carriers"),
        F.countDistinct("origin").alias("origins"),
        F.countDistinct("dest").alias("destinations"),
        F.countDistinct("cancellation_code").alias("cancellation_reason_codes"),
        F.sum(F.when(F.col("cancelled") == 1, 1).otherwise(0)).alias("cancelled"),
        F.sum(F.when(F.col("diverted") == 1, 1).otherwise(0)).alias("diverted"),
    ).first().asDict()
    return agg_row


def missing_value_profile(df: DataFrame, total: int | None = None) -> DataFrame:
    """Return one row per column with null counts and percentages."""
    total = total or df.count()
    exprs = []
    for c in df.columns:
        exprs.append(
            F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c)
        )
    row = df.agg(*exprs).first().asDict()
    data = [
        (c, int(row[c]), round(100.0 * row[c] / total, 4) if total else 0.0)
        for c in df.columns
    ]
    return df.sparkSession.createDataFrame(
        data, ["column_name", "null_count", "null_percentage"]
    )


def numeric_summary(df: DataFrame, columns: list[str] | None = None) -> DataFrame:
    """Descriptive statistics for key numeric columns as a tidy DataFrame."""
    columns = columns or KEY_NUMERIC_COLS
    stats = df.select(*columns).summary(
        "count", "mean", "stddev", "min", "25%", "50%", "75%", "max"
    )
    # summary() returns a 'summary' label column; reshape to metric-per-column.
    rows = stats.collect()
    metrics = {}
    for r in rows:
        d = r.asDict()
        metrics[d["summary"]] = d
    out = []
    for c in columns:
        out.append(
            (
                c,
                float(metrics["count"][c]) if metrics["count"][c] is not None else None,
                float(metrics["mean"][c]) if metrics["mean"][c] is not None else None,
                float(metrics["stddev"][c]) if metrics["stddev"][c] is not None else None,
                float(metrics["min"][c]) if metrics["min"][c] is not None else None,
                float(metrics["25%"][c]) if metrics["25%"][c] is not None else None,
                float(metrics["50%"][c]) if metrics["50%"][c] is not None else None,
                float(metrics["75%"][c]) if metrics["75%"][c] is not None else None,
                float(metrics["max"][c]) if metrics["max"][c] is not None else None,
            )
        )
    schema = [
        "column_name",
        "count",
        "mean",
        "stddev",
        "min",
        "p25",
        "median",
        "p75",
        "max",
    ]
    return df.sparkSession.createDataFrame(out, schema)
