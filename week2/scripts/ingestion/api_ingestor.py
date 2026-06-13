from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

try:
    from .common import (
        PROJECT_ROOT,
        base_log,
        clean_column_names,
        ensure_parent,
        drop_empty_columns,
        relative_path,
        required_field_validation,
        utc_now,
        write_csv,
        write_json,
    )
except ImportError:
    from common import (
        PROJECT_ROOT,
        base_log,
        clean_column_names,
        ensure_parent,
        drop_empty_columns,
        relative_path,
        required_field_validation,
        utc_now,
        write_csv,
        write_json,
    )


API_REQUIRED_FIELDS = ["customer_id", "email", "created_at"]


def load_api_records(input_path: Path) -> list[dict]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                return value
    raise ValueError("API sample must be a list or contain a list field")


def run_api_ingestion(
    input_path: Path = PROJECT_ROOT / "data/sample_inputs/customer_api.json",
    raw_output_path: Path = PROJECT_ROOT / "data/raw/api/sample_api_response.json",
    staging_output_path: Path = PROJECT_ROOT / "data/staging/api/api_staging.csv",
    clean_output_path: Path = PROJECT_ROOT / "data/clean/api/api_clean.csv",
    log_output_path: Path = PROJECT_ROOT / "logs/api_ingestion_log.json",
) -> dict:
    start_time = utc_now()
    try:
        ensure_parent(raw_output_path)
        shutil.copy2(input_path, raw_output_path)

        records = load_api_records(input_path)
        df = pd.json_normalize(records)
        records_read = len(df)
        staged = drop_empty_columns(clean_column_names(df))
        duplicate_rows = int(staged.duplicated().sum())
        staged = staged.drop_duplicates()
        write_csv(staged, staging_output_path)

        clean, validation = required_field_validation(staged, API_REQUIRED_FIELDS)
        write_csv(clean, clean_output_path)

        records_valid = len(clean)
        records_invalid = records_read - records_valid
        log = base_log(
            source_name="customer_api",
            source_type="api",
            input_path_or_url=relative_path(input_path),
            start_time=start_time,
            end_time=utc_now(),
            status="success",
            records_read=records_read,
            records_valid=records_valid,
            records_invalid=records_invalid,
            error_message=None,
            raw_output_path=raw_output_path,
            staging_output_path=staging_output_path,
            clean_output_path=clean_output_path,
            extra={
                "validation_status": "passed" if records_invalid == 0 else "partial_success",
                "duplicate_rows_removed": duplicate_rows,
                "required_missing_values_removed": validation["rows_missing_required_values"],
                "optional_missing_values": validation["optional_missing_values"],
                "missing_required_columns": validation["missing_required_columns"],
                "required_fields": API_REQUIRED_FIELDS,
            },
        )
    except Exception as exc:
        log = base_log(
            source_name="customer_api",
            source_type="api",
            input_path_or_url=relative_path(input_path),
            start_time=start_time,
            end_time=utc_now(),
            status="failed",
            records_read=0,
            records_valid=0,
            records_invalid=0,
            error_message=str(exc),
            raw_output_path=None,
            staging_output_path=None,
            clean_output_path=None,
        )

    write_json(log, log_output_path)
    return log


if __name__ == "__main__":
    print(run_api_ingestion())
