# Week 2 and Week 3 Ingestion Work

This folder contains the working ingestion prototypes and reusable modules for Duy's Data Foundation role.

## Main Folders

```text
week2/
  data/
    sample_inputs/
    raw/
    staging/
    clean/
  docs/
  logs/
  notebooks/data_team/
  scripts/ingestion/
```

## Notebooks

| Notebook | Purpose |
| --- | --- |
| `notebooks/data_team/csv_ingestion_demo.ipynb` | CSV ingestion prototype |
| `notebooks/data_team/excel_ingestion_demo.ipynb` | Excel ingestion prototype |
| `notebooks/data_team/api_ingestion_demo.ipynb` | API JSON ingestion prototype |
| `notebooks/data_team/pdf_extraction_demo_final.ipynb` | PDF extraction prototype |

## Reusable Modules

| Module | Purpose |
| --- | --- |
| `scripts/ingestion/csv_ingestor.py` | CSV ingestion with encoding fallback, duplicate removal, required-field validation, and logging |
| `scripts/ingestion/excel_ingestor.py` | Excel ingestion with sheet/header detection and validation |
| `scripts/ingestion/api_ingestor.py` | API JSON flattening and validation |
| `scripts/ingestion/pdf_ingestor.py` | PDF page-level text extraction and metadata generation |
| `scripts/ingestion/ingestion_engine.py` | Runs all ingestion modules |
| `scripts/ingestion/prediction_payload_builder.py` | Builds Tuong-ready prediction payload from PDF ingestion output |

## Run

From repository root:

```powershell
python -m week2.scripts.ingestion.ingestion_engine
```

## Validate

```powershell
python week2/scripts/validate_project.py
```

Expected validation summary:

```text
Validation passed
Checked 17 required outputs
Checked 7 required contract docs
Checked ingestion log schema and portable paths
```

## Cross-Team Outputs

| Consumer | Output |
| --- | --- |
| Phat | `docs/ingestion_db_handoff_for_phat.md` |
| Lap | `data/staging/pdf/document_pages.jsonl` and `docs/document_pages_jsonl_contract_for_lap.md` |
| Tuong | `scripts/ingestion/prediction_payload_builder.py` and `docs/ingestion_to_prediction_contract.md` |
| Phi/Hung | `docs/ingestion_result_contract_for_ui.md` |
