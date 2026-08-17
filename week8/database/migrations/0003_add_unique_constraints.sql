-- pipeline_runs: (run_name)
ALTER TABLE pipeline_runs
  ADD CONSTRAINT uq_pipeline_runs_run_name UNIQUE (run_name);

-- document_pages:  (document_id, page_number)
ALTER TABLE document_pages
  ADD CONSTRAINT uq_document_pages_doc_page UNIQUE (document_id, page_number);

-- ingestion_logs:  (source_id, run_id)

ALTER TABLE ingestion_logs
  ADD CONSTRAINT uq_ingestion_logs_source_run UNIQUE (source_id, run_id);

-- prediction_logs:  (document_external_id, ingestion_run_id, model_name)
ALTER TABLE prediction_logs
  ADD CONSTRAINT uq_prediction_logs_doc_run_model
  UNIQUE (document_external_id, ingestion_run_id, model_name);

-- structured_records:
ALTER TABLE structured_records
  ADD COLUMN IF NOT EXISTS record_hash VARCHAR(64);

UPDATE structured_records
  SET record_hash = md5(record_data::text)
  WHERE record_hash IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_structured_records_source_hash
  ON structured_records (source_id, record_hash);
