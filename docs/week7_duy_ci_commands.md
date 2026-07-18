# Week 7 Duy CI Commands

```bash
pip install -r requirements.txt
python scripts/week7_build_shared_test_fixtures.py
python scripts/week7_build_phat_mapping_summary.py
python scripts/week7_build_lap_mapping_summary.py --run-lap-tests
python scripts/week7_build_tuong_mapping_summary.py --run-tuong-checks
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
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
Use `--start-db` only when Docker Desktop is running. Phat's committed Week 7
evidence confirms stable database IDs and full snapshot counts; a fresh runtime
load is still required to prove Duy's latest run UUIDs.

The Lap mapping command intentionally reports two separate gates:

- the Duy page handoff contract;
- Lap's live pgvector insertion/retrieval proof.

The first can pass while the second is still pending. Do not convert the
DataFlow UI fixture into a database-proof claim.

The Tuong mapping command also keeps separate gates:

- Duy's 20-payload handoff contract;
- Tuong's 20-result/log contract;
- Tuong's unit-test and prediction smoke proof;
- real PostgreSQL prediction-log insert/query proof.

A four-state sample UI fixture or a one-row dry-run does not satisfy the real
lineage/database gate.

Database integration is a separate job supplied by Phat. Its service must expose PostgreSQL + pgvector and set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` before calling:

```bash
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
```

Phi/Hung UI mapping audit:

```bash
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
```

This is a read-only audit of the sibling UI repository. It verifies the
canonical Duy/Phat IDs, DataFlow RAG fixture, Tuong status fields, active UI
paths, and the UI test/smoke result. It writes:

```text
outputs/hung_handoff/hung_week7_mapping_summary.json
logs/hung_handoff/hung_week7_external_proof.json
```

The audit currently reports `blocked_on_phi_hung_refresh` because the sibling
fixture copies still have null `source_id`/`document_db_id` values. Do not
change the canonical Duy fixture to null values to make the UI test pass;
refresh the Phi/Hung fixtures from the owner repositories and rerun the audit.
