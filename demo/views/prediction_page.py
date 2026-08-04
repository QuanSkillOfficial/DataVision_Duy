import pandas as pd
import streamlit as st

from demo.config import PREDICTION_CONFIDENCE_THRESHOLD, get_mode_label
from demo.services.service_client import classify_document, submit_prediction_correction
from domain_config import DEFAULT_DOMAIN_KEY, get_domain_names


PREDICTION_USE_CASES = {
    "Document Type Classification": {
        "goal": "Predict what kind of document or source was uploaded.",
        "input_columns": "file_name, file_type, text_length, source_system, keywords",
        "target": "document_type",
        "model": "Logistic Regression / Random Forest",
        "metric": "Accuracy, F1 score",
        "value": "Routes documents to the right parser, workflow, and review queue.",
        "mock_result": "Predicted class: Contract / Report / Record",
    },
    "Ingestion Failure Prediction": {
        "goal": "Estimate whether a source is likely to fail parsing or validation.",
        "input_columns": "file_type, file_size, missing_values, schema_mismatch_count, source_system",
        "target": "will_fail_ingestion",
        "model": "Random Forest / Gradient Boosting",
        "metric": "Precision, recall",
        "value": "Warns users before bad files block the ingestion pipeline.",
        "mock_result": "Failure risk: Medium",
    },
    "Business Metric Prediction": {
        "goal": "Forecast a numeric metric from historical structured data.",
        "input_columns": "date, category, historical_value, seasonality, external_factors",
        "target": "future_value",
        "model": "Linear Regression / ARIMA / Prophet",
        "metric": "RMSE, MAE",
        "value": "Supports planning, budgeting, capacity management, and reporting.",
        "mock_result": "Next-period value: 108.4",
    },
    "Customer / Category Prediction": {
        "goal": "Predict a customer segment, item category, or routing label.",
        "input_columns": "profile_fields, transaction_history, behavior_score, source_category",
        "target": "customer_segment_or_category",
        "model": "Decision Tree / Random Forest",
        "metric": "Accuracy, macro F1",
        "value": "Improves personalization, classification, and downstream analytics.",
        "mock_result": "Predicted category: High-value / Priority / Standard",
    },
    "Anomaly Detection": {
        "goal": "Find unusual records, values, files, or operational patterns.",
        "input_columns": "numeric_fields, timestamp, frequency, source_system, historical_baseline",
        "target": "anomaly_score_or_flag",
        "model": "Isolation Forest / One-Class SVM",
        "metric": "Precision, recall, alert review rate",
        "value": "Surfaces fraud, data quality problems, operational risk, or unexpected behavior.",
        "mock_result": "Anomaly level: High",
    },
}

DOCUMENT_TYPE_LABELS = {
    "contract": "Contract",
    "invoice": "Invoice",
    "policy_document": "Policy Document",
    "report": "Report",
    "record": "Record",
    "financial_statement": "Financial Statement",
    "resume": "Resume",
    "research_paper": "Research Paper",
}

STATUS_DISPLAY = {
    "accepted": ("success", "Model suggestion saved"),
    "needs_review": ("warning", "Needs human review"),
    "waiting_for_source": ("info", "Awaiting better source text"),
    "failed": ("error", "Validation failed"),
}


def _display_label(label: str | None) -> str:
    if not label:
        return "Not available"
    return DOCUMENT_TYPE_LABELS.get(label, label.replace("_", " ").title())


def _confidence_policy(confidence: float, status: str) -> tuple[str, str, str]:
    if status == "waiting_for_source":
        return "Awaiting better source text", "#64748b", "Missing or insufficient extracted text."
    if status == "failed":
        return "Validation failed", "#dc2626", "Validation or system error."
    if confidence >= 0.80:
        return "High confidence", "#10b981", "Accepted for staging display."
    if confidence >= 0.60:
        return "Medium confidence", "#f59e0b", "Model suggestion; review recommended."
    return "Low confidence", "#dc2626", "Needs human review."


def _requirement_table():
    rows = []
    for use_case, config in PREDICTION_USE_CASES.items():
        rows.append(
            {
                "Use Case": use_case,
                "Input Columns Needed": config["input_columns"],
                "Target Variable": config["target"],
                "Model Type": config["model"],
                "Evaluation Metric": config["metric"],
                "Business Value": config["value"],
            }
        )
    return pd.DataFrame(rows)


def _mock_feature_importance(use_case):
    config = PREDICTION_USE_CASES[use_case]
    features = [item.strip() for item in config["input_columns"].split(",")[:4]]
    scores = [0.34, 0.27, 0.22, 0.17][: len(features)]
    return pd.DataFrame({"Feature": features, "Importance": scores})


def _sample_payload_for(source: dict) -> dict:
    """Build a Tuong-contract-compliant payload from an uploaded source."""
    return {
        "document_id": source.get("id", "doc-demo-001"),
        "source_id": source.get("source_id", "src-demo-001"),
        "file_name": source.get("filename") or source.get("name", "document.pdf"),
        "file_type": (source.get("source_type") or "pdf").lower(),
        "file_size": source.get("size", 153600),
        "text_length": len(source.get("original_text", "") or "") or 2800,
        "num_pages": source.get("num_pages", 8),
        "source_system": source.get("source_system", "external"),
        "extracted_text": source.get("original_text", "") or (
            "This agreement is entered into between the parties as of the "
            "date signed below. The vendor agrees to deliver the specified "
            "services within the timeline and budget outlined in Appendix A."
        ),
    }


def _render_prediction_result(result: dict, selected_use_case: str, selected_model: str) -> None:
    """Render the prediction result card per prediction_ui_response_contract."""
    status = result.get("status", "waiting_for_source")
    predicted_type = result.get("predicted_document_type")
    confidence = result.get("confidence", 0.0) or 0.0
    top_predictions = result.get("top_predictions", []) or []
    model_version = result.get("model_version", "unknown")
    review_reason = result.get("review_reason")

    st.subheader("🔮 Prediction Results")

    confidence_label, conf_color, confidence_note = _confidence_policy(confidence, status)
    alert_kind, alert_text = STATUS_DISPLAY.get(
        status, ("info", f"Status: {status}")
    )
    alert_fn = {"success": st.success, "warning": st.warning,
                "info": st.info, "error": st.error}[alert_kind]
    if status == "needs_review" and review_reason:
        alert_fn(f"{alert_text} — {review_reason}")
    else:
        alert_fn(alert_text)

    if status == "failed":
        if review_reason:
            st.code(review_reason, language="text")
        return

    if status == "waiting_for_source":
        return

    # UI Element 1: Prediction Result Card & UI Element 2: Confidence Badge
    st.markdown(f"""
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <h4 style="margin: 0; color: #64748b; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em;">Model Suggestion</h4>
                <p style="font-size: 26px; font-weight: bold; margin: 5px 0 0 0; color: #0f172a;">{_display_label(predicted_type)}</p>
            </div>
            <div style="background-color: {conf_color}22; border: 1px solid {conf_color}; color: {conf_color}; padding: 6px 14px; border-radius: 9999px; font-weight: bold; font-size: 14px;">
                {confidence_label}: {confidence:.0%}
            </div>
        </div>
        <div style="margin-top: 10px; color: #475569; font-size: 13px;">{confidence_note}</div>
        <div style="margin-top: 15px; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 10px;">
            <strong>Model Version:</strong> {model_version} &nbsp;|&nbsp; <strong>Engine Status:</strong> {status}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Manual Correction Feedback Form (Task 5)
    manual_review_required = (
        result.get("manual_review_required")
        or status == "needs_review"
        or (status == "accepted" and confidence < 0.80)
    )
    if manual_review_required:
        st.markdown("---")
        st.subheader("Manual Review / Correction")
        st.info("This is a model suggestion. Confirm or correct the document type before using it as final truth.")

        with st.form("prediction_correction_form"):
            options = [lbl for lbl in DOCUMENT_TYPE_LABELS.keys() if lbl != "record"]
            default_idx = options.index(predicted_type) if predicted_type in options else 0

            corrected_type = st.selectbox(
                "Correct Document Type",
                options=options,
                index=default_idx,
                format_func=lambda x: DOCUMENT_TYPE_LABELS.get(x, x)
            )

            reason = st.text_area(
                "Correction Reason / Notes",
                placeholder="Explain why this document type is selected (e.g. 'Manual review confirmed this is a contract')"
            )

            submitted = st.form_submit_button("Submit Correction", use_container_width=True)
            if submitted:
                if not reason.strip():
                    st.error("Please provide a reason for the correction.")
                else:
                    # Build Week 7 feedback payload for Tuong + Phat.
                    from datetime import datetime, timezone
                    feedback_payload = {
                        "prediction_log_id": result.get("prediction_log_id", 12),
                        "document_db_id": result.get("document_db_id"),
                        "document_external_id": result.get("document_external_id", "doc_dataflow_technical_report"),
                        "original_prediction": predicted_type,
                        "corrected_document_type": corrected_type,
                        "corrected_by": "reviewer",
                        "correction_reason": reason,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    resp = submit_prediction_correction(feedback_payload)

                    if resp.get("status") == "success":
                        st.success("Correction submitted successfully!")
                        # Dynamically update view state
                        result["status"] = "accepted"
                        result["predicted_document_type"] = corrected_type
                        result["confidence"] = 1.0
                        result["manual_review_required"] = False
                        result["review_reason"] = f"Manually corrected: {reason}"
                        st.session_state["prediction_result"] = result
                        st.rerun()
                    else:
                        error_msg = (
                            resp.get("data", {}).get("error")
                            or resp.get("metadata", {}).get("error")
                            or "Unknown error"
                        )
                        st.error(f"Failed to submit correction: {error_msg}")

    # UI Element 3: Top-3 Prediction Table
    if top_predictions:
        st.markdown("#### Top-3 Predictions Distribution")
        rows = []
        for pred in top_predictions[:3]:
            rows.append({
                "Predicted Label / Class": _display_label(pred.get("label")),
                "Probability Score": pred.get("score", 0.0),
            })
        df = pd.DataFrame(rows)
        st.dataframe(
            df.style.format({"Probability Score": "{:.0%}"}),
            use_container_width=True,
            hide_index=True,
        )
        for row in rows:
            st.progress(row["Probability Score"], text=f"{row['Predicted Label / Class']}: {row['Probability Score']:.0%}")

    # Chart Visualizations & Interpretation
    st.subheader("Feature Importance Preview")
    feature_df = _mock_feature_importance(selected_use_case)
    st.bar_chart(feature_df.set_index("Feature")["Importance"], use_container_width=True)

    st.subheader("Interpretation")
    config = PREDICTION_USE_CASES[selected_use_case]
    st.write(config["goal"])
    st.write(f"Why it matters: {config['value']}")

    st.session_state["prediction_result"] = result

    if status == "accepted" or status == "needs_review":
        if st.button("→ Generate Suggestions from this Prediction", use_container_width=True):
            st.session_state.page = "suggestions"
            st.session_state.pending_navigation_choice = "Suggestions"
            st.rerun()


def main():
    """Render the document type prediction page, backed by service_client."""
    st.title("🔮 Prediction Lab")
    st.caption(f"Data mode: {get_mode_label()}")
    st.caption(
        "Connects to Tuong's prediction service: "
        "Tuong Prediction Service → service_client.classify_document() → Prediction UI"
    )
    st.markdown("---")

    domain_options = get_domain_names()
    if st.session_state.get("selected_domain_context") not in domain_options:
        st.session_state["selected_domain_context"] = DEFAULT_DOMAIN_KEY

    # ── ML setup & Configuration ──────────────────────────────────────────
    setup_col, data_col = st.columns(2)
    with setup_col:
        st.subheader("Prediction Setup")
        st.selectbox("Domain", domain_options, key="selected_domain_context")
        selected_use_case = st.selectbox(
            "Use Case",
            list(PREDICTION_USE_CASES.keys()),
        )
        selected_model = st.selectbox(
            "Baseline Model",
            [
                PREDICTION_USE_CASES[selected_use_case]["model"],
                "Logistic Regression",
                "Random Forest",
                "Linear Regression",
                "Isolation Forest",
            ],
        )

    with data_col:
        st.subheader("Input Data")
        sources = (
            st.session_state.get("source_context")
            or st.session_state.get("last_processed_sources", [])
        )
        source_count = len(sources)
        st.selectbox(
            "Dataset",
            [
                "Last processed upload batch" if source_count else "Sample structured dataset",
                "Dummy training dataset",
                "Future API dataset",
            ],
        )
        st.slider("Training rows", min_value=100, max_value=10000, value=1000, step=100)
        st.slider("Validation split (%)", min_value=10, max_value=40, value=20, step=5)

    st.markdown("---")
    config = PREDICTION_USE_CASES[selected_use_case]

    st.subheader("Use Case Requirements")
    requirement_df = pd.DataFrame(
        [
            {"Field": "Use case", "Value": selected_use_case},
            {"Field": "Input columns needed", "Value": config["input_columns"]},
            {"Field": "Target variable", "Value": config["target"]},
            {"Field": "Model type", "Value": selected_model},
            {"Field": "Evaluation metric", "Value": config["metric"]},
            {"Field": "Business value", "Value": config["value"]},
        ]
    )
    st.dataframe(requirement_df, use_container_width=True, hide_index=True)

    with st.expander("All Tuong Prediction Use Cases", expanded=False):
        st.dataframe(_requirement_table(), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Document to Classify")
    if sources:
        source_names = [
            s.get("filename") or s.get("name", f"Source {i+1}")
            for i, s in enumerate(sources)
        ]
        selected_idx = st.selectbox(
            "Select an uploaded source",
            range(len(source_names)),
            format_func=lambda i: source_names[i],
        )
        selected_source = sources[selected_idx]
    else:
        st.info("No uploaded sources found. Using a sample payload for this demo.")
        selected_source = {}

    payload = _sample_payload_for(selected_source)

    with st.expander("View input payload sent to prediction service"):
        st.json(payload)

    if st.button("🚀 Run Classification", use_container_width=True):
        response = classify_document(payload)
        st.session_state["last_prediction_response"] = response
        if response.get("status") == "error":
            st.error("Prediction service returned an error.")
        st.session_state["prediction_result"] = response.get("data", {})

    result = st.session_state.get("prediction_result")
    if result:
        st.markdown("---")
        _render_prediction_result(result, selected_use_case, selected_model)
    else:
        st.info("Run a classification to see the prediction result card.")


if __name__ == "__main__":
    main()
