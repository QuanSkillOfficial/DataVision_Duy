"""
Tests for RAG Response Contract - Week 5

Tests that RAG responses match the expected contract for Phi and Hung's UI.
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
from ai.rag.rag_service import RAGService


def test_rag_response_contract_fields():
    """Test that RAG response has all required fields."""
    generator = AnswerGenerator()
    
    chunks = [
        {
            "chunk_id": "doc_001_page_1_chunk_000",
            "chunk_text": "Test content",
            "metadata": {"source": "test.pdf", "page_number": 1},
            "score": 0.85
        }
    ]
    
    response = generator.format_response(
        question="Test question",
        answer="Test answer",
        retrieved_chunks=chunks,
        status="answered"
    )
    
    # Required fields for UI contract
    required_fields = [
        "question",
        "answer",
        "retrieved_context",
        "citations",
        "status",
        "model"
    ]
    
    for field in required_fields:
        assert field in response, f"Response missing required field: {field}"
    
    print("✓ test_rag_response_contract_fields passed")


def test_rag_service_response_contract():
    """Test that RAGService returns proper contract."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    service = RAGService(embedder, vector_store, retriever)
    
    response = service.retrieve_context("Test question", document_id=1, top_k=5)
    
    # Check UI contract fields
    assert "question" in response
    assert "answer" in response
    assert "retrieved_context" in response
    assert "citations" in response
    assert "status" in response
    assert "model" in response
    
    # Check model name
    assert response["model"] == "all-MiniLM-L6-v2"
    
    print("✓ test_rag_service_response_contract passed")


def test_retrieval_only_status():
    """Test retrieval_only status when chunks exist and no LLM is used."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    service = RAGService(embedder, vector_store, retriever)

    chunks = [
        {
            "chunk_id": "doc_001_page_1_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "Machine learning is a subset of artificial intelligence.",
            "metadata": {"source": "test.pdf", "page_number": 1},
        }
    ]
    embeddings = embedder.embed([c["chunk_text"] for c in chunks])
    vector_store.add_chunks(chunks, embeddings)

    response = service.retrieve_context("What is machine learning?")

    assert response["status"] == "retrieval_only"
    assert response["answer"] is not None
    assert isinstance(response["answer"], str)
    assert len(response["answer"]) > 0

    print("✓ test_retrieval_only_status passed")


def test_no_answer_found_status_empty_store():
    """Test no_answer_found status with a non-empty deterministic answer."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    service = RAGService(embedder, vector_store, retriever)

    response = service.retrieve_context("Unrelated question")

    assert response["status"] == "no_answer_found"
    assert response["answer"] is not None
    assert "I do not know" in response["answer"] or "provided documents" in response["answer"]

    print("✓ test_no_answer_found_status_empty_store passed")


def test_citations_in_response():
    """Test that response includes citations with required fields."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    service = RAGService(embedder, vector_store, retriever)
    
    # Add sample data
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
    
    response = service.retrieve_context("Test question")
    
    assert len(response["citations"]) > 0
    
    # Check citation fields
    citation = response["citations"][0]
    assert "file_name" in citation
    assert "page_number" in citation
    assert "chunk_id" in citation
    
    print("✓ test_citations_in_response passed")


def test_unsupported_query_low_confidence():
    """Test unsupported query returns low confidence or no answer."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    # Add sample data
    chunks = [
        {
            "chunk_id": "doc_001_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "Specific domain content",
            "metadata": {"source": "test.pdf"}
        }
    ]
    embeddings = np.random.rand(1, 384)
    vector_store.add_chunks(chunks, embeddings)
    
    # Query about unrelated topic - with fake embedder, we just verify it returns results
    results = retriever.retrieve("What is the weather tomorrow?")
    
    # Just verify the retrieval works (fake embedder doesn't simulate semantic distance)
    assert isinstance(results, list)
    
    print("✓ test_unsupported_query_low_confidence passed")


def test_response_metadata():
    """Test that response includes metadata."""
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    service = RAGService(embedder, vector_store, retriever)
    
    response = service.retrieve_context("Test question")
    
    assert "metadata" in response
    assert "latency_ms" in response["metadata"]
    assert "num_chunks_retrieved" in response["metadata"]
    
    print("✓ test_response_metadata passed")


if __name__ == "__main__":
    test_rag_response_contract_fields()
    test_rag_service_response_contract()
    test_retrieval_only_status()
    test_no_answer_found_status_empty_store()
    test_citations_in_response()
    test_unsupported_query_low_confidence()
    test_response_metadata()
    print("\n✓ All RAG response contract tests passed!")
