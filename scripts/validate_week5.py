from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "data_engineering/ingestion/csv_ingestor.py",
    "data_engineering/ingestion/excel_ingestor.py",
    "data_engineering/ingestion/api_ingestor.py",
    "data_engineering/ingestion/pdf_ingestor.py",
    "data_engineering/pipelines/ingestion_engine.py",
    "data_engineering/pipelines/prediction_payload_builder.py",
    "data_engineering/utils/path_utils.py",
    "data_engineering/utils/file_utils.py",
    "data_engineering/utils/log_utils.py",
    "data_engineering/validation/data_quality.py",
    "data_engineering/storage/postgres_writer.py",
    "data_engineering/configs/superstore_csv.json",
    "data_engineering/configs/product_sales_excel.json",
    "data_engineering/configs/dummyjson_products_api.json",
    "data_engineering/configs/dataflow_pdf.json",
    "docs/week5_ingestion_to_schema_v2_mapping.md",
    "docs/postgres_loading_notes.md",
    "docs/ingestion_api_service_plan.md",
    "tests/data_tests/test_csv_ingestor.py",
    "tests/data_tests/test_excel_ingestor.py",
    "tests/data_tests/test_api_ingestor.py",
    "tests/data_tests/test_pdf_ingestor.py",
    "tests/data_tests/test_ingestion_engine.py",
    "pytest.ini",
]

REQUIRED_CONFIG_KEYS = [
    "source_name",
    "source_type",
    "raw_output_path",
    "staging_output_path",
    "clean_output_path",
    "latest_log_path",
    "run_log_dir",
    "run_history_path",
    "manifest_output_dir",
    "owner",
]

REQUIRED_LOG_FIELDS = [
    "run_id",
    "source_name",
    "source_type",
    "status",
    "records_read",
    "records_valid",
    "records_invalid",
    "raw_output_path",
    "staging_output_path",
    "clean_output_path",
    "data_quality_score",
]


def is_absolute_windows_path(value: object) -> bool:
    return isinstance(value, str) and len(value) >= 3 and value[1:3] == ":\\"


def validate_required_files() -> list[str]:
    return [f"Missing required file: {relative}" for relative in REQUIRED_FILES if not (PROJECT_ROOT / relative).exists()]


def validate_configs() -> list[str]:
    errors: list[str] = []
    for config_path in sorted((PROJECT_ROOT / "data_engineering/configs").glob("*.json")):
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        missing = [key for key in REQUIRED_CONFIG_KEYS if key not in payload]
        if payload.get("source_type") == "api":
            if "api_url" not in payload:
                missing.append("api_url")
        else:
            if "input_path" not in payload:
                missing.append("input_path")
        if missing:
            errors.append(f"{config_path.name} missing config keys: {', '.join(sorted(set(missing)))}")
    return errors


def validate_run_logs() -> list[str]:
    errors: list[str] = []
    run_logs = sorted((PROJECT_ROOT / "logs/runs").glob("*.json"))
    manifests = sorted((PROJECT_ROOT / "logs/manifests").glob("*_manifest.json"))
    history = PROJECT_ROOT / "logs/ingestion_runs.jsonl"

    if len(run_logs) < 4:
        errors.append("Expected at least 4 run logs under logs/runs")
    if len(manifests) < 4:
        errors.append("Expected at least 4 manifests under logs/manifests")
    if not history.exists():
        errors.append("Missing logs/ingestion_runs.jsonl")

    for log_path in run_logs:
        payload = json.loads(log_path.read_text(encoding="utf-8"))
        missing = [field for field in REQUIRED_LOG_FIELDS if field not in payload]
        if missing:
            errors.append(f"{log_path.name} missing log fields: {', '.join(missing)}")
        for field in ("input_path_or_url", "raw_output_path", "staging_output_path", "clean_output_path"):
            if is_absolute_windows_path(payload.get(field)):
                errors.append(f"{log_path.name} contains absolute path in {field}")

    return errors


def main() -> int:
    errors = validate_required_files() + validate_configs() + validate_run_logs()
    if errors:
        print("Week 5 validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Week 5 validation passed")
    print(f"Checked {len(REQUIRED_FILES)} required files")
    print("Checked source configs")
    print("Checked run logs, manifests, and portable paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
