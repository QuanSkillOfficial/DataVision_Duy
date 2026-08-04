"""Run Week 8 acceptance against cloud staging and verify its release identity."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from week8_staging_smoke_test import run_acceptance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-url", required=True)
    parser.add_argument("--ui-url", required=True)
    parser.add_argument("--expected-release-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    expected_sha = args.expected_release_sha.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise ValueError("expected release SHA must contain exactly 40 hexadecimal characters")

    result = run_acceptance(
        args.backend_url.rstrip("/"),
        args.ui_url.rstrip("/"),
        ui_backend_mode=True,
    )
    actual_sha = str(result.get("evidence", {}).get("health", {}).get("data", {}).get("release_sha", ""))
    release_matches = actual_sha == expected_sha
    # Preserve the agreed 15-check contract by strengthening its health check.
    result["checks"]["backend_healthy"] = result["checks"]["backend_healthy"] and release_matches
    result["status"] = "passed" if all(result["checks"].values()) else "failed"
    result["evidence"]["release"] = {
        "expected_sha": expected_sha,
        "actual_sha": actual_sha,
        "matches": release_matches,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": result["checks"], "output": str(output)}, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
