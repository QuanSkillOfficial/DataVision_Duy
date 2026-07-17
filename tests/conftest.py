from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTEST_TEMP_PARENT = PROJECT_ROOT / ".pytest_runtime_tmp"
_SESSION_TEMP_ROOT: Path | None = None


def pytest_configure(config):
    global _SESSION_TEMP_ROOT
    if PYTEST_TEMP_PARENT.exists():
        for stale_session in PYTEST_TEMP_PARENT.glob("session_*"):
            shutil.rmtree(stale_session, ignore_errors=True)
    temp_root = PYTEST_TEMP_PARENT / f"session_{os.getpid()}_{uuid.uuid4().hex}"
    temp_root.mkdir(parents=True, exist_ok=True)
    _SESSION_TEMP_ROOT = temp_root
    temp_path = str(temp_root)
    os.environ["TMP"] = temp_path
    os.environ["TEMP"] = temp_path
    os.environ["TMPDIR"] = temp_path
    tempfile.tempdir = temp_path


def pytest_unconfigure(config):
    global _SESSION_TEMP_ROOT
    tempfile.tempdir = None
    if _SESSION_TEMP_ROOT is not None:
        shutil.rmtree(_SESSION_TEMP_ROOT, ignore_errors=True)
        _SESSION_TEMP_ROOT = None
    # Also remove pytest's --basetemp test directories after all plugins and
    # tests have released their file handles.
    shutil.rmtree(PYTEST_TEMP_PARENT, ignore_errors=True)
