# Week 8 Team Handoff

## Current state

The five owner modules are merged into the canonical repository and use one
Compose/service contract. Local staging is no longer assembled from nested
owner repositories or manually connected laptops.

| Owner | Canonical path | Week 8 handoff | Acceptance owner |
| --- | --- | --- | --- |
| Duy | `data_engineering/`, `scripts/` | Ingestion outputs, DB loader, staging seed, CI coordination | Source/run/page counts and clean checkout proof |
| Phat | `week7/database/`, `deployment/database/init/` | Schema, pgvector, analytics views, DB smoke | Empty-volume setup and validation queries |
| Lap | `ai/rag/` | Chunking, 384D embedding, pgvector retrieval, citations | Live top-k result and RAG log |
| Tuong | `ai/prediction/`, `tests/ai_tests/` | Prediction service, batch results, prediction-log payload | DB IDs, status/confidence, review queue |
| Phi/Hung | `demo/`, root UI tests | Fixture/backend service client and Streamlit pages | Backend contract tests and UI health |

## Required team workflow

1. Branch from the latest canonical main branch.
2. Keep contracts backward compatible or update producer, consumer, fixtures,
   tests, and documentation in the same pull request.
3. Run the owner test suite and `pip check` before opening the pull request.
4. Require all GitHub Actions jobs, including the Week 8 Compose acceptance,
   before merge.
5. Deploy the resulting Git SHA to staging and attach the generated acceptance
   JSON to the release/demo record.

## Owner commands

```powershell
# Duy
pytest tests/data_tests -q

# Phat (requires the local Compose database)
python week7/database/scripts/ci_database_smoke_test.py

# Lap
pytest ai/ai_tests -q
python ai/rag/scripts/week7_rag_ci_smoke_test.py

# Tuong
pytest tests/ai_tests -q
python scripts/week7_prediction_ci_smoke_test.py

# Phi/Hung
pytest tests/test_*.py -q
python scripts/week7_ui_ci_smoke_test.py

# Whole platform
python scripts/week8_staging_smoke_test.py --start --fresh --project-name datavision-week8-local
```

## Definition of done

A module is not complete when it only runs alone. Its output must be accepted
by the next module, its owner CI job must pass, and the clean-volume Week 8
Compose acceptance must remain green.

## Immediate Week 9 queue

- Semantic RAG model selection and retrieval evaluation: Lap.
- Feedback persistence and prediction review lifecycle: Tuong + Phat.
- Authentication, secrets, TLS, logs/metrics/alerts, backup drill: Duy/CI-CD.
- Browser-level staging regression suite: Phi/Hung.
- Final demo dataset freeze and release tag: whole team.
