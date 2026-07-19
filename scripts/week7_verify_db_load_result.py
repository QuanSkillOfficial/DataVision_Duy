from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.load_ingestion_outputs_to_postgres import load_successful_run_logs


DEFAULT_RESULT = (
    PROJECT_ROOT / "logs/db_load_results/duy_to_phat_db_load_result.json"
)


def verify_result(
    result_path: Path = DEFAULT_RESULT,
    *,
    expected_structured_records: int,
    verify_handoffs: bool = False,
) -> dict[str, Any]:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    current_run_ids = sorted(
        str(run["run_id"]) for run in load_successful_run_logs()
    )
    result_run_ids = sorted(str(value) for value in result.get("current_run_ids", []))
    snapshot = result.get("snapshot_alignment") or {}
    database_run_ids = sorted(
        str(value) for value in snapshot.get("database_run_ids", [])
    )
    expected_counts = {
        "sources": 4,
        "pipeline_runs": 4,
        "ingestion_logs": 4,
        "documents": 1,
        "document_pages": 36,
        "structured_records": expected_structured_records,
    }
    source_ids = {
        item.get("source_name"): item.get("source_id")
        for item in result.get("results", [])
    }
    document_ids = {
        item.get("document_external_id"): item.get("document_db_id")
        for item in result.get("results", [])
        if item.get("document_external_id")
    }
    checks = {
        "status_passed": result.get("status") == "passed",
        "connection_confirmed": result.get("connection_status") == "connected",
        "schema_confirmed": result.get("schema_version") == "schema_v4_fixed",
        "current_runs_flag": result.get("current_duy_runs_loaded") is True,
        "current_run_ids": result_run_ids == current_run_ids,
        "database_run_ids": database_run_ids == current_run_ids,
        "snapshot_alignment_flag": snapshot.get("all_current_run_ids_loaded")
        is True,
        "exact_counts": result.get("verification") == expected_counts,
        "stable_source_ids": source_ids
        == {
            "superstore_sales_csv": 1,
            "product_sales_region_excel": 2,
            "dummyjson_products_api": 3,
            "dataflow_technical_report_pdf": 4,
        },
        "document_id": document_ids.get("doc_dataflow_technical_report") == 1,
    }
    if verify_handoffs:
        rag = json.loads(
            (
                PROJECT_ROOT
                / "outputs/rag_handoff/week7_rag_handoff_manifest.json"
            ).read_text(encoding="utf-8")
        )
        ui = json.loads(
            (
                PROJECT_ROOT
                / "outputs/ui_fixtures/duy_week7_database_enriched_summary.json"
            ).read_text(encoding="utf-8")
        )
        predictions = json.loads(
            (
                PROJECT_ROOT
                / "outputs/prediction_payloads/tuong_week7_prediction_payloads.json"
            ).read_text(encoding="utf-8")
        )
        checks.update(
            {
                "rag_handoff_current": rag.get("current_ingestion_run_loaded")
                is True,
                "ui_fixture_current": ui.get("current_ingestion_runs_loaded")
                is True,
                "prediction_payloads_current": bool(predictions)
                and all(
                    item.get("current_ingestion_runs_loaded") is True
                    for item in predictions
                ),
            }
        )
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "result_path": result_path.relative_to(PROJECT_ROOT).as_posix(),
        "expected_counts": expected_counts,
        "current_run_ids": current_run_ids,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Duy's current-run PostgreSQL load evidence"
    )
    parser.add_argument("--result", default=str(DEFAULT_RESULT))
    parser.add_argument(
        "--expected-structured-records", type=int, choices=(100, 11524), required=True
    )
    parser.add_argument("--verify-handoffs", action="store_true")
    args = parser.parse_args()
    result = verify_result(
        Path(args.result),
        expected_structured_records=args.expected_structured_records,
        verify_handoffs=args.verify_handoffs,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
