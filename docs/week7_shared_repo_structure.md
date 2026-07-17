# Week 7 Shared Repository Structure

## Purpose

Week 7 is the transition from separate repositories to one testable platform path.
This document is the merge map for Duy, Phat, Lap, Tuong, and Phi/Hung. It does
not claim that the external modules have already been merged or executed from this
repository.

The machine-readable version is:

```text
integration/shared_repo_manifest.json
```

## Target tree

```text
datavision-platform/
├── data_engineering/       # Duy
├── ai/
│   ├── rag/                # Lap
│   └── prediction/         # Tuong
├── database/               # Phat
├── demo/                   # Phi/Hung
├── backend_stub/           # contract stub before production API
├── scripts/                # shared builders and smoke tests
├── tests/                  # module and contract tests
├── outputs/                # handoffs, fixtures and evidence
├── deployment/             # Dockerfiles and database init
├── docker-compose.db.yml
├── docker-compose.yml
├── .env.example
└── .github/workflows/ci.yml
```

## Current Duy repository scope

Available now:

- `data_engineering/` and Duy's deterministic test fixtures.
- `scripts/week7_ci_ingestion_smoke_test.py`.
- `scripts/week7_shared_integration_smoke_test.py`.
- `docker-compose.db.yml` and the full-app draft `docker-compose.yml`.
- `backend_stub/` with the shared API envelope.
- `.github/workflows/ci.yml` with the data, backend-contract, readiness and
  integration-contract jobs.

Pending from other repositories:

- Phat's Week 7 fixed schema, database smoke job and fresh view samples.
- Lap's Week 7 pgvector execution proof.
- Tuong's Week 7 prediction CI proof and database log result.
- Phi/Hung's Week 7 fixture validator, UI smoke test and backend stub/UI merge.

The readiness checker reports this explicitly:

```powershell
python scripts/week7_shared_repo_readiness_check.py
```

Use strict mode only after the five repositories are merged:

```powershell
python scripts/week7_shared_repo_readiness_check.py --strict
```

## Canonical ID rule

| Field | Meaning | Owner |
| --- | --- | --- |
| `source_id` | Integer `sources.id`; never an ingestion UUID | Phat |
| `source_name` | Stable source key | Duy |
| `document_external_id` | Stable string document key | Duy/Lap/Tuong |
| `document_db_id` | Integer `documents.id` after lookup | Phat |
| `ingestion_run_id` | Duy run UUID | Duy |

The string `document_external_id` must be resolved before inserting into an
integer foreign-key column. `ingestion_run_id` must never be placed in
`source_id`.

## Merge and verification order

1. Merge Duy contracts and stable fixtures.
2. Apply Phat schema and start PostgreSQL + pgvector.
3. Run Duy smoke DB loading and query counts back.
4. Insert Lap chunks and run a real similarity query.
5. Insert Tuong prediction logs and query the review queue.
6. Replace UI fixtures with the outputs from the database and RAG/prediction jobs.
7. Run the complete GitHub Actions workflow.

## Files to use instead of obsolete copies

Only one active copy of each shared concern should remain after merge:

- database setup belongs under Phat's `database/` or `week7/database/`;
- RAG loading/retrieval belongs under `ai/rag/`;
- prediction inference/log building belongs under `ai/prediction/`;
- UI service and fixture validation belongs under `demo/`;
- shared orchestration belongs under `scripts/`;
- old patched SQL/scripts should be archived outside active runtime paths.

Do not copy a file into another repository without updating its owner contract
and its test command.
