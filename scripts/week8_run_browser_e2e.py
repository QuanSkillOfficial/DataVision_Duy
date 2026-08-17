"""
Week 8 browser E2E runner (DV-HUNG-02, DV-HUNG-03, DV-HUNG-06).

Runs the Playwright user-journey and error-handling suites, then writes one
evidence file that ties the result to a release identity. This is the command
that produces the artifacts the release review asks for:

    screenshots/week8_browser_e2e/*.png
    outputs/week8/hung_browser_e2e.json
    outputs/week8/hung_browser_e2e_junit.xml

Local run against the bundled stack:
    python scripts/week8_run_browser_e2e.py

Private staging run (DV-HUNG-06), against a deployed UI:
    # Only if the UI sits behind basic auth. Never pass a password in argv.
    export QS_E2E_HTTP_USER=reviewer
    export QS_E2E_HTTP_PASSWORD=...

    python scripts/week8_run_browser_e2e.py \
        --base-url https://staging.example.internal \
        --release-sha <exact release sha>

In that mode only the staging-capable tests run; STAGING_EXCLUSIONS below records
what was left out and why, and that record is written into the evidence file.

Exit code 0 means the browser journey passed and the evidence is releasable.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.e2e.harness import e2e_release_sha  # noqa: E402

EVIDENCE_DIR = ROOT / "outputs" / "week8"
EVIDENCE_PATH = EVIDENCE_DIR / "hung_browser_e2e.json"
JUNIT_PATH = EVIDENCE_DIR / "hung_browser_e2e_junit.xml"
SCREENSHOT_DIR = ROOT / "screenshots" / "week8_browser_e2e"
CAPTURE_MANIFEST = EVIDENCE_DIR / "e2e_captured.txt"

# Tests that cannot describe a deployed environment, and why. They are declared
# here rather than skipped silently: the Week 8 rule is that a release gate must
# never hide a test it did not run, so the reason travels with the evidence.
STAGING_EXCLUSIONS = {
    "tests/e2e/test_error_handling.py::test_unavailable_backend_is_reported_not_hidden": (
        "needs a UI pointed at a dead backend, which only a local stack can provide"
    ),
    "tests/e2e/test_error_handling.py::test_error_message_tells_the_user_what_to_do": (
        "needs a UI pointed at a dead backend, which only a local stack can provide"
    ),
    "tests/e2e/test_error_handling.py::test_prediction_failure_does_not_leave_a_stale_result": (
        "injects a fault through the stub control route, which a real backend "
        "does not and must not expose"
    ),
}

# Steps the release gate requires the browser to have exercised.
REQUIRED_JOURNEY_STEPS = [
    "00_home_release_identity",
    "01_upload_dataset_analysis",
    "02_dashboard_live_metrics",
    "03_prediction_and_review_status",
    "04_rag_answer_with_citations",
    "05_suggestions_with_evidence",
    "06_report_with_evidence_table",
]


def _run_suite(
    base_url: str | None, release_sha: str | None, marker: str
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["QS_E2E_CAPTURE_MANIFEST"] = str(CAPTURE_MANIFEST)
    if base_url:
        env["QS_E2E_BASE_URL"] = base_url
    if release_sha:
        env["QS_RELEASE_SHA"] = release_sha

    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/e2e",
        # Overrides the default "not e2e" filter in pytest.ini.
        "-m",
        marker,
        "-q",
        f"--junitxml={JUNIT_PATH}",
    ]
    print(f"$ {' '.join(command)}")
    return subprocess.run(command, env=env, cwd=str(ROOT), text=True)


def _parse_junit(path: Path) -> dict:
    root = ET.parse(path).getroot()
    suites = root.findall("testsuite") or [root]
    totals = {"tests": 0, "failures": 0, "skipped": 0}
    cases = []
    for suite in suites:
        for case in suite.findall("testcase"):
            failed = case.find("failure") is not None or case.find("error") is not None
            skipped = case.find("skipped") is not None
            totals["tests"] += 1
            totals["failures"] += int(failed)
            totals["skipped"] += int(skipped)
            cases.append(
                {
                    "name": f"{case.get('classname', '')}::{case.get('name', '')}",
                    "outcome": "failed" if failed else "skipped" if skipped else "passed",
                    "time_seconds": float(case.get("time", 0.0)),
                }
            )
    return {"totals": totals, "cases": cases}


def _reset_capture_manifest() -> None:
    CAPTURE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    CAPTURE_MANIFEST.write_text("", encoding="utf-8")


def _captured_steps() -> set[str]:
    if not CAPTURE_MANIFEST.exists():
        return set()
    return {
        line.strip()
        for line in CAPTURE_MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Week 8 browser E2E runner")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Run against an already-deployed UI instead of a local stack.",
    )
    parser.add_argument(
        "--release-sha",
        default=None,
        help="Exact release SHA this evidence belongs to.",
    )
    args = parser.parse_args()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()
    _reset_capture_manifest()

    # Against a deployed UI only the staging-capable set can run; the rest need
    # a stack this process controls.
    marker = "e2e and staging" if args.base_url else "e2e"
    result = _run_suite(args.base_url, args.release_sha, marker)
    report = _parse_junit(JUNIT_PATH) if JUNIT_PATH.exists() else {
        "totals": {"tests": 0, "failures": 0, "skipped": 0},
        "cases": [],
    }

    captured = _captured_steps()
    present = {path.name for path in SCREENSHOT_DIR.glob("*.png")}
    screenshots = sorted(
        f"{step}.png" for step in captured if f"{step}.png" in present
    )
    stale_screenshots = sorted(present - set(screenshots))
    missing_steps = [step for step in REQUIRED_JOURNEY_STEPS if step not in captured]

    failures: list[str] = []
    if report["totals"]["failures"]:
        failures.append(f"{report['totals']['failures']} browser test(s) failed")
    if report["totals"]["skipped"]:
        failures.append(f"{report['totals']['skipped']} browser test(s) were skipped")
    if not report["totals"]["tests"]:
        failures.append("No browser tests were collected")
    if missing_steps:
        failures.append("Missing journey evidence for: " + ", ".join(missing_steps))
    if result.returncode != 0 and not failures:
        failures.append(f"pytest exited with code {result.returncode}")

    evidence = {
        "task": "DV-HUNG-02/DV-HUNG-03",
        "gate": "browser_user_journey",
        "passed": not failures,
        "failures": failures,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "target": {
            "mode": "external" if args.base_url else "local_stack",
            "base_url": args.base_url,
            "http_auth": bool(os.environ.get("QS_E2E_HTTP_USER")),
        },
        "selection": {
            "marker": marker,
            # Declared, not skipped: a reviewer can see exactly what this run
            # did not cover and why, instead of inferring it from a test count.
            "excluded": STAGING_EXCLUSIONS if args.base_url else {},
        },
        # Never null: an unlabelled run records the same "local" identity the
        # UI displayed, so evidence and screenshots cannot disagree.
        "release_sha": args.release_sha or e2e_release_sha(),
        "environment": os.environ.get("QS_ENVIRONMENT", "e2e"),
        "journey": REQUIRED_JOURNEY_STEPS,
        "results": report,
        "screenshots": screenshots,
        "stale_screenshots": stale_screenshots,
        "screenshot_dir": "screenshots/week8_browser_e2e",
        "junit_report": str(JUNIT_PATH.relative_to(ROOT)).replace("\\", "/"),
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Evidence written to {EVIDENCE_PATH.relative_to(ROOT)}")

    if failures:
        print("\nBROWSER E2E GATE FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        f"\nBROWSER E2E GATE PASSED: {report['totals']['tests']} tests, "
        f"{len(screenshots)} screenshots captured."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
