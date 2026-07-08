"""Build a Week 6 Duy-to-Tuong prediction handoff summary."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TUONG_ROOT = PROJECT_ROOT.parent / "DataVision_Tuong"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def payload_summary(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    source_counts = Counter(payload.get("source_name") for payload in payloads)
    cases = []
    for payload in payloads:
        cases.append(
            {
                "document_external_id": payload.get("document_external_id") or payload.get("document_id"),
                "source_name": payload.get("source_name"),
                "file_name_present": bool(payload.get("file_name")),
                "file_type": payload.get("file_type"),
                "text_length": payload.get("text_length"),
                "num_pages": payload.get("num_pages"),
                "source_id": payload.get("source_id"),
                "document_db_id": payload.get("document_db_id"),
                "ingestion_run_id": payload.get("ingestion_run_id"),
                "test_case": payload.get("test_case"),
                "expected_status_hint": payload.get("expected_status_hint"),
            }
        )
    return {
        "total_payloads": len(payloads),
        "source_counts": dict(source_counts),
        "cases": cases,
    }


def result_summary(results_doc: dict[str, Any]) -> dict[str, Any]:
    results = results_doc.get("results", []) if isinstance(results_doc, dict) else []
    status_counts = Counter(result.get("status") for result in results)
    cases = []
    for result in results:
        cases.append(
            {
                "document_external_id": result.get("document_external_id"),
                "source_name": result.get("source_name"),
                "predicted_document_type": result.get("predicted_document_type"),
                "confidence": result.get("confidence"),
                "status": result.get("status"),
                "review_reason": result.get("review_reason"),
                "top_prediction": (result.get("top_predictions") or [{}])[0],
            }
        )
    return {
        "evaluation_timestamp": results_doc.get("evaluation_timestamp"),
        "total_payloads": results_doc.get("total_payloads", len(results)),
        "status_summary": dict(status_counts),
        "cases": cases,
        "prediction_log_payload_count": len(results_doc.get("prediction_log_payloads", [])),
    }


def read_file_status(path: Path) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "exists": path.exists(),
    }


def ui_fixture_summary(path: Path) -> dict[str, Any]:
    fixture = read_json(path, {})
    if not fixture:
        return {"path": path.as_posix(), "exists": False}

    if isinstance(fixture, dict):
        results = fixture.get("results") or fixture.get("review_items") or []
        return {
            "path": path.as_posix(),
            "exists": True,
            "description": fixture.get("description"),
            "total_items": fixture.get("total_items", len(results)),
            "item_count": len(results),
            "status_counts": dict(Counter(item.get("status") for item in results)),
            "appears_sample_fixture": fixture.get("total_items", len(results)) != 10,
        }
    return {"path": path.as_posix(), "exists": True, "item_count": len(fixture)}


def main() -> None:
    payloads = read_json(PROJECT_ROOT / "outputs" / "prediction_payloads" / "tuong_week6_prediction_payloads.json", [])
    tuong_results = read_json(TUONG_ROOT / "outputs" / "week6_duy_prediction_results.json", {})
    tuong_rag_filter = read_json(TUONG_ROOT / "outputs" / "rag_metadata" / "document_type_filter_payload.json", [])
    phat_summary = read_json(PROJECT_ROOT / "outputs" / "phat_handoff" / "phat_week6_mapping_summary.json", {})
    week6_eval_doc = TUONG_ROOT / "docs" / "week6_real_data_prediction_eval.md"
    db_result_doc = TUONG_ROOT / "docs" / "week6_prediction_db_integration_result.md"
    ingestion_contract = TUONG_ROOT / "docs" / "ingestion_to_prediction_contract.md"
    prediction_log_contract = TUONG_ROOT / "docs" / "prediction_log_contract.md"
    ui_real = TUONG_ROOT / "outputs" / "ui_fixtures" / "tuong_prediction_response_real.json"
    ui_batch = TUONG_ROOT / "outputs" / "ui_fixtures" / "tuong_prediction_batch_response.json"
    ui_review = TUONG_ROOT / "outputs" / "ui_fixtures" / "tuong_prediction_review_queue_sample.json"
    rag_filter_path = TUONG_ROOT / "outputs" / "rag_metadata" / "document_type_filter_payload.json"

    summary = {
        "handoff_owner": "Nguyen Minh Duy",
        "consumer": "Tuong - Prediction Engine Owner",
        "purpose": "Map Duy ingestion outputs to Tuong document type prediction inputs, outputs, DB logs, RAG metadata, and UI review states.",
        "duy_outputs_for_tuong": {
            "batch_payload": "outputs/prediction_payloads/tuong_week6_prediction_payloads.json",
            "batch_payload_copy": "logs/prediction_payloads/tuong_week6_prediction_payloads.json",
            "single_pdf_payload": "logs/prediction_payloads/duy_pdf_prediction_payload.json",
            "individual_payload_dir": "outputs/prediction_payloads/",
        },
        "tuong_repo_files_reviewed": {
            "week6_real_data_prediction_eval": read_file_status(week6_eval_doc),
            "week6_prediction_db_integration_result": read_file_status(db_result_doc),
            "ingestion_to_prediction_contract": read_file_status(ingestion_contract),
            "prediction_log_contract": read_file_status(prediction_log_contract),
            "week6_prediction_results": read_file_status(TUONG_ROOT / "outputs" / "week6_duy_prediction_results.json"),
            "ui_single_response_fixture": ui_fixture_summary(ui_real),
            "ui_batch_response_fixture": ui_fixture_summary(ui_batch),
            "ui_review_queue_fixture": ui_fixture_summary(ui_review),
            "rag_filter_payload": {
                "path": rag_filter_path.as_posix(),
                "exists": rag_filter_path.exists(),
                "item_count": len(tuong_rag_filter) if isinstance(tuong_rag_filter, list) else 0,
            },
        },
        "required_input_fields": [
            "file_name",
            "file_type",
            "file_size",
            "text_length",
            "num_pages",
            "source_system",
            "extracted_text",
            "document_external_id",
            "source_name",
            "ingestion_run_id",
            "source_id",
            "document_db_id",
        ],
        "id_semantics": {
            "source_id": "Phat sources.id; null before DB insert",
            "source_name": "Duy source slug from ingestion config",
            "document_external_id": "Duy stable document key",
            "document_db_id": "Phat documents.id; null before DB insert",
            "ingestion_run_id": "Duy run UUID; never use as source_id",
        },
        "current_phat_ids_if_available": {
            "source_id_map": phat_summary.get("source_id_map", {}),
            "document_id_map": phat_summary.get("document_id_map", {}),
        },
        "duy_payload_summary": payload_summary(payloads),
        "tuong_result_summary": result_summary(tuong_results),
        "real_data_quality_findings_from_tuong": {
            "source_of_truth_file": "DataVision_Tuong/outputs/week6_duy_prediction_results.json",
            "evaluation_doc": "DataVision_Tuong/docs/week6_real_data_prediction_eval.md",
            "strict_top1_correct": "1/7 predictable documents (~14%) according to Tuong report",
            "false_positive_accepted_count": 4,
            "accepted_predictions_are_not_safe_hard_filters": True,
            "full_dataflow_result": next(
                (
                    result
                    for result in tuong_results.get("results", [])
                    if result.get("document_external_id") == "doc_dataflow_technical_report"
                ),
                {},
            ),
        },
        "tuong_status_rules": {
            "accepted": "confidence >= 0.60",
            "needs_review": "confidence < 0.60",
            "waiting_for_source": "extracted_text length < 50",
            "failed": "validation error or prediction exception",
        },
        "rag_filtering_rule": {
            "hard_filter_allowed_only_when": "status == accepted and use_for_rag_filtering == true",
            "current_real_data_warning": "Tuong Week 6 evaluation reports overconfident mistakes on real data; do not use low-confidence or unreviewed predictions as hard RAG filters.",
            "tuong_rag_filter_payload_count": len(tuong_rag_filter) if isinstance(tuong_rag_filter, list) else 0,
        },
        "phat_prediction_log_integration_if_available": {
            "prediction_logs_inserted": phat_summary.get("counts", {}).get("prediction_logs"),
            "status_counts": phat_summary.get("prediction_log_status_counts", {}),
            "source_id_map": phat_summary.get("source_id_map", {}),
            "document_id_map": phat_summary.get("document_id_map", {}),
            "note": "Phat output reports 10 prediction_logs inserted. Only doc_dataflow_technical_report maps to documents.id=1; synthetic section/test payloads may keep document_id null.",
        },
        "alignment_notes": [
            "Use Tuong outputs/week6_duy_prediction_results.json as the source of truth for the 10 Duy payloads.",
            "Tuong UI fixtures are useful for Phi/Hung demo states but may be sample fixtures with 5 items, not the full 10 Duy payloads.",
            "Some Tuong docs still include older 4-payload Week 5 examples; Week 6 mapping should use the 10-payload evaluation.",
            "Duy payload source_id and document_db_id are null before DB enrichment; Phat confirmed source_id=2 and document_db_id=1 for the DataFlow PDF.",
            "Low-confidence or unreviewed predictions should not become hard RAG filters. Tuong's evaluation shows overconfident accepted false positives.",
        ],
        "what_tuong_should_return_to_duy": [
            "Prediction response for each Duy payload",
            "Batch response with accepted/needs_review/waiting_for_source/failed counts",
            "Prediction log payloads for Phat prediction_logs",
            "UI fixtures for Phi/Hung review queue",
            "RAG metadata filter payload for Lap",
            "Any required Duy payload field changes",
        ],
    }

    output_dir = PROJECT_ROOT / "outputs" / "tuong_handoff"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "tuong_week6_mapping_summary.json"
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote Tuong handoff mapping summary: {output_path}")


if __name__ == "__main__":
    main()
