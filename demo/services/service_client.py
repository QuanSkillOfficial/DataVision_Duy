"""
demo/services/service_client.py
=================================
The ONLY interface that UI pages are allowed to call.

Pages must never import mock_client or backend_client directly.
This module routes every call to either the mock implementation or the
real backend implementation, based on demo.config.USE_BACKEND.

Switching the entire platform from mock data to a real FastAPI backend
requires changing exactly one line: demo/config.py -> USE_BACKEND = True.

Usage in a page:
    from demo.services.service_client import get_dashboard_metrics
    metrics = get_dashboard_metrics(source_context)
    data = metrics["data"]
"""

from __future__ import annotations

from typing import List, Optional

from demo.config import USE_BACKEND

if USE_BACKEND:
    from demo.services import backend_client as _client
else:
    from demo.services import mock_client as _client


# ─────────────────────────────────────────────
# DASHBOARD (Duy + Phat)
# ─────────────────────────────────────────────

def get_dashboard_metrics(source_context: Optional[List[dict]] = None) -> dict:
    """
    Returns dashboard health metrics.

    Envelope: {"data": {...}, "status": "success"|"error", "metadata": {...}}
    data fields: source_count, file_count, link_count, record_count,
        data_quality_score, processing_status, duplicate_risk,
        parsing_coverage, rag_query_count, prediction_count,
        recent_activity, ingestion_runs.
    """
    return _client.get_dashboard_metrics(source_context)


def get_ingestion_status(run_id: Optional[str] = None) -> dict:
    """
    Returns the status of a specific (or the latest) ingestion run.

    data fields: run_id, source_name, source_type, status,
        raw_output_path, staging_output_path, clean_output_path,
        file_hash_sha256.
    """
    return _client.get_ingestion_status(run_id)


def get_recent_activity() -> dict:
    """Returns a list of recent platform activity events."""
    return _client.get_recent_activity()


# ─────────────────────────────────────────────
# PREDICTION (Tuong)
# ─────────────────────────────────────────────

def classify_document(input_payload: dict) -> dict:
    """
    Runs document type classification for a single document.

    data fields: predicted_document_type, confidence, model_version,
        status (accepted | needs_review | waiting_for_source | failed),
        review_reason, top_predictions (list of {label, score}).
    """
    return _client.classify_document(input_payload)


def classify_documents(input_payloads: List[dict]) -> dict:
    """Runs document type classification for a batch of documents."""
    return _client.classify_documents(input_payloads)


def submit_prediction_correction(payload: dict) -> dict:
    """
    Submits human feedback / correction for a low-confidence prediction.
    """
    return _client.submit_prediction_correction(payload)


# ─────────────────────────────────────────────
# RAG / CHATBOT (Lap)
# ─────────────────────────────────────────────

def ask_rag(question: str, document_id: Optional[str] = None) -> dict:
    """
    Asks a question against the RAG pipeline.

    data fields: question, answer, citations (list of
        {file_name, page_number, chunk_id}), retrieved_context
        (list of {chunk_text, similarity_score}), model, status.
    """
    return _client.ask_rag(question, document_id)


# ─────────────────────────────────────────────
# SUGGESTIONS
# ─────────────────────────────────────────────

def generate_suggestions(context: Optional[dict] = None) -> dict:
    """
    Generates ranked suggestions from ingestion + dashboard + prediction
    + RAG context.

    data: list of suggestion dicts, each including title, category,
        priority, final_score, final_priority, source_module,
        source_view, evidence_type, evidence_value, generated_from.
    """
    return _client.generate_suggestions(context)


# ─────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────

def generate_report(evidence_context: Optional[dict] = None) -> dict:
    """
    Generates a report draft with a full evidence table.

    data fields: title, sections (list), evidence_table (list of
        {Evidence Source, Module, Metric / Signal, Value,
        Used In Section, Limitation}).
    """
    return _client.generate_report(evidence_context)
