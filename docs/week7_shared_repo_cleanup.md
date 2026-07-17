# Week 7 Shared Repository Cleanup

## Active paths

The active Week 7 implementation is limited to:

```text
data_engineering/
scripts/week7_*.py
scripts/load_ingestion_outputs_to_postgres.py
tests/data_tests/
tests/fixtures/data/
outputs/rag_handoff/week7_*
outputs/prediction_payloads/tuong_week7_*
outputs/ui_fixtures/duy_week7_*
backend_stub/
deployment/
integration/
docker-compose*.yml
.github/workflows/ci.yml
```

These paths are the ones referenced by the current runbook and CI draft.

## Retained historical paths

The Week 1 and Week 2 folders are retained because they contain manager
deliverables, original sample inputs, and the legacy validation command. They
are not active import paths for Week 7:

```text
week1_ingestion_foundation/
week2/notebooks/
week2/scripts/ingestion/
week2/docs/
```

Deleting them would make historical validation and provenance harder to
reproduce. They should be moved to an archive branch only after the team lead
confirms that the old Week 1/2 validation is no longer required.

## Removed from the active runtime surface

- developer-specific absolute paths from new Week 7 contracts;
- generated temporary CI workspaces after each smoke run;
- Python and pytest caches through `.gitignore`;
- duplicate Week 7 builders in favor of the `scripts/week7_*` entry points;
- production claims from the backend stub: it is explicitly contract-only;
- hidden database assumptions: IDs remain null until a real Phat load confirms
  them.

No Week 6 contract or evidence file was deleted because those files document a
previous milestone. New Week 7 outputs use explicit names and do not overwrite
the Week 6 handoff contracts.

## Cleanup required in owner repositories

The following cleanup cannot be safely performed from this read-only workspace
and is assigned to the owners:

| Repository | Remove/archive | Keep as the official path |
| --- | --- | --- |
| Phat | `insert_prediction_logs_to_postgres_PATCHED.py` and duplicate active SQL copies | one official loader, `week7/database/` setup and validation |
| Lap | nested `ai/rag/ai/`, old notebooks without evidence, duplicate SQL | `ai/rag/` and `ai/ai_tests/` |
| Tuong | old Week 5 evaluation outputs and hard-filter metadata | Week 7 safety policy, CI script and DB payloads |
| Phi/Hung | old `demo/mock_backend/`, vendor RAG fixture and stale screenshots | `demo/services/`, `demo/fixtures/week7/` and UI smoke test |

After those repositories are merged, run the shared readiness checker in strict
mode and remove any paths not referenced by `integration/shared_repo_manifest.json`.
