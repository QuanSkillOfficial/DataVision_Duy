-- 1. Remove Analytics Views
DROP VIEW IF EXISTS v_dashboard_overview CASCADE;
DROP VIEW IF EXISTS v_ingestion_health CASCADE;
DROP VIEW IF EXISTS v_source_quality_summary CASCADE;
DROP VIEW IF EXISTS v_document_quality_summary CASCADE;
DROP VIEW IF EXISTS v_rag_daily_metrics CASCADE;
DROP VIEW IF EXISTS v_prediction_confidence_summary CASCADE;
DROP VIEW IF EXISTS v_recent_activity CASCADE;
DROP VIEW IF EXISTS v_latest_ingestion_runs CASCADE;
DROP VIEW IF EXISTS v_data_quality_dashboard CASCADE;
DROP VIEW IF EXISTS v_source_quality_detail CASCADE;
DROP VIEW IF EXISTS v_document_rag_readiness CASCADE;
DROP VIEW IF EXISTS v_prediction_review_queue CASCADE;
DROP TABLE IF EXISTS schema_migrations CASCADE;

-- 2. Remove Tables
DROP TABLE IF EXISTS prediction_logs CASCADE;
DROP TABLE IF EXISTS rag_query_logs CASCADE;
DROP TABLE IF EXISTS analytics_events CASCADE;
DROP TABLE IF EXISTS ingestion_logs CASCADE;
DROP TABLE IF EXISTS structured_records CASCADE;
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS document_pages CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS pipeline_runs CASCADE;
DROP TABLE IF EXISTS sources CASCADE;
