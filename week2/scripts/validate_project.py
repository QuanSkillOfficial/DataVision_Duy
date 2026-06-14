from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_OUTPUTS = [
    "data/raw/csv/superstore_raw.csv",
    "data/staging/csv/superstore_staging.csv",
    "data/clean/csv/superstore_clean.csv",
    "logs/csv_ingestion_log.json",
    "data/raw/excel/product_sales_region_raw.xlsx",
    "data/staging/excel/product_sales_region_staging.csv",
    "data/clean/excel/product_sales_region_clean.csv",
    "logs/excel_ingestion_log.json",
    "data/raw/api/dummyjson_products_raw.json",
    "data/staging/api/dummyjson_products_staging.csv",
    "data/clean/api/dummyjson_products_clean.csv",
    "logs/api_ingestion_log.json",
    "data/raw/pdf/dataflow_technical_report_raw.pdf",
    "data/staging/pdf/dataflow_pdf_text.txt",
    "data/staging/pdf/dataflow_pdf_pages_staging.csv",
    "data/clean/pdf/dataflow_pdf_pages_clean.csv",
    "data/staging/pdf/document_pages.jsonl",
    "logs/pdf_ingestion_log.json",
    "logs/pdf_metadata.json",
]

REQUIRED_DOCS = [
    "docs/standard_ingestion_output_contract.md",
    "docs/ingestion_log_schema.md",
    "docs/ingestion_db_handoff_for_phat.md",
    "docs/document_pages_jsonl_contract_for_lap.md",
    "docs/ingestion_to_prediction_contract.md",
    "docs/ingestion_result_contract_for_ui.md",
    "docs/team_handoff_index.md",
]

REQUIRED_NOTEBOOKS = [
    "notebooks/data_team/csv_ingestion_demo.ipynb",
    "notebooks/data_team/excel_ingestion_demo.ipynb",
    "notebooks/data_team/api_ingestion_demo.ipynb",
    "notebooks/data_team/pdf_extraction_demo.ipynb",
]

REQUIRED_LOG_FIELDS = [
    "run_id",
    "source_name",
    "source_type",
    "input_path_or_url",
    "start_time",
    "end_time",
    "status",
    "records_read",
    "records_valid",
    "records_invalid",
    "error_message",
    "raw_output_path",
    "staging_output_path",
    "clean_output_path",
    "owner",
]


def is_absolute_windows_path(value: object) -> bool:
    return isinstance(value, str) and len(value) >= 3 and value[1:3] == ":\\"


def validate_outputs() -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_OUTPUTS:
        path = PROJECT_ROOT / relative
        if not path.exists():
            errors.append(f"Missing output: {relative}")
    return errors


def validate_docs() -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_DOCS:
        path = PROJECT_ROOT / relative
        if not path.exists():
            errors.append(f"Missing contract doc: {relative}")
    return errors


def validate_notebooks() -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_NOTEBOOKS:
        path = PROJECT_ROOT / relative
        if not path.exists():
            errors.append(f"Missing notebook: {relative}")
    return errors


def validate_logs() -> list[str]:
    errors: list[str] = []
    for log_path in sorted((PROJECT_ROOT / "logs").glob("*_ingestion_log.json")):
        payload = json.loads(log_path.read_text(encoding="utf-8"))
        missing_fields = [field for field in REQUIRED_LOG_FIELDS if field not in payload]
        if missing_fields:
            errors.append(f"{log_path.name} missing fields: {', '.join(missing_fields)}")

        for field in (
            "input_path_or_url",
            "raw_output_path",
            "staging_output_path",
            "clean_output_path",
        ):
            value = payload.get(field)
            if is_absolute_windows_path(value):
                errors.append(f"{log_path.name} contains absolute path in {field}: {value}")
    return errors


def main() -> int:
    errors = validate_outputs() + validate_docs() + validate_notebooks() + validate_logs()
    if errors:
        print("Validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed")
    print(f"Checked {len(REQUIRED_OUTPUTS)} required outputs")
    print(f"Checked {len(REQUIRED_DOCS)} required contract docs")
    print(f"Checked {len(REQUIRED_NOTEBOOKS)} required notebooks")
    print("Checked ingestion log schema and portable paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
