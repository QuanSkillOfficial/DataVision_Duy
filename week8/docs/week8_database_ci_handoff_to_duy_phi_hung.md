# Week 8 Database CI Handoff — For Duy and Phi/Hung

**Owner:** Phat — PostgreSQL, pgvector, Schema & Data Operations
**Related tasks:** DV-PHAT-01 → DV-PHAT-07
**Scope:** What changed in the database layer since Week 7, and exactly what
Duy (CI/CD + deployment) and Phi/Hung (dashboard/UI) need to consume it.

---

## 1. What changed since Week 7

Week 7 shipped a working database that ran from a single monolithic setup
script with a hard-coded password. Week 8 replaces that with a safer,
versioned, idempotent pipeline:

| Area | Week 7 | Week 8 |
|---|---|---|
| Schema setup | One `setup_database_v3.sql` blob | Versioned migrations in `week8/database/migrations/*.sql`, tracked in `schema_migrations` table |
| Credentials | Hard-coded `datavision123` in code/compose | Read from `DB_PASSWORD` env var; no default; `.env.example` provided |
| Backup | None | Automated timestamped `pg_dump` before every migrate/seed, with checksum verification |
| Restore | None | Tested, scripted restore procedure with row-count verification |
| Seed loading | Reran full inserts each time | Idempotent (`ON CONFLICT` + unique constraints) — safe to rerun |
| Tests | Ad hoc | Marked `unit` / `integration` / `live_db`, live tests opt-in only |

None of this changes the **data shape** Duy or Phi/Hung already integrate
against — table names, view names, and JSON export formats are unchanged
from Week 7. What changes is *how the database gets set up and kept safe*,
which is what this document hands off.

---

## 2. What Duy needs (CI/CD + deployment)

### 2.1 Required environment variables

The database layer no longer accepts a default password. Any CI job or
deployment step that touches the database must set:

```
DB_HOST=<postgres host>
DB_PORT=5432
DB_USER=datavision
DB_PASSWORD=<from GitHub Actions secrets / deployment secret store>
DB_NAME=datavision_db
```

`DB_PASSWORD` must come from `secrets.DB_PASSWORD` in GitHub Actions (or the
equivalent secret store on the deployment host) — never committed, never a
literal in `ci.yml` or `docker-compose.db.yml`.

### 2.2 Updated database CI job

Replace the Week 7 "run `setup_local_db.sh`" step with the migration
runner. Minimum required job update in `.github/workflows/ci.yml`:

```yaml
database-ci:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: pgvector/pgvector:pg16
      env:
        POSTGRES_USER: datavision
        POSTGRES_PASSWORD: ${{ secrets.DB_PASSWORD }}
        POSTGRES_DB: datavision_db
      ports:
        - 5432:5432
      options: >-
        --health-cmd "pg_isready -U datavision -d datavision_db"
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5

  steps:
    - uses: actions/checkout@v4

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Run database migrations
      env:
        DB_HOST: localhost
        DB_PORT: 5432
        DB_USER: datavision
        DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        DB_NAME: datavision_db
      run: python week8/database/run_migrations.py

    - name: Load smoke data
      env:
        DB_HOST: localhost
        DB_PORT: 5432
        DB_USER: datavision
        DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        DB_NAME: datavision_db
      run: python run_database_setup.py --smoke

    - name: Run backup + restore gate
      env:
        DB_HOST: localhost
        DB_PORT: 5432
        DB_USER: datavision
        DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        DB_NAME: datavision_db
      run: |
        python week8/database/backup_database.py
        python week8/database/restore_database.py \
          --dump-file "$(ls -t week8/outputs/backups/*.dump | head -1)" \
          --verify

    - name: Run database validation queries
      run: bash week8/database/ci_database_smoke_test.sh

    - name: Run database unit + integration tests
      run: pytest -m "unit or integration"
```

### 2.3 Client/server version pinning (known CI gotcha)

If the CI runner's `pg_dump`/`pg_restore` (installed via `apt`) is a newer
major version than the `pgvector/pgvector:pg16` service container, restore
can fail with:

```
ERROR: unrecognized configuration parameter "transaction_timeout"
```

This is a harmless client/server version mismatch, not a data problem.
`restore_database.py` already tolerates this specific error and still runs
`--verify` as the real pass/fail signal. If you want to avoid it entirely in
CI, pin the CLI tools with:

```yaml
    - name: Point restore scripts at matching pg16 client tools
      run: echo "PG_BIN_DIR=/usr/lib/postgresql/16/bin" >> $GITHUB_ENV
```

(Install `postgresql-client-16` first if it isn't preinstalled on the
runner image.)

### 2.4 What must gate deployment

Per the team completion plan, **private staging must not be deployed until
the database backup/restore gate passes** on the final green `main` SHA.
Concretely: after Phat's PR is merged and the final SHA is selected, re-run

```bash
python week8/database/backup_database.py
python week8/database/restore_database.py --dump-file <dump> --verify
```

against that SHA and attach the resulting `backup_manifest.json` and
`restore_result.json` to the release evidence package before Duy proceeds
with image publishing / remote deployment.

### 2.5 Commands reference for Duy

| Purpose | Command |
|---|---|
| Apply pending migrations | `python week8/database/run_migrations.py` |
| Check what would run (no changes) | `python week8/database/run_migrations.py --dry-run` |
| Full setup + smoke data | `python run_database_setup.py --smoke` |
| Backup | `python week8/database/backup_database.py` |
| Restore + verify | `python week8/database/restore_database.py --dump-file <path> --verify` |
| Validation queries | `psql -f week8/database/validation_queries_v3.sql` |
| Unit/integration tests only | `pytest -m "unit or integration"` |

---

## 3. What Phi/Hung needs (dashboard / UI)

### 3.1 No breaking changes to consume

All 12 views Phi/Hung's UI already reads are unchanged in name and column
shape from Week 7:

```
v_dashboard_overview            v_prediction_confidence_summary
v_data_quality_dashboard        v_prediction_review_queue
v_document_quality_summary      v_rag_daily_metrics
v_document_rag_readiness        v_recent_activity
v_ingestion_health              v_source_quality_detail
v_latest_ingestion_runs         v_source_quality_summary
```

Nothing in Phi/Hung's existing service-client or fixture code needs to
change because of the Week 8 migration/backup/restore work.

### 3.2 Fresh JSON fixture samples

After the migration + smoke data load, export fresh dashboard JSON exactly
as in Week 7:

```bash
python week8/database/export_dashboard_views.py
```

Output lands in `week8/outputs/dashboard_view_samples/*.json` — same folder
and filenames as Week 7, so no path changes needed on the UI side.

### 3.3 One thing worth knowing: idempotent seeding

Smoke/demo data can now be reloaded safely without producing duplicate
rows (`python run_database_setup.py --smoke` run twice yields identical
row counts). If Phi/Hung's contract tests were previously written to
tolerate row-count drift across repeated fixture generation, that
workaround is no longer necessary — counts will now be stable across
reruns.

### 3.4 Review queue and status values (unchanged, restated for clarity)

`v_prediction_review_queue` rows have `status IN
('needs_review', 'waiting_for_source')`. Per the team completion plan,
`status = 'failed'` must **not** be treated as an acceptable state anywhere
in the UI's release-acceptance flow — that gate is owned by Tuong
(DV-TUONG-04), but the review queue view itself never surfaces `failed`
rows, so no UI change is required to comply.

---

## 4. Evidence attached with this handoff

- `docs/week8_migration_result.md` — fresh install + upgrade test output
- `docs/week8_restore_result.md` — restore rehearsal output, row-count match
- `docs/week8_idempotency_result.md` — before/after seed row counts
- `docs/week8_secrets_hardening.md` — where hard-coded credentials were removed
- `week8/outputs/backups/backup_manifest.json` — latest backup metadata/checksum
- `week8/outputs/db_validation/restore_result.json` — latest restore verification
- `week8/outputs/db_validation/idempotency_check.json` — seed rerun row counts
- PR: `<link once opened>`
- Commit SHA: `<git rev-parse HEAD>`

---

## 5. Open items / dependencies back to Duy

- Confirm `secrets.DB_PASSWORD` is configured in the canonical repo's
  GitHub Actions secrets before this CI job update is merged — the job
  will fail closed (not silently pass) if it's missing, since
  `run_migrations.py` and `restore_database.py` both refuse to run without
  `DB_PASSWORD` set.
- `ci.yml`'s database job needs the "Run database migrations" and "Run
  backup + restore gate" steps added (Section 2.2) before the database
  backup/restore gate in the team's final integration order (Section 8 of
  the completion plan) can be satisfied automatically in CI rather than
  manually.
