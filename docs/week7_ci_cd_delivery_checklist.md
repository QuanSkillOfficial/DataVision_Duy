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
- [ ] Remove the unused `torch` dependency and return a clean unit/CI result.
- [ ] Real chunk insertion, retrieval and RAG-log proof are returned.

## Tuong

- [x] Duy has supplied 20 input payloads.
- [x] Prediction CI smoke-test entry point is present in Tuong's audited repository.
- [ ] Prediction tests and CI smoke test pass in a clean Python 3.11 environment.
- [ ] Tuong refreshes the input copy and results for all 20 current Duy payloads.
- [ ] Normalized prediction logs are inserted into Phat's database.
- [ ] Review queue output is returned.

## Phi/Hung

- [x] Existing service-client architecture is available.
- [x] Fixture validator, backend contract test and UI smoke test are present.
- [x] UI smoke test passes in the audited checkout.
- [x] DataFlow RAG fixture and Week 7 screenshots are present.
- [x] Duy fixture, Phat dashboard fixture and UI code/docs pass current contracts.
- [ ] Refresh Tuong batch/review fixtures so all applicable `document_db_id` values are non-null.
- [ ] Install the pinned UI requirements and rerun the full Phi/Hung unit suite.

## Shared project

- [x] `.env.example`.
- [x] `docker-compose.db.yml`.
- [x] First `docker-compose.yml` draft.
- [x] Backend contract stub.
- [x] Local Compose contract checker.
- [x] Shared repo readiness report.
- [x] CI workflow draft with conditional owner jobs.
- [x] Deployment runbook draft.
- [ ] Full runtime integration after owner artifacts are merged.
- [ ] Physical shared-repo merge and deployment runbook sign-off by the team.
