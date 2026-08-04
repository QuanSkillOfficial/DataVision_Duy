"""
Week 7 backend client error handling tests.
"""

from unittest.mock import Mock

import requests

from demo.services import backend_client


def test_backend_client_handles_connection_error(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(backend_client.requests, "get", raise_connection_error)
    response = backend_client.get_recent_activity()
    assert response["status"] == "error"
    assert response["data"] is None
    assert response["error"]["message"] == "Backend unavailable"


def test_backend_client_handles_timeout(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise requests.Timeout("timed out")

    monkeypatch.setattr(backend_client.requests, "post", raise_timeout)
    response = backend_client.ask_rag("What is DataFlow?")
    assert response["status"] == "error"
    assert response["error"]["message"] == "Backend request timed out"


def test_backend_client_handles_invalid_json(monkeypatch):
    response_mock = Mock(status_code=200)
    response_mock.json.side_effect = ValueError("bad json")
    monkeypatch.setattr(backend_client.requests, "get", lambda *a, **k: response_mock)

    response = backend_client.get_recent_activity()
    assert response["status"] == "error"
    assert response["error"]["message"] == "Backend returned invalid JSON"


def test_backend_client_handles_missing_envelope(monkeypatch):
    response_mock = Mock(status_code=200)
    response_mock.json.return_value = {"items": []}
    monkeypatch.setattr(backend_client.requests, "post", lambda *a, **k: response_mock)

    response = backend_client.generate_report({})
    assert response["status"] == "error"
    assert "missing required fields" in response["error"]["message"]


def test_backend_client_uses_week7_prediction_route(monkeypatch):
    seen = {}
    response_mock = Mock(status_code=200)
    response_mock.json.return_value = {"data": {}, "status": "success", "metadata": {}}

    def fake_post(url, json=None, timeout=None):
        seen["url"] = url
        return response_mock

    monkeypatch.setattr(backend_client.requests, "post", fake_post)
    backend_client.classify_document({"file_name": "x.pdf"})
    assert seen["url"].endswith("/api/predict/document-type")
