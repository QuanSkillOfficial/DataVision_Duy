"""
RAG Service - Service layer for backend integration

Provides a clean API for backend/FastAPI to interact with the RAG system.
Matches Phi and Hung's UI contract for Chatbot and Report evidence UI.

Every query that goes through retrieve_context() / query_with_answer() is
automatically logged into Phat's rag_query_logs table, as long as
vector_store.connection is a live pgvector/psycopg2 connection. Logging
failures never break the response returned to the caller.
"""

import json
import time
from typing import List, Dict, Optional


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
        log_query: bool = True,
    ) -> Dict:
        """
        Retrieve relevant context for a question (Week 5).

        This is the primary function for backend/FastAPI integration.
        Returns a response matching Phi and Hung's UI contract.

        Args:
            question: User's question
            document_id: Optional document ID (INTEGER FK to documents.id)
            top_k: Number of top chunks to retrieve
            metadata_filter: Optional extra metadata filter
            log_query: Whether to write this query to rag_query_logs.
                Set to False when called internally by query_with_answer(),
                which logs once itself after the answer is generated —
                otherwise every answered query would be logged twice
                (once retrieval-only, once with the final answer).

        Returns:
            Dictionary matching UI contract:
            {
                "question": "...",
                "answer": null,
                "retrieved_context": [...],
                "citations": [...],
                "status": "retrieval_only",
                "model": "all-MiniLM-L6-v2"
            }
        """
        start_time = time.time()

        # Build metadata filter
        metadata_filter = dict(metadata_filter or {})
        if document_id is not None:
            metadata_filter["document_id"] = document_id

        # Retrieve chunks
        try:
            retrieved_chunks = self.retriever.retrieve(
                query=question,
                top_k=top_k,
                metadata_filter=metadata_filter if metadata_filter else None
            )
        except Exception as e:
            error_response = {
                "question": question,
                "answer": None,
                "retrieved_context": [],
                "citations": [],
                "status": "error",
                "model": "all-MiniLM-L6-v2",
                "error": str(e)
            }
            if log_query:
                self._log_query_safe(
                    question=question,
                    document_id=document_id,
                    response=error_response,
                    latency_ms=(time.time() - start_time) * 1000,
                )
            return error_response

        # Extract citations
        citations = self.retriever.get_source_citations(retrieved_chunks)

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Build response matching UI contract
        response = {
            "question": question,
            "answer": None,  # Will be filled by LLM if available
            "retrieved_context": retrieved_chunks,
            "citations": citations,
            "status": "retrieval_only",
            "model": "all-MiniLM-L6-v2",
            "metadata": {
                "latency_ms": round(latency_ms, 2),
                "num_chunks_retrieved": len(retrieved_chunks),
                "document_id": document_id
            }
        }

        if log_query:
            self._log_query_safe(
                question=question,
                document_id=document_id,
                response=response,
                latency_ms=latency_ms,
            )

        return response

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

        The query is logged exactly once, after the answer (if any) has
        been generated, so the log reflects the final response — not just
        the intermediate retrieval-only step.

        Args:
            question: User's question
            document_id: Optional document ID
            top_k: Number of top chunks to retrieve
            metadata_filter: Optional extra metadata filter

        Returns:
            Dictionary with answer if LLM available, otherwise retrieval_only
        """
        start_time = time.time()

        # First, retrieve context — suppress its own logging, we log once at the end
        response = self.retrieve_context(
            question, document_id, top_k, metadata_filter=metadata_filter, log_query=False
        )

        # If no answer generator, return retrieval-only response (still log it)
        if not self.answer_generator:
            self._log_query_safe(
                question=question,
                document_id=document_id,
                response=response,
                latency_ms=(time.time() - start_time) * 1000,
            )
            return response

        # If no chunks retrieved, return retrieval-only with low confidence
        if not response["retrieved_context"]:
            response["status"] = "no_context"
            response["answer"] = "I do not know based on the provided documents."
            self._log_query_safe(
                question=question,
                document_id=document_id,
                response=response,
                latency_ms=(time.time() - start_time) * 1000,
            )
            return response

        # Generate answer using LLM
        try:
            answer_result = self.answer_generator.generate_answer(
                question=question,
                retrieved_chunks=response["retrieved_context"]
            )

            # Update response with answer
            response["answer"] = answer_result.get("answer")
            response["status"] = answer_result.get("status", "answered")
            response["metadata"]["llm_model"] = answer_result.get("model")
            response["metadata"]["confidence"] = answer_result.get("confidence", 0.0)

            # If LLM indicated it doesn't know, update status
            if response["answer"] and "i do not know" in response["answer"].lower():
                response["status"] = "no_answer"

        except Exception as e:
            # Fallback to retrieval-only on error
            response["status"] = "llm_error"
            response["error"] = str(e)

        self._log_query_safe(
            question=question,
            document_id=document_id,
            response=response,
            latency_ms=(time.time() - start_time) * 1000,
        )

        return response

    def log_rag_query(
        self,
        document_id: Optional[int],
        user_query: str,
        retrieved_chunk_ids: List[str],
        retrieval_scores: List[float],
        generated_response: Optional[str],
        answer_confidence: Optional[float],
        latency_ms: float,
        model_name: str = "all-MiniLM-L6-v2"
    ) -> Dict:
        """
        Build log payload for RAG query logging (Week 5).

        This function builds the payload for logging RAG queries
        to the rag_query_logs table (Phat's schema).

        Args:
            document_id: Document ID (INTEGER FK), may be None
            user_query: User's question
            retrieved_chunk_ids: List of chunk IDs retrieved
            retrieval_scores: List of similarity scores
            generated_response: Generated answer (or None)
            answer_confidence: Confidence score (0.0-1.0), may be None
            latency_ms: Query latency in milliseconds
            model_name: Model name used

        Returns:
            Dictionary payload for logging, matching rag_query_logs columns
        """
        payload = {
            "document_id": document_id,
            "user_query": user_query,
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "retrieval_scores": retrieval_scores,
            "generated_response": generated_response,
            "answer_confidence": answer_confidence,
            "latency_ms": int(round(latency_ms)),
            "model_name": model_name
        }

        return payload

    def _log_query_safe(
        self,
        question: str,
        document_id: Optional[int],
        response: Dict,
        latency_ms: float,
    ) -> None:
        """
        Build the log payload from a response dict and insert it into
        rag_query_logs, if (and only if) a live DB connection is available.

        Never raises — a logging failure must not break the actual answer
        returned to the user. Errors are printed as a warning instead.
        """
        conn = getattr(self.vector_store, "connection", None)
        if conn is None:
            return  # in-memory mode (no pgvector connection) — nothing to log to

        retrieved_context = response.get("retrieved_context") or []
        retrieved_chunk_ids = [c.get("chunk_id") for c in retrieved_context]
        retrieval_scores = [
            c.get("score", c.get("similarity_score")) for c in retrieved_context
        ]

        # Prefer the LLM confidence if one was generated, otherwise fall back
        # to the top retrieval score as a rough proxy.
        answer_confidence = None
        if response.get("metadata"):
            answer_confidence = response["metadata"].get("confidence")
        if answer_confidence is None and retrieval_scores:
            answer_confidence = retrieval_scores[0]

        try:
            log_payload = self.log_rag_query(
                document_id=document_id,
                user_query=question,
                retrieved_chunk_ids=retrieved_chunk_ids,
                retrieval_scores=retrieval_scores,
                generated_response=response.get("answer"),
                answer_confidence=answer_confidence,
                latency_ms=latency_ms,
                model_name=response.get("model", "all-MiniLM-L6-v2"),
            )
            log_id = insert_rag_query_log(conn, log_payload)
            response.setdefault("metadata", {})["log_id"] = log_id
        except Exception as e:
            # Logging must never break the user-facing response.
            print(f"Warning: failed to log rag query to rag_query_logs: {e}")


def insert_rag_query_log(conn, log_payload: Dict) -> int:
    """
    Insert a RAG query log payload into Phat's rag_query_logs table.

    Matches the actual schema (schema_v4_fixed.sql):
        document_id, user_query, retrieved_chunk_ids (JSONB),
        retrieval_scores (JSONB), generated_response, answer_confidence,
        latency_ms, model_name

    retrieved_chunk_ids / retrieval_scores are JSONB columns, so Python
    lists must be JSON-encoded before binding — passing a raw list lets
    psycopg2 adapt it as a Postgres array instead, which does not match
    the JSONB column type and will raise a type error.

    Returns:
        The inserted row's id.
    """
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
            RETURNING id
            """,
            (
                log_payload.get("document_id"),
                log_payload.get("user_query"),
                json.dumps(log_payload.get("retrieved_chunk_ids") or []),
                json.dumps(log_payload.get("retrieval_scores") or []),
                log_payload.get("generated_response"),
                log_payload.get("answer_confidence"),
                log_payload.get("latency_ms"),
                log_payload.get("model_name"),
            ),
        )
        log_id = cursor.fetchone()[0]
        conn.commit()
        return log_id
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

    # Test with in-memory store (no DB connection -> logging is skipped, by design)
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

    # Test log payload builder directly
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

    print(
        "Note: with use_pgvector=False there is no DB connection, so "
        "retrieve_context() above did NOT write to rag_query_logs. "
        "Run against a real pgvector-backed VectorStore to see automatic logging."
    )