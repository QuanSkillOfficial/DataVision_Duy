# Week 6 Duy -> Phat Schema v4 Mapping

Owner: Nguyen Minh Duy  
Partner: Phat - Database / PostgreSQL / pgvector Owner  
Latest Phat schema: `DataVision_Phat/week6/database/schema_v4.sql`

## Purpose

This file is the Week 6 schema-v4 alias for Duy's database mapping.

The detailed source-of-truth mapping is still maintained here:

```text
docs/week6_ingestion_to_schema_v3_mapping.md
```

The filename above was created earlier from the Week 6 task wording, but the reviewed Phat implementation is now `schema_v4.sql`. For clarity, use this file when discussing Phat's latest schema.

## Current Integration Status

Machine-readable summary:

```text
outputs/phat_handoff/phat_week6_mapping_summary.json
```

Current Phat output proof:

| Integration Area | Current Result |
| --- | --- |
| Duy sources loaded | 4 |
| Duy ingestion logs loaded | 4 |
| Duy structured records loaded | 11,524 |
| Duy PDF document loaded | 1 |
| Duy document pages loaded | 36 |
| Lap document chunks loaded | 293 |
| Tuong prediction logs loaded | 10 |
| Phi/Hung dashboard view samples exported | 12 views |

## Confirmed ID Mapping

| Duy Identifier | Phat Table.Column | Confirmed DB ID |
| --- | --- | ---: |
| `superstore_sales_csv` | `sources.name -> sources.id` | 1 |
| `dataflow_technical_report_pdf` | `sources.name -> sources.id` | 2 |
| `dummyjson_products_api` | `sources.name -> sources.id` | 3 |
| `product_sales_region_excel` | `sources.name -> sources.id` | 4 |
| `doc_dataflow_technical_report` | `documents.document_external_id -> documents.id` | 1 |

Required ID rule:

```text
source_id != ingestion_run_id
document_external_id != document_db_id
```

## Duy Insert Order For Phat

```text
sources
  -> pipeline_runs
  -> ingestion_logs
  -> documents
  -> document_pages
  -> structured_records
```

For PDF document pages:

```text
Duy document_external_id = doc_dataflow_technical_report
  -> Phat documents.document_external_id
  -> Phat documents.id = 1
  -> document_pages.document_id
```

Never insert Duy's string document ID directly into `document_pages.document_id`.

## Schema v4 Capabilities Confirmed

| Requirement | Status |
| --- | --- |
| `CREATE EXTENSION IF NOT EXISTS vector` | present |
| `sources.name` unique constraint | present |
| `documents.document_external_id` | present |
| `document_chunks.chunk_id` | present |
| `document_chunks.embedding vector(384)` | present |
| `ingestion_logs.data_quality_score` | present |
| `prediction_logs.status` | present |
| `prediction_logs.review_reason` | present |

## Schema v4 Note For Phat

The reviewed `schema_v4.sql` appears to have a missing comma before the `prediction_logs` constraints:

```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
CONSTRAINT chk_prediction_status
```

Expected:

```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
CONSTRAINT chk_prediction_status
```

This does not change Duy's ingestion mapping, but Phat should fix it before running `schema_v4.sql` or `setup_database_v2.sql` on a fresh database.

## Duy Files Phat Should Use

| Duy Output | Path |
| --- | --- |
| DB dry-run plan | `logs/db_load_dry_run/duy_to_phat_db_load_plan.json` |
| Run logs | `logs/runs/*.json` |
| Run history | `logs/ingestion_runs.jsonl` |
| File manifests | `logs/manifests/*_manifest.json` |
| Superstore clean CSV | `week2/data/clean/csv/superstore_clean.csv` |
| Product Sales clean Excel output | `week2/data/clean/excel/product_sales_region_clean.csv` |
| DummyJSON clean API output | `week2/data/clean/api/dummyjson_products_clean.csv` |
| PDF metadata | `week2/logs/pdf_metadata.json` |
| PDF document pages | `week2/data/staging/pdf/document_pages.jsonl` |
| RAG handoff pages | `outputs/rag_handoff/document_pages.jsonl` |

## What Phat Should Return To Duy

| Return Item | Why Duy Needs It |
| --- | --- |
| Source ID mapping | To enrich future Duy payloads after DB insert |
| Document DB ID mapping | To pass `document_db_id` to Lap/Tuong/Phi-Hung |
| Validation query output | To prove FK and quality checks pass |
| Dashboard view sample JSON | To help Phi/Hung consume real DB-shaped outputs |
| Schema fix confirmation | To ensure `schema_v4.sql` can run from scratch |
