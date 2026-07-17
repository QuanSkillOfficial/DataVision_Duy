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
        "week7/database/schema_v4_fixed.sql",
        "week7/database/setup_database_v3.sql",
        "week7/database/validation_queries_v3.sql",
        "week7/database/ci_database_smoke_test.py",
        "week7/outputs/dashboard_view_samples",
    ),
    "Lap": (
        "ai/rag/load_document_pages_to_pgvector.py",
        "ai/rag/scripts/week7_pgvector_smoke_test.py",
        "ai/rag/scripts/week7_rag_ci_smoke_test.py",
        "ai/ai_tests",
    ),
    "Tuong": (
        "ai/prediction/prediction_service.py",
        "ai/prediction/prediction_log_payload_builder.py",
        "scripts/week7_prediction_ci_smoke_test.py",
        "outputs/db_integration/week7_prediction_log_payloads.json",
    ),
    "Phi/Hung": (
        "demo/streamlit_app.py",
        "demo/services/service_client.py",
        "demo/services/backend_client.py",
        "scripts/week7_ui_ci_smoke_test.py",
        "demo/fixtures/week7",
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
    missing_owner_count = sum(1 for value in owners.values() if value["missing"])
    return {
        "status": "ready" if missing_owner_count == 0 else "partial",
        "scope": "Week 7 shared-repository readiness, not proof of runtime integration",
        "owners": owners,
        "next_action": (
            "Merge owner artifacts into the shared repository, then rerun this report with --strict."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Week 7 shared-repository readiness")
    parser.add_argument("--strict", action="store_true", help="Fail while any owner artifact is missing")
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
    if args.strict:
        return 0 if report["status"] == "ready" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
