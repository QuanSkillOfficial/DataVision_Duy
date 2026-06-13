from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OWNER = "Nguyen Minh Duy"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def relative_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def clean_column_name(column: Any) -> str:
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


def write_csv(df: pd.DataFrame, path: Path) -> None:
    ensure_parent(path)
    df.to_csv(path, index=False)


def write_json(payload: dict[str, Any], path: Path) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=4, ensure_ascii=False), encoding="utf-8")


def copy_raw_file(input_path: Path, output_path: Path) -> None:
    ensure_parent(output_path)
    shutil.copy2(input_path, output_path)


def required_field_validation(
    df: pd.DataFrame, required_fields: list[str]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    missing_required_columns = [field for field in required_fields if field not in df.columns]
    if missing_required_columns:
        return df.iloc[0:0].copy(), {
            "required_fields": required_fields,
            "missing_required_columns": missing_required_columns,
            "rows_missing_required_values": len(df),
            "optional_missing_values": {},
        }

    required_missing_mask = df[required_fields].isna().any(axis=1)
    valid_df = df.loc[~required_missing_mask].copy()
    optional_fields = [column for column in df.columns if column not in required_fields]
    optional_missing_values = df[optional_fields].isna().sum().to_dict()

    return valid_df, {
        "required_fields": required_fields,
        "missing_required_columns": [],
        "rows_missing_required_values": int(required_missing_mask.sum()),
        "optional_missing_values": {
            key: int(value) for key, value in optional_missing_values.items()
        },
    }


def base_log(
    *,
    source_name: str,
    source_type: str,
    input_path_or_url: str,
    start_time: str,
    end_time: str,
    status: str,
    records_read: int,
    records_valid: int,
    records_invalid: int,
    error_message: str | None,
    raw_output_path: Path | None,
    staging_output_path: Path | None,
    clean_output_path: Path | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    log = {
        "run_id": str(uuid.uuid4()),
        "source_name": source_name,
        "source_type": source_type,
        "input_path_or_url": input_path_or_url,
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
        "records_read": int(records_read),
        "records_valid": int(records_valid),
        "records_invalid": int(records_invalid),
        "error_message": error_message,
        "raw_output_path": relative_path(raw_output_path),
        "staging_output_path": relative_path(staging_output_path),
        "clean_output_path": relative_path(clean_output_path),
        "owner": OWNER,
    }
    if extra:
        log.update(extra)
    return log
