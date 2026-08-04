"""
demo/config.py
==============
Central configuration switch for the Quansolution Streamlit demo.

USE_BACKEND = False  -> Mock mode (uses demo/services/mock_client.py + fixtures)
USE_BACKEND = True   -> Backend mode (uses demo/services/backend_client.py -> FastAPI)

Only this file needs to change to switch the entire UI from mock data to a
real backend. No page or service_client code needs to change.
"""

from __future__ import annotations

import os

# ─────────────────────────────────────────────
# MODE SWITCH
# ─────────────────────────────────────────────

# Set to True once the FastAPI backend is available.
# Can also be overridden via environment variable: QS_USE_BACKEND=true
USE_BACKEND: bool = os.environ.get("QS_USE_BACKEND", "false").lower() == "true"

# ─────────────────────────────────────────────
# BACKEND SETTINGS (used only when USE_BACKEND = True)
# ─────────────────────────────────────────────

BACKEND_BASE_URL: str = os.environ.get(
    "QS_BACKEND_URL",
    os.environ.get("BACKEND_BASE_URL", "http://localhost:8000/api"),
)
BACKEND_TIMEOUT_SECONDS: float = 10.0

# ─────────────────────────────────────────────
# FIXTURE SETTINGS (used only when USE_BACKEND = False)
# ─────────────────────────────────────────────

FIXTURES_DIR: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures"
)

# ─────────────────────────────────────────────
# PREDICTION THRESHOLDS (must match Tuong's contract)
# ─────────────────────────────────────────────

PREDICTION_CONFIDENCE_THRESHOLD: float = 0.60

# ─────────────────────────────────────────────
# RAG SIMILARITY BADGE THRESHOLDS (must match Lap's contract)
# ─────────────────────────────────────────────

RAG_SIMILARITY_HIGH: float = 0.80
RAG_SIMILARITY_MEDIUM: float = 0.60


def get_mode_label() -> str:
    """Human-readable label for the current data mode, shown in the UI."""
    return "Backend (FastAPI) Mode" if USE_BACKEND else "Mock Fixture Mode"
