import streamlit as st
from utils import display_kpi_cards, get_sample_activity

def main():
    """Render home page."""
    st.title("🏠 Home")
    st.markdown("Welcome to the Quansolution Platform Dashboard")

    # KPI Cards
    st.subheader("Key Performance Indicators")
    kpis = [
        {"label": "Total Files", "value": "1,247"},
        {"label": "Data Quality", "value": "89%"},
        {"label": "Active Users", "value": "324"},
        {"label": "Avg Response", "value": "2.3s"}
    ]
    display_kpi_cards(kpis)

    st.markdown("---")

    # System Health
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("System Health")
        health_metrics = {
            "Server Status": "✓ Operational",
            "Database": "✓ Operational",
            "API Gateway": "✓ Operational",
            "Cache Service": "✓ Operational"
        }
        for service, status in health_metrics.items():
            st.write(f"{service}: {status}")

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

    # Recent Activity
    st.subheader("Recent Activity")
    activity_df = get_sample_activity()
    st.dataframe(activity_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
