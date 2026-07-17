# Week 7 Team Integration Handoff for Duy

## 1. Mục đích

Tài liệu này là nguồn tham chiếu chung cho việc phối hợp giữa Duy và:

- Phat: PostgreSQL, database IDs và dashboard views.
- Lap: RAG handoff, chunking, pgvector retrieval và citations.
- Tuong: prediction payloads, prediction logs và review workflow.
- Phi/Hung: ingestion fixture, dashboard, suggestions, reports và CI/CD.

Tất cả đường dẫn bên dưới là đường dẫn tương đối tính từ thư mục gốc của repository `DataVision_Duy`.

## 2. Trạng thái dữ liệu hiện tại

| Source | Type | Latest ingestion run ID | Valid records | Data quality |
| --- | --- | --- | ---: | ---: |
| `superstore_sales_csv` | CSV | `2ff14e5d-dcec-44a2-b45e-35544042579a` | 9,994 | 100.00 |
| `product_sales_region_excel` | Excel | `413e8c49-ff70-4710-9760-75c40e97c527` | 1,500 | 99.51 |
| `dummyjson_products_api` | API | `3564b7ac-b0c0-4400-abc3-3371881c9db8` | 30 | 99.00 |
| `dataflow_technical_report_pdf` | PDF | `24aecb87-2d79-4708-82b8-01164c9fecd2` | 36 pages | 100.00 |

Current verified totals:

| Metric | Value |
| --- | ---: |
| Structured records | 11,524 |
| PDF pages | 36 |
| Non-empty PDF pages | 36 |
| Extracted PDF characters | 129,028 |
| Extracted PDF words | 17,536 |
| Prediction test payloads | 20 |
| Average data quality score | 99.63 |

Current database identity status:

```text
pending_database_load
```

`source_id` and `document_db_id` are currently `null` because Phat's fixed PostgreSQL schema has not yet been loaded and verified. Do not replace these values with guessed integers.

## 3. ID standard used by all members

| Field | Meaning | Type before DB load | Type after DB load |
| --- | --- | --- | --- |
| `source_id` | Primary key from Phat's `sources.id` | `null` | integer |
| `source_name` | Stable source name from Duy config | string | string |
| `ingestion_run_id` | UUID generated for one ingestion execution | UUID string | UUID string |
| `document_external_id` | Stable cross-repository document key | string | string |
| `document_db_id` | Internal key from Phat's `documents.id` | `null` | integer |

Mandatory rules:

1. Never store `ingestion_run_id` in `source_id`.
2. Never insert `document_external_id` into an integer `document_id` foreign key.
3. Resolve `document_external_id -> documents.id` before inserting document pages, chunks or prediction logs.
4. Keep `document_external_id` in API/UI payloads for cross-module traceability.
5. Treat `null` DB IDs as `pending_database_load`, not as zero and not as a successful mapping.

## 4. Recommended handoff sequence

1. Send the Duy-to-Phat package first.
2. Phat starts PostgreSQL/pgvector and returns confirmed database IDs.
3. Duy runs the real DB smoke load and rebuilds all DB-enriched outputs.
4. Send the rebuilt package to Lap and Tuong.
5. Send the rebuilt UI summary to Phi/Hung.
6. Lap, Tuong and Phi/Hung return their integration outputs.
7. Duy and Phi/Hung add all module commands to the shared CI workflow.

Sending the current files to Lap, Tuong and Phi/Hung before Phat completes the DB load is still useful for contract validation, but those files must be labeled as `pending_database_load`.

---

## 5. Duy -> Phat: PostgreSQL integration

### 5.1 Files Duy should send to Phat

Database loader and contract:

| File | Purpose |
| --- | --- |
| `scripts/load_ingestion_outputs_to_postgres.py` | Official dry-run, smoke write and full write loader |
| `data_engineering/storage/db_connection.py` | Environment-based PostgreSQL connection |
| `data_engineering/storage/postgres_writer.py` | Upsert, insert, transaction and schema validation logic |
| `data_engineering/configs/db_config.example.json` | Example database configuration |
| `.env.example` | Environment variable names without real secrets |
| `docs/week7_db_modes_for_ingestion.md` | Commands for the three DB loading modes |
| `docs/week7_duy_phat_real_db_loading_result.md` | Current result and pending external dependency |

Latest run logs:

| Source | Run log |
| --- | --- |
| CSV | `logs/runs/2ff14e5d-dcec-44a2-b45e-35544042579a.json` |
| Excel | `logs/runs/413e8c49-ff70-4710-9760-75c40e97c527.json` |
| API | `logs/runs/3564b7ac-b0c0-4400-abc3-3371881c9db8.json` |
| PDF | `logs/runs/24aecb87-2d79-4708-82b8-01164c9fecd2.json` |
| Append-only history | `logs/ingestion_runs.jsonl` |

File manifests:

| Source | Manifest |
| --- | --- |
| CSV | `logs/manifests/2ff14e5d-dcec-44a2-b45e-35544042579a_manifest.json` |
| Excel | `logs/manifests/413e8c49-ff70-4710-9760-75c40e97c527_manifest.json` |
| API | `logs/manifests/3564b7ac-b0c0-4400-abc3-3371881c9db8_manifest.json` |
| PDF | `logs/manifests/24aecb87-2d79-4708-82b8-01164c9fecd2_manifest.json` |

Clean data:

| Target table | Input file |
| --- | --- |
| `structured_records` from CSV | `week2/data/clean/csv/superstore_clean.csv` |
| `structured_records` from Excel | `week2/data/clean/excel/product_sales_region_clean.csv` |
| `structured_records` from API | `week2/data/clean/api/dummyjson_products_clean.csv` |
| `documents` | `outputs/rag_handoff/pdf_metadata.json` |
| `document_pages` | `outputs/rag_handoff/week7_document_pages_db_enriched.jsonl` |

Dry-run proof:

| Mode | File | Expected structured records |
| --- | --- | ---: |
| Full | `logs/db_load_dry_run/duy_to_phat_db_load_plan.json` | 11,524 |
| Smoke | `logs/db_load_dry_run/duy_to_phat_db_smoke_plan.json` | 100 |

### 5.2 Fields Phat must map

| Duy field | Phat table/column |
| --- | --- |
| `source_name` | `sources.name` |
| `source_type` | `sources.source_type` or final agreed column |
| `ingestion_run_id` | `pipeline_runs.run_id` and `ingestion_logs.run_id` |
| `status` | `pipeline_runs.status`, `ingestion_logs.status` |
| `records_read` | `ingestion_logs.records_read` |
| `records_valid` | `ingestion_logs.records_valid` |
| `records_invalid` | `ingestion_logs.records_invalid` |
| `data_quality_score` | `ingestion_logs.data_quality_score` |
| `file_hash_sha256` | source/document metadata or final schema field |
| `manifest_path` | `ingestion_logs.manifest_path` |
| `document_external_id` | `documents.document_external_id` |
| page `text` | `document_pages.page_text` or final agreed column |
| structured row | `structured_records.record_data` JSONB |

### 5.3 What Duy needs back from Phat

Phat must return:

| Required output | Expected path or content |
| --- | --- |
| Fixed schema | `week7/database/schema_v4_fixed.sql` |
| Reproducible setup | `week7/database/setup_database_v3.sql` or one-command setup script |
| Docker database | `docker-compose.db.yml` and non-secret connection instructions |
| Final column contract | Exact columns, types, constraints and insert order |
| Source ID mapping | Each `source_name -> sources.id` |
| Document ID mapping | `doc_dataflow_technical_report -> documents.id` |
| Query proof | Counts from the six ingestion tables |
| Dashboard samples | `week7/outputs/dashboard_view_samples/*.json` |

Expected database mapping response:

```json
{
  "database_identity_status": "database_ids_confirmed",
  "sources": {
    "superstore_sales_csv": 1,
    "product_sales_region_excel": 2,
    "dummyjson_products_api": 3,
    "dataflow_technical_report_pdf": 4
  },
  "documents": {
    "doc_dataflow_technical_report": 1
  }
}
```

The integers above are examples only. Duy must use the IDs actually returned by PostgreSQL.

### 5.4 Acceptance criteria for Duy + Phat

| Table | Smoke mode | Full mode |
| --- | ---: | ---: |
| `sources` | 4 | 4 |
| `pipeline_runs` | 4 or more | 4 or more |
| `ingestion_logs` | 4 | 4 |
| `documents` | 1 | 1 |
| `document_pages` | 36 | 36 |
| `structured_records` | 100 | 11,524 |

The mapping is complete only when:

- All query counts are returned from the real database.
- `source_id` and `document_db_id` are non-null in the DB result.
- Re-running the same ingestion runs does not create duplicate sources or duplicate run records.
- `logs/db_load_results/duy_to_phat_db_load_result.json` contains real query-back evidence.

---

## 6. Duy -> Lap: RAG and pgvector handoff

### 6.1 Files Duy should send to Lap

| File | Purpose |
| --- | --- |
| `outputs/rag_handoff/week7_document_pages_db_enriched.jsonl` | Primary page-level RAG input |
| `outputs/rag_handoff/week7_rag_handoff_manifest.json` | Counts, IDs, hash and expected chunk ID format |
| `outputs/rag_handoff/pdf_metadata.json` | Document-level PDF metadata |
| `docs/week7_duy_to_lap_rag_handoff.md` | Handoff rules |
| `tests/fixtures/data/sample_dataflow_pages_small.jsonl` | Small CI-safe RAG fixture |

### 6.2 Page record contract

Every JSONL row provides:

```json
{
  "document_id": "doc_dataflow_technical_report",
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": null,
  "source_id": null,
  "ingestion_run_id": "24aecb87-2d79-4708-82b8-01164c9fecd2",
  "file_name": "DataFlow_Technical_Report.pdf",
  "page_number": 1,
  "text": "...",
  "char_count": 2953,
  "character_count": 2953,
  "word_count": 343,
  "is_empty": false,
  "source": "DataFlow_Technical_Report.pdf"
}
```

Verified document facts:

- `document_external_id`: `doc_dataflow_technical_report`
- `file_name`: `DataFlow_Technical_Report.pdf`
- pages: 36
- non-empty pages: 36
- total characters: 129,028
- total words: 17,536
- expected chunk ID: `doc_dataflow_technical_report_page_{page_number}_chunk_{chunk_index:03d}`

Known extraction note:

- Some PDF symbols may appear as font-decoding artifacts such as `âˆ—` or `â€`.
- Lap should preserve page numbers and citations even if text normalization is added.
- Text normalization must not change `document_external_id`, `page_number` or source lineage.

### 6.3 What Duy needs back from Lap

| Required output | Expected path/content |
| --- | --- |
| Handoff validation | Pages loaded, skipped pages, characters and words |
| Chunk insert result | Inserted count, duplicate count and embedding dimension |
| ID resolution proof | `document_external_id -> documents.id` |
| pgvector search result | Top-k chunk IDs, pages and similarity scores |
| RAG query log result | At least one row inserted into `rag_query_logs` |
| UI response fixture | Real DataFlow response at `outputs/ui_fixtures/lap_rag_response_real.json` |
| Citation contract | `file_name`, `page_number`, `chunk_id`, `similarity_score` |

Lap's returned fixture must include:

```text
question
status
document_external_id
document_db_id
file_name
retrieved_context[]
citations[]
metadata.retrieval_backend
metadata.embedding_dimension
```

### 6.4 Acceptance criteria for Duy + Lap

- Lap loads exactly 36 pages and skips zero non-empty pages.
- The loader resolves a real integer `document_db_id`.
- Every embedding has 384 dimensions.
- `document_chunks` contains the actual generated count.
- A pgvector top-k query returns `chunk_id`, `page_number` and `similarity_score`.
- At least one RAG query log exists.
- Phi/Hung receive a real DataFlow citation fixture, not the old vendor/refund example.

---

## 7. Duy -> Tuong: prediction handoff

### 7.1 Files Duy should send to Tuong

| File | Purpose |
| --- | --- |
| `outputs/prediction_payloads/tuong_week7_prediction_payloads.json` | Primary batch containing all 20 test cases |
| `outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json` | Additional cases 11-20 only |
| `outputs/prediction_payloads/week7/*.json` | Twenty individually addressable payload files |
| `docs/week7_duy_to_tuong_prediction_payload_contract.md` | Field and ID rules |
| `docs/week7_duy_to_tuong_additional_prediction_payloads.md` | Additional case matrix and expected behavior |
| `tests/fixtures/data/sample_api_products.json` | Small structured-data CI fixture |
| `tests/fixtures/data/sample_dataflow_pages_small.jsonl` | Small PDF-text CI fixture |

### 7.2 Twenty supplied cases

| No. | File | Purpose | Expected workflow |
| ---: | --- | --- | --- |
| 1 | `01_doc_dataflow_technical_report.json` | Full DataFlow PDF | Normal prediction; accepted or review based on confidence |
| 2 | `02_doc_dataflow_technical_report_intro_pages.json` | Intro pages | Normal prediction |
| 3 | `03_doc_dataflow_technical_report_architecture_page.json` | Architecture page | Normal prediction |
| 4 | `04_doc_dataflow_technical_report_related_work.json` | Related-work section | Normal prediction |
| 5 | `05_doc_superstore_sales_csv_summary.json` | CSV summary | Normal prediction |
| 6 | `06_doc_product_sales_region_excel_summary.json` | Excel summary | Normal prediction |
| 7 | `07_doc_dummyjson_products_api_summary.json` | API summary | Normal prediction |
| 8 | `08_doc_short_text_quality_gate.json` | Very short text | `waiting_for_source` |
| 9 | `09_doc_empty_text_quality_gate.json` | Empty text | `waiting_for_source` |
| 10 | `10_doc_missing_file_name_validation.json` | Missing required field | `failed` |
| 11 | `11_doc_dataflow_system_operators_pages.json` | DataFlow system/operators pages 9-10 | Normal prediction |
| 12 | `12_doc_dataflow_pipeline_api_pages.json` | DataFlow pipeline API pages 11-12 | Normal prediction |
| 13 | `13_doc_dataflow_agent_workflow_pages.json` | DataFlow agent workflow pages 14-15 | Normal prediction |
| 14 | `14_doc_dataflow_agentic_rag_evaluation_pages.json` | Agentic RAG and evaluation pages 25, 29 | Normal prediction |
| 15 | `15_doc_superstore_order_profitability_sample.json` | New Superstore row sample | Normal prediction |
| 16 | `16_doc_product_sales_region_sample.json` | New regional sales row sample | Normal prediction |
| 17 | `17_doc_dummyjson_inventory_sample.json` | New product inventory row sample | Normal prediction |
| 18 | `18_doc_dataflow_technical_notes_markdown.json` | Unknown `md` file type with valid text | Must not crash |
| 19 | `19_missing_document_external_id.json` | Missing platform lineage ID | `failed_contract_validation` |
| 20 | `20_doc_invalid_file_size_validation.json` | Non-numeric `file_size` | `failed` |

Each payload provides or intentionally tests:

```text
source_id
source_name
document_external_id
document_db_id
ingestion_run_id
file_name
file_type
file_size
text_length
num_pages
page_range
source_system
extracted_text
parsing_status
data_quality_score
file_hash_sha256
```

Important:

- The current batch has `source_id = null` and `document_db_id = null` until Phat confirms DB IDs.
- Only the full DataFlow document should receive the stored DataFlow `document_db_id`.
- Derived sections and CSV/Excel/API summaries must not reuse the full document's internal ID.
- Case 10 intentionally omits `file_name`; Tuong must not repair it silently.
- Case 19 intentionally omits `document_external_id` and its backward-compatible alias.
- Case 20 intentionally sends `file_size = "not-a-number"` to test normalized batch errors.

### 7.3 What Duy needs back from Tuong

| Required output | Expected path/content |
| --- | --- |
| Batch result | `outputs/week7_duy_prediction_results.json` |
| DB log payloads | `outputs/db_integration/week7_prediction_log_payloads.json` |
| DB insert proof | Insert count and `v_prediction_review_queue` query result |
| UI batch fixture | `outputs/ui_fixtures/tuong_prediction_batch_response.json` |
| Review queue fixture | `outputs/ui_fixtures/tuong_prediction_review_queue_sample.json` |
| RAG filter metadata | `outputs/rag_metadata/document_type_filter_payload.json` |
| Final validation contract | Required fields, accepted file types and minimum text length |

Every returned prediction must use one standard shape with:

```text
predicted_document_type
confidence
top_predictions
status
review_reason
manual_review_required
model_name
model_version
source_id
document_external_id
document_db_id
ingestion_run_id
created_at
```

Allowed statuses:

```text
accepted
needs_review
waiting_for_source
failed
```

### 7.4 Acceptance criteria for Duy + Tuong

- All 20 inputs produce 20 standardized outputs.
- Short and empty text produce `waiting_for_source`.
- Missing `file_name` produces `failed`.
- Unknown Markdown input does not crash the batch.
- Missing `document_external_id` fails platform-contract validation.
- Invalid numeric metadata produces a normalized `failed` response.
- `source_id` is never populated with an ingestion UUID.
- `document_db_id` maps to Phat's integer `documents.id`.
- All results can be converted into Phat's `prediction_logs` payload.
- Low-confidence predictions are soft metadata only and do not become hard RAG filters.

---

## 8. Duy -> Phi/Hung: UI, dashboard and CI fixture handoff

### 8.1 Files Duy should send to Phi/Hung

Primary Week 7 fixture:

| File | Purpose |
| --- | --- |
| `outputs/ui_fixtures/duy_week7_database_enriched_summary.json` | Dashboard-ready ingestion summary |
| `docs/week7_duy_to_phi_hung_ui_fixture_contract.md` | UI field behavior |

Backward-compatible supporting fixtures:

| File | Purpose |
| --- | --- |
| `outputs/ui_fixtures/duy_latest_ingestion_summary.json` | Latest per-source ingestion rows |
| `outputs/ui_fixtures/duy_data_quality_summary.json` | Data-quality evidence |
| `outputs/ui_fixtures/duy_pdf_document_summary.json` | PDF/document summary |

CI and fixture package:

| File | Purpose |
| --- | --- |
| `tests/fixtures/data/sample_superstore_small.csv` | Small CSV fixture |
| `tests/fixtures/data/sample_product_sales_small.xlsx` | Small Excel fixture |
| `tests/fixtures/data/sample_api_products.json` | Offline API fixture |
| `tests/fixtures/data/sample_dataflow_pages_small.jsonl` | Small RAG fixture |
| `scripts/week7_ci_ingestion_smoke_test.py` | Data CI smoke command |
| `scripts/week7_data_pipeline_smoke_test.py` | Cross-output contract smoke test |
| `.github/workflows/ci.yml` | Current data-engineering CI draft |
| `docs/week7_duy_ci_commands.md` | Commands Phi/Hung can add to shared CI |

### 8.2 Current UI values

Phi/Hung should display:

| UI metric | Current value |
| --- | ---: |
| Total sources | 4 |
| Total latest runs | 4 |
| Successful runs | 4 |
| Failed runs | 0 |
| Structured records | 11,524 |
| PDF pages | 36 |
| Average data quality | 99.63 |
| Latest document | `DataFlow_Technical_Report.pdf` |
| Database identity | `pending_database_load` |

UI requirements:

- Display `source_id` and `document_db_id` only when non-null.
- Show a pending mapping state instead of converting null IDs to zero.
- Use `ingestion_run_id` for run details and recent activity.
- Use `document_external_id` for cross-module links.
- Use `file_hash_sha256` as ingestion evidence, not as a visible secret.
- Use portable handoff paths from `handoff_paths`.

### 8.3 What Duy needs back from Phi/Hung

| Required output | Expected path/content |
| --- | --- |
| Copied Week 7 fixture | `demo/fixtures/week7/duy_latest_ingestion_summary.json` |
| Fixture validation result | Duy fixture passes `fixture_validator.py` |
| Final dashboard field list | Exact fields consumed by each UI card/table |
| Data-quality display rules | Percentage precision and warning thresholds |
| ID display rules | Pending/non-null behavior |
| Report evidence fields | Final ingestion evidence columns |
| Suggestion signals | Conditions using quality, invalid records and DB status |
| UI CI command | Command added to shared GitHub Actions workflow |

### 8.4 Acceptance criteria for Duy + Phi/Hung

- Dashboard opens directly in fixture mode without requiring Upload first.
- Dashboard displays 4 sources, 4 successful runs, 11,524 structured records, 36 PDF pages and quality 99.63.
- Null database IDs are shown as pending, not zero.
- Suggestions use Duy's real quality/status evidence.
- Reports include ingestion evidence even when suggestions are unavailable.
- The fixture validator runs in CI.

---

## 9. Shared CI package for all team members

These files can be used by Phat, Lap, Tuong and Phi/Hung:

```text
tests/fixtures/data/sample_superstore_small.csv
tests/fixtures/data/sample_product_sales_small.xlsx
tests/fixtures/data/sample_api_products.json
tests/fixtures/data/sample_dataflow_pages_small.jsonl
scripts/week7_ci_ingestion_smoke_test.py
scripts/week7_data_pipeline_smoke_test.py
scripts/validate_week7.py
requirements.txt
.github/workflows/ci.yml
docs/week7_duy_ci_commands.md
docs/week7_github_ci_cd_integration_plan.md
```

Verified Duy CI commands:

```powershell
python scripts/week7_build_shared_test_fixtures.py
python scripts/week7_ci_ingestion_smoke_test.py
python -m pytest tests/data_tests/ -q
python scripts/week7_data_pipeline_smoke_test.py
python scripts/validate_week7.py
```

Current verification result:

```text
40 tests passed
Week 7 ingestion CI smoke test passed
Week 7 data pipeline smoke test passed
Week 7 validation passed
```

## 10. Commands after Phat provides PostgreSQL

Set the real local or Docker credentials without committing passwords:

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_NAME="datavision_db"
$env:DB_USER="datavision"
$env:DB_PASSWORD="<provided-securely>"
```

Run the smoke database integration:

```powershell
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
```

Rebuild all team handoffs with confirmed IDs:

```powershell
python scripts/week7_build_rag_handoff_package.py
python scripts/week7_build_prediction_payloads.py
python scripts/week7_build_ui_fixtures.py
python scripts/validate_week7.py
```

Check that:

```text
database_identity_status = database_ids_confirmed
source_id != null
document_db_id != null for the full DataFlow document
```

Then resend:

1. Lap: rebuilt RAG JSONL, manifest and PDF metadata.
2. Tuong: rebuilt 20-payload batch.
3. Phi/Hung: rebuilt DB-enriched UI summary.
4. Phat: final `logs/db_load_results/duy_to_phat_db_load_result.json`.

## 11. Completion checklist

### Duy + Phat

- [ ] Phat provides fixed schema and reachable PostgreSQL.
- [ ] Duy smoke load passes.
- [ ] Six ingestion table counts match.
- [ ] Source and document IDs are returned.
- [ ] Full or smoke DB result JSON contains query proof.

### Duy + Lap

- [ ] Lap validates 36 page records.
- [ ] Lap resolves `document_external_id` to integer DB ID.
- [ ] Chunks and 384-dimensional embeddings are inserted.
- [ ] Real pgvector top-k retrieval returns citations.
- [ ] RAG query log is inserted.

### Duy + Tuong

- [ ] Tuong validates all 20 payloads.
- [ ] Four platform statuses are standardized.
- [ ] Prediction logs insert into Phat DB.
- [ ] Review queue and UI fixtures are returned.
- [ ] RAG filter metadata uses the safe soft-filter policy.

### Duy + Phi/Hung

- [ ] Week 7 Duy fixture is copied and validated.
- [ ] Dashboard displays current metrics.
- [ ] Pending DB IDs are handled correctly.
- [ ] Suggestions and reports use Duy evidence.
- [ ] UI and data CI jobs are included in the shared workflow.

## 12. Final handoff status

| Collaboration | Duy package status | External confirmation needed |
| --- | --- | --- |
| Duy + Phat | Ready for DB smoke/full loading | Fixed schema, reachable DB, real IDs and SQL counts |
| Duy + Lap | Contract-ready; DB IDs pending | pgvector insert/search/log evidence |
| Duy + Tuong | Twenty payloads ready; DB IDs pending | Prediction results, DB logs and review fixtures |
| Duy + Phi/Hung | UI fixture ready; DB IDs pending | Fixture validation and displayed UI proof |
| Duy + Phi/Hung CI/CD | Data CI section ready | Shared workflow merge and UI CI section |

The highest-priority next action is the Duy + Phat real database smoke load. All other DB-enriched handoffs should be regenerated immediately after that load succeeds.

## 13. Project-level Week 7 delivery

Week 7 is also a shared-repository, Docker and CI/CD week. Duy's repository now
contains the project-level draft files below:

```text
.env.example
docker-compose.db.yml
docker-compose.yml
backend_stub/main.py
scripts/week7_backend_stub_smoke_test.py
scripts/week7_local_docker_integration_smoke_test.py
scripts/week7_shared_repo_readiness_check.py
scripts/week7_shared_integration_smoke_test.py
deployment/Dockerfile.data
deployment/database/init/00_extensions.sql
docs/week7_deployment_runbook.md
docs/week7_shared_repo_structure.md
docs/week7_cross_team_delivery_matrix.md
integration/shared_repo_manifest.json
.github/workflows/ci.yml
```

These files define the integration boundary. They do not claim that the
external modules have already been merged or that a PostgreSQL runtime is
available.

### What Duy sends now

| Recipient | Files / information | Expected response |
| --- | --- | --- |
| Phat | Duy loader, run logs, manifests, clean outputs, DB-enriched RAG handoff, 20 prediction payloads, Docker DB draft, DB environment variable names | Fixed schema/setup, reachable DB, integer `source_id` and `document_db_id`, table counts, DB validation JSON |
| Lap | `outputs/rag_handoff/week7_document_pages_db_enriched.jsonl`, PDF metadata/manifest, stable small fixtures, RAG command | pgvector insert count, top-k result, citation fixture, RAG query-log proof |
| Tuong | `outputs/prediction_payloads/tuong_week7_prediction_payloads.json` with 20 cases, payload contract and ID rules | Prediction result JSON, normalized statuses, DB log payloads, review queue fixture and CI smoke result |
| Phi/Hung | DB-enriched Duy UI summary, data-quality/PDF fixtures, backend envelope, fixture paths and backend URL | Fixture validator, UI smoke result, updated dashboard/prediction/RAG/report fixtures and backend contract test |
| Shared CI owners | `.github/workflows/ci.yml`, ingestion smoke command, readiness/integration smoke commands, `.env.example`, deployment runbook | Merged CI workflow with owner jobs enabled after each module is present |

### What Duy must receive before calling the mapping complete

```text
Phat:
  week7/database/schema_v4_fixed.sql
  week7/database/setup_database_v3.sql
  week7/database/ci_database_smoke_test.py or .sh
  week7/outputs/db_validation/duy_data_load_counts.json
  week7/outputs/dashboard_view_samples/*.json

Lap:
  outputs/rag/week7_pgvector_insert_result.json
  outputs/rag/week7_pgvector_query_result.json
  outputs/rag/week7_rag_query_log_payload.json
  outputs/ui_fixtures/lap_rag_response_real.json

Tuong:
  outputs/week7_duy_prediction_results.json
  outputs/db_integration/week7_prediction_log_payloads.json
  outputs/ui_fixtures/tuong_prediction_batch_response.json
  scripts/week7_prediction_ci_smoke_test.py

Phi/Hung:
  demo/services/fixture_validator.py
  scripts/week7_ui_ci_smoke_test.py
  demo/fixtures/week7/
  backend API contract and UI smoke result
```

### Current audit notes

The local snapshots inspected during this review still lack the full Week 7
deliverables from Phat, Tuong and Phi/Hung. Lap's current Week 7 RAG smoke
script also needs to import `create_sample_pages` from its fake-test helpers
before it can be treated as CI-ready. These are handoff actions for the
respective owners; they are intentionally not fabricated in Duy's repository.

Use the readiness report after each merge:

```powershell
python scripts/week7_shared_repo_readiness_check.py
python scripts/week7_shared_repo_readiness_check.py --strict
```
