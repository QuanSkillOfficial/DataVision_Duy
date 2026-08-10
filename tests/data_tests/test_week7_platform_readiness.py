from __future__ import annotations

import ast
import json
import re
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

    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "module-parity:" in workflow
    assert "python scripts/verify_module_provenance.py" in workflow
    assert "needs: module-parity" in workflow
    assert "if: ${{ needs.module-discovery" not in workflow
    assert "needs.module-discovery.outputs" not in workflow
    assert "hashFiles(" not in workflow


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
    assert manifest["historical_components"]["week1_ingestion_foundation"][
        "required_for_week7"
    ] is False
    assert manifest["historical_components"]["week2"]["required_for_week7"] is False


def test_shared_history_uses_portable_paths_and_declares_submodule() -> None:
    run_history = (ROOT / "logs/ingestion_runs.jsonl").read_text(encoding="utf-8")
    assert re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]", run_history) is None

    submodules = (ROOT / ".gitmodules").read_text(encoding="utf-8")
    assert "path = week1_ingestion_foundation" in submodules
    assert "url = https://github.com/minzi03/QuanSolution_DataVision_Platform.git" in submodules


def test_new_platform_scripts_are_syntax_valid() -> None:
    paths = [
        ROOT / "backend_stub/main.py",
        ROOT / "scripts/week7_backend_stub_smoke_test.py",
        ROOT / "scripts/week7_local_docker_integration_smoke_test.py",
        ROOT / "scripts/week7_duy_phat_docker_db_integration_test.py",
        ROOT / "scripts/week7_apply_database_schema.py",
        ROOT / "scripts/week7_verify_db_load_result.py",
        ROOT / "scripts/week7_shared_repo_readiness_check.py",
        ROOT / "scripts/week7_shared_integration_smoke_test.py",
    ]
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    subprocess_wrappers = [
        ROOT / "scripts/week7_local_docker_integration_smoke_test.py",
        ROOT / "scripts/week7_duy_phat_docker_db_integration_test.py",
        ROOT / "scripts/week7_shared_integration_smoke_test.py",
        ROOT / "scripts/week7_build_lap_mapping_summary.py",
        ROOT / "scripts/week7_build_tuong_mapping_summary.py",
        ROOT / "scripts/week7_build_phi_hung_mapping_summary.py",
    ]
    for path in subprocess_wrappers:
        source = path.read_text(encoding="utf-8")
        assert 'encoding="utf-8"' in source
        assert 'errors="replace"' in source
        if "mapping_summary" in path.name:
            assert "_redact_machine_paths" in source


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
