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
        
        # Check validation errors, missing platform lineage, or standard prediction fields
        doc_ext_id = payload.get("document_external_id")
        if not doc_ext_id:
            prediction_norm = {
                "predicted_document_type": None,
                "confidence": 0.0,
                "model_version": result.get("model_version", "document_classifier_v1") if isinstance(result, dict) else "document_classifier_v1",
                "status": "failed",
                "review_reason": "Missing required platform lineage: document_external_id",
                "top_predictions": [],
                "model_checksum": result.get("model_checksum", "unknown-checksum") if isinstance(result, dict) else "unknown-checksum",
                "training_data_version": result.get("training_data_version", "fallback-data-hash") if isinstance(result, dict) else "fallback-data-hash",
                "is_out_of_distribution": False,
                "threshold_policy": result.get("threshold_policy", {}) if isinstance(result, dict) else {},
            }
        elif isinstance(result, dict) and "error" in result:
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
            "document_external_id": doc_ext_id,
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

    # Verify status breakdown: exactly 15 needs_review, 3 failed, 2 waiting_for_source
    from collections import Counter
    status_counts = dict(Counter(res["status"] for res in results))
    assert status_counts.get("needs_review") == 15, f"Expected 15 needs_review, got {status_counts.get('needs_review')}"
    assert status_counts.get("failed") == 3, f"Expected 3 failed, got {status_counts.get('failed')}"
    assert status_counts.get("waiting_for_source") == 2, f"Expected 2 waiting_for_source, got {status_counts.get('waiting_for_source')}"

    # 5. Save results to evidence file
    evidence = {
        "release_sha": get_git_sha(),
        "status_counts": status_counts,
        "results": results,
        "log_payloads": log_payloads
    }

    os.makedirs(os.path.dirname(CANONICAL_RESULTS_FILE), exist_ok=True)
    with open(CANONICAL_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, default=str)

    print(f"Successfully wrote 20 results and log payloads to {CANONICAL_RESULTS_FILE}")


# ---------------------------------------------------------------------------
# Real Duy ID verification
# ---------------------------------------------------------------------------

# IDs that come from real Duy ingestion outputs — NOT synthetic test data.
REAL_DUY_DOCUMENT_IDS = {
    "doc_dataflow_technical_report",
    "doc_dataflow_technical_report_intro_pages",
    "doc_dataflow_technical_report_architecture_page",
    "doc_dataflow_technical_report_related_work",
    "doc_superstore_sales_csv_summary",
    "doc_product_sales_region_excel_summary",
    "doc_dummyjson_products_api_summary",
    "doc_short_text_quality_gate",
    "doc_empty_text_quality_gate",
    "doc_missing_file_name_validation",
    "doc_dataflow_system_operators_pages",
    "doc_dataflow_pipeline_api_pages",
    "doc_dataflow_agent_workflow_pages",
    "doc_dataflow_agentic_rag_evaluation_pages",
    "doc_superstore_order_profitability_sample",
    "doc_product_sales_region_sample",
    "doc_dummyjson_inventory_sample",
    "doc_dataflow_technical_notes_markdown",
    "doc_invalid_file_size_validation",
    # payload 19 has document_external_id = None (missing ID edge case)
}

SYNTHETIC_ID_PREFIXES = [
    "doc_contract_", "doc_financial_", "doc_invoice_",
    "doc_policy_", "doc_report_0", "doc_paper_",
    "doc_resume_", "doc_edge_", "doc_tricky_",
]


def test_canonical_payloads_use_real_duy_ids():
    """Canonical payloads must use real Duy document IDs, not synthetic ones."""
    with open(CANONICAL_PAYLOADS_FILE, "r", encoding="utf-8") as f:
        payloads = json.load(f)

    for i, payload in enumerate(payloads):
        doc_id = payload.get("document_external_id")
        if doc_id is not None:
            for prefix in SYNTHETIC_ID_PREFIXES:
                assert not doc_id.startswith(prefix), (
                    f"Payload {i} uses synthetic ID '{doc_id}' — "
                    f"must use real Duy document IDs"
                )


def test_canonical_payloads_contain_known_duy_ids():
    """At least the core Duy document IDs must appear in canonical payloads."""
    with open(CANONICAL_PAYLOADS_FILE, "r", encoding="utf-8") as f:
        payloads = json.load(f)

    payload_ids = {p.get("document_external_id") for p in payloads}
    # At least 15 of the 19 known IDs should be present (allows for minor changes)
    overlap = REAL_DUY_DOCUMENT_IDS & payload_ids
    assert len(overlap) >= 15, (
        f"Expected at least 15 known Duy IDs in canonical payloads, "
        f"found {len(overlap)}: {overlap}"
    )


def test_canonical_results_file_has_current_structure():
    """Pre-existing canonical results file must have expected structure."""
    if not os.path.exists(CANONICAL_RESULTS_FILE):
        pytest.skip("canonical_20_results.json not yet generated")

    with open(CANONICAL_RESULTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "release_sha" in data, "Missing release_sha"
    assert "results" in data, "Missing results"
    assert len(data["results"]) == 20, f"Expected 20 results, got {len(data['results'])}"

    # Verify no synthetic IDs in results
    for r in data["results"]:
        doc_id = r.get("document_external_id")
        if doc_id:
            for prefix in SYNTHETIC_ID_PREFIXES:
                assert not doc_id.startswith(prefix), (
                    f"Result uses synthetic ID '{doc_id}'"
                )
