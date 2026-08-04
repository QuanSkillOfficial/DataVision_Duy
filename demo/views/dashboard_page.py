import pandas as pd
import streamlit as st

from domain_config import DEFAULT_DOMAIN_KEY, get_domain_names
from demo.config import USE_BACKEND, get_mode_label
from demo.services.service_client import (
    get_dashboard_metrics,
    get_ingestion_status,
    get_recent_activity,
    generate_suggestions,
)
from utils import (
    get_active_sources,
    get_source_name,
    get_source_type,
)


def _active_sources():
    """Get the active list of processed sources."""
    return get_active_sources()


def _quality_rows_from_signals(signals):
    return [
        {
            "Signal": "Completeness",
            "Score": signals.get("data_quality_score", 0),
            "Status": "From source context" if signals.get("source_count", 0) else "Waiting",
        },
        {
            "Signal": "Format validity",
            "Score": 90 if signals.get("source_count", 0) else 0,
            "Status": "Demo estimate",
        },
        {
            "Signal": "Parsing coverage",
            "Score": round(signals.get("parsing_coverage", 0.0) * 100),
            "Status": "From previewable sources",
        },
        {
            "Signal": "Duplicate risk",
            "Score": 25 if signals.get("duplicate_risk") == "high" else 95,
            "Status": "Lower risk is better",
        },
    ]


def _source_table(sources):
    rows = []
    for source in sources:
        rows.append(
            {
                "Source": get_source_name(source),
                "Type": get_source_type(source),
                "Domain": source.get("domain_context", st.session_state.get("selected_domain_context")),
                "Category": source.get("data_category", st.session_state.get("data_category", "Unspecified")),
                "System": source.get("source_system", st.session_state.get("source_system", "Unspecified")),
                "Status": "Processed",
            }
        )
    return pd.DataFrame(rows)


def _render_document_processing_status(status_breakdown):
    st.subheader("Document Processing Status")
    if not status_breakdown:
        st.info("Not available in current data.")
        return
    df = pd.DataFrame(
        [{"Document Type": k.replace("_", " ").title(), "Count": v}
         for k, v in status_breakdown.items()]
    )
    st.bar_chart(df.set_index("Document Type")["Count"], use_container_width=True)


def _render_recent_activity(activity):
    st.subheader("Recent Activity Logs")
    if not activity:
        st.info("Not available in current data.")
        return
    df = pd.DataFrame(activity)
    st.dataframe(df, use_container_width=True, hide_index=True)


def main():
    """Render universal data health and analytics dashboard."""
    st.title("Dashboard")
    st.caption(f"Data mode: {get_mode_label()}")

    generated_dashboard = st.session_state.get("panely_generated_dashboard")

    domain_options = get_domain_names()
    if st.session_state.get("selected_domain_context") not in domain_options:
        st.session_state["selected_domain_context"] = DEFAULT_DOMAIN_KEY

    sources = _active_sources()

    # ── Fetch through service layer (Duy + Phat) ──────────────────────────
    metrics_response = get_dashboard_metrics(sources)
    signals = metrics_response["data"]
    st.session_state["dashboard_signals"] = signals

    ingestion_response = get_ingestion_status()
    ingestion_run = ingestion_response.get("data", {})

    activity_response = get_recent_activity()
    activity = activity_response.get("data", [])

    if generated_dashboard:
        st.caption(
            f"Template: {generated_dashboard.get('template', 'N/A')} | "
            f"Detected domain: {generated_dashboard.get('analysis', {}).get('detected_domain', 'N/A')}"
        )
        if generated_dashboard.get("description"):
            st.write(generated_dashboard["description"])
    elif USE_BACKEND:
        st.caption(
            "Direct backend mode: live PostgreSQL analytics are loaded "
            "without requiring the Upload page first."
        )
    else:
        st.caption(
            "Direct fixture mode: Week 7 integration fixtures are loaded "
            "without requiring the Upload page first."
        )

    # ── Top KPIs ───────────────────────────────────────────────────────────
    st.subheader("Universal Data Health")
    kpi_cols = st.columns(5)
    kpi_cols[0].metric("Sources", signals.get("source_count", 0))
    kpi_cols[1].metric("Records Read", signals.get("records_read", signals.get("record_count", 0)))
    kpi_cols[2].metric("Records Valid", signals.get("records_valid", "N/A"))
    kpi_cols[3].metric("Quality Score", f"{signals.get('data_quality_score', 0)}%")
    kpi_cols[4].metric(
        "Readiness",
        "Ready" if signals.get("processing_status") == "ready" else "Waiting",
    )

    extra_cols = st.columns(3)
    extra_cols[0].metric("RAG Queries", signals.get("rag_query_count", 0))
    extra_cols[1].metric("Prediction Count", signals.get("prediction_count", 0))
    extra_cols[2].metric(
        "Latest Ingestion",
        ingestion_run.get("status", "Not available in current data.").upper(),
    )

    week7_cols = st.columns(4)
    week7_cols[0].metric(
        "Successful Runs",
        signals.get("successful_ingestion_runs", "N/A"),
    )
    week7_cols[1].metric(
        "RAG Ready Docs",
        signals.get("rag_ready_documents", 0),
    )
    week7_cols[2].metric(
        "Review Queue",
        signals.get("prediction_review_queue_count", 0),
    )
    latest_document = signals.get("latest_document", {}) or {}
    week7_cols[3].metric(
        "Latest Document",
        latest_document.get("document_external_id", "N/A"),
    )

    if st.button(
        "Generate Suggestions",
        use_container_width=True,
        disabled=signals.get("processing_status") != "ready",
    ):
        suggestions_response = generate_suggestions({
            "dashboard_signals": signals,
            "prediction_result": st.session_state.get("prediction_result", {}),
            "rag_context": st.session_state.get("last_rag_response", {}),
        })
        st.session_state["suggestions"] = suggestions_response["data"]
        st.session_state["suggestion_details_expanded"] = False
        st.session_state.page = "suggestions"
        st.session_state.pending_navigation_choice = "Suggestions"
        st.rerun()

    # ── Ingestion Run Panel ────────────────────────────────────────────────
    st.subheader("Ingestion Run Panel")
    with st.expander("🔍 Ingestion Stepper & Path Verification", expanded=True):
        st.markdown(f"""
        **Run ID:** `{ingestion_run.get('run_id', 'Not available in current data.')}`
        **Source Document:** `{ingestion_run.get('source_name', 'Not available in current data.')}` (`{ingestion_run.get('source_type', 'N/A')}`)
        **Pipeline Status:** `{ingestion_run.get('status', 'Not available in current data.')}`
        **File Hash (SHA-256):** `{ingestion_run.get('file_hash_sha256', 'Not available in current data.')}`
        """)

        st.markdown("##### Storage Directory Paths")
        path_cols = st.columns(3)
        path_cols[0].info(f"📁 **Raw Input Path**\n`{ingestion_run.get('raw_output_path', 'Not available in current data.')}`")
        path_cols[1].info(f"🔧 **Staging Path**\n`{ingestion_run.get('staging_output_path', 'Not available in current data.')}`")
        path_cols[2].info(f"✅ **Clean Output Path**\n`{ingestion_run.get('clean_output_path', 'Not available in current data.')}`")

    review_queue = signals.get("prediction_review_queue", [])
    st.subheader("Prediction Review Queue")
    if review_queue:
        st.dataframe(pd.DataFrame(review_queue), use_container_width=True, hide_index=True)
    else:
        st.info("No prediction review queue rows available in current fixture data.")

    # ── Data Quality Signals ──────────────────────────────────────────────
    st.subheader("Data Quality Signals")
    quality_df = pd.DataFrame(_quality_rows_from_signals(signals))
    st.dataframe(quality_df, use_container_width=True, hide_index=True)
    st.bar_chart(quality_df.set_index("Signal")["Score"], use_container_width=True)

    # ── Source Explorer ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Source Explorer")
    source_df = _source_table(sources)
    if source_df.empty:
        st.info("No processed sources yet. Use the Upload page to add a file or link first.")
    else:
        st.dataframe(source_df, use_container_width=True, hide_index=True)

    # ── Document Status & Activity ─────────────────────────────────────────
    st.markdown("---")
    _render_document_processing_status(signals.get("document_processing_status", {}))

    st.markdown("---")
    _render_recent_activity(activity)

    st.caption(
        "Flow: Duy ingestion logs -> Phat analytics views -> Dashboard UI. "
        "Saved to `st.session_state['dashboard_signals']` for Suggestions and Reports."
    )


if __name__ == "__main__":
    main()
