# Week 7 Data Tests Result

Command:

```bash
pytest tests/data_tests/ -q
```

Coverage includes ingestion modules, data quality, manifests, API fallback,
PostgreSQL mapping/preflight, canonical source load order, pinned Phat schema,
exact database run-ID query-back, Week 7 page-field aliases, dry-run and smoke
counts, current full DB proof, DB-enriched RAG/prediction/UI
contracts, Duy-to-Lap and Duy-to-Tuong audit gates, the Duy-to-Phi/Hung audit
gate, and the CI-safe ingestion smoke test.

Verified result:

```text
59 passed
```

This exceeds the target of at least 25 passing tests with zero failures.
The Phi/Hung test/smoke execution is also recorded separately in
`outputs/hung_handoff/hung_week7_mapping_summary.json`; its current owner
status is blocked on Tuong fixture lineage and the missing local UI test
dependencies. Its UI code/docs and UI smoke gates pass.
