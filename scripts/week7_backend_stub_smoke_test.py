from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _request(base_url: str, method: str, path: str, body: object | None = None) -> tuple[int, dict]:
    url = f"{base_url.rstrip('/')}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"error": raw}
        return exc.code, payload
    except (URLError, TimeoutError, OSError) as exc:
        return 0, {"error": str(exc)}


def _check_envelope(status_code: int, payload: dict) -> bool:
    return (
        status_code == 200
        and payload.get("status") in {"success", "error"}
        and "data" in payload
        and "metadata" in payload
    )


def run_smoke_test(base_url: str) -> dict:
    long_text = "DataFlow pipeline integration test. " * 4
    calls = [
        ("health", "GET", "/api/health", None),
        ("dashboard", "GET", "/api/dashboard/metrics", None),
        ("recent_activity", "GET", "/api/dashboard/recent-activity", None),
        ("review_queue", "GET", "/api/predict/review-queue", None),
        ("rag", "POST", "/api/rag/query", {"question": "What is the DataFlow pipeline?", "top_k": 5}),
        (
            "prediction",
            "POST",
            "/api/predict/document-type",
            {
                "file_name": "sample.pdf",
                "file_type": "pdf",
                "extracted_text": long_text,
                "document_external_id": "doc_sample",
            },
        ),
        (
            "prediction_batch",
            "POST",
            "/api/predict/document-type/batch",
            {
                "payloads": [
                    {"file_name": "sample.pdf", "file_type": "pdf", "extracted_text": long_text},
                    {"file_name": "short.pdf", "file_type": "pdf", "extracted_text": "short"},
                ]
            },
        ),
        ("feedback", "POST", "/api/predict/feedback", {"prediction_log_id": 1}),
        ("suggestions", "POST", "/api/suggestions/generate", {}),
        ("reports", "POST", "/api/reports/generate", {}),
    ]
    results: dict[str, dict] = {}
    checks: dict[str, bool] = {}
    for name, method, path, body in calls:
        status_code, payload = _request(base_url, method, path, body)
        results[name] = {"http_status": status_code, "response": payload}
        checks[name] = _check_envelope(status_code, payload)

    batch_data = results["prediction_batch"]["response"].get("data") or {}
    predictions = batch_data.get("predictions", []) if isinstance(batch_data, dict) else []
    checks["batch_has_two_results"] = len(predictions) == 2
    checks["short_text_is_waiting_for_source"] = (
        len(predictions) == 2 and predictions[1].get("status") == "waiting_for_source"
    )
    checks["long_text_is_review_safe"] = (
        len(predictions) == 2 and predictions[0].get("status") == "needs_review"
    )
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "base_url": base_url,
        "checks": checks,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the Week 7 backend contract stub")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "outputs/integration/week7_backend_stub_smoke_result.json"),
    )
    args = parser.parse_args()
    result = run_smoke_test(args.base_url)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
