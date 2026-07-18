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

The current fixture has `database_identity_status=database_ids_confirmed`,
`source_id=4`, and `document_db_id=1`, based on Phat's validated Week 7
database evidence. It also has `current_ingestion_runs_loaded=false`; the UI
must present this as a current-run reload limitation rather than an ID failure.

## Phi/Hung acceptance gate

The canonical Duy file above is the producer source of truth. Phi/Hung must
not replace its DB-enriched IDs with `null` when copying it into
`demo/fixtures/week7/`.

Required UI lineage:

```text
source_id=4
document_external_id=doc_dataflow_technical_report
document_db_id=1
ingestion_run_id=<the run referenced by the fixture>
```

The current read-only audit of the sibling Phi/Hung repository is generated
by:

```powershell
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
```

Current audited state:

```text
Phi/Hung tests: 63 passed, 15 skipped
UI smoke test: passed
Hung Duy fixture: stale (null source_id/document_db_id)
Hung Tuong fixtures: contract-shaped but null DB lineage
Lap DataFlow fixture: passed (pgvector, 384 dimensions, document_db_id=1)
Mapping status: blocked_on_phi_hung_refresh
```

Machine-readable evidence:

```text
outputs/hung_handoff/hung_week7_mapping_summary.json
logs/hung_handoff/hung_week7_external_proof.json
docs/week7_duy_phi_hung_mapping_result.md
```

The UI prediction contract must use Tuong's four statuses:

```text
accepted
needs_review
waiting_for_source
failed
```

The staging acceptance threshold is `0.80`. A `0.60` value may be used only
as a UI medium-confidence display boundary and must not be documented as the
acceptance rule.

The Phat dashboard sample must also expose `document_external_id` for
prediction review rows whenever the row has a document FK. The UI may display
the integer `document_id` when the external key is genuinely unavailable, but
it must not fabricate a string key. The Duy-side audit treats missing joined
external IDs as a mapping blocker because they prevent a traceable review
workflow.
