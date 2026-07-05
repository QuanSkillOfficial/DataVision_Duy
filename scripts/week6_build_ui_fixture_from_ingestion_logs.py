from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_LOG_DIR = PROJECT_ROOT / "logs/runs"
OUTPUT_PATH = PROJECT_ROOT / "logs/ui_fixtures/duy_ingestion_dashboard_fixture.json"
PHI_HUNG_OUTPUT_PATH = PROJECT_ROOT / "outputs/ui_fixtures/duy_latest_ingestion_summary.json"
DATA_QUALITY_OUTPUT_PATH = PROJECT_ROOT / "outputs/ui_fixtures/duy_data_quality_summary.json"
PDF_DOCUMENT_OUTPUT_PATH = PROJECT_ROOT / "outputs/ui_fixtures/duy_pdf_document_summary.json"
PREDICTION_PAYLOAD_PATH = PROJECT_ROOT / "logs/prediction_payloads/duy_pdf_prediction_payload.json"
RAG_HANDOFF_MANIFEST_PATH = PROJECT_ROOT / "outputs/rag_handoff/rag_handoff_manifest.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _read_json(path)


def _summarize_prediction_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    summary = dict(payload)
    extracted_text = summary.pop("extracted_text", "") or ""
    summary["extracted_text_length"] = payload.get("text_length") or len(extracted_text)
    summary["extracted_text_preview"] = extracted_text[:500]
    summary["full_payload_path"] = PREDICTION_PAYLOAD_PATH.relative_to(PROJECT_ROOT).as_posix()
    return summary


def build_ui_fixture() -> dict[str, Any]:
    runs = [_read_json(path) for path in sorted(RUN_LOG_DIR.glob("*.json"))]
    if not runs:
        raise FileNotFoundError("No run logs found under logs/runs")

    scores = [run.get("data_quality_score", 0.0) or 0.0 for run in runs]
    fixture_runs = []
    for run in runs:
        manifest = run.get("file_manifest") or {}
        pdf_metadata = run.get("pdf_metadata") or {}
        fixture_runs.append(
            {
                "run_id": run["run_id"],
                "ingestion_run_id": run["run_id"],
                "source_id": None,
                "source_name": run["source_name"],
                "source_type": run["source_type"],
                "status": run["status"],
                "records_read": run["records_read"],
                "records_valid": run["records_valid"],
                "records_invalid": run["records_invalid"],
                "data_quality_score": run.get("data_quality_score"),
                "document_external_id": run.get("document_id") or manifest.get("document_id"),
                "document_db_id": None,
                "document_pages_jsonl_path": run.get("document_pages_output_path"),
                "raw_output_path": run.get("raw_output_path"),
                "staging_output_path": run.get("staging_output_path"),
                "staging_text_output_path": run.get("staging_text_output_path"),
                "clean_output_path": run.get("clean_output_path"),
                "file_hash_sha256": manifest.get("file_hash_sha256"),
                "file_size_bytes": manifest.get("file_size_bytes"),
                "page_count": run.get("page_count") or pdf_metadata.get("page_count"),
                "empty_page_count": run.get("empty_page_count") or pdf_metadata.get("empty_page_count"),
                "total_characters": run.get("total_characters") or pdf_metadata.get("total_characters"),
                "start_time": run.get("start_time"),
                "end_time": run.get("end_time"),
                "error_message": run.get("error_message"),
            }
        )

    latest_run = max(fixture_runs, key=lambda run: run.get("end_time") or "")
    prediction_payload = _optional_json(PREDICTION_PAYLOAD_PATH)
    prediction_context = _summarize_prediction_payload(prediction_payload)
    rag_handoff = _optional_json(RAG_HANDOFF_MANIFEST_PATH)
    status_counts: dict[str, int] = {}
    for run in fixture_runs:
        status = run.get("status") or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "summary": {
            "total_sources": len({run["source_name"] for run in runs}),
            "total_runs": len(runs),
            "total_records_read": sum(run["records_read"] for run in runs),
            "total_records_valid": sum(run["records_valid"] for run in runs),
            "total_records_invalid": sum(run["records_invalid"] for run in runs),
            "latest_status": latest_run["status"],
            "average_data_quality_score": round(mean(scores), 2),
            "status_counts": status_counts,
            "rag_ready_documents": 1 if rag_handoff and rag_handoff.get("parsing_status") == "ready" else 0,
            "prediction_payload_available": prediction_context is not None,
        },
        "latest_ingestion_run": latest_run,
        "id_mapping": {
            "source_id": "Database source primary key from Phat. Null before DB insert.",
            "source_name": "Stable Duy source name from config.",
            "document_external_id": "Duy document key. Maps to documents.document_external_id.",
            "document_db_id": "Database document primary key from Phat. Null before DB insert.",
            "ingestion_run_id": "Duy run UUID. Maps to ingestion_logs.run_id.",
        },
        "prediction_context": prediction_context,
        "rag_handoff": rag_handoff,
        "runs": fixture_runs,
    }


def build_data_quality_summary(fixture: dict[str, Any]) -> dict[str, Any]:
    runs = fixture["runs"]
    return {
        "summary": fixture["summary"],
        "sources": [
            {
                "run_id": run["run_id"],
                "source_name": run["source_name"],
                "source_type": run["source_type"],
                "status": run["status"],
                "records_read": run["records_read"],
                "records_valid": run["records_valid"],
                "records_invalid": run["records_invalid"],
                "data_quality_score": run["data_quality_score"],
                "file_hash_sha256": run.get("file_hash_sha256"),
            }
            for run in runs
        ],
    }


def build_pdf_document_summary(fixture: dict[str, Any]) -> dict[str, Any]:
    pdf_runs = [run for run in fixture["runs"] if run.get("source_type") == "pdf"]
    latest_pdf = max(pdf_runs, key=lambda run: run.get("end_time") or "") if pdf_runs else {}
    return {
        "document_external_id": latest_pdf.get("document_external_id"),
        "document_db_id": latest_pdf.get("document_db_id"),
        "source_name": latest_pdf.get("source_name"),
        "ingestion_run_id": latest_pdf.get("ingestion_run_id"),
        "file_name": fixture.get("rag_handoff", {}).get("file_name"),
        "file_hash_sha256": latest_pdf.get("file_hash_sha256"),
        "page_count": latest_pdf.get("page_count"),
        "valid_pages": latest_pdf.get("records_valid"),
        "empty_page_count": latest_pdf.get("empty_page_count"),
        "total_characters": latest_pdf.get("total_characters"),
        "raw_output_path": latest_pdf.get("raw_output_path"),
        "staging_output_path": latest_pdf.get("staging_output_path"),
        "staging_text_output_path": latest_pdf.get("staging_text_output_path"),
        "clean_output_path": latest_pdf.get("clean_output_path"),
        "document_pages_jsonl_path": latest_pdf.get("document_pages_jsonl_path"),
        "rag_handoff_document_pages_path": fixture.get("rag_handoff", {}).get("document_pages_path"),
    }


def main() -> int:
    fixture = build_ui_fixture()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(fixture, indent=2, ensure_ascii=False), encoding="utf-8")
    PHI_HUNG_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PHI_HUNG_OUTPUT_PATH.write_text(json.dumps(fixture, indent=2, ensure_ascii=False), encoding="utf-8")
    DATA_QUALITY_OUTPUT_PATH.write_text(
        json.dumps(build_data_quality_summary(fixture), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    PDF_DOCUMENT_OUTPUT_PATH.write_text(
        json.dumps(build_pdf_document_summary(fixture), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote UI fixture: {OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Wrote Phi/Hung UI fixture: {PHI_HUNG_OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Wrote data quality fixture: {DATA_QUALITY_OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Wrote PDF document fixture: {PDF_DOCUMENT_OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Runs included: {fixture['summary']['total_runs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
