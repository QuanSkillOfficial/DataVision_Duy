import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from textwrap import dedent

from domain_config import (
    DEFAULT_DOMAIN_KEY,
    get_domain_config,
    get_domain_dashboard_config,
    get_domain_data_categories,
    get_domain_names,
    get_domain_processing_options,
    get_domain_report_config,
    get_domain_suggestion_config,
    get_domain_source_systems,
)

def apply_custom_styling():
    """Apply custom CSS styling to the Streamlit app."""
    st.markdown("""
        <style>
        .main {
            max-width: 1400px;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            font-size: 14px;
            opacity: 0.9;
        }
        .suggestion-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 15px;
        }
        .priority-high {
            color: #ef4444;
            font-weight: bold;
        }
        .priority-medium {
            color: #f59e0b;
            font-weight: bold;
        }
        .priority-low {
            color: #10b981;
            font-weight: bold;
        }
        .flow-stepper {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 8px;
            margin: 8px 0 14px 0;
        }
        .flow-step {
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 10px 12px;
            background: #ffffff;
            min-height: 104px;
        }
        .flow-step-active {
            border-color: #0078D4;
            box-shadow: 0 0 0 2px rgba(0, 120, 212, 0.14);
        }
        .flow-step-done {
            border-color: #107C10;
            background: #f3fbf4;
        }
        .flow-step-waiting {
            background: #f9fafb;
        }
        .flow-step-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: #323130;
            color: white;
            font-size: 13px;
            font-weight: 700;
            margin-right: 6px;
        }
        .flow-step-title {
            font-weight: 700;
            color: #111827;
        }
        .flow-step-small {
            font-size: 12px;
            color: #4b5563;
            margin-top: 6px;
            line-height: 1.35;
        }
        .flow-status-pill {
            display: inline-block;
            margin-top: 8px;
            padding: 2px 8px;
            border-radius: 999px;
            background: #e5e7eb;
            color: #111827;
            font-size: 12px;
            font-weight: 600;
        }
        .flow-data-path {
            border-left: 4px solid #0078D4;
            background: #f8fafc;
            padding: 10px 12px;
            margin: 8px 0 12px 0;
            border-radius: 6px;
            color: #1f2937;
        }
        </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render navigation sidebar and return page selection."""
    with st.sidebar:
        st.title("🎯 Quansolution Platform")
        st.markdown("---")

        nav_options = [
            ("home", "Home"),
            ("upload", "Upload"),
            ("dashboard", "Dashboard"),
            ("chatbot", "Chatbot"),
            ("prediction", "Prediction"),
            ("suggestions", "Suggestions"),
            ("reports", "Reports"),
        ]
        page_to_label = dict(nav_options)
        label_to_page = {label: page_key for page_key, label in nav_options}
        query_page = st.query_params.get("page")

        if query_page in page_to_label and query_page != st.session_state.get("_current_url_page"):
            st.session_state.page = query_page
            st.session_state.navigation_choice = page_to_label[query_page]
            st.session_state["_current_url_page"] = query_page

        if st.session_state.get("page") not in page_to_label:
            st.session_state.page = "home"
        current_label = page_to_label[st.session_state.page]
        if st.session_state.get("pending_navigation_choice"):
            st.session_state.navigation_choice = st.session_state.pop("pending_navigation_choice")
        elif st.session_state.get("navigation_choice") not in label_to_page:
            st.session_state.navigation_choice = current_label

        st.caption("Navigation")
        selected_label = st.radio(
            "Navigation",
            [label for _, label in nav_options],
            key="navigation_choice",
            label_visibility="collapsed",
        )
        st.session_state.page = label_to_page[selected_label]
        if st.query_params.get("page") != st.session_state.page:
            st.query_params["page"] = st.session_state.page
            st.session_state["_current_url_page"] = st.session_state.page

        st.markdown("---")
        st.subheader("Pipeline Status")
        for label, status in get_flow_statuses().items():
            st.caption(f"{label}: {status}")
        st.markdown("---")

        # DV-HUNG-04: real release/backend identity replaces the previous
        # hardcoded "Online / v2.1.0 / 12 users" placeholder, which could not
        # be used as release evidence.
        from demo.helpers.ui_status import render_release_identity

        render_release_identity()

        return st.session_state.page


def get_flow_statuses():
    """Return completion status for the upload analysis pipeline."""
    source_count = len(st.session_state.get("source_context", []))
    dashboard_ready = bool(st.session_state.get("panely_generated_dashboard"))
    suggestion_count = len(st.session_state.get("suggestions", []))
    report_ready = st.session_state.get("last_report_preview") is not None
    return {
        "Upload": "Done" if source_count else "Waiting",
        "Dashboard": "Done" if dashboard_ready else "Waiting",
        "Suggestions": "Done" if suggestion_count else "Waiting",
        "Reports": "Done" if report_ready else "Waiting",
    }


def render_pipeline_header():
    """Render the combined upload analysis pipeline header."""
    step_meta = {
        "upload": {
            "number": "1 of 1",
            "label": "Upload",
            "role": "Creates `source_context` from uploaded files or source links.",
        }
    }
    statuses = get_flow_statuses()
    step = step_meta["upload"]
    status = statuses.get(step["label"], "Waiting")
    state_class = "flow-step-done" if status == "Done" else "flow-step-waiting"

    step_card = dedent(f"""
    <div class="flow-step {state_class}">
        <div>
            <span class="flow-step-number">1</span>
            <span class="flow-step-title">{step['label']}</span>
        </div>
        <div class="flow-step-small">{step['role']}</div>
        <span class="flow-status-pill">{status}</span>
    </div>
    """).strip()

    st.markdown("### Upload Analysis Pipeline")
    st.markdown(
        dedent(f"""
        <div class="flow-stepper">
            {step_card}
        </div>
        <div class="flow-data-path">
            <strong>Data path:</strong>
            source_context
            <br>
            <strong>Main action:</strong> Upload once, then review the analysis below.
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )
    st.markdown("---")

def initialize_session_state():
    """Initialize session state variables."""
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "selected_document" not in st.session_state:
        st.session_state.selected_document = None
    if "upload_count" not in st.session_state:
        st.session_state.upload_count = 0
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    if "last_processed_sources" not in st.session_state:
        st.session_state.last_processed_sources = []
    if "source_context" not in st.session_state:
        st.session_state.source_context = []
    if "dashboard_signals" not in st.session_state:
        st.session_state.dashboard_signals = {}
    if "suggestions" not in st.session_state:
        st.session_state.suggestions = []
    if "report_evidence_context" not in st.session_state:
        st.session_state.report_evidence_context = {}
    if "selected_domain_context" not in st.session_state:
        st.session_state.selected_domain_context = DEFAULT_DOMAIN_KEY
    if "data_category" not in st.session_state:
        st.session_state.data_category = get_domain_data_categories(DEFAULT_DOMAIN_KEY)[0]
    if "source_system" not in st.session_state:
        st.session_state.source_system = get_domain_source_systems(DEFAULT_DOMAIN_KEY)[0]
    if "process_options" not in st.session_state:
        st.session_state.process_options = get_domain_processing_options(DEFAULT_DOMAIN_KEY)[:1]
    if "skip_empty_rows" not in st.session_state:
        st.session_state.skip_empty_rows = True
    if "auto_mapping" not in st.session_state:
        st.session_state.auto_mapping = True


def get_active_domain_context():
    """Return the currently selected domain context."""
    return st.session_state.get("selected_domain_context", DEFAULT_DOMAIN_KEY)


def get_active_domain_config():
    """Return the config for the active domain."""
    return get_domain_config(get_active_domain_context())


def render_domain_filter_controls(filters, key_prefix):
    """Render a list of domain-specific filters and return the selected values."""
    if not filters:
        return {}

    result = {}
    column_count = min(2, len(filters)) or 1
    columns = st.columns(column_count)

    for index, filter_config in enumerate(filters):
        column = columns[index % column_count]
        with column:
            label = filter_config.get("label", filter_config["key"])
            kind = filter_config.get("kind", "multiselect")
            widget_key = f"{key_prefix}_{filter_config['key']}"

            if kind == "date_range":
                default_end = datetime.now().date()
                default_start = default_end - timedelta(days=30)
                result[filter_config["key"]] = st.date_input(
                    label,
                    value=(default_start, default_end),
                    key=widget_key,
                )
            elif kind == "selectbox":
                options = filter_config.get("options", [])
                result[filter_config["key"]] = st.selectbox(
                    label,
                    options,
                    index=0 if options else None,
                    key=widget_key,
                )
            else:
                options = filter_config.get("options", [])
                default = filter_config.get("default", options[:1])
                result[filter_config["key"]] = st.multiselect(
                    label,
                    options,
                    default=default,
                    key=widget_key,
                )

    return result

def display_kpi_cards(kpis):
    """Display KPI cards in a grid layout."""
    cols = st.columns(len(kpis))
    for idx, col in enumerate(cols):
        with col:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{kpis[idx]['label']}</div>
                    <div class="metric-value">{kpis[idx]['value']}</div>
                </div>
            """, unsafe_allow_html=True)

def get_sample_activity():
    """Generate sample activity data."""
    activities = [
        {"timestamp": "2 hours ago", "user": "John Smith", "action": "Uploaded financial_report.pdf", "status": "✓ Completed"},
        {"timestamp": "4 hours ago", "user": "Sarah Johnson", "action": "Generated Q2 performance report", "status": "✓ Completed"},
        {"timestamp": "6 hours ago", "user": "Mike Chen", "action": "Ran sales forecast", "status": "✓ Completed"},
        {"timestamp": "1 day ago", "user": "Emily Davis", "action": "Updated data categories", "status": "✓ Completed"},
        {"timestamp": "2 days ago", "user": "Alex Rodriguez", "action": "Submitted feedback", "status": "✓ Completed"},
    ]
    return pd.DataFrame(activities)

def get_sample_metrics(domain_context=None):
    """Generate sample metrics data for the active or requested domain."""
    active_domain = domain_context or get_active_domain_context()
    domain_config = get_domain_dashboard_config(active_domain)
    seed = sum((index + 1) * ord(char) for index, char in enumerate(active_domain))
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=datetime.now(), periods=30)
    data = {"Date": dates}

    for series in domain_config.get("series", []):
        baseline = np.linspace(series["min"], series["max"], 30)
        noise_range = max((series["max"] - series["min"]) * 0.08, 0.1)
        noise = rng.normal(0, noise_range, 30)
        data[series["name"]] = np.clip(baseline + noise, series["min"], series["max"])

    return pd.DataFrame(data)

def get_sample_suggestions(domain_context=None):
    """Generate sample suggestions for the active or requested domain."""
    return get_domain_suggestion_config(domain_context or get_active_domain_context()).get("examples", [])


def render_connection_status(service_name: str, mode: str = "mock") -> None:
    """Render a small connection status indicator for a named service.

    The connection mode (mock vs backend) is determined dynamically
    based on the USE_BACKEND flag in config.py.
    """
    try:
        from config import USE_BACKEND
        actual_mode = "backend" if USE_BACKEND else "mock"
    except ImportError:
        actual_mode = mode

    label = "Mock Demo" if actual_mode == "mock" else ("Backend Connected" if actual_mode == "backend" else actual_mode)
    
    try:
        st.caption(f"{service_name} - {label}")
    except Exception:
        # Fail silently in non-streamlit contexts
        pass


def get_active_sources() -> list:
    """Get the current active or processed sources from session state.

    Falls back in order from 'source_context', 'last_processed_sources',
    and 'uploaded_files'. Returns an empty list if none exist.
    """
    return (
        st.session_state.get("source_context")
        or st.session_state.get("last_processed_sources")
        or st.session_state.get("uploaded_files", [])
    )


def get_validated_domain_context() -> str:
    """Get the active domain context and validate it against the registry."""
    domain_options = get_domain_names()
    current_domain = st.session_state.get("selected_domain_context")
    if current_domain not in domain_options:
        current_domain = DEFAULT_DOMAIN_KEY
        st.session_state["selected_domain_context"] = current_domain
    return current_domain


def get_source_name(source: dict) -> str:
    """Extract standard source name from a source dictionary."""
    return source.get("filename") or source.get("name") or source.get("value", "Unnamed source")


def get_source_type(source: dict) -> str:
    """Extract standard source type/kind from a source dictionary."""
    return source.get("source_type") or source.get("type", "unknown")



