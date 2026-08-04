from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from render_staging_env import render  # noqa: E402


def test_render_uses_release_specific_images_and_url_encodes_password(tmp_path, monkeypatch):
    release_sha = "a" * 40
    monkeypatch.setenv("RELEASE_SHA", release_sha)
    monkeypatch.setenv("IMAGE_PREFIX", "ghcr.io/QuanSkillOfficial/DataVision")
    monkeypatch.setenv("POSTGRES_PASSWORD", "space and/@colon:")
    output = tmp_path / ".env.staging"

    render(output)

    rendered = output.read_text(encoding="utf-8")
    assert f'datavision-backend:{release_sha}"' in rendered
    assert f'datavision-ui:{release_sha}"' in rendered
    assert f'datavision-seed:{release_sha}"' in rendered
    assert "space%20and%2F%40colon%3A" in rendered
    assert 'DATAVISION_RELEASE_SHA="' + release_sha + '"' in rendered


def test_render_rejects_short_release_sha(tmp_path, monkeypatch):
    monkeypatch.setenv("RELEASE_SHA", "abc123")
    monkeypatch.setenv("IMAGE_PREFIX", "ghcr.io/example/datavision")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")

    with pytest.raises(ValueError, match="40-character"):
        render(tmp_path / ".env.staging")
