"""
Week 7 suggestion UI contract tests.

Week 8 note (DV-HUNG-01): this module imports the fixture implementation
directly instead of `service_client`. These tests pin the reference UI
contract - the shape and business rules the UI requires from any backend - so
they must produce the same result in fixture mode and in backend mode. Live
UI-to-backend integration is covered separately by
tests/test_backend_contract_smoke.py, which runs in backend mode only.
"""

from demo.services.mock_client import generate_suggestions


def test_week7_suggestions_include_cross_module_evidence_fields():
    response = generate_suggestions({
        "dashboard_signals": {
            "processing_status": "ready",
            "parsing_coverage": 1.0,
            "rag_ready_documents": 1,
        },
        "prediction_result": {
            "status": "needs_review",
            "confidence": 0.3988,
            "manual_review_required": True,
            "review_reason": "Prediction confidence below threshold",
        },
        "rag_context": {
            "status": "success",
            "citations": [{"chunk_id": "doc_dataflow_technical_report_page_4_chunk_000"}],
            "retrieved_context": [{"similarity_score": 0.84}],
        },
        "ingestion_run": {
            "file_hash_sha256": "06c0c318db353a5c5c6dbaa84c6778cde022fde92bd1bb7f56e32c485d62fa54",
        },
    })
    suggestions = response["data"]
    assert suggestions
    modules = {item["source_module"] for item in suggestions}
    assert {"prediction", "rag"} <= modules
    for item in suggestions:
        assert item["affected_document"]
        assert item["affected_source"]
        assert "confidence" in item
        assert item["recommended_action"] if "recommended_action" in item else item["next_action"]


def test_week7_suggestions_remain_sorted():
    response = generate_suggestions({
        "dashboard_signals": {"processing_status": "ready", "parsing_coverage": 0.5},
        "prediction_result": {"status": "needs_review", "confidence": 0.4},
        "rag_context": {"status": "no_match"},
    })
    scores = [item["final_score"] for item in response["data"]]
    assert scores == sorted(scores, reverse=True)
