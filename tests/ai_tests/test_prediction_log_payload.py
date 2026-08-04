"""
test_prediction_log_payload.py — Tests for prediction log payload builder.

Run with:
    python -m pytest tests/ai_tests/test_prediction_log_payload.py -v
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

from ai.prediction.prediction_log_payload_builder import build_prediction_log_payload

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_INPUT = {
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
    "extracted_text": "This policy explains the rules for access control...",
}

SAMPLE_PREDICTION_ACCEPTED = {
    "predicted_document_type": "report",
    "confidence": 0.83,
    "model_version": "document_classifier_v1",
    "status": "accepted",
    "top_predictions": [
        {"label": "report", "score": 0.83},
        {"label": "policy_document", "score": 0.10},
        {"label": "contract", "score": 0.05},
    ],
    "review_reason": None,
}

SAMPLE_PREDICTION_NEEDS_REVIEW = {
    "predicted_document_type": "report",
    "confidence": 0.48,
    "model_version": "document_classifier_v1",
    "status": "needs_review",
    "top_predictions": [
        {"label": "report", "score": 0.48},
        {"label": "policy_document", "score": 0.30},
        {"label": "contract", "score": 0.12},
    ],
    "review_reason": "Prediction confidence below threshold",
}

SAMPLE_PREDICTION_WAITING = {
    "predicted_document_type": None,
    "confidence": 0.0,
    "model_version": "document_classifier_v1",
    "status": "waiting_for_source",
    "top_predictions": [],
    "review_reason": "Extracted text is missing or too short for reliable prediction",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_returns_dict():
    """Payload builder must return a dict."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert isinstance(log, dict)


def test_contains_required_db_fields():
    """Payload must contain all fields needed for prediction_logs table."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)

    required_fields = [
        "source_id",
        "document_external_id",
        "document_id",
        "model_name",
        "model_version",
        "input_payload",
        "prediction_result",
        "predicted_label",
        "confidence_score",
        "status",
        "review_reason",
        "ingestion_run_id",
        "created_at",
    ]
    for field in required_fields:
        assert field in log, f"Missing DB field: {field}"


def test_source_id_from_input():
    """source_id must come from the input payload."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert log["source_id"] == 4


def test_document_external_id_from_input():
    """document_external_id must come from the input payload."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert log["document_external_id"] == "doc_dataflow_technical_report"


def test_model_name_is_correct():
    """model_name must be 'document_classifier'."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert log["model_name"] == "document_classifier"


def test_model_version_from_prediction():
    """model_version must come from the prediction result."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert log["model_version"] == "document_classifier_v1"


def test_predicted_label_is_correct():
    """predicted_label must match predicted_document_type."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert log["predicted_label"] == "report"


def test_confidence_score_is_correct():
    """confidence_score must match confidence."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert log["confidence_score"] == 0.83


def test_status_accepted():
    """Status must be 'accepted' for high-confidence predictions."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert log["status"] == "accepted"


def test_review_reason_null_for_accepted():
    """review_reason must be None for accepted predictions."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert log["review_reason"] is None


def test_status_needs_review():
    """Status must be 'needs_review' for low-confidence predictions."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_NEEDS_REVIEW)
    assert log["status"] == "needs_review"


def test_review_reason_for_needs_review():
    """review_reason must be present for needs_review predictions."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_NEEDS_REVIEW)
    assert log["review_reason"] == "Prediction confidence below threshold"


def test_status_waiting_for_source():
    """Status must be 'waiting_for_source' for short text."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_WAITING)
    assert log["status"] == "waiting_for_source"


def test_prediction_result_contains_top_predictions():
    """prediction_result must contain top_predictions list."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert "top_predictions" in log["prediction_result"]
    assert isinstance(log["prediction_result"]["top_predictions"], list)


def test_input_payload_stored():
    """input_payload must store the original input data."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert isinstance(log["input_payload"], dict)
    assert log["input_payload"]["file_name"] == "DataFlow_Technical_Report.pdf"


def test_created_at_present():
    """created_at timestamp must be present."""
    log = build_prediction_log_payload(SAMPLE_INPUT, SAMPLE_PREDICTION_ACCEPTED)
    assert "created_at" in log
    assert isinstance(log["created_at"], str)
    assert len(log["created_at"]) > 0
