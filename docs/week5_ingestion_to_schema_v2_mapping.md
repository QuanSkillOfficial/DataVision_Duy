# Week 5 Ingestion to PostgreSQL Schema Mapping

Owner: Nguyen Minh Duy  
Consumer: Phat - Database, Quality, and Analytics Owner

## Purpose

This document maps Duy's ingestion outputs to Phat's PostgreSQL schema_v2/schema_v3 direction. The goal is to make Duy's file-based ingestion outputs database-ready.

## Source Files

| Duy output | Database target | Purpose |
| --- | --- | --- |
| `logs/runs/<run_id>.json` | `ingestion_logs` | Store one detailed ingestion run |
| `logs/ingestion_runs.jsonl` | `pipeline_runs`, `ingestion_logs` | Append-only ingestion run history |
| `logs/manifests/<run_id>_manifest.json` | `documents`, `sources` | Store file hash, file size, raw path |
| `week2/data/staging/pdf/document_pages.jsonl` | `document_pages` | Store page-level PDF text |
| `week2/data/clean/csv/superstore_clean.csv` | `structured_records` | Store validated CSV records |
| `week2/data/clean/excel/product_sales_region_clean.csv` | `structured_records` | Store validated Excel records |
| `week2/data/clean/api/dummyjson_products_clean.csv` | `structured_records` | Store validated API records |
| `week2/data/clean/pdf/dataflow_pdf_pages_clean.csv` | `document_pages` or audit staging | Store non-empty page-level PDF extraction |

## Field Mapping

| Duy field | Phat table.column | Notes |
| --- | --- | --- |
| `run_id` | `ingestion_logs.run_id` | Stable run identifier |
| `source_name` | `sources.name`, `ingestion_logs.source_name` | Example: `superstore_sales_csv` |
| `source_type` | `sources.source_type`, `ingestion_logs.source_type` | `csv`, `excel`, `api`, `pdf` |
| `input_path_or_url` | `ingestion_logs.input_path_or_url` | Project-relative path or URL |
| `status` | `ingestion_logs.status` | `success`, `partial_success`, `failed`, `running` |
| `records_read` | `ingestion_logs.records_read` | Number of source rows/pages read |
| `records_valid` | `ingestion_logs.records_valid` | Rows/pages passing required validation |
| `records_invalid` | `ingestion_logs.records_invalid` | Rows/pages rejected or empty |
| `error_message` | `ingestion_logs.error_message` | Null for successful runs |
| `raw_output_path` | `ingestion_logs.raw_output_path` | Project-relative raw output |
| `staging_output_path` | `ingestion_logs.staging_output_path` | Project-relative staging output |
| `clean_output_path` | `ingestion_logs.clean_output_path` | Project-relative clean output |
| `data_quality_score` | analytics view or `ingestion_logs` extension | Used by dashboard and suggestions |
| `file_manifest.file_hash_sha256` | `documents.file_hash_sha256` | Used for duplicate detection |
| `file_manifest.file_size_bytes` | `documents.file_size_bytes` | File size audit |
| `pdf_metadata.document_id` | `documents.document_metadata` or external key | String document key from Duy |
| `document_pages.text` | `document_pages.page_text` | Page text for Lap RAG |
| `document_pages.page_number` | `document_pages.page_number` | Starts at 1 |
| `document_pages.character_count` | `document_pages.character_count` | Used for quality checks |
| `document_pages.is_empty` | `document_pages.is_empty` | Used to skip empty pages |

## Status Values

Duy ingestion status values:

- `success`
- `partial_success`
- `failed`
- `running`

These should align with Phat's `ingestion_logs.status` constraint.

## Current Real Sources

| Source | Source name | Records/pages valid |
| --- | --- | --- |
| Superstore CSV | `superstore_sales_csv` | 9994 |
| Product Sales Region Excel | `product_sales_region_excel` | 1500 |
| DummyJSON Products API | `dummyjson_products_api` | 30 |
| DataFlow Technical Report PDF | `dataflow_technical_report_pdf` | 36 |

