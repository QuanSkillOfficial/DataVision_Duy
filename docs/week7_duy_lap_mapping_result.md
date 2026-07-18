# Week 7 Duy - Lap Mapping and Audit Result

## Purpose

This document is the authoritative Week 7 mapping between Duy's ingestion
handoff and Lap's RAG module. It describes the exact input files, required
fields, output files, execution commands, and current proof status.

The report was generated from:

- Duy repository: `DataVision_Duy`
- Lap repository: `DataVision_Lap`
- Lap commit audited: `b1275fda7d3222d3c82972d9c224ddf858fc291f`
- Audit output: `outputs/lap_handoff/lap_week7_mapping_summary.json`

The Lap checkout was audited read-only. Lap-owned code and files must be
changed and committed by Lap before they are treated as completed.

## 1. Canonical IDs

The same identity rules must be used by Duy, Phat, Lap, Tuong and Phi/Hung.

| Field | Owner | Current DataFlow value | Meaning |
| --- | --- | --- | --- |
| `source_id` | Phat | `4` | Integer `sources.id`. Never use a run UUID here. |
| `source_name` | Duy | `dataflow_technical_report_pdf` | Stable source key. |
| `document_external_id` | Duy/Lap/Tuong | `doc_dataflow_technical_report` | Stable string document key. |
| `document_db_id` | Phat | `1` | Integer `documents.id`, resolved from `document_external_id`. |
| `ingestion_run_id` | Duy | UUID in the handoff manifest | Run UUID. It is not a source ID or document ID. |
| `document_chunks.document_id` | Phat/Lap | `1` | Integer foreign key to `documents.id`. |

Required mapping:

```text
Duy document_external_id
  -> Phat documents.document_external_id
  -> Phat documents.id
  -> Lap document_chunks.document_id
```

Lap must never insert `doc_dataflow_technical_report` directly into the
integer `document_chunks.document_id` column.

## 2. Input From Duy to Lap

### 2.1 Required files

| Purpose | Path |
| --- | --- |
| DB-enriched pages | `outputs/rag_handoff/week7_document_pages_db_enriched.jsonl` |
| Handoff metadata and identity | `outputs/rag_handoff/week7_rag_handoff_manifest.json` |
| PDF metadata | `outputs/rag_handoff/pdf_metadata.json` |
| CI-sized sample pages | `tests/fixtures/data/sample_dataflow_pages_small.jsonl` |
| Full page contract | `docs/week7_duy_to_lap_rag_handoff.md` |

### 2.2 Page record contract

Every JSONL record must include:

```json
{
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": 1,
  "source_id": 4,
  "file_name": "DataFlow_Technical_Report.pdf",
  "page_number": 1,
  "text": "...",
  "char_count": 3500,
  "word_count": 520,
  "is_empty": false,
  "ingestion_run_id": "duy-run-uuid"
}
```

### 2.3 Verified Duy handoff values

| Check | Result |
| --- | --- |
| Pages loaded | `36` |
| Non-empty pages | `36` |
| Page sequence | `1..36` |
| Total characters | `129028` |
| Total words | `17536` |
| `char_count == len(text)` | passed |
| `word_count == len(text.split())` | passed |
| `document_external_id` | `doc_dataflow_technical_report` |
| `document_db_id` | `1` |
| `source_id` | `4` |
| File name | `DataFlow_Technical_Report.pdf` |

The Duy input contract is currently **passed**.

## 3. Output Required From Lap

Lap must return all of the following files in the Lap repository:

| Purpose | Path | Required proof |
| --- | --- | --- |
| Chunk insert result | `outputs/rag/week7_chunk_insert_summary.json` | `status=success`, pages/chunks/embeddings and inserted count |
| pgvector query result | `outputs/rag/week7_pgvector_query_result.json` | `status=success`, top-k rows, scores and citations |
| RAG log payload | `outputs/rag/week7_rag_query_log_payload.json` | canonical DB field names and retrieved chunk IDs |
| UI response fixture | `outputs/ui_fixtures/lap_rag_response_real.json` | DataFlow fields, citations and response metadata |
| Handoff validation | `docs/week7_duy_to_lap_rag_handoff_validation.md` | actual page statistics and issues |
| Integration result | `docs/week7_lap_phat_pgvector_integration_result.md` | executed database proof, not only a template |
| Query log result | `docs/week7_rag_query_log_insert_result.md` | inserted row ID and `v_rag_daily_metrics` output |

### 3.1 Required chunk insert result shape

```json
{
  "status": "success",
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": 1,
  "pages_loaded": 36,
  "non_empty_pages": 36,
  "chunks_created": 293,
  "chunks_inserted": 293,
  "duplicate_chunks_skipped": 0,
  "embeddings_generated": 293,
  "embedding_dimension": 384,
  "errors": []
}
```

`293` is the current Phat database count. Lap may return a different
generated count if the chunking configuration changes, but the output must
contain the actual count and not an estimate.

### 3.2 Required retrieval row shape

Every retrieved row must contain:

```json
{
  "chunk_id": "doc_dataflow_technical_report_page_4_chunk_000",
  "document_db_id": 1,
  "document_external_id": "doc_dataflow_technical_report",
  "file_name": "DataFlow_Technical_Report.pdf",
  "page_number": 4,
  "chunk_text": "...",
  "similarity_score": 0.84
}
```

### 3.3 Required RAG log mapping

Phat's Week 7 `rag_query_logs` schema uses `user_query`. The canonical DB
payload is:

```json
{
  "document_id": 1,
  "user_query": "What is the DataFlow pipeline?",
  "retrieved_chunk_ids": [
    "doc_dataflow_technical_report_page_4_chunk_000"
  ],
  "retrieval_scores": [0.84],
  "generated_response": null,
  "answer_confidence": 0.84,
  "latency_ms": 45,
  "model_name": "all-MiniLM-L6-v2"
}
```

`query_text` may be accepted as an API alias, but it must be normalized to
`user_query` before the SQL insert. Do not send two competing field names to
Phat.

## 4. Commands

The commands below assume the five repositories are sibling folders under the
same parent directory. In a shared repository, replace the cross-repository
path with `outputs/rag_handoff/...`.

### 4.1 Run Lap unit tests

From `DataVision_Lap`:

```powershell
python -m pytest ai/ai_tests/ -q
```

Expected result: all tests collected and passed. The current audited commit
does not meet this gate because import collection fails on an unused `torch`
import.

### 4.2 Run the CI-safe RAG smoke test

From `DataVision_Lap`:

```powershell
python ai/rag/scripts/week7_rag_ci_smoke_test.py
```

This test must use `FakeEmbedder` and must not download a model or require a
database.

### 4.3 Load Duy pages into Phat pgvector

From `DataVision_Lap`, after Phat's database is running:

```powershell
$env:DATABASE_URL = "postgresql://datavision:datavision123@localhost:5432/datavision_db"
python -m ai.rag.load_document_pages_to_pgvector `
  --document-pages ..\DataVision_Duy\outputs\rag_handoff\week7_document_pages_db_enriched.jsonl `
  --document-external-id doc_dataflow_technical_report `
  --output-result outputs\rag\week7_chunk_insert_summary.json
```

The command must fail with a non-zero exit code when the database is
unavailable, the document ID cannot be resolved, the table is missing, or the
embedding dimension is not 384. It must not silently switch to in-memory mode.

### 4.4 Run the real pgvector query

From `DataVision_Lap`:

```powershell
python ai/rag/scripts/week7_pgvector_smoke_test.py `
  --query "What is the DataFlow pipeline?" `
  --document-external-id doc_dataflow_technical_report `
  --top-k 5 `
  --output-result outputs\rag\week7_pgvector_query_result.json
```

The output must show `status=success`, `document_db_id=1`, at least one
retrieved chunk, page numbers, similarity scores and citations.

### 4.5 Verify the database side

From the Phat repository:

```powershell
python week7\database\scripts\ci_database_smoke_test.py
```

The relevant SQL proof is:

```sql
SELECT COUNT(*) FROM document_chunks;
SELECT COUNT(*) FROM rag_query_logs;
SELECT * FROM v_document_rag_readiness;
SELECT * FROM v_rag_daily_metrics;
```

## 5. Current Audit Status

The generated machine-readable report is:

```text
outputs/lap_handoff/lap_week7_mapping_summary.json
logs/lap_handoff/lap_week7_external_proof.json
```

Current state:

| Area | Status | Evidence |
| --- | --- | --- |
| Duy page handoff | passed | 36 validated DB-enriched pages |
| Lap active file set | present | all canonical paths exist |
| Lap UI fixture contract | passed | DataFlow fields/citations/384 metadata present |
| Lap chunk insert execution | blocked | output status is `pending_db_connection` |
| Lap pgvector retrieval execution | blocked | output status is `pending_db_connection` |
| Lap unit test collection | blocked | `ModuleNotFoundError: No module named 'torch'` |
| RAG log DB field alignment | needs fix | output uses `query_text`; Phat schema uses `user_query` |
| Phat database counts | separately confirmed | `document_chunks=293`, `rag_query_logs=1` |

The Lap mapping status is therefore:

```text
blocked_on_lap_execution
```

The DataFlow UI fixture is useful for contract/UI tests, but it is not counted
as proof that Lap inserted or retrieved rows from PostgreSQL.

## 6. Required Lap Code Fixes

These are the concrete issues found in the audited Lap commit:

1. Remove `from torch import chunk` from `ai/rag/vector_store.py`.
2. When `use_pgvector=True`, raise a clear connection/schema error instead of
   setting `use_pgvector=False` and falling back to memory.
3. Never insert a null `document_id`; resolve
   `document_external_id -> documents.id` and fail if unresolved.
4. Validate every insert and query vector has exactly 384 dimensions.
5. When skipping duplicate chunks, keep the same indices for chunks and
   embeddings. Truncating the embedding array can associate the wrong vector
   with a chunk.
6. Normalize `query_text` to Phat's `user_query` at the DB boundary.
7. Replace pending result JSON files with outputs generated by the real loader
   and real query command.
8. Record the inserted RAG query log ID and the non-empty
   `v_rag_daily_metrics` result.

## 7. Cleanup Candidates in Lap

The following files are candidates for archive/removal after Lap confirms that
no external consumer depends on them:

```text
ai/rag/notebooks/week6_real_pgvector_rag_demo.ipynb
ai/rag/evaluation/retrieval_eval_results_week3.md
ai/rag/evaluation/retrieval_test_cases_completed.csv
ai/rag/evaluation/week6_retrieval_eval_results.md
ai/rag/evaluation/week6_retrieval_test_cases_dataflow.csv
ai/WEEK_6_SUMMARY.md
ai/week6_rag_to_schema_v4_mapping.md
week6_team_integration_handoff.md
sql/
```

The active Week 7 RAG surface should remain:

```text
ai/rag/chunker.py
ai/rag/document_loader.py
ai/rag/embedder.py
ai/rag/vector_store.py
ai/rag/retriever.py
ai/rag/rag_pipeline.py
ai/rag/rag_service.py
ai/rag/load_document_pages_to_pgvector.py
ai/rag/scripts/week7_pgvector_smoke_test.py
ai/rag/scripts/week7_rag_ci_smoke_test.py
ai/ai_tests/
outputs/rag/
outputs/ui_fixtures/
docs/week7_*.md
```

## 8. Definition of Done for Duy + Lap

- [x] Duy produces 36 validated DB-enriched pages.
- [x] `document_external_id`, `source_id`, `document_db_id` and
  `ingestion_run_id` are separated.
- [x] Phat identity mapping confirms `source_id=4` and `document_db_id=1`.
- [ ] Lap unit tests collect and pass in a clean environment.
- [ ] Lap inserts actual chunks into Phat's `document_chunks`.
- [ ] Lap retrieves actual chunks through pgvector.
- [ ] Retrieval output contains page-aware citations.
- [ ] Lap inserts a RAG query log using Phat's canonical fields.
- [ ] `v_rag_daily_metrics` returns a row from that query log.
- [ ] Lap replaces/archive legacy files and commits the cleanup.

Until the unchecked items are complete, the mapping is not an end-to-end
execution proof.
