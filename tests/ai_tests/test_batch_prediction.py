"""
test_batch_prediction.py — Tests for batch inference module.

Run with:
    python -m pytest tests/ai_tests/test_batch_prediction.py -v
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
from ai.prediction.inference import reset_model_cache

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_PAYLOAD = {
    "document_external_id": "doc-test-001",
    "source_name": "test_source",
    "ingestion_run_id": "run-test-001",
    "file_name": "policy_doc.pdf",
    "file_type": "pdf",
    "file_size": 240000,
    "text_length": 4200,
    "num_pages": 4,
    "source_system": "manual_upload",
    "extracted_text": (
        "This policy explains the rules for access control, "
        "responsibilities, approval process, and compliance review."
    ),
}

SHORT_TEXT_PAYLOAD = {
    "document_external_id": "doc-test-002",
    "source_name": "test_source",
    "ingestion_run_id": "run-test-002",
    "file_name": "short.txt",
    "file_type": "txt",
    "file_size": 20,
    "text_length": 5,
    "num_pages": 1,
    "source_system": "manual_upload",
    "extracted_text": "hi",
}


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset model cache before each test."""
    reset_model_cache()
    yield
    reset_model_cache()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_batch_returns_list():
    """Batch inference must return a list."""
    results = predict_document_types([VALID_PAYLOAD])
    assert isinstance(results, list)


def test_batch_returns_correct_count():
    """Batch inference must return one result per input payload."""
    payloads = [VALID_PAYLOAD, VALID_PAYLOAD]
    results = predict_document_types(payloads)
    assert len(results) == 2


def test_batch_result_contains_document_external_id():
    """Each batch result must include document_external_id from input."""
    results = predict_document_types([VALID_PAYLOAD])
    assert results[0]["document_external_id"] == "doc-test-001"


def test_batch_result_contains_source_name():
    """Each batch result must include source_name from input."""
    results = predict_document_types([VALID_PAYLOAD])
    assert results[0]["source_name"] == "test_source"


def test_batch_result_contains_required_fields():
    """Each batch result must contain all required output fields."""
    results = predict_document_types([VALID_PAYLOAD])
    result = results[0]

    required_fields = [
        "document_external_id",
        "source_name",
        "ingestion_run_id",
        "predicted_document_type",
        "confidence",
        "status",
        "top_predictions",
        "model_version",
    ]
    for field in required_fields:
        assert field in result, f"Missing field: {field}"


def test_batch_with_short_text_returns_waiting_for_source():
    """Short text payload in batch should return waiting_for_source status."""
    results = predict_document_types([SHORT_TEXT_PAYLOAD])
    assert results[0]["status"] == "waiting_for_source"
    assert results[0]["predicted_document_type"] is None
    assert results[0]["confidence"] == 0.0


def test_batch_mixed_payloads():
    """Batch with mixed valid and short text payloads returns correct statuses."""
    payloads = [VALID_PAYLOAD, SHORT_TEXT_PAYLOAD]
    results = predict_document_types(payloads)

    assert len(results) == 2
    assert results[0]["status"] in ("accepted", "needs_review")
    assert results[1]["status"] == "waiting_for_source"


def test_batch_empty_list():
    """Batch with empty list returns empty list."""
    results = predict_document_types([])
    assert results == []


def test_batch_preserves_order():
    """Batch results should preserve the order of input payloads."""
    payload_a = {**VALID_PAYLOAD, "document_external_id": "doc-A"}
    payload_b = {**VALID_PAYLOAD, "document_external_id": "doc-B"}
    results = predict_document_types([payload_a, payload_b])

    assert results[0]["document_external_id"] == "doc-A"
    assert results[1]["document_external_id"] == "doc-B"
