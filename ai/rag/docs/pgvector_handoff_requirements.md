# pgvector Handoff Requirements

## Overview

This document specifies the PostgreSQL/pgvector requirements from the AI team to @Lý Tấn Phát for Week 3 integration. The AI team needs a vector database to store document chunks and their embeddings for scalable semantic search.

## Database Schema Requirements

### Table: document_chunks

The AI team requires a table to store document chunks with their embeddings:

```sql
CREATE TABLE document_chunks (
    chunk_id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(384),
    page_number INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Column Specifications

| Column | Type | Description | Required |
|--------|------|-------------|----------|
| `chunk_id` | VARCHAR(255) | Unique identifier for each chunk (format: `{document_id}_chunk_{number}`) | Yes |
| `document_id` | VARCHAR(255) | Identifier for the source document | Yes |
| `chunk_text` | TEXT | The actual text content of the chunk | Yes |
| `embedding` | vector(384) | 384-dimensional embedding vector from all-MiniLM-L6-v2 | Yes |
| `page_number` | INTEGER | Page number in source document (if applicable) | No |
| `metadata` | JSONB | Additional metadata (source, author, section, etc.) | No |
| `created_at` | TIMESTAMP | Timestamp when chunk was created | Yes |

### Index Requirements

For efficient similarity search, the AI team needs:

```sql
-- Create HNSW index for fast approximate nearest neighbor search
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Optional: Index on document_id for filtering
CREATE INDEX ON document_chunks (document_id);

-- Optional: GIN index on metadata for JSONB queries
CREATE INDEX ON document_chunks USING gin (metadata);
```

## Query Requirements

### Similarity Search Query

The AI team expects to run the following query to retrieve top-k similar chunks:

```sql
SELECT 
    chunk_id,
    document_id,
    chunk_text,
    metadata,
    embedding <=> '[query_embedding]' AS distance
FROM document_chunks
ORDER BY distance
LIMIT 5;
```

**Notes**:
- `[query_embedding]` will be replaced with the actual 384-dimensional vector array
- `<=>` is the cosine distance operator (lower distance = higher similarity)
- To convert distance to similarity: `similarity = 1 - distance`
- LIMIT 5 can be adjusted based on requirements

### Alternative: Cosine Similarity Query

If using cosine similarity directly:

```sql
SELECT 
    chunk_id,
    document_id,
    chunk_text,
    metadata,
    1 - (embedding <=> '[query_embedding]') AS similarity
FROM document_chunks
ORDER BY similarity DESC
LIMIT 5;
```

### Filtered Query Example

Query with document filtering:

```sql
SELECT 
    chunk_id,
    document_id,
    chunk_text,
    metadata,
    embedding <=> '[query_embedding]' AS distance
FROM document_chunks
WHERE document_id = 'doc_001'
ORDER BY distance
LIMIT 5;
```

## Data Insertion Requirements

### Insert Statement Format

The AI team will insert chunks using:

```sql
INSERT INTO document_chunks (
    chunk_id,
    document_id,
    chunk_text,
    embedding,
    page_number,
    metadata
) VALUES (
    'doc_001_chunk_001',
    'doc_001',
    'Machine learning is a field of AI...',
    '[0.123, -0.456, 0.789, ...]',  -- 384-dimensional array
    1,
    '{"source": "ai_textbook.pdf", "author": "AI Team"}'::jsonb
);
```

### Batch Insertion

For efficiency, the AI team may use batch inserts:

```sql
INSERT INTO document_chunks (chunk_id, document_id, chunk_text, embedding, metadata)
VALUES 
    ('doc_001_chunk_001', 'doc_001', 'text1', '[...]', '{"source": "file.pdf"}'::jsonb),
    ('doc_001_chunk_002', 'doc_001', 'text2', '[...]', '{"source": "file.pdf"}'::jsonb),
    ('doc_001_chunk_003', 'doc_001', 'text3', '[...]', '{"source": "file.pdf"}'::jsonb);
```

## Connection Requirements

### Database Connection Parameters

The AI team needs:
- **Host**: PostgreSQL server address
- **Port**: Typically 5432
- **Database name**: e.g., `rag_db`
- **Username**: Database user with read/write permissions
- **Password**: Authentication credentials
- **SSL mode**: As per security requirements

### Python Library

The AI team will use `psycopg2` or `asyncpg` for database connectivity:

```python
import psycopg2
import numpy as np

# Example connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="rag_db",
    user="rag_user",
    password="password"
)
```

## Performance Requirements

### Expected Query Performance

- **Single query**: < 100ms for 10K chunks
- **Single query**: < 500ms for 100K chunks
- **Single query**: < 2s for 1M chunks

### Insert Performance

- **Single insert**: < 10ms
- **Batch insert (100 chunks)**: < 500ms
- **Bulk insert (1000 chunks)**: < 5s

## Integration Points

### From AI Team to Database

1. **Chunking**: AI team chunks documents using `ai/rag/chunker.py`
2. **Embedding**: AI team generates 384-dimensional embeddings using `ai/rag/embedder.py`
3. **Insertion**: AI team inserts chunks and embeddings into `document_chunks` table
4. **Query**: AI team generates query embedding and runs similarity search

### From Database to AI Team

1. **Retrieval**: Database returns top-k chunks with similarity scores
2. **Context**: AI team uses retrieved chunks as context for LLM
3. **Citations**: AI team uses metadata to generate citations

## Testing Requirements

### Test Data

The AI team will provide test data:
- Sample document chunks
- Sample embeddings (384-dimensional)
- Test queries

### Validation Checklist

- [ ] Table created with correct schema
- [ ] HNSW index created on embedding column
- [ ] Can insert single chunk successfully
- [ ] Can insert batch of chunks successfully
- [ ] Can retrieve chunks by document_id
- [ ] Similarity search returns correct results
- [ ] Query performance meets requirements
- [ ] Metadata JSONB queries work correctly

## Migration Requirements

### From In-Memory to pgvector

Current state (Week 2):
- Chunks stored in Python lists
- Embeddings stored in NumPy arrays
- Similarity search using sklearn

Target state (Week 3):
- Chunks stored in PostgreSQL
- Embeddings stored as vector(384) type
- Similarity search using pgvector

### Migration Steps

1. Create PostgreSQL database and table
2. Migrate existing chunks to database
3. Update AI team code to use database
4. Test retrieval accuracy
5. Benchmark performance
6. Deploy to production

## Security Requirements

### Access Control

- Database user should have minimal required permissions
- Read-only access for retrieval operations
- Write access for ingestion operations
- No DROP/ALTER permissions for application user

### Data Protection

- Encrypt connections using SSL/TLS
- Store credentials securely (environment variables)
- Implement connection pooling
- Log query operations for auditing

## Future Enhancements

### Week 4+ Features

1. **Hybrid Search**: Combine semantic search with keyword search
2. **Reranking**: Implement cross-encoder reranking
3. **Filtering**: Add advanced metadata filtering
4. **Caching**: Cache frequent queries
5. **Partitioning**: Partition table by document_id for scale
6. **Replication**: Set up read replicas for load balancing

## Contact Information

**AI Team Contact**: [Your Name]
**Database Team Contact**: @Lý Tấn Phát
**Week 3 Deadline**: [Specify date]

## References

- pgvector Documentation: https://github.com/pgvector/pgvector
- PostgreSQL JSONB: https://www.postgresql.org/docs/current/datatype-json.html
- HNSW Index: https://github.com/pgvector/pgvector#hnsw
