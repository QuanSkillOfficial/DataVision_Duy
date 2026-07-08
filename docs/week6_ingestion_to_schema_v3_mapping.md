# Week 6 Duy -> Phat Database Mapping

Owner: Nguyen Minh Duy  
Partner: Phat - Database / PostgreSQL / pgvector Owner  
Reference schema: `DataVision_Phat/week6/database/schema_v4.sql`

## Purpose

This file maps Duy's Week 6 ingestion outputs to Phat's PostgreSQL schema so both sides can prove the real integration path:

```text
Duy ingestion outputs
  -> Phat PostgreSQL tables
  -> Phat analytics views
  -> Lap RAG / Tuong prediction / Phi-Hung UI
```

## Phat Files Reviewed

| Phat file | Why it matters |
| --- | --- |
| `DataVision_Phat/week6/database/schema_v4.sql` | Final table and column names for DB insertion |
| `DataVision_Phat/week6/database/load_data.py` | Shows Phat's current CSV/JSONL loading expectations |
| `DataVision_Phat/week6/database/validate_ingestion_data.sql` | Defines expected counts and integrity checks |
| `DataVision_Phat/week6/database/validation_queries_v2.sql` | Defines Week 6 validation queries |
| `DataVision_Phat/week6/database/analytics_views_v3.sql` | Defines dashboard views powered by Duy data |
| `DataVision_Phat/week6/docs/duy_output_to_db_loading_contract_v2.md` | Direct Duy + Phat loading contract |
| `DataVision_Phat/week6/outputs/ingestion_data_Duy/*.json` | Actual Duy ingestion rows exported from Phat |
| `DataVision_Phat/week6/outputs/document_chunk_data_Lap/*.json` | Actual Lap pgvector chunk rows tied to Duy's PDF document |
| `DataVision_Phat/week6/outputs/prediction_log_data_Tuong/*.json` | Actual Tuong prediction log rows tied to Duy payloads |
| `DataVision_Phat/week6/outputs/dashboard_view_samples_PhiHung/*.json` | Dashboard view samples generated after loading Duy/Lap/Tuong data |

## Insert Order

Use this order because later tables depend on IDs from earlier tables:

```text
sources
  -> pipeline_runs
  -> ingestion_logs
  -> documents
  -> document_pages
  -> structured_records
```

For PDF:

```text
Duy document_id / document_external_id
  -> documents.document_external_id
  -> documents.id
  -> document_pages.document_id
```

Never insert Duy's string document ID directly into `document_pages.document_id`.

## Expected Row Counts

After loading the latest Duy successful runs, Phat validation should see:

| Target | Expected count |
| --- | ---: |
| `sources` | 4 |
| `pipeline_runs` | 4 if Duy loads one run per source, or 1 if Phat groups the batch |
| `ingestion_logs` | 4 |
| `documents` | 1 |
| `document_pages` | 36 |
| `structured_records` | 11,524 |

Source-level valid counts:

| Source | Type | Valid rows/pages |
| --- | --- | ---: |
| `superstore_sales_csv` | `csv` | 9,994 |
| `product_sales_region_excel` | `excel` | 1,500 |
| `dummyjson_products_api` | `api` | 30 |
| `dataflow_technical_report_pdf` | `pdf` | 36 pages |

Total `records_read` / `records_valid` in `ingestion_logs` should be:

```text
9994 + 1500 + 30 + 36 = 11560
```

## Latest Phat Output Evidence

Reviewed Phat Week 6 output folder on 2026-07-08:

| Evidence | Path | Current result |
| --- | --- | --- |
| Duy sources loaded | `DataVision_Phat/week6/outputs/ingestion_data_Duy/sources_202607051438.json` | 4 sources |
| Duy ingestion logs loaded | `DataVision_Phat/week6/outputs/ingestion_data_Duy/ingestion_logs_202607051438.json` | 4 successful ingestion logs |
| Duy PDF document loaded | `DataVision_Phat/week6/outputs/ingestion_data_Duy/documents_202607051439.json` | 1 document, `document_external_id=doc_dataflow_technical_report` |
| Duy document pages loaded | `DataVision_Phat/week6/outputs/ingestion_data_Duy/document_pages_202607051442.json` | 36 pages |
| Duy structured records loaded | `DataVision_Phat/week6/outputs/ingestion_data_Duy/structured_records_202607051442.json` | Sample export from structured records |
| Lap chunks loaded | `DataVision_Phat/week6/outputs/document_chunk_data_Lap/document_chunks_202607071256.json` | Chunks use `document_id=1`, 384-dim embeddings, `document_external_id` in metadata |
| Tuong predictions loaded | `DataVision_Phat/week6/outputs/prediction_log_data_Tuong/prediction_logs_202607071251.json` | 10 prediction logs |
| Phi/Hung dashboard overview | `DataVision_Phat/week6/outputs/dashboard_view_samples_PhiHung/v_dashboard_overview_202607071300.json` | 4 sources, 1 document, 4 successful ingestions, 10 predictions |

Important resolved ID mapping from Phat output:

| Duy identifier | Phat resolved ID |
| --- | --- |
| `source_name=superstore_sales_csv` | `source_id=1` |
| `source_name=dataflow_technical_report_pdf` | `source_id=2` |
| `source_name=dummyjson_products_api` | `source_id=3` |
| `source_name=product_sales_region_excel` | `source_id=4` |
| `document_external_id=doc_dataflow_technical_report` | `document_db_id=1` |

Tuong prediction log integration result from Phat output:

```text
prediction_logs: 10
source_id resolved: 10/10
document_id resolved: 1/10
```

Only `doc_dataflow_technical_report` resolves to `documents.id=1`. The other 9 Tuong payloads are synthetic/test-case document IDs, so `prediction_logs.document_id = NULL` is expected.

## Table Mapping

### `sources`

Phat constraint:

```sql
name VARCHAR(255) NOT NULL UNIQUE
```

Duy writer behavior:

```text
insert_or_get_source()
  -> INSERT ... ON CONFLICT (name) DO UPDATE
  -> RETURNING id
```

| Duy field | Phat column | Example |
| --- | --- | --- |
| `source_name` | `sources.name` | `superstore_sales_csv` |
| `source_type` | `sources.source_type` | `csv`, `excel`, `api`, `pdf` |
| `source_type` | `sources.source_format` | `csv`, `xlsx`, `json`, `pdf` |
| `input_path_or_url` | `sources.source_path` | `week2/data/sample_inputs/Superstore.csv` |
| API URL source | `sources.url` | `https://dummyjson.com/products` |
| `owner` | `sources.owner_name` | `Nguyen Minh Duy` |
| fixed value | `sources.sample_available` | `true` |
| fixed value | `sources.status` | `active` |

### `pipeline_runs`

Phat schema_v4 columns:

```sql
id, run_name, start_time, end_time, status, created_at
```

Important: Phat schema does **not** currently include `run_id`, `pipeline_name`, `started_at`, `ended_at`, or `run_metadata`.

| Duy field | Phat column | Example |
| --- | --- | --- |
| `source_name + "_" + run_id` | `pipeline_runs.run_name` | `superstore_sales_csv_10ed...` |
| `start_time` | `pipeline_runs.start_time` | `2026-07-04T04:16:15.862044+00:00` |
| `end_time` | `pipeline_runs.end_time` | `2026-07-04T04:16:16.143772+00:00` |
| `status` | `pipeline_runs.status` | `success` |

### `ingestion_logs`

| Duy field | Phat column | Notes |
| --- | --- | --- |
| `run_id` | `ingestion_logs.run_id` | Duy ingestion UUID |
| returned `sources.id` | `ingestion_logs.source_id` | DB FK |
| returned `pipeline_runs.id` | `ingestion_logs.pipeline_run_id` | DB FK |
| `source_type` | `ingestion_logs.source_type` | `csv`, `excel`, `api`, `pdf` |
| `input_path_or_url` | `ingestion_logs.input_path_or_url` | Project-relative path or URL |
| `status` | `ingestion_logs.status` | Allowed: `success`, `failed`, `partial_success`, `running` |
| `records_read` | `ingestion_logs.records_read` | Required by Phat validation |
| `records_valid` | `ingestion_logs.records_valid` | Required by Phat validation |
| `records_invalid` | `ingestion_logs.records_invalid` | Required by Phat validation |
| `error_message` | `ingestion_logs.error_message` | `null` on success |
| `raw_output_path` | `ingestion_logs.raw_output_path` | Project-relative path |
| `staging_output_path` | `ingestion_logs.staging_output_path` | Project-relative path |
| `clean_output_path` | `ingestion_logs.clean_output_path` | Project-relative path |
| `data_quality.data_quality_score` | `ingestion_logs.data_quality_score` | Required for successful runs |
| `data_quality.required_missing_values` | `ingestion_logs.required_missing_values` | JSONB |
| `data_quality.optional_missing_values` | `ingestion_logs.optional_missing_values` | JSONB |
| `data_quality.duplicate_count` | `ingestion_logs.duplicate_count` | Integer |
| `logs/manifests/<run_id>_manifest.json` | `ingestion_logs.manifest_path` | Project-relative path |
| `start_time` | `ingestion_logs.started_at` | Timestamp |
| `end_time` | `ingestion_logs.ended_at` | Timestamp |

Phat validation requires:

```text
records_read = records_valid + records_invalid
data_quality_score is not null for success / partial_success
run_id is not null
ended_at >= started_at
```

### `documents`

Only the PDF source creates a document row in Duy's Week 6 scope.

| Duy field | Phat column | Example |
| --- | --- | --- |
| returned `sources.id` | `documents.source_id` | Integer FK |
| `pdf_metadata.document_id` | `documents.document_external_id` | `doc_dataflow_technical_report` |
| `pdf_metadata.file_name` | `documents.file_name` | `DataFlow_Technical_Report.pdf` |
| fixed value | `documents.file_type` | `pdf` |
| `pdf_metadata.file_size_bytes` | `documents.file_size_bytes` | `2857707` |
| `file_manifest.file_hash_sha256` | `documents.file_hash_sha256` | SHA256 hash |
| `pdf_metadata.raw_output_path` | `documents.raw_path` | Raw PDF output path |
| `pdf_metadata.staging_output_path` | `documents.staging_text_path` | Extracted text path |
| `pdf_metadata.page_count` | `documents.page_count` | `36` |
| `pdf_metadata.total_characters` | `documents.character_count` | `129028` |
| full PDF metadata | `documents.document_metadata` | JSONB |
| fixed value after extraction | `documents.processing_status` | `extracted` |

### `document_pages`

Duy input file:

```text
week2/data/staging/pdf/document_pages.jsonl
outputs/rag_handoff/document_pages.jsonl
```

Each JSONL row uses Duy's external document ID. Before insert, resolve:

```sql
SELECT id FROM documents WHERE document_external_id = 'doc_dataflow_technical_report';
```

Then insert the returned integer ID into `document_pages.document_id`.

| Duy JSONL field | Phat column |
| --- | --- |
| resolved `documents.id` | `document_pages.document_id` |
| `page_number` | `document_pages.page_number` |
| `text` | `document_pages.page_text` |
| `character_count` | `document_pages.character_count` |
| `is_empty` | `document_pages.is_empty` |

Expected:

```text
36 rows
0 empty pages
0 orphaned pages
```

### `structured_records`

Duy inputs:

```text
week2/data/clean/csv/superstore_clean.csv
week2/data/clean/excel/product_sales_region_clean.csv
week2/data/clean/api/dummyjson_products_clean.csv
```

Phat schema_v4 columns:

```sql
id, source_id, record_data, status, created_at
```

Important: Phat schema uses `structured_records.status`, not `processing_status`.

| Duy input | Phat column |
| --- | --- |
| returned `sources.id` | `structured_records.source_id` |
| clean CSV row as JSON | `structured_records.record_data` |
| fixed value | `structured_records.status = 'clean'` |

Expected:

```text
9994 + 1500 + 30 = 11524 structured_records
```

## Current Duy Implementation

| File | Status |
| --- | --- |
| `data_engineering/storage/postgres_writer.py` | Aligned to Phat schema_v4 columns |
| `scripts/load_ingestion_outputs_to_postgres.py` | Supports dry-run and real `--write-db` mode |
| `logs/db_load_dry_run/duy_to_phat_db_load_plan.json` | Shows the latest insert plan |
| `docs/week6_duy_to_phat_db_load_result.md` | Human-readable integration result |

## Known Phat-Side Notes

The reviewed `schema_v4.sql` contains a likely syntax issue in `prediction_logs`:

```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
CONSTRAINT chk_prediction_status
```

There should be a comma before `CONSTRAINT`. This does not block Duy's ingestion mapping directly, but Phat should fix it before running `schema_v4.sql` or `setup_database_v2.sql` from scratch.

Current `prediction_logs` schema also includes:

```text
document_external_id
ingestion_run_id
```

These fields are useful for Tuong's prediction logs and should remain aligned with Duy's payload fields.

## Acceptance Checklist

Phat should confirm:

```text
[ ] sources has 4 Duy sources
[ ] ingestion_logs has 4 Duy run logs
[ ] sum(records_read) = 11560
[ ] sum(records_valid) = 11560
[ ] avg(data_quality_score) ~= 99.63
[ ] documents has document_external_id = doc_dataflow_technical_report
[ ] document_pages has 36 rows and 0 empty pages
[ ] structured_records has 11524 rows
[ ] no orphaned document_pages
[ ] no orphaned structured_records
[ ] v_dashboard_overview returns rows
[ ] v_data_quality_dashboard returns Duy quality scores
```
