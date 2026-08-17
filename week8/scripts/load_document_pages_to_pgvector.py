"""Load Duy document_pages.jsonl into the pgvector-backed document_chunks table."""

import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Optional

try:
    from .document_loader import DocumentLoader
    from .embedder import Embedder
    from .vector_store import VectorStore, resolve_document_db_id
except ImportError:  # pragma: no cover - direct script execution fallback
    from document_loader import DocumentLoader
    from embedder import Embedder
    from vector_store import VectorStore, resolve_document_db_id


def load_and_ingest(
    document_pages_path: str,
    document_external_id: str,
    chunk_size: int = 512,
    overlap: int = 50,
    connection_string: Optional[str] = None,
    prediction_metadata: Optional[Dict] = None,
) -> Dict:
    pages = DocumentLoader.load_document_pages_jsonl(document_pages_path)
    validation = DocumentLoader.validate_pages(pages)
    chunks = DocumentLoader.pages_to_chunks(pages, chunk_size=chunk_size, overlap=overlap)

    embedder = Embedder()
    texts = [chunk["chunk_text"] for chunk in chunks]
    embeddings = embedder.embed(texts)

    vector_store = VectorStore(use_pgvector=True, connection_string=connection_string)
    if not getattr(vector_store, "connection", None):
        raise RuntimeError("Unable to connect to pgvector")

    start_time = time.time()
    for chunk in chunks:
        chunk["document_external_id"] = document_external_id
        chunk.setdefault("metadata", {})
        chunk["metadata"]["document_external_id"] = document_external_id
        if prediction_metadata:
            chunk["metadata"].update(prediction_metadata)

    vector_store.add_chunks(chunks, embeddings)
    insertion_time = time.time() - start_time

    return {
        "pages_loaded": validation["total_pages"],
        "non_empty_pages": validation["non_empty_pages"],
        "empty_pages_skipped": validation["empty_pages"],
        "total_characters": validation["total_characters"],
        "chunks_created": len(chunks),
        "embeddings_generated": len(embeddings),
        "vectors_inserted": len(chunks),
        "insertion_time": round(insertion_time, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Load document_pages.jsonl into pgvector")
    parser.add_argument("--document-pages", required=True)
    parser.add_argument("--document-external-id", required=True)
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=50)
    parser.add_argument("--connection-string", default=None)
    args = parser.parse_args()

    result = load_and_ingest(
        document_pages_path=args.document_pages,
        document_external_id=args.document_external_id,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        connection_string=args.connection_string,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
