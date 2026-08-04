"""Refresh Week 7 prediction, DB-log and UI handoffs from Duy's 20 payloads.

The real prediction batch is never modified to manufacture an ``accepted``
result. When the current model produces no accepted prediction, the UI-only
status coverage example is stored separately under ``status_examples`` and is
explicitly labelled ``fixture_only``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.prediction.batch_inference import predict_document_types
from ai.prediction.prediction_log_payload_builder import build_prediction_log_payload


VALID_STATUSES = ("accepted", "needs_review", "waiting_for_source", "failed")
SUPPORTED_DOCUMENT_TYPES = [
    "contract",
    "financial_statement",
    "invoice",
    "policy_document",
    "report",
    "research_paper",
    "resume",
]


def default_input_path() -> Path:
    configured = os.getenv("DUY_PREDICTION_PAYLOADS")
    if configured:
        return Path(configured).expanduser().resolve()

    merged_repo_path = PROJECT_ROOT / "outputs" / "prediction_payloads" / "tuong_week7_prediction_payloads.json"
    if merged_repo_path.exists():
        return merged_repo_path

    # Local audit layout:
    # DataVision_Duy/team_repositories/DataVision_Tuong
    aggregate_root = PROJECT_ROOT.parents[1]
    return aggregate_root / "outputs" / "prediction_payloads" / "tuong_week7_prediction_payloads.json"


def read_payloads(path: Path, expected_count: int) -> list[dict[str, Any]]:
    payloads = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payloads, list):
        raise ValueError(f"{path} must contain a JSON list")
    if len(payloads) != expected_count:
        raise ValueError(f"Expected {expected_count} Duy payloads, found {len(payloads)}")
    return payloads


def enrich_result(payload: dict[str, Any], result: dict[str, Any], index: int) -> dict[str, Any]:
    enriched = dict(result)
    if not payload.get("document_external_id"):
        # Prediction inference can be used without platform lineage, but the
        # shared Week 7 handoff cannot. Normalize this integration case to a
        # visible failed record instead of dropping it or emitting a review
        # item that the UI cannot identify.
        enriched.update(
            {
                "predicted_document_type": None,
                "confidence": 0.0,
                "status": "failed",
                "top_predictions": [],
                "review_reason": "Missing required platform lineage: document_external_id",
            }
        )
    for field in (
        "source_id",
        "source_name",
        "document_external_id",
        "document_db_id",
        "ingestion_run_id",
    ):
        enriched[field] = payload.get(field)

    enriched.setdefault("predicted_document_type", None)
    enriched.setdefault("confidence", 0.0)
    enriched.setdefault("top_predictions", [])
    enriched.setdefault("model_version", "document_classifier_v1")
    enriched.setdefault("review_reason", None)
    enriched["manual_review_required"] = enriched.get("status") == "needs_review"
    enriched["batch_index"] = index
    enriched["fixture_only"] = False
    return enriched


def build_status_examples(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    by_status = {item["status"]: item for item in results if item.get("status") in VALID_STATUSES}

    for status in VALID_STATUSES:
        if status in by_status:
            examples.append(dict(by_status[status]))
            continue

        # The current Week 7 model has no >= 0.80 result on Duy's real batch.
        # Keep UI coverage honest by separating this contract-only example.
        reference = results[0]
        examples.append(
            {
                "predicted_document_type": "research_paper",
                "confidence": 0.95,
                "status": status,
                "top_predictions": [
                    {"label": "research_paper", "score": 0.95},
                    {"label": "report", "score": 0.03},
                    {"label": "contract", "score": 0.02},
                ],
                "model_version": reference.get("model_version", "document_classifier_v1"),
                "document_external_id": f"{reference['document_external_id']}_{status}_ui_example",
                "document_db_id": reference.get("document_db_id"),
                "source_id": reference.get("source_id"),
                "source_name": reference.get("source_name"),
                "ingestion_run_id": reference.get("ingestion_run_id"),
                "review_reason": None,
                "manual_review_required": status == "needs_review",
                "fixture_only": True,
                "fixture_reason": (
                    "UI contract coverage only; the current real 20-payload batch "
                    f"did not produce status={status}."
                ),
            }
        )
    return examples


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def refresh(input_path: Path, expected_count: int, ui_fixture_dir: Path | None = None) -> dict[str, Any]:
    payloads = read_payloads(input_path, expected_count)
    raw_results = predict_document_types(payloads)
    results = [
        enrich_result(payload, result, index)
        for index, (payload, result) in enumerate(zip(payloads, raw_results), start=1)
    ]

    prediction_logs = [
        build_prediction_log_payload(payload, result)
        for payload, result in zip(payloads, results)
    ]
    generated_at = datetime.now(timezone.utc).isoformat()
    status_counts = dict(Counter(item["status"] for item in results))

    batch_fixture = {
        "generated_at": generated_at,
        "source_payload_path": str(input_path),
        "total_results": len(results),
        "status_counts": status_counts,
        "results": results,
        "status_examples": build_status_examples(results),
        "metadata": {
            "owner": "Tuong",
            "real_batch": True,
            "accepted_is_ground_truth": False,
            "acceptance_threshold": 0.80,
        },
    }

    review_items = []
    for item in results:
        if item["status"] != "needs_review":
            continue
        review_item = dict(item)
        review_item.update(
            {
                "prediction_log_id": None,
                "reviewed": False,
                "corrected_document_type": None,
                "corrected_by": None,
            }
        )
        review_items.append(review_item)

    review_fixture = {
        "generated_at": generated_at,
        "total_review_items": len(review_items),
        "review_items": review_items,
        "supported_document_types": SUPPORTED_DOCUMENT_TYPES,
        "metadata": {
            "owner": "Tuong",
            "database_insert_status": "pending_database_connection",
        },
    }

    single_fixture = {
        "generated_at": generated_at,
        "response": results[0],
        "metadata": {"owner": "Tuong", "source": "real_week7_duy_batch"},
    }

    results_payload = {
        "generated_at": generated_at,
        "total_payloads": len(payloads),
        "status_counts": status_counts,
        "results": results,
        "prediction_log_payloads": prediction_logs,
    }
    log_payload = {
        "generated_at": generated_at,
        "total_payloads": len(prediction_logs),
        "prediction_log_payloads": prediction_logs,
    }

    outputs = {
        "results": PROJECT_ROOT / "outputs" / "week7_duy_prediction_results.json",
        "logs": PROJECT_ROOT / "outputs" / "db_integration" / "week7_prediction_log_payloads.json",
        "single": PROJECT_ROOT / "outputs" / "ui_fixtures" / "tuong_prediction_response_real.json",
        "batch": PROJECT_ROOT / "outputs" / "ui_fixtures" / "tuong_prediction_batch_response.json",
        "review": PROJECT_ROOT / "outputs" / "ui_fixtures" / "tuong_prediction_review_queue_sample.json",
    }
    write_json(outputs["results"], results_payload)
    write_json(outputs["logs"], log_payload)
    write_json(outputs["single"], single_fixture)
    write_json(outputs["batch"], batch_fixture)
    write_json(outputs["review"], review_fixture)

    if ui_fixture_dir is not None:
        write_json(ui_fixture_dir / "tuong_prediction_batch_response.json", batch_fixture)
        write_json(ui_fixture_dir / "tuong_prediction_review_queue_sample.json", review_fixture)

    return {
        "status": "passed",
        "input_payloads": len(payloads),
        "prediction_results": len(results),
        "prediction_logs": len(prediction_logs),
        "review_items": len(review_items),
        "status_counts": status_counts,
        "outputs": {key: str(path) for key, path in outputs.items()},
        "ui_fixture_dir": str(ui_fixture_dir) if ui_fixture_dir else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh Tuong Week 7 outputs from Duy payloads")
    parser.add_argument("--input", type=Path, default=default_input_path())
    parser.add_argument("--expected-count", type=int, default=20)
    parser.add_argument("--ui-fixture-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = refresh(
        args.input.resolve(),
        args.expected_count,
        args.ui_fixture_dir.resolve() if args.ui_fixture_dir else None,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
