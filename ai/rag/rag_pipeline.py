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
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Add a document to the RAG system.

        Args:
            text: Document text
            document_id: Optional document identifier
            metadata: Optional metadata (source, page_number, etc.)

        Returns:
            Dictionary with ingestion results
        """
        # Chunk the document
        chunks = self.chunker.chunk_text(text, document_id=document_id, metadata=metadata)

        # Extract chunk texts
        chunk_texts = [chunk["chunk_text"] for chunk in chunks]

        # Generate embeddings
        embeddings = self.embedder.embed(chunk_texts)

        # Store chunks with embeddings (preserves chunk IDs!)
        chunk_ids = self.vector_store.add_chunks(chunks, embeddings)

        # Track document
        doc_id = chunks[0]["document_id"] if chunks else document_id
        self.documents[doc_id] = {
            "text": text,
            "chunks": chunks,
            "chunk_ids": chunk_ids,
            "num_chunks": len(chunks),
            "metadata": metadata or {}
        }

        return {
            "document_id": doc_id,
            "num_chunks": len(chunks),
            "chunk_ids": chunk_ids,
            "status": "success"
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

        Args:
            question: User query
            top_k: Number of top results (uses default if None)
            min_score: Minimum similarity score threshold (0.0-1.0)
            document_id: Filter to specific document
            page_number: Filter to specific page
            metadata_filter: Custom metadata filters

        Returns:
            Dictionary with retrieved chunks and metadata
        """
        results = self.retriever.retrieve(
            question,
            top_k=top_k,
            min_score=min_score,
            document_id=document_id,
            page_number=page_number,
            metadata_filter=metadata_filter
        )

        return {
            "question": question,
            "retrieved_chunks": results,
            "num_retrieved": len(results),
            "context": self.retriever.format_for_context(results),
            "citations": self.retriever.get_source_citations(results)
        }

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
