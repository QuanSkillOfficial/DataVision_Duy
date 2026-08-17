import pandas as pd
import streamlit as st

from demo.config import get_mode_label
from demo.helpers.release_identity import probe_backend_health
from demo.helpers.ui_status import guard_response, render_release_identity
from demo.services.service_client import get_dashboard_metrics, get_recent_activity
from utils import display_kpi_cards


def _render_system_health():
    """Report the real state of the platform dependencies.

    DV-HUNG-05: the previous version hardcoded four "✓ Operational" rows, which
    stayed green even when the backend was down. Health is now derived from an
    actual probe, and fixture mode is labelled as such.
    """
    st.subheader("System Health")
    health = probe_backend_health()

    if health["state"] == "live":
        st.success(f"Backend: reachable ({health.get('service') or 'unnamed service'})")
        if health.get("latency_ms") is not None:
            st.caption(f"Health check latency: {health['latency_ms']} ms")
    elif health["state"] == "unreachable":
        st.error(f"Backend: {health['message']}")
        st.caption(health["hint"])
    else:
        st.info("Backend: not contacted — the UI is running on repository fixtures.")
        st.caption(health["hint"])

    st.caption(f"Data mode: {get_mode_label()}")


def main():
    """Render home page."""
    st.title("🏠 Home")
    st.markdown("Welcome to the Quansolution Platform Dashboard")

    # KPI Cards — sourced from the service layer, not from constants.
    st.subheader("Key Performance Indicators")
    metrics_response = get_dashboard_metrics(st.session_state.get("source_context", []))
    signals = guard_response(
        metrics_response,
        "Dashboard metrics service",
        what_is_missing="Platform KPIs cannot be shown while the metrics service is unavailable.",
    )

    if signals is not None:
        records_read = signals.get("records_read", signals.get("record_count", 0))
        kpis = [
            {"label": "Sources", "value": f"{signals.get('source_count', 0):,}"},
            {"label": "Records Read", "value": f"{records_read:,}"},
            {"label": "Data Quality", "value": f"{signals.get('data_quality_score', 0)}%"},
            {"label": "Review Queue", "value": f"{signals.get('prediction_review_queue_count', 0):,}"},
        ]
        display_kpi_cards(kpis)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        _render_system_health()

    with col2:
        st.subheader("Quick Start")
        if st.button("📤 Upload Data"):
            st.session_state.page = "upload"
            st.session_state.pending_navigation_choice = "Upload"
            st.rerun()
        if st.button("📊 View Dashboard"):
            st.session_state.page = "dashboard"
            st.session_state.pending_navigation_choice = "Dashboard"
            st.rerun()
        if st.button("💬 Ask Chatbot"):
            st.session_state.page = "chatbot"
            st.session_state.pending_navigation_choice = "Chatbot"
            st.rerun()

    st.markdown("---")

    st.subheader("Release Identity")
    render_release_identity(compact=False)

    st.markdown("---")

    # Recent Activity — real platform events, with an explicit empty state.
    st.subheader("Recent Activity")
    activity = guard_response(
        get_recent_activity(),
        "Recent activity service",
        what_is_missing="Recent platform activity cannot be shown right now.",
    )
    if activity:
        st.dataframe(pd.DataFrame(activity), use_container_width=True, hide_index=True)
    elif activity is not None:
        st.info("No recent activity recorded for the current data.")


if __name__ == "__main__":
    main()
