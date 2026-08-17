from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cloud_compose_exposes_ui_only_through_authenticated_proxy() -> None:
    compose = read("deployment/cloud/docker-compose.staging.yml")
    overlay = read("deployment/cloud/docker-compose.staging-proxy.yml")
    nginx = read("deployment/staging/nginx-staging-ui.conf")

    assert "ports: !reset []" in overlay
    assert "ui-proxy:" in overlay
    assert "STAGING_ALLOWED_CIDRS" in overlay
    assert 'command: ["nginx", "-g", "daemon off;"]' in overlay
    assert "auth_basic_user_file /etc/nginx/htpasswd;" in nginx
    assert "include /etc/nginx/allowlist.conf;" in nginx
    assert "deny all;" in nginx
    assert '127.0.0.1:${BACKEND_PUBLIC_PORT:-8000}:8000' in compose
    assert "pg_isready -h 127.0.0.1" in compose


def test_deploy_workflow_applies_security_overlay_to_start_and_rollback() -> None:
    workflow = read(".github/workflows/deploy-staging.yml")

    assert "STAGING_UI_PASSWORD: ${{ secrets.STAGING_UI_PASSWORD }}" in workflow
    assert "STAGING_ALLOWED_CIDRS: ${{ vars.STAGING_ALLOWED_CIDRS }}" in workflow
    assert "cp deployment/cloud/docker-compose.staging-proxy.yml staging-bundle/" in workflow
    assert workflow.count("-f docker-compose.staging-proxy.yml") >= 5
    assert "refusing to roll back to an unauthenticated UI" in workflow


def test_cloud_release_requires_tls_and_real_browser_acceptance() -> None:
    workflow = read(".github/workflows/deploy-staging.yml")

    assert '[[ "$UI_URL" =~ ^https://' in workflow
    assert "--backend-url http://127.0.0.1:18000/api" in workflow
    assert "Run required browser journey through the protected proxy" in workflow
    assert "python scripts/week8_run_browser_e2e.py" in workflow
    assert "outputs/week8/hung_browser_e2e.json" in workflow


def test_ui_receives_exact_release_identity_from_manifest() -> None:
    compose = read("deployment/cloud/docker-compose.staging.yml")
    renderer = read("scripts/render_staging_env.py")

    assert "QS_RELEASE_SHA: ${QS_RELEASE_SHA:?QS_RELEASE_SHA is required}" in compose
    assert "QS_IMAGE_DIGEST: ${QS_IMAGE_DIGEST:?QS_IMAGE_DIGEST is required}" in compose
    assert '"QS_IMAGE_DIGEST": image_refs["ui"].split("@", 1)[1]' in renderer


def test_live_ingestion_status_exposes_document_hash(monkeypatch) -> None:
    from backend_stub import runtime

    observed: dict[str, object] = {}

    def fake_fetch_one(query: str, params=()):
        observed["query"] = query
        observed["params"] = params
        return {"file_hash_sha256": "a" * 64}

    monkeypatch.setattr(runtime, "_fetch_one", fake_fetch_one)
    result = runtime.latest_ingestion_status("run-1")

    assert result["file_hash_sha256"] == "a" * 64
    assert "d.file_hash_sha256" in str(observed["query"])
    assert "LEFT JOIN LATERAL" in str(observed["query"])
    assert observed["params"] == ("run-1",)
