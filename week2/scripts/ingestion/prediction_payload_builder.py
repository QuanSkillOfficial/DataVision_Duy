from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_document_id(file_name: str) -> str:
    stem = Path(file_name).stem.lower()
    safe_stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return f"doc_{safe_stem or 'unknown'}"


def build_pdf_prediction_payload(
    *,
    ingestion_log_path: Path = PROJECT_ROOT / "logs/pdf_ingestion_log.json",
    metadata_path: Path = PROJECT_ROOT / "logs/pdf_metadata.json",
    source_system: str = "manual_upload",
) -> dict[str, Any]:
    ingestion_log = _read_json(ingestion_log_path)
    metadata = _read_json(metadata_path)

    input_relative = ingestion_log["input_path_or_url"]
    input_path = PROJECT_ROOT / input_relative
    text_relative_path = (
        metadata.get("staging_text_output_path")
        or metadata.get("staging_output_path")
        or ingestion_log.get("staging_text_output_path")
        or ingestion_log["staging_output_path"]
    )
    staging_path = PROJECT_ROOT / text_relative_path
    extracted_text = staging_path.read_text(encoding="utf-8") if staging_path.exists() else ""
    file_name = input_path.name
    file_type = input_path.suffix.lower().lstrip(".")

    status = ingestion_log.get("status")
    parsing_status = "ready" if status == "success" else status
    if not extracted_text.strip() and parsing_status == "ready":
        parsing_status = "partial_success"

    return {
        "document_id": _safe_document_id(file_name),
        "source_id": ingestion_log["run_id"],
        "file_name": file_name,
        "file_type": file_type,
        "file_size": input_path.stat().st_size if input_path.exists() else None,
        "text_length": metadata.get("total_characters") or len(extracted_text),
        "num_pages": metadata.get("page_count") or metadata.get("total_pages", 0),
        "source_system": source_system,
        "extracted_text": extracted_text,
        "ingestion_run_id": ingestion_log["run_id"],
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


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    payload = build_pdf_prediction_payload()
    print(json.dumps(payload, indent=4, ensure_ascii=False))
