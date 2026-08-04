"""Database-backed Week 8 staging services.

The module keeps database and owner-module execution out of the fixture stub
paths. It is activated only with ``DATAVISION_BACKEND_MODE=staging``.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from psycopg2.extras import Json, RealDictCursor


def database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://datavision:datavision123@localhost:5432/datavision_db",
    )


def connect():
    import psycopg2

    return psycopg2.connect(database_url(), connect_timeout=5)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect() as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, params)
        return _json_safe([dict(row) for row in cursor.fetchall()])


def _fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any]:
    rows = _fetch_all(query, params)
    return rows[0] if rows else {}


def health_snapshot() -> dict[str, Any]:
    with connect() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        pgvector = cursor.fetchone() is not None
        counts: dict[str, int] = {}
        for table in ("sources", "documents", "document_pages", "document_chunks", "prediction_logs", "rag_query_logs"):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = int(cursor.fetchone()[0])
    return {
        "service": "datavision-backend",
        "healthy": pgvector,
        "mode": "staging",
        "database": "reachable",
        "pgvector": pgvector,
        "embedding_mode": os.getenv("RAG_EMBEDDING_MODE", "hash"),
        "counts": counts,
    }


def review_queue() -> list[dict[str, Any]]:
    return _fetch_all(
        """
        SELECT id AS prediction_log_id, source_id, document_id AS document_db_id,
               document_external_id, predicted_label AS predicted_document_type,
               confidence_score AS confidence, status, review_reason, created_at
        FROM prediction_logs
        WHERE status IN ('needs_review', 'waiting_for_source')
        ORDER BY created_at DESC, id DESC
        LIMIT 100
        """
    )


def dashboard_metrics(source_context: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    overview = _fetch_one("SELECT * FROM v_dashboard_overview")
    quality = _fetch_one(
        """
        SELECT COALESCE(SUM(records_read), 0) AS records_read,
               COALESCE(SUM(records_valid), 0) AS records_valid,
               COALESCE(SUM(records_invalid), 0) AS records_invalid,
               COALESCE(AVG(data_quality_score), 0) AS data_quality_score,
               COUNT(*) FILTER (WHERE status = 'success') AS successful_runs
        FROM ingestion_logs
        """
    )
    latest_document = _fetch_one(
        """
        SELECT id AS document_db_id, document_external_id, file_name, file_type,
               page_count, character_count, processing_status, created_at
        FROM documents ORDER BY created_at DESC, id DESC LIMIT 1
        """
    )
    status_rows = _fetch_all(
        "SELECT processing_status, COUNT(*) AS count FROM documents GROUP BY processing_status"
    )
    runs = _fetch_all(
        """
        SELECT il.run_id, s.name AS source_name, il.source_id, il.status,
               il.records_read, il.records_valid, il.records_invalid,
               il.data_quality_score, il.started_at, il.ended_at
        FROM ingestion_logs il
        LEFT JOIN sources s ON s.id = il.source_id
        ORDER BY il.created_at DESC, il.id DESC LIMIT 20
        """
    )
    queue = review_queue()
    records_read = int(quality.get("records_read") or 0)
    records_valid = int(quality.get("records_valid") or 0)
    database_source_count = int(overview.get("total_sources") or 0)
    return {
        "source_count": len(source_context) if source_context else database_source_count,
        "file_count": int(overview.get("total_documents") or 0),
        "link_count": max(0, database_source_count - int(overview.get("total_documents") or 0)),
        "record_count": records_read,
        "records_read": records_read,
        "records_valid": records_valid,
        "records_invalid": int(quality.get("records_invalid") or 0),
        "data_quality_score": round(float(quality.get("data_quality_score") or 0), 2),
        "parsing_coverage": round(records_valid / max(records_read, 1), 4),
        "processing_status": "ready" if database_source_count else "waiting_for_source",
        "duplicate_risk": "low",
        "rag_query_count": int(overview.get("total_rag_queries") or 0),
        "prediction_count": int(overview.get("total_predictions") or 0),
        "successful_ingestion_runs": int(quality.get("successful_runs") or 0),
        "rag_ready_documents": int(
            _fetch_one("SELECT COUNT(DISTINCT document_id) AS count FROM document_chunks").get("count") or 0
        ),
        "prediction_review_queue_count": len(queue),
        "prediction_review_queue": queue,
        "latest_document": latest_document,
        "document_processing_status": {
            str(row["processing_status"]): int(row["count"]) for row in status_rows
        },
        "ingestion_runs": runs,
        "recent_activity": recent_activity(),
    }


def latest_ingestion_status(run_id: str | None = None) -> dict[str, Any]:
    condition = "WHERE il.run_id = %s" if run_id else ""
    params: tuple[Any, ...] = (run_id,) if run_id else ()
    return _fetch_one(
        f"""
        SELECT il.run_id, il.run_id AS ingestion_run_id, s.name AS source_name,
               s.source_type, il.source_id, il.status, il.records_read,
               il.records_valid, il.records_invalid, il.data_quality_score,
               il.started_at, il.ended_at, il.manifest_path
        FROM ingestion_logs il LEFT JOIN sources s ON s.id = il.source_id
        {condition}
        ORDER BY il.created_at DESC, il.id DESC LIMIT 1
        """,
        params,
    )


def recent_activity() -> list[dict[str, Any]]:
    return _fetch_all(
        """
        SELECT created_at AS timestamp, activity_type AS actor,
               description AS action, 'success' AS status
        FROM v_recent_activity ORDER BY created_at DESC LIMIT 30
        """
    )


def _resolve_document_id(cursor, document_reference: Any = None) -> int | None:
    if isinstance(document_reference, int) or str(document_reference or "").isdigit():
        return int(document_reference)
    if document_reference:
        cursor.execute(
            "SELECT id FROM documents WHERE document_external_id = %s LIMIT 1",
            (str(document_reference),),
        )
    else:
        cursor.execute(
            """
            SELECT d.id FROM documents d
            WHERE EXISTS (SELECT 1 FROM document_chunks dc WHERE dc.document_id = d.id)
            ORDER BY d.created_at DESC, d.id DESC LIMIT 1
            """
        )
    row = cursor.fetchone()
    return int(row[0]) if row else None


def rag_query(question: str, document_reference: Any = None, top_k: int = 5) -> dict[str, Any]:
    from ai.rag.embedder import create_embedder
    from ai.rag.rag_service import RAGService
    from ai.rag.retriever import Retriever
    from ai.rag.vector_store import VectorStore

    with connect() as lookup_conn, lookup_conn.cursor() as cursor:
        document_id = _resolve_document_id(cursor, document_reference)
    embedder = create_embedder()
    store = VectorStore(use_pgvector=True, connection_string=database_url())
    if not store.connection:
        raise RuntimeError("pgvector connection or schema validation failed")
    try:
        service = RAGService(embedder, store, Retriever(embedder, store, top_k=top_k))
        response = service.retrieve_context(question, document_id=document_id, top_k=top_k)
        response["retrieval_backend"] = "postgresql/pgvector"
        response["embedding_dimension"] = embedder.get_embedding_dimension()
        response.setdefault("metadata", {})["document_db_id"] = document_id
        chunks = response.get("retrieved_context", [])
        with store.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO rag_query_logs (
                    document_id, user_query, retrieved_chunk_ids, retrieval_scores,
                    generated_response, answer_confidence, latency_ms, model_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    document_id,
                    question,
                    Json([chunk.get("chunk_id") for chunk in chunks]),
                    Json([chunk.get("similarity_score", 0.0) for chunk in chunks]),
                    response.get("answer"),
                    max([chunk.get("similarity_score", 0.0) for chunk in chunks], default=0.0),
                    int(response.get("metadata", {}).get("latency_ms", 0)),
                    embedder.model_name,
                ),
            )
        store.connection.commit()
        return _json_safe(response)
    finally:
        store.connection.close()


def _normalise_prediction(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("error"):
        return {
            "predicted_document_type": None,
            "confidence": 0.0,
            "model_version": "document_classifier_v1",
            "status": "failed",
            "review_reason": result.get("message") or result.get("error"),
            "top_predictions": [],
            "manual_review_required": False,
        }
    normalised = dict(result)
    normalised["manual_review_required"] = normalised.get("status") in {
        "needs_review",
        "waiting_for_source",
    }
    return normalised


def predict_and_log(payload: dict[str, Any]) -> dict[str, Any]:
    from ai.prediction.prediction_service import classify_document

    result = _normalise_prediction(classify_document(payload))
    document_reference = payload.get("document_external_id") or payload.get("document_id")
    with connect() as conn, conn.cursor() as cursor:
        document_id = _resolve_document_id(cursor, document_reference)
        source_id = payload.get("source_id") if isinstance(payload.get("source_id"), int) else None
        if source_id is None and payload.get("source_name"):
            cursor.execute("SELECT id FROM sources WHERE name = %s", (payload["source_name"],))
            row = cursor.fetchone()
            source_id = int(row[0]) if row else None
        cursor.execute(
            """
            INSERT INTO prediction_logs (
                source_id, document_id, model_name, model_version, input_payload,
                prediction_result, predicted_label, document_external_id,
                ingestion_run_id, confidence_score, status, review_reason
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                source_id,
                document_id,
                "document_classifier",
                result.get("model_version"),
                Json(payload),
                Json(result),
                result.get("predicted_document_type"),
                payload.get("document_external_id"),
                payload.get("ingestion_run_id"),
                float(result.get("confidence") or 0.0),
                result.get("status", "failed"),
                result.get("review_reason"),
            ),
        )
        prediction_log_id = int(cursor.fetchone()[0])
    result.update(
        {
            "prediction_log_id": prediction_log_id,
            "document_db_id": document_id,
            "document_external_id": payload.get("document_external_id"),
        }
    )
    return _json_safe(result)
