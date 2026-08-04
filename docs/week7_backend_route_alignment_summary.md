# Week 7 Backend Route Alignment Summary

`BACKEND_BASE_URL` is `http://localhost:8000/api`.

Route paths in `backend_client.py` do not include another `/api` prefix.

| Service | Route |
|---|---|
| Dashboard metrics | `GET or POST /dashboard/metrics` |
| Recent activity | `GET /dashboard/recent-activity` |
| Ingestion status | `GET /ingestion/status` |
| Prediction | `POST /predict/document-type` |
| Batch prediction | `POST /predict/document-type/batch` |
| Prediction feedback | `POST /predict/feedback` |
| Review queue | `GET /predict/review-queue` |
| RAG | `POST /rag/query` |
| Suggestions | `POST /suggestions/generate` |
| Reports | `POST /reports/generate` |

Avoid `http://localhost:8000/api/api/...`.
