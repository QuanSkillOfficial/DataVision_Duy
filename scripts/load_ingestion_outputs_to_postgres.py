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
from data_engineering.pipelines.handoff_context import allocate_structured_record_limits
from data_engineering.storage.postgres_writer import (
    build_dry_run_summary,
    load_ingestion_result_to_postgres,
    query_integration_counts,
    validate_target_schema,
)

RUN_LOG_DIR = PROJECT_ROOT / "logs/runs"
DRY_RUN_OUTPUT = PROJECT_ROOT / "logs/db_load_dry_run/duy_to_phat_db_load_plan.json"
SMOKE_DRY_RUN_OUTPUT = PROJECT_ROOT / "logs/db_load_dry_run/duy_to_phat_db_smoke_plan.json"
RESULT_OUTPUT = PROJECT_ROOT / "logs/db_load_results/duy_to_phat_db_load_result.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_successful_run_logs(run_log_dir: Path = RUN_LOG_DIR) -> list[dict[str, Any]]:
    runs = [_read_json(path) for path in sorted(run_log_dir.glob("*.json"))]
    return [run for run in runs if run.get("status") in {"success", "partial_success"}]


def select_latest_run_per_source(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_by_source: dict[str, dict[str, Any]] = {}
    for run in runs:
        source_name = run.get("source_name")
        if not source_name:
            continue
        current = latest_by_source.get(source_name)
        if current is None or (run.get("end_time") or "") > (current.get("end_time") or ""):
            latest_by_source[source_name] = run
    return sorted(latest_by_source.values(), key=lambda run: run.get("source_name", ""))


def build_dry_run_plan(
    runs: list[dict[str, Any]],
    *,
    structured_record_limit: int | None = None,
) -> dict[str, Any]:
    runs = select_latest_run_per_source(runs)
    limits = allocate_structured_record_limits(runs, structured_record_limit)
    summaries = [
        build_dry_run_summary(run, structured_record_limit=limits.get(run["source_name"]))
        for run in runs
    ]
    return {
        "mode": "smoke_dry_run" if structured_record_limit is not None else "dry_run",
        "run_count": len(runs),
        "runs": summaries,
        "totals": {
            "sources": len({run["source_name"] for run in runs}),
            "pipeline_runs": len(runs),
            "ingestion_logs": len(runs),
            "structured_records": sum(summary["would_insert"]["structured_records"] for summary in summaries),
            "documents": sum(1 for run in runs if run.get("source_type") == "pdf"),
            "document_pages": sum(run.get("records_valid", 0) for run in runs if run.get("source_type") == "pdf"),
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def run_dry_run(structured_record_limit: int | None = None) -> dict[str, Any]:
    runs = load_successful_run_logs()
    plan = build_dry_run_plan(runs, structured_record_limit=structured_record_limit)
    output_path = SMOKE_DRY_RUN_OUTPUT if structured_record_limit is not None else DRY_RUN_OUTPUT
    write_json(output_path, plan)
    return plan


def run_real_load(
    config_path: str | None = None,
    *,
    structured_record_limit: int | None = None,
) -> dict[str, Any]:
    runs = select_latest_run_per_source(load_successful_run_logs())
    limits = allocate_structured_record_limits(runs, structured_record_limit)
    conn = get_connection(config_path)
    try:
        schema_columns = validate_target_schema(conn)
        results = [
            load_ingestion_result_to_postgres(
                conn,
                run,
                structured_record_limit=limits.get(run["source_name"]),
            )
            for run in runs
        ]
        document_external_ids = [
            run.get("document_id") or (run.get("pdf_metadata") or {}).get("document_id")
            for run in runs
            if run.get("source_type") == "pdf"
        ]
        verification = query_integration_counts(
            conn,
            run_ids=[run["run_id"] for run in runs],
            source_names=[run["source_name"] for run in runs],
            document_external_ids=[value for value in document_external_ids if value],
        )
    finally:
        conn.close()

    expected = build_dry_run_plan(runs, structured_record_limit=structured_record_limit)["totals"]
    verification_passed = all(
        verification.get(table, 0) >= expected_count
        for table, expected_count in expected.items()
    )
    result_statuses = {result.get("status") for result in results}
    payload = {
        "mode": "smoke_write_db" if structured_record_limit is not None else "full_write_db",
        "status": "passed" if verification_passed and "failed" not in result_statuses else "failed",
        "run_count": len(runs),
        "results": results,
        "schema_validation": {
            "status": "passed",
            "tables": {table: len(columns) for table, columns in schema_columns.items()},
        },
        "verification": verification,
        "expected_minimum_counts": expected,
    }
    write_json(RESULT_OUTPUT, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Load Duy ingestion outputs into Phat PostgreSQL schema")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Build a PostgreSQL insert plan without connecting")
    mode.add_argument("--write-db", action="store_true", help="Insert into PostgreSQL instead of dry-run")
    parser.add_argument("--smoke", action="store_true", help="Limit structured records to 100 total for CI")
    parser.add_argument(
        "--limit-structured-records",
        type=int,
        help="Maximum structured records across CSV, Excel, and API sources",
    )
    parser.add_argument("--db-config", help="Path to database config JSON")
    args = parser.parse_args()

    structured_record_limit = args.limit_structured_records
    if args.smoke:
        structured_record_limit = min(structured_record_limit, 100) if structured_record_limit is not None else 100

    try:
        if args.write_db:
            result = run_real_load(args.db_config, structured_record_limit=structured_record_limit)
            print(f"Wrote DB load result: {RESULT_OUTPUT.relative_to(PROJECT_ROOT).as_posix()}")
            print(f"Runs loaded: {result['run_count']}")
            print(f"Schema validation: {result['schema_validation']['status']}")
            print(f"Verification: {result['status']} - {result['verification']}")
        else:
            result = run_dry_run(structured_record_limit=structured_record_limit)
            output_path = SMOKE_DRY_RUN_OUTPUT if structured_record_limit is not None else DRY_RUN_OUTPUT
            print(f"Wrote DB dry-run plan: {output_path.relative_to(PROJECT_ROOT).as_posix()}")
            print(f"Runs planned: {result['run_count']}")
            print(f"Structured records planned: {result['totals']['structured_records']}")
            print(f"Document pages planned: {result['totals']['document_pages']}")
    except Exception as exc:
        print(f"Database load failed: {exc}", file=sys.stderr)
        return 1
    return 0 if not args.write_db or result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
