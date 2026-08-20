CREATE TABLE IF NOT EXISTS prediction_reviewer_corrections (
    id BIGSERIAL PRIMARY KEY,
    prediction_log_id INTEGER NOT NULL
        REFERENCES prediction_logs(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    document_external_id VARCHAR(255),
    original_prediction VARCHAR(100) NOT NULL,
    corrected_document_type VARCHAR(100) NOT NULL,
    corrected_by VARCHAR(255) NOT NULL,
    correction_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_prediction_reviewer_correction
        UNIQUE (prediction_log_id)
);

CREATE INDEX IF NOT EXISTS idx_prediction_corrections_created_at
    ON prediction_reviewer_corrections(created_at DESC);
