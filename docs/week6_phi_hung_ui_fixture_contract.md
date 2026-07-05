# Week 6 Phi/Hung UI Fixture Contract

Owner: Nguyen Minh Duy  
Consumer: Phi/Hung - UI, Suggestions, Reports, Demo

## Purpose

This contract defines Duy's real-output fixture for the Week 6 UI integration work. Phi/Hung can use this fixture to replace pure mock ingestion data in Dashboard, Suggestions, and Reports.

## Fixture Path

```text
outputs/ui_fixtures/duy_latest_ingestion_summary.json
```

Backward-compatible copy:

```text
logs/ui_fixtures/duy_ingestion_dashboard_fixture.json
```

## Source Data

The fixture is generated from:

| Source | Path |
| --- | --- |
| Run history | `logs/runs/*.json` |
| Prediction payload metadata | `logs/prediction_payloads/duy_pdf_prediction_payload.json` |
| RAG handoff metadata | `outputs/rag_handoff/rag_handoff_manifest.json` |

## Important ID Rules

| Field | Meaning |
| --- | --- |
| `source_id` | Database `sources.id` from Phat. `null` before DB insert. |
| `source_name` | Stable Duy source name from config. |
| `document_external_id` | Duy document key. Maps to `documents.document_external_id`. |
| `document_db_id` | Database `documents.id` from Phat. `null` before DB insert. |
| `ingestion_run_id` | Duy ingestion run UUID. Maps to `ingestion_logs.run_id`. |

Do not use `ingestion_run_id` as `source_id`.

## Expected Top-Level Shape

```json
{
  "summary": {
    "total_sources": 4,
    "total_runs": 4,
    "total_records_read": 11560,
    "total_records_valid": 11560,
    "total_records_invalid": 0,
    "latest_status": "success",
    "average_data_quality_score": 99.63,
    "status_counts": {"success": 4},
    "rag_ready_documents": 1,
    "prediction_payload_available": true
  },
  "latest_ingestion_run": {},
  "id_mapping": {},
  "prediction_context": {},
  "rag_handoff": {},
  "runs": []
}
```

## UI Usage

| UI Page | Fields |
| --- | --- |
| Dashboard | `summary`, `latest_ingestion_run`, `runs` |
| Suggestions | `data_quality_score`, `records_invalid`, `rag_handoff`, `prediction_context` |
| Reports | `runs`, `latest_ingestion_run`, `rag_handoff` |
| Prediction | `prediction_context.document_external_id`, `source_name`, `ingestion_run_id` |
| Chatbot/RAG | `rag_handoff.document_pages_path`, `document_external_id` |

## Notes

`prediction_context` intentionally does not include full `extracted_text` to keep UI fixtures small. The full payload remains available at:

```text
logs/prediction_payloads/duy_pdf_prediction_payload.json
```
