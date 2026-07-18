# Week 7 Duy to Tuong Prediction Payload Contract

Primary file:

`outputs/prediction_payloads/tuong_week7_prediction_payloads.json`

The primary batch contains 20 cases:

- Cases 1-10 retain the original full PDF, PDF sections, structured summaries, quality-gate inputs, and missing `file_name` validation.
- Cases 11-20 add four non-overlapping DataFlow sections, three new structured-data samples, an unknown Markdown file type, missing `document_external_id`, and invalid numeric metadata.

Additional-cases-only file:

`outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json`

Individual files:

`outputs/prediction_payloads/week7/01_*.json` through `20_*.json`

Required lineage fields are `source_id`, `source_name`, `document_external_id`, `document_db_id`, and `ingestion_run_id`. Quality fields are `data_quality_score`, `file_hash_sha256`, `page_range`, `text_length`, and `parsing_status`.

Rules:

- `source_id` is an integer database key. Current real-source values are
  CSV `1`, Excel `2`, API `3`, and PDF `4`.
- `document_db_id` is set only for the full DataFlow document currently stored in `documents`.
- Derived PDF sections and structured summaries retain stable external IDs but do not invent database document IDs.
- `ingestion_run_id` is never used as `source_id`.
- Invalid, weak-text, unknown-type, missing-lineage, and invalid-numeric cases remain in the batch for robustness and normalized-error coverage.

See `docs/week7_duy_to_tuong_additional_prediction_payloads.md` for the case 11-20 matrix and expected behavior.

Regenerate from Phat's validated Week 7 identity bridge:

```bash
python scripts/week7_build_phat_mapping_summary.py
python scripts/week7_build_prediction_payloads.py --db-load-result logs/db_load_results/phat_week7_external_database_proof.json
```

## Tuong acceptance gate

Tuong must copy the primary 20-item file exactly. Invalid and weak-input
cases are part of the contract and must not be removed during "cleaning".

Required return files:

```text
DataVision_Tuong/outputs/week7_duy_prediction_results.json
DataVision_Tuong/outputs/db_integration/week7_prediction_log_payloads.json
DataVision_Tuong/outputs/db_integration/week7_prediction_log_insert_result.json
DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_batch_response.json
DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_review_queue_sample.json
DataVision_Tuong/outputs/rag_metadata/document_type_filter_payload.json
```

Run the read-only mapping audit from Duy:

```bash
python scripts/week7_build_tuong_mapping_summary.py --run-tuong-checks
```

Current audited state:

```text
Duy payload contract: passed (20/20)
Tuong copied input: stale (10/20)
Tuong results: incomplete (8/20, all needs_review)
Tuong prediction-log payloads: incomplete (1/20)
Tuong real DB insert proof: missing
Tuong UI fixtures: contract-shaped sample IDs, not real Duy/Phat lineage
```

The detailed result and cleanup list are maintained in:

```text
docs/week7_duy_tuong_mapping_result.md
outputs/tuong_handoff/tuong_week7_mapping_summary.json
logs/tuong_handoff/tuong_week7_external_proof.json
```
