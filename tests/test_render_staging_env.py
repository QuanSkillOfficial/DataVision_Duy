from __future__ import annotations

import sys
import json
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from render_staging_env import render  # noqa: E402


def release_manifest(path: Path, release_sha: str, prefix: str) -> Path:
    images = {}
    for index, service in enumerate(("backend", "ui", "seed"), start=1):
        repository = f"{prefix.lower()}-{service}"
        digest = f"sha256:{str(index) * 64}"
        images[service] = {
            "repository": repository,
            "tag": f"{repository}:{release_sha}",
            "digest": digest,
            "ref": f"{repository}@{digest}",
        }
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "release_sha": release_sha,
                "source_ci_run_id": 123,
                "images": images,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_render_uses_release_digests_and_url_encodes_password(tmp_path, monkeypatch):
    release_sha = "a" * 40
    prefix = "ghcr.io/quanskillofficial/datavision"
    monkeypatch.setenv("RELEASE_SHA", release_sha)
    monkeypatch.setenv("IMAGE_PREFIX", prefix)
    monkeypatch.setenv("POSTGRES_PASSWORD", "space and/@colon:")
    monkeypatch.setenv("STAGING_ALLOWED_CIDRS", "203.0.113.7/32 198.51.100.0/24")
    output = tmp_path / ".env.staging"
    manifest = release_manifest(tmp_path / "release-manifest.json", release_sha, prefix)

    render(output, manifest)

    rendered = output.read_text(encoding="utf-8")
    assert f'datavision-backend@sha256:{"1" * 64}"' in rendered
    assert f'datavision-ui@sha256:{"2" * 64}"' in rendered
    assert f'datavision-seed@sha256:{"3" * 64}"' in rendered
    assert "space%20and%2F%40colon%3A" in rendered
    assert 'DATAVISION_RELEASE_SHA="' + release_sha + '"' in rendered
    assert 'STAGING_ALLOWED_CIDRS="203.0.113.7/32 198.51.100.0/24 127.0.0.1/32 172.16.0.0/12"' in rendered
    assert 'QS_ENVIRONMENT="staging"' in rendered
    assert f'QS_IMAGE_DIGEST="sha256:{"2" * 64}"' in rendered


def test_render_rejects_short_release_sha(tmp_path, monkeypatch):
    monkeypatch.setenv("RELEASE_SHA", "abc123")
    monkeypatch.setenv("IMAGE_PREFIX", "ghcr.io/example/datavision")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")

    with pytest.raises(ValueError, match="40-character"):
        render(tmp_path / ".env.staging", tmp_path / "release-manifest.json")


def test_render_rejects_manifest_for_another_release(tmp_path, monkeypatch):
    release_sha = "a" * 40
    prefix = "ghcr.io/example/datavision"
    monkeypatch.setenv("RELEASE_SHA", release_sha)
    monkeypatch.setenv("IMAGE_PREFIX", prefix)
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    manifest = release_manifest(tmp_path / "release-manifest.json", "b" * 40, prefix)

    with pytest.raises(ValueError, match="does not match"):
        render(tmp_path / ".env.staging", manifest)


@pytest.mark.parametrize("cidrs", ["not-a-cidr", "0.0.0.0/0", "::/0"])
def test_render_rejects_unsafe_allowlist(tmp_path, monkeypatch, cidrs):
    release_sha = "a" * 40
    prefix = "ghcr.io/example/datavision"
    monkeypatch.setenv("RELEASE_SHA", release_sha)
    monkeypatch.setenv("IMAGE_PREFIX", prefix)
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("STAGING_ALLOWED_CIDRS", cidrs)
    manifest = release_manifest(tmp_path / "release-manifest.json", release_sha, prefix)

    with pytest.raises(ValueError, match="STAGING_ALLOWED_CIDRS"):
        render(tmp_path / ".env.staging", manifest)
