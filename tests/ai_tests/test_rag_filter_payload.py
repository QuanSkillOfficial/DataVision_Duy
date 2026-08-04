"""
test_rag_filter_payload.py — Tests for RAG filter payload generation.

Verifies that prediction results can be correctly transformed into
RAG filter metadata following the filtering rules:
- Only 'accepted' status → use_for_rag_filtering = True
- All other statuses → use_for_rag_filtering = False

Run with:
    python -m pytest tests/ai_tests/test_rag_filter_payload.py -v
"""

import os
import sys
import json

import pytest

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.feature_builder import (
    STATUS_ACCEPTED,
    STATUS_NEEDS_REVIEW,
    STATUS_WAITING_FOR_SOURCE,
    STATUS_FAILED,
)


# ---------------------------------------------------------------------------
# RAG filter payload builder (utility function)
# ---------------------------------------------------------------------------

def build_rag_filter_metadata(prediction_result: dict) -> dict:
    """
    Build RAG filter metadata from a prediction result.
    Only 'accepted' predictions are eligible for hard RAG filtering.
    """
    status = prediction_result.get("status", STATUS_FAILED)
    use_for_filtering = status == STATUS_ACCEPTED

    if use_for_filtering:
        reason = "High confidence accepted prediction — safe to use as hard RAG filter"
    elif status == STATUS_NEEDS_REVIEW:
        reason = "Prediction is below confidence threshold (needs_review)"
    elif status == STATUS_WAITING_FOR_SOURCE:
        reason = "No prediction available (waiting_for_source)"
    elif status == STATUS_FAILED:
        reason = "Prediction failed (failed)"
    else:
        reason = f"Unknown status: {status}"

    return {
        "document_external_id": prediction_result.get("document_external_id"),
        "predicted_document_type": prediction_result.get("predicted_document_type"),
        "confidence": prediction_result.get("confidence", 0.0),
        "status": status,
        "use_for_rag_filtering": use_for_filtering,
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ACCEPTED_RESULT = {
    "document_external_id": "doc_policy_test",
    "predicted_document_type": "policy_document",
    "confidence": 0.91,
    "status": STATUS_ACCEPTED,
}

NEEDS_REVIEW_RESULT = {
    "document_external_id": "doc_report_test",
    "predicted_document_type": "report",
    "confidence": 0.45,
    "status": STATUS_NEEDS_REVIEW,
}

WAITING_RESULT = {
    "document_external_id": "doc_empty_test",
    "predicted_document_type": None,
    "confidence": 0.0,
    "status": STATUS_WAITING_FOR_SOURCE,
}

FAILED_RESULT = {
    "document_external_id": "doc_broken_test",
    "predicted_document_type": None,
    "confidence": 0.0,
    "status": STATUS_FAILED,
}

SUPPORTED_LABELS = [
    "contract", "financial_statement", "invoice",
    "policy_document", "report", "research_paper", "resume",
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_accepted_allows_rag_filtering():
    """Accepted predictions should allow hard RAG filtering."""
    metadata = build_rag_filter_metadata(ACCEPTED_RESULT)
    assert metadata["use_for_rag_filtering"] is True


def test_needs_review_blocks_rag_filtering():
    """Needs review predictions should NOT allow hard RAG filtering."""
    metadata = build_rag_filter_metadata(NEEDS_REVIEW_RESULT)
    assert metadata["use_for_rag_filtering"] is False


def test_waiting_for_source_blocks_rag_filtering():
    """Waiting for source should NOT allow hard RAG filtering."""
    metadata = build_rag_filter_metadata(WAITING_RESULT)
    assert metadata["use_for_rag_filtering"] is False


def test_failed_blocks_rag_filtering():
    """Failed predictions should NOT allow hard RAG filtering."""
    metadata = build_rag_filter_metadata(FAILED_RESULT)
    assert metadata["use_for_rag_filtering"] is False


def test_rag_metadata_contains_required_fields():
    """RAG metadata must contain all required fields."""
    metadata = build_rag_filter_metadata(ACCEPTED_RESULT)
    required = ["document_external_id", "predicted_document_type", "confidence",
                "status", "use_for_rag_filtering", "reason"]
    for field in required:
        assert field in metadata, f"Missing field: {field}"


def test_rag_metadata_preserves_document_external_id():
    """RAG metadata must preserve document_external_id."""
    metadata = build_rag_filter_metadata(ACCEPTED_RESULT)
    assert metadata["document_external_id"] == "doc_policy_test"


def test_rag_metadata_preserves_predicted_type():
    """RAG metadata must preserve predicted_document_type."""
    metadata = build_rag_filter_metadata(ACCEPTED_RESULT)
    assert metadata["predicted_document_type"] == "policy_document"


def test_rag_metadata_reason_for_accepted():
    """Accepted predictions must have a reason explaining safety."""
    metadata = build_rag_filter_metadata(ACCEPTED_RESULT)
    assert "safe" in metadata["reason"].lower() or "accepted" in metadata["reason"].lower()


def test_rag_metadata_reason_for_needs_review():
    """Needs review predictions must have a reason explaining why not filtered."""
    metadata = build_rag_filter_metadata(NEEDS_REVIEW_RESULT)
    assert "needs_review" in metadata["reason"]


def test_rag_filter_fixture_file_valid_json():
    """The RAG filter fixture file must be valid JSON."""
    fixture_path = os.path.join(_PROJECT_ROOT, "outputs", "rag_metadata", "document_type_filter_payload.json")
    if os.path.exists(fixture_path):
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0
    else:
        pytest.skip("RAG filter fixture file not found")


def test_rag_filter_fixture_has_required_fields():
    """Each item in RAG filter fixture must have required fields."""
    fixture_path = os.path.join(_PROJECT_ROOT, "outputs", "rag_metadata", "document_type_filter_payload.json")
    if os.path.exists(fixture_path):
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        required = ["document_external_id", "predicted_document_type", "confidence",
                    "status", "use_for_rag_filtering", "reason"]
        for item in data:
            for field in required:
                assert field in item, f"Missing field: {field} in item {item.get('document_external_id')}"
    else:
        pytest.skip("RAG filter fixture file not found")
