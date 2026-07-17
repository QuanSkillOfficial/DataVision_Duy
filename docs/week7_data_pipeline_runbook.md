# Week 7 Data Pipeline Runbook

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. Run full local ingestion

```bash
python -m data_engineering.pipelines.ingestion_engine --all
```

Expected valid records: CSV `9,994`, Excel `1,500`, API `30`, PDF `36` pages.

## 3. Run CI smoke ingestion

```bash
python scripts/week7_build_shared_test_fixtures.py
python scripts/week7_ci_ingestion_smoke_test.py
```

## 4. Inspect database plan

```bash
python scripts/load_ingestion_outputs_to_postgres.py --dry-run --smoke
```

## 5. Load PostgreSQL

Set the `DB_*` variables from `.env.example`, then run:

```bash
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
```

Use the same command without `--smoke` for all 11,524 structured records.

## 6. Regenerate team handoffs

```bash
python scripts/week7_build_rag_handoff_package.py
python scripts/week7_build_prediction_payloads.py
python scripts/week7_build_ui_fixtures.py
```

## 7. Validate

```bash
pytest tests/data_tests/ -q
python scripts/week7_data_pipeline_smoke_test.py
python scripts/validate_week7.py
```

## Common errors

- `connection refused`: start Phat's Docker PostgreSQL and verify `DB_PORT`.
- schema preflight failure: run Phat's fixed Week 7 setup; do not patch tables manually.
- null DB IDs: run the real loader, then regenerate all three handoffs.
- API unavailable: the configured local JSON fallback is used.
- PDF font warnings: the ingestor suppresses non-actionable pdfminer font descriptor warnings.
