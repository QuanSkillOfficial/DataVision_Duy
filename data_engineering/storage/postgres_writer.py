from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def insert_source(conn, ingestion_result: dict[str, Any]) -> int | None:
    """Insert or upsert one source row.

    This function is intentionally dependency-light for Week 5. It accepts a DB-API
    connection and uses parameterized SQL expected by Phat's schema_v2/v3 direction.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sources (name, source_type, owner_name, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
            """,
            (
                ingestion_result["source_name"],
                ingestion_result["source_type"],
                ingestion_result.get("owner"),
                "active",
            ),
        )
        row = cur.fetchone()
    return row[0] if row else None


def insert_ingestion_log(conn, ingestion_result: dict[str, Any], source_id: int | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingestion_logs (
                run_id, source_id, source_type, input_path_or_url, status,
                records_read, records_valid, records_invalid, error_message,
                raw_output_path, staging_output_path, clean_output_path,
                started_at, ended_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ingestion_result["run_id"],
                source_id,
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
                ingestion_result.get("start_time"),
                ingestion_result.get("end_time"),
            ),
        )


def insert_document(conn, pdf_metadata: dict[str, Any], source_id: int | None = None) -> int | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO documents (
                source_id, file_name, file_type, file_size_bytes, raw_path,
                staging_text_path, page_count, character_count, document_metadata,
                processing_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                source_id,
                pdf_metadata.get("file_name"),
                "pdf",
                pdf_metadata.get("file_size_bytes"),
                pdf_metadata.get("raw_output_path"),
                pdf_metadata.get("staging_output_path"),
                pdf_metadata.get("page_count"),
                pdf_metadata.get("total_characters"),
                json.dumps(pdf_metadata),
                "extracted",
            ),
        )
        row = cur.fetchone()
    return row[0] if row else None


def insert_document_pages(conn, document_pages_jsonl_path: str | Path, document_id: int) -> int:
    inserted = 0
    with Path(document_pages_jsonl_path).open("r", encoding="utf-8") as file, conn.cursor() as cur:
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
    df = pd.read_csv(clean_csv_path)
    inserted = 0
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT INTO structured_records (source_id, record_data, processing_status)
                VALUES (%s, %s, %s)
                """,
                (source_id, json.dumps(row.dropna().to_dict()), "clean"),
            )
            inserted += 1
    return inserted


def build_dry_run_summary(ingestion_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_tables": ["sources", "ingestion_logs"],
        "source_name": ingestion_result.get("source_name"),
        "source_type": ingestion_result.get("source_type"),
        "run_id": ingestion_result.get("run_id"),
        "status": ingestion_result.get("status"),
        "records_valid": ingestion_result.get("records_valid"),
        "ready_for_insert": ingestion_result.get("status") in {"success", "partial_success"},
    }

