"""
Week 7 prediction feedback contract tests.
"""

from demo.services.service_client import submit_prediction_correction


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
