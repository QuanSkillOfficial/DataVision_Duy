# DataVision Duy Project Status

Owner: Duy  
Role: Ingestion and Pipeline Owner  
Team: Data Foundation Team

## Current Status

The DataVision ingestion track is complete through Week 3 foundation work.

| Phase | Status | Main result |
| --- | --- | --- |
| Week 1 | Complete | Ingestion foundation, source inventory, raw folder structure, setup confirmation |
| Week 2 | Complete | Working notebook prototypes for CSV, Excel, API JSON, and PDF extraction |
| Week 3 | Complete | Reusable ingestion modules, standard output contract, portable logs |

## What Works Now

The project can ingest four source types:

| Source type | Input | Output |
| --- | --- | --- |
| CSV | `week2/data/sample_inputs/sales.csv` | Raw CSV, staging CSV, clean CSV, JSON log |
| Excel | `week2/data/sample_inputs/inventory.xlsx` | Raw XLSX, staging CSV, clean CSV, JSON log |
| API JSON | `week2/data/sample_inputs/customer_api.json` | Raw JSON, staging CSV, clean CSV, JSON log |
| PDF | `week2/data/sample_inputs/big-data-engineer2 - Template 16 .pdf` | Raw PDF, extracted text, metadata, JSON log |

## Run Command

```powershell
python -m week2.scripts.ingestion.ingestion_engine
```

Expected result:

```text
csv: success - 2823 valid
excel: success - 46 valid
api: success - 15 valid
pdf: success - 1 valid
```

## Validation Command

```powershell
python week2/scripts/validate_project.py
```

Expected result:

```text
Validation passed
Checked 16 required outputs
Checked ingestion log schema and portable paths
```

## Standard Data Flow

```text
Source file or response
  -> Reusable ingestion module
  -> data/raw/
  -> data/staging/
  -> data/clean/
  -> logs/
  -> PostgreSQL / RAG / ML / Dashboards / Reports
```

## Layer Definition

| Layer | Meaning |
| --- | --- |
| Raw | Original source file or response. No cleaning should be applied. |
| Staging | Parsed data with technical cleanup, such as column-name normalization. |
| Clean | Validated data after duplicate removal and required-field checks. |
| Logs | One JSON log per ingestion run, using project-relative paths. |

## Validation Rule

Clean data means required fields are present and valid. Optional missing values are allowed but must be logged separately.

Example: the CSV sales file has optional missing values in fields such as `addressline2`, `state`, `postalcode`, and `territory`. These are logged under `optional_missing_values`, but the clean CSV remains valid because required fields are present.

## Handoff to Other Members

| Member | Role | What they can use from this project |
| --- | --- | --- |
| Phat | Database, Quality, Analytics | Clean outputs and JSON logs for PostgreSQL tables |
| Lap | RAG and Embeddings | Extracted PDF text and PDF metadata |
| Tuong | Prediction and ML | Clean structured CSV/API/Excel data |
| Hung | Suggestions, Reports, Demo, AI UX | Clean data and ingestion status logs for Streamlit/demo pages |

## Next Recommended Work

1. Convert ingestion logs into PostgreSQL `ingestion_logs`.
2. Add schema contracts for each source type.
3. Add automated tests for each ingestor using small fixture files.
4. Add CLI arguments for custom input/output paths.
5. Add database loading from clean outputs.

