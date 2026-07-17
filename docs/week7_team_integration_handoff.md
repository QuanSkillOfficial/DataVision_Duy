# Week 7 Team Integration Handoff

> **Mục đích:** tài liệu này là bản giao nhận kỹ thuật giữa Duy, Phat, Lap,
> Tuong và Phi/Hung. Mỗi phần ghi rõ **ai cung cấp input**, **file ở đâu**,
> **ai nhận**, **output phải trả lại ở đâu**, **lệnh chạy** và **điều kiện
> nghiệm thu**.

- **Owner:** Duy - Data Engineering and CI/CD Data Pipeline Lead
- **Tuần:** Week 7
- **Cập nhật:** 2026-07-18
- **Nguồn dữ liệu chuẩn:** DataFlow PDF, Superstore CSV, Product Sales Region Excel,
  DummyJSON Products API
- **Nguyên tắc:** không đoán `source_id` hoặc `document_db_id`. Chỉ ghi các ID
  này sau khi Phat xác nhận bằng kết quả query PostgreSQL.

---

## 1. Repository và quy ước đường dẫn

### 1.1 Repository của từng thành viên

| Owner | GitHub repository | Local repository convention |
|---|---|---|
| Duy | [DataVision_Duy](https://github.com/QuanSkillOfficial/DataVision_Duy) | `DataVision_Duy/` |
| Phat | [DataVision_Phat](https://github.com/QuanSkillOfficial/DataVision_Phat) | `DataVision_Phat/` |
| Lap | [DataVision_Lap](https://github.com/QuanSkillOfficial/DataVision_Lap) | `DataVision_Lap/` |
| Tuong | [DataVision_Tuong](https://github.com/QuanSkillOfficial/DataVision_Tuong) | `DataVision_Tuong/` |
| Phi/Hung | [DataVision_Hung](https://github.com/QuanSkillOfficial/DataVision_Hung) | `DataVision_Hung/` |

Các đường dẫn trong tài liệu này là **relative path tính từ root của repository
tương ứng**. Ví dụ:

```text
DataVision_Duy/outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
```

Khi gửi file, phải ghi thêm:

```text
producer_repo
producer_commit
generated_at
database_identity_status
```

Lấy commit đang dùng bằng:

```bash
git rev-parse HEAD
```

### 1.2 Hai chế độ phối hợp

**Chế độ repo riêng hiện tại**

- Duy tạo artifact trong `DataVision_Duy/`.
- Người nhận copy hoặc tải đúng artifact sang thư mục input của repo mình.
- Không copy code RAG vào thư mục database của Phat.
- Không copy SQL vào repo ingestion của Duy.
- Không dùng file runtime cục bộ làm source of truth nếu đã có artifact JSON
  hoặc manifest được commit.

**Chế độ shared repo mục tiêu**

- Mỗi module được đặt vào đúng thư mục owner trong shared repo.
- Chỉ giữ một bản code active.
- Handoff vẫn giữ nguyên field name và ID semantics trong tài liệu này.
- CI chạy bằng relative path, không dùng path của laptop cá nhân.

### 1.3 Runtime file và file được commit

Các file sau được tạo lại sau mỗi lần chạy ingestion:

```text
logs/runs/<ingestion_run_id>.json
logs/manifests/<ingestion_run_id>_manifest.json
```

Đây là runtime artifact; một số file có thể bị `.gitignore` để tránh phình
repository. Khi cần Phat dùng đúng run mới nhất, Duy phải:

1. chạy lại ingestion;
2. gửi `logs/ingestion_runs.jsonl` và các file runtime tương ứng trong cùng
   một release/zip hoặc buổi integration;
3. ghi `ingestion_run_id` vào message bàn giao.

Các artifact canonical đã được commit và có thể dùng sau khi clone:

```text
logs/ingestion_runs.jsonl
logs/db_load_dry_run/duy_to_phat_db_load_plan.json
logs/db_load_dry_run/duy_to_phat_db_smoke_plan.json
outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
outputs/rag_handoff/week7_rag_handoff_manifest.json
outputs/rag_handoff/pdf_metadata.json
outputs/prediction_payloads/tuong_week7_prediction_payloads.json
outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json
outputs/prediction_payloads/week7/*.json
outputs/ui_fixtures/duy_week7_database_enriched_summary.json
```

---

## 2. Snapshot dữ liệu hiện tại của Duy

Source of truth cho các số liệu tổng hợp:

```text
outputs/ui_fixtures/duy_week7_database_enriched_summary.json
outputs/rag_handoff/week7_rag_handoff_manifest.json
logs/ingestion_runs.jsonl
```

Snapshot hiện tại:

| Metric | Value |
|---|---:|
| Sources | 4 |
| Successful runs | 4 |
| Failed runs | 0 |
| Records read | 11,524 |
| Valid records | 11,524 |
| Invalid records | 0 |
| PDF pages | 36 |
| Non-empty PDF pages | 36 |
| Empty PDF pages | 0 |
| PDF characters | 129,028 |
| PDF words | 17,536 |
| Average data quality score | 99.63 |
| Prediction payloads | 20 |
| Database identity status | `pending_database_load` |
| Data tests | 46 passed in the latest local run |

### 2.1 Bốn run hiện tại

Các UUID là giá trị của snapshot hiện tại, không hard-code vào code. Sau khi
chạy ingestion lại, phải đọc UUID mới từ `logs/ingestion_runs.jsonl` hoặc
`duy_week7_database_enriched_summary.json`.

| Source | Type | Records | Data quality | `ingestion_run_id` hiện tại |
|---|---|---:|---:|---|
| `superstore_sales_csv` | `csv` | 9,994 | 100.00 | `0a11e66b-59c8-4259-9759-d36589423758` |
| `product_sales_region_excel` | `excel` | 1,500 | 99.51 | `797e7ee4-9139-4157-b6b4-cb3c325ce469` |
| `dummyjson_products_api` | `api` | 30 | 99.00 | `7fb106e1-c920-4e92-b3c8-47402ee94ea5` |
| `dataflow_technical_report_pdf` | `pdf` | 36 pages | 100.00 | `4c595851-c11e-48e3-8c79-69f6fa52d282` |

### 2.2 Database status hiện tại

Hiện tại Duy mới có contract và dry-run plan. Các field sau đang cố ý để
`null`:

```json
{
  "source_id": null,
  "document_db_id": null,
  "database_identity_status": "pending_database_load"
}
```

Sau khi Phat load thành công, Phat phải trả về ID thật. Duy sẽ cập nhật lại
DB-enriched artifacts; không tự đặt `source_id = 4` hoặc `document_db_id = 1`
chỉ vì đó là giá trị trong ví dụ.

---

## 3. ID standard dùng chung

| Field | Kiểu | Ý nghĩa | Ai cấp |
|---|---|---|---|
| `source_id` | integer hoặc null | khóa nội bộ của `sources.id` | Phat |
| `source_name` | string | tên business ổn định của source | Duy |
| `source_type` | enum/string | `csv`, `excel`, `api`, `pdf` | Duy |
| `document_external_id` | string | ID document ổn định giữa các module | Duy |
| `document_db_id` | integer hoặc null | alias ở payload; map tới `documents.id` | Phat |
| `documents.id` | integer | FK nội bộ trong PostgreSQL | Phat |
| `ingestion_run_id` | UUID/string | ID một lần chạy ingestion | Duy |
| `pipeline_run_id` | integer/UUID theo schema | ID run trong `pipeline_runs` | Phat |
| `chunk_id` | string | ID chunk ổn định, có page và index | Lap |

Mapping bắt buộc:

```text
source_name
  -> sources.name
  -> sources.id = source_id

document_external_id
  -> documents.document_external_id
  -> documents.id = document_db_id

document_db_id
  -> document_pages.document_id
  -> document_chunks.document_id
  -> prediction_logs.document_id
  -> rag_query_logs.document_id
```

Không được làm:

```text
ingestion_run_id -> source_id
document_external_id string -> integer document_id
document_db_id -> ingestion_run_id
```

### 3.1 Status chuẩn

Prediction status chỉ dùng:

```text
accepted
needs_review
waiting_for_source
failed
```

Không dùng `rejected` trong payload mới.

---

## 4. Luồng integration Week 7

```text
Duy raw inputs
  -> ingestion engine
  -> raw/staging/clean outputs
  -> logs, manifests, data quality
  -> Phat PostgreSQL
  -> DB-enriched IDs
       -> Lap chunking + 384-dim embeddings + pgvector retrieval
       -> Tuong prediction + prediction_logs + review queue
       -> Phi/Hung dashboard, chatbot, suggestions, reports
  -> shared CI smoke tests
  -> Docker/local integration
```

Thứ tự chạy đề nghị:

1. Duy chạy ingestion và tạo artifact.
2. Duy gửi artifact cho Phat.
3. Phat setup database, load smoke mode, trả table counts và IDs.
4. Duy cập nhật handoff JSONL/payload với IDs thật.
5. Lap dùng JSONL DB-enriched để insert và query pgvector.
6. Tuong dùng prediction payload DB-enriched để tạo prediction logs.
7. Phat query review queue và RAG views.
8. Phi/Hung nhận các fixture mới và chạy UI validation.
9. Duy + Phi/Hung ghép các job vào GitHub Actions.

---

## 5. Duy -> Phat: PostgreSQL integration

### 5.1 Input Duy gửi cho Phat

| Duy source path | Nội dung | Phat dùng cho |
|---|---|---|
| `logs/ingestion_runs.jsonl` | lịch sử các run | kiểm tra 4 source và status |
| `logs/runs/<run_id>.json` | run detail mới nhất | load `pipeline_runs`, `ingestion_logs` |
| `logs/manifests/<run_id>_manifest.json` | SHA256 và output paths | file provenance |
| `week2/data/clean/csv/superstore_clean.csv` | 9,994 rows | `structured_records` |
| `week2/data/clean/excel/product_sales_region_clean.csv` | 1,500 rows | `structured_records` |
| `week2/data/clean/api/dummyjson_products_clean.csv` | 30 rows | `structured_records` |
| `outputs/rag_handoff/pdf_metadata.json` | PDF metadata | `documents` |
| `outputs/rag_handoff/week7_document_pages_db_enriched.jsonl` | 36 page records | `document_pages` |
| `logs/db_load_dry_run/duy_to_phat_db_load_plan.json` | full insert plan | kiểm tra trước khi write |
| `logs/db_load_dry_run/duy_to_phat_db_smoke_plan.json` | giới hạn 100 records | CI/smoke mode |
| `data_engineering/storage/postgres_writer.py` | writer implementation | Duy chạy loader; Phat review contract |
| `scripts/load_ingestion_outputs_to_postgres.py` | loader | write/dry-run/smoke |

Nếu Phat clone repository mới, các file clean CSV, PDF handoff và plan ở trên
là source of truth. Các runtime log không có trong clone phải được Duy tạo lại
bằng lệnh ingestion trước buổi integration.

### 5.2 Mapping vào bảng Phat

| Duy field | Phat table.column | Ghi chú |
|---|---|---|
| `source_name` | `sources.name` | unique; insert-or-get |
| `source_type` | `sources.source_type` | enum/string theo schema |
| `file_hash_sha256` | `sources.file_hash_sha256` hoặc provenance column | không đổi sau khi load |
| `ingestion_run_id` | `ingestion_logs.run_id` hoặc metadata | không dùng làm `source_id` |
| `status` | `pipeline_runs.status`, `ingestion_logs.status` | `success`/`failed` theo schema |
| `records_read` | `ingestion_logs.records_read` | số record/page đọc |
| `records_valid` | `ingestion_logs.records_valid` | số record hợp lệ |
| `records_invalid` | `ingestion_logs.records_invalid` | số record lỗi |
| `data_quality_score` | `ingestion_logs.data_quality_score` | numeric 0-100 |
| `raw_output_path` | `ingestion_logs.raw_output_path` | relative path |
| `staging_output_path` | `ingestion_logs.staging_output_path` | relative path |
| `clean_output_path` | `ingestion_logs.clean_output_path` | relative path |
| `document_external_id` | `documents.document_external_id` | unique business key |
| `file_name` | `documents.file_name` | PDF metadata |
| page `page_number` | `document_pages.page_number` | bắt đầu từ 1 |
| page `text` | `document_pages.page_text`/`text` | theo schema cuối của Phat |
| clean row | `structured_records.record_data`/JSONB | theo schema cuối của Phat |

Insert order bắt buộc:

```text
sources
  -> pipeline_runs
  -> ingestion_logs
  -> documents
  -> document_pages
  -> structured_records
```

### 5.3 Lệnh Duy chạy

Từ root `DataVision_Duy`:

```bash
# Kiểm tra plan, không chạm database
python scripts/load_ingestion_outputs_to_postgres.py --dry-run

# Dùng database local của Phat, chỉ load 100 structured records
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke

# Load đầy đủ 11,524 structured records
python scripts/load_ingestion_outputs_to_postgres.py --write-db
```

Environment variables:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=datavision_db
DB_USER=datavision
DB_PASSWORD=datavision123
```

Phat setup trước:

```bash
docker compose -f docker-compose.db.yml up -d
python week7/database/run_database_setup.py
```

Tên script setup có thể là script tương đương trong repo Phat; Phat phải gửi
lại command chính xác trước khi Duy chạy `--write-db`.

### 5.4 Output Phat phải trả cho Duy

Phat gửi các file sau:

```text
DataVision_Phat/week7/outputs/db_validation/duy_data_load_counts.json
DataVision_Phat/docs/week7_duy_phat_real_database_load_result.md
DataVision_Phat/week7/outputs/db_validation/duy_document_identity.json
```

Nếu repo Phat chưa có thư mục Week 7, dùng tạm:

```text
DataVision_Phat/week6/outputs/ingestion_data/
DataVision_Phat/week6/docs/duy_phat_db_integration_result.md
```

Payload response tối thiểu:

```json
{
  "status": "passed",
  "schema_version": "schema_v4_fixed",
  "counts": {
    "sources": 4,
    "pipeline_runs": 4,
    "ingestion_logs": 4,
    "documents": 1,
    "document_pages": 36,
    "structured_records": 100
  },
  "identities": {
    "dataflow_source_id": 4,
    "dataflow_document_db_id": 1,
    "dataflow_document_external_id": "doc_dataflow_technical_report"
  },
  "database_identity_status": "confirmed"
}
```

Giá trị `4` và `1` ở trên chỉ là ví dụ. Duy chỉ cập nhật artifact bằng giá trị
Phat query trả về.

### 5.5 Acceptance criteria Duy + Phat

- [ ] Database start từ zero bằng Docker.
- [ ] pgvector extension enabled.
- [ ] Schema và views chạy không manual patch.
- [ ] `sources` có 4 rows.
- [ ] `pipeline_runs` có ít nhất 4 rows.
- [ ] `ingestion_logs` có 4 rows.
- [ ] `documents` có 1 DataFlow document.
- [ ] `document_pages` có 36 rows.
- [ ] Smoke mode có 100 structured records; full mode có 11,524.
- [ ] Query trả được `source_id` và `document_db_id` thật.
- [ ] Không có orphan document page.

---

## 6. Duy -> Lap: RAG và pgvector handoff

### 6.1 Input Duy gửi cho Lap

| Duy source path | Lap destination đề nghị | Nội dung |
|---|---|---|
| `outputs/rag_handoff/week7_document_pages_db_enriched.jsonl` | `DataVision_Lap/outputs/rag_handoff/week7_document_pages_db_enriched.jsonl` | page-level text |
| `outputs/rag_handoff/week7_rag_handoff_manifest.json` | `DataVision_Lap/outputs/rag_handoff/week7_rag_handoff_manifest.json` | counts, IDs, hash |
| `outputs/rag_handoff/pdf_metadata.json` | `DataVision_Lap/outputs/rag_handoff/pdf_metadata.json` | file metadata |
| `outputs/rag_handoff/rag_handoff_summary.md` | `DataVision_Lap/docs/duy_rag_handoff_summary.md` | human-readable summary |
| `tests/fixtures/data/sample_dataflow_pages_small.jsonl` | `DataVision_Lap/tests/fixtures/data/sample_dataflow_pages_small.jsonl` | CI smoke input |

Nếu database chưa load xong, các field DB có thể là `null`. Lap không được
insert chunk với `document_id = null`; phải chờ Phat xác nhận ID hoặc chạy
in-memory CI smoke mode.

### 6.2 Schema mỗi page record

```json
{
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": 1,
  "source_id": 4,
  "ingestion_run_id": "uuid-from-duy",
  "file_name": "DataFlow_Technical_Report.pdf",
  "page_number": 1,
  "text": "page text",
  "char_count": 3500,
  "word_count": 520,
  "is_empty": false
}
```

`document_db_id` và `source_id` chỉ có giá trị sau Phat DB loading. `page_number`,
`text`, `char_count` và `word_count` phải có ngay từ Duy.

### 6.3 Lệnh Lap chạy

```bash
python -m ai.rag.load_document_pages_to_pgvector ^
  --document-pages outputs/rag_handoff/week7_document_pages_db_enriched.jsonl ^
  --document-external-id doc_dataflow_technical_report

python ai/rag/scripts/week7_pgvector_smoke_test.py ^
  --query "What is the DataFlow pipeline?" ^
  --document-external-id doc_dataflow_technical_report ^
  --top-k 5
```

Trên Linux/macOS, thay dấu `^` bằng `\`.

### 6.4 Output Lap phải trả cho Duy/Phat/Phi-Hung

```text
DataVision_Lap/outputs/rag/week7_chunk_insert_summary.json
DataVision_Lap/outputs/rag/week7_pgvector_query_result.json
DataVision_Lap/outputs/rag/week7_rag_query_log_payload.json
DataVision_Lap/outputs/ui_fixtures/lap_rag_response_real.json
DataVision_Lap/docs/week7_lap_phat_pgvector_integration_result.md
```

Kết quả tối thiểu:

```json
{
  "status": "passed",
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": 1,
  "embedding_dimension": 384,
  "chunks_inserted": 293,
  "top_k": 5,
  "results": [
    {
      "chunk_id": "doc_dataflow_technical_report_page_4_chunk_000",
      "page_number": 4,
      "similarity_score": 0.84,
      "citation": "DataFlow_Technical_Report.pdf, page 4"
    }
  ]
}
```

### 6.5 Acceptance criteria Duy + Lap

- [ ] Lap đọc đúng 36 pages từ artifact của Duy.
- [ ] `document_external_id` giữ nguyên.
- [ ] Không insert string external ID vào integer FK.
- [ ] Chunk embedding có dimension 384.
- [ ] Query trả `chunk_id`, `page_number`, `similarity_score`.
- [ ] Citation có file name và page number.
- [ ] Có ít nhất một `rag_query_logs` row ở Phat DB.
- [ ] `v_rag_daily_metrics` không rỗng sau query log.
- [ ] Fixture UI không còn vendor/refund-policy example cũ.

---

## 7. Duy -> Tuong: prediction handoff

### 7.1 Input Duy gửi cho Tuong

| Duy source path | Tuong destination đề nghị | Mục đích |
|---|---|---|
| `outputs/prediction_payloads/tuong_week7_prediction_payloads.json` | `DataVision_Tuong/outputs/prediction_payloads/tuong_week7_prediction_payloads.json` | 20 test cases chuẩn |
| `outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json` | `DataVision_Tuong/outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json` | payload bổ sung |
| `outputs/prediction_payloads/week7/*.json` | `DataVision_Tuong/outputs/prediction_payloads/week7/` | debug từng case |
| `logs/prediction_payloads/duy_pdf_prediction_payload.json` | Tuong archive/input | full PDF baseline |
| `docs/week7_duy_to_tuong_prediction_payload_contract.md` | `DataVision_Tuong/docs/` | contract và validation |

### 7.2 Field contract

Payload đầy đủ:

```json
{
  "source_id": null,
  "source_name": "dataflow_technical_report_pdf",
  "document_external_id": "doc_dataflow_technical_report",
  "document_db_id": null,
  "ingestion_run_id": "uuid-from-duy",
  "file_name": "DataFlow_Technical_Report.pdf",
  "file_type": "pdf",
  "file_size": 2857707,
  "extracted_text": "text from Duy",
  "text_length": 129028,
  "page_range": "1-36",
  "num_pages": 36,
  "source_system": "manual_upload",
  "data_quality_score": 100.0,
  "file_hash_sha256": "sha256",
  "parsing_status": "ready"
}
```

20 cases hiện có:

| Case group | File |
|---|---|
| Full PDF | `01_doc_dataflow_technical_report.json` |
| Intro/architecture/related work | `02` đến `04` |
| CSV/Excel/API summaries | `05` đến `07` |
| Short/empty/invalid quality gates | `08` đến `10` |
| DataFlow section samples | `11` đến `14`, `18` |
| Structured-data samples | `15` đến `17` |
| Missing external ID / invalid file size | `19` đến `20` |

Các file đầy đủ nằm tại:

```text
outputs/prediction_payloads/week7/
```

### 7.3 Lệnh và output Tuong

Tuong chạy theo script chính thức của repo Tuong; command cần thống nhất là:

```bash
python scripts/run_week7_duy_payloads.py ^
  --input outputs/prediction_payloads/tuong_week7_prediction_payloads.json ^
  --output outputs/week7_duy_prediction_results.json
```

Nếu script thực tế có tên khác, Tuong phải ghi command thực tế trong result
document, không đổi input contract.

Tuong trả về:

```text
DataVision_Tuong/outputs/week7_duy_prediction_results.json
DataVision_Tuong/outputs/db_integration/week7_prediction_log_payloads.json
DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_batch_response.json
DataVision_Tuong/outputs/ui_fixtures/tuong_prediction_review_queue_sample.json
DataVision_Tuong/outputs/rag_metadata/document_type_filter_payload.json
DataVision_Tuong/docs/week7_tuong_phat_prediction_db_insert_result.md
```

Mỗi result phải có:

```json
{
  "source_id": 4,
  "document_id": 1,
  "document_external_id": "doc_dataflow_technical_report",
  "ingestion_run_id": "uuid-from-duy",
  "predicted_document_type": "report",
  "confidence": 0.72,
  "status": "needs_review",
  "review_reason": "Confidence below staging threshold",
  "top_predictions": [],
  "manual_review_required": true,
  "model_name": "document_type_classifier",
  "model_version": "document_classifier_v1"
}
```

`document_id` trong DB payload là `documents.id` do Phat cấp; không ghi
`document_external_id` vào cột integer.

### 7.4 Acceptance criteria Duy + Tuong

- [ ] Tuong nhận đủ 20 payloads hoặc ghi rõ case nào bị loại và lý do.
- [ ] `source_id` khác semantics với `ingestion_run_id`.
- [ ] Missing/short text trả `waiting_for_source`.
- [ ] Validation error trả `failed` với cùng response shape.
- [ ] Status chỉ là `accepted`, `needs_review`, `waiting_for_source`, `failed`.
- [ ] Prediction log payload có `document_id`, `source_id`, `ingestion_run_id`.
- [ ] Low-confidence prediction đi vào review queue.
- [ ] RAG filter metadata mặc định `use_for_rag_filtering: false`.
- [ ] Tuong cung cấp command và test result để Duy/Phi-Hung thêm vào CI.

---

## 8. Duy -> Phi/Hung: UI, dashboard và fixture

### 8.1 Input Duy gửi cho Phi/Hung

| Duy source path | Hung destination hiện có/đề nghị | UI sử dụng |
|---|---|---|
| `outputs/ui_fixtures/duy_week7_database_enriched_summary.json` | `DataVision_Hung/demo/fixtures/week7/duy_latest_ingestion_summary.json` | dashboard |
| `outputs/ui_fixtures/duy_data_quality_summary.json` | `DataVision_Hung/demo/fixtures/week7/duy_data_quality_summary.json` | data quality |
| `outputs/ui_fixtures/duy_pdf_document_summary.json` | `DataVision_Hung/demo/fixtures/week7/duy_pdf_document_summary.json` | document/RAG readiness |
| Phat `week7/outputs/dashboard_view_samples/*.json` | `DataVision_Hung/demo/fixtures/week7/phat_dashboard_views_sample.json` | cards/tables |
| Lap `outputs/ui_fixtures/lap_rag_response_real.json` | `DataVision_Hung/demo/fixtures/week7/lap_rag_response_real.json` | chatbot/citation |
| Tuong `outputs/ui_fixtures/tuong_prediction_batch_response.json` | `DataVision_Hung/demo/fixtures/week7/tuong_prediction_batch_response.json` | prediction page |
| Tuong review queue fixture | `DataVision_Hung/demo/fixtures/week7/tuong_prediction_review_queue_sample.json` | manual review |

Hung hiện có các fixture Week 6 ở `demo/fixtures/`. Khi chuyển sang Week 7,
không overwrite mù; đặt bản mới trong `demo/fixtures/week7/` và cập nhật
`service_client` trỏ vào bản mới.

### 8.2 Schema Duy UI fixture

```json
{
  "total_sources": 4,
  "total_runs": 4,
  "successful_runs": 4,
  "failed_runs": 0,
  "total_records_read": 11524,
  "total_records_valid": 11524,
  "average_data_quality_score": 99.63,
  "latest_document": {
    "source_id": 4,
    "document_db_id": 1,
    "document_external_id": "doc_dataflow_technical_report",
    "ingestion_run_id": "uuid-from-duy",
    "file_name": "DataFlow_Technical_Report.pdf",
    "page_count": 36,
    "file_hash_sha256": "sha256",
    "parsing_status": "ready"
  },
  "handoff_paths": {
    "rag_handoff": "outputs/rag_handoff/week7_document_pages_db_enriched.jsonl",
    "prediction_payloads": "outputs/prediction_payloads/tuong_week7_prediction_payloads.json"
  },
  "database_identity_status": "confirmed"
}
```

Trước database loading, `source_id` và `document_db_id` phải là `null` và
`database_identity_status` là `pending_database_load`.

### 8.3 Output Phi/Hung phải trả

```text
DataVision_Hung/demo/fixtures/week7/*.json
DataVision_Hung/tests/test_week7_fixture_validation.py
DataVision_Hung/scripts/week7_ui_ci_smoke_test.py
DataVision_Hung/docs/week7_fixture_update_summary.md
DataVision_Hung/docs/week7_ui_ci_smoke_test_result.md
DataVision_Hung/screenshots/week7_staging_ready_ui/
```

UI phải hiển thị:

- tổng source, run thành công, record count;
- data quality score và file hash;
- DataFlow document ID và RAG readiness;
- prediction status và `review_reason`;
- retrieved chunk, page, similarity score và citation;
- suggestion có `source_module` và evidence;
- report vẫn chạy khi không có suggestion.

### 8.4 Acceptance criteria Duy + Phi/Hung

- [ ] Dashboard chạy trực tiếp ở fixture mode, không cần mở Upload trước.
- [ ] UI không hiển thị `rejected` cho payload mới.
- [ ] UI phân biệt `accepted`, `needs_review`, `waiting_for_source`, `failed`.
- [ ] RAG fixture dùng DataFlow PDF, không dùng vendor/refund-policy fixture cũ.
- [ ] Tất cả fixture được validate trước khi render.
- [ ] `python scripts/week7_ui_ci_smoke_test.py` chạy pass.
- [ ] Streamlit import không crash.

---

## 9. Shared CI, Docker và backend stub

### 9.1 Files Duy cung cấp cho CI/CD leads

```text
requirements.txt
scripts/week7_ci_ingestion_smoke_test.py
scripts/week7_shared_repo_readiness_check.py
scripts/week7_local_docker_integration_smoke_test.py
tests/data_tests/
tests/fixtures/data/
docker-compose.db.yml
docker-compose.yml
.env.example
docs/week7_duy_ci_commands.md
docs/week7_data_pipeline_runbook.md
```

### 9.2 Commands đề nghị trong GitHub Actions

```yaml
- name: Install dependencies
  run: pip install -r requirements.txt

- name: Run ingestion CI smoke test
  run: python scripts/week7_ci_ingestion_smoke_test.py

- name: Run data tests
  run: pytest tests/data_tests/ -q

- name: Validate shared structure
  run: python scripts/week7_shared_repo_readiness_check.py
```

Các job của thành viên khác:

| Job | Owner | Command |
|---|---|---|
| `data-engineering-ci` | Duy | `pytest tests/data_tests/` |
| `database-ci` | Phat | `bash week7/database/ci_database_smoke_test.sh` |
| `rag-ci` | Lap | `pytest ai/ai_tests/` và `python ai/rag/scripts/week7_rag_ci_smoke_test.py` |
| `prediction-ci` | Tuong | `pytest tests/ai_tests/` và `python scripts/week7_prediction_ci_smoke_test.py` |
| `ui-ci` | Phi/Hung | `pytest tests/` và `python scripts/week7_ui_ci_smoke_test.py` |
| `integration-smoke-ci` | Duy + Phi/Hung | `python scripts/week7_local_docker_integration_smoke_test.py` |

### 9.3 Docker và backend

Các file nền tảng hiện có trong repo Duy:

```text
docker-compose.db.yml
docker-compose.yml
.env.example
backend_stub/main.py
backend_stub/Dockerfile
backend_stub/requirements.txt
deployment/
```

`docker-compose.db.yml` dùng cho PostgreSQL + pgvector. `docker-compose.yml`
là draft cho full app, chưa được coi là staging production. `backend_stub/main.py`
chỉ dùng để kiểm tra API envelope và service-client mode.

Không commit password production. Chỉ commit giá trị local/demo trong
`.env.example`.

---

## 10. Chuỗi lệnh demo end-to-end

### 10.1 Duy: tạo dữ liệu

```bash
python -m data_engineering.pipelines.ingestion_engine --all
python scripts/week7_build_rag_handoff_package.py
python scripts/week7_build_prediction_payloads.py
python scripts/week7_build_ui_fixtures.py
python scripts/week7_ci_ingestion_smoke_test.py
pytest tests/data_tests/ -q
```

Kiểm tra các output:

```text
outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
outputs/rag_handoff/week7_rag_handoff_manifest.json
outputs/prediction_payloads/tuong_week7_prediction_payloads.json
outputs/ui_fixtures/duy_week7_database_enriched_summary.json
```

### 10.2 Phat: database

```bash
docker compose -f docker-compose.db.yml up -d
python week7/database/run_database_setup.py
python scripts/load_ingestion_outputs_to_postgres.py --write-db --smoke
python week7/database/ci_database_smoke_test.py
```

Phat gửi lại table counts, IDs, validation result và dashboard samples.

### 10.3 Lap: RAG

```bash
python -m ai.rag.load_document_pages_to_pgvector ^
  --document-pages outputs/rag_handoff/week7_document_pages_db_enriched.jsonl ^
  --document-external-id doc_dataflow_technical_report

python ai/rag/scripts/week7_pgvector_smoke_test.py ^
  --query "What is the DataFlow pipeline?" ^
  --document-external-id doc_dataflow_technical_report ^
  --top-k 5
```

### 10.4 Tuong: prediction

```bash
python scripts/run_week7_duy_payloads.py ^
  --input outputs/prediction_payloads/tuong_week7_prediction_payloads.json ^
  --output outputs/week7_duy_prediction_results.json

python scripts/week7_prediction_ci_smoke_test.py
```

### 10.5 Phi/Hung: UI

```bash
python scripts/week7_ui_ci_smoke_test.py
streamlit run demo/streamlit_app.py
```

---

## 11. Output phải trả theo từng cặp làm việc

| Cặp | Duy cung cấp | Người kia trả lại | Bằng chứng hoàn thành |
|---|---|---|---|
| Duy + Phat | logs, clean data, PDF pages, dry-run plan | counts JSON, source/document IDs, DB result | SQL counts và validation pass |
| Duy + Lap | DB-enriched JSONL, manifest, PDF metadata | chunk insert, retrieval, RAG log, UI fixture | top-k có page/chunk/score/citation |
| Duy + Tuong | 20 payloads với ID semantics rõ | prediction results, DB log payloads, review queue, RAG metadata | đủ 4 statuses và không drop failed |
| Duy + Phi/Hung | ingestion summary, data quality, paths, hash | validated Week 7 fixtures, UI smoke result, screenshots | dashboard/chatbot/prediction/report chạy |
| Duy + CI leads | smoke test, fixtures, compose, env example | merged `ci.yml` và job result | CI chạy không dùng laptop path |

---

## 12. Việc mỗi người cần xác nhận trong buổi integration

### Phat phải xác nhận

```text
1. schema version đang dùng
2. command setup/reset từ zero
3. DB credentials local
4. final column names cho sources/documents/ingestion_logs
5. source_id của dataflow source
6. documents.id của DataFlow document
7. smoke/full table counts
8. validation query result
9. dashboard sample paths
```

### Lap phải xác nhận

```text
1. page schema được chấp nhận
2. chunk_id format
3. embedding dimension = 384
4. document_db_id đã resolve
5. chunk insert count
6. top-k retrieval result
7. rag_query_logs insert result
8. RAG UI fixture path
```

### Tuong phải xác nhận

```text
1. 20 payloads đã được đọc
2. threshold và status policy
3. prediction_logs column mapping
4. document_id dùng documents.id
5. DB insert payload path
6. review queue output
7. safe RAG filter metadata
8. CI command
```

### Phi/Hung phải xác nhận

```text
1. fixture paths đã đổi sang Week 7
2. dashboard không phụ thuộc Upload state
3. prediction status badge đã chuẩn hóa
4. DataFlow citation hiển thị đúng
5. suggestion/report dùng evidence thật
6. backend stub và error envelope
7. UI smoke test
8. screenshot paths
```

---

## 13. Definition of Done cho mapping Week 7

### Duy

- [ ] Ingestion chạy 4 source bằng config.
- [ ] Có raw/staging/clean output, run history, manifest và data quality.
- [ ] Có DB dry-run, smoke write và full write mode.
- [ ] Có RAG handoff DB-enriched.
- [ ] Có 20 prediction payloads.
- [ ] Có UI fixture cho Phi/Hung.
- [ ] Có data tests và ingestion CI smoke test.

### Phat

- [ ] Database reproducible từ zero.
- [ ] Docker PostgreSQL + pgvector chạy được.
- [ ] Duy data load vào 6 bảng chính.
- [ ] Có ID mapping thật.
- [ ] Có validation queries và dashboard view samples.
- [ ] Có database CI smoke test.

### Lap

- [ ] Đọc Duy JSONL.
- [ ] Insert chunk vào `document_chunks`.
- [ ] Retrieval pgvector chạy với vector 384 chiều.
- [ ] Có citation-ready response.
- [ ] Có `rag_query_logs`.
- [ ] Có RAG CI smoke test.

### Tuong

- [ ] Prediction chạy trên payloads của Duy.
- [ ] Status policy staging-safe.
- [ ] Prediction logs insert được vào Phat.
- [ ] Review queue có low-confidence rows.
- [ ] RAG metadata là soft filter mặc định.
- [ ] Có prediction CI smoke test và feedback contract.

### Phi/Hung

- [ ] Fixture mode chạy độc lập.
- [ ] Dashboard dùng Duy/Phat values.
- [ ] Prediction page có manual review.
- [ ] Chatbot hiển thị DataFlow citations.
- [ ] Suggestions/reports có cross-module evidence.
- [ ] Backend stub, UI smoke test và screenshots hoàn tất.

### Toàn team

- [ ] `source_id`, `document_external_id`, `document_db_id`,
  `ingestion_run_id` không bị dùng lẫn.
- [ ] Không còn `rejected` trong contract mới.
- [ ] Không có hard-coded laptop path.
- [ ] Không dùng fake DB success để thay cho DB proof.
- [ ] Shared CI draft có data, database, RAG, prediction, UI và integration jobs.
- [ ] Docker/local integration chạy được hoặc ghi rõ blocker có owner và deadline.

---

## 14. Copy-ready messages gửi cho team

### Gửi Phat

```text
Duy đã chuẩn bị input cho DB integration:
- logs/ingestion_runs.jsonl
- logs/db_load_dry_run/duy_to_phat_db_load_plan.json
- logs/db_load_dry_run/duy_to_phat_db_smoke_plan.json
- week2/data/clean/csv/superstore_clean.csv
- week2/data/clean/excel/product_sales_region_clean.csv
- week2/data/clean/api/dummyjson_products_clean.csv
- outputs/rag_handoff/pdf_metadata.json
- outputs/rag_handoff/week7_document_pages_db_enriched.jsonl

Nhờ Phat trả:
- table counts smoke/full
- source_id và documents.id của DataFlow
- schema/setup/validation result
- week7/outputs/db_validation/duy_data_load_counts.json

Không map ingestion_run_id thành source_id và không map document_external_id
trực tiếp vào integer document_id.
```

### Gửi Lap

```text
Duy đã chuẩn bị:
- outputs/rag_handoff/week7_document_pages_db_enriched.jsonl
- outputs/rag_handoff/week7_rag_handoff_manifest.json
- outputs/rag_handoff/pdf_metadata.json
- tests/fixtures/data/sample_dataflow_pages_small.jsonl

Sau khi Phat trả document_db_id, hãy trả:
- outputs/rag/week7_chunk_insert_summary.json
- outputs/rag/week7_pgvector_query_result.json
- outputs/rag/week7_rag_query_log_payload.json
- outputs/ui_fixtures/lap_rag_response_real.json
```

### Gửi Tuong

```text
Duy đã chuẩn bị 20 payloads tại:
outputs/prediction_payloads/tuong_week7_prediction_payloads.json
và outputs/prediction_payloads/week7/

Hãy validate source_id/document_external_id/document_db_id/
ingestion_run_id, chạy staging-safe policy, rồi trả:
- outputs/week7_duy_prediction_results.json
- outputs/db_integration/week7_prediction_log_payloads.json
- outputs/ui_fixtures/tuong_prediction_batch_response.json
- outputs/ui_fixtures/tuong_prediction_review_queue_sample.json
- outputs/rag_metadata/document_type_filter_payload.json
```

### Gửi Phi/Hung

```text
Duy gửi ingestion fixture:
outputs/ui_fixtures/duy_week7_database_enriched_summary.json

Hãy merge cùng output của Phat, Lap và Tuong vào:
demo/fixtures/week7/

UI cần trả:
- fixture validation result
- dashboard/prediction/chatbot/suggestion/report smoke result
- screenshots/week7_staging_ready_ui/
- docs/week7_ui_ci_smoke_test_result.md
```

---

## 15. Current status và blocker

| Area | Status | Next owner action |
|---|---|---|
| Duy ingestion | Ready | chạy lại khi cần snapshot mới |
| Duy manifests/run history | Ready | gửi runtime logs nếu Phat cần UUID mới |
| Duy DB dry-run | Ready | chờ database thật |
| Phat DB loading | Pending confirmation | trả counts và IDs thật |
| Lap pgvector | Pending DB IDs | chạy sau khi Phat confirm schema/ID |
| Tuong prediction | Payload ready | chạy 20 cases và trả DB/UI artifacts |
| Phi/Hung UI | Fixture source ready | đổi sang `demo/fixtures/week7/` |
| Shared CI | Draft ready | ghép các job của từng owner |
| Docker full app | Draft | local integration test và ghi blocker nếu có |

**Blocker hiện tại quan trọng nhất:** `source_id` và `document_db_id` chưa được
Phat xác nhận từ PostgreSQL. Vì vậy các downstream team có thể kiểm tra
contract/in-memory mode, nhưng không được báo cáo là đã hoàn tất real DB
integration cho đến khi có SQL proof.

---

## 16. Single source of truth

Khi có nhiều file hoặc nhiều snapshot khác nhau, ưu tiên theo thứ tự:

1. output JSON có `schema_version` và `generated_at` mới nhất;
2. `outputs/ui_fixtures/duy_week7_database_enriched_summary.json`;
3. `outputs/rag_handoff/week7_rag_handoff_manifest.json`;
4. `logs/ingestion_runs.jsonl`;
5. runtime file trong `logs/runs/` và `logs/manifests/`;
6. notebook, screenshot hoặc message cũ.

Mọi thay đổi contract phải được ghi vào:

```text
docs/week7_team_integration_handoff.md
docs/week7_cross_team_delivery_matrix.md
```

và phải thông báo cho owner bị ảnh hưởng trước khi đổi field name hoặc path.
