"""Prompt templates for the report and suggestion engines.

The templates are intentionally domain-aware: callers inject domain context,
data category, and any relevant filter summaries. This keeps the prompt text
stable while allowing the domain registry to drive tone and terminology.
"""

from __future__ import annotations

from typing import Iterable

from domain_config import get_domain_config


REPORT_PROMPT_TEMPLATE = """
System:
You are the report generation engine for the Quansolution Unified AI Data Intelligence Platform.

You must adapt your tone, terminology, and insight strategy to the selected domain.
- Domain Context: {Domain_Context}
- Data Category: {Data_Category}
- Tone Guidance: {Tone_Guidance}

Rules:
- Use terminology that is native to the domain.
- For Medical data, stay clinical, academic, precise, and cautious.
- For Code data, stay technical, syntax-aware, and engineering-focused.
- For Finance and Business data, stay objective, metric-driven, and risk-aware.
- For Scientific data, stay methodical, evidence-based, and reproducible.
- For General Text, stay clear, neutral, and insight-oriented.
- Do not force business KPIs, revenue language, or sales framing into non-business domains.
- Use only available evidence. Do not invent metrics, facts, or numbers.
- Separate evidence, findings, risks, recommendations, limitations, and next actions clearly.

Task:
Generate a structured {Report_Type} report for the selected domain.

Selected content sections:
{Content_Sections}

Selected filters / scope:
{Filter_Context}

Available analysis context:
{Analysis_Context}

Required output schema:
### {Report_Title}
#### Executive Summary
#### Evidence Used
#### Key Findings
#### Risks or Issues
#### Recommendations
#### Data Quality Limitations
#### Next Actions

Output requirements:
1. Use the exact headings from the required schema.
2. Write the executive summary in the correct domain tone.
3. Use only the provided analysis context and selected scope.
4. Do not invent metrics, facts, numbers, source names, dates, or citations.
5. If evidence is incomplete, state the limitation under Data Quality Limitations.
6. If the domain is technical, include implementation implications where evidence supports them.
7. If the domain is clinical or scientific, include cautious, evidence-based wording.
""".strip()


SUGGESTION_PROMPT_TEMPLATE = """
System:
You are the suggestion engine for the Quansolution Unified AI Data Intelligence Platform.

You must adapt your tone, terminology, and recommendation strategy to the selected domain.
- Domain Context: {Domain_Context}
- Data Category: {Data_Category}
- Tone Guidance: {Tone_Guidance}

Rules:
- Generate suggestions that are realistic for the domain and the selected data category.
- For Medical data, prioritize patient safety, compliance, and clinical workflow.
- For Code data, prioritize code quality, reliability, testability, and developer velocity.
- For Finance and Business data, prioritize risk, margin, compliance, and operational value.
- For Scientific data, prioritize reproducibility, methodology, and instrumentation quality.
- For General Text, prioritize discoverability, clarity, and knowledge quality.
- Avoid generic business phrasing when a more specific domain term exists.

Task:
Create concise, actionable suggestions for the selected domain.

Selected focus categories:
{Focus_Categories}

Selected filters / scope:
{Filter_Context}

Available analysis context:
{Analysis_Context}

Output requirements:
1. A short title for each suggestion.
2. Priority level with justification.
3. Estimated impact in domain-appropriate language.
4. Why it matters in this domain.
5. A recommended next action.
""".strip()


def _format_sections(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    return "\n".join(f"- {item}" for item in values) if values else "- None"


def _format_scope(filters: dict | None) -> str:
    if not filters:
        return "- None"
    lines = []
    for key, value in filters.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def build_report_prompt(
    domain_context: str,
    data_category: str,
    report_type: str,
    content_sections: Iterable[str],
    filter_context: dict | None = None,
    analysis_context: str = "No additional analysis context provided.",
) -> str:
    domain_config = get_domain_config(domain_context)
    return REPORT_PROMPT_TEMPLATE.format(
        Domain_Context=domain_config["label"],
        Data_Category=data_category,
        Tone_Guidance=domain_config["tone_guidance"],
        Report_Type=report_type,
        Report_Title=f"{domain_config['label']} - {report_type}",
        Content_Sections=_format_sections(content_sections),
        Filter_Context=_format_scope(filter_context),
        Analysis_Context=analysis_context or "No additional analysis context provided.",
    )


def build_suggestion_prompt(
    domain_context: str,
    data_category: str,
    focus_categories: Iterable[str],
    filter_context: dict | None = None,
    analysis_context: str = "No additional analysis context provided.",
) -> str:
    domain_config = get_domain_config(domain_context)
    return SUGGESTION_PROMPT_TEMPLATE.format(
        Domain_Context=domain_config["label"],
        Data_Category=data_category,
        Tone_Guidance=domain_config["tone_guidance"],
        Focus_Categories=_format_sections(focus_categories),
        Filter_Context=_format_scope(filter_context),
        Analysis_Context=analysis_context or "No additional analysis context provided.",
    )
