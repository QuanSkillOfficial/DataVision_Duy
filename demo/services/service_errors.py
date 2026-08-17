"""
demo/services/service_errors.py
=================================
Shared vocabulary for service failures (DV-HUNG-05).

Every response returned by `service_client.py` uses the same envelope:

    {"data": ..., "status": "success"|"error", "error": {...}, "metadata": {...}}

This module is the single place that decides:

  - whether a response is a failure,
  - what *kind* of failure it is,
  - what the user should actually do about it.

It deliberately contains no Streamlit imports so it can be unit tested and
reused by CI scripts. Rendering lives in `demo/helpers/ui_status.py`.
"""

from __future__ import annotations

from typing import Any, Optional

# ─────────────────────────────────────────────
# ERROR KINDS
# ─────────────────────────────────────────────

ERROR_TIMEOUT = "timeout"
ERROR_UNAVAILABLE = "unavailable"
ERROR_HTTP = "http_error"
ERROR_INVALID_PAYLOAD = "invalid_payload"
ERROR_UNKNOWN = "unknown"

# What the reviewer/operator should do next, per failure kind. These are shown
# verbatim in the UI, so they must be actionable rather than decorative.
ERROR_HINTS = {
    ERROR_TIMEOUT: (
        "The backend accepted the connection but did not answer in time. "
        "Check backend load and the QS_BACKEND_READ_TIMEOUT setting, then retry."
    ),
    ERROR_UNAVAILABLE: (
        "The backend could not be reached at all. Verify the service is running "
        "and that QS_BACKEND_URL points at the deployed release."
    ),
    ERROR_HTTP: (
        "The backend answered with an error status. Check the backend logs for "
        "this endpoint and confirm the UI and backend run the same release."
    ),
    ERROR_INVALID_PAYLOAD: (
        "The backend answered, but the response did not match the agreed UI "
        "contract. Treat this as a contract mismatch between UI and backend, "
        "not as a UI display bug."
    ),
    ERROR_UNKNOWN: (
        "The request failed for an unclassified reason. Check backend logs and "
        "the UI console output for this endpoint."
    ),
}


def is_error(response: Any) -> bool:
    """True when the response is not a usable success envelope."""
    if not isinstance(response, dict):
        return True
    if response.get("status") == "error":
        return True
    return response.get("data") is None


def error_kind(response: Any) -> str:
    """Return the classified failure kind for an error response."""
    if not isinstance(response, dict):
        return ERROR_INVALID_PAYLOAD
    metadata = response.get("metadata") or {}
    kind = metadata.get("error_kind")
    if kind in ERROR_HINTS:
        return kind
    return ERROR_UNKNOWN


def error_message(response: Any, fallback: str = "Service request failed") -> str:
    """Short, human-readable statement of what went wrong."""
    if not isinstance(response, dict):
        return fallback
    error = response.get("error")
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])
    metadata = response.get("metadata") or {}
    if metadata.get("error"):
        return str(metadata["error"])
    return fallback


def error_detail(response: Any) -> str:
    """Raw technical detail, useful for logs and PR evidence."""
    if not isinstance(response, dict):
        return str(response)
    error = response.get("error")
    if isinstance(error, dict) and error.get("detail"):
        return str(error["detail"])
    metadata = response.get("metadata") or {}
    return str(metadata.get("error", ""))


def error_hint(response: Any) -> str:
    """Actionable next step for the classified failure kind."""
    return ERROR_HINTS[error_kind(response)]


def error_endpoint(response: Any) -> Optional[str]:
    """The backend path that failed, when the client recorded it."""
    if not isinstance(response, dict):
        return None
    metadata = response.get("metadata") or {}
    endpoint = metadata.get("endpoint")
    return str(endpoint) if endpoint else None


def describe_error(response: Any, service_label: str) -> dict:
    """Full description used by the UI and by CI evidence output."""
    return {
        "service": service_label,
        "kind": error_kind(response),
        "message": error_message(response),
        "detail": error_detail(response),
        "hint": error_hint(response),
        "endpoint": error_endpoint(response),
    }
