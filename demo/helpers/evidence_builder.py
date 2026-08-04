"""
demo/helpers/evidence_builder.py
==================================
Xây dựng evidence context để truyền vào generate_report().
Không còn phụ thuộc vào get_prediction_summary (đã bị loại bỏ) —
thông tin prediction được đọc từ st.session_state nếu có.
"""

from typing import Any, Dict


def source_metadata_for_evidence(sources: list) -> list:
    """Trả về metadata của từng source, bỏ trường 'content' (có thể rất lớn)."""
    return [
        {key: value for key, value in source.items() if key != "content"}
        for source in sources
    ]


def build_pipeline_evidence_context(
    sources: list,
    dashboard_signals: dict,
    suggestions: list,
    domain_label: str,
) -> Dict[str, Any]:
    """
    Tổng hợp evidence từ upload, dashboard, suggestions thành context
    chuẩn để truyền vào generate_report().

    Note: dashboard_signals ở đây là phần data đã bóc tách từ envelope,
    tức là caller phải truyền vào response["data"], không phải toàn bộ envelope.
    """
    source_metadata = source_metadata_for_evidence(sources)
    return {
        "source_context": source_metadata,
        "dashboard_signals": dashboard_signals,
        "suggestions": suggestions,
        # prediction_result sẽ được bổ sung bởi reports_page hoặc suggestions_page
        # thông qua st.session_state["prediction_result"] — không cần call riêng
        "time_period": "Current demo session",
        "audience": "General",
        "included_context": [
            "Upload quality",
            "Dashboard signals",
            "Prediction outputs",
            "Action suggestions",
        ],
        "domain_label": domain_label,
        "report_type": "Pipeline Evidence Report",
    }


def pipeline_analysis_context(evidence_context: dict) -> str:
    """Sinh chuỗi tóm tắt ngắn cho report prompt template."""
    dashboard_signals = evidence_context.get("dashboard_signals", {})
    return (
        f"Upload sources available: {len(evidence_context.get('source_context', []))} | "
        f"Dashboard signals: quality score {dashboard_signals.get('data_quality_score')}%, "
        f"parsing coverage {dashboard_signals.get('parsing_coverage', 0):.0%}, "
        f"duplicate risk {dashboard_signals.get('duplicate_risk')} | "
        f"Action suggestions available: {len(evidence_context.get('suggestions', []))}"
    )
