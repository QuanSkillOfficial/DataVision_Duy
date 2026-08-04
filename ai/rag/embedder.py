"""
Embedder - Turns text into numbers (embeddings) for RAG

Uses sentence-transformers to convert text chunks into vectors.
Similar texts end up with similar vectors, which lets us find related content.
"""

import hashlib
import os
import re
from typing import List, Union
import numpy as np


class HashEmbedder:
    """Deterministic, dependency-light embedder for CI and staging smoke tests.

    This is intentionally labelled as a hashing embedder. It proves the
    384-dimensional pgvector storage/retrieval path without pretending to be
    a semantic production model or downloading artifacts at runtime.
    """

    def __init__(self, embedding_dimension: int = 384):
        self.embedding_dimension = embedding_dimension
        self.model_name = "datavision-hashing-384-v1"

    def _embed_one(self, text: str) -> np.ndarray:
        vector = np.zeros(self.embedding_dimension, dtype=np.float32)
        tokens = re.findall(r"[a-z0-9_]+", str(text).lower())
        features = tokens + [f"{left}:{right}" for left, right in zip(tokens, tokens[1:])]
        for feature in features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.embedding_dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = float(np.linalg.norm(vector))
        if norm == 0.0:
            vector[0] = 1.0
        else:
            vector /= norm
        return vector

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        return np.vstack([self._embed_one(text) for text in texts])

    def embed_query(self, query: str) -> np.ndarray:
        return self._embed_one(query)

    def get_embedding_dimension(self) -> int:
        return self.embedding_dimension


class Embedder:
    """Manages embedding generation using sentence-transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the embedder with a model.

        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.model = self._load_model()
        self.embedding_dimension = self._get_embedding_dimension()

    def _get_embedding_dimension(self) -> int:
        """Support both older and newer sentence-transformers APIs."""
        getter = getattr(self.model, "get_embedding_dimension", None)
        if callable(getter):
            return int(getter())

        legacy_getter = getattr(self.model, "get_sentence_embedding_dimension", None)
        if callable(legacy_getter):
            return int(legacy_getter())

        return 384

    def _load_model(self):
        """Load the sentence-transformers embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(self.model_name)
            print(f" Loaded embedding model: {self.model_name}")
            return model
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Convert text(s) to embedding vectors.

        Args:
            texts: Single text string or list of text strings

        Returns:
            NumPy array of embeddings (shape: [n_texts, embedding_dim])
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Convert a single query to an embedding vector.

        Args:
            query: User query string

        Returns:
            NumPy array of embedding (shape: [embedding_dim])
        """
        embedding = self.model.encode(query, convert_to_numpy=True)
        return embedding

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        return self.embedding_dimension


# Wrapper functions for functional API
def load_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Embedder:
    """
    Load an embedding model (recommended API).

    Args:
        model_name: HuggingFace model identifier

    Returns:
        Embedder instance ready to use
    """
    return Embedder(model_name=model_name)


def create_embedder(mode: str | None = None):
    """Create the configured embedding implementation.

    ``hash`` is the reproducible Week 8 staging mode. ``sentence-transformers``
    remains available for semantic-quality environments that provision the
    model dependency and artifact explicitly.
    """

    selected = (mode or os.getenv("RAG_EMBEDDING_MODE", "sentence-transformers")).lower()
    if selected in {"hash", "hashing", "ci", "staging"}:
        return HashEmbedder()
    if selected in {"sentence-transformers", "sentence_transformers", "semantic"}:
        return Embedder()
    raise ValueError(f"Unsupported RAG_EMBEDDING_MODE: {selected}")


def embed_texts(texts: List[str], model: Embedder) -> np.ndarray:
    """
    Embed a list of texts using the provided model.

    Args:
        texts: List of text strings to embed
        model: Embedder instance

    Returns:
        NumPy array of embeddings (shape: [n_texts, embedding_dim])
    """
    return model.embed(texts)


def embed_query(query: str, model: Embedder) -> np.ndarray:
    """
    Embed a single query using the provided model.

    Args:
        query: Query string
        model: Embedder instance

    Returns:
        NumPy array of embedding (shape: [embedding_dim])
    """
    return model.embed_query(query)


def get_embedding_dimension(model: Embedder) -> int:
    """
    Get the embedding dimension from the model.

    Args:
        model: Embedder instance

    Returns:
        Integer dimension of embeddings
    """
    return model.get_embedding_dimension()


if __name__ == "__main__":
    # Test the embedding functions
    model = load_embedding_model()

    test_sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is a subset of artificial intelligence.",
        "RAG combines retrieval with generation for better answers."
    ]

    # Test embed_texts
    print("=== Testing embed_texts ===")
    embeddings = embed_texts(test_sentences, model)
    print(f"Shape: {embeddings.shape}")
    print(f"Dimension: {get_embedding_dimension(model)}")

    # Test embed_query
    print("\n=== Testing embed_query ===")
    query = "What is machine learning?"
    query_embedding = embed_query(query, model)
    print(f"Query embedding shape: {query_embedding.shape}")

    # Test similarity
    print("\n=== Testing similarity ===")
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity([query_embedding], embeddings)
    print(f"Similarity scores: {similarities[0]}")
    print(f"Most similar: '{test_sentences[np.argmax(similarities[0])]}'")
