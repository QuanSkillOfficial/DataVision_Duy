# Week 7 Duy-Phat Database Integration Result

## Status

`database_ids_confirmed` with one explicit limitation:

- Phat's Week 7 PostgreSQL evidence proves a complete Duy ingestion snapshot.
- Stable database IDs are confirmed and can enrich Duy's handoff files.
- The run UUIDs in Phat's snapshot are older than Duy's latest local run UUIDs.
- A fresh `--write-db` execution is still required to prove the latest Duy runs.

This distinction prevents a historical database snapshot from being presented as
proof that the newest local run logs were inserted.

## Schema and setup reviewed

| Item | Official Phat path | Result |
| --- | --- | --- |
| Schema | `DataVision_Phat/week7/database/schema/schema_v4_fixed.sql` | Passed static contract checks |
| Setup | `DataVision_Phat/week7/database/schema/setup_database_v3.sql` | Required views included |
| Validation | `DataVision_Phat/week7/database/validation/validation_queries_v3.sql` | Present |
| Setup runner | `DataVision_Phat/week7/database/scripts/run_database_setup.py` | Present |
| CI smoke test | `DataVision_Phat/week7/database/scripts/ci_database_smoke_test.py` | Phat reports 10/10 checks passed |

Verified schema properties:

- `CREATE EXTENSION IF NOT EXISTS vector`
- unique `sources.name`
- `documents.document_external_id`
- prediction statuses `accepted`, `needs_review`, `waiting_for_source`, `failed`
- no Week 6 `prediction_logs` missing-comma syntax defect
- dashboard, RAG readiness, and prediction review views

## Real database evidence from Phat

| Table or view | Confirmed count |
| --- | ---: |
| `sources` | 4 |
| `pipeline_runs` | 4 |
| `ingestion_logs` | 4 |
| `documents` | 1 |
| `document_pages` | 36 |
| `structured_records` | 11,524 |
| `document_chunks` | 293 |
| `rag_query_logs` | 1 |
| `prediction_logs` | 10 |
| `v_prediction_review_queue` | 5 |

Evidence files:

```text
DataVision_Phat/week7/database/outputs/db_validation/duy_data_load_counts.json
DataVision_Phat/week7/database/outputs/db_validation/rag_pgvector_counts.json
DataVision_Phat/week7/database/outputs/db_validation/prediction_log_counts.json
DataVision_Phat/week7/database/outputs/dashboard_view_samples/v_source_quality_summary.json
DataVision_Phat/week7/database/outputs/dashboard_view_samples/v_latest_ingestion_runs.json
DataVision_Phat/week7/database/outputs/dashboard_view_samples/v_document_rag_readiness.json
DataVision_Phat/week7/docs/week7_database_ci_smoke_test_result.md
DataVision_Phat/week7/docs/week7_database_setup_runbook.md
```

## Confirmed ID mapping

| Duy source name | Phat `sources.id` |
| --- | ---: |
| `superstore_sales_csv` | 1 |
| `product_sales_region_excel` | 2 |
| `dummyjson_products_api` | 3 |
| `dataflow_technical_report_pdf` | 4 |

| Duy document key | Phat `documents.id` |
| --- | ---: |
| `doc_dataflow_technical_report` | 1 |

Canonical rules:

```text
source_name -> sources.id -> source_id
document_external_id -> documents.id -> document_db_id
ingestion_run_id -> Duy run UUID
```

Never map `ingestion_run_id` to `source_id`, and never insert
`document_external_id` directly into an integer foreign-key column.

## Generated Duy proof and handoffs

Run:

```powershell
python scripts/week7_build_phat_mapping_summary.py
python scripts/week7_build_rag_handoff_package.py --db-load-result logs/db_load_results/phat_week7_external_database_proof.json
python scripts/week7_build_prediction_payloads.py --db-load-result logs/db_load_results/phat_week7_external_database_proof.json
python scripts/week7_build_ui_fixtures.py --db-load-result logs/db_load_results/phat_week7_external_database_proof.json
```

Generated files:

```text
outputs/phat_handoff/phat_week7_mapping_summary.json
logs/db_load_results/phat_week7_external_database_proof.json
outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
outputs/rag_handoff/week7_rag_handoff_manifest.json
outputs/prediction_payloads/tuong_week7_prediction_payloads.json
outputs/ui_fixtures/duy_week7_database_enriched_summary.json
```

The generated proof records `current_duy_runs_loaded=false` until the latest run
UUIDs are loaded. Stable IDs remain valid because Phat resolves sources by
`source_name` and documents by `document_external_id`.

## Fresh load command

Start Phat's Docker database and run its setup from the Phat repository:

```powershell
docker compose -f docker-compose.db.yml up -d
python week7/database/scripts/run_database_setup.py --smoke --skip-lap
```

Then run from the Duy repository:

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_NAME="datavision_db"
$env:DB_USER="datavision"
$env:DB_PASSWORD="datavision123"
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
```

Use the same loader without `--smoke` for all 11,524 structured records.

## Current local limitation

The Docker daemon/PostgreSQL service was not running during this review, so the
latest Duy run UUIDs could not be reinserted locally. This is not represented as
a successful current-run database load. The committed Phat outputs are used only
as external database evidence and stable ID proof.
