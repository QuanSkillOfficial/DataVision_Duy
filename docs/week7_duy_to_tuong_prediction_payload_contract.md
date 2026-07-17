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

- `source_id` is an integer database key or `null` before DB load.
- `document_db_id` is set only for the full DataFlow document currently stored in `documents`.
- Derived PDF sections and structured summaries retain stable external IDs but do not invent database document IDs.
- `ingestion_run_id` is never used as `source_id`.
- Invalid, weak-text, unknown-type, missing-lineage, and invalid-numeric cases remain in the batch for robustness and normalized-error coverage.

See `docs/week7_duy_to_tuong_additional_prediction_payloads.md` for the case 11-20 matrix and expected behavior.

Regenerate after database loading:

```bash
python scripts/week7_build_prediction_payloads.py
```
