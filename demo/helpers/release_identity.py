"""
demo/helpers/release_identity.py
==================================
Release identity and backend health resolution (DV-HUNG-04).

Week 8 acceptance requires that a reviewer looking at a running UI can confirm
*which release* and *which backend* they are looking at, without trusting a
screenshot caption. This module resolves that identity from the environment
injected at deployment time and from a live backend health probe.

No Streamlit import here: `demo/helpers/ui_status.py` renders it, and CI
scripts reuse the same resolution to write traceable evidence.
"""

from __future__ import annotations

from typing import Optional

from demo.config import (
    BACKEND_BASE_URL,
    BUILD_TIMESTAMP,
    ENVIRONMENT,
    IMAGE_DIGEST,
    RELEASE_SHA,
    USE_BACKEND,
    get_mode_label,
)
from demo.services.service_errors import (
    error_hint,
    error_kind,
    error_message,
    is_error,
)

UNKNOWN = "unknown"


def _short_sha(sha: str) -> str:
    """Abbreviate a git SHA, but leave readable labels intact.

    Blindly truncating turned a label like "e2e-local-run" into "e2e-local-ru",
    which reads as corrupted rather than shortened.
    """
    if not sha:
        return UNKNOWN
    is_full_sha = len(sha) >= 40 and all(char in "0123456789abcdefABCDEF" for char in sha)
    return sha[:12] if is_full_sha else sha


def get_release_identity() -> dict:
    """Resolve the identity of the UI build currently serving the page."""
    return {
        "release_sha": RELEASE_SHA or UNKNOWN,
        "release_sha_short": _short_sha(RELEASE_SHA),
        "image_digest": IMAGE_DIGEST or UNKNOWN,
        "environment": ENVIRONMENT or UNKNOWN,
        "build_timestamp": BUILD_TIMESTAMP or UNKNOWN,
        "data_mode": "backend" if USE_BACKEND else "fixture",
        "data_mode_label": get_mode_label(),
        "backend_base_url": BACKEND_BASE_URL if USE_BACKEND else None,
    }


def probe_backend_health() -> dict:
    """Probe the backend and report its liveness and release identity.

    Returns a flat dict that is safe to render and to serialise into evidence:
        reachable, state, message, hint, service, release_sha, environment,
        latency_ms, error_kind.

    `state` is one of: "live", "unreachable", "fixture".
    """
    # Imported lazily so fixture-mode callers never touch the HTTP client.
    from demo.services.service_client import get_backend_health

    if not USE_BACKEND:
        return {
            "reachable": False,
            "state": "fixture",
            "message": "Fixture mode - no backend is being contacted.",
            "hint": "Set QS_USE_BACKEND=true and QS_BACKEND_URL to run against a real backend.",
            "service": None,
            "release_sha": None,
            "environment": None,
            "latency_ms": None,
            "error_kind": None,
        }

    response = get_backend_health()

    if is_error(response):
        return {
            "reachable": False,
            "state": "unreachable",
            "message": error_message(response, "Backend health check failed"),
            "hint": error_hint(response),
            "service": None,
            "release_sha": None,
            "environment": None,
            "latency_ms": (response.get("metadata") or {}).get("elapsed_ms"),
            "error_kind": error_kind(response),
        }

    data = response.get("data") or {}
    metadata = response.get("metadata") or {}
    return {
        "reachable": True,
        "state": "live",
        "message": "Backend responded to the health check.",
        "hint": "",
        "service": data.get("service"),
        "release_sha": data.get("release_sha"),
        "environment": data.get("environment"),
        "latency_ms": metadata.get("elapsed_ms"),
        "error_kind": None,
    }


def release_match_state(ui_sha: str, backend_sha: Optional[str]) -> str:
    """Compare UI and backend release SHAs.

    A mismatch is a release-governance problem: the acceptance evidence would
    otherwise describe two different builds as one release.

    Returns: "match", "mismatch" or "unknown".
    """
    if not ui_sha or ui_sha == UNKNOWN or not backend_sha:
        return "unknown"
    return "match" if ui_sha == backend_sha else "mismatch"


def build_identity_evidence() -> dict:
    """Identity + health in one dict, for CI evidence artifacts."""
    identity = get_release_identity()
    health = probe_backend_health()
    return {
        "release_identity": identity,
        "backend_health": health,
        "release_match": release_match_state(
            identity["release_sha"], health.get("release_sha")
        ),
    }
