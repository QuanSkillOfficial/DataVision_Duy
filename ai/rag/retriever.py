"""
Retriever - Finds relevant documents for user queries

Combines embedding and vector search to find the best matching chunks.
Returns results with scores for downstream processing.
"""

from typing import List, Dict, Optional
import numpy as np


class Retriever:
    """Retrieves relevant chunks based on query similarity."""
    
    def __init__(self, embedder, vector_store, top_k: int = 5):
        """
        Initialize the retriever.
        
        Args:
            embedder: Embedder instance to generate query embeddings
            vector_store: VectorStore instance for similarity search
            top_k: Number of top results to return
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.top_k = top_k
    
    def retrieve(self, query: str, top_k: Optional[int] = None, 
                 min_score: float = 0.0, document_id: Optional[str] = None,
                 metadata_filter: Optional[Dict] = None,
                 page_number: Optional[int] = None) -> List[Dict]:
        """
        Retrieve the most relevant chunks for a query with optional filtering.
        
        Args:
            query: User query string
            top_k: Override default top_k if specified
            min_score: Minimum similarity score threshold (0.0-1.0)
            document_id: Filter results to specific document
            metadata_filter: Custom metadata filters (e.g., {"page_number": 1})
            page_number: Shortcut to filter by page number
        
        Returns:
            List of retrieved chunks with similarity scores, sorted by relevance
        """
        k = top_k or self.top_k
        
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Build filter dict
        filters = metadata_filter or {}
        if document_id:
            filters["document_id"] = document_id
        if page_number is not None:
            filters["page_number"] = page_number
        
        # Search vector store with filters
        results = self.vector_store.search(
            query_embedding,
            top_k=k,
            filter_metadata=filters if filters else None
        )
        
        # Filter by minimum score using either score or similarity_score
        results = [r for r in results if (r.get("similarity_score", r.get("score", 0)) >= min_score)]
        
        return results
    
    def retrieve_with_scores(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Retrieve chunks and include similarity scores.
        
        Args:
            query: User query string
            top_k: Override default top_k if specified
        
        Returns:
            List of retrieved chunks with scores
        """
        return self.retrieve(query, top_k=top_k)
    
    def format_for_context(self, results: List[Dict]) -> str:
        """
        Format retrieved results into a context string for the LLM.
        
        Args:
            results: List of retrieved chunks
        
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant information found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.get("metadata", {}).get("source", "Unknown")
            score = result.get("similarity_score", result.get("score", 0))
            text = result.get("text", "")
            
            context_parts.append(
                f"[Source {i}: {source} (similarity: {score:.3f})]\n{text}"
            )
        
        return "\n\n".join(context_parts)
    
    def get_source_citations(self, results: List[Dict]) -> List[Dict]:
        """
        Extract source citations from retrieved results (Week 5 fix).

        Citations are made unique by: file_name, page_number, chunk_id.

        Args:
            results: List of retrieved chunks

        Returns:
            List of unique sources with metadata
        """
        citations = []
        seen_sources = set()

        for result in results:
            chunk_id = result.get("chunk_id", result.get("id", ""))
            metadata = result.get("metadata", {}) or {}
            file_name = (
                result.get("file_name")
                or metadata.get("file_name")
                or metadata.get("source")
                or "Unknown"
            )
            page_number = (
                result.get("page_number")
                or metadata.get("page_number")
            )
            similarity = result.get("similarity_score", result.get("score", 0))
            document_external_id = (
                result.get("document_external_id")
                or metadata.get("document_external_id")
            )
            document_db_id = result.get("document_db_id") or result.get("document_id")

            key = (file_name, page_number, chunk_id)
            if key not in seen_sources and chunk_id:
                seen_sources.add(key)
                citation = {
                    "file_name": file_name,
                    "page_number": page_number,
                    "chunk_id": chunk_id,
                    "similarity": similarity,
                }
                if document_external_id is not None:
                    citation["document_external_id"] = document_external_id
                if document_db_id is not None:
                    citation["document_db_id"] = document_db_id
                citations.append(citation)

        return citations

    def validate_citations(self, citations: List[Dict], retrieved_chunks: List[Dict]) -> Dict:
        """
        Validate that citations correspond one-to-one with retrieved chunks.

        Ensures:
        1. Every citation references a chunk_id that exists in retrieved_chunks.
        2. Every chunk in retrieved_chunks has a matching citation (by chunk_id).
        3. No duplicate citation chunk_ids.
        4. All required citation fields are present.

        Args:
            citations: List of citation dicts from get_source_citations()
            retrieved_chunks: List of retrieved chunk dicts

        Returns:
            Dict with 'is_valid' bool and 'errors'/'warnings' lists
        """
        result = {"is_valid": True, "errors": [], "warnings": []}

        required_citation_fields = ["file_name", "page_number", "chunk_id"]

        retrieved_chunk_ids = set()
        for chunk in retrieved_chunks:
            cid = chunk.get("chunk_id", chunk.get("id"))
            if cid:
                retrieved_chunk_ids.add(cid)

        citation_chunk_ids = set()
        for i, citation in enumerate(citations):
            for field in required_citation_fields:
                if field not in citation:
                    result["is_valid"] = False
                    result["errors"].append(f"Citation #{i} missing required field: {field}")

            cid = citation.get("chunk_id")
            if cid:
                if cid in citation_chunk_ids:
                    result["warnings"].append(f"Duplicate citation chunk_id: {cid}")
                citation_chunk_ids.add(cid)
                if cid not in retrieved_chunk_ids:
                    result["is_valid"] = False
                    result["errors"].append(
                        f"Citation chunk_id {cid!r} not found in retrieved_chunks"
                    )

        for cid in retrieved_chunk_ids:
            if cid not in citation_chunk_ids:
                result["warnings"].append(
                    f"Retrieved chunk {cid!r} does not have a matching citation"
                )

        return result
