#!/usr/bin/env python3
"""
Week 7 Task 2 - One-Command Database Setup
=============================================

Orchestrates the full Week 7 database bring-up sequence:

  1. Reset database              -> reset_database_v2.sql
  2. Enable pgvector              \
  3. Create schema                 } -> setup_database_v3.sql
  4. Create analytics views       /
  5. Load Duy sample/real outputs -> load_data.py
  6. Load Tuong prediction logs   -> insert_prediction_logs_to_postgres.py
  7. (Optional) Load Lap document chunks + test RAG query
  8. Run validation queries       -> validation_queries_v3.sql
  9. Export dashboard view samples -> export_dashboard_views.py

Usage
-----
    python run_database_setup.py
    python run_database_setup.py --skip-lap
    python run_database_setup.py --smoke
    python run_database_setup.py --dbname datavision_db --host localhost --port 5432

All file paths default to the locations already in use on this machine
(see the CONFIG section below). Override any of them with CLI flags if
your paths differ.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# --------------------------------------------------------------------------
# CONFIG - defaults match the current Week 7 working paths
# --------------------------------------------------------------------------

BASE = Path(r"week7")

DEFAULT_PATHS = {
    "reset_sql": BASE / "database" / "scripts" / "reset_database_v2.sql",
    "setup_sql": BASE / "database" / "schema" / "setup_database_v3.sql",
    "validation_sql": BASE / "database" / "validation" / "validation_queries_v3.sql",

    "load_data_py": BASE / "scripts" / "load_data.py",
    "insert_predictions_py": BASE / "scripts" / "insert_prediction_logs_to_postgres.py",
    "prediction_input_json": BASE / "scripts" / "week6_duy_prediction_results.json",

    "load_chunks_py": BASE / "scripts" / "load_document_pages_to_pgvector.py",
    "document_pages_jsonl": BASE / "scripts" / "document_pages.jsonl",
    "test_rag_query_py": BASE / "database" / "scripts" / "test_rag_query.py",

    "export_views_py": BASE / "database" / "scripts" / "export_dashboard_views.py",
}

DEFAULT_DB = {
    "host": "localhost",
    "port": "5432",
    "user": "datavision",
    "password": "datavision123",
    "dbname": "datavision_db",
}

DOCUMENT_EXTERNAL_ID_LAP = "doc_dataflow_technical_report"
DOCUMENT_EXTERNAL_ID_RAG = "doc_dataflow_technical_report"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

class StepFailed(Exception):
    pass


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run_cmd(cmd, step_name, env=None, critical=True):
    """Run a subprocess command, streaming output. Raises StepFailed on error
    if critical=True, otherwise just warns and returns False."""
    log(f"--- Running: {step_name} ---")
    log("Command: " + " ".join(str(c) for c in cmd))
    try:
        result = subprocess.run(cmd, env=env)
    except FileNotFoundError as e:
        msg = f"{step_name} failed to start: {e}"
        if critical:
            raise StepFailed(msg)
        log(f"WARNING (non-critical): {msg}")
        return False

    if result.returncode != 0:
        msg = f"{step_name} exited with code {result.returncode}"
        if critical:
            raise StepFailed(msg)
        log(f"WARNING (non-critical): {msg}")
        return False

    return True


def run_psql_file(sql_file: Path, db, step_name, critical=True):
    if not sql_file.exists():
        msg = f"{step_name}: SQL file not found at {sql_file}"
        if critical:
            raise StepFailed(msg)
        log(f"WARNING (non-critical): {msg}")
        return False

    env = os.environ.copy()
    env["PGPASSWORD"] = db["password"]

    cmd = [
        "psql",
        "-h", db["host"],
        "-p", db["port"],
        "-U", db["user"],
        "-d", db["dbname"],
        "-v", "ON_ERROR_STOP=1",
        "-f", str(sql_file),
    ]
    return run_cmd(cmd, step_name, env=env, critical=critical)


def run_python_script(script: Path, args, step_name, critical=True, env=None):
    if not script.exists():
        msg = f"{step_name}: script not found at {script}"
        if critical:
            raise StepFailed(msg)
        log(f"WARNING (non-critical): {msg}")
        return False

    cmd = [sys.executable, str(script)] + [str(a) for a in args]
    return run_cmd(cmd, step_name, critical=critical, env=env)


# --------------------------------------------------------------------------
# main orchestration
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Week 7 one-command database setup")

    # DB connection
    parser.add_argument("--host", default=DEFAULT_DB["host"])
    parser.add_argument("--port", default=DEFAULT_DB["port"])
    parser.add_argument("--user", default=DEFAULT_DB["user"])
    parser.add_argument("--password", default=DEFAULT_DB["password"])
    parser.add_argument("--dbname", default=DEFAULT_DB["dbname"])

    # File paths (override defaults if needed)
    for key, default in DEFAULT_PATHS.items():
        parser.add_argument(f"--{key.replace('_', '-')}", default=str(default))

    # Behavior flags
    parser.add_argument("--smoke", action="store_true",
                         help="Load smoke-sized sample data instead of full dataset "
                              "(passed through to load_data.py as --smoke).")
    parser.add_argument("--skip-lap", action="store_true",
                         help="Skip loading Lap's document chunks / RAG smoke query "
                              "(step 7 is optional).")
    parser.add_argument("--skip-export", action="store_true",
                         help="Skip exporting dashboard view samples (step 9).")

    args = parser.parse_args()

    db = {
        "host": args.host,
        "port": args.port,
        "user": args.user,
        "password": args.password,
        "dbname": args.dbname,
    }

    paths = {key: Path(getattr(args, key)) for key in DEFAULT_PATHS}

    log("=" * 70)
    log("Week 7 Database Setup - starting fresh setup from zero")
    log(f"Target DB: {db['user']}@{db['host']}:{db['port']}/{db['dbname']}")
    log("=" * 70)

    try:
        # 1. Reset database
        run_psql_file(paths["reset_sql"], db, "Step 1/9: Reset database")
        log("Database reset completed")

        # 2-4. Enable pgvector + create schema + create analytics views
        run_psql_file(paths["setup_sql"], db,
                      "Step 2-4/9: Enable pgvector, create schema, create views")
        log("Schema created")
        log("Views created")

        # 5. Load Duy sample/real outputs
        load_data_args = ["--smoke", "--limit-structured-records", "100"] if args.smoke else []
        run_python_script(paths["load_data_py"], load_data_args,
                           "Step 5/9: Load Duy sample/real outputs")
        log("Duy data loaded")

        # 6. Load Tuong prediction logs
        run_python_script(
            paths["insert_predictions_py"],
            ["--input", paths["prediction_input_json"]],
            "Step 6/9: Load Tuong prediction logs",
        )
        log("Prediction logs loaded")

        # 7. Optionally load Lap document chunks + RAG smoke query
        if not args.skip_lap:
            lap_env = os.environ.copy()
            lap_env["PYTHONPATH"] = str(BASE / "scripts")
            lap_ok = run_python_script(
                paths["load_chunks_py"],
                [
                    "--document-pages", paths["document_pages_jsonl"],
                    "--document-external-id", DOCUMENT_EXTERNAL_ID_LAP,
                    "--chunk-size", "512",
                    "--overlap", "50",
                ],
                "Step 7/9: Load Lap document chunks (optional)",
                critical=False,
                env=lap_env
            )
            if lap_ok:
                run_python_script(
                    paths["test_rag_query_py"],
                    [
                        "--query", "What is the DataFlow pipeline?",
                        "--document-external-id", DOCUMENT_EXTERNAL_ID_RAG,
                    ],
                    "Step 7/9: Test RAG query (optional)",
                    critical=False,
                    env=lap_env
                )
        else:
            log("Step 7/9: Skipped (--skip-lap)")

        # 8. Run validation queries
        run_psql_file(paths["validation_sql"], db, "Step 8/9: Run validation queries")
        log("Validation passed")

        # 9. Export dashboard view samples
        if not args.skip_export:
            run_python_script(
                paths["export_views_py"], [],
                "Step 9/9: Export dashboard view samples",
            )
            log("Dashboard samples exported")
        else:
            log("Step 9/9: Skipped (--skip-export)")

        log("=" * 70)
        log("Week 7 database setup completed successfully.")
        log("Phat's database is reproducible from zero and ready for CI.")
        log("=" * 70)
        return 0

    except StepFailed as e:
        log("!" * 70)
        log(f"SETUP FAILED: {e}")
        log("!" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())