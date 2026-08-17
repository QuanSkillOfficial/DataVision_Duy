"""
Week 7 fixture validation helpers.

The UI consumes JSON outputs from several intern-owned modules. These
helpers keep the required contract checks in one place so tests and CI
smoke scripts can fail before Streamlit pages try to render bad data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from demo.config import FIXTURES_DIR


WEEK7_FIXTURE_DIR = Path(FIXTURES_DIR) / "week7"


class FixtureValidationError(ValueError):
    """Raised when a fixture is missing a required Week 7 field."""


def load_week7_fixture(name: str) -> dict:
    path = WEEK7_FIXTURE_DIR / f"{name}.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _get_path(payload: dict, dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise FixtureValidationError(f"Missing required field: {dotted_path}")
        current = current[part]
    return current


def _require_paths(payload: dict, paths: Iterable[str]) -> None:
    for path in paths:
        value = _get_path(payload, path)
        if value is None:
            raise FixtureValidationError(f"Required field is null: {path}")


def validate_duy_ingestion_summary(payload: dict) -> dict:
    _require_paths(
        payload,
        [
            "total_sources",
            "total_runs",
            "successful_runs",
            "average_data_quality_score",
            "latest_document.document_external_id",
            "latest_document.file_hash_sha256",
            "handoff_paths",
        ],
    )
    _get_path(payload, "latest_document.document_db_id")
    if not isinstance(payload["handoff_paths"], dict) or not payload["handoff_paths"]:
        raise FixtureValidationError("handoff_paths must be a non-empty object")
    return payload


def validate_phat_dashboard_views(payload: dict) -> dict:
    data = _get_path(payload, "data")
    _require_paths(
        data,
        [
            "v_dashboard_overview",
            "v_latest_ingestion_runs",
            "v_data_quality_dashboard",
            "v_document_rag_readiness",
            "v_prediction_review_queue",
            "v_recent_activity",
        ],
    )
    return payload


def validate_lap_rag_response(payload: dict) -> dict:
    data = _get_path(payload, "data")
    _require_paths(
        data,
        [
            "question",
            "status",
            "document_external_id",
            "retrieved_context",
            "citations",
        ],
    )
    _require_paths(payload, ["metadata.retrieval_backend"])
    if data["status"] in {"success", "retrieval_only"} and not data["citations"]:
        raise FixtureValidationError("successful RAG fixture must include citations")
    for citation in data["citations"]:
        _get_path(citation, "document_external_id")
        _get_path(citation, "document_db_id")
        _get_path(citation, "similarity_score")
    return payload


def _validate_prediction_item(item: dict) -> None:
    _require_paths(
        item,
        [
            "status",
            "confidence",
            "top_predictions",
            "document_external_id",
            "manual_review_required",
        ],
    )
    _get_path(item, "review_reason")
    _get_path(item, "document_db_id")


def validate_tuong_prediction_batch(payload: dict) -> dict:
    results = _get_path(payload, "results")
    if not isinstance(results, list) or not results:
        raise FixtureValidationError("prediction results must be a non-empty list")
    for item in results:
        _validate_prediction_item(item)
    return payload


def validate_tuong_review_queue(payload: dict) -> dict:
    review_items = _get_path(payload, "review_items")
    if not isinstance(review_items, list):
        raise FixtureValidationError("review_items must be a list")
    for item in review_items:
        _validate_prediction_item(item)
        _get_path(item, "prediction_log_id")
    return payload


def validate_all_week7_fixtures() -> dict[str, dict]:
    fixtures = {
        "duy_latest_ingestion_summary": validate_duy_ingestion_summary(
            load_week7_fixture("duy_latest_ingestion_summary")
        ),
        "phat_dashboard_views_sample": validate_phat_dashboard_views(
            load_week7_fixture("phat_dashboard_views_sample")
        ),
        "lap_rag_response_real": validate_lap_rag_response(
            load_week7_fixture("lap_rag_response_real")
        ),
        "tuong_prediction_batch_response": validate_tuong_prediction_batch(
            load_week7_fixture("tuong_prediction_batch_response")
        ),
        "tuong_prediction_review_queue_sample": validate_tuong_review_queue(
            load_week7_fixture("tuong_prediction_review_queue_sample")
        ),
    }
    return fixtures
