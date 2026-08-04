"""
test_prediction_inference.py — Tests for the document type prediction inference module.

Run with:
    python -m pytest tests/ai_tests/test_prediction_inference.py -v
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

from ai.prediction.inference import predict_document_type, reset_model_cache  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_PAYLOAD = {
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


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset model cache before each test."""
    reset_model_cache()
    yield
    reset_model_cache()


# ---------------------------------------------------------------------------
# Test 1: Valid input returns predicted_document_type
# ---------------------------------------------------------------------------

def test_valid_input_returns_predicted_document_type():
    """A valid input payload must return a 'predicted_document_type' string."""
    result = predict_document_type(VALID_PAYLOAD)
    assert "error" not in result, f"Unexpected error: {result}"
    assert "predicted_document_type" in result
    assert isinstance(result["predicted_document_type"], str)
    assert len(result["predicted_document_type"]) > 0


# ---------------------------------------------------------------------------
# Test 2: Valid input returns confidence
# ---------------------------------------------------------------------------

def test_valid_input_returns_confidence():
    """A valid input payload must return a 'confidence' float between 0 and 1."""
    result = predict_document_type(VALID_PAYLOAD)
    assert "error" not in result, f"Unexpected error: {result}"
    assert "confidence" in result
    assert isinstance(result["confidence"], float)
    assert 0.0 < result["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Test 3: Valid input returns top_predictions
# ---------------------------------------------------------------------------

def test_valid_input_returns_top_predictions():
    """A valid input payload must return 'top_predictions' as a list of 3 items."""
    result = predict_document_type(VALID_PAYLOAD)
    assert "error" not in result, f"Unexpected error: {result}"
    assert "top_predictions" in result
    top = result["top_predictions"]
    assert isinstance(top, list)
    assert len(top) == 3

    for item in top:
        assert "label" in item
        assert "score" in item
        assert isinstance(item["label"], str)
        assert isinstance(item["score"], float)
        assert 0.0 <= item["score"] <= 1.0

    # Verify sorted descending
    scores = [item["score"] for item in top]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Test 4: Missing required field returns clear error
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing_field", [
    "file_name",
    "file_type",
    "file_size",
    "text_length",
    "num_pages",
    "source_system",
    "extracted_text",
])
def test_missing_required_field_returns_error(missing_field: str):
    """Removing any required field must return an error dict with 'error' key."""
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != missing_field}
    result = predict_document_type(payload)
    assert "error" in result
    assert "message" in result
    assert missing_field in result["message"]


# ---------------------------------------------------------------------------
# Test 5: Empty extracted_text still returns output
# ---------------------------------------------------------------------------

def test_empty_extracted_text_returns_waiting_for_source():
    """An empty extracted_text should trigger the quality gate and return waiting_for_source."""
    payload = {**VALID_PAYLOAD, "extracted_text": ""}
    result = predict_document_type(payload)
    assert "error" not in result, f"Unexpected error: {result}"
    assert result["status"] == "waiting_for_source"
    assert result["predicted_document_type"] is None
    assert result["confidence"] == 0.0
    assert result["review_reason"] is not None
    assert "too short" in result["review_reason"].lower() or "missing" in result["review_reason"].lower()


# ---------------------------------------------------------------------------
# Additional tests
# ---------------------------------------------------------------------------

def test_valid_input_returns_model_version():
    """A valid input payload must return a 'model_version' string."""
    result = predict_document_type(VALID_PAYLOAD)
    assert "error" not in result
    assert "model_version" in result
    assert isinstance(result["model_version"], str)


def test_valid_input_returns_status():
    """A valid input payload must return a 'status' field."""
    result = predict_document_type(VALID_PAYLOAD)
    assert "error" not in result
    assert "status" in result
    assert result["status"] in ("accepted", "needs_review", "waiting_for_source", "failed")


def test_low_confidence_has_review_reason():
    """If status is 'needs_review', a 'review_reason' should be present."""
    # Use a very vague payload to likely trigger low confidence
    payload = {
        "file_name": "file",
        "file_type": "unknown",
        "file_size": 0,
        "text_length": 0,
        "num_pages": 0,
        "source_system": "unknown",
        "extracted_text": "",
    }
    result = predict_document_type(payload)
    assert "error" not in result
    if result["status"] == "needs_review":
        assert "review_reason" in result
        assert isinstance(result["review_reason"], str)
