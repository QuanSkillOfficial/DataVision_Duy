"""
Week 7 pgvector Smoke Test

Tests pgvector connection, chunk insertion, and retrieval for the DataFlow document.
This script proves that the RAG pipeline works end-to-end with Phat's database.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ai.rag.embedder import Embedder
from ai.rag.vector_store import VectorStore, resolve_document_db_id
from ai.rag.retriever import Retriever
from ai.rag.rag_service import RAGService


def run_pgvector_smoke_test(
    query: str,
    document_external_id: str,
    top_k: int = 5,
    connection_string: Optional[str] = None,
    output_result_path: Optional[str] = None,
) -> dict:
    """
    Run pgvector smoke test to verify RAG pipeline works with real database.
    
    Args:
        query: Test query to search for
        document_external_id: Document to search within
        top_k: Number of results to retrieve
        connection_string: Database connection string
        output_result_path: Optional path to write result JSON
    
    Returns:
        Dictionary with test results and retrieved chunks
    """
    start_time = time.time()
    result = {
        "status": "pending",
        "query": query,
        "document_external_id": document_external_id,
        "top_k": top_k,
        "document_db_id": None,
        "retrieved_chunks": [],
        "citations": [],
        "latency_ms": 0,
        "errors": []
    }
    
    try:
        print(f"=== Week 7 pgvector Smoke Test ===")
        print(f"Query: {query}")
        print(f"Document: {document_external_id}")
        print(f"Top-K: {top_k}")
        print()
        
        # Step 1: Connect to database
        print("Step 1: Connecting to pgvector database...")
        vector_store = VectorStore(use_pgvector=True, connection_string=connection_string)
        if not getattr(vector_store, "connection", None):
            raise RuntimeError("Unable to connect to pgvector - check connection string")
        print("✓ Connected to database")
        print()
        
        # Step 2: Resolve document_external_id
        print(f"Step 2: Resolving document_external_id: {document_external_id}")
        document_db_id = resolve_document_db_id(vector_store.connection, document_external_id)
        result["document_db_id"] = document_db_id
        print(f"✓ Resolved to document_db_id: {document_db_id}")
        print()
        
        # Step 3: Initialize embedder
        print("Step 3: Initializing embedder...")
        embedder = Embedder()
        embedding_dimension = embedder.get_embedding_dimension()
        print(f"✓ Embedder initialized (dimension: {embedding_dimension})")
        print()
        
        # Step 4: Initialize retriever
        print("Step 4: Initializing retriever...")
        retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=top_k)
        print("✓ Retriever initialized")
        print()
        
        # Step 5: Run retrieval
        print(f"Step 5: Running retrieval for query: '{query}'")
        retrieval_start = time.time()
        retrieved_chunks = retriever.retrieve(query, document_id=document_db_id)
        retrieval_time = (time.time() - retrieval_start) * 1000
        print(f"✓ Retrieved {len(retrieved_chunks)} chunks in {retrieval_time:.2f}ms")
        print()
        
        # Step 6: Format results
        print("Step 6: Formatting results...")
        result["retrieved_chunks"] = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            chunk_result = {
                "rank": i,
                "chunk_id": chunk.get("chunk_id"),
                "document_db_id": chunk.get("document_id"),
                "document_external_id": document_external_id,
                "page_number": chunk.get("page_number"),
                "chunk_text": chunk.get("chunk_text")[:200] + "..." if len(chunk.get("chunk_text", "")) > 200 else chunk.get("chunk_text", ""),
                "similarity_score": chunk.get("similarity_score", chunk.get("score", 0))
            }
            result["retrieved_chunks"].append(chunk_result)
            print(f"  {i}. Chunk: {chunk.get('chunk_id')}")
            print(f"     Page: {chunk.get('page_number')}")
            print(f"     Similarity: {chunk.get('similarity_score', chunk.get('score', 0)):.3f}")
            print(f"     Text: {chunk_result['chunk_text']}")
            print()
        
        # Step 7: Generate citations
        print("Step 7: Generating citations...")
        citations = retriever.get_source_citations(retrieved_chunks)
        result["citations"] = citations
        print(f"✓ Generated {len(citations)} citations")
        for citation in citations:
            print(f"  - {citation.get('file_name')}, Page {citation.get('page_number')}, Chunk {citation.get('chunk_id')}")
        print()
        
        # Step 8: Complete
        result["status"] = "success"
        result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
        print(f"=== Test Complete ===")
        print(f"Status: Success")
        print(f"Total Latency: {result['latency_ms']}ms")
        print(f"Chunks Retrieved: {len(retrieved_chunks)}")
        print(f"Citations Generated: {len(citations)}")
        
    except RuntimeError as e:
        result["status"] = "error"
        result["errors"].append(f"Database error: {e}")
        print(f"ERROR: {e}")
        
    except ValueError as e:
        result["status"] = "error"
        result["errors"].append(f"Validation error: {e}")
        print(f"ERROR: {e}")
        
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Unexpected error: {e}")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 9: Write result to file if requested
    if output_result_path:
        try:
            with open(output_result_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nResult written to {output_result_path}")
        except Exception as e:
            print(f"Warning: Could not write result to {output_result_path}: {e}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Week 7 pgvector smoke test")
    parser.add_argument("--query", required=True, help="Query to test retrieval")
    parser.add_argument("--document-external-id", required=True, help="Document external ID")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to retrieve")
    parser.add_argument("--connection-string", default=None, help="Database connection string")
    parser.add_argument("--output-result", default=None, help="Path to write result JSON")
    args = parser.parse_args()
    
    result = run_pgvector_smoke_test(
        query=args.query,
        document_external_id=args.document_external_id,
        top_k=args.top_k,
        connection_string=args.connection_string,
        output_result_path=args.output_result,
    )
    
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    
    # Exit with error code if status is error
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
