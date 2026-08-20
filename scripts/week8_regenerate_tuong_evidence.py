"""
week8_regenerate_tuong_evidence.py — Regenerate all Tuong evidence files from real Duy payloads.

Replaces:
  1. tests/ai_tests/canonical_20_payloads.json   (synthetic → real Duy)
  2. outputs/canonical_20_results.json            (run prediction on real payloads)
  3. outputs/ui_fixtures/tuong_prediction_batch_response.json  (4 → 20 results)
  4. outputs/ui_fixtures/tuong_prediction_review_queue_sample.json (1 → all needs_review)
  5. outputs/ui_fixtures/tuong_prediction_response_real.json (generic → real)

Usage:
    python scripts/week8_regenerate_tuong_evidence.py
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Resolve project root
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.inference import predict_document_type
from ai.prediction.prediction_log_payload_builder import build_prediction_log_payload
from ai.prediction.feature_builder import VALID_STATUSES

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
WEEK7_PAYLOADS_DIR = os.path.join(_PROJECT_ROOT, "outputs", "prediction_payloads", "week7")
CANONICAL_PAYLOADS_OUT = os.path.join(_PROJECT_ROOT, "tests", "ai_tests", "canonical_20_payloads.json")
CANONICAL_RESULTS_OUT = os.path.join(_PROJECT_ROOT, "outputs", "canonical_20_results.json")
UI_FIXTURES_DIR = os.path.join(_PROJECT_ROOT, "outputs", "ui_fixtures")
BATCH_FIXTURE_OUT = os.path.join(UI_FIXTURES_DIR, "tuong_prediction_batch_response.json")
REVIEW_QUEUE_OUT = os.path.join(UI_FIXTURES_DIR, "tuong_prediction_review_queue_sample.json")
SINGLE_FIXTURE_OUT = os.path.join(UI_FIXTURES_DIR, "tuong_prediction_response_real.json")

SUPPORTED_LABELS = [
    "contract", "financial_statement", "invoice",
    "policy_document", "report", "research_paper", "resume",
]


def get_git_sha():
    """Retrieve current Git commit SHA."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown-sha"


def load_real_payloads():
    """Load all 20 individual payload files from the week7 directory."""
    payloads = []
    files = sorted(f for f in os.listdir(WEEK7_PAYLOADS_DIR) if f.endswith(".json"))
    for fname in files:
        fpath = os.path.join(WEEK7_PAYLOADS_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            payload = json.load(f)
        payloads.append(payload)
    return payloads


def run_prediction_on_payloads(payloads):
    """Run prediction on each payload and return results + log payloads."""
    results = []
    log_payloads = []

    for i, payload in enumerate(payloads):
        result = predict_document_type(payload)

        if "error" in result:
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

        doc_id = payload.get("document_external_id") or "N/A"
        status = enriched_result.get("status", "unknown")
        conf = enriched_result.get("confidence", 0.0)
        pred = enriched_result.get("predicted_document_type") or "N/A"
        print(f"  [{i+1:2d}/20] {doc_id:<50s} -> {pred:<20s} conf={conf:.4f} status={status}")

    return results, log_payloads


def build_batch_fixture(results):
    """Build batch response fixture with all 20 results."""
    batch_results = []
    for result in results:
        entry = {
            "predicted_document_type": result.get("predicted_document_type"),
            "confidence": result.get("confidence", 0.0),
            "status": result.get("status"),
            "top_predictions": result.get("top_predictions", []),
            "review_reason": result.get("review_reason"),
            "manual_review_required": result.get("status") == "needs_review",
            "fixture_only": False,
            "document_external_id": result.get("document_external_id"),
            "document_db_id": result.get("document_db_id"),
            "source_id": result.get("source_id"),
            "source_name": result.get("source_name"),
            "ingestion_run_id": result.get("ingestion_run_id"),
            "model_version": result.get("model_version", "document_classifier_v1"),
        }
        batch_results.append(entry)

    # Check which statuses are covered by real results
    covered_statuses = {r["status"] for r in batch_results}
    missing_statuses = set(VALID_STATUSES) - covered_statuses

    # Add synthetic status_examples only for statuses not covered by real data
    status_examples = []
    if "accepted" in missing_statuses:
        status_examples.append({
            "predicted_document_type": "report",
            "confidence": 0.92,
            "status": "accepted",
            "top_predictions": [{"label": "report", "score": 0.92}],
            "review_reason": None,
            "manual_review_required": False,
            "fixture_only": True,
            "fixture_reason": "Synthetic example to cover 'accepted' status not present in current model results",
            "document_external_id": "fixture_accepted_example",
            "document_db_id": None,
            "source_id": None,
            "source_name": "fixture_source",
            "ingestion_run_id": "fixture-run-id",
            "model_version": "document_classifier_v1",
        })
    if "waiting_for_source" in missing_statuses:
        status_examples.append({
            "predicted_document_type": None,
            "confidence": 0.0,
            "status": "waiting_for_source",
            "top_predictions": [],
            "review_reason": "Extracted text is missing or too short",
            "manual_review_required": False,
            "fixture_only": True,
            "fixture_reason": "Synthetic example to cover 'waiting_for_source' status",
            "document_external_id": "fixture_waiting_example",
            "document_db_id": None,
            "source_id": None,
            "source_name": "fixture_source",
            "ingestion_run_id": "fixture-run-id",
            "model_version": "document_classifier_v1",
        })

    fixture = {"results": batch_results}
    if status_examples:
        fixture["status_examples"] = status_examples

    return fixture


def build_review_queue_fixture(results):
    """Build review queue from all needs_review items."""
    review_items = []
    for result in results:
        if result.get("status") != "needs_review":
            continue
        item = {
            "predicted_document_type": result.get("predicted_document_type"),
            "confidence": result.get("confidence", 0.0),
            "status": "needs_review",
            "top_predictions": result.get("top_predictions", []),
            "review_reason": result.get("review_reason"),
            "manual_review_required": True,
            "document_external_id": result.get("document_external_id"),
            "document_db_id": result.get("document_db_id"),
            "source_id": result.get("source_id"),
            "source_name": result.get("source_name"),
            "ingestion_run_id": result.get("ingestion_run_id"),
            "model_version": result.get("model_version", "document_classifier_v1"),
            "reviewed": False,
            "corrected_document_type": None,
            "corrected_by": None,
        }
        review_items.append(item)

    return {
        "review_items": review_items,
        "supported_document_types": SUPPORTED_LABELS,
    }


def build_single_fixture(results):
    """Build single response fixture from first real result with a prediction."""
    for result in results:
        if result.get("predicted_document_type") is not None:
            return {
                "response": {
                    "predicted_document_type": result["predicted_document_type"],
                    "confidence": result.get("confidence", 0.0),
                    "status": result.get("status"),
                    "top_predictions": result.get("top_predictions", []),
                    "review_reason": result.get("review_reason"),
                    "manual_review_required": result.get("status") == "needs_review",
                    "document_external_id": result.get("document_external_id"),
                    "document_db_id": result.get("document_db_id"),
                    "source_id": result.get("source_id"),
                    "source_name": result.get("source_name"),
                    "ingestion_run_id": result.get("ingestion_run_id"),
                    "model_version": result.get("model_version", "document_classifier_v1"),
                }
            }
    raise ValueError("No valid prediction result found")


def main():
    print("=" * 70)
    print("Week 8: Regenerate Tuong evidence from real Duy payloads")
    print("=" * 70)

    release_sha = get_git_sha()
    print(f"\nRelease SHA: {release_sha}")

    # 1. Load real payloads
    print(f"\n[1/5] Loading real Duy payloads from {WEEK7_PAYLOADS_DIR}")
    payloads = load_real_payloads()
    assert len(payloads) == 20, f"Expected 20 payloads, got {len(payloads)}"
    print(f"  Loaded {len(payloads)} payloads")

    # 2. Save as canonical payloads
    print(f"\n[2/5] Writing canonical payloads -> {CANONICAL_PAYLOADS_OUT}")
    with open(CANONICAL_PAYLOADS_OUT, "w", encoding="utf-8") as f:
        json.dump(payloads, f, indent=2, default=str, ensure_ascii=False)
    print(f"  Wrote {len(payloads)} payloads")

    # 3. Run prediction
    print("\n[3/5] Running prediction on all 20 payloads...")
    results, log_payloads = run_prediction_on_payloads(payloads)
    assert len(results) == 20, f"Expected 20 results, got {len(results)}"
    assert len(log_payloads) == 20, f"Expected 20 log payloads, got {len(log_payloads)}"

    # Status breakdown
    status_counts = {}
    for r in results:
        s = r.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
    print(f"\n  Status breakdown: {status_counts}")

    # Save canonical results
    print("\n[4/5] Writing evidence files...")
    evidence = {
        "release_sha": release_sha,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_results": len(results),
        "total_log_payloads": len(log_payloads),
        "status_breakdown": status_counts,
        "results": results,
        "log_payloads": log_payloads,
    }
    with open(CANONICAL_RESULTS_OUT, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, default=str, ensure_ascii=False)
    print(f"  canonical_20_results.json ({len(results)} results, SHA={release_sha[:8]})")

    # Build and save UI fixtures
    batch_fixture = build_batch_fixture(results)
    with open(BATCH_FIXTURE_OUT, "w", encoding="utf-8") as f:
        json.dump(batch_fixture, f, indent=2, default=str, ensure_ascii=False)
    print(f"  tuong_prediction_batch_response.json ({len(batch_fixture['results'])} results)")

    review_queue = build_review_queue_fixture(results)
    with open(REVIEW_QUEUE_OUT, "w", encoding="utf-8") as f:
        json.dump(review_queue, f, indent=2, default=str, ensure_ascii=False)
    print(f"  tuong_prediction_review_queue_sample.json ({len(review_queue['review_items'])} review items)")

    single_fixture = build_single_fixture(results)
    with open(SINGLE_FIXTURE_OUT, "w", encoding="utf-8") as f:
        json.dump(single_fixture, f, indent=2, default=str, ensure_ascii=False)
    print("  tuong_prediction_response_real.json")

    # Summary
    print("\n[5/5] Summary")
    print(f"  Release SHA:       {release_sha}")
    print(f"  Total results:     {len(results)}")
    print(f"  Total log payloads:{len(log_payloads)}")
    print(f"  Batch fixture:     {len(batch_fixture['results'])} results")
    needs_review_count = len(review_queue["review_items"])
    print(f"  Review queue:      {needs_review_count} items")
    print(f"  Status breakdown:  {status_counts}")

    # Assertions
    assert len(results) == 20
    assert len(log_payloads) == 20
    assert len(batch_fixture["results"]) == 20
    assert needs_review_count > 0, "Expected at least some needs_review items"

    # Verify no synthetic IDs leaked
    for r in results:
        doc_id = r.get("document_external_id")
        if doc_id:
            assert not doc_id.startswith("doc_contract_"), f"Synthetic ID leaked: {doc_id}"
            assert not doc_id.startswith("doc_financial_"), f"Synthetic ID leaked: {doc_id}"

    print("\nAll evidence files regenerated successfully from real Duy payloads")


if __name__ == "__main__":
    main()
