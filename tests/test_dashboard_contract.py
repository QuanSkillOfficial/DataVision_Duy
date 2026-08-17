"""
tests/test_dashboard_contract.py
==================================
Verifies dashboard data flows correctly: mock dashboard returns
correct shape; empty source context still returns a valid envelope
(waiting state, not a crash); suggestions are sorted by final_score.

Week 8 note (DV-HUNG-01): this module imports the fixture implementation
directly instead of `service_client`. These tests pin the reference UI
contract - the shape and business rules the UI requires from any backend - so
they must produce the same result in fixture mode and in backend mode. Live
UI-to-backend integration is covered separately by
tests/test_backend_contract_smoke.py, which runs in backend mode only.
"""

from demo.services.mock_client import (
    get_dashboard_metrics,
    generate_suggestions,
    get_ingestion_status,
)


def test_dashboard_exposes_every_field_the_ui_renders():
    """Each field here is read by demo/views/dashboard_page.py."""
    data = get_dashboard_metrics()["data"]
    required = [
        "source_count", "file_count", "link_count", "record_count",
        "data_quality_score", "processing_status", "duplicate_risk",
        "parsing_coverage",
    ]
    for field in required:
        assert field in data, f"Missing field: {field}"


def test_dashboard_counts_the_supplied_source_context():
    sources = [{"filename": "a.csv"}, {"filename": "b.pdf"}]
    assert get_dashboard_metrics(sources)["data"]["source_count"] == 2


def test_ingestion_status_exposes_traceability_fields():
    """Run and document identity are what make a dashboard number auditable."""
    data = get_ingestion_status()["data"]
    for field in [
        "run_id", "source_name", "source_type",
        "status",                    # Duy uses 'status', not 'processing_status'
        "ingestion_run_id",
        "document_external_id",
        "data_quality_score",
    ]:
        assert field in data, f"Missing field: {field}"


def test_mock_dashboard_returns_correct_shape():
    response = get_dashboard_metrics()
    data = response["data"]
    assert isinstance(data["source_count"], int)
    assert isinstance(data["parsing_coverage"], float)
    assert isinstance(data["data_quality_score"], int)
    assert data["processing_status"] in {
        "ready", "processing", "waiting_for_source", "failed"
    }


def test_dashboard_with_empty_source_context_does_not_crash():
    response = get_dashboard_metrics(source_context=[])
    assert response["status"] == "success"
    assert "data" in response


def test_dashboard_includes_ingestion_runs():
    response = get_dashboard_metrics()
    assert "ingestion_runs" in response["data"]
    assert isinstance(response["data"]["ingestion_runs"], list)


def test_dashboard_includes_document_processing_status():
    response = get_dashboard_metrics()
    assert "document_processing_status" in response["data"]
    assert isinstance(response["data"]["document_processing_status"], dict)


def test_suggestions_sorted_by_final_score_descending():
    response = generate_suggestions({
        "dashboard_signals": {"parsing_coverage": 0.5, "processing_status": "ready"},
        "prediction_result": {"status": "needs_review", "confidence": 0.5},
        "rag_context": {"status": "no_match"},
    })
    scores = [s["final_score"] for s in response["data"]]
    assert scores == sorted(scores, reverse=True)


def test_suggestions_with_no_context_returns_waiting_state():
    """Empty context should still surface exactly one actionable
    'upload a source' suggestion, never an empty/crashing list."""
    response = generate_suggestions({})
    assert len(response["data"]) >= 1
    assert response["data"][0]["source_module"] == "ingestion"


def test_suggestions_each_have_evidence_fields():
    response = generate_suggestions({
        "dashboard_signals": {"parsing_coverage": 0.5},
    })
    for s in response["data"]:
        assert "source_module" in s
        assert "source_view" in s
        assert "evidence_type" in s
        assert "evidence_value" in s
        assert "generated_from" in s
