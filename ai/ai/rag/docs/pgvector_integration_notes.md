# pgvector Integration Notes

**Status**: Week 3 - Ready for Production

## Overview

The RAG system now supports pgvector as a persistent backend for production use. In-memory storage remains available for development/testing.

## Architecture

```
Chunks (with IDs) → Embeddings → pgvector (PostgreSQL)
                                 ↓
                            Similarity Search
                                 ↓
                            Retrieved Chunks
```

## Setup

### 1. PostgreSQL Installation

Ensure PostgreSQL 13+ with pgvector extension:

```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu
sudo apt-get install postgresql postgresql-contrib

# Or use Docker
docker run --name pgvector -e POSTGRES_PASSWORD=password -p 5432:5432 pgvector/pgvector:latest
```

### 2. Enable pgvector Extension

```bash
psql -U postgres -d your_database -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Set Connection String

Environment variable or direct parameter:

```python
# Via environment
import os
os.environ['DATABASE_URL'] = 'postgresql://user:password@localhost:5432/rag_db'

# Via code
from rag.vector_store import VectorStore

store = VectorStore(
    use_pgvector=True,
    connection_string='postgresql://user:password@localhost:5432/rag_db'
)
```

## Table Schema

Created automatically by `VectorStore._create_table()`:

```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(255) UNIQUE NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(384),
    page_number INTEGER,
    metadata JSONB,
    start_char INTEGER,
    end_char INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunk_id ON document_chunks (chunk_id);
CREATE INDEX idx_document_id ON document_chunks (document_id);
CREATE INDEX idx_page_number ON document_chunks (page_number);
CREATE INDEX idx_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

**Fields:**
- `chunk_id`: Unique identifier (from chunker)
- `document_id`: Document reference (for filtering)
- `chunk_text`: Raw text content
- `embedding`: 384-dimensional vector (all-MiniLM-L6-v2)
- `page_number`: Page from source document
- `metadata`: JSON with source, file_name, etc.
- `start_char` / `end_char`: Character offsets
- `created_at`: Insertion timestamp

## Usage

### Adding Chunks

```python
from rag.vector_store import VectorStore
from rag.embedder import load_embedding_model, embed_texts

# Initialize
store = VectorStore(
    use_pgvector=True,
    connection_string='postgresql://user:password@localhost:5432/rag_db'
)

# Prepare chunks
chunks = [
    {
        "chunk_id": "doc_001_page_1_chunk_000",
        "document_id": "doc_001",
        "chunk_text": "Machine learning is...",
        "metadata": {"page_number": 1, "source": "guide.pdf"},
        "start_char": 0,
        "end_char": 50
    },
    # ... more chunks
]

# Generate embeddings
model = load_embedding_model()
texts = [c["chunk_text"] for c in chunks]
embeddings = embed_texts(texts, model)

# Store in pgvector
chunk_ids = store.add_chunks(chunks, embeddings)
print(f"Stored {len(chunk_ids)} chunks")
```

### Searching

```python
from rag.embedder import embed_query

# Query
query = "What is machine learning?"
query_embedding = embed_query(query, model)

# Search
results = store.search(
    query_embedding=query_embedding,
    top_k=5,
    filter_metadata=None  # Or {"document_id": "doc_001"}
)

# Results include:
# - chunk_id
# - document_id
# - chunk_text
# - page_number
# - metadata
# - score (similarity 0-1)
```

### Filtered Search

```python
# Search within specific document
results = store.search(
    query_embedding,
    top_k=5,
    filter_metadata={"document_id": "doc_001"}
)

# Search within specific page
results = store.search(
    query_embedding,
    top_k=5,
    filter_metadata={"page_number": 1}
)

# Combined filters
results = store.search(
    query_embedding,
    top_k=5,
    filter_metadata={
        "document_id": "doc_001",
        "page_number": 1
    }
)
```

## Query Performance

The pgvector queries use the `<=>` operator (cosine distance):

```sql
SELECT 
    chunk_id,
    document_id,
    chunk_text,
    page_number,
    metadata,
    1 - (embedding <=> query_vector::vector) AS similarity_score
FROM document_chunks
WHERE document_id = 'doc_001'  -- Optional filtering
ORDER BY embedding <=> query_vector::vector
LIMIT 5;
```

**Performance:**
- Index: `USING ivfflat` for approximate nearest neighbor search
- Typical query time: 10-50ms for 10k+ chunks
- Can be tuned with `lists` parameter for recall/speed tradeoff

## Backup & Management

### Backup

```bash
# Backup the entire database
pg_dump -U user -d rag_db > rag_db_backup.sql

# Restore
psql -U user -d rag_db < rag_db_backup.sql
```

### Clear All Chunks

```python
# SQL
store.connection.cursor().execute("TRUNCATE document_chunks")
store.connection.commit()

# Or Python
store.clear()
```

### Delete Specific Document

```sql
DELETE FROM document_chunks WHERE document_id = 'doc_001';
```

## Monitoring

### Row Count

```sql
SELECT COUNT(*) as total_chunks FROM document_chunks;
SELECT document_id, COUNT(*) as chunk_count FROM document_chunks GROUP BY document_id;
```

### Index Stats

```sql
SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes WHERE tablename='document_chunks';
```

### Embedding Distribution

```sql
-- Find chunks with low similarity scores
SELECT chunk_id, COUNT(*) as low_score_matches 
FROM document_chunks d1
CROSS JOIN document_chunks d2
WHERE d1.id < d2.id 
  AND (d1.embedding <=> d2.embedding) > 0.9
GROUP BY d1.chunk_id;
```

## Integration with RAG Pipeline

### Full Pipeline

```python
from rag.rag_pipeline import RAGPipeline
from rag.vector_store import VectorStore

# Initialize with pgvector
vector_store = VectorStore(
    use_pgvector=True,
    connection_string='postgresql://...'
)

pipeline = RAGPipeline(vector_store=vector_store)

# Ingest
pipeline.ingest_document(text, document_id="doc_001")

# Query
results = pipeline.query("What is machine learning?")
```

### Switching Backends

Same code works for both in-memory and pgvector:

```python
# Development (in-memory)
store = VectorStore(use_pgvector=False)

# Production (pgvector)
store = VectorStore(use_pgvector=True, connection_string=...)
```

## Limitations & Notes

1. **Embedding Dimension**: Fixed at 384 (all-MiniLM-L6-v2)
2. **Batch Size**: No hard limit, but recommend batches of 1000 chunks for stability
3. **Metadata Filtering**: Currently supports exact match only (no range queries)
4. **Similarity Score**: Returns 1 - distance (0 = dissimilar, 1 = identical)

## Troubleshooting

### Connection Error
```
psycopg2.OperationalError: connection failed
```
- Check PostgreSQL is running: `pg_isready`
- Verify connection string credentials
- Check firewall if remote host

### Extension Not Found
```
ERROR: extension "vector" does not exist
```
- Install pgvector: Follow setup section
- Run: `CREATE EXTENSION vector;`

### Query Timeout
```
QueryTimeoutError: Query timed out
```
- Increase timeout in connection string
- Check index status: `REINDEX INDEX idx_embedding;`
- Consider reducing `lists` parameter in IVFFlat index

### Similarity Score Out of Range
- Verify embeddings are normalized (norm = 1)
- Check embedding dimension matches table (384)

## Week 3 Checklist

- [x] VectorStore pgvector backend implemented
- [x] Chunk ID preservation working
- [x] Filtering by document_id, page_number
- [x] Proper SQL with cosine similarity
- [x] Table schema with proper indexes
- [x] Integration with RAG pipeline
- [ ] Production deployment and testing
- [ ] Performance benchmarks

## Next Steps (Week 4+)

1. Performance tuning for large datasets
2. Batch insert optimization
3. Similarity score confidence levels
4. Advanced metadata filtering (range, contains, regex)
5. Multi-tenant support (org-level partitioning)
