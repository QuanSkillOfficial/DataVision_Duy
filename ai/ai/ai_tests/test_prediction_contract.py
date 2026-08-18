import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).parent.parent.parent))

from ai.rag.retriever import Retriever
from ai.rag.vector_store import VectorStore


class DummyEmbedder:
    def __init__(self):
        self.embedding_dimension = 3

    def embed_query(self, query: str) -> np.ndarray:
        return np.array([1.0, 0.0, 0.0], dtype=float)

    def embed(self, texts):
        return np.array([[1.0, 0.0, 0.0] for _ in texts], dtype=float)


def test_retriever_supports_prediction_metadata_filters():
    vector_store = VectorStore(use_pgvector=False)
    retriever = Retriever(embedder=DummyEmbedder(), vector_store=vector_store, top_k=5)

    chunks = [
        {
            "chunk_id": "contract_chunk",
            "document_id": "doc_001",
            "chunk_text": "Contract text",
            "metadata": {
                "document_type": "contract",
                "status": "accepted",
                "confidence": 0.92,
                "source": "contract.pdf",
            },
        },
        {
            "chunk_id": "resume_chunk",
            "document_id": "doc_002",
            "chunk_text": "Resume text",
            "metadata": {
                "document_type": "resume",
                "status": "needs_review",
                "confidence": 0.41,
                "source": "resume.pdf",
            },
        },
    ]
    embeddings = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=float)
    vector_store.add_chunks(chunks, embeddings)

    results = retriever.retrieve(
        "Find contract details",
        metadata_filter={"document_type": "contract", "status": "accepted"},
    )

    assert len(results) == 1
    assert results[0]["chunk_id"] == "contract_chunk"


def test_retriever_supports_confidence_threshold_filters():
    vector_store = VectorStore(use_pgvector=False)
    retriever = Retriever(embedder=DummyEmbedder(), vector_store=vector_store, top_k=5)

    chunks = [
        {
            "chunk_id": "high_confidence_chunk",
            "document_id": "doc_001",
            "chunk_text": "High confidence text",
            "metadata": {
                "document_type": "report",
                "status": "accepted",
                "confidence": 0.91,
            },
        },
        {
            "chunk_id": "low_confidence_chunk",
            "document_id": "doc_002",
            "chunk_text": "Low confidence text",
            "metadata": {
                "document_type": "report",
                "status": "accepted",
                "confidence": 0.55,
            },
        },
    ]
    embeddings = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=float)
    vector_store.add_chunks(chunks, embeddings)

    results = retriever.retrieve(
        "Find important report details",
        metadata_filter={"confidence": {"operator": "gt", "value": 0.8}},
    )

    assert len(results) == 1
    assert results[0]["chunk_id"] == "high_confidence_chunk"
