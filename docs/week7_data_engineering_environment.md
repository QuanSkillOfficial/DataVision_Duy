# Week 7 Data Engineering Environment

Recommended Python: `3.11`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Dependencies cover pandas tabular processing, Excel, pdfplumber extraction, PyMuPDF fixture creation, HTTP ingestion, PostgreSQL, `.env` loading, and pytest.

Database variables follow `.env.example`. Secrets must be supplied by local `.env` or GitHub Actions secrets and must not be committed.
