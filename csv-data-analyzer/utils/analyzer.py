"""
utils/analyzer.py
------------------
All functions here operate on a real pandas DataFrame loaded from the
user's uploaded CSV. Nothing is hard-coded or faked - every number
shown in the UI comes from these computations.
"""
import pandas as pd
import numpy as np


def load_dataframe(filepath):
    """Load CSV robustly, trying a couple of common encodings/separators."""
    try:
        df = pd.read_csv(filepath)
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="latin-1")
    except pd.errors.ParserError:
        df = pd.read_csv(filepath, sep=None, engine="python")

    # Drop fully empty unnamed columns that sometimes trail a CSV export
    df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]
    return df


def get_column_types(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [c for c in df.columns if c not in numeric_cols]
    return numeric_cols, categorical_cols


def get_overview(df):
    numeric_cols, categorical_cols = get_column_types(df)
    missing_total = int(df.isna().sum().sum())

    return {
        "total_rows": int(df.shape[0]),
        "total_columns": int(df.shape[1]),
        "numeric_columns": len(numeric_cols),
        "categorical_columns": len(categorical_cols),
        "missing_values": missing_total,
        "numeric_col_names": numeric_cols,
        "categorical_col_names": categorical_cols,
    }


def get_column_details(df):
    numeric_cols, categorical_cols = get_column_types(df)
    details = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        col_type = "Numeric" if col in numeric_cols else "Categorical"
        missing = int(df[col].isna().sum())
        unique = int(df[col].nunique(dropna=True))
        details.append({
            "name": col,
            "dtype": dtype,
            "type": col_type,
            "missing": missing,
            "missing_pct": round((missing / len(df)) * 100, 2) if len(df) else 0,
            "unique": unique,
            "sample": _safe_sample(df[col]),
        })
    return details


def _safe_sample(series):
    non_null = series.dropna()
    if non_null.empty:
        return "N/A"
    val = non_null.iloc[0]
    return str(val)[:40]


def get_missing_values(df):
    missing_series = df.isna().sum()
    missing = [
        {
            "column": col,
            "missing_count": int(count),
            "missing_pct": round((int(count) / len(df)) * 100, 2) if len(df) else 0,
        }
        for col, count in missing_series.items()
    ]
    missing.sort(key=lambda x: x["missing_count"], reverse=True)
    total_missing = int(missing_series.sum())
    total_cells = df.shape[0] * df.shape[1]
    return {
        "columns": missing,
        "total_missing": total_missing,
        "total_cells": total_cells,
        "overall_pct": round((total_missing / total_cells) * 100, 2) if total_cells else 0,
    }


def get_statistics(df):
    numeric_cols, _ = get_column_types(df)
    if not numeric_cols:
        return []

    desc = df[numeric_cols].describe(percentiles=[0.25, 0.5, 0.75]).transpose()
    missing = df[numeric_cols].isna().sum()

    rows = []
    for col in numeric_cols:
        row = desc.loc[col]
        rows.append({
            "column": col,
            "count": int(row["count"]),
            "mean": round(float(row["mean"]), 2) if pd.notna(row["mean"]) else None,
            "std": round(float(row["std"]), 2) if pd.notna(row["std"]) else None,
            "min": round(float(row["min"]), 2) if pd.notna(row["min"]) else None,
            "p25": round(float(row["25%"]), 2) if pd.notna(row["25%"]) else None,
            "median": round(float(row["50%"]), 2) if pd.notna(row["50%"]) else None,
            "p75": round(float(row["75%"]), 2) if pd.notna(row["75%"]) else None,
            "max": round(float(row["max"]), 2) if pd.notna(row["max"]) else None,
            "missing": int(missing[col]),
        })
    return rows


def get_correlation_matrix(df):
    numeric_cols, _ = get_column_types(df)
    if len(numeric_cols) < 2:
        return None, numeric_cols
    corr = df[numeric_cols].corr(numeric_only=True).round(2)
    return corr, numeric_cols


def get_categorical_distribution(df, top_n=6):
    """Pick the first categorical column with a manageable number of
    categories and return its value counts for the pie chart."""
    _, categorical_cols = get_column_types(df)
    for col in categorical_cols:
        counts = df[col].value_counts(dropna=True)
        if counts.empty:
            continue
        if len(counts) > top_n:
            top = counts.iloc[: top_n - 1]
            others = counts.iloc[top_n - 1:].sum()
            labels = top.index.astype(str).tolist() + ["Others"]
            values = top.values.tolist() + [int(others)]
        else:
            labels = counts.index.astype(str).tolist()
            values = counts.values.tolist()
        return {"column": col, "labels": labels, "values": values}
    return None


def get_preview(df, page=1, per_page=10):
    total_rows = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    page_df = df.iloc[start:end].fillna("")
    total_pages = max(1, (total_rows + per_page - 1) // per_page)
    return {
        "columns": df.columns.tolist(),
        "rows": page_df.values.tolist(),
        "page": page,
        "total_pages": total_pages,
        "total_rows": total_rows,
        "per_page": per_page,
    }
