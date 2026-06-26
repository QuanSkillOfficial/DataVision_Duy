from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .path_utils import ensure_parent, relative_path, resolve_project_path


OWNER = "Nguyen Minh Duy"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id() -> str:
    return str(uuid.uuid4())


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    target = ensure_parent(path)
    target.write_text(json.dumps(payload, indent=4, ensure_ascii=False), encoding="utf-8")


def write_jsonl_record(payload: dict[str, Any], path: str | Path) -> None:
    target = ensure_parent(path)
    with target.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def build_ingestion_log(
    *,
    run_id: str,
    source_name: str,
    source_type: str,
    input_path_or_url: str,
    start_time: str,
    end_time: str,
    status: str,
    records_read: int,
    records_valid: int,
    records_invalid: int,
    error_message: str | None,
    raw_output_path: str | Path | None,
    staging_output_path: str | Path | None,
    clean_output_path: str | Path | None,
    owner: str = OWNER,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    log: dict[str, Any] = {
        "run_id": run_id,
        "source_name": source_name,
        "source_type": source_type,
        "input_path_or_url": input_path_or_url,
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
        "records_read": int(records_read),
        "records_valid": int(records_valid),
        "records_invalid": int(records_invalid),
        "error_message": error_message,
        "raw_output_path": relative_path(raw_output_path),
        "staging_output_path": relative_path(staging_output_path),
        "clean_output_path": relative_path(clean_output_path),
        "owner": owner,
    }
    if extra:
        log.update(extra)
    return log


def persist_run_log(
    *,
    ingestion_log: dict[str, Any],
    latest_log_path: str | Path | None = None,
    run_log_dir: str | Path = "logs/runs",
    run_history_path: str | Path = "logs/ingestion_runs.jsonl",
) -> None:
    run_id = ingestion_log["run_id"]
    write_json(ingestion_log, resolve_project_path(run_log_dir) / f"{run_id}.json")
    write_jsonl_record(ingestion_log, run_history_path)
    if latest_log_path:
        write_json(ingestion_log, latest_log_path)

