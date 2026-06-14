# DataVision Duy - Data Foundation Ingestion Track

This repository contains Duy's Data Foundation work for the DataVision platform.

The focus is ingestion: bringing API, CSV, Excel, PDF, and document-page text into a repeatable raw-to-staging-to-clean flow with portable logs and handoff contracts for PostgreSQL, RAG, prediction, dashboard, suggestions, and reports.

## Project Scope

| Area | Status | Location |
| --- | --- | --- |
| Week 1 ingestion foundation | Complete | `week1_ingestion_foundation/` |
| Week 2 ingestion prototypes | Complete | `week2/notebooks/data_team/` |
| Week 3 reusable ingestion modules | Complete | `week2/scripts/ingestion/` |
| Standard ingestion log schema | Complete | `week2/docs/ingestion_log_schema.md` |
| Standard output contract | Complete | `week2/docs/standard_ingestion_output_contract.md` |
| UI handoff contract | Complete | `week2/docs/ingestion_result_contract_for_ui.md` |
| Database handoff contract | Complete | `week2/docs/ingestion_db_handoff_for_phat.md` |
| Prediction handoff contract | Complete | `week2/docs/ingestion_to_prediction_contract.md` |
| RAG page-level handoff contract | Complete | `week2/docs/document_pages_jsonl_contract_for_lap.md` |

## Architecture

```text
Data Sources
  -> Ingestion Modules
  -> Raw Data
  -> Staging Data
  -> Clean Data
  -> PostgreSQL / Analytics / RAG / ML / Reports
```

## Current Supported Sources

| Source | Module | Raw output | Staging output | Clean output |
| --- | --- | --- | --- | --- |
| Superstore CSV | `csv_ingestor.py` | `week2/data/raw/csv/superstore_raw.csv` | `week2/data/staging/csv/superstore_staging.csv` | `week2/data/clean/csv/superstore_clean.csv` |
| Product Sales Region Excel | `excel_ingestor.py` | `week2/data/raw/excel/product_sales_region_raw.xlsx` | `week2/data/staging/excel/product_sales_region_staging.csv` | `week2/data/clean/excel/product_sales_region_clean.csv` |
| DummyJSON products API | `api_ingestor.py` | `week2/data/raw/api/dummyjson_products_raw.json` | `week2/data/staging/api/dummyjson_products_staging.csv` | `week2/data/clean/api/dummyjson_products_clean.csv` |
| DataFlow technical report PDF | `pdf_ingestor.py` | `week2/data/raw/pdf/dataflow_technical_report_raw.pdf` | `week2/data/staging/pdf/dataflow_pdf_text.txt`, `week2/data/staging/pdf/dataflow_pdf_pages_staging.csv`, and `week2/data/staging/pdf/document_pages.jsonl` | `week2/data/clean/pdf/dataflow_pdf_pages_clean.csv` |

## Run All Ingestion Modules

From the repository root:

```powershell
python -m week2.scripts.ingestion.ingestion_engine
```

Expected output:

```text
csv: success - 9994 valid
excel: success - 1500 valid
api: success - 30 valid
pdf: success - 36 valid
```

## Build Prediction Payload From PDF

```powershell
python week2/scripts/ingestion/prediction_payload_builder.py
```

This builds a Tuong-ready document type classification payload from Duy's PDF ingestion outputs.

## Validate Project

```powershell
python week2/scripts/validate_project.py
```

This checks that required outputs exist, logs use project-relative paths, and each ingestion log contains the required schema fields.

## Important Rules

- Raw data preserves original source files or responses.
- Staging data is parsed and technically normalized.
- Clean data removes duplicates and records missing required fields.
- PDF ingestion also emits page-level JSONL for RAG chunking and citations.
- Optional missing values are allowed but logged separately.
- Shared logs must use project-relative paths, not local Windows absolute paths.

## Team Handoff

| Consumer | Contract |
| --- | --- |
| Phat - Database | `week2/docs/ingestion_db_handoff_for_phat.md` |
| Lap - RAG | `week2/docs/document_pages_jsonl_contract_for_lap.md` |
| Tuong - Prediction | `week2/docs/ingestion_to_prediction_contract.md` |
| Phi/Hung - Demo UI | `week2/docs/ingestion_result_contract_for_ui.md` |
| Whole team | `week2/docs/team_handoff_index.md` |
