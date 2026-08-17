import argparse
import json
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()
# ---------------------------------------------------------------------------
# Resolve project root
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ---------------------------------------------------------------------------
# SQL — matches prediction_log_contract.md schema_v4
# ---------------------------------------------------------------------------

INSERT_SQL = """
INSERT INTO prediction_logs (
    source_id,
    document_external_id,
    document_id,
    model_name,
    model_version,
    input_payload,
    prediction_result,
    predicted_label,
    confidence_score,
    status,
    review_reason,
    ingestion_run_id,
    created_at
) VALUES (
    %(source_id)s,
    %(document_external_id)s,
    %(document_id)s,
    %(model_name)s,
    %(model_version)s,
    %(input_payload)s,
    %(prediction_result)s,
    %(predicted_label)s,
    %(confidence_score)s,
    %(status)s,
    %(review_reason)s,
    %(ingestion_run_id)s,
    %(created_at)s
)
ON CONFLICT (document_external_id, ingestion_run_id, model_name) DO UPDATE SET
    prediction_result = EXCLUDED.prediction_result,
    predicted_label   = EXCLUDED.predicted_label,
    confidence_score  = EXCLUDED.confidence_score,
    status            = EXCLUDED.status,
    review_reason     = EXCLUDED.review_reason
RETURNING id;
"""


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

def get_connection(host: str, port: int, dbname: str, user: str, password: str):
    """Create a PostgreSQL connection using psycopg2."""
    import psycopg2

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )
    return conn


# ---------------------------------------------------------------------------
# Row preparation
# ---------------------------------------------------------------------------

def resolve_source_id(cur, source_name):
    """Look up sources.id by name. Returns None if not found (does not raise)."""
    if not source_name or not cur:
        return None
    cur.execute("SELECT id FROM sources WHERE name = %s", (source_name,))
    row = cur.fetchone()
    return row[0] if row else None


def resolve_document_db_id(cur, document_external_id):
    """Look up documents.id by document_external_id. Returns None if not found."""
    if not document_external_id or not cur:
        return None
    cur.execute("SELECT id FROM documents WHERE document_external_id = %s", (document_external_id,))
    row = cur.fetchone()
    return row[0] if row else None


def prepare_row(cur, log_payload: dict) -> tuple[dict, int, int]:
    """
    Convert a prediction log payload into a parameterized INSERT row,
    and resolve source_id and document_id from the database.
    """
    from psycopg2.extras import Json

    # Get source_name from the nested input_payload
    source_name = (log_payload.get("input_payload") or {}).get("source_name")
    document_external_id = log_payload.get("document_external_id")

    # Resolve real IDs from DB
    resolved_source_id = resolve_source_id(cur, source_name)
    resolved_document_db_id = resolve_document_db_id(cur, document_external_id)

    row = {
        "source_id": resolved_source_id,
        "document_id": resolved_document_db_id,
        "document_external_id": document_external_id,
        "model_name": log_payload.get("model_name", "document_classifier"),
        "model_version": log_payload.get("model_version", "unknown"),
        "input_payload": Json(log_payload.get("input_payload", {})),
        "prediction_result": Json(log_payload.get("prediction_result", {})),
        "predicted_label": log_payload.get("predicted_label"),
        "confidence_score": log_payload.get("confidence_score", 0.0),
        "status": log_payload.get("status", "failed"),
        "review_reason": log_payload.get("review_reason"),
        "ingestion_run_id": log_payload.get("ingestion_run_id"),
        "created_at": log_payload.get("created_at", datetime.now(timezone.utc).isoformat()),
    }
    return row, resolved_source_id, resolved_document_db_id


# ---------------------------------------------------------------------------
# Insert logic
# ---------------------------------------------------------------------------

def insert_prediction_logs(
    conn,
    log_payloads: list[dict],
    *,
    batch_size: int = 50,
    dry_run: bool = False,
) -> list[int]:
    """
    Insert prediction log payloads into the prediction_logs table.

    Parameters
    ----------
    conn : psycopg2.connection
        Active PostgreSQL connection (ignored in dry_run mode).
    log_payloads : list[dict]
        Payloads from build_prediction_log_payload().
    batch_size : int
        Commit every N rows (default 50).
    dry_run : bool
        If True, print what would be inserted without DB access.

    Returns
    -------
    list[int]
        Inserted row IDs (empty list in dry_run mode).
    """
    inserted_ids = []

    # Dry run: no DB connection needed
    if dry_run:
        for i, payload in enumerate(log_payloads):
            print(f"  [DRY RUN] Row {i + 1}: {payload.get('document_external_id')}")
            print(f"    predicted_label = {payload.get('predicted_label')}")
            print(f"    confidence      = {payload.get('confidence_score')}")
            print(f"    status          = {payload.get('status')}")
        return inserted_ids

    cursor = conn.cursor()

    unresolved_source = 0
    unresolved_document = 0

    try:
        for i, payload in enumerate(log_payloads):
            row, src_id, doc_id = prepare_row(cursor, payload)
            if src_id is None:
                unresolved_source += 1
            if doc_id is None:
                unresolved_document += 1

            cursor.execute(INSERT_SQL, row)
            result = cursor.fetchone()
            row_id = result[0] if result else None
            inserted_ids.append(row_id)

            # Commit in batches
            if (i + 1) % batch_size == 0:
                conn.commit()
                print(f"  Committed batch: {i + 1}/{len(log_payloads)} rows")

        # Final commit for remaining rows
        conn.commit()
        print(f"  Committed all {len(log_payloads)} rows")
        if unresolved_source > 0:
            print(f"  ⚠️  {unresolved_source}/{len(log_payloads)} rows could not resolve source_id")
        if unresolved_document > 0:
            print(f"  ⚠️  {unresolved_document}/{len(log_payloads)} rows could not resolve document_db_id")

    except Exception as e:
        conn.rollback()
        print(f"  ERROR: {e}")
        raise
    finally:
        cursor.close()

    return inserted_ids


# ---------------------------------------------------------------------------
# Load payloads from JSON file
# ---------------------------------------------------------------------------

def load_payloads_from_file(file_path: str) -> list[dict]:
    """
    Load prediction log payloads from a JSON results file.

    Supports two formats:
    1. Direct list of log payloads: [{ ... }, { ... }]
    2. run_real_payloads.py output: { "prediction_log_payloads": [{ ... }] }
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "prediction_log_payloads" in data:
        return data["prediction_log_payloads"]
    else:
        raise ValueError(
            f"Unrecognized JSON format in {file_path}. "
            "Expected a list of payloads or a dict with 'prediction_log_payloads' key."
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Insert prediction log payloads into PostgreSQL prediction_logs table."
    )
    parser.add_argument(
        "--input", "-i",
        default=os.path.join(_PROJECT_ROOT, "outputs", "week6_duy_prediction_results.json"),
        help="Path to JSON file containing prediction log payloads (default: outputs/week6_duy_prediction_results.json)",
    )
    parser.add_argument("--host", default=os.environ.get("POSTGRES_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("POSTGRES_PORT", "5432")))
    parser.add_argument("--dbname", default=os.environ.get("POSTGRES_DB", "datavision_db"))
    parser.add_argument("--user", default=os.environ.get("POSTGRES_USER", "datavision"))
    parser.add_argument("--password", default=os.environ.get("DB_PASSWORD"))
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be inserted without actually connecting to the database.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.dry_run and not args.password:
        print("ERROR: DB_PASSWORD is not set. Refusing to connect with empty credential.")
        sys.exit(1)
    # 1. Load payloads
    print(f"Loading payloads from: {args.input}")
    log_payloads = load_payloads_from_file(args.input)
    print(f"Found {len(log_payloads)} prediction log payloads\n")

    if not log_payloads:
        print("No payloads to insert. Exiting.")
        return

    # 2. Print preview
    print("=== Preview (first 3 payloads) ===")
    for i, payload in enumerate(log_payloads[:3]):
        print(f"  [{i + 1}] {payload.get('document_external_id', 'N/A')}")
        print(f"      predicted_label  = {payload.get('predicted_label')}")
        print(f"      confidence_score = {payload.get('confidence_score')}")
        print(f"      status           = {payload.get('status')}")
    if len(log_payloads) > 3:
        print(f"  ... and {len(log_payloads) - 3} more")
    print()

    # 3. Dry run mode — no DB connection needed
    if args.dry_run:
        print("=== DRY RUN MODE (no database connection) ===\n")
        insert_prediction_logs(conn=None, log_payloads=log_payloads, dry_run=True)
        print(f"\nDry run complete. {len(log_payloads)} rows would be inserted.")
        return

    # 4. Connect and insert
    print(f"Connecting to PostgreSQL: {args.user}@{args.host}:{args.port}/{args.dbname}")
    conn = get_connection(
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        user=args.user,
        password=args.password,
    )

    try:
        print("Connection established.\n")
        print(f"=== Inserting {len(log_payloads)} rows into prediction_logs ===\n")

        inserted_ids = insert_prediction_logs(conn, log_payloads)

        print(f"\n=== Done ===")
        print(f"Successfully inserted {len(inserted_ids)} rows")
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM prediction_logs;")
        total_logs = cur.fetchone()[0]

        cur.execute("SELECT status, COUNT(*) FROM prediction_logs GROUP BY status;")
        status_counts = {row[0]: row[1] for row in cur.fetchall()}
   
        cur.execute("SELECT * FROM v_prediction_review_queue;")
        columns = [desc[0] for desc in cur.description]
        review_queue = []
        for row in cur.fetchall():
            record = {}
            for col_name, val in zip(columns, row):
                record[col_name] = str(val) if val is not None else None
            review_queue.append(record)

        cur.close()
        output_dir = os.path.join("week8", "database", "outputs", "db_validation")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "prediction_log_counts.json")
        output_data = {
            "inserted_in_this_run": len(inserted_ids),
            "total_prediction_logs": total_logs,
            "status_counts": status_counts,
            "v_prediction_review_queue_count": len(review_queue),
            "v_prediction_review_queue_data": review_queue
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4)
            
        print(f"Successfully saved count to: {output_file}")
    except Exception as e:
        print(f"Failed during execution: {e}")
    finally:
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()