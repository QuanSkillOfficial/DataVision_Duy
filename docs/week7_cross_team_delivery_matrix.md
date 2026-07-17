# Week 7 Cross-Team Delivery Matrix

## Working rule

Every handoff has four parts:

1. input file and exact path;
2. required fields and ID semantics;
3. output file and exact path;
4. command or query proving the output is usable.

An output is not considered complete because a file exists. The owner must
return the proof file or terminal result listed below.

## Duy -> Phat

### Files to send

```text
logs/runs/*.json
logs/ingestion_runs.jsonl
logs/manifests/*_manifest.json
outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
outputs/rag_handoff/pdf_metadata.json
outputs/rag_handoff/week7_rag_handoff_manifest.json
outputs/prediction_payloads/tuong_week7_prediction_payloads.json
data_engineering/storage/postgres_writer.py
scripts/load_ingestion_outputs_to_postgres.py
docs/week7_duy_phat_real_db_loading_result.md
```

### Input contract

| Table | Duy field | Phat mapping |
| --- | --- | --- |
| `sources` | `source_name`, `source_type`, `owner` | unique source row; return integer `source_id` |
| `pipeline_runs` | `run_id`, status, timestamps | run UUID; idempotent by run ID |
| `ingestion_logs` | counts, paths, hash, DQ fields | FK `source_id` and run reference |
| `documents` | `document_external_id`, file metadata | insert/get integer `documents.id` |
| `document_pages` | page number, text, char/word counts | use integer `documents.id` |
| `structured_records` | clean CSV/API/Excel rows | use integer `source_id` |

### Phat must return

```text
source_id for each source_name
document_db_id for doc_dataflow_technical_report
schema version actually executed
SQL counts for six ingestion tables
logs/db_validation/duy_data_load_counts.json
```

### Acceptance query

```sql
SELECT COUNT(*) FROM sources;
SELECT COUNT(*) FROM pipeline_runs;
SELECT COUNT(*) FROM ingestion_logs;
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM document_pages;
SELECT COUNT(*) FROM structured_records;
```

## Duy -> Lap

### Files to send

```text
outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
outputs/rag_handoff/pdf_metadata.json
outputs/rag_handoff/week7_rag_handoff_manifest.json
docs/week7_duy_to_lap_rag_handoff.md
```

### Required page fields

```json
{
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": null,
  "source_id": null,
  "file_name": "DataFlow_Technical_Report.pdf",
  "page_number": 1,
  "text": "...",
  "char_count": 3500,
  "word_count": 520,
  "ingestion_run_id": "uuid"
}
```

`document_db_id` and `source_id` remain null until Phat confirms a real DB
load. Lap must fail clearly rather than insert a null integer foreign key.

### Lap must return

```text
outputs/rag/week7_pgvector_insert_result.json
outputs/rag/week7_pgvector_query_result.json
outputs/rag/week7_rag_query_log_payload.json
outputs/ui_fixtures/lap_rag_response_real.json
```

The result must show `chunk_id`, integer `document_id`, `page_number`,
384-dimensional embeddings, `similarity_score`, and citation fields.

## Duy -> Tuong

### Files to send

```text
outputs/prediction_payloads/tuong_week7_prediction_payloads.json
outputs/prediction_payloads/week7/*.json
docs/week7_duy_to_tuong_prediction_payload_contract.md
docs/week7_duy_to_tuong_additional_prediction_payloads.md
```

There are 20 test payloads: 10 baseline and 10 additional cases. They include
real PDF sections, structured-data summaries, a short-text gate, empty text,
unknown file type, missing external ID and invalid file size.

### Required ID semantics

```text
source_id             = integer database source ID or null
source_name           = stable source key
document_external_id  = stable string document key
document_db_id        = integer database document ID or null
ingestion_run_id      = Duy run UUID
```

### Tuong must return

```text
outputs/week7_duy_prediction_results.json
outputs/db_integration/week7_prediction_log_payloads.json
outputs/ui_fixtures/tuong_prediction_batch_response.json
outputs/ui_fixtures/tuong_prediction_review_queue_sample.json
scripts/week7_prediction_ci_smoke_test.py
```

Every item must use one shape and one of:
`accepted`, `needs_review`, `waiting_for_source`, `failed`.
Failed validation must not disappear from the batch.

## Duy -> Phi/Hung

### Files to send

```text
outputs/ui_fixtures/duy_week7_database_enriched_summary.json
outputs/ui_fixtures/duy_data_quality_summary.json
outputs/ui_fixtures/duy_pdf_document_summary.json
outputs/rag_handoff/week7_rag_handoff_manifest.json
docs/week7_duy_to_phi_hung_ui_fixture_contract.md
```

### UI fields

The dashboard must be able to display:

```text
total_sources
total_runs
successful_runs
total_records_read
total_records_valid
average_data_quality_score
latest_document.document_external_id
latest_document.document_db_id
latest_document.file_hash_sha256
handoff_paths
```

### Phi/Hung must return

```text
demo/fixtures/week7/
demo/services/fixture_validator.py
tests/test_week7_fixture_validation.py
scripts/week7_ui_ci_smoke_test.py
docs/week7_ui_ci_smoke_test_result.md
```

The UI must show pending database IDs honestly and must not label the backend
stub as production.

## Phat -> Duy/Lap/Tuong/Phi-Hung

Phat must provide the shared database boundary:

```text
week7/database/schema_v4_fixed.sql
week7/database/setup_database_v3.sql
docker-compose.db.yml
week7/database/ci_database_smoke_test.py
week7/database/validation_queries_v3.sql
week7/outputs/db_validation/duy_data_load_counts.json
week7/outputs/db_validation/rag_pgvector_counts.json
week7/outputs/db_validation/prediction_log_counts.json
week7/outputs/dashboard_view_samples/*.json
```

Without these files, Duy can only provide dry-run plans and contract checks.

## Lap -> Phat/Tuong/Phi-Hung

Lap must return:

```text
document_chunks insert count
top-k retrieval result
rag_query_logs insert proof
v_rag_daily_metrics result
DataFlow citation fixture
safe document-type filter metadata behavior
```

## Tuong -> Phat/Lap/Phi-Hung

Tuong must return:

```text
prediction log field mapping
status distribution
review queue rows
manual review flag
safe RAG metadata rule
feedback payload contract
```

## Phi/Hung -> whole team

Phi/Hung must return:

```text
validated Week 7 fixtures
UI smoke test result
backend route contract
backend-client error envelope behavior
Streamlit fixture-mode proof
CI job and staging demo runbook
```

## Shared completion gate

The team can call the Week 7 mapping complete only when all of these are true:

- the two Compose files pass `docker compose config --quiet`;
- each module has a fast smoke test;
- the database starts from an empty volume with Phat's schema;
- Duy counts, Lap retrieval, Tuong review queue and UI fixtures are queryable;
- `.github/workflows/ci.yml` runs the available jobs and conditionally runs
  owner jobs after merge;
- `docs/week7_deployment_runbook.md` is followed without undocumented manual
  fixes.
