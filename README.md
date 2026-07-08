# DataVision Duy - Data Foundation Ingestion Track

This repository contains Duy's Data Foundation work for the DataVision platform.

The focus is ingestion: bringing API, CSV, Excel, PDF, and document-page text into a repeatable raw-to-staging-to-clean flow with portable logs and handoff contracts for PostgreSQL, RAG, prediction, dashboard, suggestions, and reports.

## Project Scope

| Area | Status | Location |
| --- | --- | --- |
| Week 1 ingestion foundation | Complete | `week1_ingestion_foundation/` |
| Week 2 ingestion prototypes | Complete | `week2/notebooks/data_team/` |
| Week 3 reusable ingestion modules | Complete | `week2/scripts/ingestion/` |
| Week 5 config-driven ingestion service | Complete | `data_engineering/` |
| Week 5 run history and manifests | Complete | `logs/runs/`, `logs/ingestion_runs.jsonl`, `logs/manifests/` |
| Week 6 integration handoff | Complete | `docs/week6_team_integration_handoff.md`, `outputs/*_handoff/` |
| Standard ingestion log schema | Complete | `week2/docs/ingestion_log_schema.md` |
| Standard output contract | Complete | `week2/docs/standard_ingestion_output_contract.md` |
| UI handoff contract | Complete | `week2/docs/ingestion_result_contract_for_ui.md` |
| Database handoff contract | Complete | `week2/docs/ingestion_db_handoff_for_phat.md` |
| Prediction handoff contract | Complete | `week2/docs/ingestion_to_prediction_contract.md` |
| RAG page-level handoff contract | Complete | `week2/docs/document_pages_jsonl_contract_for_lap.md` |

## Architecture

```text
Data Sources
  -> Ingestion Modules
  -> Raw Data
  -> Staging Data
  -> Clean Data
  -> PostgreSQL / Analytics / RAG / ML / Reports
```

## Current Supported Sources

| Source | Module | Raw output | Staging output | Clean output |
| --- | --- | --- | --- | --- |
| Superstore CSV | `csv_ingestor.py` | `week2/data/raw/csv/superstore_raw.csv` | `week2/data/staging/csv/superstore_staging.csv` | `week2/data/clean/csv/superstore_clean.csv` |
| Product Sales Region Excel | `excel_ingestor.py` | `week2/data/raw/excel/product_sales_region_raw.xlsx` | `week2/data/staging/excel/product_sales_region_staging.csv` | `week2/data/clean/excel/product_sales_region_clean.csv` |
| DummyJSON products API | `api_ingestor.py` | `week2/data/raw/api/dummyjson_products_raw.json` | `week2/data/staging/api/dummyjson_products_staging.csv` | `week2/data/clean/api/dummyjson_products_clean.csv` |
| DataFlow technical report PDF | `pdf_ingestor.py` | `week2/data/raw/pdf/dataflow_technical_report_raw.pdf` | `week2/data/staging/pdf/dataflow_pdf_text.txt`, `week2/data/staging/pdf/dataflow_pdf_pages_staging.csv`, and `week2/data/staging/pdf/document_pages.jsonl` | `week2/data/clean/pdf/dataflow_pdf_pages_clean.csv` |

## Run All Ingestion Modules

From the repository root:

```powershell
python -m week2.scripts.ingestion.ingestion_engine
```

Expected output:

```text
csv: success - 9994 valid
excel: success - 1500 valid
api: success - 30 valid
pdf: success - 36 valid
```

## Run Week 5 Config-Driven Ingestion

Run one source config:

```powershell
python -m data_engineering.pipelines.ingestion_engine --config data_engineering/configs/superstore_csv.json
```

Run all default Week 5 configs:

```powershell
python -m data_engineering.pipelines.ingestion_engine --all
```

Run with PostgreSQL dry-run after ingestion:

```powershell
python -m data_engineering.pipelines.ingestion_engine --config data_engineering/configs/superstore_csv.json --db-dry-run
```

Run with PostgreSQL write mode after Phat provides a working database config:

```powershell
python -m data_engineering.pipelines.ingestion_engine --config data_engineering/configs/superstore_csv.json --write-db --db-config data_engineering/configs/db_config.example.json
```

Each run writes:

```text
logs/runs/<run_id>.json
logs/ingestion_runs.jsonl
logs/manifests/<run_id>_manifest.json
```

## Build Prediction Payload From PDF

```powershell
python week2/scripts/ingestion/prediction_payload_builder.py
```

This builds a Tuong-ready document type classification payload from Duy's PDF ingestion outputs.

## Validate Project

```powershell
python week2/scripts/validate_project.py
```

This checks that required outputs exist, logs use project-relative paths, and each ingestion log contains the required schema fields.

Week 5 validation:

```powershell
python scripts/validate_week5.py
pytest tests/data_tests/
```

Week 6 integration checks:

```powershell
python scripts/load_ingestion_outputs_to_postgres.py
python scripts/week6_build_ui_fixture_from_ingestion_logs.py
python scripts/week6_build_rag_handoff_package.py
python scripts/week6_end_to_end_smoke_test.py
python scripts/validate_week6.py
```

Week 6 outputs:

```text
logs/db_load_dry_run/duy_to_phat_db_load_plan.json
logs/ui_fixtures/duy_ingestion_dashboard_fixture.json
outputs/ui_fixtures/duy_latest_ingestion_summary.json
outputs/ui_fixtures/duy_data_quality_summary.json
outputs/ui_fixtures/duy_pdf_document_summary.json
outputs/rag_handoff/document_pages.jsonl
outputs/rag_handoff/pdf_metadata.json
outputs/rag_handoff/rag_handoff_summary.md
outputs/rag_handoff/rag_handoff_manifest.json
outputs/prediction_payloads/tuong_week6_prediction_payloads.json
outputs/phat_handoff/phat_week6_mapping_summary.json
outputs/lap_handoff/lap_week6_mapping_summary.json
outputs/tuong_handoff/tuong_week6_mapping_summary.json
outputs/hung_handoff/hung_week6_mapping_summary.json
docs/week6_id_mapping_contract.md
docs/week6_ingestion_to_schema_v3_mapping.md
docs/week6_ingestion_to_schema_v4_mapping.md
docs/week6_phi_hung_ui_fixture_contract.md
docs/week6_document_pages_for_rag_confirmed.md
docs/week6_duy_to_phat_db_load_result.md
docs/week6_database_loading_result.md
docs/week6_phat_mapping_review.md
docs/week6_lap_rag_mapping_review.md
docs/week6_tuong_prediction_mapping_review.md
docs/week6_hung_ui_mapping_review.md
data_engineering/configs/db_config.example.json
data/sample_inputs/api/dummyjson_products_sample.json
```

Expected Week 6 verification:

```text
python scripts/validate_week6.py
python scripts/week6_end_to_end_smoke_test.py
pytest tests/data_tests/
```

Current verified result:

```text
Week 6 validation passed
Week 6 smoke test passed
20 pytest tests passed
```

## Important Rules

- Raw data preserves original source files or responses.
- Staging data is parsed and technically normalized.
- Clean data removes duplicates and records missing required fields.
- PDF ingestion also emits page-level JSONL for RAG chunking and citations.
- Optional missing values are allowed but logged separately.
- Shared logs must use project-relative paths, not local Windows absolute paths.

## Team Handoff

| Consumer | Contract |
| --- | --- |
| Phat - Database | `week2/docs/ingestion_db_handoff_for_phat.md` |
| Lap - RAG | `week2/docs/document_pages_jsonl_contract_for_lap.md` |
| Tuong - Prediction | `week2/docs/ingestion_to_prediction_contract.md` |
| Phi/Hung - Demo UI | `week2/docs/ingestion_result_contract_for_ui.md` |
| Whole team | `week2/docs/team_handoff_index.md` |

## Week 5 Integration Docs

| Consumer | Contract |
| --- | --- |
| Phat - PostgreSQL | `docs/week5_ingestion_to_schema_v2_mapping.md` |
| Phat - DB loading | `docs/postgres_loading_notes.md` |
| Backend/FastAPI | `docs/ingestion_api_service_plan.md` |

## Week 6 Integration Docs

| Consumer | Contract / Review |
| --- | --- |
| Whole team | `docs/week6_team_integration_handoff.md` |
| Phat - PostgreSQL | `docs/week6_phat_mapping_review.md` |
| Lap - RAG / pgvector | `docs/week6_lap_rag_mapping_review.md` |
| Tuong - Prediction | `docs/week6_tuong_prediction_mapping_review.md` |
| Hung - Streamlit UI | `docs/week6_hung_ui_mapping_review.md` |
| All modules | `docs/week6_id_mapping_contract.md` |
