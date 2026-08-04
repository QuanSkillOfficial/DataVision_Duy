"""
demo/helpers/pipeline_flow.py
================================
Điều phối pipeline: upload → dashboard metrics → suggestions → report.
Sử dụng demo.services.service_client (interface chuẩn Tuần 5),
bóc tách envelope ["data"] trước khi lưu vào session_state.
"""

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from demo.services.service_client import (
    get_dashboard_metrics,
    generate_suggestions,
    generate_report,
)
from prompt_templates import build_report_prompt
from evidence_builder import (
    build_pipeline_evidence_context,
    pipeline_analysis_context,
)


def run_pipeline(sources: list, domain_config: dict, initialize_suggestions: bool = False) -> None:
    """
    Chạy pipeline đầy đủ sau khi người dùng upload source:
    1. Lấy dashboard metrics (bóc tách envelope)
    2. Sinh suggestions nếu initialize_suggestions=True
    3. Xây dựng evidence context
    4. Sinh report draft (bóc tách envelope)
    """
    # --- Bước 1: Dashboard metrics (bóc tách envelope) ---
    dashboard_response = get_dashboard_metrics(sources)
    dashboard_signals = dashboard_response.get("data", {})

    # --- Bước 2: Suggestions (bóc tách envelope) ---
    suggestions = []
    if initialize_suggestions:
        suggestions_response = generate_suggestions({
            "dashboard_signals": dashboard_signals,
        })
        suggestions = suggestions_response.get("data", [])

    # --- Bước 3: Evidence context ---
    evidence_context = build_pipeline_evidence_context(
        sources,
        dashboard_signals,
        suggestions,
        domain_config["label"],
    )

    # --- Bước 4: Report prompt ---
    prompt = build_report_prompt(
        domain_context=st.session_state["selected_domain_context"],
        data_category=st.session_state.get("data_category", "Unspecified"),
        report_type=evidence_context["report_type"],
        content_sections=[
            "Executive Summary",
            "Evidence Used",
            "Key Findings",
            "Risks or Issues",
            "Recommendations",
            "Data Quality Limitations",
            "Next Actions",
        ],
        filter_context={
            "time_period": evidence_context["time_period"],
            "audience": evidence_context["audience"],
            "included_context": evidence_context["included_context"],
            "pipeline_page": "Upload",
        },
        analysis_context=pipeline_analysis_context(evidence_context),
    )

    # --- Bước 5: Report draft (bóc tách envelope) ---
    report_response = generate_report(evidence_context)
    report_payload = report_response.get("data", {})

    # --- Lưu kết quả vào session_state ---
    st.session_state["dashboard_signals"] = dashboard_signals
    st.session_state["suggestions"] = suggestions
    st.session_state["report_evidence_context"] = evidence_context
    st.session_state.last_report_prompt = prompt
    st.session_state.last_report_preview = pd.DataFrame(report_payload.get("sections", []))
    st.session_state.last_report_evidence = pd.DataFrame(report_payload.get("evidence_table", []))


def ensure_pipeline_outputs(domain_config: dict) -> None:
    """Chạy pipeline nếu session_state chưa có kết quả."""
    sources = st.session_state.get("source_context", [])
    if not sources:
        return
    if (
        not st.session_state.get("dashboard_signals")
        or not st.session_state.get("report_evidence_context")
        or st.session_state.get("last_report_preview") is None
    ):
        run_pipeline(
            sources,
            domain_config,
            initialize_suggestions=bool(st.session_state.get("panely_generated_dashboard")),
        )


def render_pipeline_dashboard(signals: dict) -> None:
    """Hiển thị 4 metric cards + bảng tín hiệu dashboard."""
    metric_cols = st.columns(4)
    metric_cols[0].metric("Sources", signals.get("source_count", 0))
    metric_cols[1].metric("Records / Lines", signals.get("record_count") or "N/A")
    metric_cols[2].metric("Quality Score", f"{signals.get('data_quality_score', 0)}%")
    metric_cols[3].metric("Readiness", "Ready" if signals.get("processing_status") == "ready" else "Waiting")

    signal_df = pd.DataFrame([
        {"Signal": "Parsing coverage", "Value": f"{signals.get('parsing_coverage', 0):.0%}"},
        {"Signal": "Duplicate risk", "Value": signals.get("duplicate_risk", "unknown")},
        {"Signal": "Files", "Value": str(signals.get("file_count", 0))},
        {"Signal": "Links", "Value": str(signals.get("link_count", 0))},
    ])
    st.dataframe(signal_df, use_container_width=True, hide_index=True)


def render_pipeline_suggestions(suggestions: list) -> None:
    """Hiển thị bảng suggestions có chấm điểm."""
    st.subheader("Stage 3. Scored Suggestions")
    ranking_df = pd.DataFrame([
        {
            "Priority": suggestion.get("final_priority", suggestion.get("priority")),
            "Title": suggestion["title"],
            "Final Score": suggestion.get("final_score", 0),
            "Urgency": suggestion.get("urgency_score", 0),
            "Impact": suggestion.get("impact_score", 0),
            "Confidence": suggestion.get("confidence_score", 0),
            "Effort": suggestion.get("effort_score", 0),
            "Source Signal": suggestion.get("source_signal", ""),
        }
        for suggestion in suggestions
    ])
    st.dataframe(ranking_df, use_container_width=True, hide_index=True)


def render_suggestion_preview(suggestions: list) -> None:
    """Hiển thị top-3 suggestions dạng danh sách HTML."""
    st.subheader("Suggestions")
    st.caption("Top 3 highest-score suggestions generated after the dashboard finishes.")

    top_suggestions = sorted(
        suggestions,
        key=lambda suggestion: suggestion.get("final_score", 0),
        reverse=True,
    )[:3]

    if not top_suggestions:
        st.info("Suggestions will appear after the dashboard has enough signal context.")
        return

    list_items = []
    for index, suggestion in enumerate(top_suggestions, start=1):
        priority = suggestion.get("final_priority", suggestion.get("priority", "Medium"))
        priority_class = priority.lower() if priority in {"High", "Medium", "Low"} else "medium"
        list_items.append(f"""
            <div class="suggestion-preview-item">
                <div class="suggestion-rank">{index}</div>
                <div class="suggestion-preview-content">
                    <div class="suggestion-preview-title">{escape(suggestion.get('title', 'Untitled suggestion'))}</div>
                    <div class="suggestion-preview-signal">{escape(suggestion.get('source_signal', 'Mock dashboard signal'))}</div>
                </div>
                <div class="suggestion-preview-meta">
                    <span class="suggestion-priority suggestion-priority-{priority_class}">{escape(priority)}</span>
                    <span class="suggestion-score">Score {suggestion.get('final_score', 0):.2f}</span>
                </div>
            </div>
        """)

    st.markdown(f"""<div class="suggestion-preview-list">{''.join(list_items)}</div>""", unsafe_allow_html=True)

    if st.button("View more", key="view_more_suggestions"):
        st.session_state["suggestion_details_expanded"] = True
    if st.session_state.get("suggestion_details_expanded"):
        detail_rows = [
            {
                "Suggestion": suggestion.get("title", "Untitled suggestion"),
                "Description": suggestion.get("description", ""),
                "Why it matters": suggestion.get("why_it_matters", ""),
                "Next action": suggestion.get("next_action", ""),
                "Reason": suggestion.get("reason", ""),
            }
            for suggestion in top_suggestions
        ]
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)


def render_pipeline_report() -> None:
    """Hiển thị report draft đã sinh từ pipeline."""
    st.subheader("Stage 4. Report Draft")
    report_preview = st.session_state.get("last_report_preview")
    if report_preview is None:
        st.info("Run the upload pipeline to generate a report draft.")
        return

    st.dataframe(report_preview, use_container_width=True, hide_index=True)
    with st.expander("Strict Report Prompt Preview", expanded=False):
        st.code(st.session_state.get("last_report_prompt", ""), language="text")
