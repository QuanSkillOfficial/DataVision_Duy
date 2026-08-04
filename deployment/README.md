# DataVision Week 8 Staging Deployment

This folder contains the reproducible Week 8 deployment boundary for the
canonical shared repository.

The default `docker-compose.yml` starts four stages in dependency order:

```text
PostgreSQL 16 + pgvector
-> one-shot integration seed
-> FastAPI staging backend
-> Streamlit UI in backend mode
```

Key files:

| File | Purpose |
| --- | --- |
| `database/init/00_extensions.sql` | Enables pgvector on an empty database |
| `database/init/10_phat_schema_v4_fixed.sql` | Applies the pinned writer contract |
| `database/init/20_phat_schema_and_views.sql` | Applies Phat's full schema and 12 analytics views |
| `Dockerfile.integration` | Loads Duy data, Lap chunks, and Tuong prediction logs |
| `../backend_stub/Dockerfile` | Runs the DB-backed FastAPI staging service |
| `../demo/Dockerfile` | Runs Phi/Hung Streamlit UI in backend mode |
| `../scripts/week8_staging_smoke_test.py` | Executes the 15-check acceptance test |

Start from a clean checkout with the commands in
`docs/week8_staging_runbook.md`. The compact machine-readable proof is written
to `outputs/integration/week8_staging_acceptance.json`.

The default Week 8 embedding mode is deterministic hashing with 384 dimensions.
It proves the pgvector contract without downloading a model in CI. It is a
staging plumbing implementation, not the production semantic-quality model.
