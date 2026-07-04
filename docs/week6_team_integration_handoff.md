# Week 6 Team Integration Handoff

Owner: Nguyen Minh Duy  
Role: Data Engineering / Ingestion Owner  
Purpose: Define what Duy provides to each team member and what Duy needs back to complete Week 6 integration testing.

## Week 6 Main Goal

The main risk is that every module works separately, but the full platform has not been tested together.

This week should focus on:

```text
connect
insert
query
retrieve
predict
display
test
```

Duy's ingestion layer is the entry point of the platform. The goal is to make real ingestion outputs usable by:

```text
Duy ingestion
  -> Phat PostgreSQL
  -> Lap RAG
  -> Tuong prediction
  -> Phi/Hung dashboard, suggestions, and reports
```

## Outputs Duy Provides

### 1. For Phat - Database / PostgreSQL

Duy provides database-ready ingestion outputs for Phat to load into PostgreSQL.

| File / Folder | Purpose |
| --- | --- |
| `logs/runs/*.json` | One run-specific ingestion log per source |
| `logs/ingestion_runs.jsonl` | Append-only ingestion run history |
| `logs/manifests/*_manifest.json` | File manifests with SHA256 hashes |
| `logs/db_load_dry_run/duy_to_phat_db_load_plan.json` | Dry-run database loading plan |
| `week2/data/clean/csv/superstore_clean.csv` | Clean CSV structured records |
| `week2/data/clean/excel/product_sales_region_clean.csv` | Clean Excel structured records |
| `week2/data/clean/api/dummyjson_products_clean.csv` | Clean API structured records |
| `week2/logs/pdf_metadata.json` | PDF metadata for `documents` table |
| `week2/data/staging/pdf/document_pages.jsonl` | PDF page-level text for `document_pages` table |
| `outputs/rag_handoff/document_pages.jsonl` | RAG-ready copy of page-level document text |
| `docs/week6_ingestion_to_schema_v3_mapping.md` | Mapping from Duy outputs to Phat schema |
| `docs/week6_database_loading_result.md` | DB dry-run result and real-run status |

Expected target tables:

```text
sources
pipeline_runs
ingestion_logs
documents
document_pages
structured_records
```

Important ID rules:

| Field | Meaning |
| --- | --- |
| `source_id` | PostgreSQL `sources.id`, created by Phat DB |
| `ingestion_run_id` / `run_id` | Duy ingestion execution UUID |
| `document_external_id` | Duy document key, e.g. `doc_dataflow_technical_report` |
| `document_db_id` | PostgreSQL `documents.id`, created by Phat DB |

Do not use `ingestion_run_id` as `source_id`.

### 2. For Lap - RAG / Embeddings / Retrieval

Duy provides a real PDF handoff package for Lap's chunking, embedding, pgvector insertion, retrieval evaluation, and citation generation.

| File | Purpose |
| --- | --- |
| `outputs/rag_handoff/document_pages.jsonl` | Page-level text records |
| `outputs/rag_handoff/pdf_metadata.json` | PDF metadata |
| `outputs/rag_handoff/rag_handoff_summary.md` | Human-readable handoff summary |
| `outputs/rag_handoff/rag_handoff_manifest.json` | Machine-readable handoff manifest |
| `docs/week6_document_pages_for_rag_confirmed.md` | Confirmation of RAG readiness |

Real DataFlow PDF statistics:

| Metric | Value |
| --- | --- |
| `document_external_id` | `doc_dataflow_technical_report` |
| `file_name` | `DataFlow_Technical_Report.pdf` |
| `page_count` | `36` |
| `non_empty_pages` | `36` |
| `empty_pages` | `0` |
| `total_characters` | `129028` |

Expected flow:

```text
outputs/rag_handoff/document_pages.jsonl
  -> Lap chunks
  -> Lap embeddings
  -> Phat document_chunks vector(384)
  -> Lap retrieval
  -> Phi/Hung citation cards
```

### 3. For Tuong - Prediction

Duy provides a real document classification payload from the DataFlow PDF.

| File | Purpose |
| --- | --- |
| `logs/prediction_payloads/duy_pdf_prediction_payload.json` | Tuong-ready prediction payload |
| `week2/docs/ingestion_to_prediction_contract.md` | Ingestion-to-prediction contract |
| `docs/week6_id_mapping_contract.md` | ID mapping rules |

Important payload fields:

```json
{
  "source_id": null,
  "source_name": "dataflow_technical_report_pdf",
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": null,
  "ingestion_run_id": "run-uuid",
  "file_name": "DataFlow_Technical_Report.pdf",
  "file_type": "pdf",
  "file_size": 2857707,
  "text_length": 129028,
  "num_pages": 36,
  "source_system": "manual_upload",
  "parsing_status": "ready"
}
```

Before database loading:

```text
source_id = null
document_db_id = null
```

After Phat database loading:

```text
source_id = sources.id
document_db_id = documents.id
```

### 4. For Phi/Hung - UI / Suggestions / Reports

Duy provides real ingestion fixtures for Dashboard, Suggestions, and Reports.

| File | Purpose |
| --- | --- |
| `outputs/ui_fixtures/duy_latest_ingestion_summary.json` | Main UI ingestion fixture |
| `outputs/ui_fixtures/duy_data_quality_summary.json` | Data quality source summary |
| `outputs/ui_fixtures/duy_pdf_document_summary.json` | PDF document summary |
| `logs/ui_fixtures/duy_ingestion_dashboard_fixture.json` | Backward-compatible UI fixture |
| `docs/week6_phi_hung_ui_fixture_contract.md` | UI fixture contract |

Fields available for UI:

```text
run_id
ingestion_run_id
source_id
source_name
source_type
status
records_read
records_valid
records_invalid
data_quality_score
file_hash_sha256
raw_output_path
staging_output_path
clean_output_path
document_external_id
document_db_id
document_pages_jsonl_path
```

Expected UI usage:

| UI Page | Duy fields used |
| --- | --- |
| Dashboard | run status, source count, record counts, data quality score |
| Suggestions | invalid records, low quality signals, missing documents |
| Reports | ingestion evidence, file hash, output paths |
| Prediction page | document external ID, source name, ingestion run ID |
| Chatbot/RAG page | document pages path and PDF metadata |

## Inputs Duy Needs From Others

### 1. From Phat

Duy needs Phat's final database details to run real PostgreSQL loading.

| Needed from Phat | Why Duy needs it |
| --- | --- |
| Final `schema_v3.sql` or `schema_v4.sql` | To align insert statements |
| Database host, port, database, user, password | To run `--write-db` |
| `sources` table definition | To insert/get `source_id` |
| Unique constraint on `sources.name` | To make `insert_or_get_source()` safe |
| `pipeline_runs` table definition | To insert run metadata |
| `ingestion_logs` table definition | To insert run logs and data quality fields |
| `documents.document_external_id` support | To map Duy document string ID |
| `document_pages` table definition | To insert PDF page text |
| `structured_records` JSONB format | To insert CSV/API/Excel clean rows |
| Validation queries | To prove rows were inserted correctly |

Questions for Phat:

```text
1. Is sources.name UNIQUE?
2. Does documents have document_external_id?
3. Does ingestion_logs include data_quality_score, manifest_path, duplicate_count?
4. Does ingestion_logs include pipeline_run_id?
5. What JSONB format should structured_records.record_data use?
```

### 2. From Lap

Duy needs Lap's final RAG input requirements.

| Needed from Lap | Why Duy needs it |
| --- | --- |
| Final `document_pages.jsonl` required fields | To keep PDF extraction RAG-ready |
| Chunk ID format | To align document/page/chunk IDs |
| Citation metadata requirements | To include fields needed by UI |
| Empty page handling | To decide whether to keep or skip empty pages |
| Maximum page text length, if any | To avoid oversized chunking inputs |
| RAG response fixture | To confirm UI/report compatibility |

Questions for Lap:

```text
1. Is page_number expected to start from 1?
2. Should chunk_id format be doc_dataflow_technical_report_page_1_chunk_000?
3. Which metadata fields are required: file_name, page_number, source, document_external_id?
4. Should empty pages be skipped or stored with is_empty=true?
```

### 3. From Tuong

Duy needs Tuong's final prediction input contract.

| Needed from Tuong | Why Duy needs it |
| --- | --- |
| Required prediction input fields | To produce correct payloads |
| Minimum `extracted_text` length | To avoid low-quality prediction inputs |
| Accepted `file_type` values | To standardize file metadata |
| Batch payload format | To support multi-document prediction |
| Status values | To align with UI and database |
| Prediction result sample | To verify end-to-end prediction flow |

Questions for Tuong:

```text
1. Is source_id=null acceptable before DB insert?
2. Is document_external_id the correct field name?
3. Should low confidence return needs_review?
4. Is minimum extracted_text length still 50 characters?
5. What batch payload shape do you expect from Duy?
```

### 4. From Phi/Hung

Duy needs Phi/Hung's final UI display requirements.

| Needed from Phi/Hung | Why Duy needs it |
| --- | --- |
| Final dashboard fields | To shape UI fixtures correctly |
| Data quality display format | To format scores and warnings |
| Status badge values | To align UI labels with backend statuses |
| Report evidence fields | To include enough source evidence |
| Suggestion signal fields | To support suggestion generation |
| Recent activity requirements | To expose run history correctly |

Questions for Phi/Hung:

```text
1. Is duy_latest_ingestion_summary.json enough for Dashboard?
2. Should data_quality_score be displayed as 99.63 or 99.63%?
3. Do Reports need raw/staging/clean paths?
4. Do Suggestions need required_missing_values and optional_missing_values?
5. Should file_hash_sha256 be shown in Dashboard or only Reports?
```

## Week 6 Priority Order

| Priority | Collaboration | Goal |
| --- | --- | --- |
| P0 | Duy + Phat | Prove real DB insert or dry-run with exact schema mapping |
| P0 | Duy + Lap | Confirm DataFlow PDF handoff works for chunking/RAG |
| P0 | Duy + Tuong | Run prediction on Duy real payload with correct ID semantics |
| P0 | Duy + Phi/Hung | Replace mock ingestion data with Duy real UI fixtures |
| P1 | All team | Align IDs: `source_id`, `document_external_id`, `document_db_id`, `ingestion_run_id` |
| P1 | All team | Run end-to-end smoke test |

## Current Duy Verification

Duy's project currently passes:

```text
Week 6 validation passed
Week 5 validation passed
Week 2 validation passed
pytest tests/data_tests/: 20 passed
```

End-to-end smoke test:

```powershell
python scripts/week6_end_to_end_smoke_test.py
```

Expected result:

```text
connect: true
insert: true
query: true
retrieve: true
predict: true
display: true
test: true
```

## Message Duy Can Send To Team

```text
Hi team, I prepared my Week 6 integration outputs.

For Phat:
- DB dry-run plan
- run logs
- manifests
- clean CSV/API/Excel outputs
- PDF metadata and document_pages.jsonl
- schema mapping document

For Lap:
- RAG handoff package with DataFlow PDF page-level text
- 36 pages, 36 non-empty pages, 129028 characters

For Tuong:
- corrected prediction payload
- source_id is null before DB insert
- ingestion_run_id is separate from source_id
- document_external_id is doc_dataflow_technical_report

For Phi/Hung:
- latest ingestion summary fixture
- data quality summary fixture
- PDF document summary fixture

Please confirm if my field names and output shapes match your Week 6 integration requirements.
```
