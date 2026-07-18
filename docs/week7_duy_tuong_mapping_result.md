# Week 7 Duy - Tuong Mapping and Audit Result

## Purpose

This document is the Week 7 source of truth for the integration between Duy's
ingestion outputs and Tuong's prediction module. It distinguishes four
different kinds of evidence:

1. Duy's input payload contract.
2. Tuong's prediction output contract.
3. PostgreSQL insert/query-back proof.
4. UI/RAG fixtures used for downstream contract testing.

The audit was generated from:

- Duy repository: `DataVision_Duy`
- Tuong repository: `DataVision_Tuong`
- Tuong commit audited: `657c839b7471dcf5151c2314cfbe71b84a1a983f`
- Machine-readable report:
  `outputs/tuong_handoff/tuong_week7_mapping_summary.json`

The Tuong repository was audited read-only. Tuong-owned source changes and
cleanup must be committed by Tuong.

## 1. Canonical Identity Mapping

| Field | Current value/rule | Owner |
| --- | --- | --- |
| `source_id` | CSV `1`, Excel `2`, API `3`, PDF `4` | Phat |
| `source_name` | Stable Duy source slug | Duy |
| `document_external_id` | Stable string key | Duy |
| `document_db_id` | Phat `documents.id`; full DataFlow document is `1` | Phat |
| `ingestion_run_id` | Duy execution UUID | Duy |
| DB prediction document column | `prediction_logs.document_id` | Phat |

Required mapping:

```text
Duy document_db_id
  -> Tuong prediction log payload document_id
  -> Phat prediction_logs.document_id
```

`source_id` must never contain an ingestion UUID. Derived sections and
validation-only payloads may have `document_db_id=null` because they are not
independent rows in Phat's `documents` table.

## 2. Input Duy Provides to Tuong

Primary batch:

```text
DataVision_Duy/outputs/prediction_payloads/tuong_week7_prediction_payloads.json
```

Additional cases only:

```text
DataVision_Duy/outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json
```

Individual case files:

```text
DataVision_Duy/outputs/prediction_payloads/week7/01_*.json
...
DataVision_Duy/outputs/prediction_payloads/week7/20_*.json
```

Contract documentation:

```text
DataVision_Duy/docs/week7_duy_to_tuong_prediction_payload_contract.md
DataVision_Duy/docs/week7_duy_to_tuong_additional_prediction_payloads.md
```

The primary file contains exactly 20 ordered cases:

- 14 normal/real-data prediction cases.
- Short and empty text quality gates.
- Missing `file_name`.
- Unknown Markdown file type.
- Missing `document_external_id`.
- Invalid numeric `file_size`.

Tuong must not remove invalid or weak-input cases. They prove that one bad
item does not stop the entire batch and that errors use the same result shape.

## 3. Output Tuong Must Return

| Purpose | Required file |
| --- | --- |
| Prediction results | `DataVision_Tuong/outputs/week7_duy_prediction_results.json` |
| DB payloads | `DataVision_Tuong/outputs/db_integration/week7_prediction_log_payloads.json` |
| DB insert/query proof | `DataVision_Tuong/outputs/db_integration/week7_prediction_log_insert_result.json` |
| Safe RAG metadata | `DataVision_Tuong/outputs/rag_metadata/document_type_filter_payload.json` |
| Real single UI response | `DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_response_real.json` |
| UI batch response | `DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_batch_response.json` |
| Review queue | `DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_review_queue_sample.json` |

Each prediction result must contain:

```text
predicted_document_type
confidence
top_predictions
status
review_reason
source_id
source_name
document_external_id
document_db_id
ingestion_run_id
model_name
model_version
created_at
```

Allowed statuses:

```text
accepted
needs_review
waiting_for_source
failed
```

The staging policy is:

```text
confidence >= 0.80       -> accepted
confidence < 0.80        -> needs_review
text shorter than 50     -> waiting_for_source
validation/system error  -> failed
```

`accepted` means eligible for display. It is not automatically trusted ground
truth. RAG hard filtering additionally requires manual review or a trusted
model version.

## 4. Current Audit Result

| Gate | Expected | Observed | Status |
| --- | ---: | ---: | --- |
| Duy primary payloads | 20 | 20 | Passed |
| Duy additional payloads | 10 | 10 | Passed |
| Tuong input copy | 20 | 10 | Stale |
| Tuong prediction results | 20 | 8 | Incomplete |
| Result statuses | All required edge states | 8 `needs_review` | Incomplete |
| Prediction log payloads | 20 | 1 | Incomplete |
| PostgreSQL insert proof | Inserted/query-backed rows | Missing | Not proven |
| UI batch lineage | Duy/Phat IDs | `source_id=100..103`, `doc_001..004` | Sample only |
| RAG filtering rule | Soft by default | No hard filter | Passed |
| Tuong unit test command | Pass | Dependency import failure | Not proven here |
| Tuong CI smoke command | Pass | Missing `joblib` | Not proven here |

Overall status:

```text
handoff_contract_passed=true
tuong_output_contract_passed=false
prediction_ci_proof_passed=false
database_insert_proof_passed=false
status=blocked_on_tuong_refresh
```

Phat's separate Week 7 evidence reports 10 rows in `prediction_logs`. That
proves Phat's schema can contain prediction records, but it does not prove
Tuong's current 20-payload batch was inserted and queried back.

## 5. Code and Contract Findings for Tuong

### Blocking or high-priority

1. `ai/prediction/batch_inference.py` does not preserve `source_id` and
   `document_db_id` in normalized batch results.
2. `scripts/run_real_payloads.py` only prints validation warnings and does not
   regenerate prediction-log payloads.
3. `outputs/week7_duy_prediction_results.json` covers only eight additional
   valid cases and omits validation/quality-gate cases.
4. `outputs/db_integration/week7_prediction_log_payloads.json` contains only
   one stale sample.
5. No `week7_prediction_log_insert_result.json` exists.
6. UI fixtures use synthetic IDs and must not be presented as real Duy/Phat
   outputs.
7. `docs/prediction_log_contract.md` maps to the old
   `prediction_logs.document_db_id`; Phat's column is `document_id`.
8. `docs/prediction_contract.md` still permits unsafe RAG filtering at the
   old `0.60` threshold.
9. `requirements.txt` does not include `psycopg2-binary` or
   `python-dotenv`, although the DB integration path needs them.

### Consistency fixes

1. `config.py` defines the Week 7 staging threshold as `0.80`, while
   `feature_builder.py`, old docs and `model_card.json` still expose `0.60`.
2. `model_card.json` does not record the Python/scikit-learn/joblib training
   environment claimed by the compatibility documentation.
3. The CI smoke test accepts a raw validation error instead of requiring a
   normalized `status=failed` result.
4. The CI smoke test creates RAG/UI data inline instead of calling the
   production builders.
5. `docs/week7_prediction_api_contract.md` still claims an eight-payload
   input batch.

## 6. Cleanup Candidates in Tuong Repository

These files should be archived or removed from the active shared-repo merge
after Tuong confirms no consumer depends on them:

| Candidate | Reason |
| --- | --- |
| `**/__pycache__/` | Runtime cache directories are present and no root `.gitignore` exists |
| `scripts/test_prediction_on_duy_outputs.py` | Uses old `source_id=run UUID` semantics |
| `scripts/data/duy_dataflow_real_payload.json` | Stale single-payload lineage |
| `docs/prediction_contract.md` | Old 0.60 and unsafe RAG rule |
| `docs/prediction_log_contract.md` | Old DB column and threshold |
| `docs/model_card_document_classifier.md` | Old operational threshold |
| `docs/model_report_week3.md` | Historical Week 3 report |
| `docs/tuong_week3_summary_report.md` | Historical Week 3 summary |
| `week1/`, `week2/` | Historical planning/notebook assets |
| `Tuong tasks w7.pdf` | Manager source PDF in active repository root |

Keep these as official active paths:

```text
ai/prediction/
tests/ai_tests/
scripts/run_real_payloads.py
scripts/week7_prediction_ci_smoke_test.py
scripts/insert_prediction_logs_to_postgres.py
scripts/build_rag_filter_metadata.py
outputs/week7_duy_prediction_results.json
outputs/db_integration/
outputs/ui_fixtures/
outputs/rag_metadata/
```

## 7. Required Execution Sequence

From the Tuong repository:

```bash
pip install -r requirements.txt
python scripts/run_real_payloads.py --input outputs/prediction_payloads/tuong_week7_prediction_payloads.json
python -m pytest tests/ai_tests/ -q
python scripts/week7_prediction_ci_smoke_test.py
python scripts/insert_prediction_logs_to_postgres.py --input outputs/db_integration/week7_prediction_log_payloads.json --dry-run
python scripts/insert_prediction_logs_to_postgres.py --input outputs/db_integration/week7_prediction_log_payloads.json
```

Required PostgreSQL proof:

```sql
SELECT COUNT(*) FROM prediction_logs;
SELECT status, COUNT(*) FROM prediction_logs GROUP BY status;
SELECT * FROM v_prediction_review_queue;
```

## 8. Duy Audit Command

From the Duy repository:

```bash
python scripts/week7_build_tuong_mapping_summary.py --run-tuong-checks
```

Generated evidence:

```text
outputs/tuong_handoff/tuong_week7_mapping_summary.json
logs/tuong_handoff/tuong_week7_external_proof.json
```

## 9. Definition of Done

- [x] Duy provides exactly 20 ordered Week 7 payloads.
- [x] Duy IDs follow Phat's source/document mapping.
- [ ] Tuong copies the exact current 20-payload batch.
- [ ] Tuong returns 20 normalized results.
- [ ] Tuong returns 20 Phat-compatible log payloads.
- [ ] Weak/invalid inputs produce `waiting_for_source` or `failed`.
- [ ] UI fixtures use real Duy/Phat lineage.
- [ ] RAG metadata remains soft unless the trust rule passes.
- [ ] Unit tests and prediction CI smoke pass in a clean environment.
- [ ] Real prediction-log insert and review-queue query proof are saved.
