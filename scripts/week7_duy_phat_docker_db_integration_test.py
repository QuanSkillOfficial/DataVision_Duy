from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.load_ingestion_outputs_to_postgres import load_successful_run_logs


DEFAULT_COMPOSE = PROJECT_ROOT / "docker-compose.db.yml"
DEFAULT_RESULT = (
    PROJECT_ROOT / "outputs/integration/week7_duy_phat_docker_db_result.json"
)
DB_LOAD_RESULT = (
    PROJECT_ROOT / "logs/db_load_results/duy_to_phat_db_load_result.json"
)


def _safe_project_name(value: str) -> str:
    if not re.fullmatch(r"datavision-duy-[a-z0-9-]+", value):
        raise ValueError(
            "Docker project name must match datavision-duy-[a-z0-9-]+"
        )
    return value


def _display(command: list[str]) -> list[str]:
    return [
        "python" if item == sys.executable else item.replace(str(PROJECT_ROOT), ".")
        for item in command
    ]


def _run(
    command: list[str],
    *,
    env: dict[str, str],
    timeout: int = 180,
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return {
        "command": _display(command),
        "returncode": completed.returncode,
        "stdout": (completed.stdout or "")[-4000:],
        "stderr": (completed.stderr or "")[-4000:],
    }


def _compose_base(compose_file: Path, project_name: str) -> list[str]:
    return [
        "docker",
        "compose",
        "--project-name",
        project_name,
        "-f",
        str(compose_file),
    ]


def _wait_for_database(
    compose: list[str],
    *,
    env: dict[str, str],
    timeout: int = 90,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_probe: dict[str, Any] = {}
    while time.monotonic() < deadline:
        last_probe = _run(
            compose
            + [
                "exec",
                "-T",
                "db",
                "pg_isready",
                "-U",
                env["POSTGRES_USER"],
                "-d",
                env["POSTGRES_DB"],
            ],
            env=env,
            timeout=20,
        )
        if last_probe["returncode"] == 0:
            return last_probe
        time.sleep(2)
    return last_probe


def _database_snapshot(env: dict[str, str]) -> dict[str, Any]:
    import psycopg2

    conn = psycopg2.connect(
        host=env["DB_HOST"],
        port=int(env["DB_PORT"]),
        database=env["DB_NAME"],
        user=env["DB_USER"],
        password=env["DB_PASSWORD"],
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            vector_enabled = cursor.fetchone() is not None
            tables = [
                "sources",
                "pipeline_runs",
                "ingestion_logs",
                "documents",
                "document_pages",
                "structured_records",
            ]
            counts: dict[str, int] = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = int(cursor.fetchone()[0])
            cursor.execute("SELECT run_id FROM ingestion_logs ORDER BY run_id")
            run_ids = [str(row[0]) for row in cursor.fetchall()]
            cursor.execute("SELECT name, id FROM sources ORDER BY id")
            source_ids = {str(name): int(source_id) for name, source_id in cursor.fetchall()}
            cursor.execute(
                "SELECT document_external_id, id FROM documents ORDER BY id"
            )
            document_ids = {
                str(external_id): int(document_id)
                for external_id, document_id in cursor.fetchall()
            }
    finally:
        conn.close()
    return {
        "vector_extension_enabled": vector_enabled,
        "counts": counts,
        "run_ids": run_ids,
        "source_ids": source_ids,
        "document_ids": document_ids,
        "host": env["DB_HOST"],
        "port": int(env["DB_PORT"]),
        "database": env["DB_NAME"],
    }


def run_integration(
    *,
    mode: str = "smoke-then-full",
    project_name: str = "datavision-duy-week7-integration",
    db_port: int = 55432,
    compose_file: Path = DEFAULT_COMPOSE,
    schema_path: str | None = None,
    keep_db: bool = False,
) -> dict[str, Any]:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker CLI is not available")
    project_name = _safe_project_name(project_name)
    compose_file = compose_file.resolve()
    if not compose_file.is_file():
        raise FileNotFoundError(f"Compose file not found: {compose_file}")

    env = os.environ.copy()
    env.update(
        {
            "COMPOSE_PROJECT_NAME": project_name,
            "DB_HOST": "127.0.0.1",
            "DB_PORT": str(db_port),
            "DB_NAME": "datavision_db",
            "DB_USER": "datavision",
            "DB_PASSWORD": "datavision123",
            "POSTGRES_USER": "datavision",
            "POSTGRES_PASSWORD": "datavision123",
            "POSTGRES_DB": "datavision_db",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    if schema_path:
        env["PHAT_SCHEMA_PATH"] = schema_path

    compose = _compose_base(compose_file, project_name)
    steps: dict[str, Any] = {}
    load_results: list[dict[str, Any]] = []
    status = "failed"
    error: str | None = None

    try:
        steps["clean_before"] = _run(
            compose + ["down", "--volumes", "--remove-orphans"],
            env=env,
        )
        steps["start_database"] = _run(
            compose + ["up", "-d", "db"], env=env, timeout=240
        )
        if steps["start_database"]["returncode"] != 0:
            raise RuntimeError("Docker database failed to start")

        steps["database_ready"] = _wait_for_database(compose, env=env)
        if steps["database_ready"].get("returncode") != 0:
            raise RuntimeError("PostgreSQL did not become ready")

        schema_command = [sys.executable, "scripts/week7_apply_database_schema.py"]
        if schema_path:
            schema_command.extend(["--schema", schema_path])
        steps["apply_schema"] = _run(schema_command, env=env)
        if steps["apply_schema"]["returncode"] != 0:
            raise RuntimeError("Phat schema contract setup failed")

        modes = ["smoke", "full"] if mode == "smoke-then-full" else [mode]
        for load_mode in modes:
            command = [
                sys.executable,
                "scripts/load_ingestion_outputs_to_postgres.py",
                "--write-db",
            ]
            if load_mode == "smoke":
                command.append("--smoke")
            step = _run(command, env=env, timeout=300)
            steps[f"load_{load_mode}"] = step
            if step["returncode"] != 0:
                raise RuntimeError(f"Duy {load_mode} database load failed")
            load_results.append(
                json.loads(DB_LOAD_RESULT.read_text(encoding="utf-8"))
            )

        for name, command in {
            "build_rag_handoff": [
                sys.executable,
                "scripts/week7_build_rag_handoff_package.py",
            ],
            "build_prediction_payloads": [
                sys.executable,
                "scripts/week7_build_prediction_payloads.py",
            ],
            "build_ui_fixture": [
                sys.executable,
                "scripts/week7_build_ui_fixtures.py",
            ],
        }.items():
            steps[name] = _run(command, env=env)
            if steps[name]["returncode"] != 0:
                raise RuntimeError(f"{name} failed after database load")

        snapshot = _database_snapshot(env)
        latest_runs = load_successful_run_logs()
        expected_run_ids = sorted(str(run["run_id"]) for run in latest_runs)
        expected_structured = 100 if mode == "smoke" else 11524
        expected_counts = {
            "sources": 4,
            "pipeline_runs": 4,
            "ingestion_logs": 4,
            "documents": 1,
            "document_pages": 36,
            "structured_records": expected_structured,
        }
        rag_manifest = json.loads(
            (
                PROJECT_ROOT
                / "outputs/rag_handoff/week7_rag_handoff_manifest.json"
            ).read_text(encoding="utf-8")
        )
        ui_fixture = json.loads(
            (
                PROJECT_ROOT
                / "outputs/ui_fixtures/duy_week7_database_enriched_summary.json"
            ).read_text(encoding="utf-8")
        )
        checks = {
            "vector_extension": snapshot["vector_extension_enabled"],
            "exact_table_counts": snapshot["counts"] == expected_counts,
            "latest_run_ids_loaded": snapshot["run_ids"] == expected_run_ids,
            "stable_source_ids": snapshot["source_ids"]
            == {
                "superstore_sales_csv": 1,
                "product_sales_region_excel": 2,
                "dummyjson_products_api": 3,
                "dataflow_technical_report_pdf": 4,
            },
            "document_id_resolved": snapshot["document_ids"].get(
                "doc_dataflow_technical_report"
            )
            == 1,
            "loader_proof_current": bool(
                load_results[-1].get("current_duy_runs_loaded")
            ),
            "rag_handoff_current": rag_manifest.get(
                "current_ingestion_run_loaded"
            )
            is True,
            "ui_fixture_current": ui_fixture.get("current_ingestion_runs_loaded")
            is True,
        }
        status = "passed" if all(checks.values()) else "failed"
    except Exception as exc:
        error = str(exc)
        checks = locals().get("checks", {})
        snapshot = locals().get("snapshot", {})
        expected_counts = locals().get("expected_counts", {})
        expected_run_ids = locals().get("expected_run_ids", [])
    finally:
        if not keep_db:
            steps["clean_after"] = _run(
                compose + ["down", "--volumes", "--remove-orphans"],
                env=env,
            )
            if steps["clean_after"]["returncode"] != 0:
                status = "failed"
                error = error or "Docker cleanup failed"

    result = {
        "status": status,
        "mode": mode,
        "schema_version": "schema_v4_fixed",
        "docker_project": project_name,
        "database_port": db_port,
        "checks": checks,
        "expected_counts": expected_counts,
        "expected_run_ids": expected_run_ids,
        "database_snapshot": snapshot,
        "load_results": [
            {
                "mode": item.get("mode"),
                "status": item.get("status"),
                "verification": item.get("verification"),
                "current_duy_runs_loaded": item.get("current_duy_runs_loaded"),
            }
            for item in load_results
        ],
        "error": error,
        "services_stopped": not keep_db,
        "steps": steps,
    }
    DEFAULT_RESULT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_RESULT.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run an isolated Docker Duy-to-Phat database integration test"
    )
    parser.add_argument(
        "--mode",
        choices=("smoke", "full", "smoke-then-full"),
        default="smoke-then-full",
    )
    parser.add_argument(
        "--project-name", default="datavision-duy-week7-integration"
    )
    parser.add_argument("--db-port", type=int, default=55432)
    parser.add_argument("--compose-file", default=str(DEFAULT_COMPOSE))
    parser.add_argument("--schema")
    parser.add_argument("--keep-db", action="store_true")
    args = parser.parse_args()
    result = run_integration(
        mode=args.mode,
        project_name=args.project_name,
        db_port=args.db_port,
        compose_file=Path(args.compose_file),
        schema_path=args.schema,
        keep_db=args.keep_db,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
