"""
RAG Pipeline - Puts everything together

Orchestrates the full flow: chunking → embedding → storage → retrieval
This is the main entry point for the RAG system.
"""

from typing import List, Dict, Optional

try:
    from .chunker import Chunker
    from .embedder import Embedder
    from .vector_store import VectorStore
    from .retriever import Retriever
except ImportError:  # pragma: no cover - direct script execution fallback
    from chunker import Chunker
    from embedder import Embedder
    from vector_store import VectorStore
    from retriever import Retriever


class RAGPipeline:
    """Main RAG pipeline - chunk, embed, store, retrieve."""
    
    def __init__(
        self,
        chunker: Optional[Chunker] = None,
        embedder: Optional[Embedder] = None,
        vector_store: Optional[VectorStore] = None,
        retriever: Optional[Retriever] = None,
        chunk_size: int = 512,
        overlap: int = 50,
        top_k: int = 5
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            chunker: Custom Chunker instance (creates default if None)
            embedder: Custom Embedder instance (creates default if None)
            vector_store: Custom VectorStore instance (creates default if None)
            retriever: Custom Retriever instance (creates default if None)
            chunk_size: Characters per chunk
            overlap: Overlap between chunks
            top_k: Default number of results to retrieve
        """
        self.chunker = chunker or Chunker(chunk_size=chunk_size, overlap=overlap)
        self.embedder = embedder or Embedder()
        self.vector_store = vector_store or VectorStore(use_pgvector=False)
        self.retriever = retriever or Retriever(self.embedder, self.vector_store, top_k=top_k)
        self.documents = {}  # Track ingested documents
    
    def ingest_document(
        self,
        text: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        skip_duplicates: bool = True,
    ) -> Dict:
        """
        Add a document to the RAG system with duplicate protection.

        Args:
            text: Document text
            document_id: Optional document identifier
            metadata: Optional metadata (source, page_number, etc.)
            skip_duplicates: If True, skip chunks whose chunk_id already exists
                             instead of overwriting them.

        Returns:
            Dictionary with ingestion results including duplicate stats
        """
        chunks = self.chunker.chunk_text(text, document_id=document_id, metadata=metadata)

        duplicate_chunk_ids = []
        new_chunks = chunks
        new_chunk_count = len(chunks)

        if chunks and skip_duplicates:
            existing_chunk_ids = set()
            try:
                if hasattr(self.vector_store, "in_memory_store"):
                    existing_chunk_ids = set(self.vector_store.in_memory_store.keys())
                elif hasattr(self.vector_store, "connection") and self.vector_store.connection:
                    cursor = self.vector_store.connection.cursor()
                    candidate_ids = [c["chunk_id"] for c in chunks]
                    if candidate_ids:
                        placeholders = ", ".join(["%s"] * len(candidate_ids))
                        cursor.execute(
                            f"SELECT chunk_id FROM document_chunks WHERE chunk_id IN ({placeholders})",
                            candidate_ids,
                        )
                        for row in cursor.fetchall():
                            existing_chunk_ids.add(row[0])
                    cursor.close()
            except Exception:
                existing_chunk_ids = set()

            duplicate_chunk_ids = [c["chunk_id"] for c in chunks if c["chunk_id"] in existing_chunk_ids]
            if duplicate_chunk_ids:
                new_chunks = [c for c in chunks if c["chunk_id"] not in existing_chunk_ids]
            new_chunk_count = len(new_chunks)

        chunk_texts = [chunk["chunk_text"] for chunk in new_chunks]
        stored_ids = []
        if new_chunks:
            embeddings = self.embedder.embed(chunk_texts)
            added = self.vector_store.add_chunks(new_chunks, embeddings)
            stored_ids = list(added) if added else []

        doc_id = chunks[0]["document_id"] if chunks else document_id

        prior_info = self.documents.get(doc_id)
        prior_chunk_ids = prior_info.get("chunk_ids", []) if prior_info else []
        all_chunk_ids_for_doc = list(dict.fromkeys(prior_chunk_ids + [c["chunk_id"] for c in chunks]))

        self.documents[doc_id] = {
            "text": text,
            "chunks": chunks,
            "chunk_ids": all_chunk_ids_for_doc,
            "num_chunks": len(all_chunk_ids_for_doc),
            "metadata": metadata or {},
        }

        return {
            "document_id": doc_id,
            "num_chunks": len(chunks),
            "chunks_inserted": new_chunk_count,
            "chunks_skipped_duplicates": len(duplicate_chunk_ids),
            "chunk_ids": stored_ids + duplicate_chunk_ids,
            "duplicate_chunk_ids": duplicate_chunk_ids,
            "status": "success",
            "was_reindexed": bool(prior_info),
        }
    
    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        min_score: float = 0.0,
        document_id: Optional[str] = None,
        page_number: Optional[int] = None,
        metadata_filter: Optional[Dict] = None
    ) -> Dict:
        """
        Retrieve relevant chunks for a question with optional filtering.

        Always returns a non-empty answer field and validates citations against
        the retrieved chunks.

        Args:
            question: User query
            top_k: Number of top results (uses default if None)
            min_score: Minimum similarity score threshold (0.0-1.0)
            document_id: Filter to specific document
            page_number: Filter to specific page
            metadata_filter: Custom metadata filters

        Returns:
            Dictionary with retrieved chunks, validated citations, and a
            non-empty answer fallback.
        """
        question = (question or "").strip()

        results = self.retriever.retrieve(
            question,
            top_k=top_k,
            min_score=min_score,
            document_id=document_id,
            page_number=page_number,
            metadata_filter=metadata_filter,
        )

        citations = self.retriever.get_source_citations(results)
        citation_validation = self.retriever.validate_citations(citations, results)

        if not question:
            answer = "Please provide a valid question."
            status = "error"
        elif not results:
            answer = "I do not know based on the provided documents."
            status = "no_answer_found"
        else:
            top_text = (
                results[0].get("chunk_text")
                or results[0].get("text")
                or ""
            ).strip()
            first_sentence = top_text.split(". ")[0].strip()
            if first_sentence:
                if not first_sentence.endswith("."):
                    first_sentence += "."
                answer = first_sentence
            else:
                answer = "I do not know based on the provided documents."
            status = "retrieval_only"

        first_chunk = results[0] if results else None
        if first_chunk:
            chunk_meta = first_chunk.get("metadata", {}) or {}
            file_name = (
                first_chunk.get("file_name")
                or chunk_meta.get("file_name")
                or chunk_meta.get("source")
            )
            document_external_id = (
                first_chunk.get("document_external_id")
                or chunk_meta.get("document_external_id")
            )
            document_db_id = first_chunk.get("document_db_id") or first_chunk.get("document_id_fk")
        else:
            file_name = None
            document_external_id = None
            document_db_id = None

        response = {
            "question": question,
            "answer": answer,
            "retrieved_chunks": results,
            "num_retrieved": len(results),
            "retrieved_context": results,
            "context": self.retriever.format_for_context(results),
            "citations": citations,
            "status": status,
            "model": "all-MiniLM-L6-v2",
            "metadata": {
                "num_chunks_retrieved": len(results),
                "top_k": top_k or self.retriever.top_k,
                "min_score": min_score,
                "citation_valid": citation_validation.get("is_valid", False),
                "citation_errors": citation_validation.get("errors", []),
                "citation_warnings": citation_validation.get("warnings", []),
            },
        }
        if file_name is not None:
            response["file_name"] = file_name
        if document_external_id is not None:
            response["document_external_id"] = document_external_id
        if document_db_id is not None:
            response["document_db_id"] = document_db_id
        return response
    
    def batch_ingest(self, documents: List[Dict]) -> Dict:
        """
        Ingest multiple documents at once.
        
        Args:
            documents: List of document dicts with 'text' and optional 'metadata'
        
        Returns:
            Dictionary with results for all documents
        """
        results = {}
        
        for i, doc in enumerate(documents):
            doc_id = f"doc_{i:03d}"
            result = self.ingest_document(
                text=doc["text"],
                document_id=doc_id,
                metadata=doc.get("metadata", {})
            )
            results[doc_id] = result
        
        return results
    
    def get_document_info(self, document_id: str) -> Dict:
        """Get information about an ingested document."""
        return self.documents.get(document_id, {})
    
    def clear_store(self) -> bool:
        """Wipe all documents from the system."""
        self.vector_store.clear()
        self.documents.clear()
        return True
    
    def get_stats(self) -> Dict:
        """Get statistics about the RAG system."""
        total_docs = len(self.documents)
        total_chunks = sum(doc["num_chunks"] for doc in self.documents.values())
        embedding_dim = self.embedder.get_embedding_dimension()
        
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "embedding_dimension": embedding_dim,
            "vector_store_size": len(self.vector_store.in_memory_store)
        }


if __name__ == "__main__":
    pipeline = RAGPipeline()
    
    test_text = """
    Machine learning is a subset of artificial intelligence that focuses on
    building systems that can learn from data. Deep learning is a specialized
    branch of machine learning that uses neural networks with many layers.
    Natural language processing is another important field that deals with
    the interaction between computers and human language.
    """
    
    print("Ingesting document...")
    result = pipeline.ingest_document(test_text, metadata={"source": "test"})
    print(f" Created {result['num_chunks']} chunks with IDs: {result['chunk_ids']}")
    
    print("\nQuerying the system...")
    query_result = pipeline.query("What is deep learning?")
    print(f"Question: {query_result['question']}")
    print(f"Retrieved {query_result['num_retrieved']} chunks")
    print(f"Context:\n{query_result['context']}")
    
    print("\n\nSystem stats:")
    stats = pipeline.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

