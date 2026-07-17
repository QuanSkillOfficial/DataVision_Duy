from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.pipelines.handoff_context import load_database_identity_map
from data_engineering.pipelines.prediction_payload_builder import (
    build_tuong_extended_prediction_test_payloads,
)


OUTPUT_PATH = PROJECT_ROOT / "outputs/prediction_payloads/tuong_week7_prediction_payloads.json"
ADDITIONAL_OUTPUT_PATH = (
    PROJECT_ROOT / "outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json"
)
INDIVIDUAL_DIR = PROJECT_ROOT / "outputs/prediction_payloads/week7"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Tuong's DB-enriched Week 7 prediction payloads")
    parser.add_argument("--db-load-result", default="logs/db_load_results/duy_to_phat_db_load_result.json")
    args = parser.parse_args()
    identity = load_database_identity_map(args.db_load_result)
    payloads = build_tuong_extended_prediction_test_payloads(identity)
    additional_payloads = payloads[10:]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payloads, indent=2, ensure_ascii=False), encoding="utf-8")
    ADDITIONAL_OUTPUT_PATH.write_text(
        json.dumps(additional_payloads, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    INDIVIDUAL_DIR.mkdir(parents=True, exist_ok=True)
    for index, payload in enumerate(payloads, start=1):
        payload_name = (
            payload.get("document_external_id")
            or payload.get("test_case")
            or f"prediction_case_{index:02d}"
        )
        path = INDIVIDUAL_DIR / f"{index:02d}_{payload_name}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {len(payloads)} payloads to {OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(
        f"Wrote {len(additional_payloads)} new payloads to "
        f"{ADDITIONAL_OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}"
    )
    print(f"Database identity status: {identity['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
