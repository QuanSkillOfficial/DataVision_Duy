"""
Week 7 backend client error handling tests.

Week 8 note: every call now goes through a single `requests.request` entry
point so that failures are classified once (see demo/services/service_errors.py
and tests/test_service_error_contract.py). These tests patch that entry point,
which also guarantees they never touch a real network.
"""

import json
from unittest.mock import Mock

import requests

from demo.services import backend_client


def _patch_request(monkeypatch, handler):
    """Patch the single HTTP entry point used by every backend call."""
    monkeypatch.setattr(backend_client.requests, "request", handler)


def test_backend_client_handles_connection_error(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise requests.ConnectionError("connection refused")

    _patch_request(monkeypatch, raise_connection_error)
    response = backend_client.get_recent_activity()
    assert response["status"] == "error"
    assert response["data"] is None
    assert response["error"]["message"] == "Backend unavailable"


def test_backend_client_handles_timeout(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise requests.Timeout("timed out")

    _patch_request(monkeypatch, raise_timeout)
    response = backend_client.ask_rag("What is DataFlow?")
    assert response["status"] == "error"
    assert response["error"]["message"] == "Backend request timed out"


def test_backend_client_handles_invalid_json(monkeypatch):
    response_mock = Mock(status_code=200)
    response_mock.json.side_effect = ValueError("bad json")
    _patch_request(monkeypatch, lambda *a, **k: response_mock)

    response = backend_client.get_recent_activity()
    assert response["status"] == "error"
    assert response["error"]["message"] == "Backend returned invalid JSON"


def test_backend_client_handles_missing_envelope(monkeypatch):
    response_mock = Mock(status_code=200)
    response_mock.json.return_value = {"items": []}
    _patch_request(monkeypatch, lambda *a, **k: response_mock)

    response = backend_client.generate_report({})
    assert response["status"] == "error"
    assert "missing required fields" in response["error"]["message"]


def test_backend_client_uses_week7_prediction_route(monkeypatch):
    seen = {}
    response_mock = Mock(status_code=200)
    response_mock.json.return_value = {"data": {}, "status": "success", "metadata": {}}

    def fake_request(method, url, **kwargs):
        seen["method"] = method
        seen["url"] = url
        return response_mock

    _patch_request(monkeypatch, fake_request)
    backend_client.classify_document({"file_name": "x.pdf"})
    assert seen["method"] == "POST"
    assert seen["url"].endswith("/api/predict/document-type")


def test_uploaded_file_bytes_do_not_break_json_serialisation(monkeypatch):
    """Regression: source_context carries raw file bytes under "content".

    Posting them raised TypeError and blanked the Dashboard page in backend
    mode. The transport now replaces binary content with its size.
    """
    seen = {}
    response_mock = Mock(status_code=200)
    response_mock.json.return_value = {"data": {}, "status": "success", "metadata": {}}

    def fake_request(method, url, **kwargs):
        seen["json"] = kwargs.get("json")
        return response_mock

    _patch_request(monkeypatch, fake_request)
    sources = [{"filename": "a.csv", "size": 12, "content": b"col\n1\n2\n3\n"}]
    response = backend_client.get_dashboard_metrics(sources)

    assert response["status"] == "success"
    sent_source = seen["json"]["source_context"][0]
    assert sent_source["filename"] == "a.csv"
    assert sent_source["content"] == {"omitted": "binary", "byte_length": 10}
    json.dumps(seen["json"])  # must not raise


def test_backend_client_uses_split_connect_and_read_timeouts(monkeypatch):
    """A dead host must fail on the connect timeout, not wait the full read timeout."""
    seen = {}
    response_mock = Mock(status_code=200)
    response_mock.json.return_value = {"data": {}, "status": "success", "metadata": {}}

    def fake_request(method, url, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        return response_mock

    _patch_request(monkeypatch, fake_request)
    backend_client.get_backend_health()

    connect_timeout, read_timeout = seen["timeout"]
    assert connect_timeout > 0
    assert read_timeout >= connect_timeout
