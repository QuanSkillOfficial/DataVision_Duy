from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pandas as pd
import pdfplumber

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


def clean_extracted_text(text: str | None) -> str:
    if text is None:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def count_words(text: str) -> int:
    if not text:
        return 0
    return len(text.split())


def run_pdf_ingestion(
    input_path: Path = PROJECT_ROOT / "data/sample_inputs/DataFlow_Technical_Report.pdf",
    raw_output_path: Path = PROJECT_ROOT / "data/raw/pdf/dataflow_technical_report_raw.pdf",
    staging_output_path: Path = PROJECT_ROOT / "data/staging/pdf/dataflow_pdf_text.txt",
    staging_csv_output_path: Path = PROJECT_ROOT / "data/staging/pdf/dataflow_pdf_pages_staging.csv",
    clean_output_path: Path = PROJECT_ROOT / "data/clean/pdf/dataflow_pdf_pages_clean.csv",
    document_pages_output_path: Path = PROJECT_ROOT / "data/staging/pdf/document_pages.jsonl",
    metadata_output_path: Path = PROJECT_ROOT / "logs/pdf_metadata.json",
    log_output_path: Path = PROJECT_ROOT / "logs/pdf_ingestion_log.json",
) -> dict:
    start_time = utc_now()
    try:
        ensure_parent(raw_output_path)
        shutil.copy2(input_path, raw_output_path)

        document_id = safe_document_id(input_path.name)
        page_records = []
        document_pages = []
        with pdfplumber.open(input_path) as pdf:
            total_pages = len(pdf.pages)
            for page_index, page in enumerate(pdf.pages, start=1):
                raw_text = page.extract_text() or ""
                clean_text = clean_extracted_text(raw_text)
                is_empty = len(clean_text) == 0
                page_records.append(
                    {
                        "page_number": page_index,
                        "raw_text": raw_text,
                        "clean_text": clean_text,
                        "char_count": len(clean_text),
                        "word_count": count_words(clean_text),
                        "is_empty_page": is_empty,
                    }
                )
                document_pages.append(
                    {
                        "document_id": document_id,
                        "file_name": input_path.name,
                        "page_number": page_index,
                        "text": clean_text,
                        "character_count": len(clean_text),
                        "is_empty": is_empty,
                        "source": input_path.name,
                        "raw_output_path": relative_path(raw_output_path),
                        "staging_text_path": relative_path(staging_output_path),
                    }
                )

        df_pages = pd.DataFrame(page_records)
        records_read = len(df_pages)
        empty_page_count = int(df_pages["is_empty_page"].sum()) if not df_pages.empty else 0
        total_characters = int(df_pages["char_count"].sum()) if not df_pages.empty else 0
        total_words = int(df_pages["word_count"].sum()) if not df_pages.empty else 0

        page_texts = []
        for record in page_records:
            page_texts.append(f"--- Page {record['page_number']} ---\n{record['clean_text']}")

        extracted_text = "\n\n".join(page_texts)
        ensure_parent(staging_output_path)
        staging_output_path.write_text(extracted_text, encoding="utf-8")
        write_jsonl(document_pages, document_pages_output_path)
        ensure_parent(staging_csv_output_path)
        df_pages.to_csv(staging_csv_output_path, index=False, encoding="utf-8")

        df_clean = df_pages[~df_pages["is_empty_page"]].copy()
        df_clean = df_clean.drop_duplicates(subset=["clean_text"])
        ensure_parent(clean_output_path)
        df_clean.to_csv(clean_output_path, index=False, encoding="utf-8")

        records_valid = len(df_clean)
        records_invalid = records_read - records_valid
        empty_pages = [record["page_number"] for record in page_records if record["is_empty_page"]]

        metadata = {
            "document_id": document_id,
            "source_name": "dataflow_technical_report_pdf",
            "source_type": "pdf",
            "file_name": input_path.name,
            "file_size_bytes": input_path.stat().st_size,
            "file_size_mb": round(input_path.stat().st_size / (1024 * 1024), 2),
            "input_path": relative_path(input_path),
            "raw_output_path": relative_path(raw_output_path),
            "staging_output_path": relative_path(staging_output_path),
            "staging_csv_output_path": relative_path(staging_csv_output_path),
            "clean_output_path": relative_path(clean_output_path),
            "document_pages_output_path": relative_path(document_pages_output_path),
            "page_count": total_pages,
            "total_pages": total_pages,
            "pages_extracted": records_read,
            "empty_page_count": empty_page_count,
            "extracted_character_count": len(extracted_text),
            "total_characters": total_characters,
            "total_words": total_words,
            "empty_pages": empty_pages,
            "owner": "Nguyen Minh Duy",
        }
        write_json(metadata, metadata_output_path)

        log = base_log(
            source_name="dataflow_technical_report_pdf",
            source_type="pdf",
            input_path_or_url=relative_path(input_path),
            start_time=start_time,
            end_time=utc_now(),
            status="success",
            records_read=records_read,
            records_valid=records_valid,
            records_invalid=records_invalid,
            error_message=None,
            raw_output_path=raw_output_path,
            staging_output_path=staging_csv_output_path,
            clean_output_path=clean_output_path,
            extra={
                "page_count": total_pages,
                "empty_page_count": empty_page_count,
                "extracted_character_count": len(extracted_text),
                "total_characters": total_characters,
                "total_words": total_words,
                "empty_pages": empty_pages,
                "document_id": document_id,
                "staging_text_output_path": relative_path(staging_output_path),
                "document_pages_output_path": relative_path(document_pages_output_path),
                "metadata_output_path": relative_path(metadata_output_path),
                "pdf_metadata": metadata,
            },
        )
    except Exception as exc:
        log = base_log(
            source_name="dataflow_technical_report_pdf",
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
