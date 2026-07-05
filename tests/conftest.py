from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTEST_TEMP_PARENT = PROJECT_ROOT / ".pytest_runtime_tmp"


def pytest_configure(config):
    temp_root = PYTEST_TEMP_PARENT / f"session_{os.getpid()}_{uuid.uuid4().hex}"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp_path = str(temp_root)
    os.environ["TMP"] = temp_path
    os.environ["TEMP"] = temp_path
    os.environ["TMPDIR"] = temp_path
    tempfile.tempdir = temp_path
