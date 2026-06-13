# Ingestion DB Handoff for Phat

Owner: Duy  
Consumer: Phat - Database, Quality, and Analytics Owner  
Purpose: Map Duy's ingestion outputs to Phat's schema_v2 database tables.

## Why This Contract Exists

Phat's Week 3 schema_v2 must store real outputs from Duy's ingestion pipelines. This handoff defines exactly which fields Duy produces and where they should be stored in PostgreSQL.

The main tables affected by Duy's work are:

- `sources`
- `documents`
- `document_pages`
- `structured_records`
- `ingestion_logs`
- `pipeline_runs`

## Current Duy Outputs

| Source type | Log file | Raw output | Staging output | Clean output |
| --- | --- | --- | --- | --- |
| CSV | `logs/csv_ingestion_log.json` | `data/raw/csv/sample_raw.csv` | `data/staging/csv/sample_staging.csv` | `data/clean/csv/sample_clean.csv` |
| Excel | `logs/excel_ingestion_log.json` | `data/raw/excel/inventory_raw.xlsx` | `data/staging/excel/sample_excel_staging.csv` | `data/clean/excel/sample_excel_clean.csv` |
| API JSON | `logs/api_ingestion_log.json` | `data/raw/api/sample_api_response.json` | `data/staging/api/api_staging.csv` | `data/clean/api/api_clean.csv` |
| PDF | `logs/pdf_ingestion_log.json` | `data/raw/pdf/sample_pdf_raw.pdf` | `data/staging/pdf/sample_pdf_text.txt` | `null` |

PDF ingestion also produces page-level JSONL for Lap and Phat:

```text
data/staging/pdf/document_pages.jsonl
```

## sources Table Mapping

Recommended `sources` fields for Duy's inventory and ingestion metadata:

| Duy field | Database column | Notes |
| --- | --- | --- |
| `source_name` | `sources.source_name` | Example: `sales_csv`, `customer_api`, `sample_pdf` |
| `source_type` | `sources.source_type` | `csv`, `excel`, `api`, `pdf`, `database`, `streaming` |
| `input_path_or_url` | `sources.source_location` | Project-relative path or URL |
| Inventory `file_format` | `sources.file_format` | Example: `csv`, `xlsx`, `json`, `pdf` |
| Inventory `ingestion_method` | `sources.ingestion_method` | Example: `pandas_csv`, `openpyxl`, `pymupdf` |
| Inventory `frequency` | `sources.frequency` | Example: `daily`, `weekly`, `on_demand` |
| Inventory `owner` | `sources.owner` | Example: `Nguyen Minh Duy` |
| Inventory `status` | `sources.status` | `proposed`, `sample_available`, `ready`, `blocked` |
| Inventory `authentication_required` | `sources.authentication_required` | Boolean |
| Inventory `schema_version` | `sources.schema_version` | Example: `v1.0` |
| Inventory `sample_available` | `sources.sample_available` | Boolean |
| Inventory `expected_volume` | `sources.expected_volume` | `low`, `medium`, `high` |
| Inventory `sensitive_data_flag` | `sources.sensitive_data_flag` | Boolean |
| Inventory `downstream_consumer` | `sources.downstream_consumer` | Example: `dashboard`, `rag`, `prediction` |

## ingestion_logs Table Mapping

This should match Duy's JSON logs.

| Duy log field | Database column | Required |
| --- | --- | --- |
| `run_id` | `ingestion_logs.run_id` | Yes |
| resolved source FK | `ingestion_logs.source_id` | Yes |
| resolved pipeline FK | `ingestion_logs.pipeline_run_id` | Optional |
| `source_type` | `ingestion_logs.source_type` | Yes |
| `input_path_or_url` | `ingestion_logs.input_path_or_url` | Yes |
| `status` | `ingestion_logs.status` | Yes |
| `records_read` | `ingestion_logs.records_read` | Yes |
| `records_valid` | `ingestion_logs.records_valid` | Yes |
| `records_invalid` | `ingestion_logs.records_invalid` | Yes |
| `error_message` | `ingestion_logs.error_message` | Yes |
| `raw_output_path` | `ingestion_logs.raw_output_path` | Yes |
| `staging_output_path` | `ingestion_logs.staging_output_path` | Yes |
| `clean_output_path` | `ingestion_logs.clean_output_path` | Yes |
| `start_time` | `ingestion_logs.started_at` | Yes |
| `end_time` | `ingestion_logs.ended_at` | Yes |

Additional log fields can be stored in a JSONB column such as `ingestion_logs.log_metadata`:

- `duplicate_rows_removed`
- `required_missing_values_removed`
- `optional_missing_values`
- `missing_required_columns`
- `required_fields`
- `sheet_names`
- `selected_sheet`
- `page_count`
- `extracted_character_count`
- `empty_pages`

## documents Table Mapping

Used mainly for file/document sources such as PDF, TXT, DOCX, and future document uploads.

| Duy output | Database column | Notes |
| --- | --- | --- |
| resolved source FK | `documents.source_id` | From `sources.id` |
| file name from `input_path_or_url` | `documents.file_name` | Example: `big-data-engineer2 - Template 16 .pdf` |
| file extension | `documents.file_type` | Example: `pdf` |
| local file size | `documents.file_size_bytes` | Bytes |
| future hash | `documents.file_hash_sha256` | Duy can add SHA-256 in next iteration |
| `raw_output_path` | `documents.raw_path` | Raw document path |
| `staging_output_path` | `documents.staging_text_path` | Extracted text path |
| `page_count` | `documents.page_count` | From `pdf_metadata.json` |
| `extracted_character_count` | `documents.character_count` | From `pdf_metadata.json` |
| full PDF metadata | `documents.document_metadata` | JSONB |
| mapped status | `documents.processing_status` | `uploaded`, `parsed`, `failed`, `needs_review` |

## document_pages Table Mapping

Duy's PDF extraction can populate page-level text for Lap's chunking.

| Duy output | Database column | Notes |
| --- | --- | --- |
| resolved document FK | `document_pages.document_id` | From `documents.id` |
| page number | `document_pages.page_number` | Starts at 1 |
| extracted text per page | `document_pages.page_text` | From `sample_pdf_text.txt` |
| page text length | `document_pages.character_count` | `len(page_text)` |
| empty page flag | `document_pages.is_empty` | True if page text is empty |

Recommended parser contract:

```json
{
  "document_id": 1,
  "page_number": 1,
  "page_text": "Extracted page text...",
  "character_count": 2664,
  "is_empty": false
}
```

The concrete JSONL contract is defined in `week2/docs/document_pages_jsonl_contract_for_lap.md`.

## structured_records Table Mapping

Used for CSV, Excel, and API tabular outputs.

| Duy output | Database column | Notes |
| --- | --- | --- |
| resolved source FK | `structured_records.source_id` | From `sources.id` |
| one clean row | `structured_records.record_data` | JSONB row payload |
| `clean_output_path` | `structured_records.clean_output_path` | Optional if table stores path-level references |
| source type | `structured_records.record_type` | `csv`, `excel`, `api` |
| validation status | `structured_records.status` | `valid`, `invalid`, `needs_review` |

For MVP, Phat may either:

1. Store each clean row as one JSONB record in `structured_records`.
2. Store only dataset-level metadata and keep the CSV path in `clean_output_path`.

Option 1 is better for analytics and ML.

## pipeline_runs Table Mapping

| Duy pipeline value | Database column | Notes |
| --- | --- | --- |
| pipeline name | `pipeline_runs.pipeline_name` | Example: `csv_ingestion`, `pdf_extraction` |
| source type | `pipeline_runs.pipeline_type` | `csv`, `excel`, `api`, `pdf` |
| `start_time` | `pipeline_runs.started_at` | From ingestion log |
| `end_time` | `pipeline_runs.ended_at` | From ingestion log |
| `status` | `pipeline_runs.status` | `success`, `failed`, `partial_success` |
| summary counts | `pipeline_runs.run_metadata` | JSONB |

## Status Mapping

| Duy status | Database status | UI status |
| --- | --- | --- |
| `success` | `success` | `ready` |
| `partial_success` | `partial_success` | `partial_success` |
| `failed` | `failed` | `failed` |

## Required Schema Support From Phat

Duy needs Phat's schema_v2 to support:

- `sources.source_name`
- `sources.source_type`
- `sources.source_location`
- `sources.schema_version`
- `documents.raw_path`
- `documents.staging_text_path`
- `documents.file_hash_sha256`
- `documents.page_count`
- `documents.character_count`
- `document_pages.page_text`
- `ingestion_logs.run_id`
- `ingestion_logs.records_read`
- `ingestion_logs.records_valid`
- `ingestion_logs.records_invalid`
- `ingestion_logs.raw_output_path`
- `ingestion_logs.staging_output_path`
- `ingestion_logs.clean_output_path`
- `ingestion_logs.log_metadata JSONB`

## Example Insert Flow

```text
1. Upsert source into sources.
2. Insert pipeline run into pipeline_runs.
3. Insert ingestion log into ingestion_logs.
4. For PDF: insert document into documents.
5. For PDF: insert page text into document_pages.
6. For CSV/Excel/API: insert clean rows or dataset reference into structured_records.
```

## Notes for Phat

- Store project-relative paths exactly as Duy logs them.
- Keep `run_id` as a stable external identifier even if `ingestion_logs.id` is the database primary key.
- Use JSONB for flexible metadata because each source type has different extra fields.
- Keep `document_pages` separate from `document_chunks`; pages come from Duy, chunks come from Lap.
- Use `document_chunks.embedding vector(384)` for Lap's MVP embedding model.
