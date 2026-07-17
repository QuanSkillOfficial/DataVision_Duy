# Week 7 Backend Stub Contract

## Purpose

`backend_stub/main.py` is a contract-only FastAPI service. It lets CI and the
UI validate route names, request shapes and response envelopes before the
production backend is available.

Start it locally:

```powershell
python -m pip install -r backend_stub/requirements.txt
uvicorn backend_stub.main:app --host 127.0.0.1 --port 8000
```

Run its smoke test:

```powershell
python scripts/week7_backend_stub_smoke_test.py
```

## Standard envelope

Success:

```json
{
  "status": "success",
  "data": {},
  "metadata": {
    "mode": "contract_stub",
    "backend_validation_pending": true
  }
}
```

Error:

```json
{
  "status": "error",
  "data": null,
  "error": {
    "message": "Backend unavailable",
    "detail": "..."
  },
  "metadata": {}
}
```

## Routes

| Method | Route | Owner contract |
| --- | --- | --- |
| GET | `/api/health` | CI health probe |
| GET | `/api/dashboard/metrics` | Phat views -> Phi/Hung |
| GET | `/api/dashboard/overview` | Dashboard alias |
| GET | `/api/dashboard/recent-activity` | Phat recent activity |
| GET | `/api/dashboard/review-queue` | Prediction review queue |
| GET | `/api/ingestion/status` | Duy run status |
| GET | `/api/ingestion/status/{run_id}` | Duy specific run |
| POST | `/api/ingestion/run` | Duy future API |
| POST | `/api/rag/query` | Lap response contract |
| POST | `/api/predict/document-type` | Tuong single prediction |
| POST | `/api/predict/document-type/batch` | Tuong batch prediction |
| POST | `/api/predict/feedback` | Phi/Hung -> Tuong feedback |
| GET | `/api/predict/review-queue` | Tuong/Phat review queue |
| POST | `/api/suggestions/generate` | Cross-module signals |
| POST | `/api/reports/generate` | Evidence report |

## Boundary rules

- The stub does not write PostgreSQL rows.
- The stub does not claim a real model prediction.
- Missing/short text returns `waiting_for_source`.
- Invalid prediction metadata returns `failed`.
- A valid text request returns `needs_review` until the real model service is
  connected.
- `document_external_id`, `document_db_id`, `source_id` and
  `ingestion_run_id` remain distinct fields.

The production backend may replace this service only when it preserves the
route and envelope contracts or updates the shared UI contract at the same
time.
