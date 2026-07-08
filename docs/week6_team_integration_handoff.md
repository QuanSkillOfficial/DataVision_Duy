# Week 6 Team Integration Handoff

Owner: Nguyen Minh Duy  
Role: Data Engineering / Ingestion Owner  
Repository root: `F:/data/new/quanskill/DataVision_Duy`

## Purpose

Week 6 is focused on integration, not adding many isolated features.

The main risk is:

```text
Every module works separately,
but the full platform has not been tested together.
```

This document explains exactly:

1. What outputs Duy provides to each team member.
2. Which file paths each team member should use.
3. Which fields are important.
4. What each team member must return to Duy.
5. How the team should align IDs and contracts.

The Week 6 platform flow is:

```text
Duy ingestion
  -> Phat PostgreSQL
  -> Lap RAG / pgvector
  -> Tuong prediction
  -> Phi/Hung dashboard, suggestions, reports
```

The integration keywords for this week are:

```text
connect
insert
query
retrieve
predict
display
test
```

## Current Duy Source Outputs

| Source | Source Type | Run ID | Records / Pages Valid | Data Quality Score | Main Consumer |
| --- | --- | --- | ---: | ---: | --- |
| `superstore_sales_csv` | `csv` | `10ed4959-5ace-4ff7-9b30-da28321d6708` | `9994` | `100.0` | Phat, Phi/Hung |
| `dataflow_technical_report_pdf` | `pdf` | `8e18bd87-27e5-4aa1-9566-805ffd552fdb` | `36` pages | `100.0` | Phat, Lap, Tuong, Phi/Hung |
| `dummyjson_products_api` | `api` | `9cce3b5c-b83d-4873-86e1-b99de889b077` | `30` | `99.0` | Phat, Phi/Hung |
| `product_sales_region_excel` | `excel` | `a896a888-57f0-4ea9-9083-f860c2078f7d` | `1500` | `99.51` | Phat, Phi/Hung |

Total integration-ready output:

```text
sources: 4
pipeline_runs: 4
ingestion_logs: 4
structured_records: 11524
documents: 1
document_pages: 36
```

## Common ID Rules For All Teams

These rules must be followed by everyone.

| Field | Owner | Meaning | Current Value / Example | Notes |
| --- | --- | --- | --- | --- |
| `source_name` | Duy | Stable source name from config | `dataflow_technical_report_pdf` | Use this before DB IDs exist |
| `source_id` | Phat | PostgreSQL primary key from `sources.id` | `null` before DB insert | Do not use `run_id` as `source_id` |
| `run_id` | Duy | Ingestion execution UUID | `8e18bd87-27e5-4aa1-9566-805ffd552fdb` | Same meaning as `ingestion_run_id` |
| `ingestion_run_id` | Duy | Alias for ingestion execution UUID | `8e18bd87-27e5-4aa1-9566-805ffd552fdb` | Maps to `ingestion_logs.run_id` |
| `document_external_id` | Duy | Stable string document key | `doc_dataflow_technical_report` | Maps to `documents.document_external_id` |
| `document_db_id` | Phat | PostgreSQL primary key from `documents.id` | `null` before DB insert | Used by `document_pages`, `document_chunks`, `rag_query_logs` |

Important:

```text
source_id != ingestion_run_id
document_external_id != document_db_id
```

Before database insertion:

```json
{
  "source_id": null,
  "document_db_id": null,
  "document_external_id": "doc_dataflow_technical_report",
  "ingestion_run_id": "8e18bd87-27e5-4aa1-9566-805ffd552fdb"
}
```

After Phat loads Duy outputs into PostgreSQL:

```json
{
  "source_id": 2,
  "document_db_id": 1,
  "document_external_id": "doc_dataflow_technical_report",
  "ingestion_run_id": "8e18bd87-27e5-4aa1-9566-805ffd552fdb"
}
```

Current IDs confirmed from Phat Week 6 outputs:

| `source_name` / `document_external_id` | Confirmed DB ID |
| --- | ---: |
| `superstore_sales_csv` | `source_id=1` |
| `dataflow_technical_report_pdf` | `source_id=2` |
| `dummyjson_products_api` | `source_id=3` |
| `product_sales_region_excel` | `source_id=4` |
| `doc_dataflow_technical_report` | `document_db_id=1` |

## How To Regenerate Duy Outputs

Run from repository root:

```powershell
cd F:\data\new\quanskill\DataVision_Duy
```

Run all ingestion configs:

```powershell
python -m data_engineering.pipelines.ingestion_engine --all
```

Build PostgreSQL dry-run loading plan:

```powershell
python scripts/load_ingestion_outputs_to_postgres.py
```

Build RAG handoff package for Lap:

```powershell
python scripts/week6_build_rag_handoff_package.py
```

Build prediction payload for Tuong:

```powershell
python -c "from data_engineering.pipelines.prediction_payload_builder import build_pdf_prediction_payload; import json, pathlib; pathlib.Path('logs/prediction_payloads').mkdir(parents=True, exist_ok=True); pathlib.Path('logs/prediction_payloads/duy_pdf_prediction_payload.json').write_text(json.dumps(build_pdf_prediction_payload(), indent=2, ensure_ascii=False), encoding='utf-8')"
```

Build UI fixtures for Phi/Hung:

```powershell
python scripts/week6_build_ui_fixture_from_ingestion_logs.py
```

Run integration smoke test:

```powershell
python scripts/week6_end_to_end_smoke_test.py
```

Validate:

```powershell
python scripts/validate_week6.py
pytest tests/data_tests/
```

Expected:

```text
Week 6 validation passed
20 passed
```

## Duy -> Phat: Database / PostgreSQL Handoff

### What Duy Gives Phat

Phat should use these files to test database insertion.

| File / Folder | Exact Path | Purpose |
| --- | --- | --- |
| DB dry-run loading plan | `logs/db_load_dry_run/duy_to_phat_db_load_plan.json` | Shows what Duy outputs should insert into Phat tables |
| Run-specific logs | `logs/runs/*.json` | One ingestion log per source |
| Append-only run history | `logs/ingestion_runs.jsonl` | All ingestion runs in JSONL format |
| File manifests | `logs/manifests/*_manifest.json` | SHA256 hash, file size, source name, ingestion timestamp |
| CSV clean data | `week2/data/clean/csv/superstore_clean.csv` | Structured records for `structured_records` |
| Excel clean data | `week2/data/clean/excel/product_sales_region_clean.csv` | Structured records for `structured_records` |
| API clean data | `week2/data/clean/api/dummyjson_products_clean.csv` | Structured records for `structured_records` |
| PDF metadata | `week2/logs/pdf_metadata.json` | Document metadata for `documents` |
| PDF pages JSONL | `week2/data/staging/pdf/document_pages.jsonl` | Page-level text for `document_pages` |
| RAG-ready PDF pages | `outputs/rag_handoff/document_pages.jsonl` | Same page-level text copied for RAG handoff |
| Schema mapping | `docs/week6_ingestion_to_schema_v3_mapping.md` | Maps Duy fields to Phat schema |
| Latest schema-v4 mapping alias | `docs/week6_ingestion_to_schema_v4_mapping.md` | Clarifies mapping against Phat `schema_v4.sql` |
| DB loading result note | `docs/week6_database_loading_result.md` | Current DB dry-run / real-run status |
| Duy + Phat result note | `docs/week6_duy_to_phat_db_load_result.md` | Integration result note |
| Phat mapping review | `docs/week6_phat_mapping_review.md` | Human-readable review of Phat outputs and schema notes |
| Phat machine-readable mapping | `outputs/phat_handoff/phat_week6_mapping_summary.json` | Source IDs, document IDs, counts, dashboard view samples |

### Tables Phat Should Load

| Phat Table | Duy Input File | Insert Rule |
| --- | --- | --- |
| `sources` | `logs/runs/*.json` | Insert or get by `source_name` |
| `pipeline_runs` | `logs/runs/*.json` | Insert one row per latest source run using `run_name = source_name + "_" + run_id` |
| `ingestion_logs` | `logs/runs/*.json` | Insert records read/valid/invalid, paths, quality score |
| `documents` | `week2/logs/pdf_metadata.json` | Insert one PDF document with `document_external_id` |
| `document_pages` | `week2/data/staging/pdf/document_pages.jsonl` | Insert 36 page records using internal `documents.id` |
| `structured_records` | clean CSV/API/Excel files | Insert row data as JSONB or agreed format |

### Required Field Mapping For Phat

| Duy Field | Phat Table.Column | Notes |
| --- | --- | --- |
| `source_name` | `sources.name` | Should be unique |
| `source_type` | `sources.source_type` | `csv`, `excel`, `api`, `pdf` |
| `run_id` | `ingestion_logs.run_id`; included in `pipeline_runs.run_name` | Phat `schema_v4.sql` does not currently have `pipeline_runs.run_id` |
| `start_time` | `pipeline_runs.start_time`, `ingestion_logs.started_at` | Timestamp from Duy run log |
| `end_time` | `pipeline_runs.end_time`, `ingestion_logs.ended_at` | Timestamp from Duy run log |
| `status` | `pipeline_runs.status`, `ingestion_logs.status` | Current values: `success`, `failed`, `partial_success`, `running` |
| `records_read` | `ingestion_logs.records_read` | From run log |
| `records_valid` | `ingestion_logs.records_valid` | From run log |
| `records_invalid` | `ingestion_logs.records_invalid` | From run log |
| `data_quality_score` | `ingestion_logs.data_quality_score` | Number from 0 to 100 |
| `raw_output_path` | `ingestion_logs.raw_output_path` | Project-relative path |
| `staging_output_path` | `ingestion_logs.staging_output_path` | Project-relative path |
| `clean_output_path` | `ingestion_logs.clean_output_path` | Project-relative path |
| `manifest_path` | `ingestion_logs.manifest_path` | Path under `logs/manifests/` |
| `file_hash_sha256` | `documents.file_hash_sha256` | For PDF document |
| `document_external_id` | `documents.document_external_id` | `doc_dataflow_technical_report` |
| `page_number` | `document_pages.page_number` | Starts at 1 |
| `text` | `document_pages.page_text` | Page text from JSONL |
| `character_count` | `document_pages.character_count` | Page character count |
| `is_empty` | `document_pages.is_empty` | Boolean |
| clean CSV/API/Excel row | `structured_records.record_data` | Row serialized as JSONB |
| fixed value `clean` | `structured_records.status` | Phat schema uses `status`, not `processing_status` |

### What Phat Must Return To Duy

Phat should return these outputs after DB integration:

| Output From Phat | Expected Path / Format | Why Duy Needs It |
| --- | --- | --- |
| Real `source_id` mapping | JSON or markdown table | Fill `source_id` in future payloads |
| Real `document_db_id` mapping | JSON or markdown table | Fill `document_db_id` for PDF/RAG/prediction |
| Insert proof | Screenshot or query output | Prove Duy outputs loaded successfully |
| Validation query result | `validation_queries_v2.sql` output | Prove FK and quality checks pass |
| Dashboard view samples | JSON files from Phat views | Phi/Hung can replace fixtures |

Confirmed mapping from Phat:

```json
{
  "source_name": "dataflow_technical_report_pdf",
  "source_id": 2,
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": 1,
  "ingestion_run_id": "8e18bd87-27e5-4aa1-9566-805ffd552fdb"
}
```

### Phat Output Files Now Available

| Output | Path | Current proof |
| --- | --- | --- |
| Duy ingestion exports | `DataVision_Phat/week6/outputs/ingestion_data_Duy/*.json` | 4 sources, 4 ingestion logs, 1 document, 36 document pages |
| Lap document chunks | `DataVision_Phat/week6/outputs/document_chunk_data_Lap/document_chunks_202607071256.json` | Chunks use `document_id=1`, `chunk_id`, page numbers, 384-dim embeddings |
| Tuong prediction logs | `DataVision_Phat/week6/outputs/prediction_log_data_Tuong/prediction_logs_202607071251.json` | 10 prediction logs inserted |
| Phi/Hung dashboard views | `DataVision_Phat/week6/outputs/dashboard_view_samples_PhiHung/*.json` | Dashboard views return real integrated rows |

Phat view sample row counts:

| View | Rows |
| --- | ---: |
| `v_dashboard_overview` | 1 |
| `v_data_quality_dashboard` | 4 |
| `v_document_rag_readiness` | 1 |
| `v_latest_ingestion_runs` | 4 |
| `v_prediction_review_queue` | 5 |
| `v_recent_activity` | 4 |
| `v_source_quality_detail` | 4 |
| `v_source_quality_summary` | 4 |
| `v_rag_daily_metrics` | 0 |

Dashboard overview from Phat:

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

### Phat Acceptance Checklist

Phat should confirm:

```text
[ ] sources has 4 Duy sources
[ ] pipeline_runs has 4 Duy runs
[ ] ingestion_logs has 4 Duy logs
[ ] structured_records has 11524 rows or agreed sample subset
[ ] documents has DataFlow PDF with document_external_id
[ ] document_pages has 36 rows
[ ] documents.document_external_id maps to document_pages.document_id through internal documents.id
[ ] dashboard views return rows from real Duy data
```

## Duy -> Lap: RAG / Embeddings / Retrieval Handoff

### What Duy Gives Lap

Lap should use the RAG handoff package, not the raw PDF directly.

| File | Exact Path | Purpose |
| --- | --- | --- |
| Page-level text JSONL | `outputs/rag_handoff/document_pages.jsonl` | Main input for chunking |
| PDF metadata | `outputs/rag_handoff/pdf_metadata.json` | File name, page count, character count |
| Handoff manifest | `outputs/rag_handoff/rag_handoff_manifest.json` | Machine-readable summary |
| Handoff summary | `outputs/rag_handoff/rag_handoff_summary.md` | Human-readable summary |
| RAG readiness doc | `docs/week6_document_pages_for_rag_confirmed.md` | Confirms page count and quality |
| Lap mapping review | `docs/week6_lap_rag_mapping_review.md` | Detailed Duy-to-Lap input/output contract |
| Lap machine-readable mapping | `outputs/lap_handoff/lap_week6_mapping_summary.json` | JSON summary of page stats, ID rules, pgvector mapping |

### DataFlow PDF Facts For Lap

| Field | Value |
| --- | --- |
| `document_external_id` | `doc_dataflow_technical_report` |
| `source_name` | `dataflow_technical_report_pdf` |
| `file_name` | `DataFlow_Technical_Report.pdf` |
| `page_count` | `36` |
| `non_empty_pages` | `36` |
| `empty_pages` | `0` |
| `total_characters` | `129028` |
| `ingestion_run_id` | `8e18bd87-27e5-4aa1-9566-805ffd552fdb` |
| `parsing_status` | `ready` |
| `document_db_id` from Phat if DB-loaded | `1` |
| Phat document chunks proof | `293` chunks from `DataVision_Phat/week6/outputs/document_chunk_data_Lap/document_chunks_202607071256.json` |
| Lap code readiness | `load_document_pages_to_pgvector.py` and schema-v4 mapping exist |
| Lap live notebook proof | Pending: notebook exists but has no executed outputs |
| Lap UI fixture proof | Pending: `outputs/ui_fixtures/lap_rag_response_real.json` not found in Lap repo |

### JSONL Record Shape For Lap

Each line in `outputs/rag_handoff/document_pages.jsonl` should be treated as one page.

```json
{
  "document_id": "doc_dataflow_technical_report",
  "document_external_id": "doc_dataflow_technical_report",
  "file_name": "DataFlow_Technical_Report.pdf",
  "page_number": 1,
  "text": "page text...",
  "character_count": 2650,
  "is_empty": false
}
```

Lap's loader accepts the page text from `text`, `page_text`, or `page_content`. Duy currently provides `text`, so no field rename is needed.

If Lap needs database insertion:

```text
Duy document_external_id
  -> Phat documents.document_external_id
  -> Phat documents.id
  -> document_chunks.document_id
```

Lap should not insert string document IDs into integer FK columns.

Current confirmed DB mapping from Phat's Week 6 outputs:

```text
doc_dataflow_technical_report -> documents.id = 1
```

### Expected Chunk ID Convention

Recommended:

```text
doc_dataflow_technical_report_page_1_chunk_000
doc_dataflow_technical_report_page_1_chunk_001
doc_dataflow_technical_report_page_2_chunk_000
```

Lap's current Week 6 chunk defaults:

| Setting | Value |
| --- | --- |
| Chunk size | `512` |
| Overlap | `50` |
| Empty page handling | Skip records where `is_empty = true` |
| Embedding model | `all-MiniLM-L6-v2` |
| Embedding dimension | `384` |
| pgvector field | `document_chunks.embedding vector(384)` |

### What Lap Must Return To Duy

| Output From Lap | Expected Path / Format | Why Duy Needs It |
| --- | --- | --- |
| Confirmation that JSONL loads | markdown note | Verify PDF output is RAG-ready |
| Page/chunk stats | markdown or JSON | Confirm pages converted to chunks |
| Vector insert proof | screenshot, SQL output, or JSON | Confirm chunks were inserted into Phat pgvector |
| Retrieval evaluation | markdown or CSV | Confirm top-k retrieval works on DataFlow PDF |
| Failed/empty page issues | markdown note | Duy can fix PDF extraction if needed |
| Real RAG response fixture | JSON | Phi/Hung can display citations |
| Required metadata changes | markdown note | Duy can update future JSONL output |
| Executed notebook or screenshot | notebook outputs or image | Prove live pgvector retrieval ran |
| RAG query log proof | SQL output or JSON | Prove `rag_query_logs` insert is ready |

Expected Lap response fixture:

```json
{
  "question": "What is DataFlow?",
  "answer": null,
  "retrieved_context": [
    {
      "chunk_id": "doc_dataflow_technical_report_page_4_chunk_000",
      "document_external_id": "doc_dataflow_technical_report",
      "document_db_id": 1,
      "file_name": "DataFlow_Technical_Report.pdf",
      "page_number": 4,
      "chunk_text": "...",
      "similarity_score": 0.84
    }
  ],
  "citations": [
    {
      "file_name": "DataFlow_Technical_Report.pdf",
      "page_number": 4,
      "chunk_id": "doc_dataflow_technical_report_page_4_chunk_000"
    }
  ],
  "status": "retrieval_only",
  "model": "all-MiniLM-L6-v2"
}
```

### Lap Acceptance Checklist

Lap should confirm:

```text
[ ] Loaded outputs/rag_handoff/document_pages.jsonl
[ ] Loaded 36 pages
[ ] Skipped 0 empty pages
[ ] Created page-aware chunks
[ ] Preserved document_external_id
[ ] Generated chunk IDs with page numbers
[ ] Generated 384-dimensional embeddings
[ ] Inserted chunks into Phat pgvector table or prepared exact insert payload
[ ] Resolved document_external_id to internal documents.id before pgvector insert
[ ] Returned top-k retrieval result with chunk_id, page_number, similarity_score
[ ] Returned citation-ready RAG fixture for Phi/Hung
[ ] Returned live execution proof rather than only fixture metrics
```

## Duy -> Tuong: Prediction Handoff

### What Duy Gives Tuong

Tuong should use Duy's prediction payload as real ingestion input for document classification.

| File | Exact Path | Purpose |
| --- | --- | --- |
| PDF prediction payload | `logs/prediction_payloads/duy_pdf_prediction_payload.json` | Main input for Tuong classifier |
| Batch prediction payload | `outputs/prediction_payloads/tuong_week6_prediction_payloads.json` | Main 10-payload Week 6 test input |
| Batch prediction payload copy | `logs/prediction_payloads/tuong_week6_prediction_payloads.json` | Backward-compatible log path |
| Individual prediction payloads | `outputs/prediction_payloads/01_*.json` to `10_*.json` | Debug individual test cases |
| Prediction contract | `week2/docs/ingestion_to_prediction_contract.md` | Field contract |
| ID mapping contract | `docs/week6_id_mapping_contract.md` | Separates source/run/document IDs |
| Tuong mapping review | `docs/week6_tuong_prediction_mapping_review.md` | Detailed Duy-to-Tuong input/output contract |
| Tuong machine-readable mapping | `outputs/tuong_handoff/tuong_week6_mapping_summary.json` | JSON summary of payloads, results, statuses |
| UI fixture with prediction context | `outputs/ui_fixtures/duy_latest_ingestion_summary.json` | Contains `prediction_context` block |

### Required Payload Fields For Tuong

```json
{
  "document_id": "doc_dataflow_technical_report",
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": null,
  "source_id": null,
  "source_name": "dataflow_technical_report_pdf",
  "ingestion_run_id": "8e18bd87-27e5-4aa1-9566-805ffd552fdb",
  "file_name": "DataFlow_Technical_Report.pdf",
  "file_type": "pdf",
  "file_size": 2857707,
  "text_length": 129028,
  "num_pages": 36,
  "source_system": "manual_upload",
  "parsing_status": "ready",
  "extracted_text": "..."
}
```

### Important Rules For Tuong

```text
source_id is null before Phat DB insert.
document_db_id is null before Phat DB insert.
ingestion_run_id is the Duy run UUID.
document_external_id is the stable document key.
```

Tuong should not treat `ingestion_run_id` as `source_id`.

Current confirmed DB mapping from Phat's Week 6 outputs:

```json
{
  "dataflow_technical_report_pdf": {
    "source_id": 2
  },
  "doc_dataflow_technical_report": {
    "document_db_id": 1
  }
}
```

### Duy's 10 Payloads For Tuong

| # | Document External ID | Source | Test Case |
| ---: | --- | --- | --- |
| 1 | `doc_dataflow_technical_report` | `dataflow_technical_report_pdf` | Full PDF document |
| 2 | `doc_dataflow_technical_report_intro_pages` | `dataflow_technical_report_pdf` | PDF intro section |
| 3 | `doc_dataflow_technical_report_architecture_page` | `dataflow_technical_report_pdf` | PDF architecture page |
| 4 | `doc_dataflow_technical_report_related_work` | `dataflow_technical_report_pdf` | PDF related work section |
| 5 | `doc_superstore_sales_csv_summary` | `superstore_sales_csv` | CSV structured summary |
| 6 | `doc_product_sales_region_excel_summary` | `product_sales_region_excel` | Excel structured summary |
| 7 | `doc_dummyjson_products_api_summary` | `dummyjson_products_api` | API structured summary |
| 8 | `doc_short_text_quality_gate` | `dataflow_technical_report_pdf` | Short text quality gate |
| 9 | `doc_empty_text_quality_gate` | `dataflow_technical_report_pdf` | Empty text quality gate |
| 10 | `doc_missing_file_name_validation` | `dataflow_technical_report_pdf` | Missing required file name |

Tuong's Week 6 output currently reports:

| Status | Count |
| --- | ---: |
| `accepted` | `5` |
| `needs_review` | `2` |
| `waiting_for_source` | `2` |
| `failed` | `1` |

Important real-data warning from Tuong:

```text
The current model can be overconfident on real Duy payloads.
Low-confidence or unreviewed predictions should not be used as hard RAG filters.
```

### Tuong Output Files Reviewed

Use these Tuong files when checking whether Duy's payload works with the prediction module.

| Tuong Output | Exact Path | How Duy / Team Should Use It |
| --- | --- | --- |
| Full 10-payload prediction result | `DataVision_Tuong/outputs/week6_duy_prediction_results.json` | Main Week 6 source of truth for prediction statuses and counts |
| Real-data evaluation report | `DataVision_Tuong/docs/week6_real_data_prediction_eval.md` | Explains low real-data confidence and overconfident accepted cases |
| Prediction DB integration note | `DataVision_Tuong/docs/week6_prediction_db_integration_result.md` | Useful, but contains older 4-payload examples; verify against the 10-payload JSON output |
| Single UI fixture | `DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_response_real.json` | Phi/Hung demo state, not full batch evidence |
| Batch UI fixture | `DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_batch_response.json` | Sample UI batch fixture with 5 items, not the full 10-payload result |
| Review queue fixture | `DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_review_queue_sample.json` | Sample review queue for Phi/Hung |
| RAG metadata filter payload | `DataVision_Tuong/outputs/rag_metadata/document_type_filter_payload.json` | Lap should use only safe/reviewed predictions as hard filters |

Tuong's real evaluation reports:

```text
total_payloads = 10
accepted = 5
needs_review = 2
waiting_for_source = 2
failed = 1
strict_top1_correct = 1/7 predictable documents
```

Platform decision:

```text
Prediction output is integration-ready, but current real-data accuracy requires a human-in-the-loop review workflow.
Do not let unreviewed predictions automatically restrict RAG retrieval.
```

### What Tuong Must Return To Duy

| Output From Tuong | Expected Path / Format | Why Duy Needs It |
| --- | --- | --- |
| Single prediction response | JSON | Confirm Duy payload works |
| Batch prediction response | JSON | Prepare multi-document ingestion |
| Prediction log payloads | JSON or markdown | Phat can insert into `prediction_logs` |
| UI fixtures | JSON | Phi/Hung can display prediction/review states |
| RAG metadata filter payload | JSON | Lap can use only reliable metadata |
| Review status | `accepted`, `needs_review`, `waiting_for_source`, `failed` | Align with Phat/Phi/Hung |
| Required field changes | markdown note | Duy can update payload builder |
| Min text rule confirmation | markdown note | Duy can validate future PDF extraction |

Expected Tuong response:

```json
{
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": null,
  "source_id": null,
  "source_name": "dataflow_technical_report_pdf",
  "ingestion_run_id": "8e18bd87-27e5-4aa1-9566-805ffd552fdb",
  "predicted_document_type": "report",
  "confidence": 0.39,
  "status": "needs_review",
  "review_reason": "Prediction confidence below threshold",
  "model_version": "document_classifier_v1",
  "top_predictions": [
    {
      "label": "report",
      "score": 0.39
    }
  ]
}
```

### Tuong Acceptance Checklist

Tuong should confirm:

```text
[ ] Payload loads from logs/prediction_payloads/duy_pdf_prediction_payload.json
[ ] source_id=null is accepted before DB insert
[ ] document_external_id is used as stable document key
[ ] extracted_text length is sufficient
[ ] Output uses accepted / needs_review / waiting_for_source / failed
[ ] Prediction result can be inserted into Phat prediction_logs
[ ] Prediction result can be displayed by Phi/Hung
[ ] RAG filtering rule is explicit: only accepted/reviewed predictions should be hard filters
```

## Duy -> Phi/Hung: UI / Suggestions / Reports Handoff

### What Duy Gives Phi/Hung

Phi/Hung should use these real output-shaped fixtures instead of invented mock ingestion data.

| File | Exact Path | Purpose |
| --- | --- | --- |
| Latest ingestion summary | `outputs/ui_fixtures/duy_latest_ingestion_summary.json` | Main dashboard fixture |
| Data quality summary | `outputs/ui_fixtures/duy_data_quality_summary.json` | Source-level quality signals |
| PDF document summary | `outputs/ui_fixtures/duy_pdf_document_summary.json` | PDF/RAG document summary |
| Backward-compatible dashboard fixture | `logs/ui_fixtures/duy_ingestion_dashboard_fixture.json` | Older path if UI already uses logs |
| UI fixture contract | `docs/week6_phi_hung_ui_fixture_contract.md` | Field descriptions |
| Hung UI mapping review | `docs/week6_hung_ui_mapping_review.md` | Page-by-page mapping from Duy outputs to Hung UI |
| Hung machine-readable mapping | `outputs/hung_handoff/hung_week6_mapping_summary.json` | JSON summary of fixtures, fields, IDs, and expected feedback |

### Main UI Fixture Shape

The main fixture is:

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

### Fields Phi/Hung Can Display

| UI Field | Source JSON Path | Meaning |
| --- | --- | --- |
| Total sources | `summary.total_sources` | Current value: `4` |
| Total records read | `summary.total_records_read` | Current value: `11560` |
| Total records valid | `summary.total_records_valid` | Current value: `11560` |
| Total records invalid | `summary.total_records_invalid` | Current value: `0` |
| Average quality score | `summary.average_data_quality_score` | Current value: `99.63` |
| Latest status | `summary.latest_status` | Current value: `success` |
| RAG-ready documents | `summary.rag_ready_documents` | Current value: `1` |
| Prediction payload available | `summary.prediction_payload_available` | Current value: `true` |
| Latest run ID | `latest_ingestion_run.run_id` | PDF run ID |
| Latest source name | `latest_ingestion_run.source_name` | `dataflow_technical_report_pdf` |
| File hash | `latest_ingestion_run.file_hash_sha256` | SHA256 for PDF |
| Raw path | `latest_ingestion_run.raw_output_path` | Raw PDF path |
| Staging path | `latest_ingestion_run.staging_output_path` | PDF pages staging CSV |
| Clean path | `latest_ingestion_run.clean_output_path` | PDF pages clean CSV |
| Document pages path | `latest_ingestion_run.document_pages_jsonl_path` | RAG input path |

### Suggested UI Usage

| UI Page | Duy Data To Use |
| --- | --- |
| Dashboard | `summary`, `latest_ingestion_run`, `runs` |
| Suggestions | low quality score, invalid records, missing output paths |
| Reports | file hash, run ID, source name, output paths, quality score |
| Prediction | `prediction_context` |
| Chatbot/RAG | `rag_handoff` |
| Recent Activity | `runs` |

### Hung Page-Level Mapping

| Hung Page | Hung Service Function | Duy Fields / Files |
| --- | --- | --- |
| Dashboard | `get_dashboard_metrics()`, `get_ingestion_status()`, `get_recent_activity()` | `summary.*`, `latest_ingestion_run.*`, `runs[]`, `outputs/ui_fixtures/duy_latest_ingestion_summary.json` |
| Suggestions | `generate_suggestions(context)` | `records_invalid`, `data_quality_score`, `rag_handoff.parsing_status`, `prediction_context.full_payload_path` |
| Reports | `generate_report(evidence_context)` | `run_id`, `ingestion_run_id`, `file_hash_sha256`, raw/staging/clean paths, `records_read`, `records_valid`, `records_invalid` |
| Prediction | `classify_document(payload)`, `classify_documents(payloads)` | `prediction_context`, `outputs/prediction_payloads/tuong_week6_prediction_payloads.json` |
| Chatbot/RAG | `ask_rag(question, document_id=None)` | `rag_handoff.document_pages_path`, `document_external_id`, Lap's `lap_rag_response_real.json` |

Confirmed DB-enriched IDs Hung can use after Phat loads Duy outputs:

```json
{
  "dataflow_technical_report_pdf": {
    "source_id": 2,
    "document_external_id": "doc_dataflow_technical_report",
    "document_db_id": 1
  }
}
```

Before DB loading, Duy's UI fixture intentionally keeps `source_id` and `document_db_id` as `null`. Hung should support both states.

### What Phi/Hung Must Return To Duy

| Output From Phi/Hung | Expected Path / Format | Why Duy Needs It |
| --- | --- | --- |
| Final UI contract | markdown | Confirm required ingestion fields |
| Dashboard screenshot or sample | image or JSON | Prove Duy fixture displays correctly |
| Missing fields list | markdown note | Duy can add fields to fixture builder |
| Suggestion signal requirements | markdown note | Duy can expose new data quality signals |
| Report evidence requirements | markdown note | Duy can include evidence metadata |
| DB-enriched UI sample | JSON or markdown note | Confirms whether UI wants Phat IDs merged into Duy fixture |
| Status/path formatting rules | markdown note | Duy can keep future outputs display-ready |

### Phi/Hung Acceptance Checklist

Phi/Hung should confirm:

```text
[ ] Dashboard can load outputs/ui_fixtures/duy_latest_ingestion_summary.json
[ ] UI displays source count, record counts, quality score, latest status
[ ] UI displays latest ingestion run and file hash
[ ] Suggestions can use invalid records / data quality score
[ ] Reports can use ingestion evidence and output paths
[ ] Prediction page can use prediction_context
[ ] Chatbot/RAG page can use rag_handoff
```

## Inputs Duy Needs Back From Each Team

### From Phat

| Needed From Phat | Required Format | Why It Matters |
| --- | --- | --- |
| `schema_v4.sql` or latest schema | SQL file | Duy aligns writer with final columns |
| DB credentials | `.env` or JSON config | Duy can run `--write-db` |
| Source ID mapping | JSON or query output | Duy updates payloads after DB insert |
| Document DB ID mapping | JSON or query output | Duy passes `document_db_id` to Lap/Tuong |
| Insert validation output | SQL result or screenshot | Proves real DB integration |

### From Lap

| Needed From Lap | Required Format | Why It Matters |
| --- | --- | --- |
| RAG load result | markdown or JSON | Confirms Duy JSONL works |
| Chunk stats | markdown or JSON | Confirms page text is chunkable |
| Citation-ready response | JSON | Phi/Hung can display real citations |
| Required metadata changes | markdown | Duy updates PDF output if needed |

### From Tuong

| Needed From Tuong | Required Format | Why It Matters |
| --- | --- | --- |
| Prediction output on Duy payload | JSON | Confirms payload is model-ready |
| Batch output shape | JSON | Duy can support multiple documents |
| Prediction log payloads | JSON or markdown | Duy/Phat can verify `prediction_logs` mapping |
| RAG metadata filter payload | JSON | Duy/Lap can avoid unsafe hard filters |
| UI fixtures | JSON | Duy/Phi/Hung can align prediction display |
| Error/low-confidence rules | markdown | Duy can validate source quality earlier |
| Required field changes | markdown | Duy updates payload builder |

### From Phi/Hung

| Needed From Phi/Hung | Required Format | Why It Matters |
| --- | --- | --- |
| Final dashboard field list | markdown | Duy maintains fixture compatibility |
| UI screenshot/result | image or notes | Proves display integration |
| Suggestion evidence fields | markdown | Duy exposes right data quality signals |
| Report evidence fields | markdown | Duy exposes right lineage/output paths |

## Week 6 Priority Order

| Priority | Collaboration | Main Goal | Duy Output | Team Output Back |
| --- | --- | --- | --- | --- |
| P0 | Duy + Phat | Prove DB loading | `logs/db_load_dry_run/duy_to_phat_db_load_plan.json` | real `source_id` / `document_db_id` mapping |
| P0 | Duy + Lap | Prove RAG input works | `outputs/rag_handoff/document_pages.jsonl` | RAG response fixture with citations |
| P0 | Duy + Tuong | Prove prediction input works | `outputs/prediction_payloads/tuong_week6_prediction_payloads.json` | prediction batch response with status |
| P0 | Duy + Phi/Hung | Prove UI can display Duy data | `outputs/ui_fixtures/*.json` | screenshot or UI contract confirmation |
| P1 | All team | Align IDs | `docs/week6_id_mapping_contract.md` | agreement on ID naming |
| P1 | All team | Run smoke test | `scripts/week6_end_to_end_smoke_test.py` | confirm end-to-end chain |

## Current Verification Status

Duy's repository currently verifies:

```text
python scripts/validate_week6.py
pytest tests/data_tests/
```

Expected:

```text
Week 6 validation passed
20 passed
```

End-to-end smoke test:

```powershell
python scripts/week6_end_to_end_smoke_test.py
```

Expected checks:

```json
{
  "connect": true,
  "insert": true,
  "query": true,
  "retrieve": true,
  "predict": true,
  "display": true,
  "test": true
}
```

## Short Message Duy Can Send To The Team

```text
Hi team, I prepared my Week 6 integration outputs.

For Phat:
- Use logs/db_load_dry_run/duy_to_phat_db_load_plan.json
- Use logs/runs/*.json, logs/manifests/*.json
- Use clean CSV/API/Excel outputs
- Use week2/logs/pdf_metadata.json and week2/data/staging/pdf/document_pages.jsonl
- Please return source_id and document_db_id mapping after DB insert.

For Lap:
- Use outputs/rag_handoff/document_pages.jsonl
- DataFlow PDF has 36 pages, 36 non-empty pages, 129028 characters
- document_external_id = doc_dataflow_technical_report
- Please return chunk stats and a citation-ready RAG response fixture.

For Tuong:
- Use logs/prediction_payloads/duy_pdf_prediction_payload.json
- Use outputs/prediction_payloads/tuong_week6_prediction_payloads.json for the 10-payload batch test
- source_id is null before DB insert
- ingestion_run_id is separate from source_id
- document_external_id = doc_dataflow_technical_report
- Please return prediction response with accepted / needs_review / waiting_for_source / failed.
- Please do not allow low-confidence or unreviewed predictions to become hard RAG filters.

For Phi/Hung:
- Use outputs/ui_fixtures/duy_latest_ingestion_summary.json
- Use outputs/ui_fixtures/duy_data_quality_summary.json
- Use outputs/ui_fixtures/duy_pdf_document_summary.json
- Please confirm if Dashboard, Suggestions, Reports, Prediction, and RAG pages have enough fields.

Main ID rule:
source_id != ingestion_run_id
document_external_id != document_db_id
```
