"""
tests/test_release_identity.py
================================
DV-HUNG-04: the UI must state which release and backend it is running against.

The Week 8 release rule is that every acceptance result identifies the exact
commit or digest that produced it. These tests keep the UI side of that rule
honest, including the case where the UI and backend disagree about the SHA.
"""

import importlib
from unittest.mock import patch

import pytest


@pytest.fixture
def identity_module(monkeypatch):
    """Reload config + release_identity with a controlled environment."""

    def _load(**env):
        for key in [
            "QS_RELEASE_SHA",
            "QS_IMAGE_DIGEST",
            "QS_ENVIRONMENT",
            "QS_BUILD_TIMESTAMP",
            "QS_USE_BACKEND",
            "DATAVISION_RELEASE_SHA",
        ]:
            monkeypatch.delenv(key, raising=False)
        for key, value in env.items():
            monkeypatch.setenv(key, value)

        import demo.config
        import demo.helpers.release_identity

        importlib.reload(demo.config)
        return importlib.reload(demo.helpers.release_identity)

    yield _load

    # Restore the default module state for the rest of the suite.
    import demo.config
    import demo.helpers.release_identity

    importlib.reload(demo.config)
    importlib.reload(demo.helpers.release_identity)


RELEASE_SHA = "68bd1e154b529ae836a65949c40b3cab4ea4fb3b"


def test_release_identity_reports_injected_deployment_values(identity_module):
    module = identity_module(
        QS_RELEASE_SHA=RELEASE_SHA,
        QS_IMAGE_DIGEST="sha256:abc123",
        QS_ENVIRONMENT="staging",
    )
    identity = module.get_release_identity()

    assert identity["release_sha"] == RELEASE_SHA
    assert identity["release_sha_short"] == RELEASE_SHA[:12]
    assert identity["image_digest"] == "sha256:abc123"
    assert identity["environment"] == "staging"


def test_release_identity_never_invents_a_sha(identity_module):
    """An unlabelled build must read as unknown, not as a valid release."""
    module = identity_module()
    identity = module.get_release_identity()

    assert identity["release_sha"] == module.UNKNOWN
    assert identity["release_sha_short"] == module.UNKNOWN


def test_release_sha_falls_back_to_the_canonical_staging_variable(identity_module):
    """The canonical cloud staging pipeline injects DATAVISION_RELEASE_SHA only.

    Reading QS_RELEASE_SHA alone meant a UI deployed by that pipeline reported
    an unknown release, which made DV-HUNG-04 unverifiable on real staging.
    """
    module = identity_module(DATAVISION_RELEASE_SHA=RELEASE_SHA)
    identity = module.get_release_identity()

    assert identity["release_sha"] == RELEASE_SHA
    assert identity["release_sha_short"] == RELEASE_SHA[:12]


def test_deployment_specific_sha_overrides_the_platform_wide_one(identity_module):
    """QS_RELEASE_SHA is the deployment's own value, so it must win."""
    other_sha = "ca19091095809047a143536186bd76d03f728449"
    module = identity_module(
        QS_RELEASE_SHA=RELEASE_SHA,
        DATAVISION_RELEASE_SHA=other_sha,
    )

    assert module.get_release_identity()["release_sha"] == RELEASE_SHA


def test_fixture_mode_never_claims_a_reachable_backend(identity_module):
    module = identity_module(QS_USE_BACKEND="false")
    health = module.probe_backend_health()

    assert health["state"] == "fixture"
    assert health["reachable"] is False
    assert health["release_sha"] is None


def test_backend_mode_reports_live_backend_identity(identity_module):
    module = identity_module(QS_USE_BACKEND="true", QS_RELEASE_SHA=RELEASE_SHA)
    healthy = {
        "data": {
            "ok": True,
            "service": "week7_backend_stub",
            "release_sha": RELEASE_SHA,
            "environment": "staging",
        },
        "status": "success",
        "metadata": {"elapsed_ms": 7},
    }
    with patch("demo.services.service_client.get_backend_health", return_value=healthy):
        health = module.probe_backend_health()

    assert health["state"] == "live"
    assert health["reachable"] is True
    assert health["release_sha"] == RELEASE_SHA
    assert health["latency_ms"] == 7


def test_unreachable_backend_is_reported_with_actionable_guidance(identity_module):
    module = identity_module(QS_USE_BACKEND="true")
    failure = {
        "data": None,
        "status": "error",
        "error": {"message": "Backend unavailable", "detail": "refused"},
        "metadata": {"error_kind": "unavailable", "endpoint": "/health"},
    }
    with patch("demo.services.service_client.get_backend_health", return_value=failure):
        health = module.probe_backend_health()

    assert health["state"] == "unreachable"
    assert health["reachable"] is False
    assert health["error_kind"] == "unavailable"
    assert health["hint"].strip()


@pytest.mark.parametrize(
    "ui_sha, backend_sha, expected",
    [
        (RELEASE_SHA, RELEASE_SHA, "match"),
        (RELEASE_SHA, "0000000000000000000000000000000000000000", "mismatch"),
        (RELEASE_SHA, None, "unknown"),
        ("unknown", RELEASE_SHA, "unknown"),
        ("", RELEASE_SHA, "unknown"),
    ],
)
def test_release_match_state(identity_module, ui_sha, backend_sha, expected):
    module = identity_module()
    assert module.release_match_state(ui_sha, backend_sha) == expected


def test_identity_evidence_bundles_identity_health_and_match(identity_module):
    module = identity_module(QS_USE_BACKEND="false", QS_RELEASE_SHA=RELEASE_SHA)
    evidence = module.build_identity_evidence()

    assert evidence["release_identity"]["release_sha"] == RELEASE_SHA
    assert evidence["backend_health"]["state"] == "fixture"
    assert evidence["release_match"] == "unknown"
