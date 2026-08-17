"""
tests/test_prediction_ui_contract.py
======================================
Verifies classify_document() honors the prediction_ui_contract:
required fields, 4 status values, confidence threshold, top-3 shape.

Week 8 note (DV-HUNG-01): this module imports the fixture implementation
directly instead of `service_client`. These tests pin the reference UI
contract - the shape and business rules the UI requires from any backend - so
they must produce the same result in fixture mode and in backend mode. Live
UI-to-backend integration is covered separately by
tests/test_backend_contract_smoke.py, which runs in backend mode only.
"""

import pytest

from demo.config import PREDICTION_CONFIDENCE_THRESHOLD
from demo.services.mock_client import classify_document, classify_documents


VALID_PAYLOAD = {
    "document_id": "doc-001",
    "source_id": "src-001",
    "file_name": "vendor_contract.pdf",
    "file_type": "pdf",
    "file_size": 153600,
    "text_length": 2800,
    "num_pages": 8,
    "source_system": "external",
    "extracted_text": "This agreement is entered into between the parties.",
}


def test_valid_payload_returns_envelope():
    response = classify_document(VALID_PAYLOAD)
    assert "data" in response
    assert "status" in response


def test_valid_payload_has_required_fields():
    response = classify_document(VALID_PAYLOAD)
    data = response["data"]
    for field in [
        "predicted_document_type", "confidence", "model_version",
        "status", "review_reason", "top_predictions",
    ]:
        assert field in data, f"Missing field: {field}"


def test_status_is_one_of_four_contract_values():
    response = classify_document(VALID_PAYLOAD)
    status = response["data"]["status"]
    assert status in {"accepted", "needs_review", "waiting_for_source", "failed"}


def test_missing_required_field_returns_failed():
    bad_payload = {"file_name": "test.pdf", "file_type": "pdf"}
    response = classify_document(bad_payload)
    assert response["data"]["status"] == "failed"
    assert response["data"]["review_reason"] is not None


def test_empty_extracted_text_returns_waiting_for_source():
    payload = dict(VALID_PAYLOAD, extracted_text="")
    response = classify_document(payload)
    assert response["data"]["status"] == "waiting_for_source"


def test_confidence_in_valid_range():
    response = classify_document(VALID_PAYLOAD)
    confidence = response["data"]["confidence"]
    assert 0.0 <= confidence <= 1.0


def test_threshold_consistency_accepted():
    """If status is accepted, confidence must be >= threshold."""
    response = classify_document(VALID_PAYLOAD)
    data = response["data"]
    if data["status"] == "accepted":
        assert data["confidence"] >= PREDICTION_CONFIDENCE_THRESHOLD
        assert data["review_reason"] is None


def test_threshold_consistency_needs_review():
    """If status is needs_review, confidence must be below threshold."""
    response = classify_document(VALID_PAYLOAD)
    data = response["data"]
    if data["status"] == "needs_review":
        assert data["confidence"] < PREDICTION_CONFIDENCE_THRESHOLD
        assert data["review_reason"] is not None


def test_top_predictions_shape_when_accepted_or_review():
    response = classify_document(VALID_PAYLOAD)
    data = response["data"]
    if data["status"] in {"accepted", "needs_review"}:
        assert len(data["top_predictions"]) == 3
        for pred in data["top_predictions"]:
            assert "label" in pred
            assert "score" in pred
            assert 0.0 <= pred["score"] <= 1.0


def test_top_predictions_empty_when_failed_or_waiting():
    bad_payload = {"file_name": "x.pdf"}
    response = classify_document(bad_payload)
    assert response["data"]["top_predictions"] == []


def test_classify_documents_batch():
    payloads = [VALID_PAYLOAD, dict(VALID_PAYLOAD, document_id="doc-002")]
    response = classify_documents(payloads)
    assert isinstance(response["data"], list)
    assert len(response["data"]) == 2


def test_model_version_always_present():
    response = classify_document(VALID_PAYLOAD)
    assert response["data"]["model_version"] == "document_classifier_v1"


def test_submit_prediction_correction_success():
    from demo.services.mock_client import submit_prediction_correction
    valid_feedback = {
        "prediction_log_id": 12,
        "document_db_id": 1,
        "document_external_id": "doc_dataflow_technical_report",
        "predicted_document_type": "report",
        "corrected_document_type": "contract",
        "corrected_by": "user",
        "correction_reason": "Manual review confirmed this is a contract",
        "created_at": "2026-07-05T10:00:00Z"
    }
    response = submit_prediction_correction(valid_feedback)
    assert response["status"] == "success"
    assert response["data"]["success"] is True


def test_submit_prediction_correction_missing_fields_fails():
    from demo.services.mock_client import submit_prediction_correction
    invalid_feedback = {
        "prediction_log_id": 12,
        "corrected_document_type": "contract"
    }
    response = submit_prediction_correction(invalid_feedback)
    assert response["status"] == "error"
    assert "Missing required fields" in response["data"]["error"]
