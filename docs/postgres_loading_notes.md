# PostgreSQL Loading Notes

> Historical Week 5 note. The executable Week 6 source of truth is `data_engineering/storage/postgres_writer.py` together with `docs/week6_database_loading_result.md`.

Owner: Nguyen Minh Duy

## Current Scope

The Week 5 PostgreSQL writer is prepared as a DB-API compatible skeleton in:

```text
data_engineering/storage/postgres_writer.py
```

It is designed to work with Phat's schema_v2/schema_v3 direction, but it does not own table creation. Phat owns schema files and constraints.

## Writer Functions

| Function | Target table | Input |
| --- | --- | --- |
| `insert_source(conn, ingestion_result)` | `sources` | One ingestion result |
| `insert_ingestion_log(conn, ingestion_result, source_id)` | `ingestion_logs` | One run log |
| `insert_document(conn, pdf_metadata, source_id)` | `documents` | PDF metadata |
| `insert_document_pages(conn, document_pages_jsonl_path, document_id)` | `document_pages` | Duy page-level JSONL |
| `insert_structured_records(conn, clean_csv_path, source_id)` | `structured_records` | Clean CSV/API/Excel output |
| `build_dry_run_summary(ingestion_result)` | none | DB insert readiness check |

## Expected Loading Order

1. Insert or find source in `sources`.
2. Insert ingestion log into `ingestion_logs`.
3. For PDF sources, insert document metadata into `documents`.
4. For PDF sources, load `document_pages.jsonl` into `document_pages`.
5. For CSV, Excel, and API sources, load clean CSV rows into `structured_records`.

## Current Limitation

The writer is intentionally conservative for Week 5. It prepares SQL shape and dry-run checks, but full integration should wait for Phat's final schema_v3 table definitions and local database credentials.
