"""Matplotlib visualisations for aggregated Spark results.

Only small aggregated results are passed to these functions; the full CSV is
never converted to pandas for plotting.
"""
from __future__ import annotations

import sys

import matplotlib

if "IPython" not in sys.modules:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .export_results import export_figure

COLORS = {
    "navy": "#17324d",
    "blue": "#2f6690",
    "teal": "#3a7ca5",
    "amber": "#d9a441",
    "red": "#b23a48",
    "green": "#3f7d5c",
    "grey": "#7d8a97",
    "light": "#dbe4ec",
}


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#b8c4cf",
            "axes.labelcolor": "#22313f",
            "axes.titleweight": "bold",
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "grid.color": "#e3e9ef",
            "grid.linewidth": 0.8,
            "font.family": "DejaVu Sans",
        }
    )


def show_figure(fig, filename: str, dpi: int = 160):
    """Save the exact figure to results_analysis/graphs and display inline."""
    _style()
    path = export_figure(fig, filename, dpi=dpi)
    try:
        from IPython.display import display

        display(fig)
    except Exception:
        pass
    return path


def plot_flight_volume_by_airline(df: pd.DataFrame):
    _style()
    d = df.sort_values("flights", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6.2))
    labels = d["op_unique_carrier"] + "  " + d["carrier_name"]
    bars = ax.barh(labels, d["flights"], color=COLORS["blue"], edgecolor="white")
    ax.set_xlabel("Number of scheduled flight legs")
    ax.set_title("Flight Volume by Operating Airline (2024)")
    ax.grid(axis="x", alpha=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, d["flights"]):
        ax.text(
            value + d["flights"].max() * 0.008,
            bar.get_y() + bar.get_height() / 2,
            f"{int(value):,}",
            va="center",
            fontsize=8,
            color="#22313f",
        )
    fig.tight_layout()
    return fig


def plot_average_delay_by_airline(df: pd.DataFrame):
    _style()
    d = df.sort_values("avg_dep_delay_min", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6.2))
    labels = d["op_unique_carrier"] + "  " + d["carrier_name"]
    colors = [
        COLORS["red"] if v >= d["avg_dep_delay_min"].median() else COLORS["teal"]
        for v in d["avg_dep_delay_min"]
    ]
    bars = ax.barh(labels, d["avg_dep_delay_min"], color=colors, edgecolor="white")
    ax.axvline(0, color="#22313f", linewidth=0.9)
    ax.set_xlabel("Mean departure delay (minutes)")
    ax.set_title("Average Departure Delay by Airline (minimum 10,000 flights)")
    ax.grid(axis="x", alpha=0.8)
    ax.set_axisbelow(True)
    for bar, value, rate in zip(
        bars, d["avg_dep_delay_min"], d["delayed_departure_rate_pct"]
    ):
        ax.text(
            value + 0.35,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f} min | {rate:.1f}% delayed",
            va="center",
            fontsize=8,
        )
    fig.tight_layout()
    return fig


def plot_monthly_delay_trends(df: pd.DataFrame):
    _style()
    d = df.sort_values("month")
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    ax = axes[0]
    ax.bar(d["month"], d["flights"], color=COLORS["light"], edgecolor=COLORS["blue"])
    ax.set_ylabel("Flights")
    ax.set_title("Monthly Flight Volume and Delay Trends (2024)")
    ax.grid(axis="y", alpha=0.8)
    ax2 = ax.twinx()
    ax2.plot(
        d["month"],
        d["cancellation_rate_pct"],
        color=COLORS["red"],
        marker="o",
        linewidth=1.8,
        label="Cancellation rate",
    )
    ax2.set_ylabel("Cancellation rate (%)", color=COLORS["red"])
    ax2.tick_params(axis="y", colors=COLORS["red"])
    ax2.legend(loc="upper right", fontsize=8)

    ax = axes[1]
    ax.plot(
        d["month"],
        d["avg_dep_delay_min"],
        color=COLORS["blue"],
        marker="o",
        linewidth=2,
        label="Mean departure delay",
    )
    ax.plot(
        d["month"],
        d["median_dep_delay_min"],
        color=COLORS["green"],
        marker="s",
        linewidth=1.6,
        label="Median departure delay",
    )
    ax.set_ylabel("Departure delay (minutes)")
    ax.grid(axis="y", alpha=0.8)
    ax3 = ax.twinx()
    ax3.plot(
        d["month"],
        d["delayed_departure_rate_pct"],
        color=COLORS["amber"],
        marker="^",
        linewidth=1.8,
        linestyle="--",
        label="Delayed departure rate",
    )
    ax3.set_ylabel("Delayed departure rate (%)", color=COLORS["amber"])
    ax3.tick_params(axis="y", colors=COLORS["amber"])
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)
    ax.set_xlabel("Month")
    ax.set_xticks(d["month"])
    ax.set_xticklabels([m[:3] for m in d["month_name"]])
    fig.tight_layout()
    return fig


def plot_delay_distribution(df: pd.DataFrame, kind: str = "Departure"):
    _style()
    d = df.copy()
    fig, ax = plt.subplots(figsize=(11, 5.6))
    def _bin_color(label: str) -> str:
        if label.startswith("<") or label.startswith("-"):
            return COLORS["green"]
        if label.startswith("0 to"):
            return COLORS["light"]
        if label.startswith(("15 to", "30 to", "45 to")):
            return COLORS["amber"]
        return COLORS["red"]

    colors = [_bin_color(b) for b in d["delay_bin"]]
    bars = ax.bar(d["delay_bin"], d["percentage"], color=colors, edgecolor="white")
    ax.set_ylabel("Percentage of observed flights (%)")
    ax.set_xlabel("Delay relative to schedule (minutes)")
    ax.set_title(f"{kind} Delay Distribution (15-minute bins)")
    ax.grid(axis="y", alpha=0.8)
    ax.set_axisbelow(True)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    for bar, value in zip(bars, d["percentage"]):
        if value >= 2.0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.15,
                f"{value:.1f}%",
                ha="center",
                fontsize=7.5,
            )
    fig.tight_layout()
    return fig


def plot_cancellation_analysis(airline_df: pd.DataFrame, reason_df: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    d = airline_df.sort_values("cancellation_rate_pct", ascending=True)
    ax = axes[0]
    colors = [
        COLORS["red"] if v >= airline_df["cancellation_rate_pct"].median() else COLORS["teal"]
        for v in d["cancellation_rate_pct"]
    ]
    bars = ax.barh(d["op_unique_carrier"], d["cancellation_rate_pct"], color=colors)
    ax.set_xlabel("Cancellation rate (%)")
    ax.set_title("Cancellation Rate by Airline")
    ax.grid(axis="x", alpha=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, d["cancellation_rate_pct"]):
        ax.text(value + 0.03, bar.get_y() + bar.get_height() / 2, f"{value:.2f}%", va="center", fontsize=7.5)

    ax = axes[1]
    r = reason_df.sort_values("cancellations", ascending=True)
    bars = ax.barh(
        r["cancellation_reason"],
        r["share_of_cancellations_pct"],
        color=[COLORS["red"], COLORS["amber"], COLORS["blue"], COLORS["green"]][: len(r)],
    )
    ax.set_xlabel("Share of cancellations (%)")
    ax.set_title("Cancellation Reasons")
    ax.grid(axis="x", alpha=0.8)
    ax.set_axisbelow(True)
    for bar, value, count in zip(
        bars, r["share_of_cancellations_pct"], r["cancellations"]
    ):
        ax.text(value + 0.8, bar.get_y() + bar.get_height() / 2, f"{value:.1f}% ({int(count):,})", va="center", fontsize=8)
    fig.suptitle("Cancellation Analysis (2024)", fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    return fig


def plot_airport_performance(df: pd.DataFrame):
    _style()
    d = df.sort_values("flights", ascending=False).head(18).copy()
    d = d.sort_values("delayed_departure_rate_pct", ascending=True)
    fig, ax = plt.subplots(figsize=(11, 6.8))
    labels = d["origin"] + " (" + d["origin_city_name"].str.split(",").str[0] + ")"
    bars = ax.barh(
        labels,
        d["delayed_departure_rate_pct"],
        color=[
            COLORS["red"] if v >= df["delayed_departure_rate_pct"].median() else COLORS["teal"]
            for v in d["delayed_departure_rate_pct"]
        ],
    )
    ax.set_xlabel("Delayed departure rate (%)")
    ax.set_title("Origin-Airport Performance: 18 Busiest Airports")
    ax.grid(axis="x", alpha=0.8)
    ax.set_axisbelow(True)
    for bar, rate, flights, avg in zip(
        bars,
        d["delayed_departure_rate_pct"],
        d["flights"],
        d["avg_dep_delay_min"],
    ):
        ax.text(
            rate + 0.25,
            bar.get_y() + bar.get_height() / 2,
            f"{rate:.1f}% | {int(flights):,} flights | {avg:.1f} min",
            va="center",
            fontsize=7.5,
        )
    fig.tight_layout()
    return fig


def plot_route_delay_analysis(df: pd.DataFrame):
    _style()
    d = df.sort_values("flights", ascending=False).head(16).copy()
    d = d.sort_values("delayed_departure_rate_pct", ascending=True)
    fig, ax = plt.subplots(figsize=(11, 6.8))
    bars = ax.barh(
        d["route"],
        d["delayed_departure_rate_pct"],
        color=[
            COLORS["red"] if v >= df["delayed_departure_rate_pct"].median() else COLORS["teal"]
            for v in d["delayed_departure_rate_pct"]
        ],
    )
    ax.set_xlabel("Delayed departure rate (%)")
    ax.set_title("Route-Level Performance: 16 Busiest Routes (minimum 200 flights)")
    ax.grid(axis="x", alpha=0.8)
    ax.set_axisbelow(True)
    for bar, rate, flights, avg in zip(
        bars,
        d["delayed_departure_rate_pct"],
        d["flights"],
        d["avg_dep_delay_min"],
    ):
        ax.text(
            rate + 0.25,
            bar.get_y() + bar.get_height() / 2,
            f"{rate:.1f}% | {int(flights):,} flights | {avg:.1f} min",
            va="center",
            fontsize=7.5,
        )
    fig.tight_layout()
    return fig


def plot_delay_causes(df: pd.DataFrame):
    _style()
    d = df.sort_values("share_of_attributed_minutes_pct", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5.4))
    bars = ax.barh(
        d["cause"],
        d["share_of_attributed_minutes_pct"],
        color=[COLORS["red"], COLORS["amber"], COLORS["blue"], COLORS["green"], COLORS["teal"]][: len(d)],
    )
    ax.set_xlabel("Share of attributed delay minutes (%)")
    ax.set_title("Attributed Delay Minutes by Cause (delayed departures with cause data)")
    ax.grid(axis="x", alpha=0.8)
    ax.set_axisbelow(True)
    for bar, value, minutes in zip(
        bars, d["share_of_attributed_minutes_pct"], d["attributed_minutes"]
    ):
        ax.text(
            value + 0.8,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}% | {int(minutes):,} min",
            va="center",
            fontsize=8,
        )
    fig.tight_layout()
    return fig


def plot_risk_distribution(df: pd.DataFrame):
    _style()
    order = [
        "On-time / early (<15 min)",
        "Minor (15-29 min)",
        "Moderate (30-59 min)",
        "Severe (60-119 min)",
        "Extreme (120+ min)",
    ]
    d = df.set_index("delay_risk").reindex(order).dropna().reset_index()
    fig, ax = plt.subplots(figsize=(10, 5.4))
    bars = ax.bar(
        d["delay_risk"],
        d["share_pct"],
        color=[COLORS["green"], COLORS["amber"], COLORS["teal"], COLORS["red"], "#7b1f2b"],
        edgecolor="white",
    )
    ax.set_ylabel("Share of flown flights (%)")
    ax.set_xlabel("Departure-delay risk category")
    ax.set_title("Delay-Risk Category Distribution (flown flights)")
    ax.grid(axis="y", alpha=0.8)
    ax.set_axisbelow(True)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    for bar, value, count in zip(bars, d["share_pct"], d["flights"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.5,
            f"{value:.2f}%\n({int(count):,})",
            ha="center",
            fontsize=8,
        )
    fig.tight_layout()
    return fig


def plot_model_evaluation(metrics_df: pd.DataFrame, cm_df: pd.DataFrame):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    ax = axes[0]
    matrix = cm_df.pivot(index="actual", columns="predicted", values="count").reindex(
        index=["Not delayed", "Delayed"], columns=["Not delayed", "Delayed"]
    )
    im = ax.imshow(matrix.values, cmap="Blues")
    ax.set_xticks([0, 1], ["Not delayed", "Delayed"])
    ax.set_yticks([0, 1], ["Not delayed", "Delayed"])
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("Actual label")
    ax.set_title("Confusion Matrix (20% hold-out)")
    for i in range(2):
        for j in range(2):
            val = matrix.values[i, j]
            ax.text(
                j,
                i,
                f"{int(val):,}",
                ha="center",
                va="center",
                color="white" if val > matrix.values.max() * 0.5 else "#17324d",
                fontsize=11,
                fontweight="bold",
            )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax = axes[1]
    d = metrics_df.set_index("model")
    cols = ["accuracy", "precision", "recall", "f1", "auc"]
    x = np.arange(len(cols))
    width = 0.38
    models = list(d.index)
    colors = [COLORS["grey"], COLORS["blue"]]
    for i, model in enumerate(models):
        vals = [d.loc[model, c] for c in cols]
        bars = ax.bar(x + (i - 0.5) * width, vals, width, label=model, color=colors[i])
        for bar, v in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + 0.015,
                f"{v:.3f}",
                ha="center",
                fontsize=7.5,
            )
    ax.set_xticks(x, [c.upper() if c == "auc" else c.capitalize() for c in cols])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Model versus Majority-Class Baseline")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.8)
    ax.set_axisbelow(True)
    fig.suptitle("Delay-Prediction Model Evaluation", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    return fig
