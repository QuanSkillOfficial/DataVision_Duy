"""
Week 7 RAG CI Smoke Test

Fast CI-safe smoke test for GitHub Actions.
Uses fake implementations to avoid external dependencies (database, model downloads).
Tests the RAG pipeline end-to-end without requiring real infrastructure.
"""

import sys
import json
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ai.ai_tests.fakes import FakeEmbedder, FakeVectorStore, create_sample_chunks, create_sample_pages
from ai.rag.chunker import Chunker
from ai.rag.document_loader import DocumentLoader
from ai.rag.retriever import Retriever
from ai.rag.rag_service import RAGService


def run_ci_smoke_test():
    """
    Run CI smoke test to verify RAG pipeline works without external dependencies.
    
    Returns:
        Dictionary with test results
    """
    results = {
        "status": "pending",
        "tests": [],
        "errors": []
    }
    
    try:
        print("=== Week 7 RAG CI Smoke Test ===\n")
        
        # Test 1: Chunker
        print("Test 1: Chunker")
        chunker = Chunker(chunk_size=100, overlap=10)
        text = "A" * 200
        chunks = chunker.chunk_text(text, document_id="doc_001")
        assert len(chunks) > 0, "Chunker should create chunks"
        assert all("chunk_id" in c for c in chunks), "Chunks should have chunk_id"
        assert all("document_id" in c for c in chunks), "Chunks should have document_id"
        results["tests"].append({"name": "chunker", "status": "pass"})
        print("✓ Chunker test passed\n")
        
        # Test 2: Document Loader
        print("Test 2: Document Loader")
        pages = create_sample_pages(3)
        chunks = DocumentLoader.pages_to_chunks(pages, chunk_size=50, overlap=5)
        assert len(chunks) > 0, "Document loader should create chunks"
        results["tests"].append({"name": "document_loader", "status": "pass"})
        print("✓ Document Loader test passed\n")
        
        # Test 3: Fake Embedder
        print("Test 3: Fake Embedder")
        embedder = FakeEmbedder()
        embedding = embedder.embed("test text")
        assert embedding.shape == (1, 384), "Embedding should be 384-dimensional"
        assert embedder.get_embedding_dimension() == 384, "Dimension should be 384"
        results["tests"].append({"name": "fake_embedder", "status": "pass"})
        print("✓ Fake Embedder test passed\n")
        
        # Test 4: Fake Vector Store
        print("Test 4: Fake Vector Store")
        vector_store = FakeVectorStore()
        chunks = create_sample_chunks(5)
        embeddings = embedder.embed([c["chunk_text"] for c in chunks])
        vector_store.add_chunks(chunks, embeddings)
        assert len(vector_store.chunks) == 5, "Vector store should have 5 chunks"
        results["tests"].append({"name": "fake_vector_store", "status": "pass"})
        print("✓ Fake Vector Store test passed\n")
        
        # Test 5: Retriever
        print("Test 5: Retriever")
        retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=3)
        retrieved = retriever.retrieve("test query")
        assert len(retrieved) <= 3, f"Retriever should return at most 3 results, got {len(retrieved)}"
        assert all("chunk_id" in r for r in retrieved), "Results should have chunk_id"
        assert all("similarity_score" in r for r in retrieved), "Results should have similarity_score"
        results["tests"].append({"name": "retriever", "status": "pass"})
        print("✓ Retriever test passed\n")
        
        # Test 6: RAG Service
        print("Test 6: RAG Service")
        service = RAGService(embedder, vector_store, retriever)
        response = service.retrieve_context("test question", document_id="doc_001", top_k=3)
        assert "question" in response, "Response should have question"
        assert "retrieved_context" in response, "Response should have retrieved_context"
        assert "citations" in response, "Response should have citations"
        assert "status" in response, "Response should have status"
        assert response["status"] == "retrieval_only", "Status should be retrieval_only"
        results["tests"].append({"name": "rag_service", "status": "pass"})
        print("✓ RAG Service test passed\n")
        
        # Test 7: Citation Format
        print("Test 7: Citation Format")
        assert len(response["citations"]) > 0, "Should have citations"
        citation = response["citations"][0]
        assert "file_name" in citation, "Citation should have file_name"
        assert "page_number" in citation, "Citation should have page_number"
        assert "chunk_id" in citation, "Citation should have chunk_id"
        results["tests"].append({"name": "citation_format", "status": "pass"})
        print("✓ Citation Format test passed\n")
        
        # Test 8: Response Metadata
        print("Test 8: Response Metadata")
        assert "metadata" in response, "Response should have metadata"
        assert "latency_ms" in response["metadata"], "Metadata should have latency_ms"
        assert "num_chunks_retrieved" in response["metadata"], "Metadata should have num_chunks_retrieved"
        results["tests"].append({"name": "response_metadata", "status": "pass"})
        print("✓ Response Metadata test passed\n")
        
        # Test 9: Document Filter
        print("Test 9: Document Filter")
        filtered = retriever.retrieve("test query", document_id="doc_001")
        assert len(filtered) > 0, "Should return results with document filter"
        results["tests"].append({"name": "document_filter", "status": "pass"})
        print("✓ Document Filter test passed\n")
        
        # Test 10: Top-K Limit
        print("Test 10: Top-K Limit")
        retriever_top2 = Retriever(embedder=embedder, vector_store=vector_store, top_k=2)
        retrieved_top2 = retriever_top2.retrieve("test query")
        assert len(retrieved_top2) <= 2, f"Should return at most 2 results, got {len(retrieved_top2)}"
        results["tests"].append({"name": "top_k_limit", "status": "pass"})
        print("✓ Top-K Limit test passed\n")
        
        # Finalize
        results["status"] = "success"
        results["total_tests"] = len(results["tests"])
        results["passed_tests"] = len([t for t in results["tests"] if t["status"] == "pass"])
        results["failed_tests"] = len([t for t in results["tests"] if t["status"] == "fail"])
        
        print("=== CI Smoke Test Complete ===")
        print(f"Status: {results['status']}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        
    except AssertionError as e:
        results["status"] = "error"
        results["errors"].append(f"Assertion failed: {e}")
        print(f"ERROR: {e}")
        
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Unexpected error: {e}")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    return results


def main():
    """Main entry point for CI smoke test."""
    results = run_ci_smoke_test()
    
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(json.dumps(results, indent=2))
    
    # Exit with error code if any test failed
    if results["status"] == "error" or results["failed_tests"] > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
