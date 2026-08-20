"""Demo data: optional, human-readable sample content used for local/demo
environments only. Never loaded automatically by migrations. Staging can
opt out entirely via SKIP_DEMO_DATA=1. Idempotent: re-running does not
create duplicate rows, and never touches runtime/business data.
"""
import os
import sys
sys.path.insert(0, "week8/database/scripts")
from db_connection import get_db_connection

DEMO_SOURCE = {"name": "demo_source", "source_type": "demo"}

DEMO_DOCUMENT = {
    "document_external_id": "demo_doc_sample_001",
    "file_name": "demo_sample_document.txt",
    "file_type": "txt",
    "processing_status": "uploaded",
}


def should_skip_demo_data():
    return os.environ.get("SKIP_DEMO_DATA", "").strip().lower() in ("1", "true", "yes")


def seed_demo_data(conn):
    if should_skip_demo_data():
        return "skipped"

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sources (name, source_type)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE
                SET source_type = EXCLUDED.source_type
            RETURNING id;
            """,
            (DEMO_SOURCE["name"], DEMO_SOURCE["source_type"]),
        )
        source_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO documents (
                source_id, file_name, file_type,
                document_external_id, processing_status, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (document_external_id) DO UPDATE
                SET file_name = EXCLUDED.file_name,
                    file_type = EXCLUDED.file_type,
                    processing_status = EXCLUDED.processing_status,
                    updated_at = CURRENT_TIMESTAMP;
            """,
            (
                source_id,
                DEMO_DOCUMENT["file_name"],
                DEMO_DOCUMENT["file_type"],
                DEMO_DOCUMENT["document_external_id"],
                DEMO_DOCUMENT["processing_status"],
            ),
        )
    conn.commit()
    return "seeded"


def main():
    conn = get_db_connection()
    try:
        result = seed_demo_data(conn)
        print(f"Demo data: {result}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
