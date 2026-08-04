# Suggestion UI Contract

**Owner (data provider):** Phi & Hung (aggregation logic), sourcing from
Duy (ingestion) + Phat (dashboard) + Tuong (prediction) + Lap (RAG)
**Consumer:** `demo/suggestions_page.py`
**Service entry point:** `service_client.generate_suggestions(context)`

---

## Input Context

```json
{
  "dashboard_signals": { "parsing_coverage": 0.5, "processing_status": "ready" },
  "prediction_result": { "status": "needs_review", "confidence": 0.52 },
  "rag_context": { "status": "no_match" }
}
```

All three keys are optional — missing context simply means fewer
suggestion candidates are generated.

---

## Output — Suggestion Object

```json
{
  "title": "Review document type before report generation",
  "category": "Data Quality",
  "priority": "High",
  "description": "...",
  "why_it_matters": "...",
  "next_action": "...",
  "source_signal": "prediction.confidence_score = 0.52",
  "difficulty": "Low",
  "reason": "...",
  "urgency_score": 0.9,
  "impact_score": 0.85,
  "confidence_score": 0.95,
  "effort_score": 0.1,
  "final_score": 0.76,
  "final_priority": "High",
  "source_module": "prediction",
  "source_view": "prediction_logs",
  "evidence_type": "confidence_score",
  "evidence_value": 0.52,
  "generated_from": ["prediction_logs"]
}
```

### Required Fields

| Field | Type | Description |
|---|---|---|
| `title` | str | Suggestion headline |
| `category` | str | Grouping label |
| `priority` | str | Initial priority before scoring |
| `description` | str | Full explanation |
| `next_action` | str | Recommended next step |
| `urgency_score` / `impact_score` / `confidence_score` / `effort_score` | float (0.0–1.0) | Component scores |
| `final_score` | float | Computed ranking score |
| `final_priority` | str | `High` / `Medium` / `Low` after scoring |
| `source_module` | str | Origin module: `ingestion`, `dashboard`, `prediction`, `rag` |
| `source_view` | str | DB view or log used as evidence |
| `evidence_type` | str | Name of the specific signal |
| `evidence_value` | any | Value of that signal |
| `affected_document` | str | Document or source id affected by the recommendation |
| `affected_source` | str | File/source name affected by the recommendation |
| `confidence` | float | Confidence in the recommendation itself |
| `generated_from` | list[str] | All raw sources contributing to this suggestion |

---

## Scoring Formula

```
final_score = (
    0.35 * urgency_score +
    0.30 * impact_score +
    0.20 * confidence_score -
    0.15 * effort_score
)
```

Clamped to `0..1`. Sorted descending by `final_score`.

## Priority Mapping

| `final_score` | `final_priority` |
|---|---|
| `>= 0.60` | High |
| `0.35–0.59` | Medium |
| `< 0.35` | Low |

---

## Cross-Module Evidence Examples

| Trigger | `source_module` | `evidence_type` |
|---|---|---|
| Low parsing coverage | `ingestion` | `parsing_coverage` |
| Dashboard ready for reporting | `dashboard` | `processing_status` |
| Low prediction confidence | `prediction` | `confidence_score` |
| RAG query with no match | `rag` | `retrieval_match` |
| No data at all | `ingestion` | `source_count` |

## Week 7 Signal Sources

Suggestions should be generated from real-output-shaped integration
fixtures:

| Source | Signals |
|---|---|
| Duy ingestion | data quality, missing/invalid records, file hash, ingestion status |
| Phat dashboard | review queue, RAG readiness, recent activity, dashboard views |
| Lap RAG | similarity score, retrieved context, citation count |
| Tuong prediction | status, confidence, review reason, manual review flag |

## UI Behavior Rules

- Suggestions must always be sorted by `final_score` descending.
- If `prediction_result.status == "needs_review"`, a suggestion with
  `source_module = "prediction"` must always be present.
- If no signals are available at all, return exactly one suggestion
  prompting the user to upload a source — never an empty list.
