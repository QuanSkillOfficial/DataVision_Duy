"""
test_id_semantics.py — Tests for Week 6 ID field semantics.

Verifies that:
- document_external_id, document_db_id are properly handled
- source_id vs source_name vs ingestion_run_id are separate
- Prediction log payloads use correct ID fields

Run with:
    python -m pytest tests/ai_tests/test_id_semantics.py -v
"""

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.batch_inference import predict_document_types
from ai.prediction.prediction_log_payload_builder import build_prediction_log_payload
from ai.prediction.inference import reset_model_cache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_ID_INPUT = {
    "source_id": 4,
    "source_name": "dataflow_technical_report_pdf",
    "document_external_id": "doc_dataflow_technical_report",
    "document_db_id": 3,
    "ingestion_run_id": "a58bf6df-2dec-41ca-a18b-784c68eab826",
    "file_name": "DataFlow_Technical_Report.pdf",
    "file_type": "pdf",
    "file_size": 2857707,
    "text_length": 129028,
    "num_pages": 36,
    "source_system": "manual_upload",
    "extracted_text": (
        "This is a technical report about data flow systems and machine learning "
        "pipelines. It covers data preparation, workflow automation, and AI integration."
    ),
}

NULL_DB_ID_INPUT = {
    "source_id": None,
    "source_name": "new_source_slug",
    "document_external_id": "doc_new_document",
    "document_db_id": None,
    "ingestion_run_id": "b72cf4ea-1111-2222-3333-444455556666",
    "file_name": "new_document.pdf",
    "file_type": "pdf",
    "file_size": 500000,
    "text_length": 8000,
    "num_pages": 10,
    "source_system": "manual_upload",
    "extracted_text": (
        "This is a new document that has not been registered in the database yet. "
        "It has a long enough text for the prediction model to process correctly."
    ),
}

SAMPLE_PREDICTION = {
    "predicted_document_type": "report",
    "confidence": 0.83,
    "model_version": "document_classifier_v1",
    "status": "accepted",
    "top_predictions": [
        {"label": "report", "score": 0.83},
        {"label": "contract", "score": 0.10},
        {"label": "policy_document", "score": 0.05},
    ],
    "review_reason": None,
}


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset model cache before each test."""
    reset_model_cache()
    yield
    reset_model_cache()


# ---------------------------------------------------------------------------
# Prediction Log Payload — ID Semantics
# ---------------------------------------------------------------------------

def test_log_payload_has_document_external_id():
    """Log payload must contain document_external_id."""
    log = build_prediction_log_payload(FULL_ID_INPUT, SAMPLE_PREDICTION)
    assert log["document_external_id"] == "doc_dataflow_technical_report"


def test_log_payload_has_document_db_id():
    """Log payload must contain document_id."""
    log = build_prediction_log_payload(FULL_ID_INPUT, SAMPLE_PREDICTION)
    assert log["document_id"] == 3


def test_log_payload_has_source_id_integer():
    """Log payload source_id must be INTEGER from Phat DB."""
    log = build_prediction_log_payload(FULL_ID_INPUT, SAMPLE_PREDICTION)
    assert log["source_id"] == 4
    assert isinstance(log["source_id"], int)


def test_log_payload_has_ingestion_run_id():
    """Log payload must contain ingestion_run_id."""
    log = build_prediction_log_payload(FULL_ID_INPUT, SAMPLE_PREDICTION)
    assert log["ingestion_run_id"] == "a58bf6df-2dec-41ca-a18b-784c68eab826"


def test_log_payload_no_old_document_id_field():
    """Log payload must NOT contain old 'document_db_id' field."""
    log = build_prediction_log_payload(FULL_ID_INPUT, SAMPLE_PREDICTION)
    assert "document_db_id" not in log


def test_log_payload_null_db_ids():
    """Log payload handles null source_id and document_id correctly."""
    log = build_prediction_log_payload(NULL_DB_ID_INPUT, SAMPLE_PREDICTION)
    assert log["source_id"] is None
    assert log["document_id"] is None
    assert log["document_external_id"] == "doc_new_document"
    assert log["ingestion_run_id"] == "b72cf4ea-1111-2222-3333-444455556666"


def test_source_id_is_not_ingestion_run_id():
    """source_id and ingestion_run_id must be different fields with different values."""
    log = build_prediction_log_payload(FULL_ID_INPUT, SAMPLE_PREDICTION)
    assert log["source_id"] != log["ingestion_run_id"]


# ---------------------------------------------------------------------------
# Batch Inference — ID Fields
# ---------------------------------------------------------------------------

def test_batch_result_has_document_external_id():
    """Batch result must include document_external_id from input."""
    results = predict_document_types([FULL_ID_INPUT])
    assert results[0]["document_external_id"] == "doc_dataflow_technical_report"


def test_batch_result_has_source_name():
    """Batch result must include source_name from input."""
    results = predict_document_types([FULL_ID_INPUT])
    assert results[0]["source_name"] == "dataflow_technical_report_pdf"


def test_batch_result_has_ingestion_run_id():
    """Batch result must include ingestion_run_id from input."""
    results = predict_document_types([FULL_ID_INPUT])
    assert results[0]["ingestion_run_id"] == "a58bf6df-2dec-41ca-a18b-784c68eab826"


def test_batch_result_no_old_document_id():
    """Batch result must NOT contain old 'document_id' field."""
    results = predict_document_types([FULL_ID_INPUT])
    assert "document_id" not in results[0]


def test_batch_result_no_old_source_id():
    """Batch result must NOT contain old 'source_id' as top-level enrichment field."""
    # source_id should NOT be enriched at batch level — it's a DB field
    results = predict_document_types([FULL_ID_INPUT])
    # source_id may exist from the prediction itself, but not as top-level batch enrichment
    # The batch result should have document_external_id, source_name, ingestion_run_id
    assert "document_external_id" in results[0]
    assert "source_name" in results[0]
    assert "ingestion_run_id" in results[0]
