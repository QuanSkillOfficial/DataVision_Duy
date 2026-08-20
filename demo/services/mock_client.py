"""
demo/services/mock_client.py
=============================
Mock implementation of the platform service API.

Loads realistic fixture data (modeled after each intern's real contract)
instead of returning ad-hoc fake strings. This lets the UI be developed
and tested against data that has the same shape as the real backend will
eventually return.

Every function returns the envelope shape:
    {"data": {...}, "status": "success" | "error", "metadata": {...}}

This module is never imported directly by page code — always go through
`service_client.py`.
"""

from __future__ import annotations

import copy
import json
import os
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from demo.config import FIXTURES_DIR, PREDICTION_CONFIDENCE_THRESHOLD


# ─────────────────────────────────────────────
# FIXTURE LOADING
# ─────────────────────────────────────────────

_fixture_cache: Dict[str, dict] = {}


def _load_fixture(name: str) -> dict:
    """Load and cache a fixture JSON file by name (without extension).

    Week 7 fixtures are preferred when present. The root fixture folder is
    kept as a fallback so older tests and demos continue to work.
    """
    if name not in _fixture_cache:
        week7_path = os.path.join(FIXTURES_DIR, "week7", f"{name}.json")
        path = week7_path if os.path.exists(week7_path) else os.path.join(FIXTURES_DIR, f"{name}.json")
        with open(path, "r", encoding="utf-8") as f:
            _fixture_cache[name] = json.load(f)
    # Return a deep copy so callers can mutate without corrupting the cache.
    return copy.deepcopy(_fixture_cache[name])


def _envelope(data: Any, status: str = "success", **metadata) -> dict:
    return {"data": data, "status": status, "metadata": metadata}


# ─────────────────────────────────────────────
# HEALTH / RELEASE IDENTITY (DV-HUNG-04)
# ─────────────────────────────────────────────

def get_backend_health() -> dict:
    """Fixture mode has no backend, and must never claim it does.

    The UI uses `source` to label the health panel honestly, so a reviewer can
    never mistake a fixture-mode green state for a live backend.
    """
    return _envelope(
        {
            "ok": True,
            "service": "fixture_mode",
            "backend_reachable": False,
            "release_sha": None,
            "environment": None,
        },
        source="fixtures",
    )


# ─────────────────────────────────────────────
# DASHBOARD (Duy + Phat)
# ─────────────────────────────────────────────

def get_dashboard_metrics(source_context: Optional[List[dict]] = None) -> dict:
    """Mock dashboard metrics sourced from Phat's Week 6 analytics views."""
    fixture = _load_fixture("phat_dashboard_views_sample")
    duy_fixture = _load_fixture("duy_latest_ingestion_summary")
    views = fixture["data"]

    # Flatten the view-keyed structure into the flat data envelope the UI
    # expects, pulling each field from its correct source view.
    overview_list = views.get("v_dashboard_overview", [{}])
    overview = overview_list[0] if isinstance(overview_list, list) and overview_list else (overview_list or {})
    
    quality_list = views.get("v_data_quality_dashboard", [])
    
    ingestion_health_list = views.get("v_ingestion_health", [{}])
    ingestion_health = ingestion_health_list[0] if isinstance(ingestion_health_list, list) and ingestion_health_list else {}

    raw_ingestion_runs = views.get("v_latest_ingestion_runs", [])
    recent_activity_raw = views.get("v_recent_activity", [])
    rag_readiness = views.get("v_document_rag_readiness", [])
    review_queue = views.get("v_prediction_review_queue", [])
    latest_document = duy_fixture.get("latest_document", {})

    # Map raw_ingestion_runs to the expected structure in get_ingestion_status
    ingestion_runs = []
    for run in raw_ingestion_runs:
        source_name = run.get("source_name")
        # Find matching invalid records count from v_data_quality_dashboard
        invalid_count = 0
        valid_count = 0
        quality_score = 100.0
        for q in quality_list:
            if q.get("source_name") == source_name:
                invalid_count = q.get("records_invalid", 0)
                valid_count = q.get("records_valid", 0)
                quality_score = q.get("data_quality_score", 100.0)
                break
        ingestion_runs.append({
            "run_id": run.get("run_name"),
            "source_name": source_name,
            "source_id": next((q.get("source_id") for q in quality_list if q.get("source_name") == source_name), None),
            "status": run.get("ingestion_status"),
            "ingestion_run_id": run.get("run_name"),
            "file_hash_sha256": "8f43c336b9e59dcd1d8327deb882cf99a929532d84784781d4a8e3f607182930",
            "records_read": run.get("records_read", 0),
            "records_valid": valid_count,
            "records_invalid": invalid_count,
            "data_quality_score": quality_score,
            "raw_output_path": f"data/raw/{source_name}",
            "staging_output_path": f"data/staging/{source_name}",
            "clean_output_path": f"data/clean/{source_name}",
        })

    # Map raw recent_activity to the expected contract
    recent_activity = []
    for act in recent_activity_raw:
        recent_activity.append({
            "timestamp": act.get("created_at"),
            "actor": act.get("activity_type", "system").capitalize(),
            "action": f"{act.get('activity_type', 'activity').capitalize()} event for {act.get('label')}",
            "status": act.get("status", "success"),
        })

    # Build document processing status breakdown from v_prediction_confidence_summary
    document_processing_status = {}
    confidence_summary = views.get("v_prediction_confidence_summary", [])
    for item in confidence_summary:
        label = item.get("predicted_label")
        if label:
            document_processing_status[label] = document_processing_status.get(label, 0) + item.get("prediction_count", 0)

    # Compute overall quality score as average of data quality scores
    scores = [q.get("data_quality_score", 100.0) for q in quality_list]
    avg_quality_score = round(sum(scores) / len(scores)) if scores else 100

    total_read = ingestion_health.get("total_read", 0)
    total_valid = ingestion_health.get("total_valid", 0)
    total_invalid = ingestion_health.get("total_invalid", 0)
    if total_read == 0:
        for q in quality_list:
            total_read += q.get("records_read", 0)
            total_valid += q.get("records_valid", 0)
            total_invalid += q.get("records_invalid", 0)

    data = {
        # v_dashboard_overview
        "source_count": overview.get("total_sources", 0),
        "file_count": overview.get("total_documents", 0),
        "link_count": max(0, overview.get("total_sources", 0) - overview.get("total_documents", 0)),
        "record_count": total_read,
        "rag_query_count": overview.get("total_rag_queries", 0),
        "rag_avg_latency_ms": 0,
        "prediction_count": overview.get("total_predictions", 0),
        "successful_ingestion_runs": overview.get(
            "successful_ingestions",
            duy_fixture.get("successful_runs", 0),
        ),
        "latest_document": latest_document,
        "rag_ready_documents": len(rag_readiness),
        "prediction_review_queue_count": len(review_queue),
        "prediction_review_queue": review_queue,
        # v_data_quality_dashboard / health
        "records_read": total_read,
        "records_valid": total_valid,
        "records_invalid": total_invalid,
        "data_quality_score": avg_quality_score,
        "duplicate_risk": "low",
        "parsing_coverage": round(total_valid / max(total_read, 1), 2),
        "processing_status": "ready",
        "document_processing_status": document_processing_status,
        # v_latest_ingestion_runs + v_recent_activity
        "ingestion_runs": ingestion_runs,
        "recent_activity": recent_activity,
    }

    # If the demo session has its own uploaded sources, reflect that count
    # while keeping all other fixture-derived signals realistic.
    if source_context is not None:
        data["source_count"] = len(source_context) or data["source_count"]

    return _envelope(data, source_view="v_dashboard_overview", owner="Phat")


def get_ingestion_status(run_id: Optional[str] = None) -> dict:
    """Mock ingestion run status from Duy's latest Week 7-ready summary."""
    fixture = _load_fixture("duy_latest_ingestion_summary")
    latest_ingestion_run = fixture.get("latest_ingestion_run") or {}
    if not latest_ingestion_run.get("source_name") and fixture.get("runs"):
        latest_ingestion_run = fixture["runs"][0]
    run_data = latest_ingestion_run or fixture.get("latest_document") or {}
    latest_document = fixture.get("latest_document") or {}
    if latest_document:
        merged = copy.deepcopy(run_data)
        for key, value in latest_document.items():
            merged.setdefault(key, value)
        run_data = merged
    run_data.setdefault("run_id", run_data.get("ingestion_run_id"))
    return _envelope(run_data, source_module="ingestion", owner="Duy")


def get_recent_activity() -> dict:
    """Mock recent platform activity feed from Phat's v_recent_activity view."""
    # Use get_dashboard_metrics to get mapped/formatted activity logs
    metrics = get_dashboard_metrics()
    activity = metrics["data"].get("recent_activity", [])
    return _envelope(activity, source_view="v_recent_activity", owner="Phat")


# ─────────────────────────────────────────────
# PREDICTION (Tuong)
# ─────────────────────────────────────────────

REQUIRED_PREDICTION_FIELDS = [
    "document_id", "source_id", "file_name", "file_type",
    "file_size", "text_length", "num_pages",
    "source_system", "extracted_text",
]


def classify_document(input_payload: dict) -> dict:
    """
    Mock single-document classification, modeled after Tuong's
    predict_document_type() contract.

    Honors the 4 status values: accepted, needs_review,
    waiting_for_source, failed.
    """
    payload = input_payload or {}

    missing = [f for f in REQUIRED_PREDICTION_FIELDS if f not in payload]
    if missing:
        return _envelope(
            {
                "predicted_document_type": None,
                "confidence": 0.0,
                "model_version": "document_classifier_v1",
                "status": "failed",
                "review_reason": f"Missing required fields: {missing}",
                "top_predictions": [],
            },
            status="error",
            owner="Tuong",
        )

    extracted_text = (payload.get("extracted_text") or "").strip()
    if not extracted_text:
        return _envelope(
            {
                "predicted_document_type": None,
                "confidence": 0.0,
                "model_version": "document_classifier_v1",
                "status": "waiting_for_source",
                "review_reason": "No extracted text available yet.",
                "top_predictions": [],
            },
            owner="Tuong",
        )

    # Use the fixture as the base "real" prediction shape, then vary
    # confidence deterministically based on document_id so repeated
    # calls with the same payload are stable (useful for tests/demo).
    fixture = _load_fixture("tuong_prediction_batch_response")
    results = fixture.get("results", [])
    dataflow_result = next(
        (
            item for item in results
            if item.get("document_external_id") == "doc_dataflow_technical_report"
        ),
        results[0] if results else {},
    )
    result = copy.deepcopy(dataflow_result)

    seed = sum(ord(c) for c in str(payload.get("document_id", "")))
    rng = random.Random(seed)
    confidence = round(rng.uniform(0.45, 0.97), 4)
    result["confidence"] = confidence
    result.setdefault("model_version", "document_classifier_v1")
    result.setdefault("document_external_id", payload.get("document_external_id", payload.get("document_id")))
    result.setdefault("document_db_id", payload.get("document_db_id"))
    result.setdefault("manual_review_required", False)

    if confidence >= PREDICTION_CONFIDENCE_THRESHOLD:
        result["status"] = "accepted"
        result["review_reason"] = None
        result["manual_review_required"] = False
    else:
        result["status"] = "needs_review"
        result["review_reason"] = "Prediction confidence below threshold"
        result["manual_review_required"] = True

    return _envelope(result, owner="Tuong")


def classify_documents(input_payloads: List[dict]) -> dict:
    """Mock batch classification — classify_document() applied to a list."""
    results = [classify_document(p)["data"] for p in (input_payloads or [])]
    return _envelope(results, owner="Tuong")


def submit_prediction_correction(payload: dict) -> dict:
    """Mock submission of prediction feedback."""
    required = [
        "prediction_log_id", "document_db_id", "document_external_id",
        "corrected_document_type", "corrected_by", "correction_reason"
    ]
    missing = [f for f in required if f not in payload]
    has_original = "original_prediction" in payload or "predicted_document_type" in payload
    if not has_original:
        missing.append("original_prediction")
    if missing:
        return _envelope(
            {"success": False, "error": f"Missing required fields: {missing}"},
            status="error",
            owner="Tuong"
        )
    return _envelope(
        {
            "success": True,
            "saved": True,
            "feedback_payload": payload,
        },
        owner="Tuong",
    )


# ─────────────────────────────────────────────
# RAG / CHATBOT (Lap)
# ─────────────────────────────────────────────

def ask_rag(question: str, document_id: Optional[str] = None) -> dict:
    """Mock RAG query, modeled after Lap's rag_response_contract."""
    if not question or not question.strip():
        return _envelope(
            {
                "question": question,
                "answer": "Please enter a question.",
                "citations": [],
                "retrieved_context": [],
                "model": "all-MiniLM-L6-v2",
                "status": "error",
            },
            status="error",
            owner="Lap",
        )

    fixture = _load_fixture("lap_rag_response_real")
    data = copy.deepcopy(fixture.get("data", fixture))
    data["question"] = question
    metadata = fixture.get("metadata", data.get("metadata", {}))
    data["retrieval_backend"] = metadata.get("retrieval_backend")
    data["embedding_dimension"] = metadata.get("embedding_dimension")

    # Simulate "no relevant context found" for clearly unrelated prompts,
    # while keeping older tests and the Week 7 DataFlow demo on the success path.
    unrelated_terms = ("weather", "sports", "recipe")
    if any(term in question.lower() for term in unrelated_terms):
        data["answer"] = (
            "I do not know based on the provided documents."
        )
        data["citations"] = []
        data["retrieved_context"] = []
        data["status"] = "no_match"

    if document_id:
        data["citations"] = [
            c for c in data["citations"]
            if document_id in c.get("chunk_id", "")
        ] or data["citations"]

    envelope_metadata = {k: v for k, v in metadata.items() if k != "owner"}
    return _envelope(data, owner=metadata.get("owner", "Lap"), **envelope_metadata)


# ─────────────────────────────────────────────
# SUGGESTIONS (aggregates Duy + Phat + Tuong + Lap)
# ─────────────────────────────────────────────

def generate_suggestions(context: Optional[dict] = None) -> dict:
    """
    Mock suggestion generation that traces evidence back to the
    originating module (ingestion / dashboard / prediction / rag),
    per the suggestion_ui_contract.
    """
    context = context or {}
    dashboard_signals = context.get("dashboard_signals", {})
    prediction_result = context.get("prediction_result", {})
    rag_context = context.get("rag_context", {})
    ingestion_run = context.get("ingestion_run", {})

    suggestions: List[dict] = []

    parsing_coverage = dashboard_signals.get("parsing_coverage", 0.91)
    if parsing_coverage < 0.95:
        suggestions.append(_build_suggestion(
            title="Improve parsing coverage before final reporting",
            category="Data Quality",
            priority="Medium",
            description="Some uploaded sources do not have a fully readable preview.",
            why_it_matters="Reports should clearly state which sources were parsed.",
            next_action="Add parsing support for unparsed file types.",
            source_module="ingestion",
            source_view="v_ingestion_summary",
            evidence_type="parsing_coverage",
            evidence_value=parsing_coverage,
            urgency=0.6, impact=0.7, confidence=0.8, effort=0.4,
            generated_from=["dashboard_signals", "ingestion_logs"],
        ))

    pred_confidence = prediction_result.get("confidence")
    if prediction_result.get("status") == "needs_review":
        suggestions.append(_build_suggestion(
            title="Review document type before report generation",
            category="Data Quality",
            priority="High",
            description="The prediction confidence for this document is below the automated threshold.",
            why_it_matters="Low-confidence predictions can route documents to the wrong workflow.",
            next_action="Manually confirm the document type before generating a report.",
            source_module="prediction",
            source_view="prediction_logs",
            evidence_type="confidence_score",
            evidence_value=pred_confidence if pred_confidence is not None else 0.0,
            urgency=0.9, impact=0.85, confidence=0.95, effort=0.1,
            generated_from=["prediction_logs"],
        ))

    if prediction_result.get("manual_review_required") or (
        prediction_result.get("confidence") is not None
        and prediction_result.get("confidence", 1.0) < 0.80
        and prediction_result.get("status") == "accepted"
    ):
        suggestions.append(_build_suggestion(
            title="Treat medium-confidence prediction as a model suggestion",
            category="Staging Safety",
            priority="High",
            description="The prediction is below the Week 7 high-confidence threshold.",
            why_it_matters="Staging demos must not present uncertain model output as final truth.",
            next_action="Route this document through the manual review workflow before hard filtering or reporting.",
            source_module="prediction",
            source_view="prediction_logs",
            evidence_type="manual_review_required",
            evidence_value=prediction_result.get("manual_review_required", True),
            urgency=0.85, impact=0.8, confidence=0.9, effort=0.2,
            generated_from=["prediction_logs", "review_queue"],
        ))

    retrieved_context = rag_context.get("retrieved_context", []) or []
    similarity_scores = [
        item.get("similarity_score", 0.0)
        for item in retrieved_context
        if isinstance(item.get("similarity_score", 0.0), (int, float))
    ]
    avg_similarity = (
        sum(similarity_scores) / len(similarity_scores)
        if similarity_scores else None
    )
    if rag_context.get("status") == "no_match" or (
        avg_similarity is not None and avg_similarity < 0.60
    ):
        suggestions.append(_build_suggestion(
            title="Expand document coverage for chatbot queries",
            category="Retrieval Quality",
            priority="Medium",
            description="The chatbot could not find relevant context for a recent question.",
            why_it_matters="Gaps in retrieval reduce the usefulness of the RAG chatbot.",
            next_action="Ingest additional source documents covering this topic.",
            source_module="rag",
            source_view="rag_query_logs",
            evidence_type="retrieval_match",
            evidence_value=round(avg_similarity or 0.0, 2),
            urgency=0.5, impact=0.6, confidence=0.7, effort=0.5,
            generated_from=["rag_query_logs"],
        ))

    rag_ready_count = dashboard_signals.get("rag_ready_documents")
    if rag_ready_count or rag_context.get("citations"):
        suggestions.append(_build_suggestion(
            title="Use DataFlow RAG citations as report evidence",
            category="Retrieval Quality",
            priority="Medium",
            description="The DataFlow technical report has citation-ready chunks available for UI evidence cards.",
            why_it_matters="Report claims should point back to page-aware retrieved context.",
            next_action="Include file name, page, chunk ID, and similarity score in report evidence.",
            source_module="rag",
            source_view="document_chunks",
            evidence_type="citation_count",
            evidence_value=len(rag_context.get("citations", [])),
            urgency=0.45, impact=0.75, confidence=0.85, effort=0.25,
            generated_from=["rag_response", "document_chunks"],
        ))

    if ingestion_run.get("file_hash_sha256"):
        suggestions.append(_build_suggestion(
            title="Keep file hash in the staging evidence table",
            category="Traceability",
            priority="Medium",
            description="Duy's ingestion output includes a SHA-256 hash for the DataFlow PDF.",
            why_it_matters="The staging demo can prove which exact source file produced downstream evidence.",
            next_action="Show the hash in Reports and keep it out of free-form generated claims.",
            source_module="ingestion",
            source_view="ingestion_logs",
            evidence_type="file_hash_sha256",
            evidence_value=ingestion_run.get("file_hash_sha256"),
            urgency=0.35, impact=0.65, confidence=0.9, effort=0.15,
            generated_from=["duy_latest_ingestion_summary"],
        ))

    if dashboard_signals.get("processing_status") == "ready":
        suggestions.append(_build_suggestion(
            title="Generate report draft from current evidence",
            category="Reporting",
            priority="Medium",
            description="Dashboard signals are ready for downstream report generation.",
            why_it_matters="Confirms data is flowing through the full platform vertical.",
            next_action="Open Reports and generate a draft using current evidence.",
            source_module="dashboard",
            source_view="v_ingestion_summary",
            evidence_type="processing_status",
            evidence_value="ready",
            urgency=0.4, impact=0.65, confidence=0.85, effort=0.2,
            generated_from=["dashboard_signals"],
        ))

    if not suggestions:
        suggestions.append(_build_suggestion(
            title="Upload a source before reviewing actions",
            category="Data Quality",
            priority="High",
            description="No dashboard, prediction, or RAG signals are available yet.",
            why_it_matters="The platform needs at least one signal before suggestions are meaningful.",
            next_action="Upload a CSV, PDF, or TXT file, then revisit this page.",
            source_module="ingestion",
            source_view="v_ingestion_summary",
            evidence_type="source_count",
            evidence_value=0,
            urgency=0.95, impact=0.9, confidence=0.95, effort=0.2,
            generated_from=["dashboard_signals"],
        ))

    suggestions = _score_and_sort(suggestions)
    return _envelope(suggestions, owner="Phi/Hung")


def _build_suggestion(
    title, category, priority, description, why_it_matters, next_action,
    source_module, source_view, evidence_type, evidence_value,
    urgency, impact, confidence, effort, generated_from,
    affected_document=None, affected_source=None,
) -> dict:
    return {
        "title": title,
        "category": category,
        "priority": priority,
        "impact": why_it_matters,
        "description": description,
        "why_it_matters": why_it_matters,
        "next_action": next_action,
        "source_signal": f"{source_module}.{evidence_type} = {evidence_value}",
        "difficulty": "Low" if effort < 0.4 else "Medium" if effort < 0.7 else "High",
        "reason": description,
        "urgency_score": urgency,
        "impact_score": impact,
        "confidence_score": confidence,
        "effort_score": effort,
        "source_module": source_module,
        "source_view": source_view,
        "evidence_type": evidence_type,
        "evidence_value": evidence_value,
        "affected_document": affected_document or "doc_dataflow_technical_report",
        "affected_source": affected_source or "DataFlow_Technical_Report.pdf",
        "confidence": confidence,
        "generated_from": generated_from,
    }


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _score_and_sort(suggestions: List[dict]) -> List[dict]:
    scored = []
    for s in suggestions:
        urgency = _clamp(s["urgency_score"])
        impact = _clamp(s["impact_score"])
        confidence = _clamp(s["confidence_score"])
        effort = _clamp(s["effort_score"])
        final_score = round(
            _clamp(0.35 * urgency + 0.30 * impact + 0.20 * confidence - 0.15 * effort),
            2,
        )
        final_priority = (
            "High" if final_score >= 0.6 else
            "Medium" if final_score >= 0.35 else
            "Low"
        )
        scored.append({
            **s,
            "final_score": final_score,
            "final_priority": final_priority,
        })
    return sorted(scored, key=lambda s: s["final_score"], reverse=True)


# ─────────────────────────────────────────────
# REPORTS (aggregates everything)
# ─────────────────────────────────────────────

def generate_report(evidence_context: Optional[dict] = None) -> dict:
    """
    Mock report generation with a full evidence table sourced from
    ingestion, dashboard, prediction, RAG, and suggestions —
    per the report_ui_contract.
    """
    ctx = evidence_context or {}
    audience = ctx.get("audience", "General")
    domain_label = ctx.get("domain_label", "Selected Domain")
    report_type = ctx.get("report_type", "Domain Summary")

    sources = ctx.get("source_context", [])
    dashboard_signals = ctx.get("dashboard_signals", {})
    suggestions = ctx.get("suggestions", [])
    prediction_result = ctx.get("prediction_result", {})
    rag_context = ctx.get("rag_context", {})
    ingestion_run = ctx.get("ingestion_run")
    if not ingestion_run:
        try:
            ingestion_fixture = _load_fixture("duy_latest_ingestion_summary")
            ingestion_run = (
                ingestion_fixture.get("latest_ingestion_run")
                or ingestion_fixture.get("latest_document")
                or {}
            )
        except FileNotFoundError:
            ingestion_run = {}

    evidence_summary = (
        f"{len(sources)} upload source(s), "
        f"{len(dashboard_signals)} dashboard signal(s), "
        f"{len(suggestions)} suggestion(s)"
    )

    quality_summary = (
        f"Data quality score: {dashboard_signals.get('data_quality_score', 'Not available in current data.')}; "
        f"parsing coverage: {dashboard_signals.get('parsing_coverage', 'Not available in current data.')}."
        if dashboard_signals
        else "Not available in current data."
    )

    recommendations = (
        "\n".join(
            f"- {s.get('final_priority', s.get('priority', 'Medium'))}: "
            f"{s.get('title', 'Untitled')}. Next action: {s.get('next_action', 'Review.')}"
            for s in suggestions[:3]
        )
        if suggestions
        else "Not available in current data."
    )

    sections = [
        {"Section": "Title", "Preview": f"{domain_label} - {report_type}", "Audience": audience},
        {"Section": "Executive Summary", "Preview": f"Draft for {audience.lower()} audience using current session context.", "Audience": audience},
        {"Section": "Evidence Used", "Preview": evidence_summary, "Audience": audience},
        {"Section": "Key Findings", "Preview": quality_summary, "Audience": audience},
        {"Section": "Risks or Issues", "Preview": _risk_summary(prediction_result, rag_context), "Audience": audience},
        {"Section": "Recommendations", "Preview": recommendations, "Audience": audience},
        {"Section": "Data Quality Limitations", "Preview": "Week 7 integration fixtures are used for staging; backend validation is pending.", "Audience": audience},
        {"Section": "Next Actions", "Preview": "Validate backend routes, run the backend stub smoke tests, and replace fixtures with live API responses in Week 8.", "Audience": audience},
    ]

    evidence_table = _build_evidence_table(
        sources, dashboard_signals, prediction_result, rag_context, suggestions, ingestion_run
    )

    report = {
        "title": f"{domain_label} - {report_type}",
        "sections": sections,
        "evidence_table": evidence_table,
    }
    return _envelope(report, owner="Phi/Hung")


def _risk_summary(prediction_result: dict, rag_context: dict) -> str:
    risks = []
    if prediction_result.get("status") == "needs_review":
        risks.append("Document type prediction requires manual review.")
    if rag_context.get("status") == "no_match":
        risks.append("Chatbot could not find relevant context for at least one query.")
    return " ".join(risks) if risks else "Not available in current data."


def _build_evidence_table(
    sources, dashboard_signals, prediction_result, rag_context, suggestions, ingestion_run=None
) -> List[dict]:
    rows: List[dict] = []

    ingestion_run = ingestion_run or {}
    if ingestion_run:
        rows.append({
            "Evidence Source": ingestion_run.get("source_name", "Duy ingestion summary"),
            "Module": "ingestion",
            "Metric / Signal": "File Integrity Hash",
            "Value": str(ingestion_run.get("file_hash_sha256", "Not available in current data.")),
            "Used In Section": "Evidence Used",
            "Limitation": "Week 7 integration fixture; backend validation pending.",
        })

    for source in sources[:3]:
        rows.append({
            "Evidence Source": source.get("filename") or source.get("name", "Unknown source"),
            "Module": "ingestion",
            "Metric / Signal": "File Size",
            "Value": f"{source.get('size', 'Not available in current data.')}",
            "Used In Section": "Evidence Used",
            "Limitation": "Week 7 integration fixture; backend validation pending.",
        })

    if dashboard_signals:
        rows.append({
            "Evidence Source": "Dashboard Analytics",
            "Module": "analytics",
            "Metric / Signal": "Data Quality Score",
            "Value": str(dashboard_signals.get("data_quality_score", "Not available in current data.")),
            "Used In Section": "Key Findings",
            "Limitation": "Database-backed sample; backend validation pending.",
        })

    if prediction_result:
        rows.append({
            "Evidence Source": "Prediction Engine",
            "Module": "prediction",
            "Metric / Signal": "Predicted Document Type / Confidence",
            "Value": f"{prediction_result.get('predicted_document_type', 'Not available in current data.')} "
                     f"({prediction_result.get('confidence', 0):.0%})" if prediction_result.get("confidence") is not None
                     else "Not available in current data.",
            "Used In Section": "Risks or Issues",
            "Limitation": "Prediction output pending review.",
        })

    if rag_context:
        rows.append({
            "Evidence Source": "RAG Chatbot",
            "Module": "rag",
            "Metric / Signal": "Citation Count",
            "Value": str(len(rag_context.get("citations", []))),
            "Used In Section": "Risks or Issues",
            "Limitation": "RAG retrieval output from pgvector fixture.",
        })

    for s in suggestions[:2]:
        rows.append({
            "Evidence Source": s.get("title", "Suggestion"),
            "Module": s.get("source_module", "suggestions"),
            "Metric / Signal": s.get("evidence_type", "Not available in current data."),
            "Value": str(s.get("evidence_value", "Not available in current data.")),
            "Used In Section": "Recommendations",
            "Limitation": "Generated from Week 7 integration fixture signals.",
        })

    if not rows:
        rows.append({
            "Evidence Source": "Not available in current data.",
            "Module": "Not available in current data.",
            "Metric / Signal": "Not available in current data.",
            "Value": "Not available in current data.",
            "Used In Section": "Not available in current data.",
            "Limitation": "No evidence sources were available when this report was generated.",
        })

    return rows
