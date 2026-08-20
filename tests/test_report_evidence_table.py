"""
tests/test_report_evidence_table.py
=====================================
Verifies generate_report() produces a strict 8-section schema plus
an evidence_table that traces back to ingestion / dashboard /
prediction / RAG / suggestions, and degrades gracefully when sources
are missing.

Week 8 note (DV-HUNG-01): this module imports the fixture implementation
directly instead of `service_client`. These tests pin the reference UI
contract - the shape and business rules the UI requires from any backend - so
they must produce the same result in fixture mode and in backend mode. Live
UI-to-backend integration is covered separately by
tests/test_backend_contract_smoke.py, which runs in backend mode only.
"""

from demo.services.mock_client import generate_report


STRICT_SECTIONS = [
    "Title", "Executive Summary", "Evidence Used", "Key Findings",
    "Risks or Issues", "Recommendations", "Data Quality Limitations",
    "Next Actions",
]


def test_generate_report_returns_envelope():
    response = generate_report({})
    assert "data" in response
    assert "status" in response


def test_report_has_title():
    response = generate_report({"domain_label": "Business", "report_type": "Summary"})
    assert "title" in response["data"]
    assert "Business" in response["data"]["title"]


def test_report_has_strict_8_sections():
    response = generate_report({})
    sections = [s["Section"] for s in response["data"]["sections"]]
    assert sections == STRICT_SECTIONS


def test_report_has_evidence_table():
    response = generate_report({})
    assert "evidence_table" in response["data"]
    assert isinstance(response["data"]["evidence_table"], list)
    assert len(response["data"]["evidence_table"]) > 0


def test_evidence_table_row_has_required_columns():
    response = generate_report({
        "dashboard_signals": {"data_quality_score": 84},
        "prediction_result": {"predicted_document_type": "contract", "confidence": 0.7},
    })
    for row in response["data"]["evidence_table"]:
        for col in [
            "Evidence Source", "Module", "Metric / Signal",
            "Value", "Used In Section", "Limitation",
        ]:
            assert col in row, f"Missing column: {col}"


def test_evidence_table_includes_prediction_when_provided():
    response = generate_report({
        "prediction_result": {"predicted_document_type": "contract", "confidence": 0.7},
    })
    modules = {row["Module"] for row in response["data"]["evidence_table"]}
    assert "prediction" in modules


def test_evidence_table_includes_rag_when_provided():
    response = generate_report({
        "rag_context": {"citations": [{"file_name": "policy.pdf"}]},
    })
    modules = {row["Module"] for row in response["data"]["evidence_table"]}
    assert "rag" in modules


def test_no_evidence_falls_back_to_not_available_row():
    response = generate_report({})
    table = response["data"]["evidence_table"]
    assert len(table) >= 1
    # Every value in the fallback / partial rows must be a real string,
    # never a Python None leaking into the UI.
    for row in table:
        for value in row.values():
            assert value is not None


def test_report_never_invents_missing_data():
    """When no suggestions/prediction/rag provided, key cells must say
    'Not available in current data.' rather than being blank or guessed."""
    response = generate_report({})
    sections_preview = {s["Section"]: s["Preview"] for s in response["data"]["sections"]}
    assert sections_preview["Recommendations"] == "Not available in current data."


def test_week7_report_uses_integration_fixture_language():
    response = generate_report({
        "dashboard_signals": {"data_quality_score": 99},
        "prediction_result": {"predicted_document_type": "report", "confidence": 0.4},
        "rag_context": {"citations": [{"file_name": "DataFlow_Technical_Report.pdf"}]},
    })
    rendered = " ".join(
        [section["Preview"] for section in response["data"]["sections"]]
        + [row["Limitation"] for row in response["data"]["evidence_table"]]
    )
    assert "Week 7 integration fixture" in rendered
    assert "backend validation pending" in rendered.lower()
    assert "Mock" not in rendered
