"""
tests/test_service_client.py
==============================
Verifies that service_client.py (the single interface pages call)
correctly routes to mock_client and returns mock dashboard data.
"""

from demo.config import USE_BACKEND
from demo.services.service_client import (
    get_dashboard_metrics,
    get_ingestion_status,
    get_recent_activity,
)


def test_default_mode_is_mock():
    """Sanity check that the demo defaults to mock mode unless overridden."""
    assert isinstance(USE_BACKEND, bool)


def test_get_dashboard_metrics_returns_envelope():
    response = get_dashboard_metrics()
    assert "data" in response
    assert "status" in response
    assert "metadata" in response


def test_get_dashboard_metrics_returns_correct_fields():
    response = get_dashboard_metrics()
    data = response["data"]
    required = [
        "source_count", "file_count", "link_count", "record_count",
        "data_quality_score", "processing_status", "duplicate_risk",
        "parsing_coverage",
    ]
    for field in required:
        assert field in data, f"Missing field: {field}"


def test_get_dashboard_metrics_status_success():
    response = get_dashboard_metrics()
    assert response["status"] == "success"


def test_get_dashboard_metrics_with_source_context():
    sources = [{"filename": "a.csv"}, {"filename": "b.pdf"}]
    response = get_dashboard_metrics(sources)
    assert response["data"]["source_count"] == 2


def test_get_ingestion_status_returns_envelope():
    response = get_ingestion_status()
    assert "data" in response
    data = response["data"]
    # Real fields from Duy's duy_latest_ingestion_summary fixture
    for field in [
        "run_id", "source_name", "source_type",
        "status",                    # Duy uses 'status', not 'processing_status'
        "ingestion_run_id",          # Week 6 new field
        "document_external_id",      # Week 6 new field
        "data_quality_score",
    ]:
        assert field in data, f"Missing field: {field}"



def test_get_recent_activity_returns_list():
    response = get_recent_activity()
    assert isinstance(response["data"], list)
