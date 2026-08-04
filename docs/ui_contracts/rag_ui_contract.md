# RAG / Chatbot UI Contract

**Owner (data provider):** Lap (RAG & Embeddings)
**Consumer:** Phi & Hung — `demo/chatbot_page.py`
**Service entry point:** `service_client.ask_rag(question, document_id=None)`

---

## 1. Input

| Field | Type | Required | Notes |
|---|---|---|---|
| `question` | str | Yes | User's natural-language question |
| `document_id` | str | No | Restricts retrieval to one document if provided |

---

## 2. Response — Match Found

```json
{
  "question": "What is the DataFlow pipeline?",
  "answer": "DataFlow is described as an LLM-driven framework...",
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": null,
  "citations": [
    {
      "file_name": "DataFlow_Technical_Report.pdf",
      "page_number": 4,
      "chunk_id": "doc_dataflow_technical_report_page_4_chunk_000",
      "document_external_id": "doc_dataflow_technical_report",
      "document_db_id": null
    }
  ],
  "retrieved_context": [
    {
      "chunk_text": "Customers may request a full refund within 30 days...",
      "similarity_score": 0.89,
      "chunk_id": "doc_001_page_2_chunk_003"
    }
  ],
  "model": "all-MiniLM-L6-v2 + gpt-4o-mini",
  "retrieval_backend": "pgvector",
  "embedding_dimension": 384,
  "status": "success"
}
```

## 3. Response — No Match Found

```json
{
  "question": "What is the weather today?",
  "answer": "I do not know based on the provided documents.",
  "citations": [],
  "retrieved_context": [],
  "model": "all-MiniLM-L6-v2",
  "status": "no_match"
}
```

---

## Field Reference

### Citation Object

| Field | Type | Notes |
|---|---|---|
| `file_name` | str | |
| `page_number` | int | |
| `chunk_id` | str | |
| `document_external_id` | str | Links to Duy's ingestion result (**NEW Week 6**) |
| `document_db_id` | str | Links to Phat's DB record (**NEW Week 6**) |

### Retrieved Context Object

| Field | Type |
|---|---|
| `chunk_text` | str |
| `similarity_score` | float (0.0–1.0) |
| `chunk_id` | str (matches the citation it supports) |

---

## UI Behavior Rules

### Similarity Badge

| Range | Color |
|---|---|
| `>= 0.80` | 🟢 Green |
| `0.60–0.79` | 🟡 Orange/Yellow |
| `< 0.60` | 🔴 Red |

### Citation Cards
Each citation renders as an expandable card titled
`📄 {file_name} — Page {page_number}`, showing:
1. Similarity badge
2. Chunk ID (monospace)
3. Full chunk text (context expander)

Week 7 fixture mode must use `DataFlow_Technical_Report.pdf` citations
with chunk IDs in the form
`doc_dataflow_technical_report_page_X_chunk_YYY`.

### Empty State
When `citations` is empty (no match), render the literal answer text
`"I do not know based on the provided documents."` — do not render
an empty citations section, do not show a stack trace or blank box.

### Status Values

| Status | Meaning |
|---|---|
| `success` | Answer generated with grounding context |
| `no_match` | No relevant context found in the corpus |
| `error` | Question was empty or the RAG service failed |
