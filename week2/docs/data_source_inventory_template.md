# data_source_inventory_template.md

# Data Source Inventory Template

## 1. Purpose

This document tracks all current and future data sources connected to the platform.

The purpose of this inventory is to:

- identify all ingestion sources
- document source structure and format
- standardize ingestion planning
- support pipeline development
- improve observability and governance
- prepare for future ingestion scaling

This inventory will be used as the foundation for ingestion prototypes and pipeline implementation in future development phases.

---

# 2. Data Source Inventory

| Source Name          | Source Type       | File Format | Sample Location               | Expected Fields                   | Ingestion Method         | Frequency | Difficulty | Owner | Status  |
| -------------------- | ----------------- | ----------- | ----------------------------- | --------------------------------- | ------------------------ | --------- | ---------- | ----- | ------- |
| DummyJSON Products API | API | JSON | https://dummyjson.com/products | id, title, category, price, rating, stock, sku | Python Requests API Pull with local raw fallback | On demand | Medium | Duy | Ready |
| Superstore CSV | CSV File | CSV | data/sample_inputs/Superstore.csv | row_id, order_id, customer_id, product_id, sales, quantity, profit | Pandas CSV Loader | On demand | Easy | Duy | Ready |
| DataFlow Technical Report | PDF Document | PDF | data/sample_inputs/DataFlow_Technical_Report.pdf | page_number, clean_text, char_count, word_count | pdfplumber Extraction | On demand | Medium | Duy | Ready |
| Product Sales Region Excel | Excel Spreadsheet | XLSX | data/sample_inputs/Product-Sales-Region.xlsx | date, region, product, quantity, totalprice, orderid | Pandas/OpenPyXL Loader | On demand | Medium | Duy | Ready |
| Transaction Database | Database          | PostgreSQL  | db_connection_string          | transaction_id, amount, timestamp | SQLAlchemy Connector     | Real-time | Hard       | Duy   | Future  |
| IoT Sensor Stream    | Streaming         | JSON Stream | kafka://sensor_topic          | timestamp, sensor_id, value       | Kafka Consumer           | Streaming | Hard       | Duy   | Future  |

---

# 3. Field Definitions

| Field            | Description                              |
| ---------------- | ---------------------------------------- |
| Source Name      | Name of the data source                  |
| Source Type      | Type of source (API, CSV, PDF, DB, etc.) |
| File Format      | Format of incoming data                  |
| Sample Location  | Location of sample input data            |
| Expected Fields  | Expected schema or columns               |
| Ingestion Method | Planned ingestion technique or tool      |
| Frequency        | How often data arrives                   |
| Difficulty       | Estimated ingestion complexity           |
| Owner            | Responsible ingestion owner              |
| Status           | Current ingestion development status     |

---

# 4. Supported Source Types

## API Sources

External systems accessed through REST or GraphQL APIs.

Examples:

- payment APIs
- CRM systems
- SaaS integrations

---

## CSV Sources

Structured flat-file datasets.

Examples:

- sales exports
- transaction records
- marketing reports

---

## Excel Sources

Spreadsheet-based business data.

Examples:

- inventory reports
- financial spreadsheets
- KPI tracking files

---

## PDF Sources

Semi-structured or unstructured documents.

Examples:

- invoices
- contracts
- research reports

---

## Database Sources

Structured relational or warehouse systems.

Examples:

- PostgreSQL
- MySQL
- SQL Server
- Snowflake

---

## Streaming Sources

Continuous real-time event systems.

Examples:

- Kafka streams
- sensor events
- WebSocket feeds

---

# 5. Ingestion Method Examples

| Method             | Description                       |
| ------------------ | --------------------------------- |
| API Pull           | Retrieve data using HTTP requests |
| File Upload        | Manual or automated file loading  |
| Database Connector | Direct database connection        |
| Stream Consumer    | Real-time event consumption       |
| Batch Loader       | Scheduled batch ingestion         |

---

# 6. Frequency Definitions

| Frequency | Meaning                             |
| --------- | ----------------------------------- |
| Real-time | Continuous streaming ingestion      |
| Hourly    | Data arrives every hour             |
| Daily     | Data arrives once per day           |
| Weekly    | Data arrives weekly                 |
| Monthly   | Data arrives monthly                |
| On Demand | Manual or event-triggered ingestion |

---

# 7. Difficulty Scale

| Level  | Meaning                                       |
| ------ | --------------------------------------------- |
| Easy   | Structured flat files with stable schemas     |
| Medium | Requires transformation or validation         |
| Hard   | Unstructured, complex, or real-time ingestion |

---

# 8. Status Definitions

| Status      | Meaning                               |
| ----------- | ------------------------------------- |
| Planned     | Source identified but not implemented |
| In Progress | Currently under development           |
| Testing     | Under ingestion validation            |
| Production  | Live ingestion pipeline               |
| Deprecated  | No longer used                        |

---

# 9. Inventory Management Rules

- Every new source must be documented before ingestion development begins.
- Sample data should be stored whenever possible.
- Schema changes should update this inventory.
- Deprecated sources should remain documented for historical tracking.
- Each source must have a clearly assigned owner.

---

# 10. Future Expansion

Future versions of this inventory may include:

- schema versioning
- data quality metrics
- SLA tracking
- source authentication methods
- lineage metadata
- ingestion latency metrics
- monitoring dashboards

---

# 11. Conclusion

This inventory serves as the central reference for ingestion planning and source management.

A well-maintained inventory improves:

- ingestion reliability
- pipeline scalability
- debugging efficiency
- onboarding clarity
- long-term platform maintainability
