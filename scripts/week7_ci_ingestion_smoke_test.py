from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.pipelines.handoff_context import build_database_enriched_ui_summary
from data_engineering.pipelines.ingestion_engine import run_ingestion
from data_engineering.pipelines.prediction_payload_builder import build_pdf_prediction_payload


FIXTURE_DIR = PROJECT_ROOT / "tests/fixtures/data"


def _common_paths(root: Path, source_name: str) -> dict[str, str]:
    return {
        "raw_output_path": str(root / "raw" / f"{source_name}_raw"),
        "staging_output_path": str(root / "staging" / f"{source_name}_staging.csv"),
        "clean_output_path": str(root / "clean" / f"{source_name}_clean.csv"),
        "latest_log_path": str(root / "latest" / f"{source_name}.json"),
        "run_log_dir": str(root / "logs" / "runs"),
        "run_history_path": str(root / "logs" / "ingestion_runs.jsonl"),
        "manifest_output_dir": str(root / "logs" / "manifests"),
        "owner": "Nguyen Minh Duy",
    }


def build_smoke_configs(root: Path) -> list[dict[str, Any]]:
    csv = {
        **_common_paths(root, "sample_csv"),
        "source_name": "sample_superstore_csv",
        "source_type": "csv",
        "input_path": str(FIXTURE_DIR / "sample_superstore_small.csv"),
        "required_fields": ["row_id", "order_id", "sales"],
        "numeric_fields": ["sales"],
    }
    csv["raw_output_path"] += ".csv"

    excel = {
        **_common_paths(root, "sample_excel"),
        "source_name": "sample_product_sales_excel",
        "source_type": "excel",
        "input_path": str(FIXTURE_DIR / "sample_product_sales_small.xlsx"),
        "required_fields": ["date", "region", "product", "quantity"],
        "numeric_fields": ["quantity"],
    }
    excel["raw_output_path"] += ".xlsx"

    api = {
        **_common_paths(root, "sample_api"),
        "source_name": "sample_products_api",
        "source_type": "api",
        "api_url": "https://invalid.localhost/products",
        "record_path": "products",
        "use_cached_response": True,
        "fallback_path": str(FIXTURE_DIR / "sample_api_products.json"),
        "required_fields": ["id", "title", "price"],
    }
    api["raw_output_path"] += ".json"

    pdf = {
        **_common_paths(root, "sample_pdf"),
        "source_name": "sample_dataflow_pdf",
        "source_type": "pdf",
        "document_id": "doc_sample_dataflow",
        "input_path": str(FIXTURE_DIR / "sample_dataflow_small.pdf"),
        "staging_text_output_path": str(root / "staging" / "sample_dataflow_text.txt"),
        "document_pages_output_path": str(root / "staging" / "sample_document_pages.jsonl"),
        "metadata_output_path": str(root / "latest" / "sample_pdf_metadata.json"),
    }
    pdf["raw_output_path"] += ".pdf"
    return [csv, excel, api, pdf]


def run_ci_smoke_test() -> dict[str, Any]:
    started = time.perf_counter()
    required = {
        "sample_superstore_small.csv",
        "sample_product_sales_small.xlsx",
        "sample_api_products.json",
        "sample_dataflow_pages_small.jsonl",
        "sample_dataflow_small.pdf",
    }
    available = {path.name for path in FIXTURE_DIR.glob("*")}
    if required - available:
        raise FileNotFoundError(
            "Missing shared fixtures. Run: python scripts/week7_build_shared_test_fixtures.py"
        )

    runtime_parent = PROJECT_ROOT / ".ci_runtime_tmp"
    runtime_parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="datavision_week7_smoke_", dir=runtime_parent) as temp_dir:
            root = Path(temp_dir)
            results = [run_ingestion(config) for config in build_smoke_configs(root)]
            result_by_type = {result["source_type"]: result for result in results}
            if any(result.get("status") not in {"success", "partial_success"} for result in results):
                raise RuntimeError(f"One or more smoke ingestions failed: {results}")

            pdf_result = result_by_type["pdf"]
            pages_path = Path(pdf_result["document_pages_output_path"])
            pages = [json.loads(line) for line in pages_path.read_text(encoding="utf-8").splitlines() if line]
            prediction_payload = build_pdf_prediction_payload(
                ingestion_log_path=root / "latest/sample_pdf.json",
                metadata_path=root / "latest/sample_pdf_metadata.json",
            )
            ui_fixture = build_database_enriched_ui_summary(
                results,
                {"status": "ci_without_database", "source_ids": {}, "document_db_ids": {}},
            )
            manifest_count = len(list((root / "logs/manifests").glob("*_manifest.json")))

            checks = {
                "csv_ingestion": result_by_type["csv"]["records_valid"] == 8,
                "excel_ingestion": result_by_type["excel"]["records_valid"] == 8,
                "api_fallback_ingestion": result_by_type["api"]["records_valid"] == 5,
                "pdf_ingestion": len(pages) == 2,
                "manifest_creation": manifest_count == 4,
                "data_quality_scores": all(result.get("data_quality_score") is not None for result in results),
                "rag_handoff_creation": all("page_number" in page and "text" in page for page in pages),
                "prediction_payload_creation": prediction_payload["document_external_id"] == "doc_sample_dataflow",
                "ui_fixture_creation": ui_fixture["total_sources"] == 4,
            }
    finally:
        shutil.rmtree(runtime_parent, ignore_errors=True)

    elapsed = round(time.perf_counter() - started, 3)
    return {
        "status": "passed" if all(checks.values()) and elapsed < 120 else "failed",
        "elapsed_seconds": elapsed,
        "checks": checks,
        "records_valid": {source_type: result["records_valid"] for source_type, result in result_by_type.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CI-safe ingestion tests using small local fixtures")
    parser.add_argument("--output", help="Optional JSON result path")
    args = parser.parse_args()
    result = run_ci_smoke_test()
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
