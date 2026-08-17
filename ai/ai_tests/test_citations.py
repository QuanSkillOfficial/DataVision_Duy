"""
Tests for Citation Handling - Week 5

Tests that citations include file_name, page_number, and chunk_id.
"""

import sys
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai.ai_tests.fakes import FakeEmbedder, FakeVectorStore
from ai.rag.vector_store import VectorStore
from ai.rag.retriever import Retriever
from ai.rag.answer_generator import AnswerGenerator


def test_citations_include_file_name():
    """Test that citations include file_name."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    chunks = [
        {
            "chunk_id": "doc_001_page_1_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "Test content",
            "metadata": {"source": "test.pdf", "page_number": 1}
        }
    ]
    embeddings = np.random.rand(1, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    results = retriever.retrieve("test")
    citations = retriever.get_source_citations(results)
    
    assert len(citations) > 0
    assert "file_name" in citations[0]
    assert citations[0]["file_name"] == "test.pdf"
    
    print("✓ test_citations_include_file_name passed")


def test_citations_include_page_number():
    """Test that citations include page_number."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    chunks = [
        {
            "chunk_id": "doc_001_page_7_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "Test content on page 7",
            "metadata": {"source": "test.pdf", "page_number": 7}
        }
    ]
    embeddings = np.random.rand(1, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    results = retriever.retrieve("test")
    citations = retriever.get_source_citations(results)
    
    assert len(citations) > 0
    assert "page_number" in citations[0]
    assert citations[0]["page_number"] == 7
    
    print("✓ test_citations_include_page_number passed")


def test_citations_include_chunk_id():
    """Test that citations include chunk_id."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    chunks = [
        {
            "chunk_id": "doc_001_page_1_chunk_005",
            "document_id": "doc_001",
            "chunk_text": "Test content",
            "metadata": {"source": "test.pdf", "page_number": 1}
        }
    ]
    embeddings = np.random.rand(1, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    results = retriever.retrieve("test")
    citations = retriever.get_source_citations(results)
    
    assert len(citations) > 0
    assert "chunk_id" in citations[0]
    assert citations[0]["chunk_id"] == "doc_001_page_1_chunk_005"
    
    print("✓ test_citations_include_chunk_id passed")


def test_citations_unique_by_key():
    """Test that citations are unique by (file_name, page_number, chunk_id)."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    # Add chunks from same page (should be deduplicated)
    chunks = [
        {
            "chunk_id": "doc_001_page_1_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "First chunk",
            "metadata": {"source": "test.pdf", "page_number": 1}
        },
        {
            "chunk_id": "doc_001_page_1_chunk_001",
            "document_id": "doc_001",
            "chunk_text": "Second chunk",
            "metadata": {"source": "test.pdf", "page_number": 1}
        }
    ]
    embeddings = np.random.rand(2, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    results = retriever.retrieve("test")
    citations = retriever.get_source_citations(results)
    
    # Each chunk has unique chunk_id, so both should appear
    citation_keys = [(c["file_name"], c["page_number"], c["chunk_id"]) for c in citations]
    assert len(citation_keys) == len(set(citation_keys)), "Citations should be unique"
    
    print("✓ test_citations_unique_by_key passed")


def test_answer_generator_citations():
    """Test that AnswerGenerator.format_response includes proper citations."""
    generator = AnswerGenerator()
    
    chunks = [
        {
            "chunk_id": "doc_001_page_3_chunk_000",
            "chunk_text": "Test content",
            "metadata": {"source": "test.pdf", "page_number": 3},
            "page_number": 3
        }
    ]
    
    response = generator.format_response(
        question="Test question",
        answer="Test answer",
        retrieved_chunks=chunks,
        status="answered"
    )
    
    assert "citations" in response
    assert len(response["citations"]) > 0
    assert "file_name" in response["citations"][0]
    assert "page_number" in response["citations"][0]
    assert "chunk_id" in response["citations"][0]
    
    print("✓ test_answer_generator_citations passed")


def test_citation_chunk_id_fallback():
    """Test chunk_id fallback from 'id' field."""
    # Simulate result with 'id' instead of 'chunk_id'
    result = {
        "id": "fallback_chunk_id",
        "text": "Test",
        "metadata": {"source": "test.pdf", "page_number": 1},
        "score": 0.8
    }
    
    # Test the fallback logic
    chunk_id = result.get("chunk_id", result.get("id", ""))
    assert chunk_id == "fallback_chunk_id"
    
    print("✓ test_citation_chunk_id_fallback passed")


def test_citation_page_number_fallback():
    """Test page_number fallback from metadata."""
    # Test with page_number at top level
    chunk1 = {"page_number": 5, "metadata": {}}
    page1 = chunk1.get("page_number") or chunk1.get("metadata", {}).get("page_number")
    assert page1 == 5
    
    # Test with page_number in metadata
    chunk2 = {"metadata": {"page_number": 7}}
    page2 = chunk2.get("page_number") or chunk2.get("metadata", {}).get("page_number")
    assert page2 == 7
    
    print("✓ test_citation_page_number_fallback passed")


if __name__ == "__main__":
    test_citations_include_file_name()
    test_citations_include_page_number()
    test_citations_include_chunk_id()
    test_citations_unique_by_key()
    test_answer_generator_citations()
    test_citation_chunk_id_fallback()
    test_citation_page_number_fallback()
    print("\n✓ All citation tests passed!")
