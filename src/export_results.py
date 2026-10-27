"""Report-ready export helpers used by the notebook and the report builder."""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .spark_session import CSV_DIR, GRAPH_DIR, PROFILE_DIR


def coerce_decimals(pdf: pd.DataFrame) -> pd.DataFrame:
    """Convert Spark Decimal objects to float for plotting and arithmetic."""
    for col in pdf.columns:
        if pdf[col].dtype == object:
            non_null = pdf[col].dropna()
            if len(non_null) and isinstance(non_null.iloc[0], Decimal):
                pdf[col] = pdf[col].astype(float)
    return pdf


def ensure_directories() -> None:
    for d in (CSV_DIR, GRAPH_DIR, PROFILE_DIR):
        Path(d).mkdir(parents=True, exist_ok=True)


def export_frame(frame, filename: str, max_rows: int = 250000) -> pd.DataFrame:
    """Export a Spark or pandas DataFrame as a single report-ready CSV."""
    ensure_directories()
    if isinstance(frame, pd.DataFrame):
        pdf = frame.copy()
    else:
        pdf = frame.toPandas()
    pdf = coerce_decimals(pdf)
    if len(pdf) > max_rows:
        raise ValueError(
            f"Refusing to export {len(pdf):,} rows for {filename}; aggregate first."
        )
    path = CSV_DIR / filename
    pdf.to_csv(path, index=False, encoding="utf-8-sig", float_format="%.4f")
    return pdf


def export_pandas(frame: pd.DataFrame, filename: str, directory: Path | None = None) -> Path:
    directory = Path(directory or CSV_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    frame = coerce_decimals(frame.copy())
    frame.to_csv(path, index=False, encoding="utf-8-sig", float_format="%.4f")
    return path


def export_figure(fig, filename: str, dpi: int = 160) -> Path:
    ensure_directories()
    path = GRAPH_DIR / filename
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    return path


def write_text(path: Path, text: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_json(path: Path, payload: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def md_table(frame: pd.DataFrame, max_rows: int = 100, floatfmt: str = ".2f") -> str:
    """Return a GitHub-flavoured markdown table without optional deps."""
    pdf = frame.head(max_rows).copy()
    if pdf.empty:
        return "_No rows._"
    for col in pdf.columns:
        if pd.api.types.is_float_dtype(pdf[col]):
            pdf[col] = pdf[col].map(
                lambda v: "" if pd.isna(v) else format(float(v), floatfmt)
            )
    headers = [str(c) for c in pdf.columns]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for _, row in pdf.iterrows():
        vals = ["" if pd.isna(v) else str(v).replace("|", "\\|") for v in row]
        lines.append("| " + " | ".join(vals) + " |")
    if len(frame) > len(pdf):
        lines.append(
            f"\n_Showing {len(pdf):,} of {len(frame):,} rows in this document; "
            f"the CSV contains all rows._"
        )
    return "\n".join(lines)


def pct(numerator: float, denominator: float, digits: int = 4) -> float:
    if not denominator:
        return float("nan")
    return round(100.0 * numerator / denominator, digits)
