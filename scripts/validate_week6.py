from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "scripts/load_ingestion_outputs_to_postgres.py",
    "scripts/week6_end_to_end_smoke_test.py",
    "scripts/week6_build_ui_fixture_from_ingestion_logs.py",
    "scripts/week6_build_phat_mapping_summary.py",
    "scripts/week6_build_lap_mapping_summary.py",
    "scripts/week6_build_tuong_mapping_summary.py",
    "scripts/week6_build_hung_mapping_summary.py",
    "docs/week6_id_mapping_contract.md",
    "docs/week6_ingestion_to_schema_v3_mapping.md",
    "docs/week6_document_pages_for_rag_confirmed.md",
    "docs/week6_duy_to_phat_db_load_result.md",
    "docs/week6_database_loading_result.md",
    "docs/week6_phi_hung_ui_fixture_contract.md",
    "data_engineering/storage/db_connection.py",
    "data_engineering/configs/db_config.example.json",
    "data/sample_inputs/api/dummyjson_products_sample.json",
    "logs/db_load_dry_run/duy_to_phat_db_load_plan.json",
    "logs/ui_fixtures/duy_ingestion_dashboard_fixture.json",
    "outputs/ui_fixtures/duy_latest_ingestion_summary.json",
    "outputs/ui_fixtures/duy_data_quality_summary.json",
    "outputs/ui_fixtures/duy_pdf_document_summary.json",
    "logs/prediction_payloads/duy_pdf_prediction_payload.json",
    "outputs/rag_handoff/document_pages.jsonl",
    "outputs/rag_handoff/pdf_metadata.json",
    "outputs/rag_handoff/rag_handoff_summary.md",
    "outputs/rag_handoff/rag_handoff_manifest.json",
    "outputs/phat_handoff/phat_week6_mapping_summary.json",
    "outputs/lap_handoff/lap_week6_mapping_summary.json",
    "outputs/tuong_handoff/tuong_week6_mapping_summary.json",
    "outputs/hung_handoff/hung_week6_mapping_summary.json",
    "tests/data_tests/test_week6_db_payload_mapping.py",
]


def validate_required_files() -> list[str]:
    return [f"Missing Week 6 file: {path}" for path in REQUIRED_FILES if not (PROJECT_ROOT / path).exists()]


def validate_load_plan() -> list[str]:
    errors: list[str] = []
    path = PROJECT_ROOT / "logs/db_load_dry_run/duy_to_phat_db_load_plan.json"
    if not path.exists():
        return ["Missing DB dry-run plan"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("mode") != "dry_run":
        errors.append("DB load plan should be in dry_run mode until Phat database config is confirmed")
    totals = payload.get("totals", {})
    if totals.get("sources") != 4:
        errors.append("DB dry-run should plan 4 sources")
    if totals.get("pipeline_runs") != 4:
        errors.append("DB dry-run should plan 4 pipeline_runs")
    if totals.get("ingestion_logs") != 4:
        errors.append("DB dry-run should plan 4 ingestion_logs")
    if totals.get("structured_records") != 11524:
        errors.append("DB dry-run should plan 11524 structured records")
    if totals.get("documents") != 1 or totals.get("document_pages") != 36:
        errors.append("DB dry-run should plan 1 PDF document and 36 document_pages")
    run_tables = {run.get("source_name"): set(run.get("target_tables", [])) for run in payload.get("runs", [])}
    if "document_pages" not in run_tables.get("dataflow_technical_report_pdf", set()):
        errors.append("PDF dry-run should target document_pages")
    if "structured_records" not in run_tables.get("superstore_sales_csv", set()):
        errors.append("CSV dry-run should target structured_records")
    return errors


def validate_ui_fixture() -> list[str]:
    errors: list[str] = []
    path = PROJECT_ROOT / "outputs/ui_fixtures/duy_latest_ingestion_summary.json"
    if not path.exists():
        return ["Missing Duy latest ingestion summary fixture for Phi/Hung"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload.get("summary", {})
    if summary.get("total_sources", 0) < 4:
        errors.append("UI fixture should include at least 4 Duy sources")
    if summary.get("total_records_valid", 0) < 11560:
        errors.append("UI fixture should include real Duy valid record/page counts")
    if not payload.get("runs"):
        errors.append("UI fixture has no runs")
    latest = payload.get("latest_ingestion_run", {})
    required_latest_fields = [
        "run_id",
        "ingestion_run_id",
        "source_name",
        "source_type",
        "status",
        "records_read",
        "records_valid",
        "records_invalid",
        "data_quality_score",
        "raw_output_path",
        "staging_output_path",
        "clean_output_path",
    ]
    missing = [field for field in required_latest_fields if field not in latest]
    if missing:
        errors.append(f"Latest ingestion run missing UI fields: {missing}")
    if not any(run.get("file_hash_sha256") for run in payload.get("runs", [])):
        errors.append("UI fixture should include file_hash_sha256 values")
    prediction_context = payload.get("prediction_context") or {}
    if "extracted_text" in prediction_context:
        errors.append("UI fixture prediction_context should not embed full extracted_text")
    if prediction_context.get("extracted_text_length") != 129028:
        errors.append("UI fixture should expose extracted_text_length for Prediction UI")
    if prediction_context.get("source_id") is not None:
        errors.append("UI fixture prediction_context source_id should be null before DB insert")
    if prediction_context.get("document_external_id") != "doc_dataflow_technical_report":
        errors.append("UI fixture should expose Duy document_external_id")
    rag_handoff = payload.get("rag_handoff") or {}
    if rag_handoff.get("document_pages_path") != "outputs/rag_handoff/document_pages.jsonl":
        errors.append("UI fixture should expose RAG handoff document_pages path")
    return errors


def validate_phi_hung_summary_fixtures() -> list[str]:
    errors: list[str] = []
    dq_path = PROJECT_ROOT / "outputs/ui_fixtures/duy_data_quality_summary.json"
    pdf_path = PROJECT_ROOT / "outputs/ui_fixtures/duy_pdf_document_summary.json"
    if not dq_path.exists() or not pdf_path.exists():
        return ["Missing Phi/Hung summary fixtures"]
    dq = json.loads(dq_path.read_text(encoding="utf-8"))
    pdf = json.loads(pdf_path.read_text(encoding="utf-8"))
    if dq.get("summary", {}).get("total_sources") != 4:
        errors.append("Data quality fixture should include 4 sources")
    if len(dq.get("sources", [])) != 4:
        errors.append("Data quality fixture should include 4 source rows")
    if pdf.get("document_external_id") != "doc_dataflow_technical_report":
        errors.append("PDF document summary should include document_external_id")
    if pdf.get("page_count") != 36 or pdf.get("valid_pages") != 36:
        errors.append("PDF document summary should include 36 valid pages")
    return errors


def validate_api_fallback_sample() -> list[str]:
    path = PROJECT_ROOT / "data/sample_inputs/api/dummyjson_products_sample.json"
    if not path.exists():
        return ["Missing API fallback sample input"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if len(payload.get("products", [])) != 30:
        return ["API fallback sample should contain 30 DummyJSON products"]
    return []


def validate_prediction_payload() -> list[str]:
    errors: list[str] = []
    path = PROJECT_ROOT / "logs/prediction_payloads/duy_pdf_prediction_payload.json"
    if not path.exists():
        return ["Missing Duy prediction payload"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("document_external_id") != "doc_dataflow_technical_report":
        errors.append("Prediction payload must include document_external_id")
    if payload.get("document_db_id") is not None:
        errors.append("document_db_id should be null before Phat DB insert")
    if payload.get("source_id") is not None:
        errors.append("source_id should be null before Phat DB insert")
    if not payload.get("source_name"):
        errors.append("Prediction payload must include source_name")
    if not payload.get("ingestion_run_id"):
        errors.append("Prediction payload must include ingestion_run_id")
    if payload.get("source_id") == payload.get("ingestion_run_id"):
        errors.append("source_id must not reuse ingestion_run_id")
    return errors


def validate_rag_handoff() -> list[str]:
    errors: list[str] = []
    manifest_path = PROJECT_ROOT / "outputs/rag_handoff/rag_handoff_manifest.json"
    pages_path = PROJECT_ROOT / "outputs/rag_handoff/document_pages.jsonl"
    summary_path = PROJECT_ROOT / "outputs/rag_handoff/rag_handoff_summary.md"
    if not manifest_path.exists() or not pages_path.exists():
        return ["Missing RAG handoff output package"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    page_count = sum(1 for line in pages_path.read_text(encoding="utf-8").splitlines() if line.strip())
    if manifest.get("document_external_id") != "doc_dataflow_technical_report":
        errors.append("RAG handoff must identify doc_dataflow_technical_report")
    if manifest.get("page_count") != 36 or page_count != 36:
        errors.append("RAG handoff should include 36 DataFlow PDF pages")
    if manifest.get("non_empty_pages") != 36:
        errors.append("RAG handoff should report 36 non-empty pages")
    if manifest.get("empty_pages") != 0:
        errors.append("RAG handoff should report 0 empty pages")
    if manifest.get("total_characters") != 129028:
        errors.append("RAG handoff should preserve the real total character count")
    if summary_path.exists() and "TBD" in summary_path.read_text(encoding="utf-8"):
        errors.append("RAG handoff summary must not contain TBD values")
    return errors


def _iter_string_values(payload):
    if isinstance(payload, dict):
        for value in payload.values():
            yield from _iter_string_values(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from _iter_string_values(value)
    elif isinstance(payload, str):
        yield payload


def validate_portable_handoff_paths() -> list[str]:
    errors: list[str] = []
    paths = [
        PROJECT_ROOT / "outputs/phat_handoff/phat_week6_mapping_summary.json",
        PROJECT_ROOT / "outputs/lap_handoff/lap_week6_mapping_summary.json",
        PROJECT_ROOT / "outputs/tuong_handoff/tuong_week6_mapping_summary.json",
        PROJECT_ROOT / "outputs/hung_handoff/hung_week6_mapping_summary.json",
    ]
    for path in paths:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        absolute_paths = [value for value in _iter_string_values(payload) if re.match(r"^[A-Za-z]:[/\\]", value)]
        if absolute_paths:
            errors.append(f"Handoff summary contains local absolute paths: {path.relative_to(PROJECT_ROOT).as_posix()}")
    return errors


def validate_cross_team_integration_proof() -> list[str]:
    errors: list[str] = []
    phat = json.loads((PROJECT_ROOT / "outputs/phat_handoff/phat_week6_mapping_summary.json").read_text(encoding="utf-8"))
    lap = json.loads((PROJECT_ROOT / "outputs/lap_handoff/lap_week6_mapping_summary.json").read_text(encoding="utf-8"))
    tuong = json.loads((PROJECT_ROOT / "outputs/tuong_handoff/tuong_week6_mapping_summary.json").read_text(encoding="utf-8"))
    hung = json.loads((PROJECT_ROOT / "outputs/hung_handoff/hung_week6_mapping_summary.json").read_text(encoding="utf-8"))

    integration = phat.get("integration_status", {})
    required_phat_checks = [
        "duy_ingestion_loaded",
        "document_external_id_resolved",
        "structured_records_loaded",
        "lap_chunks_loaded",
        "tuong_prediction_logs_loaded",
        "phi_hung_dashboard_views_exported",
    ]
    if not all(integration.get(check) is True for check in required_phat_checks):
        errors.append("Phat handoff summary does not prove the full Week 6 database integration chain")
    if lap.get("lap_evaluation_fixture", {}).get("queries", 0) < 15:
        errors.append("Lap handoff summary should include at least 15 retrieval evaluation queries")
    if tuong.get("tuong_result_summary", {}).get("total_payloads") != 10:
        errors.append("Tuong handoff summary should include all 10 Duy prediction payloads")
    hung_status = hung.get("current_hung_fixture_status", {})
    required_hung_fixtures = [
        "duy_fixture_loaded_by_hung",
        "phat_dashboard_fixture_loaded_by_hung",
        "tuong_prediction_batch_fixture_loaded_by_hung",
        "lap_rag_response_fixture_loaded_by_hung",
    ]
    if not all(hung_status.get(check) is True for check in required_hung_fixtures):
        errors.append("Hung handoff summary is missing one or more real-output fixtures")
    return errors


def collect_cross_team_warnings() -> list[str]:
    warnings: list[str] = []
    lap = json.loads((PROJECT_ROOT / "outputs/lap_handoff/lap_week6_mapping_summary.json").read_text(encoding="utf-8"))
    tuong = json.loads((PROJECT_ROOT / "outputs/tuong_handoff/tuong_week6_mapping_summary.json").read_text(encoding="utf-8"))
    hung = json.loads((PROJECT_ROOT / "outputs/hung_handoff/hung_week6_mapping_summary.json").read_text(encoding="utf-8"))

    if not lap.get("lap_execution_status", {}).get("live_pgvector_notebook_executed"):
        warnings.append("Lap notebook has no executed live pgvector output; Phat chunk exports remain the integration proof.")
    if not lap.get("lap_execution_status", {}).get("live_ui_fixture_available"):
        warnings.append("Lap repository has not published outputs/ui_fixtures/lap_rag_response_real.json.")
    if not tuong.get("lineage_alignment", {}).get("all_current_lineage_matches"):
        warnings.append("Tuong results use an earlier Duy ingestion_run_id snapshot; stable document IDs still match.")
    if not hung.get("current_hung_fixture_status", {}).get("hung_fixture_matches_duy_latest_run"):
        warnings.append("Hung's copied Duy fixture should be refreshed after Duy's latest ingestion run.")
    return warnings


def main() -> int:
    errors = (
        validate_required_files()
        + validate_load_plan()
        + validate_ui_fixture()
        + validate_phi_hung_summary_fixtures()
        + validate_prediction_payload()
        + validate_rag_handoff()
        + validate_api_fallback_sample()
        + validate_portable_handoff_paths()
        + validate_cross_team_integration_proof()
    )
    if errors:
        print("Week 6 validation failed")
        for error in errors:
            print(f"- {error}")
        return 1
    warnings = collect_cross_team_warnings()
    print("Week 6 validation passed")
    print(f"Checked {len(REQUIRED_FILES)} required Week 6 files")
    print("Checked DB dry-run mapping")
    print("Checked UI fixture from real ingestion logs")
    print("Checked Phi/Hung data quality and PDF summary fixtures")
    print("Checked Tuong prediction payload ID semantics")
    print("Checked Lap RAG handoff package")
    print("Checked API fallback sample")
    print("Checked portable cross-repository handoff paths")
    print("Checked Phat/Lap/Tuong/Hung integration evidence")
    for warning in warnings:
        print(f"Warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
