"""
week8_prediction_db_round_trip.py — Prove prediction INSERT + query-back + correction round-trip.

This script:
  1. Applies the prediction_logs table schema.
  2. Inserts all 20 prediction log payloads.
  3. Queries back all 20 rows.
  4. Creates the reviewer_corrections table.
  5. Inserts sample corrections for needs_review items.
  6. Queries back corrections joined with prediction logs.
  7. Outputs evidence JSON.

Usage:
    python scripts/week8_prediction_db_round_trip.py
    python scripts/week8_prediction_db_round_trip.py --dry-run

Environment variables for DB connection:
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    (or DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Resolve project root
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.reviewer_corrections import build_correction_payload

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PREDICTION_LOG_PAYLOADS_PATH = os.path.join(
    _PROJECT_ROOT, "outputs", "db_integration", "week7_prediction_log_payloads.json"
)
EVIDENCE_OUTPUT_PATH = os.path.join(
    _PROJECT_ROOT, "outputs", "integration", "week8_prediction_db_round_trip.json"
)

# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

CREATE_PREDICTION_LOGS_SQL = """
CREATE TABLE IF NOT EXISTS prediction_logs (
    id                  SERIAL PRIMARY KEY,
    source_id           INTEGER,
    document_external_id TEXT,
    document_id         INTEGER,
    model_name          TEXT NOT NULL,
    model_version       TEXT NOT NULL,
    input_payload       JSONB,
    prediction_result   JSONB,
    predicted_label     TEXT,
    confidence_score    FLOAT,
    status              TEXT NOT NULL,
    review_reason       TEXT,
    ingestion_run_id    TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
"""

CREATE_REVIEWER_CORRECTIONS_SQL = """
CREATE TABLE IF NOT EXISTS reviewer_corrections (
    id                   SERIAL PRIMARY KEY,
    prediction_log_id    INTEGER NOT NULL REFERENCES prediction_logs(id),
    document_id          INTEGER,
    document_external_id TEXT,
    original_prediction  TEXT NOT NULL,
    corrected_document_type TEXT NOT NULL,
    corrected_by         TEXT NOT NULL,
    correction_reason    TEXT,
    created_at           TIMESTAMPTZ DEFAULT NOW()
);
"""

INSERT_PREDICTION_LOG_SQL = """
INSERT INTO prediction_logs (
    source_id, document_external_id, document_id,
    model_name, model_version, input_payload, prediction_result,
    predicted_label, confidence_score, status, review_reason,
    ingestion_run_id, created_at
) VALUES (
    %(source_id)s, %(document_external_id)s, %(document_id)s,
    %(model_name)s, %(model_version)s, %(input_payload)s, %(prediction_result)s,
    %(predicted_label)s, %(confidence_score)s, %(status)s, %(review_reason)s,
    %(ingestion_run_id)s, %(created_at)s
)
RETURNING id;
"""

INSERT_CORRECTION_SQL = """
INSERT INTO reviewer_corrections (
    prediction_log_id, document_id, document_external_id,
    original_prediction, corrected_document_type,
    corrected_by, correction_reason, created_at
) VALUES (
    %(prediction_log_id)s, %(document_id)s, %(document_external_id)s,
    %(original_prediction)s, %(corrected_document_type)s,
    %(corrected_by)s, %(correction_reason)s, %(created_at)s
)
RETURNING id;
"""

QUERY_PREDICTION_LOGS_SQL = """
SELECT id, source_id, document_external_id, document_id,
       model_name, model_version, predicted_label, confidence_score,
       status, review_reason, ingestion_run_id, created_at
FROM prediction_logs
ORDER BY id;
"""

QUERY_CORRECTIONS_WITH_LOGS_SQL = """
SELECT
    rc.id AS correction_id,
    rc.prediction_log_id,
    rc.document_external_id,
    rc.original_prediction,
    rc.corrected_document_type,
    rc.corrected_by,
    rc.correction_reason,
    rc.created_at AS correction_created_at,
    pl.predicted_label AS log_predicted_label,
    pl.confidence_score AS log_confidence_score,
    pl.status AS log_status
FROM reviewer_corrections rc
JOIN prediction_logs pl ON rc.prediction_log_id = pl.id
ORDER BY rc.id;
"""


def get_git_sha():
    """Retrieve current Git commit SHA."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_PROJECT_ROOT,
            capture_output=True, text=True, check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown-sha"


def get_connection(host, port, dbname, user, password):
    """Create a PostgreSQL connection."""
    import psycopg2
    return psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password,
    )


def load_prediction_log_payloads():
    """Load prediction log payloads from the DB integration output."""
    with open(PREDICTION_LOG_PAYLOADS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("prediction_log_payloads", [])


def run_dry_run(log_payloads):
    """Print what would be inserted without DB access."""
    print("\n=== DRY RUN: Prediction Logs ===")
    for i, lp in enumerate(log_payloads):
        doc_id = lp.get("document_external_id") or "N/A"
        pred = lp.get("predicted_label") or "N/A"
        print(f"  [{i+1:2d}] {doc_id:<50s} "
              f"predicted={pred:<20s} "
              f"status={lp.get('status')}")

    needs_review = [lp for lp in log_payloads if lp.get("status") == "needs_review"]
    print(f"\n=== DRY RUN: Reviewer Corrections ({len(needs_review)} items) ===")
    for i, lp in enumerate(needs_review[:5]):
        doc_id = lp.get("document_external_id") or "N/A"
        pred = lp.get("predicted_label") or "N/A"
        print(f"  [{i+1}] prediction_log_id=<TBD>, "
              f"doc={doc_id}, "
              f"{pred} -> {pred} (confirmed)")
    if len(needs_review) > 5:
        print(f"  ... and {len(needs_review) - 5} more")

    print(f"\nDry run complete. {len(log_payloads)} prediction logs and "
          f"{len(needs_review)} corrections would be inserted.")


def run_round_trip(conn, log_payloads):
    """Execute the full INSERT + query-back round-trip."""
    from psycopg2.extras import Json

    cursor = conn.cursor()
    evidence = {
        "release_sha": get_git_sha(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        # Step 1: Create tables
        print("\n[1/6] Creating prediction_logs table...")
        cursor.execute(CREATE_PREDICTION_LOGS_SQL)
        conn.commit()
        print("  Done")

        # Step 2: Insert prediction logs
        print(f"\n[2/6] Inserting {len(log_payloads)} prediction log payloads...")
        inserted_log_ids = []
        for lp in log_payloads:
            row = {
                "source_id": lp.get("source_id"),
                "document_external_id": lp.get("document_external_id"),
                "document_id": lp.get("document_id"),
                "model_name": lp.get("model_name", "document_classifier"),
                "model_version": lp.get("model_version", "unknown"),
                "input_payload": Json(lp.get("input_payload", {})),
                "prediction_result": Json(lp.get("prediction_result", {})),
                "predicted_label": lp.get("predicted_label"),
                "confidence_score": lp.get("confidence_score", 0.0),
                "status": lp.get("status", "failed"),
                "review_reason": lp.get("review_reason"),
                "ingestion_run_id": lp.get("ingestion_run_id"),
                "created_at": lp.get("created_at", datetime.now(timezone.utc).isoformat()),
            }
            cursor.execute(INSERT_PREDICTION_LOG_SQL, row)
            result = cursor.fetchone()
            inserted_log_ids.append(result[0] if result else None)
        conn.commit()
        print(f"  Inserted {len(inserted_log_ids)} rows: {inserted_log_ids}")
        evidence["prediction_log_ids"] = inserted_log_ids

        # Step 3: Query back prediction logs
        print(f"\n[3/6] Querying back prediction logs...")
        cursor.execute(QUERY_PREDICTION_LOGS_SQL)
        columns = [desc[0] for desc in cursor.description]
        queried_logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
        print(f"  Retrieved {len(queried_logs)} rows")
        assert len(queried_logs) == len(log_payloads), \
            f"Expected {len(log_payloads)} rows, got {len(queried_logs)}"
        evidence["prediction_logs_queried_back"] = len(queried_logs)

        # Step 4: Create reviewer_corrections table
        print(f"\n[4/6] Creating reviewer_corrections table...")
        cursor.execute(CREATE_REVIEWER_CORRECTIONS_SQL)
        conn.commit()
        print("  Done")

        # Step 5: Insert sample corrections for needs_review items
        print(f"\n[5/6] Building and inserting reviewer corrections...")
        needs_review_logs = [
            (log_id, lp) for log_id, lp in zip(inserted_log_ids, log_payloads)
            if lp.get("status") == "needs_review" and log_id is not None
        ]
        print(f"  Found {len(needs_review_logs)} needs_review items")

        inserted_correction_ids = []
        for log_id, lp in needs_review_logs:
            correction = build_correction_payload(
                prediction_log_id=log_id,
                original_prediction=lp.get("predicted_label", "unknown"),
                corrected_document_type=lp.get("predicted_label", "unknown"),
                corrected_by="reviewer_duy",
                correction_reason=f"Reviewed and confirmed as {lp.get('predicted_label')}",
                document_external_id=lp.get("document_external_id"),
            )
            cursor.execute(INSERT_CORRECTION_SQL, correction)
            result = cursor.fetchone()
            inserted_correction_ids.append(result[0] if result else None)
        conn.commit()
        print(f"  Inserted {len(inserted_correction_ids)} corrections: {inserted_correction_ids}")
        evidence["correction_ids"] = inserted_correction_ids

        # Step 6: Query back corrections with log join
        print(f"\n[6/6] Querying back corrections joined with prediction logs...")
        cursor.execute(QUERY_CORRECTIONS_WITH_LOGS_SQL)
        columns = [desc[0] for desc in cursor.description]
        queried_corrections = [dict(zip(columns, row)) for row in cursor.fetchall()]
        print(f"  Retrieved {len(queried_corrections)} corrections")

        for qc in queried_corrections[:5]:
            print(f"    id={qc['correction_id']}, prediction_log_id={qc['prediction_log_id']}, "
                  f"doc={qc.get('document_external_id', 'N/A')}, "
                  f"{qc['original_prediction']} -> {qc['corrected_document_type']}")
        if len(queried_corrections) > 5:
            print(f"    ... and {len(queried_corrections) - 5} more")

        evidence["corrections_queried_back"] = len(queried_corrections)
        evidence["status"] = "passed"
        evidence["summary"] = {
            "prediction_logs_inserted": len(inserted_log_ids),
            "prediction_logs_queried": len(queried_logs),
            "corrections_inserted": len(inserted_correction_ids),
            "corrections_queried": len(queried_corrections),
        }

    except Exception as e:
        conn.rollback()
        evidence["status"] = "failed"
        evidence["error"] = str(e)
        raise
    finally:
        cursor.close()

    return evidence


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prediction DB round-trip proof: INSERT + query-back."
    )
    parser.add_argument("--host", default=os.environ.get("POSTGRES_HOST",
                        os.environ.get("DB_HOST", "localhost")))
    parser.add_argument("--port", type=int, default=int(os.environ.get("POSTGRES_PORT",
                        os.environ.get("DB_PORT", "5432"))))
    parser.add_argument("--dbname", default=os.environ.get("POSTGRES_DB",
                        os.environ.get("DB_NAME", "datavision_db")))
    parser.add_argument("--user", default=os.environ.get("POSTGRES_USER",
                        os.environ.get("DB_USER", "datavision")))
    parser.add_argument("--password", default=os.environ.get("POSTGRES_PASSWORD",
                        os.environ.get("DB_PASSWORD", "datavision123")))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", "-o", default=EVIDENCE_OUTPUT_PATH)
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 70)
    print("Week 8: Prediction DB Round-Trip Proof")
    print("=" * 70)

    # Load payloads
    print(f"\nLoading prediction log payloads from: {PREDICTION_LOG_PAYLOADS_PATH}")
    log_payloads = load_prediction_log_payloads()
    print(f"Found {len(log_payloads)} payloads")

    if args.dry_run:
        run_dry_run(log_payloads)
        return

    # Connect
    print(f"\nConnecting to: {args.user}@{args.host}:{args.port}/{args.dbname}")
    conn = get_connection(
        host=args.host, port=args.port, dbname=args.dbname,
        user=args.user, password=args.password,
    )

    try:
        evidence = run_round_trip(conn, log_payloads)

        # Save evidence
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(evidence, f, indent=2, default=str)
        print(f"\nEvidence written to: {args.output}")

        print("\n=== Round-Trip Summary ===")
        s = evidence.get("summary", {})
        print(f"  Prediction logs: {s.get('prediction_logs_inserted')} inserted, "
              f"{s.get('prediction_logs_queried')} queried back")
        print(f"  Corrections:     {s.get('corrections_inserted')} inserted, "
              f"{s.get('corrections_queried')} queried back")
        print(f"  Status: {evidence.get('status')}")

    finally:
        conn.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()
