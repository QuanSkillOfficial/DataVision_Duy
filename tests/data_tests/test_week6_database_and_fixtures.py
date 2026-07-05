from __future__ import annotations

from pathlib import Path

from data_engineering.ingestion.api_ingestor import fetch_api_payload
from data_engineering.storage.db_connection import build_connection_kwargs, load_db_config
from data_engineering.storage.postgres_writer import build_dry_run_summary, insert_or_get_source
from scripts.load_ingestion_outputs_to_postgres import build_dry_run_plan, load_successful_run_logs
from scripts.week6_end_to_end_smoke_test import run_smoke_test
from scripts.week6_build_ui_fixture_from_ingestion_logs import (
    DATA_QUALITY_OUTPUT_PATH,
    PDF_DOCUMENT_OUTPUT_PATH,
    build_data_quality_summary,
    build_pdf_document_summary,
    build_ui_fixture,
)


class FakeCursor:
    def __init__(self):
        self.executed = []

    def execute(self, sql, params):
        self.executed.append((sql, params))

    def fetchone(self):
        return (42,)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj


def test_db_config_example_has_required_connection_fields():
    config = load_db_config("data_engineering/configs/db_config.example.json")
    kwargs = build_connection_kwargs(config)

    assert kwargs["host"] == "localhost"
    assert kwargs["port"] == 5432
    assert kwargs["database"] == "platform_db_dev"


def test_insert_or_get_source_returns_existing_or_inserted_source_id():
    conn = FakeConnection()
    source_id = insert_or_get_source(
        conn,
        {
            "source_name": "superstore_sales_csv",
            "source_type": "csv",
            "input_path_or_url": "week2/data/sample_inputs/Superstore.csv",
            "owner": "Nguyen Minh Duy",
        },
    )

    assert source_id == 42
    assert "ON CONFLICT (name)" in conn.cursor_obj.executed[0][0]


def test_database_dry_run_plan_targets_week6_tables():
    runs = load_successful_run_logs()
    plan = build_dry_run_plan(runs)

    assert plan["totals"]["sources"] == 4
    assert plan["totals"]["pipeline_runs"] == 4
    assert plan["totals"]["ingestion_logs"] == 4
    assert plan["totals"]["structured_records"] == 11524
    assert plan["totals"]["documents"] == 1
    assert plan["totals"]["document_pages"] == 36


def test_postgres_writer_dry_run_summary_includes_expected_target_table():
    pdf_run = next(run for run in load_successful_run_logs() if run["source_type"] == "pdf")
    csv_run = next(run for run in load_successful_run_logs() if run["source_type"] == "csv")

    assert "document_pages" in build_dry_run_summary(pdf_run)["target_tables"]
    assert "structured_records" in build_dry_run_summary(csv_run)["target_tables"]


def test_api_fallback_reads_stable_sample_input():
    payload, error = fetch_api_payload(
        "https://invalid.localhost/products",
        "data/sample_inputs/api/dummyjson_products_sample.json",
        use_cached_response=True,
    )

    assert error == "used cached API response"
    assert "products" in payload
    assert len(payload["products"]) == 30


def test_phi_hung_data_quality_and_pdf_summary_outputs_are_real_shaped():
    fixture = build_ui_fixture()
    data_quality = build_data_quality_summary(fixture)
    pdf_summary = build_pdf_document_summary(fixture)

    assert data_quality["summary"]["total_sources"] == 4
    assert len(data_quality["sources"]) == 4
    assert pdf_summary["document_external_id"] == "doc_dataflow_technical_report"
    assert pdf_summary["page_count"] == 36
    assert pdf_summary["valid_pages"] == 36

    assert DATA_QUALITY_OUTPUT_PATH.as_posix().endswith("outputs/ui_fixtures/duy_data_quality_summary.json")
    assert PDF_DOCUMENT_OUTPUT_PATH.as_posix().endswith("outputs/ui_fixtures/duy_pdf_document_summary.json")


def test_week6_end_to_end_smoke_test_passes_for_duy_outputs():
    result = run_smoke_test()

    assert result["status"] == "passed"
    assert all(result["checks"].values())
    assert result["evidence"]["db_plan"] == "logs/db_load_dry_run/duy_to_phat_db_load_plan.json"
