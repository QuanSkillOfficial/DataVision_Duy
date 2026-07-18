from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]


OWNER_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "Duy": (
        "data_engineering/ingestion/csv_ingestor.py",
        "data_engineering/pipelines/ingestion_engine.py",
        "data_engineering/storage/postgres_writer.py",
        "scripts/week7_ci_ingestion_smoke_test.py",
        "tests/data_tests",
    ),
    "Phat": (
        "week7/database/schema/schema_v4_fixed.sql",
        "week7/database/schema/setup_database_v3.sql",
        "week7/database/validation/validation_queries_v3.sql",
        "week7/database/scripts/run_database_setup.py",
        "week7/database/scripts/ci_database_smoke_test.py",
        "week7/database/outputs/dashboard_view_samples",
    ),
    "Lap": (
        "ai/rag/vector_store.py",
        "ai/rag/rag_service.py",
        "ai/rag/load_document_pages_to_pgvector.py",
        "ai/rag/scripts/week7_pgvector_smoke_test.py",
        "ai/rag/scripts/week7_rag_ci_smoke_test.py",
        "ai/ai_tests",
        "outputs/rag/week7_chunk_insert_summary.json",
        "outputs/rag/week7_pgvector_query_result.json",
        "outputs/ui_fixtures/lap_rag_response_real.json",
    ),
    "Tuong": (
        "ai/prediction/config.py",
        "ai/prediction/prediction_service.py",
        "ai/prediction/prediction_log_payload_builder.py",
        "scripts/week7_prediction_ci_smoke_test.py",
        "outputs/week7_duy_prediction_results.json",
        "outputs/db_integration/week7_prediction_log_payloads.json",
        "outputs/rag_metadata/document_type_filter_payload.json",
        "outputs/ui_fixtures/tuong_prediction_batch_response.json",
        "outputs/ui_fixtures/tuong_prediction_review_queue_sample.json",
    ),
    "Phi/Hung": (
        "demo/streamlit_app.py",
        "demo/config.py",
        "demo/services/service_client.py",
        "demo/services/mock_client.py",
        "demo/services/fixture_validator.py",
        "demo/services/backend_client.py",
        "demo/views/dashboard_page.py",
        "demo/views/prediction_page.py",
        "demo/views/chatbot_page.py",
        "demo/views/suggestions_page.py",
        "demo/views/reports_page.py",
        "demo/views/upload_page.py",
        "scripts/week7_refresh_fixtures.py",
        "scripts/week7_ui_ci_smoke_test.py",
        "tests/test_week7_fixture_validation.py",
        "tests/test_backend_contract_smoke.py",
        "tests/test_backend_client_error_handling.py",
        "docs/ui_contracts/prediction_ui_contract.md",
        "docs/ui_contracts/rag_ui_contract.md",
        "docs/ui_contracts/suggestion_ui_contract.md",
        "docs/ui_contracts/report_ui_contract.md",
        "docs/backend_api_contract_for_ui.md",
        "docs/week7_ui_runbook.md",
        "docs/week7_github_actions_ui_job.md",
        "docs/week7_backend_route_alignment_summary.md",
        "demo/fixtures/week7",
        "screenshots/week7_staging_ready_ui",
        "backend_stub/main.py",
        ".github/workflows/ci.yml",
    ),
}


def _repo_candidates() -> dict[str, Path]:
    configured = Path(os.getenv("TEAM_REPOS_ROOT", PROJECT_ROOT.parent))
    if not configured.is_absolute():
        configured = (PROJECT_ROOT / configured).resolve()
    return {
        "Duy": PROJECT_ROOT,
        "Phat": configured / "DataVision_Phat",
        "Lap": configured / "DataVision_Lap",
        "Tuong": configured / "DataVision_Tuong",
        "Phi/Hung": configured / "DataVision_Hung",
    }


def _find_existing(root: Path, candidates: Iterable[str]) -> list[str]:
    return [candidate for candidate in candidates if (root / candidate).exists()]


def build_report() -> dict:
    owners: dict[str, dict] = {}
    for owner, required in OWNER_REQUIREMENTS.items():
        root = _repo_candidates()[owner]
        present = _find_existing(root, required) if root.exists() else []
        missing = [item for item in required if item not in present]
        owners[owner] = {
            "repository_present": root.exists(),
            "repository_label": owner,
            "present": present,
            "missing": missing,
            "status": "ready" if not missing else "pending_owner_delivery",
        }
        if owner == "Lap":
            audit_path = PROJECT_ROOT / "outputs/lap_handoff/lap_week7_mapping_summary.json"
            if audit_path.exists():
                audit = json.loads(audit_path.read_text(encoding="utf-8"))
                owners[owner]["execution_audit"] = {
                    "status": audit.get("status"),
                    "handoff_contract_passed": audit.get("handoff_contract_passed"),
                    "live_pgvector_proof_passed": audit.get("live_pgvector_proof_passed"),
                    "blocking_findings": len(audit.get("blocking_findings", [])),
                }
        if owner == "Tuong":
            audit_path = (
                PROJECT_ROOT
                / "outputs/tuong_handoff/tuong_week7_mapping_summary.json"
            )
            if audit_path.exists():
                audit = json.loads(audit_path.read_text(encoding="utf-8"))
                owners[owner]["execution_audit"] = {
                    "status": audit.get("status"),
                    "handoff_contract_passed": audit.get(
                        "handoff_contract_passed"
                    ),
                    "tuong_output_contract_passed": audit.get(
                        "tuong_output_contract_passed"
                    ),
                    "prediction_ci_proof_passed": audit.get(
                        "prediction_ci_proof_passed"
                    ),
                    "database_insert_proof_passed": audit.get(
                        "database_insert_proof_passed"
                    ),
                    "blocking_findings": len(
                        audit.get("blocking_findings", [])
                    ),
                }
        if owner == "Phi/Hung":
            audit_path = (
                PROJECT_ROOT
                / "outputs/hung_handoff/hung_week7_mapping_summary.json"
            )
            proof_path = (
                PROJECT_ROOT
                / "logs/hung_handoff/hung_week7_external_proof.json"
            )
            if audit_path.exists():
                audit = json.loads(audit_path.read_text(encoding="utf-8"))
                proof = (
                    json.loads(proof_path.read_text(encoding="utf-8"))
                    if proof_path.exists()
                    else {}
                )
                gates = audit.get("gates", {})
                proof_gates = proof.get("gates", {})
                owners[owner]["execution_audit"] = {
                    "status": audit.get("status"),
                    "fixture_contract_passed": gates.get(
                        "fixture_contract_passed"
                    ),
                    "duy_fixture_lineage_passed": gates.get(
                        "duy_fixture_lineage_passed"
                    ),
                    "phat_dashboard_contract_passed": gates.get(
                        "phat_dashboard_contract_passed"
                    ),
                    "lap_rag_fixture_passed": gates.get(
                        "lap_rag_fixture_passed"
                    ),
                    "tuong_fixture_contract_passed": gates.get(
                        "tuong_fixture_contract_passed"
                    ),
                    "ui_structure_passed": gates.get("ui_structure_passed"),
                    "ui_code_docs_passed": gates.get("ui_code_docs_passed"),
                    "real_lineage_passed": gates.get("real_lineage_passed"),
                    "hung_unit_tests_passed": gates.get(
                        "hung_unit_tests_passed"
                    ),
                    "ui_smoke_passed": gates.get("ui_smoke_passed"),
                    "blocking_findings": len(
                        audit.get("blocking_findings", [])
                    ),
                    "proof_gates_match": bool(proof_gates)
                    and proof_gates == gates,
                }
    missing_owner_count = sum(1 for value in owners.values() if value["missing"])
    execution_blockers = {
        owner: value["execution_audit"]
        for owner, value in owners.items()
        if value.get("execution_audit", {}).get("status") not in {None, "passed"}
    }
    return {
        "status": "ready" if missing_owner_count == 0 else "partial",
        "execution_status": "passed" if not execution_blockers else "blocked",
        "scope": "Week 7 shared-repository readiness, not proof of runtime integration",
        "owners": owners,
        "execution_blockers": execution_blockers,
        "next_action": (
            "Resolve owner execution blockers, then rerun with --strict --strict-execution."
            if execution_blockers
            else "Run the merged shared repository in CI and proceed to the Week 8 staging checklist."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Week 7 shared-repository readiness")
    parser.add_argument("--strict", action="store_true", help="Fail while any owner artifact is missing")
    parser.add_argument(
        "--strict-execution",
        action="store_true",
        help="Also fail when a recorded owner execution audit is blocked",
    )
    parser.add_argument(
        "--allow-missing-owner-modules",
        action="store_true",
        help="Document missing external owner artifacts without failing",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "outputs/integration/week7_shared_repo_readiness.json"),
    )
    args = parser.parse_args()
    report = build_report()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if args.strict and report["status"] != "ready":
        return 1
    if args.strict_execution and report["execution_blockers"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
