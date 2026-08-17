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
        
        Citations are made unique by: file_name, page_number, chunk_id
        
        Args:
            results: List of retrieved chunks
        
        Returns:
            List of unique sources with metadata
        """
        citations = []
        seen_sources = set()
        
        for result in results:
            # Fix chunk_id fallback (Week 5)
            chunk_id = result.get("chunk_id", result.get("id", ""))
            metadata = result.get("metadata", {}) or {}
            file_name = (
                metadata.get("file_name")
                or metadata.get("source")
                or result.get("file_name")
                or "Unknown"
            )
            # Fix page_number fallback (Week 5)
            page_number = (
                result.get("page_number")
                or metadata.get("page_number")
            )
            similarity = result.get("similarity_score", result.get("score", 0))
            
            # Make citations unique by file_name, page_number, chunk_id (Week 5)
            key = (file_name, page_number, chunk_id)
            if key not in seen_sources:
                seen_sources.add(key)
                document_external_id = metadata.get("document_external_id") or result.get("document_external_id")
                document_db_id = result.get("document_id")
                citations.append({
                    "file_name": file_name,
                    "page_number": page_number,
                    "chunk_id": chunk_id,
                    "similarity": similarity,
                    "document_external_id": document_external_id,
                    "document_db_id": document_db_id
                })
        
        return citations
