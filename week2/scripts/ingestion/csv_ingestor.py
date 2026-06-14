from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from .common import (
        PROJECT_ROOT,
        base_log,
        clean_column_names,
        copy_raw_file,
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
        copy_raw_file,
        drop_empty_columns,
        relative_path,
        required_field_validation,
        utc_now,
        write_csv,
        write_json,
    )


CSV_REQUIRED_FIELDS = [
    "row_id",
    "order_id",
    "order_date",
    "ship_date",
    "customer_id",
    "customer_name",
    "country",
    "city",
    "state",
    "region",
    "product_id",
    "category",
    "sub_category",
    "product_name",
    "sales",
    "quantity",
    "discount",
    "profit",
]

CSV_OPTIONAL_FIELDS = ["ship_mode", "segment", "postal_code"]


def read_csv_with_fallback(input_path: Path) -> pd.DataFrame:
    for encoding in ("utf-8", "utf-8-sig", "latin1", "cp1252"):
        try:
            return pd.read_csv(input_path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(input_path)


def run_csv_ingestion(
    input_path: Path = PROJECT_ROOT / "data/sample_inputs/Superstore.csv",
    raw_output_path: Path = PROJECT_ROOT / "data/raw/csv/superstore_raw.csv",
    staging_output_path: Path = PROJECT_ROOT / "data/staging/csv/superstore_staging.csv",
    clean_output_path: Path = PROJECT_ROOT / "data/clean/csv/superstore_clean.csv",
    log_output_path: Path = PROJECT_ROOT / "logs/csv_ingestion_log.json",
) -> dict:
    start_time = utc_now()
    try:
        df = read_csv_with_fallback(input_path)
        records_read = len(df)
        copy_raw_file(input_path, raw_output_path)

        staged = drop_empty_columns(clean_column_names(df))
        duplicate_rows = int(staged.duplicated().sum())
        missing_values = {key: int(value) for key, value in staged.isna().sum().to_dict().items()}
        required_missing_values = {
            key: int(value)
            for key, value in staged[CSV_REQUIRED_FIELDS].isna().sum().to_dict().items()
        }
        existing_optional_fields = [field for field in CSV_OPTIONAL_FIELDS if field in staged.columns]
        optional_missing_values = {
            key: int(value)
            for key, value in staged[existing_optional_fields].isna().sum().to_dict().items()
        }
        staged = staged.drop_duplicates()
        write_csv(staged, staging_output_path)

        clean, validation = required_field_validation(staged, CSV_REQUIRED_FIELDS)
        write_csv(clean, clean_output_path)

        records_valid = len(clean)
        records_invalid = records_read - records_valid
        log = base_log(
            source_name="superstore_sales_csv",
            source_type="csv",
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
                "duplicate_rows_removed": duplicate_rows,
                "required_missing_values_removed": validation["rows_missing_required_values"],
                "missing_values": missing_values,
                "required_missing_values": required_missing_values,
                "optional_missing_values": optional_missing_values,
                "total_missing_values": int(sum(missing_values.values())),
                "missing_required_columns": validation["missing_required_columns"],
                "required_fields": CSV_REQUIRED_FIELDS,
                "optional_fields": CSV_OPTIONAL_FIELDS,
            },
        )
    except Exception as exc:
        log = base_log(
            source_name="superstore_sales_csv",
            source_type="csv",
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
    print(run_csv_ingestion())
