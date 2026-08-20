import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from collections import Counter

# Set root
try:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
except NameError:
    PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ai.prediction.inference import predict_document_type
from ai.prediction.prediction_log_payload_builder import build_prediction_log_payload


def get_git_sha(repo_path: str) -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "mocked-release-sha"


def regenerate_fixtures(repo_root: str):
    payloads_file = os.path.join(repo_root, "tests", "ai_tests", "canonical_20_payloads.json")
    with open(payloads_file, "r", encoding="utf-8") as f:
        payloads = json.load(f)

    results = []
    log_payloads = []

    for payload in payloads:
        result = predict_document_type(payload)
        doc_ext_id = payload.get("document_external_id")
        if not doc_ext_id:
            prediction_norm = {
                "predicted_document_type": None,
                "confidence": 0.0,
                "model_version": (
                    result.get("model_version", "document_classifier_v1")
                    if isinstance(result, dict)
                    else "document_classifier_v1"
                ),
                "status": "failed",
                "review_reason": "Missing required platform lineage: document_external_id",
                "top_predictions": [],
                "model_checksum": (
                    result.get("model_checksum", "unknown-checksum")
                    if isinstance(result, dict)
                    else "unknown-checksum"
                ),
                "training_data_version": (
                    result.get("training_data_version", "fallback-data-hash")
                    if isinstance(result, dict)
                    else "fallback-data-hash"
                ),
                "is_out_of_distribution": False,
                "threshold_policy": (
                    result.get("threshold_policy", {})
                    if isinstance(result, dict)
                    else {}
                ),
            }
        elif isinstance(result, dict) and "error" in result:
            err_msg = result.get("message", "Unknown validation error")
            prediction_norm = {
                "predicted_document_type": None,
                "confidence": 0.0,
                "model_version": "document_classifier_v1",
                "status": "failed",
                "review_reason": f"Validation error: {err_msg}",
                "top_predictions": [],
            }
        else:
            prediction_norm = result

        enriched_result = {
            "document_external_id": doc_ext_id,
            "source_name": payload.get("source_name"),
            "ingestion_run_id": payload.get("ingestion_run_id"),
            **prediction_norm,
        }
        # Add UI contract fields
        enriched_result["manual_review_required"] = (enriched_result.get("status") == "needs_review")
        enriched_result["fixture_only"] = False
        results.append(enriched_result)

        log_payload = build_prediction_log_payload(payload, prediction_norm)
        log_payloads.append(log_payload)

    status_counts = dict(Counter(res["status"] for res in results))
    release_sha = get_git_sha(repo_root)
    generated_at = datetime.now(timezone.utc).isoformat()

    # 1. canonical_20_results.json
    c20_data = {
        "release_sha": release_sha,
        "status_counts": status_counts,
        "results": results,
        "log_payloads": log_payloads,
    }
    c20_path = os.path.join(repo_root, "outputs", "canonical_20_results.json")
    os.makedirs(os.path.dirname(c20_path), exist_ok=True)
    with open(c20_path, "w", encoding="utf-8") as f:
        json.dump(c20_data, f, indent=2, default=str)

    # 2. tuong_prediction_batch_response.json
    # Build status examples for UI contract
    valid_statuses = ["accepted", "needs_review", "failed", "waiting_for_source"]
    by_status = {item["status"]: item for item in results if item.get("status") in valid_statuses}
    status_examples = []
    for st in valid_statuses:
        if st in by_status:
            status_examples.append(dict(by_status[st]))
        else:
            status_examples.append({
                "predicted_document_type": "research_paper",
                "confidence": 0.95,
                "status": st,
                "top_predictions": [
                    {"label": "research_paper", "score": 0.95},
                    {"label": "report", "score": 0.03},
                    {"label": "contract", "score": 0.02},
                ],
                "model_version": "document_classifier_v1",
                "document_external_id": f"doc_example_{st}",
                "document_db_id": 1,
                "source_id": 1,
                "source_name": "example_source",
                "ingestion_run_id": "example-run-id",
                "review_reason": None,
                "manual_review_required": (st == "needs_review"),
                "fixture_only": True,
                "fixture_reason": f"UI contract coverage only; current real 20-payload batch did not produce status={st}.",
            })

    batch_fixture = {
        "generated_at": generated_at,
        "release_sha": release_sha,
        "total_results": len(results),
        "status_counts": status_counts,
        "results": results,
        "status_examples": status_examples,
        "metadata": {
            "owner": "Tuong",
            "real_batch": True,
            "accepted_is_ground_truth": False,
            "acceptance_threshold": 0.80,
        },
    }
    batch_path = os.path.join(repo_root, "outputs", "ui_fixtures", "tuong_prediction_batch_response.json")
    os.makedirs(os.path.dirname(batch_path), exist_ok=True)
    with open(batch_path, "w", encoding="utf-8") as f:
        json.dump(batch_fixture, f, indent=2, default=str)

    # 3. tuong_prediction_review_queue_sample.json
    review_items = []
    for item in results:
        if item["status"] == "needs_review":
            r_item = dict(item)
            r_item.update({
                "prediction_log_id": None,
                "reviewed": False,
                "corrected_document_type": None,
                "corrected_by": None,
            })
            review_items.append(r_item)

    review_fixture = {
        "generated_at": generated_at,
        "release_sha": release_sha,
        "total_review_items": len(review_items),
        "review_items": review_items,
        "supported_document_types": [
            "contract",
            "financial_statement",
            "invoice",
            "policy_document",
            "report",
            "research_paper",
            "resume",
        ],
        "metadata": {
            "owner": "Tuong",
            "database_insert_status": "pending_database_connection",
        },
    }
    review_path = os.path.join(repo_root, "outputs", "ui_fixtures", "tuong_prediction_review_queue_sample.json")
    os.makedirs(os.path.dirname(review_path), exist_ok=True)
    with open(review_path, "w", encoding="utf-8") as f:
        json.dump(review_fixture, f, indent=2, default=str)

    # 4. tuong_prediction_response_real.json
    single_fixture = {
        "generated_at": generated_at,
        "release_sha": release_sha,
        "response": results[0],
        "metadata": {"owner": "Tuong", "source": "canonical_20_payloads"},
    }
    single_path = os.path.join(repo_root, "outputs", "ui_fixtures", "tuong_prediction_response_real.json")
    os.makedirs(os.path.dirname(single_path), exist_ok=True)
    with open(single_path, "w", encoding="utf-8") as f:
        json.dump(single_fixture, f, indent=2, default=str)

    # 5. db_integration/week7_prediction_log_payloads.json
    db_payload = {
        "generated_at": generated_at,
        "release_sha": release_sha,
        "total_payloads": len(log_payloads),
        "prediction_log_payloads": log_payloads,
    }
    db_path = os.path.join(repo_root, "outputs", "db_integration", "week7_prediction_log_payloads.json")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db_payload, f, indent=2, default=str)

    print(f"Successfully regenerated all fixtures in {repo_root}:")
    print(f"  Status counts: {status_counts}")
    print(f"  Review queue items: {len(review_items)}")
    print(f"  DB log payloads: {len(log_payloads)}")
    print(f"  Release SHA: {release_sha}")


if __name__ == "__main__":
    regenerate_fixtures(r"f:\Quanskill")
    if os.path.exists(r"f:\Quanskill\quanskill\DataVision_Duy"):
        regenerate_fixtures(r"f:\Quanskill\quanskill\DataVision_Duy")
