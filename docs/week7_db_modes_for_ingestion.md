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

## Configuration priority

1. `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
2. Legacy `DATAVISION_DB_*` variables
3. JSON config passed with `--db-config`
4. `data_engineering/configs/db_config.example.json`

Every real write runs schema validation first. Each source load commits independently and rolls back on failure.
