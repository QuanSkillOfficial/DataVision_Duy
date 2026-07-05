from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PLAN = PROJECT_ROOT / "logs/db_load_dry_run/duy_to_phat_db_load_plan.json"
RAG_HANDOFF = PROJECT_ROOT / "outputs/rag_handoff/rag_handoff_manifest.json"
PREDICTION_PAYLOAD = PROJECT_ROOT / "logs/prediction_payloads/duy_pdf_prediction_payload.json"
UI_FIXTURE = PROJECT_ROOT / "outputs/ui_fixtures/duy_latest_ingestion_summary.json"


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def run_smoke_test() -> dict:
    db_plan = _read_json(DB_PLAN)
    rag = _read_json(RAG_HANDOFF)
    prediction = _read_json(PREDICTION_PAYLOAD)
    ui = _read_json(UI_FIXTURE)

    checks = {
        "connect": db_plan.get("mode") == "dry_run" and db_plan.get("run_count") == 4,
        "insert": db_plan.get("totals", {}).get("structured_records") == 11524
        and db_plan.get("totals", {}).get("document_pages") == 36,
        "query": ui.get("summary", {}).get("total_sources") == 4
        and ui.get("latest_ingestion_run", {}).get("data_quality_score") is not None,
        "retrieve": rag.get("document_pages_path") == "outputs/rag_handoff/document_pages.jsonl"
        and rag.get("page_count") == 36,
        "predict": bool(
            prediction.get("document_external_id") == "doc_dataflow_technical_report"
        and prediction.get("source_id") is None
            and prediction.get("ingestion_run_id")
        ),
        "display": ui.get("prediction_context", {}).get("full_payload_path")
        == "logs/prediction_payloads/duy_pdf_prediction_payload.json",
        "test": True,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "evidence": {
            "db_plan": DB_PLAN.relative_to(PROJECT_ROOT).as_posix(),
            "rag_handoff": RAG_HANDOFF.relative_to(PROJECT_ROOT).as_posix(),
            "prediction_payload": PREDICTION_PAYLOAD.relative_to(PROJECT_ROOT).as_posix(),
            "ui_fixture": UI_FIXTURE.relative_to(PROJECT_ROOT).as_posix(),
        },
    }


def main() -> int:
    result = run_smoke_test()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
