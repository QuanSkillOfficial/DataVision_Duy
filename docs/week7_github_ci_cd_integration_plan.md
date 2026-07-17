# Week 7 GitHub CI/CD Integration Plan

Duy and Phi/Hung co-lead the shared workflow. The current draft is in
`.github/workflows/ci.yml`.

## Jobs in the draft

| Job | Current state | Owner |
| --- | --- | --- |
| `data-engineering-ci` | Active and passing in Duy's repository | Duy |
| `backend-contract-ci` | Active when the stub dependencies are installed | Duy/shared |
| `shared-readiness-ci` | Active; reports missing external owner artifacts without hiding them | Duy |
| `integration-contract-ci` | Active; validates Duy outputs and both Compose files | Duy |
| `database-ci` | Conditional until `week7/database/` is merged | Phat |
| `rag-ci` | Conditional until the shared RAG smoke script is merged | Lap |
| `prediction-ci` | Conditional until the prediction smoke script is merged | Tuong |
| `ui-ci` | Conditional until the UI smoke script and fixtures are merged | Phi/Hung |

The conditional jobs are deliberate. A standalone Duy repository must not
pretend that another owner's files exist. After the five repositories are
merged, remove the conditional guard or keep it only as a path-based monorepo
optimization.

## Commands

```powershell
python scripts/week7_ci_ingestion_smoke_test.py
python -m pytest tests/data_tests/ -q
python scripts/week7_backend_stub_smoke_test.py
python scripts/week7_shared_integration_smoke_test.py
```

Owner commands after merge:

```powershell
python week7/database/ci_database_smoke_test.py
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
