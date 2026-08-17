"""
tests/e2e/conftest.py
=======================
Fixtures for the Week 8 browser suite (DV-HUNG-02/03).

The suite runs the real Streamlit UI in backend mode against a real HTTP
backend and drives it with a real browser. Nothing here substitutes fixture
responses for a live call: if the backend is not up, the tests fail.

Environment overrides:
    QS_E2E_BASE_URL   Point the journey at an already-deployed UI
                      (used for the private staging run, DV-HUNG-06).
    QS_E2E_HEADED=1   Watch the run in a visible browser.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from tests.e2e.harness import (
    DEFAULT_TIMEOUT_MS,
    ROOT,
    SCREENSHOT_DIR,
    free_port,
    start_backend_stub,
    start_streamlit,
)

LOG_DIR = ROOT / "outputs" / "week8" / "e2e_logs"


@pytest.fixture(scope="session", autouse=True)
def e2e_session():
    """Configure the browser assertions and start from a clean evidence folder.

    This is a fixture and not a ``pytest_configure`` hook on purpose. A hook in
    this conftest fires as soon as pytest *collects* this directory, even when
    the e2e tests are deselected, which had two consequences:

      * it imported Playwright in jobs that only install ``requirements.txt``,
        aborting collection before a single backend-mode test ran (DV-HUNG-01);
      * it deleted the committed screenshots in
        ``screenshots/week8_browser_e2e/`` on any unrelated test run.

    As a fixture the setup runs only when an e2e test is actually executed.
    """
    from playwright.sync_api import expect

    # Streamlit renders through a websocket rerun, so the default 5s assertion
    # budget is too tight for a real page transition.
    expect.set_options(timeout=DEFAULT_TIMEOUT_MS)

    if SCREENSHOT_DIR.exists() and os.environ.get("QS_E2E_KEEP_SCREENSHOTS") != "1":
        shutil.rmtree(SCREENSHOT_DIR)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# STACK
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def backend_port() -> int:
    return free_port()


@pytest.fixture(scope="session")
def backend_stub(backend_port):
    """The healthy backend used by the main user journey."""
    if os.environ.get("QS_E2E_BASE_URL"):
        yield None
        return
    proc = start_backend_stub(backend_port, LOG_DIR)
    try:
        yield proc
    finally:
        proc.stop()


@pytest.fixture(scope="session")
def app_url(backend_stub, backend_port) -> str:
    """Base URL of the UI under test."""
    external = os.environ.get("QS_E2E_BASE_URL")
    if external:
        return external.rstrip("/")

    ui_port = free_port()
    proc = start_streamlit(
        ui_port, f"http://127.0.0.1:{backend_port}/api", LOG_DIR
    )
    try:
        yield f"http://127.0.0.1:{ui_port}"
    finally:
        proc.stop()


@pytest.fixture(scope="session")
def unreachable_backend_app_url():
    """A UI wired to a backend that is not listening.

    Used to prove the unavailable-backend path (DV-HUNG-05) in the browser,
    rather than only at the unit level.
    """
    if os.environ.get("QS_E2E_BASE_URL"):
        # This fixture always starts its own local Streamlit, so in external
        # mode it would quietly test localhost and file the result as staging
        # evidence. Fail loudly instead of producing a misleading pass.
        pytest.fail(
            "The unavailable-backend tests need a UI they control and cannot "
            "describe a deployed environment. Select the staging acceptance "
            "set with -m 'e2e and staging'.",
            pytrace=False,
        )

    dead_port = free_port()  # nothing is started on it
    ui_port = free_port()
    proc = start_streamlit(
        ui_port,
        f"http://127.0.0.1:{dead_port}/api",
        LOG_DIR,
        QS_BACKEND_CONNECT_TIMEOUT="2",
        QS_BACKEND_READ_TIMEOUT="2",
    )
    try:
        yield f"http://127.0.0.1:{ui_port}"
    finally:
        proc.stop()


# ──────────────────────────────────────────────────────────────────────────────
# BROWSER
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def playwright_instance():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as instance:
        yield instance


@pytest.fixture(scope="session")
def browser(playwright_instance):
    headed = os.environ.get("QS_E2E_HEADED") == "1"
    launched = playwright_instance.chromium.launch(headless=not headed)
    try:
        yield launched
    finally:
        launched.close()


def _http_credentials() -> dict:
    """Basic-auth credentials for a protected staging UI (DV-HUNG-06/07).

    Credentials embedded in a URL (https://user:pass@host) are not attached to
    Streamlit's websocket or XHR requests, so the app authenticates the first
    document and then fails every rerun. Playwright has to carry them on the
    browser context instead.

    Read from the environment rather than argv so a reviewer password never
    lands in a process listing or a CI log.
    """
    username = os.environ.get("QS_E2E_HTTP_USER")
    password = os.environ.get("QS_E2E_HTTP_PASSWORD")
    if not username or not password:
        return {}
    return {"http_credentials": {"username": username, "password": password}}


@pytest.fixture
def page(browser):
    """A fresh browser context per test, so Streamlit session state is clean."""
    context = browser.new_context(
        viewport={"width": 1600, "height": 1100},
        **_http_credentials(),
    )
    context.set_default_timeout(DEFAULT_TIMEOUT_MS)
    new_page = context.new_page()
    try:
        yield new_page
    finally:
        context.close()


@pytest.fixture(autouse=True)
def reset_backend_faults(backend_port, request):
    """Clear injected faults after every test.

    The stub is session-scoped, so a fault left behind by an error-handling
    test would silently break every later test that shares it.
    """
    yield
    if os.environ.get("QS_E2E_BASE_URL"):
        return
    import urllib.error
    import urllib.request

    try:
        urllib.request.urlopen(
            urllib.request.Request(
                f"http://127.0.0.1:{backend_port}/api/_control/reset",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            ),
            timeout=5,
        ).close()
    except (urllib.error.URLError, OSError):
        # The stub may not have been started for this test.
        pass


@pytest.fixture
def sample_csv(tmp_path) -> Path:
    """A small, realistic operational file for the upload step."""
    path = tmp_path / "monthly_inspection_results.csv"
    path.write_text(
        "inspection_id,site,inspection_date,defects_found,status\n"
        "INS-1001,Hanoi Plant,2026-07-02,3,closed\n"
        "INS-1002,Da Nang Plant,2026-07-09,0,closed\n"
        "INS-1003,Hanoi Plant,2026-07-16,7,open\n"
        "INS-1004,Can Tho Plant,2026-07-23,1,open\n"
        "INS-1005,Da Nang Plant,2026-07-30,2,closed\n",
        encoding="utf-8",
    )
    return path
