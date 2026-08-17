"""
demo/helpers/ui_status.py
===========================
Streamlit rendering for release identity and service failures.

Covers two Week 8 acceptance requirements:

  DV-HUNG-04  Reviewers can confirm which release and backend the UI is using.
  DV-HUNG-05  The UI reports actionable errors and never presents stale
              fixture success as live data.

Every page that calls the service layer should route failures through
`render_service_error()` instead of rendering a bare exception or, worse,
silently falling back to fixture content.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from demo.helpers.release_identity import (
    get_release_identity,
    probe_backend_health,
    release_match_state,
)
from demo.services.service_errors import describe_error, is_error

# Stable DOM markers so the Playwright browser suite can assert on UI state
# without depending on wording that a copy edit might change.
RELEASE_IDENTITY_TESTID = "qs-release-identity"
SERVICE_ERROR_TESTID = "qs-service-error"

_STATE_BADGE = {
    "live": ("🟢", "Backend live"),
    "unreachable": ("🔴", "Backend unreachable"),
    "fixture": ("⚪", "Fixture mode - no backend"),
}


def render_release_identity(compact: bool = True) -> dict:
    """Render the release/environment/backend identity block.

    Returns the resolved identity so callers can reuse it without probing the
    backend twice.
    """
    identity = get_release_identity()
    health = probe_backend_health()
    match_state = release_match_state(identity["release_sha"], health.get("release_sha"))

    icon, state_label = _STATE_BADGE.get(health["state"], ("⚪", health["state"]))

    st.markdown(
        f'<div data-testid="{RELEASE_IDENTITY_TESTID}" '
        f'data-environment="{identity["environment"]}" '
        f'data-release-sha="{identity["release_sha"]}" '
        f'data-data-mode="{identity["data_mode"]}" '
        f'data-backend-state="{health["state"]}" '
        f'data-release-match="{match_state}"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(f"**Release identity**  \n{icon} {state_label}")
    st.caption(f"Environment: `{identity['environment']}`")
    st.caption(f"UI release: `{identity['release_sha_short']}`")
    st.caption(f"Data mode: `{identity['data_mode_label']}`")

    if identity["backend_base_url"]:
        st.caption(f"Backend: `{identity['backend_base_url']}`")

    if health["state"] == "live":
        from demo.helpers.release_identity import _short_sha

        st.caption(f"Backend release: `{_short_sha(str(health.get('release_sha') or ''))}`")
        if health.get("latency_ms") is not None:
            st.caption(f"Health latency: `{health['latency_ms']} ms`")
        if match_state == "mismatch":
            st.warning(
                "UI and backend report different release SHAs. Acceptance "
                "evidence from this session covers two different builds."
            )
    elif health["state"] == "unreachable":
        st.error(health["message"])
        st.caption(health["hint"])
    else:
        st.caption("Data shown on this page comes from repository fixtures.")

    if not compact:
        st.caption(f"Image digest: `{identity['image_digest']}`")
        st.caption(f"Build timestamp: `{identity['build_timestamp']}`")

    return identity


def render_service_error(
    response: Any,
    service_label: str,
    what_is_missing: Optional[str] = None,
) -> dict:
    """Render an actionable failure block for a service response.

    `what_is_missing` states plainly which part of the page cannot be shown, so
    a reviewer never has to guess whether the remaining content is live.
    """
    described = describe_error(response, service_label)

    st.markdown(
        f'<div data-testid="{SERVICE_ERROR_TESTID}" '
        f'data-service="{service_label}" '
        f'data-error-kind="{described["kind"]}"></div>',
        unsafe_allow_html=True,
    )

    st.error(f"{service_label}: {described['message']}")
    if what_is_missing:
        st.warning(what_is_missing)
    st.caption(f"What to do: {described['hint']}")

    with st.expander("Technical detail for the release evidence"):
        st.write(f"Failure kind: `{described['kind']}`")
        if described["endpoint"]:
            st.write(f"Endpoint: `{described['endpoint']}`")
        st.code(described["detail"] or "No detail reported.", language="text")

    return described


def guard_response(
    response: Any,
    service_label: str,
    what_is_missing: Optional[str] = None,
) -> Optional[Any]:
    """Return `response["data"]` on success, or render the error and return None.

    This is the pattern pages should use: it makes a failed dependency a
    visible, explained gap rather than a traceback or a silent fixture fallback.
    """
    if is_error(response):
        render_service_error(response, service_label, what_is_missing)
        return None
    return response.get("data")
