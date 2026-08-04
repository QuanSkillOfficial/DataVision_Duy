"""
test_prediction_service.py — Tests for prediction service wrapper.

Run with:
    python -m pytest tests/ai_tests/test_prediction_service.py -v
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

from ai.prediction.prediction_service import classify_document, classify_documents
from ai.prediction.inference import reset_model_cache

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

DUY_STYLE_PAYLOAD = {
    "document_external_id": "doc_dataflow_technical_report",
    "source_name": "dataflow_technical_report_pdf",
    "ingestion_run_id": "a58bf6df-2dec-41ca-a18b-784c68eab826",
    "file_name": "DataFlow_Technical_Report_2024.pdf",
    "file_type": "pdf",
    "file_size": 3200000,
    "text_length": 15200,
    "num_pages": 28,
    "source_system": "manual_upload",
    "extracted_text": (
        "DataFlow Technical Report 2024. This document provides a comprehensive "
        "overview of the DataFlow platform architecture, including data ingestion "
        "pipelines, transformation layers, storage solutions, and API gateway design. "
        "The system processes over 10,000 documents daily with automated classification, "
        "metadata extraction, and full-text indexing."
    ),
}

SHORT_TEXT_PAYLOAD = {
    "file_name": "empty.pdf",
    "file_type": "pdf",
    "file_size": 100,
    "text_length": 5,
    "num_pages": 1,
    "source_system": "manual_upload",
    "extracted_text": "short",
}


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset model cache before each test."""
    reset_model_cache()
    yield
    reset_model_cache()


# ---------------------------------------------------------------------------
# Tests: classify_document
# ---------------------------------------------------------------------------

def test_classify_document_returns_dict():
    """classify_document must return a dict."""
    result = classify_document(VALID_PAYLOAD)
    assert isinstance(result, dict)


def test_classify_document_returns_prediction():
    """classify_document must return predicted_document_type."""
    result = classify_document(VALID_PAYLOAD)
    assert "predicted_document_type" in result
    assert isinstance(result["predicted_document_type"], str)


def test_classify_document_returns_confidence():
    """classify_document must return a confidence score."""
    result = classify_document(VALID_PAYLOAD)
    assert "confidence" in result
    assert isinstance(result["confidence"], float)
    assert 0.0 < result["confidence"] <= 1.0


def test_classify_document_returns_status():
    """classify_document must return a valid status."""
    result = classify_document(VALID_PAYLOAD)
    assert "status" in result
    assert result["status"] in ("accepted", "needs_review", "waiting_for_source", "failed")


def test_classify_document_returns_top_predictions():
    """classify_document must return top_predictions."""
    result = classify_document(VALID_PAYLOAD)
    assert "top_predictions" in result
    assert isinstance(result["top_predictions"], list)


def test_classify_document_returns_model_version():
    """classify_document must return model_version."""
    result = classify_document(VALID_PAYLOAD)
    assert "model_version" in result
    assert isinstance(result["model_version"], str)


def test_classify_document_short_text_returns_waiting():
    """classify_document with short text should return waiting_for_source."""
    result = classify_document(SHORT_TEXT_PAYLOAD)
    assert result["status"] == "waiting_for_source"
    assert result["predicted_document_type"] is None
    assert result["confidence"] == 0.0


def test_classify_document_missing_field_returns_error():
    """classify_document with missing field should return error."""
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "file_name"}
    result = classify_document(payload)
    assert "error" in result


# ---------------------------------------------------------------------------
# Tests: classify_documents (batch)
# ---------------------------------------------------------------------------

def test_classify_documents_returns_list():
    """classify_documents must return a list."""
    results = classify_documents([VALID_PAYLOAD])
    assert isinstance(results, list)


def test_classify_documents_correct_count():
    """classify_documents must return one result per input."""
    results = classify_documents([VALID_PAYLOAD, VALID_PAYLOAD])
    assert len(results) == 2


def test_classify_documents_empty_list():
    """classify_documents with empty list returns empty list."""
    results = classify_documents([])
    assert results == []


# ---------------------------------------------------------------------------
# Tests: Duy-style payload
# ---------------------------------------------------------------------------

def test_duy_style_payload_works():
    """A Duy-style payload (with document_external_id, source_name) must produce a valid prediction."""
    result = classify_document(DUY_STYLE_PAYLOAD)
    assert "error" not in result
    assert "predicted_document_type" in result
    assert "confidence" in result
    assert "status" in result
    assert result["status"] in ("accepted", "needs_review")


def test_duy_style_payload_in_batch():
    """Duy-style payloads in batch should preserve document_external_id and source_name."""
    results = classify_documents([DUY_STYLE_PAYLOAD])
    assert results[0]["document_external_id"] == "doc_dataflow_technical_report"
    assert results[0]["source_name"] == "dataflow_technical_report_pdf"
    assert results[0]["ingestion_run_id"] == "a58bf6df-2dec-41ca-a18b-784c68eab826"
    assert "predicted_document_type" in results[0]
