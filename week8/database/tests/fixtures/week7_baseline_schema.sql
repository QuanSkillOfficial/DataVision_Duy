

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
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

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_name VARCHAR(255),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    document_external_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    CONSTRAINT chk_document_processing_status
        CHECK (processing_status IN ('uploaded', 'extracted', 'chunked', 'embedded', 'processed', 'failed'))
);

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

CREATE TABLE IF NOT EXISTS structured_records (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id) ON DELETE CASCADE,
    record_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'clean',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS document_pages (
    id SERIAL PRIMARY KEY,
    document_id INT REFERENCES documents(id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    page_text TEXT,
    character_count INT,
    is_empty BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);