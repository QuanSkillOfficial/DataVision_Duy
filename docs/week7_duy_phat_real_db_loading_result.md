# Week 7 Duy-Phat Real Database Loading Result

## Final status

`passed` on 2026-07-20.

Duy's four current ingestion run UUIDs were loaded into a fresh, isolated
PostgreSQL 16 + pgvector database using Phat's `schema_v4_fixed` contract. The
test ran smoke mode first and then upgraded the same source snapshots to full
mode without duplicating `pipeline_runs` or `ingestion_logs`.

Machine-readable evidence:

```text
logs/db_load_results/duy_to_phat_db_load_result.json
outputs/integration/week7_duy_phat_docker_db_result.json
```

## Schema contract

Phat remains the database schema owner. Duy keeps this pinned, offline-capable
snapshot solely for standalone CI and local integration tests:

```text
deployment/database/init/10_phat_schema_v4_fixed.sql
```

The snapshot supports:

```text
sources
pipeline_runs
ingestion_logs
documents
document_pages
structured_records
document_chunks with vector(384)
prediction_logs
rag_query_logs
analytics_events
```

Before every write, `postgres_writer.validate_target_schema()` checks the six
tables owned by the ingestion boundary and fails if a required column is
missing.

## Reproducible command

From the Duy repository root with Docker Desktop running:

```powershell
python scripts/week7_duy_phat_docker_db_integration_test.py `
  --mode smoke-then-full `
  --project-name datavision-duy-week7-integration `
  --db-port 55432
```

The runner:

1. creates an isolated Compose project and volume;
2. starts `pgvector/pgvector:pg16`;
3. enables `vector` and applies `schema_v4_fixed`;
4. runs Duy's loader in smoke mode;
5. verifies 100 structured records;
6. runs full mode on the same run IDs;
7. verifies all 11,524 structured records;
8. rebuilds the Lap, Tuong, and Phi/Hung handoffs from the real DB result;
9. queries IDs and table counts back from PostgreSQL;
10. stops and removes the isolated container, network, and volume.

## Exact results

| Table | Smoke | Full |
| --- | ---: | ---: |
| `sources` | 4 | 4 |
| `pipeline_runs` | 4 | 4 |
| `ingestion_logs` | 4 | 4 |
| `documents` | 1 | 1 |
| `document_pages` | 36 | 36 |
| `structured_records` | 100 | 11,524 |

The full test completed in approximately 21 seconds on the reviewed machine.
The machine-readable result records every command, return code, query count,
and cleanup result.

## Current run proof

```text
superstore_sales_csv
  run_id=0a11e66b-59c8-4259-9759-d36589423758

product_sales_region_excel
  run_id=797e7ee4-9139-4157-b6b4-cb3c325ce469

dummyjson_products_api
  run_id=7fb106e1-c920-4e92-b3c8-47402ee94ea5

dataflow_technical_report_pdf
  run_id=4c595851-c11e-48e3-8c79-69f6fa52d282
```

All four UUIDs are present in `ingestion_logs`. Therefore:

```text
current_duy_runs_loaded=true
current_ingestion_run_loaded=true
current_ingestion_runs_loaded=true
```

## Canonical ID mapping

| Duy source | PostgreSQL `sources.id` |
| --- | ---: |
| `superstore_sales_csv` | 1 |
| `product_sales_region_excel` | 2 |
| `dummyjson_products_api` | 3 |
| `dataflow_technical_report_pdf` | 4 |

| Duy document key | PostgreSQL `documents.id` |
| --- | ---: |
| `doc_dataflow_technical_report` | 1 |

Rules:

```text
source_name -> sources.id -> source_id
document_external_id -> documents.id -> document_db_id
ingestion_run_id -> Duy run UUID
```

`source_id` must never contain `ingestion_run_id`, and the string
`document_external_id` must never be inserted into an integer document FK.

## Idempotency behavior

Phat's Week 7 schema does not store a run ID on `structured_records` or
`document_pages`. Duy therefore treats these rows as the current source or
document snapshot:

- an existing ingestion run does not create another pipeline run or log;
- structured rows for that source are replaced with the selected smoke/full
  snapshot;
- PDF metadata is upserted by `document_external_id`;
- document pages are replaced for the resolved `documents.id`.

This allows smoke mode to be followed by full mode while keeping exact counts.

## Verification command

```powershell
python scripts/week7_verify_db_load_result.py `
  --expected-structured-records 11524 `
  --verify-handoffs
```

The verification passes only when the result uses the current run IDs, exact
counts, canonical source/document IDs, and current DB-enriched handoffs.

## Ownership boundary

This closes Duy's database-loading responsibility. Phat still owns any future
schema migration, view definition, and production database setup. When Phat
changes the schema, update the pinned test snapshot only after reviewing the
new contract and rerunning this integration test.
