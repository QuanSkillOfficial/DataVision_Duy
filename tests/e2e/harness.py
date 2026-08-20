"""
tests/e2e/harness.py
======================
Process and browser plumbing for the Week 8 browser suite (DV-HUNG-02/03).

Keeping this separate from the tests means the same harness can start a local
stack for CI and, later, point the identical browser journey at the private
staging URL (DV-HUNG-06) by setting QS_E2E_BASE_URL.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_DIR = ROOT / "screenshots" / "week8_browser_e2e"

# Streamlit needs a generous budget: every interaction is a server rerun.
DEFAULT_TIMEOUT_MS = 30_000
STARTUP_TIMEOUT_SECONDS = 120.0


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_http(url: str, timeout: float = STARTUP_TIMEOUT_SECONDS) -> None:
    """Block until an HTTP endpoint answers, or raise with the last error."""
    deadline = time.time() + timeout
    last_error = "no attempt made"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status < 500:
                    return
                last_error = f"status {resp.status}"
        except (urllib.error.URLError, OSError) as exc:
            last_error = str(exc)
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


class ManagedProcess:
    """A child process that is always cleaned up, even on test failure."""

    def __init__(self, name: str, command: list[str], env: dict, log_path: Path):
        self.name = name
        self.command = command
        self.env = env
        self.log_path = log_path
        self.process: subprocess.Popen | None = None
        self._log_handle = None

    def start(self) -> "ManagedProcess":
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_handle = self.log_path.open("w", encoding="utf-8")
        self.process = subprocess.Popen(
            self.command,
            env=self.env,
            cwd=str(ROOT),
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
        )
        return self

    def assert_running(self) -> None:
        if self.process is not None and self.process.poll() is not None:
            log = self.log_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(
                f"{self.name} exited with code {self.process.returncode}.\n"
                f"--- {self.log_path.name} ---\n{log[-4000:]}"
            )

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self._log_handle is not None:
            self._log_handle.close()


def e2e_release_sha() -> str:
    """The release identity this run is evidence for.

    CI passes the real candidate SHA; a local run is labelled as local so its
    screenshots can never be mistaken for release evidence.
    """
    return os.environ.get("QS_RELEASE_SHA") or "e2e-local-run"


def contract_stub_path() -> Path:
    """Locate the fault-injectable backend contract stub.

    The stub exposes /api/_control routes that make a route fail on demand, so
    it must never be the same artefact as a backend that serves a real
    environment. In the canonical repository, where `backend_stub/` is the image
    deployed to cloud staging, this stub therefore lives under `tests/`. In this
    repository the local stub doubles as the contract stub, so that is the
    fallback.
    """
    test_only = ROOT / "tests" / "e2e" / "contract_stub" / "main.py"
    return test_only if test_only.exists() else ROOT / "backend_stub" / "main.py"


def start_backend_stub(port: int, log_dir: Path, **extra_env: str) -> ManagedProcess:
    """Start the fixture-backed backend contract stub."""
    env = dict(os.environ)
    env["BACKEND_HOST"] = "127.0.0.1"
    env["BACKEND_PORT"] = str(port)
    # The stub must advertise the same release as the UI, so a mismatch in the
    # browser evidence means a genuine mismatch.
    env["QS_RELEASE_SHA"] = e2e_release_sha()
    env.setdefault("QS_ENVIRONMENT", "e2e")
    env.update(extra_env)

    proc = ManagedProcess(
        "backend stub",
        [sys.executable, str(contract_stub_path())],
        env,
        log_dir / f"backend_stub_{port}.log",
    ).start()
    try:
        wait_for_http(f"http://127.0.0.1:{port}/api/health", timeout=30)
    except RuntimeError:
        proc.assert_running()
        proc.stop()
        raise
    return proc


def start_streamlit(port: int, backend_url: str, log_dir: Path, **extra_env: str) -> ManagedProcess:
    """Start the Streamlit UI in backend mode with a labelled release identity."""
    env = dict(os.environ)
    env["QS_USE_BACKEND"] = "true"
    env["QS_BACKEND_URL"] = backend_url
    env.setdefault("QS_ENVIRONMENT", "e2e")
    env["QS_RELEASE_SHA"] = e2e_release_sha()
    env["PYTHONPATH"] = str(ROOT)
    env.update(extra_env)

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ROOT / "demo" / "streamlit_app.py"),
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--server.fileWatcherType",
        "none",
        "--browser.gatherUsageStats",
        "false",
    ]

    proc = ManagedProcess(
        "streamlit UI", command, env, log_dir / f"streamlit_{port}.log"
    ).start()
    try:
        wait_for_http(f"http://127.0.0.1:{port}/_stcore/health")
    except RuntimeError:
        proc.assert_running()
        proc.stop()
        raise
    return proc
