import os
import pytest
import psycopg2

pytestmark = pytest.mark.live_db


def _live_db_target():
    """The dbname a live test is allowed to touch.

    Deliberately does NOT fall back to DEFAULT DB_NAME — a live test must
    say explicitly which database it means to run against.
    """
    return os.environ.get("LIVE_DB_NAME")


def test_live_database_requires_explicit_flag():
    """This test only *collects and runs* when RUN_LIVE_DB_TESTS=1 (enforced
    by tests/conftest.py). It further requires LIVE_DB_NAME to be set
    explicitly, so a live run can never accidentally target the default
    DB_NAME (which may be a disposable/local db) or be left unset.
    """
    target = _live_db_target()
    assert target, (
        "LIVE_DB_NAME must be set explicitly to run live_db tests "
        "(no implicit fallback to DB_NAME)."
    )
    assert target != "postgres", "Refusing to target the postgres maintenance db."


@pytest.mark.skipif(not _live_db_target(), reason="LIVE_DB_NAME not set")
def test_live_database_is_reachable_and_has_core_tables():
    import sys
    sys.path.insert(0, "week8/database/scripts")
    from db_schema_constants import CORE_TABLES

    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dbname=_live_db_target(),
    )
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public';"
        )
        tables = {r[0] for r in cur.fetchall()}
        assert set(CORE_TABLES).issubset(tables)
    finally:
        conn.close()