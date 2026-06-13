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


EXCEL_REQUIRED_FIELDS = ["product_id", "product_name"]


def detect_header_row(input_path: Path, sheet_name: str) -> int:
    preview = pd.read_excel(input_path, sheet_name=sheet_name, header=None, nrows=20)
    for index, row in preview.iterrows():
        normalized = [str(value).strip().lower() for value in row.dropna().tolist()]
        if any("product id" in value for value in normalized):
            return int(index)
    return 0


def run_excel_ingestion(
    input_path: Path = PROJECT_ROOT / "data/sample_inputs/inventory.xlsx",
    raw_output_path: Path = PROJECT_ROOT / "data/raw/excel/inventory_raw.xlsx",
    staging_output_path: Path = PROJECT_ROOT / "data/staging/excel/sample_excel_staging.csv",
    clean_output_path: Path = PROJECT_ROOT / "data/clean/excel/sample_excel_clean.csv",
    log_output_path: Path = PROJECT_ROOT / "logs/excel_ingestion_log.json",
) -> dict:
    start_time = utc_now()
    try:
        excel_file = pd.ExcelFile(input_path)
        sheet_names = excel_file.sheet_names
        selected_sheet = sheet_names[0]
        header_row = detect_header_row(input_path, selected_sheet)
        df = pd.read_excel(input_path, sheet_name=selected_sheet, header=header_row)
        df = df.dropna(how="all")
        records_read = len(df)

        copy_raw_file(input_path, raw_output_path)
        staged = drop_empty_columns(clean_column_names(df))
        duplicate_rows = int(staged.duplicated().sum())
        staged = staged.drop_duplicates()
        write_csv(staged, staging_output_path)

        clean, validation = required_field_validation(staged, EXCEL_REQUIRED_FIELDS)
        write_csv(clean, clean_output_path)

        records_valid = len(clean)
        records_invalid = records_read - records_valid
        log = base_log(
            source_name="inventory_excel",
            source_type="excel",
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
                "sheet_names": sheet_names,
                "selected_sheet": selected_sheet,
                "detected_header_row": header_row,
                "duplicate_rows_removed": duplicate_rows,
                "required_missing_values_removed": validation["rows_missing_required_values"],
                "optional_missing_values": validation["optional_missing_values"],
                "missing_required_columns": validation["missing_required_columns"],
                "required_fields": EXCEL_REQUIRED_FIELDS,
            },
        )
    except Exception as exc:
        log = base_log(
            source_name="inventory_excel",
            source_type="excel",
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
    print(run_excel_ingestion())
