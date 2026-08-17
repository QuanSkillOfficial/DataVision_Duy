"""
tests/e2e/test_user_journey.py
================================
DV-HUNG-02 and DV-HUNG-03: the complete user journey in a real browser,
against a real backend, in backend mode.

    Upload/Ingestion -> Dashboard -> Prediction -> Review status
    -> RAG -> Citations -> Suggestions -> Reports

This is one continuous browser session on purpose. Streamlit keeps session
state per connection, so navigating through the sidebar (rather than reloading
URLs) is what makes this a single user journey instead of eight isolated page
visits. Each step writes a screenshot to screenshots/week8_browser_e2e/.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from tests.e2e.ui import (
    ask_chatbot,
    capture,
    click_button,
    navigate,
    expect_page,
    open_app,
    page_text,
    release_identity,
    service_errors,
    upload_file,
)

RAG_QUESTION = "What is the DataFlow pipeline?"


@pytest.mark.e2e
@pytest.mark.staging
def test_complete_user_journey(page, app_url, sample_csv):
    open_app(page, app_url)

    # ── 0. Release identity ────────────────────────────────────────────────
    # Before trusting anything on screen, confirm which build and backend the
    # browser is actually looking at (DV-HUNG-04).
    identity = release_identity(page)
    assert identity["data_mode"] == "backend", (
        f"Journey must run against a backend, not fixtures: {identity}"
    )
    assert identity["backend_state"] == "live", (
        f"Backend was not live at the start of the journey: {identity}"
    )
    assert identity["release_sha"] and identity["release_sha"] != "unknown"
    assert identity["release_match"] != "mismatch", (
        f"UI and backend report different releases: {identity}"
    )
    capture(page, "00_home_release_identity")

    # ── 1. Upload / ingestion ──────────────────────────────────────────────
    navigate(page, "Upload")
    expect_page(page, "Upload")
    upload_file(page, sample_csv)

    expect(page.get_by_text("Dataset Analysis by AI")).to_be_visible()
    assert sample_csv.name in page_text(page), "Uploaded file is not listed as a source"
    capture(page, "01_upload_dataset_analysis")

    click_button(page, "Select template")
    click_button(page, "Generate Dashboard")

    # ── 2. Dashboard ───────────────────────────────────────────────────────
    # Generating the dashboard routes the user there automatically.
    expect_page(page, "Dashboard")
    assert not service_errors(page), (
        f"Dashboard reported service failures: {service_errors(page)}"
    )

    dashboard_text = page_text(page)
    for expected in ["Universal Data Health", "Ingestion Run Panel", "Prediction Review Queue"]:
        assert expected in dashboard_text, f"Dashboard is missing '{expected}'"

    # Traceability: the run must be identifiable back to its source file.
    assert "File Hash (SHA-256)" in dashboard_text
    assert "Not available in current data." not in dashboard_text.split("Storage Directory Paths")[0], (
        "Dashboard rendered placeholders instead of live ingestion values"
    )
    capture(page, "02_dashboard_live_metrics")

    # ── 3. Prediction ──────────────────────────────────────────────────────
    navigate(page, "Prediction")
    expect_page(page, "Prediction Lab")
    click_button(page, "Run Classification")

    expect(page.get_by_role("heading", name="Prediction Results")).to_be_visible()
    assert not service_errors(page), (
        f"Prediction reported service failures: {service_errors(page)}"
    )

    prediction_text = page_text(page)
    assert "Model Version:" in prediction_text, "Prediction card omits model version"
    assert "Top-3 Predictions Distribution" in prediction_text

    # ── 4. Review status ───────────────────────────────────────────────────
    # A prediction must land in an explicit review state. A `failed` status is
    # not an acceptable outcome for the release gate.
    review_states = [
        "Model suggestion saved",       # accepted
        "Needs human review",           # needs_review
    ]
    assert any(state in prediction_text for state in review_states), (
        "Prediction did not surface an acceptable review status"
    )
    assert "Validation failed" not in prediction_text, (
        "A failed prediction must not satisfy the browser acceptance run"
    )
    capture(page, "03_prediction_and_review_status")

    # ── 5. RAG ─────────────────────────────────────────────────────────────
    navigate(page, "Chatbot")
    expect_page(page, "QS Chatbot")
    ask_chatbot(page, RAG_QUESTION)

    assert not service_errors(page), (
        f"RAG reported service failures: {service_errors(page)}"
    )

    chat_text = page_text(page)
    assert RAG_QUESTION in chat_text, "The question was not recorded in the transcript"

    # ── 6. Citations ───────────────────────────────────────────────────────
    expect(page.get_by_text("Citations").first).to_be_visible()
    assert "Chunk:" in chat_text, "Citation is missing its chunk identifier"
    assert "Page" in chat_text, "Citation is missing its page number"
    assert "Ext ID:" in chat_text, "Citation is missing its document identifier"
    capture(page, "04_rag_answer_with_citations")

    # ── 7. Suggestions ─────────────────────────────────────────────────────
    navigate(page, "Suggestions")
    expect_page(page, "Action Suggestions")
    click_button(page, "Refresh Suggestions from All Sources")

    assert not service_errors(page), (
        f"Suggestions reported service failures: {service_errors(page)}"
    )
    suggestions_text = page_text(page)
    assert "Recommended Actions" in suggestions_text, "No suggestions were produced"
    # Streamlit renders dataframes to a canvas, so the ranking table's cells are
    # not readable as DOM text. The assertions below use the surrounding markup,
    # which is what a reviewer reads to know the list is evidence-backed.
    assert "Evidence trace:" in suggestions_text, "Suggestions carry no evidence trace"
    assert "Action History" in suggestions_text
    capture(page, "05_suggestions_with_evidence")

    # ── 8. Reports ─────────────────────────────────────────────────────────
    navigate(page, "Reports")
    expect_page(page, "Reports")
    assert not service_errors(page), (
        f"Reports reported service failures: {service_errors(page)}"
    )

    reports_text = page_text(page)
    assert "Report Draft Preview" in reports_text
    assert "Evidence Table" in reports_text
    assert "Traces every claim back to its originating module" in reports_text
    # The page prints this placeholder only when the evidence table is empty.
    assert "Not available in current data." not in reports_text, (
        "The report was generated without any evidence rows"
    )
    expect(page.get_by_role("button", name="Download Markdown Draft")).to_be_enabled()
    capture(page, "06_report_with_evidence_table")

    # The journey ends on the same release it started on.
    assert release_identity(page)["release_sha"] == identity["release_sha"]
