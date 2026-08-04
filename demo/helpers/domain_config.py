"""Shared domain configuration for the Quansolution Streamlit app.

The registry keeps UI labels, allowed filters, metrics, and prompt guidance
in one place so new domains can be added by extending the dictionary only.
"""

from __future__ import annotations

from typing import Dict, List


DEFAULT_DOMAIN_KEY = "Business"


DOMAIN_CONFIGS: Dict[str, Dict] = {
    "Business": {
        "label": "Business",
        "tone_guidance": "objective, metric-driven, executive-ready",
        "data_categories": [
            "Sales Data",
            "Customer Data",
            "Financial Data",
            "Inventory",
            "Operations",
        ],
        "source_systems": [
            "ERP System",
            "CRM System",
            "Data Warehouse",
            "Finance System",
            "Other",
        ],
        "processing_options": [
            "Remove Duplicates",
            "Validate Data",
            "Auto-Categorize",
            "Generate Insights",
        ],
        "dashboard": {
            "kpis": [
                {"label": "Total Revenue", "value": "$2.4M"},
                {"label": "YoY Growth", "value": "+23%"},
                {"label": "Active Deals", "value": "127"},
                {"label": "Win Rate", "value": "68%"},
            ],
            "filters": [
                {
                    "key": "date_range",
                    "label": "Date Range",
                    "kind": "date_range",
                },
                {
                    "key": "department",
                    "label": "Department",
                    "kind": "multiselect",
                    "options": ["Sales", "Operations", "Finance", "Marketing", "IT"],
                    "default": ["Sales"],
                },
                {
                    "key": "region",
                    "label": "Region",
                    "kind": "multiselect",
                    "options": ["North America", "EMEA", "APAC", "LATAM"],
                    "default": ["North America"],
                },
            ],
            "series": [
                {"name": "Revenue", "min": 50000, "max": 150000},
                {"name": "Cost", "min": 20000, "max": 60000},
                {"name": "Growth", "min": -5, "max": 15},
            ],
            "primary_metric": "Revenue",
            "secondary_metric": "Cost",
            "bar_chart_title": "Sales by Category",
            "bar_chart_data": [
                {"label": "Electronics", "value": 450000},
                {"label": "Software", "value": 380000},
                {"label": "Services", "value": 290000},
                {"label": "Hardware", "value": 210000},
                {"label": "Other", "value": 70000},
            ],
            "detail_rows": [
                {"Metric": "Average Deal Size", "Value": "$18,900", "Trend": "↑ +5.2%"},
                {"Metric": "Sales Cycle Length", "Value": "42 days", "Trend": "↓ -8.1%"},
                {"Metric": "Customer Satisfaction", "Value": "4.7/5.0", "Trend": "↑ +0.3%"},
                {"Metric": "Churn Rate", "Value": "2.3%", "Trend": "↓ -1.2%"},
                {"Metric": "New Customers", "Value": "89", "Trend": "↑ +12.4%"},
            ],
        },
        "reports": {
            "report_types": [
                "Executive Summary",
                "Financial Analysis",
                "Sales Performance",
                "Customer Insights",
                "Operational Metrics",
            ],
            "content_options": [
                "Key Metrics & KPIs",
                "Performance Trends",
                "AI Recommendations",
                "Comparative Analysis",
                "Data Quality Insights",
            ],
            "filters": [
                {
                    "key": "business_unit",
                    "label": "Business Unit",
                    "kind": "multiselect",
                    "options": ["Sales", "Finance", "Operations", "Marketing"],
                    "default": ["Sales"],
                },
                {
                    "key": "report_audience",
                    "label": "Audience",
                    "kind": "selectbox",
                    "options": ["Executive", "Manager", "Analyst"],
                },
            ],
        },
        "suggestions": {
            "categories": [
                "Performance",
                "Cost Savings",
                "Security",
                "User Experience",
                "Compliance",
            ],
            "stats": {
                "Total Suggestions": "47",
                "High Priority": "12",
                "Potential Impact": "$2.3M",
                "Implementation Time": "120h",
            },
            "examples": [
                {
                    "title": "Optimize Revenue Forecasting",
                    "priority": "High",
                    "impact": "+15% Accuracy",
                    "description": "Refine forecasting inputs to improve planning confidence and reduce variance.",
                },
                {
                    "title": "Improve Dashboard Refresh Cycle",
                    "priority": "Medium",
                    "impact": "+22% Speed",
                    "description": "Reduce latency in refresh jobs to surface metrics faster for stakeholders.",
                },
                {
                    "title": "Review Compliance Reporting",
                    "priority": "High",
                    "impact": "Risk Reduction",
                    "description": "Audit the reporting pipeline for missing controls and traceability gaps.",
                },
            ],
        },
    },
    "Medical": {
        "label": "Medical",
        "tone_guidance": "clinical, academic, cautious, evidence-based",
        "data_categories": [
            "Patient Records",
            "Clinical Notes",
            "Lab Results",
            "Imaging Reports",
            "Research Papers",
        ],
        "source_systems": ["EHR", "LIS", "PACS", "Clinical Research", "Other"],
        "processing_options": ["Validate Data", "Detect Anomalies", "Extract Entities", "Generate Insights"],
        "dashboard": {
            "kpis": [
                {"label": "Active Patients", "value": "1.2K"},
                {"label": "Critical Alerts", "value": "18"},
                {"label": "Avg Wait Time", "value": "24m"},
                {"label": "Data Completeness", "value": "96%"},
            ],
            "filters": [
                {"key": "date_range", "label": "Date Range", "kind": "date_range"},
                {
                    "key": "care_unit",
                    "label": "Care Unit",
                    "kind": "multiselect",
                    "options": ["Emergency", "Inpatient", "Outpatient", "ICU"],
                    "default": ["Emergency"],
                },
                {
                    "key": "severity",
                    "label": "Severity",
                    "kind": "multiselect",
                    "options": ["Low", "Moderate", "High", "Critical"],
                    "default": ["High", "Critical"],
                },
            ],
            "series": [
                {"name": "Patient Volume", "min": 400, "max": 1200},
                {"name": "Average Wait Time", "min": 10, "max": 60},
                {"name": "Readmission Rate", "min": 1, "max": 15},
            ],
            "primary_metric": "Patient Volume",
            "secondary_metric": "Average Wait Time",
            "bar_chart_title": "Cases by Care Unit",
            "bar_chart_data": [
                {"label": "Emergency", "value": 320},
                {"label": "Inpatient", "value": 280},
                {"label": "Outpatient", "value": 410},
                {"label": "ICU", "value": 95},
            ],
            "detail_rows": [
                {"Metric": "Admission Rate", "Value": "12.8%", "Trend": "↑ +1.1%"},
                {"Metric": "Average LOS", "Value": "4.2 days", "Trend": "↓ -0.4 days"},
                {"Metric": "Readmission Rate", "Value": "8.1%", "Trend": "↓ -0.7%"},
                {"Metric": "Protocol Adherence", "Value": "94%", "Trend": "↑ +2.0%"},
            ],
        },
        "reports": {
            "report_types": [
                "Clinical Summary",
                "Operational Quality Report",
                "Data Quality Assessment",
                "Research Insight Report",
                "Custom Combined Report",
            ],
            "content_options": [
                "Key Metrics & KPIs",
                "Clinical Trends",
                "Safety Signals",
                "Data Quality Insights",
                "Comparative Analysis",
            ],
            "filters": [
                {
                    "key": "care_unit",
                    "label": "Care Unit",
                    "kind": "multiselect",
                    "options": ["Emergency", "Inpatient", "Outpatient", "ICU"],
                    "default": ["Emergency"],
                },
                {
                    "key": "patient_cohort",
                    "label": "Patient Cohort",
                    "kind": "multiselect",
                    "options": ["Adult", "Pediatric", "Geriatric", "Critical Care"],
                    "default": ["Adult"],
                },
            ],
        },
        "suggestions": {
            "categories": ["Patient Safety", "Workflow Efficiency", "Compliance", "Data Quality", "Research Opportunities"],
            "stats": {"Total Suggestions": "31", "High Priority": "9", "Potential Impact": "18%", "Implementation Time": "64h"},
            "examples": [
                {"title": "Reduce Charting Delays", "priority": "High", "impact": "Faster Documentation", "description": "Streamline clinical note capture to reduce clinician overhead."},
                {"title": "Improve Alert Prioritization", "priority": "High", "impact": "Risk Reduction", "description": "Refine alert thresholds to prioritize actionable clinical signals."},
                {"title": "Standardize Terminology", "priority": "Medium", "impact": "Cleaner Records", "description": "Normalize labels across care teams to improve downstream analysis."},
            ],
        },
    },
    "Code": {
        "label": "Code",
        "tone_guidance": "technical, syntax-aware, engineering-focused",
        "data_categories": ["Repositories", "Pull Requests", "Issues", "Logs", "Documentation"],
        "source_systems": ["GitHub", "GitLab", "Bitbucket", "CI/CD", "Other"],
        "processing_options": ["Validate Data", "Detect Anomalies", "Extract Entities", "Generate Insights"],
        "dashboard": {
            "kpis": [
                {"label": "Open Issues", "value": "128"},
                {"label": "Build Success Rate", "value": "97%"},
                {"label": "Code Coverage", "value": "84%"},
                {"label": "Lead Time", "value": "2.4d"},
            ],
            "filters": [
                {"key": "date_range", "label": "Date Range", "kind": "date_range"},
                {"key": "repository", "label": "Repository", "kind": "multiselect", "options": ["api-service", "ui-app", "data-pipeline", "infra"], "default": ["api-service"]},
                {"key": "language", "label": "Language", "kind": "multiselect", "options": ["Python", "TypeScript", "JavaScript", "SQL", "Go"], "default": ["Python"]},
            ],
            "series": [
                {"name": "Build Success Rate", "min": 88, "max": 100},
                {"name": "Code Coverage", "min": 60, "max": 95},
                {"name": "Open Issues", "min": 40, "max": 180},
            ],
            "primary_metric": "Build Success Rate",
            "secondary_metric": "Code Coverage",
            "bar_chart_title": "Issues by Repository",
            "bar_chart_data": [
                {"label": "api-service", "value": 42},
                {"label": "ui-app", "value": 36},
                {"label": "data-pipeline", "value": 28},
                {"label": "infra", "value": 22},
            ],
            "detail_rows": [
                {"Metric": "Mean Time to Merge", "Value": "1.8 days", "Trend": "↓ -0.3 days"},
                {"Metric": "Build Failure Rate", "Value": "3.2%", "Trend": "↓ -0.6%"},
                {"Metric": "Review Coverage", "Value": "89%", "Trend": "↑ +4.0%"},
                {"Metric": "Hotspots Addressed", "Value": "14", "Trend": "↑ +2"},
            ],
        },
        "reports": {
            "report_types": ["Release Readiness Summary", "Code Quality Analysis", "Incident Review", "Developer Productivity Report", "Custom Combined Report"],
            "content_options": ["Key Metrics & KPIs", "Repository Trends", "Quality Findings", "Risk Hotspots", "Actionable Refactor Suggestions"],
            "filters": [
                {"key": "repository", "label": "Repository", "kind": "multiselect", "options": ["api-service", "ui-app", "data-pipeline", "infra"], "default": ["api-service"]},
                {"key": "branch", "label": "Branch", "kind": "multiselect", "options": ["main", "develop", "release", "feature"], "default": ["main"]},
            ],
        },
        "suggestions": {
            "categories": ["Code Quality", "Reliability", "Security", "Developer Experience", "Documentation"],
            "stats": {"Total Suggestions": "22", "High Priority": "7", "Potential Impact": "Code Health", "Implementation Time": "40h"},
            "examples": [
                {"title": "Reduce Build Flakiness", "priority": "High", "impact": "Stability", "description": "Address intermittent CI failures to improve developer trust in the pipeline."},
                {"title": "Improve Type Coverage", "priority": "Medium", "impact": "Safer Refactors", "description": "Increase type coverage in shared modules to reduce regressions."},
                {"title": "Document API Contracts", "priority": "Medium", "impact": "Faster Onboarding", "description": "Add concise API contract notes for the most used endpoints."},
            ],
        },
    },
    "Finance": {
        "label": "Finance",
        "tone_guidance": "objective, risk-aware, compliance-conscious",
        "data_categories": ["Transactions", "Ledger", "Portfolio", "Risk Reports", "Statements"],
        "source_systems": ["ERP", "Banking System", "Trading Platform", "Treasury", "Other"],
        "processing_options": ["Validate Data", "Detect Anomalies", "Normalize Instruments", "Generate Insights"],
        "dashboard": {
            "kpis": [
                {"label": "Portfolio Value", "value": "$18.9M"},
                {"label": "Risk Exposure", "value": "Low"},
                {"label": "Return", "value": "+7.4%"},
                {"label": "Data Freshness", "value": "8m"},
            ],
            "filters": [
                {"key": "date_range", "label": "Date Range", "kind": "date_range"},
                {"key": "portfolio", "label": "Portfolio", "kind": "multiselect", "options": ["Growth", "Income", "Balanced", "Hedged"], "default": ["Balanced"]},
                {"key": "risk_level", "label": "Risk Level", "kind": "multiselect", "options": ["Low", "Moderate", "High"], "default": ["Low", "Moderate"]},
            ],
            "series": [
                {"name": "Portfolio Value", "min": 12000000, "max": 21000000},
                {"name": "Risk Exposure", "min": 1, "max": 15},
                {"name": "Return", "min": -3, "max": 12},
            ],
            "primary_metric": "Portfolio Value",
            "secondary_metric": "Risk Exposure",
            "bar_chart_title": "Assets by Class",
            "bar_chart_data": [
                {"label": "Equities", "value": 8_200_000},
                {"label": "Fixed Income", "value": 5_400_000},
                {"label": "Cash", "value": 2_300_000},
                {"label": "Alternatives", "value": 3_000_000},
            ],
            "detail_rows": [
                {"Metric": "Sharpe Ratio", "Value": "1.42", "Trend": "↑ +0.08"},
                {"Metric": "VaR", "Value": "$240K", "Trend": "↓ -12K"},
                {"Metric": "Drawdown", "Value": "3.1%", "Trend": "↓ -0.4%"},
                {"Metric": "Rebalancing Drift", "Value": "0.6%", "Trend": "↓ -0.1%"},
            ],
        },
        "reports": {
            "report_types": ["Executive Risk Summary", "Portfolio Performance Report", "Compliance Review", "Forecast Report", "Custom Combined Report"],
            "content_options": ["Key Metrics & KPIs", "Performance Trends", "Risk Signals", "Comparative Analysis", "Compliance Notes"],
            "filters": [
                {"key": "portfolio", "label": "Portfolio", "kind": "multiselect", "options": ["Growth", "Income", "Balanced", "Hedged"], "default": ["Balanced"]},
                {"key": "asset_class", "label": "Asset Class", "kind": "multiselect", "options": ["Equities", "Fixed Income", "Cash", "Alternatives"], "default": ["Equities"]},
            ],
        },
        "suggestions": {
            "categories": ["Risk Reduction", "Performance", "Compliance", "Cost Efficiency", "Forecast Accuracy"],
            "stats": {"Total Suggestions": "18", "High Priority": "6", "Potential Impact": "$1.4M", "Implementation Time": "58h"},
            "examples": [
                {"title": "Tighten Risk Thresholds", "priority": "High", "impact": "Lower Volatility", "description": "Review exposure thresholds for concentration risk in volatile assets."},
                {"title": "Automate Reconciliation", "priority": "Medium", "impact": "Lower Effort", "description": "Reduce manual review time by automating recurring account reconciliations."},
                {"title": "Expand Compliance Checks", "priority": "High", "impact": "Audit Readiness", "description": "Add automated checks to surface missing controls before reporting cycles."},
            ],
        },
    },
    "Scientific": {
        "label": "Scientific",
        "tone_guidance": "methodical, reproducible, evidence-centered",
        "data_categories": ["Experiments", "Observations", "Lab Results", "Research Papers", "Protocols"],
        "source_systems": ["LIMS", "ELN", "Instrument Logs", "Research Repository", "Other"],
        "processing_options": ["Validate Data", "Detect Anomalies", "Normalize Measurements", "Generate Insights"],
        "dashboard": {
            "kpis": [
                {"label": "Experiments Completed", "value": "48"},
                {"label": "Success Rate", "value": "79%"},
                {"label": "Reproducibility", "value": "91%"},
                {"label": "Open Anomalies", "value": "7"},
            ],
            "filters": [
                {"key": "date_range", "label": "Date Range", "kind": "date_range"},
                {"key": "study_type", "label": "Study Type", "kind": "multiselect", "options": ["Wet Lab", "Dry Lab", "Field Study", "Simulation"], "default": ["Wet Lab"]},
                {"key": "method", "label": "Method", "kind": "multiselect", "options": ["PCR", "Microscopy", "Sequencing", "Modeling"], "default": ["Modeling"]},
            ],
            "series": [
                {"name": "Experiments Completed", "min": 20, "max": 70},
                {"name": "Success Rate", "min": 60, "max": 98},
                {"name": "Reproducibility", "min": 70, "max": 99},
            ],
            "primary_metric": "Experiments Completed",
            "secondary_metric": "Success Rate",
            "bar_chart_title": "Observations by Study Type",
            "bar_chart_data": [
                {"label": "Wet Lab", "value": 24},
                {"label": "Dry Lab", "value": 13},
                {"label": "Field Study", "value": 9},
                {"label": "Simulation", "value": 18},
            ],
            "detail_rows": [
                {"Metric": "Protocol Adherence", "Value": "93%", "Trend": "↑ +1.5%"},
                {"Metric": "Outlier Rate", "Value": "2.1%", "Trend": "↓ -0.4%"},
                {"Metric": "Replication Success", "Value": "88%", "Trend": "↑ +3.0%"},
                {"Metric": "Instrumentation Downtime", "Value": "1.2h", "Trend": "↓ -0.3h"},
            ],
        },
        "reports": {
            "report_types": ["Experiment Summary", "Research Analysis", "Lab Quality Report", "Literature Review", "Custom Combined Report"],
            "content_options": ["Key Metrics & KPIs", "Experimental Trends", "Methodology Review", "Comparative Analysis", "Data Quality Insights"],
            "filters": [
                {"key": "study_type", "label": "Study Type", "kind": "multiselect", "options": ["Wet Lab", "Dry Lab", "Field Study", "Simulation"], "default": ["Wet Lab"]},
                {"key": "instrument", "label": "Instrument", "kind": "multiselect", "options": ["Microscope", "Sequencer", "Spectrometer", "Sensor Array"], "default": ["Microscope"]},
            ],
        },
        "suggestions": {
            "categories": ["Methodology", "Reproducibility", "Data Quality", "Throughput", "Documentation"],
            "stats": {"Total Suggestions": "26", "High Priority": "8", "Potential Impact": "Experimental Rigor", "Implementation Time": "72h"},
            "examples": [
                {"title": "Standardize Experimental Metadata", "priority": "High", "impact": "Reproducibility", "description": "Capture core protocol metadata consistently across experiments."},
                {"title": "Reduce Manual Transcription", "priority": "Medium", "impact": "Data Quality", "description": "Replace manual entry with instrument integrations where possible."},
                {"title": "Improve Method Notes", "priority": "Medium", "impact": "Traceability", "description": "Document deviations and exceptions alongside each run for review."},
            ],
        },
    },
    "Legal": {
        "label": "Legal",
        "tone_guidance": "precise, risk-aware, citation-conscious, compliance-focused",
        "data_categories": ["Contracts", "Case Files", "Policies", "Regulations", "Legal Memos"],
        "source_systems": ["Document Management", "Contract Repository", "Case Management", "Compliance System", "Other"],
        "processing_options": ["Validate Data", "Detect Anomalies", "Extract Entities", "Generate Insights"],
        "dashboard": {
            "kpis": [
                {"label": "Documents Reviewed", "value": "842"},
                {"label": "Open Risk Flags", "value": "36"},
                {"label": "Clause Coverage", "value": "91%"},
                {"label": "Review SLA", "value": "94%"},
            ],
            "filters": [
                {"key": "date_range", "label": "Date Range", "kind": "date_range"},
                {"key": "document_type", "label": "Document Type", "kind": "multiselect", "options": ["Contract", "Policy", "Case File", "Regulation"], "default": ["Contract"]},
                {"key": "risk_level", "label": "Risk Level", "kind": "multiselect", "options": ["Low", "Moderate", "High", "Critical"], "default": ["Moderate", "High"]},
            ],
            "series": [
                {"name": "Documents Reviewed", "min": 200, "max": 900},
                {"name": "Open Risk Flags", "min": 10, "max": 80},
                {"name": "Clause Coverage", "min": 70, "max": 98},
            ],
            "primary_metric": "Documents Reviewed",
            "secondary_metric": "Open Risk Flags",
            "bar_chart_title": "Risk Flags by Document Type",
            "bar_chart_data": [
                {"label": "Contracts", "value": 18},
                {"label": "Policies", "value": 7},
                {"label": "Case Files", "value": 6},
                {"label": "Regulations", "value": 5},
            ],
            "detail_rows": [
                {"Metric": "Missing Clause Rate", "Value": "4.8%", "Trend": "↓ -0.9%"},
                {"Metric": "High-Risk Terms", "Value": "36", "Trend": "↑ +4"},
                {"Metric": "Review Turnaround", "Value": "2.1 days", "Trend": "↓ -0.4 days"},
                {"Metric": "Citation Coverage", "Value": "88%", "Trend": "↑ +3.2%"},
            ],
        },
        "reports": {
            "report_types": ["Contract Risk Summary", "Compliance Review", "Case File Brief", "Policy Gap Report", "Custom Combined Report"],
            "content_options": ["Key Metrics & KPIs", "Risk Signals", "Clause Findings", "Compliance Notes", "Comparative Analysis"],
            "filters": [
                {"key": "document_type", "label": "Document Type", "kind": "multiselect", "options": ["Contract", "Policy", "Case File", "Regulation"], "default": ["Contract"]},
                {"key": "jurisdiction", "label": "Jurisdiction", "kind": "multiselect", "options": ["US", "EU", "APAC", "Global"], "default": ["US"]},
            ],
        },
        "suggestions": {
            "categories": ["Risk Review", "Compliance", "Clause Quality", "Workflow Efficiency", "Documentation"],
            "stats": {"Total Suggestions": "24", "High Priority": "8", "Potential Impact": "Risk Reduction", "Implementation Time": "52h"},
            "examples": [
                {"title": "Review High-Risk Clauses", "priority": "High", "impact": "Risk Reduction", "description": "Prioritize contracts with unusual liability, renewal, or termination language."},
                {"title": "Improve Citation Coverage", "priority": "Medium", "impact": "Audit Readiness", "description": "Attach source references to legal findings that require traceability."},
                {"title": "Standardize Policy Labels", "priority": "Medium", "impact": "Faster Review", "description": "Normalize policy categories so compliance reviews can compare documents reliably."},
            ],
        },
    },
    "General Text": {
        "label": "General Text",
        "tone_guidance": "clear, neutral, insight-oriented",
        "data_categories": ["Articles", "Documents", "Notes", "Knowledge Base", "Transcripts"],
        "source_systems": ["Document Store", "CMS", "Knowledge Base", "Drive", "Other"],
        "processing_options": ["Validate Data", "Detect Anomalies", "Summarize", "Generate Insights"],
        "dashboard": {
            "kpis": [
                {"label": "Documents Processed", "value": "3.8K"},
                {"label": "Retrieval Accuracy", "value": "93%"},
                {"label": "Response Time", "value": "1.4s"},
                {"label": "Coverage", "value": "87%"},
            ],
            "filters": [
                {"key": "date_range", "label": "Date Range", "kind": "date_range"},
                {"key": "source_type", "label": "Source Type", "kind": "multiselect", "options": ["Document Store", "CMS", "Knowledge Base", "Drive"], "default": ["Knowledge Base"]},
                {"key": "topic", "label": "Topic", "kind": "multiselect", "options": ["Policy", "Operations", "Support", "Product", "Training"], "default": ["Operations"]},
            ],
            "series": [
                {"name": "Documents Processed", "min": 150, "max": 500},
                {"name": "Retrieval Accuracy", "min": 80, "max": 99},
                {"name": "Response Time", "min": 0.8, "max": 3.0},
            ],
            "primary_metric": "Documents Processed",
            "secondary_metric": "Retrieval Accuracy",
            "bar_chart_title": "Coverage by Topic",
            "bar_chart_data": [
                {"label": "Policy", "value": 82},
                {"label": "Operations", "value": 96},
                {"label": "Support", "value": 74},
                {"label": "Product", "value": 88},
            ],
            "detail_rows": [
                {"Metric": "Answer Relevance", "Value": "91%", "Trend": "↑ +2.1%"},
                {"Metric": "Duplicate Docs", "Value": "3.4%", "Trend": "↓ -0.7%"},
                {"Metric": "Average Summary Length", "Value": "128 words", "Trend": "↓ -12 words"},
                {"Metric": "Taxonomy Coverage", "Value": "89%", "Trend": "↑ +1.8%"},
            ],
        },
        "reports": {
            "report_types": ["Executive Summary", "Content Analysis", "Knowledge Base Review", "Trend Report", "Custom Combined Report"],
            "content_options": ["Key Metrics & KPIs", "Text Trends", "Comparative Analysis", "Summaries", "Data Quality Insights"],
            "filters": [
                {"key": "source_type", "label": "Source Type", "kind": "multiselect", "options": ["Document Store", "CMS", "Knowledge Base", "Drive"], "default": ["Knowledge Base"]},
                {"key": "topic", "label": "Topic", "kind": "multiselect", "options": ["Policy", "Operations", "Support", "Product", "Training"], "default": ["Operations"]},
            ],
        },
        "suggestions": {
            "categories": ["Content Quality", "Retrieval Optimization", "Taxonomy", "Summarization", "Knowledge Gaps"],
            "stats": {"Total Suggestions": "35", "High Priority": "10", "Potential Impact": "Faster Discovery", "Implementation Time": "50h"},
            "examples": [
                {"title": "Refine Taxonomy Labels", "priority": "High", "impact": "Better Search", "description": "Simplify category names so users can discover content more reliably."},
                {"title": "Improve Summary Templates", "priority": "Medium", "impact": "Clarity", "description": "Use shorter summaries for common document types to increase readability."},
                {"title": "Fill Knowledge Gaps", "priority": "High", "impact": "Coverage", "description": "Identify topics with low coverage and prioritize new source ingestion."},
            ],
        },
    },
    "E-commerce": {
        "label": "E-commerce",
        "tone_guidance": "merchant-focused, conversion-oriented, operationally precise",
        "data_categories": ["Orders", "Catalog", "Customer Reviews", "Inventory", "Marketing"],
        "source_systems": ["Shop Platform", "Warehouse", "CRM", "Ad Platform", "Other"],
        "processing_options": ["Remove Duplicates", "Validate Data", "Detect Anomalies", "Generate Insights"],
        "dashboard": {
            "kpis": [
                {"label": "Orders", "value": "18.2K"},
                {"label": "Conversion Rate", "value": "4.8%"},
                {"label": "AOV", "value": "$92"},
                {"label": "Return Rate", "value": "3.9%"},
            ],
            "filters": [
                {"key": "date_range", "label": "Date Range", "kind": "date_range"},
                {"key": "channel", "label": "Channel", "kind": "multiselect", "options": ["Paid Search", "Organic", "Email", "Social"], "default": ["Organic"]},
                {"key": "product_category", "label": "Product Category", "kind": "multiselect", "options": ["Apparel", "Electronics", "Home", "Beauty"], "default": ["Apparel"]},
            ],
            "series": [
                {"name": "Orders", "min": 12000, "max": 24000},
                {"name": "Conversion Rate", "min": 2.5, "max": 6.0},
                {"name": "Average Order Value", "min": 70, "max": 120},
            ],
            "primary_metric": "Orders",
            "secondary_metric": "Conversion Rate",
            "bar_chart_title": "Orders by Category",
            "bar_chart_data": [
                {"label": "Apparel", "value": 6400},
                {"label": "Electronics", "value": 5200},
                {"label": "Home", "value": 3600},
                {"label": "Beauty", "value": 3000},
            ],
            "detail_rows": [
                {"Metric": "Repeat Purchase Rate", "Value": "22%", "Trend": "↑ +1.4%"},
                {"Metric": "Cart Abandonment", "Value": "68%", "Trend": "↓ -2.1%"},
                {"Metric": "Refund Rate", "Value": "3.9%", "Trend": "↓ -0.3%"},
                {"Metric": "Fulfillment SLA", "Value": "97%", "Trend": "↑ +0.8%"},
            ],
        },
        "reports": {
            "report_types": ["Executive Summary", "Sales Performance", "Catalog Health", "Customer Insight", "Custom Combined Report"],
            "content_options": ["Key Metrics & KPIs", "Conversion Trends", "Customer Experience", "Comparative Analysis", "Catalog Insights"],
            "filters": [
                {"key": "channel", "label": "Channel", "kind": "multiselect", "options": ["Paid Search", "Organic", "Email", "Social"], "default": ["Organic"]},
                {"key": "product_category", "label": "Product Category", "kind": "multiselect", "options": ["Apparel", "Electronics", "Home", "Beauty"], "default": ["Apparel"]},
            ],
        },
        "suggestions": {
            "categories": ["Conversion", "Retention", "Inventory", "Customer Experience", "Margin"],
            "stats": {"Total Suggestions": "28", "High Priority": "11", "Potential Impact": "$820K", "Implementation Time": "96h"},
            "examples": [
                {"title": "Reduce Cart Abandonment", "priority": "High", "impact": "+Conversion", "description": "Streamline the checkout flow and remove friction in payment steps."},
                {"title": "Improve Stock Replenishment", "priority": "High", "impact": "Fewer Stockouts", "description": "Use demand signals to prevent inventory gaps on top sellers."},
                {"title": "Prioritize Review Sentiment", "priority": "Medium", "impact": "Better CX", "description": "Surface negative product feedback faster for response and remediation."},
            ],
        },
    },
}


def get_domain_names() -> List[str]:
    return list(DOMAIN_CONFIGS.keys())


def get_domain_config(domain_key: str | None) -> Dict:
    return DOMAIN_CONFIGS.get(domain_key or DEFAULT_DOMAIN_KEY, DOMAIN_CONFIGS[DEFAULT_DOMAIN_KEY])


def get_domain_data_categories(domain_key: str | None) -> List[str]:
    return get_domain_config(domain_key)["data_categories"]


def get_domain_source_systems(domain_key: str | None) -> List[str]:
    return get_domain_config(domain_key)["source_systems"]


def get_domain_processing_options(domain_key: str | None) -> List[str]:
    return get_domain_config(domain_key)["processing_options"]


def get_domain_dashboard_config(domain_key: str | None) -> Dict:
    return get_domain_config(domain_key)["dashboard"]


def get_domain_report_config(domain_key: str | None) -> Dict:
    return get_domain_config(domain_key)["reports"]


def get_domain_suggestion_config(domain_key: str | None) -> Dict:
    return get_domain_config(domain_key)["suggestions"]
