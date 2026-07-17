from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHAT_WEEK6_ROOT = PROJECT_ROOT.parent / "DataVision_Phat" / "week6"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "phat_handoff" / "phat_week6_mapping_summary.json"


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    for base in (PROJECT_ROOT.resolve(), PROJECT_ROOT.parent.resolve()):
        try:
            return resolved.relative_to(base).as_posix()
        except ValueError:
            continue
    return f"external/{path.name}"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_file(folder: Path, pattern: str) -> Path | None:
    files = sorted(folder.glob(pattern))
    return files[-1] if files else None


def _records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not payload:
        return []
    if isinstance(payload, list):
        return payload
    first_value = next(iter(payload.values()), [])
    return first_value if isinstance(first_value, list) else []


def _schema_findings(schema_path: Path) -> dict[str, Any]:
    if not schema_path.exists():
        return {
            "schema_file": _portable_path(schema_path),
            "exists": False,
            "notes": ["schema_v4.sql not found"],
        }

    text = schema_path.read_text(encoding="utf-8")
    notes: list[str] = []
    has_vector_extension = "CREATE EXTENSION IF NOT EXISTS vector" in text
    has_document_external_id = "document_external_id" in text
    has_prediction_status = "status VARCHAR(50)" in text and "chk_prediction_status" in text
    has_review_reason = "review_reason" in text
    has_data_quality_score = "data_quality_score FLOAT" in text
    has_source_unique = "name VARCHAR(255) NOT null UNIQUE" in text or "name VARCHAR(255) NOT NULL UNIQUE" in text
    has_prediction_missing_comma = (
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n    CONSTRAINT chk_prediction_status" in text
        or "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\r\n    CONSTRAINT chk_prediction_status" in text
    )

    if has_prediction_missing_comma:
        notes.append("schema_v4.sql appears to be missing a comma before prediction_logs constraints.")
    if not has_vector_extension:
        notes.append("pgvector extension statement not found.")
    if not has_document_external_id:
        notes.append("documents.document_external_id not found.")

    return {
        "schema_file": _portable_path(schema_path),
        "exists": True,
        "has_vector_extension": has_vector_extension,
        "has_source_unique_constraint": has_source_unique,
        "has_document_external_id": has_document_external_id,
        "has_prediction_status_constraint": has_prediction_status,
        "has_prediction_review_reason": has_review_reason,
        "has_ingestion_data_quality_score": has_data_quality_score,
        "has_prediction_logs_missing_comma_risk": has_prediction_missing_comma,
        "notes": notes,
    }


def build_mapping_summary(phat_week6_root: Path = DEFAULT_PHAT_WEEK6_ROOT) -> dict[str, Any]:
    outputs_root = phat_week6_root / "outputs"
    ingestion_dir = outputs_root / "ingestion_data_Duy"
    prediction_dir = outputs_root / "prediction_log_data_Tuong"
    chunks_dir = outputs_root / "document_chunk_data_Lap"
    dashboard_dir = outputs_root / "dashboard_view_samples_PhiHung"

    sources_file = _latest_file(ingestion_dir, "sources_*.json")
    documents_file = _latest_file(ingestion_dir, "documents_*.json")
    ingestion_logs_file = _latest_file(ingestion_dir, "ingestion_logs_*.json")
    document_pages_file = _latest_file(ingestion_dir, "document_pages_*.json")
    structured_records_file = _latest_file(ingestion_dir, "structured_records_*.json")
    prediction_logs_file = _latest_file(prediction_dir, "prediction_logs_*.json")
    chunks_file = _latest_file(chunks_dir, "document_chunks_*.json")
    dashboard_file = _latest_file(dashboard_dir, "v_dashboard_overview_*.json")
    data_quality_file = _latest_file(dashboard_dir, "v_data_quality_dashboard_*.json")
    view_files = sorted(dashboard_dir.glob("v_*.json")) if dashboard_dir.exists() else []

    sources = _records(_read_json(sources_file)) if sources_file else []
    documents = _records(_read_json(documents_file)) if documents_file else []
    ingestion_logs = _records(_read_json(ingestion_logs_file)) if ingestion_logs_file else []
    document_pages = _records(_read_json(document_pages_file)) if document_pages_file else []
    structured_records = _records(_read_json(structured_records_file)) if structured_records_file else []
    prediction_logs = _records(_read_json(prediction_logs_file)) if prediction_logs_file else []
    chunks = _records(_read_json(chunks_file)) if chunks_file else []
    dashboard = _records(_read_json(dashboard_file)) if dashboard_file else []
    data_quality = _records(_read_json(data_quality_file)) if data_quality_file else []
    dashboard_views = {
        view_file.stem.rsplit("_", 1)[0]: {
            "path": _portable_path(view_file),
            "row_count": len(_records(_read_json(view_file))),
        }
        for view_file in view_files
    }

    source_id_map = {
        row.get("name"): {
            "source_id": row.get("id"),
            "source_type": row.get("source_type"),
            "source_format": row.get("source_format"),
            "source_path": row.get("source_path"),
        }
        for row in sources
    }
    document_id_map = {
        row.get("document_external_id"): {
            "document_db_id": row.get("id"),
            "source_id": row.get("source_id"),
            "file_name": row.get("file_name"),
            "page_count": row.get("page_count"),
            "character_count": row.get("character_count"),
            "processing_status": row.get("processing_status"),
        }
        for row in documents
    }

    status_counts: dict[str, int] = {}
    for row in prediction_logs:
        status = row.get("status")
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "source": "DataVision_Phat/week6 outputs",
        "phat_week6_root": _portable_path(phat_week6_root),
        "files_used": {
            "schema_v4": _portable_path(phat_week6_root / "database" / "schema_v4.sql"),
            "setup_database_v2": _portable_path(phat_week6_root / "database" / "setup_database_v2.sql"),
            "reset_database_v2": _portable_path(phat_week6_root / "database" / "reset_database_v2.sql"),
            "analytics_views_v3": _portable_path(phat_week6_root / "database" / "analytics_views_v3.sql"),
            "validation_queries_v2": _portable_path(phat_week6_root / "database" / "validation_queries_v2.sql"),
            "validate_ingestion_data": _portable_path(phat_week6_root / "database" / "validate_ingestion_data.sql"),
            "sources": _portable_path(sources_file) if sources_file else None,
            "documents": _portable_path(documents_file) if documents_file else None,
            "ingestion_logs": _portable_path(ingestion_logs_file) if ingestion_logs_file else None,
            "document_pages": _portable_path(document_pages_file) if document_pages_file else None,
            "structured_records": _portable_path(structured_records_file) if structured_records_file else None,
            "prediction_logs": _portable_path(prediction_logs_file) if prediction_logs_file else None,
            "document_chunks": _portable_path(chunks_file) if chunks_file else None,
            "dashboard_overview": _portable_path(dashboard_file) if dashboard_file else None,
            "data_quality_dashboard": _portable_path(data_quality_file) if data_quality_file else None,
        },
        "schema_findings": _schema_findings(phat_week6_root / "database" / "schema_v4.sql"),
        "source_id_map": source_id_map,
        "document_id_map": document_id_map,
        "counts": {
            "sources": len(sources),
            "documents": len(documents),
            "ingestion_logs": len(ingestion_logs),
            "document_pages": len(document_pages),
            "structured_records_sample_rows": len(structured_records),
            "prediction_logs": len(prediction_logs),
            "document_chunks": len(chunks),
        },
        "prediction_log_status_counts": status_counts,
        "dashboard_overview": dashboard[0] if dashboard else {},
        "data_quality_dashboard": data_quality,
        "dashboard_view_samples": dashboard_views,
        "integration_status": {
            "duy_ingestion_loaded": len(sources) == 4 and len(ingestion_logs) == 4 and len(document_pages) == 36,
            "document_external_id_resolved": "doc_dataflow_technical_report" in document_id_map,
            "structured_records_loaded": len(structured_records) == 11524,
            "lap_chunks_loaded": len(chunks) > 0,
            "tuong_prediction_logs_loaded": len(prediction_logs) == 10,
            "phi_hung_dashboard_views_exported": bool(dashboard_views),
        },
        "duy_expected_validation_totals": {
            "sources": 4,
            "ingestion_logs": 4,
            "total_records_read": 11560,
            "document_pages": 36,
            "structured_records": 11524,
            "average_data_quality_score": 99.63,
        },
        "id_rules": {
            "source_id": "Phat sources.id, resolved from Duy source_name",
            "document_external_id": "Duy stable document key, stored in Phat documents.document_external_id",
            "document_db_id": "Phat documents.id, used by document_pages/document_chunks/rag_query_logs/prediction_logs.document_id",
            "ingestion_run_id": "Duy ingestion run UUID, stored in ingestion_logs.run_id and prediction_logs.ingestion_run_id",
        },
    }


def main() -> int:
    phat_root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PHAT_WEEK6_ROOT
    summary = build_mapping_summary(phat_root)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote Phat mapping summary: {OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Sources: {summary['counts']['sources']}")
    print(f"Documents: {summary['counts']['documents']}")
    print(f"Document chunks: {summary['counts']['document_chunks']}")
    print(f"Prediction logs: {summary['counts']['prediction_logs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
