"""
Week 7 prediction feedback contract tests.

Week 8 note (DV-HUNG-01): this module imports the fixture implementation
directly instead of `service_client`. These tests pin the reference UI
contract - the shape and business rules the UI requires from any backend - so
they must produce the same result in fixture mode and in backend mode. Live
UI-to-backend integration is covered separately by
tests/test_backend_contract_smoke.py, which runs in backend mode only.
"""

from demo.services.mock_client import submit_prediction_correction


def test_week7_prediction_feedback_payload_is_accepted():
    payload = {
        "prediction_log_id": 12,
        "document_db_id": 1,
        "document_external_id": "doc_dataflow_technical_report",
        "original_prediction": "contract",
        "corrected_document_type": "report",
        "corrected_by": "reviewer",
        "correction_reason": "The document is a technical report, not a contract.",
    }
    response = submit_prediction_correction(payload)
    assert response["status"] == "success"
    assert response["data"]["success"] is True
    assert response["data"]["feedback_payload"]["original_prediction"] == "contract"


def test_prediction_feedback_requires_original_prediction():
    payload = {
        "prediction_log_id": 12,
        "document_external_id": "doc_dataflow_technical_report",
        "corrected_document_type": "report",
        "corrected_by": "reviewer",
        "correction_reason": "Correction reason.",
    }
    response = submit_prediction_correction(payload)
    assert response["status"] == "error"
    assert "original_prediction" in response["data"]["error"]
