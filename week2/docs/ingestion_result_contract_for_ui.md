# Ingestion Result Contract for UI

Owner: Duy  
Consumer: Phi/Hung - Suggestions, Reports, Demo, and AI UX Owner  
Purpose: Define the ingestion output shape that the Streamlit Upload and Dashboard pages can consume.

## Why This Contract Exists

Phi and Hung's Week 3 UI needs real ingestion signals from Duy's pipelines. This contract defines the exact JSON shape that the UI can expect from ingestion logs or a future ingestion API.

For now, these fields are available from JSON files in `week2/logs/`. Later, the same shape can be returned by FastAPI or queried from PostgreSQL.

## UI Consumption Flow

```text
Duy ingestion module
  -> logs/<source>_ingestion_log.json
  -> Phat ingestion_logs table / analytics views
  -> Phi/Hung service_client.py
  -> Upload page and Dashboard page
```

## Required UI Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `run_id` | string | Yes | Unique ingestion run ID |
| `source_name` | string | Yes | Stable source name, such as `sales_csv` |
| `source_type` | string | Yes | `csv`, `excel`, `api`, `pdf`, `database`, or `streaming` |
| `file_name` | string/null | Yes | File name displayed in Upload and Dashboard |
| `file_size_bytes` | integer/null | Yes | Source file size if available |
| `input_path_or_url` | string | Yes | Project-relative path or source URL |
| `processing_status` | string | Yes | UI-friendly status: `ready`, `failed`, `partial_success`, or `waiting` |
| `records_read` | integer | Yes | Rows, API records, or PDF pages read |
| `records_valid` | integer | Yes | Records/pages that passed required validation |
| `records_invalid` | integer | Yes | Records/pages that failed validation or were removed |
| `missing_values` | object | Yes | Combined missing-value summary for UI display |
| `required_missing_values_removed` | integer | Yes | Rows removed because required fields were missing |
| `optional_missing_values` | object | Yes | Optional missing values kept in clean data |
| `duplicate_rows_removed` | integer | Yes | Duplicate rows removed during cleaning |
| `raw_output_path` | string/null | Yes | Project-relative raw output path |
| `staging_output_path` | string/null | Yes | Project-relative staging output path |
| `clean_output_path` | string/null | Yes | Project-relative clean output path |
| `start_time` | string | Yes | ISO 8601 UTC start time |
| `end_time` | string | Yes | ISO 8601 UTC end time |
| `owner` | string | Yes | Ingestion owner |

## Optional UI Fields

| Field | Type | Used by |
| --- | --- | --- |
| `page_count` | integer | PDF dashboard and RAG preparation |
| `extracted_character_count` | integer | PDF parsing coverage signal |
| `empty_pages` | array | PDF data quality warning |
| `sheet_names` | array | Excel upload details |
| `selected_sheet` | string | Excel source metadata |
| `required_fields` | array | Data quality explanation |
| `missing_required_columns` | array | Error state and validation warning |
| `metadata_output_path` | string | PDF metadata traceability |

## Processing Status Mapping

| Ingestion log `status` | UI `processing_status` |
| --- | --- |
| `success` | `ready` |
| `partial_success` | `partial_success` |
| `failed` | `failed` |
| No source uploaded | `waiting` |

## Example CSV Result

```json
{
  "run_id": "2660ff58-bedc-433f-bbd3-41d2479dbcd0",
  "source_name": "sales_csv",
  "source_type": "csv",
  "file_name": "sales.csv",
  "file_size_bytes": 527958,
  "input_path_or_url": "data/sample_inputs/sales.csv",
  "processing_status": "ready",
  "records_read": 2823,
  "records_valid": 2823,
  "records_invalid": 0,
  "missing_values": {
    "required_missing_values_removed": 0,
    "optional_missing_values": {
      "addressline2": 2521,
      "state": 1486,
      "postalcode": 76,
      "territory": 1074
    }
  },
  "required_missing_values_removed": 0,
  "optional_missing_values": {
    "addressline2": 2521,
    "state": 1486,
    "postalcode": 76,
    "territory": 1074
  },
  "duplicate_rows_removed": 0,
  "raw_output_path": "data/raw/csv/sample_raw.csv",
  "staging_output_path": "data/staging/csv/sample_staging.csv",
  "clean_output_path": "data/clean/csv/sample_clean.csv",
  "start_time": "2026-06-13T16:15:39.555437+00:00",
  "end_time": "2026-06-13T16:15:39.654392+00:00",
  "owner": "Nguyen Minh Duy"
}
```

## Example PDF Result

```json
{
  "run_id": "c77b8cf3-d542-4242-af90-b5aa866715bf",
  "source_name": "sample_pdf",
  "source_type": "pdf",
  "file_name": "big-data-engineer2 - Template 16 .pdf",
  "file_size_bytes": 63047,
  "input_path_or_url": "data/sample_inputs/big-data-engineer2 - Template 16 .pdf",
  "processing_status": "ready",
  "records_read": 1,
  "records_valid": 1,
  "records_invalid": 0,
  "page_count": 1,
  "extracted_character_count": 2664,
  "empty_pages": [],
  "missing_values": {
    "empty_pages": []
  },
  "required_missing_values_removed": 0,
  "optional_missing_values": {},
  "duplicate_rows_removed": 0,
  "raw_output_path": "data/raw/pdf/sample_pdf_raw.pdf",
  "staging_output_path": "data/staging/pdf/sample_pdf_text.txt",
  "clean_output_path": null,
  "metadata_output_path": "logs/pdf_metadata.json",
  "start_time": "2026-06-13T16:13:28.855088+00:00",
  "end_time": "2026-06-13T16:13:28.878859+00:00",
  "owner": "Nguyen Minh Duy"
}
```

## Dashboard Signals Phi/Hung Can Derive

| UI signal | Calculation |
| --- | --- |
| `source_count` | Count of ingestion results shown in the UI |
| `record_count` | Sum of `records_read` |
| `data_quality_score` | `records_valid / records_read * 100`, adjusted for duplicate and missing required issues |
| `processing_status` | Use mapped `processing_status` |
| `duplicate_risk` | High if `duplicate_rows_removed / records_read > 0.05` |
| `parsing_coverage` | For PDFs, `records_valid / records_read`; for structured data, `records_valid / records_read` |

## Notes for Phi/Hung

- Use `raw_output_path` only for traceability, not user-facing cleaned analytics.
- Use `staging_output_path` when showing parsed data previews.
- Use `clean_output_path` for dashboard, prediction, suggestions, and report evidence.
- Display optional missing values as data quality limitations, not ingestion failures.
- Treat `records_invalid > 0` or `missing_required_columns` as warning/error signals.

