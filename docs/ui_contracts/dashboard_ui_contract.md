# Dashboard UI Contract

**Owners (data providers):** Duy (ingestion) + Phat (analytics)
**Consumer:** Phi & Hung — `demo/dashboard_page.py`
**Service entry point:** `service_client.get_dashboard_metrics(source_context)`,
`service_client.get_ingestion_status(run_id)`, `service_client.get_recent_activity()`

---

## Week 6 — Phat Database Views Reference

All dashboard data in Week 6 is sourced from Phat's **`analytics_views_v3.sql`** views.
The UI consumes these 6 views via the backend API or mock fixture.

| View | Purpose | UI Section |
|---|---|---|
| `v_dashboard_overview` | High-level KPI counters | Top metric cards |
| `v_latest_ingestion_runs` | Per-run ingestion log entries | Ingestion Run Panel table |
| `v_data_quality_dashboard` | Per-source quality scores and invalid records | Data Quality chart |
| `v_document_rag_readiness` | Document embed status and chunk count | RAG Readiness indicator |
| `v_prediction_review_queue` | Low-confidence predictions needing review | Prediction Review Panel |
| `v_recent_activity` | Live feed of platform events | Activity feed |

---

## 1. `get_dashboard_metrics()` Response

Aggregates data from multiple Phat views into one envelope.

```json
{
  "data": {
    "source_count": 6,
    "file_count": 5,
    "link_count": 1,
    "record_count": 184,
    "records_read": 184,
    "records_valid": 178,
    "records_invalid": 6,
    "data_quality_score": 84,
    "processing_status": "ready",
    "duplicate_risk": "low",
    "parsing_coverage": 0.91,
    "rag_query_count": 37,
    "rag_avg_latency_ms": 412,
    "prediction_count": 22,
    "document_processing_status": {
      "contract": 6,
      "invoice": 5
    },
    "recent_activity": [ ... ],
    "ingestion_runs": [ ... ]
  },
  "status": "success",
  "metadata": {
    "owner": "Phat",
    "source_view": "v_dashboard_overview"
  }
}
```

### Required Fields

| Field | Type | Phat View | Notes |
|---|---|---|---|
| `source_count` | int | `v_dashboard_overview` → `total_sources` | Total sources |
| `file_count` | int | `v_dashboard_overview` → `total_documents` | Uploaded files |
| `link_count` | int | Derived | Source links submitted |
| `record_count` | int | `v_dashboard_overview` → `total_documents` | Parsed rows/lines |
| `records_read` | int | `v_latest_ingestion_runs` → `records_read` | Total records read |
| `records_valid` | int | `v_data_quality_dashboard` → `records_valid` | Valid records |
| `records_invalid` | int | `v_data_quality_dashboard` → `records_invalid` | Invalid records |
| `data_quality_score` | int (0–100) | `v_data_quality_dashboard` → `data_quality_score` | Overall quality score |
| `processing_status` | str | Duy ingestion output | `ready` / `waiting_for_source` / `processing` / `failed` |
| `duplicate_risk` | str | Phat derived | `low` / `high` |
| `parsing_coverage` | float (0.0–1.0) | `v_data_quality_dashboard` | Fraction of records valid |
| `rag_query_count` | int | `v_dashboard_overview` → `total_rag_queries` | Total RAG queries |
| `rag_avg_latency_ms` | int | `v_rag_daily_metrics` → `avg_latency_ms` | Average RAG latency |
| `prediction_count` | int | `v_dashboard_overview` → `total_predictions` | Total predictions |
| `document_processing_status` | object | `v_document_quality_summary` | Per-type counts `{label: count}` |
| `recent_activity` | array | `v_recent_activity` | See Section 3 |
| `ingestion_runs` | array | `v_latest_ingestion_runs` | See Section 2 |

---

## 2. `get_ingestion_status()` Response — Ingestion Run Object

Sourced from Phat's **`v_latest_ingestion_runs`** + Duy's ingestion outputs.

| Field | Type | Phat View / Duy Field | Notes |
|---|---|---|---|
| `run_id` | str | `v_latest_ingestion_runs` → `run_name` | Unique run identifier |
| `ingestion_run_id` | str | Duy — `ingestion_logs.run_id` | Duy's ingestion-specific UUID (**Week 6**) |
| `source_id` | int or null | `v_latest_ingestion_runs` → `source_id` | DB primary key from Phat (**Week 6**) |
| `source_name` | str | `v_latest_ingestion_runs` → `source_name` | File or link name |
| `source_type` | str | Duy output | `pdf`, `csv`, `xlsx`, `json`, `api` |
| `document_external_id` | str | Duy — `ingestion_logs` | Duy document key (**Week 6**) |
| `document_db_id` | int or null | Phat — `documents.id` | DB document primary key; null before insert (**Week 6**) |
| `status` | str | `v_latest_ingestion_runs` → `ingestion_status` | `ready` / `processing` / `waiting_for_source` / `failed` |
| `records_read` | int | `v_latest_ingestion_runs` → `records_read` | |
| `records_valid` | int | `v_data_quality_dashboard` → `records_valid` | |
| `records_invalid` | int | `v_data_quality_dashboard` → `records_invalid` | |
| `data_quality_score` | float | `v_data_quality_dashboard` → `data_quality_score` | Percentage (e.g. `99.63`) |
| `file_hash_sha256` | str | Duy output | Integrity hash (shown in Reports only) |
| `raw_output_path` | str | Duy output | |
| `staging_output_path` | str | Duy output | |
| `clean_output_path` | str | Duy output | |

---

## 3. `get_recent_activity()` Response — Activity Item

Sourced from Phat's **`v_recent_activity`** view.

| Field | Type | Phat View Field | Notes |
|---|---|---|---|
| `timestamp` | str (ISO 8601) | `created_at` | |
| `actor` | str | Derived from `activity_type` | Module or person that triggered the event |
| `action` | str | `description` | Human-readable event description |
| `status` | str | Derived | `success` / `accepted` / `generated` / `failed` |

**Activity types surfaced by `v_recent_activity`:**
- `RAG Query` — from `rag_query_logs`
- `Ingestion Issue` — from `ingestion_logs` where `status != 'success'`
- `New Source Added` — from `sources`

---

## 4. `v_document_rag_readiness` — RAG Readiness Panel

| Phat Field | UI Display | Notes |
|---|---|---|
| `document_external_id` | Document ID | Links to Duy's ingestion key |
| `file_name` | File name | |
| `processing_status` | Status badge | `embedded` = RAG-ready |
| `total_chunks` | Chunk count | Number of embedded chunks |
| `source_name` | Source | |

**RAG-ready rule:** `processing_status == 'embedded'` → green badge.

---

## 5. `v_prediction_review_queue` — Prediction Review Panel

| Phat Field | UI Display | Notes |
|---|---|---|
| `document_id` | Document (DB ref) | Phat FK to `documents.id` |
| `predicted_label` | Predicted type | |
| `confidence_score` | Confidence badge | `>= 0.80` Green / `0.60–0.79` Yellow / `< 0.60` Red |
| `status` | Status | `needs_review` / `waiting_for_source` |
| `review_reason` | Warning text | Shown under prediction card |
| `created_at` | Timestamp | |

**Filter rule:** View returns rows where `status IN ('needs_review', 'waiting_for_source') OR confidence_score < 0.60`.

---

## UI Behavior Rules

- `processing_status == "waiting_for_source"` → show info banner, no metrics rendered.
- `duplicate_risk == "high"` → quality signal row renders red/low score.
- `document_processing_status` empty → render `"Not available in current data."` instead of an empty chart.
- `v_prediction_review_queue` empty → hide panel or show `"No documents pending review."`.
- `v_document_rag_readiness` empty → show `"No RAG-ready documents yet."`.
- All numeric fields missing → default to `0` or `"Not available in current data."`, never crash.

## Week 7 Direct Fixture Mode

When `USE_BACKEND = False`, the Dashboard must be viewable without first
using the Upload page. It loads Week 7 fixtures from `demo/fixtures/week7/`
and must show total sources, successful ingestion runs, records processed,
average data quality, latest document, RAG readiness, prediction review queue
count, and recent activity.
