import importlib
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))


def test_vector_store_import_does_not_require_torch(monkeypatch):
    """The vector store should not hard-import torch when running in a lean CI environment."""
    sys.modules.pop("ai.rag.vector_store", None)
    monkeypatch.setitem(sys.modules, "torch", None)

    module = importlib.import_module("ai.rag.vector_store")

    assert hasattr(module, "VectorStore")
    assert hasattr(module, "resolve_document_db_id")


def test_repeated_add_chunks_is_idempotent_for_same_chunk_id():
    """Repeated indexing with the same chunk_id should upsert without duplicating stored rows."""
    from ai.rag.vector_store import VectorStore

    vector_store = VectorStore(use_pgvector=False)
    embedding = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    chunks = [
        {
            "chunk_id": "reindex_chunk_1",
            "document_id": "doc_001",
            "chunk_text": "alpha",
            "metadata": {"page_number": 1},
        },
        {
            "chunk_id": "reindex_chunk_1",
            "document_id": "doc_001",
            "chunk_text": "alpha updated",
            "metadata": {"page_number": 1},
        },
    ]

    vector_store.add_chunks(chunks[:1], embedding[:1])
    vector_store.add_chunks(chunks[1:], embedding[1:])

    assert len(vector_store.in_memory_store) == 1
    assert vector_store.in_memory_store["reindex_chunk_1"]["chunk_text"] == "alpha updated"
