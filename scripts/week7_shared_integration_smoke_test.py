from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _display_command(command: list[str]) -> list[str]:
    root_text = str(PROJECT_ROOT)
    return [
        "python" if item == sys.executable else item.replace(root_text, ".")
        for item in command
    ]


def _portable_text(value: str) -> str:
    docker_config = str(Path.home() / ".docker" / "config.json")
    return value.replace(str(PROJECT_ROOT), ".").replace(
        docker_config, "<docker-config>"
    )


def _run(command: list[str]) -> dict:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "command": _display_command(command),
        "returncode": completed.returncode,
        "stdout": _portable_text((completed.stdout or "")[-4000:]),
        "stderr": _portable_text((completed.stderr or "")[-4000:]),
    }


def run_smoke_test() -> dict:
    data_pipeline = _run([sys.executable, "scripts/week7_data_pipeline_smoke_test.py"])
    readiness = _run([sys.executable, "scripts/week7_shared_repo_readiness_check.py"])
    compose_db = _run(["docker", "compose", "-f", "docker-compose.db.yml", "config", "--quiet"])
    compose_full = _run(["docker", "compose", "-f", "docker-compose.yml", "config", "--quiet"])
    checks = {
        "data_pipeline_contract": data_pipeline["returncode"] == 0,
        "shared_repo_readiness_report": readiness["returncode"] == 0,
        "database_compose_contract": compose_db["returncode"] == 0,
        "full_compose_contract": compose_full["returncode"] == 0,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "runtime_note": "Docker services are not started by this contract smoke test.",
        "steps": {
            "data_pipeline": data_pipeline,
            "readiness": readiness,
            "docker_db_compose": compose_db,
            "docker_full_compose": compose_full,
        },
    }


def main() -> int:
    result = run_smoke_test()
    output = PROJECT_ROOT / "outputs/integration/week7_shared_integration_smoke_result.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
