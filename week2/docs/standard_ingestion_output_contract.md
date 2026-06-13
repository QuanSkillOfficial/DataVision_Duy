# Standard Ingestion Output Contract

Owner: Duy  
Role: Ingestion and Pipeline Owner  
Scope: Week 3 reusable ingestion modules

## Purpose

This contract defines what every ingestion module must produce so the Database, RAG, ML, Analytics, and Demo teams can consume ingestion outputs consistently.

## Standard Flow

```text
source input
  -> reusable ingestor
  -> raw output
  -> staging output
  -> clean output
  -> ingestion log
```

## Output Layers

| Layer | What it stores | Rule | Consumers |
| --- | --- | --- | --- |
| Raw | Original file or original API response | Preserve source data with no cleaning | Data engineering, audit, replay |
| Staging | Parsed data with technical cleanup such as column-name normalization | Can still contain invalid rows or optional missing values | Database and quality checks |
| Clean | Validated records after duplicate removal and required-field validation | Required fields must be present and non-null | PostgreSQL, analytics, ML, AI |
| Logs | One JSON record per ingestion run | Paths must be project-relative, not local absolute paths | PostgreSQL `ingestion_logs`, monitoring |

## Required Module Output

Each ingestor should return a Python dictionary matching the ingestion log schema and write that same dictionary to `logs/<source>_ingestion_log.json`.

Required fields:

| Field | Required | Notes |
| --- | --- | --- |
| `run_id` | Yes | UUID generated per run |
| `source_name` | Yes | Stable source identifier |
| `source_type` | Yes | `csv`, `excel`, `api`, `pdf`, `database`, or `streaming` |
| `input_path_or_url` | Yes | Project-relative path or URL |
| `start_time` | Yes | ISO 8601 UTC timestamp |
| `end_time` | Yes | ISO 8601 UTC timestamp |
| `status` | Yes | `success`, `failed`, or `partial_success` |
| `records_read` | Yes | Rows, records, or pages read |
| `records_valid` | Yes | Records that satisfy required validation |
| `records_invalid` | Yes | Duplicate rows removed plus rows/pages failing required validation |
| `error_message` | Yes | `null` for successful runs |
| `raw_output_path` | Yes when raw output exists | Project-relative path |
| `staging_output_path` | Yes when staging output exists | Project-relative path |
| `clean_output_path` | Yes when clean output exists | Project-relative path or `null` for PDF text extraction |
| `owner` | Yes | Ingestion owner |

## Required-Field Validation

Clean data means validated data. A row may still have missing optional fields, but it must not be missing required fields.

Current required fields:

| Source | Required fields |
| --- | --- |
| CSV sales | `ordernumber`, `quantityordered`, `priceeach`, `sales`, `orderdate`, `status`, `customername` |
| Excel inventory | `product_id`, `product_name` |
| API customer JSON | `customer_id`, `email`, `created_at` |
| PDF | Non-empty extracted page text |

Optional missing values should be logged separately in `optional_missing_values`.

## Current Reusable Modules

| Module | Responsibility |
| --- | --- |
| `scripts/ingestion/csv_ingestor.py` | CSV raw copy, staging parse, required-field clean output, log |
| `scripts/ingestion/excel_ingestor.py` | Excel sheet detection, header-row detection, staging and clean CSV, log |
| `scripts/ingestion/api_ingestor.py` | API JSON load, flatten, required-field validation, log |
| `scripts/ingestion/pdf_ingestor.py` | PDF raw copy, page-level text extraction, metadata, log |
| `scripts/ingestion/ingestion_engine.py` | Runs all current ingestion modules |

## Downstream Handoff

| Team | What they consume |
| --- | --- |
| Phat - Database/Quality | Clean CSV outputs, staging outputs, and JSON logs for PostgreSQL tables |
| Lap - RAG/Embeddings | PDF extracted text and metadata |
| Tuong - Prediction/ML | Clean structured CSV/API/Excel records |
| Hung - Demo/Reports/UX | Clean data and ingestion status logs for demo screens |

