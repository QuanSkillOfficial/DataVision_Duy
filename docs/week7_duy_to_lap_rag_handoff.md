# Week 7 Duy to Lap RAG Handoff

## Files

- `outputs/rag_handoff/week7_document_pages_db_enriched.jsonl`
- `outputs/rag_handoff/week7_rag_handoff_manifest.json`
- `outputs/rag_handoff/pdf_metadata.json`

## Verified document

| Field | Value |
| --- | --- |
| document_external_id | `doc_dataflow_technical_report` |
| file_name | `DataFlow_Technical_Report.pdf` |
| pages | 36 |
| non-empty pages | 36 |
| characters | 129,028 |
| words | 17,536 |

Each JSONL record includes `document_external_id`, `document_db_id`, `source_id`, `ingestion_run_id`, `page_number`, `text`, `char_count`, `word_count`, and `is_empty`.

`document_db_id` and `source_id` remain `null` before a real Phat database load. After `--write-db`, rerun:

```bash
python scripts/week7_build_rag_handoff_package.py
```

Lap must map `document_external_id` to the integer `documents.id`; a string ID must never be inserted into `document_chunks.document_id`.
