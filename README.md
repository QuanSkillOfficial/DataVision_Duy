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
| Week 7 CI-ready ingestion pipeline | Complete for Duy: current-run DB load, Docker integration, CI smoke, and DB-enriched handoffs proven; sibling execution blockers tracked separately | `scripts/week7_*`, `outputs/*/week7_*`, `.github/workflows/ci.yml` |
| Standard ingestion log schema | Complete | `week2/docs/ingestion_log_schema.md` |
| Standard output contract | Complete | `week2/docs/standard_ingestion_output_contract.md` |
| UI handoff contract | Complete | `week2/docs/ingestion_result_contract_for_ui.md` |
| Database handoff contract | Complete | `week2/docs/ingestion_db_handoff_for_phat.md` |
| Prediction handoff contract | Complete | `week2/docs/ingestion_to_prediction_contract.md` |
| RAG page-level handoff contract | Complete | `week2/docs/document_pages_jsonl_contract_for_lap.md` |

`week1_ingestion_foundation/` is retained as a historical Git submodule. Use
`git clone --recurse-submodules <repository-url>` when the Week 1 evidence is
needed; Week 7 ingestion, tests, Docker, and CI do not depend on that submodule.

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

## Legacy Week 2 Demo Command

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

The official shared-repo implementation is the config-driven module below. The Week 2 command remains only for historical notebook/demo validation.

## Run Official Config-Driven Ingestion

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

## Build Prediction Payloads For Tuong

```powershell
python scripts/week6_build_tuong_prediction_payloads.py
```

This builds the single DataFlow PDF payload, the 10-case batch, and individual test payload files using the latest successful ingestion runs.

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

Use `python scripts/load_ingestion_outputs_to_postgres.py --write-db --db-config <config>` for a real PostgreSQL load. The loader validates Phat's target schema before writing, prevents duplicate run insertion, replaces the latest page/structured snapshots instead of duplicating rows, uses commit/rollback, queries inserted rows back, and exits non-zero when verification fails.

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

Historical Week 6 verification result:

```text
Week 6 validation passed
Week 6 smoke test passed
28 pytest tests passed
```

## Week 7 Shared CI, Docker and Database Integration

Week 7 adds the project-level integration boundary. The detailed two-way
handoff is in:

```text
docs/week7_cross_team_delivery_matrix.md
docs/week7_shared_repo_structure.md
integration/shared_repo_manifest.json
```

The local deployment draft provides:

```text
.env.example
docker-compose.db.yml
docker-compose.yml
backend_stub/
deployment/
docs/week7_backend_stub_contract.md
docs/week7_deployment_runbook.md
```

The `module-discovery` CI job keeps external owner jobs conditional until
their modules are merged into the shared repository. The readiness report makes
missing owner artifacts visible:

```powershell
python scripts/week7_shared_repo_readiness_check.py
python scripts/week7_shared_repo_readiness_check.py --strict --strict-execution
```

`--strict` checks the shared merge tree. The generated report exposes
`status` (artifact readiness) separately from `execution_status` (owner/runtime
proof). `--strict-execution` additionally fails when a recorded Lap, Tuong or
Phi/Hung execution audit is blocked.

Build deterministic shared fixtures and run the fast ingestion smoke test:

```powershell
python scripts/week7_build_shared_test_fixtures.py
python scripts/week7_ci_ingestion_smoke_test.py
```

Run PostgreSQL dry-run, smoke write, or full write:

```powershell
python scripts/load_ingestion_outputs_to_postgres.py --dry-run --smoke
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
python scripts/load_ingestion_outputs_to_postgres.py --write-db
```

Run the isolated Duy-to-Phat Docker proof. It loads smoke mode, upgrades the
same run IDs to full mode, verifies exact counts, rebuilds handoffs, and removes
the test stack:

```powershell
python scripts/week7_duy_phat_docker_db_integration_test.py --mode smoke-then-full
```

After a successful DB load, regenerate every DB-enriched handoff:

```powershell
python scripts/week7_build_rag_handoff_package.py
python scripts/week7_build_prediction_payloads.py
python scripts/week7_build_ui_fixtures.py
```

The Week 7 prediction builder writes a 20-case combined batch, a separate
10-case addition for cases 11-20, and individual files for debugging.

Validate the complete Week 7 data pipeline:

```powershell
pytest tests/data_tests/ -q
python scripts/week7_data_pipeline_smoke_test.py
python scripts/validate_week7.py
```

The builders never invent database IDs. The current canonical Week 7 DB result
confirms `source_id=4`, `document_db_id=1`, and all four latest Duy run UUIDs.
See `docs/week7_duy_phat_real_db_loading_result.md`.
Latest-run discovery combines the tracked `logs/ingestion_runs.jsonl` history
with local run files, so handoff regeneration also works from a clean clone.
The committed external Phat proof remains historical fallback evidence only;
`logs/db_load_results/duy_to_phat_db_load_result.json` is now the authoritative
current-run result.

Current Week 7 data-engineering test result: `59 passed` including shared
platform readiness checks.

Audit the Phi/Hung mapping from the Duy repository:

```powershell
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
```

The audit writes `outputs/hung_handoff/hung_week7_mapping_summary.json` and
`logs/hung_handoff/hung_week7_external_proof.json`. At the current audited
commit, Duy, Phat, and Lap fixtures plus the UI code/docs, screenshots, and UI
smoke pass. Tuong-derived fixtures still contain eight null
`document_db_id` values, and the full UI test suite needs the pinned Phi/Hung
dependencies installed. The audit therefore remains
`blocked_on_phi_hung_refresh`.

Run the project-level contract checks:

```powershell
docker compose -f docker-compose.db.yml config --quiet
docker compose -f docker-compose.yml config --quiet
python scripts/week7_backend_stub_smoke_test.py --base-url http://127.0.0.1:8000
python scripts/week7_shared_integration_smoke_test.py
```

The backend smoke test requires the stub to be running:

```powershell
python -m pip install -r backend_stub/requirements.txt
uvicorn backend_stub.main:app --host 127.0.0.1 --port 8000
```

The Docker database and Duy loader have real current-run execution proof. The
backend remains a contract stub, and this Duy proof does not replace Lap's real
pgvector retrieval, Tuong's prediction-log insertion, or Phi/Hung's UI owner
proof.

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

## Week 7 Integration Docs

| Area | Contract / Runbook |
| --- | --- |
| Whole-team handoff | `docs/week7_team_integration_handoff.md` |
| Whole data pipeline | `docs/week7_data_pipeline_runbook.md` |
| PostgreSQL modes | `docs/week7_db_modes_for_ingestion.md` |
| Phat DB loading | `docs/week7_duy_phat_real_db_loading_result.md` |
| Lap RAG handoff | `docs/week7_duy_to_lap_rag_handoff.md` |
| Tuong prediction payloads | `docs/week7_duy_to_tuong_prediction_payload_contract.md` |
| Tuong additional cases 11-20 | `docs/week7_duy_to_tuong_additional_prediction_payloads.md` |
| Phi/Hung UI fixture | `docs/week7_duy_to_phi_hung_ui_fixture_contract.md` |
| Phi/Hung mapping audit | `docs/week7_duy_phi_hung_mapping_result.md` |
| Cross-team delivery matrix | `docs/week7_cross_team_delivery_matrix.md` |
| CI commands | `docs/week7_duy_ci_commands.md` |
| Final review and cleanup | `docs/week7_final_project_review.md` |
