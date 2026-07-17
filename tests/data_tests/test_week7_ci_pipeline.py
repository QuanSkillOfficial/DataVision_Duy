from __future__ import annotations

import json
from pathlib import Path

from data_engineering.pipelines.handoff_context import (
    allocate_structured_record_limits,
    load_database_identity_map,
)
from data_engineering.storage.db_connection import load_db_config
from scripts.load_ingestion_outputs_to_postgres import build_dry_run_plan, load_successful_run_logs
from scripts.week7_ci_ingestion_smoke_test import run_ci_smoke_test
from scripts.week7_data_pipeline_smoke_test import run_smoke_test


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_week7_shared_test_fixtures_are_small_and_complete():
    fixture_dir = PROJECT_ROOT / "tests/fixtures/data"
    expected = {
        "sample_superstore_small.csv",
        "sample_product_sales_small.xlsx",
        "sample_api_products.json",
        "sample_dataflow_pages_small.jsonl",
        "sample_dataflow_small.pdf",
    }
    assert expected <= {path.name for path in fixture_dir.iterdir()}
    assert (fixture_dir / "sample_superstore_small.csv").stat().st_size < 100_000
    assert (fixture_dir / "sample_dataflow_small.pdf").stat().st_size < 1_000_000


def test_week7_smoke_allocation_is_100_records_across_sources():
    runs = load_successful_run_logs()
    allocation = allocate_structured_record_limits(runs, 100)

    assert sum(value or 0 for value in allocation.values()) == 100
    assert set(allocation) == {
        "superstore_sales_csv",
        "product_sales_region_excel",
        "dummyjson_products_api",
    }
    assert all((value or 0) > 0 for value in allocation.values())


def test_week7_db_smoke_plan_uses_expected_counts():
    plan = build_dry_run_plan(load_successful_run_logs(), structured_record_limit=100)

    assert plan["mode"] == "smoke_dry_run"
    assert plan["totals"] == {
        "sources": 4,
        "pipeline_runs": 4,
        "ingestion_logs": 4,
        "structured_records": 100,
        "documents": 1,
        "document_pages": 36,
    }


def test_week7_db_config_supports_standard_ci_environment(monkeypatch):
    monkeypatch.setenv("DB_HOST", "ci-postgres")
    monkeypatch.setenv("DB_PORT", "55432")
    monkeypatch.setenv("DB_NAME", "ci_datavision")
    monkeypatch.setenv("DB_USER", "ci_user")
    monkeypatch.setenv("DB_PASSWORD", "ci_password")

    config = load_db_config()

    assert config["host"] == "ci-postgres"
    assert config["port"] == 55432
    assert config["database"] == "ci_datavision"
    assert config["user"] == "ci_user"


def test_week7_identity_map_is_explicitly_pending_without_db_result(tmp_path):
    identity = load_database_identity_map(tmp_path / "missing_result.json")

    assert identity["status"] == "pending_database_load"
    assert identity["source_ids"] == {}
    assert identity["document_db_ids"] == {}


def test_week7_identity_map_reads_confirmed_source_and_document_ids(tmp_path):
    result_path = tmp_path / "db_result.json"
    result_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "mode": "smoke_write_db",
                "results": [
                    {
                        "source_name": "dataflow_technical_report_pdf",
                        "source_id": 2,
                        "document_external_id": "doc_dataflow_technical_report",
                        "document_db_id": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    identity = load_database_identity_map(result_path)

    assert identity["status"] == "database_ids_confirmed"
    assert identity["source_ids"]["dataflow_technical_report_pdf"] == 2
    assert identity["document_db_ids"]["doc_dataflow_technical_report"] == 1


def test_week7_rag_handoff_has_database_ready_page_contract():
    manifest = json.loads(
        (PROJECT_ROOT / "outputs/rag_handoff/week7_rag_handoff_manifest.json").read_text(encoding="utf-8")
    )
    first_page = json.loads(
        (PROJECT_ROOT / "outputs/rag_handoff/week7_document_pages_db_enriched.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )

    assert manifest["page_count"] == 36
    assert manifest["total_characters"] == 129028
    assert first_page["document_external_id"] == "doc_dataflow_technical_report"
    assert first_page["ingestion_run_id"]
    assert first_page["char_count"] > 0
    assert first_page["word_count"] > 0


def test_week7_prediction_payloads_have_platform_ids_and_quality_fields():
    payloads = json.loads(
        (PROJECT_ROOT / "outputs/prediction_payloads/tuong_week7_prediction_payloads.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(payloads) == 20
    assert {payload["test_case"] for payload in payloads} >= {
        "full_pdf_document",
        "short_extracted_text_quality_gate",
        "empty_extracted_text_quality_gate",
        "missing_required_file_name",
    }
    assert all("source_id" in payload for payload in payloads)
    assert all("document_db_id" in payload for payload in payloads)
    assert all("ingestion_run_id" in payload for payload in payloads)
    assert all("data_quality_score" in payload for payload in payloads)
    assert all("file_hash_sha256" in payload for payload in payloads)


def test_week7_additional_prediction_payloads_cover_new_sections_and_validation_cases():
    additional_payloads = json.loads(
        (
            PROJECT_ROOT
            / "outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json"
        ).read_text(encoding="utf-8")
    )

    assert len(additional_payloads) == 10
    assert [payload["test_case"] for payload in additional_payloads] == [
        "pdf_system_operators_section",
        "pdf_pipeline_api_section",
        "pdf_agent_workflow_section",
        "pdf_agentic_rag_evaluation_section",
        "csv_order_profitability_sample",
        "excel_regional_sales_sample",
        "api_inventory_sample",
        "unknown_file_type_markdown",
        "missing_document_external_id",
        "invalid_file_size_type",
    ]

    required_model_fields = {
        "file_name",
        "file_type",
        "file_size",
        "text_length",
        "num_pages",
        "source_system",
        "extracted_text",
    }
    assert all(
        required_model_fields <= payload.keys()
        for payload in additional_payloads[:8]
    )
    assert all(payload["text_length"] >= 50 for payload in additional_payloads[:8])
    assert additional_payloads[7]["file_type"] == "md"
    assert "document_external_id" not in additional_payloads[8]
    assert additional_payloads[8]["expected_status_hint"] == "failed_contract_validation"
    assert additional_payloads[9]["file_size"] == "not-a-number"
    assert additional_payloads[9]["expected_status_hint"] == "failed"

    individual_files = list(
        (PROJECT_ROOT / "outputs/prediction_payloads/week7").glob("*.json")
    )
    assert len(individual_files) == 20


def test_week7_ui_fixture_matches_phi_hung_contract():
    fixture = json.loads(
        (PROJECT_ROOT / "outputs/ui_fixtures/duy_week7_database_enriched_summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert fixture["total_sources"] == 4
    assert fixture["total_runs"] == 4
    assert fixture["successful_runs"] == 4
    assert fixture["total_records_read"] == 11524
    assert fixture["total_document_pages_read"] == 36
    assert fixture["average_data_quality_score"] == 99.63
    assert fixture["latest_document"]["document_external_id"] == "doc_dataflow_technical_report"
    assert fixture["handoff_paths"]["rag_handoff"].endswith("week7_document_pages_db_enriched.jsonl")


def test_week7_ci_smoke_test_passes_under_two_minutes():
    result = run_ci_smoke_test()

    assert result["status"] == "passed"
    assert result["elapsed_seconds"] < 120
    assert all(result["checks"].values())


def test_week7_data_pipeline_smoke_test_passes():
    result = run_smoke_test()

    assert result["status"] == "passed"
    assert all(result["checks"].values())
