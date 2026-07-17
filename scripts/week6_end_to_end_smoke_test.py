from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PLAN = PROJECT_ROOT / "logs/db_load_dry_run/duy_to_phat_db_load_plan.json"
RAG_HANDOFF = PROJECT_ROOT / "outputs/rag_handoff/rag_handoff_manifest.json"
PREDICTION_PAYLOAD = PROJECT_ROOT / "logs/prediction_payloads/duy_pdf_prediction_payload.json"
UI_FIXTURE = PROJECT_ROOT / "outputs/ui_fixtures/duy_latest_ingestion_summary.json"
PHAT_PROOF = PROJECT_ROOT / "outputs/phat_handoff/phat_week6_mapping_summary.json"
LAP_PROOF = PROJECT_ROOT / "outputs/lap_handoff/lap_week6_mapping_summary.json"
TUONG_PROOF = PROJECT_ROOT / "outputs/tuong_handoff/tuong_week6_mapping_summary.json"
HUNG_PROOF = PROJECT_ROOT / "outputs/hung_handoff/hung_week6_mapping_summary.json"


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def run_smoke_test() -> dict:
    db_plan = _read_json(DB_PLAN)
    rag = _read_json(RAG_HANDOFF)
    prediction = _read_json(PREDICTION_PAYLOAD)
    ui = _read_json(UI_FIXTURE)
    phat = _read_json(PHAT_PROOF)
    lap = _read_json(LAP_PROOF)
    tuong = _read_json(TUONG_PROOF)
    hung = _read_json(HUNG_PROOF)

    integration = phat.get("integration_status", {})
    database_counts = phat.get("counts", {})
    dashboard = phat.get("dashboard_overview", {})
    lap_evaluation = lap.get("lap_evaluation_fixture", {})
    tuong_results = tuong.get("tuong_result_summary", {})
    hung_status = hung.get("current_hung_fixture_status", {})
    lineage = tuong.get("lineage_alignment", {})
    lap_execution = lap.get("lap_execution_status", {})

    checks = {
        "connect": integration.get("duy_ingestion_loaded") is True,
        "insert": database_counts.get("structured_records_sample_rows") == 11524
        and database_counts.get("document_pages") == 36
        and database_counts.get("documents") == 1,
        "query": dashboard.get("total_sources") == 4
        and dashboard.get("successful_ingestions") == 4,
        "retrieve": integration.get("lap_chunks_loaded") is True
        and database_counts.get("document_chunks", 0) > 0
        and lap_evaluation.get("queries", 0) >= 15
        and rag.get("page_count") == 36,
        "predict": bool(
            prediction.get("document_external_id") == "doc_dataflow_technical_report"
            and prediction.get("source_id") is None
            and prediction.get("ingestion_run_id")
            and tuong_results.get("total_payloads") == 10
            and integration.get("tuong_prediction_logs_loaded") is True
        ),
        "display": all(
            hung_status.get(field) is True
            for field in (
                "duy_fixture_loaded_by_hung",
                "phat_dashboard_fixture_loaded_by_hung",
                "tuong_prediction_batch_fixture_loaded_by_hung",
                "lap_rag_response_fixture_loaded_by_hung",
            )
        ),
        "test": db_plan.get("run_count") == 4
        and ui.get("summary", {}).get("total_sources") == 4
        and phat.get("document_id_map", {}).get("doc_dataflow_technical_report", {}).get("document_db_id") == 1,
    }
    warnings = []
    if not hung_status.get("hung_fixture_matches_duy_latest_run"):
        warnings.append("Hung's copied Duy fixture is older than Duy's latest ingestion run.")
    if not lineage.get("all_current_lineage_matches"):
        warnings.append("Tuong's 10 results use valid stable document IDs but not Duy's latest ingestion_run_id values.")
    if not lap_execution.get("live_pgvector_notebook_executed"):
        warnings.append("Phat exports prove stored chunks, but Lap's pgvector notebook is not executed in the Lap repository.")
    if not lap_execution.get("live_ui_fixture_available"):
        warnings.append("Lap's citation-ready UI fixture is still absent from the Lap repository.")

    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "warnings": warnings,
        "evidence": {
            "db_plan": DB_PLAN.relative_to(PROJECT_ROOT).as_posix(),
            "rag_handoff": RAG_HANDOFF.relative_to(PROJECT_ROOT).as_posix(),
            "prediction_payload": PREDICTION_PAYLOAD.relative_to(PROJECT_ROOT).as_posix(),
            "ui_fixture": UI_FIXTURE.relative_to(PROJECT_ROOT).as_posix(),
            "phat_database_proof": PHAT_PROOF.relative_to(PROJECT_ROOT).as_posix(),
            "lap_retrieval_proof": LAP_PROOF.relative_to(PROJECT_ROOT).as_posix(),
            "tuong_prediction_proof": TUONG_PROOF.relative_to(PROJECT_ROOT).as_posix(),
            "hung_display_proof": HUNG_PROOF.relative_to(PROJECT_ROOT).as_posix(),
        },
    }


def main() -> int:
    result = run_smoke_test()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
