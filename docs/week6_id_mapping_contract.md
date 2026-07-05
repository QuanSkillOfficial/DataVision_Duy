# Week 6 ID Mapping Contract

Owner: Nguyen Minh Duy  
Consumers: Phat, Lap, Tuong, Phi/Hung

## Why This Matters

Week 6 integration can break if different modules use the same field name for different meanings. The most important distinction is:

- Duy and Lap use string document IDs for external traceability.
- Phat's PostgreSQL schema uses integer primary keys internally.

## Canonical ID Rules

| Field | Meaning | Owner | Database mapping | Used by |
| --- | --- | --- | --- | --- |
| `source_name` | Stable source name from ingestion config | Duy | `sources.name` | Phat, Phi/Hung |
| `source_id` | Internal PostgreSQL source primary key | Phat | `sources.id` | Duy writer, Tuong logs |
| `ingestion_run_id` / `run_id` | UUID for one ingestion execution | Duy | `ingestion_logs.run_id`; included inside `pipeline_runs.run_name` for Phat schema_v4 | Phat, Phi/Hung |
| `document_id` | Duy external document key, e.g. `doc_dataflow_technical_report` | Duy | `documents.document_external_id` | Phat, Lap, Tuong |
| `document_db_id` | Internal PostgreSQL document primary key | Phat | `documents.id` | document_pages, document_chunks, rag_query_logs |
| `chunk_id` | Stable RAG chunk key | Lap | `document_chunks.chunk_id` | Lap, Phi/Hung |

## Correct Document Mapping

```text
Duy document_id string
  -> documents.document_external_id
  -> documents.id
  -> document_pages.document_id
  -> document_chunks.document_id
  -> rag_query_logs.document_id
```

Example:

```text
Duy document_id = doc_dataflow_technical_report
documents.document_external_id = doc_dataflow_technical_report
documents.id = 3
document_pages.document_id = 3
document_chunks.document_id = 3
rag_query_logs.document_id = 3
```

## Incorrect Mapping To Avoid

Do not insert Duy's string `document_id` directly into:

```text
document_pages.document_id
document_chunks.document_id
rag_query_logs.document_id
```

Those fields should reference the internal integer `documents.id`.

## Prediction Payload Rules For Tuong

Before Phat loads Duy outputs into PostgreSQL, Duy's prediction payload should use:

```json
{
  "source_id": null,
  "source_name": "dataflow_technical_report_pdf",
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": null,
  "ingestion_run_id": "run-uuid-from-duy-log"
}
```

After Phat loads the same source and document into PostgreSQL, downstream services may enrich the payload with:

```json
{
  "source_id": 4,
  "source_name": "dataflow_technical_report_pdf",
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": 3,
  "ingestion_run_id": "run-uuid-from-duy-log"
}
```

`source_id` and `document_db_id` are database IDs. `ingestion_run_id` is the ingestion execution UUID. These fields must not be used interchangeably.
