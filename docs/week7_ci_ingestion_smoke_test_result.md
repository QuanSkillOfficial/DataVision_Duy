# Week 7 CI Ingestion Smoke Test Result

Command:

```bash
python scripts/week7_build_shared_test_fixtures.py
python scripts/week7_ci_ingestion_smoke_test.py
```

Result: `passed`

The local run completed in under one second and validated:

- CSV ingestion: 8 rows
- Excel ingestion: 8 rows
- API local fallback: 5 rows
- PDF extraction: 2 pages
- four SHA256 manifests
- data-quality scores
- page-level RAG handoff
- prediction payload creation
- UI fixture creation

The smoke test writes only to a temporary workspace directory and removes it after completion. It does not require internet access, DBeaver, PostgreSQL, or laptop-specific paths.
