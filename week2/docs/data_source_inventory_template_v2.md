# Data Source Inventory Template V2

## 1. Purpose

This document defines the Version 2 Data Source Inventory Template for the ingestion platform.

The inventory is used to:

- document all ingestion sources
- standardize ingestion planning
- support governance and observability
- track ingestion metadata
- prepare for scalable ETL and ELT workflows
- support AI, analytics, and downstream systems
- improve source traceability and ownership

Version 2 extends the original inventory with governance, security, schema, and operational metadata.

This inventory will later support:

- ingestion automation
- metadata management
- PostgreSQL catalog tables
- monitoring systems
- data quality tracking
- lineage and governance systems

---

# 2. Data Source Inventory Table

| Source Name          | Source Type       | File Format | Sample Location               | Expected Fields                   | Ingestion Method         | Frequency | Difficulty | Authentication Required | Schema Version | Sample Available | Last Ingested At     | Expected Volume | Sensitive Data Flag | Downstream Consumer  | Owner | Status  |
| -------------------- | ----------------- | ----------- | ----------------------------- | --------------------------------- | ------------------------ | --------- | ---------- | ----------------------- | -------------- | ---------------- | -------------------- | --------------- | ------------------- | -------------------- | ----- | ------- |
| Customer API         | API               | JSON        | /samples/customer_api.json    | customer_id, email, created_at    | Python Requests API Pull | Daily     | Medium     | Yes                     | v1.0           | Yes              | 2026-05-29T10:00:00Z | Medium          | Yes                 | Analytics Team       | Duy   | Planned |
| Sales CSV            | CSV File          | CSV         | /samples/sales.csv            | order_id, product_id, revenue     | Pandas CSV Loader        | Daily     | Easy       | No                      | v1.0           | Yes              | 2026-05-29T10:00:00Z | Low             | No                  | BI Dashboard         | Duy   | Planned |
| Financial Report PDF | PDF Document      | PDF         | /samples/financial_report.pdf | revenue, expenses, financial_text | pdfplumber Extraction    | Weekly    | Hard       | No                      | v1.0           | Yes              | 2026-05-29T10:00:00Z | Low             | Yes                 | AI Team              | Duy   | Planned |
| Inventory Excel      | Excel Spreadsheet | XLSX        | /samples/inventory.xlsx       | sku, quantity, warehouse          | OpenPyXL Loader          | Weekly    | Medium     | No                      | v1.0           | Yes              | 2026-05-29T10:00:00Z | Medium          | No                  | Operations Dashboard | Duy   | Planned |
| Transaction Database | Database          | PostgreSQL  | db_connection_string          | transaction_id, amount, timestamp | SQLAlchemy Connector     | Real-time | Hard       | Yes                     | v2.0           | No               | Not Yet Ingested     | High            | Yes                 | ML Pipeline          | Duy   | Future  |
| IoT Sensor Stream    | Streaming         | JSON Stream | kafka://sensor_topic          | timestamp, sensor_id, value       | Kafka Consumer           | Streaming | Hard       | Yes                     | v1.0           | No               | Not Yet Ingested     | High            | No                  | Monitoring System    | Duy   | Future  |

---

# 3. Field Definitions

| Field                   | Description                                     |
| ----------------------- | ----------------------------------------------- |
| Source Name             | Human-readable source identifier                |
| Source Type             | Source category such as API, CSV, PDF, Database |
| File Format             | Data format received from source                |
| Sample Location         | Path or location of sample data                 |
| Expected Fields         | Expected schema or columns                      |
| Ingestion Method        | Planned ingestion technique or tool             |
| Frequency               | Expected ingestion schedule                     |
| Difficulty              | Estimated ingestion complexity                  |
| Authentication Required | Whether authentication is needed                |
| Schema Version          | Version of source schema                        |
| Sample Available        | Whether sample data exists                      |
| Last Ingested At        | Last successful ingestion timestamp             |
| Expected Volume         | Estimated ingestion data size                   |
| Sensitive Data Flag     | Whether source contains sensitive data          |
| Downstream Consumer     | Team or system consuming the data               |
| Owner                   | Responsible ingestion owner                     |
| Status                  | Current ingestion implementation status         |

---

# 4. Authentication Required

## Purpose

Defines whether the ingestion source requires authentication or credentials.

Examples:

- API keys
- OAuth tokens
- database credentials
- cloud access tokens

---

## Allowed Values

| Value | Meaning                    |
| ----- | -------------------------- |
| Yes   | Authentication is required |
| No    | Public or local source     |

---

# 5. Schema Version

## Purpose

Tracks schema evolution and source structure changes.

Schema versioning helps:

- ingestion validation
- backward compatibility
- schema drift detection
- pipeline maintenance

---

## Recommended Format

```text id="u1m8yt"
v1.0
v1.1
v2.0
```

---

# 6. Sample Available

## Purpose

Indicates whether sample input data exists for testing and validation.

Sample data is important for:

- ingestion prototype development
- parser validation
- testing
- debugging

---

## Allowed Values

| Value |
| ----- |
| Yes   |
| No    |

---

# 7. Last Ingested At

## Purpose

Tracks the latest successful ingestion execution time.

Useful for:

- freshness monitoring
- operational tracking
- SLA monitoring
- ingestion observability

---

## Recommended Format

```text id="m74f6j"
2026-05-29T10:15:00Z
```

Use:

- UTC timezone
- ISO 8601 format

---

# 8. Expected Volume

## Purpose

Estimates expected ingestion data size or throughput.

Useful for:

- infrastructure planning
- storage estimation
- performance optimization
- pipeline scaling

---

## Volume Definitions

| Level  | Meaning                    |
| ------ | -------------------------- |
| Low    | Less than 10 MB/day        |
| Medium | Between 10 MB and 1 GB/day |
| High   | Greater than 1 GB/day      |

---

# 9. Sensitive Data Flag

## Purpose

Indicates whether the source contains sensitive or regulated data.

Examples:

- personally identifiable information (PII)
- financial records
- confidential business data
- internal operational data

---

## Allowed Values

| Value | Meaning                      |
| ----- | ---------------------------- |
| Yes   | Contains sensitive data      |
| No    | Non-sensitive or public data |

---

# 10. Downstream Consumer

## Purpose

Identifies which team, system, or application consumes the ingested data.

This improves:

- governance
- ownership clarity
- dependency management
- platform coordination

---

## Example Consumers

- Analytics Team
- BI Dashboard
- AI Team
- ML Pipeline
- RAG System
- Streamlit Application
- Monitoring Dashboard

---

# 11. Supported Source Types

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

Spreadsheet-based business datasets.

Examples:

- inventory reports
- KPI tracking
- operational spreadsheets

---

## PDF Sources

Semi-structured or unstructured documents.

Examples:

- invoices
- financial reports
- contracts
- research documents

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

# 12. Governance Rules

- Every source must have a clearly assigned owner.
- Sensitive sources must be flagged before production ingestion.
- Schema changes require schema version updates.
- Authentication requirements must be documented.
- Sample data should be available whenever possible.
- New sources must be documented before ingestion development begins.
- Deprecated sources should remain documented for historical traceability.
- Downstream consumers must be identified before production deployment.

---

# 13. Operational Usage

This inventory supports:

## Ingestion Team

To build and manage ingestion pipelines.

## Database Team

To design metadata and governance tables.

## Analytics Team

To understand source availability and freshness.

## AI Team

To identify reliable sources for RAG and LLM workflows.

## Platform Team

To monitor ingestion scalability and operational dependencies.

---

# 14. Future Expansion

Future versions of this inventory may include:

- ingestion SLA tracking
- schema drift detection
- lineage metadata
- source health monitoring
- data quality metrics
- ingestion latency tracking
- retry policies
- ownership escalation rules
- cloud storage metadata
- observability integration

---

# 15. Example Production Use Case

```text id="4rc0ye"
Customer API
↓
API ingestion pipeline
↓
Raw JSON storage
↓
Validation and staging
↓
Clean customer table
↓
Analytics dashboard
↓
AI recommendation system
```

The inventory tracks:

- source metadata
- ingestion ownership
- schema version
- authentication requirements
- downstream dependencies

---

# 16. Summary

The Data Source Inventory Template V2 provides a production-oriented metadata foundation for the ingestion platform.

It improves:

- ingestion governance
- source traceability
- operational visibility
- schema management
- downstream coordination
- scalability planning

This inventory serves as a centralized reference for ingestion architecture, pipeline planning, and future platform expansion.
