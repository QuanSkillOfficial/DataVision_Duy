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
