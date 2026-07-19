from __future__ import annotations

import json
import re
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
    "data_engineering/validation/data_quality.py",
    "data_engineering/utils/path_utils.py",
    "data_engineering/utils/log_utils.py",
    "data_engineering/utils/file_utils.py",
    "data_engineering/configs/superstore_csv.json",
    "data_engineering/configs/product_sales_excel.json",
    "data_engineering/configs/dummyjson_products_api.json",
    "data_engineering/configs/dataflow_pdf.json",
    "scripts/load_ingestion_outputs_to_postgres.py",
    "scripts/week7_apply_database_schema.py",
    "scripts/week7_duy_phat_docker_db_integration_test.py",
    "scripts/week7_verify_db_load_result.py",
    "scripts/week7_ci_ingestion_smoke_test.py",
    "scripts/week7_build_rag_handoff_package.py",
    "scripts/week7_build_prediction_payloads.py",
    "scripts/week7_build_ui_fixtures.py",
    "scripts/week7_build_shared_test_fixtures.py",
    "scripts/week7_build_phat_mapping_summary.py",
    "scripts/week7_build_lap_mapping_summary.py",
    "scripts/week7_build_tuong_mapping_summary.py",
    "scripts/week7_build_phi_hung_mapping_summary.py",
    "scripts/week7_data_pipeline_smoke_test.py",
    "logs/db_load_dry_run/duy_to_phat_db_smoke_plan.json",
    "logs/db_load_results/duy_to_phat_db_load_result.json",
    "logs/db_load_results/phat_week7_external_database_proof.json",
    "outputs/phat_handoff/phat_week7_mapping_summary.json",
    "logs/lap_handoff/lap_week7_external_proof.json",
    "outputs/lap_handoff/lap_week7_mapping_summary.json",
    "docs/week7_duy_lap_mapping_result.md",
    "logs/tuong_handoff/tuong_week7_external_proof.json",
    "outputs/tuong_handoff/tuong_week7_mapping_summary.json",
    "docs/week7_duy_tuong_mapping_result.md",
    "outputs/hung_handoff/hung_week7_mapping_summary.json",
    "logs/hung_handoff/hung_week7_external_proof.json",
    "docs/week7_duy_phi_hung_mapping_result.md",
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
    "docs/week7_ci_ingestion_smoke_test_result.md",
    "docs/week7_db_modes_for_ingestion.md",
    "docs/week7_duy_phat_real_db_loading_result.md",
    "docs/week7_duy_to_lap_rag_handoff.md",
    "docs/week7_duy_to_tuong_prediction_payload_contract.md",
    "docs/week7_duy_to_phi_hung_ui_fixture_contract.md",
    "docs/week7_shared_test_fixtures.md",
    "docs/week7_data_engineering_environment.md",
    "docs/week7_data_tests_result.md",
    "docs/week7_data_pipeline_runbook.md",
    "docs/week7_duy_to_tuong_additional_prediction_payloads.md",
    "docs/week7_team_integration_handoff.md",
    "docs/week7_cross_team_delivery_matrix.md",
    "docs/week7_shared_repo_structure.md",
    "docs/week7_shared_repo_cleanup.md",
    "docs/week7_ci_cd_delivery_checklist.md",
    "docs/week7_github_ci_cd_integration_plan.md",
    "docs/week7_deployment_runbook.md",
    "docs/week7_final_project_review.md",
    "docs/week7_backend_stub_contract.md",
    "integration/shared_repo_manifest.json",
    "requirements.txt",
    ".gitmodules",
    ".env.example",
    "docker-compose.db.yml",
    "docker-compose.yml",
    "backend_stub/main.py",
    "backend_stub/Dockerfile",
    "backend_stub/requirements.txt",
    "deployment/Dockerfile.data",
    "deployment/database/init/00_extensions.sql",
    "deployment/database/init/10_phat_schema_v4_fixed.sql",
    "outputs/integration/week7_duy_phat_docker_db_result.json",
    "outputs/integration/week7_local_docker_smoke_result.json",
    "outputs/integration/week7_shared_repo_readiness.json",
    "outputs/integration/week7_shared_integration_smoke_result.json",
    "scripts/week7_backend_stub_smoke_test.py",
    "scripts/week7_local_docker_integration_smoke_test.py",
    "scripts/week7_shared_repo_readiness_check.py",
    "scripts/week7_shared_integration_smoke_test.py",
    ".github/workflows/ci.yml",
]

WINDOWS_ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]")


def iter_string_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_string_values(item)


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
    phat_mapping = json.loads(
        (
            PROJECT_ROOT
            / "outputs/phat_handoff/phat_week7_mapping_summary.json"
        ).read_text(encoding="utf-8")
    )
    phat_identity_proof = json.loads(
        (
            PROJECT_ROOT
            / "logs/db_load_results/phat_week7_external_database_proof.json"
        ).read_text(encoding="utf-8")
    )
    current_db_proof = json.loads(
        (
            PROJECT_ROOT
            / "logs/db_load_results/duy_to_phat_db_load_result.json"
        ).read_text(encoding="utf-8")
    )
    docker_db_proof = json.loads(
        (
            PROJECT_ROOT
            / "outputs/integration/week7_duy_phat_docker_db_result.json"
        ).read_text(encoding="utf-8")
    )
    local_docker_proof = json.loads(
        (
            PROJECT_ROOT
            / "outputs/integration/week7_local_docker_smoke_result.json"
        ).read_text(encoding="utf-8")
    )
    lap_mapping = json.loads(
        (
            PROJECT_ROOT
            / "outputs/lap_handoff/lap_week7_mapping_summary.json"
        ).read_text(encoding="utf-8")
    )
    lap_external_proof = json.loads(
        (
            PROJECT_ROOT
            / "logs/lap_handoff/lap_week7_external_proof.json"
        ).read_text(encoding="utf-8")
    )
    tuong_mapping = json.loads(
        (
            PROJECT_ROOT
            / "outputs/tuong_handoff/tuong_week7_mapping_summary.json"
        ).read_text(encoding="utf-8")
    )
    tuong_external_proof = json.loads(
        (
            PROJECT_ROOT
            / "logs/tuong_handoff/tuong_week7_external_proof.json"
        ).read_text(encoding="utf-8")
    )
    hung_mapping = json.loads(
        (
            PROJECT_ROOT
            / "outputs/hung_handoff/hung_week7_mapping_summary.json"
        ).read_text(encoding="utf-8")
    )
    hung_external_proof = json.loads(
        (
            PROJECT_ROOT
            / "logs/hung_handoff/hung_week7_external_proof.json"
        ).read_text(encoding="utf-8")
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
    assert manifest["database_identity_status"] == "database_ids_confirmed"
    assert manifest["source_id"] == 4
    assert manifest["document_db_id"] == 1
    assert manifest["current_ingestion_run_loaded"] is True
    assert len(payloads) == 20
    assert len(additional_payloads) == 10
    assert payloads[10:] == additional_payloads
    assert all("source_id" in payload and "document_db_id" in payload for payload in payloads)
    assert all(payload["current_ingestion_runs_loaded"] is True for payload in payloads)
    assert ui_fixture["total_sources"] == 4
    assert ui_fixture["total_records_read"] == 11524
    assert ui_fixture["database_identity_status"] == "database_ids_confirmed"
    assert ui_fixture["latest_document"]["source_id"] == 4
    assert ui_fixture["latest_document"]["document_db_id"] == 1
    assert ui_fixture["current_ingestion_runs_loaded"] is True
    assert phat_mapping["status"] == "passed"
    assert phat_mapping["database_ci_smoke_test_passed"] is True
    assert phat_mapping["counts"]["structured_records"] == 11524
    assert phat_mapping["counts"]["document_chunks"] == 293
    assert phat_mapping["counts"]["prediction_logs"] == 10
    assert phat_identity_proof["status"] == "passed"
    assert phat_identity_proof["database_identity_status"] == "database_ids_confirmed"
    assert isinstance(phat_identity_proof["current_duy_runs_loaded"], bool)
    assert current_db_proof["status"] == "passed"
    assert current_db_proof["connection_status"] == "connected"
    assert current_db_proof["schema_version"] == "schema_v4_fixed"
    assert current_db_proof["current_duy_runs_loaded"] is True
    assert sorted(
        current_db_proof["snapshot_alignment"]["database_run_ids"]
    ) == sorted(current_db_proof["current_run_ids"])
    assert (
        current_db_proof["snapshot_alignment"]["all_current_run_ids_loaded"]
        is True
    )
    assert current_db_proof["verification"] == {
        "sources": 4,
        "ingestion_logs": 4,
        "pipeline_runs": 4,
        "documents": 1,
        "document_pages": 36,
        "structured_records": 11524,
    }
    assert docker_db_proof["status"] == "passed"
    assert docker_db_proof["services_stopped"] is True
    assert all(docker_db_proof["checks"].values())
    assert local_docker_proof["status"] == "passed"
    assert local_docker_proof["checks"]["full_up"] is True
    assert local_docker_proof["checks"]["backend_health"] is True
    assert local_docker_proof["checks"]["backend_contract_smoke"] is True
    assert local_docker_proof["checks"]["full_cleanup"] is True
    assert "removed" in local_docker_proof["runtime_note"].lower()
    assert lap_mapping["handoff_contract_passed"] is True
    assert lap_mapping["canonical_identity"]["source_id"] == 4
    assert lap_mapping["canonical_identity"]["document_db_id"] == 1
    assert lap_mapping["canonical_identity"]["document_external_id"] == "doc_dataflow_technical_report"
    assert lap_external_proof["handoff_contract_passed"] is True
    assert lap_external_proof["live_pgvector_proof_passed"] is False
    assert lap_mapping["status"] in {"blocked_on_lap_execution", "passed"}
    assert tuong_mapping["handoff_contract_passed"] is True
    assert tuong_mapping["duy_input_contract"]["primary_count"] == 20
    assert tuong_mapping["duy_input_contract"]["additional_count"] == 10
    assert tuong_mapping["canonical_identity"]["source_id_map"] == {
        "superstore_sales_csv": 1,
        "product_sales_region_excel": 2,
        "dummyjson_products_api": 3,
        "dataflow_technical_report_pdf": 4,
    }
    assert tuong_mapping["canonical_identity"]["document_db_id"] == 1
    assert tuong_mapping["canonical_identity"]["document_external_id"] == (
        "doc_dataflow_technical_report"
    )
    assert tuong_mapping["status"] in {"blocked_on_tuong_refresh", "passed"}
    assert (
        tuong_external_proof["tuong_output_contract_passed"]
        == tuong_mapping["tuong_output_contract_passed"]
    )
    assert (
        tuong_external_proof["database_insert_proof_passed"]
        == tuong_mapping["database_insert_proof_passed"]
    )
    if tuong_mapping["status"] == "passed":
        assert tuong_mapping["tuong_output_contract_passed"] is True
        assert tuong_mapping["prediction_ci_proof_passed"] is True
        assert tuong_mapping["database_insert_proof_passed"] is True
    else:
        assert tuong_mapping["blocking_findings"]
    assert hung_mapping["canonical_identity"]["source_id"] == 4
    assert hung_mapping["canonical_identity"]["document_db_id"] == 1
    assert (
        hung_mapping["canonical_identity"]["document_external_id"]
        == "doc_dataflow_technical_report"
    )
    assert hung_mapping["status"] in {
        "blocked_on_phi_hung_refresh",
        "ready_with_lineage_caveat",
        "passed",
    }
    assert hung_external_proof["gates"] == hung_mapping["gates"]
    if hung_mapping["status"] == "passed":
        assert hung_mapping["gates"]["fixture_contract_passed"] is True
        assert hung_mapping["gates"]["real_lineage_passed"] is True
        assert hung_mapping["gates"]["ui_code_docs_passed"] is True
        assert hung_mapping["gates"]["hung_unit_tests_passed"] is True
        assert hung_mapping["gates"]["ui_smoke_passed"] is True
    else:
        assert hung_mapping["blocking_findings"]
    assert smoke_plan["totals"]["structured_records"] == 100
    for member_section in ("Duy -> Phat", "Duy -> Lap", "Duy -> Tuong", "Duy -> Phi/Hung"):
        assert member_section in team_handoff
    assert set(manifest_json["owner_contracts"]) == {"Duy", "Phat", "Lap", "Tuong", "Phi/Hung"}
    assert "docker-compose.db.yml" in team_handoff
    assert "backend_stub/main.py" in team_handoff
    assert WINDOWS_ABSOLUTE_PATH.search(team_handoff) is None
    for owner_report in (lap_mapping, tuong_mapping, hung_mapping):
        assert all(
            WINDOWS_ABSOLUTE_PATH.search(value) is None
            for value in iter_string_values(owner_report)
        )

    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for dependency in ("pandas", "openpyxl", "pymupdf", "requests", "pytest", "psycopg2-binary", "python-dotenv"):
        assert dependency in requirements

    print("Week 7 validation passed")
    print(f"Checked {len(REQUIRED_FILES)} required Week 7 files")
    print("Checked smoke DB plan: 4 sources, 36 pages, 100 structured records")
    print("Checked Duy's current-run Docker DB load and Phat schema_v4 ID mapping")
    print("Checked Duy-to-Lap, Duy-to-Tuong and Duy-to-Phi/Hung mapping audits, plus shared Docker/CI drafts")
    if not lap_mapping["live_pgvector_proof_passed"]:
        print("Note: Lap handoff contract passes, but live chunk insert/retrieval proof is still pending in the Lap repository")
    if not tuong_mapping["tuong_output_contract_passed"]:
        print("Note: Tuong handoff contract passes, but the current results/log/UI fixtures do not cover Duy's 20-payload batch")
    if hung_mapping["status"] != "passed":
        print("Note: one or more Phi/Hung execution or fixture-lineage gates remain pending; see the generated mapping summary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
