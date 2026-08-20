"""
insert_reviewer_corrections_to_postgres.py — Insert reviewer corrections into PostgreSQL.

Reads correction payloads from a JSON file (or generates sample corrections
from existing prediction results), inserts them into the reviewer_corrections
table, and queries back to prove the round-trip.

Usage:
    python scripts/insert_reviewer_corrections_to_postgres.py --dry-run
    python scripts/insert_reviewer_corrections_to_postgres.py --input corrections.json
    python scripts/insert_reviewer_corrections_to_postgres.py --from-results outputs/canonical_20_results.json
"""

import argparse
import json
import os
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
# SQL — reviewer_corrections table
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reviewer_corrections (
    id              SERIAL PRIMARY KEY,
    prediction_log_id   INTEGER NOT NULL REFERENCES prediction_logs(id),
    document_id         INTEGER,
    document_external_id TEXT,
    original_prediction  TEXT NOT NULL,
    corrected_document_type TEXT NOT NULL,
    corrected_by         TEXT NOT NULL,
    correction_reason    TEXT,
    created_at           TIMESTAMPTZ DEFAULT NOW()
);
"""

INSERT_SQL = """
INSERT INTO reviewer_corrections (
    prediction_log_id,
    document_id,
    document_external_id,
    original_prediction,
    corrected_document_type,
    corrected_by,
    correction_reason,
    created_at
) VALUES (
    %(prediction_log_id)s,
    %(document_id)s,
    %(document_external_id)s,
    %(original_prediction)s,
    %(corrected_document_type)s,
    %(corrected_by)s,
    %(correction_reason)s,
    %(created_at)s
)
RETURNING id;
"""

QUERY_BACK_SQL = """
SELECT
    rc.id,
    rc.prediction_log_id,
    rc.document_external_id,
    rc.original_prediction,
    rc.corrected_document_type,
    rc.corrected_by,
    rc.correction_reason,
    rc.created_at,
    pl.predicted_label AS log_predicted_label,
    pl.confidence_score AS log_confidence_score,
    pl.status AS log_status
FROM reviewer_corrections rc
JOIN prediction_logs pl ON rc.prediction_log_id = pl.id
ORDER BY rc.id;
"""


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

def get_connection(host, port, dbname, user, password):
    """Create a PostgreSQL connection."""
    import psycopg2
    return psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password,
    )


# ---------------------------------------------------------------------------
# Build sample corrections from canonical results
# ---------------------------------------------------------------------------

def build_sample_corrections_from_results(results_path, prediction_log_ids=None):
    """
    Build sample correction payloads from canonical results.
    
    For each needs_review result, creates a correction payload.
    If prediction_log_ids is provided, uses those IDs; otherwise uses
    sequential integers starting from 1.
    """
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    corrections = []
    log_id_counter = 0

    for result in results:
        if result.get("status") != "needs_review":
            continue

        log_id_counter += 1
        pred_log_id = (
            prediction_log_ids[log_id_counter - 1]
            if prediction_log_ids and log_id_counter <= len(prediction_log_ids)
            else log_id_counter
        )

        predicted = result.get("predicted_document_type", "unknown")
        doc_ext_id = result.get("document_external_id")

        # For evidence: keep the same label as a "confirmation" correction
        # In real usage, the reviewer would change this
        correction = build_correction_payload(
            prediction_log_id=pred_log_id,
            original_prediction=predicted,
            corrected_document_type=predicted,  # confirmation — reviewer agrees
            corrected_by="reviewer_duy",
            correction_reason=f"Reviewed and confirmed as {predicted} (manual review)",
            document_external_id=doc_ext_id,
        )
        corrections.append(correction)

    return corrections


# ---------------------------------------------------------------------------
# Insert logic
# ---------------------------------------------------------------------------

def insert_corrections(conn, corrections, dry_run=False):
    """Insert correction payloads into reviewer_corrections table."""
    inserted_ids = []

    if dry_run:
        for i, c in enumerate(corrections):
            print(f"  [DRY RUN] Row {i+1}: prediction_log_id={c['prediction_log_id']}, "
                  f"doc={c.get('document_external_id')}, "
                  f"{c['original_prediction']} -> {c['corrected_document_type']}")
        return inserted_ids

    cursor = conn.cursor()
    try:
        # Ensure table exists
        cursor.execute(CREATE_TABLE_SQL)
        conn.commit()

        for i, correction in enumerate(corrections):
            cursor.execute(INSERT_SQL, correction)
            result = cursor.fetchone()
            row_id = result[0] if result else None
            inserted_ids.append(row_id)

        conn.commit()
        print(f"  Committed {len(corrections)} reviewer corrections")

    except Exception as e:
        conn.rollback()
        print(f"  ERROR: {e}")
        raise
    finally:
        cursor.close()

    return inserted_ids


def query_back_corrections(conn):
    """Query back all corrections joined with prediction logs."""
    cursor = conn.cursor()
    try:
        cursor.execute(QUERY_BACK_SQL)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Insert reviewer corrections into PostgreSQL."
    )
    parser.add_argument(
        "--input", "-i",
        help="Path to JSON file containing correction payloads.",
    )
    parser.add_argument(
        "--from-results",
        default=os.path.join(_PROJECT_ROOT, "outputs", "canonical_20_results.json"),
        help="Build sample corrections from canonical results file.",
    )
    parser.add_argument("--host", default=os.environ.get("POSTGRES_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("POSTGRES_PORT", "5432")))
    parser.add_argument("--dbname", default=os.environ.get("POSTGRES_DB", "postgres"))
    parser.add_argument("--user", default=os.environ.get("POSTGRES_USER", "postgres"))
    parser.add_argument("--password", default=os.environ.get("POSTGRES_PASSWORD", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--output", "-o",
        default=os.path.join(_PROJECT_ROOT, "outputs", "integration", "week8_reviewer_corrections_result.json"),
        help="Output evidence file.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Load or build corrections
    if args.input:
        print(f"Loading corrections from: {args.input}")
        with open(args.input, "r", encoding="utf-8") as f:
            corrections = json.load(f)
    else:
        print(f"Building sample corrections from: {args.from_results}")
        corrections = build_sample_corrections_from_results(args.from_results)

    print(f"Found {len(corrections)} corrections\n")

    if not corrections:
        print("No corrections to insert.")
        return

    # 2. Preview
    print("=== Preview (first 3 corrections) ===")
    for i, c in enumerate(corrections[:3]):
        print(f"  [{i+1}] prediction_log_id={c['prediction_log_id']}, "
              f"doc={c.get('document_external_id', 'N/A')}")
        print(f"      {c['original_prediction']} -> {c['corrected_document_type']}")
    if len(corrections) > 3:
        print(f"  ... and {len(corrections) - 3} more")
    print()

    # 3. Dry run or insert
    if args.dry_run:
        print("=== DRY RUN MODE ===\n")
        insert_corrections(conn=None, corrections=corrections, dry_run=True)
        print(f"\nDry run complete. {len(corrections)} rows would be inserted.")
        return

    # 4. Connect and insert
    print(f"Connecting to PostgreSQL: {args.user}@{args.host}:{args.port}/{args.dbname}")
    conn = get_connection(
        host=args.host, port=args.port, dbname=args.dbname,
        user=args.user, password=args.password,
    )

    try:
        inserted_ids = insert_corrections(conn, corrections)
        print(f"\nInserted {len(inserted_ids)} corrections")
        print(f"Row IDs: {inserted_ids}")

        # Query back
        print("\n=== Query-back verification ===")
        query_results = query_back_corrections(conn)
        print(f"Found {len(query_results)} corrections in database")

        for qr in query_results[:5]:
            print(f"  id={qr['id']}, prediction_log_id={qr['prediction_log_id']}, "
                  f"doc={qr['document_external_id']}, "
                  f"{qr['original_prediction']} -> {qr['corrected_document_type']}")

        # Save evidence
        evidence = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_corrections_inserted": len(inserted_ids),
            "inserted_ids": inserted_ids,
            "total_corrections_queried_back": len(query_results),
            "query_back_results": query_results,
        }

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(evidence, f, indent=2, default=str)
        print(f"\nEvidence written to: {args.output}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
