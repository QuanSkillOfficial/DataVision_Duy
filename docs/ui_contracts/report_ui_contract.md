# Report UI Contract

**Owner (data provider):** Phi & Hung (aggregation logic), sourcing from
Duy (ingestion) + Phat (analytics) + Tuong (prediction) + Lap (RAG) + suggestions
**Consumer:** `demo/reports_page.py`
**Service entry point:** `service_client.generate_report(evidence_context)`

---

## Input — Evidence Context

```json
{
  "source_context": [ ... ],
  "dashboard_signals": { ... },
  "suggestions": [ ... ],
  "prediction_result": { ... },
  "rag_context": { ... },
  "domain_label": "Business",
  "report_type": "Suggestion Summary",
  "audience": "General"
}
```

---

## Output

```json
{
  "title": "Business - Suggestion Summary",
  "sections": [
    {"Section": "Title", "Preview": "Business - Suggestion Summary", "Audience": "General"},
    {"Section": "Executive Summary", "Preview": "...", "Audience": "General"},
    {"Section": "Evidence Used", "Preview": "2 upload source(s), 5 suggestion(s)", "Audience": "General"},
    {"Section": "Key Findings", "Preview": "...", "Audience": "General"},
    {"Section": "Risks or Issues", "Preview": "...", "Audience": "General"},
    {"Section": "Recommendations", "Preview": "...", "Audience": "General"},
    {"Section": "Data Quality Limitations", "Preview": "...", "Audience": "General"},
    {"Section": "Next Actions", "Preview": "...", "Audience": "General"}
  ],
  "evidence_table": [
    {
      "Evidence Source": "financial_report.csv",
      "Module": "ingestion",
      "Metric / Signal": "File Size",
      "Value": "15,420 bytes",
      "Used In Section": "Evidence Used",
      "Limitation": "Week 7 integration fixture; backend validation pending."
    }
  ]
}
```

### Section Object

| Field | Type |
|---|---|
| `Section` | str — one of the strict 8 schema headings |
| `Preview` | str |
| `Audience` | str |

### Evidence Table Row

| Column | Type | Notes |
|---|---|---|
| `Evidence Source` | str | File name, view name, or signal name |
| `Module` | str | `ingestion` / `analytics` / `prediction` / `rag` / suggestion source |
| `Metric / Signal` | str | What is being measured |
| `Value` | str | The actual value, pre-formatted |
| `Used In Section` | str | Which report section cites this row |
| `Limitation` | str | Caveat — never blank |

---

## Strict Report Schema (8 sections, fixed order)

```
### {Report Title}
#### Executive Summary
#### Evidence Used
#### Key Findings
#### Risks or Issues
#### Recommendations
#### Data Quality Limitations
#### Next Actions
```

Rule inherited from Week 2: **use only available evidence — do not
invent metrics, facts, or numbers.**

---

## Missing-Data Rule

If any evidence source is unavailable when building the table, the
cell value must be the literal string:

```
Not available in current data.
```

The report generation function must **never fail** due to missing
upstream data — it always degrades gracefully to this placeholder.

## Week 7 Evidence Language

Reports must avoid "mock data" wording when using Week 7 integration
fixtures. Use precise staging language instead:

| Old wording | Week 7 wording |
|---|---|
| Mock data | Week 7 integration fixture |
| Mock prediction response | Prediction output pending review |
| Mock RAG response | RAG retrieval output from pgvector |
| Mock analytics view | Database-backed sample |

Reports should include ingestion evidence, dashboard/data-quality
evidence, prediction evidence, RAG citation evidence, limitations, and
next actions.

## UI Behavior Rules

- Report draft renders even when `suggestions` is empty — a warning banner is shown, and the "Recommendations" section degrades gracefully to "Not available in current data." (changed in Week 6 Task 8).
- Evidence table renders even when most rows show "Not available in current data." — an empty table is replaced by a single explanatory row, never a blank Streamlit dataframe.
- Markdown download button always reflects the currently rendered sections (not a cached older version).
