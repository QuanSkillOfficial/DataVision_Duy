# Week 7 Final Project Review

Review date: 2026-07-20
Owner: Nguyen Minh Duy  
Scope: Duy ingestion, database loading, CI/Docker readiness, and handoffs

## Result

Duy's Week 7 ownership boundary is complete and execution-proven:

- the data module is shared-repo-ready;
- ingestion unit and CI smoke tests pass;
- PostgreSQL + pgvector starts in an isolated Docker project;
- the full Compose draft starts PostgreSQL and the backend stub, passes the API
  contract smoke test, and removes its isolated runtime;
- Phat's schema contract is applied from zero;
- the four latest Duy runs load in smoke and full modes;
- the loader queries exact counts back from PostgreSQL;
- current database IDs enrich the Lap, Tuong, and Phi/Hung handoffs;
- GitHub Actions contains both ingestion and DB-loading jobs;
- the local test stack is removed after verification.

Sibling-owner execution remains separate. Lap, Tuong, and Phi/Hung still need
to replace their pending/stale outputs with owner-generated current proofs.

## Coverage against `duy_week7.pdf`

| Duy task | Status | Authoritative evidence |
| --- | --- | --- |
| 1. Shared-repo-ready module | Complete | `data_engineering/`, `scripts/`, `tests/data_tests/` |
| 2. Real PostgreSQL integration | Complete | `logs/db_load_results/duy_to_phat_db_load_result.json` |
| 3. CI-friendly ingestion smoke | Complete | `scripts/week7_ci_ingestion_smoke_test.py` |
| 4. GitHub Actions coordination | Complete draft | `.github/workflows/ci.yml`, `docs/week7_duy_ci_commands.md` |
| 5. CI-compatible DB loading | Complete | DB dry-run, smoke and full modes plus environment-based connection |
| 6. DB-enriched RAG handoff | Complete | `outputs/rag_handoff/week7_document_pages_db_enriched.jsonl` |
| 7. DB-enriched prediction payloads | Complete | 20 current payloads, including the 10 required edge/integration cases |
| 8. DB-enriched UI fixture | Complete | `outputs/ui_fixtures/duy_week7_database_enriched_summary.json` |
| 9. Stable CI sample data | Complete | `tests/fixtures/data/` |
| 10. CI requirements | Complete | `requirements.txt`, `.env.example` |
| 11. Data test coverage | Complete | 59 passing tests |
| 12. Data pipeline runbook | Complete | `docs/week7_data_pipeline_runbook.md` |

Result: all 12 tasks and all 15 final deliverables assigned to Duy are
present and locally verified.

## Platform-wide readiness against all five PDFs

| Week 7 outcome | Current state |
| --- | --- |
| Shared repository structure | Manifest, paths and merge plan complete; physical owner-module merge is still a team action |
| GitHub Actions CI draft | Complete; Duy/DB/backend jobs are active and sibling jobs activate after merge |
| Docker Compose database | Complete and execution-proven with PostgreSQL 16 + pgvector |
| CI smoke tests for every module | Duy and backend proven; Lap/Tuong/Phi-Hung execution gates remain owner work |
| Local Docker integration | DB and backend proven; complete RAG/prediction/UI runtime awaits owner merge |
| First full-app Compose draft | Complete; UI remains an optional profile requiring Phi/Hung's image/module |
| `.env.example` | Complete |
| Backend API skeleton/stub | Complete and contract-smoke-tested |
| UI fixture mode | Duy/Phat/Lap fixtures and UI smoke pass; Tuong-derived fixture IDs and full UI unit execution remain pending |
| Deployment runbook draft | Complete; team sign-off remains pending |

Therefore the Duy repository is complete for its ownership boundary, but the
whole platform is not yet a single fully executed runtime. Reporting these two
states separately prevents Duy's completed work from masking sibling-owner
integration blockers.

## Main fixes

### Current-run database proof

The previous state used Phat's historical snapshot for stable IDs while
recording `current_duy_runs_loaded=false`. The new authoritative file is:

```text
logs/db_load_results/duy_to_phat_db_load_result.json
```

It now records:

```text
status=passed
connection_status=connected
schema_version=schema_v4_fixed
current_duy_runs_loaded=true
```

The loader queries the requested ingestion UUIDs back from PostgreSQL and
stores those exact values under `snapshot_alignment.database_run_ids`. A row
count alone is no longer accepted as proof that the current Duy runs loaded.

The independent Docker execution trace is:

```text
outputs/integration/week7_duy_phat_docker_db_result.json
```

### Stable ID order

The loader now inserts fresh sources in the agreed order:

```text
CSV -> source_id 1
Excel -> source_id 2
API -> source_id 3
PDF -> source_id 4
```

The DataFlow document resolves to `document_db_id=1` through
`document_external_id=doc_dataflow_technical_report`.

### Smoke-to-full idempotency

Running smoke mode and then full mode no longer leaves the database at 100
rows or duplicates run/log rows. Existing run IDs refresh only the mutable
source/document snapshots:

```text
pipeline_runs=4
ingestion_logs=4
structured_records=11,524
document_pages=36
```

### Page handoff compatibility

The PostgreSQL page writer now accepts both `character_count` and the Week 7
handoff alias `char_count`. The page-plan validator resolves either
`document_external_id` or the legacy `document_id`, while still requiring one
stable external document identifier.

### Docker isolation

The fixed `container_name` was removed from both Compose drafts. Tests now use
an isolated project name and port, so they do not collide with another team
database. The integration runner removes its container, network, and volume.

### Standalone CI schema

Phat remains the schema owner. Duy stores a pinned schema-v4 snapshot only for
offline standalone CI:

```text
deployment/database/init/10_phat_schema_v4_fixed.sql
```

Future Phat migrations must be reviewed before this snapshot is updated.

## Exact database proof

| Check | Result |
| --- | ---: |
| pgvector extension | enabled |
| `sources` | 4 |
| `pipeline_runs` | 4 |
| `ingestion_logs` | 4 |
| `documents` | 1 |
| `document_pages` | 36 |
| smoke `structured_records` | 100 |
| full `structured_records` | 11,524 |
| latest Duy run IDs present | 4/4 |
| isolated services removed | yes |

## Current handoffs

```text
outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
outputs/rag_handoff/week7_rag_handoff_manifest.json
outputs/prediction_payloads/tuong_week7_prediction_payloads.json
outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json
outputs/ui_fixtures/duy_week7_database_enriched_summary.json
```

All current outputs preserve:

```text
source_id=4
document_external_id=doc_dataflow_technical_report
document_db_id=1
ingestion_run_id=4c595851-c11e-48e3-8c79-69f6fa52d282
current_ingestion_run(s)_loaded=true
```

## Cleanup decision

Removed or ignored:

- Python bytecode and pytest runtime caches;
- generated temporary CI workspaces;
- fixed Docker container naming that caused cross-project collisions;
- stale statements claiming Docker/current-run DB proof was unavailable.

Kept intentionally:

- Week 1/2 inputs and validators used for historical reproducibility;
- Week 5/6 contracts and evidence as historical milestones;
- Phat's external proof as fallback/history, not current authoritative proof;
- all 20 Week 7 prediction payload cases required by Tuong.

No active duplicate implementation or `*_PATCHED.py` remains in Duy's repo.

## Verification

```text
python -m pytest tests/data_tests/ -q -p no:cacheprovider
python scripts/week7_ci_ingestion_smoke_test.py
python scripts/week7_data_pipeline_smoke_test.py
python scripts/week7_duy_phat_docker_db_integration_test.py --mode smoke-then-full
python scripts/week7_verify_db_load_result.py --expected-structured-records 11524 --verify-handoffs
python scripts/validate_week7.py
python scripts/week7_shared_integration_smoke_test.py
docker compose -f docker-compose.db.yml config --quiet
docker compose -f docker-compose.yml config --quiet
```

Observed result:

| Check | Result |
| --- | --- |
| Data tests | 59 passed |
| Ingestion CI smoke | passed |
| Data-pipeline smoke | passed |
| Duy-to-Phat Docker DB integration | passed |
| Full Compose backend contract smoke | passed; isolated runtime removed |
| Current DB/handoff verification | passed |
| Week 7 validator | passed; 96 required files |
| Compose validation | both passed |

## Remaining cross-team work

| Owner | Required proof |
| --- | --- |
| Lap | Consume the current 36-page handoff, insert real chunks, run pgvector retrieval, and insert a RAG query log |
| Tuong | Consume all 20 current payloads, return normalized predictions/DB payloads, and prove prediction-log insertion |
| Phi/Hung | Refresh Tuong-derived fixtures, install UI requirements, and rerun the full unit/lineage checks |
| Phat | Adopt/confirm the same current Duy run IDs in the shared database environment and own future schema migration |

These dependencies do not reopen Duy's ingestion or DB-loading tasks. They are
the next owner actions needed to make `--strict-execution` pass for the whole
platform.
