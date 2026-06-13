<<<<<<< HEAD
# DataVision Duy - Data Foundation Ingestion Track

This repository contains Duy's Data Foundation work for the DataVision platform.

The focus is ingestion: bringing API, CSV, Excel, and PDF data into a repeatable raw-to-staging-to-clean flow with portable logs for later PostgreSQL, analytics, RAG, ML, and demo integration.

## Project Scope

| Area | Status | Location |
| --- | --- | --- |
| Week 1 ingestion foundation | Complete | `week1_ingestion_foundation/` |
| Week 2 ingestion prototypes | Complete | `week2/notebooks/data_team/` |
| Week 3 reusable ingestion modules | Complete | `week2/scripts/ingestion/` |
| Standard ingestion log schema | Complete | `week2/docs/ingestion_log_schema.md` |
| Standard output contract | Complete | `week2/docs/standard_ingestion_output_contract.md` |

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
| PDF document | `pdf_ingestor.py` | `week2/data/raw/pdf/sample_pdf_raw.pdf` | `week2/data/staging/pdf/sample_pdf_text.txt` | Not applicable for Week 3 |

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

## Validate Project

```powershell
python week2/scripts/validate_project.py
```

This checks that required outputs exist, logs use project-relative paths, and each ingestion log contains the required schema fields.

## Important Rules

- Raw data preserves original source files or responses.
- Staging data is parsed and technically normalized.
- Clean data removes duplicates and records missing required fields.
- Optional missing values are allowed but logged separately.
- Shared logs must use project-relative paths, not local Windows absolute paths.

=======
# QuanSolution DataVision Platform — Ingestion Foundation

## Overview

This repository contains the ingestion foundation and ingestion prototype implementations for the QuanSolution DataVision Platform.

The project focuses on building the first operational layer of the platform — the ingestion layer.

The ingestion layer is responsible for:

* receiving external data
* preserving raw source files
* validating incoming data
* preparing staging datasets
* generating clean datasets
* tracking ingestion metadata
* supporting downstream analytics, AI, and RAG workflows

This repository currently includes:

* CSV ingestion prototype
* Excel ingestion prototype
* API JSON ingestion prototype
* PDF extraction prototype
* ingestion logging framework
* raw/staging/clean data architecture
* ingestion metadata inventory

---

# Platform Architecture

```text
External Sources
        ↓
Ingestion Layer
        ↓
Raw Storage Layer
        ↓
Staging Layer
        ↓
Clean Layer
        ↓
Analytics / ML / RAG / LLM Systems
```

---

# Project Structure

```text
QuanSolution_DataVision_Platform/
│
├── data/
│   ├── sample_inputs/
│   │   ├── sales.csv
│   │   ├── inventory.xlsx
│   │   ├── sample_api_response.json
│   │   └── resume.pdf
│   │
│   ├── raw/
│   │   ├── csv/
│   │   ├── excel/
│   │   ├── api/
│   │   └── pdf/
│   │
│   ├── staging/
│   │   ├── csv/
│   │   ├── excel/
│   │   ├── api/
│   │   └── pdf/
│   │
│   └── clean/
│       ├── csv/
│       ├── excel/
│       └── api/
│
├── notebooks/
│   └── data_team/
│       ├── csv_ingestion_demo.ipynb
│       ├── excel_ingestion_demo.ipynb
│       ├── api_ingestion_demo.ipynb
│       └── pdf_extraction_demo.ipynb
│
├── logs/
│   ├── csv_ingestion_log.json
│   ├── excel_ingestion_log.json
│   ├── api_ingestion_log.json
│   ├── pdf_ingestion_log.json
│   └── pdf_metadata.json
│
├── docs/
│   ├── ingestion_owner_understanding.md
│   ├── raw_data_folder_structure.md
│   ├── setup_confirmation.md
│   ├── ingestion_log_schema.md
│   ├── data_source_inventory_template.md
│   └── data_source_inventory_template_v2.md
│
├── requirements.txt
└── README.md
```

---

# Week 1 Deliverables

## 1. Ingestion Owner Understanding

Document explaining:

* ingestion responsibilities
* ingestion architecture
* raw-to-clean workflow
* ingestion observability
* pipeline logging
* validation and error handling

File:

```text
docs/ingestion_owner_understanding.md
```

---

## 2. Data Source Inventory Template

Initial metadata inventory for ingestion sources.

Includes:

* source type
* file format
* ingestion method
* owner
* status
* frequency
* expected fields

File:

```text
docs/data_source_inventory_template.md
```

---

## 3. Raw Data Folder Structure

Defines:

* raw data architecture
* folder partitioning
* staging and clean layers
* naming conventions
* ingestion organization standards

File:

```text
docs/raw_data_folder_structure.md
```

---

## 4. Setup Confirmation

Environment setup and dependency validation.

Includes:

* Python
* VS Code
* Git
* Pandas
* Requests
* OpenPyXL
* PyMuPDF
* pdfplumber

File:

```text
docs/setup_confirmation.md
```

---

# Week 2 Deliverables

## Task 1 — CSV Ingestion Prototype

Notebook:

```text
notebooks/data_team/csv_ingestion_demo.ipynb
```

Features:

* load CSV file
* clean column names
* remove duplicates
* check missing values
* save staging dataset
* save clean dataset
* generate ingestion log

Generated outputs:

```text
data/raw/csv/sample_raw.csv
data/staging/csv/sample_staging.csv
data/clean/csv/sample_clean.csv
logs/csv_ingestion_log.json
```

---

## Task 2 — Excel Ingestion Prototype

Notebook:

```text
notebooks/data_team/excel_ingestion_demo.ipynb
```

Features:

* detect Excel sheets
* detect header row
* clean column names
* validate data
* save staging dataset
* save clean dataset
* generate ingestion log

Generated outputs:

```text
data/raw/excel/inventory_raw.xlsx
data/staging/excel/sample_excel_staging.csv
data/clean/excel/sample_excel_clean.csv
logs/excel_ingestion_log.json
```

---

## Task 3 — API Ingestion Prototype

Notebook:

```text
notebooks/data_team/api_ingestion_demo.ipynb
```

Features:

* load JSON API response
* flatten JSON structure
* validate required fields
* save raw JSON
* save staging dataset
* save clean dataset
* generate ingestion log

Generated outputs:

```text
data/raw/api/sample_api_response.json
data/staging/api/api_staging.csv
data/clean/api/api_clean.csv
logs/api_ingestion_log.json
```

---

## Task 4 — PDF Extraction Prototype

Notebook:

```text
notebooks/data_team/pdf_extraction_demo.ipynb
```

Features:

* load PDF document
* extract text page-by-page
* detect empty pages
* count pages and characters
* generate metadata
* save extracted text
* generate ingestion log

Generated outputs:

```text
data/staging/pdf/sample_pdf_text.txt
logs/pdf_ingestion_log.json
logs/pdf_metadata.json
```

---

## Task 5 — Standard Ingestion Log Schema

Defines the standard ingestion log structure for all ingestion pipelines.

Includes:

* run_id
* source_name
* status
* timestamps
* records_read
* records_valid
* output paths
* error handling metadata

File:

```text
docs/ingestion_log_schema.md
```

---

## Task 6 — Data Source Inventory Template V2

Enhanced metadata inventory with governance and operational metadata.

Additional fields:

* authentication_required
* schema_version
* sample_available
* last_ingested_at
* expected_volume
* sensitive_data_flag
* downstream_consumer

File:

```text
docs/data_source_inventory_template_v2.md
```

---

# Raw vs Staging vs Clean

## Raw Layer

Purpose:

* preserve original source data
* immutable storage
* debugging and replay

Examples:

```text
raw CSV
raw Excel
raw JSON
raw PDF
```

---

## Staging Layer

Purpose:

* parsed intermediate layer
* standardized structure
* temporary validation outputs

Examples:

```text
flattened API tables
parsed CSV
parsed PDF text
```

---

## Clean Layer

Purpose:

* validated datasets
* duplicate removal
* ready for analytics and AI workflows

Examples:

```text
clean customer table
clean sales dataset
validated structured outputs
```

---

# Ingestion Logging

Each ingestion run generates a structured JSON log.

Logs contain:

* ingestion timestamps
* ingestion status
* records processed
* validation information
* output paths
* error details

Example log:

```json
{
  "run_id": "uuid",
  "source_name": "sales_csv",
  "status": "success",
  "records_read": 2823,
  "records_valid": 2823
}
```

---

# Future Roadmap

Future platform improvements may include:

* Airflow orchestration
* Kafka streaming ingestion
* PostgreSQL metadata storage
* cloud object storage
* vector database integration
* OCR pipelines
* document chunking
* embedding pipelines
* semantic search
* RAG ingestion workflows
* ingestion monitoring dashboards

---

# AI / RAG Alignment

The platform is designed to support future LLM and RAG systems.

Examples:

```text
Resume PDF
        ↓
PDF extraction
        ↓
Text chunking
        ↓
Embedding generation
        ↓
Vector database
        ↓
RAG retrieval pipeline
        ↓
LLM application
```

---

# Technologies Used

| Component            | Technology           |
| -------------------- | -------------------- |
| Programming Language | Python               |
| Notebook Environment | Jupyter Notebook     |
| CSV Processing       | Pandas               |
| Excel Processing     | OpenPyXL             |
| API Processing       | Requests / JSON      |
| PDF Extraction       | PyMuPDF / pdfplumber |
| Version Control      | Git                  |
| IDE                  | VS Code              |

---

# Installation

## Clone Repository

```bash
git clone https://github.com/minzi03/QuanSolution_DataVision_Platform.git
```

---

## Create Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Author

Nguyen Minh Duy

Role:

```text
Ingestion and Pipeline Owner
```

QuanSolution DataVision Platform
>>>>>>> c7208d603efdfce628cf9c8c049af1de46d1bb3e
