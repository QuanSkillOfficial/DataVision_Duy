# Week 7 Additional Prediction Payloads for Tuong

## Purpose

Duy provides 10 additional payloads so Tuong can extend real-data and validation testing from 10 to 20 cases without losing the original Week 6/7 baseline.

## Output files

| File | Content |
| --- | --- |
| `outputs/prediction_payloads/tuong_week7_prediction_payloads.json` | Combined cases 1-20 |
| `outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json` | New cases 11-20 only |
| `outputs/prediction_payloads/week7/11_*.json` to `20_*.json` | Individual new cases |

## New case matrix

| Case | Test case | Input focus | Expected behavior |
| ---: | --- | --- | --- |
| 11 | `pdf_system_operators_section` | Real DataFlow pages 9-10 | `accepted` or `needs_review` based on confidence |
| 12 | `pdf_pipeline_api_section` | Real DataFlow pages 11-12 | `accepted` or `needs_review` based on confidence |
| 13 | `pdf_agent_workflow_section` | Real DataFlow pages 14-15 | `accepted` or `needs_review` based on confidence |
| 14 | `pdf_agentic_rag_evaluation_section` | Real DataFlow pages 25 and 29 | `accepted` or `needs_review` based on confidence |
| 15 | `csv_order_profitability_sample` | Six new Superstore rows | `accepted` or `needs_review` based on confidence |
| 16 | `excel_regional_sales_sample` | Six new Product Sales Region rows | `accepted` or `needs_review` based on confidence |
| 17 | `api_inventory_sample` | Six new DummyJSON product rows | `accepted` or `needs_review` based on confidence |
| 18 | `unknown_file_type_markdown` | Valid text with unknown `file_type=md` | Model should handle unknown category without crashing |
| 19 | `missing_document_external_id` | Platform lineage field intentionally removed | `failed_contract_validation` |
| 20 | `invalid_file_size_type` | `file_size="not-a-number"` | `failed` with normalized validation response |

## Why these cases are different

- Cases 11-14 use PDF sections that were not used by cases 1-4.
- Cases 15-17 use different rows from the original structured summaries.
- Case 18 tests OneHotEncoder unknown-category behavior.
- Case 19 tests the cross-team lineage contract, not only model features.
- Case 20 tests numeric metadata validation and batch error normalization.

## Required checks in Tuong's result

Tuong should return one standardized result per input with:

```text
predicted_document_type
confidence
top_predictions
status
review_reason
model_name
model_version
document_external_id
document_db_id
source_id
source_name
ingestion_run_id
```

Required assertions:

1. Twenty inputs produce twenty outputs.
2. A validation failure does not stop the remaining batch.
3. Case 18 does not crash because `md` is an unseen file type.
4. Case 19 fails platform-contract validation even though model feature fields are present; Tuong should normalize this as `failed`, not invent a `rejected` status.
5. Case 20 returns `failed` with `confidence=0.0` and an empty `top_predictions` list.
6. `source_id` is never populated with `ingestion_run_id`.
7. Real DataFlow IDs use Phat's confirmed mapping (`source_id=4`,
   `document_db_id=1`); derived or intentionally invalid documents keep
   `document_db_id=null` because no matching `documents` row exists.

## Current Tuong runner compatibility

At review time, Tuong's `scripts/run_real_payloads.py` still reads the hardcoded file:

```text
tuong_week6_prediction_payloads.json
```

Tuong should update the runner to accept:

```powershell
python scripts/run_real_payloads.py --input outputs/prediction_payloads/tuong_week7_prediction_payloads.json
```

Until that CLI option exists, Tuong can copy the combined JSON into the filename expected by the runner. The preferred fix is adding `--input`, because renaming files makes evaluation evidence harder to trace.

## Regeneration

After Phat returns real database IDs:

```powershell
python scripts/week7_build_prediction_payloads.py
```

The builder preserves all 20 test cases while enriching valid source records with confirmed `source_id` values. Only the full stored DataFlow document receives its real `document_db_id`; derived sections and synthetic validation cases must not invent document IDs.
