from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from data_engineering.utils.path_utils import resolve_project_path


DEFAULT_DB_LOAD_RESULT = "logs/db_load_results/duy_to_phat_db_load_result.json"
DEFAULT_EXTERNAL_DB_PROOF = "logs/db_load_results/phat_week7_external_database_proof.json"
DEFAULT_RUN_HISTORY = "logs/ingestion_runs.jsonl"


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


def load_latest_successful_runs(
    run_log_dir: str | Path = "logs/runs",
    run_history_path: str | Path | None = DEFAULT_RUN_HISTORY,
) -> list[dict[str, Any]]:
    """Load the latest successful run for every source.

    Run-specific JSON files are runtime artifacts and newer files are ignored
    by Git. The append-only JSONL history is tracked, so combining both sources
    keeps local execution convenient while making a clean checkout
    reproducible. Duplicate run IDs are collapsed before selecting the latest
    source snapshot.
    """
    directory = resolve_project_path(run_log_dir)
    runs_by_id: dict[str, dict[str, Any]] = {}
    if directory is not None and directory.exists():
        for path in directory.glob("*.json"):
            run = json.loads(path.read_text(encoding="utf-8"))
            run_id = run.get("run_id")
            if run_id:
                runs_by_id[str(run_id)] = run

    history = resolve_project_path(run_history_path) if run_history_path else None
    if history is not None and history.exists():
        # utf-8-sig accepts both plain UTF-8 and the BOM used by the original
        # Windows-created history file.
        with history.open("r", encoding="utf-8-sig") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    run = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON in run history {history} at line {line_number}"
                    ) from exc
                run_id = run.get("run_id")
                if run_id:
                    runs_by_id[str(run_id)] = run

    selected = select_latest_successful_runs(list(runs_by_id.values()))
    if not selected:
        raise FileNotFoundError(
            f"No successful ingestion runs found under {run_log_dir} "
            f"or {run_history_path}"
        )
    return selected


def _identity_from_payload(
    payload: dict[str, Any],
    *,
    result_path: str | Path,
) -> dict[str, Any]:
    identity = {
        "status": "pending_database_load",
        "result_path": str(result_path).replace("\\", "/"),
        "source_ids": {},
        "document_db_ids": {},
    }
    for result in payload.get("results", []):
        source_name = result.get("source_name")
        source_id = result.get("source_id")
        if source_name and source_id is not None:
            identity["source_ids"][source_name] = int(source_id)
        document_external_id = result.get("document_external_id")
        document_db_id = result.get("document_db_id")
        if document_external_id and document_db_id is not None:
            identity["document_db_ids"][document_external_id] = int(document_db_id)

    payload_status = payload.get("status")
    has_source_ids = bool(identity["source_ids"])
    has_document_ids = bool(identity["document_db_ids"])
    if payload_status == "passed" and has_source_ids and has_document_ids:
        identity["status"] = "database_ids_confirmed"
    elif has_source_ids or has_document_ids:
        identity["status"] = "database_identity_incomplete"
    identity["database_result_status"] = payload_status
    identity["mode"] = payload.get("mode")
    for field in (
        "schema_version",
        "source",
        "phat_commit",
        "current_duy_runs_loaded",
        "snapshot_alignment",
        "evidence",
    ):
        if field in payload:
            identity[field] = payload[field]
    return identity


def load_database_identity_map(
    result_path: str | Path = DEFAULT_DB_LOAD_RESULT,
) -> dict[str, Any]:
    """Resolve stable database IDs without hiding an unexecuted local load.

    A local loader result is authoritative when it has actually run. In a
    clean checkout, however, the tracked local result may intentionally be a
    ``pending_external_database`` placeholder while Phat's committed proof
    already confirms the stable source/document IDs. In that specific default
    case, use the external proof as a fallback and retain its snapshot-alignment
    fields. Explicit custom result paths never fall back implicitly.
    """
    resolved = resolve_project_path(result_path)
    default_resolved = resolve_project_path(DEFAULT_DB_LOAD_RESULT)
    external_resolved = resolve_project_path(DEFAULT_EXTERNAL_DB_PROOF)
    is_default_request = resolved is not None and resolved == default_resolved

    primary_identity: dict[str, Any] | None = None
    if resolved is not None and resolved.exists():
        primary_payload = json.loads(resolved.read_text(encoding="utf-8"))
        primary_identity = _identity_from_payload(
            primary_payload,
            result_path=DEFAULT_DB_LOAD_RESULT
            if is_default_request
            else result_path,
        )
        if primary_identity["status"] not in {
            "pending_database_load",
            "database_identity_incomplete",
        }:
            return primary_identity
        # A failed or incomplete explicit load must remain visible. Only the
        # default placeholder is eligible for the committed Phat fallback.
        if not is_default_request or primary_payload.get("status") not in {
            None,
            "pending_external_database",
            "not_executed",
        }:
            return primary_identity

    if is_default_request and external_resolved is not None and external_resolved.exists():
        external_payload = json.loads(external_resolved.read_text(encoding="utf-8"))
        external_identity = _identity_from_payload(
            external_payload,
            result_path=DEFAULT_EXTERNAL_DB_PROOF,
        )
        if external_identity["status"] == "database_ids_confirmed":
            external_identity["identity_source"] = "phat_external_proof_fallback"
            external_identity["fallback_from"] = DEFAULT_DB_LOAD_RESULT
            return external_identity

    if primary_identity is not None:
        return primary_identity
    return {
        "status": "pending_database_load",
        "result_path": str(result_path).replace("\\", "/"),
        "source_ids": {},
        "document_db_ids": {},
    }


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
        "database_schema_version": identity_map.get("schema_version"),
        "database_identity_source": identity_map.get("result_path"),
        "current_ingestion_runs_loaded": identity_map.get(
            "current_duy_runs_loaded"
        ),
        "handoff_paths": {
            "rag_handoff": "outputs/rag_handoff/week7_document_pages_db_enriched.jsonl",
            "rag_manifest": "outputs/rag_handoff/week7_rag_handoff_manifest.json",
            "prediction_payloads": "outputs/prediction_payloads/tuong_week7_prediction_payloads.json",
        },
        "runs": run_rows,
    }
