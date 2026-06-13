from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import fitz

try:
    from .common import (
        PROJECT_ROOT,
        base_log,
        ensure_parent,
        relative_path,
        utc_now,
        write_json,
    )
except ImportError:
    from common import (
        PROJECT_ROOT,
        base_log,
        ensure_parent,
        relative_path,
        utc_now,
        write_json,
)


def safe_document_id(file_name: str) -> str:
    stem = Path(file_name).stem.lower()
    safe_stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return f"doc_{safe_stem or 'unknown'}"


def write_jsonl(records: list[dict], path: Path) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_pdf_ingestion(
    input_path: Path = PROJECT_ROOT / "data/sample_inputs/big-data-engineer2 - Template 16 .pdf",
    raw_output_path: Path = PROJECT_ROOT / "data/raw/pdf/sample_pdf_raw.pdf",
    staging_output_path: Path = PROJECT_ROOT / "data/staging/pdf/sample_pdf_text.txt",
    document_pages_output_path: Path = PROJECT_ROOT / "data/staging/pdf/document_pages.jsonl",
    metadata_output_path: Path = PROJECT_ROOT / "logs/pdf_metadata.json",
    log_output_path: Path = PROJECT_ROOT / "logs/pdf_ingestion_log.json",
) -> dict:
    start_time = utc_now()
    try:
        ensure_parent(raw_output_path)
        shutil.copy2(input_path, raw_output_path)

        document = fitz.open(input_path)
        document_id = safe_document_id(input_path.name)
        page_texts = []
        page_records = []
        empty_pages = []
        for page_index, page in enumerate(document, start=1):
            text = page.get_text().strip()
            if not text:
                empty_pages.append(page_index)
            page_texts.append(f"--- Page {page_index} ---\n{text}")
            page_records.append(
                {
                    "document_id": document_id,
                    "file_name": input_path.name,
                    "page_number": page_index,
                    "text": text,
                    "character_count": len(text),
                    "is_empty": not bool(text),
                    "source": input_path.name,
                    "raw_output_path": relative_path(raw_output_path),
                    "staging_text_path": relative_path(staging_output_path),
                }
            )

        extracted_text = "\n\n".join(page_texts)
        ensure_parent(staging_output_path)
        staging_output_path.write_text(extracted_text, encoding="utf-8")
        write_jsonl(page_records, document_pages_output_path)

        metadata = {
            "document_id": document_id,
            "source_name": "sample_pdf",
            "source_type": "pdf",
            "input_path": relative_path(input_path),
            "raw_output_path": relative_path(raw_output_path),
            "staging_output_path": relative_path(staging_output_path),
            "document_pages_output_path": relative_path(document_pages_output_path),
            "page_count": len(document),
            "extracted_character_count": len(extracted_text),
            "empty_pages": empty_pages,
            "owner": "Nguyen Minh Duy",
        }
        write_json(metadata, metadata_output_path)

        log = base_log(
            source_name="sample_pdf",
            source_type="pdf",
            input_path_or_url=relative_path(input_path),
            start_time=start_time,
            end_time=utc_now(),
            status="success",
            records_read=len(document),
            records_valid=len(document) - len(empty_pages),
            records_invalid=len(empty_pages),
            error_message=None,
            raw_output_path=raw_output_path,
            staging_output_path=staging_output_path,
            clean_output_path=None,
            extra={
                "page_count": len(document),
                "extracted_character_count": len(extracted_text),
                "empty_pages": empty_pages,
                "document_id": document_id,
                "document_pages_output_path": relative_path(document_pages_output_path),
                "metadata_output_path": relative_path(metadata_output_path),
            },
        )
    except Exception as exc:
        log = base_log(
            source_name="sample_pdf",
            source_type="pdf",
            input_path_or_url=relative_path(input_path),
            start_time=start_time,
            end_time=utc_now(),
            status="failed",
            records_read=0,
            records_valid=0,
            records_invalid=0,
            error_message=str(exc),
            raw_output_path=None,
            staging_output_path=None,
            clean_output_path=None,
        )

    write_json(log, log_output_path)
    return log


if __name__ == "__main__":
    print(run_pdf_ingestion())
