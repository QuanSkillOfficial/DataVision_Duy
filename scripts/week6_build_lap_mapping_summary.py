"""Build a Week 6 Duy-to-Lap RAG handoff summary.

The script reads Duy's RAG handoff package and, when available, Lap's
Week 6 mapping/evaluation files plus Phat's DB-shaped mapping summary.
It writes one machine-readable JSON file for team handoff.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAP_ROOT = PROJECT_ROOT.parent / "DataVision_Lap"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def count_jsonl(path: Path) -> dict[str, Any]:
    stats = {
        "path": path.as_posix(),
        "exists": path.exists(),
        "pages_loaded": 0,
        "non_empty_pages": 0,
        "empty_pages": 0,
        "total_characters": 0,
        "first_record_keys": [],
    }
    if not path.exists():
        return stats

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if line_number == 1:
                stats["first_record_keys"] = sorted(record.keys())
            stats["pages_loaded"] += 1
            if record.get("is_empty"):
                stats["empty_pages"] += 1
            else:
                stats["non_empty_pages"] += 1
            stats["total_characters"] += int(record.get("character_count") or len(record.get("text") or ""))
    return stats


def read_lap_eval(eval_csv: Path) -> dict[str, Any]:
    if not eval_csv.exists():
        return {"exists": False}

    rows = list(csv.DictReader(eval_csv.read_text(encoding="utf-8").splitlines()))
    if not rows:
        return {"exists": True, "queries": 0}

    hit_at_1 = sum(int(row.get("hit_at_1") or 0) for row in rows) / len(rows)
    hit_at_3 = sum(int(row.get("hit_at_3") or 0) for row in rows) / len(rows)
    hit_at_5 = sum(int(row.get("hit_at_5") or 0) for row in rows) / len(rows)
    avg_similarity = sum(float(row.get("similarity_score") or 0) for row in rows) / len(rows)
    return {
        "exists": True,
        "queries": len(rows),
        "hit_at_1": round(hit_at_1, 4),
        "hit_at_3": round(hit_at_3, 4),
        "hit_at_5": round(hit_at_5, 4),
        "average_similarity": round(avg_similarity, 4),
        "sample_retrieved_chunk_id": rows[0].get("retrieved_chunk_id"),
        "evaluation_type": "fixture_or_recorded_results",
    }


def read_notebook_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cells = notebook.get("cells", [])
    output_count = sum(len(cell.get("outputs", [])) for cell in cells)
    executed_cells = sum(1 for cell in cells if cell.get("execution_count"))
    return {
        "exists": True,
        "cell_count": len(cells),
        "executed_cells": executed_cells,
        "output_count": output_count,
        "appears_executed": executed_cells > 0 and output_count > 0,
    }


def file_status(path: Path) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "exists": path.exists(),
    }


def main() -> None:
    rag_dir = PROJECT_ROOT / "outputs" / "rag_handoff"
    phat_summary = read_json(PROJECT_ROOT / "outputs" / "phat_handoff" / "phat_week6_mapping_summary.json", {})
    pdf_metadata = read_json(rag_dir / "pdf_metadata.json", {})
    rag_manifest = read_json(rag_dir / "rag_handoff_manifest.json", {})

    lap_eval_csv = LAP_ROOT / "ai" / "rag" / "evaluation" / "week6_retrieval_test_cases_dataflow.csv"
    lap_eval_md = LAP_ROOT / "ai" / "rag" / "evaluation" / "week6_retrieval_eval_results.md"
    lap_response_fixture = LAP_ROOT / "outputs" / "ui_fixtures" / "lap_rag_response_real.json"
    lap_notebook = LAP_ROOT / "ai" / "rag" / "notebooks" / "week6_real_pgvector_rag_demo.ipynb"
    lap_screenshot = LAP_ROOT / "screenshots" / "week6_pgvector_retrieval_result.png"
    lap_duy_result = LAP_ROOT / "ai" / "week6_duy_dataflow_ingestion_result.md"
    lap_week6_summary = LAP_ROOT / "ai" / "WEEK_6_SUMMARY.md"
    lap_schema_mapping = LAP_ROOT / "ai" / "week6_rag_to_schema_v4_mapping.md"
    lap_loader_script = LAP_ROOT / "ai" / "rag" / "load_document_pages_to_pgvector.py"
    lap_rag_service = LAP_ROOT / "ai" / "rag" / "rag_service.py"

    document_external_id = (
        pdf_metadata.get("document_id")
        or rag_manifest.get("document_external_id")
        or "doc_dataflow_technical_report"
    )
    document_id_map = phat_summary.get("document_id_map", {}).get(document_external_id, {})

    summary = {
        "handoff_owner": "Nguyen Minh Duy",
        "consumer": "Lap - RAG and Embeddings Owner",
        "purpose": "Map Duy PDF extraction outputs to Lap chunking, pgvector retrieval, citations, and UI response needs.",
        "duy_outputs_for_lap": {
            "document_pages_jsonl": "outputs/rag_handoff/document_pages.jsonl",
            "pdf_metadata": "outputs/rag_handoff/pdf_metadata.json",
            "rag_handoff_manifest": "outputs/rag_handoff/rag_handoff_manifest.json",
            "rag_handoff_summary": "outputs/rag_handoff/rag_handoff_summary.md",
        },
        "lap_repo_files_reviewed": {
            "schema_v4_mapping": file_status(lap_schema_mapping),
            "loader_script": file_status(lap_loader_script),
            "rag_service": file_status(lap_rag_service),
            "week6_summary": file_status(lap_week6_summary),
            "retrieval_eval_csv": file_status(lap_eval_csv),
            "retrieval_eval_markdown": file_status(lap_eval_md),
            "notebook": file_status(lap_notebook),
            "ui_fixture": file_status(lap_response_fixture),
            "screenshot": file_status(lap_screenshot),
            "duy_dataflow_ingestion_result": file_status(lap_duy_result),
        },
        "document": {
            "document_external_id": document_external_id,
            "document_db_id_from_phat_if_available": document_id_map.get("document_db_id"),
            "source_name": pdf_metadata.get("source_name"),
            "file_name": pdf_metadata.get("file_name"),
            "page_count": pdf_metadata.get("page_count") or pdf_metadata.get("total_pages"),
            "total_characters": pdf_metadata.get("total_characters"),
            "parsing_status": "ready" if pdf_metadata.get("pages_extracted") else "unknown",
        },
        "document_pages_stats": count_jsonl(rag_dir / "document_pages.jsonl"),
        "lap_expected_loader_behavior": {
            "loader": "ai/rag/document_loader.py::load_document_pages_jsonl",
            "accepted_text_fields": ["text", "page_text", "page_content"],
            "empty_page_rule": "Skip records where is_empty=true",
            "chunk_size": 512,
            "overlap": 50,
            "chunk_id_pattern": f"{document_external_id}_page_<page_number>_chunk_<000>",
        },
        "pgvector_mapping": {
            "document_external_id": "documents.document_external_id",
            "document_db_id": "documents.id",
            "chunk_id": "document_chunks.chunk_id",
            "chunk_text": "document_chunks.chunk_text",
            "page_number": "document_chunks.page_number",
            "metadata": "document_chunks.chunk_metadata",
            "embedding": "document_chunks.embedding vector(384)",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": 384,
            "phat_document_chunks_count_if_available": phat_summary.get("counts", {}).get("document_chunks"),
            "phat_document_external_id_resolved": bool(document_id_map),
        },
        "lap_evaluation_fixture": read_lap_eval(lap_eval_csv),
        "lap_notebook_status": read_notebook_status(lap_notebook),
        "lap_response_fixture_status": {
            "expected_path": "outputs/ui_fixtures/lap_rag_response_real.json",
            "found_in_lap_repo": lap_response_fixture.exists(),
        },
        "lap_execution_status": {
            "code_ready_for_pgvector": lap_loader_script.exists() and lap_schema_mapping.exists(),
            "live_pgvector_notebook_executed": read_notebook_status(lap_notebook).get("appears_executed", False),
            "live_ui_fixture_available": lap_response_fixture.exists(),
            "live_screenshot_available": lap_screenshot.exists(),
            "duy_ingestion_result_doc_available": lap_duy_result.exists(),
            "summary_note": "Lap repo has schema mapping and loader code. Live pgvector execution proof/UI fixture/screenshot are still pending if files are absent or notebook has no outputs.",
        },
        "status_alignment_notes": {
            "duy_rag_input_status": "ready",
            "lap_retrieval_status_expected_by_ui": ["retrieval_only", "answered", "no_answer_found", "error"],
            "lap_service_additional_statuses_seen": ["no_context", "no_answer", "llm_error"],
            "recommendation": "Lap and Phi/Hung should align no-answer status naming before backend integration.",
        },
        "what_lap_should_return_to_duy": [
            "Page/chunk ingestion stats with no TBD values",
            "Number of embeddings generated and vectors inserted",
            "Top-k retrieval result with chunk_id, page_number, similarity_score",
            "Citation-ready response fixture for Phi/Hung",
            "Any metadata change request for Duy's future PDF output",
            "Confirmation whether live pgvector insertion used Phat documents.id=1",
            "RAG query log insert proof for Phat rag_query_logs",
        ],
    }

    output_dir = PROJECT_ROOT / "outputs" / "lap_handoff"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "lap_week6_mapping_summary.json"
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote Lap handoff mapping summary: {output_path}")


if __name__ == "__main__":
    main()
