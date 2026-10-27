"""Cleaning and feature derivation for the airline flight dataset.

The source CSV is never modified. All changes are applied to an in-memory
Spark DataFrame and documented for the academic report.
"""
from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .data_loader import DELAY_CAUSE_COLS

CARRIER_NAMES = {
    "9E": "Endeavor Air",
    "AA": "American Airlines",
    "AS": "Alaska Airlines",
    "B6": "JetBlue Airways",
    "DL": "Delta Air Lines",
    "F9": "Frontier Airlines",
    "G4": "Allegiant Air",
    "HA": "Hawaiian Airlines",
    "MQ": "Envoy Air",
    "NK": "Spirit Airlines",
    "OH": "PSA Airlines",
    "OO": "SkyWest Airlines",
    "UA": "United Airlines",
    "WN": "Southwest Airlines",
    "YX": "Republic Airways",
}

CANCELLATION_REASONS = {
    "A": "Carrier",
    "B": "Weather",
    "C": "National Airspace System",
    "D": "Security",
}

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _carrier_name_expr():
    expr = F.lit("Unknown")
    for code, name in CARRIER_NAMES.items():
        expr = F.when(F.col("op_unique_carrier") == code, F.lit(name)).otherwise(expr)
    return expr


def _cancellation_reason_expr():
    expr = F.lit("Not cancelled")
    for code, name in CANCELLATION_REASONS.items():
        expr = (
            F.when(F.col("cancellation_code") == code, F.lit(name))
            .otherwise(expr)
        )
    return expr


def add_derived_columns(df: DataFrame) -> DataFrame:
    """Add documented analytical fields without changing the raw columns."""
    cause_total = sum(F.coalesce(c, F.lit(0)) for c in DELAY_CAUSE_COLS)

    dep_valid = (F.col("cancelled") == 0) & F.col("dep_delay").isNotNull()
    arr_valid = (
        (F.col("cancelled") == 0)
        & (F.col("diverted") == 0)
        & F.col("arr_delay").isNotNull()
    )
    dep_delayed = F.when(
        dep_valid, F.when(F.col("dep_delay") >= 15, 1).otherwise(0)
    )
    arr_delayed = F.when(
        arr_valid, F.when(F.col("arr_delay") >= 15, 1).otherwise(0)
    )

    valid_sched_dep = F.col("crs_dep_time").between(0, 2359)
    sched_hour = F.when(
        valid_sched_dep, F.floor(F.col("crs_dep_time") / 100)
    ).otherwise(F.lit(None).cast("int"))

    dep_hour = F.when(
        F.col("dep_time").between(0, 2400),
        (F.floor(F.col("dep_time") / 100).cast("int") % 24),
    ).otherwise(F.lit(None).cast("int"))

    delay_risk = (
        F.when(F.col("cancelled") == 1, F.lit("Cancelled"))
        .when(
            dep_valid & (F.col("dep_delay") >= 120), F.lit("Extreme (120+ min)")
        )
        .when(
            dep_valid & (F.col("dep_delay") >= 60), F.lit("Severe (60-119 min)")
        )
        .when(
            dep_valid & (F.col("dep_delay") >= 30), F.lit("Moderate (30-59 min)")
        )
        .when(
            dep_valid & (F.col("dep_delay") >= 15), F.lit("Minor (15-29 min)")
        )
        .when(dep_valid, F.lit("On-time / early (<15 min)"))
        .otherwise(F.lit(None).cast("string"))
    )

    distance_band = (
        F.when(F.col("distance") < 250, F.lit("<250 mi"))
        .when(F.col("distance") < 500, F.lit("250-499 mi"))
        .when(F.col("distance") < 1000, F.lit("500-999 mi"))
        .when(F.col("distance") < 1500, F.lit("1000-1499 mi"))
        .otherwise(F.lit("1500+ mi"))
    )

    month_name = F.element_at(
        F.array(*[F.lit(m) for m in MONTH_NAMES]), F.col("month").cast("int")
    )
    day_name = F.element_at(
        F.array(*[F.lit(d) for d in DAY_NAMES]), F.col("day_of_week").cast("int")
    )

    return (
        df.withColumn("carrier_name", _carrier_name_expr())
        .withColumn("cancellation_reason", _cancellation_reason_expr())
        .withColumn("month_name", month_name)
        .withColumn("day_name", day_name)
        .withColumn("route", F.concat_ws("-", F.col("origin"), F.col("dest")))
        .withColumn("sched_dep_hour", sched_hour)
        .withColumn("dep_hour", dep_hour)
        .withColumn("is_cancelled", F.col("cancelled").cast("int"))
        .withColumn("is_diverted", F.col("diverted").cast("int"))
        .withColumn("is_flown", F.when(F.col("cancelled") == 0, 1).otherwise(0))
        .withColumn("dep_delay_valid", dep_valid)
        .withColumn("arr_delay_valid", arr_valid)
        .withColumn("dep_delayed", dep_delayed)
        .withColumn("arr_delayed", arr_delayed)
        .withColumn("delay_risk", delay_risk)
        .withColumn("distance_band", distance_band)
        .withColumn("cause_total", cause_total)
        .withColumn(
            "cause_available",
            dep_valid & (F.col("dep_delay") >= 15) & (cause_total > 0),
        )
        .withColumn(
            "extreme_dep_gt_24h",
            F.when(F.col("dep_delay") > 1440, 1).otherwise(0),
        )
        .withColumn(
            "extreme_dep_gt_12h",
            F.when(F.col("dep_delay") > 720, 1).otherwise(0),
        )
        .withColumn(
            "valid_sched_dep_time",
            F.when(valid_sched_dep, 1).otherwise(0),
        )
        .withColumn(
            "valid_crs_elapsed",
            F.when(F.col("crs_elapsed_time") > 0, 1).otherwise(0),
        )
        .withColumn("quarter", F.quarter("fl_date"))
    )


def clean_flights(df: DataFrame, duplicate_count: int = 0) -> DataFrame:
    """Return the cleaned/derived DataFrame.

    Exact duplicates are removed only when the caller has established that
    they exist. No valid delay record, cancellation, diversion, or extreme
    delay is removed.
    """
    base = df.dropDuplicates() if duplicate_count > 0 else df
    return add_derived_columns(base)


def cleaning_summary(cleaned: DataFrame, raw_rows: int, duplicate_count: int) -> dict:
    """Collect before/after and data-quality counts in one aggregation."""
    row = (
        cleaned.agg(
            F.count(F.lit(1)).alias("rows_after"),
            F.sum("is_cancelled").alias("cancelled"),
            F.sum("is_diverted").alias("diverted"),
            F.sum("is_flown").alias("flown"),
            F.sum(F.when(F.col("dep_delay").isNull(), 1).otherwise(0)).alias(
                "dep_delay_missing"
            ),
            F.sum(F.when(F.col("arr_delay").isNull(), 1).otherwise(0)).alias(
                "arr_delay_missing"
            ),
            F.sum(F.when(F.col("dep_delay_valid"), 1).otherwise(0)).alias(
                "dep_delay_valid"
            ),
            F.sum(F.when(F.col("arr_delay_valid"), 1).otherwise(0)).alias(
                "arr_delay_valid"
            ),
            F.sum("dep_delayed").alias("dep_delayed"),
            F.sum("arr_delayed").alias("arr_delayed"),
            F.sum(F.when(F.col("cause_available"), 1).otherwise(0)).alias(
                "cause_available"
            ),
            F.sum(
                F.when(
                    (F.col("cancelled") == 0)
                    & (F.col("dep_delay") >= 15)
                    & (~F.col("cause_available")),
                    1,
                ).otherwise(0)
            ).alias("delayed_without_cause"),
            F.sum("extreme_dep_gt_24h").alias("extreme_dep_gt_24h"),
            F.sum("extreme_dep_gt_12h").alias("extreme_dep_gt_12h"),
            F.sum(F.when(F.col("valid_sched_dep_time") == 0, 1).otherwise(0)).alias(
                "invalid_sched_dep_time"
            ),
            F.sum(F.when(F.col("valid_crs_elapsed") == 0, 1).otherwise(0)).alias(
                "invalid_crs_elapsed"
            ),
            F.sum(
                F.when(
                    (F.col("cancelled") == 1) & F.col("dep_delay").isNotNull(),
                    1,
                ).otherwise(0)
            ).alias("cancelled_with_dep_delay"),
            F.min("fl_date").alias("min_date"),
            F.max("fl_date").alias("max_date"),
            F.countDistinct("route").alias("routes"),
            F.countDistinct("op_unique_carrier").alias("carriers"),
            F.countDistinct("origin").alias("origins"),
        )
        .first()
        .asDict()
    )
    row["rows_before"] = raw_rows
    row["duplicate_count"] = duplicate_count
    row["rows_after"] = int(row["rows_after"])
    row["duplicates_removed"] = int(raw_rows - row["rows_after"])
    for k, v in list(row.items()):
        if hasattr(v, "isoformat"):
            row[k] = v.isoformat()
    return row
