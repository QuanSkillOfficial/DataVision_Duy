from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from data_engineering.utils.path_utils import resolve_project_path


def _read_json(path: str | Path) -> dict[str, Any]:
    resolved = resolve_project_path(path)
    if resolved is None or not resolved.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def _safe_document_id(file_name: str) -> str:
    stem = Path(file_name).stem.lower()
    safe_stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return f"doc_{safe_stem or 'unknown'}"


def build_pdf_prediction_payload(
    *,
    ingestion_log_path: str | Path = "week2/logs/pdf_ingestion_log.json",
    metadata_path: str | Path = "week2/logs/pdf_metadata.json",
    source_system: str = "manual_upload",
    source_id: int | None = None,
    document_db_id: int | None = None,
) -> dict[str, Any]:
    ingestion_log = _read_json(ingestion_log_path)
    metadata = _read_json(metadata_path)
    input_relative = ingestion_log["input_path_or_url"]
    input_path = resolve_project_path(input_relative)
    text_relative_path = (
        metadata.get("staging_text_output_path")
        or metadata.get("staging_output_path")
        or ingestion_log.get("staging_text_output_path")
        or ingestion_log["staging_output_path"]
    )
    staging_path = resolve_project_path(text_relative_path)
    extracted_text = staging_path.read_text(encoding="utf-8") if staging_path and staging_path.exists() else ""
    file_name = input_path.name if input_path else metadata.get("file_name", "unknown.pdf")

    parsing_status = "ready" if ingestion_log.get("status") == "success" else ingestion_log.get("status")
    if not extracted_text.strip() and parsing_status == "ready":
        parsing_status = "partial_success"

    document_external_id = metadata.get("document_id") or ingestion_log.get("document_id") or _safe_document_id(file_name)
    source_name = metadata.get("source_name") or ingestion_log.get("source_name")
    ingestion_run_id = ingestion_log["run_id"]

    return {
        # Backward-compatible alias for earlier Tuong contracts.
        "document_id": document_external_id,
        "document_external_id": document_external_id,
        "document_db_id": document_db_id,
        "source_id": source_id,
        "source_name": source_name,
        "file_name": file_name,
        "file_type": Path(file_name).suffix.lower().lstrip("."),
        "file_size": input_path.stat().st_size if input_path and input_path.exists() else metadata.get("file_size_bytes"),
        "text_length": metadata.get("total_characters") or len(extracted_text),
        "num_pages": metadata.get("page_count") or metadata.get("total_pages", 0),
        "source_system": source_system,
        "extracted_text": extracted_text,
        "ingestion_run_id": ingestion_run_id,
        "raw_output_path": ingestion_log.get("raw_output_path"),
        "staging_output_path": text_relative_path,
        "staging_csv_output_path": metadata.get("staging_csv_output_path"),
        "document_pages_output_path": metadata.get("document_pages_output_path"),
        "clean_output_path": ingestion_log.get("clean_output_path"),
        "records_read": ingestion_log.get("records_read", 0),
        "records_valid": ingestion_log.get("records_valid", 0),
        "records_invalid": ingestion_log.get("records_invalid", 0),
        "empty_pages": metadata.get("empty_pages", []),
        "empty_page_count": metadata.get("empty_page_count", 0),
        "parsing_status": parsing_status,
    }
