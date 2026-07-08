# Week 6 Phat Mapping Review

Owner: Nguyen Minh Duy  
Partner: Phat - Database / PostgreSQL / pgvector Owner  
Review date: 2026-07-08

## Purpose

This document summarizes the latest mapping review between Duy's ingestion outputs and Phat's Week 6 PostgreSQL outputs.

The integration goal is:

```text
Duy ingestion outputs
  -> Phat PostgreSQL
  -> Lap pgvector chunks
  -> Tuong prediction logs
  -> Phi/Hung dashboard views
```

## Phat Inputs Reviewed

| Folder | Purpose |
| --- | --- |
| `DataVision_Phat/week6/database/` | Schema, setup, loaders, validation, pgvector/prediction scripts |
| `DataVision_Phat/week6/docs/` | Duy/Phat, Lap/Phat, Tuong/Phat, dashboard contracts |
| `DataVision_Phat/week6/outputs/` | Real DB-shaped outputs for Duy, Lap, Tuong, Phi/Hung |

## Confirmed ID Mapping

| Duy identifier | Phat table.column | Confirmed DB value |
| --- | --- | --- |
| `superstore_sales_csv` | `sources.name -> sources.id` | `source_id=1` |
| `dataflow_technical_report_pdf` | `sources.name -> sources.id` | `source_id=2` |
| `dummyjson_products_api` | `sources.name -> sources.id` | `source_id=3` |
| `product_sales_region_excel` | `sources.name -> sources.id` | `source_id=4` |
| `doc_dataflow_technical_report` | `documents.document_external_id -> documents.id` | `document_db_id=1` |

ID rule remains:

```text
source_id != ingestion_run_id
document_external_id != document_db_id
```

## Confirmed Duy Data Loaded By Phat

| Output | Phat file | Result |
| --- | --- | --- |
| Sources | `week6/outputs/ingestion_data_Duy/sources_202607051438.json` | 4 sources |
| Pipeline runs | `week6/outputs/ingestion_data_Duy/pipeline_runs_202607051438.json` | pipeline run export exists |
| Ingestion logs | `week6/outputs/ingestion_data_Duy/ingestion_logs_202607051438.json` | 4 success logs |
| Documents | `week6/outputs/ingestion_data_Duy/documents_202607051439.json` | 1 DataFlow PDF document |
| Document pages | `week6/outputs/ingestion_data_Duy/document_pages_202607051442.json` | 36 pages |
| Structured records | `week6/outputs/ingestion_data_Duy/structured_records_202607051442.json` | structured records export exists |

Machine-readable summary:

```text
outputs/phat_handoff/phat_week6_mapping_summary.json
```

Latest integration status from the summary:

| Check | Status |
| --- | --- |
| Duy ingestion loaded into Phat output exports | `true` |
| `document_external_id` resolved to internal `documents.id` | `true` |
| Structured records loaded | `true` |
| Lap chunks loaded against Duy PDF document | `true` |
| Tuong prediction logs loaded | `true` |
| Phi/Hung dashboard views exported | `true` |

## Confirmed Downstream Integration Through Phat

| Downstream module | Phat output | Meaning |
| --- | --- | --- |
| Lap RAG | `week6/outputs/document_chunk_data_Lap/document_chunks_202607071256.json` | DataFlow PDF was chunked and inserted with `document_id=1`, stable `chunk_id`, page number, 384-dim embedding, and `document_external_id` metadata |
| Tuong Prediction | `week6/outputs/prediction_log_data_Tuong/prediction_logs_202607071251.json` | 10 prediction logs inserted from Duy-style payloads |
| Phi/Hung UI | `week6/outputs/dashboard_view_samples_PhiHung/*.json` | Dashboard views now return integrated rows |

## Dashboard Evidence

From:

```text
DataVision_Phat/week6/outputs/dashboard_view_samples_PhiHung/v_dashboard_overview_202607071300.json
```

Current dashboard overview:

```json
{
  "total_sources": 4,
  "total_documents": 1,
  "successful_ingestions": 4,
  "failed_ingestions": 0,
  "total_rag_queries": 0,
  "total_predictions": 10
}
```

From:

```text
DataVision_Phat/week6/outputs/dashboard_view_samples_PhiHung/v_data_quality_dashboard_202607071300.json
```

Duy sources show:

| Source | Status | Records read | Records valid | Records invalid | Data quality |
| --- | --- | ---: | ---: | ---: | ---: |
| `superstore_sales_csv` | `success` | 9,994 | 9,994 | 0 | 100.0 |
| `dataflow_technical_report_pdf` | `success` | 36 | 36 | 0 | 100.0 |
| `dummyjson_products_api` | `success` | 30 | 30 | 0 | 99.0 |
| `product_sales_region_excel` | `success` | 1,500 | 1,500 | 0 | 99.51 |

## Dashboard View Samples Reviewed

Phat exported the following Week 6 dashboard view samples for Phi/Hung. Duy can reference these in reports and handoff discussions because they are downstream evidence created from Duy + Lap + Tuong data.

| View | Row Count | Purpose |
| --- | ---: | --- |
| `v_dashboard_overview` | 1 | System-level metric cards |
| `v_data_quality_dashboard` | 4 | Duy ingestion quality rows |
| `v_document_quality_summary` | 1 | Document processing status |
| `v_document_rag_readiness` | 1 | DataFlow PDF chunk/RAG readiness |
| `v_ingestion_health` | 1 | Aggregate ingestion health |
| `v_latest_ingestion_runs` | 4 | Latest source run list |
| `v_prediction_confidence_summary` | 4 | Prediction confidence distribution |
| `v_prediction_review_queue` | 5 | Manual review queue |
| `v_rag_daily_metrics` | 0 | No RAG query logs yet |
| `v_recent_activity` | 4 | Dashboard activity feed |
| `v_source_quality_detail` | 4 | Source-level quality detail |
| `v_source_quality_summary` | 4 | Source-level volume and quality summary |

## Prediction Log Evidence

From:

```text
DataVision_Phat/week6/outputs/prediction_log_data_Tuong/prediction_logs_202607071251.json
```

Current result:

```text
prediction_logs = 10
source_id resolved = 10/10
document_id resolved = 1/10
```

This is expected:

- `doc_dataflow_technical_report` maps to the real `documents.id=1`.
- The other 9 payloads are synthetic test cases generated for Tuong, so `prediction_logs.document_id = null` is acceptable.

## Known Phat Schema Note

The reviewed `schema_v4.sql` and `setup_database_v2.sql` still appear to have a missing comma in `prediction_logs`:

```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
CONSTRAINT chk_prediction_status
```

Expected:

```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
CONSTRAINT chk_prediction_status
```

This does not change Duy's mapping, but Phat should fix it before running schema setup from scratch.

Schema capabilities confirmed from Phat `schema_v4.sql`:

| Requirement | Confirmed |
| --- | --- |
| `CREATE EXTENSION IF NOT EXISTS vector` | yes |
| `sources.name` unique constraint | yes |
| `documents.document_external_id` | yes |
| `document_chunks.embedding vector(384)` | yes |
| `document_chunks.chunk_id` | yes |
| `ingestion_logs.data_quality_score` | yes |
| `prediction_logs.status` | yes |
| `prediction_logs.review_reason` | yes |

## Cleanup Review

Duy-side cleanup performed during this review:

```text
Removed generated __pycache__ folders from DataVision_Duy.
Kept week1/week2 folders because they are historical deliverables and current Week 6 outputs still reference week2 paths.
```

## Duy Files Updated For This Mapping

| Duy file | Role |
| --- | --- |
| `docs/week6_ingestion_to_schema_v3_mapping.md` | Main Duy -> Phat mapping source of truth |
| `docs/week6_ingestion_to_schema_v4_mapping.md` | Schema-v4 alias for the latest Phat mapping |
| `docs/week6_database_loading_result.md` | DB loading status and Phat output evidence |
| `docs/week6_team_integration_handoff.md` | Cross-team handoff with confirmed Phat IDs |
| `outputs/phat_handoff/phat_week6_mapping_summary.json` | Machine-readable Phat mapping summary |
| `scripts/week6_build_phat_mapping_summary.py` | Regenerates the machine-readable summary from Phat outputs |
