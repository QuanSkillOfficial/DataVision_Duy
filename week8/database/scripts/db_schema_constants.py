"""Single source of truth for core table/view names.

Imported by backup_database.py, restore_database.py and the test suite so
row-count checks always agree with each other instead of drifting out of
sync (previously restore_database.py redefined these lists locally).
"""

CORE_TABLES = [
    "sources",
    "documents",
    "document_pages",
    "document_chunks",
    "structured_records",
    "ingestion_logs",
    "pipeline_runs",
    "analytics_events",
    "rag_query_logs",
    "prediction_logs",
]

CORE_VIEWS = [
    "v_dashboard_overview",
    "v_ingestion_health",
    "v_source_quality_summary",
    "v_document_quality_summary",
    "v_rag_daily_metrics",
    "v_prediction_confidence_summary",
    "v_recent_activity",
    "v_latest_ingestion_runs",
    "v_data_quality_dashboard",
    "v_source_quality_detail",
    "v_document_rag_readiness",
    "v_prediction_review_queue",
]
