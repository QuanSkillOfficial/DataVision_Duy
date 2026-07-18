# DataVision Duy Project Status

Owner: Duy  
Role: Ingestion and Pipeline Owner  
Team: Data Foundation Team

## Current Status

The DataVision ingestion track is complete through Week 6 and now has the Week
7 GitHub/CI/CD/Docker readiness implementation. Phat's committed Week 7
evidence confirms the stable database IDs (`source_id=4`,
`document_db_id=1`); a fresh reload of the newest Duy run UUIDs and live
cross-repository execution are tracked separately.

| Phase | Status | Main result |
| --- | --- | --- |
| Week 1 | Complete | Ingestion foundation, source inventory, raw folder structure, setup confirmation |
| Week 2 | Complete | Working notebook prototypes for CSV, Excel, API JSON, and PDF extraction |
| Week 3 | Complete | Reusable ingestion modules, standard output contract, portable logs, cross-team handoff contracts |
| Week 5 | Complete | Config-driven ingestion service, run history logs, manifests, data quality score, PostgreSQL writer skeleton, pytest tests |
| Week 6 | Complete | Executable DB writer plus Phat export proof, RAG handoff, prediction payloads, UI fixtures, portable ID mapping, and cross-team smoke tests |
| Week 7 | Artifact-ready; owner execution blockers tracked | Shared repo manifest, GitHub Actions draft, Docker Compose database/full-app drafts, CI smoke tests, local integration contract, backend stub, UI fixture contract, DB modes, DB-enriched handoffs, readiness audits, cleanup plan, and deployment runbook |

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

## Week 6 Integration Evidence (historical milestone)

The Week 6 target was:

```text
connect -> insert -> query -> retrieve -> predict -> display -> test
```

The following records the Week 6 evidence package. Week 7 adds reproducible
Docker/CI contracts and keeps live runtime proof separate:

| Integration Step | Status | Evidence |
| --- | --- | --- |
| Connect | Complete | Phat's PostgreSQL export proof is summarized in `outputs/phat_handoff/phat_week6_mapping_summary.json` |
| Insert | Complete | Phat proof contains 4 sources, 4 ingestion logs, 11,524 structured records, 1 document, and 36 pages |
| Query | Complete | Phat dashboard view exports return integrated ingestion, quality, RAG, and prediction rows |
| Retrieve | Integrated with proof caveat | Duy supplied 36 real pages and Phat exported 293 chunks; Lap's 15-query evaluation is recorded, but Lap's notebook is not executed |
| Predict | Complete for stable document IDs | Tuong processed all 10 Duy payloads and Phat stored 10 prediction logs; rerun only when the newest ingestion run IDs must be logged |
| Display | Contract-connected | Hung loads Duy, Phat, Lap, and Tuong fixtures; Hung's copied Duy snapshot must be refreshed after a new Duy run |
| Test | Complete | Week 6 validation, smoke test, and `pytest tests/data_tests/` pass |

Historical Week 6 verification:

```text
Week 6 validation passed
Week 6 smoke test passed
Week 5 validation passed
Week 2 validation passed
28 pytest tests passed at the Week 6 milestone
```

## Week 7 Project Readiness

Available in this repository:

```text
.env.example
docker-compose.db.yml
docker-compose.yml
backend_stub/
deployment/
integration/shared_repo_manifest.json
scripts/week7_backend_stub_smoke_test.py
scripts/week7_local_docker_integration_smoke_test.py
scripts/week7_shared_repo_readiness_check.py
scripts/week7_shared_integration_smoke_test.py
.github/workflows/ci.yml
```

Artifact and contract verification:

```text
51 data-engineering tests passed
Week 7 ingestion smoke test passed
Week 7 validator passed (63 required files)
Both Compose files pass `docker compose config --quiet`
Shared integration contract smoke passed
```

Current readiness split:

```text
artifact_status=ready
execution_status=blocked
```

The machine-readable readiness report is:

```powershell
python scripts/week7_shared_repo_readiness_check.py
```

Use the stricter execution gate when all owner repositories are available:

```powershell
python scripts/week7_shared_repo_readiness_check.py --strict --strict-execution
```

The current execution blockers are recorded per owner:

```text
Lap: live pgvector insertion/retrieval proof pending
Tuong: 20-result/log/database execution proof pending
Phi/Hung: copied fixture lineage and UI contract refresh pending
```

The current local environment has not started the PostgreSQL service during
the contract checks. The runtime command is available through
`scripts/week7_local_docker_integration_smoke_test.py --start-full` when Docker
Desktop is running.

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
| `docs/week7_cross_team_delivery_matrix.md` | Whole team | Exact Week 7 input/output files, ID rules, proofs and acceptance gates |
| `docs/week7_shared_repo_structure.md` | Whole team | Shared repository tree and merge order |
| `docs/week7_deployment_runbook.md` | Whole team | Docker, backend stub, DB loading, CI and local integration commands |

## Next Recommended Work

1. Start Phat's Docker PostgreSQL + pgvector setup with the documented Week 7 credentials.
2. Run `python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke` and confirm 4/4/4/1/36/100 counts for the newest Duy run UUIDs.
3. Regenerate the Lap, Tuong, and Phi/Hung Week 7 outputs from that current-run load; stable `source_id=4` and `document_db_id=1` are already confirmed.
4. Merge Lap, Tuong, Phat, and Phi/Hung smoke commands into the shared workflow after each command passes independently.
5. Start the backend stub or production backend and run the backend contract smoke test.
6. Preserve manual-review safety: prediction labels must not become hard RAG filters without Tuong/Lap's trusted policy.

## Week 7 Verification

The CI-safe ingestion smoke test covers CSV, Excel, local API fallback, two-page PDF extraction, manifests, data quality, RAG page records, prediction payloads, and UI fixture creation. The Week 7 Tuong handoff now contains 20 cases: the original 10-case baseline plus 10 new PDF, structured-data, unknown-type, lineage, and numeric-validation cases. PostgreSQL smoke planning produces 4 sources, 4 logs, 1 document, 36 pages, and 100 structured rows.

Latest data test result: `51 passed`.
