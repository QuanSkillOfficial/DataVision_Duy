# Week 6 Database Loading Result

Owner: Nguyen Minh Duy  
Consumer: Phat - Database, Quality, and Analytics Owner

## Current Result

Duy's database loading flow is implemented with two modes:

```powershell
python scripts/load_ingestion_outputs_to_postgres.py
```

This creates a dry-run plan without needing PostgreSQL.

```powershell
python scripts/load_ingestion_outputs_to_postgres.py --write-db --db-config data_engineering/configs/db_config.example.json
```

This attempts a real PostgreSQL insert when Phat provides a working schema/database config.

## Dry-Run Output

```text
logs/db_load_dry_run/duy_to_phat_db_load_plan.json
```

Latest dry-run result:

| Target | Planned rows |
| --- | ---: |
| `sources` | 4 |
| `pipeline_runs` | 4 |
| `ingestion_logs` | 4 |
| `structured_records` | 11524 |
| `documents` | 1 |
| `document_pages` | 36 |

## Implemented Writer Functions

| Function | Purpose |
| --- | --- |
| `insert_or_get_source()` | Inserts source or returns existing `sources.id` via `ON CONFLICT (name)` |
| `insert_pipeline_run()` | Inserts ingestion execution metadata |
| `insert_ingestion_log()` | Inserts records, status, paths, data quality, manifest path |
| `insert_document()` | Inserts PDF metadata and preserves Duy `document_external_id` |
| `insert_document_pages()` | Inserts page-level text using Phat internal `documents.id` |
| `insert_structured_records()` | Inserts clean CSV/API/Excel rows as JSON records |
| `load_ingestion_result_to_postgres()` | Transaction wrapper with commit/rollback |

## Real-Run Status

Real PostgreSQL insert is ready in code but still depends on Phat providing:

- final schema v3/v4 database
- source unique constraint on `sources.name`
- `pipeline_runs` table columns
- `ingestion_logs.pipeline_run_id`
- `documents.document_external_id`
- database credentials

Until those are confirmed, Duy's safe proof is the dry-run plan plus pytest coverage.
