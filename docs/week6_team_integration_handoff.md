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
  "source_id": 4,
  "document_db_id": 1,
  "document_external_id": "doc_dataflow_technical_report",
  "ingestion_run_id": "8e18bd87-27e5-4aa1-9566-805ffd552fdb"
}
```

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
| DB loading result note | `docs/week6_database_loading_result.md` | Current DB dry-run / real-run status |
| Duy + Phat result note | `docs/week6_duy_to_phat_db_load_result.md` | Integration result note |

### Tables Phat Should Load

| Phat Table | Duy Input File | Insert Rule |
| --- | --- | --- |
| `sources` | `logs/runs/*.json` | Insert or get by `source_name` |
| `pipeline_runs` | `logs/runs/*.json` | Insert one row per `run_id` |
| `ingestion_logs` | `logs/runs/*.json` | Insert records read/valid/invalid, paths, quality score |
| `documents` | `week2/logs/pdf_metadata.json` | Insert one PDF document with `document_external_id` |
| `document_pages` | `week2/data/staging/pdf/document_pages.jsonl` | Insert 36 page records using internal `documents.id` |
| `structured_records` | clean CSV/API/Excel files | Insert row data as JSONB or agreed format |

### Required Field Mapping For Phat

| Duy Field | Phat Table.Column | Notes |
| --- | --- | --- |
| `source_name` | `sources.name` | Should be unique |
| `source_type` | `sources.source_type` | `csv`, `excel`, `api`, `pdf` |
| `run_id` | `pipeline_runs.run_id` and `ingestion_logs.run_id` | Duy execution UUID |
| `status` | `pipeline_runs.status`, `ingestion_logs.status` | Current values: `success`, `failed` |
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

### What Phat Must Return To Duy

Phat should return these outputs after DB integration:

| Output From Phat | Expected Path / Format | Why Duy Needs It |
| --- | --- | --- |
| Real `source_id` mapping | JSON or markdown table | Fill `source_id` in future payloads |
| Real `document_db_id` mapping | JSON or markdown table | Fill `document_db_id` for PDF/RAG/prediction |
| Insert proof | Screenshot or query output | Prove Duy outputs loaded successfully |
| Validation query result | `validation_queries_v2.sql` output | Prove FK and quality checks pass |
| Dashboard view samples | JSON files from Phat views | Phi/Hung can replace fixtures |

Expected mapping from Phat:

```json
{
  "source_name": "dataflow_technical_report_pdf",
  "source_id": 4,
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": 1,
  "ingestion_run_id": "8e18bd87-27e5-4aa1-9566-805ffd552fdb"
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

If Lap needs database insertion:

```text
Duy document_external_id
  -> Phat documents.document_external_id
  -> Phat documents.id
  -> document_chunks.document_id
```

Lap should not insert string document IDs into integer FK columns.

### Expected Chunk ID Convention

Recommended:

```text
doc_dataflow_technical_report_page_1_chunk_000
doc_dataflow_technical_report_page_1_chunk_001
doc_dataflow_technical_report_page_2_chunk_000
```

### What Lap Must Return To Duy

| Output From Lap | Expected Path / Format | Why Duy Needs It |
| --- | --- | --- |
| Confirmation that JSONL loads | markdown note | Verify PDF output is RAG-ready |
| Page/chunk stats | markdown or JSON | Confirm pages converted to chunks |
| Failed/empty page issues | markdown note | Duy can fix PDF extraction if needed |
| Real RAG response fixture | JSON | Phi/Hung can display citations |
| Required metadata changes | markdown note | Duy can update future JSONL output |

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
[ ] Returned citation-ready RAG fixture for Phi/Hung
```

## Duy -> Tuong: Prediction Handoff

### What Duy Gives Tuong

Tuong should use Duy's prediction payload as real ingestion input for document classification.

| File | Exact Path | Purpose |
| --- | --- | --- |
| PDF prediction payload | `logs/prediction_payloads/duy_pdf_prediction_payload.json` | Main input for Tuong classifier |
| Prediction contract | `week2/docs/ingestion_to_prediction_contract.md` | Field contract |
| ID mapping contract | `docs/week6_id_mapping_contract.md` | Separates source/run/document IDs |
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

### What Tuong Must Return To Duy

| Output From Tuong | Expected Path / Format | Why Duy Needs It |
| --- | --- | --- |
| Single prediction response | JSON | Confirm Duy payload works |
| Batch prediction response | JSON | Prepare multi-document ingestion |
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

### What Phi/Hung Must Return To Duy

| Output From Phi/Hung | Expected Path / Format | Why Duy Needs It |
| --- | --- | --- |
| Final UI contract | markdown | Confirm required ingestion fields |
| Dashboard screenshot or sample | image or JSON | Prove Duy fixture displays correctly |
| Missing fields list | markdown note | Duy can add fields to fixture builder |
| Suggestion signal requirements | markdown note | Duy can expose new data quality signals |
| Report evidence requirements | markdown note | Duy can include evidence metadata |

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
| P0 | Duy + Tuong | Prove prediction input works | `logs/prediction_payloads/duy_pdf_prediction_payload.json` | prediction response with status |
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
- source_id is null before DB insert
- ingestion_run_id is separate from source_id
- document_external_id = doc_dataflow_technical_report
- Please return prediction response with accepted / needs_review / waiting_for_source / failed.

For Phi/Hung:
- Use outputs/ui_fixtures/duy_latest_ingestion_summary.json
- Use outputs/ui_fixtures/duy_data_quality_summary.json
- Use outputs/ui_fixtures/duy_pdf_document_summary.json
- Please confirm if Dashboard, Suggestions, Reports, Prediction, and RAG pages have enough fields.

Main ID rule:
source_id != ingestion_run_id
document_external_id != document_db_id
```
