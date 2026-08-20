"""Reference data: fixed, small catalog rows that must exist in every
environment (fresh install, staging, production). Idempotent by design —
safe to run on every deploy. Never touches runtime/business data.
"""
import sys
sys.path.insert(0, "week8/database/scripts")
from db_connection import get_db_connection  # noqa: E402

REFERENCE_SOURCES = [
    {"name": "internal_csv_catalog", "source_type": "csv"},
    {"name": "internal_pdf_catalog", "source_type": "pdf"},
    {"name": "internal_manual_catalog", "source_type": "manual"},
]


def seed_reference_data(conn, sources=None):
    """Upsert reference sources. Returns number of rows affected.

    Uses ON CONFLICT (name) DO UPDATE so that:
    - re-running is a no-op when nothing changed (idempotent),
    - a genuine change to a reference row (e.g. source_type) is applied,
      not silently skipped.
    """
    sources = sources if sources is not None else REFERENCE_SOURCES
    with conn.cursor() as cur:
        for row in sources:
            cur.execute(
                """
                INSERT INTO sources (name, source_type)
                VALUES (%s, %s)
                ON CONFLICT (name) DO UPDATE
                    SET source_type = EXCLUDED.source_type;
                """,
                (row["name"], row["source_type"]),
            )
    conn.commit()
    return len(sources)


def main():
    conn = get_db_connection()
    try:
        count = seed_reference_data(conn)
        print(f"Reference data seeded/upserted: {count} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
