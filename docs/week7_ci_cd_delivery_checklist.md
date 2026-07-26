# Week 7 CI/CD Delivery Checklist

## Duy

- [x] Shared data-engineering structure.
- [x] Local deterministic fixtures.
- [x] Ingestion CI smoke test.
- [x] Dry-run, smoke-write and full-write loader modes.
- [x] DB-enriched RAG, prediction and UI handoffs.
- [x] Data-engineering CI job draft.
- [x] Current-run Docker DB integration: smoke 100 and full 11,524.
- [x] Exact source/document ID and query-back verification.
- [x] All 12 Duy tasks and all 15 final deliverables from `duy_week7.pdf`.
- [x] 59 data-engineering tests pass.

## Phat

- [x] Fixed schema contract runs from zero in Duy's isolated integration test.
- [x] Docker PostgreSQL + pgvector setup is validated.
- [x] Duy smoke/full counts are queried back.
- [x] Historical Week 7 dashboard view samples are exported.
- [ ] Phat refreshes the shared DB/views from Duy's current run UUIDs if needed.

## Lap

- [x] RAG smoke-test files are present in the audited repository snapshot.
- [x] Duy's 36-page DB-enriched handoff passes Lap's input contract.
- [x] Remove the unused direct `torch` dependency.
- [x] Add a lightweight `ai/rag/requirements-ci.txt`.
- [x] RAG unit suite passes: 59 tests.
- [x] RAG FakeEmbedder smoke passes: 10/10 checks without model download.
- [ ] Real chunk insertion, retrieval and RAG-log proof are returned.

## Tuong

- [x] Duy has supplied 20 input payloads.
- [x] Prediction CI smoke-test entry point is present in Tuong's audited repository.
- [x] Add `ai/prediction/requirements-ci.txt` with scikit-learn 1.7.2.
- [x] Prediction tests pass in a clean isolated environment: 116 tests.
- [x] Prediction CI smoke test passes.
- [x] Tuong refreshes results and log payloads for all 20 current Duy payloads.
- [x] UI batch and review fixtures are refreshed from the current real batch.
- [ ] Normalized prediction logs are inserted into Phat's database.
- [x] Review queue output is returned with 15 real `needs_review` items.
- [ ] Replace pending `prediction_log_id` values after the database insert.

## Phi/Hung

- [x] Existing service-client architecture is available.
- [x] Fixture validator, backend contract test and UI smoke test are present.
- [x] UI smoke test passes in the audited checkout.
- [x] DataFlow RAG fixture and Week 7 screenshots are present.
- [x] Duy fixture, Phat dashboard fixture and UI code/docs pass current contracts.
- [x] Refresh Tuong batch/review fixtures from the current 20-payload run.
- [x] Preserve the failed missing-lineage case instead of dropping it.
- [x] Add `demo/requirements-ci.txt`.
- [x] Fixture-mode suite passes: 63 tests; 15 backend-only tests are intentionally skipped.
- [x] UI smoke test passes.
- [x] Backend contract suite passes separately: 15/15 tests.
- [ ] Replace pending prediction-log IDs after Tuong inserts logs into Phat's DB.

## Shared project

- [x] `.env.example`.
- [x] `docker-compose.db.yml`.
- [x] First `docker-compose.yml` draft.
- [x] Backend contract stub.
- [x] Local Compose contract checker.
- [x] Shared repo readiness report.
- [x] CI workflow draft with conditional owner jobs.
- [x] Separate CI dependency manifests for Data, DB, RAG, Prediction and UI.
- [x] Every CI install runs `python -m pip check`.
- [x] Backend stub and UI client contracts are aligned and tested.
- [x] Both Compose files pass `docker compose config --quiet`.
- [x] Deployment runbook draft.
- [ ] Full runtime integration after owner artifacts are merged.
- [ ] Physical shared-repo merge and deployment runbook sign-off by the team.
- [ ] Start a Docker daemon/staging host for DB-backed RAG and prediction-log proof.
