"""Shared helpers for integration tests that create/drop disposable
databases. Centralizes the pg_terminate_backend step so a test that fails
mid-way (leaving its own connection open) doesn't block the next test's
DROP DATABASE with a psycopg2.errors.ObjectInUse error.
"""
import os
import psycopg2


def admin_conn():
    return psycopg2.connect(
        host=os.environ["DB_HOST"], user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"], dbname="postgres",
    )


def terminate_connections(conn, dbname):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid();",
            (dbname,),
        )


def drop_database(conn, dbname):
    terminate_connections(conn, dbname)
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {dbname};")


def connect(dbname):
    return psycopg2.connect(
        host=os.environ["DB_HOST"], user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"], dbname=dbname,
    )


def pg_bin(cmd_name):
    """Resolve a PostgreSQL client binary path the same way
    restore_database.py does. Tests that shell out to pg_dump/pg_restore
    directly (rather than through restore_database.py) MUST use this
    instead of the bare command name — otherwise pg_dump can silently
    come from a different, newer PostgreSQL install on PATH than the one
    PG_BIN_DIR points restore_database.py at, producing a dump file whose
    archive format the mismatched pg_restore can't read
    ("unsupported version (x.y) in file header").
    """
    pg_bin_dir = os.environ.get("PG_BIN_DIR", "")
    if pg_bin_dir:
        return os.path.join(pg_bin_dir, cmd_name)
    return cmd_name