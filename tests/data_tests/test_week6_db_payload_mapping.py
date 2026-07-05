from __future__ import annotations

import json
from pathlib import Path

from data_engineering.pipelines.prediction_payload_builder import build_pdf_prediction_payload
from scripts.load_ingestion_outputs_to_postgres import build_dry_run_plan, load_successful_run_logs
from scripts.week6_build_ui_fixture_from_ingestion_logs import build_ui_fixture
from scripts.week6_build_rag_handoff_package import build_rag_handoff_package


def test_week6_document_id_maps_to_external_id_first():
    fixture = build_ui_fixture()

    assert fixture["latest_ingestion_run"]["document_external_id"] == "doc_dataflow_technical_report"
    assert fixture["latest_ingestion_run"]["document_db_id"] is None
    assert fixture["id_mapping"]["document_external_id"] == "Duy document key. Maps to documents.document_external_id."
    assert fixture["id_mapping"]["document_db_id"] == "Database document primary key from Phat. Null before DB insert."


def test_week6_document_pages_plan_uses_internal_fk_rule():
    plan = build_dry_run_plan(load_successful_run_logs())
    pdf_plan = next(run for run in plan["runs"] if run["source_name"] == "dataflow_technical_report_pdf")

    assert "documents" in pdf_plan["target_tables"]
    assert "document_pages" in pdf_plan["target_tables"]
    assert pdf_plan["would_insert"]["documents"] == 1
    assert pdf_plan["would_insert"]["document_pages"] == 36


def test_week6_ui_fixture_uses_real_ingestion_runs():
    fixture = build_ui_fixture()

    assert fixture["summary"]["total_sources"] >= 4
    assert fixture["summary"]["total_records_valid"] >= 11560
    assert fixture["summary"]["prediction_payload_available"] is True
    assert fixture["runs"]
    assert all("data_quality_score" in run for run in fixture["runs"])
    assert fixture["latest_ingestion_run"]["ingestion_run_id"]
    assert fixture["id_mapping"]["document_external_id"]
    assert fixture["prediction_context"]["document_external_id"] == "doc_dataflow_technical_report"
    assert fixture["prediction_context"]["source_id"] is None
    assert "extracted_text" not in fixture["prediction_context"]
    assert fixture["prediction_context"]["extracted_text_length"] == 129028
    assert fixture["prediction_context"]["full_payload_path"] == "logs/prediction_payloads/duy_pdf_prediction_payload.json"
    assert fixture["rag_handoff"]["document_pages_path"] == "outputs/rag_handoff/document_pages.jsonl"
    assert any(run.get("file_hash_sha256") for run in fixture["runs"])


def test_week6_prediction_payload_separates_db_ids_from_run_id():
    payload = build_pdf_prediction_payload()

    assert payload["document_external_id"] == "doc_dataflow_technical_report"
    assert payload["document_id"] == payload["document_external_id"]
    assert payload["source_id"] is None
    assert payload["document_db_id"] is None
    assert payload["source_name"] == "dataflow_technical_report_pdf"
    assert payload["ingestion_run_id"]
    assert payload["source_id"] != payload["ingestion_run_id"]


def test_week6_rag_handoff_package_uses_real_dataflow_pdf_values():
    summary = build_rag_handoff_package()

    assert summary["document_external_id"] == "doc_dataflow_technical_report"
    assert summary["page_count"] == 36
    assert summary["non_empty_pages"] == 36
    assert summary["empty_pages"] == 0
    assert summary["total_characters"] == 129028

    manifest_path = Path("outputs/rag_handoff/rag_handoff_manifest.json")
    pages_path = Path("outputs/rag_handoff/document_pages.jsonl")
    summary_path = Path("outputs/rag_handoff/rag_handoff_summary.md")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    page_count = sum(1 for line in pages_path.read_text(encoding="utf-8").splitlines() if line.strip())

    assert manifest["document_external_id"] == "doc_dataflow_technical_report"
    assert page_count == 36
    assert "TBD" not in summary_path.read_text(encoding="utf-8")
