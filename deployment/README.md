# Deployment Draft

This folder contains the Week 7 local deployment boundary:

- `Dockerfile.data` packages Duy's CI-safe ingestion smoke test.
- `database/init/00_extensions.sql` enables pgvector in a fresh database.
- `../docker-compose.db.yml` starts PostgreSQL + pgvector.
- `../docker-compose.yml` starts the database and backend contract stub, with
  optional data and UI profiles.

The production database schema remains Phat's responsibility. The production
backend and the Streamlit image remain team-level deliverables. See
`docs/week7_deployment_runbook.md` before starting a real load.

## Week 7 readiness outputs

| Required output | Repository path | Current scope |
| --- | --- | --- |
| Shared repo structure | `docs/week7_shared_repo_structure.md` | Merge contract and owner boundaries |
| GitHub Actions draft | `.github/workflows/ci.yml` | Duy jobs active; owner jobs activate after merge |
| Database Compose | `docker-compose.db.yml` | PostgreSQL 16 + pgvector |
| Module CI smoke tests | `scripts/week7_*_smoke_test.py` plus owner entrypoints | Duy and shared contract tests available |
| Local Docker integration | `scripts/week7_local_docker_integration_smoke_test.py` | Contract mode by default; runtime mode needs Docker |
| Full-app Compose draft | `docker-compose.yml` | DB, backend stub, ingestion profile, UI image contract |
| Environment template | `.env.example` | Local non-secret defaults |
| Backend API stub | `backend_stub/` | Contract test double, not production backend |
| UI fixture mode | `outputs/ui_fixtures/` and Phi/Hung `demo/fixtures/week7/` | Duy output ready; owner refresh audit tracked |
| Deployment runbook | `docs/week7_deployment_runbook.md` | Local, CI, DB loading, and Week 8 checklist |

Machine-readable readiness is written to
`outputs/integration/week7_shared_repo_readiness.json`. Its `status` checks
artifact availability; `execution_status` remains separate until every owner
has supplied live runtime proof.
