# Embedding Model Notes

## Model Selection

**Model**: `sentence-transformers/all-MiniLM-L6-v2`

**HuggingFace**: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

## Model Specifications

### Key Parameters
- **Embedding Dimension**: 384
- **Model Size**: ~80MB
- **Max Sequence Length**: 512 tokens
- **Architecture**: MiniLM with 6 layers
- **Training Data**: Various NLI and STS benchmarks

### Why This Model?

**Advantages**:
- **Fast**: Small model size enables quick inference
- **Good Quality**: Strong performance on semantic similarity tasks
- **Lightweight**: Suitable for CPU inference
- **Well-tested**: Widely used in production RAG systems
- **384-dimensional**: Compact vectors for efficient storage and search

**Trade-offs**:
- Lower dimension than larger models (e.g., 768 for BERT-base)
- Less nuanced understanding compared to larger models
- May struggle with very domain-specific terminology

## Embedding Dimension Impact

### Why 384 Matters for pgvector

The embedding dimension directly affects the PostgreSQL schema:

```sql
CREATE TABLE document_chunks (
    chunk_id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(384),  -- Must match model dimension
    page_number INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Critical**: The `vector(384)` type must exactly match the model's output dimension. Mismatched dimensions will cause errors.

### Storage Considerations

- **Per vector**: 384 × 4 bytes (float32) = ~1.5KB
- **10K chunks**: ~15MB for embeddings
- **100K chunks**: ~150MB for embeddings
- **1M chunks**: ~1.5GB for embeddings

### Search Performance

- **Index type**: HNSW (Hierarchical Navigable Small World)
- **Build time**: Fast for 384-dimensional vectors
- **Query time**: Sub-millisecond for typical queries
- **Memory**: Lower memory footprint than higher-dimensional models

## Usage

### Installation

```bash
pip install sentence-transformers
```

### Loading the Model

```python
from ai.rag.embedder import load_embedding_model

model = load_embedding_model("sentence-transformers/all-MiniLM-L6-v2")
```

### Embedding Texts

```python
from ai.rag.embedder import embed_texts

texts = ["Machine learning is awesome.", "Deep learning uses neural networks."]
embeddings = embed_texts(texts, model)
# embeddings.shape: (2, 384)
```

### Embedding Queries

```python
from ai.rag.embedder import embed_query

query = "What is deep learning?"
query_embedding = embed_query(query, model)
# query_embedding.shape: (384,)
```

### Getting Dimension

```python
from ai.rag.embedder import get_embedding_dimension

dim = get_embedding_dimension(model)
# dim: 384
```

## Semantic Similarity

### Cosine Similarity

```python
from sklearn.metrics.pairwise import cosine_similarity

# Compare query to chunks
similarities = cosine_similarity([query_embedding], chunk_embeddings)
# Returns array of similarity scores [0, 1]
```

### Interpretation
- **1.0**: Identical meaning
- **0.8-0.9**: Very similar
- **0.6-0.8**: Related concepts
- **0.4-0.6**: Somewhat related
- **0.0-0.4**: Unrelated

## Performance Benchmarks

### Inference Speed (CPU)
- **Single text**: ~5-10ms
- **Batch of 10**: ~20-30ms
- **Batch of 100**: ~150-200ms

### Memory Usage
- **Model loading**: ~300MB
- **Inference**: ~50MB additional

## Testing

The embedder includes tests in the `__main__` block:
- Model loading
- Text embedding
- Query embedding
- Similarity computation

Run tests with:
```bash
python ai/rag/embedder.py
```

## Integration with RAG Pipeline

1. **Chunking**: Documents split into chunks
2. **Embedding**: Each chunk → 384-dimensional vector
3. **Storage**: Vectors stored in pgvector as `vector(384)`
4. **Query**: User query → 384-dimensional vector
5. **Search**: Cosine similarity between query and chunk vectors
6. **Retrieval**: Top-k most similar chunks returned

## Future Model Considerations

### Potential Upgrades
- **all-mpnet-base-v2**: 768 dimensions, better quality, slower
- **e5-large-v2**: 1024 dimensions, instruction-tuned
- **bge-large-en-v1.5**: 1024 dimensions, state-of-the-art

### When to Upgrade
- Need higher precision for complex queries
- Domain-specific terminology not well captured
- Sufficient compute resources for larger models
- Quality metrics show retrieval issues

### Migration Strategy
1. Benchmark current model
2. Test candidate models on sample data
3. Compare retrieval quality
4. Evaluate performance impact
5. Update pgvector schema dimension
6. Re-embed all chunks
7. Deploy with monitoring

## References

- Sentence-Transformers Documentation: https://www.sbert.net/
- HuggingFace Model Card: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
