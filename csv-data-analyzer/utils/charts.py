"""
utils/charts.py
----------------
Generates real charts from the dataframe with matplotlib/seaborn and
returns them as base64-encoded PNGs so they can be embedded directly
in HTML (<img src="data:image/png;base64,...">) and reused as-is
inside the generated PDF report.
"""
import io
import base64
import matplotlib
matplotlib.use("Agg")  # headless rendering, no GUI backend needed
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

sns.set_style("whitegrid")
PALETTE = ["#2563eb", "#22c55e", "#f59e0b", "#a855f7", "#ef4444", "#06b6d4", "#94a3b8"]


def _fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=130, transparent=True)
    plt.close(fig)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def column_type_donut(numeric_count, categorical_count):
    fig, ax = plt.subplots(figsize=(4, 4))
    values = [numeric_count, categorical_count]
    labels = [f"Numeric: {numeric_count}", f"Categorical: {categorical_count}"]
    colors = ["#2563eb", "#22c55e"]
    if sum(values) == 0:
        values = [1]
        labels = ["No columns"]
        colors = ["#e2e8f0"]
    wedges, _ = ax.pie(values, colors=colors, startangle=90,
                        wedgeprops=dict(width=0.42, edgecolor="white"))
    ax.text(0, 0.08, str(numeric_count + categorical_count), ha="center", va="center",
            fontsize=22, fontweight="bold", color="#1e293b")
    ax.text(0, -0.15, "Total Columns", ha="center", va="center",
            fontsize=9, color="#64748b")
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.05, 0.5),
               frameon=False, fontsize=9)
    ax.set_aspect("equal")
    return _fig_to_base64(fig)


def missing_values_bar(missing_columns, limit=12):
    cols = missing_columns[:limit]
    if not cols:
        fig, ax = plt.subplots(figsize=(7, 3.2))
        ax.text(0.5, 0.5, "No missing values", ha="center", va="center", fontsize=12, color="#64748b")
        ax.axis("off")
        return _fig_to_base64(fig)

    names = [c["column"] for c in cols]
    counts = [c["missing_count"] for c in cols]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.bar(names, counts, color="#f87171", width=0.6, edgecolor="none")
    ax.set_ylabel("Missing Count", fontsize=9, color="#475569")
    ax.tick_params(axis="x", rotation=45, labelsize=8, colors="#475569")
    ax.tick_params(axis="y", labelsize=8, colors="#475569")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return _fig_to_base64(fig)


def numeric_boxplot(df, numeric_cols, limit=10):
    cols = numeric_cols[:limit]
    if not cols:
        fig, ax = plt.subplots(figsize=(7, 3.2))
        ax.text(0.5, 0.5, "No numeric columns", ha="center", va="center", fontsize=12, color="#64748b")
        ax.axis("off")
        return _fig_to_base64(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    data = [df[c].dropna().values for c in cols]
    try:
        # Matplotlib >= 3.9 renamed 'labels' to 'tick_labels'
        bp = ax.boxplot(data, patch_artist=True, tick_labels=cols, showfliers=True,
                         flierprops=dict(marker="o", markersize=3, markerfacecolor="#94a3b8", markeredgecolor="none"))
    except TypeError:
        # Older Matplotlib (< 3.9) still uses 'labels'
        bp = ax.boxplot(data, patch_artist=True, labels=cols, showfliers=True,
                         flierprops=dict(marker="o", markersize=3, markerfacecolor="#94a3b8", markeredgecolor="none"))
    for i, box in enumerate(bp["boxes"]):
        box.set_facecolor(PALETTE[i % len(PALETTE)])
        box.set_alpha(0.75)
    ax.set_ylabel("Values", fontsize=9, color="#475569")
    ax.tick_params(axis="x", rotation=30, labelsize=8, colors="#475569")
    ax.tick_params(axis="y", labelsize=8, colors="#475569")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return _fig_to_base64(fig)


def correlation_heatmap(corr):
    if corr is None or corr.empty:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "Need at least 2 numeric columns", ha="center", va="center",
                fontsize=11, color="#64748b")
        ax.axis("off")
        return _fig_to_base64(fig)

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    sns.heatmap(corr, cmap="RdBu_r", vmin=-1, vmax=1, annot=corr.shape[0] <= 8,
                fmt=".2f", linewidths=0.5, linecolor="white",
                cbar_kws={"shrink": 0.8}, ax=ax, annot_kws={"size": 7})
    ax.tick_params(labelsize=8, colors="#475569")
    fig.tight_layout()
    return _fig_to_base64(fig)


def categorical_pie(cat_data):
    if not cat_data:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.text(0.5, 0.5, "No categorical columns", ha="center", va="center", fontsize=11, color="#64748b")
        ax.axis("off")
        return _fig_to_base64(fig)

    labels = cat_data["labels"]
    values = cat_data["values"]
    total = sum(values)
    pct_labels = [f"{l} ({(v/total*100):.1f}%)" for l, v in zip(labels, values)]

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    wedges, _ = ax.pie(values, colors=PALETTE[:len(values)], startangle=90,
                        wedgeprops=dict(edgecolor="white", linewidth=1.5))
    ax.legend(wedges, pct_labels, loc="center left", bbox_to_anchor=(1.0, 0.5),
              frameon=False, fontsize=8)
    ax.set_aspect("equal")
    fig.tight_layout()
    return _fig_to_base64(fig)


def distribution_histogram(df, col):
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    data = df[col].dropna()
    if data.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
        return _fig_to_base64(fig)
    sns.histplot(data, kde=True, color="#2563eb", ax=ax, edgecolor="white")
    ax.set_xlabel(col, fontsize=9, color="#475569")
    ax.set_ylabel("Frequency", fontsize=9, color="#475569")
    ax.tick_params(labelsize=8, colors="#475569")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return _fig_to_base64(fig)


def categorical_bar(df, col, top_n=10):
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    counts = df[col].value_counts(dropna=True).head(top_n)
    if counts.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
        return _fig_to_base64(fig)
    ax.bar(counts.index.astype(str), counts.values, color=PALETTE[1], width=0.6)
    ax.set_xlabel(col, fontsize=9, color="#475569")
    ax.set_ylabel("Count", fontsize=9, color="#475569")
    ax.tick_params(axis="x", rotation=40, labelsize=8, colors="#475569")
    ax.tick_params(axis="y", labelsize=8, colors="#475569")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return _fig_to_base64(fig)