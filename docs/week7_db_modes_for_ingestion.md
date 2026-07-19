# Week 7 Database Modes for Ingestion

## Dry-run

```bash
python scripts/load_ingestion_outputs_to_postgres.py --dry-run
```

Builds an insert plan without opening a database connection.

## Smoke DB write

```bash
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
```

Loads all four sources, all four ingestion logs, the DataFlow document, 36 document pages, and 100 structured records distributed across CSV, Excel, and API sources.

## Limited DB write

```bash
python scripts/load_ingestion_outputs_to_postgres.py --write-db --limit-structured-records 250
```

## Full DB write

```bash
python scripts/load_ingestion_outputs_to_postgres.py --write-db
```

Loads all 11,524 structured records.

## Smoke then full

The same four run IDs may be loaded first in smoke mode and later in full mode.
The loader keeps one `pipeline_runs`/`ingestion_logs` row per run and refreshes
the mutable structured/page snapshots, so the final counts are exactly
`4/4/4/1/36/11524` rather than duplicated rows.

Reproduce this behavior against an isolated Docker database:

```bash
python scripts/week7_duy_phat_docker_db_integration_test.py --mode smoke-then-full
```

Verify the current proof and all DB-enriched handoffs:

```bash
python scripts/week7_verify_db_load_result.py --expected-structured-records 11524 --verify-handoffs
```

## Configuration priority

1. `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
2. Legacy `DATAVISION_DB_*` variables
3. JSON config passed with `--db-config`
4. `data_engineering/configs/db_config.example.json`

Every real write runs schema validation first. Each source load commits independently and rolls back on failure.
