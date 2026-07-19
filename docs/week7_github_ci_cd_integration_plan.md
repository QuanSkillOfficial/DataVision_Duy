# Week 7 GitHub CI/CD Integration Plan

Duy and Phi/Hung co-lead the shared workflow. The current draft is in
`.github/workflows/ci.yml`.

## Jobs in the draft

| Job | Current state | Owner |
| --- | --- | --- |
| `data-engineering-ci` | Active and passing in Duy's repository | Duy |
| `data-db-loading-ci` | Active; starts pgvector, applies schema, loads current Duy smoke data, verifies handoffs | Duy |
| `backend-contract-ci` | Active when the stub dependencies are installed | Duy/shared |
| `shared-readiness-ci` | Active; reports missing external owner artifacts without hiding them | Duy |
| `integration-contract-ci` | Active; validates Duy outputs and both Compose files | Duy |
| `database-ci` | Conditional until `week7/database/` is merged | Phat |
| `rag-ci` | Conditional until the shared RAG smoke script is merged | Lap |
| `prediction-ci` | Conditional until the prediction smoke script is merged | Tuong |
| `ui-ci` | Conditional until the UI smoke script and fixtures are merged | Phi/Hung |

The conditional jobs are deliberate. The `module-discovery` job checks the
checked-out tree and exposes explicit outputs for Phat, Lap, Tuong, and
Phi/Hung. A standalone Duy repository therefore skips absent owner jobs; the
same jobs activate automatically after those modules are merged.

## Commands

```powershell
python scripts/week7_ci_ingestion_smoke_test.py
python -m pytest tests/data_tests/ -q
python scripts/week7_verify_db_load_result.py --expected-structured-records 11524 --verify-handoffs
python scripts/week7_backend_stub_smoke_test.py
python scripts/week7_shared_integration_smoke_test.py
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
```

Owner commands after merge:

```powershell
python week7/database/scripts/ci_database_smoke_test.py
python ai/rag/scripts/week7_rag_ci_smoke_test.py
python scripts/week7_prediction_ci_smoke_test.py
python scripts/week7_ui_ci_smoke_test.py
```

## Full integration job after merge

The final integration job should:

1. start Phat's pgvector service;
2. run the fixed schema and views from an empty volume;
3. load Duy smoke data;
4. run Lap chunk insertion and retrieval;
5. run Tuong prediction-log insertion;
6. validate Phi/Hung fixtures and backend envelopes;
7. fail on any ID, status, vector-dimension or required-field mismatch.

Until these owner artifacts are merged, `scripts/week7_shared_repo_readiness_check.py`
is the source of truth for what is still missing.

Duy's local current-run database proof can be reproduced independently:

```powershell
python scripts/week7_duy_phat_docker_db_integration_test.py --mode smoke-then-full
```

The readiness checker has two distinct gates:

```powershell
python scripts/week7_shared_repo_readiness_check.py --strict
python scripts/week7_shared_repo_readiness_check.py --strict --strict-execution
```

`--strict` checks that the shared-repository artifacts exist. The
`--strict-execution` variant also fails when a recorded owner audit is
blocked. The Phi/Hung execution audit is stored in
`outputs/hung_handoff/hung_week7_mapping_summary.json`; passing UI tests alone
does not prove that the copied fixtures preserve the Duy/Phat database IDs.

For Lap specifically, structural readiness and execution readiness are
separate. Run:

```powershell
python scripts/week7_build_lap_mapping_summary.py --run-lap-tests
```

The shared workflow must not mark the RAG integration complete while
`live_pgvector_proof_passed` is false. A pending Lap output is allowed only in
fixture/contract mode and must be reported as pending in the CI summary.

For Tuong, structural readiness and execution readiness are also separate:

```powershell
python scripts/week7_build_tuong_mapping_summary.py --run-tuong-checks
```

The prediction integration must remain pending while any of these are false:

```text
tuong_output_contract_passed
prediction_ci_proof_passed
database_insert_proof_passed
```

A four-state sample fixture, eight partial results, or a one-row DB dry-run is
not a substitute for the current 20-payload prediction/log/review workflow.
