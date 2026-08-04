# Backend API Contract for UI

**Owner (consumer):** Phi & Hung — `demo/services/backend_client.py`
**Owner (provider):** Duy, Phat, Tuong, Lap — FastAPI backend
**Last Updated:** 2026-07-06

This document defines the exact HTTP endpoints that the Streamlit UI
calls when `USE_BACKEND = True` (i.e. `QS_USE_BACKEND=true`).

In **Mock Fixture Mode** (default), these endpoints are not called — the
UI reads from `demo/services/mock_client.py` instead. When the team is
ready to connect the real FastAPI backend, every endpoint listed here
must match what the backend exposes.

---

## Base URL

```
http://localhost:8000/api
```

Configurable via environment variable `QS_BACKEND_URL`.

Week 7 route rule: `BACKEND_BASE_URL` already includes `/api`, so route
paths in `backend_client.py` must not include another `/api` prefix. The
full dashboard URL is `http://localhost:8000/api/dashboard/metrics`, not
`http://localhost:8000/api/api/dashboard/metrics`.

---

## Envelope Format

Every endpoint must return the following JSON envelope:

```json
{
  "data": <object | list | null>,
  "status": "success" | "error",
  "metadata": { ... }
}
```

- `data`: the primary payload; never omit this key.
- `status`: `"success"` on normal response, `"error"` on failure.
- `metadata`: optional context (owner, source view, timestamps).

The UI checks `status != "error"` and `data is not None` before
rendering. Any missing key causes a graceful fallback, never a crash.

---

## Endpoints

---

### 1. Dashboard — `GET or POST /dashboard/metrics`

**Owner:** Phat (analytics views) + Duy (ingestion logs)
**Service client function:** `get_dashboard_metrics(source_context)`

#### Request Body

```json
{
  "source_context": [
    { "filename": "report.pdf", "size": 2048 }
  ]
}
```

`source_context` may be an empty list `[]` — the backend must not crash.

#### Response `data` Fields

| Field | Type | Source | Notes |
|---|---|---|---|
| `source_count` | int | Phat | Total sources |
| `file_count` | int | Phat | Uploaded files |
| `link_count` | int | Phat | Source links |
| `record_count` | int | Phat | Total parsed rows/lines |
| `records_read` | int | Duy | Total records read |
| `records_valid` | int | Duy | Valid records |
| `records_invalid` | int | Duy | Invalid records |
| `data_quality_score` | int (0–100) | Phat | From `v_data_quality_dashboard` |
| `processing_status` | str | Duy | `ready` / `processing` / `waiting_for_source` / `failed` |
| `duplicate_risk` | str | Phat | `low` / `high` |
| `parsing_coverage` | float (0.0–1.0) | Phat | From `v_ingestion_health` |
| `rag_query_count` | int | Phat | From `v_dashboard_overview` |
| `rag_avg_latency_ms` | int | Phat | From `v_rag_daily_metrics` |
| `prediction_count` | int | Phat | From `v_dashboard_overview` |
| `document_processing_status` | object | Phat | Per-type counts from `v_document_quality_summary` |
| `recent_activity` | list | Phat | From `v_recent_activity` |
| `ingestion_runs` | list | Duy | From `v_latest_ingestion_runs` |

---

### 2. Ingestion Status — `GET /ingestion/status`

**Owner:** Duy
**Service client function:** `get_ingestion_status(run_id)`

#### Query Parameters

| Param | Type | Required | Notes |
|---|---|---|---|
| `run_id` | str | No | If omitted, returns the latest run |

#### Response `data` Fields

| Field | Type | Notes |
|---|---|---|
| `run_id` | str | Unique run UUID |
| `ingestion_run_id` | str | Duy's ingestion-specific run ID |
| `source_id` | int or null | DB primary key from Phat — null before insert |
| `source_name` | str | File or link name |
| `source_type` | str | `pdf`, `csv`, `xlsx`, `json`, `api` |
| `document_external_id` | str | Duy document key |
| `document_db_id` | int or null | DB document primary key from Phat |
| `status` | str | `ready` / `processing` / `waiting_for_source` / `failed` |
| `records_read` | int | |
| `records_valid` | int | |
| `records_invalid` | int | |
| `data_quality_score` | float | Percentage (e.g. `99.63`) |
| `file_hash_sha256` | str | Integrity hash |
| `raw_output_path` | str | |
| `staging_output_path` | str | |
| `clean_output_path` | str | |

---

### 3. Recent Activity — `GET /dashboard/recent-activity`

**Owner:** Phat (`v_recent_activity`)
**Service client function:** `get_recent_activity()`

#### Response `data`

A **list** of activity event objects:

| Field | Type | Notes |
|---|---|---|
| `timestamp` | str (ISO 8601) | |
| `actor` | str | Module or person that triggered the action |
| `action` | str | Human-readable description |
| `status` | str | `success` / `accepted` / `generated` / `failed` |

---

### 4. Classify Document — `POST /predict/document-type`

**Owner:** Tuong
**Service client function:** `classify_document(input_payload)`

#### Request Body (Tuong's prediction payload contract)

```json
{
  "document_id": "doc_dataflow_technical_report",
  "source_id": "src-001",
  "file_name": "DataFlow_Technical_Report.pdf",
  "file_type": "pdf",
  "file_size": 2857707,
  "text_length": 129028,
  "num_pages": 36,
  "source_system": "manual_upload",
  "extracted_text": "--- Page 1 --- ..."
}
```

All 9 fields are **required**. Missing any field → backend must return
`status = "failed"`.

Minimum `extracted_text` length: **50 characters**. Below this
threshold → `status = "waiting_for_source"`.

#### Response `data` Fields

| Field | Type | Notes |
|---|---|---|
| `predicted_document_type` | str or null | Top predicted label |
| `confidence` | float (0.0–1.0) | Confidence of top prediction |
| `model_version` | str | e.g. `document_classifier_v1` |
| `status` | str | `accepted` / `needs_review` / `waiting_for_source` / `failed` |
| `review_reason` | str or null | Explanation when not `accepted` |
| `top_predictions` | list | `[{ "label": str, "score": float }, ...]` — top 3 |

**Status rules:**
- `confidence >= 0.60` → `accepted`
- `confidence < 0.60` → `needs_review`
- No extracted text → `waiting_for_source`
- Missing required fields → `failed`

---

### 5. Classify Documents (Batch) — `POST /predict/document-type/batch`

**Owner:** Tuong
**Service client function:** `classify_documents(input_payloads)`

#### Request Body

```json
{
  "items": [ <classify_document payload>, ... ]
}
```

#### Response `data`

A **list** of `classify_document` response objects (one per item).

---

### 6. Submit Prediction Correction — `POST /predict/feedback`

**Owner:** Tuong (feedback contract)
**Service client function:** `submit_prediction_correction(payload)`

#### Request Body (Tuong's feedback contract)

```json
{
  "prediction_log_id": 12,
  "document_external_id": "doc_dataflow_technical_report",
  "predicted_document_type": "report",
  "corrected_document_type": "contract",
  "corrected_by": "user",
  "correction_reason": "Manual review confirmed this is a contract",
  "created_at": "2026-07-05T10:00:00Z"
}
```

All 7 fields are **required**.

#### Response `data`

```json
{ "success": true }
```

or on error:

```json
{ "success": false, "error": "Missing required fields: [...]" }
```

---

### 7. RAG Query — `POST /rag/query`

**Owner:** Lap
**Service client function:** `ask_rag(question, document_id)`

#### Request Body

```json
{
  "question": "What does the policy say about refunds?",
  "document_id": "ext-doc-00042"
}
```

`document_id` is optional — if provided, filters retrieval to that document.

#### Response `data` Fields

| Field | Type | Notes |
|---|---|---|
| `question` | str | Echoed from input |
| `answer` | str | Generated answer |
| `citations` | list | See citation object below |
| `retrieved_context` | list | See context object below |
| `model` | str | e.g. `all-MiniLM-L6-v2 + gpt-4o-mini` |
| `status` | str | `success` / `no_match` / `error` |

**Citation object:**

| Field | Type | Notes |
|---|---|---|
| `file_name` | str | |
| `page_number` | int | |
| `chunk_id` | str | |
| `document_external_id` | str | Duy's document key |
| `document_db_id` | int or null | Phat's DB document ID |

**Retrieved context object:**

| Field | Type | Notes |
|---|---|---|
| `chunk_text` | str | First 300 chars shown in UI |
| `similarity_score` | float (0.0–1.0) | Cosine similarity |
| `chunk_id` | str | |

**Status rules:**
- `success` → answer and citations returned
- `no_match` → no relevant context found; UI shows empty state
- `error` → question was empty or retrieval failed

---

### 8. Generate Suggestions — `POST /suggestions/generate`

**Owner:** Phi & Hung (aggregation of all modules)
**Service client function:** `generate_suggestions(context)`

#### Request Body

```json
{
  "dashboard_signals": {
    "data_quality_score": 91.7,
    "parsing_coverage": 0.88,
    "processing_status": "ready"
  },
  "prediction_result": {
    "status": "needs_review",
    "confidence": 0.45
  },
  "rag_context": {
    "status": "no_match"
  }
}
```

All fields are optional — an empty `{}` body must still return
at least one suggestion.

#### Response `data`

A **list** of suggestion objects, sorted descending by `final_score`:

| Field | Type | Notes |
|---|---|---|
| `title` | str | Short action title |
| `category` | str | `Data Quality` / `Retrieval Quality` / `Reporting` |
| `priority` | str | `High` / `Medium` / `Low` |
| `description` | str | |
| `why_it_matters` | str | |
| `next_action` | str | |
| `source_module` | str | `ingestion` / `prediction` / `rag` / `dashboard` |
| `source_view` | str | Phat view or log table name |
| `evidence_type` | str | e.g. `confidence_score`, `parsing_coverage` |
| `evidence_value` | any | Numeric or string signal value |
| `generated_from` | list | Module names that contributed |
| `final_score` | float | Computed priority score (0.0–1.0) |
| `final_priority` | str | Recomputed from `final_score` |

---

### 9. Generate Report — `POST /reports/generate`

**Owner:** Phi & Hung
**Service client function:** `generate_report(evidence_context)`

#### Request Body

```json
{
  "domain_label": "Financial Services",
  "report_type": "Domain Summary",
  "audience": "Management",
  "source_context": [ ... ],
  "dashboard_signals": { ... },
  "suggestions": [ ... ],
  "prediction_result": { ... },
  "rag_context": { ... }
}
```

All fields are optional — `{}` must still generate a valid report shell.
Reports **do not require suggestions** to generate.

#### Response `data` Fields

| Field | Type | Notes |
|---|---|---|
| `title` | str | Report title |
| `sections` | list | Ordered list of `{ Section, Preview, Audience }` rows |
| `evidence_table` | list | Rows of `{ Evidence Source, Module, Metric / Signal, Value, Used In Section, Limitation }` |

---

## How to Enable Backend Mode

```powershell
$env:QS_USE_BACKEND="true"
streamlit run demo/streamlit_app.py
```

Run backend smoke tests:

```powershell
$env:QS_USE_BACKEND="true"
.\.venv\Scripts\pytest tests/test_backend_contract_smoke.py -v
```

---

## Envelope Validation Rules (All Endpoints)

The UI validates every response with these three checks before rendering:

1. Response is a `dict`.
2. `"data"` key exists and is not `None`.
3. `"status"` key exists and is not `"error"`.

If any check fails, the UI shows a fallback message — it never crashes.
