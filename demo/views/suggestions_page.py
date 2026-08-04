import pandas as pd
import streamlit as st

from demo.config import get_mode_label
from demo.services.service_client import generate_suggestions
from domain_config import DEFAULT_DOMAIN_KEY, get_domain_names


def _record_action(suggestion_id, action):
    st.session_state.setdefault("suggestion_status", {})
    st.session_state.setdefault("suggestion_action_history", [])
    st.session_state["suggestion_status"][suggestion_id] = action
    st.session_state["suggestion_action_history"].append(
        {"Suggestion": suggestion_id, "Action": action, "Status": "Demo only"}
    )


def main():
    """Render universal action suggestions page."""
    st.title("💡 Action Suggestions")
    st.caption(f"Data mode: {get_mode_label()}")

    dashboard_signals = st.session_state.get("dashboard_signals", {})
    prediction_result = st.session_state.get("prediction_result", {})
    rag_context = st.session_state.get("last_rag_response", {})

    # ── Cross-module signal banner ──────────────────────────────────────────
    if prediction_result.get("status") == "needs_review":
        st.warning(
            "⚠️ Prediction confidence is low for the current document. "
            "Suggestions below include a manual review recommendation."
        )
    if prediction_result.get("predicted_document_type"):
        st.info(
            f"📄 Document type detected: "
            f"**{prediction_result['predicted_document_type'].replace('_', ' ').title()}**"
        )
    if rag_context.get("status") == "no_match":
        st.warning(
            "⚠️ A recent chatbot question had no matching context. "
            "Suggestions below include a coverage recommendation."
        )

    if st.button("🔁 Refresh Suggestions from All Sources", use_container_width=True):
        response = generate_suggestions({
            "dashboard_signals": dashboard_signals,
            "prediction_result": prediction_result,
            "rag_context": rag_context,
        })
        st.session_state["suggestions"] = response.get("data", [])
        st.rerun()

    suggestions = st.session_state.get("suggestions", [])
    if not suggestions:
        st.info(
            "No suggestions yet. Visit the Dashboard page first, or click "
            "'Refresh Suggestions from All Sources' above."
        )
        return

    status_map = st.session_state.setdefault("suggestion_status", {})

    st.subheader("Recommended Actions")
    st.caption(
        "Evidence trace: Duy ingestion → Phat dashboard → Tuong prediction → "
        "Lap RAG → Suggestions"
    )

    ranking_df = pd.DataFrame([
        {
            "Priority": s.get("final_priority", s.get("priority", "Medium")),
            "Title": s.get("title", "Untitled"),
            "Final Score": s.get("final_score", 0.0),
            "Source Module": s.get("source_module", "Not available in current data."),
            "Source View": s.get("source_view", "Not available in current data."),
            "Evidence Type": s.get("evidence_type", "Not available in current data."),
            "Evidence Value": str(s.get("evidence_value", "Not available in current data.")),
            "Affected Document": s.get("affected_document", "Not available in current data."),
        }
        for s in suggestions
    ])
    st.dataframe(ranking_df, use_container_width=True, hide_index=True)

    if st.button("Generate Reports", use_container_width=True):
        st.session_state.page = "reports"
        st.session_state.pending_navigation_choice = "Reports"
        st.rerun()

    for suggestion in suggestions:
        suggestion_id = suggestion.get("title", "Untitled")
        status = status_map.get(suggestion_id, "New")

        with st.expander(
            f"{suggestion.get('final_priority', 'Medium')} | "
            f"{suggestion.get('title', 'Untitled')} | {status}",
            expanded=suggestion.get("final_priority") == "High",
        ):
            meta_col, detail_col = st.columns([1, 2])
            with meta_col:
                st.metric("Final Score", f"{suggestion.get('final_score', 0.0):.2f}")
                st.write(f"**Category:** {suggestion.get('category', 'N/A')}")
                st.write(f"**Difficulty:** {suggestion.get('difficulty', 'N/A')}")
                st.write(f"**Source module:** {suggestion.get('source_module', 'N/A')}")
                st.write(f"**Source view:** {suggestion.get('source_view', 'N/A')}")
                st.write(f"**Evidence type:** {suggestion.get('evidence_type', 'N/A')}")
                st.write(f"**Evidence value:** {suggestion.get('evidence_value', 'N/A')}")
                st.write(f"**Affected document:** {suggestion.get('affected_document', 'N/A')}")
                st.write(f"**Affected source:** {suggestion.get('affected_source', 'N/A')}")
                st.write(f"**Generated from:** {', '.join(suggestion.get('generated_from', []))}")
            with detail_col:
                st.write(suggestion.get("description", ""))
                st.write(f"**Why it matters:** {suggestion.get('why_it_matters', '')}")
                st.write(f"**Next action:** {suggestion.get('next_action', '')}")
                score_df = pd.DataFrame([
                    {"Score": "Urgency", "Value": suggestion.get("urgency_score", 0.0)},
                    {"Score": "Impact", "Value": suggestion.get("impact_score", 0.0)},
                    {"Score": "Confidence", "Value": suggestion.get("confidence_score", 0.0)},
                    {"Score": "Effort", "Value": suggestion.get("effort_score", 0.0)},
                ])
                st.dataframe(score_df, use_container_width=True, hide_index=True)

            action_col, dismiss_col = st.columns(2)
            with action_col:
                if st.button("Accept", key=f"accept_{suggestion_id}"):
                    _record_action(suggestion_id, "Accepted")
                    st.rerun()
            with dismiss_col:
                if st.button("Dismiss", key=f"dismiss_{suggestion_id}"):
                    _record_action(suggestion_id, "Dismissed")
                    st.rerun()

    st.markdown("---")
    st.subheader("Action History")
    history = st.session_state.get("suggestion_action_history", [])
    if history:
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
    else:
        st.info("No actions recorded yet.")


if __name__ == "__main__":
    main()
