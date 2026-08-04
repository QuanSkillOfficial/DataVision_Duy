# Week 8 Staging Acceptance Report

**Execution date:** 4 August 2026
**Owner:** Duy, CI/CD lead
**Result:** LOCAL/CI PASSED; CLOUD PROMOTION PENDING HOST CREDENTIALS

## Acceptance result

The complete DataVision pipeline was built from the canonical repository and
executed on local and ephemeral-CI Docker Compose staging stacks. All 15
end-to-end acceptance checks passed in those environments. Cloud staging is a
separate acceptance gate and must not be reported as passed until its URL and
exact release SHA are verified by `Deploy staging`.

| Layer | Verified evidence | Result |
| --- | --- | --- |
| Duy ingestion | 4 sources, 11,560 valid records, 36 DataFlow PDF pages | Passed |
| Phat database | PostgreSQL reachable, pgvector enabled, 10 required tables and 12 views | Passed |
| Lap RAG | 293 chunks, vector(384), live top-5 retrieval, page/chunk citations, RAG log | Passed |
| Tuong prediction | Live prediction returned, prediction log inserted, review queue queryable | Passed |
| Backend | DB-backed health, dashboard, RAG, prediction, suggestions, and report routes | Passed |
| Phi/Hung UI | Streamlit healthy in backend mode; 15 backend contract tests passed | Passed |

The acceptance checks were:

```text
backend_healthy, database_reachable, pgvector_enabled,
duy_sources_available, duy_pages_available,
lap_chunks_available, lap_retrieval_context, lap_citations,
lap_pgvector_backend, tuong_prediction_executed,
tuong_prediction_logged, review_queue_queryable,
ui_healthy, suggestions_contract, report_contract
```

## Test summary

| Test group | Result |
| --- | --- |
| Combined scoped test suites | 300 passed, 15 skipped |
| Duy data engineering | 59 passed |
| Lap RAG owner suite | 61 passed; CI smoke 10/10 |
| Tuong prediction owner suite | 116 passed; CI smoke passed |
| Backend route smoke | 13/13 passed |
| Phi/Hung UI suite | 64 passed, 15 skipped |
| UI-to-backend contract | 15 passed |
| Phat live database smoke | 10/10 passed |
| Week 8 Docker acceptance | 15/15 passed |
| Dependency consistency | `pip check` passed |

Machine-readable evidence:

- `outputs/integration/week8_staging_acceptance.json`
- `outputs/integration/week8_pgvector_runtime_result.json`
- `outputs/integration/week7_shared_repo_readiness.json`

## CI gates

The consolidated workflow now requires separate Data Engineering, Database,
RAG, Prediction, UI, backend contract, and shared integration jobs. After those
jobs pass, `week8-staging-compose-ci` creates an empty-volume stack, runs the
same 15-check acceptance script, removes its isolated resources, and uploads
the JSON proof as a GitHub Actions artifact.

## Scope and limitations

Week 8 proves integration and reproducibility. The 384-dimensional hash
embedder is deliberately deterministic and download-free for CI/staging; it
does not claim production semantic retrieval quality. The RAG service currently
returns retrieved evidence and citations rather than a generated LLM answer.
Authentication, TLS, managed secrets, persistent user feedback, observability,
and disaster-recovery automation are Week 9/production-readiness work.

## Decision

The Week 8 staging MVP is accepted for local demonstration and GitHub CI
execution. The repository includes exact-SHA GHCR publishing, SSH deployment,
release verification, evidence upload, and application-image rollback. Week 8
closes fully only after those workflows run against the supplied cloud host and
the cloud acceptance artifact reports 15/15 for the deployed SHA.
