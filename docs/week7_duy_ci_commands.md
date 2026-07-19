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
python scripts/week7_verify_db_load_result.py --expected-structured-records 11524 --verify-handoffs
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
python scripts/week7_duy_phat_docker_db_integration_test.py --mode smoke-then-full
```

The default local Docker check validates Compose without starting services.
The Duy-to-Phat runner creates a separate Docker project at port `55432`,
proves both smoke and full DB modes, rebuilds handoffs, and removes its test
stack. Its current result confirms all latest Duy run UUIDs.

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

The workflow contains Duy's standalone `data-db-loading-ci` job. It starts a
pgvector service, applies the pinned Phat schema contract, loads current Duy
runs in smoke mode, rebuilds handoffs, and verifies exact counts. Phat still
owns the shared database job and future schema changes.

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

The audit currently reports `blocked_on_phi_hung_refresh`. Duy, Phat, and Lap
fixtures pass, but four Tuong batch rows and four Tuong review rows still have
null `document_db_id`; the full UI tests also require the pinned Phi/Hung
dependencies. Do not weaken Duy's canonical DB lineage to make a downstream
fixture pass. Refresh Tuong's fixtures, install the UI requirements, and rerun
the audit.
