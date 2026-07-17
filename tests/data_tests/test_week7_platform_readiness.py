from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_env_example_contains_shared_runtime_keys() -> None:
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in (
        "DB_HOST=",
        "DB_PORT=",
        "DB_NAME=",
        "DB_USER=",
        "DB_PASSWORD=",
        "BACKEND_BASE_URL=",
        "QS_USE_BACKEND=",
        "UI_PORT=",
    ):
        assert key in content


def test_compose_drafts_define_database_and_backend() -> None:
    database_compose = (ROOT / "docker-compose.db.yml").read_text(encoding="utf-8")
    full_compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "pgvector/pgvector:pg16" in database_compose
    assert "services:" in database_compose and "db:" in database_compose
    assert "db:" in full_compose and "backend:" in full_compose
    assert "ingestion-smoke:" in full_compose


def test_backend_stub_exposes_required_route_names() -> None:
    source = (ROOT / "backend_stub/main.py").read_text(encoding="utf-8")
    for route in (
        "/api/health",
        "/api/dashboard/metrics",
        "/api/rag/query",
        "/api/predict/document-type",
        "/api/predict/feedback",
        "/api/suggestions/generate",
        "/api/reports/generate",
    ):
        assert route in source


def test_shared_manifest_is_valid_and_has_all_owners() -> None:
    manifest = json.loads(
        (ROOT / "integration/shared_repo_manifest.json").read_text(encoding="utf-8")
    )
    assert set(manifest["owner_contracts"]) == {"Duy", "Phat", "Lap", "Tuong", "Phi/Hung"}
    assert manifest["canonical_ids"]["source_id"].startswith("Integer")
    assert "duy" in manifest["source_repositories"]


def test_new_platform_scripts_are_syntax_valid() -> None:
    paths = [
        ROOT / "backend_stub/main.py",
        ROOT / "scripts/week7_backend_stub_smoke_test.py",
        ROOT / "scripts/week7_local_docker_integration_smoke_test.py",
        ROOT / "scripts/week7_shared_repo_readiness_check.py",
        ROOT / "scripts/week7_shared_integration_smoke_test.py",
    ]
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_deployment_runbook_names_owner_boundaries() -> None:
    content = (ROOT / "docs/week7_deployment_runbook.md").read_text(encoding="utf-8")
    for phrase in (
        "schema; Duy owns the ingestion loader",
        "Phat owns the final database",
        "Lap inserts",
        "Tuong prediction logs",
        "Phi/Hung",
    ):
        assert phrase in content
