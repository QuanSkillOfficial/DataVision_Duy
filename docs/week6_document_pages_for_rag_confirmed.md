# Week 6 Document Pages for RAG Confirmation

Owner: Nguyen Minh Duy  
Consumer: Lap - RAG and Embeddings Owner

## Confirmed Input

```text
week2/data/staging/pdf/document_pages.jsonl
```

## Current PDF Source

| Field | Value |
| --- | --- |
| Source file | `DataFlow_Technical_Report.pdf` |
| Document external ID | `doc_dataflow_technical_report` |
| Pages extracted | 36 |
| Empty pages | 0 |
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

