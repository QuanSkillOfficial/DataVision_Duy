"""
prediction_service.py — Service wrapper for document type prediction.

This module provides the top-level API functions that will be called by
the REST endpoints:

    POST /api/predict/document-type        → classify_document()
    POST /api/predict/document-type/batch  → classify_documents()

Usage:
    from ai.prediction.prediction_service import classify_document, classify_documents
"""

import os
import sys

# ---------------------------------------------------------------------------
# Resolve project root
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.inference import predict_document_type
from ai.prediction.batch_inference import predict_document_types


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def classify_document(payload: dict) -> dict:
    """
    Classify a single document.

    Wraps predict_document_type() for use by the API layer.

    Parameters
    ----------
    payload : dict
        Document metadata and extracted text.

    Returns
    -------
    dict
        Prediction result with predicted_document_type, confidence,
        status, top_predictions, model_version, and review_reason.
    """
    return predict_document_type(payload)


def classify_documents(payloads: list[dict]) -> list[dict]:
    """
    Classify multiple documents in batch.

    Wraps predict_document_types() for use by the API layer.

    Parameters
    ----------
    payloads : list[dict]
        List of document payloads.

    Returns
    -------
    list[dict]
        List of prediction results, each enriched with document_id and source_id.
    """
    return predict_document_types(payloads)


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    # Single prediction
    single_payload = {
        "file_name": "policy_doc.pdf",
        "file_type": "pdf",
        "file_size": 240000,
        "text_length": 4200,
        "num_pages": 4,
        "source_system": "manual_upload",
        "extracted_text": (
            "This policy explains the rules for access control, "
            "responsibilities, approval process, and compliance review."
        ),
    }

    print("=== Single Classification ===")
    result = classify_document(single_payload)
    print(json.dumps(result, indent=2, default=str))

    # Batch prediction
    batch_payloads = [
        {**single_payload, "document_id": "doc-001", "source_id": "src-001"},
        {
            "document_id": "doc-002",
            "source_id": "src-002",
            "file_name": "financial_q4_2024.xlsx",
            "file_type": "xlsx",
            "file_size": 120000,
            "text_length": 3500,
            "num_pages": 5,
            "source_system": "sharepoint",
            "extracted_text": (
                "Q4 2024 Financial Statement. Revenue: $2.5M. "
                "Net Income: $450K. Total Assets: $10M. "
                "Balance sheet and income statement summary."
            ),
        },
    ]

    print("\n=== Batch Classification ===")
    results = classify_documents(batch_payloads)
    print(json.dumps(results, indent=2, default=str))
