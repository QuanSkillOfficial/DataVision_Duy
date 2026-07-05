# Week 6 RAG Handoff Summary

Owner: Nguyen Minh Duy  
Consumer: Lap - RAG and Embeddings Owner  
Purpose: Provide Duy's real DataFlow PDF extraction output for chunking, embedding, pgvector insertion, retrieval evaluation, and citation generation.

## Files

| File | Purpose |
| --- | --- |
| `outputs/rag_handoff/document_pages.jsonl` | Page-level text records for Lap chunking |
| `outputs/rag_handoff/pdf_metadata.json` | PDF metadata and extraction statistics |
| `outputs/rag_handoff/rag_handoff_manifest.json` | Machine-readable handoff summary |

## Real Extraction Statistics

| Metric | Value |
| --- | --- |
| `document_external_id` | `doc_dataflow_technical_report` |
| `source_name` | `dataflow_technical_report_pdf` |
| `file_name` | `DataFlow_Technical_Report.pdf` |
| `ingestion_run_id` | `1abee790-3e55-4855-b6b6-fa64ee1dbd54` |
| `page_count` | `36` |
| `non_empty_pages` | `36` |
| `empty_pages` | `0` |
| `total_characters` | `129028` |
| `parsing_status` | `ready` |

## ID Mapping Rule

Lap should treat `document_id` in `document_pages.jsonl` as Duy's external document key.

```text
document_pages.jsonl.document_id
  -> documents.document_external_id
  -> documents.id
  -> document_chunks.document_id
```

Do not insert the string `document_id` directly into `document_chunks.document_id`; Phat's table expects the internal integer `documents.id`.

## Page Record Contract

Each line in `document_pages.jsonl` contains:

```json
{
  "document_id": "doc_dataflow_technical_report",
  "file_name": "DataFlow_Technical_Report.pdf",
  "page_number": 1,
  "text": "...",
  "character_count": 2953,
  "is_empty": false,
  "source": "DataFlow_Technical_Report.pdf"
}
```
