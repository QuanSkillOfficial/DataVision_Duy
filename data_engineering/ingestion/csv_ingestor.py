from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from data_engineering.utils.file_utils import copy_file, create_file_manifest
from data_engineering.utils.log_utils import (
    build_ingestion_log,
    new_run_id,
    persist_run_log,
    utc_now,
    write_json,
)
from data_engineering.utils.path_utils import relative_path, resolve_project_path
from data_engineering.validation.data_quality import (
    build_data_quality_report,
    clean_column_names,
    drop_empty_columns,
    validate_required_fields,
)


def read_csv_with_fallback(input_path: Path) -> pd.DataFrame:
    for encoding in ("utf-8", "utf-8-sig", "latin1", "cp1252"):
        try:
            return pd.read_csv(input_path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(input_path)


def run_csv_ingestion(source_config: dict[str, Any]) -> dict[str, Any]:
    run_id = source_config.get("run_id") or new_run_id()
    start_time = utc_now()
    source_name = source_config["source_name"]
    input_path = resolve_project_path(source_config["input_path"])
    raw_output_path = resolve_project_path(source_config["raw_output_path"])
    staging_output_path = resolve_project_path(source_config["staging_output_path"])
    clean_output_path = resolve_project_path(source_config["clean_output_path"])
    required_fields = source_config.get("required_fields", [])
    optional_fields = source_config.get("optional_fields", [])

    try:
        if input_path is None or not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {source_config['input_path']}")

        df = read_csv_with_fallback(input_path)
        records_read = len(df)
        copy_file(input_path, raw_output_path)

        staged = drop_empty_columns(clean_column_names(df))
        duplicate_rows = int(staged.duplicated().sum())
        staged = staged.drop_duplicates()
        staging_output_path.parent.mkdir(parents=True, exist_ok=True)
        staged.to_csv(staging_output_path, index=False)

        clean, validation = validate_required_fields(staged, required_fields)
        clean_output_path.parent.mkdir(parents=True, exist_ok=True)
        clean.to_csv(clean_output_path, index=False)

        records_valid = len(clean)
        records_invalid = records_read - records_valid
        quality_report = build_data_quality_report(
            df=staged,
            required_fields=required_fields,
            optional_fields=optional_fields,
            numeric_fields=source_config.get("numeric_fields", []),
            date_fields=source_config.get("date_fields", []),
            records_invalid=records_invalid,
        )
        manifest = create_file_manifest(
            run_id=run_id,
            source_name=source_name,
            source_type="csv",
            input_path=input_path,
            raw_output_path=raw_output_path,
            ingested_at=start_time,
        )
        log = build_ingestion_log(
            run_id=run_id,
            source_name=source_name,
            source_type="csv",
            input_path_or_url=relative_path(input_path) or source_config["input_path"],
            start_time=start_time,
            end_time=utc_now(),
            status="success" if records_invalid == 0 else "partial_success",
            records_read=records_read,
            records_valid=records_valid,
            records_invalid=records_invalid,
            error_message=None,
            raw_output_path=raw_output_path,
            staging_output_path=staging_output_path,
            clean_output_path=clean_output_path,
            owner=source_config.get("owner", "Nguyen Minh Duy"),
            extra={
                "duplicate_rows_removed": duplicate_rows,
                "required_missing_values_removed": validation["rows_missing_required_values"],
                "missing_required_columns": validation["missing_required_columns"],
                "required_fields": required_fields,
                "optional_fields": optional_fields,
                "data_quality": quality_report,
                "data_quality_score": quality_report["data_quality_score"],
                "file_manifest": manifest,
            },
        )
    except Exception as exc:
        log = build_ingestion_log(
            run_id=run_id,
            source_name=source_name,
            source_type="csv",
            input_path_or_url=source_config.get("input_path", ""),
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
            owner=source_config.get("owner", "Nguyen Minh Duy"),
            extra={"data_quality_score": 0.0},
        )

    persist_run_log(
        ingestion_log=log,
        latest_log_path=source_config.get("latest_log_path"),
        run_log_dir=source_config.get("run_log_dir", "logs/runs"),
        run_history_path=source_config.get("run_history_path", "logs/ingestion_runs.jsonl"),
    )
    manifest = log.get("file_manifest")
    if manifest:
        manifest_output_dir = source_config.get("manifest_output_dir", "logs/manifests")
        write_json(manifest, f"{manifest_output_dir}/{run_id}_manifest.json")
    return log
