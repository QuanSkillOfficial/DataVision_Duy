"""
Tests for Fake implementations - Week 7

Tests that fake implementations work correctly for CI-safe testing.
"""

import sys
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai.ai_tests.fakes import FakeEmbedder, FakeVectorStore, FakeDatabaseConnection, FakeCursor, create_sample_chunks, create_sample_pages


def test_fake_embedder_dimension():
    """Test that FakeEmbedder returns correct dimension."""
    embedder = FakeEmbedder(embedding_dimension=384)
    
    assert embedder.get_embedding_dimension() == 384
    
    print("✓ test_fake_embedder_dimension passed")


def test_fake_embedder_single_text():
    """Test that FakeEmbedder handles single text input."""
    embedder = FakeEmbedder()
    
    embedding = embedder.embed("test text")
    
    assert embedding.shape == (1, 384)
    
    print("✓ test_fake_embedder_single_text passed")


def test_fake_embedder_multiple_texts():
    """Test that FakeEmbedder handles multiple text input."""
    embedder = FakeEmbedder()
    
    texts = ["text 1", "text 2", "text 3"]
    embeddings = embedder.embed(texts)
    
    assert embeddings.shape == (3, 384)
    
    print("✓ test_fake_embedder_multiple_texts passed")


def test_fake_embedder_query():
    """Test that FakeEmbedder handles query embedding."""
    embedder = FakeEmbedder()
    
    query_embedding = embedder.embed_query("test query")
    
    assert query_embedding.shape == (384,)
    
    print("✓ test_fake_embedder_query passed")


def test_fake_embedder_deterministic():
    """Test that FakeEmbedder returns deterministic embeddings."""
    embedder = FakeEmbedder()
    
    text = "same text"
    embedding1 = embedder.embed(text)
    embedding2 = embedder.embed(text)
    
    np.testing.assert_array_equal(embedding1, embedding2)
    
    print("✓ test_fake_embedder_deterministic passed")


def test_fake_vector_store_add_chunks():
    """Test that FakeVectorStore can add chunks."""
    vector_store = FakeVectorStore()
    
    chunks = create_sample_chunks(3)
    embeddings = np.random.rand(3, 384)
    
    vector_store.add_chunks(chunks, embeddings)
    
    assert len(vector_store.chunks) == 3
    
    print("✓ test_fake_vector_store_add_chunks passed")


def test_fake_vector_store_search():
    """Test that FakeVectorStore can search."""
    vector_store = FakeVectorStore()
    
    chunks = create_sample_chunks(3)
    embeddings = np.random.rand(3, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    query_embedding = np.random.rand(384)
    results = vector_store.search(query_embedding, top_k=2)
    
    assert len(results) <= 2
    
    print("✓ test_fake_vector_store_search passed")


def test_fake_vector_store_document_filter():
    """Test that FakeVectorStore can filter by document_id."""
    vector_store = FakeVectorStore()
    
    chunks = [
        {"chunk_id": "doc1_chunk_0", "document_id": "doc1", "chunk_text": "text", "metadata": {}},
        {"chunk_id": "doc2_chunk_0", "document_id": "doc2", "chunk_text": "text", "metadata": {}}
    ]
    embeddings = np.random.rand(2, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    query_embedding = np.random.rand(384)
    results = vector_store.search(query_embedding, filter_metadata={"document_id": "doc1"})
    
    assert len(results) == 1
    assert results[0]["document_id"] == "doc1"
    
    print("✓ test_fake_vector_store_document_filter passed")


def test_fake_vector_store_page_filter():
    """Test that FakeVectorStore can filter by page_number."""
    vector_store = FakeVectorStore()
    
    chunks = [
        {"chunk_id": "doc1_chunk_0", "document_id": "doc1", "chunk_text": "text", "metadata": {"page_number": 1}},
        {"chunk_id": "doc1_chunk_1", "document_id": "doc1", "chunk_text": "text", "metadata": {"page_number": 2}}
    ]
    embeddings = np.random.rand(2, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    query_embedding = np.random.rand(384)
    results = vector_store.search(query_embedding, filter_metadata={"page_number": 1})
    
    assert len(results) == 1
    assert results[0]["metadata"]["page_number"] == 1
    
    print("✓ test_fake_vector_store_page_filter passed")


def test_fake_database_connection():
    """Test that FakeDatabaseConnection can be created."""
    conn = FakeDatabaseConnection()
    
    assert conn.closed == False
    
    print("✓ test_fake_database_connection passed")


def test_fake_database_cursor():
    """Test that FakeDatabaseConnection returns cursor."""
    conn = FakeDatabaseConnection()
    cursor = conn.cursor()
    
    assert isinstance(cursor, FakeCursor)
    
    print("✓ test_fake_database_cursor passed")


def test_fake_cursor_execute():
    """Test that FakeCursor can execute queries."""
    conn = FakeDatabaseConnection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM documents")
    
    assert cursor.rowcount >= 0
    
    print("✓ test_fake_cursor_execute passed")


def test_fake_cursor_fetchone():
    """Test that FakeCursor can fetch one row."""
    conn = FakeDatabaseConnection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM documents WHERE document_external_id = %s", ("doc_001",))
    result = cursor.fetchone()
    
    assert result is not None
    
    print("✓ test_fake_cursor_fetchone passed")


def test_create_sample_chunks():
    """Test that create_sample_chunks returns correct structure."""
    chunks = create_sample_chunks(5)
    
    assert len(chunks) == 5
    assert all("chunk_id" in c for c in chunks)
    assert all("document_id" in c for c in chunks)
    assert all("chunk_text" in c for c in chunks)
    
    print("✓ test_create_sample_chunks passed")


def test_create_sample_pages():
    """Test that create_sample_pages returns correct structure."""
    pages = create_sample_pages(3)
    
    assert len(pages) == 3
    assert all("document_external_id" in p for p in pages)
    assert all("page_number" in p for p in pages)
    assert all("text" in p for p in pages)
    
    print("✓ test_create_sample_pages passed")


if __name__ == "__main__":
    test_fake_embedder_dimension()
    test_fake_embedder_single_text()
    test_fake_embedder_multiple_texts()
    test_fake_embedder_query()
    test_fake_embedder_deterministic()
    test_fake_vector_store_add_chunks()
    test_fake_vector_store_search()
    test_fake_vector_store_document_filter()
    test_fake_vector_store_page_filter()
    test_fake_database_connection()
    test_fake_database_cursor()
    test_fake_cursor_execute()
    test_fake_cursor_fetchone()
    test_create_sample_chunks()
    test_create_sample_pages()
    print("\n✓ All fakes tests passed!")
