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

from typing import List, Optional

import requests

from demo.config import BACKEND_BASE_URL, BACKEND_TIMEOUT_SECONDS


def _error_response(message: str, detail: str, status_code: Optional[int] = None) -> dict:
    metadata = {"error": detail}
    if status_code is not None:
        metadata["status_code"] = status_code
    return {
        "data": None,
        "status": "error",
        "error": {
            "message": message,
            "detail": detail,
        },
        "metadata": metadata,
    }


def _normalize_response(resp: requests.Response) -> dict:
    try:
        payload = resp.json()
    except ValueError as exc:
        return _error_response(
            "Backend returned invalid JSON",
            str(exc),
            resp.status_code,
        )

    if resp.status_code >= 400:
        return _error_response(
            "Backend returned an error response",
            str(payload),
            resp.status_code,
        )

    if not isinstance(payload, dict):
        return _error_response(
            "Backend response envelope is invalid",
            "Response JSON must be an object.",
            resp.status_code,
        )

    if "data" not in payload or "status" not in payload:
        return _error_response(
            "Backend response envelope is missing required fields",
            "Expected top-level keys: data, status, metadata.",
            resp.status_code,
        )

    if payload.get("status") == "error":
        return _error_response(
            "Backend returned an error response",
            str(payload.get("error") or payload.get("metadata") or payload),
            resp.status_code,
        )

    payload.setdefault("metadata", {})
    return payload


def _get(path: str, params: Optional[dict] = None) -> dict:
    try:
        resp = requests.get(
            f"{BACKEND_BASE_URL}{path}",
            params=params,
            timeout=BACKEND_TIMEOUT_SECONDS,
        )
        return _normalize_response(resp)
    except requests.Timeout as exc:
        return _error_response("Backend request timed out", str(exc))
    except requests.ConnectionError as exc:
        return _error_response("Backend unavailable", str(exc))
    except requests.RequestException as exc:
        return _error_response("Backend request failed", str(exc))


def _post(path: str, payload: Optional[dict] = None) -> dict:
    try:
        resp = requests.post(
            f"{BACKEND_BASE_URL}{path}",
            json=payload or {},
            timeout=BACKEND_TIMEOUT_SECONDS,
        )
        return _normalize_response(resp)
    except requests.Timeout as exc:
        return _error_response("Backend request timed out", str(exc))
    except requests.ConnectionError as exc:
        return _error_response("Backend unavailable", str(exc))
    except requests.RequestException as exc:
        return _error_response("Backend request failed", str(exc))


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
