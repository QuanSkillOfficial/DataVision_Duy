# Message to Satyam — Week 8 Deliverables and Deadlines

Hi Satyam,

As the CI/CD lead, I have consolidated the Week 7 integration dependencies and
prepared the updated delivery plan for the upcoming week, 27-31 July.

The software dependency layer is now ready:

- Separate CI dependency manifests are defined for Data Engineering, Database,
  RAG, Prediction and UI.
- Every CI installation now runs `pip check`.
- Duy Data Engineering: 59 tests passed.
- Lap RAG: 59 tests passed and the FakeEmbedder smoke test passed 10/10 without
  downloading torch or an embedding model.
- Tuong Prediction: 116 tests passed and the prediction CI smoke test passed.
- Tuong's output was refreshed from Duy's current 20 payloads, producing
  20 prediction results, 20 prediction-log payloads and 15 real review items.
- Phi/Hung UI: 63 fixture-mode tests passed, the UI smoke test passed, and all
  15 UI-to-backend contract tests passed separately.
- The backend contract stub passed all 13 smoke checks.
- Both Docker Compose files pass static configuration validation.

The remaining dependencies are now limited to shared infrastructure and
physical owner-module merge gates:

1. Confirm the canonical shared GitHub repository and merge owner modules by
   Monday, 27 July.
2. Provide a running Docker daemon or staging host by Tuesday morning.
3. Phat completes the from-zero PostgreSQL/pgvector runtime proof and Duy smoke
   load by Tuesday EOD.
4. Lap returns live pgvector chunk/retrieval/RAG-log proof by Wednesday 15:00.
5. Tuong and Phat insert the current prediction logs and return real review
   queue IDs by Wednesday EOD.
6. Duy and Phi/Hung complete backend-mode integration and the first staging
   deployment by Thursday EOD.
7. The team submits the staging acceptance report, runbook, rollback notes and
   Week 8 MVP demo by Friday, 31 July.

Updated Week 8 deliverables:

- 27 Jul: canonical shared repo, owner PR merge and consolidated CI workflow.
- 28 Jul: PostgreSQL + pgvector from-zero setup with Duy smoke data.
- 29 Jul: live RAG retrieval and prediction-log/review-queue DB integration.
- 30 Jul: full service-layer/UI integration and first Docker staging deployment.
- 31 Jul: staging acceptance evidence, deployment runbook and MVP demo.

The Week 8 success criterion is no longer that each module runs independently.
The success criterion is that a clean shared-repo checkout passes CI and the
DataFlow pipeline runs on staging without depending on individual laptops.

Current external blocker: the Docker daemon/staging host is not running in the
local audit environment, so the final DB-backed RAG and prediction-log proofs
remain scheduled for the infrastructure window above. No unresolved Python
package dependency remains.

Regards,
Duy
