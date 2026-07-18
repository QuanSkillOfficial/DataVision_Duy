from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.pipelines.handoff_context import load_latest_successful_runs


DEFAULT_PHAT_WEEK7_ROOT = PROJECT_ROOT.parent / "DataVision_Phat" / "week7"
SUMMARY_OUTPUT = PROJECT_ROOT / "outputs/phat_handoff/phat_week7_mapping_summary.json"
IDENTITY_OUTPUT = PROJECT_ROOT / "logs/db_load_results/phat_week7_external_database_proof.json"

EXPECTED_INGESTION_COUNTS = {
    "sources": 4,
    "pipeline_runs": 4,
    "ingestion_logs": 4,
    "documents": 1,
    "document_pages": 36,
    "structured_records": 11524,
}
EXPECTED_SOURCE_NAMES = {
    "superstore_sales_csv",
    "product_sales_region_excel",
    "dummyjson_products_api",
    "dataflow_technical_report_pdf",
}
DATAFLOW_DOCUMENT_EXTERNAL_ID = "doc_dataflow_technical_report"


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required Phat Week 7 evidence is missing: {path}")
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-16")


def _read_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    for base in (PROJECT_ROOT.resolve(), PROJECT_ROOT.parent.resolve()):
        try:
            return resolved.relative_to(base).as_posix()
        except ValueError:
            continue
    return f"external/{path.name}"


def _git_head(repository_root: Path) -> str | None:
    git_dir = repository_root / ".git"
    head_path = git_dir / "HEAD"
    if not head_path.exists():
        return None
    head = head_path.read_text(encoding="ascii").strip()
    if not head.startswith("ref: "):
        return head or None

    ref_name = head.removeprefix("ref: ").strip()
    ref_path = git_dir / ref_name
    if ref_path.exists():
        return ref_path.read_text(encoding="ascii").strip() or None

    packed_refs = git_dir / "packed-refs"
    if packed_refs.exists():
        for line in packed_refs.read_text(encoding="ascii").splitlines():
            if line and not line.startswith(("#", "^")):
                commit, name = line.split(" ", 1)
                if name == ref_name:
                    return commit
    return None


def _extract_loaded_run_ids(rows: list[dict[str, Any]]) -> dict[str, str]:
    run_ids: dict[str, str] = {}
    for row in rows:
        source_name = row.get("source_name")
        run_name = row.get("run_name")
        prefix = f"{source_name}_" if source_name else None
        if source_name and run_name and prefix and run_name.startswith(prefix):
            run_ids[source_name] = run_name[len(prefix) :]
    return run_ids


def _extract_document_id_map(runbook_path: Path) -> dict[str, int]:
    text = _read_text(runbook_path)
    pattern = re.compile(
        r"Resolved document_external_id=['\"](?P<external_id>[^'\"]+)['\"]"
        r"\s*->\s*documents\.id=(?P<document_id>\d+)"
    )
    result = {
        match.group("external_id"): int(match.group("document_id"))
        for match in pattern.finditer(text)
    }
    if not result:
        raise ValueError(
            "Phat runbook does not contain a document_external_id -> documents.id proof"
        )
    return result


def _schema_findings(schema_path: Path, setup_path: Path) -> dict[str, Any]:
    schema_text = _read_text(schema_path)
    setup_text = _read_text(setup_path)
    missing_comma_risk = bool(
        re.search(
            r"created_at\s+TIMESTAMP\s+DEFAULT\s+CURRENT_TIMESTAMP\s*"
            r"CONSTRAINT\s+chk_prediction_status",
            schema_text,
            flags=re.IGNORECASE,
        )
    )
    return {
        "schema_file": _portable_path(schema_path),
        "setup_file": _portable_path(setup_path),
        "has_vector_extension": "CREATE EXTENSION IF NOT EXISTS vector" in schema_text,
        "has_source_unique_constraint": bool(
            re.search(
                r"name\s+VARCHAR\(255\)\s+NOT\s+NULL\s+UNIQUE",
                schema_text,
                flags=re.IGNORECASE,
            )
        ),
        "has_document_external_id": "document_external_id" in schema_text,
        "has_prediction_status_constraint": all(
            status in schema_text
            for status in ("accepted", "needs_review", "waiting_for_source", "failed")
        ),
        "has_prediction_logs_missing_comma_risk": missing_comma_risk,
        "has_required_views": all(
            view in setup_text
            for view in (
                "v_dashboard_overview",
                "v_latest_ingestion_runs",
                "v_data_quality_dashboard",
                "v_document_rag_readiness",
                "v_prediction_review_queue",
                "v_rag_daily_metrics",
            )
        ),
    }


def _validate_summary(summary: dict[str, Any]) -> None:
    errors: list[str] = []
    counts = summary["counts"]
    for table, expected in EXPECTED_INGESTION_COUNTS.items():
        actual = counts.get(table)
        if table == "pipeline_runs":
            if actual is None or int(actual) < expected:
                errors.append(f"{table}: expected at least {expected}, got {actual}")
        elif actual != expected:
            errors.append(f"{table}: expected {expected}, got {actual}")

    source_names = set(summary["source_id_map"])
    if source_names != EXPECTED_SOURCE_NAMES:
        errors.append(
            f"source names do not match: expected {sorted(EXPECTED_SOURCE_NAMES)}, "
            f"got {sorted(source_names)}"
        )

    document = summary["document_id_map"].get(DATAFLOW_DOCUMENT_EXTERNAL_ID)
    if not document or document.get("document_db_id") is None:
        errors.append("DataFlow document database ID is not proven")

    schema = summary["schema_findings"]
    required_schema_checks = (
        "has_vector_extension",
        "has_source_unique_constraint",
        "has_document_external_id",
        "has_prediction_status_constraint",
        "has_required_views",
    )
    for check in required_schema_checks:
        if not schema.get(check):
            errors.append(f"schema check failed: {check}")
    if schema.get("has_prediction_logs_missing_comma_risk"):
        errors.append("schema still has the prediction_logs missing-comma risk")

    if summary["counts"].get("document_chunks", 0) <= 0:
        errors.append("document_chunks proof is empty")
    if summary["counts"].get("rag_query_logs", 0) <= 0:
        errors.append("rag_query_logs proof is empty")
    if summary["counts"].get("prediction_logs", 0) <= 0:
        errors.append("prediction_logs proof is empty")
    if not summary["database_ci_smoke_test_passed"]:
        errors.append("Phat database CI smoke result is not a confirmed pass")

    if errors:
        raise ValueError("Phat Week 7 evidence validation failed: " + "; ".join(errors))


def build_mapping_summary(phat_week7_root: Path = DEFAULT_PHAT_WEEK7_ROOT) -> dict[str, Any]:
    database_root = phat_week7_root / "database"
    schema_path = database_root / "schema/schema_v4_fixed.sql"
    setup_path = database_root / "schema/setup_database_v3.sql"
    validation_path = database_root / "validation/validation_queries_v3.sql"
    db_validation_dir = database_root / "outputs/db_validation"
    dashboard_dir = database_root / "outputs/dashboard_view_samples"
    runbook_path = phat_week7_root / "docs/week7_database_setup_runbook.md"
    ci_result_path = phat_week7_root / "docs/week7_database_ci_smoke_test_result.md"

    ingestion_counts = _read_json(db_validation_dir / "duy_data_load_counts.json")
    prediction_counts = _read_json(db_validation_dir / "prediction_log_counts.json")
    rag_counts = _read_json(db_validation_dir / "rag_pgvector_counts.json")
    source_rows = _read_json(dashboard_dir / "v_source_quality_summary.json")
    latest_run_rows = _read_json(dashboard_dir / "v_latest_ingestion_runs.json")
    dashboard_rows = _read_json(dashboard_dir / "v_dashboard_overview.json")
    data_quality_rows = _read_json(dashboard_dir / "v_data_quality_dashboard.json")
    rag_readiness_rows = _read_json(dashboard_dir / "v_document_rag_readiness.json")
    document_ids = _extract_document_id_map(runbook_path)

    source_id_map = {
        row["source_name"]: {
            "source_id": int(row["source_id"]),
            "source_type": row.get("source_type"),
            "status": row.get("status"),
            "total_documents": int(row.get("total_documents") or 0),
            "total_structured_records": int(row.get("total_structured_records") or 0),
        }
        for row in source_rows
    }
    dataflow_source = source_id_map.get("dataflow_technical_report_pdf") or {}
    readiness_by_external_id = {
        row["document_external_id"]: row for row in rag_readiness_rows
    }
    document_id_map = {
        external_id: {
            "document_db_id": document_id,
            "source_id": dataflow_source.get("source_id"),
            "file_name": readiness_by_external_id.get(external_id, {}).get("file_name"),
            "page_count": int(
                readiness_by_external_id.get(external_id, {}).get("page_count") or 0
            ),
            "total_chunks": int(
                readiness_by_external_id.get(external_id, {}).get("total_chunks") or 0
            ),
            "processing_status": readiness_by_external_id.get(external_id, {}).get(
                "processing_status"
            ),
        }
        for external_id, document_id in document_ids.items()
    }

    current_duy_runs = {
        run["source_name"]: run["run_id"] for run in load_latest_successful_runs()
    }
    phat_loaded_runs = _extract_loaded_run_ids(latest_run_rows)
    run_alignment = {
        source_name: {
            "phat_loaded_run_id": phat_loaded_runs.get(source_name),
            "current_duy_run_id": current_duy_runs.get(source_name),
            "matches": phat_loaded_runs.get(source_name) == current_duy_runs.get(source_name),
        }
        for source_name in sorted(EXPECTED_SOURCE_NAMES)
    }

    ci_result_text = _read_text(ci_result_path)
    counts = {
        **{key: int(value) for key, value in ingestion_counts.items()},
        "document_chunks": int(rag_counts.get("document_chunks") or 0),
        "rag_query_logs": int(rag_counts.get("rag_query_logs") or 0),
        "prediction_logs": int(prediction_counts.get("total_prediction_logs") or 0),
        "prediction_review_queue": int(
            prediction_counts.get("v_prediction_review_queue_count") or 0
        ),
    }

    summary = {
        "schema_version": "duy_phat_week7_mapping_v1",
        "status": "passed",
        "source": "DataVision_Phat/week7 real PostgreSQL evidence",
        "phat_commit": _git_head(phat_week7_root.parent),
        "phat_week7_root": _portable_path(phat_week7_root),
        "files_used": {
            "schema": _portable_path(schema_path),
            "setup": _portable_path(setup_path),
            "validation": _portable_path(validation_path),
            "duy_counts": _portable_path(
                db_validation_dir / "duy_data_load_counts.json"
            ),
            "rag_counts": _portable_path(
                db_validation_dir / "rag_pgvector_counts.json"
            ),
            "prediction_counts": _portable_path(
                db_validation_dir / "prediction_log_counts.json"
            ),
            "source_ids": _portable_path(
                dashboard_dir / "v_source_quality_summary.json"
            ),
            "latest_runs": _portable_path(
                dashboard_dir / "v_latest_ingestion_runs.json"
            ),
            "document_readiness": _portable_path(
                dashboard_dir / "v_document_rag_readiness.json"
            ),
            "database_ci_result": _portable_path(ci_result_path),
            "database_runbook": _portable_path(runbook_path),
        },
        "schema_findings": _schema_findings(schema_path, setup_path),
        "database_ci_smoke_test_passed": (
            "10/10 checks passed" in ci_result_text
            and "All database smoke test checks passed." in ci_result_text
        ),
        "source_id_map": source_id_map,
        "document_id_map": document_id_map,
        "counts": counts,
        "prediction_status_counts": prediction_counts.get("status_counts", {}),
        "dashboard_overview": dashboard_rows[0] if dashboard_rows else {},
        "data_quality_dashboard": data_quality_rows,
        "snapshot_alignment": {
            "phat_loaded_run_ids": phat_loaded_runs,
            "current_duy_run_ids": current_duy_runs,
            "all_current_run_ids_loaded": all(
                row["matches"] for row in run_alignment.values()
            ),
            "by_source": run_alignment,
            "note": (
                "Database identities are stable and confirmed. Current Duy run UUIDs "
                "must still be loaded with Duy's writer for current-run proof."
            ),
        },
        "integration_status": {
            "phat_database_setup_proven": True,
            "duy_snapshot_loaded": counts["sources"] == 4
            and counts["document_pages"] == 36
            and counts["structured_records"] == 11524,
            "database_ids_confirmed": bool(source_id_map)
            and DATAFLOW_DOCUMENT_EXTERNAL_ID in document_id_map,
            "lap_pgvector_proven": counts["document_chunks"] > 0
            and counts["rag_query_logs"] > 0,
            "tuong_prediction_logs_proven": counts["prediction_logs"] > 0,
            "dashboard_views_exported": bool(dashboard_rows)
            and bool(data_quality_rows),
        },
        "id_rules": {
            "source_id": "Phat sources.id resolved by source_name",
            "document_external_id": "Duy stable document key",
            "document_db_id": "Phat documents.id resolved by document_external_id",
            "ingestion_run_id": "Duy run UUID; never use as source_id",
        },
    }
    _validate_summary(summary)
    return summary


def build_external_identity_proof(summary: dict[str, Any]) -> dict[str, Any]:
    dataflow_document = summary["document_id_map"][DATAFLOW_DOCUMENT_EXTERNAL_ID]
    results = []
    for source_name, source in sorted(summary["source_id_map"].items()):
        result = {
            "source_name": source_name,
            "source_id": source["source_id"],
            "status": "identity_confirmed",
        }
        if source_name == "dataflow_technical_report_pdf":
            result.update(
                {
                    "document_external_id": DATAFLOW_DOCUMENT_EXTERNAL_ID,
                    "document_db_id": dataflow_document["document_db_id"],
                }
            )
        results.append(result)

    snapshot_alignment = summary["snapshot_alignment"]
    return {
        "mode": "external_phat_week7_database_proof",
        "status": "passed",
        "database_identity_status": "database_ids_confirmed",
        "schema_version": "schema_v4_fixed",
        "source": "outputs/phat_handoff/phat_week7_mapping_summary.json",
        "phat_commit": summary.get("phat_commit"),
        "results": results,
        "verification": {
            key: summary["counts"][key] for key in EXPECTED_INGESTION_COUNTS
        },
        "integration_counts": {
            "document_chunks": summary["counts"]["document_chunks"],
            "rag_query_logs": summary["counts"]["rag_query_logs"],
            "prediction_logs": summary["counts"]["prediction_logs"],
            "prediction_review_queue": summary["counts"][
                "prediction_review_queue"
            ],
        },
        "current_duy_runs_loaded": snapshot_alignment[
            "all_current_run_ids_loaded"
        ],
        "snapshot_alignment": snapshot_alignment,
        "evidence": summary["files_used"],
        "note": (
            "Phat Week 7 proves the stable source/document IDs and a full Duy data "
            "snapshot. The current Duy run UUIDs differ, so rerun Duy's --write-db "
            "loader when Docker/PostgreSQL is available to prove the latest runs."
        ),
    }


def write_outputs(summary: dict[str, Any]) -> tuple[Path, Path]:
    SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    IDENTITY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    IDENTITY_OUTPUT.write_text(
        json.dumps(
            build_external_identity_proof(summary),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return SUMMARY_OUTPUT, IDENTITY_OUTPUT


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Phat Week 7 DB proof and build Duy's identity bridge"
    )
    parser.add_argument(
        "--phat-week7-root",
        type=Path,
        default=DEFAULT_PHAT_WEEK7_ROOT,
    )
    args = parser.parse_args()
    summary = build_mapping_summary(args.phat_week7_root)
    summary_path, identity_path = write_outputs(summary)
    print(
        f"Wrote Phat mapping summary: "
        f"{summary_path.relative_to(PROJECT_ROOT).as_posix()}"
    )
    print(
        f"Wrote external identity proof: "
        f"{identity_path.relative_to(PROJECT_ROOT).as_posix()}"
    )
    print(
        "Database identities: "
        f"{len(summary['source_id_map'])} sources, "
        f"{len(summary['document_id_map'])} document"
    )
    print(
        "Current Duy run IDs loaded: "
        f"{summary['snapshot_alignment']['all_current_run_ids_loaded']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
