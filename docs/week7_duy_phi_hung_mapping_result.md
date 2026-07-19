# Week 7 Duy - Phi/Hung Mapping Audit

Audit date: 2026-07-20
Audited Phi/Hung commit: `2e0f49dbf4e12d0210efa28f3f28f5ba7deb9a8e`
Status: `blocked_on_phi_hung_refresh`

This document records the current read-only audit of the Duy-to-Phi/Hung
boundary. The machine-readable sources are authoritative:

```text
outputs/hung_handoff/hung_week7_mapping_summary.json
logs/hung_handoff/hung_week7_external_proof.json
```

## Inputs owned by Duy

Phi/Hung should consume these current files:

```text
outputs/ui_fixtures/duy_week7_database_enriched_summary.json
outputs/rag_handoff/week7_rag_handoff_manifest.json
outputs/prediction_payloads/tuong_week7_prediction_payloads.json
logs/db_load_results/duy_to_phat_db_load_result.json
```

Canonical DataFlow identity:

```text
source_id=4
document_external_id=doc_dataflow_technical_report
document_db_id=1
ingestion_run_id=4c595851-c11e-48e3-8c79-69f6fa52d282
database_identity_status=database_ids_confirmed
```

## Current audit gates

| Gate | Result |
| --- | --- |
| Duy fixture lineage | Passed |
| Phat dashboard fixture contract | Passed |
| Lap DataFlow RAG fixture | Passed |
| Tuong prediction fixture contract | Failed |
| UI active structure | Passed: 26/26 files |
| UI code and backend-route docs | Passed |
| Screenshots present | Passed |
| UI CI smoke test | Passed |
| Phi/Hung unit tests | Failed during collection |
| Overall real lineage | Blocked |

The Duy fixture in Phi/Hung now preserves `source_id=4`,
`document_db_id=1`, the external document ID and the current ingestion run
UUID. Phat's dashboard fixture and Lap's pgvector-shaped citation fixture also
pass their current contracts.

## Remaining blockers

1. `demo/fixtures/week7/tuong_prediction_batch_response.json` contains four
   records with `document_db_id=null`.
2. `demo/fixtures/week7/tuong_prediction_review_queue_sample.json` contains
   four records with `document_db_id=null`.
3. `python -m pytest tests -q -p no:cacheprovider` cannot collect the suite in
   the audited environment because `streamlit` is not installed.

These are Phi/Hung/Tuong environment and fixture blockers. They do not require
changes to Duy's ingestion pipeline or current UI fixture.

## Required Phi/Hung actions

1. Refresh both Tuong fixtures from Tuong's normalized current Week 7 output.
2. Preserve integer `source_id` and `document_db_id` plus
   `document_external_id` and `ingestion_run_id` in every applicable row.
3. Install the pinned UI requirements in Python 3.11.
4. Rerun the fixture validator, unit tests and UI CI smoke test.
5. Commit the refreshed fixtures and return the new audit evidence to Duy.

## Commands

From `DataVision_Hung`:

```powershell
python -m pip install -r requirements.txt
python -m pytest tests -q -p no:cacheprovider
python scripts/week7_ui_ci_smoke_test.py
```

From `DataVision_Duy` after Phi/Hung commits the refresh:

```powershell
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
python scripts/validate_week7.py
```

The mapping is complete only when all gates in
`outputs/hung_handoff/hung_week7_mapping_summary.json` are true.
