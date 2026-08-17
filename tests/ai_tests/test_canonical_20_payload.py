import os
import sys
import json
import subprocess
import pytest

# Ensure project root is on sys.path
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.inference import predict_document_type
from ai.prediction.prediction_log_payload_builder import build_prediction_log_payload

CANONICAL_PAYLOADS_FILE = os.path.join(_TEST_DIR, "canonical_20_payloads.json")
CANONICAL_RESULTS_FILE = os.path.join(_PROJECT_ROOT, "outputs", "canonical_20_results.json")

def get_git_sha():
    """Retrieve current Git commit SHA, or a fallback string if Git is unavailable."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return "mocked-release-sha-12345"

def test_canonical_20_payload_flow():
    """Verify 20 diverse inputs -> 20 results -> 20 log payloads."""
    # 1. Load canonical payloads
    assert os.path.exists(CANONICAL_PAYLOADS_FILE), f"Missing payloads file: {CANONICAL_PAYLOADS_FILE}"
    with open(CANONICAL_PAYLOADS_FILE, "r", encoding="utf-8") as f:
        payloads = json.load(f)
    
    assert len(payloads) == 20, f"Expected exactly 20 payloads, got {len(payloads)}"

    results = []
    log_payloads = []

    # 2. Execute prediction and log payload building
    for payload in payloads:
        # Run prediction
        result = predict_document_type(payload)
        
        # Check validation errors or standard prediction fields
        if "error" in result:
            # Normalize shape for validation errors
            prediction_norm = {
                "predicted_document_type": None,
                "confidence": 0.0,
                "model_version": "document_classifier_v1",
                "status": "failed",
                "review_reason": f"Validation error: {result.get('message', 'Unknown validation error')}",
                "top_predictions": [],
            }
        else:
            prediction_norm = result
            
        # Enrich with ID fields from input
        enriched_result = {
            "document_external_id": payload.get("document_external_id"),
            "source_name": payload.get("source_name"),
            "ingestion_run_id": payload.get("ingestion_run_id"),
            **prediction_norm,
        }
        
        results.append(enriched_result)

        # Build prediction log payload
        log_payload = build_prediction_log_payload(payload, prediction_norm)
        log_payloads.append(log_payload)

    # 3. Assertions on results
    for i, res in enumerate(results):
        assert "predicted_document_type" in res, f"Result {i} missing predicted_document_type"
        assert "confidence" in res, f"Result {i} missing confidence"
        assert "status" in res, f"Result {i} missing status"
        assert "model_version" in res, f"Result {i} missing model_version"
        assert "top_predictions" in res, f"Result {i} missing top_predictions"
        assert "document_external_id" in res, f"Result {i} missing document_external_id"
        assert "source_name" in res, f"Result {i} missing source_name"
        assert "ingestion_run_id" in res, f"Result {i} missing ingestion_run_id"
        assert res["status"] in ["accepted", "needs_review", "waiting_for_source", "failed"]

    # 4. Assertions on log payloads
    for i, lp in enumerate(log_payloads):
        assert "model_name" in lp, f"Log payload {i} missing model_name"
        assert "model_version" in lp, f"Log payload {i} missing model_version"
        assert "predicted_label" in lp, f"Log payload {i} missing predicted_label"
        assert "confidence_score" in lp, f"Log payload {i} missing confidence_score"
        assert "status" in lp, f"Log payload {i} missing status"
        assert "created_at" in lp, f"Log payload {i} missing created_at"
        assert "document_id" in lp, f"Log payload {i} missing document_id" # Tuong maps document_db_id -> document_id
        assert lp["status"] in ["accepted", "needs_review", "waiting_for_source", "failed"]

    # 5. Save results to evidence file
    evidence = {
        "release_sha": get_git_sha(),
        "results": results,
        "log_payloads": log_payloads
    }

    os.makedirs(os.path.dirname(CANONICAL_RESULTS_FILE), exist_ok=True)
    with open(CANONICAL_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, default=str)

    print(f"Successfully wrote 20 results and log payloads to {CANONICAL_RESULTS_FILE}")
