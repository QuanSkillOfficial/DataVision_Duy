"""
test_batch_validation_normalization.py — Tests for batch validation error normalization.

Verifies that validation errors from predict_document_type() are normalized
into the same uniform shape as successful predictions in batch mode.

Run with:
    python -m pytest tests/ai_tests/test_batch_validation_normalization.py -v
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
    "document_external_id": "doc-test-valid",
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

# Missing extracted_text — triggers validation error
MISSING_TEXT_PAYLOAD = {
    "document_external_id": "doc-test-missing-text",
    "source_name": "test_source",
    "ingestion_run_id": "run-test-002",
    "file_name": "missing.pdf",
    "file_type": "pdf",
    "file_size": 100000,
    "text_length": 0,
    "num_pages": 5,
    "source_system": "manual_upload",
    # extracted_text intentionally missing
}

# Missing file_name — triggers validation error
MISSING_FILENAME_PAYLOAD = {
    "document_external_id": "doc-test-missing-filename",
    "source_name": "test_source",
    "ingestion_run_id": "run-test-003",
    # file_name intentionally missing
    "file_type": "pdf",
    "file_size": 100000,
    "text_length": 500,
    "num_pages": 5,
    "source_system": "manual_upload",
    "extracted_text": "This is a long enough text for prediction to work properly with the model.",
}

# Missing multiple fields
MISSING_MULTIPLE_PAYLOAD = {
    "document_external_id": "doc-test-missing-multi",
    "source_name": "test_source",
    "ingestion_run_id": "run-test-004",
    # file_name, file_type, source_system all missing
    "file_size": 100000,
    "text_length": 500,
    "num_pages": 5,
    "extracted_text": "This is a valid text but other fields are missing from the payload.",
}

UNIFORM_FIELDS = [
    "predicted_document_type",
    "confidence",
    "model_version",
    "status",
    "review_reason",
    "top_predictions",
]


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset model cache before each test."""
    reset_model_cache()
    yield
    reset_model_cache()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_validation_error_normalized_to_failed_status():
    """Validation error in batch must be normalized to status='failed'."""
    results = predict_document_types([MISSING_TEXT_PAYLOAD])
    assert results[0]["status"] == "failed"


def test_validation_error_has_null_prediction():
    """Validation error must have predicted_document_type=None."""
    results = predict_document_types([MISSING_TEXT_PAYLOAD])
    assert results[0]["predicted_document_type"] is None


def test_validation_error_has_zero_confidence():
    """Validation error must have confidence=0.0."""
    results = predict_document_types([MISSING_TEXT_PAYLOAD])
    assert results[0]["confidence"] == 0.0


def test_validation_error_has_empty_top_predictions():
    """Validation error must have empty top_predictions."""
    results = predict_document_types([MISSING_TEXT_PAYLOAD])
    assert results[0]["top_predictions"] == []


def test_validation_error_has_review_reason():
    """Validation error must have descriptive review_reason."""
    results = predict_document_types([MISSING_TEXT_PAYLOAD])
    assert results[0]["review_reason"] is not None
    assert "Validation error" in results[0]["review_reason"]


def test_validation_error_has_model_version():
    """Validation error must have model_version."""
    results = predict_document_types([MISSING_TEXT_PAYLOAD])
    assert results[0]["model_version"] == "document_classifier_v1"


def test_validation_error_uniform_shape():
    """Validation error result must have the same fields as successful predictions."""
    results = predict_document_types([MISSING_TEXT_PAYLOAD])
    for field in UNIFORM_FIELDS:
        assert field in results[0], f"Missing uniform field: {field}"


def test_mixed_valid_and_invalid_all_have_uniform_shape():
    """Both valid and invalid items in batch must have uniform shape."""
    results = predict_document_types([VALID_PAYLOAD, MISSING_TEXT_PAYLOAD])
    assert len(results) == 2

    for i, result in enumerate(results):
        for field in UNIFORM_FIELDS:
            assert field in result, f"Result {i} missing uniform field: {field}"


def test_missing_filename_normalized():
    """Missing file_name triggers validation error, normalized in batch."""
    results = predict_document_types([MISSING_FILENAME_PAYLOAD])
    assert results[0]["status"] == "failed"
    assert "Validation error" in results[0]["review_reason"]


def test_missing_multiple_fields_normalized():
    """Missing multiple fields triggers validation error, normalized in batch."""
    results = predict_document_types([MISSING_MULTIPLE_PAYLOAD])
    assert results[0]["status"] == "failed"
    assert results[0]["predicted_document_type"] is None


def test_validation_error_preserves_id_fields():
    """Normalized validation error must still include ID fields from input."""
    results = predict_document_types([MISSING_TEXT_PAYLOAD])
    assert results[0]["document_external_id"] == "doc-test-missing-text"
    assert results[0]["source_name"] == "test_source"
    assert results[0]["ingestion_run_id"] == "run-test-002"
