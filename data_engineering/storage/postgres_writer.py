from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from data_engineering.utils.path_utils import resolve_project_path


REQUIRED_SCHEMA_COLUMNS = {
    "sources": {
        "id",
        "name",
        "source_type",
        "source_format",
        "source_path",
        "url",
        "owner_name",
        "sample_available",
        "downstream_consumer",
        "status",
        "updated_at",
    },
    "pipeline_runs": {"id", "run_name", "start_time", "end_time", "status"},
    "ingestion_logs": {
        "run_id",
        "source_id",
        "pipeline_run_id",
        "source_type",
        "input_path_or_url",
        "status",
        "records_read",
        "records_valid",
        "records_invalid",
        "error_message",
        "raw_output_path",
        "staging_output_path",
        "clean_output_path",
        "data_quality_score",
        "required_missing_values",
        "optional_missing_values",
        "duplicate_count",
        "manifest_path",
        "started_at",
        "ended_at",
    },
    "documents": {
        "id",
        "source_id",
        "document_external_id",
        "file_name",
        "file_type",
        "file_size_bytes",
        "file_hash_sha256",
        "raw_path",
        "staging_text_path",
        "page_count",
        "character_count",
        "document_metadata",
        "processing_status",
        "updated_at",
    },
    "document_pages": {"document_id", "page_number", "page_text", "character_count", "is_empty"},
    "structured_records": {"source_id", "record_data", "status"},
}


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _source_format(ingestion_result: dict[str, Any]) -> str:
    configured_format = ingestion_result.get("source_format")
    if configured_format:
        return str(configured_format).lower()

    source_type = str(ingestion_result.get("source_type") or "").lower()
    if source_type == "api":
        return "json"

    input_path_or_url = str(ingestion_result.get("input_path_or_url") or "")
    suffix = Path(input_path_or_url).suffix.lower().lstrip(".")
    return suffix or source_type


def insert_or_get_source(conn, ingestion_result: dict[str, Any]) -> int:
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
                source_format = EXCLUDED.source_format,
                source_path = EXCLUDED.source_path,
                url = EXCLUDED.url,
                owner_name = EXCLUDED.owner_name,
                sample_available = EXCLUDED.sample_available,
                downstream_consumer = EXCLUDED.downstream_consumer,
                status = EXCLUDED.status,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
            """,
            (
                ingestion_result["source_name"],
                ingestion_result["source_type"],
                _source_format(ingestion_result),
                ingestion_result.get("input_path_or_url"),
                ingestion_result.get("input_path_or_url") if ingestion_result.get("source_type") == "api" else None,
                ingestion_result.get("owner"),
                True,
                "database, rag, prediction, dashboard, reports",
                "active",
            ),
        )
        row = cur.fetchone()
    if not row:
        raise RuntimeError(f"PostgreSQL did not return a source ID for {ingestion_result['source_name']}")
    return int(row[0])


def insert_source(conn, ingestion_result: dict[str, Any]) -> int:
    return insert_or_get_source(conn, ingestion_result)


def insert_pipeline_run(conn, ingestion_result: dict[str, Any]) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pipeline_runs (
                run_name, start_time, end_time, status
            )
            VALUES (%s, %s, %s, %s)
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
    if not row:
        raise RuntimeError(f"PostgreSQL did not return a pipeline run ID for {ingestion_result['run_id']}")
    return int(row[0])


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


def ingestion_run_exists(conn, run_id: str) -> bool:
    """Return whether an ingestion run has already been loaded.

    Phat's schema_v4 does not declare ingestion_logs.run_id as UNIQUE. This
    guard keeps the loader idempotent and prevents duplicate structured rows
    when the same run package is submitted more than once.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM ingestion_logs WHERE run_id = %s LIMIT 1",
            (run_id,),
        )
        return cur.fetchone() is not None


def get_existing_ingestion_mapping(conn, ingestion_result: dict[str, Any]) -> dict[str, int | None]:
    """Resolve IDs for an idempotently skipped run so handoffs remain DB-enriched."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_id, pipeline_run_id
            FROM ingestion_logs
            WHERE run_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (ingestion_result["run_id"],),
        )
        row = cur.fetchone()

    mapping: dict[str, int | None] = {
        "source_id": int(row[0]) if row and row[0] is not None else None,
        "pipeline_run_id": int(row[1]) if row and row[1] is not None else None,
        "document_db_id": None,
    }
    pdf_metadata = ingestion_result.get("pdf_metadata") or {}
    document_external_id = (
        ingestion_result.get("document_external_id")
        or ingestion_result.get("document_id")
        or pdf_metadata.get("document_external_id")
        or pdf_metadata.get("document_id")
    )
    if document_external_id:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM documents WHERE document_external_id = %s LIMIT 1",
                (document_external_id,),
            )
            document_row = cur.fetchone()
        if document_row:
            mapping["document_db_id"] = int(document_row[0])
    return mapping


def insert_document(conn, pdf_metadata: dict[str, Any], source_id: int | None = None) -> int:
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
                source_id = EXCLUDED.source_id,
                file_name = EXCLUDED.file_name,
                file_type = EXCLUDED.file_type,
                file_size_bytes = EXCLUDED.file_size_bytes,
                file_hash_sha256 = EXCLUDED.file_hash_sha256,
                raw_path = EXCLUDED.raw_path,
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
                pdf_metadata.get("document_external_id") or pdf_metadata.get("document_id"),
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
    if not row:
        raise RuntimeError("PostgreSQL did not return a document ID")
    return int(row[0])


def insert_document_pages(conn, document_pages_jsonl_path: str | Path, document_id: int) -> int:
    inserted = 0
    resolved = resolve_project_path(document_pages_jsonl_path)
    if resolved is None or not resolved.exists():
        raise FileNotFoundError(f"document_pages JSONL not found: {document_pages_jsonl_path}")
    with resolved.open("r", encoding="utf-8") as file, conn.cursor() as cur:
        # document_pages has no run_id or unique page constraint in schema_v4.
        # Replace the document snapshot so a new ingestion run cannot duplicate pages.
        cur.execute("DELETE FROM document_pages WHERE document_id = %s", (document_id,))
        for line in file:
            page = json.loads(line)
            page_text = page.get("text")
            character_count = page.get("character_count")
            if character_count is None:
                character_count = page.get("char_count")
            if character_count is None and isinstance(page_text, str):
                character_count = len(page_text)
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
                    page_text,
                    character_count,
                    page.get("is_empty", False),
                ),
            )
            inserted += 1
    return inserted


def insert_structured_records(
    conn,
    clean_csv_path: str | Path,
    source_id: int,
    *,
    replace_existing: bool = True,
    limit: int | None = None,
) -> int:
    resolved = resolve_project_path(clean_csv_path)
    if resolved is None or not resolved.exists():
        raise FileNotFoundError(f"Clean CSV not found: {clean_csv_path}")
    df = pd.read_csv(resolved)
    if limit is not None:
        if limit < 0:
            raise ValueError("Structured record limit must be zero or greater")
        df = df.head(limit)
    inserted = 0
    with conn.cursor() as cur:
        # schema_v4 structured_records has no ingestion run identifier. Treat
        # Duy's clean output as the latest source snapshot to avoid double counts.
        if replace_existing:
            cur.execute("DELETE FROM structured_records WHERE source_id = %s", (source_id,))
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


def validate_target_schema(conn) -> dict[str, list[str]]:
    """Fail before loading if Phat's database is not compatible with Duy's writer."""
    table_names = sorted(REQUIRED_SCHEMA_COLUMNS)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = ANY(%s)
            """,
            (table_names,),
        )
        rows = cur.fetchall()

    actual: dict[str, set[str]] = {table: set() for table in table_names}
    for table_name, column_name in rows:
        if table_name in actual:
            actual[table_name].add(column_name)

    missing = {
        table: sorted(required - actual[table])
        for table, required in REQUIRED_SCHEMA_COLUMNS.items()
        if required - actual[table]
    }
    if missing:
        details = "; ".join(f"{table}: {columns}" for table, columns in sorted(missing.items()))
        raise RuntimeError(f"PostgreSQL schema is not compatible with Duy Week 7 writer ({details})")

    return {table: sorted(columns) for table, columns in actual.items()}


def build_dry_run_summary(
    ingestion_result: dict[str, Any],
    *,
    structured_record_limit: int | None = None,
) -> dict[str, Any]:
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
            "structured_records": min(ingestion_result.get("records_valid", 0), structured_record_limit)
            if structured_record_limit is not None and ingestion_result.get("source_type") in {"csv", "excel", "api"}
            else ingestion_result.get("records_valid", 0)
            if ingestion_result.get("source_type") in {"csv", "excel", "api"}
            else 0,
        },
    }


def load_ingestion_result_to_postgres(
    conn,
    ingestion_result: dict[str, Any],
    *,
    structured_record_limit: int | None = None,
) -> dict[str, Any]:
    pdf_metadata = ingestion_result.get("pdf_metadata") or {}
    document_external_id = (
        ingestion_result.get("document_external_id")
        or ingestion_result.get("document_id")
        or pdf_metadata.get("document_external_id")
        or pdf_metadata.get("document_id")
    )
    summary: dict[str, Any] = {
        "run_id": ingestion_result.get("run_id"),
        "source_name": ingestion_result.get("source_name"),
        "source_type": ingestion_result.get("source_type"),
        "status": "started",
        "inserted": {},
        "document_external_id": document_external_id,
    }
    if ingestion_result.get("status") not in {"success", "partial_success"}:
        summary["status"] = "skipped"
        summary["reason"] = "Only successful or partial-success ingestion runs can be loaded"
        return summary

    try:
        if ingestion_run_exists(conn, ingestion_result["run_id"]):
            mapping = get_existing_ingestion_mapping(conn, ingestion_result)
            source_id = mapping.get("source_id") or insert_or_get_source(
                conn, ingestion_result
            )
            summary.update(mapping)
            summary["source_id"] = source_id
            summary["inserted"].update(
                {"sources": 0, "pipeline_runs": 0, "ingestion_logs": 0}
            )

            # The schema stores structured rows and PDF pages as the latest
            # source/document snapshot, not per ingestion run. Refresh those
            # rows so a smoke load can be upgraded to a full load without
            # duplicating pipeline_runs or ingestion_logs.
            if ingestion_result.get("source_type") == "pdf":
                pdf_metadata = dict(ingestion_result.get("pdf_metadata") or {})
                file_manifest = ingestion_result.get("file_manifest") or {}
                if file_manifest.get("file_hash_sha256"):
                    pdf_metadata["file_hash_sha256"] = file_manifest[
                        "file_hash_sha256"
                    ]
                document_id = insert_document(conn, pdf_metadata, source_id=source_id)
                document_pages_path = ingestion_result.get(
                    "document_pages_output_path"
                ) or pdf_metadata.get("document_pages_output_path")
                pages_inserted = (
                    insert_document_pages(conn, document_pages_path, document_id)
                    if document_pages_path
                    else 0
                )
                summary["document_db_id"] = document_id
                summary["document_external_id"] = (
                    pdf_metadata.get("document_external_id")
                    or pdf_metadata.get("document_id")
                )
                summary["inserted"].update(
                    {"documents": 0, "document_pages": pages_inserted}
                )
            elif ingestion_result.get("source_type") in {"csv", "excel", "api"}:
                summary["inserted"]["structured_records"] = (
                    insert_structured_records(
                        conn,
                        ingestion_result["clean_output_path"],
                        int(source_id),
                        limit=structured_record_limit,
                    )
                )

            conn.commit()
            summary["status"] = "success"
            summary["load_action"] = "refreshed_existing_run_snapshot"
            summary["reason"] = (
                "ingestion_run_id already existed; refreshed mutable source data"
            )
            return summary

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
            summary["document_external_id"] = pdf_metadata.get("document_external_id") or pdf_metadata.get("document_id")
            summary["inserted"].update({"documents": 1 if document_id else 0, "document_pages": pages_inserted})
        elif ingestion_result.get("source_type") in {"csv", "excel", "api"}:
            records_inserted = insert_structured_records(
                conn,
                ingestion_result["clean_output_path"],
                source_id,
                limit=structured_record_limit,
            )
            summary["inserted"]["structured_records"] = records_inserted

        conn.commit()
        summary["status"] = "success"
        summary["load_action"] = "inserted_new_run"
    except Exception as exc:
        conn.rollback()
        summary["status"] = "failed"
        summary["error"] = str(exc)
    return summary


def query_integration_counts(
    conn,
    *,
    run_ids: list[str],
    source_names: list[str],
    document_external_ids: list[str],
) -> dict[str, int]:
    """Query loaded rows back from Phat's schema_v4 for integration proof."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM sources WHERE name = ANY(%s)),
                (SELECT COUNT(*) FROM ingestion_logs WHERE run_id = ANY(%s)),
                (
                    SELECT COUNT(*)
                    FROM pipeline_runs pr
                    JOIN ingestion_logs il ON il.pipeline_run_id = pr.id
                    WHERE il.run_id = ANY(%s)
                ),
                (
                    SELECT COUNT(*)
                    FROM documents
                    WHERE document_external_id = ANY(%s)
                ),
                (
                    SELECT COUNT(*)
                    FROM document_pages dp
                    JOIN documents d ON d.id = dp.document_id
                    WHERE d.document_external_id = ANY(%s)
                ),
                (
                    SELECT COUNT(*)
                    FROM structured_records sr
                    JOIN sources s ON s.id = sr.source_id
                    WHERE s.name = ANY(%s)
                )
            """,
            (
                source_names,
                run_ids,
                run_ids,
                document_external_ids,
                document_external_ids,
                source_names,
            ),
        )
        row = cur.fetchone()

    if row is None:
        raise RuntimeError("PostgreSQL verification query returned no result")
    keys = [
        "sources",
        "ingestion_logs",
        "pipeline_runs",
        "documents",
        "document_pages",
        "structured_records",
    ]
    return {key: int(value) for key, value in zip(keys, row)}


def query_loaded_run_ids(conn, run_ids: list[str]) -> list[str]:
    """Return the exact requested ingestion UUIDs currently present in PostgreSQL."""
    if not run_ids:
        return []
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT run_id
            FROM ingestion_logs
            WHERE run_id = ANY(%s)
            ORDER BY run_id
            """,
            (run_ids,),
        )
        rows = cur.fetchall()
    return [str(row[0]) for row in rows if row and row[0] is not None]


def build_document_page_insert_plan(document_pages_jsonl_path: str | Path) -> dict[str, Any]:
    """Return a dry-run plan showing Duy external document IDs and page counts.

    document_pages.document_id must receive Phat's internal documents.id, not
    Duy's string document_id. The string ID maps first to
    documents.document_external_id.
    """
    path = resolve_project_path(document_pages_jsonl_path)
    if path is None or not path.exists():
        raise FileNotFoundError(
            f"document_pages JSONL not found: {document_pages_jsonl_path}"
        )
    external_ids: dict[str, int] = {}
    total_pages = 0
    empty_pages = 0
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            page = json.loads(line)
            total_pages += 1
            external_id = page.get("document_external_id") or page.get(
                "document_id"
            )
            if not external_id:
                raise ValueError(
                    "Each document page must include document_external_id or document_id"
                )
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
