# Session State Flow & Implementation Guide

This guide explains the Week 2 vertical demo flow and provides step-by-step instructions, file templates, mock-service examples, and testing/checklist items.

## Goal
Build a Streamlit demo moving metadata and context through four pages:
Upload → Dashboard → Suggestions → Reports

## Week 2 Work Tracker

Use this checklist to track implementation progress.

### Task 1: Build one complete vertical demo flow
- [x] Update `demo/streamlit_app.py` so the demo supports the full vertical flow: Upload → Dashboard → Suggestions → Reports.
- [x] Update Upload page to accept sample CSV/PDF/TXT files.
- [x] Update Upload page to accept source links.
- [x] Store source metadata in `st.session_state['source_context']`.
- [x] Include key source fields: `id`, `filename` or link value, `source_type`, `uploaded_at`, and parsed text/preview when available.
- [x] Update Dashboard page to read `st.session_state['source_context']`.
- [x] Generate basic data-health signals from the uploaded source context.
- [x] Store dashboard signals in `st.session_state['dashboard_signals']`.
- [x] Update Suggestions page to read dashboard signals.
- [x] Store generated suggestions in `st.session_state['suggestions']`.
- [x] Update Reports page to use suggestion output as the main input, with upload context and dashboard signals included as supporting evidence.
- [x] Verify data moves from page to page without re-uploading.
- [x] Update this file, `demo/session_state_flow_notes.md`, with final flow notes.
- [x] Capture screenshots in `screenshots/week2_vertical_flow/`.

### Task 2: Add mock service contracts
- [x] Create `demo/mock_services.py`.
- [x] Add `mock_get_dashboard_metrics(source_context)`.
- [x] Add `mock_generate_suggestions(dashboard_signals)`.
- [x] Add `mock_generate_report(evidence_context)`.
- [x] Add `mock_get_prediction_summary(source_context)`.
- [x] Make the Streamlit pages call these mock services instead of using scattered page-only mock logic.

Task 2 status:
The mock service contracts are implemented in `demo/mock_services.py`. Suggestion scoring is separated into `demo/mock_suggestion_engine.py`, and the Streamlit pages call these local mock contracts as future backend API stand-ins.

### Task 3: Improve suggestion scoring
- [x] Create `demo/mock_suggestion_engine.py`.
- [x] Create `suggestion_engine_concept_v2.md`.
- [x] Add `urgency_score` to each suggestion.
- [x] Add `impact_score` to each suggestion.
- [x] Add `confidence_score` to each suggestion.
- [x] Add `effort_score` to each suggestion.
- [x] Add `final_score` to each suggestion.
- [x] Add `priority` or `final_priority` as High / Medium / Low.
- [x] Implement the scoring formula:
  ```py
  suggestion_score = (
      0.35 * urgency_score +
      0.30 * impact_score +
      0.20 * confidence_score -
      0.15 * effort_score
  )
  ```
- [x] Sort suggestions by `final_score` descending.
- [x] Show scoring details clearly in the Suggestions page.

Task 3 status:
Suggestion scoring is implemented in `demo/mock_suggestion_engine.py`. It clamps component scores to `0..1`, computes `final_score`, maps `final_priority`, and returns suggestions sorted by `final_score` descending.

### Task 4: Improve report prompt with strict schema
- [x] Create `report_prompt_draft_v2.txt`.
- [x] Add the strict report structure:
  ```text
  ### {Report Title}
  #### Executive Summary
  #### Evidence Used
  #### Key Findings
  #### Risks or Issues
  #### Recommendations
  #### Data Quality Limitations
  #### Next Actions
  ```
- [x] Add strict rule: "Use only available evidence. Do not invent metrics, facts, or numbers."
- [x] Update the Reports page, prompt template, and mock report payload so generated drafts follow the strict schema.

Task 4 status:
The strict report schema is documented in `report_prompt_draft_v2.txt`, implemented in `demo/prompt_templates.py`, and reflected in the `sections` payload returned by `mock_generate_report(evidence_context)`. The current Report page displays the restrained suggestion-based draft sections and does not show a prompt preview.

### Task 5: Prepare Friday demo
- [x] Create `week2_demo_script.md`.
- [x] Show the Streamlit app running.
- [x] Demo uploading one sample source.
- [x] Show Dashboard receiving the same source context.
- [x] Show Suggestions generated from dashboard signals.
- [x] Show Report draft using suggestion output as the main input, with upload + dashboard context included as supporting evidence.
- [x] Explain what is mocked now.
- [x] Explain what will later connect to backend APIs.
- [x] Save demo screenshots under `screenshots/week2_vertical_flow/`. User will recapture latest UI screenshots after final page changes.

Task 5 status:
The Friday demo script is updated for the latest UI. The demo still follows Upload -> Dashboard -> Suggestions -> Report, and the Report step is now described as a restrained suggestion-based draft. Screenshot capture is left to the user.

### Final verification
- [x] Run the app with `streamlit run demo/streamlit_app.py`.
- [x] Test one CSV upload.
- [x] Test one TXT or PDF upload if available.
- [x] Test one source link.
- [x] Confirm `source_context`, `dashboard_signals`, and `suggestions` persist in session state.
- [x] Confirm report output does not invent unsupported numbers or facts.
- [x] Confirm Report waits for generated suggestions before producing the draft.
- [x] Review all expected files before demo.

## Expected files to create/update
- [x] `demo/streamlit_app.py` — vertical flow UI and navigation
- [x] `demo/mock_services.py` — mock API contract functions
- [x] `demo/mock_suggestion_engine.py` — suggestion generator + scoring
- [x] `report_prompt_draft_v2.txt` — strict report schema prompt
- [x] `demo/session_state_flow_notes.md` — this file
- [x] `suggestion_engine_concept_v2.md` — concept + scoring details
- [x] `week2_demo_script.md` — demo script and mocked vs real
- [x] `screenshots/week2_vertical_flow/` — directory for screenshots. Screenshots are user-captured and may need refreshing after UI changes.

## Task 1 Implementation Notes

Implemented session-state flow:
Upload writes processed files/links to `st.session_state['source_context']`.
Dashboard reads `source_context`, computes data-health signals, and writes `st.session_state['dashboard_signals']`.
Suggestions reads `dashboard_signals`, generates action suggestions, and writes `st.session_state['suggestions']`.
Reports reads `source_context`, `dashboard_signals`, and `suggestions`, then writes `st.session_state['report_evidence_context']` before generating the draft preview.
The Reports detail page is intentionally restrained: it does not show evidence counters, prompt preview, or complex report controls. It requires `st.session_state['suggestions']` and uses the suggestion output as the main input to the draft.

Current UI note:
The main Friday demo flow follows the current Streamlit pages: Upload & Analyze -> Dash board -> Suggestion -> Report. The presenter uploads once on Upload & Analyze, selects a dashboard template, clicks Generate Dashboard, then uses Generate Suggestions and Generate Reports on the next pages. The pages are connected through `st.session_state`, so the same source context moves from upload metadata into dashboard signals, scored suggestions, and the report draft.

## High-level steps
1. Upload page
   - Allow uploading CSV/PDF/TXT or entering a source link.
   - Save `source_context` in `st.session_state['source_context']` with keys: `id`, `filename`, `source_type`, `original_text` (if parsed), `uploaded_at`.

2. Dashboard page
   - Read `st.session_state['source_context']`.
   - Call `mock_get_dashboard_metrics(source_context)` to receive signals like `parsing_coverage`, `data_quality_score`, `processing_status`.
   - Display simple data-health indicators and flags.

3. Suggestions page
   - Use dashboard signals to call `mock_generate_suggestions(dashboard_signals)` or use `mock_suggestion_engine`.
   - Each suggestion should include: `title`, `reason`, `source_signal`, `urgency_score`, `impact_score`, `confidence_score`, `effort_score`, `final_score`, `priority`, `next_action`.
   - Sort suggestions by `final_score` descending.

4. Reports page
   - Require generated suggestions before showing a draft.
   - Aggregate top suggestions as the main input, with `source_context` and dashboard metrics as supporting evidence.
   - Call `mock_generate_report(evidence_context)` to produce a restrained report draft following the strict schema (see below).

## Mock service templates (examples)

### demo/mock_services.py
```py
def mock_get_dashboard_metrics(source_context):
    return {
        "source_count": 1,
        "data_quality_score": 82,
        "processing_status": "ready",
        "duplicate_risk": "low",
        "parsing_coverage": 0.91
    }

def mock_generate_suggestions(dashboard_signals):
    # Return a list of suggestion dicts (see suggestion schema)
    return []

def mock_generate_report(evidence_context):
    return {
        "title": "Domain - Suggestion Summary",
        "sections": [
            {"Section": "Title", "Preview": "Domain - Suggestion Summary"},
            {"Section": "Executive Summary", "Preview": "..."},
            {"Section": "Evidence Used", "Preview": "..."},
            {"Section": "Key Findings", "Preview": "..."},
            {"Section": "Risks or Issues", "Preview": "..."},
            {"Section": "Recommendations", "Preview": "..."},
            {"Section": "Data Quality Limitations", "Preview": "..."},
            {"Section": "Next Actions", "Preview": "..."},
        ],
    }

def mock_get_prediction_summary(source_context):
    return {"predicted_labels": [], "confidence": 0.75}
```

### demo/mock_suggestion_engine.py
```py
# Scoring formula
# suggestion_score = 0.35*urgency + 0.30*impact + 0.20*confidence - 0.15*effort

def compute_suggestion_score(suggestion):
    urgency = _clamp_score(suggestion.get('urgency_score', 0))
    impact = _clamp_score(suggestion.get('impact_score', 0))
    confidence = _clamp_score(suggestion.get('confidence_score', 0))
    effort = _clamp_score(suggestion.get('effort_score', 0))
    score = 0.35*urgency + 0.30*impact + 0.20*confidence - 0.15*effort
    return round(_clamp_score(score), 2)

def rank_priority(score):
    if score >= 0.6:
        return 'High'
    if score >= 0.35:
        return 'Medium'
    return 'Low'
```

## Suggestion schema
- `title` (str)
- `reason` (str)
- `source_signal` (str)
- `urgency_score` (0..1)
- `impact_score` (0..1)
- `confidence_score` (0..1)
- `effort_score` (0..1)
- `final_score` (0..1)
- `priority` (High/Medium/Low)
- `next_action` (str)

## Report prompt schema (strict)
Every report must follow this structure. Use only available evidence.
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

## Run & test locally
1. Activate virtual env and install dependencies (if not already):
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# or at minimum: pip install streamlit
```
2. Run the app:
```powershell
streamlit run demo/streamlit_app.py
```

## Checklist for demo
- [x] Upload accepts CSV/PDF/TXT and stores `source_context`.
- [x] Dashboard reads `source_context` and shows metrics from mock service.
- [x] Suggestions are generated, scored, and ranked.
- [x] Report draft follows strict schema, uses only evidence, and depends on the generated suggestion output.
- [x] Screenshot directory exists at `screenshots/week2_vertical_flow/`. User will refresh screenshots when the UI changes.
- [x] `week2_demo_script.md` explains what is mocked vs what will be real APIs.

## What to screenshot
- Upload page after successful upload (show `source_context`).
- Dashboard with metrics and flags.
- Suggestions page showing ranked suggestions and scores.
- Report page showing the restrained suggestion-based draft sections.

## Example minimal `st.session_state['source_context']`
```py
{
  'id': 'src-001',
  'filename': 'sample.csv',
  'source_type': 'csv',
  'uploaded_at': '2026-05-25T10:00:00Z',
  'original_text': '...'
}
```

## Next steps (suggested)
1. I can implement `demo/mock_services.py` and `demo/mock_suggestion_engine.py` now.
2. Then I will wire `demo/streamlit_app.py` pages to use these mocks and persist `st.session_state`.

---
Generated on 2026-05-25.
