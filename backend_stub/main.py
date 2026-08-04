from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = PROJECT_ROOT / "outputs" / "ui_fixtures"

BACKEND_MODE = os.getenv("DATAVISION_BACKEND_MODE", "fixture").lower()
STAGING_MODE = BACKEND_MODE == "staging"

app = FastAPI(title="DataVision Platform API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_json(filename: str, fallback: Any) -> Any:
    path = FIXTURE_DIR / filename
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _metadata() -> dict[str, Any]:
    return {
        "mode": BACKEND_MODE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backend_validation_pending": not STAGING_MODE,
    }


def _success(data: Any, **extra: Any) -> dict[str, Any]:
    metadata = _metadata()
    metadata.update(extra)
    return {"status": "success", "data": data, "metadata": metadata}


def _error(message: str, detail: str | None = None) -> dict[str, Any]:
    return {
        "status": "error",
        "data": None,
        "error": {"message": message, "detail": detail or message},
        "metadata": _metadata(),
    }


def _duy_summary() -> dict[str, Any]:
    return _read_json(
        "duy_week7_database_enriched_summary.json",
        {
            "total_sources": 0,
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_records_read": 0,
            "total_records_valid": 0,
            "average_data_quality_score": None,
            "latest_document": None,
            "handoff_paths": {},
        },
    )


def _phat_views() -> dict[str, Any]:
    return _read_json(
        "phat_dashboard_views_sample.json",
        {
            "v_dashboard_overview": [],
            "v_latest_ingestion_runs": [],
            "v_data_quality_dashboard": [],
            "v_document_rag_readiness": [],
            "v_prediction_review_queue": [],
            "v_recent_activity": [],
        },
    )


def _lap_rag_fixture() -> dict[str, Any]:
    return _read_json(
        "lap_rag_response_real.json",
        {
            "question": "",
            "answer": None,
            "status": "retrieval_only",
            "retrieved_context": [],
            "citations": [],
            "metadata": {"retrieval_backend": "stub", "embedding_dimension": 384},
        },
    )


def _tuong_batch() -> dict[str, Any]:
    return _read_json(
        "tuong_prediction_batch_response.json",
        {"predictions": [], "summary": {}},
    )


def _tuong_review_queue() -> Any:
    return _read_json("tuong_prediction_review_queue_sample.json", [])


def _dashboard_metrics() -> dict[str, Any]:
    duy = _duy_summary()
    views = _phat_views()
    overview = views.get("v_dashboard_overview", [])
    if isinstance(overview, list) and overview:
        first = overview[0] if isinstance(overview[0], dict) else {}
    elif isinstance(overview, dict):
        first = overview
    else:
        first = {}
    review_queue = views.get("v_prediction_review_queue", [])
    if not isinstance(review_queue, list):
        review_queue = []
    return {
        "total_sources": first.get("total_sources", duy.get("total_sources", 0)),
        "total_runs": first.get("total_runs", duy.get("total_runs", 0)),
        "successful_runs": first.get("successful_runs", duy.get("successful_runs", 0)),
        "total_records": first.get("total_records", duy.get("total_records_read", 0)),
        "average_data_quality_score": first.get(
            "average_data_quality_score", duy.get("average_data_quality_score")
        ),
        "prediction_review_queue_count": len(review_queue),
        "rag_query_count": first.get("rag_query_count", 0),
        "prediction_count": first.get("prediction_count", 0),
        "latest_document": duy.get("latest_document"),
    }


def _prediction_result(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("extracted_text")
    if not payload.get("file_name") or not payload.get("file_type"):
        return {
            "predicted_document_type": None,
            "confidence": 0.0,
            "model_name": "document_type_classifier",
            "model_version": "contract_stub_v1",
            "status": "failed",
            "review_reason": "Validation error: file_name and file_type are required",
            "top_predictions": [],
            "manual_review_required": False,
        }
    if not isinstance(text, str) or len(text.strip()) < 50:
        return {
            "predicted_document_type": None,
            "confidence": 0.0,
            "model_name": "document_type_classifier",
            "model_version": "contract_stub_v1",
            "status": "waiting_for_source",
            "review_reason": "Extracted text is missing or shorter than 50 characters",
            "top_predictions": [],
            "manual_review_required": True,
        }
    return {
        "predicted_document_type": None,
        "confidence": 0.0,
        "model_name": "document_type_classifier",
        "model_version": "contract_stub_v1",
        "status": "needs_review",
        "review_reason": "Backend model execution is pending; review required",
        "top_predictions": [],
        "manual_review_required": True,
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    if STAGING_MODE:
        try:
            from backend_stub.runtime import health_snapshot

            snapshot = health_snapshot()
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Database health check failed: {exc}") from exc
        if not snapshot.get("healthy"):
            raise HTTPException(status_code=503, detail=snapshot)
        return _success(snapshot)
    return _success({"service": "backend_stub", "healthy": True})


@app.get("/api/dashboard/metrics")
@app.get("/api/dashboard/overview")
def dashboard_metrics() -> dict[str, Any]:
    if STAGING_MODE:
        from backend_stub.runtime import dashboard_metrics as live_dashboard_metrics

        return _success(live_dashboard_metrics(), source="PostgreSQL analytics views")
    return _success(_dashboard_metrics(), source="Duy fixture + Phat view contract")


@app.post("/api/dashboard/metrics")
def dashboard_metrics_with_context(
    payload: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    if STAGING_MODE:
        from backend_stub.runtime import dashboard_metrics as live_dashboard_metrics

        source_context = payload.get("source_context", [])
        return _success(
            live_dashboard_metrics(source_context),
            source="PostgreSQL analytics views",
            source_context_count=len(source_context),
        )
    return _success(
        _dashboard_metrics(),
        source="Duy fixture + Phat view contract",
        source_context_count=len(payload.get("source_context", [])),
    )


@app.get("/api/dashboard/recent-activity")
def dashboard_recent_activity() -> dict[str, Any]:
    if STAGING_MODE:
        from backend_stub.runtime import recent_activity

        return _success(recent_activity())
    return _success(_phat_views().get("v_recent_activity", []))


@app.get("/api/dashboard/review-queue")
@app.get("/api/predict/review-queue")
def prediction_review_queue() -> dict[str, Any]:
    if STAGING_MODE:
        from backend_stub.runtime import review_queue

        return _success(review_queue())
    queue = _phat_views().get("v_prediction_review_queue")
    if not queue:
        queue = _tuong_review_queue()
    return _success(queue)


@app.get("/api/ingestion/status")
def ingestion_status(run_id: str | None = None) -> dict[str, Any]:
    if STAGING_MODE:
        from backend_stub.runtime import latest_ingestion_status

        return _success(latest_ingestion_status(run_id))
    summary = _duy_summary()
    return _success({"run_id": run_id, "summary": summary})


@app.get("/api/ingestion/status/{run_id}")
def ingestion_status_by_id(run_id: str) -> dict[str, Any]:
    return ingestion_status(run_id=run_id)


@app.post("/api/ingestion/run")
def ingestion_run(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return _success(
        {
            "accepted": False,
            "status": "contract_only",
            "message": "Use Duy's local ingestion engine until the production API is available.",
            "request": payload,
        }
    )


@app.post("/api/rag/query")
def rag_query(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    if STAGING_MODE:
        from backend_stub.runtime import rag_query as live_rag_query

        question = str(payload.get("question") or "").strip()
        if not question:
            return _error("question is required")
        return _success(
            live_rag_query(
                question,
                payload.get("document_id"),
                int(payload.get("top_k", 5)),
            )
        )
    fixture = _lap_rag_fixture()
    question = payload.get("question") or fixture.get("question")
    if fixture.get("retrieved_context"):
        data = dict(fixture)
        data["question"] = question
    else:
        data = {
            "question": question,
            "answer": None,
            "retrieved_context": [],
            "citations": [],
            "status": "retrieval_only",
            "model": "contract_stub",
            "metadata": {
                "retrieval_backend": "stub",
                "embedding_dimension": 384,
                "top_k": payload.get("top_k", 5),
            },
        }
    return _success(data)


@app.post("/api/predict/document-type")
def predict_document_type(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    if STAGING_MODE:
        from backend_stub.runtime import predict_and_log

        return _success(predict_and_log(payload))
    return _success(_prediction_result(payload))


@app.post("/api/predict/document-type/batch")
def predict_document_type_batch(payload: Any = Body(default_factory=dict)) -> dict[str, Any]:
    if isinstance(payload, list):
        items = payload
    else:
        items = (
            payload.get("items", payload.get("payloads", []))
            if isinstance(payload, dict)
            else []
        )
    if STAGING_MODE:
        from backend_stub.runtime import predict_and_log

        predictions = [predict_and_log(item if isinstance(item, dict) else {}) for item in items]
    else:
        predictions = [_prediction_result(item if isinstance(item, dict) else {}) for item in items]
    return _success(predictions, count=len(predictions))


@app.post("/api/predict/feedback")
def predict_feedback(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return _success(
        {
            "saved": False,
            "status": "contract_only",
            "message": "Feedback contract accepted by stub; persistence is pending.",
            "feedback": payload,
        }
    )


@app.post("/api/suggestions/generate")
def suggestions_generate(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    if STAGING_MODE:
        from backend_stub.runtime import dashboard_metrics as live_dashboard_metrics

        metrics = live_dashboard_metrics()
        queue_count = metrics.get("prediction_review_queue_count", 0)
        return _success(
            [
                {
                    "title": "Review low-confidence predictions" if queue_count else "Monitor staging pipeline",
                    "priority": "high" if queue_count else "medium",
                    "source_module": "prediction" if queue_count else "integration",
                    "source_view": "v_prediction_review_queue" if queue_count else "v_dashboard_overview",
                    "evidence_type": "row_count",
                    "evidence_value": queue_count,
                    "generated_from": "PostgreSQL staging evidence",
                    "reason": f"{queue_count} predictions currently require review.",
                    "recommended_action": "Open the review queue and confirm labels." if queue_count else "Continue monitoring health checks.",
                    "final_score": 1.0 if queue_count else 0.5,
                }
            ]
        )
    return _success(
        [
            {
                "title": "Backend validation pending",
                "priority": "medium",
                "source_module": "integration",
                "reason": "The local stub is serving contract-shaped data.",
                "recommended_action": "Run the shared integration stack before staging.",
                "request_context_present": bool(payload),
            }
        ]
    )


@app.post("/api/reports/generate")
def reports_generate(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    if STAGING_MODE:
        from backend_stub.runtime import dashboard_metrics as live_dashboard_metrics

        live_metrics = live_dashboard_metrics()
        evidence = {
            "dashboard": live_metrics,
            "mode": "staging",
        }
        return _success(
            {
                "title": "DataVision Week 8 staging report",
                "status": "staging",
                "sections": [
                    {"Section": "Pipeline Health", "Preview": "Live PostgreSQL-backed staging metrics."},
                    {"Section": "Review Queue", "Preview": f"{live_metrics.get('prediction_review_queue_count', 0)} items require review."},
                    {"Section": "RAG Activity", "Preview": f"{live_metrics.get('rag_query_count', 0)} logged RAG queries."},
                ],
                "evidence_table": [
                    {
                        "Evidence Source": "PostgreSQL staging",
                        "Metric / Signal": "DataVision pipeline state",
                        "Value": "healthy",
                        "Used In Section": "Pipeline Health",
                        "Limitation": "Hash embeddings validate retrieval plumbing, not semantic model quality.",
                    }
                ],
                "evidence": evidence,
                "request": payload,
            }
        )
    evidence = {
        "ingestion": _duy_summary(),
        "dashboard": _phat_views(),
        "rag": _lap_rag_fixture(),
        "prediction": _tuong_batch(),
    }
    return _success(
        {
            "title": "DataVision integration report",
            "status": "contract_only",
            "sections": [
                {
                    "Section": "Executive Summary",
                    "Preview": "Contract-stub report generated from current integration fixtures.",
                },
                {
                    "Section": "Evidence Used",
                    "Preview": "Duy ingestion, Phat views, Lap RAG and Tuong prediction fixtures.",
                },
                {
                    "Section": "Next Actions",
                    "Preview": "Replace contract fixtures with live Week 8 staging services.",
                },
            ],
            "evidence_table": [
                {
                    "Evidence Source": "DataVision integration fixtures",
                    "Metric / Signal": "Contract availability",
                    "Value": "ready",
                    "Used In Section": "Evidence Used",
                    "Limitation": "Backend execution remains pending.",
                }
            ],
            "evidence": evidence,
            "request": payload,
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend_stub.main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=False,
    )
