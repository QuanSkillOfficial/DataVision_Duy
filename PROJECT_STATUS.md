# DataVision Duy Project Status

Owner: Duy  
Role: Ingestion and Pipeline Owner  
Team: Data Foundation Team

## Current Status

The DataVision ingestion track is complete through Week 5 platform-readiness work and is now in Week 6 integration-hardening.

| Phase | Status | Main result |
| --- | --- | --- |
| Week 1 | Complete | Ingestion foundation, source inventory, raw folder structure, setup confirmation |
| Week 2 | Complete | Working notebook prototypes for CSV, Excel, API JSON, and PDF extraction |
| Week 3 | Complete | Reusable ingestion modules, standard output contract, portable logs, cross-team handoff contracts |
| Week 5 | Complete | Config-driven ingestion service, run history logs, manifests, data quality score, PostgreSQL writer skeleton, pytest tests |
| Week 6 | Complete | Integration-ready handoff package for Phat, Lap, Tuong, and Hung; DB dry-run proof, RAG handoff, prediction payloads, UI fixtures, ID mapping, and smoke tests |

## What Works Now

The project can ingest four source types:

| Source type | Input | Output |
| --- | --- | --- |
| CSV | `week2/data/sample_inputs/Superstore.csv` | Raw CSV, staging CSV, clean CSV, JSON log |
| Excel | `week2/data/sample_inputs/Product-Sales-Region.xlsx` | Raw XLSX, staging CSV, clean CSV, JSON log |
| API JSON | `https://dummyjson.com/products` with local raw fallback | Raw JSON, staging CSV, clean CSV, JSON log |
| PDF | `week2/data/sample_inputs/DataFlow_Technical_Report.pdf` | Raw PDF, extracted text, page-level JSONL, page CSV, clean page CSV, metadata, JSON log |

## Run Command

```powershell
python -m week2.scripts.ingestion.ingestion_engine
```

Week 5 config-driven command:

```powershell
python -m data_engineering.pipelines.ingestion_engine --all
```

Expected result:

```text
csv: success - 9994 valid
excel: success - 1500 valid
api: success - 30 valid
pdf: success - 36 valid
```

## Validation Command

```powershell
python week2/scripts/validate_project.py
```

Expected result:

```text
Validation passed
Checked 19 required outputs
Checked 7 required contract docs
Checked 4 required notebooks
Checked ingestion log schema and portable paths
```

## Standard Data Flow

```text
Source file or response
  -> Reusable ingestion module
  -> data/raw/
  -> data/staging/
  -> data/clean/
  -> logs/
  -> PostgreSQL / RAG / ML / Dashboards / Reports
```

## Layer Definition

| Layer | Meaning |
| --- | --- |
| Raw | Original source file or response. No cleaning should be applied. |
| Staging | Parsed data with technical cleanup, such as column-name normalization. |
| Clean | Validated data after duplicate removal and required-field checks. |
| Logs | One JSON log per ingestion run, using project-relative paths. |

## Validation Rule

Clean data means required fields are present and valid. Optional missing values are allowed but must be logged separately.

Example: the DummyJSON API product data has missing values in optional fields such as `brand`. These are logged under `optional_missing_values`, but the clean API dataset remains valid because required fields are present.

## Handoff to Other Members

| Member | Role | What they can use from this project |
| --- | --- | --- |
| Phat | Database, Quality, Analytics | Clean outputs, page-level document text, and JSON logs for PostgreSQL tables |
| Lap | RAG and Embeddings | `document_pages.jsonl`, extracted PDF text, PDF metadata |
| Tuong | Prediction and ML | Clean structured CSV/API/Excel data and Duy-style PDF prediction payload |
| Phi/Hung | Suggestions, Reports, Demo, AI UX | Ingestion result contract and data quality signals for Streamlit/demo pages |

## Week 6 Integration Evidence

The Week 6 target is:

```text
connect -> insert -> query -> retrieve -> predict -> display -> test
```

Current evidence:

| Integration Step | Status | Evidence |
| --- | --- | --- |
| Connect | Complete | `scripts/week6_end_to_end_smoke_test.py` reads all integration outputs |
| Insert | Complete as dry-run package | `logs/db_load_dry_run/duy_to_phat_db_load_plan.json` |
| Query | Complete as UI-ready fixture | `outputs/ui_fixtures/duy_latest_ingestion_summary.json` |
| Retrieve | Complete as RAG handoff | `outputs/rag_handoff/document_pages.jsonl` and `outputs/rag_handoff/rag_handoff_manifest.json` |
| Predict | Complete as Tuong payload package | `outputs/prediction_payloads/tuong_week6_prediction_payloads.json` |
| Display | Complete as Phi/Hung fixture | `outputs/ui_fixtures/*.json` |
| Test | Complete | Week 6 validation, smoke test, and `pytest tests/data_tests/` pass |

Latest verification:

```text
Week 6 validation passed
Week 6 smoke test passed
Week 5 validation passed
Week 2 validation passed
20 pytest tests passed
```

## Cross-Team Contracts

| Contract | Consumer | Purpose |
| --- | --- | --- |
| `week2/docs/ingestion_db_handoff_for_phat.md` | Phat | Maps Duy output to PostgreSQL schema_v2 tables |
| `week2/docs/document_pages_jsonl_contract_for_lap.md` | Lap | Defines page-level document text for chunking and citation |
| `week2/docs/ingestion_to_prediction_contract.md` | Tuong | Defines model-ready document metadata and extracted text |
| `week2/docs/ingestion_result_contract_for_ui.md` | Phi/Hung | Defines dashboard/upload UI fields from ingestion logs |
| `week2/docs/team_handoff_index.md` | Whole team | One-page index of all Duy handoff contracts |
| `docs/week6_team_integration_handoff.md` | Whole team | Week 6 cross-team input/output map |
| `docs/week6_phat_mapping_review.md` | Phat | Final Duy-to-Phat DB loading and dashboard view mapping |
| `docs/week6_lap_rag_mapping_review.md` | Lap | Final Duy-to-Lap RAG handoff mapping |
| `docs/week6_tuong_prediction_mapping_review.md` | Tuong | Final Duy-to-Tuong prediction payload mapping |
| `docs/week6_hung_ui_mapping_review.md` | Hung | Final Duy-to-Hung UI fixture and page mapping |

## Next Recommended Work

1. Execute real PostgreSQL write mode with Phat's live schema and credentials.
2. Ask Phat to return final `source_id` and `document_db_id` mappings after live DB insert.
3. Ask Lap to return real pgvector retrieval proof and citation-ready fixture.
4. Ask Tuong to keep using the 10-payload package and return reviewed prediction status.
5. Ask Hung to refresh `demo/fixtures/duy_latest_ingestion_summary.json` from Duy's canonical fixture.
