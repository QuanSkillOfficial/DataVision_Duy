# Week 7 Duy - Phi/Hung Mapping and Audit Result

## Purpose

This document is the Week 7 source of truth for the handoff from Duy's
ingestion outputs to the Phi/Hung UI, suggestions, reports, backend client,
and UI CI layer.

The audit was generated from:

- Duy repository: `DataVision_Duy`
- Phi/Hung repository: `DataVision_Hung`
- Phi/Hung commit audited: `3e24e03e8da13641e3739449116d35d7c8c9904f`
- Machine-readable summary:
  `outputs/hung_handoff/hung_week7_mapping_summary.json`
- External proof:
  `logs/hung_handoff/hung_week7_external_proof.json`

The Phi/Hung repository was audited read-only. Phi/Hung-owned source fixes and
cleanup must be committed in the Phi/Hung repository.

## 1. Canonical identity for the UI

| Field | Canonical meaning | Current confirmed value |
| --- | --- | --- |
| `source_id` | Integer `sources.id` from Phat | PDF `4` |
| `source_name` | Stable Duy source key | `dataflow_technical_report_pdf` |
| `document_external_id` | Stable external document key | `doc_dataflow_technical_report` |
| `document_db_id` | Integer `documents.id` from Phat | `1` |
| `ingestion_run_id` | Duy execution UUID | Must come from the referenced run |
| `file_name` | Source file name | `DataFlow_Technical_Report.pdf` |

The UI must display these fields without renaming or conflating them:

```text
source_name
  -> sources.name
  -> source_id

document_external_id
  -> documents.document_external_id
  -> document_db_id

ingestion_run_id
  -> Duy ingestion/pipeline run UUID
```

`ingestion_run_id` must never be displayed or stored as `source_id`.

## 2. Inputs Duy sends to Phi/Hung

### 2.1 DB-enriched ingestion summary

```text
DataVision_Duy/outputs/ui_fixtures/duy_week7_database_enriched_summary.json
```

Required top-level fields:

```text
total_sources
total_runs
successful_runs
failed_runs
total_records_read
total_records_valid
total_records_invalid
average_data_quality_score
latest_document
handoff_paths
database_identity_status
database_schema_version
current_ingestion_runs_loaded
```

Required `latest_document` fields:

```text
source_id
document_db_id
document_external_id
ingestion_run_id
file_name
page_count
file_hash_sha256
parsing_status
```

Current canonical values:

```text
total_sources: 4
total_runs: 4
total_records_read: 11524
total_records_valid: 11524
average_data_quality_score: 99.63
source_id: 4
document_db_id: 1
document_external_id: doc_dataflow_technical_report
page_count: 36
database_identity_status: database_ids_confirmed
```

### 2.2 Handoff paths

```text
DataVision_Duy/outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
DataVision_Duy/outputs/rag_handoff/week7_rag_handoff_manifest.json
DataVision_Duy/outputs/prediction_payloads/tuong_week7_prediction_payloads.json
DataVision_Duy/outputs/phat_handoff/phat_week7_mapping_summary.json
DataVision_Duy/docs/week7_duy_to_phi_hung_ui_fixture_contract.md
```

Phi/Hung should copy the files into `demo/fixtures/week7/` only after checking
the source commit and the identity fields.

## 3. Files Phi/Hung must return

### 3.1 UI fixtures

```text
DataVision_Hung/demo/fixtures/week7/duy_latest_ingestion_summary.json
DataVision_Hung/demo/fixtures/week7/phat_dashboard_views_sample.json
DataVision_Hung/demo/fixtures/week7/lap_rag_response_real.json
DataVision_Hung/demo/fixtures/week7/tuong_prediction_batch_response.json
DataVision_Hung/demo/fixtures/week7/tuong_prediction_review_queue_sample.json
```

### 3.2 Runtime and validation

```text
DataVision_Hung/demo/services/fixture_validator.py
DataVision_Hung/scripts/week7_refresh_fixtures.py
DataVision_Hung/scripts/week7_ui_ci_smoke_test.py
DataVision_Hung/backend_stub/main.py
DataVision_Hung/.github/workflows/ci.yml
DataVision_Hung/docs/week7_ui_ci_smoke_test_result.md
DataVision_Hung/docs/week7_ui_runbook.md
DataVision_Hung/docs/week7_github_actions_ui_job.md
DataVision_Hung/screenshots/week7_staging_ready_ui/*.png
```

## 4. Fixture mapping

| UI fixture | Producer | UI consumers | Acceptance |
| --- | --- | --- | --- |
| `duy_latest_ingestion_summary.json` | Duy | Dashboard, Suggestions, Reports | Must use DB-enriched IDs and current hash/run |
| `phat_dashboard_views_sample.json` | Phat | Dashboard, review queue, Reports | Required views exist and counts match Phat proof |
| `lap_rag_response_real.json` | Lap | Chatbot, Reports, Suggestions | DataFlow citations, page, chunk, score, DB ID |
| `tuong_prediction_batch_response.json` | Tuong | Prediction page, Suggestions | Four canonical statuses and lineage fields |
| `tuong_prediction_review_queue_sample.json` | Tuong/Phat | Manual review UI | `prediction_log_id`, status, reason, document IDs |

### 4.1 Phat dashboard view contract

`phat_dashboard_views_sample.json` must contain:

```text
v_dashboard_overview
v_latest_ingestion_runs
v_data_quality_dashboard
v_document_rag_readiness
v_prediction_review_queue
v_recent_activity
```

The Week 7 sample should show:

```text
sources: 4
documents: 1
document_pages: 36
structured_records: 11524
document_chunks: 293
rag_query_logs: 1
prediction_logs: 10
```

Review-queue rows should include `document_id` and, where available, the
joined `document_external_id`. A database view that only exposes an integer
ID is still valid SQL evidence, but the UI adapter must not invent an external
ID.

### 4.2 Lap RAG contract

The active UI fixture must be the DataFlow fixture, not the historical vendor
refund-policy fixture:

```text
question: What is the DataFlow pipeline?
status: retrieval_only
document_external_id: doc_dataflow_technical_report
document_db_id: 1
file_name: DataFlow_Technical_Report.pdf
retrieval_backend: pgvector
embedding_dimension: 384
```

Each citation must include:

```text
file_name
page_number
chunk_id
document_external_id
document_db_id
similarity_score
```

### 4.3 Tuong prediction contract

The UI accepts only:

```text
accepted
needs_review
waiting_for_source
failed
```

Each result must include:

```text
source_id
source_name
document_external_id
document_db_id
ingestion_run_id
predicted_document_type
confidence
status
review_reason
top_predictions
manual_review_required
model_version
```

The Week 7 staging policy is:

```text
confidence >= 0.80                 -> accepted for staging display
0.60 <= confidence < 0.80          -> medium confidence, review recommended
confidence < 0.60                  -> needs_review
missing/short extracted_text       -> waiting_for_source
validation/system error            -> failed
```

`accepted` means suitable for display, not human-confirmed truth. The UI must
not present a medium-confidence or low-confidence prediction as final truth.

## 5. Current audit result

Run:

```powershell
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
```

Observed result:

| Gate | Result |
| --- | --- |
| Phi/Hung active structure | Passed |
| Phi/Hung unit tests | `63 passed, 15 skipped` |
| UI CI smoke test | Passed |
| Lap DataFlow fixture | Passed |
| Phat dashboard fixture structure/counts | Passed |
| Duy fixture lineage in Hung copy | Failed |
| Tuong fixture lineage in Hung copy | Failed |
| Overall mapping | `blocked_on_phi_hung_refresh` |

Current blocking differences:

1. Hung's copied Duy fixture has `source_id=null`,
   `document_db_id=null`, and `database_identity_status=pending_database_load`
   while Duy's canonical DB-enriched fixture has `source_id=4` and
   `document_db_id=1`.
2. Hung's Duy fixture metadata points to the ignored `code_by_others/` path.
3. All five Tuong batch UI items have null `source_id` and
   `document_db_id`.
4. All three Tuong review-queue items have null `document_db_id`.
5. Phat's copied review-queue rows do not expose
   `document_external_id`, so the UI cannot show the complete lineage without
   an adapter or refreshed view sample.
6. `demo/config.py` still sets `PREDICTION_CONFIDENCE_THRESHOLD=0.60`.
7. `docs/backend_api_contract_for_ui.md` still documents the legacy `0.60`
   acceptance rule and a string `source_id` example.
8. `scripts/week7_refresh_fixtures.py` depends on an ignored nested-repository
   directory, so a clean checkout cannot refresh fixtures from sibling repos
   without manual copying.

The current screenshots are present, including all eight Week 7 files, but
their freshness must be reconfirmed after the fixture refresh. The dashboard
screenshot currently shows the older `11560` record snapshot, while the
canonical Week 7 Duy database-enriched fixture is `11524`.

## 6. Cleanup list for Phi/Hung

Archive or remove only after checking active imports and tests:

```text
demo/fixtures/*.json
docs/Task Week 1-6.md
docs/W1/
docs/W2/
docs/W3/
docs/W5/
docs/W6/
materials/
frontend/
powerbi/
database/
data_engineering/
screenshots/week2_vertical_flow/
screenshots/week3_integration_ready_ui/
screenshots/week5_contract_connected_ui/
screenshots/week6_real_output_connected_ui/
```

Keep as the active Week 7 surface:

```text
demo/
demo/fixtures/week7/
demo/services/
demo/views/
tests/
scripts/week7_refresh_fixtures.py
scripts/week7_ui_ci_smoke_test.py
backend_stub/
docs/backend_api_contract_for_ui.md
docs/ui_contracts/
screenshots/week7_staging_ready_ui/
.github/workflows/ci.yml
```

Do not delete historical files blindly. Move them to an explicit archive
folder or archive branch after confirming no CI/import path uses them.

## 7. Commands after Phi/Hung refresh

### 7.1 Owner refresh checklist

Phi/Hung should refresh the five active fixtures from these producer files,
not from `code_by_others/` or from a historical Week 5/6 copy:

| Hung destination | Producer source |
| --- | --- |
| `demo/fixtures/week7/duy_latest_ingestion_summary.json` | `DataVision_Duy/outputs/ui_fixtures/duy_week7_database_enriched_summary.json` |
| `demo/fixtures/week7/phat_dashboard_views_sample.json` | `DataVision_Phat/week7/database/outputs/dashboard_view_samples/*.json` |
| `demo/fixtures/week7/lap_rag_response_real.json` | `DataVision_Lap/outputs/ui_fixtures/lap_rag_response_real.json` |
| `demo/fixtures/week7/tuong_prediction_batch_response.json` | `DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_batch_response.json` |
| `demo/fixtures/week7/tuong_prediction_review_queue_sample.json` | `DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_review_queue_sample.json` |

After copying, preserve these fields instead of defaulting them to `null`:

```text
source_id
source_name
document_external_id
document_db_id
ingestion_run_id
```

For the DataFlow document the values must be `4`,
`dataflow_technical_report_pdf`, `doc_dataflow_technical_report`, `1`, and
the matching Duy run UUID. For a record that genuinely has no database row
yet, the UI should label it `pending_database_load`; it must not silently
present a database-enriched fixture with null IDs.

From `DataVision_Hung`:

```powershell
python -m pytest tests -q
python scripts/week7_ui_ci_smoke_test.py
python backend_stub/main.py
streamlit run demo/streamlit_app.py
```

From `DataVision_Duy`:

```powershell
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
python scripts/validate_week7.py
python scripts/week7_shared_repo_readiness_check.py --strict
python scripts/week7_shared_repo_readiness_check.py --strict --strict-execution
```

The mapping is complete only when the audit status changes to `passed`, with
`fixture_contract_passed`, `ui_code_docs_passed`, and `real_lineage_passed`
all true. The `--strict-execution` command is expected to fail until Phi/Hung
commits the owner-side refresh; that failure is intentional evidence rather
than a reason to weaken the canonical Duy fixture.
