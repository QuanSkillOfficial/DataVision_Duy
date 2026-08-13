import os
import glob
import sys
import psycopg2
from dotenv import load_dotenv
load_dotenv()
def get_db_connection():
    password = os.environ.get("DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "DB_PASSWORD environment variable is required. "
            "Set it before running migrations, e.g.:\n"
            "  export DB_PASSWORD='your-password'"
        )
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "datavision_db"),
        user=os.environ.get("DB_USER", "datavision"),
        password=password,
    )

def ensure_migration_table_exists(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """)
    conn.commit()

def run_migrations(allow_destructive=False):
    migration_dir = os.path.join(os.path.dirname(__file__))
    migration_files = sorted(glob.glob(os.path.join(migration_dir, "*.sql")))

    if not migration_files:
        print("No migration files found.")
        return

    conn = get_db_connection()
    ensure_migration_table_exists(conn)

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version FROM schema_migrations;")
            applied_versions = set(row[0] for row in cur.fetchall())

            for file_path in migration_files:
                filename = os.path.basename(file_path)

                if filename in applied_versions:
                    print(f"Skipping already applied migration: {filename}")
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    sql_content = f.read()

                if not allow_destructive and (
                    "DROP TABLE" in sql_content.upper()
                    or "DROP DATABASE" in sql_content.upper()
                ):
                    print(
                        f"BLOCKED: {filename} contains destructive statements "
                        f"(DROP TABLE/DATABASE). Re-run with --allow-destructive "
                        f"if this is intentional (e.g. local reset)."
                    )
                    raise RuntimeError(f"Destructive migration blocked: {filename}")

                print(f"Applying migration: {filename}...")
                try:
                    cur.execute(sql_content)
                    cur.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s);",
                        (filename,),
                    )
                    conn.commit()
                    print(f"Success: {filename}")
                except Exception as e:
                    conn.rollback()
                    print(f"Error applying {filename}: {e}")
                    raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("--- Starting Database Migrations ---")
    allow_destructive = "--allow-destructive" in sys.argv
    run_migrations(allow_destructive=allow_destructive)
    print("--- Migrations Completed ---")