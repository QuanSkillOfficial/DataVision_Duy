"""
RAG Service - Service layer for backend integration

Provides a clean API for backend/FastAPI to interact with the RAG system.
Matches Phi and Hung's UI contract for Chatbot and Report evidence UI.
"""

from typing import List, Dict, Optional
import time


class RAGService:
    """Service layer for RAG operations - backend integration point."""
    
    def __init__(self, embedder, vector_store, retriever, answer_generator=None):
        """
        Initialize the RAG service.
        
        Args:
            embedder: Embedder instance
            vector_store: VectorStore instance
            retriever: Retriever instance
            answer_generator: Optional AnswerGenerator instance
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.retriever = retriever
        self.answer_generator = answer_generator
    
    def retrieve_context(
        self,
        question: str,
        document_id: Optional[int] = None,
        top_k: int = 5,
        metadata_filter: Optional[Dict] = None,
    ) -> Dict:
        """
        Retrieve relevant context for a question (Week 5).

        This is the primary function for backend/FastAPI integration.
        Returns a response matching Phi and Hung's UI contract.

        Args:
            question: User's question
            document_id: Optional document ID (INTEGER FK to documents.id)
            top_k: Number of top chunks to retrieve

        Returns:
            Dictionary matching UI contract - always non-empty structure.
        """
        start_time = time.time()

        question = (question or "").strip()

        metadata_filter = dict(metadata_filter or {})
        if document_id is not None:
            metadata_filter["document_id"] = document_id

        try:
            retrieved_chunks = self.retriever.retrieve(
                query=question,
                top_k=top_k,
                metadata_filter=metadata_filter if metadata_filter else None
            )
        except Exception as e:
            return {
                "question": question,
                "answer": "I do not know based on the provided documents.",
                "retrieved_context": [],
                "citations": [],
                "status": "error",
                "model": "all-MiniLM-L6-v2",
                "error": str(e),
                "metadata": {
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                    "num_chunks_retrieved": 0,
                    "document_id": document_id,
                    "reason": f"Retrieval error: {e}",
                    "error_code": "RETRIEVAL_EXCEPTION",
                },
            }

        citations = self.retriever.get_source_citations(retrieved_chunks)
        citation_validation = self.retriever.validate_citations(citations, retrieved_chunks)

        if not question:
            status = "error"
            default_answer = "Please provide a valid question."
            reason = "Question cannot be empty"
            error_code = "INVALID_QUESTION"
        elif not retrieved_chunks:
            status = "no_answer_found"
            default_answer = "I do not know based on the provided documents."
            reason = "No chunks matched the query above similarity threshold"
            error_code = None
        else:
            status = "retrieval_only"
            default_answer = None
            reason = None
            error_code = None

        first_chunk = retrieved_chunks[0] if retrieved_chunks else None
        if first_chunk:
            chunk_meta = first_chunk.get("metadata", {}) or {}
            document_external_id = (
                first_chunk.get("document_external_id")
                or chunk_meta.get("document_external_id")
            )
            file_name = (
                first_chunk.get("file_name")
                or chunk_meta.get("file_name")
                or chunk_meta.get("source")
            )
            document_db_id = first_chunk.get("document_db_id") or first_chunk.get("document_id")
        else:
            document_external_id = None
            file_name = None
            document_db_id = document_id

        latency_ms = (time.time() - start_time) * 1000

        answer_value = (
            default_answer
            if default_answer is not None
            else self._summarize_top_chunk(retrieved_chunks)
        )

        response = {
            "question": question,
            "answer": answer_value,
            "retrieved_context": retrieved_chunks,
            "citations": citations,
            "status": status,
            "model": "all-MiniLM-L6-v2",
            "metadata": {
                "latency_ms": round(latency_ms, 2),
                "num_chunks_retrieved": len(retrieved_chunks),
                "document_id": document_id,
                "top_k": top_k,
                "filter_applied": metadata_filter or None,
                "reason": reason,
                "error_code": error_code,
                "citation_valid": citation_validation.get("is_valid", False),
                "citation_errors": citation_validation.get("errors", []),
                "citation_warnings": citation_validation.get("warnings", []),
            },
        }

        if document_external_id is not None:
            response["document_external_id"] = document_external_id
        if document_db_id is not None:
            response["document_db_id"] = document_db_id
        if file_name is not None:
            response["file_name"] = file_name

        return response

    @staticmethod
    def _summarize_top_chunk(retrieved_chunks: List[Dict]) -> Optional[str]:
        """Return a deterministic non-empty answer fallback from the top chunk."""
        if not retrieved_chunks:
            return None
        top_chunk = retrieved_chunks[0]
        text = (
            top_chunk.get("chunk_text")
            or top_chunk.get("text")
            or ""
        ).strip()
        if not text:
            return None
        first_sentence = text.split(". ")[0].strip()
        if first_sentence and not first_sentence.endswith("."):
            first_sentence += "."
        return first_sentence or None
    
    def query_with_answer(
        self,
        question: str,
        document_id: Optional[int] = None,
        top_k: int = 5,
        metadata_filter: Optional[Dict] = None,
    ) -> Dict:
        """
        Retrieve context and generate answer (Week 5 - secondary).

        This function adds LLM answer generation on top of retrieval.
        Only used if LLM is configured and retrieval is stable.

        Args:
            question: User's question
            document_id: Optional document ID
            top_k: Number of top chunks to retrieve

        Returns:
            Dictionary with answer if LLM available, otherwise retrieval_only.
            Always contains a non-empty answer field.
        """
        response = self.retrieve_context(question, document_id, top_k, metadata_filter=metadata_filter)

        if not self.answer_generator:
            if not response["answer"]:
                response["answer"] = "I do not know based on the provided documents."
            return response

        if not response["retrieved_context"]:
            response["status"] = "no_context"
            response["answer"] = response.get("answer") or "I do not know based on the provided documents."
            return response

        try:
            answer_result = self.answer_generator.generate_answer(
                question=question,
                retrieved_chunks=response["retrieved_context"]
            )

            llm_answer = answer_result.get("answer")
            if not llm_answer:
                llm_answer = response.get("answer") or "I do not know based on the provided documents."

            response["answer"] = llm_answer
            response["status"] = answer_result.get("status", "answered")
            response["metadata"]["llm_model"] = answer_result.get("model")
            response["metadata"]["confidence"] = answer_result.get("confidence", 0.0)

            if "i do not know" in llm_answer.lower() or "not provided" in llm_answer.lower():
                if response["status"] == "answered":
                    response["status"] = "no_answer"

        except Exception as e:
            response["status"] = "llm_error"
            response["error"] = str(e)
            if not response["answer"]:
                response["answer"] = "I do not know based on the provided documents."

        return response
    
    def log_rag_query(
        self,
        document_id: int,
        user_query: str,
        retrieved_chunk_ids: List[str],
        retrieval_scores: List[float],
        generated_response: Optional[str],
        answer_confidence: float,
        latency_ms: float,
        model_name: str = "all-MiniLM-L6-v2"
    ) -> Dict:
        """
        Build log payload for RAG query logging (Week 5).
        
        This function builds the payload for logging RAG queries
        to the rag_query_logs table (Phat's schema).
        
        Args:
            document_id: Document ID (INTEGER FK)
            user_query: User's question
            retrieved_chunk_ids: List of chunk IDs retrieved
            retrieval_scores: List of similarity scores
            generated_response: Generated answer (or None)
            answer_confidence: Confidence score (0.0-1.0)
            latency_ms: Query latency in milliseconds
            model_name: Model name used
        
        Returns:
            Dictionary payload for logging
        """
        payload = {
            "document_id": document_id,
            "user_query": user_query,
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "retrieval_scores": retrieval_scores,
            "generated_response": generated_response,
            "answer_confidence": answer_confidence,
            "latency_ms": latency_ms,
            "model_name": model_name
        }
        
        return payload


def insert_rag_query_log(conn, log_payload: Dict) -> Dict:
    """Insert a RAG query log payload into Phat's rag_query_logs table if possible."""
    if conn is None:
        raise ValueError("A database connection is required to insert a query log")

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO rag_query_logs (
                document_id,
                user_query,
                retrieved_chunk_ids,
                retrieval_scores,
                generated_response,
                answer_confidence,
                latency_ms,
                model_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                log_payload.get("document_id"),
                log_payload.get("user_query"),
                log_payload.get("retrieved_chunk_ids"),
                log_payload.get("retrieval_scores"),
                log_payload.get("generated_response"),
                log_payload.get("answer_confidence"),
                log_payload.get("latency_ms"),
                log_payload.get("model_name"),
            ),
        )
        conn.commit()
        return log_payload
    except Exception as exc:
        conn.rollback()
        raise RuntimeError(f"Failed to insert rag_query_log: {exc}") from exc
    finally:
        cursor.close()


def create_rag_service(
    connection_string: Optional[str] = None,
    use_pgvector: bool = False,
    llm_model: Optional[str] = None,
    llm_api_key: Optional[str] = None
) -> RAGService:
    """
    Factory function to create a configured RAG service.
    
    Args:
        connection_string: PostgreSQL connection string
        use_pgvector: Whether to use pgvector (True) or in-memory (False)
        llm_model: Optional LLM model name
        llm_api_key: Optional LLM API key
    
    Returns:
        Configured RAGService instance
    """
    from .embedder import Embedder
    from .vector_store import VectorStore
    from .retriever import Retriever
    from .answer_generator import AnswerGenerator
    
    # Initialize components
    embedder = Embedder()
    vector_store = VectorStore(use_pgvector=use_pgvector, connection_string=connection_string)
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=5)
    
    # Initialize answer generator if LLM credentials provided
    answer_generator = None
    if llm_model and llm_api_key:
        answer_generator = AnswerGenerator(llm_model=llm_model, api_key=llm_api_key)
    
    # Create service
    service = RAGService(
        embedder=embedder,
        vector_store=vector_store,
        retriever=retriever,
        answer_generator=answer_generator
    )
    
    return service


if __name__ == "__main__":
    print("=== Testing RAGService ===\n")
    
    # Test with in-memory store
    from .embedder import Embedder
    from .vector_store import VectorStore
    from .retriever import Retriever
    
    embedder = Embedder()
    vector_store = VectorStore(use_pgvector=False)
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    
    service = RAGService(embedder, vector_store, retriever)
    
    # Test retrieve_context
    print("Testing retrieve_context...")
    response = service.retrieve_context("What is machine learning?")
    print(f" Status: {response['status']}")
    print(f" Chunks retrieved: {len(response['retrieved_context'])}")
    print(f" Citations: {len(response['citations'])}\n")
    
    # Test log payload
    print("Testing log_rag_query...")
    log_payload = service.log_rag_query(
        document_id=1,
        user_query="What is the data pipeline?",
        retrieved_chunk_ids=["doc_001_page_4_chunk_002", "doc_001_page_5_chunk_000"],
        retrieval_scores=[0.84, 0.79],
        generated_response=None,
        answer_confidence=0.84,
        latency_ms=320
    )
    print(f" Log payload: {log_payload}\n")
