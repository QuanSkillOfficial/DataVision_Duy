# Week 7 Team Integration Handoff

## 1. Mục đích

Tài liệu này là source of truth cho việc bàn giao dữ liệu giữa:

- Duy: Data Engineering và CI/CD data pipeline
- Phat: PostgreSQL, pgvector và database CI
- Lap: RAG, chunking, embedding và retrieval
- Tuong: prediction, review workflow và prediction logging
- Phi/Hung: UI, fixture validation, backend contract và UI CI

Mọi đường dẫn đều là relative path tính từ root của repository tương ứng.
Không dùng đường dẫn tuyệt đối trên laptop.

Luồng tích hợp Week 7:

```text
Duy ingestion
  -> Phat PostgreSQL
  -> Lap pgvector retrieval
  -> Tuong prediction logs
  -> Phi/Hung UI
  -> shared CI smoke tests
```

## 2. Trạng thái tích hợp hiện tại

Phat đã cung cấp bằng chứng PostgreSQL Week 7 tại commit:

```text
f4aeb3e2e8ae08b105e09853b5b38ad39681a9ce
```

Kết quả đã xác nhận:

| Thành phần | Giá trị |
| --- | ---: |
| `sources` | 4 |
| `pipeline_runs` | 4 |
| `ingestion_logs` | 4 |
| `documents` | 1 |
| `document_pages` | 36 |
| `structured_records` | 11,524 |
| `document_chunks` | 293 |
| `rag_query_logs` | 1 |
| `prediction_logs` | 10 |
| `v_prediction_review_queue` | 5 |
| Database CI | 10/10 checks passed |

ID ổn định đã xác nhận:

| Source | `source_id` |
| --- | ---: |
| `superstore_sales_csv` | 1 |
| `product_sales_region_excel` | 2 |
| `dummyjson_products_api` | 3 |
| `dataflow_technical_report_pdf` | 4 |

| Document | `document_db_id` |
| --- | ---: |
| `doc_dataflow_technical_report` | 1 |

Giới hạn cần ghi rõ:

```text
database_ids_confirmed = true
current_duy_runs_loaded = false
```

Phat đã nạp một snapshot Duy đầy đủ, nhưng run UUID trong snapshot đó cũ hơn
run UUID mới nhất hiện có ở repo Duy. Vì vậy:

- Có thể dùng `source_id` và `document_db_id` đã xác nhận.
- Không được tuyên bố rằng các run mới nhất đã được nạp vào PostgreSQL.
- Cần chạy lại Duy loader khi PostgreSQL/Docker khả dụng để có current-run proof.

## 3. Quy ước ID bắt buộc

| Field | Ý nghĩa | Quy tắc |
| --- | --- | --- |
| `source_id` | `sources.id` của Phat | integer, resolve bằng `source_name` |
| `source_name` | business key của source | ổn định giữa các module |
| `document_external_id` | document key của Duy | string, ví dụ `doc_dataflow_technical_report` |
| `document_db_id` | `documents.id` của Phat | integer, resolve bằng `document_external_id` |
| `ingestion_run_id` | UUID của một lần ingestion | không bao giờ dùng làm `source_id` |
| DB `document_id` | integer foreign key | dùng `document_db_id`, không dùng string external ID |

Mapping chuẩn:

```text
source_name
  -> sources.name
  -> sources.id
  -> source_id

document_external_id
  -> documents.document_external_id
  -> documents.id
  -> document_db_id

ingestion_run_id
  -> pipeline run UUID
```

## 4. Snapshot output của Duy

| Source | Valid records/pages | Data quality |
| --- | ---: | ---: |
| Superstore CSV | 9,994 | theo run log mới nhất |
| Product Sales Region Excel | 1,500 | theo run log mới nhất |
| DummyJSON API | 30 | theo run log mới nhất |
| DataFlow PDF | 36 pages | 100.0 |

Tổng structured records:

```text
9,994 + 1,500 + 30 = 11,524
```

DataFlow PDF:

```text
document_external_id: doc_dataflow_technical_report
document_db_id: 1
source_id: 4
pages: 36
non-empty pages: 36
characters: 129,028
chunks in Phat proof: 293
```

## 5. Duy -> Phat

### 5.1 Input Duy gửi cho Phat

Run logs và manifests:

```text
DataVision_Duy/logs/ingestion_runs.jsonl
DataVision_Duy/logs/runs/<ingestion_run_id>.json
DataVision_Duy/logs/manifests/<ingestion_run_id>_manifest.json
DataVision_Duy/logs/db_load_dry_run/duy_to_phat_db_load_plan.json
DataVision_Duy/logs/db_load_dry_run/duy_to_phat_db_smoke_plan.json
```

Structured clean outputs:

```text
DataVision_Duy/week2/data/clean/csv/superstore_clean.csv
DataVision_Duy/week2/data/clean/excel/product_sales_region_clean.csv
DataVision_Duy/week2/data/clean/api/dummyjson_products_clean.csv
```

PDF outputs:

```text
DataVision_Duy/outputs/rag_handoff/pdf_metadata.json
DataVision_Duy/outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
DataVision_Duy/outputs/rag_handoff/week7_rag_handoff_manifest.json
```

Loader và mapping:

```text
DataVision_Duy/data_engineering/storage/db_connection.py
DataVision_Duy/data_engineering/storage/postgres_writer.py
DataVision_Duy/scripts/load_ingestion_outputs_to_postgres.py
DataVision_Duy/scripts/week7_build_phat_mapping_summary.py
DataVision_Duy/docs/week7_duy_phat_real_db_loading_result.md
```

### 5.2 Mapping vào bảng Phat

| Phat table | Duy input | Khóa |
| --- | --- | --- |
| `sources` | `source_name`, `source_type` | insert-or-get bằng `source_name` |
| `pipeline_runs` | `run_id`, status, timestamps | idempotent bằng run UUID |
| `ingestion_logs` | counts, paths, hash, DQ fields | FK `source_id` |
| `documents` | PDF metadata, external ID | resolve `documents.id` |
| `document_pages` | JSONL page records | FK integer `documents.id` |
| `structured_records` | CSV/API/Excel clean rows | FK integer `sources.id` |

Insert order:

```text
sources
  -> pipeline_runs
  -> ingestion_logs
  -> documents
  -> document_pages
  -> structured_records
```

### 5.3 Lệnh Duy chạy

Dry-run:

```powershell
python scripts/load_ingestion_outputs_to_postgres.py --dry-run
python scripts/load_ingestion_outputs_to_postgres.py --dry-run --smoke
```

Real smoke load:

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_NAME="datavision_db"
$env:DB_USER="datavision"
$env:DB_PASSWORD="datavision123"
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
```

Full load:

```powershell
python scripts/load_ingestion_outputs_to_postgres.py --write-db
```

Smoke mode phải nạp:

```text
4 sources
4 pipeline runs
4 ingestion logs
1 document
36 document pages
100 structured records
```

Full mode phải nạp:

```text
4 sources
4 or more pipeline runs
4 ingestion logs
1 document
36 document pages
11,524 structured records
```

### 5.4 Output Phat trả cho Duy

Schema, setup và validation:

```text
DataVision_Phat/week7/database/schema/schema_v4_fixed.sql
DataVision_Phat/week7/database/schema/setup_database_v3.sql
DataVision_Phat/week7/database/validation/validation_queries_v3.sql
DataVision_Phat/week7/database/scripts/run_database_setup.py
DataVision_Phat/week7/database/scripts/ci_database_smoke_test.py
```

DB evidence:

```text
DataVision_Phat/week7/database/outputs/db_validation/duy_data_load_counts.json
DataVision_Phat/week7/database/outputs/db_validation/rag_pgvector_counts.json
DataVision_Phat/week7/database/outputs/db_validation/prediction_log_counts.json
DataVision_Phat/week7/database/outputs/dashboard_view_samples/v_source_quality_summary.json
DataVision_Phat/week7/database/outputs/dashboard_view_samples/v_latest_ingestion_runs.json
DataVision_Phat/week7/database/outputs/dashboard_view_samples/v_document_rag_readiness.json
DataVision_Phat/week7/docs/week7_database_ci_smoke_test_result.md
DataVision_Phat/week7/docs/week7_database_setup_runbook.md
```

### 5.5 Duy tạo identity bridge từ output Phat

```powershell
python scripts/week7_build_phat_mapping_summary.py
```

Output:

```text
DataVision_Duy/outputs/phat_handoff/phat_week7_mapping_summary.json
DataVision_Duy/logs/db_load_results/phat_week7_external_database_proof.json
```

Sau đó regenerate các handoff:

```powershell
python scripts/week7_build_rag_handoff_package.py --db-load-result logs/db_load_results/phat_week7_external_database_proof.json
python scripts/week7_build_prediction_payloads.py --db-load-result logs/db_load_results/phat_week7_external_database_proof.json
python scripts/week7_build_ui_fixtures.py --db-load-result logs/db_load_results/phat_week7_external_database_proof.json
```

### 5.6 Acceptance criteria Duy-Phat

- Schema có pgvector, unique source name và `document_external_id`.
- Writer trả lại existing `source_id`, không trả `None`.
- Transaction có commit/rollback rõ ràng.
- Page string ID được resolve sang integer `documents.id`.
- Query-back count đúng smoke/full mode.
- Output proof ghi rõ schema version và ID mapping.
- Snapshot cũ và run mới nhất không bị đánh đồng.

## 6. Duy -> Lap

### 6.1 Input Duy gửi

```text
DataVision_Duy/outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
DataVision_Duy/outputs/rag_handoff/week7_rag_handoff_manifest.json
DataVision_Duy/outputs/rag_handoff/pdf_metadata.json
DataVision_Duy/tests/fixtures/data/sample_dataflow_pages_small.jsonl
```

Mỗi page record có:

```text
document_external_id
document_db_id
source_id
ingestion_run_id
file_name
page_number
text
char_count
word_count
is_empty
```

### 6.2 Output Lap trả

```text
DataVision_Lap/outputs/rag/week7_chunk_insert_summary.json
DataVision_Lap/outputs/rag/week7_pgvector_query_result.json
DataVision_Lap/outputs/rag/week7_rag_query_log_payload.json
DataVision_Lap/outputs/ui_fixtures/lap_rag_response_real.json
DataVision_Lap/docs/week7_duy_to_lap_rag_handoff_validation.md
```

Acceptance:

- 36 pages được đọc, không có page rỗng.
- Resolve `doc_dataflow_technical_report` thành `documents.id=1`.
- Embedding có 384 dimensions.
- Query trả `chunk_id`, page, text, score và citation.
- Có ít nhất một `rag_query_logs` row.

## 7. Duy -> Tuong

### 7.1 Input Duy gửi

```text
DataVision_Duy/outputs/prediction_payloads/tuong_week7_prediction_payloads.json
DataVision_Duy/outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json
DataVision_Duy/outputs/prediction_payloads/week7/*.json
DataVision_Duy/docs/week7_duy_to_tuong_prediction_payload_contract.md
DataVision_Duy/docs/week7_duy_to_tuong_additional_prediction_payloads.md
```

Batch hiện có 20 payload:

- PDF full document và các section thật
- CSV, Excel và API summary/sample
- short text
- empty text
- missing `file_name`
- missing `document_external_id`
- invalid `file_size`
- unknown `file_type`

Payload DataFlow chính có:

```text
source_id: 4
document_external_id: doc_dataflow_technical_report
document_db_id: 1
ingestion_run_id: Duy run UUID
database_identity_status: database_ids_confirmed
current_ingestion_runs_loaded: false
```

### 7.2 Output Tuong trả

```text
DataVision_Tuong/outputs/week7_duy_prediction_results.json
DataVision_Tuong/outputs/db_integration/week7_prediction_log_payloads.json
DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_batch_response.json
DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_review_queue_sample.json
DataVision_Tuong/outputs/rag_metadata/document_type_filter_payload.json
```

Acceptance:

- 20 inputs tạo 20 outputs.
- Một invalid item không dừng cả batch.
- Status chỉ dùng `accepted`, `needs_review`, `waiting_for_source`, `failed`.
- Error result vẫn có cùng response shape.
- Không dùng `ingestion_run_id` làm `source_id`.
- Chỉ document đã tồn tại trong Phat DB mới có `document_db_id`.

## 8. Duy -> Phi/Hung

### 8.1 Input Duy gửi

```text
DataVision_Duy/outputs/ui_fixtures/duy_week7_database_enriched_summary.json
DataVision_Duy/outputs/rag_handoff/week7_rag_handoff_manifest.json
DataVision_Duy/outputs/phat_handoff/phat_week7_mapping_summary.json
DataVision_Duy/docs/week7_duy_to_phi_hung_ui_fixture_contract.md
```

UI fixture có:

```text
total_sources
total_runs
successful_runs
failed_runs
total_records_read
total_records_valid
total_records_invalid
average_data_quality_score
latest_document
database_identity_status
database_schema_version
database_identity_source
current_ingestion_runs_loaded
handoff_paths
runs
```

### 8.2 Output Phi/Hung trả

```text
DataVision_Hung/demo/fixtures/week7/duy_latest_ingestion_summary.json
DataVision_Hung/demo/services/fixture_validator.py
DataVision_Hung/tests/test_week7_fixture_validation.py
DataVision_Hung/scripts/week7_ui_ci_smoke_test.py
DataVision_Hung/docs/week7_ui_ci_smoke_test_result.md
DataVision_Hung/docs/backend_api_contract_for_ui.md
DataVision_Hung/demo/fixtures/week7/phat_dashboard_views_sample.json
DataVision_Hung/demo/fixtures/week7/lap_rag_response_real.json
DataVision_Hung/demo/fixtures/week7/tuong_prediction_batch_response.json
DataVision_Hung/demo/fixtures/week7/tuong_prediction_review_queue_sample.json
```

Acceptance:

- Dashboard mở trực tiếp trong fixture mode.
- UI hiển thị DataFlow IDs, hash, quality và handoff paths.
- `current_ingestion_runs_loaded=false` được hiển thị như limitation, không bị
  trình bày thành lỗi ID.
- Week 7 database-enriched copies preserve `source_id=4`,
  `document_external_id=doc_dataflow_technical_report`,
  `document_db_id=1`, and the relevant `ingestion_run_id`.
- Prediction UI uses exactly `accepted`, `needs_review`, `waiting_for_source`,
  and `failed`; `0.80` is the staging acceptance threshold.
- Phat review-queue rows expose `document_external_id` when the row is tied to
  a document.
- Backend stub không được mô tả là production backend.

The Duy-side read-only audit is:

```powershell
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
```

Evidence paths:

```text
DataVision_Duy/outputs/hung_handoff/hung_week7_mapping_summary.json
DataVision_Duy/logs/hung_handoff/hung_week7_external_proof.json
DataVision_Duy/docs/week7_duy_phi_hung_mapping_result.md
```

At the time of this handoff, the sibling UI tests and smoke test pass, but
the copied Duy/Tuong fixtures still have null database IDs and the UI
contract/refresh script contain legacy rules. The mapping is therefore
`blocked_on_phi_hung_refresh` until Phi/Hung commits the refresh.

## 9. Duy cần nhận gì từ từng thành viên

| Từ | Duy cần nhận | Dùng để làm gì |
| --- | --- | --- |
| Phat | fixed schema, DB credentials, source/document IDs, query counts, CI result | real DB load và identity mapping |
| Lap | page validation, chunk contract, retrieval proof, citation fixture | xác nhận PDF output RAG-ready |
| Tuong | payload validation, prediction outputs, status policy, DB log payload | xác nhận prediction handoff |
| Phi/Hung | fixture validation, final UI fields, CI commands, backend contract | xác nhận UI-ready output |

## 10. Shared CI và Docker

Các file điều phối trong repo Duy:

```text
DataVision_Duy/.github/workflows/ci.yml
DataVision_Duy/docker-compose.db.yml
DataVision_Duy/docker-compose.yml
DataVision_Duy/.env.example
DataVision_Duy/backend_stub/main.py
DataVision_Duy/backend_stub/Dockerfile
DataVision_Duy/integration/shared_repo_manifest.json
DataVision_Duy/scripts/week7_shared_repo_readiness_check.py
DataVision_Duy/scripts/week7_shared_integration_smoke_test.py
```

CI commands theo owner:

| Job | Command |
| --- | --- |
| Data Engineering | `pytest tests/data_tests/ -q` |
| Data smoke | `python scripts/week7_ci_ingestion_smoke_test.py` |
| Database setup | `python week7/database/scripts/run_database_setup.py --smoke --skip-lap` |
| Database smoke | `python week7/database/scripts/ci_database_smoke_test.py` |
| RAG smoke | `python ai/rag/scripts/week7_rag_ci_smoke_test.py` |
| Prediction smoke | `python scripts/week7_prediction_ci_smoke_test.py` |
| UI smoke | `python scripts/week7_ui_ci_smoke_test.py` |

Local contract validation:

```powershell
docker compose -f docker-compose.db.yml config --quiet
docker compose -f docker-compose.yml config --quiet
python scripts/week7_shared_repo_readiness_check.py --strict
python scripts/week7_shared_integration_smoke_test.py
```

`docker compose config` chỉ xác nhận cấu hình. Real runtime proof cần Docker
daemon đang chạy và PostgreSQL reachable.

## 11. Thứ tự integration meeting

1. Phat start PostgreSQL + pgvector và chạy setup.
2. Duy chạy `--dry-run --smoke`.
3. Duy chạy `--write-db --smoke`.
4. Phat query sáu bảng ingestion và trả IDs/counts.
5. Duy regenerate RAG, prediction và UI handoffs.
6. Lap insert chunks, query pgvector và insert RAG log.
7. Tuong predict batch, insert prediction logs và query review queue.
8. Phat export dashboard views mới.
9. Phi/Hung copy fixtures, validate và chạy UI smoke test.
10. Cả team chạy shared integration smoke test.

## 12. Definition of Done

- [x] Duy writer hỗ trợ dry-run, smoke và full mode.
- [x] Phat schema/setup/validation paths đã được map đúng.
- [x] Stable source IDs và DataFlow document DB ID đã được xác nhận.
- [x] Phat full snapshot counts đã được kiểm tra.
- [x] Duy DB-enriched RAG/prediction/UI outputs đã được tạo.
- [x] Readiness checker nhận diện Phat đúng cấu trúc thực tế.
- [x] Shared Docker Compose contracts pass.
- [x] Data tests và Week 7 validators pass.
- [ ] Phi/Hung refreshes DB-enriched fixtures, removes legacy UI contract rules,
  and passes the Duy-side mapping audit.
- [ ] Nạp lại các run UUID mới nhất của Duy vào PostgreSQL.
- [ ] Chạy local Docker runtime end-to-end trong cùng một session.
- [ ] Merge các module vào shared repository và chạy GitHub Actions.

## 13. Lệnh kiểm tra cuối của Duy

```powershell
python scripts/week7_build_phat_mapping_summary.py
python scripts/week7_build_lap_mapping_summary.py --run-lap-tests
python scripts/week7_build_tuong_mapping_summary.py --run-tuong-checks
python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
python scripts/validate_week7.py
python scripts/week7_ci_ingestion_smoke_test.py
python scripts/week7_data_pipeline_smoke_test.py
python scripts/week7_shared_repo_readiness_check.py --strict
python scripts/week7_shared_integration_smoke_test.py
python -m pytest tests/data_tests/ -q
```

Kết quả kỳ vọng:

```text
Phat mapping: passed
Week 7 validation: passed
Ingestion CI smoke: passed
Data pipeline smoke: passed
Shared repo readiness: ready
Shared integration contract smoke: passed
Data tests: 50 passed or more
```

## 14. Lap audit gate

The exact Duy-to-Lap mapping is maintained in:

```text
docs/week7_duy_lap_mapping_result.md
outputs/lap_handoff/lap_week7_mapping_summary.json
logs/lap_handoff/lap_week7_external_proof.json
```

The Duy page contract is currently passed:

```text
36 pages
document_external_id=doc_dataflow_technical_report
source_id=4
document_db_id=1
total_characters=129028
```

The Lap repository still needs execution proof before the whole platform can
be marked end-to-end complete. Its current chunk insert and pgvector query
outputs are `pending_db_connection`, and its unit-test collection is blocked
by an unused `torch` import in `ai/rag/vector_store.py`.

Do not present the DataFlow UI fixture as PostgreSQL proof. Lap must replace
the pending output files after running the real loader and query against
Phat's database. The RAG log must use Phat's `user_query` column, and the
document ID must remain the integer `documents.id`.

## 15. Tuong audit gate

The exact Duy-to-Tuong mapping is maintained in:

```text
docs/week7_duy_tuong_mapping_result.md
outputs/tuong_handoff/tuong_week7_mapping_summary.json
logs/tuong_handoff/tuong_week7_external_proof.json
```

Duy's current batch contains 20 ordered payloads with stable source IDs,
DataFlow `document_db_id=1`, quality metadata, weak-text cases, and normalized
validation cases.

The audited Tuong checkout is not yet aligned with that batch:

```text
Tuong input copy: 10/20
Tuong results: 8/20
Tuong result statuses: 8 needs_review
Tuong prediction-log payloads: 1/20
Tuong DB insert result: missing
Tuong UI fixture IDs: synthetic source_id=100..103
```

Tuong must preserve all lineage fields, return one normalized result and one
DB payload for every input, then save real PostgreSQL insert/query-back proof.
The operational staging threshold is `0.80`; old `0.60` contracts must not be
used to permit automatic RAG filtering.
