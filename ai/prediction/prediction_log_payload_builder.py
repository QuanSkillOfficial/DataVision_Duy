"""
prediction_log_payload_builder.py — Build database-ready prediction log payloads.

This module transforms the prediction input and output into a payload
that can be inserted directly into Phat's `prediction_logs` table.

Usage:
    from ai.prediction.prediction_log_payload_builder import build_prediction_log_payload

    log_payload = build_prediction_log_payload(input_payload, prediction_result)
"""

import os
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Resolve project root
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.feature_builder import MODEL_NAME


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------

def build_prediction_log_payload(
    input_payload: dict,
    prediction_result: dict,
) -> dict:
    """
    Build a prediction log payload for insertion into the prediction_logs table.

    Parameters
    ----------
    input_payload : dict
        The original input sent to the prediction model.
        May contain document_external_id, document_db_id, source_id,
        source_name, ingestion_run_id, and all feature fields.
    prediction_result : dict
        The prediction output from predict_document_type() or classify_document().

    Returns
    -------
    dict
        A database-ready payload with the following fields:
            - source_id (INTEGER, from Phat DB sources.id)
            - document_external_id (VARCHAR, Duy document key)
            - document_db_id (INTEGER, from Phat DB documents.id)
            - model_name
            - model_version
            - input_payload (full input for traceability)
            - prediction_result (top_predictions list)
            - predicted_label
            - confidence_score
            - status
            - review_reason
            - ingestion_run_id (UUID, Duy ingestion execution ID)
            - created_at
    """
    # Extract IDs from input (may come from ingestion / Phat DB)
    source_id = input_payload.get("source_id")                       # INTEGER, Phat DB
    document_external_id = input_payload.get("document_external_id") # VARCHAR, Duy key
    document_id = input_payload.get("document_db_id")                # INTEGER, Phat DB (Tuong uses document_db_id internally, mapped to document_id)
    ingestion_run_id = input_payload.get("ingestion_run_id")         # UUID, Duy
    source_name = input_payload.get("source_name")                   # VARCHAR, Duy slug

    # Build the log payload matching prediction_logs schema
    log_payload = {
        "source_id": source_id,
        "document_external_id": document_external_id,
        "document_id": document_id,
        "model_name": MODEL_NAME,
        "model_version": prediction_result.get("model_version", "unknown"),
        "input_payload": _sanitize_input_payload(input_payload),
        "prediction_result": {
            "top_predictions": prediction_result.get("top_predictions", []),
        },
        "predicted_label": prediction_result.get("predicted_document_type"),
        "confidence_score": prediction_result.get("confidence", 0.0),
        "status": prediction_result.get("status", "failed"),
        "review_reason": prediction_result.get("review_reason"),
        "ingestion_run_id": ingestion_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return log_payload


def _sanitize_input_payload(input_payload: dict) -> dict:
    """
    Create a clean copy of the input payload for storage.
    Removes overly long extracted_text to save storage (keeps first 500 chars).
    """
    sanitized = dict(input_payload)

    # Truncate extracted_text for storage efficiency
    if "extracted_text" in sanitized:
        text = str(sanitized["extracted_text"])
        if len(text) > 500:
            sanitized["extracted_text"] = text[:500] + "... [truncated]"

    return sanitized


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    sample_input = {
        "source_id": 4,
        "source_name": "dataflow_technical_report_pdf",
        "document_external_id": "doc_dataflow_technical_report",
        "document_db_id": 3,
        "ingestion_run_id": "a58bf6df-2dec-41ca-a18b-784c68eab826",
        "file_name": "DataFlow_Technical_Report.pdf",
        "file_type": "pdf",
        "file_size": 2857707,
        "text_length": 129028,
        "num_pages": 36,
        "source_system": "manual_upload",
        "extracted_text": "This policy explains the rules for access control...",
    }

    sample_prediction = {
        "predicted_document_type": "report",
        "confidence": 0.83,
        "model_version": "document_classifier_v1",
        "status": "accepted",
        "top_predictions": [
            {"label": "report", "score": 0.83},
            {"label": "policy_document", "score": 0.10},
            {"label": "contract", "score": 0.05},
        ],
        "review_reason": None,
    }

    log = build_prediction_log_payload(sample_input, sample_prediction)
    print("=== Prediction Log Payload ===")
    print(json.dumps(log, indent=2, default=str))
