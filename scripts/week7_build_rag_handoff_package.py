from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.pipelines.handoff_context import (
    identity_for_document,
    identity_for_source,
    load_database_identity_map,
    load_latest_successful_runs,
)


DEFAULT_PAGES = PROJECT_ROOT / "outputs/rag_handoff/document_pages.jsonl"
DEFAULT_METADATA = PROJECT_ROOT / "outputs/rag_handoff/pdf_metadata.json"
OUTPUT_PAGES = PROJECT_ROOT / "outputs/rag_handoff/week7_document_pages_db_enriched.jsonl"
OUTPUT_MANIFEST = PROJECT_ROOT / "outputs/rag_handoff/week7_rag_handoff_manifest.json"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def build_week7_rag_handoff(
    *,
    pages_path: Path = DEFAULT_PAGES,
    metadata_path: Path = DEFAULT_METADATA,
    db_result_path: str | Path = "logs/db_load_results/duy_to_phat_db_load_result.json",
) -> dict[str, Any]:
    if not pages_path.exists() or not metadata_path.exists():
        raise FileNotFoundError("Run the Week 6 RAG handoff builder before the Week 7 enrichment step")

    pages = _read_jsonl(pages_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    pdf_run = next(run for run in load_latest_successful_runs() if run.get("source_type") == "pdf")
    identity = load_database_identity_map(db_result_path)
    document_external_id = metadata.get("document_external_id") or metadata.get("document_id")
    source_id = identity_for_source(identity, pdf_run["source_name"])
    document_db_id = identity_for_document(identity, document_external_id)
    ingestion_run_id = pdf_run["run_id"]

    enriched = []
    for page in pages:
        text = page.get("text") or ""
        enriched.append(
            {
                "document_id": document_external_id,
                "document_external_id": document_external_id,
                "document_db_id": document_db_id,
                "source_id": source_id,
                "ingestion_run_id": ingestion_run_id,
                "file_name": page.get("file_name") or metadata.get("file_name"),
                "page_number": int(page["page_number"]),
                "text": text,
                "char_count": int(page.get("char_count") or page.get("character_count") or len(text)),
                "character_count": int(page.get("character_count") or page.get("char_count") or len(text)),
                "word_count": int(page.get("word_count") or len(text.split())),
                "is_empty": bool(page.get("is_empty", not bool(text.strip()))),
                "source": page.get("source") or metadata.get("file_name"),
            }
        )

    OUTPUT_PAGES.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PAGES.open("w", encoding="utf-8") as file:
        for page in enriched:
            file.write(json.dumps(page, ensure_ascii=False) + "\n")

    file_manifest = pdf_run.get("file_manifest") or {}
    manifest = {
        "schema_version": "week7_rag_handoff_v1",
        "status": "ready" if enriched and all(not page["is_empty"] for page in enriched) else "partial_success",
        "database_identity_status": identity.get("status"),
        "database_schema_version": identity.get("schema_version"),
        "database_identity_source": identity.get("result_path"),
        "current_ingestion_run_loaded": identity.get("current_duy_runs_loaded"),
        "source_id": source_id,
        "source_name": pdf_run["source_name"],
        "document_external_id": document_external_id,
        "document_db_id": document_db_id,
        "ingestion_run_id": ingestion_run_id,
        "file_name": metadata.get("file_name"),
        "file_hash_sha256": file_manifest.get("file_hash_sha256"),
        "page_count": len(enriched),
        "non_empty_pages": sum(not page["is_empty"] for page in enriched),
        "empty_pages": sum(page["is_empty"] for page in enriched),
        "total_characters": sum(page["char_count"] for page in enriched),
        "total_words": sum(page["word_count"] for page in enriched),
        "document_pages_path": OUTPUT_PAGES.relative_to(PROJECT_ROOT).as_posix(),
        "pdf_metadata_path": DEFAULT_METADATA.relative_to(PROJECT_ROOT).as_posix(),
        "expected_chunk_id_format": "doc_dataflow_technical_report_page_{page_number}_chunk_{chunk_index:03d}",
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    metadata.update(
        {
            "document_external_id": document_external_id,
            "document_db_id": document_db_id,
            "source_id": source_id,
            "ingestion_run_id": ingestion_run_id,
            "file_hash_sha256": file_manifest.get("file_hash_sha256"),
            "database_identity_status": identity.get("status"),
            "database_schema_version": identity.get("schema_version"),
            "database_identity_source": identity.get("result_path"),
            "current_ingestion_run_loaded": identity.get(
                "current_duy_runs_loaded"
            ),
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Lap's DB-enriched Week 7 PDF handoff")
    parser.add_argument("--db-load-result", default="logs/db_load_results/duy_to_phat_db_load_result.json")
    args = parser.parse_args()
    manifest = build_week7_rag_handoff(db_result_path=args.db_load_result)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
