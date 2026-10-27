"""Spark session configuration for the Airline Delay Analytics project.

Only process-local settings are used. No Windows, Java, or global environment
configuration is modified.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
DATA_FILE = PROJECT_ROOT / "flight_data_2024.csv"
RESULTS_DIR = PROJECT_ROOT / "results_analysis"
CSV_DIR = RESULTS_DIR / "analytical_results"
GRAPH_DIR = RESULTS_DIR / "graphs"
PROFILE_DIR = RESULTS_DIR / "dataset_profile"
DETAIL_DIR = RESULTS_DIR / "detailed_analysis"
LOG_DIR = RESULTS_DIR / "execution_logs"

APP_NAME = "AirlineDelayAnalytics2024"


def configure_python_worker() -> str:
    """Pin Spark's Python workers to the project virtual environment."""
    py = str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))
    os.environ["PYSPARK_PYTHON"] = py
    os.environ["PYSPARK_DRIVER_PYTHON"] = py
    return py


def build_spark_session(
    app_name: str = APP_NAME,
    master: str = "local[8]",
    driver_memory: str = "6g",
    shuffle_partitions: int = "64",
):
    """Create (or reuse) a local Spark session with modest resource settings."""
    configure_python_worker()
    from pyspark.sql import SparkSession

    py = os.environ["PYSPARK_PYTHON"]
    builder = (
        SparkSession.builder.appName(app_name)
        .master(master)
        .config("spark.driver.memory", driver_memory)
        .config("spark.executor.memory", driver_memory)
        .config("spark.pyspark.python", py)
        .config("spark.pyspark.driver.python", py)
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.files.maxPartitionBytes", "128m")
        .config("spark.driver.maxResultSize", "512m")
        .config("spark.ui.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .config("spark.network.timeout", "300s")
        .config("spark.sql.ansi.enabled", "false")
    )
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def stop_spark(spark) -> None:
    """Stop the session cleanly if it is still active."""
    try:
        if spark is not None and not spark.sparkContext._jsc.sc().isStopped():
            spark.stop()
    except Exception:
        pass
