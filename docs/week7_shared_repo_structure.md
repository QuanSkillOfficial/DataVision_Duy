# Week 7 Shared Repository Structure

## Purpose

Week 7 moves the platform from separate repositories toward one reproducible
CI and Docker workflow. This file defines the merge layout and ownership
boundaries. It does not claim that the five repositories are already merged.

Machine-readable contract:

```text
integration/shared_repo_manifest.json
```

## Target tree

```text
datavision-platform/
|-- data_engineering/          # Duy
|-- ai/
|   |-- rag/                   # Lap
|   `-- prediction/            # Tuong
|-- week7/
|   `-- database/              # Phat Week 7 database package
|       |-- schema/
|       |-- scripts/
|       |-- validation/
|       `-- outputs/
|-- demo/                      # Phi/Hung
|-- backend_stub/
|-- scripts/
|-- tests/
|-- outputs/
|-- deployment/
|-- docker-compose.db.yml
|-- docker-compose.yml
|-- .env.example
`-- .github/workflows/ci.yml
```

## Active owner paths

### Duy

```text
data_engineering/
scripts/week7_ci_ingestion_smoke_test.py
scripts/load_ingestion_outputs_to_postgres.py
scripts/week7_apply_database_schema.py
scripts/week7_duy_phat_docker_db_integration_test.py
scripts/week7_verify_db_load_result.py
scripts/week7_build_phat_mapping_summary.py
tests/data_tests/
tests/fixtures/data/
outputs/rag_handoff/
outputs/prediction_payloads/
outputs/ui_fixtures/
outputs/integration/week7_duy_phat_docker_db_result.json
```

### Phat

```text
week7/database/schema/schema_v4_fixed.sql
week7/database/schema/setup_database_v3.sql
week7/database/scripts/run_database_setup.py
week7/database/scripts/ci_database_smoke_test.py
week7/database/validation/validation_queries_v3.sql
week7/database/outputs/db_validation/
week7/database/outputs/dashboard_view_samples/
```

### Lap

```text
ai/rag/
ai/rag/scripts/week7_pgvector_smoke_test.py
ai/rag/scripts/week7_rag_ci_smoke_test.py
ai/ai_tests/
outputs/rag/
outputs/ui_fixtures/lap_rag_response_real.json
```

### Tuong

```text
ai/prediction/
scripts/week7_prediction_ci_smoke_test.py
scripts/insert_prediction_logs_to_postgres.py
tests/ai_tests/
outputs/db_integration/
outputs/rag_metadata/
outputs/ui_fixtures/
```

### Phi/Hung

```text
demo/
demo/services/
demo/views/
demo/fixtures/week7/
scripts/week7_ui_ci_smoke_test.py
tests/
backend_stub/
```

## Current readiness

The strict readiness checker currently finds all required Week 7 artifacts in
all five sibling repositories:

```powershell
python scripts/week7_shared_repo_readiness_check.py --strict
```

Expected result:

```text
status: ready
Duy: ready
Phat: ready
Lap: ready
Tuong: ready
Phi/Hung: ready
```

This is artifact-level readiness (`status=ready`). Runtime/owner execution is
tracked independently as `execution_status` and may still be `blocked`; it
requires a running PostgreSQL + pgvector service and one end-to-end execution
session.

Owner execution audits are separate from file presence:

```text
Lap: blocked until live pgvector insert/retrieval proof passes
Tuong: blocked until 20 results/log payloads, CI checks and DB insert proof pass
Phi/Hung: blocked until DB-enriched fixtures and UI contract cleanup pass
```

Use:

```text
python scripts/week7_build_lap_mapping_summary.py --run-lap-tests
python scripts/week7_build_tuong_mapping_summary.py --run-tuong-checks
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
```

The readiness checker distinguishes artifact readiness from execution
readiness:

```text
python scripts/week7_shared_repo_readiness_check.py --strict
python scripts/week7_shared_repo_readiness_check.py --strict --strict-execution
```

The first command checks the merge tree. The second also fails on a recorded
owner audit blocker. For Phi/Hung, the required lineage is `source_id=4`,
`document_external_id=doc_dataflow_technical_report`, `document_db_id=1`, and
the corresponding `ingestion_run_id`.

## Canonical IDs

| Field | Meaning | Owner |
| --- | --- | --- |
| `source_id` | integer `sources.id` | Phat |
| `source_name` | stable source key | Duy |
| `document_external_id` | stable string document key | Duy |
| `document_db_id` | integer `documents.id` | Phat |
| `ingestion_run_id` | Duy run UUID | Duy |

Rules:

- Never put `ingestion_run_id` into `source_id`.
- Resolve `document_external_id` before writing an integer document FK.
- Preserve both external and database document IDs in cross-team payloads.
- Keep snapshot alignment separate from stable ID confirmation.

## Merge order

1. Merge Duy contracts, sample fixtures, tests and handoff builders.
2. Merge Phat schema, setup scripts, validation and database outputs.
3. Run Duy smoke DB loading and query counts back.
4. Merge Lap RAG module and prove pgvector retrieval.
5. Merge Tuong prediction module and insert prediction logs.
6. Merge Phi/Hung UI, fixture validator and backend contract.
7. Run all module jobs and the integration smoke job in GitHub Actions.

## CI entrypoints

```text
python scripts/week7_ci_ingestion_smoke_test.py
pytest tests/data_tests/ -q
python week7/database/scripts/run_database_setup.py --smoke --skip-lap
python week7/database/scripts/ci_database_smoke_test.py
python ai/rag/scripts/week7_rag_ci_smoke_test.py
python scripts/week7_prediction_ci_smoke_test.py
python scripts/week7_ui_ci_smoke_test.py
python scripts/week7_shared_integration_smoke_test.py
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
```

## Cleanup rules

- Keep one official implementation for each active concern.
- Do not copy RAG runtime code into the database package.
- Do not copy prediction runtime code into the database package.
- Do not keep tracked `__pycache__` or `.pyc` files.
- Remove `*_PATCHED.py` after the patched file becomes the official file.
- Retain historical Week 5/6 evidence only under clearly historical paths.
- Do not use obsolete paths in current CI or runbooks.
