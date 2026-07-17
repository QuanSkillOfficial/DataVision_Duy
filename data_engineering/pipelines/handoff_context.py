from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from data_engineering.utils.path_utils import resolve_project_path


DEFAULT_DB_LOAD_RESULT = "logs/db_load_results/duy_to_phat_db_load_result.json"


def allocate_structured_record_limits(
    runs: list[dict[str, Any]],
    total_limit: int | None,
) -> dict[str, int | None]:
    structured_runs = [run for run in runs if run.get("source_type") in {"csv", "excel", "api"}]
    if total_limit is None:
        return {run["source_name"]: None for run in structured_runs}
    if total_limit < 0:
        raise ValueError("Structured record limit must be zero or greater")
    if not structured_runs:
        return {}

    allocation = {run["source_name"]: 0 for run in structured_runs}
    remaining = total_limit
    while remaining > 0:
        eligible = [
            run
            for run in structured_runs
            if allocation[run["source_name"]] < int(run.get("records_valid") or 0)
        ]
        if not eligible:
            break
        share = max(1, remaining // len(eligible))
        progressed = 0
        for run in eligible:
            source_name = run["source_name"]
            available = int(run.get("records_valid") or 0) - allocation[source_name]
            amount = min(share, available, remaining)
            allocation[source_name] += amount
            remaining -= amount
            progressed += amount
            if remaining == 0:
                break
        if progressed == 0:
            break
    return allocation


def select_latest_successful_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for run in runs:
        if run.get("status") not in {"success", "partial_success"} or not run.get("source_name"):
            continue
        current = latest.get(run["source_name"])
        if current is None or (run.get("end_time") or "") > (current.get("end_time") or ""):
            latest[run["source_name"]] = run
    return sorted(latest.values(), key=lambda item: item["source_name"])


def load_latest_successful_runs(run_log_dir: str | Path = "logs/runs") -> list[dict[str, Any]]:
    directory = resolve_project_path(run_log_dir)
    if directory is None or not directory.exists():
        raise FileNotFoundError(f"Run log directory not found: {run_log_dir}")
    runs = [json.loads(path.read_text(encoding="utf-8")) for path in directory.glob("*.json")]
    selected = select_latest_successful_runs(runs)
    if not selected:
        raise FileNotFoundError(f"No successful ingestion runs found under {run_log_dir}")
    return selected


def load_database_identity_map(
    result_path: str | Path = DEFAULT_DB_LOAD_RESULT,
) -> dict[str, Any]:
    resolved = resolve_project_path(result_path)
    identity = {
        "status": "pending_database_load",
        "result_path": str(result_path).replace("\\", "/"),
        "source_ids": {},
        "document_db_ids": {},
    }
    if resolved is None or not resolved.exists():
        return identity

    payload = json.loads(resolved.read_text(encoding="utf-8"))
    for result in payload.get("results", []):
        source_name = result.get("source_name")
        source_id = result.get("source_id")
        if source_name and source_id is not None:
            identity["source_ids"][source_name] = int(source_id)
        document_external_id = result.get("document_external_id")
        document_db_id = result.get("document_db_id")
        if document_external_id and document_db_id is not None:
            identity["document_db_ids"][document_external_id] = int(document_db_id)

    if identity["source_ids"]:
        identity["status"] = "database_ids_confirmed"
    identity["database_result_status"] = payload.get("status")
    identity["mode"] = payload.get("mode")
    return identity


def identity_for_source(identity_map: dict[str, Any], source_name: str) -> int | None:
    return identity_map.get("source_ids", {}).get(source_name)


def identity_for_document(identity_map: dict[str, Any], document_external_id: str) -> int | None:
    return identity_map.get("document_db_ids", {}).get(document_external_id)


def build_database_enriched_ui_summary(
    runs: list[dict[str, Any]],
    identity_map: dict[str, Any],
) -> dict[str, Any]:
    selected = select_latest_successful_runs(runs)
    if not selected:
        raise ValueError("At least one successful ingestion run is required")
    pdf_run = next((run for run in selected if run.get("source_type") == "pdf"), None)
    structured_runs = [run for run in selected if run.get("source_type") in {"csv", "excel", "api"}]
    scores = [float(run.get("data_quality_score") or 0.0) for run in selected]
    run_rows = []
    for run in selected:
        document_external_id = run.get("document_id") or (run.get("pdf_metadata") or {}).get("document_id")
        run_rows.append(
            {
                "source_id": identity_for_source(identity_map, run["source_name"]),
                "source_name": run["source_name"],
                "source_type": run["source_type"],
                "ingestion_run_id": run["run_id"],
                "status": run["status"],
                "records_read": run.get("records_read", 0),
                "records_valid": run.get("records_valid", 0),
                "records_invalid": run.get("records_invalid", 0),
                "data_quality_score": run.get("data_quality_score"),
                "file_hash_sha256": (run.get("file_manifest") or {}).get("file_hash_sha256"),
                "document_external_id": document_external_id,
                "document_db_id": identity_for_document(identity_map, document_external_id)
                if document_external_id
                else None,
                "raw_output_path": run.get("raw_output_path"),
                "staging_output_path": run.get("staging_output_path"),
                "clean_output_path": run.get("clean_output_path"),
            }
        )

    latest_document = None
    if pdf_run:
        metadata = pdf_run.get("pdf_metadata") or {}
        document_external_id = pdf_run.get("document_id") or metadata.get("document_id")
        latest_document = {
            "source_id": identity_for_source(identity_map, pdf_run["source_name"]),
            "document_db_id": identity_for_document(identity_map, document_external_id),
            "document_external_id": document_external_id,
            "ingestion_run_id": pdf_run["run_id"],
            "file_name": metadata.get("file_name"),
            "page_count": metadata.get("page_count") or pdf_run.get("page_count"),
            "file_hash_sha256": (pdf_run.get("file_manifest") or {}).get("file_hash_sha256"),
            "parsing_status": "ready" if pdf_run.get("status") == "success" else pdf_run.get("status"),
        }

    return {
        "total_sources": len({run["source_name"] for run in selected}),
        "total_runs": len(selected),
        "successful_runs": sum(run.get("status") == "success" for run in selected),
        "failed_runs": sum(run.get("status") == "failed" for run in selected),
        "total_records_read": sum(int(run.get("records_read") or 0) for run in structured_runs),
        "total_records_valid": sum(int(run.get("records_valid") or 0) for run in structured_runs),
        "total_records_invalid": sum(int(run.get("records_invalid") or 0) for run in structured_runs),
        "total_document_pages_read": int(pdf_run.get("records_read") or 0) if pdf_run else 0,
        "average_data_quality_score": round(mean(scores), 2),
        "latest_document": latest_document,
        "database_identity_status": identity_map.get("status"),
        "handoff_paths": {
            "rag_handoff": "outputs/rag_handoff/week7_document_pages_db_enriched.jsonl",
            "rag_manifest": "outputs/rag_handoff/week7_rag_handoff_manifest.json",
            "prediction_payloads": "outputs/prediction_payloads/tuong_week7_prediction_payloads.json",
        },
        "runs": run_rows,
    }
