from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCUMENT_PAGES = PROJECT_ROOT / "week2/data/staging/pdf/document_pages.jsonl"
DEFAULT_PDF_METADATA = PROJECT_ROOT / "week2/logs/pdf_metadata.json"
DEFAULT_PDF_LOG = PROJECT_ROOT / "week2/logs/pdf_ingestion_log.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs/rag_handoff"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def build_rag_handoff_package(
    *,
    document_pages_path: Path = DEFAULT_DOCUMENT_PAGES,
    pdf_metadata_path: Path = DEFAULT_PDF_METADATA,
    pdf_log_path: Path = DEFAULT_PDF_LOG,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    if not document_pages_path.exists():
        raise FileNotFoundError(f"Missing document_pages.jsonl: {document_pages_path}")
    if not pdf_metadata_path.exists():
        raise FileNotFoundError(f"Missing pdf metadata: {pdf_metadata_path}")

    pages = _read_jsonl(document_pages_path)
    metadata = _read_json(pdf_metadata_path)
    log = _read_json(pdf_log_path) if pdf_log_path.exists() else {}

    output_dir.mkdir(parents=True, exist_ok=True)
    output_document_pages = output_dir / "document_pages.jsonl"
    output_metadata = output_dir / "pdf_metadata.json"
    output_summary = output_dir / "rag_handoff_summary.md"
    output_manifest = output_dir / "rag_handoff_manifest.json"

    shutil.copyfile(document_pages_path, output_document_pages)
    shutil.copyfile(pdf_metadata_path, output_metadata)

    total_pages = len(pages)
    empty_pages = [page for page in pages if page.get("is_empty")]
    non_empty_pages = total_pages - len(empty_pages)
    total_characters = sum(int(page.get("character_count") or len(page.get("text", ""))) for page in pages)
    document_external_ids = sorted({page.get("document_id") for page in pages if page.get("document_id")})
    file_names = sorted({page.get("file_name") for page in pages if page.get("file_name")})

    summary = {
        "package_owner": "Nguyen Minh Duy",
        "consumer": "Lap - RAG and Embeddings Owner",
        "document_external_id": metadata.get("document_id") or (document_external_ids[0] if document_external_ids else None),
        "source_name": metadata.get("source_name") or log.get("source_name"),
        "source_type": "pdf",
        "file_name": metadata.get("file_name") or (file_names[0] if file_names else None),
        "page_count": total_pages,
        "non_empty_pages": non_empty_pages,
        "empty_pages": len(empty_pages),
        "empty_page_numbers": [page.get("page_number") for page in empty_pages],
        "total_characters": total_characters,
        "ingestion_run_id": log.get("run_id"),
        "parsing_status": "ready" if non_empty_pages == total_pages and total_pages > 0 else "partial_success",
        "document_pages_path": _relative(output_document_pages),
        "pdf_metadata_path": _relative(output_metadata),
        "source_document_pages_path": _relative(document_pages_path),
        "source_pdf_metadata_path": _relative(pdf_metadata_path),
    }

    summary_md = f"""# Week 6 RAG Handoff Summary

Owner: Nguyen Minh Duy  
Consumer: Lap - RAG and Embeddings Owner  
Purpose: Provide Duy's real DataFlow PDF extraction output for chunking, embedding, pgvector insertion, retrieval evaluation, and citation generation.

## Files

| File | Purpose |
| --- | --- |
| `{summary["document_pages_path"]}` | Page-level text records for Lap chunking |
| `{summary["pdf_metadata_path"]}` | PDF metadata and extraction statistics |
| `{_relative(output_manifest)}` | Machine-readable handoff summary |

## Real Extraction Statistics

| Metric | Value |
| --- | --- |
| `document_external_id` | `{summary["document_external_id"]}` |
| `source_name` | `{summary["source_name"]}` |
| `file_name` | `{summary["file_name"]}` |
| `ingestion_run_id` | `{summary["ingestion_run_id"]}` |
| `page_count` | `{summary["page_count"]}` |
| `non_empty_pages` | `{summary["non_empty_pages"]}` |
| `empty_pages` | `{summary["empty_pages"]}` |
| `total_characters` | `{summary["total_characters"]}` |
| `parsing_status` | `{summary["parsing_status"]}` |

## ID Mapping Rule

Lap should treat `document_id` in `document_pages.jsonl` as Duy's external document key.

```text
document_pages.jsonl.document_id
  -> documents.document_external_id
  -> documents.id
  -> document_chunks.document_id
```

Do not insert the string `document_id` directly into `document_chunks.document_id`; Phat's table expects the internal integer `documents.id`.

## Page Record Contract

Each line in `document_pages.jsonl` contains:

```json
{{
  "document_id": "doc_dataflow_technical_report",
  "file_name": "DataFlow_Technical_Report.pdf",
  "page_number": 1,
  "text": "...",
  "character_count": 2953,
  "is_empty": false,
  "source": "DataFlow_Technical_Report.pdf"
}}
```
"""
    output_summary.write_text(summary_md, encoding="utf-8")
    _write_json(output_manifest, summary)
    return summary


def main() -> int:
    summary = build_rag_handoff_package()
    print(f"Wrote RAG handoff package: {_relative(DEFAULT_OUTPUT_DIR)}")
    print(f"Pages: {summary['page_count']}")
    print(f"Non-empty pages: {summary['non_empty_pages']}")
    print(f"Total characters: {summary['total_characters']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
