from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

from .path_utils import ensure_parent, relative_path, resolve_project_path


def compute_sha256(file_path: str | Path) -> str:
    path = resolve_project_path(file_path)
    if path is None or not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_file_size_bytes(file_path: str | Path) -> int:
    path = resolve_project_path(file_path)
    if path is None or not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return path.stat().st_size


def copy_file(input_path: str | Path, output_path: str | Path) -> None:
    source = resolve_project_path(input_path)
    target = ensure_parent(output_path)
    if source is None or not source.exists():
        raise FileNotFoundError(f"File not found: {input_path}")
    shutil.copy2(source, target)


def create_file_manifest(
    *,
    run_id: str,
    source_name: str,
    source_type: str,
    input_path: str | Path | None,
    raw_output_path: str | Path | None,
    ingested_at: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "source_name": source_name,
        "source_type": source_type,
        "input_path": relative_path(input_path),
        "raw_output_path": relative_path(raw_output_path),
        "ingested_at": ingested_at,
    }

    raw_path = resolve_project_path(raw_output_path)
    if raw_path is not None and raw_path.exists():
        manifest.update(
            {
                "file_name": raw_path.name,
                "file_size_bytes": get_file_size_bytes(raw_path),
                "file_hash_sha256": compute_sha256(raw_path),
            }
        )

    if extra:
        manifest.update(extra)
    return manifest

