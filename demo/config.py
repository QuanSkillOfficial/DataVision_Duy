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

# BACKEND_BASE_URL is the name the compose files use for the same value, so it
# is honoured as a fallback: the canonical stack and this repository's
# docker-compose.yml both set it.
BACKEND_BASE_URL: str = os.environ.get(
    "QS_BACKEND_URL",
    os.environ.get("BACKEND_BASE_URL", "http://localhost:8000/api"),
)
BACKEND_TIMEOUT_SECONDS: float = float(os.environ.get("QS_BACKEND_TIMEOUT", "10"))

# Split timeouts so a dead host fails fast while a slow model call still gets
# time to answer. requests accepts a (connect, read) tuple.
BACKEND_CONNECT_TIMEOUT_SECONDS: float = float(
    os.environ.get("QS_BACKEND_CONNECT_TIMEOUT", "3")
)
BACKEND_READ_TIMEOUT_SECONDS: float = float(
    os.environ.get("QS_BACKEND_READ_TIMEOUT", str(BACKEND_TIMEOUT_SECONDS))
)

# ─────────────────────────────────────────────
# RELEASE IDENTITY (DV-HUNG-04)
# ─────────────────────────────────────────────
# Injected by the deployment workflow so a reviewer can confirm exactly which
# release and environment the UI in front of them is running.
#
# The canonical cloud staging pipeline (deployment/cloud/docker-compose.staging.yml
# in DataVision_Duy) injects DATAVISION_RELEASE_SHA into every service, not
# QS_RELEASE_SHA. Without the fallback below, a UI deployed by that pipeline
# reports release_sha "unknown" and release_match "unknown", so DV-HUNG-04 could
# not be verified on the very environment it exists to describe. QS_* still wins
# when both are set, so a deployment can override the platform-wide value.

RELEASE_SHA: str = (
    os.environ.get("QS_RELEASE_SHA")
    or os.environ.get("DATAVISION_RELEASE_SHA", "")
)
IMAGE_DIGEST: str = os.environ.get("QS_IMAGE_DIGEST", "")
ENVIRONMENT: str = os.environ.get("QS_ENVIRONMENT", "local")
BUILD_TIMESTAMP: str = os.environ.get("QS_BUILD_TIMESTAMP", "")

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
