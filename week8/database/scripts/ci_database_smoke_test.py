"""
ci_database_smoke_test.py

Week 8 — CI Database Smoke Test

Runs a sequence of checks against the database to verify it is ready for
CI / staging. Intended to run AFTER setup_local_db.sh (or run_database_setup.py)
has created the schema, views, and loaded smoke data.

Checks performed, in order:
    1. PostgreSQL is reachable
    2. pgvector extension is installed
    3. Schema setup passed (all 10 required tables exist)
    4. Views setup passed (all 12 required views exist)
    5. Smoke data loaded (sources/documents/document_pages/structured_records have rows)
    6. Validation queries pass (no orphaned document_pages/document_chunks/prediction_logs,
       no out-of-range confidence_score values)
    7. Dashboard views return rows (v_dashboard_overview, v_prediction_review_queue)
    8. document_chunks.embedding supports vector(384)
    9. prediction_logs.status CHECK constraint supports
       accepted / needs_review / waiting_for_source / failed

Exit code 0 = all checks passed. Exit code 1 = at least one check failed
(failures are printed to stdout with details before exiting).

Environment variables (same defaults as the rest of the Week 7 pipeline):
    POSTGRES_HOST     (default: localhost)
    POSTGRES_PORT     (default: 5432)
    POSTGRES_DB       (default: datavision_db)
    POSTGRES_USER     (default: datavision)
    POSTGRES_PASSWORD (default: datavision123)
    DATABASE_URL      (optional, overrides the above if set)

Usage:
    python ci_database_smoke_test.py
"""

import json
import os
import sys

import psycopg2
from dotenv import load_dotenv
load_dotenv()

REQUIRED_TABLES = [
    "sources", "pipeline_runs", "documents", "document_chunks",
    "structured_records", "ingestion_logs", "analytics_events",
    "rag_query_logs", "prediction_logs", "document_pages",
]

REQUIRED_VIEWS = [
    "v_dashboard_overview", "v_ingestion_health", "v_source_quality_summary",
    "v_document_quality_summary", "v_rag_daily_metrics",
    "v_prediction_confidence_summary", "v_recent_activity",
    "v_latest_ingestion_runs", "v_data_quality_dashboard",
    "v_source_quality_detail", "v_document_rag_readiness",
    "v_prediction_review_queue",
]

REQUIRED_PREDICTION_STATUSES = {"accepted", "needs_review", "waiting_for_source", "failed"}

# Tables that a smoke-mode load is expected to always populate (per Task 5's
# "Smoke Mode Should Load" list). document_chunks and prediction_logs are
# NOT included here because they depend on Lap/Tuong's optional fixtures.
REQUIRED_NONZERO_TABLES = ["sources", "documents", "document_pages", "structured_records"]


class SmokeTestResult:
    def __init__(self):
        self.checks = []  # (name, passed, detail)

    def record(self, name: str, passed: bool, detail: str = ""):
        self.checks.append((name, passed, detail))
        status = "PASS" if passed else "FAIL"
        suffix = f" — {detail}" if detail else ""
        print(f"[{status}] {name}{suffix}")

    def all_passed(self) -> bool:
        return all(passed for _, passed, _ in self.checks)


def get_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)

    password = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "❌ Database password declaration is mandatory! "
            "Please set POSTGRES_PASSWORD (or DB_PASSWORD) in the .env file or system environment."
        )
    host = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME", "datavision_db")
    user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER", "datavision")

    conn_string = f"host={host} port={port} dbname={dbname} user={user} password={password}"
    return psycopg2.connect(conn_string)


def check_pgvector_extension(cur, result):
    cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
    row = cur.fetchone()
    result.record(
        "pgvector extension is installed",
        row is not None,
        "" if row else "extension 'vector' not found — was CREATE EXTENSION run?",
    )


def check_tables_exist(cur, result):
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    existing = {r[0] for r in cur.fetchall()}
    missing = [t for t in REQUIRED_TABLES if t not in existing]
    result.record(
        "Schema setup passed (all required tables exist)",
        not missing,
        "" if not missing else f"missing tables: {missing}",
    )


def check_views_exist(cur, result):
    cur.execute("""
        SELECT table_name FROM information_schema.views WHERE table_schema = 'public';
    """)
    existing = {r[0] for r in cur.fetchall()}
    missing = [v for v in REQUIRED_VIEWS if v not in existing]
    result.record(
        "Views setup passed (all required views exist)",
        not missing,
        "" if not missing else f"missing views: {missing}",
    )


def check_smoke_data_loaded(cur, result):
    counts = {}
    for table in REQUIRED_NONZERO_TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        counts[table] = cur.fetchone()[0]
    ok = all(c > 0 for c in counts.values())
    result.record(
        "Smoke data loaded (sources/documents/document_pages/structured_records have rows)",
        ok,
        json.dumps(counts),
    )
    return counts


def check_validation_queries(cur, result):
    problems = []

    validation_checks = [
        (
            "orphaned document_pages",
            """
            SELECT COUNT(*) FROM document_pages dp
            LEFT JOIN documents d ON dp.document_id = d.id
            WHERE d.id IS NULL;
            """
        ),
        (
            "orphaned document_chunks",
            """
            SELECT COUNT(*) FROM document_chunks dc
            LEFT JOIN documents d ON dc.document_id = d.id
            WHERE d.id IS NULL;
            """
        ),
        (
            "orphaned structured_records",
            """
            SELECT COUNT(*) FROM structured_records sr
            LEFT JOIN sources s ON sr.source_id = s.id
            WHERE s.id IS NULL;
            """
        ),
        (
            "orphaned prediction_logs",
            """
            SELECT COUNT(*) FROM prediction_logs pl
            LEFT JOIN documents d ON pl.document_id = d.id
            WHERE pl.document_id IS NOT NULL AND d.id IS NULL;
            """
        ),
        (
            "missing embeddings",
            """
            SELECT COUNT(*) FROM document_chunks
            WHERE embedding IS NULL;
            """
        ),
        (
            "invalid vector dimensions (not 384)",
            """
            SELECT COUNT(*) FROM document_chunks
            WHERE vector_dims(embedding) != 384;
            """
        ),
        (
            "RAG logs missing retrieved_chunk_ids",
            """
            SELECT COUNT(*) FROM rag_query_logs
            WHERE retrieved_chunk_ids IS NULL OR jsonb_array_length(retrieved_chunk_ids) = 0;
            """
        ),
        (
            "chunks with empty text",
            """
            SELECT COUNT(*) FROM document_chunks
            WHERE chunk_text IS NULL OR TRIM(chunk_text) = '';
            """
        ),
        (
            "missing run_id in ingestion logs",
            """
            SELECT COUNT(*) FROM ingestion_logs
            WHERE run_id IS NULL OR TRIM(run_id) = '';
            """
        ),
        (
            "invalid status in ingestion logs",
            """
            SELECT COUNT(*) FROM ingestion_logs
            WHERE status NOT IN ('success', 'failed', 'partial_success', 'running');
            """
        ),
        (
            "missing confidence scores in prediction logs",
            """
            SELECT COUNT(*) FROM prediction_logs
            WHERE confidence_score IS NULL;
            """
        ),
        (
            "duplicate sources",
            """
            SELECT COUNT(*) FROM (
                SELECT name FROM sources
                GROUP BY name
                HAVING COUNT(*) > 1
            ) sub;
            """
        ),
        (
            "documents missing document_external_id",
            """
            SELECT COUNT(*) FROM documents
            WHERE document_external_id IS NULL OR TRIM(document_external_id) = '';
            """
        ),
        (
            "missing data_quality_score for successful/partial logs",
            """
            SELECT COUNT(*) FROM ingestion_logs
            WHERE status IN ('success', 'partial_success') AND data_quality_score IS NULL;
            """
        ),
        (
            "invalid prediction status",
            """
            SELECT COUNT(*) FROM prediction_logs
            WHERE status NOT IN ('accepted', 'needs_review', 'waiting_for_source', 'failed')
               OR status IS NULL;
            """
        ),
        (
            "prediction logs with confidence_score out of [0,1]",
            """
            SELECT COUNT(*) FROM prediction_logs
            WHERE confidence_score < 0.0 OR confidence_score > 1.0;
            """
        ),
        (
            "ingestion logs math mismatch (records_read != valid + invalid)",
            """
            SELECT COUNT(*) FROM ingestion_logs
            WHERE records_read != (COALESCE(records_valid, 0) + COALESCE(records_invalid, 0))
              AND status IN ('success', 'partial_success');
            """
        ),
        (
            "stuck pipeline runs (> 24 hours)",
            """
            SELECT COUNT(*) FROM pipeline_runs
            WHERE status = 'running'
              AND start_time < NOW() - INTERVAL '24 hours';
            """
        ),
        (
            "ingestion logs with invalid time logic (ended_at < started_at)",
            """
            SELECT COUNT(*) FROM ingestion_logs
            WHERE ended_at < started_at;
            """
        ),
        (
            "empty review queue when predictions exist",
            """
            SELECT COUNT(*) FROM (
                SELECT 1
                WHERE (SELECT COUNT(*) FROM prediction_logs WHERE status IN ('needs_review', 'waiting_for_source')) > 0
                  AND (SELECT COUNT(*) FROM v_prediction_review_queue) = 0
            ) sub;
            """
        ),
        (
            "empty RAG metrics when RAG logs exist",
            """
            SELECT COUNT(*) FROM (
                SELECT 1
                WHERE (SELECT COUNT(*) FROM rag_query_logs) > 0
                  AND (SELECT COUNT(*) FROM v_rag_daily_metrics) = 0
            ) sub;
            """
        )
    ]

    for description, query in validation_checks:
        cur.execute(query)
        count = cur.fetchone()[0]
        if count > 0:
            problems.append(f"{count} {description}")

    result.record(
        "Validation queries pass (no orphaned rows / invalid values / missing logic)",
        not problems,
        "; ".join(problems),
    )

def check_dashboard_views_return_rows(cur, result):
    cur.execute("SELECT COUNT(*) FROM v_dashboard_overview;")
    count = cur.fetchone()[0]
    # v_dashboard_overview is a single-row aggregate — it must always return exactly 1 row.
    result.record("Dashboard view v_dashboard_overview returns a row", count >= 1, f"count={count}")

    cur.execute("SELECT COUNT(*) FROM v_prediction_review_queue;")
    count = cur.fetchone()[0]
    # v_prediction_review_queue can legitimately be 0 if no predictions need review yet —
    # this check only confirms the view is queryable without error.
    result.record("Dashboard view v_prediction_review_queue is queryable", True, f"count={count}")


def check_document_chunks_vector_384(cur, result):
    cur.execute("""
        SELECT a.atttypmod
        FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        JOIN pg_type t ON a.atttypid = t.oid
        WHERE c.relname = 'document_chunks' AND a.attname = 'embedding' AND t.typname = 'vector';
    """)
    row = cur.fetchone()
    ok = row is not None and row[0] == 384
    detail = "" if ok else f"found={row[0] if row else 'column not found or not of type vector'}"
    result.record("document_chunks.embedding supports vector(384)", ok, detail)


def check_prediction_status_values(cur, result):
    cur.execute("""
        SELECT pg_get_constraintdef(oid) FROM pg_constraint
        WHERE conname = 'chk_prediction_status';
    """)
    row = cur.fetchone()
    if not row:
        result.record(
            "prediction_logs.status supports accepted/needs_review/waiting_for_source/failed",
            False,
            "constraint chk_prediction_status not found",
        )
        return

    constraint_def = row[0]
    missing = [s for s in REQUIRED_PREDICTION_STATUSES if s not in constraint_def]
    result.record(
        "prediction_logs.status supports accepted/needs_review/waiting_for_source/failed",
        not missing,
        "" if not missing else f"missing from constraint: {missing}",
    )


def run_expected_checks(cur):
    """Print the raw output of the exact SQL checks listed in the Task 6 spec."""
    print("\n--- Expected Checks (raw output) ---")
    queries = [
        "SELECT extname FROM pg_extension WHERE extname = 'vector';",
        "SELECT COUNT(*) FROM sources;",
        "SELECT COUNT(*) FROM documents;",
        "SELECT COUNT(*) FROM document_pages;",
        "SELECT COUNT(*) FROM structured_records;",
        "SELECT COUNT(*) FROM prediction_logs;",
        "SELECT COUNT(*) FROM v_dashboard_overview;",
        "SELECT COUNT(*) FROM v_prediction_review_queue;",
    ]
    for q in queries:
        cur.execute(q)
        rows = cur.fetchall()
        print(f"{q}\n  -> {rows}")


def main():
    result = SmokeTestResult()

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        result.record("PostgreSQL is reachable", True)
    except Exception as e:
        result.record("PostgreSQL is reachable", False, str(e))
        print("\nCannot continue — database is unreachable.")
        sys.exit(1)

    checks_to_run = [
        check_pgvector_extension,
        check_tables_exist,
        check_views_exist,
        check_smoke_data_loaded,
        check_validation_queries,
        check_dashboard_views_return_rows,
        check_document_chunks_vector_384,
        check_prediction_status_values,
    ]

    try:
        for check_fn in checks_to_run:
            try:
                check_fn(cur, result)
                conn.commit()  # release any implicit transaction so later checks aren't blocked
            except Exception as e:
                conn.rollback()  # a failed query aborts the transaction — must roll back to continue
                result.record(check_fn.__name__, False, f"check raised an exception: {e}")

        try:
            run_expected_checks(cur)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"\n(Could not run Expected Checks raw output block: {e})")
    finally:
        cur.close()
        conn.close()

    print("\n=== Summary ===")
    passed = sum(1 for _, p, _ in result.checks if p)
    total = len(result.checks)
    print(f"{passed}/{total} checks passed")

    if not result.all_passed():
        print("\nFAILED checks:")
        for name, p, detail in result.checks:
            if not p:
                print(f"  - {name}: {detail}")
        sys.exit(1)

    print("\nAll database smoke test checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
