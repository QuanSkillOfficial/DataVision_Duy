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
    Supports chunk-id deduplication (upsert) on repeated add_chunks calls.
    """

    def __init__(self, use_pgvector: bool = False):
        """
        Initialize fake vector store.

        Args:
            use_pgvector: Ignored, always uses in-memory storage
        """
        self.use_pgvector = False
        self.connection = None
        self._chunk_by_id = {}
        self._chunk_index = []

    @property
    def in_memory_store(self):
        """Dict-like interface compatible with real VectorStore.in_memory_store."""
        return self._chunk_by_id

    @property
    def chunks(self):
        return [self._chunk_by_id[cid]["chunk"] for cid in self._chunk_index]

    @property
    def embeddings(self):
        if not self._chunk_index:
            return np.zeros((0, 384))
        return np.vstack([self._chunk_by_id[cid]["embedding"] for cid in self._chunk_index])

    def add_chunks(self, chunks: List[dict], embeddings: np.ndarray) -> List[str]:
        """
        Add chunks and embeddings to the store (upsert on chunk_id).

        Args:
            chunks: List of chunk dictionaries
            embeddings: NumPy array of embeddings

        Returns:
            List of chunk IDs stored
        """
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")
        stored_ids = []
        for i, chunk in enumerate(chunks):
            cid = chunk.get("chunk_id") or f"fake_chunk_{len(self._chunk_index) + i}"
            if cid not in self._chunk_by_id:
                self._chunk_index.append(cid)
            self._chunk_by_id[cid] = {
                "chunk": chunk,
                "embedding": np.asarray(embeddings[i]).reshape(-1),
            }
            stored_ids.append(cid)
        return stored_ids

    def search(self, query_embedding: np.ndarray, top_k: int = 5,
               filter_metadata: dict = None) -> List[dict]:
        """
        Search for similar chunks using cosine similarity.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of chunk dictionaries with similarity scores and contract fields.
        """
        if not self._chunk_index:
            return []

        from sklearn.metrics.pairwise import cosine_similarity
        emb_matrix = np.vstack([self._chunk_by_id[cid]["embedding"] for cid in self._chunk_index])
        similarities = cosine_similarity([query_embedding], emb_matrix)[0]

        filtered_indices = []
        for i, cid in enumerate(self._chunk_index):
            chunk = self._chunk_by_id[cid]["chunk"]
            matches = True
            if filter_metadata:
                for key, value in filter_metadata.items():
                    if key == "document_id":
                        if chunk.get("document_id") != value:
                            matches = False
                            break
                    elif key == "page_number":
                        page = chunk.get("page_number") or chunk.get("metadata", {}).get("page_number")
                        if page != value:
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
        sorted_indices = np.argsort(filtered_similarities)[::-1][:top_k]

        results = []
        for idx in sorted_indices:
            original_idx = filtered_indices[idx]
            cid = self._chunk_index[original_idx]
            chunk = self._chunk_by_id[cid]["chunk"].copy()
            metadata = chunk.get("metadata", {}) or {}
            score = float(filtered_similarities[idx])
            normalized_score = max(0.0, min(1.0, (score + 1.0) / 2.0))

            page_number = (
                chunk.get("page_number")
                or metadata.get("page_number")
            )
            file_name = (
                chunk.get("file_name")
                or metadata.get("file_name")
                or metadata.get("source")
            )
            document_external_id = (
                chunk.get("document_external_id")
                or metadata.get("document_external_id")
            )
            document_db_id = chunk.get("document_db_id") or chunk.get("document_id_fk")

            chunk["score"] = normalized_score
            chunk["similarity_score"] = normalized_score
            chunk["page_number"] = page_number
            chunk["file_name"] = file_name
            chunk["text"] = chunk.get("chunk_text") or chunk.get("text", "")
            chunk["chunk_text"] = chunk.get("chunk_text") or chunk.get("text", "")
            if document_external_id is not None:
                chunk["document_external_id"] = document_external_id
            if document_db_id is not None:
                chunk["document_db_id"] = document_db_id
            if "id" not in chunk:
                chunk["id"] = cid
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
