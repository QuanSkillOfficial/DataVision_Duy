# Week 7 UI Runbook

## Install

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run Fixture Mode

```powershell
$env:QS_USE_BACKEND="false"
.\.venv\Scripts\streamlit.exe run demo\streamlit_app.py
```

Dashboard can open directly in fixture mode without Upload first.

## Run Backend Mode

```powershell
$env:QS_USE_BACKEND="true"
$env:QS_BACKEND_URL="http://localhost:8000/api"
.\.venv\Scripts\streamlit.exe run demo\streamlit_app.py
```

## Run Backend Stub

```powershell
.\.venv\Scripts\python.exe backend_stub\main.py
```

## Update Fixtures

Replace files in `demo/fixtures/week7/`, then run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_week7_fixture_validation.py
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest tests
.\.venv\Scripts\python.exe scripts\week7_ui_ci_smoke_test.py
```

Do not use full repo-root `pytest` as the main check unless `code_by_others` is
excluded; copied intern repos have their own import roots/dependencies.

## Screenshots

Create screenshots manually in `screenshots/week7_staging_ready_ui/` using the
checklist in that folder.
