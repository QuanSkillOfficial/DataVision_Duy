# raw_data_folder_structure.md

# Raw Data Folder Structure

## Purpose

The raw data layer is the first landing zone of the platform.

Its purpose is to:

- store original source data before transformation
- preserve immutable source files
- support ingestion debugging and recovery
- provide traceability between source systems and downstream pipelines
- enable future ETL, ELT, and LLM processing workflows

This layer acts as the foundation of the ingestion architecture.

---

# Raw Data Layer Principles

## 1. Store Original Files Only

Raw data must remain unchanged after ingestion.

Examples:

- original CSV files
- original Excel files
- original API responses
- original PDF documents
- original JSON payloads

No cleaning or transformation should happen inside the raw layer.

---

## 2. Separate Data by Source Type

Each ingestion source should have its own directory.

This improves:

- organization
- scalability
- debugging
- pipeline management

---

## 3. Partition Data by Date

Data should be partitioned using:

- year
- month
- day

This helps:

- incremental ingestion
- historical tracking
- replay/reprocessing
- performance optimization

---

## 4. Maintain Source Traceability

Each file must remain traceable to:

- original source
- ingestion time
- ingestion method
- owner/system

---

# Standard Folder Structure

```text
data/
├── raw/
│   ├── api/
│   ├── csv/
│   ├── excel/
│   ├── pdf/
│   ├── database/
│   └── streaming/
│
├── staging/
│
├── clean/
│
├── archive/
│
└── logs/
```

---

# Raw Layer Detailed Structure

## API Sources

```text
data/raw/api/
└── customer_api/
    └── 2026/
        └── 05/
            └── 22/
                ├── customers_001.json
                └── customers_002.json
```

### Purpose

- store API response payloads
- preserve original JSON responses
- support API replay/debugging

---

## CSV Sources

```text
data/raw/csv/
└── sales_reports/
    └── 2026/
        └── 05/
            └── 22/
                ├── sales_q1.csv
                └── sales_q2.csv
```

### Purpose

- store uploaded CSV datasets
- preserve manual or scheduled file deliveries

---

## Excel Sources

```text
data/raw/excel/
└── finance_reports/
    └── 2026/
        └── 05/
            └── 22/
                ├── budget.xlsx
                └── revenue.xlsx
```

### Purpose

- store business Excel reports
- support multi-sheet ingestion workflows

---

## PDF Sources

```text
data/raw/pdf/
└── invoices/
    └── 2026/
        └── 05/
            └── 22/
                ├── invoice_1001.pdf
                └── invoice_1002.pdf
```

### Purpose

- preserve original PDF documents
- support OCR or LLM extraction later

---

## Database Exports

```text
data/raw/database/
└── postgres_export/
    └── 2026/
        └── 05/
            └── 22/
                ├── customers.parquet
                └── transactions.parquet
```

### Purpose

- store extracted database snapshots
- support CDC or batch ingestion

---

## Streaming Sources

```text
data/raw/streaming/
└── kafka_events/
    └── 2026/
        └── 05/
            └── 22/
                ├── events_batch_001.json
                └── events_batch_002.json
```

### Purpose

- store streamed event batches
- preserve raw event history

---

# Sample Input Testing Folder

```text
data/sample_inputs/
├── sample.csv
├── sample.xlsx
├── sample.pdf
└── sample_api_response.json
```

## Purpose

- ingestion testing
- parser validation
- pipeline development
- debugging

---

# Naming Convention

## Folder Naming Rules

Use:

- lowercase
- snake_case
- meaningful source names

Examples:

- customer_api
- finance_reports
- sales_reports

Avoid:

- spaces
- special characters
- unclear abbreviations

---

## File Naming Rules

Recommended format:

```text
<source_name>_<batch_or_timestamp>.<extension>
```

Examples:

```text
customers_20260522.json
sales_20260522.csv
invoice_1001.pdf
```

---

# Raw Data Rules

## Immutable Raw Data

Raw files must never be edited manually after ingestion.

If correction is needed:

- create a new ingestion version
- preserve original files

---

## No Transformation in Raw Layer

The raw layer should not contain:

- cleaned data
- normalized data
- transformed outputs
- feature engineering

Transformation belongs in:

- staging
- clean
- downstream processing layers

---

# Raw → Clean Data Flow

```text
Source System
      ↓
Raw Layer
      ↓
Staging Layer
      ↓
Clean Layer
      ↓
Analytics / ML / LLM Systems
```

---

# Future Scalability

This structure is designed to support future:

- automated ingestion pipelines
- Airflow orchestration
- Kafka streaming ingestion
- cloud storage migration
- data lake architecture
- LLM document ingestion
- OCR pipelines
- metadata tracking
- lineage systems

---

# Recommended Technologies

| Component       | Suggested Tool       |
| --------------- | -------------------- |
| File Processing | Python               |
| CSV Handling    | Pandas               |
| Excel Handling  | OpenPyXL             |
| PDF Extraction  | PyMuPDF / pdfplumber |
| API Ingestion   | Requests             |
| Orchestration   | Airflow              |
| Storage         | Local / S3 / ADLS    |
| Logging         | Python logging       |

---
