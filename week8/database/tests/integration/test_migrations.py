import os
import json
import sys
from pathlib import Path
import pytest
import psycopg2

sys.path.insert(0, "week8/database/tests")
import db_test_utils  # noqa: E402

from week8.database.migrations.run_migrations import run_migrations
from week8.database.scripts.backup_database import get_row_counts as backup_get_row_counts
from week8.database.scripts.restore_database import main as restore_main
from week8.database.scripts.db_schema_constants import CORE_TABLES, CORE_VIEWS

DISPOSABLE_DB = os.environ.get("TEST_DB_NAME", "datavision_test_migrations")


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
    return db_test_utils.connect(dbname)


@pytest.mark.integration
def test_migration_fresh_install(disposable_db, monkeypatch):
    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()

    conn = _connect(disposable_db)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = {r[0] for r in cur.fetchall()}
    assert set(CORE_TABLES).issubset(tables)

    cur.execute("SELECT table_name FROM information_schema.views WHERE table_schema='public';")
    views = {r[0] for r in cur.fetchall()}
    assert set(CORE_VIEWS).issubset(views)

    cur.execute("SELECT extname FROM pg_extension WHERE extname='vector';")
    assert cur.fetchone() is not None
    conn.close()


@pytest.mark.integration
def test_migration_upgrade_from_week7(disposable_db, monkeypatch):
    conn = _connect(disposable_db)
    cur = conn.cursor()

    baseline_path = Path("week8/database/tests/fixtures/week7_baseline_schema.sql")
    cur.execute(baseline_path.read_text(encoding="utf-8"))
    cur.execute("""
        INSERT INTO sources (name, source_type) VALUES ('week7_baseline_source', 'csv');
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM sources;")
    baseline_count = cur.fetchone()[0]
    assert baseline_count > 0

    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()

    cur.execute("SELECT COUNT(*) FROM sources;")
    assert cur.fetchone()[0] == baseline_count

    cur.execute("""
        SELECT conname FROM pg_constraint WHERE conname = 'uq_document_pages_doc_page';
    """)
    assert cur.fetchone() is not None
    conn.close()


@pytest.mark.integration
def test_migration_second_run_is_noop(disposable_db, monkeypatch):
    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()

    conn = _connect(disposable_db)
    cur = conn.cursor()
    cur.execute("SELECT version, applied_at FROM schema_migrations ORDER BY version;")
    before = cur.fetchall()

    run_migrations()

    cur.execute("SELECT version, applied_at FROM schema_migrations ORDER BY version;")
    after = cur.fetchall()

    assert before == after
    conn.close()


@pytest.mark.integration
def test_destructive_migration_is_blocked(tmp_path):
    bad_dir = tmp_path / "migrations"
    bad_dir.mkdir()
    # IF NOT EXISTS matters here: run_migrations() always calls
    # ensure_migration_table_exists() first, which already creates
    # schema_migrations. A bare CREATE TABLE (no IF NOT EXISTS) collides
    # with that and raises DuplicateTable before we ever reach the
    # destructive-statement check this test is meant to exercise.
    (bad_dir / "0001_bad.sql").write_text(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version TEXT PRIMARY KEY, applied_at TIMESTAMP);"
    )
    (bad_dir / "0002_drop.sql").write_text("DROP TABLE sources;")

    with pytest.raises(RuntimeError, match="Destructive migration blocked"):
        run_migrations(allow_destructive=False, migration_dir=str(bad_dir))


@pytest.mark.integration
def test_backup_failure_blocks_setup(monkeypatch):
    import subprocess
    monkeypatch.setenv("DB_HOST", "nonexistent-host-for-test")
    result = subprocess.run(
        ["python", "week8/database/scripts/backup_database.py"],
        capture_output=True,
    )
    assert result.returncode != 0


@pytest.mark.integration
def test_backup_manifest_contains_row_counts(disposable_db, monkeypatch, tmp_path):
    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()
    counts = backup_get_row_counts(
        os.environ["DB_HOST"], os.environ["DB_PORT"],
        os.environ["DB_USER"], disposable_db, os.environ["DB_PASSWORD"],
    )
    assert "sources" in counts
    assert "pgvector_extension_present" in counts


@pytest.mark.integration
def test_restore_into_disposable_database(disposable_db, monkeypatch, tmp_path):
    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()

    conn = _connect(disposable_db)
    cur = conn.cursor()
    cur.execute("INSERT INTO sources (name, source_type) VALUES ('restore_test_src', 'csv');")
    conn.commit()

    reference_counts = backup_get_row_counts(
        os.environ["DB_HOST"], os.environ["DB_PORT"],
        os.environ["DB_USER"], disposable_db, os.environ["DB_PASSWORD"],
    )
    ref_file = tmp_path / "reference.json"
    ref_file.write_text(json.dumps({"counts": reference_counts}))

    dump_file = tmp_path / "test_backup.dump"
    import subprocess
    env = os.environ.copy()
    env["PGPASSWORD"] = os.environ["DB_PASSWORD"]
    subprocess.run(
        [db_test_utils.pg_bin("pg_dump"), "-h", os.environ["DB_HOST"], "-U", os.environ["DB_USER"],
         "-d", disposable_db, "-F", "c", "-f", str(dump_file)],
        env=env, check=True,
    )

    result = subprocess.run(
        ["python", "week8/database/scripts/restore_database.py",
         "--dump-file", str(dump_file),
         "--dbname", f"{disposable_db}_restore_test",
         "--verify",
         "--reference-counts", str(ref_file),
         "--output", str(tmp_path / "restore_result.json")],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    report = json.loads((tmp_path / "restore_result.json").read_text())
    assert report["overall_result"] == "PASS"
    assert report["mismatches"] == []

    admin = db_test_utils.admin_conn()
    admin.autocommit = True
    db_test_utils.drop_database(admin, f"{disposable_db}_restore_test")
    admin.close()
    conn.close()
