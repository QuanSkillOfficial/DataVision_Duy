CREATE EXTENSION IF NOT EXISTS vector;
-- 1. sources
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT null UNIQUE,
    source_type VARCHAR(50) NOT NULL,
    source_format VARCHAR(50),
    source_path TEXT,
    url TEXT,
    owner_name VARCHAR(100),
    authentication_required BOOLEAN DEFAULT FALSE,
    schema_version VARCHAR(50),
    sample_available BOOLEAN DEFAULT FALSE,
    expected_volume VARCHAR(100),
    sensitive_data_flag BOOLEAN DEFAULT FALSE,
    downstream_consumer TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- 2. pipeline_runs
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_name VARCHAR(255),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. documents
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id) ON DELETE CASCADE,
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    file_size_bytes BIGINT,
    file_hash_sha256 VARCHAR(255),
    raw_path TEXT,
    staging_text_path TEXT,
    page_count INT,
    character_count INT,
    document_metadata JSONB,
    processing_status VARCHAR(50) DEFAULT 'uploaded',
    document_external_id VARCHAR(255) unique,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    CONSTRAINT chk_document_processing_status
        CHECK (processing_status IN ('uploaded', 'extracted', 'chunked', 'embedded', 'processed', 'failed'))
);
-- 4. document_chunks
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(255) UNIQUE NOT NULL,
    document_id INT REFERENCES documents(id) ON DELETE CASCADE,
    page_number INT,
    chunk_text TEXT NOT NULL,
    chunk_index INT,
    embedding vector(384),
    embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    embedding_dimension INT DEFAULT 384,
    chunk_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 5. structured_records
CREATE TABLE IF NOT EXISTS structured_records (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id) ON DELETE CASCADE,
    record_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'clean',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. ingestion_logs
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100),
    source_id INT REFERENCES sources(id) ON DELETE CASCADE,
    pipeline_run_id INT REFERENCES pipeline_runs(id) ON DELETE SET NULL,
    source_type VARCHAR(50),
    input_path_or_url TEXT,
    status VARCHAR(50),
    records_read INT,
    records_valid INT,
    records_invalid INT,
    error_message TEXT,
    raw_output_path TEXT,
    staging_output_path TEXT,
    clean_output_path TEXT,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    data_quality_score FLOAT,
	required_missing_values JSONB,
	optional_missing_values JSONB,
    duplicate_count INT,
	manifest_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_ingestion_status
    CHECK (status IN ('success', 'failed', 'partial_success', 'running'))
);

-- 7. analytics_events
CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. rag_query_logs
CREATE TABLE IF NOT EXISTS rag_query_logs (
    id SERIAL PRIMARY KEY,
    document_id INT REFERENCES documents(id) ON DELETE SET NULL,
    user_query TEXT NOT NULL,
    retrieved_chunk_ids JSONB,
    retrieval_scores JSONB,
    generated_response TEXT,
    answer_confidence FLOAT,
    latency_ms INT,
    model_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. prediction_logs
CREATE TABLE IF NOT EXISTS prediction_logs (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id) ON DELETE SET NULL,
    document_id INT REFERENCES documents(id) ON DELETE SET NULL,
    structured_record_id INT REFERENCES structured_records(id) ON DELETE SET NULL,
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    input_payload JSONB,
    prediction_result JSONB,
    predicted_label VARCHAR(100),
    document_external_id VARCHAR(255),
	ingestion_run_id VARCHAR(100),
    confidence_score FLOAT,
    status VARCHAR(50),
	review_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_prediction_status
        CHECK (status IN ('accepted', 'needs_review', 'waiting_for_source', 'failed')),
    CONSTRAINT chk_prediction_confidence
        CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- 10. document_pages
CREATE TABLE IF NOT EXISTS document_pages (
    id SERIAL PRIMARY KEY,
    document_id INT REFERENCES documents(id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    page_text TEXT,
    character_count INT,
    is_empty BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create basic indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_source_id ON documents(source_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_logs_pipeline_id ON ingestion_logs(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_pages_document_id ON document_pages(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops);
-- DROP TABLE documents CASCADE;
-- Recent Activity
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_created_at ON pipeline_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_created_at ON ingestion_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_created_at ON prediction_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rag_query_logs_created_at ON rag_query_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at DESC);

-- Dashboard Overview
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_status ON ingestion_logs(status);
CREATE INDEX IF NOT EXISTS idx_prediction_logs_status ON prediction_logs(status);
CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);

-- 1. v_dashboard_overview (High-level system metrics)
CREATE OR REPLACE VIEW v_dashboard_overview AS
SELECT
    (SELECT COUNT(*) FROM sources) AS total_sources,
    (SELECT COUNT(*) FROM documents) AS total_documents,
    (SELECT COUNT(*) FROM ingestion_logs WHERE status = 'success') AS successful_ingestions,
    (SELECT COUNT(*) FROM ingestion_logs WHERE status = 'failed') AS failed_ingestions,
    (SELECT COUNT(*) FROM rag_query_logs) AS total_rag_queries,
    (SELECT COUNT(*) FROM prediction_logs) AS total_predictions;

-- 2. v_ingestion_health (Track ETL quality over time)
CREATE OR REPLACE VIEW v_ingestion_health AS
SELECT
    DATE(created_at) AS ingestion_date,
    status,
    COUNT(*) AS run_count,
    SUM(records_read) AS total_read,
    SUM(records_valid) AS total_valid,
    SUM(records_invalid) AS total_invalid
FROM ingestion_logs
GROUP BY DATE(created_at), status
ORDER BY ingestion_date DESC;

-- 3. v_source_quality_summary (Track volume and error rates per source)
CREATE OR REPLACE VIEW v_source_quality_summary AS
SELECT
    s.id AS source_id,
    s.name AS source_name,
    s.source_type,
    s.status,
    COUNT(DISTINCT d.id) AS total_documents,
    COUNT(DISTINCT sr.id) AS total_structured_records,
    COALESCE(SUM(il.records_invalid), 0) AS total_invalid_records
FROM sources s
LEFT JOIN documents d ON s.id = d.source_id
LEFT JOIN structured_records sr ON s.id = sr.source_id
LEFT JOIN ingestion_logs il ON s.id = il.source_id
GROUP BY s.id, s.name, s.source_type, s.status;

-- 4. v_document_quality_summary (Track processing status of unstructured data)
CREATE OR REPLACE VIEW v_document_quality_summary AS
SELECT
    processing_status,
    file_type,
    COUNT(*) AS document_count,
    COALESCE(AVG(page_count), 0) AS avg_page_count
FROM documents
GROUP BY processing_status, file_type;

-- 5. v_rag_daily_metrics (Track chatbot performance and confidence)
CREATE OR REPLACE VIEW v_rag_daily_metrics AS
SELECT
    DATE(created_at) AS query_date,
    COUNT(*) AS total_queries,
    AVG(latency_ms) AS avg_latency_ms,
    AVG(answer_confidence) AS avg_confidence,
    model_name
FROM rag_query_logs
GROUP BY DATE(created_at), model_name
ORDER BY query_date DESC;

-- 6. v_prediction_confidence_summary (Track ML model outputs for review)
CREATE OR REPLACE VIEW v_prediction_confidence_summary AS
SELECT
    model_name,
    model_version,
    predicted_label,
    COUNT(*) AS prediction_count,
    AVG(confidence_score) AS avg_confidence,
    MIN(confidence_score) AS min_confidence
FROM prediction_logs
GROUP BY model_name, model_version, predicted_label;

-- 7. v_recent_activity (Live feed for Streamlit dashboard)
CREATE OR REPLACE VIEW v_recent_activity AS
SELECT
    'RAG Query' AS activity_type,
    user_query AS description,
    created_at
FROM rag_query_logs
UNION ALL
SELECT
    'Ingestion Issue' AS activity_type,
    error_message AS description,
    created_at
FROM ingestion_logs
WHERE error_message IS NOT NULL AND status != 'success'
UNION ALL
SELECT
    'New Source Added' AS activity_type,
    name AS description,
    created_at
FROM sources
ORDER BY created_at DESC
LIMIT 50;

-- 8. v_latest_ingestion_runs
CREATE OR REPLACE VIEW v_latest_ingestion_runs AS
SELECT
    pr.run_name,
    s.name AS source_name,
    il.status AS ingestion_status,
    il.records_read,
    il.error_message,
    il.started_at,
    il.ended_at,
    il.created_at
FROM ingestion_logs il
JOIN sources s ON il.source_id = s.id
LEFT JOIN pipeline_runs pr ON il.pipeline_run_id = pr.id
ORDER BY il.created_at DESC;

-- 9. v_data_quality_dashboard
CREATE OR REPLACE VIEW v_data_quality_dashboard AS
SELECT
    s.name AS source_name,
    il.run_id,
    il.status,
    il.records_read,
    il.records_valid,
    il.records_invalid,
    il.data_quality_score,
    il.duplicate_count,
    il.created_at
FROM ingestion_logs il
JOIN sources s ON il.source_id = s.id
ORDER BY il.created_at DESC;

-- 10. v_source_quality_detail
CREATE OR REPLACE VIEW v_source_quality_detail AS
SELECT
    s.name AS source_name,
    s.source_type,
    COUNT(il.id) AS total_runs,
    ROUND(CAST(AVG(il.data_quality_score) AS NUMERIC), 2) AS avg_data_quality_score,
    SUM(il.records_invalid) AS total_invalid_records,
    SUM(il.duplicate_count) AS total_duplicates,
    MAX(il.created_at) AS last_run_at
FROM sources s
LEFT JOIN ingestion_logs il ON s.id = il.source_id
GROUP BY s.id, s.name, s.source_type;

-- 11. v_document_rag_readiness
CREATE OR REPLACE VIEW v_document_rag_readiness AS
SELECT
    d.document_external_id,
    d.file_name,
    s.name AS source_name,
    d.processing_status,
    d.page_count,
    COUNT(dc.id) AS total_chunks,
    d.created_at,
    d.updated_at
FROM documents d
JOIN sources s ON d.source_id = s.id
LEFT JOIN document_chunks dc ON d.id = dc.document_id
GROUP BY d.id, d.document_external_id, d.file_name, s.name, d.processing_status, d.page_count, d.created_at, d.updated_at;

-- 12. v_prediction_review_queue
CREATE OR REPLACE VIEW v_prediction_review_queue AS
SELECT
    id,
    document_id,
    predicted_label,
    confidence_score,
    status,
    review_reason,
    created_at
FROM prediction_logs
WHERE status IN ('needs_review', 'waiting_for_source')
   OR confidence_score < 0.60
ORDER BY created_at DESC;
