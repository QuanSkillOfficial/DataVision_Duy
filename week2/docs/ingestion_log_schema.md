# Ingestion Log Schema

## 1. Purpose

This document defines the standard ingestion log schema for all ingestion prototypes in the platform.

Every ingestion run should generate one log record.

The ingestion log helps the team:

- track ingestion execution
- debug failed pipelines
- measure records read and validated
- trace raw, staging, and clean outputs
- support auditability and observability
- prepare for PostgreSQL `ingestion_logs` table design

This schema will be used by CSV, Excel, API, PDF, and future ingestion pipelines.

---

# 2. Log Schema Overview

| Field               | Data Type        | Required | Description                                                      |
| ------------------- | ---------------- | -------- | ---------------------------------------------------------------- |
| run_id              | string           | Yes      | Unique ID for each ingestion run                                 |
| source_name         | string           | Yes      | Name of the data source                                          |
| source_type         | string           | Yes      | Type of source such as csv, excel, api, pdf, database, streaming |
| input_path_or_url   | string           | Yes      | File path, API endpoint, or source URL                           |
| start_time          | timestamp/string | Yes      | Time when ingestion started                                      |
| end_time            | timestamp/string | Yes      | Time when ingestion completed                                    |
| status              | string           | Yes      | Execution status: success, failed, partial_success               |
| records_read        | integer          | Yes      | Number of records read from source                               |
| records_valid       | integer          | Yes      | Number of valid records after validation or cleaning             |
| records_invalid     | integer          | Yes      | Number of invalid, failed, or removed records                    |
| error_message       | string/null      | Yes      | Error details if ingestion failed; null if successful            |
| raw_output_path     | string/null      | Yes      | Location of raw output file, if available                        |
| staging_output_path | string/null      | Yes      | Location of parsed/staging output                                |
| clean_output_path   | string/null      | Yes      | Location of cleaned output                                       |
| owner               | string           | Yes      | Person responsible for the ingestion run                         |

---

# 3. Field Definitions

## run_id

A unique identifier for one ingestion run.

Recommended format:

```text
UUID
```

Example:

```text
6e52a7d0-7d44-4c29-a1f3-5c79dc674db2
```

---

## source_name

The human-readable source name.

Examples:

```text
sales_csv
inventory_excel
sample_api_response
financial_report_pdf
```

---

## source_type

The source category.

Allowed values:

```text
csv
excel
api
pdf
database
streaming
```

---

## input_path_or_url

The original input location.

Examples:

```text
data/sample_inputs/sales.csv
data/sample_inputs/inventory.xlsx
data/sample_inputs/sample_api_response.json
https://api.example.com/customers
```

---

## start_time

Timestamp when the ingestion run starts.

Recommended format:

```text
ISO 8601 UTC
```

Example:

```text
2026-05-29T10:15:30.123456+00:00
```

---

## end_time

Timestamp when the ingestion run completes.

Recommended format:

```text
ISO 8601 UTC
```

Example:

```text
2026-05-29T10:15:35.654321+00:00
```

---

## status

Final status of the ingestion run.

Allowed values:

| Status          | Meaning                                     |
| --------------- | ------------------------------------------- |
| success         | Ingestion completed successfully            |
| failed          | Ingestion failed                            |
| partial_success | Some records were processed but some failed |

---

## records_read

Total number of records read from the source.

For CSV, Excel, and API:

```text
number of dataframe rows
```

For PDF:

```text
number of pages or extracted text blocks
```

---

## records_valid

Number of records considered valid after parsing, validation, and cleaning.

Examples:

- records after duplicate removal
- records with required fields available
- valid extracted pages for PDF

---

## records_invalid

Number of invalid, removed, or failed records.

Examples:

- duplicate rows removed
- rows missing required fields
- empty PDF pages
- corrupted records

---

## error_message

Stores the error message if ingestion fails.

If successful:

```json
null
```

If failed:

```text
Missing required field: customer_id
```

---

## raw_output_path

Path to the raw output stored by the ingestion pipeline.

Examples:

```text
data/raw/api/sample_api_response.json
data/raw/excel/inventory_raw.xlsx
```

If not applicable:

```json
null
```

---

## staging_output_path

Path to the parsed/intermediate output.

Examples:

```text
data/staging/csv/sample_staging.csv
data/staging/api/api_staging.csv
data/staging/pdf/sample_pdf_text.txt
```

---

## clean_output_path

Path to the cleaned output.

Examples:

```text
data/clean/csv/sample_clean.csv
data/clean/excel/sample_excel_clean.csv
data/clean/api/api_clean.csv
```

For PDF extraction, this may be null if only staging text is generated in Week 2.

---

## owner

The person responsible for the ingestion pipeline.

Example:

```text
Nguyen Minh Duy
```

---

# 4. Example JSON Log

```json
{
  "run_id": "6e52a7d0-7d44-4c29-a1f3-5c79dc674db2",
  "source_name": "sales_csv",
  "source_type": "csv",
  "input_path_or_url": "data/sample_inputs/sales.csv",
  "start_time": "2026-05-29T10:15:30.123456+00:00",
  "end_time": "2026-05-29T10:15:35.654321+00:00",
  "status": "success",
  "records_read": 2823,
  "records_valid": 2823,
  "records_invalid": 0,
  "error_message": null,
  "raw_output_path": "data/raw/csv/sample_raw.csv",
  "staging_output_path": "data/staging/csv/sample_staging.csv",
  "clean_output_path": "data/clean/csv/sample_clean.csv",
  "owner": "Nguyen Minh Duy"
}
```

---

# 5. Mapping to Future PostgreSQL Table

This schema will later be converted into a PostgreSQL table by the Database, Quality, and Analytics Owner.

Suggested table name:

```text
ingestion_logs
```

Suggested PostgreSQL schema:

```sql
CREATE TABLE ingestion_logs (
    run_id UUID PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    input_path_or_url TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    status TEXT NOT NULL,
    records_read INTEGER,
    records_valid INTEGER,
    records_invalid INTEGER,
    error_message TEXT,
    raw_output_path TEXT,
    staging_output_path TEXT,
    clean_output_path TEXT,
    owner TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 6. Usage Across Ingestion Prototypes

## CSV Ingestion

Expected log path:

```text
logs/csv_ingestion_log.json
```

## Excel Ingestion

Expected log path:

```text
logs/excel_ingestion_log.json
```

## API Ingestion

Expected log path:

```text
logs/api_ingestion_log.json
```

## PDF Ingestion

Expected log path:

```text
logs/pdf_ingestion_log.json
```

---

# 7. Logging Rules

- Each ingestion run must generate one log file or one log record.
- `run_id` must be unique for every run.
- `start_time` and `end_time` should use UTC time.
- `status` must clearly show whether the run succeeded or failed.
- Output paths should be recorded even if some downstream files are not generated.
- Error messages should be clear enough for debugging.
- Logs should be stored in the `logs/` directory during prototype development.
- Later, these logs can be inserted into the PostgreSQL `ingestion_logs` table.

---

# 8. Downstream Usage

The ingestion log will be used by:

## Data Intern 2

To design and populate the PostgreSQL `ingestion_logs` table.

## Analytics Layer

To monitor pipeline runs, failures, data volume, and source freshness.

## AI Team

To understand whether source data is reliable before using it for RAG, embeddings, or ML.

## Demo / Report Team

To show ingestion status, latest runs, and pipeline health in Streamlit or reports.

---

# 9. Summary

The ingestion log schema provides a standard way to record ingestion execution metadata.

It supports:

- traceability
- debugging
- observability
- auditability
- PostgreSQL integration
- downstream analytics and AI reliability
