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

Detailed Week 6 mapping review for Hung:

```text
docs/week6_hung_ui_mapping_review.md
outputs/hung_handoff/hung_week6_mapping_summary.json
```

Hung's local demo copy should be refreshed from Duy's canonical fixture when Duy reruns ingestion:

```text
F:/data/new/quanskill/DataVision_Hung/demo/fixtures/duy_latest_ingestion_summary.json
```

If the copied file and Duy's canonical file differ, use the Duy repo fixture as the latest source of truth.

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

Confirmed DB-enriched IDs from Phat's Week 6 load:

| Entity | Confirmed ID |
| --- | ---: |
| `superstore_sales_csv` | `source_id = 1` |
| `dataflow_technical_report_pdf` | `source_id = 2` |
| `dummyjson_products_api` | `source_id = 3` |
| `product_sales_region_excel` | `source_id = 4` |
| `doc_dataflow_technical_report` | `document_db_id = 1` |

Duy's fixture may keep `source_id` and `document_db_id` as `null` before real DB insertion. Hung should support both pre-DB and post-DB states.

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

## UI Fixture Refresh Rule

When Duy regenerates Week 6 outputs, Phi/Hung should copy these three files into their `demo/fixtures/` folder or update their mock client to read them directly:

| Duy Canonical File | Hung Demo Fixture Target | UI Usage |
| --- | --- | --- |
| `outputs/ui_fixtures/duy_latest_ingestion_summary.json` | `DataVision_Hung/demo/fixtures/duy_latest_ingestion_summary.json` | Dashboard, Reports, Suggestions |
| `outputs/ui_fixtures/duy_data_quality_summary.json` | optional fixture copy | Data quality and Suggestions |
| `outputs/ui_fixtures/duy_pdf_document_summary.json` | optional fixture copy | Reports and RAG readiness |

Fields that may be `null` before Phat DB enrichment:

```text
source_id
document_db_id
```

Fields that should remain available even before DB enrichment:

```text
source_name
ingestion_run_id
document_external_id
data_quality_score
file_hash_sha256
raw_output_path
staging_output_path
clean_output_path
document_pages_jsonl_path
```

## Page-Level Mapping To Hung Service Layer

| Hung Page | Service Function | Duy Data |
| --- | --- | --- |
| Dashboard | `get_dashboard_metrics()`, `get_ingestion_status()`, `get_recent_activity()` | `summary`, `latest_ingestion_run`, `runs` |
| Suggestions | `generate_suggestions(context)` | `data_quality_score`, `records_invalid`, `prediction_context`, `rag_handoff` |
| Reports | `generate_report(evidence_context)` | `run_id`, `file_hash_sha256`, raw/staging/clean paths, data quality fields |
| Prediction | `classify_document()`, `classify_documents()` | `prediction_context` and `logs/prediction_payloads/duy_pdf_prediction_payload.json` |
| Chatbot/RAG | `ask_rag()` | `rag_handoff` for readiness; Lap fixture for retrieved context and citations |

## What Hung Should Return To Duy

| Return Item | Format | Why |
| --- | --- | --- |
| Dashboard display confirmation | screenshot or markdown | Proves Duy fixture is UI-ready |
| Missing field list | markdown table | Duy can update fixture builder |
| Suggestion evidence requirements | markdown or JSON | Duy can expose new quality signals |
| Report evidence requirements | markdown or JSON | Duy can add lineage metadata |
| DB-enriched fixture preference | markdown note | Confirms whether Hung wants Phat IDs merged into Duy fixture |

## Notes

`prediction_context` intentionally does not include full `extracted_text` to keep UI fixtures small. The full payload remains available at:

```text
logs/prediction_payloads/duy_pdf_prediction_payload.json
```
