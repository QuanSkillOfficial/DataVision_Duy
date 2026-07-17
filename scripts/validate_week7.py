from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.load_ingestion_outputs_to_postgres import run_dry_run


REQUIRED_FILES = [
    "data_engineering/ingestion/csv_ingestor.py",
    "data_engineering/ingestion/excel_ingestor.py",
    "data_engineering/ingestion/api_ingestor.py",
    "data_engineering/ingestion/pdf_ingestor.py",
    "data_engineering/pipelines/ingestion_engine.py",
    "data_engineering/pipelines/prediction_payload_builder.py",
    "data_engineering/pipelines/handoff_context.py",
    "data_engineering/storage/db_connection.py",
    "data_engineering/storage/postgres_writer.py",
    "scripts/load_ingestion_outputs_to_postgres.py",
    "scripts/week7_ci_ingestion_smoke_test.py",
    "scripts/week7_build_rag_handoff_package.py",
    "scripts/week7_build_prediction_payloads.py",
    "scripts/week7_build_ui_fixtures.py",
    "scripts/week7_data_pipeline_smoke_test.py",
    "logs/db_load_dry_run/duy_to_phat_db_smoke_plan.json",
    "outputs/rag_handoff/week7_document_pages_db_enriched.jsonl",
    "outputs/rag_handoff/week7_rag_handoff_manifest.json",
    "outputs/prediction_payloads/tuong_week7_prediction_payloads.json",
    "outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json",
    "outputs/ui_fixtures/duy_week7_database_enriched_summary.json",
    "tests/fixtures/data/sample_superstore_small.csv",
    "tests/fixtures/data/sample_product_sales_small.xlsx",
    "tests/fixtures/data/sample_api_products.json",
    "tests/fixtures/data/sample_dataflow_pages_small.jsonl",
    "tests/fixtures/data/sample_dataflow_small.pdf",
    "docs/week7_duy_ci_commands.md",
    "docs/week7_data_pipeline_runbook.md",
    "docs/week7_duy_to_tuong_additional_prediction_payloads.md",
    "docs/week7_team_integration_handoff.md",
    "docs/week7_cross_team_delivery_matrix.md",
    "docs/week7_shared_repo_structure.md",
    "docs/week7_deployment_runbook.md",
    "docs/week7_backend_stub_contract.md",
    "integration/shared_repo_manifest.json",
    ".env.example",
    "docker-compose.db.yml",
    "docker-compose.yml",
    "backend_stub/main.py",
    "backend_stub/Dockerfile",
    "backend_stub/requirements.txt",
    "deployment/Dockerfile.data",
    "deployment/database/init/00_extensions.sql",
    "scripts/week7_backend_stub_smoke_test.py",
    "scripts/week7_local_docker_integration_smoke_test.py",
    "scripts/week7_shared_repo_readiness_check.py",
    "scripts/week7_shared_integration_smoke_test.py",
    ".github/workflows/ci.yml",
]


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (PROJECT_ROOT / path).exists()]
    if missing:
        raise FileNotFoundError(f"Missing Week 7 files: {missing}")

    manifest = json.loads(
        (PROJECT_ROOT / "outputs/rag_handoff/week7_rag_handoff_manifest.json").read_text(encoding="utf-8")
    )
    payloads = json.loads(
        (PROJECT_ROOT / "outputs/prediction_payloads/tuong_week7_prediction_payloads.json").read_text(
            encoding="utf-8"
        )
    )
    additional_payloads = json.loads(
        (
            PROJECT_ROOT
            / "outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json"
        ).read_text(encoding="utf-8")
    )
    ui_fixture = json.loads(
        (PROJECT_ROOT / "outputs/ui_fixtures/duy_week7_database_enriched_summary.json").read_text(
            encoding="utf-8"
        )
    )
    team_handoff = (PROJECT_ROOT / "docs/week7_team_integration_handoff.md").read_text(
        encoding="utf-8"
    )
    manifest_json = json.loads(
        (PROJECT_ROOT / "integration/shared_repo_manifest.json").read_text(encoding="utf-8")
    )
    smoke_plan = run_dry_run(structured_record_limit=100)

    assert manifest["page_count"] == 36
    assert manifest["non_empty_pages"] == 36
    assert manifest["total_characters"] == 129028
    assert len(payloads) == 20
    assert len(additional_payloads) == 10
    assert payloads[10:] == additional_payloads
    assert all("source_id" in payload and "document_db_id" in payload for payload in payloads)
    assert ui_fixture["total_sources"] == 4
    assert ui_fixture["total_records_read"] == 11524
    assert smoke_plan["totals"]["structured_records"] == 100
    for member_section in ("Duy -> Phat", "Duy -> Lap", "Duy -> Tuong", "Duy -> Phi/Hung"):
        assert member_section in team_handoff
    assert set(manifest_json["owner_contracts"]) == {"Duy", "Phat", "Lap", "Tuong", "Phi/Hung"}
    assert "docker-compose.db.yml" in team_handoff
    assert "backend_stub/main.py" in team_handoff
    assert "F:\\" not in team_handoff
    assert "C:\\Users\\" not in team_handoff

    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for dependency in ("pandas", "openpyxl", "pymupdf", "requests", "pytest", "psycopg2-binary", "python-dotenv"):
        assert dependency in requirements

    print("Week 7 validation passed")
    print(f"Checked {len(REQUIRED_FILES)} required Week 7 files")
    print("Checked smoke DB plan: 4 sources, 36 pages, 100 structured records")
    print("Checked Lap, Tuong's 20 prediction payloads, Phi/Hung contracts, and shared Docker/CI drafts")
    if manifest.get("database_identity_status") != "database_ids_confirmed":
        print("Warning: database IDs remain pending until Phat's fixed schema and PostgreSQL are available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
