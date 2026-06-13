# Team Handoff Index

Owner: Duy  
Role: Ingestion and Pipeline Owner  
Purpose: One-page index of all contracts Duy provides to the rest of the DataVision team.

## Duy Output Summary

```text
CSV / Excel / API / PDF sources
  -> reusable ingestion modules
  -> raw outputs
  -> staging outputs
  -> clean outputs
  -> ingestion logs
  -> team-specific handoff contracts
```

## Contracts

| Consumer | Contract | What it defines |
| --- | --- | --- |
| Phat - Database | `ingestion_db_handoff_for_phat.md` | Mapping from Duy outputs to `sources`, `documents`, `document_pages`, `structured_records`, `ingestion_logs`, and `pipeline_runs` |
| Lap - RAG | `document_pages_jsonl_contract_for_lap.md` | Page-level JSONL format for chunking, embedding, pgvector storage, and citations |
| Tuong - Prediction | `ingestion_to_prediction_contract.md` | Document metadata and extracted text payload for document type classification |
| Phi/Hung - Demo UI | `ingestion_result_contract_for_ui.md` | Upload/Dashboard fields, data quality signals, and UI status mapping |

## Current Generated Outputs

| Output | Path |
| --- | --- |
| CSV raw | `data/raw/csv/sample_raw.csv` |
| CSV staging | `data/staging/csv/sample_staging.csv` |
| CSV clean | `data/clean/csv/sample_clean.csv` |
| Excel raw | `data/raw/excel/inventory_raw.xlsx` |
| Excel staging | `data/staging/excel/sample_excel_staging.csv` |
| Excel clean | `data/clean/excel/sample_excel_clean.csv` |
| API raw | `data/raw/api/sample_api_response.json` |
| API staging | `data/staging/api/api_staging.csv` |
| API clean | `data/clean/api/api_clean.csv` |
| PDF raw | `data/raw/pdf/sample_pdf_raw.pdf` |
| PDF text | `data/staging/pdf/sample_pdf_text.txt` |
| PDF pages JSONL | `data/staging/pdf/document_pages.jsonl` |
| PDF metadata | `logs/pdf_metadata.json` |

## Module Entry Points

| Module | Command / Function |
| --- | --- |
| Run all ingestion | `python -m week2.scripts.ingestion.ingestion_engine` |
| Build prediction payload | `python week2/scripts/ingestion/prediction_payload_builder.py` |
| Validate outputs | `python week2/scripts/validate_project.py` |

## Integration Notes

- Phat should store Duy logs in `ingestion_logs` and page records in `document_pages`.
- Lap should use `document_pages.jsonl` for page-aware chunks and citations.
- Tuong should use `prediction_payload_builder.py` output as the prototype inference input.
- Phi/Hung should derive Upload/Dashboard status from ingestion logs and UI contract fields.

