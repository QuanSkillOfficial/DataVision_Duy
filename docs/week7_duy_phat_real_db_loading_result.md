# Week 7 Duy-Phat Real Database Loading Result

## Current status

`pending_external_database`

The Duy loader is ready for Phat's fixed `schema_v4` and supports schema preflight, source upsert, transaction rollback, idempotent run detection, smoke mode, full mode, and SQL count verification. A real Week 7 write was not claimed because PostgreSQL was not reachable at `localhost:5432` during this review and `schema_v4_fixed.sql` was not yet available from Phat.

## Verified dry-run

```powershell
python scripts/load_ingestion_outputs_to_postgres.py --dry-run --smoke
```

| Table | Smoke count | Full count |
| --- | ---: | ---: |
| sources | 4 | 4 |
| pipeline_runs | 4 | 4 or more |
| ingestion_logs | 4 | 4 |
| documents | 1 | 1 |
| document_pages | 36 | 36 |
| structured_records | 100 | 11,524 |

## Real-run command

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_NAME="datavision_db"
$env:DB_USER="datavision"
$env:DB_PASSWORD="datavision123"
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
```

The command overwrites `logs/db_load_results/duy_to_phat_db_load_result.json` with confirmed `source_id`, `pipeline_run_id`, `document_db_id`, inserted counts, and query-back evidence.

## Required proof after Phat handoff

```sql
SELECT COUNT(*) FROM sources;
SELECT COUNT(*) FROM pipeline_runs;
SELECT COUNT(*) FROM ingestion_logs;
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM document_pages;
SELECT COUNT(*) FROM structured_records;
```
