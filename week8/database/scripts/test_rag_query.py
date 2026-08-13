"""
test_rag_query.py

Runs a real end-to-end RAG query against the pgvector-backed document_chunks
that Lap already loaded, using the fixed RAGService (which now auto-logs
every query into rag_query_logs).

Run this AFTER document_chunks has data (i.e. after
load_document_pages_to_pgvector.py has been run successfully).

Usage:
    python test_rag_query.py --query "What is the DataFlow pipeline?" --document-external-id doc_dataflow_technical_report
"""

import argparse
import json
import os

from embedder import Embedder
from vector_store import VectorStore, resolve_document_db_id
from retriever import Retriever
from rag_service import RAGService


def main():
    parser = argparse.ArgumentParser(description="Run a real RAG query and log it to rag_query_logs")
    parser.add_argument("--query", required=True, help="The natural language question to ask")
    parser.add_argument(
        "--document-external-id",
        default=None,
        help="Optional: restrict the search to one document (Duy's document_external_id)",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--connection-string", default=None)
    args = parser.parse_args()

    # 1. Build the pgvector-backed vector store (this is the SAME connection
    #    the RAGService will reuse for logging).
    vector_store = VectorStore(use_pgvector=True, connection_string=args.connection_string)
    if not getattr(vector_store, "connection", None):
        raise RuntimeError(
            "Could not connect to pgvector. Check POSTGRES_HOST/PORT/USER/PASSWORD/DB "
            "env vars, or pass --connection-string explicitly."
        )

    # 2. Resolve document_external_id -> documents.id (integer), if provided
    document_id = None
    if args.document_external_id:
        document_id = resolve_document_db_id(vector_store.connection, args.document_external_id)
        print(f"Resolved document_external_id={args.document_external_id!r} -> documents.id={document_id}")

    # 3. Build the rest of the RAG stack
    embedder = Embedder()
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=args.top_k)
    service = RAGService(embedder=embedder, vector_store=vector_store, retriever=retriever)

    # 4. Run the query — retrieve_context() will automatically INSERT into
    #    rag_query_logs because vector_store.connection is live.
    response = service.retrieve_context(
        question=args.query,
        document_id=document_id,
        top_k=args.top_k,
    )

    print(json.dumps(response, indent=2, default=str))

    if response.get("metadata", {}).get("log_id"):
        print(f"\nLogged to rag_query_logs with id={response['metadata']['log_id']}")
    else:
        print(
            "\nWarning: no log_id in response metadata — the query was NOT logged. "
            "Check the console output above for a 'Warning: failed to log rag query' message."
        )
    conn = vector_store.connection
    if conn:
        print("\n--- Generating Validation JSON ---")
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM document_chunks;")
        chunks_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM rag_query_logs;")
        logs_count = cur.fetchone()[0]

        cur.execute("SELECT * FROM v_rag_daily_metrics;")
        col_metrics = [desc[0] for desc in cur.description]
        metrics_data = [dict(zip(col_metrics, [str(v) if v is not None else None for v in row])) for row in cur.fetchall()]

        cur.execute("SELECT * FROM v_document_rag_readiness;")
        col_ready = [desc[0] for desc in cur.description]
        readiness_data = [dict(zip(col_ready, [str(v) if v is not None else None for v in row])) for row in cur.fetchall()]

        cur.close()

        output_data = {
            "document_chunks": chunks_count,
            "rag_query_logs": logs_count,
            "v_rag_daily_metrics_is_not_empty": len(metrics_data) > 0,
            "v_rag_daily_metrics_data": metrics_data,
            "v_document_rag_readiness_is_not_empty": len(readiness_data) > 0,
            "v_document_rag_readiness_data": readiness_data
        }

        output_dir = os.path.join("week8", "database", "outputs", "db_validation")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "rag_pgvector_counts.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4)

        print(f"Successfully saved RAG validation counts to: {output_file}")
    else:
        print("\nWarning: No DB connection found to generate validation JSON.")
    # =========================================================


if __name__ == "__main__":
    main()
