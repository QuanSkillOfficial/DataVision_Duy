from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

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


API_URL = "https://dummyjson.com/products"

API_REQUIRED_FIELDS = [
    "id",
    "title",
    "description",
    "category",
    "price",
    "rating",
    "stock",
    "sku",
    "availabilitystatus",
]

API_OPTIONAL_FIELDS = [
    "brand",
    "tags",
    "images",
    "thumbnail",
    "warrantyinformation",
    "shippinginformation",
    "returnpolicy",
    "minimumorderquantity",
    "dimensions_width",
    "dimensions_height",
    "dimensions_depth",
    "meta_createdat",
    "meta_updatedat",
    "meta_barcode",
    "meta_qrcode",
    "reviews",
]


def fetch_api_payload(api_url: str, fallback_path: Path) -> tuple[dict, str | None]:
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        return response.json(), None
    except Exception as exc:
        if fallback_path.exists():
            return json.loads(fallback_path.read_text(encoding="utf-8")), str(exc)
        raise


def flatten_list_value(value):
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return value


def flatten_products(api_response: dict) -> pd.DataFrame:
    products = api_response.get("products", [])
    df = pd.json_normalize(products, sep="_")
    for column in df.columns:
        df[column] = df[column].apply(flatten_list_value)
    return df


def run_api_ingestion(
    api_url: str = API_URL,
    raw_output_path: Path = PROJECT_ROOT / "data/raw/api/dummyjson_products_raw.json",
    staging_output_path: Path = PROJECT_ROOT / "data/staging/api/dummyjson_products_staging.csv",
    clean_output_path: Path = PROJECT_ROOT / "data/clean/api/dummyjson_products_clean.csv",
    log_output_path: Path = PROJECT_ROOT / "logs/api_ingestion_log.json",
) -> dict:
    start_time = utc_now()
    try:
        ensure_parent(raw_output_path)
        api_response, fallback_error = fetch_api_payload(api_url, raw_output_path)
        write_json(api_response, raw_output_path)

        df = flatten_products(api_response)
        records_read = len(df)
        staged = drop_empty_columns(clean_column_names(df))
        duplicate_rows = int(staged.duplicated().sum())
        missing_values = {key: int(value) for key, value in staged.isna().sum().to_dict().items()}
        required_missing_values = {
            key: int(value)
            for key, value in staged[API_REQUIRED_FIELDS].isna().sum().to_dict().items()
        }
        existing_optional_fields = [field for field in API_OPTIONAL_FIELDS if field in staged.columns]
        optional_missing_values = {
            key: int(value)
            for key, value in staged[existing_optional_fields].isna().sum().to_dict().items()
        }
        staged = staged.drop_duplicates()
        write_csv(staged, staging_output_path)

        clean, validation = required_field_validation(staged, API_REQUIRED_FIELDS)
        write_csv(clean, clean_output_path)

        records_valid = len(clean)
        records_invalid = records_read - records_valid
        log = base_log(
            source_name="dummyjson_products_api",
            source_type="api",
            input_path_or_url=api_url,
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
                "api_total": api_response.get("total"),
                "api_skip": api_response.get("skip"),
                "api_limit": api_response.get("limit"),
                "api_fallback_error": fallback_error,
                "required_missing_values_removed": validation["rows_missing_required_values"],
                "missing_values": missing_values,
                "required_missing_values": required_missing_values,
                "optional_missing_values": optional_missing_values,
                "total_missing_values": int(sum(missing_values.values())),
                "missing_required_columns": validation["missing_required_columns"],
                "required_fields": API_REQUIRED_FIELDS,
                "optional_fields": API_OPTIONAL_FIELDS,
            },
        )
    except Exception as exc:
        log = base_log(
            source_name="dummyjson_products_api",
            source_type="api",
            input_path_or_url=api_url,
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
