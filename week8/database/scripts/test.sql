SELECT COUNT(*) FROM sources;
SELECT COUNT(*) FROM pipeline_runs;
SELECT COUNT(*) FROM ingestion_logs;
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM document_pages;
SELECT COUNT(*) FROM structured_records;

SELECT COUNT(*) FROM prediction_logs;
SELECT status, COUNT(*) FROM prediction_logs GROUP BY status;
SELECT * FROM v_prediction_review_queue;

SELECT COUNT(*) FROM document_chunks;
SELECT COUNT(*) FROM rag_query_logs;
SELECT * FROM v_document_rag_readiness;
SELECT * FROM v_rag_daily_metrics;
