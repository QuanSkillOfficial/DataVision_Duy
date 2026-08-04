# Chunking Strategy for RAG System

## Overview

This document describes the chunking strategy used in the RAG system for Week 2. Chunking is the process of splitting large documents into smaller, manageable pieces that can be embedded and retrieved effectively.

## Current Implementation (Week 2)

### Fixed-Size Chunking with Overlap

**File**: `ai/rag/chunker.py`

**Functions**:
- `fixed_size_chunk(text, chunk_size=512, overlap=50)` - Splits text into fixed-size chunks
- `create_chunks(document_id, text, metadata=None, chunk_size=512, overlap=50)` - Creates formatted chunks with metadata

### Parameters

- **chunk_size**: 512 characters (default)
  - Reasonable size for most embedding models
  - Balances context preservation with embedding efficiency
  - Can be adjusted based on document type

- **overlap**: 50 characters (default)
  - Ensures continuity between chunks
  - Helps prevent cutting off important information at chunk boundaries
  - Improves retrieval by providing context overlap

### Chunk Structure

Each chunk contains:
```python
{
    "document_id": "doc_001",
    "chunk_id": "doc_001_chunk_001",
    "chunk_text": "...",
    "start_char": 0,
    "end_char": 512,
    "metadata": {}
}
```

### Metadata

Metadata can include:
- `source`: Original document filename/URL
- `page_number`: Page number in PDF
- `section`: Document section header
- `author`: Document author
- `created_at`: Timestamp
- Custom fields as needed

## Why Fixed-Size Chunking?

### Advantages
- **Simple to implement**: No complex NLP processing required
- **Predictable**: Consistent chunk sizes for storage and retrieval
- **Fast**: No dependency on sentence tokenizers or semantic analysis
- **Deterministic**: Same input always produces same output

### Limitations
- May split sentences or paragraphs in the middle
- Doesn't consider semantic boundaries
- Can lose context at chunk boundaries
- Not optimal for all document types

## Future Improvements (Week 3+)

### 1. Sentence-Based Chunking
- Split at sentence boundaries
- Maintain sentence integrity
- Better for natural language processing
- Requires sentence tokenizer

### 2. Semantic Chunking
- Use embeddings to identify natural breakpoints
- Group semantically related sentences
- More context-aware
- Requires embedding model and clustering

### 3. Recursive Character Chunking
- Hierarchical chunking strategy
- Different chunk sizes for different sections
- More flexible for complex documents

### 4. Markdown/HTML-Aware Chunking
- Respect document structure
- Chunk by headers, sections, paragraphs
- Better for technical documentation

## Usage Example

```python
from ai.rag.chunker import create_chunks

# Create chunks from a document
chunks = create_chunks(
    document_id="policy_doc_001",
    text="Document text here...",
    metadata={
        "source": "company_policy.pdf",
        "page_number": 1,
        "section": "Introduction"
    },
    chunk_size=512,
    overlap=50
)

# Access chunk data
for chunk in chunks:
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Text: {chunk['chunk_text']}")
    print(f"Metadata: {chunk['metadata']}")
```

## Testing

The chunker includes a test suite in the `__main__` block that:
- Tests basic chunking functionality
- Verifies chunk structure
- Demonstrates metadata handling
- Shows character position tracking

Run tests with:
```bash
python ai/rag/chunker.py
```

## Integration with RAG Pipeline

1. **Ingestion**: Documents are loaded and chunked
2. **Embedding**: Each chunk is converted to a 384-dimensional vector
3. **Storage**: Chunks and embeddings stored in pgvector
4. **Retrieval**: Query embedding compared to chunk embeddings
5. **Generation**: Retrieved chunks used as context for LLM

## Performance Considerations

- Chunk size affects retrieval precision vs. recall
- Larger chunks = more context but less precise matching
- Smaller chunks = more precise but may lose context
- Overlap helps balance this trade-off
- Optimal parameters depend on use case and document type

## References

- LangChain Chunking Strategies: https://python.langchain.com/docs/modules/data_connection/document_transformers/
- Semantic Chunking Research: Various academic papers on text segmentation
