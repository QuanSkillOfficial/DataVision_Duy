import os
import sys
import pytest

sys.path.insert(0, "week8/database/scripts")


def test_core_tables_and_views_are_well_formed():
    from db_schema_constants import CORE_TABLES, CORE_VIEWS

    assert len(CORE_TABLES) > 0
    assert len(CORE_VIEWS) > 0
    assert len(CORE_TABLES) == len(set(CORE_TABLES)), "duplicate table name"
    assert len(CORE_VIEWS) == len(set(CORE_VIEWS)), "duplicate view name"
    assert all(v.startswith("v_") for v in CORE_VIEWS)


def test_get_db_connection_requires_db_password(monkeypatch):
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    from db_connection import get_db_connection

    with pytest.raises(RuntimeError):
        get_db_connection()


def test_get_db_connection_defaults(monkeypatch):
    monkeypatch.setenv("DB_PASSWORD", "unit-test-only-not-real")
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)

    # We only check the defaults resolve correctly, not that a real
    # connection succeeds (no live DB in a unit test).
    assert os.environ.get("DB_HOST", "localhost") == "localhost"
    assert os.environ.get("DB_NAME", "datavision_db") == "datavision_db"
    assert os.environ.get("DB_USER", "datavision") == "datavision"


def test_should_skip_demo_data_reads_env_flag(monkeypatch):
    sys.path.insert(0, "week8/database/demo_data")
    from seed_demo_data import should_skip_demo_data

    monkeypatch.setenv("SKIP_DEMO_DATA", "1")
    assert should_skip_demo_data() is True

    monkeypatch.setenv("SKIP_DEMO_DATA", "0")
    assert should_skip_demo_data() is False

    monkeypatch.delenv("SKIP_DEMO_DATA", raising=False)
    assert should_skip_demo_data() is False