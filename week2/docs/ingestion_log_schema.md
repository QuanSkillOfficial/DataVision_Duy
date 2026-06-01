# Ingestion Log Schema

## 1. Purpose

This document defines the standard ingestion log schema used across all ingestion pipelines in the platform.

Each ingestion execution should generate one ingestion log record.

The ingestion log is used to:

- track ingestion execution
- monitor ingestion health and status
- debug failed pipelines
- measure records read and validated
- trace raw, staging, and clean outputs
- support auditability and observability
- prepare future PostgreSQL logging integration
- support downstream analytics and AI systems

This schema is shared across:

- CSV ingestion
- Excel ingestion
- API ingestion
- PDF extraction ingestion
- future database ingestion
- future streaming ingestion

---

# 2. Log Schema Overview

| Field               | Data Type        | Required | Description                                 |
| ------------------- | ---------------- | -------- | ------------------------------------------- |
| run_id              | string           | Yes      | Unique identifier for each ingestion run    |
| source_name         | string           | Yes      | Human-readable source name                  |
| source_type         | string           | Yes      | Type of source such as csv, excel, api, pdf |
| input_path_or_url   | string           | Yes      | Original input file path or API URL         |
| start_time          | timestamp/string | Yes      | Time when ingestion started                 |
| end_time            | timestamp/string | Yes      | Time when ingestion completed               |
| status              | string           | Yes      | Final ingestion status                      |
| records_read        | integer          | Yes      | Total records/pages read                    |
| records_valid       | integer          | Yes      | Valid records after validation/cleaning     |
| records_invalid     | integer          | Yes      | Invalid or removed records                  |
| error_message       | string/null      | Yes      | Error details if failure occurs             |
| raw_output_path     | string/null      | Yes      | Location of raw output file                 |
| staging_output_path | string/null      | Yes      | Location of staging output                  |
| clean_output_path   | string/null      | Yes      | Location of clean output                    |
| owner               | string           | Yes      | Ingestion pipeline owner                    |

---

# 3. Field Definitions

## run_id

A unique identifier generated for every ingestion execution.

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

Human-readable name of the ingestion source.

Examples:

```text
sales_csv
inventory_excel
sample_api_response
resume_pdf
```

---

## source_type

The category of the source.

Supported values:

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

Original source location.

Examples:

```text
data/sample_inputs/sales.csv
data/sample_inputs/inventory.xlsx
data/sample_inputs/sample_api_response.json
https://api.example.com/customers
```

---

## start_time

Timestamp when ingestion starts.

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

Timestamp when ingestion finishes.

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

Final ingestion execution status.

| Status          | Meaning                                  |
| --------------- | ---------------------------------------- |
| success         | Ingestion completed successfully         |
| failed          | Ingestion failed                         |
| partial_success | Some records succeeded while some failed |

---

## records_read

Total records/pages extracted from the source.

Examples:

- CSV rows
- Excel rows
- API records
- PDF pages

---

## records_valid

Number of valid records after cleaning or validation.

Examples:

- rows after duplicate removal
- records with required fields
- valid extracted pages

---

## records_invalid

Number of invalid or removed records.

Examples:

- duplicate rows
- missing required fields
- empty PDF pages
- corrupted records

---

## error_message

Stores failure details if ingestion fails.

Successful execution:

```json
null
```

Failure example:

```text
Missing required field: customer_id
```

---

## raw_output_path

Location of raw layer output.

Examples:

```text
data/raw/csv/sample_raw.csv
data/raw/excel/inventory_raw.xlsx
data/raw/api/sample_api_response.json
```

---

## staging_output_path

Location of parsed or intermediate staging output.

Examples:

```text
data/staging/csv/sample_staging.csv
data/staging/api/api_staging.csv
data/staging/pdf/sample_pdf_text.txt
```

---

## clean_output_path

Location of cleaned output.

Examples:

```text
data/clean/csv/sample_clean.csv
data/clean/excel/sample_excel_clean.csv
data/clean/api/api_clean.csv
```

For PDF extraction during Week 2, this field may be null.

---

## owner

The ingestion pipeline owner.

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

# 5. Suggested PostgreSQL Table Design

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

# 6. Expected Log Outputs by Pipeline

## CSV Ingestion

```text
logs/csv_ingestion_log.json
```

## Excel Ingestion

```text
logs/excel_ingestion_log.json
```

## API Ingestion

```text
logs/api_ingestion_log.json
```

## PDF Ingestion

```text
logs/pdf_ingestion_log.json
```

---

# 7. Logging Rules

- Every ingestion run must generate one ingestion log.
- `run_id` must be unique for every execution.
- `start_time` and `end_time` should use UTC timestamps.
- `status` must clearly indicate success or failure.
- Output paths should always be logged when generated.
- Error messages should be descriptive enough for debugging.
- Logs should be stored in the `logs/` directory during prototype development.
- Future versions may store logs directly in PostgreSQL.

---

# 8. Downstream Usage

## Data Engineering Team

Used for:

- pipeline monitoring
- debugging
- auditing
- ingestion observability

---

## Database Team

Used to create and populate the PostgreSQL `ingestion_logs` table.

---

## Analytics Team

Used to:

- monitor pipeline freshness
- track ingestion failures
- monitor source activity
- measure ingestion volume

---

## AI / RAG Team

Used to:

- verify source reliability
- track ingestion freshness
- validate document availability before embedding or indexing

---

# 9. Future Improvements

Future versions of the ingestion log schema may include:

- ingestion latency
- retry count
- schema version
- pipeline duration
- ingestion environment
- validation score
- source authentication metadata
- SLA metrics
- data lineage tracking
- monitoring dashboard integration

---
