"""
Embedder - Turns text into numbers (embeddings) for RAG

Uses sentence-transformers to convert text chunks into vectors.
Similar texts end up with similar vectors, which lets us find related content.
"""

from typing import List, Union
import os
import hashlib
import numpy as np


def _deterministic_vector_for_text(text: str, dim: int = 384) -> np.ndarray:
    """Create a deterministic embedding for a text using hashed RNG.

    This is used for CI to make embeddings stable and fast without external
    models. It is intentionally simple and reproducible.
    """
    if text is None:
        text = ""
    # Use SHA256 to derive a seed
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "big") & 0xFFFFFFFF
    rng = np.random.RandomState(seed)
    vec = rng.randn(dim).astype(np.float32)
    # Normalize to unit length for cosine similarity compatibility
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


class Embedder:
    """Manages embedding generation using sentence-transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", mode: str = None):
        """
        Initialize the embedder with a model.
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.mode = mode or os.getenv("EMBEDDING_MODE", "semantic")
        self.model = None
        if self.mode == "semantic":
            self.model = self._load_model()
        # Default embedding dimension; overwritten if semantic model provides one
        self.embedding_dimension = 384 if self.mode == "deterministic" else self._get_embedding_dimension()

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

        if self.mode == "deterministic":
            dim = self.get_embedding_dimension()
            embs = np.stack([_deterministic_vector_for_text(t, dim) for t in texts], axis=0)
            return embs

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
        if self.mode == "deterministic":
            return _deterministic_vector_for_text(query, dim=self.get_embedding_dimension())
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
