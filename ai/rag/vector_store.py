"""
Vector Store - Stores embeddings for fast similarity search

Uses pgvector (PostgreSQL) for production, in-memory for testing.
Embeddings are stored alongside text and metadata for retrieval.
Preserves original chunk IDs and document structure.
"""

import os
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from torch import chunk


def resolve_document_db_id(conn, document_external_id: str) -> int:
    """Resolve a Lap document identifier to the integer documents.id used by Phat."""
    if conn is None:
        raise ValueError("A database connection is required to resolve document_external_id")

    if isinstance(document_external_id, int):
        return document_external_id

    if isinstance(document_external_id, str) and document_external_id.isdigit():
        return int(document_external_id)

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM documents WHERE document_external_id = %s OR id::text = %s LIMIT 1",
            (document_external_id, document_external_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(
                f"No document found for document_external_id={document_external_id!r}"
            )
        return int(row[0])
    finally:
        cursor.close()


class VectorStore:
    """Stores and retrieves embeddings - pgvector for prod, in-memory for testing."""
    
    def __init__(self, use_pgvector: bool = False, connection_string: Optional[str] = None):
        self.use_pgvector = use_pgvector
        self.connection_string = connection_string
        self.connection = None
        self.in_memory_store = {}  # chunk_id -> chunk_data
        
        if use_pgvector:
            self._connect_pgvector()
    
    def _connect_pgvector(self):
        """Connect to PostgreSQL with pgvector and validate the existing schema."""
        try:
            import psycopg2

            connection_string = (
                self.connection_string
                or os.getenv("DATABASE_URL")
                or os.getenv("POSTGRES_URL")
            )
            if not connection_string:
                raise ValueError("No database connection string provided. Set connection_string or DATABASE_URL.")

            self.connection = psycopg2.connect(connection_string)
            print("Connected to PostgreSQL with pgvector")
            self._validate_existing_schema()
        except ImportError:
            print("Need psycopg2 - run: pip install psycopg2-binary")
            self.use_pgvector = False
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            self.use_pgvector = False
    
    def _metadata_matches_filter(self, chunk_data: Dict, filter_metadata: Optional[Dict]) -> bool:
        """Check whether chunk data satisfies a metadata filter structure."""
        if not filter_metadata:
            return True

        metadata = chunk_data.get("metadata", {}) or {}
        for key, expected in filter_metadata.items():
            if key in {"document_id", "page_number"}:
                continue

            value = chunk_data.get(key, metadata.get(key))
            if isinstance(expected, dict):
                operator = expected.get("operator", "eq")
                threshold = expected.get("value")
                if operator in {"gt", "gte", "lt", "lte"}:
                    try:
                        numeric_value = float(value)
                        numeric_threshold = float(threshold)
                    except (TypeError, ValueError):
                        return False

                    if operator == "gt":
                        match = numeric_value > numeric_threshold
                    elif operator == "gte":
                        match = numeric_value >= numeric_threshold
                    elif operator == "lt":
                        match = numeric_value < numeric_threshold
                    else:
                        match = numeric_value <= numeric_threshold
                elif operator == "ne":
                    match = value != threshold
                else:
                    match = value == threshold
            else:
                match = value == expected

            if not match:
                return False

        return True

    def _build_pgvector_filter_clause(self, filter_metadata: Optional[Dict]) -> Tuple[str, List[Any]]:
        """Translate metadata filters into a pgvector WHERE clause."""
        if not filter_metadata:
            return "", []

        terms: List[str] = []
        params: List[Any] = []

        for key, expected in filter_metadata.items():
            if key == "document_id":
                terms.append("document_id = %s")
                params.append(expected)
            elif key == "page_number":
                terms.append("page_number = %s")
                params.append(expected)
            elif isinstance(expected, dict):
                operator = expected.get("operator", "eq")
                threshold = expected.get("value")
                if operator in {"gt", "gte", "lt", "lte"}:
                    comparison = {
                        "gt": ">",
                        "gte": ">=",
                        "lt": "<",
                        "lte": "<=",
                    }[operator]
                    terms.append(f"COALESCE((chunk_metadata->>%s)::float, 0.0) {comparison} %s")
                    params.extend([key, threshold])
                elif operator == "ne":
                    terms.append("chunk_metadata->>%s <> %s")
                    params.extend([key, str(threshold)])
                else:
                    terms.append("chunk_metadata->>%s = %s")
                    params.extend([key, str(threshold)])
            else:
                terms.append("chunk_metadata->>%s = %s")
                params.extend([key, str(expected)])

        return " AND ".join(terms), params

    def _validate_existing_schema(self):
        """Validate that the production schema already exists and is usable."""
        if not self.connection:
            return

        try:
            cursor = self.connection.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cursor.execute("""
                SELECT to_regclass('public.document_chunks')
            """)
            table_exists = cursor.fetchone()[0]
            if not table_exists:
                raise RuntimeError("Expected existing public.document_chunks table; schema v4 table was not found")

            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'document_chunks'
            """)
            columns = {row[0] for row in cursor.fetchall()}
            required_columns = {"chunk_id", "document_id", "chunk_text", "embedding"}
            missing_columns = required_columns - columns
            if missing_columns:
                raise RuntimeError(f"document_chunks is missing required columns: {sorted(missing_columns)}")
            if "chunk_metadata" not in columns:
                raise RuntimeError("document_chunks is missing the chunk_metadata column required for citation metadata")

            self.connection.commit()
            print("Validated existing document_chunks schema for pgvector inserts")
        except Exception as e:
            print(f"Schema validation failed: {e}")
            self.connection.rollback()
            self.use_pgvector = False
    
    def add_chunks(
        self,
        chunks: List[Dict],
        embeddings: np.ndarray
    ) -> List[str]:
        """
        Store chunks with their embeddings (preserves chunk IDs).
        
        Args:
            chunks: List of chunk dicts with chunk_id, document_id, chunk_text, metadata, etc.
            embeddings: NumPy array of embeddings (one per chunk)
        
        Returns:
            List of chunk IDs that were stored
        """
        if self.use_pgvector and self.connection:
            return self._add_chunks_pgvector(chunks, embeddings)
        else:
            return self._add_chunks_in_memory(chunks, embeddings)
    
    def _add_chunks_pgvector(self, chunks: List[Dict], embeddings: np.ndarray) -> List[str]:
        """Add chunks to pgvector aligned with Phat's schema_v3 (Week 5)."""
        if not self.connection:
            raise RuntimeError("Not connected to pgvector")

        import json
        try:
            cursor = self.connection.cursor()
            chunk_ids = []

            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'document_chunks'")
            available_columns = {row[0] for row in cursor.fetchall()}

            for chunk, embedding in zip(chunks, embeddings):
                chunk_id = chunk["chunk_id"]
                document_id = chunk.get("document_id_fk")
                if document_id is None and chunk.get("document_external_id"):
                    document_id = resolve_document_db_id(self.connection, chunk["document_external_id"])
                elif document_id is None:
                    document_id = chunk.get("document_id")
                if document_id is not None and not isinstance(document_id, int):
                    try:
                        document_id = int(document_id)
                    except (TypeError, ValueError):
                        document_id = None
                chunk_text = chunk["chunk_text"]
                chunk_metadata = json.dumps(chunk.get("metadata", {}))
                page_number = chunk.get("metadata", {}).get("page_number")
                start_char = chunk.get("start_char")
                end_char = chunk.get("end_char")

                embedding_array = np.asarray(embedding).reshape(-1)
                embedding_str = str(embedding_array.tolist())

                insert_columns = ["chunk_id", "document_id", "chunk_text", "embedding"]
                insert_values = [chunk_id, document_id, chunk_text, embedding_str]

                if "page_number" in available_columns:
                    insert_columns.append("page_number")
                    insert_values.append(page_number)
                if "chunk_index" in available_columns:
                    insert_columns.append("chunk_index")
                    insert_values.append(chunk.get("chunk_index"))
                if "chunk_metadata" in available_columns:
                    insert_columns.append("chunk_metadata")
                    insert_values.append(chunk_metadata)
                if "start_char" in available_columns:
                    insert_columns.append("start_char")
                    insert_values.append(start_char)
                if "end_char" in available_columns:
                    insert_columns.append("end_char")
                    insert_values.append(end_char)

                insert_sql = "INSERT INTO document_chunks ({columns}) VALUES ({placeholders})".format(
                    columns=", ".join(insert_columns),
                    placeholders=", ".join(["%s"] * len(insert_columns)),
                )
                on_conflict_clause = " ON CONFLICT (chunk_id) DO UPDATE SET embedding = EXCLUDED.embedding, chunk_text = EXCLUDED.chunk_text"
                if "chunk_metadata" in available_columns:
                    on_conflict_clause += ", chunk_metadata = EXCLUDED.chunk_metadata"
                if "page_number" in available_columns:
                    on_conflict_clause += ", page_number = EXCLUDED.page_number"
                if "chunk_index" in available_columns:
                    on_conflict_clause += ", chunk_index = EXCLUDED.chunk_index"
                cursor.execute(insert_sql + on_conflict_clause, insert_values)

                chunk_ids.append(chunk_id)
            
            self.connection.commit()
            print(f" Added {len(chunk_ids)} chunks to pgvector")
            return chunk_ids
            
        except Exception as e:
            print(f"Error adding chunks to pgvector: {e}")
            self.connection.rollback()
            raise
    
    def _add_chunks_in_memory(self, chunks: List[Dict], embeddings: np.ndarray) -> List[str]:
        """Add chunks to in-memory store while preserving chunk IDs, upserting duplicates."""
        chunk_ids = []

        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = chunk["chunk_id"]
            document_external_id = (
                chunk.get("document_external_id")
                or chunk.get("metadata", {}).get("document_external_id")
            )
            document_db_id = chunk.get("document_id_fk") or chunk.get("document_db_id")
            file_name = (
                chunk.get("file_name")
                or chunk.get("metadata", {}).get("file_name")
                or chunk.get("metadata", {}).get("source")
            )

            self.in_memory_store[chunk_id] = {
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "document_db_id": document_db_id,
                "document_external_id": document_external_id,
                "file_name": file_name,
                "chunk_text": chunk["chunk_text"],
                "embedding": embedding,
                "metadata": chunk.get("metadata", {}),
                "start_char": chunk.get("start_char"),
                "end_char": chunk.get("end_char"),
                "chunk_index": chunk.get("chunk_index", 0),
            }

            chunk_ids.append(chunk_id)

        return chunk_ids
    
    def add_embeddings(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        metadata: Optional[List[Dict]] = None
    ) -> List[str]:
        """
        DEPRECATED: Use add_chunks() instead. 
        Store embeddings with their text and metadata (legacy API).
        """
        import warnings
        warnings.warn(
            "add_embeddings() is deprecated. Use add_chunks() with full chunk dicts instead.",
            DeprecationWarning
        )
        
        chunks = []
        for i, text in enumerate(texts):
            chunk = {
                "chunk_id": f"legacy_doc_{i}",
                "document_id": f"legacy_doc",
                "chunk_text": text,
                "metadata": metadata[i] if metadata else {},
                "start_char": 0,
                "end_char": len(text),
                "chunk_index": i
            }
            chunks.append(chunk)
        
        return self.add_chunks(chunks, embeddings)
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Find similar embeddings using cosine similarity."""
        if self.use_pgvector and self.connection:
            return self._search_pgvector(query_embedding, top_k, filter_metadata)
        else:
            return self._search_in_memory(query_embedding, top_k, filter_metadata)
    
    def _search_pgvector(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        filter_metadata: Optional[Dict]
    ) -> List[Dict]:
        """Search pgvector for similar embeddings (Week 3)."""
        if not self.connection:
            raise RuntimeError("Not connected to pgvector")

        try:
            cursor = self.connection.cursor()
            embedding_str = str(query_embedding.tolist())

            where_clause = "WHERE 1=1"
            params = [embedding_str]

            if filter_metadata:
                filter_clause, filter_params = self._build_pgvector_filter_clause(filter_metadata)
                if filter_clause:
                    where_clause += f" AND {filter_clause}"
                    params.extend(filter_params)

            query = f"""
                SELECT
                    chunk_id,
                    document_id,
                    page_number,
                    chunk_text,
                    chunk_metadata,
                    1 - (embedding <=> %s::vector) AS similarity_score
                FROM document_chunks
                {where_clause}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """

            params.extend([embedding_str, top_k])
            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                import json
                similarity = float(row[5])
                normalized_similarity = max(0.0, min(1.0, (similarity + 1.0) / 2.0))
                metadata = json.loads(row[4]) if isinstance(row[4], str) else (row[4] or {})
                file_name = (
                    metadata.get("file_name")
                    or metadata.get("source")
                )
                document_external_id = metadata.get("document_external_id")
                document_db_id = row[1]
                results.append({
                    "chunk_id": row[0],
                    "document_id": row[1],
                    "document_db_id": document_db_id,
                    "document_external_id": document_external_id,
                    "file_name": file_name,
                    "text": row[3],
                    "chunk_text": row[3],
                    "page_number": row[2],
                    "metadata": metadata,
                    "score": normalized_similarity,
                    "similarity_score": normalized_similarity,
                })

            return results

        except Exception as e:
            print(f"Error searching pgvector: {e}")
            raise
    
    def _search_in_memory(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        filter_metadata: Optional[Dict]
    ) -> List[Dict]:
        """Search in-memory store with cosine similarity."""
        from sklearn.metrics.pairwise import cosine_similarity

        results = []
        query_embedding = query_embedding.reshape(1, -1)

        for chunk_id, chunk_data in self.in_memory_store.items():
            if filter_metadata:
                if "document_id" in filter_metadata:
                    if chunk_data.get("document_id") != filter_metadata["document_id"]:
                        continue
                if "page_number" in filter_metadata:
                    page = chunk_data.get("metadata", {}).get("page_number")
                    if page != filter_metadata["page_number"]:
                        continue
                if not self._metadata_matches_filter(chunk_data, filter_metadata):
                    continue

            embedding = chunk_data["embedding"].reshape(1, -1)
            similarity = cosine_similarity(query_embedding, embedding)[0][0]
            normalized_similarity = max(0.0, min(1.0, (float(similarity) + 1.0) / 2.0))

            metadata = chunk_data.get("metadata", {}) or {}
            page_number = (
                chunk_data.get("page_number")
                or metadata.get("page_number")
            )
            file_name = (
                chunk_data.get("file_name")
                or metadata.get("file_name")
                or metadata.get("source")
            )
            document_external_id = (
                chunk_data.get("document_external_id")
                or metadata.get("document_external_id")
            )
            document_db_id = chunk_data.get("document_db_id")
            results.append({
                "chunk_id": chunk_data["chunk_id"],
                "document_id": chunk_data["document_id"],
                "document_db_id": document_db_id,
                "document_external_id": document_external_id,
                "file_name": file_name,
                "id": chunk_id,
                "text": chunk_data["chunk_text"],
                "chunk_text": chunk_data["chunk_text"],
                "page_number": page_number,
                "metadata": metadata,
                "score": normalized_similarity,
                "similarity_score": normalized_similarity,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def delete(self, chunk_ids: List[str]) -> bool:
        """Remove chunks by their IDs."""
        if self.use_pgvector and self.connection:
            return self._delete_chunks_pgvector(chunk_ids)

        for chunk_id in chunk_ids:
            if chunk_id in self.in_memory_store:
                del self.in_memory_store[chunk_id]
        return True

    def _delete_chunks_pgvector(self, chunk_ids: List[str]) -> bool:
        """Delete chunks from the pgvector-backed table by their chunk_ids."""
        if not self.connection:
            raise RuntimeError("Not connected to pgvector")

        if not chunk_ids:
            return True

        try:
            cursor = self.connection.cursor()
            # Build placeholder list safely
            placeholders = ", ".join(["%s"] * len(chunk_ids))
            sql = f"DELETE FROM document_chunks WHERE chunk_id IN ({placeholders})"
            cursor.execute(sql, chunk_ids)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error deleting chunks from pgvector: {e}")
            self.connection.rollback()
            return False

    def get_chunk_ids_for_document(self, document_db_id: int) -> List[str]:
        """Return a list of chunk_ids currently stored for a given document id."""
        if self.use_pgvector and self.connection:
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT chunk_id FROM document_chunks WHERE document_id = %s", (document_db_id,))
                ids = [row[0] for row in cursor.fetchall()]
                cursor.close()
                return ids
            except Exception as e:
                print(f"Error fetching chunk ids for document {document_db_id}: {e}")
                return []

        # In-memory store fallback
        return [c["chunk_id"] for c in self.in_memory_store.values() if c.get("document_id") == document_db_id]
    
    def clear(self) -> bool:
        """Wipe all embeddings from the store."""
        self.in_memory_store.clear()
        return True
    
    def get_chunk(self, chunk_id: str) -> Optional[Dict]:
        """Retrieve a chunk by its ID."""
        return self.in_memory_store.get(chunk_id)
    
    def get_all_chunks_for_document(self, document_id: str) -> List[Dict]:
        """Get all chunks for a specific document."""
        return [
            chunk for chunk in self.in_memory_store.values()
            if chunk["document_id"] == document_id
        ]


if __name__ == "__main__":
    # Test the vector store
    print("=== Testing VectorStore ===\n")
    
    # Create in-memory store
    vector_store = VectorStore(use_pgvector=False)
    
    # Create sample chunks
    chunks = [
        {
            "chunk_id": "doc_001_chunk_000",
            "document_id": "doc_001",
            "chunk_text": "Machine learning is a subset of artificial intelligence.",
            "metadata": {"source": "ai_guide.pdf", "page_number": 1},
            "start_char": 0,
            "end_char": 57
        },
        {
            "chunk_id": "doc_001_chunk_001",
            "document_id": "doc_001",
            "chunk_text": "Deep learning uses neural networks with multiple layers.",
            "metadata": {"source": "ai_guide.pdf", "page_number": 2},
            "start_char": 58,
            "end_char": 113
        },
        {
            "chunk_id": "doc_001_chunk_002",
            "document_id": "doc_001",
            "chunk_text": "Natural language processing handles human language understanding.",
            "metadata": {"source": "ai_guide.pdf", "page_number": 2},
            "start_char": 114,
            "end_char": 177
        }
    ]
    
    # Create dummy embeddings
    embeddings = np.random.rand(3, 384)
    
    # Add chunks (preserves chunk IDs!)
    print("Adding chunks...")
    added_ids = vector_store.add_chunks(chunks, embeddings)
    print(f" Added {len(added_ids)} chunks")
    print(f"  Chunk IDs: {added_ids}\n")
    
    # Search
    print("Searching...")
    query_embedding = np.random.rand(384)
    results = vector_store.search(query_embedding, top_k=2)
    print(f" Found {len(results)} results:")
    for result in results:
        print(f"  - {result['chunk_id']}: score={result['score']:.4f}")
        print(f"    Document: {result['document_id']}")
        print(f"    Page: {result.get('metadata', {}).get('page_number')}\n")
    
    # Test metadata filtering
    print("Searching with document_id filter...")
    filtered_results = vector_store.search(
        query_embedding,
        top_k=5,
        filter_metadata={"document_id": "doc_001"}
    )
    print(f" Found {len(filtered_results)} results for doc_001\n")
