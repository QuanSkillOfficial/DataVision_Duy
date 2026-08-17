import os
import sys
import pytest
import psycopg2

sys.path.insert(0, "week8/database/scripts")
sys.path.insert(0, "week8/database/migrations")
sys.path.insert(0, "week8/database/tests")
import db_test_utils  

from run_migrations import run_migrations  
from reference_data.seed_reference_data import ( 
    seed_reference_data,
    REFERENCE_SOURCES,
)
from demo_data.seed_demo_data import ( 
    seed_demo_data,
    DEMO_SOURCE,
    DEMO_DOCUMENT,
)

DISPOSABLE_DB = os.environ.get("TEST_DB_NAME", "datavision_test_lifecycle")


@pytest.fixture
def disposable_db():
    conn = db_test_utils.admin_conn()
    conn.autocommit = True
    db_test_utils.drop_database(conn, DISPOSABLE_DB)
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE {DISPOSABLE_DB};")
    yield DISPOSABLE_DB
    db_test_utils.drop_database(conn, DISPOSABLE_DB)
    conn.close()



def _connect(dbname):
    return psycopg2.connect(
        host=os.environ["DB_HOST"], user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"], dbname=dbname,
    )


@pytest.mark.integration
def test_migration_does_not_load_demo_data(disposable_db, monkeypatch):
    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()

    conn = _connect(disposable_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sources WHERE name = %s;", (DEMO_SOURCE["name"],))
    assert cur.fetchone()[0] == 0
    conn.close()


@pytest.mark.integration
def test_reference_data_seed_is_idempotent(disposable_db, monkeypatch):
    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()
    conn = _connect(disposable_db)

    seed_reference_data(conn)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sources WHERE source_type != 'demo';")
    after_run1 = cur.fetchone()[0]

    seed_reference_data(conn)
    cur.execute("SELECT COUNT(*) FROM sources WHERE source_type != 'demo';")
    after_run2 = cur.fetchone()[0]

    assert after_run1 == len(REFERENCE_SOURCES)
    assert after_run2 == after_run1
    conn.close()


@pytest.mark.integration
def test_reference_data_change_is_applied_not_skipped(disposable_db, monkeypatch):
    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()
    conn = _connect(disposable_db)

    seed_reference_data(conn)
    changed = [{"name": REFERENCE_SOURCES[0]["name"], "source_type": "changed_type"}]
    seed_reference_data(conn, sources=changed)

    cur = conn.cursor()
    cur.execute(
        "SELECT source_type FROM sources WHERE name = %s;",
        (REFERENCE_SOURCES[0]["name"],),
    )
    assert cur.fetchone()[0] == "changed_type"
    conn.close()


@pytest.mark.integration
def test_staging_can_skip_demo_data(disposable_db, monkeypatch):
    monkeypatch.setenv("DB_NAME", disposable_db)
    monkeypatch.setenv("SKIP_DEMO_DATA", "1")
    run_migrations()
    conn = _connect(disposable_db)

    result = seed_demo_data(conn)
    assert result == "skipped"

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sources WHERE name = %s;", (DEMO_SOURCE["name"],))
    assert cur.fetchone()[0] == 0
    conn.close()


@pytest.mark.integration
def test_seed_second_run_has_no_duplicates(disposable_db, monkeypatch):
    monkeypatch.delenv("SKIP_DEMO_DATA", raising=False)
    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()
    conn = _connect(disposable_db)

    seed_reference_data(conn)
    seed_demo_data(conn)
    seed_reference_data(conn)
    seed_demo_data(conn)

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sources WHERE name = %s;", (DEMO_SOURCE["name"],))
    assert cur.fetchone()[0] == 1

    cur.execute(
        "SELECT COUNT(*) FROM documents WHERE document_external_id = %s;",
        (DEMO_DOCUMENT["document_external_id"],),
    )
    assert cur.fetchone()[0] == 1
    conn.close()


@pytest.mark.integration
def test_runtime_data_not_overwritten_by_reseed(disposable_db, monkeypatch):
    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()
    conn = _connect(disposable_db)
    cur = conn.cursor()

    # Simulate runtime/business data produced by the application.
    cur.execute(
        "INSERT INTO prediction_logs (model_name, input_payload, prediction_result) "
        "VALUES ('demo_model', '{}', '{}');"
    )
    cur.execute(
        "INSERT INTO rag_query_logs (user_query, generated_response) "
        "VALUES ('q1', 'r1');"
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM prediction_logs;")
    predictions_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM rag_query_logs;")
    queries_before = cur.fetchone()[0]

    seed_reference_data(conn)
    seed_demo_data(conn)
    seed_reference_data(conn)
    seed_demo_data(conn)

    cur.execute("SELECT COUNT(*) FROM prediction_logs;")
    predictions_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM rag_query_logs;")
    queries_after = cur.fetchone()[0]

    assert predictions_after == predictions_before
    assert queries_after == queries_before
    conn.close()