from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _display_command(command: list[str]) -> list[str]:
    root_text = str(PROJECT_ROOT)
    return [
        "python" if item == sys.executable else item.replace(root_text, ".")
        for item in command
    ]


def _portable_text(value: str) -> str:
    return value.replace(str(PROJECT_ROOT), ".").replace(
        r"C:\Users\miynzi\.docker\config.json", "<docker-config>"
    )


def _compose_file(name: str) -> Path:
    return PROJECT_ROOT / name


def _run(command: list[str], timeout: int = 120) -> dict:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "command": _display_command(command),
        "returncode": completed.returncode,
        "stdout": _portable_text(completed.stdout[-4000:]),
        "stderr": _portable_text(completed.stderr[-4000:]),
    }


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _wait_for_url(url: str, timeout: int = 60) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=3):
                return True
        except (URLError, TimeoutError, OSError):
            time.sleep(2)
    return False


def run_smoke_test(start_db: bool = False, start_full: bool = False, down: bool = False) -> dict:
    checks: dict[str, bool] = {}
    steps: dict[str, dict] = {}
    if not _docker_available():
        return {
            "status": "failed" if (start_db or start_full or down) else "contract_passed_runtime_not_run",
            "checks": {"docker_cli_available": False},
            "steps": steps,
            "message": "Docker CLI is not available on this machine.",
        }

    steps["database_compose_config"] = _run(
        ["docker", "compose", "-f", str(_compose_file("docker-compose.db.yml")), "config", "--quiet"]
    )
    steps["full_compose_config"] = _run(
        ["docker", "compose", "-f", str(_compose_file("docker-compose.yml")), "config", "--quiet"]
    )
    checks["database_compose_config"] = steps["database_compose_config"]["returncode"] == 0
    checks["full_compose_config"] = steps["full_compose_config"]["returncode"] == 0

    if down:
        steps["database_down"] = _run(
            ["docker", "compose", "-f", str(_compose_file("docker-compose.db.yml")), "down"]
        )
        steps["full_down"] = _run(
            ["docker", "compose", "-f", str(_compose_file("docker-compose.yml")), "down"]
        )
        checks["database_down"] = steps["database_down"]["returncode"] == 0
        checks["full_down"] = steps["full_down"]["returncode"] == 0

    if start_db:
        steps["database_up"] = _run(
            ["docker", "compose", "-f", str(_compose_file("docker-compose.db.yml")), "up", "-d"],
            timeout=180,
        )
        checks["database_up"] = steps["database_up"]["returncode"] == 0
        if checks["database_up"]:
            user = os.getenv("POSTGRES_USER", "datavision")
            database = os.getenv("POSTGRES_DB", "datavision_db")
            ready = False
            for _ in range(30):
                probe = _run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(_compose_file("docker-compose.db.yml")),
                        "exec",
                        "-T",
                        "db",
                        "pg_isready",
                        "-U",
                        user,
                        "-d",
                        database,
                    ],
                    timeout=20,
                )
                if probe["returncode"] == 0:
                    ready = True
                    steps["database_ready_probe"] = probe
                    break
                time.sleep(2)
            checks["database_ready"] = ready
            if ready:
                steps["vector_extension_probe"] = _run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(_compose_file("docker-compose.db.yml")),
                        "exec",
                        "-T",
                        "db",
                        "psql",
                        "-U",
                        user,
                        "-d",
                        database,
                        "-Atqc",
                        "SELECT extname FROM pg_extension WHERE extname = 'vector';",
                    ],
                    timeout=20,
                )
                checks["vector_extension_probe"] = (
                    steps["vector_extension_probe"]["returncode"] == 0
                    and "vector" in steps["vector_extension_probe"]["stdout"].lower()
                )

    if start_full:
        steps["full_up"] = _run(
            ["docker", "compose", "-f", str(_compose_file("docker-compose.yml")), "up", "-d", "db", "backend"],
            timeout=240,
        )
        checks["full_up"] = steps["full_up"]["returncode"] == 0
        if checks["full_up"]:
            backend_url = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000/api").rstrip("/")
            checks["backend_health"] = _wait_for_url(f"{backend_url}/health")
            if checks["backend_health"]:
                backend_smoke = _run(
                    [sys.executable, "scripts/week7_backend_stub_smoke_test.py", "--base-url", backend_url[:-4]],
                    timeout=120,
                )
                steps["backend_smoke"] = backend_smoke
                checks["backend_contract_smoke"] = backend_smoke["returncode"] == 0

    runtime_requested = start_db or start_full or down
    services_started = checks.get("database_up", False) or checks.get("full_up", False)
    if not checks:
        status = "contract_passed_runtime_not_run"
    else:
        status = "passed" if all(checks.values()) else "failed"
        if not runtime_requested and status == "passed":
            status = "contract_passed_runtime_not_run"
    return {
        "status": status,
        "checks": checks,
        "steps": steps,
        "runtime_note": (
            "Services remain running after a successful start. Use --down when finished."
            if services_started and not down
            else "No Docker service was started by this run."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or run the local Week 7 Docker integration stack")
    parser.add_argument("--start-db", action="store_true")
    parser.add_argument("--start-full", action="store_true")
    parser.add_argument("--down", action="store_true")
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "outputs/integration/week7_local_docker_smoke_result.json"),
    )
    args = parser.parse_args()
    result = run_smoke_test(args.start_db, args.start_full, args.down)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in {"passed", "contract_passed_runtime_not_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
