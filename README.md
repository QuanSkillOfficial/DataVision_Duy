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
| CSV sales file | `csv_ingestor.py` | `week2/data/raw/csv/sample_raw.csv` | `week2/data/staging/csv/sample_staging.csv` | `week2/data/clean/csv/sample_clean.csv` |
| Excel inventory file | `excel_ingestor.py` | `week2/data/raw/excel/inventory_raw.xlsx` | `week2/data/staging/excel/sample_excel_staging.csv` | `week2/data/clean/excel/sample_excel_clean.csv` |
| API JSON sample | `api_ingestor.py` | `week2/data/raw/api/sample_api_response.json` | `week2/data/staging/api/api_staging.csv` | `week2/data/clean/api/api_clean.csv` |
| PDF document | `pdf_ingestor.py` | `week2/data/raw/pdf/sample_pdf_raw.pdf` | `week2/data/staging/pdf/sample_pdf_text.txt` and `week2/data/staging/pdf/document_pages.jsonl` | Not applicable for Week 3 |

## Run All Ingestion Modules

From the repository root:

```powershell
python -m week2.scripts.ingestion.ingestion_engine
```

Expected output:

```text
csv: success - 2823 valid
excel: success - 46 valid
api: success - 15 valid
pdf: success - 1 valid
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
