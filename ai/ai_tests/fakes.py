"""
Fake implementations for CI-safe testing

Provides fake implementations that don't require external dependencies
like sentence-transformers, making tests fast and CI-safe.
"""

import numpy as np
from typing import List, Union


class FakeEmbedder:
    """
    Fake embedder for CI-safe testing.

    Returns deterministic fake embeddings without requiring
    sentence-transformers download or model loading.
    """

    def __init__(self, model_name: str = "fake-model", embedding_dimension: int = 384):
        """
        Initialize fake embedder.

        Args:
            model_name: Ignored, for API compatibility
            embedding_dimension: Dimension of fake embeddings (default: 384)
        """
        self.model_name = model_name
        self.embedding_dimension = embedding_dimension
        self._seed = 42  # For deterministic embeddings

    def _get_embedding_dimension(self) -> int:
        """Return the embedding dimension."""
        return self.embedding_dimension

    def _load_model(self):
        """No-op for fake embedder."""
        return self

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate fake embeddings for text(s).

        Args:
            texts: Single text string or list of text strings

        Returns:
            NumPy array of fake embeddings (shape: [n_texts, embedding_dim])
        """
        if isinstance(texts, str):
            texts = [texts]

        # Generate deterministic embeddings based on text content
        embeddings = []
        for i, text in enumerate(texts):
            # Use text hash + index for deterministic but varied embeddings
            text_hash = hash(text) % 1000
            base_embedding = np.ones(self.embedding_dimension) * 0.1
            base_embedding[:10] = (text_hash + i) / 1000.0
            embeddings.append(base_embedding)

        return np.array(embeddings)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate fake embedding for a query.

        Args:
            query: User query string

        Returns:
            NumPy array of fake embedding (shape: [embedding_dim])
        """
        # Use query hash for deterministic embedding
        query_hash = hash(query) % 1000
        embedding = np.ones(self.embedding_dimension) * 0.1
        embedding[:10] = query_hash / 1000.0
        return embedding

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        return self.embedding_dimension


class FakeVectorStore:
    """
    Fake vector store for CI-safe testing.

    Provides in-memory vector storage without requiring database connection.
    """

    def __init__(self, use_pgvector: bool = False):
        """
        Initialize fake vector store.

        Args:
            use_pgvector: Ignored, always uses in-memory storage
        """
        self.use_pgvector = False
        self.chunks = []
        self.embeddings = []

    def add_chunks(self, chunks: List[dict], embeddings: np.ndarray):
        """
        Add chunks and embeddings to the store.

        Args:
            chunks: List of chunk dictionaries
            embeddings: NumPy array of embeddings
        """
        self.chunks.extend(chunks)
        if len(self.embeddings) == 0:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])

    def search(self, query_embedding: np.ndarray, top_k: int = 5,
               filter_metadata: dict = None) -> List[dict]:
        """
        Search for similar chunks using cosine similarity.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"document_id": "doc1", "page_number": 1})

        Returns:
            List of chunk dictionaries with similarity scores
        """
        if len(self.embeddings) == 0:
            return []

        # Calculate cosine similarity with NumPy so the CI fake stays small and
        # does not pull the prediction module's scikit-learn dependency.
        query_vector = np.asarray(query_embedding, dtype=float).reshape(-1)
        embedding_matrix = np.asarray(self.embeddings, dtype=float)
        denominator = np.linalg.norm(embedding_matrix, axis=1) * np.linalg.norm(query_vector)
        denominator = np.where(denominator == 0, 1.0, denominator)
        similarities = embedding_matrix @ query_vector / denominator

        # Apply filters
        filtered_indices = []
        for i, chunk in enumerate(self.chunks):
            matches = True
            if filter_metadata:
                for key, value in filter_metadata.items():
                    if key == "document_id":
                        if chunk.get("document_id") != value:
                            matches = False
                            break
                    elif key == "page_number":
                        if chunk.get("metadata", {}).get("page_number") != value:
                            matches = False
                            break
                    else:
                        if chunk.get(key) != value and chunk.get("metadata", {}).get(key) != value:
                            matches = False
                            break
            if matches:
                filtered_indices.append(i)

        if not filtered_indices:
            return []

        filtered_similarities = similarities[filtered_indices]
        filtered_chunks = [self.chunks[i] for i in filtered_indices]

        # Sort by similarity and take top_k
        sorted_indices = np.argsort(filtered_similarities)[::-1][:top_k]

        results = []
        for idx in sorted_indices:
            chunk = filtered_chunks[idx].copy()
            chunk["score"] = float(filtered_similarities[idx])
            chunk["similarity_score"] = float(filtered_similarities[idx])
            # Add page_number as top-level field like real VectorStore
            chunk["page_number"] = chunk.get("metadata", {}).get("page_number")
            results.append(chunk)

        return results


class FakeDatabaseConnection:
    """
    Fake database connection for CI-safe testing.

    Provides a mock connection interface without requiring real database.
    """

    def __init__(self):
        """Initialize fake database connection."""
        self.closed = False
        self._data = {
            "documents": [],
            "document_chunks": [],
            "rag_query_logs": []
        }

    def cursor(self):
        """Return a fake cursor."""
        return FakeCursor(self._data)

    def close(self):
        """Close the fake connection."""
        self.closed = True

    def commit(self):
        """No-op commit for fake connection."""
        pass

    def rollback(self):
        """No-op rollback for fake connection."""
        pass


class FakeCursor:
    """
    Fake database cursor for CI-safe testing.
    """

    def __init__(self, data):
        """Initialize fake cursor with data."""
        self._data = data
        self._results = []
        self._rowcount = 0

    def execute(self, query, params=None):
        """
        Execute a fake query.

        For SELECT queries, returns fake data.
        For INSERT queries, increments rowcount.
        """
        if "SELECT" in query.upper():
            # Return fake data for document_id resolution
            if "documents" in query.lower() and "document_external_id" in query.lower():
                self._results = [(1,)]  # Fake document_id = 1
                self._rowcount = 1
            else:
                self._results = []
                self._rowcount = 0
        elif "INSERT" in query.upper():
            self._rowcount = 1
        else:
            self._rowcount = 0

    def fetchone(self):
        """Fetch one row from results."""
        if self._results:
            return self._results.pop(0)
        return None

    def fetchall(self):
        """Fetch all rows from results."""
        results = self._results
        self._results = []
        return results

    @property
    def rowcount(self):
        """Return the number of rows affected."""
        return self._rowcount


def create_sample_chunks(count: int = 5) -> List[dict]:
    """
    Create sample chunk data for testing.

    Args:
        count: Number of sample chunks to create

    Returns:
        List of chunk dictionaries
    """
    chunks = []
    for i in range(count):
        chunks.append({
            "chunk_id": f"doc_001_page_{i}_chunk_000",
            "document_id": "doc_001",
            "chunk_text": f"Sample chunk content {i} for testing purposes.",
            "metadata": {
                "source": "test.pdf",
                "page_number": i + 1
            }
        })
    return chunks


def create_sample_pages(count: int = 3) -> List[dict]:
    """
    Create sample page data for testing.

    Args:
        count: Number of sample pages to create

    Returns:
        List of page dictionaries
    """
    pages = []
    for i in range(count):
        pages.append({
            "document_external_id": "doc_dataflow_technical_report",
            "file_name": "DataFlow_Technical_Report.pdf",
            "page_number": i + 1,
            "text": f"Sample page {i + 1} content for testing the document loader.",
            "char_count": 50,
            "word_count": 10,
            "is_empty": False
        })
    return pages