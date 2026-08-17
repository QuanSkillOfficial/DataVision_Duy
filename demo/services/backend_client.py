"""
demo/services/backend_client.py
=================================
Real backend implementation of the platform service API.

Calls the FastAPI backend over HTTP. Every function mirrors the exact
signature of the corresponding function in mock_client.py so that
service_client.py can swap between the two without any page-level changes.

This module is never imported directly by page code — always go through
`service_client.py`.

NOTE: This module requires a running FastAPI backend at
demo.config.BACKEND_BASE_URL. Until the backend exists, set
USE_BACKEND = False in demo/config.py to use mock_client.py instead.
"""

from __future__ import annotations

import time
from typing import List, Optional

import requests

from demo.config import (
    BACKEND_BASE_URL,
    BACKEND_CONNECT_TIMEOUT_SECONDS,
    BACKEND_READ_TIMEOUT_SECONDS,
)
from demo.services.service_errors import (
    ERROR_HTTP,
    ERROR_INVALID_PAYLOAD,
    ERROR_TIMEOUT,
    ERROR_UNAVAILABLE,
    ERROR_UNKNOWN,
)


_TIMEOUT = (BACKEND_CONNECT_TIMEOUT_SECONDS, BACKEND_READ_TIMEOUT_SECONDS)


def _error_response(
    message: str,
    detail: str,
    status_code: Optional[int] = None,
    kind: str = ERROR_UNKNOWN,
    endpoint: Optional[str] = None,
    elapsed_ms: Optional[int] = None,
) -> dict:
    metadata = {"error": detail, "error_kind": kind}
    if status_code is not None:
        metadata["status_code"] = status_code
    if endpoint is not None:
        metadata["endpoint"] = endpoint
    if elapsed_ms is not None:
        metadata["elapsed_ms"] = elapsed_ms
    return {
        "data": None,
        "status": "error",
        "error": {
            "message": message,
            "detail": detail,
            "kind": kind,
        },
        "metadata": metadata,
    }


def _normalize_response(
    resp: requests.Response,
    endpoint: Optional[str] = None,
    elapsed_ms: Optional[int] = None,
) -> dict:
    def fail(message: str, detail: str, kind: str) -> dict:
        return _error_response(
            message,
            detail,
            resp.status_code,
            kind=kind,
            endpoint=endpoint,
            elapsed_ms=elapsed_ms,
        )

    try:
        payload = resp.json()
    except ValueError as exc:
        return fail("Backend returned invalid JSON", str(exc), ERROR_INVALID_PAYLOAD)

    if resp.status_code >= 400:
        return fail("Backend returned an error response", str(payload), ERROR_HTTP)

    if not isinstance(payload, dict):
        return fail(
            "Backend response envelope is invalid",
            "Response JSON must be an object.",
            ERROR_INVALID_PAYLOAD,
        )

    if "data" not in payload or "status" not in payload:
        return fail(
            "Backend response envelope is missing required fields",
            "Expected top-level keys: data, status, metadata.",
            ERROR_INVALID_PAYLOAD,
        )

    if payload.get("status") == "error":
        return fail(
            "Backend returned an error response",
            str(payload.get("error") or payload.get("metadata") or payload),
            ERROR_HTTP,
        )

    metadata = payload.setdefault("metadata", {})
    if isinstance(metadata, dict):
        metadata.setdefault("endpoint", endpoint)
        if elapsed_ms is not None:
            metadata.setdefault("elapsed_ms", elapsed_ms)
    return payload


def _request(method: str, path: str, **kwargs) -> dict:
    """Single entry point so every backend call is classified the same way."""
    started = time.perf_counter()

    def elapsed_ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    try:
        resp = requests.request(
            method,
            f"{BACKEND_BASE_URL}{path}",
            timeout=_TIMEOUT,
            **kwargs,
        )
        return _normalize_response(resp, endpoint=path, elapsed_ms=elapsed_ms())
    except requests.Timeout as exc:
        return _error_response(
            "Backend request timed out",
            str(exc),
            kind=ERROR_TIMEOUT,
            endpoint=path,
            elapsed_ms=elapsed_ms(),
        )
    except requests.ConnectionError as exc:
        return _error_response(
            "Backend unavailable",
            str(exc),
            kind=ERROR_UNAVAILABLE,
            endpoint=path,
            elapsed_ms=elapsed_ms(),
        )
    except requests.RequestException as exc:
        return _error_response(
            "Backend request failed",
            str(exc),
            kind=ERROR_UNKNOWN,
            endpoint=path,
            elapsed_ms=elapsed_ms(),
        )


_JSON_PRIMITIVES = (str, int, float, bool, type(None))


def _json_safe(value):
    """Make a UI payload safe to serialise.

    Session state carries objects the JSON encoder cannot handle - most
    importantly the raw bytes of an uploaded file, which `source_context`
    stores under "content". Those bytes are never part of a metadata call, so
    they are replaced by their size rather than being sent or crashing the page.
    """
    if isinstance(value, _JSON_PRIMITIVES):
        return value
    if isinstance(value, (bytes, bytearray)):
        return {"omitted": "binary", "byte_length": len(value)}
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _get(path: str, params: Optional[dict] = None) -> dict:
    return _request("GET", path, params=params)


def _post(path: str, payload: Optional[dict] = None) -> dict:
    return _request("POST", path, json=_json_safe(payload or {}))


# ─────────────────────────────────────────────
# HEALTH / RELEASE IDENTITY (DV-HUNG-04)
# ─────────────────────────────────────────────

def get_backend_health() -> dict:
    """Returns backend liveness plus whatever release identity it reports."""
    return _get("/health")


# ─────────────────────────────────────────────
# DASHBOARD (Duy + Phat)
# ─────────────────────────────────────────────

def get_dashboard_metrics(source_context: Optional[List[dict]] = None) -> dict:
    return _post("/dashboard/metrics", {"source_context": source_context or []})


def get_ingestion_status(run_id: Optional[str] = None) -> dict:
    return _get("/ingestion/status", {"run_id": run_id} if run_id else None)


def get_recent_activity() -> dict:
    return _get("/dashboard/recent-activity")


# ─────────────────────────────────────────────
# PREDICTION (Tuong)
# ─────────────────────────────────────────────

def classify_document(input_payload: dict) -> dict:
    return _post("/predict/document-type", input_payload)


def classify_documents(input_payloads: List[dict]) -> dict:
    return _post("/predict/document-type/batch", {"items": input_payloads})


def submit_prediction_correction(payload: dict) -> dict:
    return _post("/predict/feedback", payload)


# ─────────────────────────────────────────────
# RAG / CHATBOT (Lap)
# ─────────────────────────────────────────────

def ask_rag(question: str, document_id: Optional[str] = None) -> dict:
    return _post("/rag/query", {"question": question, "document_id": document_id})


# ─────────────────────────────────────────────
# SUGGESTIONS
# ─────────────────────────────────────────────

def generate_suggestions(context: Optional[dict] = None) -> dict:
    return _post("/suggestions/generate", context or {})


# ─────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────

def generate_report(evidence_context: Optional[dict] = None) -> dict:
    return _post("/reports/generate", evidence_context or {})
