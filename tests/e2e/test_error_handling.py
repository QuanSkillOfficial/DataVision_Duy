"""
tests/e2e/test_error_handling.py
==================================
DV-HUNG-05 in the browser: what a user actually sees when the backend is not
answering.

The release rule these tests defend is that fixture-mode success must never be
presented as live data. A UI that quietly renders repository fixtures when the
backend is down would produce a green screenshot for a broken release.
"""

from __future__ import annotations

import pytest

from tests.e2e.ui import (
    capture,
    click_button,
    expect_page,
    navigate,
    open_app,
    page_text,
    release_identity,
    service_errors,
)


@pytest.mark.e2e
def test_unavailable_backend_is_reported_not_hidden(page, unreachable_backend_app_url):
    """A UI pointed at a dead backend must say so, on every data page."""
    open_app(page, unreachable_backend_app_url)

    identity = release_identity(page)
    assert identity["data_mode"] == "backend"
    assert identity["backend_state"] == "unreachable", (
        f"UI claims backend state '{identity['backend_state']}' while nothing "
        "is listening on the configured port"
    )

    # Home fetches platform KPIs, so it must report the failure rather than
    # fall back to the fixtures that are still present in the repository.
    home_errors = service_errors(page)
    assert home_errors, "Home rendered without reporting the backend failure"
    # Either classification is correct here: depending on the host, a request to
    # a port nothing is listening on is refused outright or times out while
    # connecting. What matters is that the UI reports a transport failure and
    # does not render data.
    assert all(
        error["kind"] in {"unavailable", "timeout"} for error in home_errors
    ), home_errors

    home_text = page_text(page)
    # The fixture record count must not appear anywhere on a failed page.
    assert "11,560" not in home_text, (
        "Fixture data leaked into the UI while the backend was unreachable"
    )
    capture(page, "10_error_home_backend_unreachable")

    # Reports asks the backend on every render, so it must refuse to produce a
    # draft rather than present an evidence table built from nothing.
    navigate(page, "Reports")
    report_errors = service_errors(page)
    assert report_errors, "Reports rendered without reporting the backend failure"

    reports_text = page_text(page)
    assert "Report Draft Preview" not in reports_text, (
        "A report draft was rendered while the backend was unreachable"
    )
    capture(page, "11_error_reports_actionable_message")


@pytest.mark.e2e
def test_error_message_tells_the_user_what_to_do(page, unreachable_backend_app_url):
    """An error is only useful if it names the failure and the next step."""
    open_app(page, unreachable_backend_app_url)

    text = page_text(page)
    assert "What to do:" in text, "The failure block offers no next step"
    assert "QS_BACKEND" in text, (
        "The guidance does not name a concrete setting the operator can check"
    )
    assert "Technical detail for the release evidence" in text, (
        "No technical detail is available to attach to the release evidence"
    )


@pytest.mark.e2e
def test_prediction_failure_does_not_leave_a_stale_result(page, app_url, backend_port):
    """A failing prediction call must clear the previous result card.

    Otherwise a reviewer can read an old successful classification as the
    outcome of the run that just failed.
    """
    open_app(page, app_url)
    navigate(page, "Prediction")
    expect_page(page, "Prediction Lab")

    # First run succeeds against the healthy backend.
    click_button(page, "Run Classification")
    assert "Prediction Results" in page_text(page)
    assert not service_errors(page)

    # Flip the prediction route to failing, then re-run the same action.
    _inject_prediction_failure(backend_port)

    click_button(page, "Run Classification")
    errors = service_errors(page)
    assert errors, "A failed prediction call was not reported"
    assert any(error["service"] == "Prediction service" for error in errors), errors

    text = page_text(page)
    assert "Model Suggestion" not in text, (
        "A stale prediction card survived a failed classification run"
    )
    capture(page, "12_error_prediction_no_stale_result")


def _inject_prediction_failure(backend_port: int) -> None:
    """Ask the running stub to start failing the prediction route."""
    import urllib.request

    request = urllib.request.Request(
        f"http://127.0.0.1:{backend_port}/api/_control/fail",
        data=b'{"route": "/api/predict/document-type"}',
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        assert response.status == 200
