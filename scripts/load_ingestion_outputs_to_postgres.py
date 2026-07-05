from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.storage.db_connection import get_connection
from data_engineering.storage.postgres_writer import build_dry_run_summary, load_ingestion_result_to_postgres

RUN_LOG_DIR = PROJECT_ROOT / "logs/runs"
DRY_RUN_OUTPUT = PROJECT_ROOT / "logs/db_load_dry_run/duy_to_phat_db_load_plan.json"
RESULT_OUTPUT = PROJECT_ROOT / "logs/db_load_results/duy_to_phat_db_load_result.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_successful_run_logs(run_log_dir: Path = RUN_LOG_DIR) -> list[dict[str, Any]]:
    runs = [_read_json(path) for path in sorted(run_log_dir.glob("*.json"))]
    return [run for run in runs if run.get("status") in {"success", "partial_success"}]


def build_dry_run_plan(runs: list[dict[str, Any]]) -> dict[str, Any]:
    summaries = [build_dry_run_summary(run) for run in runs]
    return {
        "mode": "dry_run",
        "run_count": len(runs),
        "runs": summaries,
        "totals": {
            "sources": len({run["source_name"] for run in runs}),
            "pipeline_runs": len(runs),
            "ingestion_logs": len(runs),
            "structured_records": sum(
                run.get("records_valid", 0) for run in runs if run.get("source_type") in {"csv", "excel", "api"}
            ),
            "documents": sum(1 for run in runs if run.get("source_type") == "pdf"),
            "document_pages": sum(run.get("records_valid", 0) for run in runs if run.get("source_type") == "pdf"),
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def run_dry_run() -> dict[str, Any]:
    runs = load_successful_run_logs()
    plan = build_dry_run_plan(runs)
    write_json(DRY_RUN_OUTPUT, plan)
    return plan


def run_real_load(config_path: str | None = None) -> dict[str, Any]:
    runs = load_successful_run_logs()
    conn = get_connection(config_path)
    try:
        results = [load_ingestion_result_to_postgres(conn, run) for run in runs]
    finally:
        conn.close()
    payload = {"mode": "write_db", "run_count": len(runs), "results": results}
    write_json(RESULT_OUTPUT, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Load Duy ingestion outputs into Phat PostgreSQL schema")
    parser.add_argument("--write-db", action="store_true", help="Insert into PostgreSQL instead of dry-run")
    parser.add_argument("--db-config", help="Path to database config JSON")
    args = parser.parse_args()

    if args.write_db:
        result = run_real_load(args.db_config)
        print(f"Wrote DB load result: {RESULT_OUTPUT.relative_to(PROJECT_ROOT).as_posix()}")
        print(f"Runs loaded: {result['run_count']}")
    else:
        result = run_dry_run()
        print(f"Wrote DB dry-run plan: {DRY_RUN_OUTPUT.relative_to(PROJECT_ROOT).as_posix()}")
        print(f"Runs planned: {result['run_count']}")
        print(f"Structured records planned: {result['totals']['structured_records']}")
        print(f"Document pages planned: {result['totals']['document_pages']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
