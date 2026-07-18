# Week 7 Final Project Review

Review date: 2026-07-19  
Owner: Nguyen Minh Duy  
Scope: Duy ingestion repository and the cross-repository Week 7 handoff boundary

## Review Result

The Duy repository is artifact-ready and CI-contract-ready. The local data
pipeline, handoff builders, database dry-run plan, shared-repository checks,
and validation suite pass from the repository root.

The repository does not claim that Docker runtime or every sibling module has
already completed live execution. Those states are recorded explicitly in the
readiness report and the owner mapping reports.

## Completed In This Review

### Reproducible database identity resolution

- `source_id` remains the integer `sources.id`; it is never populated with a
  run UUID.
- `document_external_id` remains the stable string document key.
- `document_db_id` remains the integer `documents.id`.
- `ingestion_run_id` remains Duy's UUID.
- A real local DB result is authoritative when available.
- If the default local result is still the tracked
  `pending_external_database` placeholder, builders use
  `logs/db_load_results/phat_week7_external_database_proof.json` for the stable
  IDs and preserve `current_duy_runs_loaded=false`.

This behavior is implemented in:

```text
data_engineering/pipelines/handoff_context.py
```

It is covered by:

```text
tests/data_tests/test_week7_ci_pipeline.py
```

### Clean-clone handoff generation

The latest successful run discovery combines:

```text
logs/ingestion_runs.jsonl
logs/runs/*.json
```

The tracked JSONL history is sufficient when ignored runtime run files are not
present. The Week 6 UI fixture builder now uses the same discovery helper, so
historical regeneration does not depend on local-only run files.

### Week 7 handoffs

The default commands regenerate stable, DB-enriched outputs:

```text
python scripts/week7_build_rag_handoff_package.py
python scripts/week7_build_prediction_payloads.py
python scripts/week7_build_ui_fixtures.py
```

Canonical outputs:

```text
outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
outputs/rag_handoff/week7_rag_handoff_manifest.json
outputs/prediction_payloads/tuong_week7_prediction_payloads.json
outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json
outputs/prediction_payloads/week7/*.json
outputs/ui_fixtures/duy_week7_database_enriched_summary.json
```

The current stable identity bridge is:

```text
dataflow_technical_report_pdf -> source_id 4
doc_dataflow_technical_report -> document_db_id 1
```

The current Duy run UUIDs are retained in the handoffs, while the Phat proof
reports whether those UUIDs have been reloaded into the database.

## Cleanup Completed

Removed from the working tree:

- Python `__pycache__` directories.
- Pytest runtime caches.
- Ignored runtime run and manifest files that duplicated the tracked
  baseline/history evidence.

Kept intentionally:

- `week1_ingestion_foundation/` and `week2/` historical inputs and validation
  assets, because the historical validators and provenance documents use them.
- The four tracked baseline run logs and manifests required by the Week 5
  validator.
- The Week 6 individual payloads and fixtures, because they remain historical
  compatibility artifacts and are referenced by Week 6 validation.
- The Week 7 mapping summaries and external proof files, because they are the
  cross-repository acceptance evidence.

No tracked cache, `.pyc`, `*_PATCHED.py`, or duplicate active database/RAG/
prediction implementation remains in this repository.

## Verification

Commands run from the repository root:

```text
python -m pytest tests/data_tests/ -q -p no:cacheprovider
python scripts/validate_week5.py
python scripts/validate_week6.py
python scripts/validate_week7.py
python week2/scripts/validate_project.py
python scripts/week7_ci_ingestion_smoke_test.py
python scripts/week7_data_pipeline_smoke_test.py
python scripts/week7_shared_integration_smoke_test.py
python scripts/week7_local_docker_integration_smoke_test.py
git diff --check
```

Observed results:

| Check | Result |
| --- | --- |
| Data-engineering tests | 52 passed |
| Week 5 validation | Passed |
| Week 6 validation | Passed |
| Week 7 validation | Passed; 64 required files |
| Week 2 validation | Passed |
| CI ingestion smoke | Passed |
| Data pipeline smoke | Passed: 4 sources, 4 runs, 4 logs, 1 document, 36 pages, 100 smoke records |
| Shared integration contract | Passed |
| Compose syntax contract | Passed for both Compose files |
| Local Docker integration contract | Passed; runtime not started |
| Docker runtime | Not executed because Docker Desktop/daemon was unavailable |

## Remaining Cross-Team Blockers

These are recorded blockers, not hidden failures in Duy's ingestion code:

| Owner | Remaining proof |
| --- | --- |
| Lap | Live `document_chunks` insertion, pgvector retrieval, and RAG query-log proof |
| Tuong | Refresh from all 20 Duy payloads, produce 20 normalized results/log payloads, and show DB insertion |
| Phi/Hung | Refresh copied fixtures with non-null canonical IDs, align the 0.80 staging policy, and rerun UI lineage gates |
| Phat/Duy | Reload the newest Duy run UUIDs when PostgreSQL/Docker is available |

Machine-readable status:

```text
outputs/integration/week7_shared_repo_readiness.json
```

Expected current state:

```text
status=ready
execution_status=blocked
```

The execution gate should be rerun after the owner repositories provide their
live proofs:

```text
python scripts/week7_shared_repo_readiness_check.py --strict --strict-execution
```
