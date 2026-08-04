"""
Week 7 UI CI smoke test.

Run:
    python scripts/week7_ui_ci_smoke_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo.services.fixture_validator import validate_all_week7_fixtures
from demo.services.service_client import (
    ask_rag,
    classify_document,
    generate_report,
    generate_suggestions,
    get_dashboard_metrics,
    get_ingestion_status,
)


def assert_envelope(label: str, response: dict) -> dict:
    if not isinstance(response, dict):
        raise AssertionError(f"{label}: response must be a dict")
    for key in ["data", "status", "metadata"]:
        if key not in response:
            raise AssertionError(f"{label}: missing envelope key {key}")
    if response["status"] == "error":
        raise AssertionError(f"{label}: returned error envelope {response}")
    if response["data"] is None:
        raise AssertionError(f"{label}: data must not be None")
    return response["data"]


def main() -> None:
    validate_all_week7_fixtures()

    dashboard = assert_envelope("dashboard", get_dashboard_metrics())
    for field in [
        "source_count",
        "records_read",
        "data_quality_score",
        "latest_document",
        "prediction_review_queue_count",
    ]:
        if field not in dashboard:
            raise AssertionError(f"dashboard: missing {field}")

    ingestion = assert_envelope("ingestion", get_ingestion_status())
    if not ingestion.get("file_hash_sha256"):
        raise AssertionError("ingestion: missing file_hash_sha256")

    payload = {
        "document_id": "doc_dataflow_technical_report",
        "document_external_id": "doc_dataflow_technical_report",
        "document_db_id": None,
        "source_id": None,
        "file_name": "DataFlow_Technical_Report.pdf",
        "file_type": "pdf",
        "file_size": 2857707,
        "text_length": 129028,
        "num_pages": 36,
        "source_system": "manual_upload",
        "extracted_text": "DataFlow technical report content for CI smoke testing.",
    }
    prediction = assert_envelope("prediction", classify_document(payload))
    for field in ["status", "confidence", "top_predictions", "manual_review_required"]:
        if field not in prediction:
            raise AssertionError(f"prediction: missing {field}")

    rag = assert_envelope("rag", ask_rag("What is the DataFlow pipeline?"))
    if not rag.get("citations"):
        raise AssertionError("rag: expected DataFlow citations")

    suggestions = assert_envelope(
        "suggestions",
        generate_suggestions({
            "dashboard_signals": dashboard,
            "prediction_result": prediction,
            "rag_context": rag,
            "ingestion_run": ingestion,
        }),
    )
    if not isinstance(suggestions, list) or not suggestions:
        raise AssertionError("suggestions: expected non-empty list")

    report = assert_envelope(
        "report",
        generate_report({
            "dashboard_signals": dashboard,
            "prediction_result": prediction,
            "rag_context": rag,
            "suggestions": suggestions,
            "ingestion_run": ingestion,
        }),
    )
    if not report.get("evidence_table"):
        raise AssertionError("report: missing evidence table")

    print("Week 7 UI CI smoke test passed.")


if __name__ == "__main__":
    main()
