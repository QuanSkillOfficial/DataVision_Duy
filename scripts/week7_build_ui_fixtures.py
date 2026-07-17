from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.pipelines.handoff_context import (
    build_database_enriched_ui_summary,
    load_database_identity_map,
    load_latest_successful_runs,
)


OUTPUT_PATH = PROJECT_ROOT / "outputs/ui_fixtures/duy_week7_database_enriched_summary.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phi/Hung's DB-enriched Week 7 ingestion fixture")
    parser.add_argument("--db-load-result", default="logs/db_load_results/duy_to_phat_db_load_result.json")
    args = parser.parse_args()
    identity = load_database_identity_map(args.db_load_result)
    fixture = build_database_enriched_ui_summary(load_latest_successful_runs(), identity)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(fixture, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Database identity status: {identity['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
