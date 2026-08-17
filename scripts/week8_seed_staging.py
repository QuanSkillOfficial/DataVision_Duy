"""Seed and verify the complete Week 8 staging database.

This entrypoint runs inside the ``staging-seed`` container after PostgreSQL is
healthy. It is idempotent for downstream RAG/prediction evidence and exits
non-zero unless every owner handoff is queryable from the shared database.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = PROJECT_ROOT / "outputs/integration/week8_seed_result.json"
DOCUMENT_EXTERNAL_ID = "doc_dataflow_technical_report"


def run_step(name: str, command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    result = {
        "name": name,
        "command": ["python" if item == sys.executable else item for item in command],
        "returncode": completed.returncode,
        "stdout": (completed.stdout or "")[-3000:],
        "stderr": (completed.stderr or "")[-3000:],
    }
    if completed.returncode != 0:
        raise RuntimeError(f"{name} failed: {result['stderr'] or result['stdout']}")
    return result


def database_counts() -> dict[str, int]:
    from backend_stub.runtime import connect

    tables = (
        "sources",
        "pipeline_runs",
        "documents",
        "document_pages",
        "structured_records",
        "document_chunks",
        "prediction_logs",
        "rag_query_logs",
    )
    with connect() as conn, conn.cursor() as cursor:
        counts: dict[str, int] = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = int(cursor.fetchone()[0])
    return counts


def main() -> int:
    os.environ.setdefault("RAG_EMBEDDING_MODE", "hash")
    steps: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "status": "failed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "docker_staging_seed",
        "embedding_model": "datavision-hashing-384-v1",
        "steps": steps,
        "checks": {},
    }
    try:
        steps.append(
            run_step(
                "apply_schema",
                [sys.executable, "scripts/week7_apply_database_schema.py"],
            )
        )
        steps.append(
            run_step(
                "apply_versioned_migrations",
                [sys.executable, "week8/database/migrations/run_migrations.py"],
            )
        )
        steps.append(
            run_step(
                "load_duy_smoke_data",
                [
                    sys.executable,
                    "scripts/load_ingestion_outputs_to_postgres.py",
                    "--write-db",
                    "--smoke",
                ],
            )
        )
        for name, script in (
            ("build_rag_handoff", "scripts/week7_build_rag_handoff_package.py"),
            ("build_prediction_payloads", "scripts/week7_build_prediction_payloads.py"),
            ("build_ui_fixture", "scripts/week7_build_ui_fixtures.py"),
        ):
            steps.append(run_step(name, [sys.executable, script]))

        from ai.rag.load_document_pages_to_pgvector import load_and_ingest
        from backend_stub.runtime import database_url, rag_query

        document_pages = PROJECT_ROOT / "outputs/rag_handoff/week7_document_pages_db_enriched.jsonl"
        rag_load = load_and_ingest(
            str(document_pages),
            DOCUMENT_EXTERNAL_ID,
            connection_string=database_url(),
            output_result_path=str(PROJECT_ROOT / "outputs/integration/week8_chunk_load_result.json"),
        )
        if rag_load.get("status") != "success" or rag_load.get("chunks_inserted", 0) <= 0:
            raise RuntimeError(f"RAG chunk load did not insert chunks: {rag_load}")
        rag_reindex = load_and_ingest(
            str(document_pages),
            DOCUMENT_EXTERNAL_ID,
            connection_string=database_url(),
            output_result_path=str(PROJECT_ROOT / "outputs/integration/week8_chunk_reindex_result.json"),
        )
        if rag_reindex.get("status") != "success":
            raise RuntimeError(f"Repeated RAG indexing failed: {rag_reindex}")

        prediction_path = PROJECT_ROOT / "outputs/db_integration/week7_prediction_log_payloads.json"
        from scripts.insert_prediction_logs_to_postgres import (
            get_connection,
            insert_prediction_logs,
            load_payloads_from_file,
        )

        prediction_payloads = load_payloads_from_file(str(prediction_path))
        prediction_conn = get_connection(
            os.getenv("POSTGRES_HOST", "db"),
            int(os.getenv("POSTGRES_PORT", "5432")),
            os.getenv("POSTGRES_DB", "datavision_db"),
            os.getenv("POSTGRES_USER", "datavision"),
            os.getenv("POSTGRES_PASSWORD", "datavision123"),
        )
        try:
            prediction_ids = insert_prediction_logs(prediction_conn, prediction_payloads)
        finally:
            prediction_conn.close()

        rag_response = rag_query("What is the DataFlow pipeline?", DOCUMENT_EXTERNAL_ID, top_k=5)
        counts = database_counts()
        checks = {
            "duy_sources_loaded": counts["sources"] == 4,
            "duy_document_loaded": counts["documents"] == 1,
            "duy_pages_loaded": counts["document_pages"] == 36,
            "duy_structured_smoke_loaded": counts["structured_records"] == 100,
            "lap_chunks_loaded": counts["document_chunks"] > 0,
            "lap_reindex_is_idempotent": (
                rag_reindex.get("chunks_inserted") == 0
                and rag_reindex.get("rows_before") == rag_reindex.get("rows_after")
            ),
            "lap_retrieval_returned_context": len(rag_response.get("retrieved_context", [])) > 0,
            "lap_citations_returned": len(rag_response.get("citations", [])) > 0,
            "tuong_prediction_logs_loaded": counts["prediction_logs"] >= len(prediction_payloads),
            "tuong_prediction_ids_returned": len(prediction_ids) == len(prediction_payloads),
            "rag_query_logged": counts["rag_query_logs"] >= 1,
        }
        result.update(
            {
                "status": "passed" if all(checks.values()) else "failed",
                "checks": checks,
                "counts": counts,
                "rag_load": rag_load,
                "rag_reindex": rag_reindex,
                "rag_response": rag_response,
                "prediction_log_ids": prediction_ids,
            }
        )
        if result["status"] != "passed":
            raise RuntimeError(f"Week 8 seed checks failed: {checks}")

        steps.append(
            run_step(
                "phat_database_smoke",
                [sys.executable, "week7/database/scripts/ci_database_smoke_test.py"],
            )
        )
    except Exception as exc:
        result["error"] = str(exc)
        result["status"] = "failed"
    finally:
        RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
        RESULT_PATH.write_text(
            json.dumps(result, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
