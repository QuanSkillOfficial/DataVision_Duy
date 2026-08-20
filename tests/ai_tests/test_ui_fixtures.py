"""
test_ui_fixtures.py — Tests for UI fixture file structure and validity.

Verifies that UI fixture files match the prediction UI response contract.

Run with:
    python -m pytest tests/ai_tests/test_ui_fixtures.py -v
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

from ai.prediction.feature_builder import VALID_STATUSES


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

FIXTURES_DIR = os.path.join(_PROJECT_ROOT, "outputs", "ui_fixtures")
SINGLE_FIXTURE = os.path.join(FIXTURES_DIR, "tuong_prediction_response_real.json")
BATCH_FIXTURE = os.path.join(FIXTURES_DIR, "tuong_prediction_batch_response.json")
REVIEW_FIXTURE = os.path.join(FIXTURES_DIR, "tuong_prediction_review_queue_sample.json")

RESPONSE_REQUIRED_FIELDS = [
    "predicted_document_type",
    "confidence",
    "status",
    "top_predictions",
    "model_version",
    "document_external_id",
    "source_name",
    "ingestion_run_id",
]

SUPPORTED_LABELS = [
    "contract", "financial_statement", "invoice",
    "policy_document", "report", "research_paper", "resume",
]


# ---------------------------------------------------------------------------
# Tests — Single Response Fixture
# ---------------------------------------------------------------------------

def test_single_fixture_exists():
    """Single prediction response fixture file must exist."""
    assert os.path.exists(SINGLE_FIXTURE), f"Missing: {SINGLE_FIXTURE}"


def test_single_fixture_valid_json():
    """Single fixture must be valid JSON."""
    with open(SINGLE_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_single_fixture_has_response():
    """Single fixture must have a 'response' key."""
    with open(SINGLE_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "response" in data


def test_single_fixture_response_has_required_fields():
    """Single fixture response must have all required fields."""
    with open(SINGLE_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    response = data["response"]
    for field in RESPONSE_REQUIRED_FIELDS:
        assert field in response, f"Missing field in single fixture: {field}"


def test_single_fixture_valid_status():
    """Single fixture must have a valid status."""
    with open(SINGLE_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["response"]["status"] in VALID_STATUSES


# ---------------------------------------------------------------------------
# Tests — Batch Response Fixture
# ---------------------------------------------------------------------------

def test_batch_fixture_exists():
    """Batch prediction response fixture file must exist."""
    assert os.path.exists(BATCH_FIXTURE), f"Missing: {BATCH_FIXTURE}"


def test_batch_fixture_valid_json():
    """Batch fixture must be valid JSON."""
    with open(BATCH_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_batch_fixture_has_results():
    """Batch fixture must have exactly 20 real prediction results."""
    with open(BATCH_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 20, (
        f"Batch fixture must contain all 20 real Duy prediction results, "
        f"got {len(data['results'])}"
    )


def test_batch_fixture_results_have_required_fields():
    """Each batch result must have all required fields."""
    with open(BATCH_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for i, result in enumerate(data["results"]):
        for field in RESPONSE_REQUIRED_FIELDS:
            assert field in result, f"Result {i} missing field: {field}"


def test_batch_fixture_covers_all_statuses():
    """Real results plus explicit UI examples must cover all 4 statuses."""
    with open(BATCH_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    statuses = {r["status"] for r in data["results"]}
    statuses.update(r["status"] for r in data.get("status_examples", []))
    for status in VALID_STATUSES:
        assert status in statuses, f"Batch fixture missing status: {status}"


def test_fixture_only_examples_are_not_mixed_into_real_results():
    """Synthetic UI coverage must stay separate from the real prediction batch."""
    with open(BATCH_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert all(result.get("fixture_only") is False for result in data["results"])
    for example in data.get("status_examples", []):
        if example.get("fixture_only"):
            assert example.get("fixture_reason")


def test_batch_fixture_valid_statuses():
    """All batch results must have valid statuses."""
    with open(BATCH_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for result in data["results"]:
        assert result["status"] in VALID_STATUSES, f"Invalid status: {result['status']}"


# ---------------------------------------------------------------------------
# Tests — Review Queue Fixture
# ---------------------------------------------------------------------------

def test_review_fixture_exists():
    """Review queue fixture file must exist."""
    assert os.path.exists(REVIEW_FIXTURE), f"Missing: {REVIEW_FIXTURE}"


def test_review_fixture_valid_json():
    """Review queue fixture must be valid JSON."""
    with open(REVIEW_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_review_fixture_has_review_items():
    """Review queue fixture must have 'review_items' list with exactly 15 items."""
    with open(REVIEW_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "review_items" in data
    assert isinstance(data["review_items"], list)
    assert len(data["review_items"]) == 15, (
        f"Review queue must contain at least 15 items from real Duy predictions, "
        f"got {len(data['review_items'])}"
    )


def test_review_fixture_items_are_needs_review():
    """All review queue items must have status 'needs_review'."""
    with open(REVIEW_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data["review_items"]:
        assert item["status"] == "needs_review", f"Review queue item should be needs_review, got: {item['status']}"


def test_review_fixture_items_have_correction_fields():
    """Review queue items must have correction tracking fields."""
    with open(REVIEW_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data["review_items"]:
        assert "reviewed" in item
        assert "corrected_document_type" in item
        assert "corrected_by" in item


def test_review_fixture_has_supported_types():
    """Review queue fixture must list supported document types."""
    with open(REVIEW_FIXTURE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "supported_document_types" in data
    assert set(data["supported_document_types"]) == set(SUPPORTED_LABELS)
