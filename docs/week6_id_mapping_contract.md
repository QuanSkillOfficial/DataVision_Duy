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
documents.id = 1
document_pages.document_id = 1
document_chunks.document_id = 1
rag_query_logs.document_id = 1
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
  "source_id": 2,
  "source_name": "dataflow_technical_report_pdf",
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": 1,
  "ingestion_run_id": "run-uuid-from-duy-log"
}
```

`source_id` and `document_db_id` are database IDs. `ingestion_run_id` is the ingestion execution UUID. These fields must not be used interchangeably.

Current Week 6 Phat mapping for Duy's real outputs:

| Duy Field | Confirmed DB ID |
| --- | ---: |
| `source_name = superstore_sales_csv` | `source_id = 1` |
| `source_name = dataflow_technical_report_pdf` | `source_id = 2` |
| `source_name = dummyjson_products_api` | `source_id = 3` |
| `source_name = product_sales_region_excel` | `source_id = 4` |
| `document_external_id = doc_dataflow_technical_report` | `document_db_id = 1` |

## Tuong Prediction Integration Notes

Tuong should use the Duy payload fields exactly as follows:

| Field In Duy Payload | Should Tuong Treat As | Current Value Before DB | Current Value After Phat DB Load |
| --- | --- | --- | --- |
| `source_name` | Stable source slug | `dataflow_technical_report_pdf` | `dataflow_technical_report_pdf` |
| `source_id` | Phat `sources.id` | `null` | `2` for DataFlow |
| `ingestion_run_id` | Duy run UUID | Duy run UUID | same Duy run UUID |
| `document_external_id` | Stable Duy document key | `doc_dataflow_technical_report` | `doc_dataflow_technical_report` |
| `document_db_id` | Phat `documents.id` | `null` | `1` for DataFlow |

Do not use older example IDs from stale docs if they conflict with the Week 6 Phat mapping. The confirmed DataFlow mapping is:

```json
{
  "source_name": "dataflow_technical_report_pdf",
  "source_id": 2,
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": 1
}
```

Tuong's full Week 6 prediction source of truth is:

```text
DataVision_Tuong/outputs/week6_duy_prediction_results.json
```

The UI fixture files in Tuong's repo are sample/demo outputs and may not contain all 10 Duy payloads.
