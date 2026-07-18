# Week 7 Data Tests Result

Command:

```bash
pytest tests/data_tests/ -q
```

Coverage includes ingestion modules, data quality, manifests, API fallback,
PostgreSQL mapping/preflight, dry-run and smoke counts, DB-enriched
RAG/prediction/UI contracts, Duy-to-Lap and Duy-to-Tuong audit gates, the
Duy-to-Phi/Hung audit gate, and the CI-safe ingestion smoke test.

Verified result:

```text
51 passed in 16.90s
```

This exceeds the target of at least 25 passing tests with zero failures.
The Phi/Hung test/smoke execution is also recorded separately in
`outputs/hung_handoff/hung_week7_mapping_summary.json`; its current owner
status is blocked only on stale fixture lineage and contract cleanup.
