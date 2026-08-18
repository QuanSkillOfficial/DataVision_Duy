"""
Tests for Retriever - Week 5

Tests retrieval functionality including chunk_id and page_number handling.
"""

import sys
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai.ai_tests.fakes import FakeEmbedder, FakeVectorStore
from ai.rag.vector_store import VectorStore
from ai.rag.retriever import Retriever


def test_retriever_returns_chunk_id():
    """Test that retriever returns chunk_id in results."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    # Add sample chunks
    chunks = [
        {
            "chunk_id": "doc_001_page_1_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "Machine learning is a subset of AI.",
            "metadata": {"source": "test.pdf", "page_number": 1}
        }
    ]
    embeddings = np.random.rand(1, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    # Retrieve
    results = retriever.retrieve("What is machine learning?")
    
    assert len(results) > 0, "Should return results"
    assert "chunk_id" in results[0], "Result should have chunk_id"
    assert results[0]["chunk_id"] == "doc_001_page_1_chunk_000"
    
    print("✓ test_retriever_returns_chunk_id passed")


def test_retriever_returns_page_number():
    """Test that retriever returns page_number in results."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    chunks = [
        {
            "chunk_id": "doc_001_page_5_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "This content is on page 5.",
            "metadata": {"source": "test.pdf", "page_number": 5}
        }
    ]
    embeddings = np.random.rand(1, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    results = retriever.retrieve("Page 5 content")
    
    assert len(results) > 0
    assert "page_number" in results[0], "Result should have page_number"
    assert results[0]["page_number"] == 5
    
    print("✓ test_retriever_returns_page_number passed")


def test_retriever_with_document_filter():
    """Test retrieval with document_id filter."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    chunks = [
        {
            "chunk_id": "doc_001_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "Content from document 1",
            "metadata": {"source": "doc1.pdf"}
        },
        {
            "chunk_id": "doc_002_chunk_000",
            "document_id": "doc_002",
            "chunk_text": "Content from document 2",
            "metadata": {"source": "doc2.pdf"}
        }
    ]
    embeddings = np.random.rand(2, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    # Filter by document_id
    results = retriever.retrieve("content", document_id="doc_001")
    
    assert len(results) == 1
    assert results[0]["document_id"] == "doc_001"
    
    print("✓ test_retriever_with_document_filter passed")


def test_retriever_with_min_score():
    """Test retrieval with minimum score threshold."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    chunks = [
        {
            "chunk_id": "doc_001_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "Test content",
            "metadata": {"source": "test.pdf"}
        }
    ]
    embeddings = np.random.rand(1, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    # With high min_score, should return no results
    results = retriever.retrieve("unrelated query", min_score=0.99)
    assert len(results) == 0
    
    # With low min_score, should return results
    results = retriever.retrieve("test", min_score=0.0)
    assert len(results) > 0
    
    print("✓ test_retriever_with_min_score passed")


def test_retriever_score_field():
    """Test that retriever returns score field."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    chunks = [
        {
            "chunk_id": "doc_001_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "Test content",
            "metadata": {"source": "test.pdf"}
        }
    ]
    embeddings = np.random.rand(1, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    results = retriever.retrieve("test")
    
    assert "score" in results[0]
    assert isinstance(results[0]["score"], float)
    assert 0.0 <= results[0]["score"] <= 1.0
    
    print("✓ test_retriever_score_field passed")


def test_retriever_top_k_limit():
    """Test that retriever respects top_k parameter."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=3)
    
    # Add 10 chunks
    chunks = [
        {
            "chunk_id": f"doc_001_chunk_{i:03d}",
            "document_id": "doc_001",
            "chunk_text": f"Content {i}",
            "metadata": {"source": "test.pdf"}
        }
        for i in range(10)
    ]
    embeddings = embedder.embed([c["chunk_text"] for c in chunks])
    vector_store.add_chunks(chunks, embeddings)
    
    results = retriever.retrieve("content")
    
    assert len(results) <= 3, f"Should return at most 3 results, got {len(results)}"
    
    print("✓ test_retriever_top_k_limit passed")


def test_retriever_similarity_score_range():
    """Test that similarity scores are in valid range [0, 1]."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    chunks = [
        {
            "chunk_id": "doc_001_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "Test content",
            "metadata": {"source": "test.pdf"}
        }
    ]
    embeddings = embedder.embed([c["chunk_text"] for c in chunks])
    vector_store.add_chunks(chunks, embeddings)
    
    results = retriever.retrieve("test")
    
    for result in results:
        assert 0.0 <= result["similarity_score"] <= 1.0, f"Score {result['similarity_score']} out of range"
    
    print("✓ test_retriever_similarity_score_range passed")


def test_retriever_empty_store():
    """Test retriever behavior with empty vector store."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    results = retriever.retrieve("test query")
    
    assert len(results) == 0, "Should return empty results for empty store"
    
    print("✓ test_retriever_empty_store passed")


def test_retriever_chunk_text_preserved():
    """Test that chunk_text is preserved in results."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    original_text = "This is the original chunk text that should be preserved."
    chunks = [
        {
            "chunk_id": "doc_001_chunk_000",
            "document_id": "doc_001",
            "chunk_text": original_text,
            "metadata": {"source": "test.pdf"}
        }
    ]
    embeddings = embedder.embed([c["chunk_text"] for c in chunks])
    vector_store.add_chunks(chunks, embeddings)
    
    results = retriever.retrieve("original")
    
    assert len(results) > 0
    assert results[0]["chunk_text"] == original_text, "Chunk text should be preserved"
    
    print("✓ test_retriever_chunk_text_preserved passed")


if __name__ == "__main__":
    test_retriever_returns_chunk_id()
    test_retriever_returns_page_number()
    test_retriever_with_document_filter()
    test_retriever_with_min_score()
    test_retriever_score_field()
    test_retriever_top_k_limit()
    test_retriever_similarity_score_range()
    test_retriever_empty_store()
    test_retriever_chunk_text_preserved()
    print("\n✓ All retriever tests passed!")
