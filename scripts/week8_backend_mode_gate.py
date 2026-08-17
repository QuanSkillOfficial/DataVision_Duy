"""
Week 8 backend-mode release gate (DV-HUNG-01).

Acceptance criteria:
    No required UI-to-backend integration test is skipped in the release
    candidate workflow.

What this script does:
    1. Starts the backend contract service (the bundled stub by default, or an
       external backend with --backend-url).
    2. Waits for /health and records the release identity the backend reports.
    3. Runs the UI test suite with QS_USE_BACKEND=true and
       QS_REQUIRE_BACKEND_TESTS=true, producing a JUnit XML report.
    4. Fails when any test was skipped, when any test failed, or when the
       backend-mode contract module did not actually execute.
    5. Writes traceable evidence to outputs/week8/.

Run:
    python scripts/week8_backend_mode_gate.py
    python scripts/week8_backend_mode_gate.py --backend-url http://staging:8000/api

Exit code 0 means the gate passed and the evidence file is releasable.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = ROOT / "outputs" / "week8"
EVIDENCE_PATH = EVIDENCE_DIR / "hung_backend_mode_gate.json"
JUNIT_PATH = EVIDENCE_DIR / "hung_backend_mode_junit.xml"

# The module that carries the UI-to-backend contract. It must run, not skip.
REQUIRED_TEST_MODULE = "test_backend_contract_smoke"
MIN_REQUIRED_CONTRACT_TESTS = 15


# Top-level test modules that belong to another module. The UI gate reports on
# the UI-to-backend contract, so another owner's result must not be attributed
# to it. Nothing is hidden: these run in their owner's own CI job.
NON_UI_TEST_MODULES = {
    "test_render_staging_env.py",  # Duy - scripts/render_staging_env.py
}


def _ui_test_targets() -> list[str]:
    """The top-level test modules this gate is accountable for.

    Deliberately not the whole `tests/` tree. In the canonical repository that
    directory also holds other owners' suites (`tests/ai_tests`,
    `tests/data_tests`) and the browser suite, and a gate that fails because
    someone else's test failed would say nothing about the UI-to-backend
    contract. Globbing also keeps the browser suite out without depending on an
    --ignore flag, so the gate never needs the Playwright stack installed.
    """
    return sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in (ROOT / "tests").glob("test_*.py")
        if path.name not in NON_UI_TEST_MODULES
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(base_url: str, timeout: float = 30.0) -> dict:
    """Block until the backend answers /health, then return its payload."""
    deadline = time.time() + timeout
    last_error = "no attempt made"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last_error = str(exc)
            time.sleep(0.4)
    raise RuntimeError(f"Backend never became healthy at {base_url}: {last_error}")


def _start_stub(port: int) -> subprocess.Popen:
    # Resolved rather than hard-coded: in the canonical repository the contract
    # stub lives under tests/, because backend_stub/ there is the image deployed
    # to cloud staging and must not carry fault-injection routes.
    from tests.e2e.harness import contract_stub_path

    env = dict(os.environ)
    env["BACKEND_HOST"] = "127.0.0.1"
    env["BACKEND_PORT"] = str(port)
    return subprocess.Popen(
        [sys.executable, str(contract_stub_path())],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        cwd=str(ROOT),
    )


def _run_backend_mode_tests(backend_url: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["QS_USE_BACKEND"] = "true"
    env["QS_REQUIRE_BACKEND_TESTS"] = "true"
    env["QS_BACKEND_URL"] = backend_url

    targets = _ui_test_targets()
    command = [
        sys.executable,
        "-m",
        "pytest",
        *targets,
        "-q",
        "-rs",
        f"--junitxml={JUNIT_PATH}",
    ]
    print(f"$ QS_USE_BACKEND=true QS_REQUIRE_BACKEND_TESTS=true {' '.join(command)}")
    return subprocess.run(command, env=env, cwd=str(ROOT), text=True)


def _parse_junit(path: Path) -> dict:
    """Extract per-test outcomes so skips can be reported by name."""
    tree = ET.parse(path)
    root = tree.getroot()
    suites = root.findall("testsuite") or [root]

    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    skipped_tests: list[str] = []
    failed_tests: list[str] = []
    contract_tests_run = 0

    for suite in suites:
        for case in suite.findall("testcase"):
            totals["tests"] += 1
            name = f"{case.get('classname', '')}::{case.get('name', '')}"
            is_skipped = case.find("skipped") is not None
            is_failed = (
                case.find("failure") is not None or case.find("error") is not None
            )
            if is_skipped:
                totals["skipped"] += 1
                skipped_tests.append(name)
            if is_failed:
                totals["failures"] += 1
                failed_tests.append(name)
            if REQUIRED_TEST_MODULE in name and not is_skipped:
                contract_tests_run += 1

    return {
        "totals": totals,
        "skipped_tests": skipped_tests,
        "failed_tests": failed_tests,
        "contract_tests_run": contract_tests_run,
    }


def _write_evidence(payload: dict) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Evidence written to {EVIDENCE_PATH.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Week 8 backend-mode release gate")
    parser.add_argument(
        "--backend-url",
        default=None,
        help="Use an already-running backend instead of the bundled stub.",
    )
    args = parser.parse_args()

    stub = None
    if args.backend_url:
        backend_url = args.backend_url.rstrip("/")
        backend_source = "external"
    else:
        port = _free_port()
        backend_url = f"http://127.0.0.1:{port}/api"
        backend_source = "backend_stub"
        stub = _start_stub(port)

    started_at = datetime.now(timezone.utc).isoformat()
    failures: list[str] = []

    try:
        health = _wait_for_health(backend_url)
        health_data = health.get("data", {}) if isinstance(health, dict) else {}
        print(f"Backend healthy at {backend_url} ({health_data.get('service')})")

        result = _run_backend_mode_tests(backend_url)
        report = _parse_junit(JUNIT_PATH)
        totals = report["totals"]

        print(
            f"\nBackend-mode run: {totals['tests']} tests, "
            f"{totals['failures']} failed, {totals['skipped']} skipped"
        )

        if totals["failures"]:
            failures.append(
                f"{totals['failures']} test(s) failed: "
                + ", ".join(report["failed_tests"][:10])
            )
        if totals["skipped"]:
            failures.append(
                f"{totals['skipped']} test(s) were skipped in the release "
                "candidate workflow: " + ", ".join(report["skipped_tests"][:10])
            )
        if report["contract_tests_run"] < MIN_REQUIRED_CONTRACT_TESTS:
            failures.append(
                f"Only {report['contract_tests_run']} UI-to-backend contract "
                f"tests executed; at least {MIN_REQUIRED_CONTRACT_TESTS} are required."
            )
        if result.returncode != 0 and not failures:
            failures.append(f"pytest exited with code {result.returncode}")

        evidence = {
            "task": "DV-HUNG-01",
            "gate": "backend_mode_tests_mandatory",
            "passed": not failures,
            "failures": failures,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "backend": {
                "source": backend_source,
                "url": backend_url,
                "service": health_data.get("service"),
                "release_sha": health_data.get("release_sha") or None,
                "environment": health_data.get("environment"),
            },
            "ui_release_sha": os.environ.get("QS_RELEASE_SHA") or None,
            "environment": os.environ.get("QS_ENVIRONMENT", "local"),
            "command": (
                "QS_USE_BACKEND=true QS_REQUIRE_BACKEND_TESTS=true "
                "python -m pytest " + " ".join(_ui_test_targets())
            ),
            "results": report,
            "junit_report": str(JUNIT_PATH.relative_to(ROOT)).replace("\\", "/"),
        }
        _write_evidence(evidence)

    finally:
        if stub is not None:
            stub.terminate()
            try:
                stub.wait(timeout=10)
            except subprocess.TimeoutExpired:
                stub.kill()

    if failures:
        print("\nBACKEND-MODE GATE FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("\nBACKEND-MODE GATE PASSED: no required backend test was skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
