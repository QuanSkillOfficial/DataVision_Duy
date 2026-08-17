"""
tests/e2e/ui.py
=================
Streamlit-aware browser helpers for the Week 8 journey (DV-HUNG-02/03).

Streamlit re-runs the whole script on every interaction, so a click is not
finished when it returns - the page is finished when the run-status widget goes
away. Centralising that here keeps the journey test readable and keeps flaky
"element not ready" failures out of the evidence.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, expect

from tests.e2e.harness import SCREENSHOT_DIR

STATUS_WIDGET = '[data-testid="stStatusWidget"]'
RELEASE_IDENTITY = '[data-testid="qs-release-identity"]'
SERVICE_ERROR = '[data-testid="qs-service-error"]'


def open_app(page: Page, base_url: str) -> None:
    """Open the UI and wait for the first full render."""
    page.goto(base_url, wait_until="domcontentloaded")
    expect(page.get_by_test_id("stSidebar")).to_be_visible()
    wait_idle(page)


def wait_idle(page: Page, timeout: int = 60_000) -> None:
    """Wait until Streamlit has finished the current script run.

    Streamlit shows a run-status widget while the script re-executes. It only
    appears once the run is slow enough to be worth showing, so we wait briefly
    for it to appear and then wait for it to go away. Without the first wait,
    an assertion can read the page in the gap between the click and the rerun.
    """
    status = page.locator(STATUS_WIDGET)
    try:
        status.wait_for(state="visible", timeout=1_500)
    except Exception:
        pass
    try:
        status.wait_for(state="hidden", timeout=timeout)
    except Exception:
        pass
    page.wait_for_timeout(500)


def navigate(page: Page, label: str) -> None:
    """Move between pages via the sidebar.

    Deliberately not a URL jump: a reload would start a new Streamlit session
    and discard the session state built up earlier in the journey, which would
    make the "one continuous user journey" claim false.
    """
    radio = page.get_by_test_id("stSidebar").get_by_role("radio", name=label, exact=True)
    # Streamlit hides the real <input> and paints the visible control on the
    # surrounding <label>, so the label is what a user actually clicks.
    radio.locator("xpath=ancestor::label[1]").click()
    wait_idle(page)
    expect(page.get_by_test_id("stSidebar")).to_be_visible()


def expect_page(page: Page, title_fragment: str) -> None:
    """Assert which page the browser is on.

    Matches on the page title (h1) rather than on any heading, because page
    titles carry emoji prefixes and several pages repeat words like
    "Dashboard" or "Reports" in their sub-headings.
    """
    # The sidebar has its own h1 ("Quansolution Platform") on every page, so the
    # page title is "the first h1 that is not in the sidebar". Expressed as an
    # ancestor exclusion rather than a container test id, because the Chatbot
    # page uses st.chat_input, which changes which container wraps the title.
    #
    # Asserted on text rather than visibility: a long page can leave the title
    # scrolled out of the viewport while the user is unambiguously on that page.
    title = page.locator(
        'xpath=//h1[not(ancestor::*[@data-testid="stSidebar"])]'
    ).first
    expect(title).to_contain_text(title_fragment)


def click_button(page: Page, name: str, exact: bool = False) -> None:
    button = page.get_by_role("button", name=name, exact=exact).first
    button.scroll_into_view_if_needed()
    button.click()
    wait_idle(page)


def upload_file(page: Page, path: Path) -> None:
    page.locator('input[type="file"]').first.set_input_files(str(path))
    wait_idle(page)


def ask_chatbot(page: Page, question: str) -> None:
    chat_input = page.get_by_test_id("stChatInput").locator("textarea")

    # Typed key by key rather than filled: the chat box is a controlled React
    # component, so a programmatic value assignment leaves its internal state
    # empty and the send button never enables.
    #
    # Retried because a Streamlit rerun landing mid-type re-mounts the textarea
    # and silently drops what was typed. Asserting on the value we can actually
    # read is more reliable than adding a longer sleep.
    for attempt in range(3):
        chat_input.click()
        chat_input.press_sequentially(question, delay=15)
        page.wait_for_timeout(400)
        if chat_input.input_value().strip() == question:
            break
        wait_idle(page)
    else:
        raise AssertionError(
            f"Chat input did not retain the question after 3 attempts: {question!r}"
        )

    send = page.get_by_role("button", name="Send message")
    expect(send).to_be_enabled()
    send.click()
    wait_idle(page)


def release_identity(page: Page) -> dict:
    """Read the release identity the UI is advertising."""
    marker = page.locator(RELEASE_IDENTITY).first
    marker.wait_for(state="attached")
    return {
        "environment": marker.get_attribute("data-environment"),
        "release_sha": marker.get_attribute("data-release-sha"),
        "data_mode": marker.get_attribute("data-data-mode"),
        "backend_state": marker.get_attribute("data-backend-state"),
        "release_match": marker.get_attribute("data-release-match"),
    }


def service_errors(page: Page) -> list[dict]:
    """Every service failure block currently rendered on the page."""
    blocks = page.locator(SERVICE_ERROR)
    return [
        {
            "service": blocks.nth(index).get_attribute("data-service"),
            "kind": blocks.nth(index).get_attribute("data-error-kind"),
        }
        for index in range(blocks.count())
    ]


def page_text(page: Page) -> str:
    return page.locator("body").inner_text()


def capture(page: Page, name: str) -> Path:
    """Save a full-page screenshot as release evidence."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return path
