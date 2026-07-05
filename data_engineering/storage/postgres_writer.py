from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from data_engineering.utils.path_utils import resolve_project_path


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False)


def insert_or_get_source(conn, ingestion_result: dict[str, Any]) -> int | None:
    """Insert or upsert one source row.

    Expected Phat schema_v4 behavior:
    sources.name should be unique, so repeated Duy loads can safely resolve the
    same source_id instead of creating duplicate source rows.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sources (
                name, source_type, source_format, source_path, url,
                owner_name, sample_available, downstream_consumer, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE
            SET
                source_type = EXCLUDED.source_type,
                owner_name = EXCLUDED.owner_name,
                status = EXCLUDED.status,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
            """,
            (
                ingestion_result["source_name"],
                ingestion_result["source_type"],
                ingestion_result.get("source_type"),
                ingestion_result.get("input_path_or_url"),
                ingestion_result.get("input_path_or_url") if ingestion_result.get("source_type") == "api" else None,
                ingestion_result.get("owner"),
                True,
                "database, rag, prediction, dashboard, reports",
                "active",
            ),
        )
        row = cur.fetchone()
    return row[0] if row else None


def insert_source(conn, ingestion_result: dict[str, Any]) -> int | None:
    return insert_or_get_source(conn, ingestion_result)


def insert_pipeline_run(conn, ingestion_result: dict[str, Any]) -> int | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pipeline_runs (
                run_name, start_time, end_time, status
            )
            RETURNING id
            """,
            (
                f"{ingestion_result['source_name']}_{ingestion_result['run_id']}",
                ingestion_result.get("start_time"),
                ingestion_result.get("end_time"),
                ingestion_result["status"],
            ),
        )
        row = cur.fetchone()
    return row[0] if row else None


def _quality_fields(ingestion_result: dict[str, Any]) -> dict[str, Any]:
    data_quality = ingestion_result.get("data_quality") or {}
    manifest = ingestion_result.get("file_manifest") or {}
    return {
        "data_quality_score": ingestion_result.get("data_quality_score"),
        "required_missing_values": data_quality.get("required_missing_values"),
        "optional_missing_values": data_quality.get("optional_missing_values"),
        "duplicate_count": data_quality.get("duplicate_count"),
        "manifest_path": f"logs/manifests/{ingestion_result['run_id']}_manifest.json" if manifest else None,
    }


def insert_ingestion_log(
    conn,
    ingestion_result: dict[str, Any],
    source_id: int | None = None,
    pipeline_run_id: int | None = None,
) -> None:
    quality = _quality_fields(ingestion_result)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingestion_logs (
                run_id, source_id, pipeline_run_id, source_type, input_path_or_url, status,
                records_read, records_valid, records_invalid, error_message,
                raw_output_path, staging_output_path, clean_output_path,
                data_quality_score, required_missing_values, optional_missing_values,
                duplicate_count, manifest_path, started_at, ended_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s)
            """,
            (
                ingestion_result["run_id"],
                source_id,
                pipeline_run_id,
                ingestion_result["source_type"],
                ingestion_result["input_path_or_url"],
                ingestion_result["status"],
                ingestion_result["records_read"],
                ingestion_result["records_valid"],
                ingestion_result["records_invalid"],
                ingestion_result.get("error_message"),
                ingestion_result.get("raw_output_path"),
                ingestion_result.get("staging_output_path"),
                ingestion_result.get("clean_output_path"),
                quality["data_quality_score"],
                _json_dumps(quality["required_missing_values"] or {}),
                _json_dumps(quality["optional_missing_values"] or {}),
                quality["duplicate_count"],
                quality["manifest_path"],
                ingestion_result.get("start_time"),
                ingestion_result.get("end_time"),
            ),
        )


def insert_document(conn, pdf_metadata: dict[str, Any], source_id: int | None = None) -> int | None:
    """Insert one PDF document and preserve Duy's string ID as document_external_id."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO documents (
                source_id, document_external_id, file_name, file_type, file_size_bytes, file_hash_sha256, raw_path,
                staging_text_path, page_count, character_count, document_metadata,
                processing_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (document_external_id) DO UPDATE
            SET
                file_name = EXCLUDED.file_name,
                file_size_bytes = EXCLUDED.file_size_bytes,
                file_hash_sha256 = EXCLUDED.file_hash_sha256,
                staging_text_path = EXCLUDED.staging_text_path,
                page_count = EXCLUDED.page_count,
                character_count = EXCLUDED.character_count,
                document_metadata = EXCLUDED.document_metadata,
                processing_status = EXCLUDED.processing_status,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
            """,
            (
                source_id,
                pdf_metadata.get("document_id"),
                pdf_metadata.get("file_name"),
                "pdf",
                pdf_metadata.get("file_size_bytes"),
                pdf_metadata.get("file_hash_sha256"),
                pdf_metadata.get("raw_output_path"),
                pdf_metadata.get("staging_text_path") or pdf_metadata.get("staging_text_output_path") or pdf_metadata.get("text_output_path"),
                pdf_metadata.get("page_count"),
                pdf_metadata.get("total_characters"),
                _json_dumps(pdf_metadata),
                "extracted",
            ),
        )
        row = cur.fetchone()
    return row[0] if row else None


def insert_document_pages(conn, document_pages_jsonl_path: str | Path, document_id: int) -> int:
    inserted = 0
    resolved = resolve_project_path(document_pages_jsonl_path)
    if resolved is None or not resolved.exists():
        raise FileNotFoundError(f"document_pages JSONL not found: {document_pages_jsonl_path}")
    with resolved.open("r", encoding="utf-8") as file, conn.cursor() as cur:
        for line in file:
            page = json.loads(line)
            cur.execute(
                """
                INSERT INTO document_pages (
                    document_id, page_number, page_text, character_count, is_empty
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    document_id,
                    page["page_number"],
                    page.get("text"),
                    page.get("character_count"),
                    page.get("is_empty", False),
                ),
            )
            inserted += 1
    return inserted


def insert_structured_records(conn, clean_csv_path: str | Path, source_id: int) -> int:
    resolved = resolve_project_path(clean_csv_path)
    if resolved is None or not resolved.exists():
        raise FileNotFoundError(f"Clean CSV not found: {clean_csv_path}")
    df = pd.read_csv(resolved)
    inserted = 0
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT INTO structured_records (source_id, record_data, status)
                VALUES (%s, %s, %s)
                """,
                (source_id, _json_dumps(row.dropna().to_dict()), "clean"),
            )
            inserted += 1
    return inserted


def build_dry_run_summary(ingestion_result: dict[str, Any]) -> dict[str, Any]:
    quality = _quality_fields(ingestion_result)
    target_tables = ["sources", "pipeline_runs", "ingestion_logs"]
    if ingestion_result.get("source_type") == "pdf":
        target_tables.extend(["documents", "document_pages"])
    elif ingestion_result.get("source_type") in {"csv", "excel", "api"}:
        target_tables.append("structured_records")
    return {
        "target_tables": target_tables,
        "source_name": ingestion_result.get("source_name"),
        "source_type": ingestion_result.get("source_type"),
        "run_id": ingestion_result.get("run_id"),
        "status": ingestion_result.get("status"),
        "records_valid": ingestion_result.get("records_valid"),
        "data_quality_score": quality["data_quality_score"],
        "manifest_path": quality["manifest_path"],
        "ready_for_insert": ingestion_result.get("status") in {"success", "partial_success"},
        "would_insert": {
            "sources": 1,
            "pipeline_runs": 1,
            "ingestion_logs": 1,
            "documents": 1 if ingestion_result.get("source_type") == "pdf" else 0,
            "document_pages": ingestion_result.get("records_valid", 0) if ingestion_result.get("source_type") == "pdf" else 0,
            "structured_records": ingestion_result.get("records_valid", 0)
            if ingestion_result.get("source_type") in {"csv", "excel", "api"}
            else 0,
        },
    }


def load_ingestion_result_to_postgres(conn, ingestion_result: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "run_id": ingestion_result.get("run_id"),
        "source_name": ingestion_result.get("source_name"),
        "source_type": ingestion_result.get("source_type"),
        "status": "started",
        "inserted": {},
    }
    try:
        source_id = insert_or_get_source(conn, ingestion_result)
        pipeline_run_id = insert_pipeline_run(conn, ingestion_result)
        insert_ingestion_log(conn, ingestion_result, source_id=source_id, pipeline_run_id=pipeline_run_id)
        summary["source_id"] = source_id
        summary["pipeline_run_id"] = pipeline_run_id
        summary["inserted"].update({"sources": 1, "pipeline_runs": 1, "ingestion_logs": 1})

        if ingestion_result.get("source_type") == "pdf":
            pdf_metadata = dict(ingestion_result.get("pdf_metadata") or {})
            file_manifest = ingestion_result.get("file_manifest") or {}
            if file_manifest.get("file_hash_sha256"):
                pdf_metadata["file_hash_sha256"] = file_manifest["file_hash_sha256"]
            document_id = insert_document(conn, pdf_metadata, source_id=source_id)
            document_pages_path = ingestion_result.get("document_pages_output_path") or pdf_metadata.get("document_pages_output_path")
            pages_inserted = insert_document_pages(conn, document_pages_path, document_id) if document_id and document_pages_path else 0
            summary["document_db_id"] = document_id
            summary["inserted"].update({"documents": 1 if document_id else 0, "document_pages": pages_inserted})
        elif ingestion_result.get("source_type") in {"csv", "excel", "api"}:
            records_inserted = insert_structured_records(conn, ingestion_result["clean_output_path"], source_id)
            summary["inserted"]["structured_records"] = records_inserted

        conn.commit()
        summary["status"] = "success"
    except Exception as exc:
        conn.rollback()
        summary["status"] = "failed"
        summary["error"] = str(exc)
    return summary


def build_document_page_insert_plan(document_pages_jsonl_path: str | Path) -> dict[str, Any]:
    """Return a dry-run plan showing Duy external document IDs and page counts.

    document_pages.document_id must receive Phat's internal documents.id, not
    Duy's string document_id. The string ID maps first to
    documents.document_external_id.
    """
    path = Path(document_pages_jsonl_path)
    external_ids: dict[str, int] = {}
    total_pages = 0
    empty_pages = 0
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            page = json.loads(line)
            total_pages += 1
            external_id = page["document_id"]
            external_ids[external_id] = external_ids.get(external_id, 0) + 1
            if page.get("is_empty"):
                empty_pages += 1
    return {
        "source_file": path.as_posix(),
        "document_external_ids": external_ids,
        "total_pages": total_pages,
        "empty_pages": empty_pages,
        "target_table": "document_pages",
        "id_mapping_rule": "document_pages.document_id must use documents.id after resolving documents.document_external_id",
    }
