"""
Week 7 fixture validation tests.

These tests protect the UI from malformed handoff JSON before Streamlit
tries to render it.
"""

import pytest

from demo.services.fixture_validator import (
    FixtureValidationError,
    load_week7_fixture,
    validate_all_week7_fixtures,
    validate_duy_ingestion_summary,
    validate_lap_rag_response,
    validate_phat_dashboard_views,
    validate_tuong_prediction_batch,
    validate_tuong_review_queue,
)


def test_all_week7_fixtures_validate():
    fixtures = validate_all_week7_fixtures()
    assert set(fixtures) == {
        "duy_latest_ingestion_summary",
        "phat_dashboard_views_sample",
        "lap_rag_response_real",
        "tuong_prediction_batch_response",
        "tuong_prediction_review_queue_sample",
    }


def test_duy_fixture_has_required_week7_fields():
    payload = validate_duy_ingestion_summary(
        load_week7_fixture("duy_latest_ingestion_summary")
    )
    assert payload["total_sources"] >= 1
    assert payload["successful_runs"] >= 1
    assert payload["latest_document"]["document_external_id"]
    assert "rag_handoff" in payload["handoff_paths"]
    assert "prediction_payloads" in payload["handoff_paths"]


def test_phat_fixture_has_required_views():
    payload = validate_phat_dashboard_views(
        load_week7_fixture("phat_dashboard_views_sample")
    )
    views = payload["data"]
    assert views["v_dashboard_overview"]
    assert isinstance(views["v_prediction_review_queue"], list)


def test_lap_fixture_uses_dataflow_citations():
    payload = validate_lap_rag_response(load_week7_fixture("lap_rag_response_real"))
    data = payload["data"]
    assert data["document_external_id"] == "doc_dataflow_technical_report"
    assert data["status"] in {"success", "retrieval_only"}
    assert payload["metadata"]["retrieval_backend"] == "pgvector"
    assert payload["metadata"]["embedding_dimension"] == 384
    for citation in data["citations"]:
        assert citation["file_name"] == "DataFlow_Technical_Report.pdf"
        assert citation["document_external_id"] == "doc_dataflow_technical_report"
        assert citation["document_db_id"] is not None
        assert citation["similarity_score"] is not None
        assert citation["chunk_id"].startswith(
            "doc_dataflow_technical_report_page_"
        )


def test_tuong_batch_fixture_has_manual_review_flags():
    payload = validate_tuong_prediction_batch(
        load_week7_fixture("tuong_prediction_batch_response")
    )
    assert payload["results"]
    assert any(item["manual_review_required"] for item in payload["results"])


def test_tuong_review_queue_fixture_has_feedback_ids():
    payload = validate_tuong_review_queue(
        load_week7_fixture("tuong_prediction_review_queue_sample")
    )
    assert payload["review_items"]
    for item in payload["review_items"]:
        assert item["prediction_log_id"] is not None
        assert item["manual_review_required"] is True


def test_validator_reports_missing_required_field():
    with pytest.raises(FixtureValidationError, match="total_sources"):
        validate_duy_ingestion_summary({})
