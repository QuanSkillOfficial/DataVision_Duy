# Week 7 Deployment and Local Integration Runbook

## Scope

This is the first local Docker and CI/CD draft. It is intentionally
staging-oriented, not a production deployment. Phat owns the final database
schema; Duy owns the ingestion loader; Duy and Phi/Hung coordinate CI; the
other module owners provide their smoke tests.

The ten Week 7 readiness outputs are mapped as follows:

| Output | Path or command |
| --- | --- |
| Shared repository structure | `docs/week7_shared_repo_structure.md` |
| GitHub Actions CI draft | `.github/workflows/ci.yml` |
| Docker database setup | `docker-compose.db.yml` |
| Module CI smoke tests | Duy and owner-specific Week 7 smoke entrypoints |
| Local Docker integration test | `scripts/week7_local_docker_integration_smoke_test.py` |
| Full application Compose draft | `docker-compose.yml` |
| Environment template | `.env.example` |
| Backend API skeleton/stub | `backend_stub/` |
| UI fixture mode contract | `outputs/ui_fixtures/` plus Phi/Hung `demo/fixtures/week7/` |
| Deployment runbook | this document |

Artifact presence is not the same as live execution proof. Check both fields in
`outputs/integration/week7_shared_repo_readiness.json`:

```text
status            # merge/artifact readiness
execution_status  # live owner/runtime readiness
```

## Prerequisites

- Docker Desktop with Compose v2.
- Python 3.11 or newer.
- A copy of `.env.example` named `.env`.
- PostgreSQL credentials supplied by Phat for real loading.

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

The backend stub has separate dependencies:

```powershell
python -m pip install -r backend_stub/requirements.txt
```

## Validate Compose files without starting services

```powershell
docker compose -f docker-compose.db.yml config --quiet
docker compose -f docker-compose.yml config --quiet
```

This checks interpolation and structure. It does not prove that PostgreSQL,
Phat's schema, or the UI image is available.

## Start PostgreSQL + pgvector

```powershell
docker compose -f docker-compose.db.yml up -d
```

The init directory enables the `vector` extension. Phat's schema and views
must be applied next; this repository does not silently mount a copied schema.

Check the extension:

```powershell
docker compose -f docker-compose.db.yml exec -T db `
  psql -U datavision -d datavision_db -Atqc `
  "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

Stop the database:

```powershell
docker compose -f docker-compose.db.yml down
```

Remove the local volume only when a full reset is intended:

```powershell
docker compose -f docker-compose.db.yml down -v
```

## Start the contract backend

Local Python mode:

```powershell
python -m pip install -r backend_stub/requirements.txt
uvicorn backend_stub.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
python scripts/week7_backend_stub_smoke_test.py
```

Docker mode:

```powershell
docker compose up -d db backend
python scripts/week7_backend_stub_smoke_test.py
```

The stub returns the standard envelope:

```json
{
  "status": "success",
  "data": {},
  "metadata": {}
}
```

It is a contract test double. It does not replace the production FastAPI
service and does not claim that database-backed routes are complete.

## Run the data pipeline smoke test

```powershell
python scripts/week7_ci_ingestion_smoke_test.py
python -m pytest tests/data_tests/ -q
```

The smoke test uses only `tests/fixtures/data/`, including the local API
fallback. It must not require internet access or a developer-specific path.

## Run database loading

Dry-run:

```powershell
python scripts/load_ingestion_outputs_to_postgres.py --dry-run --smoke
```

Smoke write after Phat's schema is installed:

```powershell
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
```

Full write:

```powershell
python scripts/load_ingestion_outputs_to_postgres.py --write-db
```

Expected smoke counts:

```text
sources              4
pipeline_runs        4 or more
ingestion_logs       4
documents            1
document_pages       36
structured_records   100
```

Expected full structured-record count is 11,524. The loader must print and
persist the query-back result under:

```text
logs/db_load_results/duy_to_phat_db_load_result.json
```

## Regenerate handoffs after confirmed database IDs

```powershell
python scripts/week7_build_rag_handoff_package.py
python scripts/week7_build_prediction_payloads.py
python scripts/week7_build_ui_fixtures.py
python scripts/validate_week7.py
```

Do not manually replace `null` IDs. They become non-null only after a real DB
load returns `source_id` and `document_db_id`.

## Run local Docker contract and integration checks

Contract-only mode:

```powershell
python scripts/week7_local_docker_integration_smoke_test.py
```

Start and probe the database:

```powershell
python scripts/week7_local_docker_integration_smoke_test.py --start-db
```

Start the database and backend:

```powershell
python scripts/week7_local_docker_integration_smoke_test.py --start-full
```

Stop services started by the probe:

```powershell
python scripts/week7_local_docker_integration_smoke_test.py --down
```

## Shared CI commands

```powershell
python scripts/week7_ci_ingestion_smoke_test.py
python scripts/week7_shared_repo_readiness_check.py
python scripts/week7_shared_integration_smoke_test.py
```

After owner repositories are merged, the conditional CI jobs run:

- Phat database setup and smoke test;
- Lap RAG CI smoke test;
- Tuong prediction CI smoke test;
- Phi/Hung UI CI smoke test.

## Week 8 staging checklist

- [ ] Phat fixed schema runs from an empty PostgreSQL volume.
- [ ] Duy smoke DB load returns all six table counts.
- [ ] Lap inserts and retrieves 384-dimensional vectors.
- [ ] Tuong prediction logs and review queue are queryable.
- [ ] Phi/Hung UI consumes the same JSON contracts in fixture mode.
- [ ] Production backend replaces the stub without changing UI envelopes.
- [ ] Real secrets are supplied through the deployment environment, never Git.
