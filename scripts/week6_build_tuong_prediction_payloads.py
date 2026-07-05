from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.pipelines.prediction_payload_builder import build_tuong_prediction_test_payloads


OUTPUT_DIR = PROJECT_ROOT / "outputs/prediction_payloads"
LOG_OUTPUT_DIR = PROJECT_ROOT / "logs/prediction_payloads"
BATCH_FILE_NAME = "tuong_week6_prediction_payloads.json"
SUMMARY_FILE = PROJECT_ROOT / "docs/week6_tuong_prediction_payloads.md"


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_summary(payloads: list[dict]) -> None:
    rows = [
        "# Week 6 Tuong Prediction Payloads",
        "",
        "Owner: Nguyen Minh Duy  ",
        "Consumer: Tuong - Prediction Engine Owner",
        "",
        "## Purpose",
        "",
        "These 10 payloads are Duy-style ingestion outputs for Tuong to test single and batch document classification.",
        "",
        "Main batch file:",
        "",
        "```text",
        "outputs/prediction_payloads/tuong_week6_prediction_payloads.json",
        "logs/prediction_payloads/tuong_week6_prediction_payloads.json",
        "```",
        "",
        "## Payload Inventory",
        "",
        "| # | document_external_id | source_name | file_type | text_length | test_case | expected_status_hint |",
        "| ---: | --- | --- | --- | ---: | --- | --- |",
    ]
    for index, payload in enumerate(payloads, start=1):
        rows.append(
            "| {index} | `{document_external_id}` | `{source_name}` | `{file_type}` | {text_length} | `{test_case}` | `{expected}` |".format(
                index=index,
                document_external_id=payload.get("document_external_id"),
                source_name=payload.get("source_name"),
                file_type=payload.get("file_type"),
                text_length=payload.get("text_length"),
                test_case=payload.get("test_case"),
                expected=payload.get("expected_status_hint"),
            )
        )
    rows.extend(
        [
            "",
            "## ID Rules",
            "",
            "```text",
            "source_id is null before Phat DB insert.",
            "document_db_id is null before Phat DB insert.",
            "ingestion_run_id is Duy's run UUID.",
            "document_external_id is the stable document key.",
            "```",
            "",
            "## Test Coverage",
            "",
            "- Full DataFlow PDF payload",
            "- PDF section-level payloads",
            "- CSV / Excel / API structured source summaries",
            "- Short extracted text quality gate",
            "- Empty extracted text quality gate",
            "- Missing required field validation case",
            "",
            "Tuong should use these to test:",
            "",
            "```text",
            "accepted",
            "needs_review",
            "waiting_for_source",
            "failed",
            "batch validation error normalization",
            "```",
        ]
    )
    SUMMARY_FILE.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    payloads = build_tuong_prediction_test_payloads()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    _write_json(OUTPUT_DIR / BATCH_FILE_NAME, payloads)
    _write_json(LOG_OUTPUT_DIR / BATCH_FILE_NAME, payloads)

    for index, payload in enumerate(payloads, start=1):
        document_id = payload.get("document_external_id") or f"payload_{index:02d}"
        file_name = f"{index:02d}_{document_id}.json"
        _write_json(OUTPUT_DIR / file_name, payload)

    _write_summary(payloads)

    print(f"Wrote batch payloads: {(OUTPUT_DIR / BATCH_FILE_NAME).relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Wrote log copy: {(LOG_OUTPUT_DIR / BATCH_FILE_NAME).relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Wrote individual payloads: {len(payloads)}")
    print(f"Wrote summary: {SUMMARY_FILE.relative_to(PROJECT_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
