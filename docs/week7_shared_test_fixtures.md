# Week 7 Shared Test Fixtures

Folder: `tests/fixtures/data/`

| File | Purpose |
| --- | --- |
| `sample_superstore_small.csv` | CSV ingestion and DB smoke data |
| `sample_product_sales_small.xlsx` | Excel ingestion smoke data |
| `sample_api_products.json` | Offline API fallback |
| `sample_dataflow_pages_small.jsonl` | RAG and page contract tests |
| `sample_dataflow_small.pdf` | Two-page PDF extraction test |

Regenerate deterministically:

```bash
python scripts/week7_build_shared_test_fixtures.py
```

These fixtures are intentionally small, project-relative, internet-independent, and reusable by database, RAG, prediction, and UI CI jobs.
