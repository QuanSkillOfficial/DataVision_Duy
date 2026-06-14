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


EXCEL_REQUIRED_FIELDS = [
    "date",
    "region",
    "product",
    "quantity",
    "unitprice",
    "storelocation",
    "customertype",
    "discount",
    "salesperson",
    "totalprice",
    "paymentmethod",
    "returned",
    "orderid",
    "customername",
    "shippingcost",
    "orderdate",
    "deliverydate",
    "regionmanager",
]

EXCEL_OPTIONAL_FIELDS = ["promotion"]


def run_excel_ingestion(
    input_path: Path = PROJECT_ROOT / "data/sample_inputs/Product-Sales-Region.xlsx",
    raw_output_path: Path = PROJECT_ROOT / "data/raw/excel/product_sales_region_raw.xlsx",
    staging_output_path: Path = PROJECT_ROOT / "data/staging/excel/product_sales_region_staging.csv",
    clean_output_path: Path = PROJECT_ROOT / "data/clean/excel/product_sales_region_clean.csv",
    log_output_path: Path = PROJECT_ROOT / "logs/excel_ingestion_log.json",
) -> dict:
    start_time = utc_now()
    try:
        excel_file = pd.ExcelFile(input_path)
        sheet_names = excel_file.sheet_names
        selected_sheet = sheet_names[0]
        df = pd.read_excel(input_path, sheet_name=selected_sheet)
        df = df.dropna(how="all")
        records_read = len(df)

        copy_raw_file(input_path, raw_output_path)
        staged = drop_empty_columns(clean_column_names(df))
        duplicate_rows = int(staged.duplicated().sum())
        missing_values = {key: int(value) for key, value in staged.isna().sum().to_dict().items()}
        required_missing_values = {
            key: int(value)
            for key, value in staged[EXCEL_REQUIRED_FIELDS].isna().sum().to_dict().items()
        }
        existing_optional_fields = [field for field in EXCEL_OPTIONAL_FIELDS if field in staged.columns]
        optional_missing_values = {
            key: int(value)
            for key, value in staged[existing_optional_fields].isna().sum().to_dict().items()
        }
        staged = staged.drop_duplicates()
        write_csv(staged, staging_output_path)

        clean, validation = required_field_validation(staged, EXCEL_REQUIRED_FIELDS)
        write_csv(clean, clean_output_path)

        records_valid = len(clean)
        records_invalid = records_read - records_valid
        log = base_log(
            source_name="product_sales_region_excel",
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
                "duplicate_rows_removed": duplicate_rows,
                "required_missing_values_removed": validation["rows_missing_required_values"],
                "missing_values": missing_values,
                "required_missing_values": required_missing_values,
                "optional_missing_values": optional_missing_values,
                "total_missing_values": int(sum(missing_values.values())),
                "missing_required_columns": validation["missing_required_columns"],
                "required_fields": EXCEL_REQUIRED_FIELDS,
                "optional_fields": EXCEL_OPTIONAL_FIELDS,
            },
        )
    except Exception as exc:
        log = base_log(
            source_name="product_sales_region_excel",
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
