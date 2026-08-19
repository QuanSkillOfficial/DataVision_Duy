# RAG Response Contract

**API Version**: 1.0  
**Last Updated**: Week 3  
**Consumers**: Backend (Phi), Chatbot UI (Hung), Dashboard (Phi)

## Overview

Defines the response format from the RAG retrieval system that will be consumed by downstream services.

## Response Structure

### Retrieval-Only Response (Initial Implementation)

When only semantic search is performed (no LLM answer generation):

```json
{
  "question": "What is the refund policy?",
  "answer": null,
  "retrieved_context": [
    {
      "chunk_id": "doc_001_page_1_chunk_000",
      "document_id": "doc_001",
      "file_name": "policy.pdf",
      "page_number": 1,
      "similarity_score": 0.87,
      "chunk_text": "Refunds are available within 30 days of purchase..."
    },
    {
      "chunk_id": "doc_001_page_1_chunk_001",
      "document_id": "doc_001",
      "file_name": "policy.pdf",
      "page_number": 1,
      "similarity_score": 0.82,
      "chunk_text": "Original packaging must be intact for returns..."
    }
  ],
  "citations": [
    {
      "file_name": "policy.pdf",
      "page_number": 1,
      "chunk_id": "doc_001_page_1_chunk_000"
    },
    {
      "file_name": "policy.pdf",
      "page_number": 1,
      "chunk_id": "doc_001_page_1_chunk_001"
    }
  ],
  "status": "retrieval_only",
  "model": "all-MiniLM-L6-v2",
  "metadata": {
    "retrieval_time_ms": 45,
    "num_chunks_searched": 2500,
    "top_k": 5,
    "filter_applied": null
  }
}
```

### With LLM Answer (Future - Week 4+)

When LLM answer generation is enabled:

```json
{
  "question": "What is the refund policy?",
  "answer": "According to the provided documents, refunds are available within 30 days of purchase if the original packaging is intact.",
  "answer_confidence": 0.92,
  "retrieved_context": [
    {
      "chunk_id": "doc_001_page_1_chunk_000",
      "document_id": "doc_001",
      "file_name": "policy.pdf",
      "page_number": 1,
      "similarity_score": 0.87,
      "chunk_text": "Refunds are available within 30 days of purchase..."
    }
  ],
  "citations": [
    {
      "file_name": "policy.pdf",
      "page_number": 1,
      "chunk_id": "doc_001_page_1_chunk_000"
    }
  ],
  "status": "answered",
  "model": "all-MiniLM-L6-v2",
  "metadata": {
    "retrieval_time_ms": 45,
    "llm_time_ms": 1200,
    "total_time_ms": 1245,
    "num_chunks_searched": 2500,
    "top_k": 5,
    "filter_applied": null,
    "llm_model": "gpt-3.5-turbo"
  }
}
```

### No Answer Found Response

When query doesn't match any documents:

```json
{
  "question": "What is the secret ingredient?",
  "answer": null,
  "retrieved_context": [],
  "citations": [],
  "status": "no_answer_found",
  "model": "all-MiniLM-L6-v2",
  "metadata": {
    "retrieval_time_ms": 32,
    "num_chunks_searched": 2500,
    "top_k": 5,
    "filter_applied": null,
    "reason": "No chunks matched the query above similarity threshold"
  }
}
```

## Field Definitions

### Top Level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | The original user question |
| `answer` | string or null | Yes | LLM-generated answer (null if not generated) |
| `answer_confidence` | number (0-1) | No | Confidence score for generated answer (0.0-1.0) |
| `retrieved_context` | array | Yes | List of relevant chunks found |
| `citations` | array | Yes | Unique sources for the answer |
| `status` | enum | Yes | One of: `retrieval_only`, `answered`, `no_answer_found`, `error` |
| `model` | string | Yes | Name of embedding model used (e.g., "all-MiniLM-L6-v2") |
| `metadata` | object | Yes | Timing and performance information |

### retrieved_context[n]

Each chunk in the retrieved context:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chunk_id` | string | Yes | Unique chunk identifier (e.g., "doc_001_page_1_chunk_000") |
| `document_id` | string | Yes | Source document ID |
| `file_name` | string | Yes | Original filename for display |
| `page_number` | integer | No | Page number if applicable |
| `similarity_score` | number (0-1) | Yes | Cosine similarity score |
| `chunk_text` | string | Yes | The actual text content |

### citations[n]

Unique source references:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file_name` | string | Yes | PDF/document filename |
| `page_number` | integer | No | Page number in the document |
| `chunk_id` | string | Yes | Reference to the chunk |

### metadata

Performance and configuration info:

| Field | Type | Description |
|-------|------|-------------|
| `retrieval_time_ms` | integer | Time to search vector store |
| `llm_time_ms` | integer | Time to generate answer (if applicable) |
| `total_time_ms` | integer | Total request time |
| `num_chunks_searched` | integer | How many chunks exist in database |
| `top_k` | integer | How many chunks were requested |
| `filter_applied` | object or null | Metadata filters applied (e.g., `{document_id: "doc_001"}`) |
| `llm_model` | string | LLM used for answer generation (if applicable) |
| `reason` | string | Explanation for status (if status is error or no_answer_found) |

## HTTP API Endpoints

### POST /rag/retrieve

Retrieve relevant chunks without answer generation:

**Request:**
```json
{
  "question": "What is the refund policy?",
  "top_k": 5,
  "min_similarity_score": 0.5,
  "filter": {
    "document_id": "doc_001"
  }
}
```

**Response:** Retrieval-only response (status: "retrieval_only")

**Status Codes:**
- 200: Success
- 400: Invalid query or parameters
- 500: Server error

### POST /rag/answer

Retrieve chunks AND generate answer:

**Request:**
```json
{
  "question": "What is the refund policy?",
  "top_k": 5,
  "min_similarity_score": 0.5,
  "generate_answer": true,
  "filter": {
    "document_id": "doc_001"
  }
}
```

**Response:** Response with answer (status: "answered" or "no_answer_found")

**Status Codes:**
- 200: Success (may have answer or not)
- 400: Invalid query or parameters
- 500: Server error

## Integration Examples

### Backend (Phi) - Store Results

```python
# POST /rag/retrieve
response = rag_client.retrieve(
    question="What is the policy?",
    top_k=5
)

# Store for analytics
save_to_database({
    "question": response["question"],
    "chunks_found": len(response["retrieved_context"]),
    "citations": response["citations"],
    "timestamp": datetime.now()
})
```

### Chatbot UI (Hung) - Display to User

```python
# Display answer with sources
if response["status"] == "answered":
    display_answer(response["answer"])
    display_citations(response["citations"])
elif response["status"] == "retrieval_only":
    # Show chunks instead
    for chunk in response["retrieved_context"]:
        display_context(
            text=chunk["chunk_text"],
            source=chunk["file_name"],
            page=chunk["page_number"]
        )
else:
    display_message("I don't know based on the provided documents")
```

### Dashboard (Phi) - Analyze Performance

```python
# Track retrieval quality
metrics = {
    "avg_similarity_score": mean([c["similarity_score"] for c in response["retrieved_context"]]),
    "retrieval_time_ms": response["metadata"]["retrieval_time_ms"],
    "llm_time_ms": response["metadata"].get("llm_time_ms", 0),
    "total_time_ms": response["metadata"]["total_time_ms"]
}

log_metrics(metrics)
```

## Error Responses

### Invalid Question

```json
{
  "question": null,
  "answer": null,
  "retrieved_context": [],
  "citations": [],
  "status": "error",
  "model": "all-MiniLM-L6-v2",
  "metadata": {
    "reason": "Question cannot be empty",
    "error_code": "INVALID_QUESTION"
  }
}
```

### Database Error

```json
{
  "question": "What is the policy?",
  "answer": null,
  "retrieved_context": [],
  "citations": [],
  "status": "error",
  "model": "all-MiniLM-L6-v2",
  "metadata": {
    "reason": "Failed to connect to vector store",
    "error_code": "DATABASE_ERROR",
    "retrieval_time_ms": null
  }
}
```

## Backward Compatibility

### Version 1.0 → 1.1

When upgrading RAG system:
- New fields will be added with sensible defaults
- Existing consumers should ignore unknown fields
- Old responses will still be parseable

### Versioning

Include API version in requests for future compatibility:

```json
{
  "api_version": "1.0",
  "question": "...",
  ...
}
```

## Performance Expectations

| Metric | Target | Notes |
|--------|--------|-------|
| Retrieval latency | < 100ms | For 10k chunks |
| LLM latency | 1-3 seconds | Depends on LLM |
| Similarity score | 0.6+ | For relevant results |
| Chunk relevance | > 70% | Evaluated manually |

## Future Enhancements

- [ ] Streaming responses for long answers
- [ ] Bulk retrieval for multiple questions
- [ ] Feedback mechanism for relevance ranking
- [ ] Cached responses for repeated questions
- [ ] Advanced filtering (date ranges, metadata conditions)
- [ ] Multi-language support
- [ ] Explainability scores (why chunks were selected)
