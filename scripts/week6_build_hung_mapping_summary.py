from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HUNG_ROOT = PROJECT_ROOT.parent / "DataVision_Hung"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "hung_handoff" / "hung_week6_mapping_summary.json"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def file_status(path: Path) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def compact_run(run: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "run_id",
        "ingestion_run_id",
        "source_id",
        "source_name",
        "source_type",
        "status",
        "records_read",
        "records_valid",
        "records_invalid",
        "data_quality_score",
        "document_external_id",
        "document_db_id",
        "file_hash_sha256",
        "raw_output_path",
        "staging_output_path",
        "clean_output_path",
        "document_pages_jsonl_path",
    ]
    return {key: run.get(key) for key in keys}


def main() -> None:
    duy_fixture = read_json(PROJECT_ROOT / "outputs" / "ui_fixtures" / "duy_latest_ingestion_summary.json", {})
    duy_quality = read_json(PROJECT_ROOT / "outputs" / "ui_fixtures" / "duy_data_quality_summary.json", {})
    duy_pdf = read_json(PROJECT_ROOT / "outputs" / "ui_fixtures" / "duy_pdf_document_summary.json", {})
    phat_summary = read_json(PROJECT_ROOT / "outputs" / "phat_handoff" / "phat_week6_mapping_summary.json", {})
    lap_summary = read_json(PROJECT_ROOT / "outputs" / "lap_handoff" / "lap_week6_mapping_summary.json", {})
    tuong_summary = read_json(PROJECT_ROOT / "outputs" / "tuong_handoff" / "tuong_week6_mapping_summary.json", {})

    hung_duy_fixture = read_json(HUNG_ROOT / "demo" / "fixtures" / "duy_latest_ingestion_summary.json", {})
    hung_phat_views = read_json(HUNG_ROOT / "demo" / "fixtures" / "phat_dashboard_views_sample.json", {})
    hung_prediction_batch = read_json(HUNG_ROOT / "demo" / "fixtures" / "tuong_prediction_batch_response.json", {})
    hung_rag_response = read_json(HUNG_ROOT / "demo" / "fixtures" / "lap_rag_response_real.json", {})
    hung_duy_fixture_path = HUNG_ROOT / "demo" / "fixtures" / "duy_latest_ingestion_summary.json"
    hung_phat_fixture_path = HUNG_ROOT / "demo" / "fixtures" / "phat_dashboard_views_sample.json"
    hung_tuong_batch_path = HUNG_ROOT / "demo" / "fixtures" / "tuong_prediction_batch_response.json"
    hung_lap_rag_path = HUNG_ROOT / "demo" / "fixtures" / "lap_rag_response_real.json"

    latest_run = duy_fixture.get("latest_ingestion_run", {})
    prediction_context = duy_fixture.get("prediction_context", {})
    rag_handoff = duy_fixture.get("rag_handoff", {})

    source_id_map = phat_summary.get("source_id_map", {})
    document_id_map = phat_summary.get("document_id_map", {})

    summary = {
        "owner": "Nguyen Minh Duy",
        "consumer": "Hung - Streamlit UI, Suggestions, Reports, Demo",
        "purpose": "Map Duy Week 6 ingestion outputs to Hung's UI fixtures, pages, and service-client contracts.",
        "duy_outputs_for_hung": {
            "latest_ingestion_summary": "outputs/ui_fixtures/duy_latest_ingestion_summary.json",
            "data_quality_summary": "outputs/ui_fixtures/duy_data_quality_summary.json",
            "pdf_document_summary": "outputs/ui_fixtures/duy_pdf_document_summary.json",
            "backward_compatible_dashboard_fixture": "logs/ui_fixtures/duy_ingestion_dashboard_fixture.json",
            "rag_handoff_package": "outputs/rag_handoff/",
            "prediction_payload_batch": "outputs/prediction_payloads/tuong_week6_prediction_payloads.json",
            "phat_mapping_summary": "outputs/phat_handoff/phat_week6_mapping_summary.json",
            "lap_mapping_summary": "outputs/lap_handoff/lap_week6_mapping_summary.json",
            "tuong_mapping_summary": "outputs/tuong_handoff/tuong_week6_mapping_summary.json",
        },
        "hung_repo_files_reviewed": {
            "duy_fixture_copy": file_status(hung_duy_fixture_path),
            "phat_dashboard_views_fixture": file_status(hung_phat_fixture_path),
            "tuong_prediction_batch_fixture": file_status(hung_tuong_batch_path),
            "lap_rag_response_fixture": file_status(hung_lap_rag_path),
            "mock_client": file_status(HUNG_ROOT / "demo" / "services" / "mock_client.py"),
            "service_client": file_status(HUNG_ROOT / "demo" / "services" / "service_client.py"),
            "dashboard_page": file_status(HUNG_ROOT / "demo" / "views" / "dashboard_page.py"),
            "suggestions_page": file_status(HUNG_ROOT / "demo" / "views" / "suggestions_page.py"),
            "reports_page": file_status(HUNG_ROOT / "demo" / "views" / "reports_page.py"),
            "prediction_page": file_status(HUNG_ROOT / "demo" / "views" / "prediction_page.py"),
            "chatbot_page": file_status(HUNG_ROOT / "demo" / "views" / "chatbot_page.py"),
            "dashboard_contract": file_status(HUNG_ROOT / "docs" / "ui_contracts" / "dashboard_ui_contract.md"),
            "week6_handoff": file_status(HUNG_ROOT / "docs" / "W6" / "week6_team_integration_handoff.md"),
        },
        "duy_fixture_summary": duy_fixture.get("summary", {}),
        "latest_ingestion_run": compact_run(latest_run),
        "prediction_context_summary": {
            "document_external_id": prediction_context.get("document_external_id"),
            "source_name": prediction_context.get("source_name"),
            "source_id": prediction_context.get("source_id"),
            "document_db_id": prediction_context.get("document_db_id"),
            "ingestion_run_id": prediction_context.get("ingestion_run_id"),
            "file_name": prediction_context.get("file_name"),
            "file_type": prediction_context.get("file_type"),
            "text_length": prediction_context.get("text_length"),
            "num_pages": prediction_context.get("num_pages"),
            "full_payload_path": prediction_context.get("full_payload_path"),
        },
        "confirmed_db_ids_from_phat": {
            "source_ids": source_id_map,
            "document_db_ids": document_id_map,
        },
        "page_to_data_mapping": {
            "Dashboard": {
                "service_function": "get_dashboard_metrics(), get_ingestion_status(), get_recent_activity()",
                "duy_fields": [
                    "summary.total_sources",
                    "summary.total_records_read",
                    "summary.total_records_valid",
                    "summary.total_records_invalid",
                    "summary.average_data_quality_score",
                    "latest_ingestion_run.status",
                    "latest_ingestion_run.file_hash_sha256",
                    "latest_ingestion_run.raw_output_path",
                    "latest_ingestion_run.staging_output_path",
                    "latest_ingestion_run.clean_output_path",
                    "runs[]",
                ],
            },
            "Suggestions": {
                "service_function": "generate_suggestions(context)",
                "duy_fields": [
                    "records_invalid",
                    "data_quality_score",
                    "status",
                    "document_pages_jsonl_path",
                    "prediction_context.parsing_status",
                    "rag_handoff.parsing_status",
                ],
            },
            "Reports": {
                "service_function": "generate_report(evidence_context)",
                "duy_fields": [
                    "source_name",
                    "source_type",
                    "run_id",
                    "ingestion_run_id",
                    "file_hash_sha256",
                    "raw_output_path",
                    "staging_output_path",
                    "clean_output_path",
                    "data_quality_score",
                    "records_read",
                    "records_valid",
                    "records_invalid",
                ],
            },
            "Prediction": {
                "service_function": "classify_document(payload), classify_documents(payloads)",
                "duy_fields": [
                    "prediction_context.document_external_id",
                    "prediction_context.document_db_id",
                    "prediction_context.source_id",
                    "prediction_context.source_name",
                    "prediction_context.ingestion_run_id",
                    "prediction_context.file_name",
                    "prediction_context.file_type",
                    "prediction_context.text_length",
                    "prediction_context.num_pages",
                    "prediction_context.full_payload_path",
                ],
            },
            "Chatbot/RAG": {
                "service_function": "ask_rag(question, document_id=None)",
                "duy_fields": [
                    "rag_handoff.document_external_id",
                    "rag_handoff.document_pages_path",
                    "rag_handoff.pdf_metadata_path",
                    "rag_handoff.page_count",
                    "rag_handoff.total_characters",
                ],
            },
        },
        "current_hung_fixture_status": {
            "hung_repo_exists": HUNG_ROOT.exists(),
            "duy_fixture_loaded_by_hung": bool(hung_duy_fixture),
            "phat_dashboard_fixture_loaded_by_hung": bool(hung_phat_views),
            "tuong_prediction_batch_fixture_loaded_by_hung": bool(hung_prediction_batch),
            "lap_rag_response_fixture_loaded_by_hung": bool(hung_rag_response),
            "hung_latest_source_id": hung_duy_fixture.get("latest_ingestion_run", {}).get("source_id"),
            "hung_latest_document_db_id": hung_duy_fixture.get("latest_ingestion_run", {}).get("document_db_id"),
            "hung_prediction_context_ingestion_run_id": hung_duy_fixture.get("prediction_context", {}).get("ingestion_run_id"),
            "duy_latest_ingestion_run_id": latest_run.get("ingestion_run_id"),
            "duy_prediction_context_ingestion_run_id": prediction_context.get("ingestion_run_id"),
            "hung_fixture_matches_duy_latest_run": (
                hung_duy_fixture.get("latest_ingestion_run", {}).get("ingestion_run_id")
                == latest_run.get("ingestion_run_id")
            ),
            "hung_fixture_matches_duy_prediction_context": (
                hung_duy_fixture.get("prediction_context", {}).get("ingestion_run_id")
                == prediction_context.get("ingestion_run_id")
            ),
        },
        "cross_team_counts_for_ui": {
            "total_sources_from_duy": duy_fixture.get("summary", {}).get("total_sources"),
            "total_records_read_from_duy": duy_fixture.get("summary", {}).get("total_records_read"),
            "average_data_quality_score_from_duy": duy_fixture.get("summary", {}).get("average_data_quality_score"),
            "document_pages_for_rag": rag_handoff.get("page_count"),
            "rag_chunks_from_lap_or_phat": (
                lap_summary.get("pgvector_mapping", {}).get("phat_document_chunks_count_if_available")
                or phat_summary.get("counts", {}).get("document_chunks")
            ),
            "prediction_payloads_for_tuong": tuong_summary.get("duy_payload_summary", {}).get("total_payloads"),
            "prediction_review_queue_rows": (
                phat_summary.get("prediction_log_status_counts", {}).get("needs_review", 0)
                + phat_summary.get("prediction_log_status_counts", {}).get("waiting_for_source", 0)
                + phat_summary.get("prediction_log_status_counts", {}).get("failed", 0)
            ),
        },
        "what_hung_should_return_to_duy": [
            "Confirm Dashboard renders Duy latest ingestion summary and run list.",
            "Confirm Suggestions can consume data_quality_score, records_invalid, prediction status, and RAG status.",
            "Confirm Reports evidence table includes ingestion run ID, file hash, output paths, and data quality score.",
            "Confirm whether UI wants DB-enriched IDs in Duy fixture after Phat insert.",
            "Return missing field list if Dashboard/Suggestions/Reports need additional ingestion signals.",
            "Return screenshot or JSON sample showing Duy fixture displayed in Streamlit.",
        ],
        "alignment_notes": [
            "Duy's source of truth fixture is outputs/ui_fixtures/duy_latest_ingestion_summary.json.",
            "Hung's demo/fixtures/duy_latest_ingestion_summary.json should be refreshed from Duy's source-of-truth fixture when Duy reruns ingestion.",
            "Before DB insert, source_id and document_db_id remain null in Duy's fixture.",
            "After Phat DB insert, Hung can enrich dataflow_technical_report_pdf with source_id=2 and document_db_id=1.",
            "Do not use ingestion_run_id as source_id.",
            "The prediction_context ingestion_run_id should match the payload it references; latest_ingestion_run.ingestion_run_id remains the dashboard run ID.",
            "Dashboard should use Phat view fixture for aggregated database metrics and Duy fixture for ingestion lineage/path details.",
            "Reports should degrade gracefully when suggestions are empty and display Not available in current data.",
        ],
        "missing_or_follow_up_items_for_hung": [
            "Return a screenshot or markdown confirmation after copying the latest Duy fixture into demo/fixtures.",
            "Confirm whether Hung wants Duy to publish a DB-enriched fixture after Phat assigns source_id and document_db_id.",
            "Confirm any additional fields needed for report evidence rows beyond run_id, file_hash_sha256, output paths, and data_quality_score.",
            "Confirm Suggestions thresholds for data_quality_score and RAG similarity_score.",
        ],
        "source_files_checked": {
            "duy_quality_fixture_present": bool(duy_quality),
            "duy_pdf_fixture_present": bool(duy_pdf),
            "hung_mock_client": str(HUNG_ROOT / "demo" / "services" / "mock_client.py"),
            "hung_dashboard_page": str(HUNG_ROOT / "demo" / "views" / "dashboard_page.py"),
            "hung_suggestions_page": str(HUNG_ROOT / "demo" / "views" / "suggestions_page.py"),
            "hung_reports_page": str(HUNG_ROOT / "demo" / "views" / "reports_page.py"),
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote Hung mapping summary: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
