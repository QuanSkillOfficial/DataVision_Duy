import json
import os
import subprocess
import sys
import pytest
import psycopg2

sys.path.insert(0, "week8/database/tests")
import db_test_utils  # noqa: E402

DISPOSABLE_DB = os.environ.get("TEST_DB_NAME", "datavision_test_backup_restore")


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


@pytest.mark.integration
def test_backup_is_non_empty_and_readable(disposable_db, monkeypatch, tmp_path):
    from week8.database.migrations.run_migrations import run_migrations

    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()

    env = os.environ.copy()
    env["DB_NAME"] = disposable_db
    env["PGPASSWORD"] = os.environ["DB_PASSWORD"]

    dump_file = tmp_path / "backup_test.dump"
    subprocess.run(
        [db_test_utils.pg_bin("pg_dump"), "-h", env["DB_HOST"], "-U", env["DB_USER"],
         "-d", disposable_db, "-F", "c", "-f", str(dump_file)],
        env=env, check=True,
    )

    assert dump_file.exists()
    assert dump_file.stat().st_size > 0

    result = subprocess.run(
        [db_test_utils.pg_bin("pg_restore"), "--list", str(dump_file)],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.integration
def test_restore_preserves_pgvector(disposable_db, monkeypatch, tmp_path):
    from week8.database.migrations.run_migrations import run_migrations
    from week8.database.scripts.restore_database import get_row_counts

    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()

    env = os.environ.copy()
    env["PGPASSWORD"] = os.environ["DB_PASSWORD"]
    dump_file = tmp_path / "pgvector_test.dump"
    subprocess.run(
        [db_test_utils.pg_bin("pg_dump"), "-h", os.environ["DB_HOST"], "-U", os.environ["DB_USER"],
         "-d", disposable_db, "-F", "c", "-f", str(dump_file)],
        env=env, check=True,
    )

    target_db = f"{disposable_db}_restore_pgvector"
    result = subprocess.run(
        ["python", "week8/database/scripts/restore_database.py",
         "--dump-file", str(dump_file), "--dbname", target_db, "--verify",
         "--output", str(tmp_path / "restore_result.json")],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    counts = get_row_counts(
        {"host": os.environ["DB_HOST"], "port": os.environ.get("DB_PORT", "5432"),
         "user": os.environ["DB_USER"], "dbname": target_db},
        env,
    )
    assert counts["pgvector_extension_present"] is True

    admin = db_test_utils.admin_conn()
    admin.autocommit = True
    db_test_utils.drop_database(admin, target_db)
    admin.close()


@pytest.mark.integration
def test_restore_counts_match(disposable_db, monkeypatch, tmp_path):
    from week8.database.migrations.run_migrations import run_migrations
    from week8.database.scripts.backup_database import get_row_counts as backup_counts

    monkeypatch.setenv("DB_NAME", disposable_db)
    run_migrations()

    conn = db_test_utils.connect(disposable_db)
    try:
        conn.cursor().execute(
            "INSERT INTO sources (name, source_type) VALUES ('counts_match_src', 'csv');"
        )
        conn.commit()

        reference = backup_counts(
            os.environ["DB_HOST"], os.environ.get("DB_PORT", "5432"),
            os.environ["DB_USER"], disposable_db, os.environ["DB_PASSWORD"],
        )
        ref_file = tmp_path / "reference.json"
        ref_file.write_text(json.dumps({"counts": reference}))

        env = os.environ.copy()
        env["PGPASSWORD"] = os.environ["DB_PASSWORD"]
        dump_file = tmp_path / "counts_match.dump"
        subprocess.run(
            [db_test_utils.pg_bin("pg_dump"), "-h", os.environ["DB_HOST"], "-U", os.environ["DB_USER"],
             "-d", disposable_db, "-F", "c", "-f", str(dump_file)],
            env=env, check=True,
        )

        target_db = f"{disposable_db}_restore_counts"
        result = subprocess.run(
            ["python", "week8/database/scripts/restore_database.py",
             "--dump-file", str(dump_file), "--dbname", target_db, "--verify",
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
        db_test_utils.drop_database(admin, target_db)
        admin.close()
    finally:
        conn.close()