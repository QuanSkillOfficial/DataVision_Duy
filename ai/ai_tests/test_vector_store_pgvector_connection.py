import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).parent.parent.parent))

from ai.rag.vector_store import VectorStore, resolve_document_db_id


def test_vector_store_uses_database_url_from_environment(monkeypatch):
    captured = {}

    class DummyConnection:
        def cursor(self):
            raise RuntimeError("cursor should not be used in this test")

        def commit(self):
            pass

        def rollback(self):
            pass

    def fake_connect(connection_string):
        captured["connection_string"] = connection_string
        return DummyConnection()

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/rag_db")
    monkeypatch.setattr(VectorStore, "_validate_existing_schema", lambda self: None)
    monkeypatch.setitem(sys.modules, "psycopg2", types.SimpleNamespace(connect=fake_connect))

    vector_store = VectorStore(use_pgvector=True)

    assert captured["connection_string"] == "postgresql://user:pass@localhost:5432/rag_db"
    assert vector_store.connection is not None


def test_resolve_document_db_id_uses_document_external_id(monkeypatch):
    executed = {}

    class DummyCursor:
        def execute(self, query, params):
            executed["query"] = query
            executed["params"] = params
        def fetchone(self):
            return (123,)
        def close(self):
            pass

    class DummyConnection:
        def cursor(self):
            return DummyCursor()

    monkeypatch.setitem(sys.modules, "psycopg2", types.SimpleNamespace())

    document_id = resolve_document_db_id(DummyConnection(), "doc_dataflow_technical_report")

    assert document_id == 123
    assert executed["query"] == "SELECT id FROM documents WHERE document_external_id = %s OR id::text = %s LIMIT 1"
    assert executed["params"] == ("doc_dataflow_technical_report", "doc_dataflow_technical_report")
