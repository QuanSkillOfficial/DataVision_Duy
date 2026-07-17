# Week 7 Duy CI Commands

```bash
pip install -r requirements.txt
python scripts/week7_build_shared_test_fixtures.py
python scripts/week7_ci_ingestion_smoke_test.py
pytest tests/data_tests/ -q
python scripts/week7_data_pipeline_smoke_test.py
python scripts/validate_week7.py
python scripts/week7_shared_repo_readiness_check.py
python scripts/week7_shared_integration_smoke_test.py
```

GitHub Actions implementation: `.github/workflows/ci.yml`.

Backend contract smoke (after installing the separate stub dependencies):

```bash
pip install -r backend_stub/requirements.txt
uvicorn backend_stub.main:app --host 127.0.0.1 --port 8000
python scripts/week7_backend_stub_smoke_test.py
```

Compose contract and local runtime commands:

```bash
docker compose -f docker-compose.db.yml config --quiet
docker compose -f docker-compose.yml config --quiet
python scripts/week7_local_docker_integration_smoke_test.py
python scripts/week7_local_docker_integration_smoke_test.py --start-db
```

The default local Docker check validates Compose without starting services.
Use `--start-db` only when Docker Desktop is running. The database run is not
considered complete until Phat's schema and validation query result are
available.

Database integration is a separate job supplied by Phat. Its service must expose PostgreSQL + pgvector and set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` before calling:

```bash
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
```
