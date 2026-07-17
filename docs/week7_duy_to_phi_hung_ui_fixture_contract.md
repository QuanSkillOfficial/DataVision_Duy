# Week 7 Duy to Phi/Hung UI Fixture Contract

Fixture:

`outputs/ui_fixtures/duy_week7_database_enriched_summary.json`

Top-level metrics include four sources, four successful latest runs, 11,524 structured records, 36 PDF pages, average data quality `99.63`, latest document metadata, and handoff paths.

`latest_document` includes:

- `source_id`
- `document_db_id`
- `document_external_id`
- `ingestion_run_id`
- `file_name`
- `page_count`
- `file_hash_sha256`
- `parsing_status`

The field `database_identity_status` is `pending_database_load` before real PostgreSQL loading and `database_ids_confirmed` after successful loading. The UI should display pending mapping honestly instead of treating null IDs as zero.
