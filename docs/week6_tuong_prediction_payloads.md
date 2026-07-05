# Week 6 Tuong Prediction Payloads

Owner: Nguyen Minh Duy  
Consumer: Tuong - Prediction Engine Owner

## Purpose

These 10 payloads are Duy-style ingestion outputs for Tuong to test single and batch document classification.

Main batch file:

```text
outputs/prediction_payloads/tuong_week6_prediction_payloads.json
logs/prediction_payloads/tuong_week6_prediction_payloads.json
```

## Payload Inventory

| # | document_external_id | source_name | file_type | text_length | test_case | expected_status_hint |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `doc_dataflow_technical_report` | `dataflow_technical_report_pdf` | `pdf` | 129028 | `full_pdf_document` | `accepted_or_needs_review` |
| 2 | `doc_dataflow_technical_report_intro_pages` | `dataflow_technical_report_pdf` | `pdf` | 9377 | `pdf_intro_section` | `accepted_or_needs_review` |
| 3 | `doc_dataflow_technical_report_architecture_page` | `dataflow_technical_report_pdf` | `pdf` | 4521 | `pdf_architecture_page` | `accepted_or_needs_review` |
| 4 | `doc_dataflow_technical_report_related_work` | `dataflow_technical_report_pdf` | `pdf` | 7594 | `pdf_related_work_section` | `accepted_or_needs_review` |
| 5 | `doc_superstore_sales_csv_summary` | `superstore_sales_csv` | `csv` | 2516 | `csv_structured_summary` | `accepted_or_needs_review` |
| 6 | `doc_product_sales_region_excel_summary` | `product_sales_region_excel` | `xlsx` | 2051 | `excel_structured_summary` | `accepted_or_needs_review` |
| 7 | `doc_dummyjson_products_api_summary` | `dummyjson_products_api` | `json` | 7679 | `api_structured_summary` | `accepted_or_needs_review` |
| 8 | `doc_short_text_quality_gate` | `dataflow_technical_report_pdf` | `pdf` | 11 | `short_extracted_text_quality_gate` | `waiting_for_source_or_needs_review` |
| 9 | `doc_empty_text_quality_gate` | `dataflow_technical_report_pdf` | `pdf` | 0 | `empty_extracted_text_quality_gate` | `waiting_for_source` |
| 10 | `doc_missing_file_name_validation` | `dataflow_technical_report_pdf` | `pdf` | 90 | `missing_required_file_name` | `failed` |

## ID Rules

```text
source_id is null before Phat DB insert.
document_db_id is null before Phat DB insert.
ingestion_run_id is Duy's run UUID.
document_external_id is the stable document key.
```

## Test Coverage

- Full DataFlow PDF payload
- PDF section-level payloads
- CSV / Excel / API structured source summaries
- Short extracted text quality gate
- Empty extracted text quality gate
- Missing required field validation case

Tuong should use these to test:

```text
accepted
needs_review
waiting_for_source
failed
batch validation error normalization
```
