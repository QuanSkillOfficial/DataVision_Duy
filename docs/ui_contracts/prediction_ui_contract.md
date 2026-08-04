# Prediction UI Contract

**Owner (data provider):** Tuong (AI Prediction)
**Consumer:** Phi & Hung — `demo/prediction_page.py`
**Service entry point:** `service_client.classify_document(input_payload)`,
`service_client.classify_documents(input_payloads)`

----

## 1. Input Payload — Required Fields

| Field | Type | Example | Source |
|---|---|---|---|
| `document_id` | str | "doc-001" | Duy |
| `document_external_id` | str | "ext-doc-00042" | Duy (**NEW Week 6**) |
| `document_db_id` | str | "db-doc-0098" | Duy (**NEW Week 6**) |
| `source_id` | str | "src-001" | Duy |
| `file_name` | str | "contract_2024.pdf" | Duy |
| `file_type` | str | "pdf" | Duy |
| `file_size` | int | 153600 | Duy |
| `text_length` | int | 2800 | Duy |
| `num_pages` | int | 8 | Duy |
| `source_system` | str | "external" | Duy |
| `extracted_text` | str | "This agreement..." | Duy |

Missing any field → response `status = "failed"`.
Empty/blank `extracted_text` → response `status = "waiting_for_source"`.

----

## 2. Response — Accepted

```json
{
  "document_external_id": "ext-doc-00042",
  "document_db_id": "db-doc-0098",
  "predicted_document_type": "policy_document",
  "confidence": 0.91,
  "model_version": "document_classifier_v1",
  "status": "accepted",
  "review_reason": null,
  "top_predictions": [
    {"label": "policy_document", "score": 0.91},
    {"label": "contract", "score": 0.06},
    {"label": "report", "score": 0.03}
  ]
}
```

## 3. Response — Needs Review

```json
{
  "document_external_id": "ext-doc-00042",
  "document_db_id": "db-doc-0098",
  "predicted_document_type": "report",
  "confidence": 0.48,
  "model_version": "document_classifier_v1",
  "status": "needs_review",
  "review_reason": "Prediction confidence below threshold",
  "top_predictions": [ ... ]
}
```

## 4. Response — Waiting for Source

```json
{
  "predicted_document_type": null,
  "confidence": 0.0,
  "model_version": "document_classifier_v1",
  "status": "waiting_for_source",
  "review_reason": "No extracted text available yet.",
  "top_predictions": []
}
```

## 5. Response — Failed

```json
{
  "document_external_id": null,
  "document_db_id": null,
  "predicted_document_type": null,
  "confidence": 0.0,
  "model_version": "document_classifier_v1",
  "status": "failed",
  "review_reason": "Missing required fields: ['extracted_text', 'num_pages']",
  "top_predictions": []
}
```

----

## Status → UI Behavior

| Status | Alert | Badge Color | What renders |
|---|---|---|---|
| `accepted` | `st.success` | 🟢 Green | Full result card + top-3 |
| `needs_review` | `st.warning` | 🟡 Yellow | Result card + `review_reason` text |
| `waiting_for_source` | `st.info` | ⚪ Gray | Nothing further — wait for ingestion |
| `failed` | `st.error` | 🔴 Red | `review_reason` only, no result card |

## Confidence Threshold

```text
# Aligned to Tuong's document_classifier_v1 (confirmed Week 6):
confidence >= 0.60  -> accepted
confidence <  0.60  -> needs_review
```

## Confidence Badge (3‑tier — aligned to Tuong's model card)

| Confidence Range | Badge Color | Badge Text |
|---|---|---|
| `>= 0.80` | 🟢 Green | High Confidence |
| `0.60 – 0.79` | 🟡 Yellow | Medium Confidence |
| `< 0.60` | 🔴 Red | Low Confidence |

## Week 7 Staging Safety Policy

Medium-confidence predictions are model suggestions, not final truth.

| Confidence / Status | UI wording | Required action |
|---|---|---|
| `>= 0.80` | High confidence | Can be shown as accepted in staging |
| `0.60–0.79` | Medium confidence / Model suggestion | Review recommended before hard filtering or reporting |
| `< 0.60` | Low confidence / Needs human review | Manual correction flow required |
| `waiting_for_source` | Awaiting better source text | Wait for ingestion/extraction |
| `failed` | Validation failed | Check payload/logs |

## Document Type Labels (7 labels — Tuong's document_classifier_v1)

| Label | Display Name |
|---|---|
| `contract` | Contract |
| `invoice` | Invoice |
| `policy_document` | Policy Document |
| `report` | Report |
| `financial_statement` | Financial Statement |
| `resume` | Resume |
| `research_paper` | Research Paper |

## Rules

- `review_reason` is `null` when `status == "accepted"` — UI must hide the field entirely, never render the literal string `"None"` or `"null"`.
- `top_predictions` always contains exactly 3 items when status is `accepted` or `needs_review`; empty array otherwise.
- `model_version` always rendered in the card footer regardless of status.
- `extracted_text` minimum 50 characters for reliable prediction (Tuong's model requirement).
- `source_id` and `document_db_id` may be `null` before Phat's DB assigns them — UI must handle null gracefully.

----

## Manual Correction Feedback Payload

**Used when a user overrides a `needs_review` classification. Aligned to Tuong's `prediction_feedback_contract.md`.**

```json
{
  "prediction_log_id": 12,
  "document_db_id": 1,
  "document_external_id": "doc_dataflow_technical_report",
  "original_prediction": "contract",
  "corrected_document_type": "report",
  "corrected_by": "reviewer",
  "correction_reason": "The document is a technical report, not a contract."
}
```

| Field | Type | Notes |
|---|---|---|
| `prediction_log_id` | int | Phat DB prediction_logs.id — required |
| `document_db_id` | int/null | Phat DB document id when available |
| `document_external_id` | str | Duy document key |
| `original_prediction` | str | What the model originally predicted |
| `corrected_document_type` | str | The override label chosen by reviewer |
| `corrected_by` | str | Role/name of reviewer |
| `correction_reason` | str | Free-text reason for override |
| `created_at` | str | Optional ISO 8601 timestamp — client-generated |
