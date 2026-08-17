"""
tests/test_backend_contract_smoke.py
======================================
Backend API contract smoke tests.

These tests only run when the demo is configured in Backend Mode
(USE_BACKEND = True, typically set via the QS_USE_BACKEND environment
variable). In Mock Fixture Mode (the default), all tests in this module
are automatically skipped.

To run against a live FastAPI server:
    $env:QS_USE_BACKEND="true"; .venv\\Scripts\\pytest tests/test_backend_contract_smoke.py

These tests verify the HTTP contract (not the full business logic) —
each test checks:
  - The response is a dict with the required envelope keys.
  - The top-level `status` field is not `"error"`.
  - The `data` field is non-None.
"""

import os

import pytest

from demo.config import USE_BACKEND
from demo.services import backend_client

# ──────────────────────────────────────────────────────────────────────────────
# Skip policy (DV-HUNG-01)
# ──────────────────────────────────────────────────────────────────────────────
# By default this module skips in Mock Fixture Mode, so day-to-day UI work does
# not require a running backend.
#
# The release workflow sets QS_REQUIRE_BACKEND_TESTS=true. In that mode the
# module must never skip: a missing backend has to fail the release candidate
# instead of quietly producing a green run with no integration evidence.
# ──────────────────────────────────────────────────────────────────────────────

REQUIRE_BACKEND_TESTS = (
    os.environ.get("QS_REQUIRE_BACKEND_TESTS", "false").lower() == "true"
)

_BACKEND_REQUIRED = pytest.mark.skipif(
    not USE_BACKEND and not REQUIRE_BACKEND_TESTS,
    reason="Backend smoke tests only run when USE_BACKEND=True (QS_USE_BACKEND=true).",
)


def test_backend_mode_is_enabled_when_required():
    """Fail closed when the release workflow demands backend-mode evidence.

    This test is never skipped, so a release candidate cannot be accepted on a
    run where the UI-to-backend contract was silently not exercised.
    """
    if not REQUIRE_BACKEND_TESTS:
        pytest.skip(
            "Set QS_REQUIRE_BACKEND_TESTS=true to enforce backend-mode evidence."
        )
    assert USE_BACKEND, (
        "QS_REQUIRE_BACKEND_TESTS=true but QS_USE_BACKEND is not true. "
        "The release candidate workflow requires real UI-to-backend contract "
        "tests, not fixture-mode substitution."
    )


@pytest.fixture(autouse=True)
def _fail_closed_without_backend_mode():
    """Prevent required backend tests from running against fixtures."""
    if REQUIRE_BACKEND_TESTS and not USE_BACKEND:
        pytest.fail(
            "Backend-mode evidence was required but the UI is in fixture mode. "
            "Set QS_USE_BACKEND=true and point QS_BACKEND_URL at the release backend."
        )


# ──────────────────────────────────────────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────────────────────────────────────────

def _assert_valid_envelope(response: dict, label: str) -> None:
    """Assert the response matches the expected envelope shape."""
    assert isinstance(response, dict), f"{label}: response must be a dict"
    assert "data" in response, f"{label}: missing 'data' key"
    assert "status" in response, f"{label}: missing 'status' key"
    assert response["data"] is not None, f"{label}: 'data' must not be None"
    assert response["status"] != "error", (
        f"{label}: status is 'error' — backend returned: {response}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# HEALTH AND RELEASE IDENTITY (DV-HUNG-04)
# ──────────────────────────────────────────────────────────────────────────────

@_BACKEND_REQUIRED
def test_backend_health_returns_envelope():
    """GET /api/health returns a valid response envelope."""
    response = backend_client.get_backend_health()
    _assert_valid_envelope(response, "get_backend_health")


@_BACKEND_REQUIRED
def test_backend_health_exposes_release_identity_fields():
    """Health must let the UI header name the release it is talking to.

    A backend that only serves repository fixtures has no release to report, and
    says so: the integrated backend sets ``metadata.mode`` or ``data.mode`` to
    "fixture", and the UI then renders release_match as "unknown" rather than
    claiming a match. What must never happen is a backend presenting itself as a
    real deployment while hiding which build it is, so the SHA is required in
    every other mode.

    `ok` is deliberately not required. Nothing consumes it - the UI reads
    service, release_sha and environment - and the integrated backend spells
    liveness `healthy`, so demanding both names would test nothing. Liveness is
    already covered by the envelope status.
    """
    response = backend_client.get_backend_health()
    _assert_valid_envelope(response, "get_backend_health (identity)")
    data = response["data"]
    metadata = response.get("metadata") or {}

    assert "service" in data, "get_backend_health: missing field 'service'"

    serves_fixtures = "fixture" in {
        str(metadata.get("mode", "")).lower(),
        str(data.get("mode", "")).lower(),
    }
    if serves_fixtures:
        return

    assert data.get("release_sha"), (
        "get_backend_health: a backend that does not declare fixture mode must "
        f"report the release it is serving; got {data!r}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD (Duy + Phat)
# ──────────────────────────────────────────────────────────────────────────────

@_BACKEND_REQUIRED
def test_backend_get_dashboard_metrics_returns_envelope():
    """GET /api/dashboard/metrics returns a valid response envelope."""
    response = backend_client.get_dashboard_metrics()
    _assert_valid_envelope(response, "get_dashboard_metrics")


@_BACKEND_REQUIRED
def test_backend_get_dashboard_metrics_with_source_context():
    """GET /api/dashboard/metrics with source_context payload returns valid data."""
    sources = [{"filename": "test.pdf"}, {"filename": "data.csv"}]
    response = backend_client.get_dashboard_metrics(sources)
    _assert_valid_envelope(response, "get_dashboard_metrics (with source_context)")


@_BACKEND_REQUIRED
def test_backend_get_ingestion_status_returns_envelope():
    """GET /api/ingestion/status returns a valid response envelope."""
    response = backend_client.get_ingestion_status()
    _assert_valid_envelope(response, "get_ingestion_status")


@_BACKEND_REQUIRED
def test_backend_get_recent_activity_returns_list():
    """GET /api/dashboard/recent-activity returns a list inside the data field."""
    response = backend_client.get_recent_activity()
    _assert_valid_envelope(response, "get_recent_activity")
    assert isinstance(response["data"], list), (
        "get_recent_activity: 'data' must be a list"
    )


# ──────────────────────────────────────────────────────────────────────────────
# PREDICTION (Tuong)
# ──────────────────────────────────────────────────────────────────────────────

# Minimal valid payload per prediction_ui_contract.md
_VALID_CLASSIFY_PAYLOAD = {
    "document_id": "smoke-doc-001",
    "source_id": "smoke-src-001",
    "file_name": "smoke_test.pdf",
    "file_type": "pdf",
    "file_size": 10240,
    "text_length": 500,
    "num_pages": 2,
    "source_system": "smoke_test",
    "extracted_text": "This is a smoke test document with enough text to classify.",
}


@_BACKEND_REQUIRED
def test_backend_classify_document_returns_envelope():
    """POST /api/predict/document-type returns a valid response envelope."""
    response = backend_client.classify_document(_VALID_CLASSIFY_PAYLOAD)
    _assert_valid_envelope(response, "classify_document")


@_BACKEND_REQUIRED
def test_backend_classify_document_has_required_fields():
    """classify_document data contains the required prediction fields."""
    response = backend_client.classify_document(_VALID_CLASSIFY_PAYLOAD)
    _assert_valid_envelope(response, "classify_document (field check)")
    data = response["data"]
    required_fields = [
        "predicted_document_type",
        "confidence",
        "model_version",
        "status",
        "review_reason",
        "top_predictions",
    ]
    for field in required_fields:
        assert field in data, f"classify_document: missing field '{field}'"


@_BACKEND_REQUIRED
def test_backend_classify_document_status_is_valid():
    """classify_document status must be one of the 4 canonical values."""
    response = backend_client.classify_document(_VALID_CLASSIFY_PAYLOAD)
    valid_statuses = {"accepted", "needs_review", "waiting_for_source", "failed"}
    status_value = response["data"].get("status")
    assert status_value in valid_statuses, (
        f"classify_document: status '{status_value}' not in {valid_statuses}"
    )


@_BACKEND_REQUIRED
def test_backend_classify_documents_batch_returns_list():
    """POST /api/predict/document-type/batch returns a list in the data field."""
    response = backend_client.classify_documents([_VALID_CLASSIFY_PAYLOAD])
    _assert_valid_envelope(response, "classify_documents")
    assert isinstance(response["data"], list), (
        "classify_documents: 'data' must be a list"
    )


# ──────────────────────────────────────────────────────────────────────────────
# RAG / CHATBOT (Lap)
# ──────────────────────────────────────────────────────────────────────────────

@_BACKEND_REQUIRED
def test_backend_ask_rag_returns_envelope():
    """POST /api/rag/query returns a valid response envelope."""
    response = backend_client.ask_rag("What is the refund policy?")
    _assert_valid_envelope(response, "ask_rag")


@_BACKEND_REQUIRED
def test_backend_ask_rag_has_required_fields():
    """ask_rag data contains the required RAG response fields."""
    response = backend_client.ask_rag("What is the refund policy?")
    _assert_valid_envelope(response, "ask_rag (field check)")
    data = response["data"]
    required_fields = ["question", "answer", "citations", "retrieved_context", "status"]
    for field in required_fields:
        assert field in data, f"ask_rag: missing field '{field}'"


@_BACKEND_REQUIRED
def test_backend_ask_rag_status_is_valid():
    """ask_rag status must be one the UI knows how to render.

    "retrieval_only" is in the set because the integrated RAG service returns it:
    chunks were retrieved but no answer was generated. It is a real state of the
    contract, not a failure, and the UI must render it rather than treat it as an
    unknown status. Whether a retrieval-only answer may be *accepted* for a
    release is a separate question and a separate gate - the review requires
    staging acceptance to reject fallback-only answers (DV-LAP-03) - so it is not
    decided here.
    """
    response = backend_client.ask_rag("What is the refund policy?")
    valid_statuses = {"success", "no_match", "error", "retrieval_only"}
    status_value = response["data"].get("status")
    assert status_value in valid_statuses, (
        f"ask_rag: status '{status_value}' not in {valid_statuses}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# SUGGESTIONS (Phi/Hung aggregation)
# ──────────────────────────────────────────────────────────────────────────────

@_BACKEND_REQUIRED
def test_backend_generate_suggestions_returns_envelope():
    """POST /api/suggestions/generate returns a valid response envelope."""
    response = backend_client.generate_suggestions({})
    _assert_valid_envelope(response, "generate_suggestions")


@_BACKEND_REQUIRED
def test_backend_generate_suggestions_returns_list():
    """generate_suggestions data must be a list."""
    response = backend_client.generate_suggestions({})
    _assert_valid_envelope(response, "generate_suggestions (list check)")
    assert isinstance(response["data"], list), (
        "generate_suggestions: 'data' must be a list"
    )


# ──────────────────────────────────────────────────────────────────────────────
# REPORTS (Phi/Hung)
# ──────────────────────────────────────────────────────────────────────────────

@_BACKEND_REQUIRED
def test_backend_generate_report_returns_envelope():
    """POST /api/reports/generate returns a valid response envelope."""
    response = backend_client.generate_report({})
    _assert_valid_envelope(response, "generate_report")


@_BACKEND_REQUIRED
def test_backend_generate_report_has_sections():
    """generate_report data contains 'title' and 'sections' fields."""
    response = backend_client.generate_report({
        "domain_label": "Business",
        "report_type": "Smoke Test Summary",
        "audience": "General",
    })
    _assert_valid_envelope(response, "generate_report (sections check)")
    data = response["data"]
    assert "title" in data, "generate_report: missing 'title'"
    assert "sections" in data, "generate_report: missing 'sections'"
    assert isinstance(data["sections"], list), "generate_report: 'sections' must be a list"
