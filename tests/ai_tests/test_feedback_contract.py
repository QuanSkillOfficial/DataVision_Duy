"""
test_feedback_contract.py — Tests for human feedback/correction payload format.

Verifies that feedback correction payloads conform to the contract
defined in docs/prediction_feedback_contract.md.

Run with:
    python -m pytest tests/ai_tests/test_feedback_contract.py -v
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


# ---------------------------------------------------------------------------
# Feedback payload validation (utility function)
# ---------------------------------------------------------------------------

SUPPORTED_LABELS = [
    "contract", "financial_statement", "invoice",
    "policy_document", "report", "research_paper", "resume",
]

REQUIRED_FEEDBACK_FIELDS = [
    "prediction_log_id",
    "document_external_id",
    "predicted_document_type",
    "corrected_document_type",
    "corrected_by",
    "created_at",
]


def validate_feedback_payload(payload: dict) -> list[str]:
    """Validate a feedback correction payload. Returns list of errors."""
    errors = []

    for field in REQUIRED_FEEDBACK_FIELDS:
        if field not in payload:
            errors.append(f"Missing required field: '{field}'")

    if "corrected_document_type" in payload:
        if payload["corrected_document_type"] not in SUPPORTED_LABELS:
            errors.append(
                f"Invalid corrected_document_type: '{payload['corrected_document_type']}'. "
                f"Must be one of: {SUPPORTED_LABELS}"
            )

    if "corrected_by" in payload:
        if not str(payload["corrected_by"]).strip():
            errors.append("corrected_by must not be empty")

    if "prediction_log_id" in payload:
        if not isinstance(payload["prediction_log_id"], int):
            errors.append("prediction_log_id must be an integer")

    return errors


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_CORRECTION = {
    "prediction_log_id": 12,
    "document_external_id": "doc_contract_vendor_agreement_2024",
    "predicted_document_type": "report",
    "corrected_document_type": "contract",
    "corrected_by": "user",
    "correction_reason": "Manual review confirmed this is a contract",
    "created_at": "2026-07-05T10:00:00Z",
}

VALID_CONFIRMATION = {
    "prediction_log_id": 1,
    "document_external_id": "doc_dataflow_technical_report",
    "predicted_document_type": "report",
    "corrected_document_type": "report",
    "corrected_by": "user",
    "correction_reason": "Confirmed: this is a technical report",
    "created_at": "2026-07-05T10:15:00Z",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_valid_correction_has_no_errors():
    """Valid correction payload must pass validation."""
    errors = validate_feedback_payload(VALID_CORRECTION)
    assert errors == []


def test_valid_confirmation_has_no_errors():
    """Valid confirmation (same type) must pass validation."""
    errors = validate_feedback_payload(VALID_CONFIRMATION)
    assert errors == []


def test_missing_prediction_log_id():
    """Missing prediction_log_id must return error."""
    payload = {k: v for k, v in VALID_CORRECTION.items() if k != "prediction_log_id"}
    errors = validate_feedback_payload(payload)
    assert any("prediction_log_id" in e for e in errors)


def test_missing_document_external_id():
    """Missing document_external_id must return error."""
    payload = {k: v for k, v in VALID_CORRECTION.items() if k != "document_external_id"}
    errors = validate_feedback_payload(payload)
    assert any("document_external_id" in e for e in errors)


def test_missing_corrected_document_type():
    """Missing corrected_document_type must return error."""
    payload = {k: v for k, v in VALID_CORRECTION.items() if k != "corrected_document_type"}
    errors = validate_feedback_payload(payload)
    assert any("corrected_document_type" in e for e in errors)


def test_missing_corrected_by():
    """Missing corrected_by must return error."""
    payload = {k: v for k, v in VALID_CORRECTION.items() if k != "corrected_by"}
    errors = validate_feedback_payload(payload)
    assert any("corrected_by" in e for e in errors)


def test_invalid_document_type():
    """Invalid corrected_document_type must return error."""
    payload = {**VALID_CORRECTION, "corrected_document_type": "invalid_type"}
    errors = validate_feedback_payload(payload)
    assert any("Invalid corrected_document_type" in e for e in errors)


def test_empty_corrected_by():
    """Empty corrected_by must return error."""
    payload = {**VALID_CORRECTION, "corrected_by": "  "}
    errors = validate_feedback_payload(payload)
    assert any("corrected_by" in e for e in errors)


def test_non_integer_prediction_log_id():
    """Non-integer prediction_log_id must return error."""
    payload = {**VALID_CORRECTION, "prediction_log_id": "not_an_int"}
    errors = validate_feedback_payload(payload)
    assert any("prediction_log_id" in e for e in errors)


def test_all_supported_labels_accepted():
    """All 7 supported labels must be valid as corrected_document_type."""
    for label in SUPPORTED_LABELS:
        payload = {**VALID_CORRECTION, "corrected_document_type": label}
        errors = validate_feedback_payload(payload)
        assert errors == [], f"Label '{label}' should be valid but got errors: {errors}"


def test_correction_reason_is_optional():
    """correction_reason is optional — payload without it should be valid."""
    payload = {k: v for k, v in VALID_CORRECTION.items() if k != "correction_reason"}
    errors = validate_feedback_payload(payload)
    assert errors == []
