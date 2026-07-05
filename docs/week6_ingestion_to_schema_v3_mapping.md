# Week 6 Ingestion to Schema v3 Mapping

Owner: Nguyen Minh Duy  
Consumer: Phat - Database, Quality, and Analytics Owner

## Purpose

Map Duy's real ingestion outputs into Phat's PostgreSQL tables for Week 6 integration testing.

## Insert Order

```text
sources
  -> pipeline_runs
  -> ingestion_logs
  -> documents + document_pages for PDF
  -> structured_records for CSV / Excel / API
```

## Table Mapping

| Duy output | Phat table.column |
| --- | --- |
| `source_name` | `sources.name` |
| `source_type` | `sources.source_type` |
| `input_path_or_url` | `sources.source_path` or `sources.url` |
| `owner` | `sources.owner_name` |
| `run_id` | `pipeline_runs.run_id` |
| `source_type + "_ingestion"` | `pipeline_runs.pipeline_name` |
| `status` | `pipeline_runs.status`, `ingestion_logs.status` |
| `start_time` | `pipeline_runs.started_at`, `ingestion_logs.started_at` |
| `end_time` | `pipeline_runs.ended_at`, `ingestion_logs.ended_at` |
| `records_read` | `ingestion_logs.records_read` |
| `records_valid` | `ingestion_logs.records_valid` |
| `records_invalid` | `ingestion_logs.records_invalid` |
| `error_message` | `ingestion_logs.error_message` |
| `raw_output_path` | `ingestion_logs.raw_output_path` |
| `staging_output_path` | `ingestion_logs.staging_output_path` |
| `clean_output_path` | `ingestion_logs.clean_output_path` |
| `data_quality_score` | `ingestion_logs.data_quality_score` |
| `data_quality.required_missing_values` | `ingestion_logs.required_missing_values` |
| `data_quality.optional_missing_values` | `ingestion_logs.optional_missing_values` |
| `data_quality.duplicate_count` | `ingestion_logs.duplicate_count` |
| `logs/manifests/<run_id>_manifest.json` | `ingestion_logs.manifest_path` |
| `file_manifest.file_hash_sha256` | `documents.file_hash_sha256` if document source; otherwise report evidence |
| `pdf_metadata.document_id` | `documents.document_external_id` |
| `pdf_metadata.file_name` | `documents.file_name` |
| `pdf_metadata.file_size_bytes` | `documents.file_size_bytes` |
| `pdf_metadata.raw_output_path` | `documents.raw_path` |
| `pdf_metadata.staging_output_path` | `documents.staging_text_path` |
| `pdf_metadata.page_count` | `documents.page_count` |
| `pdf_metadata.total_characters` | `documents.character_count` |
| `document_pages.jsonl.page_number` | `document_pages.page_number` |
| `document_pages.jsonl.text` | `document_pages.page_text` |
| `document_pages.jsonl.character_count` | `document_pages.character_count` |
| `document_pages.jsonl.is_empty` | `document_pages.is_empty` |
| clean CSV/API/Excel row | `structured_records.record_data` |

## ID Rules

| Field | Rule |
| --- | --- |
| `source_id` | Returned by `sources.id` after `insert_or_get_source()` |
| `ingestion_run_id` | Duy `run_id`; do not use it as `source_id` |
| `document_external_id` | Duy string document ID, stored in `documents.document_external_id` |
| `document_db_id` | Phat integer `documents.id`, used as FK in `document_pages.document_id` |

## Current Duy Outputs

| Source | Valid records/pages | Main output |
| --- | ---: | --- |
| Superstore CSV | 9994 | `week2/data/clean/csv/superstore_clean.csv` |
| Product Sales Region Excel | 1500 | `week2/data/clean/excel/product_sales_region_clean.csv` |
| DummyJSON Products API | 30 | `week2/data/clean/api/dummyjson_products_clean.csv` |
| DataFlow Technical Report PDF | 36 pages | `outputs/rag_handoff/document_pages.jsonl` |
