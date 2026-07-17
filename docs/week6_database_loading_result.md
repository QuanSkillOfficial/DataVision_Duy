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
| `insert_pipeline_run()` | Inserts ingestion execution metadata using executable schema_v4 SQL |
| `insert_ingestion_log()` | Inserts records, status, paths, data quality, manifest path |
| `insert_document()` | Inserts PDF metadata and preserves Duy `document_external_id` |
| `insert_document_pages()` | Replaces the latest page snapshot, then inserts page-level text using Phat internal `documents.id` |
| `insert_structured_records()` | Replaces the latest source snapshot, then inserts clean CSV/API/Excel rows as JSON records |
| `load_ingestion_result_to_postgres()` | Transaction wrapper with commit/rollback |
| `ingestion_run_exists()` | Prevents duplicate reloads because schema_v4 does not make `run_id` unique |
| `validate_target_schema()` | Checks all required Week 6 tables/columns before the first insert |
| `query_integration_counts()` | Queries sources, runs, logs, documents, pages, and structured rows back after loading |

## Real-Run Status

The Duy-side writer now performs schema preflight, INSERT, and query-back verification. The command exits non-zero if the schema is incompatible, a database write fails, or returned row counts are below the expected Week 6 totals. Because Phat schema_v4 has no run identifier in `document_pages` or `structured_records`, Duy treats these tables as latest snapshots and replaces rows for the same document/source on a new successful run.

Real PostgreSQL insert is aligned to Phat's reviewed `schema_v4.sql` columns:

| Target | Confirmed schema_v4 mapping |
| --- | --- |
| `sources` | `name`, `source_type`, `source_format`, `source_path`, `url`, `owner_name`, `sample_available`, `downstream_consumer`, `status` |
| `pipeline_runs` | `run_name`, `start_time`, `end_time`, `status` |
| `ingestion_logs` | `run_id`, `source_id`, `pipeline_run_id`, counts, paths, quality JSONB, manifest path, timestamps |
| `documents` | `document_external_id`, file metadata, SHA256 hash, PDF metadata JSONB, `processing_status='extracted'` |
| `document_pages` | internal `documents.id`, `page_number`, `page_text`, `character_count`, `is_empty` |
| `structured_records` | `source_id`, `record_data`, `status='clean'` |

## Phat Integration Evidence Reviewed

Phat has exported DB-shaped outputs showing Duy data loaded into PostgreSQL:

| Evidence | Phat output path | Result |
| --- | --- | --- |
| Sources | `DataVision_Phat/week6/outputs/ingestion_data_Duy/sources_202607051438.json` | 4 Duy sources |
| Ingestion logs | `DataVision_Phat/week6/outputs/ingestion_data_Duy/ingestion_logs_202607051438.json` | 4 successful runs |
| PDF document | `DataVision_Phat/week6/outputs/ingestion_data_Duy/documents_202607051439.json` | `document_external_id=doc_dataflow_technical_report`, `documents.id=1` |
| Document pages | `DataVision_Phat/week6/outputs/ingestion_data_Duy/document_pages_202607051442.json` | 36 pages |
| Dashboard overview | `DataVision_Phat/week6/outputs/dashboard_view_samples_PhiHung/v_dashboard_overview_202607071300.json` | 4 sources, 1 document, 4 successful ingestions, 10 predictions |
| Dashboard view samples | `DataVision_Phat/week6/outputs/dashboard_view_samples_PhiHung/v_*.json` | 12 view exports |
| Lap chunks | `DataVision_Phat/week6/outputs/document_chunk_data_Lap/document_chunks_202607071256.json` | 293 chunks for DataFlow PDF |
| Tuong prediction logs | `DataVision_Phat/week6/outputs/prediction_log_data_Tuong/prediction_logs_202607071251.json` | 10 prediction logs |

Resolved IDs from Phat output:

| Source / Document | Resolved DB ID |
| --- | ---: |
| `superstore_sales_csv` | `source_id=1` |
| `dataflow_technical_report_pdf` | `source_id=2` |
| `dummyjson_products_api` | `source_id=3` |
| `product_sales_region_excel` | `source_id=4` |
| `doc_dataflow_technical_report` | `document_db_id=1` |

If Duy needs to run `--write-db` locally, the only remaining requirement is Phat's PostgreSQL connection credentials and a runnable local schema. Note: Phat's current `schema_v4.sql` / `setup_database_v2.sql` still appears to need a comma before `prediction_logs` constraints.

The real cross-team load itself is already evidenced by Phat's exported rows listed above. Duy's local default remains dry-run because no database password is committed to this repository.

## Latest Phat Mapping Files

| File | Purpose |
| --- | --- |
| `docs/week6_ingestion_to_schema_v4_mapping.md` | Latest schema-v4 mapping alias |
| `docs/week6_phat_mapping_review.md` | Human-readable Phat mapping review |
| `outputs/phat_handoff/phat_week6_mapping_summary.json` | Machine-readable summary generated from Phat outputs |
| `scripts/week6_build_phat_mapping_summary.py` | Regenerates the summary from `DataVision_Phat/week6` |

Current cleanup status:

```text
Generated __pycache__ folders were removed from DataVision_Duy.
Week1/week2 folders were kept because they are historical deliverables and active Week 6 outputs still reference week2 paths.
```
