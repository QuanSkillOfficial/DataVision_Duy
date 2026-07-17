from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.load_ingestion_outputs_to_postgres import run_dry_run


REQUIRED_OUTPUTS = {
    "rag_handoff": PROJECT_ROOT / "outputs/rag_handoff/week7_document_pages_db_enriched.jsonl",
    "rag_manifest": PROJECT_ROOT / "outputs/rag_handoff/week7_rag_handoff_manifest.json",
    "prediction_payloads": PROJECT_ROOT / "outputs/prediction_payloads/tuong_week7_prediction_payloads.json",
    "ui_fixture": PROJECT_ROOT / "outputs/ui_fixtures/duy_week7_database_enriched_summary.json",
}


def run_smoke_test() -> dict:
    plan = run_dry_run(structured_record_limit=100)
    checks = {
        "outputs_exist": all(path.exists() for path in REQUIRED_OUTPUTS.values()),
        "db_smoke_plan": plan["totals"] == {
            "sources": 4,
            "pipeline_runs": 4,
            "ingestion_logs": 4,
            "structured_records": 100,
            "documents": 1,
            "document_pages": 36,
        },
    }
    if checks["outputs_exist"]:
        rag_manifest = json.loads(REQUIRED_OUTPUTS["rag_manifest"].read_text(encoding="utf-8"))
        predictions = json.loads(REQUIRED_OUTPUTS["prediction_payloads"].read_text(encoding="utf-8"))
        ui_fixture = json.loads(REQUIRED_OUTPUTS["ui_fixture"].read_text(encoding="utf-8"))
        checks.update(
            {
                "rag_contract": rag_manifest.get("page_count") == 36,
                "prediction_contract": len(predictions) == 20,
                "ui_contract": ui_fixture.get("total_sources") == 4,
            }
        )
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "db_smoke_counts": plan["totals"],
        "outputs": {name: path.relative_to(PROJECT_ROOT).as_posix() for name, path in REQUIRED_OUTPUTS.items()},
    }


def main() -> int:
    result = run_smoke_test()
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
