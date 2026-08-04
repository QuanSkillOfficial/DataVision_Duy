import pandas as pd
import streamlit as st

from domain_config import (
    DEFAULT_DOMAIN_KEY,
    get_domain_config,
    get_domain_data_categories,
    get_domain_names,
    get_domain_processing_options,
    get_domain_source_systems,
)
from pipeline_flow import run_pipeline
from source_context_builder import analyze_sources, build_source_entries, parse_links, preview_file, source_type_from_name
from utils import get_validated_domain_context


SUPPORTED_FILE_TYPES = ["csv", "xlsx", "xls", "json", "parquet", "png", "jpg", "jpeg", "webp"]


def _sync_domain_defaults(domain_key):
    category_options = get_domain_data_categories(domain_key)
    source_options = get_domain_source_systems(domain_key)
    processing_options = get_domain_processing_options(domain_key)

    if st.session_state.get("data_category") not in category_options:
        st.session_state["data_category"] = category_options[0]
    if st.session_state.get("source_system") not in source_options:
        st.session_state["source_system"] = source_options[0]

    selected_processing = [option for option in st.session_state.get("process_options", []) if option in processing_options]
    st.session_state["process_options"] = selected_processing or processing_options[:1]


def _render_upload_styles():
    st.markdown(
        """
        <style>
        .suggestion-preview-list { width: 100%; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; margin: 8px 0 12px 0; background: #ffffff; }
        .suggestion-preview-item { display: grid; grid-template-columns: 40px minmax(0, 1fr) auto; gap: 12px; align-items: start; border-bottom: 1px solid #e5e7eb; padding: 12px 14px; box-sizing: border-box; }
        .suggestion-preview-item:last-child { border-bottom: 0; }
        .suggestion-rank { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 999px; background: #f3f4f6; color: #111827; font-size: 13px; font-weight: 700; }
        .suggestion-preview-title { color: #111827; font-size: 15px; font-weight: 700; line-height: 1.35; overflow-wrap: anywhere; }
        .suggestion-preview-signal { color: #4b5563; font-size: 13px; line-height: 1.4; margin-top: 4px; overflow-wrap: anywhere; }
        .suggestion-preview-meta { display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex-wrap: wrap; }
        .suggestion-priority { border-radius: 999px; padding: 2px 8px; font-size: 12px; font-weight: 700; white-space: nowrap; }
        .suggestion-priority-high { background: #fee2e2; color: #991b1b; }
        .suggestion-priority-medium { background: #fef3c7; color: #92400e; }
        .suggestion-priority-low { background: #dcfce7; color: #166534; }
        .suggestion-score { color: #374151; font-size: 12px; font-weight: 600; white-space: nowrap; }
        @media (max-width: 720px) { .suggestion-preview-item { grid-template-columns: 32px minmax(0, 1fr); } .suggestion-preview-meta { grid-column: 2; justify-content: flex-start; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    _render_upload_styles()

    st.title("Upload")
    st.caption("Provide a dataset first. Once a file or link is available, AI will generate Dataset Analysis automatically.")

    domain_options = get_domain_names()


    active_domain = get_validated_domain_context()
    _sync_domain_defaults(active_domain)
    domain_config = get_domain_config(active_domain)

    st.session_state.setdefault("panely_analysis", None)
    st.session_state.setdefault("panely_generated_dashboard", None)
    st.session_state.setdefault("dashboard_template_choice", "")

    with st.container(border=True):
        st.markdown("### Provide Data")
        st.caption("Upload files or paste source links. At least one source is required before Dataset Analysis appears.")

        uploaded_files = st.file_uploader(
            "Upload files",
            type=SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            key="panely_uploaded_files",
        ) or []

        raw_links = st.text_area(
            "Source links",
            key="panely_source_links",
            placeholder="Paste one source URL per line",
            height=88,
        )
        links = parse_links(raw_links)

        with st.expander("Advanced source context", expanded=False):
            st.selectbox("Domain", domain_options, key="selected_domain_context")
            active_domain = st.session_state["selected_domain_context"]
            _sync_domain_defaults(active_domain)
            domain_config = get_domain_config(active_domain)
            st.selectbox("Source System", get_domain_source_systems(active_domain), key="source_system")
            st.selectbox("Data Category", get_domain_data_categories(active_domain), key="data_category")
            st.multiselect("Processing Options", get_domain_processing_options(active_domain), key="process_options")
            st.checkbox("Skip empty rows", value=True, key="skip_empty_rows")
            st.checkbox("Automatic column mapping", value=True, key="auto_mapping")

    source_signature = (tuple((file.name, file.size) for file in uploaded_files), tuple(links))
    source_count = len(uploaded_files) + len(links)

    if st.session_state.get("panely_upload_signature") != source_signature:
        st.session_state["panely_upload_signature"] = source_signature
        if source_count:
            st.session_state["panely_generated_dashboard"] = None
            st.session_state["dashboard_template_choice"] = ""
            st.session_state["suggestion_details_expanded"] = False
            st.session_state["suggestions"] = []
            analysis = analyze_sources(uploaded_files, links)
            processed_sources = build_source_entries(uploaded_files, links)
            st.session_state["panely_analysis"] = analysis
            st.session_state["uploaded_files"] = processed_sources
            st.session_state["last_processed_sources"] = processed_sources
            st.session_state["source_context"] = processed_sources
            run_pipeline(processed_sources, domain_config, initialize_suggestions=False)
        else:
            has_previous_source = bool(
                st.session_state.get("source_context")
                or st.session_state.get("last_processed_sources")
                or st.session_state.get("panely_analysis")
            )
            if not has_previous_source:
                st.session_state["panely_analysis"] = None
                st.session_state["uploaded_files"] = []
                st.session_state["last_processed_sources"] = []
                st.session_state["source_context"] = []
                st.session_state["dashboard_signals"] = {}
                st.session_state["suggestions"] = []
                st.session_state["report_evidence_context"] = {}
                st.session_state["last_report_preview"] = None
                st.session_state["last_report_prompt"] = ""

    analysis = st.session_state.get("panely_analysis")
    if analysis:
        display_source_count = source_count or len(st.session_state.get("source_context", []))
        st.markdown("---")
        with st.container(border=True):
            st.subheader("Dataset Analysis by AI")
            st.success(f"{display_source_count} source(s) detected. AI analysis is ready.")

            metric_cols = st.columns(4)
            metric_cols[0].metric("Detected Domain", analysis["detected_domain"])
            metric_cols[1].metric("Confidence", f"{analysis['confidence']:.0%}")
            metric_cols[2].metric("Rows", f"{analysis['row_count']:,}" if analysis["row_count"] else "N/A")
            metric_cols[3].metric("Columns", f"{analysis['column_count']:,}" if analysis["column_count"] else "N/A")

            st.markdown("#### Sources")
            if uploaded_files:
                for index, uploaded_file in enumerate(uploaded_files, start=1):
                    source_type = source_type_from_name(uploaded_file.name).upper()
                    with st.expander(f"{index}. {uploaded_file.name}", expanded=index == 1):
                        st.caption(f"Type: {source_type} | Size: {uploaded_file.size:,} bytes")
                        preview_file(uploaded_file)
            if links:
                for link in links:
                    st.write(link)
                    st.caption("Link captured for extraction and dashboard analysis.")

            detail_col, table_col = st.columns([0.85, 1.15], gap="large")
            with detail_col:
                st.markdown("#### Suggested Dashboard Focus")
                st.info(analysis["suggested_focus"])
                st.markdown("#### Key Detected Columns")
                if analysis["key_columns"]:
                    st.write(", ".join(analysis["key_columns"]))
                else:
                    st.caption("No tabular columns detected.")
            with table_col:
                st.markdown("#### Source Analysis")
                st.dataframe(pd.DataFrame(analysis["file_summaries"]), use_container_width=True, hide_index=True)
    else:
        st.markdown("---")
        st.info("Dataset Analysis will appear after you upload a supported file or paste a source link.")

    if analysis:
        st.markdown("#### Choose Dashboard Template")
        st.caption("Select one dashboard template to continue.")
        template_choice = st.session_state.get("dashboard_template_choice", "")
        template_cols = st.columns(2)
        dashboard_templates = {
            "ecommerce": {"label": "E-commerce Performance", "description": "Revenue, orders, AOV, returns, and fulfillment trends.", "chart_count": "6 charts"},
            "generic": {"label": "Generic Exploratory", "description": "Best-effort overview for unknown or mixed datasets.", "chart_count": "5 charts"},
        }
        for column, (template_key, template) in zip(template_cols, dashboard_templates.items()):
            with column:
                with st.container(border=True):
                    if template_choice == template_key:
                        st.success(template["label"])
                    else:
                        st.markdown(f"**{template['label']}**")
                    st.caption(template["description"])
                    st.caption(template["chart_count"])
                    if st.button("Selected" if template_choice == template_key else "Select template", key=f"select_template_{template_key}", disabled=template_choice == template_key):
                        st.session_state["dashboard_template_choice"] = template_key
                        st.session_state["panely_generated_dashboard"] = None
                        st.session_state["suggestions"] = []
                        st.session_state["suggestion_details_expanded"] = False
                        st.rerun()

        st.text_area("Describe what you want (Optional)", key="dashboard_description", placeholder="Example: Focus on revenue trends, top products, customer segments, and unusual changes.", height=110)

        generate_ready = st.session_state.get("dashboard_template_choice") in dashboard_templates
        generate_clicked = st.button("Generate Dashboard", disabled=not generate_ready, help=None if generate_ready else "Choose a dashboard template")

        if generate_clicked:
            template_key = st.session_state["dashboard_template_choice"]
            run_pipeline(st.session_state.get("source_context", []), domain_config, initialize_suggestions=False)
            st.session_state["panely_generated_dashboard"] = {
                "template": dashboard_templates[template_key]["label"],
                "analysis": st.session_state["panely_analysis"],
                "description": st.session_state.get("dashboard_description", ""),
            }
            st.session_state["suggestions"] = []
            st.session_state["suggestion_details_expanded"] = False
            st.session_state.page = "dashboard"
            st.session_state.pending_navigation_choice = "Dashboard"
            st.rerun()


if __name__ == "__main__":
    main()
