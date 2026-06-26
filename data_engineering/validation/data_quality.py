from __future__ import annotations

from typing import Any

import pandas as pd


def clean_column_name(column: Any) -> str:
    import re

    name = str(column).strip().lower()
    name = re.sub(r"[\r\n]+", " ", name)
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [clean_column_name(column) for column in cleaned.columns]
    return cleaned


def drop_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(axis=1, how="all")


def validate_required_fields(
    df: pd.DataFrame, required_fields: list[str]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    missing_required_columns = [field for field in required_fields if field not in df.columns]
    if missing_required_columns:
        return df.iloc[0:0].copy(), {
            "required_fields": required_fields,
            "missing_required_columns": missing_required_columns,
            "required_missing_count": len(df),
            "rows_missing_required_values": len(df),
        }

    required_missing_mask = df[required_fields].isna().any(axis=1)
    valid_df = df.loc[~required_missing_mask].copy()
    return valid_df, {
        "required_fields": required_fields,
        "missing_required_columns": [],
        "required_missing_count": int(required_missing_mask.sum()),
        "rows_missing_required_values": int(required_missing_mask.sum()),
    }


def missing_value_summary(df: pd.DataFrame, fields: list[str] | None = None) -> dict[str, int]:
    selected_fields = fields or list(df.columns)
    existing_fields = [field for field in selected_fields if field in df.columns]
    return {key: int(value) for key, value in df[existing_fields].isna().sum().to_dict().items()}


def duplicate_row_count(df: pd.DataFrame) -> int:
    return int(df.duplicated().sum())


def empty_file_check(df: pd.DataFrame) -> bool:
    return df.empty


def numeric_column_validation(df: pd.DataFrame, numeric_fields: list[str] | None = None) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for field in numeric_fields or []:
        if field not in df.columns:
            results[field] = {"exists": False, "invalid_count": None}
            continue
        coerced = pd.to_numeric(df[field], errors="coerce")
        invalid_count = int(coerced.isna().sum() - df[field].isna().sum())
        results[field] = {"exists": True, "invalid_count": max(invalid_count, 0)}
    return results


def date_column_validation(df: pd.DataFrame, date_fields: list[str] | None = None) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for field in date_fields or []:
        if field not in df.columns:
            results[field] = {"exists": False, "invalid_count": None}
            continue
        parsed = pd.to_datetime(df[field], errors="coerce", dayfirst=True)
        invalid_count = int(parsed.isna().sum() - df[field].isna().sum())
        results[field] = {"exists": True, "invalid_count": max(invalid_count, 0)}
    return results


def calculate_data_quality_score(
    *,
    records_read: int,
    records_invalid: int,
    duplicate_count: int,
    optional_missing_count: int,
) -> float:
    if records_read <= 0:
        return 0.0
    invalid_penalty = (records_invalid / records_read) * 60
    duplicate_penalty = (duplicate_count / records_read) * 20
    optional_missing_penalty = min((optional_missing_count / max(records_read, 1)) * 2, 20)
    return round(max(0.0, 100.0 - invalid_penalty - duplicate_penalty - optional_missing_penalty), 2)


def build_data_quality_report(
    *,
    df: pd.DataFrame,
    required_fields: list[str],
    optional_fields: list[str] | None = None,
    numeric_fields: list[str] | None = None,
    date_fields: list[str] | None = None,
    records_invalid: int = 0,
) -> dict[str, Any]:
    duplicate_count = duplicate_row_count(df)
    required_missing = missing_value_summary(df, required_fields)
    optional_missing = missing_value_summary(df, optional_fields or [])
    optional_missing_count = int(sum(optional_missing.values()))
    data_quality_score = calculate_data_quality_score(
        records_read=len(df),
        records_invalid=records_invalid,
        duplicate_count=duplicate_count,
        optional_missing_count=optional_missing_count,
    )
    status = "passed" if records_invalid == 0 else "partial_success"
    if df.empty:
        status = "failed"
    return {
        "data_quality_score": data_quality_score,
        "required_missing_count": int(sum(required_missing.values())),
        "optional_missing_count": optional_missing_count,
        "duplicate_count": duplicate_count,
        "missing_values": missing_value_summary(df),
        "required_missing_values": required_missing,
        "optional_missing_values": optional_missing,
        "numeric_validation": numeric_column_validation(df, numeric_fields),
        "date_validation": date_column_validation(df, date_fields),
        "is_empty_file": empty_file_check(df),
        "status": status,
    }

