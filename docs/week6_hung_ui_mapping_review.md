# Week 6 Duy to Hung UI Mapping Review

Owner: Nguyen Minh Duy  
Consumer: Hung - Streamlit UI, Suggestions, Reports, Demo  
Repository reviewed: `DataVision_Hung/` in the shared team workspace

## Purpose

This document maps Duy's Week 6 ingestion outputs to Hung's Streamlit UI layer.

The goal is to make the UI consume real platform-shaped outputs instead of invented mock data:

```text
Duy ingestion outputs
  -> Hung service_client / mock fixture mode
  -> Dashboard, Suggestions, Reports, Prediction, Chatbot
```

## Hung Files Reviewed

| Area | Hung Path | What It Consumes |
| --- | --- | --- |
| Service mock layer | `DataVision_Hung/demo/services/mock_client.py` | Loads JSON fixtures and returns service envelopes |
| Service client layer | `DataVision_Hung/demo/services/service_client.py` | Public UI-facing functions for mock/backend mode |
| Dashboard page | `DataVision_Hung/demo/views/dashboard_page.py` | Dashboard metrics, latest ingestion status, recent activity |
| Suggestions page | `DataVision_Hung/demo/views/suggestions_page.py` | Dashboard signals, prediction result, RAG context |
| Reports page | `DataVision_Hung/demo/views/reports_page.py` | Source context, dashboard signals, suggestions, prediction, RAG |
| Prediction page | `DataVision_Hung/demo/views/prediction_page.py` | Tuong prediction output and manual review workflow |
| Chatbot page | `DataVision_Hung/demo/views/chatbot_page.py` | Lap RAG response with citations and retrieved context |
| Dashboard contract | `DataVision_Hung/docs/ui_contracts/dashboard_ui_contract.md` | Required dashboard fields and view names |
| Report contract | `DataVision_Hung/docs/ui_contracts/report_ui_contract.md` | Report evidence table contract |
| Week 6 handoff | `DataVision_Hung/docs/W6/week6_team_integration_handoff.md` | UI integration requirements from Duy/Phat/Lap/Tuong |

## Hung Fixture Files Reviewed

| Hung Fixture | Path | Current Usage |
| --- | --- | --- |
| Duy ingestion fixture copy | `DataVision_Hung/demo/fixtures/duy_latest_ingestion_summary.json` | Dashboard latest ingestion panel, Suggestions/Reports ingestion evidence |
| Phat dashboard views fixture | `DataVision_Hung/demo/fixtures/phat_dashboard_views_sample.json` | Dashboard cards, view tables, prediction review queue |
| Tuong prediction batch fixture | `DataVision_Hung/demo/fixtures/tuong_prediction_batch_response.json` | Prediction page and review workflow |
| Tuong prediction review queue fixture | `DataVision_Hung/demo/fixtures/tuong_prediction_review_queue_sample.json` | Manual review panel |
| Lap real RAG fixture | `DataVision_Hung/demo/fixtures/lap_rag_response_real.json` | Chatbot citations and retrieved context |

Important:

```text
Duy's canonical fixture is outputs/ui_fixtures/duy_latest_ingestion_summary.json.
Hung's demo fixture is a copied snapshot and should be refreshed after Duy reruns ingestion or payload generation.
```

## What Duy Gives Hung

Hung should use these files from Duy's repository.

| Output | Duy Path | Hung Usage |
| --- | --- | --- |
| Latest ingestion summary | `outputs/ui_fixtures/duy_latest_ingestion_summary.json` | Main fixture for Dashboard and latest ingestion panel |
| Data quality summary | `outputs/ui_fixtures/duy_data_quality_summary.json` | Data quality cards, source quality table, Suggestions |
| PDF document summary | `outputs/ui_fixtures/duy_pdf_document_summary.json` | PDF/RAG readiness card and report evidence |
| Backward-compatible UI fixture | `logs/ui_fixtures/duy_ingestion_dashboard_fixture.json` | Older UI fixture path if needed |
| RAG handoff package | `outputs/rag_handoff/document_pages.jsonl` | Input reference for Chatbot/RAG and report evidence |
| RAG metadata | `outputs/rag_handoff/pdf_metadata.json` | PDF metadata for citation/report context |
| Tuong prediction payload batch | `outputs/prediction_payloads/tuong_week6_prediction_payloads.json` | Prediction test input reference |
| Phat mapping summary | `outputs/phat_handoff/phat_week6_mapping_summary.json` | Confirmed `source_id` and `document_db_id` values |
| Lap mapping summary | `outputs/lap_handoff/lap_week6_mapping_summary.json` | RAG page count, chunk convention, citation needs |
| Tuong mapping summary | `outputs/tuong_handoff/tuong_week6_mapping_summary.json` | Prediction status summary and review workflow |
| Machine-readable Hung mapping | `outputs/hung_handoff/hung_week6_mapping_summary.json` | Compact mapping summary for UI integration |

## Canonical vs Copied Fixture Rule

Hung should treat Duy's file as the source of truth:

```text
DataVision_Duy/outputs/ui_fixtures/duy_latest_ingestion_summary.json
```

Hung can copy that file into:

```text
DataVision_Hung/demo/fixtures/duy_latest_ingestion_summary.json
```

The copied file is for Streamlit demo convenience only. If the values differ, use the Duy repo file for the latest run IDs, output paths, and prediction context.

## Main Fixture Shape

Primary file:

```text
outputs/ui_fixtures/duy_latest_ingestion_summary.json
```

Top-level sections:

```text
summary
latest_ingestion_run
id_mapping
prediction_context
rag_handoff
runs
```

## Dashboard Mapping

Hung's Dashboard currently calls:

```python
get_dashboard_metrics()
get_ingestion_status()
get_recent_activity()
```

Duy fields for Dashboard:

| Dashboard UI Field | Duy JSON Path | Current Value / Rule |
| --- | --- | --- |
| Total sources | `summary.total_sources` | `4` |
| Records read | `summary.total_records_read` | `11560` |
| Records valid | `summary.total_records_valid` | `11560` |
| Records invalid | `summary.total_records_invalid` | `0` |
| Quality score | `summary.average_data_quality_score` | `99.63` |
| Latest status | `summary.latest_status` | `success` |
| Latest run ID | `latest_ingestion_run.run_id` | Duy ingestion UUID |
| Source name | `latest_ingestion_run.source_name` | `dataflow_technical_report_pdf` |
| Source type | `latest_ingestion_run.source_type` | `pdf` |
| File hash | `latest_ingestion_run.file_hash_sha256` | SHA256 for PDF input |
| Raw path | `latest_ingestion_run.raw_output_path` | Project-relative path |
| Staging path | `latest_ingestion_run.staging_output_path` | Project-relative path |
| Clean path | `latest_ingestion_run.clean_output_path` | Project-relative path |
| Run list | `runs[]` | 4 latest source runs |

Hung's dashboard also uses Phat's view fixture for aggregate database metrics:

```text
DataVision_Hung/demo/fixtures/phat_dashboard_views_sample.json
```

Duy fixture should be used for ingestion lineage details that Phat views may not expose:

```text
file_hash_sha256
raw_output_path
staging_output_path
clean_output_path
document_pages_jsonl_path
document_external_id
ingestion_run_id
```

## Suggestions Mapping

Hung's Suggestions page combines:

```text
dashboard_signals
prediction_result
last_rag_response
```

Duy signals that can become suggestion evidence:

| Suggestion Signal | Duy JSON Path | Intended Use |
| --- | --- | --- |
| Data quality score | `runs[].data_quality_score` | Trigger quality review if below threshold |
| Invalid records | `runs[].records_invalid` | Trigger data cleanup recommendation |
| Missing output paths | `runs[].raw_output_path`, `staging_output_path`, `clean_output_path` | Trigger lineage/path completeness warning |
| PDF readiness | `rag_handoff.parsing_status` | Show whether PDF is RAG-ready |
| Document pages path | `rag_handoff.document_pages_path` | Show RAG handoff is available |
| Prediction payload path | `prediction_context.full_payload_path` | Show ML handoff is available |

Suggested evidence labels:

```json
{
  "source_module": "ingestion",
  "source_view": "duy_latest_ingestion_summary",
  "evidence_type": "data_quality_score",
  "evidence_value": 99.63,
  "generated_from": ["ingestion_logs", "data_quality_summary"]
}
```

## Reports Mapping

Hung's Reports page builds an evidence context with:

```text
source_context
dashboard_signals
suggestions
prediction_result
rag_context
```

Duy evidence rows for the report table:

| Evidence Source | Module | Metric / Signal | Value Source | Used In Section |
| --- | --- | --- | --- | --- |
| DataFlow PDF ingestion | ingestion | Ingestion run ID | `latest_ingestion_run.ingestion_run_id` | Evidence Used |
| DataFlow PDF ingestion | ingestion | File hash | `latest_ingestion_run.file_hash_sha256` | Evidence Used |
| Data quality | ingestion | Data quality score | `latest_ingestion_run.data_quality_score` | Data Quality Limitations |
| Data quality | ingestion | Valid / invalid records | `records_valid`, `records_invalid` | Key Findings |
| Storage lineage | ingestion | Raw / staging / clean paths | output path fields | Evidence Used |
| RAG handoff | ingestion/RAG | Page count and document pages path | `rag_handoff` | Evidence Used |

Important behavior:

```text
Reports should still render when suggestions are empty.
Use "Not available in current data." instead of blocking report generation.
```

## Prediction Mapping

Duy does not run Tuong's model. Duy provides ingestion-ready prediction payloads.

Hung can reference:

| Field | Duy JSON Path |
| --- | --- |
| Stable document key | `prediction_context.document_external_id` |
| DB document ID | `prediction_context.document_db_id` |
| Source DB ID | `prediction_context.source_id` |
| Source name | `prediction_context.source_name` |
| Ingestion run ID | `prediction_context.ingestion_run_id` |
| File name | `prediction_context.file_name` |
| File type | `prediction_context.file_type` |
| Text length | `prediction_context.text_length` |
| Page count | `prediction_context.num_pages` |
| Full payload | `prediction_context.full_payload_path` |

Tuong's returned statuses should remain:

```text
accepted
needs_review
waiting_for_source
failed
```

## Chatbot / RAG Mapping

Duy gives the page-level input package. Lap returns the final RAG response fixture.

Duy fields Hung can show as RAG readiness:

| Field | Duy JSON Path | Meaning |
| --- | --- | --- |
| Document external ID | `rag_handoff.document_external_id` | Stable document key |
| Document pages path | `rag_handoff.document_pages_path` | Lap input file |
| PDF metadata path | `rag_handoff.pdf_metadata_path` | Metadata source |
| Page count | `rag_handoff.page_count` | `36` |
| Non-empty pages | `rag_handoff.non_empty_pages` | `36` |
| Total characters | `rag_handoff.total_characters` | `129028` |
| Parsing status | `rag_handoff.parsing_status` | `ready` |

Lap's final UI fixture should be copied to:

```text
DataVision_Hung/demo/fixtures/lap_rag_response_real.json
```

## ID Alignment

Before Phat DB insertion, Duy's UI fixture keeps:

```json
{
  "source_id": null,
  "document_db_id": null,
  "document_external_id": "doc_dataflow_technical_report",
  "ingestion_run_id": "Duy run UUID"
}
```

Confirmed DB IDs from Phat Week 6 outputs:

| Entity | Confirmed ID |
| --- | ---: |
| `superstore_sales_csv` | `source_id = 1` |
| `dataflow_technical_report_pdf` | `source_id = 2` |
| `dummyjson_products_api` | `source_id = 3` |
| `product_sales_region_excel` | `source_id = 4` |
| `doc_dataflow_technical_report` | `document_db_id = 1` |

Important:

```text
source_id != ingestion_run_id
document_external_id != document_db_id
```

## Current Alignment Notes For Hung

1. `outputs/ui_fixtures/duy_latest_ingestion_summary.json` is Duy's source-of-truth fixture.
2. If Hung wants DB-enriched fixtures, use Phat's confirmed mapping: DataFlow `source_id=2`, `document_db_id=1`.
3. The UI should not assume `source_id` exists before database insert.
4. The UI should display project-relative paths exactly as Duy provides them.
5. If a field is missing, use `Not available in current data.` rather than inventing metrics.
6. Prediction UI should use Tuong's output, not Duy's payload, for `predicted_document_type`, `confidence`, `status`, and `top_predictions`.
7. Chatbot UI should use Lap's output, not Duy's page JSONL directly, for `retrieved_context`, `citations`, and `similarity_score`.
8. Reports should render even when Suggestions are empty.
9. Suggestions should use Duy data quality signals plus Tuong/Lap/Phat signals, not ingestion data alone.
10. Hung should refresh copied fixtures after Duy reruns `scripts/week6_build_ui_fixture_from_ingestion_logs.py`.

## Service Function Mapping

| Hung Function | Primary Provider | Duy Contribution |
| --- | --- | --- |
| `get_dashboard_metrics()` | Phat views | Duy provides source/run quality facts behind Phat views |
| `get_ingestion_status()` | Duy fixture | Duy provides latest run details and lineage paths |
| `get_recent_activity()` | Phat views | Duy source additions appear as recent activity after DB load |
| `classify_document()` | Tuong | Duy provides prediction input payload under `prediction_context.full_payload_path` |
| `classify_documents()` | Tuong | Duy provides 10-payload batch file |
| `ask_rag()` | Lap | Duy provides `outputs/rag_handoff/document_pages.jsonl` used by Lap |
| `generate_suggestions()` | Hung service layer | Duy contributes quality/path/RAG-readiness signals |
| `generate_report()` | Hung service layer | Duy contributes evidence rows and lineage metadata |

## Required Duy Fields Hung Should Support

| Field | Required For | Null Before DB? |
| --- | --- | --- |
| `source_name` | Dashboard, Reports, Suggestions | No |
| `source_id` | Dashboard DB mapping, Reports, Prediction review | Yes |
| `ingestion_run_id` | Dashboard, Reports, lineage | No |
| `document_external_id` | RAG, Prediction, Reports | No for PDF |
| `document_db_id` | RAG DB joins, Prediction review | Yes |
| `data_quality_score` | Dashboard, Suggestions, Reports | No |
| `records_read` / `records_valid` / `records_invalid` | Dashboard, Suggestions, Reports | No |
| `file_hash_sha256` | Reports evidence | No for file sources |
| `raw_output_path` / `staging_output_path` / `clean_output_path` | Reports evidence | No |
| `document_pages_jsonl_path` | RAG readiness | No for PDF |

## What Hung Should Return To Duy

| Return Item | Format | Why Duy Needs It |
| --- | --- | --- |
| Dashboard display confirmation | Screenshot or markdown note | Proves Duy fixture is UI-ready |
| Missing field list | Markdown table | Duy can update fixture builder |
| Suggestion signal needs | Markdown or JSON | Duy can expose new quality signals |
| Report evidence needs | Markdown or JSON | Duy can add lineage/evidence metadata |
| Final UI field names | Markdown contract | Duy can keep output stable |
| Status/path formatting rules | Markdown note | Duy can match UI display conventions |
| Fixture freshness confirmation | Markdown note | Confirms Hung copied latest Duy fixture after rerun |
| DB-enriched fixture preference | Markdown note | Confirms whether Duy should publish a second post-DB fixture |

## Acceptance Checklist

Hung should confirm:

```text
[ ] Dashboard loads Duy latest ingestion fixture
[ ] Dashboard displays total sources, records, quality score, latest status
[ ] Dashboard displays file hash and raw/staging/clean paths
[ ] Suggestions can use data_quality_score and records_invalid
[ ] Reports can render ingestion evidence without requiring suggestions
[ ] Prediction page can reference Duy prediction payload context
[ ] Chatbot page can reference Duy RAG handoff and Lap RAG response
[ ] UI handles source_id/document_db_id being null before DB insert
[ ] UI can use Phat-enriched IDs after DB insert
```
