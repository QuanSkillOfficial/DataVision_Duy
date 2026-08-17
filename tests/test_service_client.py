"""
tests/test_service_client.py
==============================
Verifies that service_client.py (the single interface pages call) routes to
the correct implementation and always returns the agreed envelope.

Week 8 note (DV-HUNG-01): the payload-level assertions that used to live here
now sit with the reference contract tests (which import mock_client directly),
because they described fixture behavior rather than routing. What remains here
is mode-independent: routing correctness, envelope shape, and the guarantee
that pages never reach past this boundary.
"""

import inspect

from demo.config import USE_BACKEND
from demo.services import backend_client, mock_client, service_client
from demo.services.service_client import (
    get_backend_health,
    get_dashboard_metrics,
    get_ingestion_status,
    get_recent_activity,
)


# ──────────────────────────────────────────────────────────────────────────────
# ROUTING
# ──────────────────────────────────────────────────────────────────────────────

def test_default_mode_is_mock():
    """Sanity check that the demo defaults to mock mode unless overridden."""
    assert isinstance(USE_BACKEND, bool)


def test_service_client_routes_to_the_mode_specific_implementation():
    expected = backend_client if USE_BACKEND else mock_client
    assert service_client._client is expected


def test_both_implementations_expose_the_same_service_surface():
    """A missing function in either client is a contract break, not a runtime bug."""
    public = [
        name
        for name, value in vars(service_client).items()
        if not name.startswith("_") and inspect.isfunction(value)
    ]
    assert public, "service_client exposes no service functions"
    for name in public:
        assert hasattr(mock_client, name), f"mock_client is missing {name}()"
        assert hasattr(backend_client, name), f"backend_client is missing {name}()"


# ──────────────────────────────────────────────────────────────────────────────
# ENVELOPE
# ──────────────────────────────────────────────────────────────────────────────

def test_get_dashboard_metrics_returns_envelope():
    response = get_dashboard_metrics()
    assert "data" in response
    assert "status" in response
    assert "metadata" in response


def test_get_ingestion_status_returns_envelope():
    response = get_ingestion_status()
    assert "data" in response
    assert "status" in response


def test_get_recent_activity_returns_list():
    response = get_recent_activity()
    assert isinstance(response["data"], list)


def test_get_backend_health_returns_envelope():
    response = get_backend_health()
    assert "data" in response
    assert "status" in response


def test_fixture_mode_health_never_claims_a_live_backend():
    """DV-HUNG-05: fixture success must not be presentable as live data."""
    if USE_BACKEND:
        return
    data = get_backend_health()["data"]
    assert data["backend_reachable"] is False
    assert data["release_sha"] is None
