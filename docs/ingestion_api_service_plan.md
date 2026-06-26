# Ingestion API Service Plan

Owner: Nguyen Minh Duy

## Purpose

This document defines the future FastAPI service shape for running config-driven ingestion from the backend.

## Future Endpoints

### POST `/api/ingestion/run`

Request:

```json
{
  "source_config_path": "data_engineering/configs/superstore_csv.json"
}
```

Response:

```json
{
  "run_id": "uuid",
  "source_name": "superstore_sales_csv",
  "source_type": "csv",
  "status": "success",
  "records_read": 9994,
  "records_valid": 9994,
  "records_invalid": 0,
  "data_quality_score": 100.0
}
```

### GET `/api/ingestion/status/{run_id}`

Returns the run-specific log from:

```text
logs/runs/<run_id>.json
```

### GET `/api/ingestion/logs/{run_id}`

Returns the full ingestion log, including output paths, data quality details, and manifest metadata.

## Current CLI Equivalent

```powershell
python -m data_engineering.pipelines.ingestion_engine --config data_engineering/configs/superstore_csv.json
```

Run all default configs:

```powershell
python -m data_engineering.pipelines.ingestion_engine --all
```

## Backend Integration Notes

- The API should call `run_ingestion(source_config)`.
- The API should return the same log shape used in `logs/runs/<run_id>.json`.
- `USE_BACKEND=True` in Phi/Hung's UI can later call these endpoints instead of mock fixtures.

