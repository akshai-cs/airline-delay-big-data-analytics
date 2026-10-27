"""Advanced analytics: delay-risk bins, correlations, sensitivity, and MLlib."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.feature import OneHotEncoder, StringIndexer, VectorAssembler
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

DELAY_BINS = [
    ("< -30", None, -30),
    ("-30 to -15", -30, -15),
    ("-15 to 0", -15, 0),
    ("0 to 15", 0, 15),
    ("15 to 30", 15, 30),
    ("30 to 45", 30, 45),
    ("45 to 60", 45, 60),
    ("60 to 90", 60, 90),
    ("90 to 120", 90, 120),
    ("120 to 180", 120, 180),
    ("180+", 180, None),
]


def delay_bin_distribution(cleaned: DataFrame, kind: str = "departure") -> pd.DataFrame:
    """Aggregate delay values into ordered 15/30-minute bins using Spark."""
    if kind.lower().startswith("dep"):
        col, valid = "dep_delay", "dep_delay_valid"
    else:
        col, valid = "arr_delay", "arr_delay_valid"

    expr = None
    for label, low, high in DELAY_BINS:
        if low is None:
            cond = F.col(col) < high
        elif high is None:
            cond = F.col(col) >= low
        else:
            cond = (F.col(col) >= low) & (F.col(col) < high)
        expr = F.when(cond, F.lit(label)) if expr is None else expr.when(cond, F.lit(label))

    agg = (
        cleaned.filter(F.col(valid))
        .select(expr.alias("delay_bin"))
        .groupBy("delay_bin")
        .count()
    )
    pdf = agg.toPandas()
    order = [b[0] for b in DELAY_BINS]
    pdf = (
        pdf.set_index("delay_bin")
        .reindex(order)
        .fillna(0)
        .rename_axis("delay_bin")
        .reset_index()
    )
    pdf["count"] = pdf["count"].astype(int)
    total = int(pdf["count"].sum())
    pdf["percentage"] = (100.0 * pdf["count"] / total).round(4) if total else 0.0
    return pdf


def delay_sensitivity(cleaned: DataFrame) -> pd.DataFrame:
    """Compare delay central tendency with and without extreme observations."""
    valid = F.col("dep_delay_valid")
    rows = []
    variants = [
        ("All observed delays", valid),
        ("Excluding departures > 24 h", valid & (F.col("dep_delay") <= 1440)),
        ("Excluding departures > 12 h", valid & (F.col("dep_delay") <= 720)),
    ]
    for label, cond in variants:
        r = (
            cleaned.filter(cond)
            .agg(
                F.count(F.lit(1)).alias("n"),
                F.round(F.avg("dep_delay"), 4).alias("mean_min"),
                F.round(F.expr("percentile_approx(dep_delay, 0.5)"), 2).alias(
                    "median_min"
                ),
                F.round(F.expr("percentile_approx(dep_delay, 0.99)"), 2).alias(
                    "p99_min"
                ),
            )
            .first()
            .asDict()
        )
        rows.append({"variant": label, **r})
    return pd.DataFrame(rows)


def correlation_summary(airline_df: pd.DataFrame, airport_df: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation between group volume and delay rate.

    Correlations are descriptive group-level associations, not causal effects.
    """
    rows = []
    a = airline_df[["flights", "delayed_departure_rate_pct"]].dropna()
    if len(a) >= 3:
        r, p = _pearson(a["flights"], a["delayed_departure_rate_pct"])
        rows.append(
            {
                "group_level": "Airline",
                "groups": len(a),
                "correlation": round(r, 4),
                "p_value": round(p, 4),
            }
        )
    ap = airport_df[["flights", "delayed_departure_rate_pct"]].dropna()
    if len(ap) >= 3:
        r, p = _pearson(ap["flights"], ap["delayed_departure_rate_pct"])
        rows.append(
            {
                "group_level": "Origin airport",
                "groups": len(ap),
                "correlation": round(r, 4),
                "p_value": round(p, 4),
            }
        )
    return pd.DataFrame(rows)


def _pearson(x: pd.Series, y: pd.Series):
    try:
        from scipy.stats import pearsonr

        r, p = pearsonr(x.astype(float), y.astype(float))
        return float(r), float(p)
    except Exception:
        r = float(np.corrcoef(x.astype(float), y.astype(float))[0, 1])
        return r, float("nan")


def train_delay_model(cleaned: DataFrame, seed: int = 42, top_airports: int = 50) -> dict:
    """Train a bounded-feature Spark MLlib logistic-regression model.

    Target: departure delay >= 15 minutes for flown flights.
    Post-outcome fields and delay-cause fields are excluded to prevent leakage.
    """
    t0 = time.time()
    base = cleaned.filter(
        (F.col("is_flown") == 1)
        & F.col("dep_delay_valid")
        & F.col("sched_dep_hour").isNotNull()
        & (F.col("valid_crs_elapsed") == 1)
    ).select(
        "dep_delayed",
        "op_unique_carrier",
        "origin",
        "dest",
        "month",
        "day_of_week",
        "sched_dep_hour",
        "distance",
        "crs_elapsed_time",
    )

    top_origins = [
        r["origin"]
        for r in base.groupBy("origin")
        .count()
        .orderBy(F.desc("count"))
        .limit(top_airports)
        .collect()
    ]
    top_dests = [
        r["dest"]
        for r in base.groupBy("dest")
        .count()
        .orderBy(F.desc("count"))
        .limit(top_airports)
        .collect()
    ]

    model_data = (
        base.withColumn(
            "origin_grp",
            F.when(F.col("origin").isin(top_origins), F.col("origin")).otherwise(
                "OTHER"
            ),
        )
        .withColumn(
            "dest_grp",
            F.when(F.col("dest").isin(top_dests), F.col("dest")).otherwise("OTHER"),
        )
        .withColumn("label", F.col("dep_delayed").cast("double"))
        .withColumn(
            "carrier_grp", F.col("op_unique_carrier").cast("string")
        )
        .select(
            "label",
            "carrier_grp",
            "origin_grp",
            "dest_grp",
            F.col("month").cast("string").alias("month_grp"),
            F.col("day_of_week").cast("string").alias("dow_grp"),
            F.col("sched_dep_hour").cast("string").alias("hour_grp"),
            F.col("distance").cast("double"),
            F.col("crs_elapsed_time").cast("double"),
        )
        .filter(F.col("distance").isNotNull() & F.col("crs_elapsed_time").isNotNull())
    )

    counts = {
        int(r["label"]): int(r["count"])
        for r in model_data.groupBy("label").count().collect()
    }
    n_total = counts.get(0, 0) + counts.get(1, 0)
    n_pos = counts.get(1, 0)
    n_neg = counts.get(0, 0)
    w_pos = n_total / (2.0 * n_pos) if n_pos else 1.0
    w_neg = n_total / (2.0 * n_neg) if n_neg else 1.0
    model_data = model_data.withColumn(
        "class_weight",
        F.when(F.col("label") == 1.0, F.lit(w_pos)).otherwise(F.lit(w_neg)),
    )

    train, test = model_data.randomSplit([0.8, 0.2], seed=seed)
    train = train.persist()
    test = test.persist()
    train_rows = train.count()
    test_rows = test.count()

    cat_cols = [
        "carrier_grp",
        "origin_grp",
        "dest_grp",
        "month_grp",
        "dow_grp",
        "hour_grp",
    ]
    num_cols = ["distance", "crs_elapsed_time"]
    indexers = [
        StringIndexer(
            inputCol=c, outputCol=f"{c}_idx", handleInvalid="keep"
        )
        for c in cat_cols
    ]
    encoder = OneHotEncoder(
        inputCols=[f"{c}_idx" for c in cat_cols],
        outputCols=[f"{c}_oh" for c in cat_cols],
        handleInvalid="keep",
    )
    assembler = VectorAssembler(
        inputCols=[f"{c}_oh" for c in cat_cols] + num_cols,
        outputCol="features",
        handleInvalid="keep",
    )
    lr = LogisticRegression(
        featuresCol="features",
        labelCol="label",
        weightCol="class_weight",
        maxIter=20,
        regParam=0.01,
        elasticNetParam=0.0,
        threshold=0.5,
        predictionCol="prediction",
    )
    pipeline = Pipeline(stages=indexers + [encoder, assembler, lr])
    model = pipeline.fit(train)
    predictions = model.transform(test).select(
        "label", "prediction", "rawPrediction"
    ).persist()

    tp = predictions.filter((F.col("label") == 1.0) & (F.col("prediction") == 1.0)).count()
    tn = predictions.filter((F.col("label") == 0.0) & (F.col("prediction") == 0.0)).count()
    fp = predictions.filter((F.col("label") == 0.0) & (F.col("prediction") == 1.0)).count()
    fn = predictions.filter((F.col("label") == 1.0) & (F.col("prediction") == 0.0)).count()

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    accuracy = (tp + tn) / max(tp + tn + fp + fn, 1)
    auc = BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol="rawPrediction",
        metricName="areaUnderROC",
    ).evaluate(predictions)

    n_pos_test = tp + fn
    n_neg_test = tn + fp
    baseline_accuracy = n_neg_test / max(n_pos_test + n_neg_test, 1)
    metrics = pd.DataFrame(
        [
            {
                "model": "Majority baseline",
                "accuracy": round(baseline_accuracy, 4),
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "auc": 0.5,
                "tp": 0,
                "tn": n_neg_test,
                "fp": 0,
                "fn": n_pos_test,
            },
            {
                "model": "Logistic regression",
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "auc": round(float(auc), 4),
                "tp": tp,
                "tn": tn,
                "fp": fp,
                "fn": fn,
            },
        ]
    )
    confusion = pd.DataFrame(
        [
            {"actual": "Not delayed", "predicted": "Not delayed", "count": tn},
            {"actual": "Not delayed", "predicted": "Delayed", "count": fp},
            {"actual": "Delayed", "predicted": "Not delayed", "count": fn},
            {"actual": "Delayed", "predicted": "Delayed", "count": tp},
        ]
    )

    runtime = time.time() - t0
    result = {
        "metrics": metrics,
        "confusion": confusion,
        "train_rows": int(train_rows),
        "test_rows": int(test_rows),
        "label_positive": int(n_pos),
        "label_negative": int(n_neg),
        "positive_rate_pct": round(100.0 * n_pos / max(n_total, 1), 4),
        "n_features": int(model.stages[-1].coefficients.size),
        "w_pos": round(w_pos, 4),
        "w_neg": round(w_neg, 4),
        "runtime_sec": round(runtime, 1),
        "top_origins": len(top_origins),
        "top_dests": len(top_dests),
    }
    predictions.unpersist()
    train.unpersist()
    test.unpersist()
    return result
