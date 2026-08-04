"""
run_real_payloads.py — Run prediction on real Duy payloads from JSON file.

Usage:
    python scripts/run_real_payloads.py --input outputs/prediction_payloads/tuong_week7_prediction_payloads.json
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.batch_inference import predict_document_types

def validate_payload(payload):
    """Validate all required fields per Task 2."""
    required = [
        "source_id",
        "document_external_id",
        "document_db_id",
        "ingestion_run_id",
        "file_name",
        "file_type",
        "data_quality_score",
        "file_hash_sha256"
    ]
    for req in required:
        if req not in payload:
            print(f"Warning: Payload missing {req}")
    if "extracted_text" not in payload:
        print("Warning: Payload missing extracted_text (may trigger waiting_for_source)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Path to the input JSON file")
    args = parser.parse_args()

    payloads_file = os.path.abspath(args.input)
    with open(payloads_file, "r", encoding="utf-8") as f:
        duy_payloads = json.load(f)

    timestamp = datetime.now(timezone.utc).isoformat()

    print(f"Loaded {len(duy_payloads)} payloads from {payloads_file}")

    for p in duy_payloads:
        validate_payload(p)

    # Run batch prediction
    results = predict_document_types(duy_payloads)

    # Enrichment as per Task 4 output requirements
    enriched_results = []
    for payload, result in zip(duy_payloads, results):
        enriched = {
            "predicted_document_type": result.get("predicted_document_type"),
            "confidence": result.get("confidence"),
            "top_predictions": result.get("top_predictions"),
            "status": result.get("status"),
            "review_reason": result.get("review_reason"),
            "source_id": payload.get("source_id"),
            "source_name": payload.get("source_name"),
            "document_external_id": payload.get("document_external_id"),
            "document_db_id": payload.get("document_db_id"),
            "ingestion_run_id": payload.get("ingestion_run_id"),
            "model_name": "document_classifier",
            "model_version": result.get("model_version"),
            "created_at": timestamp
        }
        enriched_results.append(enriched)

    # Compute summary
    status_counts = {"accepted": 0, "needs_review": 0, "waiting_for_source": 0, "failed": 0}
    for r in enriched_results:
        status = r.get("status", "failed")
        status_counts[status] = status_counts.get(status, 0) + 1

    # Write results
    output_path = os.path.join(_PROJECT_ROOT, "outputs", "week7_duy_prediction_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_results, f, indent=2, default=str)

    # Print summary
    print(f"=== Week 7 Real Payload Evaluation Results ===")
    print(f"Total payloads: {len(duy_payloads)}")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    print(f"\nResults written to: {output_path}")

if __name__ == "__main__":
    main()
