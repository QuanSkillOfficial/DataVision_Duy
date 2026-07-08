# Week 6 Document Pages for RAG Confirmation

Owner: Nguyen Minh Duy  
Consumer: Lap - RAG and Embeddings Owner

## Confirmed Input

```text
week2/data/staging/pdf/document_pages.jsonl
outputs/rag_handoff/document_pages.jsonl
```

Lap should use `outputs/rag_handoff/document_pages.jsonl` for Week 6 integration. The `week2/` path is the original generated output; the `outputs/rag_handoff/` path is the packaged handoff path.

## Current PDF Source

| Field | Value |
| --- | --- |
| Source file | `DataFlow_Technical_Report.pdf` |
| Document external ID | `doc_dataflow_technical_report` |
| Internal DB document ID from Phat | `1` |
| Pages extracted | 36 |
| Empty pages | 0 |
| Total characters | 129028 |
| Page number base | Starts at 1 |
| Ready for chunking | Yes |

## JSONL Record Shape

```json
{
  "document_id": "doc_dataflow_technical_report",
  "file_name": "DataFlow_Technical_Report.pdf",
  "page_number": 1,
  "text": "...",
  "character_count": 1234,
  "is_empty": false,
  "source": "DataFlow_Technical_Report.pdf",
  "raw_output_path": "week2/data/raw/pdf/dataflow_technical_report_raw.pdf",
  "staging_text_path": "week2/data/staging/pdf/dataflow_pdf_text.txt"
}
```

## Lap Usage

Lap should use:

- `document_id` as external key for chunk ID construction.
- `file_name` and `page_number` for citations.
- `text` for chunking and embedding.
- `is_empty` to skip empty pages.

Recommended chunk ID pattern:

```text
doc_dataflow_technical_report_page_1_chunk_000
```

Lap's Week 6 defaults:

| Setting | Value |
| --- | --- |
| Chunk size | `512` |
| Overlap | `50` |
| Embedding model | `all-MiniLM-L6-v2` |
| Embedding dimension | `384` |

Expected output back from Lap:

| Output | Expected Path / Format |
| --- | --- |
| Load/chunk stats | Markdown or JSON from Lap |
| pgvector insertion proof | Screenshot, SQL output, or JSON |
| Retrieval evaluation | `ai/rag/evaluation/week6_retrieval_eval_results.md` |
| Citation-ready UI fixture | `outputs/ui_fixtures/lap_rag_response_real.json` |
| Duy-to-Lap summary | `outputs/lap_handoff/lap_week6_mapping_summary.json` |

## Current Lap Review Status

Reviewed from `F:/data/new/quanskill/DataVision_Lap`:

| Item | Status |
| --- | --- |
| `ai/rag/load_document_pages_to_pgvector.py` | exists |
| `ai/week6_rag_to_schema_v4_mapping.md` | exists |
| `ai/rag/evaluation/week6_retrieval_test_cases_dataflow.csv` | exists with 15 queries |
| `ai/rag/evaluation/week6_retrieval_eval_results.md` | exists as fixture/recorded evaluation |
| `ai/rag/notebooks/week6_real_pgvector_rag_demo.ipynb` | exists but has no executed outputs |
| `outputs/ui_fixtures/lap_rag_response_real.json` | not found in Lap repo |
| `screenshots/week6_pgvector_retrieval_result.png` | not found in Lap repo |

Current conclusion:

```text
Duy's document_pages.jsonl is ready.
Lap's code is ready for pgvector insertion/retrieval.
Lap still needs to provide live execution proof, UI fixture, and screenshot/query-log evidence.
```
