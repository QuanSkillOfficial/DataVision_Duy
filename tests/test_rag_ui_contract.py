"""
tests/test_rag_ui_contract.py
================================
Verifies ask_rag() honors the rag_ui_contract: answer, citations,
retrieved_context, similarity_score, chunk_id, status.

Week 8 note (DV-HUNG-01): this module imports the fixture implementation
directly instead of `service_client`. These tests pin the reference UI
contract - the shape and business rules the UI requires from any backend - so
they must produce the same result in fixture mode and in backend mode. Live
UI-to-backend integration is covered separately by
tests/test_backend_contract_smoke.py, which runs in backend mode only.
"""

from demo.services.mock_client import ask_rag


def test_valid_question_returns_envelope():
    response = ask_rag("What does the policy say about refunds?")
    assert "data" in response
    assert "status" in response


def test_response_has_required_fields():
    response = ask_rag("What does the policy say about refunds?")
    data = response["data"]
    for field in ["question", "answer", "citations", "retrieved_context", "status"]:
        assert field in data, f"Missing field: {field}"


def test_has_citation_with_required_fields():
    response = ask_rag("What does the policy say about refunds?")
    citations = response["data"]["citations"]
    assert len(citations) > 0
    for citation in citations:
        assert "file_name" in citation
        assert "page_number" in citation
        assert "chunk_id" in citation
        assert "document_external_id" in citation
        assert "document_db_id" in citation


def test_has_similarity_score_in_retrieved_context():
    response = ask_rag("What does the policy say about refunds?")
    context = response["data"]["retrieved_context"]
    assert len(context) > 0
    for chunk in context:
        assert "chunk_text" in chunk
        assert "similarity_score" in chunk
        assert 0.0 <= chunk["similarity_score"] <= 1.0


def test_citation_chunk_id_matches_context_chunk_id():
    """Citations and retrieved_context should be linkable via chunk_id."""
    response = ask_rag("What does the policy say about refunds?")
    data = response["data"]
    citation_ids = {c["chunk_id"] for c in data["citations"]}
    context_ids = {c["chunk_id"] for c in data["retrieved_context"]}
    assert citation_ids & context_ids, "No overlapping chunk_id between citations and context"


def test_no_match_returns_i_do_not_know():
    response = ask_rag("What is the weather today?")
    data = response["data"]
    assert data["citations"] == []
    assert data["retrieved_context"] == []
    assert "do not know" in data["answer"].lower()
    assert data["status"] == "no_match"


def test_empty_question_returns_error():
    response = ask_rag("")
    assert response["status"] == "error"
    assert response["data"]["citations"] == []


def test_document_id_filter_does_not_crash():
    response = ask_rag(
        "What does the policy say about refunds?",
        document_id="doc_001",
    )
    assert "data" in response


def test_week7_dataflow_rag_metadata_is_available():
    response = ask_rag("What is the DataFlow pipeline?")
    data = response["data"]
    assert data["document_external_id"] == "doc_dataflow_technical_report"
    assert data["retrieval_backend"] == "pgvector"
    assert data["embedding_dimension"] == 384
    assert data["citations"][0]["file_name"] == "DataFlow_Technical_Report.pdf"
