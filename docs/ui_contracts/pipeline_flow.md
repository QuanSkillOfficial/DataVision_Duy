# Platform Pipeline Flow — Week 5

This document maps how data flows end-to-end across the platform and
which UI contract governs each handoff.

```
Duy (Ingestion)
    ↓  ingestion_result_contract  →  dashboard_ui_contract.md
Phat (Database / Analytics)
    ↓  analytics_views            →  dashboard_ui_contract.md
Tuong (Prediction / ML)
    ↓  prediction_response        →  prediction_ui_contract.md
Lap (RAG)
    ↓  rag_response               →  rag_ui_contract.md
Phi & Hung (UI Integration Layer)
    ├── Dashboard      (reads Duy + Phat)
    ├── Prediction     (reads Tuong)
    ├── Chatbot        (reads Lap)
    ├── Suggestions    (reads Dashboard + Prediction + RAG)  → suggestion_ui_contract.md
    └── Reports        (reads everything above)              → report_ui_contract.md
```

---

## Service Layer Architecture

```
demo/
├── config.py                  ← USE_BACKEND switch (mock vs real)
├── services/
│   ├── service_client.py      ← single interface, pages call ONLY this
│   ├── mock_client.py         ← fixture-backed mock implementation
│   └── backend_client.py      ← real FastAPI implementation
├── fixtures/
│   ├── duy_ingestion_result.json
│   ├── phat_dashboard_overview.json
│   ├── lap_rag_response.json
│   └── tuong_prediction_response.json
├── dashboard_page.py     → service_client.get_dashboard_metrics / get_ingestion_status / get_recent_activity
├── prediction_page.py    → service_client.classify_document / classify_documents
├── chatbot_page.py       → service_client.ask_rag
├── suggestions_page.py   → service_client.generate_suggestions
└── reports_page.py       → service_client.generate_report
```

### Switching to a Real Backend

Change exactly one line in `demo/config.py`:

```python
USE_BACKEND = True
```

No page code changes. `service_client.py` automatically routes to
`backend_client.py`, which calls the FastAPI backend over HTTP at
`BACKEND_BASE_URL` (default `http://localhost:8000/api`).

---

## Per-Module Contract Index

| Module | Contract File | Service Functions |
|---|---|---|
| Duy + Phat | `dashboard_ui_contract.md` | `get_dashboard_metrics`, `get_ingestion_status`, `get_recent_activity` |
| Tuong | `prediction_ui_contract.md` | `classify_document`, `classify_documents` |
| Lap | `rag_ui_contract.md` | `ask_rag` |
| Phi/Hung (aggregation) | `suggestion_ui_contract.md` | `generate_suggestions` |
| Phi/Hung (aggregation) | `report_ui_contract.md` | `generate_report` |

---

## Session State Keys Used Across Pages

| Key | Set By | Read By |
|---|---|---|
| `source_context` | Upload page | Dashboard, Prediction, Reports |
| `dashboard_signals` | Dashboard page | Suggestions, Reports |
| `prediction_result` | Prediction page | Suggestions, Reports |
| `last_rag_response` | Chatbot page | Suggestions, Reports |
| `suggestions` | Suggestions page | Reports |
| `last_report_preview` / `last_report_evidence_table` | Reports page | Pipeline status sidebar |

---

## Pipeline Status Sidebar

`utils.get_flow_statuses()` now tracks 6 steps instead of 4:

```
Upload | Dash board | Prediction | Chatbot | Suggestion | Report
```

A step shows "Done" once its corresponding session-state key is
populated with real (or mock) data.
