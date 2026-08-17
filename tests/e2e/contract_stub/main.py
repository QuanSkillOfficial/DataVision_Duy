"""
Small Week 7 backend stub for UI CI smoke testing.

Run:
    python backend_stub/main.py

It intentionally uses only the Python standard library so CI does not need
FastAPI/uvicorn before the real backend is ready.
"""

from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


def _repository_root() -> Path:
    """Find the repository root by looking for the fixtures the stub serves.

    Resolved by search rather than by a fixed number of parent hops, because
    this file sits at a different depth in each repository: at `backend_stub/`
    here, and at `tests/e2e/contract_stub/` in the canonical repository, where
    `backend_stub/` is the image deployed to cloud staging and must not carry
    the /api/_control fault-injection routes.
    """
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "demo" / "fixtures" / "week7").is_dir():
            return candidate
    raise RuntimeError(
        f"Could not locate demo/fixtures/week7 above {here}; the contract stub "
        "must run from inside a checkout of the UI repository."
    )


ROOT = _repository_root()
FIXTURES = ROOT / "demo" / "fixtures" / "week7"

# The repository root is needed to import the UI module's reference
# implementation for the routes it owns (see `suggestions` and `report`).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_json(name: str) -> dict:
    with (FIXTURES / f"{name}.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _envelope(data, **metadata) -> dict:
    return {"data": data, "status": "success", "metadata": metadata}


def health() -> dict:
    """Liveness plus release identity, consumed by the UI header (DV-HUNG-04).

    The real backend must expose the same fields so the UI can prove which
    release it is talking to.
    """
    return _envelope(
        {
            "ok": True,
            "service": "week7_backend_stub",
            "backend_reachable": True,
            "release_sha": os.environ.get("QS_RELEASE_SHA", ""),
            "image_digest": os.environ.get("QS_IMAGE_DIGEST", ""),
            "environment": os.environ.get("QS_ENVIRONMENT", "local"),
        },
        owner="backend_stub",
    )


def dashboard_metrics() -> dict:
    phat = _load_json("phat_dashboard_views_sample")["data"]
    duy = _load_json("duy_latest_ingestion_summary")
    overview = (phat.get("v_dashboard_overview") or [{}])[0]
    quality = phat.get("v_data_quality_dashboard") or []
    total_read = sum(row.get("records_read", 0) for row in quality)
    total_valid = sum(row.get("records_valid", 0) for row in quality)
    total_invalid = sum(row.get("records_invalid", 0) for row in quality)
    scores = [row.get("data_quality_score", 100) for row in quality]
    data = {
        "source_count": overview.get("total_sources", 0),
        "file_count": overview.get("total_documents", 0),
        "link_count": max(0, overview.get("total_sources", 0) - overview.get("total_documents", 0)),
        "record_count": total_read,
        "records_read": total_read,
        "records_valid": total_valid,
        "records_invalid": total_invalid,
        "data_quality_score": round(sum(scores) / len(scores)) if scores else 100,
        "processing_status": "ready",
        "duplicate_risk": "low",
        "parsing_coverage": round(total_valid / max(total_read, 1), 2),
        "rag_query_count": overview.get("total_rag_queries", 0),
        "prediction_count": overview.get("total_predictions", 0),
        "successful_ingestion_runs": duy.get("successful_runs", 0),
        "latest_document": duy.get("latest_document", {}),
        "rag_ready_documents": len(phat.get("v_document_rag_readiness", [])),
        "prediction_review_queue_count": len(phat.get("v_prediction_review_queue", [])),
        "prediction_review_queue": phat.get("v_prediction_review_queue", []),
        "document_processing_status": {},
        "recent_activity": phat.get("v_recent_activity", []),
        "ingestion_runs": phat.get("v_latest_ingestion_runs", []),
    }
    return _envelope(data, owner="backend_stub")


def ingestion_status() -> dict:
    return _envelope(_load_json("duy_latest_ingestion_summary")["latest_ingestion_run"], owner="backend_stub")


def recent_activity() -> dict:
    phat = _load_json("phat_dashboard_views_sample")["data"]
    return _envelope(phat.get("v_recent_activity", []), owner="backend_stub")


def review_queue() -> dict:
    return _envelope(_load_json("tuong_prediction_review_queue_sample")["review_items"], owner="backend_stub")


# The Week 7 normalized fixture from the prediction owner does not carry
# `model_version`, but docs/ui_contracts/prediction_ui_contract.md requires it
# on every prediction response and the UI renders it in the result card footer.
# The stub serves the contract-complete shape so UI CI tests the agreed
# contract; the gap itself is tracked against DV-TUONG-05.
STUB_MODEL_VERSION = os.environ.get("QS_STUB_MODEL_VERSION", "document_classifier_v1")


def _with_contract_defaults(result: dict) -> dict:
    complete = dict(result)
    complete.setdefault("model_version", STUB_MODEL_VERSION)
    complete.setdefault("review_reason", None)
    complete.setdefault("top_predictions", [])
    return complete


def prediction_one() -> dict:
    batch = _load_json("tuong_prediction_batch_response")
    return _envelope(_with_contract_defaults(batch["results"][1]), owner="backend_stub")


def prediction_batch() -> dict:
    results = _load_json("tuong_prediction_batch_response")["results"]
    return _envelope([_with_contract_defaults(r) for r in results], owner="backend_stub")


def rag_query() -> dict:
    payload = _load_json("lap_rag_response_real")
    data = dict(payload.get("data", {}))
    metadata = dict(payload.get("metadata", {}))
    if data.get("status") == "retrieval_only":
        metadata["rag_generation_status"] = "retrieval_only"
        data["status"] = "success"
    return {"data": data, "status": payload.get("status", "success"), "metadata": metadata}


# Suggestion ranking and report assembly are owned by the UI module, and
# docs/backend_api_contract_for_ui.md still requires the backend to expose them.
# The stub therefore serves the module's own reference implementation instead of
# an empty list: returning [] made backend-mode CI skip past the Suggestions and
# Reports pages without ever rendering them.


def _reference_implementation():
    from demo.services import mock_client

    return mock_client


def suggestions(body: dict) -> dict:
    generated = _reference_implementation().generate_suggestions(body or {})
    return _envelope(
        generated.get("data", []),
        owner="backend_stub",
        note="Served from the UI module reference implementation.",
    )


def report(body: dict) -> dict:
    generated = _reference_implementation().generate_report(body or {})
    return _envelope(
        generated.get("data", {}),
        owner="backend_stub",
        note="Served from the UI module reference implementation.",
    )


def feedback(body: dict) -> dict:
    saved = _reference_implementation().submit_prediction_correction(body or {})
    if saved.get("status") == "error":
        return {
            "data": None,
            "status": "error",
            "error": {"message": "Feedback rejected", "detail": str(saved.get("data"))},
            "metadata": {"owner": "backend_stub"},
        }
    return _envelope(saved.get("data", {}), owner="backend_stub")


GET_ROUTES = {
    "/api/health": health,
    "/api/dashboard/metrics": dashboard_metrics,
    "/api/ingestion/status": ingestion_status,
    "/api/dashboard/recent-activity": recent_activity,
    "/api/dashboard/review-queue": review_queue,
    "/api/predict/review-queue": review_queue,
}

# POST handlers receive the decoded request body; GET handlers take no argument.
POST_ROUTES = {
    "/api/dashboard/metrics": lambda body: dashboard_metrics(),
    "/api/predict/document-type": lambda body: prediction_one(),
    "/api/predict/document-type/batch": lambda body: prediction_batch(),
    "/api/predict/feedback": feedback,
    "/api/rag/query": lambda body: rag_query(),
    "/api/suggestions/generate": suggestions,
    "/api/reports/generate": report,
}


# ─────────────────────────────────────────────
# FAULT INJECTION (DV-HUNG-05)
# ─────────────────────────────────────────────
# Lets the browser suite prove timeout / partial-service / unavailable handling
# without needing a real broken backend. Off unless explicitly configured.
#
#   QS_STUB_SLOW_ROUTES=/api/rag/query   QS_STUB_DELAY_SECONDS=30
#   QS_STUB_FAIL_ROUTES=/api/predict/document-type


def _route_set(env_name: str) -> set:
    raw = os.environ.get(env_name, "")
    return {item.strip() for item in raw.split(",") if item.strip()}


SLOW_ROUTES = _route_set("QS_STUB_SLOW_ROUTES")
FAIL_ROUTES = _route_set("QS_STUB_FAIL_ROUTES")
STUB_DELAY_SECONDS = float(os.environ.get("QS_STUB_DELAY_SECONDS", "0"))

# Control routes let a running browser test flip a single endpoint to failing
# mid-session, which is how partial-service behavior is proven end to end.
CONTROL_FAIL = "/api/_control/fail"
CONTROL_RESET = "/api/_control/reset"


class Handler(BaseHTTPRequestHandler):
    def _apply_faults(self, path: str) -> bool:
        """Apply configured faults. Returns True when the request was answered."""
        if path in FAIL_ROUTES:
            self._send(
                503,
                {
                    "data": None,
                    "status": "error",
                    "error": {"message": "Injected backend failure", "detail": path},
                    "metadata": {"path": path, "injected": True},
                },
            )
            return True
        if path in SLOW_ROUTES and STUB_DELAY_SECONDS > 0:
            time.sleep(STUB_DELAY_SECONDS)
        return False

    def _send(self, status_code: int, payload: dict) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if self._apply_faults(path):
            return
        handler = GET_ROUTES.get(path)
        if handler is None:
            self._send(404, {"data": None, "status": "error", "metadata": {"path": path}})
            return
        self._send(200, handler())

    def _handle_control(self, path: str, body: bytes) -> bool:
        """Handle fault-injection control routes. Returns True when handled."""
        if path == CONTROL_RESET:
            FAIL_ROUTES.clear()
            self._send(200, _envelope({"fail_routes": sorted(FAIL_ROUTES)}))
            return True
        if path == CONTROL_FAIL:
            try:
                route = json.loads(body or b"{}").get("route")
            except ValueError:
                route = None
            if not route:
                self._send(
                    400,
                    {"data": None, "status": "error", "metadata": {"error": "route required"}},
                )
                return True
            FAIL_ROUTES.add(route)
            self._send(200, _envelope({"fail_routes": sorted(FAIL_ROUTES)}))
            return True
        return False

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        path = urlparse(self.path).path
        if self._handle_control(path, body):
            return
        if self._apply_faults(path):
            return
        handler = POST_ROUTES.get(path)
        if handler is None:
            self._send(404, {"data": None, "status": "error", "metadata": {"path": path}})
            return

        try:
            decoded = json.loads(body) if body else {}
        except ValueError:
            self._send(
                400,
                {
                    "data": None,
                    "status": "error",
                    "error": {"message": "Request body is not valid JSON", "detail": path},
                    "metadata": {"path": path},
                },
            )
            return

        response = handler(decoded if isinstance(decoded, dict) else {})
        self._send(500 if response.get("status") == "error" else 200, response)

    def log_message(self, format, *args):  # noqa: A003
        return


def main() -> None:
    host = os.environ.get("BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Week 7 backend stub listening on http://{host}:{port}/api")
    server.serve_forever()


if __name__ == "__main__":
    main()
