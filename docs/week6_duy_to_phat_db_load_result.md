# Week 6 Duy to Phat DB Loading Result

Owner: Nguyen Minh Duy  
Partner: Phat - Database / PostgreSQL / pgvector

## Current Result

Duy prepared a database loading plan and writer functions for Phat's schema_v4 direction.

Current mode:

```text
dry_run
```

Reason:

```text
Final local PostgreSQL schema_v4 connection details are still needed before executing real INSERT statements.
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

## Next Execution Step

After Phat provides schema/database config and confirms table columns, run:

```powershell
python scripts\load_ingestion_outputs_to_postgres.py --write-db --db-config data_engineering\configs\db_config.example.json
```
