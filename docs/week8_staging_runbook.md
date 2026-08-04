# Week 8 Staging Runbook

## Purpose

This runbook reproduces the Week 8 MVP from one canonical checkout. It does not
depend on a team member's laptop state or an external model download.

The deployment runs:

```text
Duy ingestion outputs
-> Phat PostgreSQL + pgvector
-> Lap chunk loading and live top-k retrieval
-> Tuong prediction and DB logging
-> FastAPI service layer
-> Phi/Hung Streamlit UI
```

## Prerequisites

- Git and Docker Desktop/Engine with Compose v2.
- Ports `5432`, `8000`, and `8501` available, or changed in `.env`.
- At least 4 GB of free Docker memory.
- Python 3.11+ only when running the acceptance wrapper from the host.

## First deployment from a clean checkout

Run from the repository root in PowerShell:

```powershell
Copy-Item .env.example .env
docker compose --project-name datavision-week8-local config --quiet
python scripts/week8_staging_smoke_test.py --start --fresh --project-name datavision-week8-local
```

`--fresh` removes only the named Compose project's disposable local volume
before startup. Do not use it on a shared environment that contains data.

Successful acceptance prints `15/15 checks passed` and writes:

```text
outputs/integration/week8_staging_acceptance.json
```

Open:

- Streamlit UI: `http://localhost:8501`
- FastAPI health: `http://localhost:8000/api/health`
- FastAPI documentation: `http://localhost:8000/docs`

## Normal start, validation, and stop

```powershell
docker compose --project-name datavision-week8-local up -d --build
docker compose --project-name datavision-week8-local ps
python scripts/week8_staging_smoke_test.py --project-name datavision-week8-local
docker compose --project-name datavision-week8-local down
```

The named PostgreSQL volume remains after `down`. To create an isolated CI proof
and clean it automatically:

```powershell
python scripts/week8_staging_smoke_test.py --start --fresh --cleanup --project-name datavision-week8-ci
```

## Expected seeded evidence

The one-shot `staging-seed` container must exit with code 0. It applies the
schema and analytics views, loads four Duy sources, the 36-page DataFlow PDF,
293 Lap chunks with 384-dimensional vectors, 20 Tuong prediction payloads, and
a real pgvector query with citations. Re-running the seed replaces downstream
staging evidence instead of duplicating chunks.

Inspect services and logs:

```powershell
docker compose --project-name datavision-week8-local ps -a
docker compose --project-name datavision-week8-local logs staging-seed
docker compose --project-name datavision-week8-local logs backend
docker compose --project-name datavision-week8-local logs ui
```

Run focused verification:

```powershell
python scripts/week7_shared_repo_readiness_check.py --strict --strict-execution
python ai/rag/scripts/week7_pgvector_smoke_test.py
python scripts/week7_backend_stub_smoke_test.py --base-url http://127.0.0.1:8000
$env:QS_USE_BACKEND='true'
$env:BACKEND_BASE_URL='http://127.0.0.1:8000/api'
pytest tests/test_backend_contract_smoke.py -q
```

## Backup and rollback

Before changing a shared staging database, capture a dump outside the container:

```powershell
docker compose --project-name datavision-week8-local exec -T db pg_dump -U datavision -d datavision_db -Fc > datavision_week8.dump
```

Rollback procedure:

1. Record the failing Git SHA and save service logs and acceptance JSON.
2. Stop the application services without deleting the database volume.
3. Check out the last green Git SHA or use the previously tagged images.
4. Rebuild and rerun acceptance without `--fresh`.
5. Restore the database dump only if the schema/data change cannot be rolled
   forward. Never remove a shared staging volume before verifying the backup.

## Troubleshooting

- Port conflict: change `DB_PORT`, `BACKEND_PORT`, or `UI_PORT` in `.env`.
- Seed failure: inspect `staging-seed` logs; backend intentionally waits for a
  successful seed.
- Stale local image name: ensure `.env` uses
  `UI_IMAGE=datavision-ui:week8-staging`.
- Database not initialized as expected: use a new project name for a disposable
  proof. Init scripts run automatically only on an empty PostgreSQL volume.
- Retrieval returns no chunks: verify `RAG_EMBEDDING_MODE=hash` for the Week 8
  proof and confirm `document_chunks` contains 293 rows.

## Known Week 9 follow-ups

- Replace the deterministic staging embedder with a versioned semantic model
  artifact and evaluate retrieval quality.
- Persist user feedback; the current feedback route validates the contract only.
- Add authentication, secret management, TLS, monitoring, and managed backups
  before any production deployment.
