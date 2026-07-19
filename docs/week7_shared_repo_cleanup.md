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
- ignored runtime ingestion run logs and manifests that duplicated the tracked
  history; only the four tracked baseline runs and manifests remain;
- duplicate Week 7 builders in favor of the `scripts/week7_*` entry points;
- production claims from the backend stub: it is explicitly contract-only;
- hidden database assumptions: IDs remain null until a real Phat load confirms
  them, or until Phat's committed Week 7 database evidence is validated by the
  identity-bridge builder.

The run-log cleanup preserved every record in `logs/ingestion_runs.jsonl` and
the tracked baseline evidence. Two historical failure messages were sanitized
from machine-specific absolute paths to project-relative paths; no run was
deleted. The latest CSV/Excel/API/PDF run records are preserved in the tracked
JSONL history and in the generated Week 7 handoffs.
The loader and handoff builders combine the tracked JSONL history with any
local run files, deduplicate by `run_id`, and select the newest successful run
per source. This keeps a clean Git checkout reproducible without tracking every
generated run file.

No Week 6 contract or evidence file was deleted because those files document a
previous milestone. New Week 7 outputs use explicit names and do not overwrite
the Week 6 handoff contracts.

The retained Week 1 repository is declared in root `.gitmodules`. It is
historical-only and is not required by any Week 7 command.

## Duplicate-file audit

A content-hash scan found no duplicate implementation in the active Week 7
surface. The remaining byte-identical files are intentional evidence:

- Week 2 raw/staging/clean copies demonstrate each pipeline layer even when a
  particular transformation does not change bytes;
- Week 6 log/output copies preserve the contract paths consumed during that
  milestone;
- current Week 7 consumers use only the canonical `week7_*` handoff paths
  listed in `integration/shared_repo_manifest.json`.

These historical files were not deleted because doing so would break prior
milestone validation without reducing the active Week 7 runtime. Runtime
caches, temporary workspaces and redundant current implementation files remain
removed or ignored.

## Cleanup required in owner repositories

The following cleanup cannot be safely performed from this read-only workspace
and is assigned to the owners:

| Repository | Remove/archive | Keep as the official path |
| --- | --- | --- |
| Phat | tracked `week6/database/__pycache__/*.pyc`, `week7/database/__pycache__/*.pyc`, `week7/scripts/__pycache__/*.pyc`, `week6/database/insert_prediction_logs_to_postgres_PATCHED.py`, and stale docs that reference it | `week7/database/schema/`, `week7/database/scripts/`, `week7/database/validation/`, and one official prediction-log loader |
| Lap | unused `torch` import, old notebook/evaluation artifacts, duplicate SQL, stale Week 6 handoff files | `ai/rag/`, `ai/ai_tests/`, `outputs/rag/`, and `outputs/ui_fixtures/` |
| Tuong | `__pycache__/` directories, missing root `.gitignore`, legacy `scripts/test_prediction_on_duy_outputs.py`, stale single-payload data, old 0.60 contracts/model docs, historical Week 1-3 assets, root manager PDF, and synthetic UI fixtures | `ai/prediction/`, `tests/ai_tests/`, official Week 7 runner/CI/DB scripts, current 20-result output, DB payloads, soft RAG metadata, and real-lineage UI fixtures |
| Phi/Hung | root pre-Week 7 fixtures, historical Week 1-6 docs/folders, and old screenshots | `demo/services/`, `demo/fixtures/week7/`, `demo/services/fixture_validator.py`, current screenshots, and UI smoke test |

After those repositories are merged, run the shared readiness checker in strict
mode and remove any paths not referenced by `integration/shared_repo_manifest.json`.

The Phat cleanup is intentionally recorded here rather than performed from the
Duy workspace. Phat should commit that deletion so ownership and review history
remain clear.

## Lap audit result

The Duy-to-Lap audit is generated by:

```text
scripts/week7_build_lap_mapping_summary.py
```

It writes:

```text
outputs/lap_handoff/lap_week7_mapping_summary.json
logs/lap_handoff/lap_week7_external_proof.json
docs/week7_duy_lap_mapping_result.md
```

The audit found that the Duy handoff is valid, but Lap's current
`week7_chunk_insert_summary.json` and `week7_pgvector_query_result.json` are
still `pending_db_connection`. It also found an unused `torch` import that
prevents clean test collection. These are Lap-owner fixes; they are not hidden
inside the Duy repo.

## Tuong audit result

The Duy-to-Tuong audit is generated by:

```text
scripts/week7_build_tuong_mapping_summary.py
```

It writes:

```text
outputs/tuong_handoff/tuong_week7_mapping_summary.json
logs/tuong_handoff/tuong_week7_external_proof.json
docs/week7_duy_tuong_mapping_result.md
```

The audit confirms Duy's 20-item payload contract. Tuong's current checkout
still contains a stale 10-item input copy, eight results, one DB log payload,
synthetic UI IDs, and no real prediction-log insert result. It also contains
active 0.60 documentation alongside the Week 7 0.80 staging policy. These are
Tuong-owner changes and must be committed in the Tuong repository.

## Phi/Hung audit result

The Duy-to-Phi/Hung audit is generated by:

```text
scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
```

It writes:

```text
outputs/hung_handoff/hung_week7_mapping_summary.json
logs/hung_handoff/hung_week7_external_proof.json
docs/week7_duy_phi_hung_mapping_result.md
```

The current sibling checkout passes the Duy, Phat, and Lap fixture gates. Its
UI structure, code/document contracts, screenshot set, and UI smoke test also
pass. The remaining fixture blocker is Tuong lineage: four batch items and
four review-queue items still have a null `document_db_id`. The full Phi/Hung
test command cannot collect tests in the audited environment because the
pinned UI dependencies, including `streamlit`, are not installed there.

These are owner-repository changes and are not silently normalized in Duy's
repo. Phi/Hung must refresh Tuong fixtures, install the pinned requirements,
rerun the full tests, and commit the result. The mapping remains
`blocked_on_phi_hung_refresh` until the audit reports:

```text
tuong_fixture_contract_passed=true
real_lineage_passed=true
hung_unit_tests_passed=true
ui_smoke_passed=true
```

The root legacy fixtures and historical screenshots should be archived only
after the Week 7 fixture validator confirms that no active test or page imports
them. Keep `demo/fixtures/week7/` and
`screenshots/week7_staging_ready_ui/` as the active paths.
