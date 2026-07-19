# Week 7 Duy to Lap RAG Handoff

## Files

- `outputs/rag_handoff/week7_document_pages_db_enriched.jsonl`
- `outputs/rag_handoff/week7_rag_handoff_manifest.json`
- `outputs/rag_handoff/pdf_metadata.json`

## Verified document

| Field | Value |
| --- | --- |
| document_external_id | `doc_dataflow_technical_report` |
| document_db_id | `1` |
| source_id | `4` |
| file_name | `DataFlow_Technical_Report.pdf` |
| pages | 36 |
| non-empty pages | 36 |
| characters | 129,028 |
| words | 17,536 |

Each JSONL record includes `document_external_id`, `document_db_id`, `source_id`, `ingestion_run_id`, `page_number`, `text`, `char_count`, `word_count`, and `is_empty`.

The current Duy-to-Phat Docker proof confirms the stable IDs and the latest PDF
run UUID. The manifest now records `current_ingestion_run_loaded=true`.
Regenerate from the current DB result with:

```bash
python scripts/week7_build_rag_handoff_package.py
```

Lap must map `document_external_id` to the integer `documents.id`; a string ID must never be inserted into `document_chunks.document_id`.

## Lap output contract

Lap must return these files after running against Phat's PostgreSQL database:

```text
DataVision_Lap/outputs/rag/week7_chunk_insert_summary.json
DataVision_Lap/outputs/rag/week7_pgvector_query_result.json
DataVision_Lap/outputs/rag/week7_rag_query_log_payload.json
DataVision_Lap/outputs/ui_fixtures/lap_rag_response_real.json
```

The insert result must report the actual page, chunk and embedding counts.
The query result must report `chunk_id`, integer `document_db_id`,
`document_external_id`, `file_name`, `page_number`, `chunk_text`, and
`similarity_score`. The UI fixture may be used for contract tests, but it is
not PostgreSQL execution proof by itself.

Phat's Week 7 database schema uses `user_query` in `rag_query_logs`. If Lap
accepts `query_text` at the service boundary, it must normalize that alias to
`user_query` before inserting the row.

## Current audit status

The Duy handoff contract passes. The Lap repository audit is recorded in:

```text
outputs/lap_handoff/lap_week7_mapping_summary.json
logs/lap_handoff/lap_week7_external_proof.json
docs/week7_duy_lap_mapping_result.md
```

At the audited Lap commit, the chunk insert and pgvector query result files
are still `pending_db_connection`, and Lap unit-test collection stops on an
unused `torch` import in `ai/rag/vector_store.py`. Therefore the current
mapping status is `blocked_on_lap_execution`, not end-to-end proven.

Before closing the handoff, Lap must:

1. remove the unused `torch` import and pass `pytest ai/ai_tests/ -q`;
2. make `use_pgvector=True` fail clearly instead of silently falling back to
   in-memory storage;
3. reject unresolved or null `documents.id` values before insert;
4. enforce 384-dimensional embeddings;
5. fix duplicate filtering so chunks and embeddings remain aligned;
6. run the real loader and query commands and replace the pending JSON files;
7. insert one RAG log and return a non-empty `v_rag_daily_metrics` row.
