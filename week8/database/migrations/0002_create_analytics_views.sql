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
