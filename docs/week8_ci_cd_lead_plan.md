# Week 8 CI/CD Lead Delivery Plan

**Owner:** Nguyen Minh Duy
**Co-lead:** Phi/Hung
**Delivery window:** 27-31 July 2026
**Goal:** turn the Week 7 local integration baseline into the first reproducible staging MVP.

## Final status on 4 August 2026

The implementation gates in this plan are now complete in the canonical local
staging environment. All owner modules are merged; Docker daemon access is
available; PostgreSQL/pgvector, live RAG retrieval, prediction-log insertion,
backend-mode UI, and the 15-check Compose acceptance have passed. The GitHub
workflow is prepared to reproduce the same empty-volume proof after these
changes are pushed. See `docs/week8_acceptance_report.md` for evidence and
`docs/week8_staging_runbook.md` for operations and rollback.

## Verified baseline on 26 July

| Gate | Result |
| --- | --- |
| Shared Python dependency resolution | Passed (`pip check`) |
| Duy data tests | 59 passed |
| Lap RAG tests | 59 passed |
| Lap FakeEmbedder smoke | 10/10 passed |
| Tuong prediction tests | 116 passed |
| Tuong prediction smoke | Passed |
| Current Duy payload refresh | 20 results, 20 log payloads |
| Current prediction distribution | 15 `needs_review`, 2 `waiting_for_source`, 3 `failed` |
| Phi/Hung fixture-mode tests | 63 passed, 15 backend-only tests skipped by design |
| Phi/Hung UI smoke | Passed |
| Backend stub smoke | 13/13 checks passed |
| Phi/Hung backend-mode contract tests | 15/15 passed |
| Docker Compose static validation | Both Compose files passed |

## Completed dependency work

1. Added separate CI dependency manifests:
   - `requirements-ci.txt`
   - `week7/database/requirements-ci.txt`
   - `ai/rag/requirements-ci.txt`
   - `ai/prediction/requirements-ci.txt`
   - `demo/requirements-ci.txt`
2. Changed owner jobs to install only their own dependency set.
3. Added `pip check` as a dependency gate.
4. Removed the unused direct `torch` dependency from the RAG CI path.
5. Removed scikit-learn from the RAG fake/search CI implementation.
6. Refreshed Tuong outputs from Duy's current 20 payloads.
7. Kept synthetic accepted-state UI coverage separate from the real prediction results.
8. Synchronized Tuong batch/review fixtures into Phi/Hung's UI.
9. Aligned the backend stub with the UI service-client contract.

## Remaining execution dependencies

These are infrastructure/merge gates, not unresolved Python packages:

1. **Canonical shared GitHub repository**
   - Owner: Duy + Phi/Hung
   - Required by: Monday 27 July, 12:00 ICT
   - Gate: owner modules merged through PRs; no nested repositories.
2. **Docker daemon or staging host**
   - Owner: CI/CD lead / platform access owner
   - Required by: Tuesday 28 July, 10:00 ICT
   - Gate: PostgreSQL + pgvector is healthy from an empty volume.
3. **Phat DB runtime proof**
   - Owner: Phat
   - Required by: Tuesday 28 July, EOD
   - Gate: schema/views applied; Duy smoke load queried back.
4. **Lap live pgvector proof**
   - Owner: Lap
   - Required by: Wednesday 29 July, 15:00 ICT
   - Gate: real chunk insert, top-k retrieval, citations and RAG-log insert.
5. **Tuong prediction-log DB proof**
   - Owner: Tuong + Phat
   - Required by: Wednesday 29 July, EOD
   - Gate: 20 logs inserted or explicitly rejected by validation; review queue IDs returned.
6. **Staging access**
   - Owner: project/platform owner
   - Required by: Thursday 30 July, 10:00 ICT
   - Gate: server credentials/secrets are available outside Git.

## Deliverables and deadlines

| Date | Deliverable | Owner | Acceptance gate |
| --- | --- | --- | --- |
| Mon 27 Jul | Canonical shared repo and clean owner PR merge | Duy + Phi/Hung | CI detects all five modules |
| Mon 27 Jul | Consolidated CI workflow and dependency manifests | Duy | All non-DB jobs green |
| Tue 28 Jul | DB from zero with pgvector, schema and Duy smoke data | Phat + Duy | DB smoke and query-back pass |
| Wed 29 Jul | Live RAG and prediction-log DB integration | Lap + Tuong + Phat | pgvector/RAG-log/prediction-log proofs returned |
| Thu 30 Jul | Full service-layer and UI backend-mode integration | Duy + Phi/Hung | Backend contract and end-to-end smoke pass |
| Thu 30 Jul | First Docker staging deployment | Duy + Phi/Hung | DB/backend/UI health checks pass |
| Fri 31 Jul | Staging acceptance report, runbook and rollback notes | Duy | Reproducible from a clean checkout |
| Fri 31 Jul | Week 8 staging MVP demo | Whole team | DataFlow flow works without owner laptops |

## Week 8 completion rule

Week 8 is complete only when the shared repository is green in CI and the
staging flow demonstrates:

```text
DataFlow ingestion
-> PostgreSQL/pgvector
-> RAG retrieval and citations
-> prediction and review queue
-> backend service contract
-> Phi/Hung UI
```

Fixture mode remains the safe fallback, but staging acceptance requires the
DB-backed execution proofs to be labelled separately and truthfully.
