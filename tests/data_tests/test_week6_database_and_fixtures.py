from __future__ import annotations

from pathlib import Path

import pytest

from data_engineering.ingestion.api_ingestor import fetch_api_payload
from data_engineering.storage.db_connection import build_connection_kwargs, load_db_config
from data_engineering.storage.postgres_writer import (
    REQUIRED_SCHEMA_COLUMNS,
    build_dry_run_summary,
    ingestion_run_exists,
    insert_document_pages,
    insert_or_get_source,
    insert_pipeline_run,
    insert_structured_records,
    query_integration_counts,
    validate_target_schema,
)
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

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, cursor=None):
        self.cursor_obj = cursor or FakeCursor()

    def cursor(self):
        return self.cursor_obj


def test_db_config_example_has_required_connection_fields():
    config = load_db_config("data_engineering/configs/db_config.example.json")
    kwargs = build_connection_kwargs(config)

    assert kwargs["host"] == "localhost"
    assert kwargs["port"] == 5432
    assert kwargs["database"] == "datavision_db"


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
    assert conn.cursor_obj.executed[0][1][2] == "csv"


def test_insert_or_get_source_never_silently_returns_none():
    cursor = FakeCursor()
    cursor.fetchone = lambda: None

    with pytest.raises(RuntimeError, match="did not return a source ID"):
        insert_or_get_source(
            FakeConnection(cursor),
            {
                "source_name": "missing_source",
                "source_type": "api",
                "input_path_or_url": "https://example.test/items",
            },
        )


def test_insert_pipeline_run_uses_executable_values_clause():
    conn = FakeConnection()
    pipeline_run_id = insert_pipeline_run(
        conn,
        {
            "source_name": "superstore_sales_csv",
            "run_id": "run-001",
            "start_time": "2026-07-15T00:00:00+00:00",
            "end_time": "2026-07-15T00:01:00+00:00",
            "status": "success",
        },
    )

    sql, params = conn.cursor_obj.executed[0]
    assert pipeline_run_id == 42
    assert "VALUES (%s, %s, %s, %s)" in sql
    assert len(params) == 4


def test_ingestion_run_exists_queries_by_run_id():
    conn = FakeConnection()

    assert ingestion_run_exists(conn, "run-001") is True
    assert conn.cursor_obj.executed[0][1] == ("run-001",)


def test_query_integration_counts_returns_named_database_proof():
    cursor = FakeCursor()
    cursor.fetchone = lambda: (4, 4, 4, 1, 36, 11524)
    counts = query_integration_counts(
        FakeConnection(cursor),
        run_ids=["run-1", "run-2", "run-3", "run-4"],
        source_names=["csv", "excel", "api", "pdf"],
        document_external_ids=["doc_dataflow_technical_report"],
    )

    assert counts == {
        "sources": 4,
        "ingestion_logs": 4,
        "pipeline_runs": 4,
        "documents": 1,
        "document_pages": 36,
        "structured_records": 11524,
    }


def test_target_schema_preflight_accepts_all_week6_columns():
    cursor = FakeCursor()
    cursor.fetchall = lambda: [
        (table_name, column_name)
        for table_name, columns in REQUIRED_SCHEMA_COLUMNS.items()
        for column_name in columns
    ]

    result = validate_target_schema(FakeConnection(cursor))

    assert set(result) == set(REQUIRED_SCHEMA_COLUMNS)
    assert "document_external_id" in result["documents"]
    assert "data_quality_score" in result["ingestion_logs"]


def test_target_schema_preflight_reports_missing_columns():
    cursor = FakeCursor()
    cursor.fetchall = lambda: [("sources", "id"), ("sources", "name")]

    with pytest.raises(RuntimeError, match="schema is not compatible"):
        validate_target_schema(FakeConnection(cursor))


def test_document_pages_replace_existing_snapshot(tmp_path):
    pages = tmp_path / "document_pages.jsonl"
    pages.write_text(
        '\n'.join(
            [
                '{"page_number": 1, "text": "Page one", "character_count": 8, "is_empty": false}',
                '{"page_number": 2, "text": "Page two", "character_count": 8, "is_empty": false}',
            ]
        ),
        encoding="utf-8",
    )
    conn = FakeConnection()

    inserted = insert_document_pages(conn, pages, document_id=7)

    assert inserted == 2
    assert "DELETE FROM document_pages" in conn.cursor_obj.executed[0][0]
    assert conn.cursor_obj.executed[0][1] == (7,)


def test_structured_records_replace_existing_source_snapshot(tmp_path):
    clean_csv = tmp_path / "clean.csv"
    clean_csv.write_text("id,value\n1,alpha\n2,beta\n", encoding="utf-8")
    conn = FakeConnection()

    inserted = insert_structured_records(conn, clean_csv, source_id=9)

    assert inserted == 2
    assert "DELETE FROM structured_records" in conn.cursor_obj.executed[0][0]
    assert conn.cursor_obj.executed[0][1] == (9,)


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
    assert isinstance(result["warnings"], list)
    assert result["evidence"]["db_plan"] == "logs/db_load_dry_run/duy_to_phat_db_load_plan.json"
