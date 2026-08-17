"""
Week 8 staging acceptance runner (DV-HUNG-06, DV-HUNG-07).

One command that produces the whole staging acceptance record: the access
control checks and the browser journey, in one evidence file bound to one
release SHA.

Before this script the four access-control checks were curl commands in a
runbook and the browser journey was a separate command, so the result had to be
transcribed by hand. The Week 8 review rejects exactly that: "manually edited
summaries without traceable source identity are not sufficient."

Run (from a machine inside STAGING_ALLOWED_CIDRS):

    export QS_E2E_HTTP_USER=reviewer
    export QS_E2E_HTTP_PASSWORD=...

    python scripts/week8_staging_acceptance.py \
        --ui-url https://staging.example.internal \
        --release-sha <exact 40-character release sha> \
        --allowlist-denied-verified

Exit code 0 means every check passed and outputs/week8/hung_staging_acceptance.json
is releasable evidence.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = ROOT / "outputs" / "week8"
EVIDENCE_PATH = EVIDENCE_DIR / "hung_staging_acceptance.json"
BROWSER_EVIDENCE_PATH = EVIDENCE_DIR / "hung_browser_e2e.json"

# The raw Streamlit port. The proxy overlay leaves the UI with no host port, so
# this must not answer from outside the deployment host.
DEFAULT_DIRECT_UI_PORT = 8501

REQUEST_TIMEOUT_SECONDS = 10


def _check(name: str, passed: bool, expected: str, actual: str, detail: str = "") -> dict:
    return {
        "check": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
        "detail": detail,
    }


def _status_code(url: str, credentials: tuple[str, str] | None) -> tuple[int | None, str]:
    """Return the HTTP status for a GET, or (None, reason) when nothing answered.

    Credentials are sent as an explicit Authorization header rather than through
    the URL, so they never appear in a log line or a process listing.
    """
    request = urllib.request.Request(url, method="GET")
    if credentials:
        raw = f"{credentials[0]}:{credentials[1]}".encode("utf-8")
        request.add_header("Authorization", "Basic " + base64.b64encode(raw).decode())

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.status, "ok"
    except urllib.error.HTTPError as exc:
        # A 401 or 403 is a successful observation, not an error, for this gate.
        return exc.code, f"HTTP {exc.code}"
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return None, str(exc)


def _direct_ui_url(ui_url: str, port: int) -> str:
    host = urlparse(ui_url).hostname or ui_url
    return f"http://{host}:{port}/"


def check_direct_ui_unreachable(url: str) -> dict:
    """The Streamlit port itself must not be reachable (DV-HUNG-07)."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port or DEFAULT_DIRECT_UI_PORT

    try:
        with socket.create_connection((host, port), timeout=5):
            return _check(
                "direct_ui_port_unreachable",
                False,
                "connection refused or timeout",
                "connection accepted",
                f"{host}:{port} accepted a TCP connection, so the UI is exposed "
                "without the proxy in front of it",
            )
    except OSError as exc:
        return _check(
            "direct_ui_port_unreachable",
            True,
            "connection refused or timeout",
            "connection failed",
            f"{host}:{port}: {exc}",
        )


def check_proxy_requires_auth(ui_url: str) -> dict:
    """An unauthenticated request must be rejected (DV-HUNG-07)."""
    code, detail = _status_code(ui_url, credentials=None)
    return _check(
        "proxy_requires_authentication",
        code == 401,
        "401",
        "no response" if code is None else str(code),
        detail,
    )


def check_reviewer_allowed(ui_url: str, credentials: tuple[str, str]) -> dict:
    """An approved reviewer with credentials must get through (DV-HUNG-07)."""
    code, detail = _status_code(ui_url, credentials)
    return _check(
        "authorised_reviewer_allowed",
        code == 200,
        "200",
        "no response" if code is None else str(code),
        detail,
    )


def check_allowlist_denies_outside(attested: bool) -> dict:
    """The allowlist check cannot be automated from an allowlisted machine.

    Fails closed rather than reporting an untested control as green: the
    operator has to run the request from outside STAGING_ALLOWED_CIDRS, confirm
    the 403, and pass --allowlist-denied-verified.
    """
    return _check(
        "allowlist_denies_outside_networks",
        attested,
        "403 from a network outside STAGING_ALLOWED_CIDRS",
        "attested by operator" if attested else "not verified",
        ""
        if attested
        else "Run `curl -o /dev/null -w '%{http_code}' <ui-url>` from a machine "
        "outside the allowlist, confirm 403, then re-run with "
        "--allowlist-denied-verified.",
    )


def run_browser_journey(ui_url: str, release_sha: str) -> dict:
    """Delegate to the existing browser runner and fold in its result."""
    command = [
        sys.executable,
        str(ROOT / "scripts" / "week8_run_browser_e2e.py"),
        "--base-url",
        ui_url,
        "--release-sha",
        release_sha,
    ]
    print(f"$ {' '.join(command)}")
    result = subprocess.run(command, cwd=str(ROOT), text=True)

    summary: dict = {}
    if BROWSER_EVIDENCE_PATH.exists():
        try:
            summary = json.loads(BROWSER_EVIDENCE_PATH.read_text(encoding="utf-8"))
        except ValueError as exc:
            summary = {"error": f"unreadable browser evidence: {exc}"}

    check = _check(
        "browser_journey_against_deployed_ui",
        result.returncode == 0,
        "exit 0 with every required journey screenshot",
        f"exit {result.returncode}",
        "; ".join(summary.get("failures", [])) if summary else "",
    )
    check["evidence"] = {
        "path": str(BROWSER_EVIDENCE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "totals": (summary.get("results") or {}).get("totals"),
        "selection": summary.get("selection"),
        "screenshots": summary.get("screenshots"),
    }
    return check


def main() -> int:
    parser = argparse.ArgumentParser(description="Week 8 staging acceptance runner")
    parser.add_argument("--ui-url", required=True, help="Deployed UI base URL.")
    parser.add_argument(
        "--release-sha",
        required=True,
        help="The exact 40-character release SHA that was deployed.",
    )
    parser.add_argument(
        "--direct-ui-url",
        default=None,
        help="Raw Streamlit address that must NOT answer. Defaults to the UI "
        f"host on port {DEFAULT_DIRECT_UI_PORT}.",
    )
    parser.add_argument(
        "--allowlist-denied-verified",
        action="store_true",
        help="Attest that a request from outside STAGING_ALLOWED_CIDRS returned 403.",
    )
    args = parser.parse_args()

    release_sha = args.release_sha.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", release_sha):
        parser.error(
            "--release-sha must be a full 40-character lowercase Git SHA, so the "
            "evidence names exactly one build"
        )

    username = os.environ.get("QS_E2E_HTTP_USER")
    password = os.environ.get("QS_E2E_HTTP_PASSWORD")
    if not username or not password:
        parser.error(
            "Set QS_E2E_HTTP_USER and QS_E2E_HTTP_PASSWORD: the acceptance record "
            "has to prove an authenticated reviewer can reach the UI"
        )

    ui_url = args.ui_url.rstrip("/") + "/"
    direct_url = args.direct_ui_url or _direct_ui_url(ui_url, DEFAULT_DIRECT_UI_PORT)
    started_at = datetime.now(timezone.utc).isoformat()

    checks = [
        check_direct_ui_unreachable(direct_url),
        check_proxy_requires_auth(ui_url),
        check_reviewer_allowed(ui_url, (username, password)),
        check_allowlist_denies_outside(args.allowlist_denied_verified),
    ]
    for check in checks:
        print(f"  [{'PASS' if check['passed'] else 'FAIL'}] {check['check']}")

    # The journey is the expensive step, so it runs only once the access
    # controls hold: a green journey against an unprotected UI would be
    # evidence of the wrong thing.
    access_controls_pass = all(check["passed"] for check in checks)
    if access_controls_pass:
        checks.append(run_browser_journey(ui_url, release_sha))
    else:
        checks.append(
            _check(
                "browser_journey_against_deployed_ui",
                False,
                "runs once the access controls pass",
                "not attempted",
                "Access control checks failed; fix them before recording a journey.",
            )
        )

    passed = all(check["passed"] for check in checks)
    evidence = {
        "task": "DV-HUNG-06/DV-HUNG-07",
        "gate": "staging_acceptance",
        "passed": passed,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "release_sha": release_sha,
        "environment": os.environ.get("QS_ENVIRONMENT", "staging"),
        "target": {
            "ui_url": ui_url,
            "direct_ui_url": direct_url,
            "reviewer": username,
        },
        "checks": checks,
        "failures": [check["check"] for check in checks if not check["passed"]],
    }

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"\nEvidence written to {EVIDENCE_PATH.relative_to(ROOT)}")

    if not passed:
        print("\nSTAGING ACCEPTANCE FAILED")
        for name in evidence["failures"]:
            print(f"  - {name}")
        return 1

    print("\nSTAGING ACCEPTANCE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
