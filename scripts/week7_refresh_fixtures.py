"""
Refresh Week 7 UI fixtures from the latest intern-owned repositories.

The nested intern repos are not tracked by this UI repo, so this script gives
us a repeatable way to normalize their current handoff files into the stable
`demo/fixtures/week7/` contract used by tests, mock services, and CI smoke.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WEEK7_DIR = ROOT / "demo" / "fixtures" / "week7"
OTHERS = ROOT / "code_by_others"
DOCUMENT_TYPE_LABELS = [
    "contract",
    "invoice",
    "policy_document",
    "report",
    "financial_statement",
    "resume",
    "research_paper",
]


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _first_existing(paths: list[Path]) -> tuple[Path, bool]:
    for index, path in enumerate(paths):
        if path.exists():
            return path, index == 0
    raise FileNotFoundError("None of the candidate fixture paths exist: " + ", ".join(str(p) for p in paths))


def _normalize_view_name(path: Path) -> str:
    stem = path.stem
    return re.sub(r"_\d{12,}$", "", stem)


def refresh_duy() -> dict:
    source, exact = _first_existing(
        [
            OTHERS / "DataVision_Duy" / "outputs" / "ui_fixtures" / "duy_week7_database_enriched_summary.json",
            OTHERS / "DataVision_Duy" / "outputs" / "ui_fixtures" / "duy_latest_ingestion_summary.json",
            WEEK7_DIR / "duy_latest_ingestion_summary.json",
        ]
    )
    payload = _read_json(source)

    latest_run = (payload.get("runs") or [{}])[0] or {}
    latest_document = payload.get("latest_document") or payload.get("latest_ingestion_run") or {}
    payload.setdefault("latest_document", latest_document)
    if "latest_ingestion_run" not in payload:
        merged_run = dict(latest_run)
        for key, value in latest_document.items():
            merged_run.setdefault(key, value)
        merged_run.setdefault("run_id", merged_run.get("ingestion_run_id"))
        payload["latest_ingestion_run"] = merged_run
    payload.setdefault("handoff_paths", {})
    payload["handoff_paths"].setdefault("rag_handoff", payload["handoff_paths"].get("document_pages_jsonl_path"))
    payload["handoff_paths"].setdefault("prediction_payloads", payload["handoff_paths"].get("prediction_payload_path"))
    payload.setdefault("metadata", {})
    payload["metadata"].update(
        {
            "normalized_for": "week7_ui",
            "source_path": str(source.relative_to(ROOT)),
            "exact_week7_source_available": exact,
            "owner": "Duy",
        }
    )
    _write_json(WEEK7_DIR / "duy_latest_ingestion_summary.json", payload)
    return {"fixture": "duy_latest_ingestion_summary", "source": source, "exact": exact}


def refresh_phat() -> dict:
    source_dir, exact = _first_existing(
        [
            OTHERS / "DataVision_Phat" / "week7" / "database" / "outputs" / "dashboard_view_samples",
            OTHERS / "DataVision_Phat" / "week6" / "outputs" / "dashboard_view_samples_PhiHung",
            WEEK7_DIR,
        ]
    )

    views: dict[str, Any] = {}
    for path in sorted(source_dir.glob("v_*.json")):
        views[_normalize_view_name(path)] = _read_json(path)

    payload = {
        "data": views,
        "status": "success",
        "metadata": {
            "normalized_for": "week7_ui",
            "source_path": str(source_dir.relative_to(ROOT)),
            "exact_week7_source_available": exact,
            "owner": "Phat",
        },
    }
    _write_json(WEEK7_DIR / "phat_dashboard_views_sample.json", payload)
    return {"fixture": "phat_dashboard_views_sample", "source": source_dir, "exact": exact}


def _citation_lookup(context: list[dict]) -> dict[str, dict]:
    return {str(item.get("chunk_id")): item for item in context if item.get("chunk_id")}


def refresh_lap() -> dict:
    source, exact = _first_existing(
        [
            OTHERS / "DataVision_Lap" / "outputs" / "ui_fixtures" / "lap_rag_response_real.json",
            WEEK7_DIR / "lap_rag_response_real.json",
        ]
    )
    raw = _read_json(source)
    data = deepcopy(raw.get("data", raw))
    metadata = deepcopy(raw.get("metadata", data.get("metadata", {})))
    metadata.update(
        {
            "normalized_for": "week7_ui",
            "source_path": str(source.relative_to(ROOT)),
            "exact_week7_source_available": exact,
            "owner": "Lap",
        }
    )

    if not data.get("answer"):
        data["answer"] = (
            "Retrieved DataFlow context is available, but this fixture is retrieval-only "
            "and does not include a generated final answer."
        )

    data.setdefault("status", "retrieval_only")
    data.setdefault("document_external_id", "doc_dataflow_technical_report")
    data.setdefault("document_db_id", None)
    data["retrieval_backend"] = metadata.get("retrieval_backend")
    data["embedding_dimension"] = metadata.get("embedding_dimension")

    context_by_chunk = _citation_lookup(data.get("retrieved_context", []))
    normalized_citations = []
    for citation in data.get("citations", []):
        normalized = dict(citation)
        chunk = context_by_chunk.get(str(normalized.get("chunk_id")), {})
        normalized.setdefault("document_external_id", chunk.get("document_external_id", data.get("document_external_id")))
        normalized.setdefault("document_db_id", chunk.get("document_db_id", data.get("document_db_id")))
        normalized.setdefault("similarity_score", chunk.get("similarity_score"))
        normalized_citations.append(normalized)
    data["citations"] = normalized_citations

    payload = {"data": data, "status": "success", "metadata": metadata}
    _write_json(WEEK7_DIR / "lap_rag_response_real.json", payload)
    return {"fixture": "lap_rag_response_real", "source": source, "exact": exact}


def _with_review_flag(item: dict) -> dict:
    normalized = dict(item)
    normalized.setdefault("document_db_id", None)
    confidence = normalized.get("confidence", normalized.get("confidence_score", 0.0))
    status = normalized.get("status")
    if status in {"accepted", "needs_review"}:
        top_predictions = [dict(pred) for pred in normalized.get("top_predictions", [])]
        used_labels = {pred.get("label") for pred in top_predictions}
        for label in DOCUMENT_TYPE_LABELS:
            if len(top_predictions) >= 3:
                break
            if label not in used_labels:
                top_predictions.append({"label": label, "score": 0.0})
                used_labels.add(label)
        normalized["top_predictions"] = top_predictions[:3]
    normalized["manual_review_required"] = bool(
        normalized.get("manual_review_required")
        or status == "needs_review"
        or (isinstance(confidence, (int, float)) and confidence < 0.80 and status not in {"failed", "waiting_for_source"})
    )
    return normalized


def refresh_tuong_batch() -> dict:
    source, exact = _first_existing(
        [
            OTHERS / "DataVision_Tuong" / "outputs" / "ui_fixtures" / "tuong_prediction_batch_response.json",
            WEEK7_DIR / "tuong_prediction_batch_response.json",
        ]
    )
    raw = _read_json(source)
    payload = {"results": raw} if isinstance(raw, list) else raw
    payload["results"] = [_with_review_flag(item) for item in payload.get("results", [])]
    payload.setdefault("metadata", {})
    payload["metadata"].update(
        {
            "normalized_for": "week7_ui",
            "source_path": str(source.relative_to(ROOT)),
            "exact_week7_source_available": exact,
            "owner": "Tuong",
        }
    )
    _write_json(WEEK7_DIR / "tuong_prediction_batch_response.json", payload)
    return {"fixture": "tuong_prediction_batch_response", "source": source, "exact": exact}


def refresh_tuong_queue() -> dict:
    source, exact = _first_existing(
        [
            OTHERS / "DataVision_Tuong" / "outputs" / "ui_fixtures" / "tuong_prediction_review_queue_sample.json",
            WEEK7_DIR / "tuong_prediction_review_queue_sample.json",
        ]
    )
    raw = _read_json(source)
    payload = {"review_items": raw} if isinstance(raw, list) else raw
    review_items = []
    prediction_log_id_backfilled = False
    for index, item in enumerate(payload.get("review_items", []), start=1):
        normalized = _with_review_flag(item)
        if normalized.get("prediction_log_id") is None:
            normalized["prediction_log_id"] = index
            prediction_log_id_backfilled = True
        review_items.append(normalized)
    payload["review_items"] = review_items
    payload.setdefault("metadata", {})
    payload["metadata"].update(
        {
            "normalized_for": "week7_ui",
            "source_path": str(source.relative_to(ROOT)),
            "exact_week7_source_available": exact,
            "owner": "Tuong",
            "prediction_log_id_backfilled": prediction_log_id_backfilled,
        }
    )
    _write_json(WEEK7_DIR / "tuong_prediction_review_queue_sample.json", payload)
    return {"fixture": "tuong_prediction_review_queue_sample", "source": source, "exact": exact}


def main() -> int:
    results = [
        refresh_duy(),
        refresh_phat(),
        refresh_lap(),
        refresh_tuong_batch(),
        refresh_tuong_queue(),
    ]
    for result in results:
        exact_label = "exact Week 7" if result["exact"] else "fallback"
        print(f"{result['fixture']}: {exact_label} source -> {result['source'].relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
