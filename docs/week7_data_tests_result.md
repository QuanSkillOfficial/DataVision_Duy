# Week 7 Data Tests Result

Command:

```bash
pytest tests/data_tests/ -q
```

Coverage includes ingestion modules, data quality, manifests, API fallback, PostgreSQL mapping/preflight, dry-run and smoke counts, DB-enriched RAG/prediction/UI contracts, and the CI-safe ingestion smoke test.

Verified result:

```text
40 passed in 9.56s
```

This exceeds the target of at least 25 passing tests with zero failures.
