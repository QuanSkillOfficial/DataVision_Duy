# Week 6 Duy to Phat DB Loading Result

Owner: Nguyen Minh Duy  
Partner: Phat - Database / PostgreSQL / pgvector

## Current Result

Duy prepared an executable database loader for Phat's schema_v4 direction. It supports schema preflight, transaction rollback, duplicate-run protection, latest-snapshot replacement, query-back verification, and a credential-free dry-run.

Current local mode:

```text
dry_run
```

Reason:

```text
The repository does not commit PostgreSQL passwords. Use Phat's local database config or environment variables for a local write.
```

## Dry-Run Output

```text
logs/db_load_dry_run/duy_to_phat_db_load_plan.json
```

## Real Inputs Covered

| Duy file | Target table |
| --- | --- |
| `logs/runs/*.json` | `sources`, `pipeline_runs`, `ingestion_logs` |
| `logs/manifests/*_manifest.json` | `sources`, `documents` |
| `week2/logs/pdf_metadata.json` | `documents` |
| `week2/data/staging/pdf/document_pages.jsonl` | `document_pages` |
| `week2/data/clean/csv/superstore_clean.csv` | `structured_records` |
| `week2/data/clean/excel/product_sales_region_clean.csv` | `structured_records` |
| `week2/data/clean/api/dummyjson_products_clean.csv` | `structured_records` |

## Insert Order

```text
sources
pipeline_runs
ingestion_logs
documents
document_pages
structured_records
```

## Important Mapping Fix

Duy's string `document_id` maps to:

```text
documents.document_external_id
```

Then Phat's internal:

```text
documents.id
```

is used by:

```text
document_pages.document_id
document_chunks.document_id
rag_query_logs.document_id
```

## Schema v4 Alignment Notes

After reviewing Phat's `DataVision_Phat/week6/database/schema_v4.sql`, Duy's writer follows these schema_v4 rules:

```text
pipeline_runs uses run_name / start_time / end_time / status.
pipeline_runs does not currently have run_id or pipeline_name.
structured_records uses status, not processing_status.
documents.file_hash_sha256 is filled from Duy's file manifest.
document_pages.document_id always receives Phat's internal documents.id.
document_pages is replaced per document on a new run to prevent duplicate pages.
structured_records is replaced per source on a new run because schema_v4 has no run_id in that table.
```

## Next Execution Step

After Phat provides schema/database config and confirms table columns, run:

```powershell
python scripts\load_ingestion_outputs_to_postgres.py --write-db --db-config data_engineering\configs\db_config.example.json
```

The real shared integration has already been confirmed through Phat's exports: 4 sources, 4 ingestion logs, 11,524 structured records, 1 PDF document, and 36 document pages. The command above reproduces that integration in another local PostgreSQL environment and queries the inserted rows back before returning success.
