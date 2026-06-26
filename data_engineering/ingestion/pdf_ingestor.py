from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber

from data_engineering.utils.file_utils import copy_file, create_file_manifest
from data_engineering.utils.log_utils import (
    build_ingestion_log,
    new_run_id,
    persist_run_log,
    utc_now,
    write_json,
)
from data_engineering.utils.path_utils import ensure_parent, relative_path, resolve_project_path
from data_engineering.validation.data_quality import calculate_data_quality_score


def safe_document_id(file_name: str) -> str:
    stem = Path(file_name).stem.lower()
    safe_stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return f"doc_{safe_stem or 'unknown'}"


def clean_extracted_text(text: str | None) -> str:
    if text is None:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def count_words(text: str) -> int:
    return len(text.split()) if text else 0


def write_jsonl(records: list[dict[str, Any]], path: str | Path) -> None:
    target = ensure_parent(path)
    with target.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_pdf_ingestion(source_config: dict[str, Any]) -> dict[str, Any]:
    run_id = source_config.get("run_id") or new_run_id()
    start_time = utc_now()
    source_name = source_config["source_name"]
    input_path = resolve_project_path(source_config["input_path"])
    raw_output_path = resolve_project_path(source_config["raw_output_path"])
    staging_text_output_path = resolve_project_path(source_config["staging_text_output_path"])
    staging_output_path = resolve_project_path(source_config["staging_output_path"])
    clean_output_path = resolve_project_path(source_config["clean_output_path"])
    document_pages_output_path = resolve_project_path(source_config["document_pages_output_path"])
    metadata_output_path = resolve_project_path(source_config["metadata_output_path"])

    try:
        if input_path is None or not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {source_config['input_path']}")

        copy_file(input_path, raw_output_path)
        document_id = source_config.get("document_id") or safe_document_id(input_path.name)
        page_records: list[dict[str, Any]] = []
        document_pages: list[dict[str, Any]] = []

        with pdfplumber.open(input_path) as pdf:
            total_pages = len(pdf.pages)
            for page_index, page in enumerate(pdf.pages, start=1):
                raw_text = page.extract_text() or ""
                clean_text = clean_extracted_text(raw_text)
                is_empty = not bool(clean_text)
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
                        "staging_text_path": relative_path(staging_text_output_path),
                    }
                )

        df_pages = pd.DataFrame(page_records)
        records_read = len(df_pages)
        empty_page_count = int(df_pages["is_empty_page"].sum()) if not df_pages.empty else 0
        total_characters = int(df_pages["char_count"].sum()) if not df_pages.empty else 0
        total_words = int(df_pages["word_count"].sum()) if not df_pages.empty else 0
        page_texts = [f"--- Page {record['page_number']} ---\n{record['clean_text']}" for record in page_records]

        ensure_parent(staging_text_output_path)
        staging_text_output_path.write_text("\n\n".join(page_texts), encoding="utf-8")
        write_jsonl(document_pages, document_pages_output_path)

        staging_output_path.parent.mkdir(parents=True, exist_ok=True)
        df_pages.to_csv(staging_output_path, index=False, encoding="utf-8")
        df_clean = df_pages[~df_pages["is_empty_page"]].drop_duplicates(subset=["clean_text"]).copy()
        clean_output_path.parent.mkdir(parents=True, exist_ok=True)
        df_clean.to_csv(clean_output_path, index=False, encoding="utf-8")

        records_valid = len(df_clean)
        records_invalid = records_read - records_valid
        empty_pages = [record["page_number"] for record in page_records if record["is_empty_page"]]
        data_quality_score = calculate_data_quality_score(
            records_read=records_read,
            records_invalid=records_invalid,
            duplicate_count=records_read - len(df_pages.drop_duplicates(subset=["clean_text"])),
            optional_missing_count=empty_page_count,
        )
        metadata = {
            "document_id": document_id,
            "source_name": source_name,
            "source_type": "pdf",
            "file_name": input_path.name,
            "file_size_bytes": input_path.stat().st_size,
            "file_size_mb": round(input_path.stat().st_size / (1024 * 1024), 2),
            "input_path": relative_path(input_path),
            "raw_output_path": relative_path(raw_output_path),
            "staging_output_path": relative_path(staging_text_output_path),
            "staging_csv_output_path": relative_path(staging_output_path),
            "clean_output_path": relative_path(clean_output_path),
            "document_pages_output_path": relative_path(document_pages_output_path),
            "page_count": total_pages,
            "total_pages": total_pages,
            "pages_extracted": records_read,
            "empty_page_count": empty_page_count,
            "total_characters": total_characters,
            "total_words": total_words,
            "empty_pages": empty_pages,
            "owner": source_config.get("owner", "Nguyen Minh Duy"),
        }
        write_json(metadata, metadata_output_path)
        manifest = create_file_manifest(
            run_id=run_id,
            source_name=source_name,
            source_type="pdf",
            input_path=input_path,
            raw_output_path=raw_output_path,
            ingested_at=start_time,
            extra={"document_id": document_id},
        )
        log = build_ingestion_log(
            run_id=run_id,
            source_name=source_name,
            source_type="pdf",
            input_path_or_url=relative_path(input_path) or source_config["input_path"],
            start_time=start_time,
            end_time=utc_now(),
            status="success" if records_invalid == 0 else "partial_success",
            records_read=records_read,
            records_valid=records_valid,
            records_invalid=records_invalid,
            error_message=None,
            raw_output_path=raw_output_path,
            staging_output_path=staging_output_path,
            clean_output_path=clean_output_path,
            owner=source_config.get("owner", "Nguyen Minh Duy"),
            extra={
                "page_count": total_pages,
                "empty_page_count": empty_page_count,
                "total_characters": total_characters,
                "total_words": total_words,
                "empty_pages": empty_pages,
                "document_id": document_id,
                "staging_text_output_path": relative_path(staging_text_output_path),
                "document_pages_output_path": relative_path(document_pages_output_path),
                "metadata_output_path": relative_path(metadata_output_path),
                "pdf_metadata": metadata,
                "data_quality_score": data_quality_score,
                "file_manifest": manifest,
            },
        )
    except Exception as exc:
        log = build_ingestion_log(
            run_id=run_id,
            source_name=source_name,
            source_type="pdf",
            input_path_or_url=source_config.get("input_path", ""),
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
            owner=source_config.get("owner", "Nguyen Minh Duy"),
            extra={"data_quality_score": 0.0},
        )

    persist_run_log(
        ingestion_log=log,
        latest_log_path=source_config.get("latest_log_path"),
        run_log_dir=source_config.get("run_log_dir", "logs/runs"),
        run_history_path=source_config.get("run_history_path", "logs/ingestion_runs.jsonl"),
    )
    manifest = log.get("file_manifest")
    if manifest:
        manifest_output_dir = source_config.get("manifest_output_dir", "logs/manifests")
        write_json(manifest, f"{manifest_output_dir}/{run_id}_manifest.json")
    return log
