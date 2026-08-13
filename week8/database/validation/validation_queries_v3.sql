-- 1. Metadata Validation (Check if Tables & Views exist)
-- ==========================================
-- This should list exactly 10 tables
SELECT 'Missing Table' AS issue, unnest(ARRAY['sources', 'documents', 'document_pages', 'document_chunks', 'structured_records', 'ingestion_logs', 'pipeline_runs', 'analytics_events', 'rag_query_logs', 'prediction_logs']) AS required_table
EXCEPT
SELECT 'Missing Table', table_name 
FROM information_schema.tables WHERE table_schema = 'public';

-- This should list exactly 12 views (v_dashboard_overview, etc.)
SELECT 'Missing View' AS issue, unnest(ARRAY['v_dashboard_overview', 'v_data_quality_dashboard', 'v_document_quality_summary', 'v_document_rag_readiness', 'v_ingestion_health', 'v_latest_ingestion_runs', 'v_prediction_confidence_summary', 'v_prediction_review_queue', 'v_rag_daily_metrics', 'v_recent_activity', 'v_source_quality_detail', 'v_source_quality_summary']) AS required_view
EXCEPT
SELECT 'Missing View', table_name 
FROM information_schema.views WHERE table_schema = 'public';

-- ==========================================
-- 2. Foreign Key Integrity Checks (Orphan checks)
-- ==========================================
-- Check 2.1: Do all document_pages link to a valid document? (Expected: 0)
SELECT COUNT(*) AS orphaned_pages 
FROM document_pages dp 
LEFT JOIN documents d ON dp.document_id = d.id 
WHERE d.id IS NULL;

-- Check 2.2: Do all document_chunks link to a valid document? (Expected: 0)
SELECT COUNT(*) AS orphaned_chunks 
FROM document_chunks dc 
LEFT JOIN documents d ON dc.document_id = d.id 
WHERE d.id IS NULL;

-- Check 2.3: Do all structured_records link to a valid source? (Expected: 0)
SELECT COUNT(*) AS orphaned_records 
FROM structured_records sr 
LEFT JOIN sources s ON sr.source_id = s.id 
WHERE s.id IS NULL;

-- ==========================================
-- 3. RAG & VECTOR DATA QUALITY CHECKS
-- ==========================================
-- Check 3.1: Missing embeddings (Expected: 0)
SELECT COUNT(*) AS missing_embeddings 
FROM document_chunks 
WHERE embedding IS NULL;

-- Check 3.2: Invalid embedding dimensions (Expected: 0)
SELECT COUNT(*) AS invalid_vector_dimensions 
FROM document_chunks 
WHERE vector_dims(embedding) != 384;

-- Check 3.3: RAG logs missing retrieved_chunk_ids (Expected: 0)
SELECT COUNT(*) AS missing_retrieved_chunks 
FROM rag_query_logs 
WHERE retrieved_chunk_ids IS NULL OR jsonb_array_length(retrieved_chunk_ids) = 0;

--  Check 3.4: Chunks with empty text (Expected: 0)
SELECT COUNT(*) AS empty_chunk_text
FROM document_chunks
WHERE chunk_text IS NULL OR TRIM(chunk_text) = '';

-- ==========================================
-- 4. Pipeline & Log Data Quality Checks
-- ==========================================
-- Check 4.1: Do all ingestion logs have a run_id assigned? (Expected: 0)
SELECT COUNT(*) AS missing_run_id_logs 
FROM ingestion_logs 
WHERE run_id IS NULL OR TRIM(run_id) = '';

-- Check 4.2: Are there any invalid status values bypassing constraints? (Expected: 0)
SELECT COUNT(*) AS invalid_status_logs 
FROM ingestion_logs 
WHERE status NOT IN ('success', 'failed', 'partial_success', 'running');

-- Check 4.3: Do prediction logs correctly contain a confidence score? (Expected:>=0)
SELECT COUNT(*) AS missing_confidence_scores 
FROM prediction_logs 
WHERE confidence_score IS NULL;

-- ==========================================
-- 5. Dashboard Data Ready Check
-- ==========================================
-- Ensure the main dashboard view is calculating successfully
SELECT COUNT(*) AS dashboard_overview_rows FROM v_dashboard_overview;

-- ==========================================
-- 6. SOURCE & DOCUMENT CHECKS
-- ==========================================
-- Check 6.1: Duplicate sources (Expected: 0)
SELECT name, COUNT(*) AS duplicate_count 
FROM sources 
GROUP BY name 
HAVING COUNT(*) > 1;

-- Check 6.2: Missing document_external_id (Expected: 0)
SELECT COUNT(*) AS missing_external_id 
FROM documents 
WHERE document_external_id IS NULL OR TRIM(document_external_id) = '';

-- ==========================================
-- 7. PIPELINE & PREDICTION LOG CHECKS
-- ==========================================
-- Check 7.1: Missing data_quality_score (Expected: 0)
SELECT COUNT(*) AS missing_data_quality_score 
FROM ingestion_logs 
WHERE status IN ('success', 'partial_success') AND data_quality_score IS NULL;

-- Check 7.2: Prediction logs missing status (Expected: 0)
SELECT COUNT(*) AS invalid_prediction_status 
FROM prediction_logs 
WHERE status NOT IN ('accepted', 'needs_review', 'waiting_for_source', 'failed') 
   OR status IS NULL;

-- Check 7.3: Confidence_score outside 0–1 (Expected: 0)
SELECT COUNT(*) AS out_of_bounds_confidence 
FROM prediction_logs 
WHERE confidence_score < 0.0 OR confidence_score > 1.0;

-- Check 7.4: Ingestion Math Mismatch (Expected: 0)
SELECT COUNT(*) AS math_mismatch_logs
FROM ingestion_logs
WHERE records_read != (COALESCE(records_valid, 0) + COALESCE(records_invalid, 0))
  AND status IN ('success', 'partial_success');

-- Check 7.5: Stuck Pipeline Runs (> 24 hours) (Expected: 0)
SELECT COUNT(*) AS stuck_pipelines
FROM pipeline_runs
WHERE status = 'running' 
  AND start_time < NOW() - INTERVAL '24 hours';

-- Check 7.6: Time logic error (end time before start time) (Expected: 0)
SELECT COUNT(*) AS invalid_time_logic
FROM ingestion_logs
WHERE ended_at < started_at;

-- Check 8: Missing pgvector extension (Expected: 1 row with 'vector')
SELECT extname FROM pg_extension WHERE extname = 'vector';

-- Check 9: Orphaned prediction_logs (Expected: 0)
SELECT COUNT(*) AS orphaned_predictions 
FROM prediction_logs pl 
LEFT JOIN documents d ON pl.document_id = d.id 
WHERE pl.document_id IS NOT NULL AND d.id IS NULL;

-- Check 10: Empty review queue when predictions exist
-- Expected: rows_in_queue_view >= predictions_needing_review
SELECT 
    (SELECT COUNT(*) FROM prediction_logs WHERE status IN ('needs_review', 'waiting_for_source')) AS predictions_needing_review,
    (SELECT COUNT(*) FROM v_prediction_review_queue) AS rows_in_queue_view;

-- Check 11: Empty RAG metrics when RAG logs exist
-- Expected: IF total_rag_logs > 0 then rows_in_rag_metrics_view > 0
SELECT 
    (SELECT COUNT(*) FROM rag_query_logs) AS total_rag_logs,
    (SELECT COUNT(*) FROM v_rag_daily_metrics) AS rows_in_rag_metrics_view;