import pandas as pd
import streamlit as st

from demo.config import get_mode_label
from demo.helpers.ui_status import guard_response
from demo.services.service_client import generate_report
from domain_config import DEFAULT_DOMAIN_KEY, get_domain_config, get_domain_names


def _source_context():
    return st.session_state.get("source_context") or st.session_state.get("last_processed_sources", [])


def _source_metadata_for_evidence():
    metadata = []
    for source in _source_context():
        metadata.append({k: v for k, v in source.items() if k != "content"})
    return metadata


def _markdown_from_report_preview(report_preview, evidence_preview=None):
    if report_preview.empty:
        return ""

    title_rows = report_preview[report_preview["Section"] == "Title"]
    title = title_rows.iloc[0]["Preview"] if not title_rows.empty else "Report Draft"
    lines = [f"### {title}"]

    for _, row in report_preview.iterrows():
        section = row["Section"]
        if section == "Title":
            continue
        lines.append(f"#### {section}")
        lines.append(str(row["Preview"]))

    if evidence_preview is not None and not evidence_preview.empty:
        lines.append("#### Structured Evidence Table")
        headers = list(evidence_preview.columns)
        table_headers = " | ".join(headers)
        table_separators = " | ".join(["---"] * len(headers))
        table_lines = [
            f"| {table_headers} |",
            f"| {table_separators} |"
        ]
        for _, row in evidence_preview.iterrows():
            cells = [str(row[h]).replace("|", "\\|") for h in headers]
            table_lines.append("| " + " | ".join(cells) + " |")
        lines.append("\n".join(table_lines))

    return "\n\n".join(lines)


def main():
    """Render the cross-module report builder page."""
    st.title("📑 Reports")
    st.caption(f"Data mode: {get_mode_label()}")
    st.caption(
        "Evidence sources: ingestion logs (Duy) → analytics views (Phat) → "
        "prediction result (Tuong) → RAG citations (Lap) → suggestions"
    )

    domain_options = get_domain_names()
    if st.session_state.get("selected_domain_context") not in domain_options:
        st.session_state["selected_domain_context"] = DEFAULT_DOMAIN_KEY

    active_domain = st.session_state["selected_domain_context"]
    domain_config = get_domain_config(active_domain)
    suggestions = st.session_state.get("suggestions", [])

    if not suggestions:
        st.warning(
            "⚠️ No suggestions available yet. "
            "The report will render with 'Not available in current data.' "
            "for the Recommendations section. "
            "Visit the Suggestions page first to generate ranked action items."
        )

    evidence_context = {
        "source_context": _source_metadata_for_evidence(),
        "dashboard_signals": st.session_state.get("dashboard_signals", {}),
        "suggestions": suggestions,
        "prediction_result": st.session_state.get("prediction_result", {}),
        "rag_context": st.session_state.get("last_rag_response", {}),
        "domain_label": domain_config["label"],
        "report_type": "Suggestion Summary",
        "audience": "General",
    }
    st.session_state["report_evidence_context"] = evidence_context

    response = generate_report(evidence_context)
    report_payload = guard_response(
        response,
        "Report service",
        what_is_missing=(
            "No report draft or evidence table can be produced. A report is "
            "only valid when every evidence row comes from a live module."
        ),
    )
    if report_payload is None:
        return

    st.session_state.last_report_preview = pd.DataFrame(report_payload.get("sections", []))
    st.session_state.last_report_evidence_table = report_payload.get("evidence_table", [])

    st.markdown("---")
    st.subheader("Report Draft Preview")
    for _, row in st.session_state.last_report_preview.iterrows():
        section = row["Section"]
        if section == "Title":
            continue
        with st.expander(section, expanded=section in {"Executive Summary", "Recommendations"}):
            st.markdown(str(row["Preview"]))

    st.markdown("---")
    st.subheader("Evidence Table")
    st.caption(
        "Traces every claim back to its originating module, source view, "
        "and value."
    )
    evidence_table = st.session_state.last_report_evidence_table
    if evidence_table:
        evidence_df = pd.DataFrame(evidence_table)
        st.dataframe(evidence_df, use_container_width=True, hide_index=True)
    else:
        evidence_df = None
        st.info("Not available in current data.")

    markdown_draft = _markdown_from_report_preview(
        st.session_state.last_report_preview,
        evidence_df
    )
    st.download_button(
        "Download Markdown Draft",
        markdown_draft.encode("utf-8"),
        file_name=f"{active_domain.lower().replace(' ', '_')}_suggestion_summary.md",
        mime="text/markdown",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
