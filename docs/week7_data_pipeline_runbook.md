# Week 7 Data Pipeline Runbook

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. Run full local ingestion

```bash
python -m data_engineering.pipelines.ingestion_engine --all
```

Expected valid records: CSV `9,994`, Excel `1,500`, API `30`, PDF `36` pages.

`logs/ingestion_runs.jsonl` is the tracked, append-only run history used to
reconstruct the latest successful run for each source in a clean checkout.
Run-specific files under `logs/runs/` remain useful locally, but new files are
runtime artifacts and do not need to be committed.

## 3. Run CI smoke ingestion

```bash
python scripts/week7_build_shared_test_fixtures.py
python scripts/week7_ci_ingestion_smoke_test.py
```

## 4. Inspect database plan

```bash
python scripts/load_ingestion_outputs_to_postgres.py --dry-run --smoke
```

## 5. Load PostgreSQL

Set the `DB_*` variables from `.env.example`, then run:

```bash
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
```

Use the same command without `--smoke` for all 11,524 structured records.

## 6. Regenerate team handoffs

When the sibling Phat repository is available, validate its Week 7 evidence and
build the stable ID bridge first:

```bash
python scripts/week7_build_phat_mapping_summary.py
python scripts/week7_build_rag_handoff_package.py --db-load-result logs/db_load_results/phat_week7_external_database_proof.json
python scripts/week7_build_prediction_payloads.py --db-load-result logs/db_load_results/phat_week7_external_database_proof.json
python scripts/week7_build_ui_fixtures.py --db-load-result logs/db_load_results/phat_week7_external_database_proof.json
```

The bridge confirms stable `source_id` and `document_db_id` values from Phat's
historical database evidence. The current authoritative result is now Duy's
fresh local Docker load at
`logs/db_load_results/duy_to_phat_db_load_result.json`.

The three Week 7 builders resolve the default identity input from the current
local DB proof. It confirms all four latest run UUIDs and sets
`current_duy_runs_loaded=true`. The external Phat proof remains a fallback for
older clean clones only; it must not replace the current-run evidence.

Run the complete isolated proof with:

```bash
python scripts/week7_duy_phat_docker_db_integration_test.py --mode smoke-then-full
python scripts/week7_verify_db_load_result.py --expected-structured-records 11524 --verify-handoffs
```

Audit the Lap boundary after regenerating the handoff:

```bash
python scripts/week7_build_lap_mapping_summary.py --run-lap-tests
```

Audit the Tuong boundary after regenerating prediction payloads:

```bash
python scripts/week7_build_tuong_mapping_summary.py --run-tuong-checks
```

Audit the Phi/Hung UI boundary after the owner refreshes its Week 7
fixtures:

```bash
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
```

The Tuong audit must report 20 copied inputs, 20 normalized prediction
results, 20 DB payloads, real Duy/Phat IDs in UI fixtures, and a separate
PostgreSQL insert/query result. Sample fixtures and DB dry-runs remain clearly
labelled as contract evidence only.

This writes `outputs/lap_handoff/lap_week7_mapping_summary.json` and records
whether the Lap output files contain executed pgvector proof. A
`pending_db_connection` result is an integration blocker, not a successful
retrieval result.

The Phi/Hung audit writes:

```text
outputs/hung_handoff/hung_week7_mapping_summary.json
logs/hung_handoff/hung_week7_external_proof.json
```

It keeps fixture-contract validity separate from real lineage. The UI copy
must preserve `source_id=4`,
`document_external_id=doc_dataflow_technical_report`, `document_db_id=1`, and
the relevant `ingestion_run_id`. A result of `blocked_on_phi_hung_refresh`
means the UI repository still needs an owner commit; it is not proof that
Duy's source fixture is invalid.

## 7. Validate

```bash
pytest tests/data_tests/ -q
python scripts/week7_data_pipeline_smoke_test.py
python scripts/validate_week7.py
```

## Common errors

- `connection refused`: start Phat's Docker PostgreSQL and verify `DB_PORT`.
- schema preflight failure: run Phat's fixed Week 7 setup; do not patch tables manually.
- null DB IDs: run the real loader or build the Phat Week 7 identity bridge,
  then regenerate all three handoffs.
- `current_ingestion_runs_loaded=false`: the current local DB proof was
  replaced or not regenerated. Run the isolated Docker integration command
  above; do not present the historical fallback as current-run proof.
- UTF-16 Phat evidence: use `week7_build_phat_mapping_summary.py`; it reads both
  UTF-8 and UTF-16 evidence files.
- API unavailable: the configured local JSON fallback is used.
- PDF font warnings: the ingestor suppresses non-actionable pdfminer font descriptor warnings.
