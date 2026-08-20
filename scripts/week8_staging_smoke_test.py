"""Start and verify the complete Week 8 Docker staging stack."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs/integration/week8_staging_acceptance.json"


def compose_command(project_name: str) -> list[str]:
    if not re.fullmatch(r"datavision-week8-[a-z0-9-]+", project_name):
        raise ValueError("project name must match datavision-week8-[a-z0-9-]+")
    return ["docker", "compose", "--project-name", project_name, "-f", "docker-compose.yml"]


def run(command: list[str], timeout: int = 900) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "command": command,
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": (completed.stdout or "")[-6000:],
        "stderr": (completed.stderr or "")[-6000:],
    }


def request_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def request_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as response:
        return response.read().decode("utf-8")


def wait_for_json(url: str, timeout: int = 300) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return request_json(url)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(2)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def run_acceptance(backend_url: str, ui_url: str, ui_backend_mode: bool) -> dict[str, Any]:
    health = wait_for_json(f"{backend_url}/health")
    ui_health = request_text(f"{ui_url}/_stcore/health")
    dashboard = request_json(f"{backend_url}/dashboard/metrics")
    rag = request_json(
        f"{backend_url}/rag/query",
        {
            "question": "What is the DataFlow pipeline?",
            "document_id": "doc_dataflow_technical_report",
            "top_k": 5,
        },
    )
    review_queue = request_json(f"{backend_url}/dashboard/review-queue")
    suggestions = request_json(f"{backend_url}/suggestions/generate", {})
    report = request_json(
        f"{backend_url}/reports/generate",
        {"report_type": "Week 8 acceptance"},
    )

    health_data = health.get("data", {})
    dashboard_data = dashboard.get("data", {})
    rag_data = rag.get("data", {})
    checks = {
        "backend_healthy": health_data.get("healthy") is True,
        "database_reachable": health_data.get("database") == "reachable",
        "pgvector_enabled": health_data.get("pgvector") is True,
        "duy_sources_available": dashboard_data.get("source_count") == 4,
        "duy_pages_available": health_data.get("counts", {}).get("document_pages") == 36,
        "lap_chunks_available": health_data.get("counts", {}).get("document_chunks", 0) > 0,
        "lap_retrieval_context": len(rag_data.get("retrieved_context", [])) > 0,
        "lap_citations": len(rag_data.get("citations", [])) > 0,
        "lap_pgvector_backend": rag_data.get("retrieval_backend") == "postgresql/pgvector",
        "review_queue_queryable": isinstance(review_queue.get("data"), list),
        "ui_healthy": "ok" in ui_health.lower() and ui_backend_mode,
        "suggestions_contract": isinstance(suggestions.get("data"), list),
        "report_contract": isinstance(report.get("data", {}).get("sections"), list),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "evidence": {
            "health": health,
            "dashboard": dashboard,
            "rag": rag,
            "review_queue": review_queue,
            "suggestions": suggestions,
            "report": report,
            "ui_health": ui_health,
            "ui_backend_mode": ui_backend_mode,
        },
    }


def collect_failure_evidence(compose: list[str], project_root: Path) -> dict[str, Any]:
    """Capture the failed one-shot seed container's output before cleanup."""
    evidence = {
        "compose_ps": run(compose + ["ps", "-a"]),
        "staging_seed_logs": run(compose + ["logs", "--no-color", "--tail", "300", "staging-seed"]),
    }
    seed_result_path = project_root / "outputs/integration/week8_seed_result.json"
    seed_result_path.parent.mkdir(parents=True, exist_ok=True)
    evidence["seed_result_copy"] = run(
        compose + [
            "cp",
            "staging-seed:/app/outputs/integration/week8_seed_result.json",
            str(seed_result_path),
        ]
    )
    if seed_result_path.exists():
        try:
            evidence["seed_result"] = json.loads(seed_result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            evidence["seed_result_error"] = str(exc)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", default="datavision-week8-local")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000/api")
    parser.add_argument("--ui-url", default="http://127.0.0.1:8501")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()

    compose = compose_command(args.project_name)
    orchestration: dict[str, Any] = {}
    result: dict[str, Any]
    try:
        if args.fresh:
            orchestration["clean_before"] = run(compose + ["down", "--volumes", "--remove-orphans"])
        if args.start:
            orchestration["start"] = run(compose + ["up", "--detach", "--build"], timeout=1200)
            if orchestration["start"]["returncode"] != 0:
                raise RuntimeError(orchestration["start"]["stderr"] or orchestration["start"]["stdout"])

        ui_mode = run(
            compose + [
                "exec", "-T", "ui", "python", "-c",
                "import os; print(os.getenv('QS_USE_BACKEND', 'false'))",
            ]
        )
        if ui_mode["returncode"] != 0:
            raise RuntimeError(ui_mode["stderr"] or ui_mode["stdout"])
        orchestration["ui_mode"] = ui_mode
        result = run_acceptance(
            args.backend_url.rstrip("/"),
            args.ui_url.rstrip("/"),
            ui_mode["stdout"].strip().lower() == "true",
        )
    except Exception as exc:
        failure_evidence = collect_failure_evidence(compose, PROJECT_ROOT)
        seed_logs = failure_evidence["staging_seed_logs"]
        result = {
            "status": "failed",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "error": (
                f"{exc}\n"
                f"staging-seed stderr/stdout:\n"
                f"{seed_logs.get('stderr', '')}\n{seed_logs.get('stdout', '')}"
            )[-12000:],
        }
        orchestration["failure_evidence"] = failure_evidence
    finally:
        if args.cleanup:
            orchestration["clean_after"] = run(compose + ["down", "--volumes", "--remove-orphans"])

    result["orchestration"] = orchestration
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result.get("status"),
        "checks": result.get("checks", {}),
        "output": str(output),
        "error": result.get("error"),
    }, indent=2))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
