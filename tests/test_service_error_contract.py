"""
tests/test_service_error_contract.py
======================================
DV-HUNG-05: timeout, unavailable-backend and partial-service behavior.

These tests pin the error contract that the UI depends on. If a backend
failure stops being classified, the UI silently loses its actionable message,
so these assertions guard the user-visible behavior, not just the plumbing.
"""

from unittest.mock import patch

import pytest
import requests

from demo.services import backend_client
from demo.services.service_errors import (
    ERROR_HTTP,
    ERROR_INVALID_PAYLOAD,
    ERROR_TIMEOUT,
    ERROR_UNAVAILABLE,
    describe_error,
    error_detail,
    error_hint,
    error_kind,
    error_message,
    is_error,
)


# ──────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION OF TRANSPORT FAILURES
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "exception, expected_kind",
    [
        (requests.Timeout("read timed out"), ERROR_TIMEOUT),
        (requests.ConnectionError("connection refused"), ERROR_UNAVAILABLE),
    ],
)
def test_transport_failures_are_classified(exception, expected_kind):
    with patch("demo.services.backend_client.requests.request", side_effect=exception):
        response = backend_client.get_dashboard_metrics()

    assert is_error(response)
    assert error_kind(response) == expected_kind
    assert response["data"] is None
    assert response["status"] == "error"


def test_timeout_and_unavailable_have_different_guidance():
    """A dead host and a slow host need different operator actions."""
    with patch(
        "demo.services.backend_client.requests.request",
        side_effect=requests.Timeout("read timed out"),
    ):
        timeout_response = backend_client.ask_rag("q")
    with patch(
        "demo.services.backend_client.requests.request",
        side_effect=requests.ConnectionError("refused"),
    ):
        unavailable_response = backend_client.ask_rag("q")

    assert error_hint(timeout_response) != error_hint(unavailable_response)
    assert error_hint(timeout_response).strip()
    assert error_hint(unavailable_response).strip()


def test_failed_request_records_endpoint_for_evidence():
    with patch(
        "demo.services.backend_client.requests.request",
        side_effect=requests.ConnectionError("refused"),
    ):
        response = backend_client.classify_document({})

    assert response["metadata"]["endpoint"] == "/predict/document-type"
    assert isinstance(response["metadata"]["elapsed_ms"], int)


# ──────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION OF PROTOCOL FAILURES
# ──────────────────────────────────────────────────────────────────────────────

class _FakeResponse:
    def __init__(self, status_code, payload, raise_value_error=False):
        self.status_code = status_code
        self._payload = payload
        self._raise = raise_value_error

    def json(self):
        if self._raise:
            raise ValueError("no json object could be decoded")
        return self._payload


@pytest.mark.parametrize(
    "fake, expected_kind",
    [
        (_FakeResponse(500, {"detail": "boom"}), ERROR_HTTP),
        (_FakeResponse(200, None, raise_value_error=True), ERROR_INVALID_PAYLOAD),
        (_FakeResponse(200, ["not", "an", "object"]), ERROR_INVALID_PAYLOAD),
        (_FakeResponse(200, {"data": {}}), ERROR_INVALID_PAYLOAD),
        (_FakeResponse(200, {"data": None, "status": "error"}), ERROR_HTTP),
    ],
)
def test_protocol_failures_are_classified(fake, expected_kind):
    with patch("demo.services.backend_client.requests.request", return_value=fake):
        response = backend_client.get_recent_activity()

    assert is_error(response)
    assert error_kind(response) == expected_kind


def test_successful_response_is_not_an_error():
    fake = _FakeResponse(200, {"data": {"ok": True}, "status": "success"})
    with patch("demo.services.backend_client.requests.request", return_value=fake):
        response = backend_client.get_backend_health()

    assert not is_error(response)
    assert response["data"] == {"ok": True}
    assert response["metadata"]["endpoint"] == "/health"


def test_success_envelope_with_null_data_is_treated_as_a_failure():
    """A 200 with no payload must not render as an empty but valid page."""
    fake = _FakeResponse(200, {"data": None, "status": "success"})
    with patch("demo.services.backend_client.requests.request", return_value=fake):
        response = backend_client.get_dashboard_metrics()

    assert is_error(response)


# ──────────────────────────────────────────────────────────────────────────────
# MESSAGE QUALITY
# ──────────────────────────────────────────────────────────────────────────────

def test_describe_error_is_complete_enough_for_the_ui():
    with patch(
        "demo.services.backend_client.requests.request",
        side_effect=requests.Timeout("read timed out"),
    ):
        response = backend_client.generate_report({})

    described = describe_error(response, "Report service")
    assert described["service"] == "Report service"
    assert described["kind"] == ERROR_TIMEOUT
    assert described["message"]
    assert described["hint"]
    assert described["endpoint"] == "/reports/generate"


def test_error_helpers_tolerate_non_dict_responses():
    """The UI must not crash on a malformed client response."""
    assert is_error("not a dict")
    assert error_kind("not a dict") == ERROR_INVALID_PAYLOAD
    assert error_message("not a dict", "fallback") == "fallback"
    assert error_detail("not a dict") == "not a dict"
    assert error_hint(None)
