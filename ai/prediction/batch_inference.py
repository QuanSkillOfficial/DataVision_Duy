"""
batch_inference.py — Batch prediction for multiple documents.

Usage:
    from ai.prediction.batch_inference import predict_document_types

    results = predict_document_types([payload1, payload2, payload3])
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

from ai.prediction.feature_builder import (
    STATUS_FAILED,
    STATUS_ACCEPTED,
    STATUS_NEEDS_REVIEW,
    STATUS_WAITING_FOR_SOURCE,
)
from ai.prediction.inference import predict_document_type, MODEL_PATH, _load_model
from ai.prediction.config import STAGING_ACCEPTANCE_THRESHOLD, REVIEW_THRESHOLD, MIN_EXTRACTED_TEXT_LENGTH



# ---------------------------------------------------------------------------
# Batch prediction
# ---------------------------------------------------------------------------

def predict_document_types(
    payloads: list[dict],
    *,
    model_path: str = MODEL_PATH,
) -> list[dict]:
    """
    Predict document types for a batch of input payloads.

    Parameters
    ----------
    payloads : list[dict]
        List of input payloads, each containing the fields defined in
        feature_builder.REQUIRED_FIELDS plus optional ID fields:
        document_external_id, document_db_id, source_id, source_name,
        ingestion_run_id.
    model_path : str
        Path to the .joblib model package.

    Returns
    -------
    list[dict]
        List of prediction results. Each result includes:
            - document_external_id (from input, or None)
            - source_name (from input, or None)
            - ingestion_run_id (from input, or None)
            - predicted_document_type
            - confidence
            - status
            - top_predictions
            - model_version
            - review_reason (if applicable)

    Notes
    -----
    Validation errors from predict_document_type() are normalized into
    the same shape as successful predictions with status='failed', so
    downstream consumers never need special error handling.
    """
    results: list[dict] = []

    for payload in payloads:
        try:
            prediction = predict_document_type(payload, model_path=model_path)
        except Exception as e:
            prediction = {
                "predicted_document_type": None,
                "confidence": 0.0,
                "model_version": "document_classifier_v1",
                "status": STATUS_FAILED,
                "review_reason": f"Prediction failed: {str(e)}",
                "top_predictions": [],
            }

        # Normalize validation errors into uniform shape
        if "error" in prediction:
            try:
                pkg = _load_model(model_path)
                model_version = pkg.get("model_version", "document_classifier_v1")
                model_checksum = pkg.get("model_checksum", "unknown-checksum")
                training_data_version = pkg.get("training_data_version", "fallback-data-hash")
            except Exception:
                model_version = "document_classifier_v1"
                model_checksum = "unknown-checksum"
                training_data_version = "fallback-data-hash"

            prediction = {
                "predicted_document_type": None,
                "confidence": 0.0,
                "model_version": model_version,
                "status": STATUS_FAILED,
                "review_reason": f"Validation error: {prediction.get('message', 'Unknown validation error')}",
                "top_predictions": [],
                "model_checksum": model_checksum,
                "training_data_version": training_data_version,
                "is_out_of_distribution": False,
                "threshold_policy": {
                    "staging_acceptance_threshold": STAGING_ACCEPTANCE_THRESHOLD,
                    "review_threshold": REVIEW_THRESHOLD,
                    "min_extracted_text_length": MIN_EXTRACTED_TEXT_LENGTH
                }
            }

        # Enrich with ID fields from input
        doc_ext_id = payload.get("document_external_id")
        if not doc_ext_id:
            prediction.update({
                "predicted_document_type": None,
                "confidence": 0.0,
                "status": STATUS_FAILED,
                "top_predictions": [],
                "review_reason": "Missing required platform lineage: document_external_id",
                "is_out_of_distribution": False,
            })

        result = {
            "document_external_id": doc_ext_id,
            "source_name": payload.get("source_name"),
            "ingestion_run_id": payload.get("ingestion_run_id"),
            **prediction,
        }

        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    sample_payloads = [
        {
            "document_external_id": "doc_dataflow_technical_report",
            "source_name": "dataflow_technical_report_pdf",
            "ingestion_run_id": "a58bf6df-2dec-41ca-a18b-784c68eab826",
            "file_name": "DataFlow_Technical_Report.pdf",
            "file_type": "pdf",
            "file_size": 2857707,
            "text_length": 129028,
            "num_pages": 36,
            "source_system": "manual_upload",
            "extracted_text": (
                "This policy explains the rules for access control, "
                "responsibilities, approval process, and compliance review."
            ),
        },
        {
            "document_external_id": "doc_superstore_sales_2024",
            "source_name": "superstore_sales_csv",
            "ingestion_run_id": "run-csv-002",
            "file_name": "Superstore_Sales_2024.csv",
            "file_type": "csv",
            "file_size": 1500000,
            "text_length": 5200,
            "num_pages": 0,
            "source_system": "manual_upload",
            "extracted_text": (
                "Invoice #12345. Date: 2024-01-15. Amount: $5,000.00. "
                "Payment due: 30 days. Bill to: ABC Corp."
            ),
        },
        {
            "document_external_id": "doc_empty_scan",
            "source_name": "empty_scan_pdf",
            "ingestion_run_id": "run-pdf-005",
            "file_name": "short.txt",
            "file_type": "txt",
            "file_size": 20,
            "text_length": 5,
            "num_pages": 1,
            "source_system": "manual_upload",
            "extracted_text": "hi",
        },
    ]

    print("=== Batch Inference Demo ===\n")
    results = predict_document_types(sample_payloads)
    print(json.dumps(results, indent=2, default=str))
